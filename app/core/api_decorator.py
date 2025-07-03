import logging
from functools import wraps
from typing import List, Optional, Type

from fastapi import HTTPException
from pydantic import BaseModel

logger = logging.getLogger(__name__)


class BaseResponse(BaseModel):
    success: bool = True
    message: str
    data: Optional[dict] = None


def api_route(
    path: str,
    method: str = "POST",
    response_model: Type[BaseModel] = BaseResponse,
    summary: str = "",
    description: str = "",
    tags: List[str] = None,
    status_code: int = 200,
):
    def decorator(func):
        if not summary:
            raise ValueError(f"API {path} must provide summary")
        if not description:
            raise ValueError(f"API {path} must provide description")

        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                logger.info(f"API called: {method} {path}")
                result = func(*args, **kwargs)
                if not isinstance(result, BaseModel):
                    if isinstance(result, dict):
                        result = BaseResponse(
                            message="Operation successful", data=result
                        )
                    else:
                        result = BaseResponse(
                            message="Operation successful", data={"result": result}
                        )
                logger.info(f"API success: {method} {path}")
                return result
            except HTTPException as e:
                logger.warning(f"HTTP error in {path}: {e.detail}")
                raise
            except ValueError as e:
                logger.error(f"Business logic error in {path}: {str(e)}")
                raise HTTPException(status_code=400, detail=str(e))
            except Exception as e:
                logger.error(f"Unexpected error in {path}: {str(e)}")
                raise HTTPException(status_code=500, detail="Internal server error")

        wrapper._route_config = {
            "path": path,
            "method": method,
            "response_model": response_model,
            "summary": summary,
            "description": description,
            "tags": tags or [],
            "status_code": status_code,
        }
        return wrapper

    return decorator


def get_route(path: str, summary: str, description: str, **kwargs):
    return api_route(path, "GET", summary=summary, description=description, **kwargs)


def post_route(path: str, summary: str, description: str, **kwargs):
    return api_route(path, "POST", summary=summary, description=description, **kwargs)


def put_route(path: str, summary: str, description: str, **kwargs):
    return api_route(path, "PUT", summary=summary, description=description, **kwargs)


def delete_route(path: str, summary: str, description: str, **kwargs):
    return api_route(path, "DELETE", summary=summary, description=description, **kwargs)


def auto_register_routes(router, module):
    import inspect

    for name, func in inspect.getmembers(module, inspect.isfunction):
        if hasattr(func, "_route_config"):
            config = func._route_config
            route_method = getattr(router, config["method"].lower())
            route_method(
                config["path"],
                response_model=config["response_model"],
                summary=config["summary"],
                description=config["description"],
                tags=config["tags"],
                status_code=config["status_code"],
            )(func)
