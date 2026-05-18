"""
AI媒体生成API
"""

import asyncio
import ipaddress
import logging
import urllib.parse
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, Query, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, validator
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db, require_admin
from app.core.errors import ErrorCode
from app.core.responses import error_response, success_response
from app.models.ai_media_generation import MediaProviderType, MediaTaskStatus
from app.services.ai_media_generation import AIMediaGenerationService, encrypt_media_api_key
from app.services.ai_media_providers import MediaProviderError

logger = logging.getLogger(__name__)

router = APIRouter()

# 服务商连通性测试超时（秒）
_PROVIDER_TEST_TIMEOUT = 30


class CreateMediaProviderRequest(BaseModel):
    provider_code: str = Field(alias="providerCode")
    provider_name: str = Field(alias="providerName")
    provider_type: MediaProviderType = Field(alias="providerType")
    api_key: str = Field(alias="apiKey")
    app_id: Optional[str] = Field(default=None, alias="appId")
    api_endpoint: Optional[str] = Field(default=None, alias="apiEndpoint")
    default_model: Optional[str] = Field(default=None, alias="defaultModel")
    is_active: bool = Field(default=True, alias="isActive")
    is_primary: bool = Field(default=False, alias="isPrimary")
    priority: int = 0
    cost_per_unit: float = Field(default=0.0, alias="costPerUnit")
    rate_limit_per_minute: int = Field(default=60, alias="rateLimitPerMinute")
    config: Optional[Dict[str, Any]] = None

    model_config = {"populate_by_name": True}

    @validator('api_endpoint')
    def validate_endpoint_not_private(cls, v):
        if v:
            try:
                parsed = urllib.parse.urlparse(v)
                if not parsed.scheme or not parsed.netloc:
                    raise ValueError('api_endpoint 必须是合法的 URL（含 scheme 和 host）')
                host = parsed.hostname
                if host:
                    try:
                        ip = ipaddress.ip_address(host)
                        if ip.is_private or ip.is_loopback or ip.is_link_local:
                            raise ValueError('不允许使用内网地址')
                    except ValueError as e:
                        if '不允许' in str(e):
                            raise
                        # host is a domain name, not an IP — allowed
            except ValueError:
                raise
            except Exception as e:
                raise ValueError(f'api_endpoint 格式无效: {e}')
        return v


class UpdateMediaProviderRequest(BaseModel):
    provider_name: Optional[str] = Field(default=None, alias="providerName")
    provider_type: Optional[MediaProviderType] = Field(default=None, alias="providerType")
    api_key: Optional[str] = Field(default=None, alias="apiKey")
    app_id: Optional[str] = Field(default=None, alias="appId")
    api_endpoint: Optional[str] = Field(default=None, alias="apiEndpoint")
    default_model: Optional[str] = Field(default=None, alias="defaultModel")
    is_active: Optional[bool] = Field(default=None, alias="isActive")
    is_primary: Optional[bool] = Field(default=None, alias="isPrimary")
    priority: Optional[int] = None
    cost_per_unit: Optional[float] = Field(default=None, alias="costPerUnit")
    rate_limit_per_minute: Optional[int] = Field(default=None, alias="rateLimitPerMinute")
    config: Optional[Dict[str, Any]] = None

    model_config = {"populate_by_name": True}


class CreateImageTaskRequest(BaseModel):
    prompt: str = Field(..., min_length=1, max_length=2000)
    negative_prompt: Optional[str] = Field(default=None, max_length=1000, alias="negativePrompt")
    provider_id: Optional[int] = Field(default=None, alias="providerId")
    model: Optional[str] = Field(default=None, max_length=100)
    width: Optional[int] = Field(default=1024, ge=128, le=4096)
    height: Optional[int] = Field(default=1024, ge=128, le=4096)
    result_count: int = Field(default=1, ge=1, le=4, alias="resultCount")
    params: Optional[Dict[str, Any]] = None

    model_config = {"populate_by_name": True}


