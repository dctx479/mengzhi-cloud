"""
租户AI配置管理API
"""
from fastapi import APIRouter, Depends, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from cryptography.fernet import Fernet
from typing import Optional

from app.api.deps import get_db, get_current_user
from app.core.responses import success_response, error_response
from app.core.errors import ErrorCode, BusinessException
from app.core.config import settings
from app.models.tenant_ai_config import TenantAIConfig
from app.models.enterprise import Enterprise
from app.models.user import User, UserRole
from app.services.ai.factory import AIProviderFactory
from app.services.ai.base_provider import ChatCompletionRequest, ChatMessage

router = APIRouter()

# 加密密钥（生产环境应从环境变量读取）
ENCRYPTION_KEY = settings.SECRET_KEY.encode()[:32].ljust(32, b'0')
cipher = Fernet(Fernet.generate_key())


def encrypt_api_key(api_key: str) -> str:
    """加密API密钥"""
    return cipher.encrypt(api_key.encode()).decode()


def decrypt_api_key(encrypted: str) -> str:
    """解密API密钥"""
    return cipher.decrypt(encrypted.encode()).decode()


def check_enterprise_admin(user_id: str, enterprise_id: int, db: Session) -> bool:
    """检查用户是否为企业管理员"""
    user = db.query(User).filter(User.user_uuid == user_id).first()
    if not user:
        return False
    return user.role in [UserRole.ADMIN, UserRole.ENTERPRISE_ADMIN] and user.enterprise_id == enterprise_id


