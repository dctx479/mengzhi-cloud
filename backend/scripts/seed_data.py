#!/usr/bin/env python3
"""数据库种子数据脚本

功能:
- 创建测试用户
- 创建示例产品
- 创建管理员账户
- 填充演示数据

使用:
    python -m scripts.seed_data [--users N] [--products N]

选项:
    --users N: 创建N个测试用户（默认5个）
    --products N: 创建N个示例产品（默认10个）
    --clear: 清空现有数据（谨慎使用）
"""

import sys
import os
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Optional

# 添加项目根目录到Python路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy.orm import Session
from passlib.context import CryptContext
from app.database import SessionLocal, engine
from app.models.user import User, UserType, UserStatus, UserRole
from app.models.product import Product
from app.models.conversation import Conversation, Message
from app.models.base import generate_uuid
from app.models.quota_package import QuotaPackage, PackageType, PackagePeriod


# 密码加密上下文
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    """哈希密码"""
    return pwd_context.hash(password)


def create_admin_user(db: Session) -> Optional[User]:
    """创建管理员用户"""
    # 检查管理员是否已存在
    existing_admin = db.query(User).filter(
        User.username == "admin"
    ).first()

    if existing_admin:
        print("  ℹ 管理员账户已存在，跳过创建")
        return existing_admin

    admin = User(
        user_uuid=generate_uuid(),
        username="admin",
        email="admin@platform.local",
        phone=None,
        password_hash=hash_password("admin123456"),
        user_type=UserType.PERSONAL,
        status=UserStatus.ACTIVE,
        role=UserRole.ADMIN,
        nickname="系统管理员",
        gender=1,
    )

    db.add(admin)
    db.commit()
    db.refresh(admin)
    print(f"  ✓ 管理员用户已创建 (ID: {admin.id}, UUID: {admin.user_uuid})")
    return admin


def create_test_users(db: Session, count: int = 5) -> List[User]:
    """创建测试用户"""
    users = []

    # 检查现有用户
    existing_count = db.query(User).filter(
        User.username.like("testuser%")
    ).count()

    if existing_count > 0:
        print(f"  ℹ 已存在{existing_count}个测试用户，跳过创建")
        return db.query(User).filter(User.username.like("testuser%")).all()

    user_data = [
        {
            "username": "testuser001",
            "email": "testuser001@platform.local",
            "phone": "13800000001",
            "nickname": "测试用户001",
            "user_type": UserType.PERSONAL,
        },
        {
            "username": "testuser002",
            "email": "testuser002@platform.local",
            "phone": "13800000002",
            "nickname": "测试用户002",
            "user_type": UserType.PERSONAL,
        },
        {
            "username": "testuser003",
            "email": "testuser003@platform.local",
            "phone": "13800000003",
            "nickname": "测试用户003",
            "user_type": UserType.ENTERPRISE,
        },
        {
            "username": "testuser004",
            "email": "testuser004@platform.local",
            "phone": "13800000004",
            "nickname": "测试用户004",
            "user_type": UserType.PERSONAL,
        },
        {
            "username": "testuser005",
            "email": "testuser005@platform.local",
            "phone": "13800000005",
            "nickname": "测试用户005",
            "user_type": UserType.ENTERPRISE,
        },
    ]

    for data in user_data[:count]:
        user = User(
            user_uuid=generate_uuid(),
            username=data["username"],
            email=data["email"],
            phone=data["phone"],
            password_hash=hash_password("password123"),
            user_type=data["user_type"],
            status=UserStatus.ACTIVE,
            role=UserRole.USER,
            nickname=data["nickname"],
            gender=0,
        )
        db.add(user)
        users.append(user)

    db.commit()
    for user in users:
        db.refresh(user)
        print(f"  ✓ 测试用户已创建: {user.username} (ID: {user.id})")

    return users


