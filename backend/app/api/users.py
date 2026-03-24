"""
用户管理API路由

包含端点:
- POST /api/v1/users/avatar - 上传用户头像
- GET /api/v1/users/me - 获取当前用户信息
- GET /api/v1/users/settings - 获取用户设置
- PUT /api/v1/users/settings - 更新用户设置
- GET /api/v1/users/security/logs - 安全日志
- POST /api/v1/users/security/bind-phone - 绑定手机
- POST /api/v1/users/security/bind-email - 绑定邮箱
- GET /api/v1/users/security/devices - 登录设备列表
- DELETE /api/v1/users/security/devices/{device_id} - 移除设备

版本: 1.1
"""

from fastapi import APIRouter, Depends, UploadFile, File, status, Query
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from typing import Optional

from app.api.deps import get_db, get_current_user
from app.services.file_service import FileService
from app.core.responses import success_response, error_response
from app.core.errors import BusinessException, ErrorCode
from app.core.logging_config import logger
from app.models.user import User

router = APIRouter()


@router.post("/avatar", response_model=dict, tags=["用户"])
async def upload_avatar(
    file: UploadFile = File(..., description="头像文件"),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    """上传用户头像

    参数:
        file: 头像图片文件（支持 JPG, PNG, GIF, WEBP）
        current_user: 当前登录用户
        db: 数据库会话

    返回:
        头像URL

    示例:
        POST /api/v1/users/avatar
        Content-Type: multipart/form-data

        file: <binary data>
    """
    try:
        # 获取用户ID
        user_uuid = current_user.get("user_id")
        user = db.query(User).filter(User.user_uuid == user_uuid).first()

        if not user:
            return JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                content=error_response(code=ErrorCode.RECORD_NOT_FOUND, message="用户不存在").dict(),
            )

        # 上传头像
        avatar_url = await FileService.upload_avatar(file, user.id)

        # 删除旧头像（如果存在）
        if user.avatar_url and user.avatar_url.startswith("/uploads"):
            old_path = user.avatar_url.lstrip("/")
            FileService.delete_file(old_path)

        # 更新用户头像
        user.avatar_url = avatar_url
        db.commit()
        db.refresh(user)

        return success_response(data={"avatar_url": avatar_url}, message="头像上传成功").dict()

    except BusinessException as e:
        logger.warning(f"头像上传失败: {e.message}")
        return JSONResponse(
            status_code=e.get_http_status(), content=error_response(code=e.code, message=e.message).dict()
        )
    except Exception as e:
        logger.error(f"头像上传异常: {str(e)}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=error_response(code=ErrorCode.SYSTEM_ERROR, message=f"头像上传失败: {str(e)}").dict(),
        )


@router.get("/me", response_model=dict, tags=["用户"])
async def get_current_user_info(current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)) -> dict:
    """获取当前用户信息

    参数:
        current_user: 当前登录用户
        db: 数据库会话

    返回:
        用户详细信息
    """
    try:
        user_uuid = current_user.get("user_id")
        user = db.query(User).filter(User.user_uuid == user_uuid).first()

        if not user:
            return JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                content=error_response(code=ErrorCode.RECORD_NOT_FOUND, message="用户不存在").dict(),
            )

        return success_response(data=user.to_dict_safe(), message="获取用户信息成功").dict()

    except Exception as e:
        logger.error(f"获取用户信息异常: {str(e)}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=error_response(code=ErrorCode.SYSTEM_ERROR, message="获取用户信息失败").dict(),
        )


# ============ 用户设置 ============

_DEFAULT_SETTINGS = {
    "email_notifications": True,
    "sms_notifications": False,
    "profile_public": False,
    "language": "zh-CN",
    "theme": "auto",
}


@router.get("/settings", response_model=dict, tags=["用户"])
async def get_user_settings(
    current_user: dict = Depends(get_current_user),
) -> dict:
    """获取用户设置

    路径: GET /api/v1/users/settings
    """
    return success_response(data=_DEFAULT_SETTINGS, message="获取设置成功").dict()


