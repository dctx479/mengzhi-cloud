#!/usr/bin/env python3
"""
简化版配额初始化脚本
"""
import pymysql
import yaml
from pathlib import Path

def load_config():
    config_path = Path(__file__).parent.parent / "config" / "quota_rules.yaml"
    with open(config_path) as f:
        return yaml.safe_load(f)

def main():
    print("🔄 开始初始化配额和计费规则...")

    config = load_config()

    # 连接数据库
    conn = pymysql.connect(
        host='localhost',
        user='root',
        password='root123',
        database='agri_platform',
        charset='utf8mb4'
    )

    try:
        cursor = conn.cursor()

        # 创建配额层级表（如果不存在）
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS quota_tiers (
                id BIGINT PRIMARY KEY AUTO_INCREMENT,
                tier_key VARCHAR(50) UNIQUE NOT NULL,
                name VARCHAR(100) NOT NULL,
                monthly_tokens INT NOT NULL,
                daily_tokens INT NOT NULL,
                max_requests_per_minute INT NOT NULL,
                price DECIMAL(10,2) NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # 插入配额层级
        tiers = config['default_quotas']
        for tier_key, tier_data in tiers.items():
            cursor.execute("""
                INSERT INTO quota_tiers
                (tier_key, name, monthly_tokens, daily_tokens, max_requests_per_minute, price)
                VALUES (%s, %s, %s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE
                name=VALUES(name),
                monthly_tokens=VALUES(monthly_tokens),
                daily_tokens=VALUES(daily_tokens),
                max_requests_per_minute=VALUES(max_requests_per_minute),
                price=VALUES(price)
            """, (
                tier_key,
                tier_data['name'],
                tier_data['monthly_tokens'],
                tier_data['daily_tokens'],
                tier_data['max_requests_per_minute'],
                tier_data['price']
            ))
            print(f"✅ 配额层级: {tier_data['name']}")

        # 创建计费规则表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS billing_rules (
                id BIGINT PRIMARY KEY AUTO_INCREMENT,
                rule_type VARCHAR(50) NOT NULL,
                provider VARCHAR(50),
                token_type VARCHAR(50),
                feature VARCHAR(100),
                price DECIMAL(10,6) NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE KEY unique_rule (rule_type, provider, token_type, feature)
            )
        """)

        # 插入Token计费规则
        rules = config['billing_rules']
        for provider, pricing in rules['token_pricing'].items():
            for token_type, price in pricing.items():
                cursor.execute("""
                    INSERT INTO billing_rules
                    (rule_type, provider, token_type, price)
                    VALUES (%s, %s, %s, %s)
                    ON DUPLICATE KEY UPDATE price=VALUES(price)
                """, ('token', provider, token_type, price))

        # 插入请求计费规则
        for feature, price in rules['request_pricing'].items():
            cursor.execute("""
                INSERT INTO billing_rules
                (rule_type, feature, price)
                VALUES (%s, %s, %s)
                ON DUPLICATE KEY UPDATE price=VALUES(price)
            """, ('request', feature, price))

        print("✅ 计费规则初始化完成")

        conn.commit()
        print("✅ 配额和计费规则初始化成功")

    except Exception as e:
        print(f"❌ 初始化失败: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    main()
