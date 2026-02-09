#!/usr/bin/env python3
"""
初始化配额和计费规则
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import yaml
from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.models.quota import EnterpriseQuota, QuotaTier
from app.models.billing import BillingRule
from loguru import logger

def load_config():
    """加载配置文件"""
    config_path = Path(__file__).parent.parent / "config" / "quota_rules.yaml"
    with open(config_path) as f:
        return yaml.safe_load(f)

def init_quota_tiers(db: Session, config: dict):
    """初始化配额层级"""
    tiers = config['default_quotas']
    for tier_key, tier_data in tiers.items():
        existing = db.query(QuotaTier).filter_by(tier_key=tier_key).first()
        if not existing:
            tier = QuotaTier(
                tier_key=tier_key,
                name=tier_data['name'],
                monthly_tokens=tier_data['monthly_tokens'],
                daily_tokens=tier_data['daily_tokens'],
                max_requests_per_minute=tier_data['max_requests_per_minute'],
                features=tier_data['features'],
                price=tier_data['price']
            )
            db.add(tier)
            logger.info(f"创建配额层级: {tier_data['name']}")
    db.commit()

def init_billing_rules(db: Session, config: dict):
    """初始化计费规则"""
    rules = config['billing_rules']

    # Token计费
    for provider, pricing in rules['token_pricing'].items():
        for token_type, price in pricing.items():
            rule = BillingRule(
                rule_type='token',
                provider=provider,
                token_type=token_type,
                price=price
            )
            db.add(rule)

    # 请求计费
    for feature, price in rules['request_pricing'].items():
        rule = BillingRule(
            rule_type='request',
            feature=feature,
            price=price
        )
        db.add(rule)

    db.commit()
    logger.info("计费规则初始化完成")

def main():
    """主函数"""
    logger.info("开始初始化配额和计费规则...")

    config = load_config()
    db = SessionLocal()

    try:
        init_quota_tiers(db, config)
        init_billing_rules(db, config)
        logger.info("✅ 配额和计费规则初始化成功")
    except Exception as e:
        logger.error(f"❌ 初始化失败: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    main()
