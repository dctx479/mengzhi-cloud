"""
AI服务商配置管理API
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, Field
from typing import Optional
from app.core.deps import get_db, get_current_user
from app.core.security import aes_encrypt, aes_decrypt
from app.core.config import settings
from app.models.ai_config import AIProviderConfig
from sqlalchemy import select

router = APIRouter()


class AIConfigCreate(BaseModel):
    provider: str
    provider_type: str
    api_endpoint: str
    api_key: str
    model_name: str
    is_active: bool = True
    priority: int = 1
    config_json: Optional[dict] = None


class AIConfigUpdate(BaseModel):
    api_endpoint: Optional[str] = None
    api_key: Optional[str] = None
    model_name: Optional[str] = None
    is_active: Optional[bool] = None
    priority: Optional[int] = None
    config_json: Optional[dict] = None


@router.get("/")
async def get_ai_providers(
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """获取所有AI服务商配置"""
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="仅管理员可访问")

    result = await db.execute(select(AIProviderConfig))
    configs = result.scalars().all()

    return [
        {
            "id": c.id,
            "provider": c.provider,
            "provider_type": c.provider_type,
            "api_endpoint": c.api_endpoint,
            "api_key_encrypted": c.api_key_encrypted[:10] + "****" if c.api_key_encrypted else None,
            "model_name": c.model_name,
            "is_active": c.is_active,
            "priority": c.priority,
            "config_json": c.config_json,
            "created_at": c.created_at.isoformat(),
            "updated_at": c.updated_at.isoformat()
        }
        for c in configs
    ]


@router.post("/")
async def create_ai_provider(
    data: AIConfigCreate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """创建AI服务商配置"""
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="仅管理员可访问")

    # 检查是否已存在
    result = await db.execute(
        select(AIProviderConfig).where(AIProviderConfig.provider == data.provider)
    )
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="该服务商已存在")

    # 加密API Key
    encrypted_key = aes_encrypt(data.api_key, settings.SECRET_KEY)

    config = AIProviderConfig(
        provider=data.provider,
        provider_type=data.provider_type,
        api_endpoint=data.api_endpoint,
        api_key_encrypted=encrypted_key,
        model_name=data.model_name,
        is_active=data.is_active,
        priority=data.priority,
        config_json=data.config_json
    )

    db.add(config)
    await db.commit()

    return {"message": "创建成功", "provider": data.provider}


@router.put("/{provider}")
async def update_ai_provider(
    provider: str,
    data: AIConfigUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """更新AI服务商配置"""
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="仅管理员可访问")

    result = await db.execute(
        select(AIProviderConfig).where(AIProviderConfig.provider == provider)
    )
    config = result.scalar_one_or_none()

    if not config:
        raise HTTPException(status_code=404, detail="服务商不存在")

    # 更新字段
    if data.api_endpoint:
        config.api_endpoint = data.api_endpoint
    if data.api_key:
        config.api_key_encrypted = aes_encrypt(data.api_key, settings.SECRET_KEY)
    if data.model_name:
        config.model_name = data.model_name
    if data.is_active is not None:
        config.is_active = data.is_active
    if data.priority:
        config.priority = data.priority
    if data.config_json:
        config.config_json = data.config_json

    await db.commit()

    return {"message": "更新成功"}


@router.delete("/{provider}")
async def delete_ai_provider(
    provider: str,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """删除AI服务商配置"""
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="仅管理员可访问")

    result = await db.execute(
        select(AIProviderConfig).where(AIProviderConfig.provider == provider)
    )
    config = result.scalar_one_or_none()

    if not config:
        raise HTTPException(status_code=404, detail="服务商不存在")

    await db.delete(config)
    await db.commit()

    return {"message": "删除成功"}


@router.post("/{provider}/test")
async def test_ai_provider(
    provider: str,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """测试AI服务商连接"""
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="仅管理员可访问")

    result = await db.execute(
        select(AIProviderConfig).where(AIProviderConfig.provider == provider)
    )
    config = result.scalar_one_or_none()

    if not config:
        raise HTTPException(status_code=404, detail="服务商不存在")

    # 解密API Key
    api_key = aes_decrypt(config.api_key_encrypted, settings.SECRET_KEY)

    try:
        if provider == "deepseek":
            from openai import OpenAI
            client = OpenAI(api_key=api_key, base_url=config.api_endpoint)
            response = client.chat.completions.create(
                model=config.model_name,
                messages=[{"role": "user", "content": "测试"}],
                max_tokens=10
            )
            return {
                "success": True,
                "message": "连接成功",
                "model": response.model
            }

        elif provider.startswith("volcengine"):
            from volcengine.visual.VisualService import VisualService
            service = VisualService()
            # 解析access_key和secret_key (假设存储在config_json中)
            access_key = config.config_json.get("access_key") if config.config_json else None
            secret_key = config.config_json.get("secret_key") if config.config_json else None

            if not access_key or not secret_key:
                raise Exception("缺少access_key或secret_key")

            service.set_ak(aes_decrypt(access_key, settings.SECRET_KEY))
            service.set_sk(aes_decrypt(secret_key, settings.SECRET_KEY))

            # 简单测试（不实际生成）
            return {
                "success": True,
                "message": "配置验证通过",
                "model": config.model_name
            }

        elif provider == "claude":
            import anthropic
            client = anthropic.AsyncAnthropic(api_key=api_key)
            response = await client.messages.create(
                model=config.model_name,
                max_tokens=10,
                messages=[{"role": "user", "content": "测试"}]
            )
            return {
                "success": True,
                "message": "连接成功",
                "model": response.model
            }

        else:
            return {"success": False, "message": "不支持的服务商"}

    except Exception as e:
        return {
            "success": False,
            "message": f"连接失败: {str(e)}"
        }
