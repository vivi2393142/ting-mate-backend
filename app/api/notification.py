import asyncio
import json
from typing import List

from fastapi import APIRouter, Body, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse

from app.api.deps import get_current_user_or_create_anonymous
from app.core.api_decorator import get_route, put_route
from app.repositories.notification import NotificationRepository
from app.schemas.notification import (
    NotificationCategory,
    NotificationData,
    NotificationLevel,
)

router = APIRouter()


async def notification_event_generator(user_id: str):
    queue = user_queues.setdefault(user_id, asyncio.Queue())
    try:
        while True:
            notification = await queue.get()
            yield f"data: {json.dumps(notification)}\n\n"
    except asyncio.CancelledError:
        user_queues.pop(user_id, None)


@get_route(
    path="/notifications",
    summary="Get Notifications",
    description="Get notification list for the current user.",
    response_model=list[NotificationData],
    tags=["notifications"],
)
def get_notifications_api(
    user=Depends(get_current_user_or_create_anonymous),
    category: NotificationCategory = Query(None, description="Filter by category"),
    level: NotificationLevel = Query(None, description="Filter by level"),
    is_read: bool = Query(None, description="Filter by read status"),
    limit: int = Query(
        50, ge=1, le=100, description="Number of notifications to return"
    ),
    offset: int = Query(0, ge=0, description="Number of notifications to skip"),
):
    return NotificationRepository.get_notifications_by_user(
        user_id=user.id,
        category=category,
        is_read=is_read,
        level=level,
        limit=limit,
        offset=offset,
    )


@put_route(
    path="/notifications/mark-read",
    summary="Mark Notifications as Read",
    description="Mark multiple notifications as read by their IDs.",
    tags=["notifications"],
)
def mark_notifications_as_read_api(
    notification_ids: List[str] = Body(
        ..., description="List of notification IDs to mark as read"
    ),
    user=Depends(get_current_user_or_create_anonymous),
):
    """Mark notifications as read for the current user."""
    if not notification_ids:
        raise HTTPException(
            status_code=400, detail="Notification IDs list cannot be empty"
        )

    # Verify all notifications belong to the current user
    for notification_id in notification_ids:
        notification = NotificationRepository.get_notifications_by_id(notification_id)
        if not notification:
            raise HTTPException(
                status_code=404, detail=f"Notification {notification_id} not found"
            )
        if notification.user_id != user.id:
            raise HTTPException(
                status_code=403,
                detail=f"Notification {notification_id} does not belong to current user",
            )

    # Mark notifications as read
    success_count = 0
    for notification_id in notification_ids:
        if NotificationRepository.mark_as_read(notification_id):
            success_count += 1

    return {
        "message": f"Successfully marked {success_count} out of {len(notification_ids)} notifications as read",
        "marked_count": success_count,
        "total_count": len(notification_ids),
    }


# In-memory queue for each user (user_id: asyncio.Queue)
user_queues = {}


@get_route(
    path="/notifications/sse",
    summary="SSE Notification Stream",
    description="Server-Sent Events for real-time notifications. Use EventSource to connect.",
    tags=["notifications"],
    response_class=StreamingResponse,
)
async def notifications_sse(user=Depends(get_current_user_or_create_anonymous)):
    async def event_stream():
        async for event in notification_event_generator(user.id):
            yield event

    return StreamingResponse(event_stream(), media_type="text/event-stream")


# Helper for NotificationManager to push to SSE
async def push_notification_to_sse(user_id: str, notification: NotificationData):
    queue = user_queues.get(user_id)
    if queue:
        await queue.put(notification.model_dump())
