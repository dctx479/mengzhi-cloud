"""
租户AI配置管理API
"""

import asyncio
import base64
import hashlib

from loguru import logger
from fastapi import APIRouter, Depends, status, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, field_validator
from sqlalchemy.orm import Session
from cryptography.fernet import Fernet
from typing import Optional

from app.api.deps import get_db, get_current_user
from app.core.responses import success_response, error_response
from app.core.errors import ErrorCode, BusinessException
from app.core.config import settings
from app.core.security import decrypt_api_key
from app.models.tenant_ai_config import TenantAIConfig
from app.models.enterprise import Enterprise
from app.models.user import User, UserRole
from app.services.ai.factory import AIProviderFactory
from app.services.ai.base_provider import ChatCompletionRequest, ChatMessage
from app.core.audit import audit_log

router = APIRouter()

# 加密密钥 - 从 SECRET_KEY 确定性派生，确保重启后可解密历史数据
# Fernet要求32字节密钥，先用SHA256派生固定长度密钥，再base64编码
_raw_key = hashlib.sha256(settings.SECRET_KEY.encode()).digest()  # 32字节
_cipher = Fernet(base64.urlsafe_b64encode(_raw_key))

# 测试连接超时（秒）
_TEST_TIMEOUT = 30

# 允许的 AI 提供商白名单
_ALLOWED_PROVIDERS = frozenset({
    "openai", "azure", "anthropic", "deepseek",
    "qwen", "wenxin", "glm", "spark", "moonshot", "custom"
})


# ==================== 请求体 Schema ====================


class CreateAIConfigRequest(BaseModel):
    """创建AI配置请求体 — 接受前端 camelCase 字段"""

    provider: str
    api_key: str = Field(alias="apiKey")
    base_url: Optional[str] = Field(default=None, alias="endpoint")
    default_model: Optional[str] = Field(default=None, alias="model")
    is_active: bool = Field(default=True, alias="isActive")
    name: Optional[str] = None  # 前端传入但后端不存储

    model_config = {"populate_by_name": True}

    @field_validator("provider")
    @classmethod
    def validate_provider(cls, v: str) -> str:
        if v.lower() not in _ALLOWED_PROVIDERS:
            raise ValueError(f"不支持的 provider，允许值: {', '.join(sorted(_ALLOWED_PROVIDERS))}")
        return v.lower()

    @field_validator("api_key")
    @classmethod
    def validate_api_key(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("api_key 不能为空")
        if len(v) > 512:
            raise ValueError("api_key 长度不能超过 512 字符")
        return v


class UpdateAIConfigRequest(BaseModel):
    """更新AI配置请求体 — 接受前端 camelCase 字段"""

    api_key: Optional[str] = Field(default=None, alias="apiKey")
    base_url: Optional[str] = Field(default=None, alias="endpoint")
    default_model: Optional[str] = Field(default=None, alias="model")
    is_active: Optional[bool] = Field(default=None, alias="isActive")
    name: Optional[str] = None

    model_config = {"populate_by_name": True}


# ==================== 工具函数 ====================


def encrypt_api_key(api_key: str) -> str:
    """加密API密钥"""
    return _cipher.encrypt(api_key.encode()).decode()


def _safe_config_dict(config) -> dict:
    """返回配置字典，过滤掉 api_key_encrypted 字段，防止泄露给前端"""
    d = config.to_dict()
    d.pop("api_key_encrypted", None)
    return d


def check_enterprise_admin(user_id: str, enterprise_id: int, db: Session) -> bool:
    """检查用户是否为企业管理员（系统管理员对任何企业都有权限）"""
    user = db.query(User).filter(User.user_uuid == user_id).first()
    if not user:
        return False
    if user.role == UserRole.ADMIN:
        return True
    return user.role == UserRole.ENTERPRISE_ADMIN and user.enterprise_id == enterprise_id


@router.get("/enterprises/{enterprise_id}/ai-configs")
async def list_ai_configs(
    enterprise_id: int, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)
):
    """获取企业AI配置列表"""
    try:
        if not check_enterprise_admin(current_user["user_id"], enterprise_id, db):
            return JSONResponse(
                status_code=status.HTTP_403_FORBIDDEN,
                content=error_response(ErrorCode.PERMISSION_DENIED, "权限不足").dict(),
            )

        configs = db.query(TenantAIConfig).filter(TenantAIConfig.enterprise_id == enterprise_id).all()

        return success_response(data=[_safe_config_dict(config) for config in configs], message="获取配置列表成功").dict()

    except Exception as e:
        logger.error(f"AI config operation failed: {str(e)}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=error_response(ErrorCode.SYSTEM_ERROR, "获取配置失败").dict(),
        )


