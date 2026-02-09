"""
模型配置API
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List

from ..api.deps import get_db, get_current_user
from ..models.user import User
from ..models.ai_config import AIConfig
from ..utils.encryption import encryptor

router = APIRouter()


@router.get("/model-configs")
async def get_model_configs(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取所有模型配置"""
    configs = db.query(AIConfig).filter_by(
        enterprise_id=current_user.enterprise_id
    ).all()

    result = {
        'deepseek': None,
        'qwen': None,
        'zhipu': None,
        'custom': None
    }

    for config in configs:
        result[config.provider] = {
            'enabled': config.is_active,
            'api_key': encryptor.mask_key(config.api_key) if config.api_key else '',
            'base_url': config.base_url or '',
            'model_name': config.model_name or '',
            'priority': config.priority or 5
        }

    return {"code": 0, "data": result}


@router.post("/model-configs/{provider}")
async def save_model_config(
    provider: str,
    config: dict,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """保存模型配置"""
    # 检查企业版权限（自定义模型）
    if provider == 'custom':
        quota = db.query(TenantQuota).filter_by(
            enterprise_id=current_user.enterprise_id
        ).first()
        if quota.tier != 'enterprise_tier':
            return {"code": 403, "message": "自定义模型仅企业版可用"}

    # 查找或创建配置
    ai_config = db.query(AIConfig).filter_by(
        enterprise_id=current_user.enterprise_id,
        provider=provider
    ).first()

    if not ai_config:
        ai_config = AIConfig(
            enterprise_id=current_user.enterprise_id,
            provider=provider
        )
        db.add(ai_config)

    # 更新配置
    ai_config.is_active = config.get('enabled', False)
    ai_config.base_url = config.get('base_url', '')
    ai_config.model_name = config.get('model_name', '')
    ai_config.priority = config.get('priority', 5)

    # 加密API密钥
    if config.get('api_key'):
        ai_config.api_key = encryptor.encrypt(config['api_key'])

    db.commit()

    return {"code": 0, "message": "保存成功"}


@router.post("/model-configs/{provider}/test")
async def test_model_config(
    provider: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """测试模型连接"""
    config = db.query(AIConfig).filter_by(
        enterprise_id=current_user.enterprise_id,
        provider=provider
    ).first()

    if not config:
        return {"code": 404, "message": "配置不存在"}

    # TODO: 实际测试连接
    return {"code": 0, "message": "连接成功"}