def create_sample_products(db: Session, count: int = 10) -> List[Product]:
    """创建示例产品"""
    products = []

    # 检查现有产品
    existing_count = db.query(Product).filter(
        Product.sku.like("SAMPLE%")
    ).count()

    if existing_count > 0:
        print(f"  ℹ 已存在{existing_count}个示例产品，跳过创建")
        return db.query(Product).filter(Product.sku.like("SAMPLE%")).all()

    product_data = [
        {
            "sku": "SAMPLE001",
            "name": "内蒙古牛肉",
            "category": "肉类",
            "price": 88.88,
            "cost": 45.00,
            "stock": 100,
            "region": "内蒙古自治区",
            "cultural_tags": ["草原", "生态", "优质"],
            "cultural_description": "来自内蒙古大草原的优质牛肉，绿色无污染",
            "origin_story": "这是来自蒙古族聚居区的传统优质牛肉",
            "efficacy": "营养丰富，高蛋白低脂肪",
            "usage": "适合烤、炖、涮",
        },
        {
            "sku": "SAMPLE002",
            "name": "蒙古羊肉",
            "category": "肉类",
            "price": 98.88,
            "cost": 50.00,
            "stock": 150,
            "region": "内蒙古自治区",
            "cultural_tags": ["原生态", "传统", "美味"],
            "cultural_description": "蒙古族传统美食，肉质鲜嫩",
            "origin_story": "源自千年草原游牧文化",
            "efficacy": "温阳补气，增强体质",
            "usage": "适合涮火锅、红烧",
        },
        {
            "sku": "SAMPLE003",
            "name": "蒙古酸奶",
            "category": "乳制品",
            "price": 22.88,
            "cost": 8.00,
            "stock": 500,
            "region": "内蒙古自治区",
            "cultural_tags": ["发酵", "益生菌", "传统"],
            "cultural_description": "传统蒙古酸奶制作工艺",
            "origin_story": "蒙古族传统饮品，历史悠久",
            "efficacy": "促进消化，强健骨骼",
            "usage": "直接饮用或作为沙拉酱料",
        },
        {
            "sku": "SAMPLE004",
            "name": "套马杆手工艺品",
            "category": "工艺品",
            "price": 188.88,
            "cost": 80.00,
            "stock": 30,
            "region": "呼和浩特市",
            "cultural_tags": ["手工", "文化", "收藏"],
            "cultural_description": "蒙古族传统套马杆手工制品",
            "origin_story": "源于蒙古族游牧时期的传统工具，现为文化艺术品",
            "efficacy": "装饰收藏价值",
            "usage": "室内装饰、收藏品",
        },
        {
            "sku": "SAMPLE005",
            "name": "蒙古刀具套装",
            "category": "工艺品",
            "price": 368.88,
            "cost": 150.00,
            "stock": 20,
            "region": "包头市",
            "cultural_tags": ["手工", "传统", "精品"],
            "cultural_description": "蒙古族传统刀具，工艺精湛",
            "origin_story": "蒙古族传统冷兵器制作技艺传承",
            "efficacy": "实用性与观赏性兼备",
            "usage": "实用工具或装饰收藏",
        },
        {
            "sku": "SAMPLE006",
            "name": "内蒙古莜面",
            "category": "农产品",
            "price": 18.88,
            "cost": 6.00,
            "stock": 300,
            "region": "乌兰察布市",
            "cultural_tags": ["粗粮", "健康", "传统"],
            "cultural_description": "内蒙古特产莜面，营养丰富",
            "origin_story": "乌兰察布地区的特色农产品",
            "efficacy": "低GI食品，有益血糖控制",
            "usage": "煮粥、做面条",
        },
        {
            "sku": "SAMPLE007",
            "name": "蒙古奶酪",
            "category": "乳制品",
            "price": 48.88,
            "cost": 15.00,
            "stock": 100,
            "region": "锡林郭勒盟",
            "cultural_tags": ["发酵", "传统", "营养"],
            "cultural_description": "蒙古族传统奶制品",
            "origin_story": "游牧民族的传统食品",
            "efficacy": "高钙高蛋白，助消化",
            "usage": "直接食用或配餐",
        },
        {
            "sku": "SAMPLE008",
            "name": "内蒙古蜂蜜",
            "category": "农产品",
            "price": 58.88,
            "cost": 20.00,
            "stock": 80,
            "region": "兴安盟",
            "cultural_tags": ["有机", "天然", "滋补"],
            "cultural_description": "纯天然蒙古蜂蜜",
            "origin_story": "来自大草原的天然蜂蜜",
            "efficacy": "润肺止咳，美容养颜",
            "usage": "水冲饮用、调味",
        },
        {
            "sku": "SAMPLE009",
            "name": "蒙古族服饰",
            "category": "服饰",
            "price": 288.88,
            "cost": 100.00,
            "stock": 15,
            "region": "呼伦贝尔市",
            "cultural_tags": ["传统", "手工", "文化"],
            "cultural_description": "蒙古族传统服饰，工艺精美",
            "origin_story": "蒙古族传统民族服装",
            "efficacy": "文化展示与穿着",
            "usage": "民族庆典、文化展示",
        },
        {
            "sku": "SAMPLE010",
            "name": "草原奶茶",
            "category": "饮品",
            "price": 28.88,
            "cost": 8.00,
            "stock": 200,
            "region": "阿拉善盟",
            "cultural_tags": ["传统", "饮品", "文化"],
            "cultural_description": "蒙古草原传统奶茶",
            "origin_story": "蒙古族传统饮品文化",
            "efficacy": "温暖身体，补充能量",
            "usage": "热水冲泡",
        },
    ]

    for data in product_data[:count]:
        product = Product(
            sku=data["sku"],
            name=data["name"],
            description=f"{data['cultural_description']}。{data['efficacy']}。",
            category=data["category"],
            price=data["price"],
            cost=data["cost"],
            stock=data["stock"],
            region=data["region"],
            cultural_tags=data["cultural_tags"],
            cultural_description=data["cultural_description"],
            origin_story=data["origin_story"],
            efficacy=data["efficacy"],
            usage=data["usage"],
            status="active",
            is_featured=(len(products) < 3),
        )
        db.add(product)
        products.append(product)

    db.commit()
    for product in products:
        db.refresh(product)
        print(f"  ✓ 产品已创建: {product.name} (SKU: {product.sku}, ID: {product.id})")

    return products