@router.post("/enterprises/{enterprise_id}/ai-configs")
@audit_log(action="create", resource="ai_config", capture_request_body=True)
async def create_ai_config(
    enterprise_id: int,
    request_body: CreateAIConfigRequest,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
    request: Request = None,
):
    """创建AI配置"""
    try:
        if not check_enterprise_admin(current_user["user_id"], enterprise_id, db):
            return JSONResponse(
                status_code=status.HTTP_403_FORBIDDEN,
                content=error_response(ErrorCode.PERMISSION_DENIED, "权限不足").dict(),
            )

        # 检查企业是否存在
        enterprise = db.query(Enterprise).filter(Enterprise.id == enterprise_id).first()
        if not enterprise:
            return JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                content=error_response(ErrorCode.RECORD_NOT_FOUND, "企业不存在").dict(),
            )

        # 检查provider是否已存在
        existing = (
            db.query(TenantAIConfig)
            .filter(TenantAIConfig.enterprise_id == enterprise_id, TenantAIConfig.provider == request_body.provider)
            .first()
        )
        if existing:
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content=error_response(ErrorCode.PARAM_VALIDATION_FAILED, "该Provider配置已存在").dict(),
            )

        # 创建配置
        config = TenantAIConfig(
            enterprise_id=enterprise_id,
            provider=request_body.provider,
            api_key_encrypted=encrypt_api_key(request_body.api_key),
            base_url=request_body.base_url,
            default_model=request_body.default_model,
            is_active=request_body.is_active,
        )
        db.add(config)
        db.commit()
        db.refresh(config)

        return success_response(data=_safe_config_dict(config), message="创建配置成功").dict()

    except Exception as e:
        logger.error(f"AI config operation failed: {str(e)}")
        db.rollback()
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=error_response(ErrorCode.SYSTEM_ERROR, "创建配置失败").dict(),
        )


@router.patch("/enterprises/{enterprise_id}/ai-configs/{config_id}")
@audit_log(action="update", resource="ai_config", get_resource_id=lambda kwargs: kwargs.get("config_id"), capture_request_body=True)
async def update_ai_config(
    enterprise_id: int,
    config_id: int,
    request_body: UpdateAIConfigRequest,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
    request: Request = None,
):
    """更新AI配置"""
    try:
        if not check_enterprise_admin(current_user["user_id"], enterprise_id, db):
            return JSONResponse(
                status_code=status.HTTP_403_FORBIDDEN,
                content=error_response(ErrorCode.PERMISSION_DENIED, "权限不足").dict(),
            )

        config = (
            db.query(TenantAIConfig)
            .filter(TenantAIConfig.id == config_id, TenantAIConfig.enterprise_id == enterprise_id)
            .first()
        )

        if not config:
            return JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                content=error_response(ErrorCode.RECORD_NOT_FOUND, "配置不存在").dict(),
            )

        if request_body.api_key:
            config.api_key_encrypted = encrypt_api_key(request_body.api_key)
        if request_body.base_url is not None:
            config.base_url = request_body.base_url
        if request_body.default_model is not None:
            config.default_model = request_body.default_model
        if request_body.is_active is not None:
            config.is_active = request_body.is_active

        db.commit()
        db.refresh(config)

        return success_response(data=_safe_config_dict(config), message="更新配置成功").dict()

    except Exception as e:
        logger.error(f"AI config operation failed: {str(e)}")
        db.rollback()
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=error_response(ErrorCode.SYSTEM_ERROR, "更新配置失败").dict(),
        )


@router.delete("/enterprises/{enterprise_id}/ai-configs/{config_id}")
@audit_log(action="delete", resource="ai_config", get_resource_id=lambda kwargs: kwargs.get("config_id"))
async def delete_ai_config(
    enterprise_id: int, config_id: int, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db), request: Request = None
):
    """删除AI配置"""
    try:
        if not check_enterprise_admin(current_user["user_id"], enterprise_id, db):
            return JSONResponse(
                status_code=status.HTTP_403_FORBIDDEN,
                content=error_response(ErrorCode.PERMISSION_DENIED, "权限不足").dict(),
            )

        config = (
            db.query(TenantAIConfig)
            .filter(TenantAIConfig.id == config_id, TenantAIConfig.enterprise_id == enterprise_id)
            .first()
        )

        if not config:
            return JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                content=error_response(ErrorCode.RECORD_NOT_FOUND, "配置不存在").dict(),
            )

        db.delete(config)
        db.commit()

        return success_response(message="删除配置成功").dict()

    except Exception as e:
        logger.error(f"AI config operation failed: {str(e)}")
        db.rollback()
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=error_response(ErrorCode.SYSTEM_ERROR, "删除配置失败").dict(),
        )


