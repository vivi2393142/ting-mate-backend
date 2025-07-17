from typing import List, Optional

from fastapi import Depends, Query

from app.api.deps import get_current_user_or_create_anonymous
from app.core.api_decorator import get_route
from app.repositories.activity_log import ActivityLogRepository
from app.repositories.user import UserRepository
from app.schemas.activity_log import (
    Action,
    ActivityLogListResponse,
    ActivityLogResponse,
    AvailableActionsResponse,
    UserInfo,
)
from app.schemas.user import User


@get_route(
    path="/activity-logs",
    summary="Get Activity Logs",
    description="Get activity logs for the current user with optional filtering by action types.",
    response_model=ActivityLogListResponse,
    tags=["activity-logs"],
)
def get_activity_logs(
    user: User = Depends(get_current_user_or_create_anonymous),
    actions: Optional[List[Action]] = Query(
        None, description="Filter by specific action types"
    ),
    limit: int = Query(50, ge=1, le=100, description="Number of logs to return"),
    offset: int = Query(0, ge=0, description="Number of logs to skip"),
):
    try:
        logs = ActivityLogRepository.get_activity_logs(
            user_id=user.id,
            user_role=user.role,
            actions=actions,
            limit=limit,
            offset=offset,
        )
        total = ActivityLogRepository.get_activity_logs_count(
            user_id=user.id, user_role=user.role, actions=actions
        )
        log_responses = []
        for log in logs:
            user_info = UserRepository.get_user(log.user_id, "id")
            user_settings = UserRepository.get_user_settings(log.user_id)
            user_data = UserInfo(
                id=log.user_id,
                email=user_info.email if user_info else None,
                name=user_settings.get("name") if user_settings else None,
            )
            target_user_data = None
            if log.target_user_id:
                target_user_info = UserRepository.get_user(log.target_user_id, "id")
                target_user_settings = UserRepository.get_user_settings(
                    log.target_user_id
                )
                if target_user_info:
                    target_user_data = UserInfo(
                        id=log.target_user_id,
                        email=target_user_info.email,
                        name=(
                            target_user_settings.get("name")
                            if target_user_settings
                            else None
                        ),
                    )
            log_responses.append(
                ActivityLogResponse(
                    id=log.id,
                    user=user_data,
                    target_user=target_user_data,
                    action=log.action,
                    detail=log.detail,
                    timestamp=log.timestamp,
                )
            )
        return ActivityLogListResponse(
            logs=log_responses, total=total, limit=limit, offset=offset
        )
    except Exception as e:
        raise ValueError(f"Failed to get activity logs: {str(e)}")


@get_route(
    path="/activity-logs/actions",
    summary="Get Available Actions",
    description="Get list of available action types for filtering activity logs.",
    response_model=AvailableActionsResponse,
    tags=["activity-logs"],
)
def get_available_actions():
    return AvailableActionsResponse(actions=[action.value for action in Action])