def create_quota_packages(db: Session) -> List[QuotaPackage]:
    """创建默认配额套餐"""
    existing_count = db.query(QuotaPackage).count()
    if existing_count > 0:
        print(f"  ℹ 已存在{existing_count}个配额套餐，跳过创建")
        return db.query(QuotaPackage).all()

    packages_data = [
        {
            "name": "专业版",
            "package_type": PackageType.PROFESSIONAL,
            "period": PackagePeriod.MONTHLY,
            "price": 99.00,
            "chat_quota": 1000,
            "generation_quota": 500,
            "storage_quota_mb": 10240,  # 10GB
            "validity_days": 30,
            "is_active": True,
            "is_recommended": False,
            "sort_order": 1,
        },
        {
            "name": "商业版",
            "package_type": PackageType.STANDARD,
            "period": PackagePeriod.MONTHLY,
            "price": 299.00,
            "chat_quota": 5000,
            "generation_quota": 2000,
            "storage_quota_mb": 102400,  # 100GB
            "validity_days": 30,
            "is_active": True,
            "is_recommended": True,
            "sort_order": 2,
        },
        {
            "name": "企业版",
            "package_type": PackageType.ENTERPRISE,
            "period": PackagePeriod.MONTHLY,
            "price": 999.00,
            "chat_quota": 0,  # 0 = unlimited
            "generation_quota": 0,
            "storage_quota_mb": 0,
            "validity_days": 30,
            "is_active": True,
            "is_recommended": False,
            "sort_order": 3,
        },
    ]

    packages = []
    for data in packages_data:
        pkg = QuotaPackage(**data)
        db.add(pkg)
        packages.append(pkg)

    db.commit()
    for pkg in packages:
        db.refresh(pkg)
        print(f"  ✓ 套餐已创建: {pkg.name} (ID: {pkg.id}, ¥{pkg.price}/月)")

    return packages