@router.post("/enterprises/{enterprise_id}/ai-configs/{config_id}/test")
async def test_ai_config(
    enterprise_id: int, config_id: int, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)
):
    """测试AI配置"""
    try:
        if not check_enterprise_admin(current_user["user_id"], enterprise_id, db):
            return JSONResponse(
                status_code=status.HTTP_403_FORBIDDEN,
                content=error_response(ErrorCode.PERMISSION_DENIED, "权限不足").dict(),
            )

        config = (
            db.query(TenantAIConfig)
            .filter(TenantAIConfig.id == config_id, TenantAIConfig.enterprise_id == enterprise_id)
            .first()
        )

        if not config:
            return JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                content=error_response(ErrorCode.RECORD_NOT_FOUND, "配置不存在").dict(),
            )

        # 解密API密钥并测试连接
        api_key = decrypt_api_key(config.api_key_encrypted)
        provider = AIProviderFactory.create(provider_type=config.provider, api_key=api_key, base_url=config.base_url)

        # 发送测试请求（带超时保护）
        test_request = ChatCompletionRequest(messages=[ChatMessage(role="user", content="test")], max_tokens=10)
        try:
            response = await asyncio.wait_for(
                provider.chat(test_request),
                timeout=_TEST_TIMEOUT
            )
        except asyncio.TimeoutError:
            logger.error(f"AI配置测试超时 (config_id={config_id}, timeout={_TEST_TIMEOUT}s)")
            return JSONResponse(
                status_code=status.HTTP_504_GATEWAY_TIMEOUT,
                content=error_response(ErrorCode.SYSTEM_ERROR, "配置测试超时，请检查网络或API地址").dict(),
            )

        return success_response(
            data={"success": True, "message": "配置测试成功", "model": response.model}, message="配置测试成功"
        ).dict()

    except Exception as e:
        logger.error(f"AI config operation failed: {str(e)}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=error_response(ErrorCode.SYSTEM_ERROR, "配置测试失败").dict(),
        )


# ==================== 用户端获取可用提供商 ====================


@router.get("/available-providers")
async def get_available_providers(current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    """
    获取当前用户可用的AI提供商列表

    管理员返回全部提供商；普通用户返回管理员启用的提供商 + 自定义
    """
    from app.models.system_config import SystemConfig

    # 所有提供商定义
    all_providers = [
        {"id": "openai", "name": "OpenAI", "group": "international"},
        {"id": "azure", "name": "Azure OpenAI", "group": "international"},
        {"id": "anthropic", "name": "Anthropic", "group": "international"},
        {"id": "deepseek", "name": "DeepSeek（深度求索）", "group": "national"},
        {"id": "qwen", "name": "通义千问（阿里）", "group": "national"},
        {"id": "wenxin", "name": "文心一言（百度）", "group": "national"},
        {"id": "glm", "name": "智谱GLM", "group": "national"},
        {"id": "spark", "name": "讯飞星火", "group": "national"},
        {"id": "moonshot", "name": "Moonshot（月之暗面）", "group": "national"},
        {"id": "custom", "name": "自定义接入", "group": "other"},
    ]

    is_admin = current_user.get("role") == "admin"

    if is_admin:
        return success_response(data={"providers": all_providers}).dict()

    # 普通用户：获取管理员启用的提供商
    config = db.query(SystemConfig).filter(SystemConfig.config_key == "enabled_providers").first()

    if config and config.config_value:
        try:
            import json as _json
            # config_value 可能是 list（ORM JSON列）或 JSON 字符串
            raw = config.config_value
            if isinstance(raw, str):
                raw = _json.loads(raw)
            if isinstance(raw, list):
                enabled_ids = set(raw)
            else:
                logger.warning("⚠️ WARNING: enabled_providers 格式无效，回退到全部启用")
                enabled_ids = {p["id"] for p in all_providers}
        except (TypeError, ValueError, _json.JSONDecodeError):
            logger.warning("⚠️ WARNING: enabled_providers 解析失败，回退到全部启用")
            # config_value format invalid, fallback to all
            enabled_ids = {p["id"] for p in all_providers}
    else:
        # 默认全部启用
        enabled_ids = {p["id"] for p in all_providers}

    # 确保 custom 始终可用
    enabled_ids.add("custom")

    filtered = [p for p in all_providers if p["id"] in enabled_ids]
    return success_response(data={"providers": filtered}).dict()