class CreateVideoTaskRequest(BaseModel):
    prompt: str = Field(..., min_length=1, max_length=2000)
    negative_prompt: Optional[str] = Field(default=None, max_length=1000, alias="negativePrompt")
    provider_id: Optional[int] = Field(default=None, alias="providerId")
    model: Optional[str] = Field(default=None, max_length=100)
    width: Optional[int] = Field(default=1280, ge=128, le=4096)
    height: Optional[int] = Field(default=720, ge=128, le=4096)
    duration: int = Field(default=5, ge=1, le=300)
    params: Optional[Dict[str, Any]] = None

    model_config = {"populate_by_name": True}


def _request_to_provider_data(request_body: CreateMediaProviderRequest) -> Dict[str, Any]:
    return {
        "provider_code": request_body.provider_code,
        "provider_name": request_body.provider_name,
        "provider_type": request_body.provider_type,
        "api_key_encrypted": encrypt_media_api_key(request_body.api_key),
        "app_id": request_body.app_id,
        "api_endpoint": request_body.api_endpoint,
        "default_model": request_body.default_model,
        "is_active": request_body.is_active,
        "is_primary": request_body.is_primary,
        "priority": request_body.priority,
        "cost_per_unit": request_body.cost_per_unit,
        "rate_limit_per_minute": request_body.rate_limit_per_minute,
        "config": request_body.config,
    }


def _update_request_to_data(request_body: UpdateMediaProviderRequest) -> Dict[str, Any]:
    data = request_body.model_dump(exclude_unset=True, by_alias=False)
    if "api_key" in data:
        data["api_key_encrypted"] = encrypt_media_api_key(data.pop("api_key"))
    return data


def _json_error(http_status: int, code: ErrorCode, message: str) -> JSONResponse:
    return JSONResponse(status_code=http_status, content=error_response(code, message).dict())


@router.get("/admin/media-providers")
async def list_media_providers(
    provider_type: Optional[MediaProviderType] = Query(default=None, alias="providerType"),
    include_inactive: bool = Query(default=False, alias="includeInactive"),
    current_user: dict = Depends(require_admin),
    db: Session = Depends(get_db),
):
    service = AIMediaGenerationService(db)
    providers = service.list_providers(provider_type=provider_type, include_inactive=include_inactive)
    return success_response(data={"items": [provider.to_dict() for provider in providers]}).dict()


@router.post("/admin/media-providers", status_code=status.HTTP_201_CREATED)
async def create_media_provider(
    request_body: CreateMediaProviderRequest,
    current_user: dict = Depends(require_admin),
    db: Session = Depends(get_db),
):
    try:
        service = AIMediaGenerationService(db)
        provider = service.create_provider(_request_to_provider_data(request_body))
        return success_response(data=provider.to_dict(), message="创建服务商成功").dict()
    except Exception as exc:
        logger.exception("创建媒体服务商失败: %s", exc)
        db.rollback()
        return _json_error(status.HTTP_500_INTERNAL_SERVER_ERROR, ErrorCode.SYSTEM_ERROR, "创建服务商失败")


@router.put("/admin/media-providers/{provider_id}")
async def update_media_provider(
    provider_id: int,
    request_body: UpdateMediaProviderRequest,
    current_user: dict = Depends(require_admin),
    db: Session = Depends(get_db),
):
    try:
        service = AIMediaGenerationService(db)
        provider = service.get_provider(provider_id)
        if not provider:
            return _json_error(status.HTTP_404_NOT_FOUND, ErrorCode.RECORD_NOT_FOUND, "服务商不存在")
        provider = service.update_provider(provider, _update_request_to_data(request_body))
        return success_response(data=provider.to_dict(), message="更新服务商成功").dict()
    except Exception as exc:
        logger.exception("更新媒体服务商失败 provider_id=%s: %s", provider_id, exc)
        db.rollback()
        return _json_error(status.HTTP_500_INTERNAL_SERVER_ERROR, ErrorCode.SYSTEM_ERROR, "更新服务商失败")


@router.delete("/admin/media-providers/{provider_id}")
async def delete_media_provider(
    provider_id: int,
    current_user: dict = Depends(require_admin),
    db: Session = Depends(get_db),
):
    try:
        service = AIMediaGenerationService(db)
        provider = service.get_provider(provider_id)
        if not provider:
            return _json_error(status.HTTP_404_NOT_FOUND, ErrorCode.RECORD_NOT_FOUND, "服务商不存在")
        service.delete_provider(provider)
        return success_response(message="服务商已禁用").dict()
    except Exception as exc:
        logger.exception("删除媒体服务商失败 provider_id=%s: %s", provider_id, exc)
        db.rollback()
        return _json_error(status.HTTP_500_INTERNAL_SERVER_ERROR, ErrorCode.SYSTEM_ERROR, "删除服务商失败")