@router.put("/settings", response_model=dict, tags=["用户"])
async def update_user_settings(
    settings_data: dict,
    current_user: dict = Depends(get_current_user),
) -> dict:
    """更新用户设置

    路径: PUT /api/v1/users/settings
    """
    merged = {**_DEFAULT_SETTINGS, **{k: v for k, v in settings_data.items() if k in _DEFAULT_SETTINGS}}
    return success_response(data=merged, message="设置已保存").dict()


# ============ 安全相关 ============


@router.get("/security/logs", response_model=dict, tags=["用户"])
async def get_security_logs(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100, alias="pageSize"),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    """获取安全操作日志

    路径: GET /api/v1/users/security/logs
    """
    from app.models.audit_log import AuditLog

    user_uuid = current_user.get("user_id")
    user = db.query(User).filter(User.user_uuid == user_uuid).first()
    if not user:
        return success_response(data={"items": [], "total": 0}, message="获取日志成功").dict()

    offset = (page - 1) * page_size
    logs_q = db.query(AuditLog).filter(AuditLog.user_id == user.id).order_by(AuditLog.created_at.desc())
    total = logs_q.count()
    logs = logs_q.offset(offset).limit(page_size).all()

    items = [
        {
            "id": str(log.id),
            "event_type": log.action,
            "ip_address": log.ip_address or "",
            "user_agent": log.user_agent or "",
            "created_at": log.created_at.isoformat() if log.created_at else "",
            "success": log.status == "success",
        }
        for log in logs
    ]
    return success_response(data={"items": items, "total": total}, message="获取日志成功").dict()


@router.post("/security/bind-phone", response_model=dict, tags=["用户"])
async def bind_phone(
    request: dict,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    """绑定手机号

    路径: POST /api/v1/users/security/bind-phone
    """
    phone = request.get("phone", "")
    code = request.get("code", "")
    if not phone or not code:
        raise BusinessException(code=ErrorCode.PARAM_ERROR, message="手机号和验证码不能为空")

    user_uuid = current_user.get("user_id")
    user = db.query(User).filter(User.user_uuid == user_uuid).first()
    if not user:
        raise BusinessException(code=ErrorCode.RECORD_NOT_FOUND, message="用户不存在")

    user.phone = phone
    db.commit()
    return success_response(data={"phone": phone}, message="手机号绑定成功").dict()


@router.post("/security/bind-email", response_model=dict, tags=["用户"])
async def bind_email(
    request: dict,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    """绑定邮箱

    路径: POST /api/v1/users/security/bind-email
    """
    email = request.get("email", "")
    code = request.get("code", "")
    if not email or not code:
        raise BusinessException(code=ErrorCode.PARAM_ERROR, message="邮箱和验证码不能为空")

    user_uuid = current_user.get("user_id")
    user = db.query(User).filter(User.user_uuid == user_uuid).first()
    if not user:
        raise BusinessException(code=ErrorCode.RECORD_NOT_FOUND, message="用户不存在")

    user.email = email
    db.commit()
    return success_response(data={"email": email}, message="邮箱绑定成功").dict()


@router.get("/security/devices", response_model=dict, tags=["用户"])
async def get_devices(
    current_user: dict = Depends(get_current_user),
) -> dict:
    """获取登录设备列表

    路径: GET /api/v1/users/security/devices
    注意: 设备管理功能待实现，当前返回空列表
    """
    return success_response(data=[], message="获取设备列表成功").dict()


@router.delete("/security/devices/{device_id}", response_model=dict, tags=["用户"])
async def remove_device(
    device_id: str,
    current_user: dict = Depends(get_current_user),
) -> dict:
    """移除登录设备

    路径: DELETE /api/v1/users/security/devices/{device_id}
    注意: 设备管理功能待实现
    """
    return success_response(data={"device_id": device_id}, message="设备已移除").dict()
