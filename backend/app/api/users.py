"""
用户管理API路由 - BUG-022 修复

包含端点:
- POST /api/v1/users/avatar - 上传用户头像
- GET /api/v1/users/me - 获取当前用户信息
- PUT /api/v1/users/me - 更新用户信息

版本: 1.0
创建日期: 2026-01-17
"""

from fastapi import APIRouter, Depends, UploadFile, File, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

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
    db: Session = Depends(get_db)
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
        user_uuid = current_user.get("user_uuid")
        user = db.query(User).filter(User.user_uuid == user_uuid).first()
        
        if not user:
            return JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                content=error_response(
                    code=ErrorCode.RECORD_NOT_FOUND,
                    message="用户不存在"
                ).dict()
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
        
        return success_response(
            data={"avatar_url": avatar_url},
            message="头像上传成功"
        ).dict()
        
    except BusinessException as e:
        logger.warning(f"头像上传失败: {e.message}")
        return JSONResponse(
            status_code=e.get_http_status(),
            content=error_response(
                code=e.code,
                message=e.message
            ).dict()
        )
    except Exception as e:
        logger.error(f"头像上传异常: {str(e)}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=error_response(
                code=ErrorCode.SYSTEM_ERROR,
                message=f"头像上传失败: {str(e)}"
            ).dict()
        )


@router.get("/me", response_model=dict, tags=["用户"])
async def get_current_user_info(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> dict:
    """获取当前用户信息
    
    参数:
        current_user: 当前登录用户
        db: 数据库会话
    
    返回:
        用户详细信息
    """
    try:
        user_uuid = current_user.get("user_uuid")
        user = db.query(User).filter(User.user_uuid == user_uuid).first()
        
        if not user:
            return JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                content=error_response(
                    code=ErrorCode.RECORD_NOT_FOUND,
                    message="用户不存在"
                ).dict()
            )
        
        return success_response(
            data=user.to_dict_safe(),
            message="获取用户信息成功"
        ).dict()
        
    except Exception as e:
        logger.error(f"获取用户信息异常: {str(e)}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=error_response(
                code=ErrorCode.SYSTEM_ERROR,
                message="获取用户信息失败"
            ).dict()
        )