@router.post("/admin/media-providers/{provider_id}/test")
async def test_media_provider(
    provider_id: int,
    current_user: dict = Depends(require_admin),
    db: Session = Depends(get_db),
):
    service = AIMediaGenerationService(db)
    provider = service.get_provider(provider_id)
    if not provider:
        return _json_error(status.HTTP_404_NOT_FOUND, ErrorCode.RECORD_NOT_FOUND, "服务商不存在")
    try:
        result = await asyncio.wait_for(service.validate_provider(provider), timeout=_PROVIDER_TEST_TIMEOUT)
    except asyncio.TimeoutError:
        logger.error("媒体服务商测试超时 provider_id=%s", provider_id)
        return _json_error(status.HTTP_504_GATEWAY_TIMEOUT, ErrorCode.SYSTEM_ERROR, "服务商连通性测试超时")
    data = {"success": result["success"], "message": result["message"], "provider": provider.to_dict()}
    return success_response(data=data).dict()


@router.post("/admin/media-providers/{provider_id}/health-check")
async def health_check_media_provider(
    provider_id: int,
    current_user: dict = Depends(require_admin),
    db: Session = Depends(get_db),
):
    service = AIMediaGenerationService(db)
    provider = service.get_provider(provider_id)
    if not provider:
        return _json_error(status.HTTP_404_NOT_FOUND, ErrorCode.RECORD_NOT_FOUND, "服务商不存在")
    try:
        result = await asyncio.wait_for(service.validate_provider(provider), timeout=_PROVIDER_TEST_TIMEOUT)
    except asyncio.TimeoutError:
        logger.error("媒体服务商健康检查超时 provider_id=%s", provider_id)
        return _json_error(status.HTTP_504_GATEWAY_TIMEOUT, ErrorCode.SYSTEM_ERROR, "服务商健康检查超时")
    data = {"success": result["success"], "message": result["message"], "provider": provider.to_dict()}
    return success_response(data=data, message="健康检查完成").dict()


@router.get("/admin/media-generation/costs")
async def get_media_generation_costs(
    media_type: Optional[MediaProviderType] = Query(default=None, alias="mediaType"),
    current_user: dict = Depends(require_admin),
    db: Session = Depends(get_db),
):
    service = AIMediaGenerationService(db)
    return success_response(data=service.get_cost_summary(media_type=media_type)).dict()