def create_sample_conversations(db: Session, users: List[User]) -> List[Conversation]:
    """创建示例对话"""
    conversations = []

    # 检查现有对话
    existing_count = db.query(Conversation).count()
    if existing_count > 0:
        print(f"  ℹ 已存在{existing_count}个对话，跳过创建")
        return db.query(Conversation).all()

    if not users:
        print("  ℹ 没有用户，跳过创建对话")
        return []

    for i, user in enumerate(users[:3]):  # 为前3个用户创建对话
        conv = Conversation(
            id=generate_uuid(),
            user_id=user.user_uuid,
            title=f"对话 {i + 1}: 产品咨询",
            description="关于内蒙古特产的咨询",
            message_count=2,
            total_tokens=150,
            total_cost=0.02,
            status="active",
        )
        db.add(conv)
        conversations.append(conv)

    db.commit()
    for conv in conversations:
        db.refresh(conv)
        print(f"  ✓ 对话已创建: {conv.title} (ID: {conv.id})")

    # 创建示例消息
    print("  创建示例消息...")
    messages = []
    for conv in conversations:
        # 用户消息
        user_msg = Message(
            id=generate_uuid(),
            conversation_id=conv.id,
            role="user",
            content="请介绍一下内蒙古的特色产品",
            input_tokens=20,
            output_tokens=0,
            total_tokens=20,
            cost=0.001,
        )
        messages.append(user_msg)

        # 助手消息
        assistant_msg = Message(
            id=generate_uuid(),
            conversation_id=conv.id,
            role="assistant",
            content="内蒙古有很多特色产品，包括牛肉、羊肉、奶制品等。这些产品都来自草原，品质优秀。",
            input_tokens=20,
            output_tokens=75,
            total_tokens=95,
            cost=0.01,
        )
        messages.append(assistant_msg)

    db.add_all(messages)
    db.commit()
    print(f"  ✓ 已创建{len(messages)}条示例消息")

    return conversations


def clear_all_data(db: Session) -> bool:
    """清空所有数据"""
    try:
        print("警告: 即将删除所有数据，该操作不可恢复！")
        confirm = input("继续? (yes/no): ").lower()
        if confirm != "yes":
            print("取消操作")
            return False

        # 删除消息
        db.query(Message).delete()
        # 删除对话
        db.query(Conversation).delete()
        # 删除产品
        db.query(Product).delete()
        # 删除用户
        db.query(User).delete()

        db.commit()
        print("✓ 所有数据已清空")
        return True
    except Exception as e:
        print(f"✗ 清空数据失败: {str(e)}")
        db.rollback()
        return False


def seed_database(
    clear: bool = False,
    num_users: int = 5,
    num_products: int = 10
) -> bool:
    """执行种子数据创建"""
    db = SessionLocal()

    try:
        print("\n" + "=" * 60)
        print("  数据库种子数据创建")
        print("=" * 60)

        # 清空数据
        if clear:
            if not clear_all_data(db):
                return False

        # 创建管理员
        print("\n创建管理员用户...")
        admin = create_admin_user(db)

        # 创建测试用户
        print("\n创建测试用户...")
        users = create_test_users(db, num_users)

        # 创建配额套餐
        print("\n创建配额套餐...")
        quota_packages = create_quota_packages(db)

        # 创建产品
        print("\n创建示例产品...")
        products = create_sample_products(db, num_products)

        # 创建对话
        print("\n创建示例对话...")
        conversations = create_sample_conversations(db, users)

        print("\n" + "=" * 60)
        print("  种子数据创建完成")
        print("=" * 60)
        print(f"✓ 已创建:")
        print(f"  - 管理员: 1人")
        print(f"  - 测试用户: {len(users)}人")
        print(f"  - 配额套餐: {len(quota_packages)}个")
        print(f"  - 示例产品: {len(products)}个")
        print(f"  - 示例对话: {len(conversations)}个")
        print("=" * 60)

        return True

    except Exception as e:
        print(f"\n✗ 种子数据创建失败: {str(e)}")
        db.rollback()
        return False
    finally:
        db.close()


def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(
        description="数据库种子数据脚本"
    )
    parser.add_argument(
        "--users",
        type=int,
        default=5,
        help="创建的测试用户数量"
    )
    parser.add_argument(
        "--products",
        type=int,
        default=10,
        help="创建的示例产品数量"
    )
    parser.add_argument(
        "--clear",
        action="store_true",
        help="清空现有数据后重建"
    )

    args = parser.parse_args()

    success = seed_database(
        clear=args.clear,
        num_users=args.users,
        num_products=args.products
    )

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