@router.get("/enterprises/{enterprise_id}/ai-configs")
async def list_ai_configs(
    enterprise_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取企业AI配置列表"""
    try:
        if not check_enterprise_admin(current_user["user_id"], enterprise_id, db):
            return JSONResponse(
                status_code=status.HTTP_403_FORBIDDEN,
                content=error_response(ErrorCode.PERMISSION_DENIED, "权限不足").dict()
            )

        configs = db.query(TenantAIConfig).filter(
            TenantAIConfig.enterprise_id == enterprise_id
        ).all()

        return success_response(
            data=[config.to_dict() for config in configs],
            message="获取配置列表成功"
        ).dict()

    except Exception as e:
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=error_response(ErrorCode.SYSTEM_ERROR, f"获取配置失败: {str(e)}").dict()
        )


@router.post("/enterprises/{enterprise_id}/ai-configs")
async def create_ai_config(
    enterprise_id: int,
    provider: str,
    api_key: str,
    base_url: Optional[str] = None,
    default_model: Optional[str] = None,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """创建AI配置"""
    try:
        if not check_enterprise_admin(current_user["user_id"], enterprise_id, db):
            return JSONResponse(
                status_code=status.HTTP_403_FORBIDDEN,
                content=error_response(ErrorCode.PERMISSION_DENIED, "权限不足").dict()
            )

        # 检查企业是否存在
        enterprise = db.query(Enterprise).filter(Enterprise.id == enterprise_id).first()
        if not enterprise:
            return JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                content=error_response(ErrorCode.RECORD_NOT_FOUND, "企业不存在").dict()
            )

        # 检查provider是否已存在
        existing = db.query(TenantAIConfig).filter(
            TenantAIConfig.enterprise_id == enterprise_id,
            TenantAIConfig.provider == provider
        ).first()
        if existing:
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content=error_response(ErrorCode.PARAM_VALIDATION_FAILED, "该Provider配置已存在").dict()
            )

        # 创建配置
        config = TenantAIConfig(
            enterprise_id=enterprise_id,
            provider=provider,
            api_key_encrypted=encrypt_api_key(api_key),
            base_url=base_url,
            default_model=default_model,
            is_active=True
        )
        db.add(config)
        db.commit()
        db.refresh(config)

        return success_response(data=config.to_dict(), message="创建配置成功").dict()

    except Exception as e:
        db.rollback()
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=error_response(ErrorCode.SYSTEM_ERROR, f"创建配置失败: {str(e)}").dict()
        )


@router.patch("/enterprises/{enterprise_id}/ai-configs/{config_id}")
async def update_ai_config(
    enterprise_id: int,
    config_id: int,
    api_key: Optional[str] = None,
    base_url: Optional[str] = None,
    default_model: Optional[str] = None,
    is_active: Optional[bool] = None,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """更新AI配置"""
    try:
        if not check_enterprise_admin(current_user["user_id"], enterprise_id, db):
            return JSONResponse(
                status_code=status.HTTP_403_FORBIDDEN,
                content=error_response(ErrorCode.PERMISSION_DENIED, "权限不足").dict()
            )

        config = db.query(TenantAIConfig).filter(
            TenantAIConfig.id == config_id,
            TenantAIConfig.enterprise_id == enterprise_id
        ).first()

        if not config:
            return JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                content=error_response(ErrorCode.RECORD_NOT_FOUND, "配置不存在").dict()
            )

        if api_key:
            config.api_key_encrypted = encrypt_api_key(api_key)
        if base_url is not None:
            config.base_url = base_url
        if default_model is not None:
            config.default_model = default_model
        if is_active is not None:
            config.is_active = is_active

        db.commit()
        db.refresh(config)

        return success_response(data=config.to_dict(), message="更新配置成功").dict()

    except Exception as e:
        db.rollback()
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=error_response(ErrorCode.SYSTEM_ERROR, f"更新配置失败: {str(e)}").dict()
        )


@router.delete("/enterprises/{enterprise_id}/ai-configs/{config_id}")
async def delete_ai_config(
    enterprise_id: int,
    config_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """删除AI配置"""
    try:
        if not check_enterprise_admin(current_user["user_id"], enterprise_id, db):
            return JSONResponse(
                status_code=status.HTTP_403_FORBIDDEN,
                content=error_response(ErrorCode.PERMISSION_DENIED, "权限不足").dict()
            )

        config = db.query(TenantAIConfig).filter(
            TenantAIConfig.id == config_id,
            TenantAIConfig.enterprise_id == enterprise_id
        ).first()

        if not config:
            return JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                content=error_response(ErrorCode.RECORD_NOT_FOUND, "配置不存在").dict()
            )

        db.delete(config)
        db.commit()

        return success_response(message="删除配置成功").dict()

    except Exception as e:
        db.rollback()
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=error_response(ErrorCode.SYSTEM_ERROR, f"删除配置失败: {str(e)}").dict()
        )


@router.post("/enterprises/{enterprise_id}/ai-configs/{config_id}/test")
async def test_ai_config(
    enterprise_id: int,
    config_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """测试AI配置"""
    try:
        if not check_enterprise_admin(current_user["user_id"], enterprise_id, db):
            return JSONResponse(
                status_code=status.HTTP_403_FORBIDDEN,
                content=error_response(ErrorCode.PERMISSION_DENIED, "权限不足").dict()
            )

        config = db.query(TenantAIConfig).filter(
            TenantAIConfig.id == config_id,
            TenantAIConfig.enterprise_id == enterprise_id
        ).first()

        if not config:
            return JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                content=error_response(ErrorCode.RECORD_NOT_FOUND, "配置不存在").dict()
            )

        # 解密API密钥并测试连接
        api_key = decrypt_api_key(config.api_key_encrypted)
        provider = AIProviderFactory.create(
            provider_type=config.provider,
            api_key=api_key,
            base_url=config.base_url
        )

        # 发送测试请求
        test_request = ChatCompletionRequest(
            messages=[ChatMessage(role="user", content="test")],
            max_tokens=10
        )
        response = await provider.chat(test_request)

        return success_response(
            data={"status": "success", "model": response.model},
            message="配置测试成功"
        ).dict()

    except Exception as e:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content=error_response(ErrorCode.PARAM_VALIDATION_FAILED, f"配置测试失败: {str(e)}").dict()
        )
