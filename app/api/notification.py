import asyncio
import json
import logging
from typing import List

from fastapi import APIRouter, Body, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse

from app.api.deps import get_current_user_or_create_anonymous, get_registered_user
from app.core.api_decorator import get_route, put_route
from app.repositories.notification import NotificationRepository
from app.schemas.notification import (
    NotificationCategory,
    NotificationLevel,
    NotificationListResponse,
)

logger = logging.getLogger(__name__)

router = APIRouter()


@get_route(
    path="/notifications",
    summary="Get Notifications",
    description="Get notification list for the current user.",
    response_model=NotificationListResponse,
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
    notifications = NotificationRepository.get_notifications_by_user(
        user_id=user.id,
        category=category,
        is_read=is_read,
        level=level,
        limit=limit,
        offset=offset,
    )

    # Get total count
    total_count = NotificationRepository.get_notifications_count_by_user(
        user_id=user.id,
        category=category,
        is_read=is_read,
        level=level,
    )

    return NotificationListResponse(
        notifications=notifications,
        total=total_count,
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


async def notification_event_generator(user_id: str):
    queue = user_queues.setdefault(user_id, asyncio.Queue())
    try:
        while True:
            # Add timeout to prevent hanging connections
            notification = await asyncio.wait_for(queue.get(), timeout=30)
            yield f"data: {json.dumps(notification)}\n\n"
    except asyncio.TimeoutError:
        logger.info(f"Connection timeout for user {user_id}")
    except asyncio.CancelledError:
        logger.info(f"Connection cancelled for user {user_id}")
    finally:
        user_queues.pop(user_id, None)


@router.get(
    "/notifications/sse",
    summary="SSE Notification Stream",
    description=(
        "Server-Sent Events for real-time notifications. "
        "This is a test endpoint that sends counter messages every 2 seconds. "
        "Use EventSource to connect."
    ),
    tags=["notifications"],
)
async def notifications_sse(user=Depends(get_registered_user)):
    async def event_stream():
        async for event in notification_event_generator(user.id):
            yield event

    return StreamingResponse(event_stream(), media_type="text/event-stream")


# Periodic cleanup of inactive connections
async def cleanup_inactive_queues():
    """Clean up inactive queues every 5 minutes"""
    while True:
        try:
            await asyncio.sleep(300)  # Wait 5 minutes
            inactive_users = []

            for user_id, queue in user_queues.items():
                # Check if queue is empty and no active consumers
                if queue.empty() and not queue._getters:
                    inactive_users.append(user_id)
                    logger.info(f"Cleaning up inactive queue for user {user_id}")

            # Remove inactive queues
            for user_id in inactive_users:
                user_queues.pop(user_id, None)

            if inactive_users:
                logger.info(f"Cleaned up {len(inactive_users)} inactive queues")

        except Exception as e:
            logger.warning(f"Error during queue cleanup: {e}")


# Start cleanup task when module loads
try:
    # Try to get running loop to start cleanup task
    loop = asyncio.get_running_loop()
    loop.create_task(cleanup_inactive_queues())
except RuntimeError:
    # No running loop, cleanup will start when first SSE connects
    pass