@router.post("/images", status_code=status.HTTP_201_CREATED)
async def create_image_generation_task(
    request_body: CreateImageTaskRequest,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return await _create_generation_task(current_user, db, MediaProviderType.IMAGE, request_body)


@router.post("/videos", status_code=status.HTTP_201_CREATED)
async def create_video_generation_task(
    request_body: CreateVideoTaskRequest,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return await _create_generation_task(current_user, db, MediaProviderType.VIDEO, request_body)


async def _create_generation_task(current_user: dict, db: Session, media_type: MediaProviderType, request_body):
    try:
        service = AIMediaGenerationService(db)
        user = service.get_user_by_uuid(current_user["user_id"])
        if not user:
            return _json_error(status.HTTP_401_UNAUTHORIZED, ErrorCode.USER_NOT_FOUND, "用户不存在")
        provider = service.select_provider(media_type, request_body.provider_id)
        if not provider:
            return _json_error(
                status.HTTP_503_SERVICE_UNAVAILABLE, ErrorCode.SERVICE_UNAVAILABLE, "没有可用的媒体生成服务商"
            )
        task = service.create_generation_task(
            user=user,
            media_type=media_type,
            prompt=request_body.prompt,
            provider=provider,
            model=request_body.model,
            negative_prompt=request_body.negative_prompt,
            width=request_body.width,
            height=request_body.height,
            duration=getattr(request_body, "duration", None),
            result_count=getattr(request_body, "result_count", 1),
            request_params=request_body.params,
        )
        try:
            task = await service.submit_task_to_provider(task)
        except MediaProviderError as submit_err:
            logger.warning("媒体服务商提交任务失败 (MediaProviderError): %s", submit_err)
            service.db.rollback()
            task = service.db.merge(task)  # rollback 后重新附加到 session，防止 DetachedInstanceError
            task.status = MediaTaskStatus.FAILED
            task.error_message = "服务商提交失败"
            task.completed_at = datetime.now(timezone.utc)
            service.db.commit()
            service.db.refresh(task)
        except Exception as submit_err:
            logger.exception("媒体服务商提交任务发生未知错误: %s", submit_err)
            service.db.rollback()
            return _json_error(
                status.HTTP_502_BAD_GATEWAY,
                ErrorCode.SERVICE_UNAVAILABLE,
                "媒体生成服务暂时不可用，请稍后重试",
            )
        return success_response(data=task.to_dict(), message="生成任务已创建").dict()
    except Exception as exc:
        logger.exception("创建生成任务失败: %s", exc)
        db.rollback()
        return _json_error(status.HTTP_500_INTERNAL_SERVER_ERROR, ErrorCode.SYSTEM_ERROR, "创建生成任务失败")


@router.get("/tasks")
async def list_generation_tasks(
    status_filter: Optional[MediaTaskStatus] = Query(default=None, alias="status"),
    media_type: Optional[MediaProviderType] = Query(default=None, alias="mediaType"),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100, alias="pageSize"),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    service = AIMediaGenerationService(db)
    user = service.get_user_by_uuid(current_user["user_id"])
    if not user:
        return _json_error(status.HTTP_401_UNAUTHORIZED, ErrorCode.USER_NOT_FOUND, "用户不存在")
    total, items = service.list_tasks(
        user=user,
        is_admin=current_user.get("role") == "admin",
        status=status_filter,
        media_type=media_type,
        page=page,
        page_size=page_size,
    )
    return success_response(data={"items": [item.to_dict() for item in items], "total": total, "page": page}).dict()


@router.get("/tasks/{task_uuid}")
async def get_generation_task(
    task_uuid: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    service = AIMediaGenerationService(db)
    user = service.get_user_by_uuid(current_user["user_id"])
    if not user:
        return _json_error(status.HTTP_401_UNAUTHORIZED, ErrorCode.USER_NOT_FOUND, "用户不存在")
    task = service.get_task(task_uuid)
    if not task:
        return _json_error(status.HTTP_404_NOT_FOUND, ErrorCode.RECORD_NOT_FOUND, "生成任务不存在")
    if current_user.get("role") != "admin" and task.user_id != user.id:
        return _json_error(status.HTTP_403_FORBIDDEN, ErrorCode.PERMISSION_DENIED, "权限不足")

    # 对于进行中的任务，主动向服务商同步最新状态（轮询场景）
    if task.status in (MediaTaskStatus.PENDING, MediaTaskStatus.PROCESSING):
        try:
            task = await service.sync_task_status(task)
        except Exception as sync_err:
            # 同步失败不影响返回已有状态，记录警告即可
            logger.warning("同步任务状态失败 task_uuid=%s: %s", task_uuid, sync_err)

    return success_response(data=task.to_dict()).dict()


@router.post("/tasks/{task_uuid}/cancel")
async def cancel_generation_task(
    task_uuid: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    service = AIMediaGenerationService(db)
    user = service.get_user_by_uuid(current_user["user_id"])
    if not user:
        return _json_error(status.HTTP_401_UNAUTHORIZED, ErrorCode.USER_NOT_FOUND, "用户不存在")
    task = service.get_task(task_uuid)
    if not task:
        return _json_error(status.HTTP_404_NOT_FOUND, ErrorCode.RECORD_NOT_FOUND, "生成任务不存在")
    if current_user.get("role") != "admin" and task.user_id != user.id:
        return _json_error(status.HTTP_403_FORBIDDEN, ErrorCode.PERMISSION_DENIED, "权限不足")
    if task.status in [MediaTaskStatus.SUCCEEDED, MediaTaskStatus.FAILED, MediaTaskStatus.CANCELED]:
        return _json_error(status.HTTP_400_BAD_REQUEST, ErrorCode.PARAM_VALUE_INVALID, "当前任务状态不可取消")
    task = service.cancel_task(task)
    return success_response(data=task.to_dict(), message="任务已取消").dict()
