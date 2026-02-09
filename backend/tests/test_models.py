"""
数据模型单元测试

测试内容：
- 模型字段验证
- 关系映射
- to_dict()方法
- 业务逻辑方法
- Enum验证

运行: pytest tests/test_models.py -v
"""

import pytest
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.models.base import BaseModel, generate_uuid
from app.models.user import User, UserType, UserStatus, UserRole, Gender
from app.models.product import Product, ProductStatus


# ==================== 基类模型测试 ====================

class TestBaseModel:
    """基类模型功能测试"""

    @pytest.mark.unit
    def test_generate_uuid(self):
        """测试UUID生成"""
        uuid1 = generate_uuid()
        uuid2 = generate_uuid()

        # 应该生成有效的UUID
        assert uuid1 is not None
        assert isinstance(uuid1, str)
        assert len(uuid1) == 36

        # 每次应该生成不同的UUID
        assert uuid1 != uuid2

    @pytest.mark.unit
    def test_base_model_timestamps(self, test_db_session):
        """测试基类时间戳字段"""
        before = datetime.utcnow()

        product = Product(
            sku="TEST-001",
            name="测试产品",
            category="测试",
            price=100.00,
            cost=50.00,
            stock=10,
            region="测试地区",
            region_code="00"
        )

        test_db_session.add(product)
        test_db_session.commit()

        after = datetime.utcnow()

        # 验证创建时间在合理范围内
        assert product.created_at is not None
        assert before <= product.created_at <= after
        assert product.updated_at is not None

    @pytest.mark.unit
    def test_base_model_to_dict(self, test_db_session):
        """测试to_dict()方法"""
        product = Product(
            sku="TEST-001",
            name="测试产品",
            category="测试",
            price=100.00,
            cost=50.00,
            stock=10,
            region="测试地区",
            region_code="00"
        )

        test_db_session.add(product)
        test_db_session.commit()

        result = product.to_dict()

        # 应该返回字典，包含所有字段
        assert isinstance(result, dict)
        assert "sku" in result
        assert "name" in result
        assert result["name"] == "测试产品"

    @pytest.mark.unit
    def test_base_model_to_dict_exclude(self, test_db_session):
        """测试to_dict_exclude()方法"""
        product = Product(
            sku="TEST-001",
            name="测试产品",
            category="测试",
            price=100.00,
            cost=50.00,
            stock=10,
            region="测试地区",
            region_code="00"
        )

        test_db_session.add(product)
        test_db_session.commit()

        result = product.to_dict_exclude(exclude=["created_at", "updated_at"])

        # 不应该包含被排除的字段
        assert "created_at" not in result
        assert "updated_at" not in result
        assert "name" in result

    @pytest.mark.unit
    def test_base_model_from_dict(self):
        """测试from_dict()方法"""
        data = {
            "sku": "TEST-001",
            "name": "测试产品",
            "category": "测试",
            "price": 100.00,
            "cost": 50.00,
            "stock": 10,
            "region": "测试地区",
            "region_code": "00"
        }

        product = Product.from_dict(data)

        assert product.sku == "TEST-001"
        assert product.name == "测试产品"


# ==================== 用户模型测试 ====================

class TestUserModel:
    """用户模型功能测试"""

    @pytest.mark.unit
    def test_user_enum_types(self):
        """测试用户类型枚举"""
        assert UserType.PERSONAL.value == "personal"
        assert UserType.ENTERPRISE.value == "enterprise"

    @pytest.mark.unit
    def test_user_enum_status(self):
        """测试用户状态枚举"""
        assert UserStatus.ACTIVE.value == "active"
        assert UserStatus.INACTIVE.value == "inactive"
        assert UserStatus.BANNED.value == "banned"
        assert UserStatus.PENDING.value == "pending"

    @pytest.mark.unit
    def test_user_enum_role(self):
        """测试用户角色枚举"""
        assert UserRole.ADMIN.value == "admin"
        assert UserRole.ENTERPRISE_ADMIN.value == "enterprise_admin"
        assert UserRole.USER.value == "user"

    @pytest.mark.unit
    def test_user_enum_gender(self):
        """测试性别枚举"""
        assert Gender.MALE.value == 1
        assert Gender.FEMALE.value == 2
        assert Gender.UNKNOWN.value == 0

    @pytest.mark.unit
    def test_user_creation(self, test_db_session):
        """测试用户创建"""
        user = User(
            user_uuid=generate_uuid(),
            username="testuser",
            email="test@example.com",
            phone="13800138000",
            password_hash="hashed_password",
            user_type="personal",
            status="active",
            role="user"
        )

        test_db_session.add(user)
        test_db_session.commit()

        # 验证用户数据
        assert user.username == "testuser"
        assert user.email == "test@example.com"
        assert user.status == "active"

    @pytest.mark.unit
    def test_user_required_fields(self, test_db_session):
        """测试用户必需字段"""
        # 缺少必需字段应该抛出异常
        user = User()
        test_db_session.add(user)

        with pytest.raises(Exception):  # SQLAlchemy IntegrityError
            test_db_session.commit()

    @pytest.mark.unit
    def test_user_unique_constraints(self, test_db_session):
        """测试用户唯一性约束"""
        user1 = User(
            user_uuid=generate_uuid(),
            username="testuser",
            email="test@example.com",
            password_hash="hashed_password",
            user_type="personal",
            status="active",
            role="user"
        )

        test_db_session.add(user1)
        test_db_session.commit()

        # 创建相同用户名的用户应该失败
        user2 = User(
            user_uuid=generate_uuid(),
            username="testuser",
            email="test2@example.com",
            password_hash="hashed_password",
            user_type="personal",
            status="active",
            role="user"
        )

        test_db_session.add(user2)

        with pytest.raises(Exception):  # SQLAlchemy IntegrityError
            test_db_session.commit()


# ==================== 产品模型测试 ====================

class TestProductModel:
    """产品模型功能测试"""

    @pytest.mark.unit
    def test_product_enum_status(self):
        """测试产品状态枚举"""
        assert ProductStatus.DRAFT.value == "draft"
        assert ProductStatus.PENDING.value == "pending"
        assert ProductStatus.PUBLISHED.value == "published"
        assert ProductStatus.OFFLINE.value == "offline"

    @pytest.mark.unit
    def test_product_creation(self, test_db_session):
        """测试产品创建"""
        product = Product(
            sku="PROD-001",
            name="内蒙古羊肉",
            category="肉类",
            price=99.99,
            cost=50.00,
            stock=100,
            region="内蒙古",
            region_code="15"
        )

        test_db_session.add(product)
        test_db_session.commit()

        assert product.name == "内蒙古羊肉"
        assert product.price == 99.99
        assert product.stock == 100

    @pytest.mark.unit
    def test_product_required_fields(self, test_db_session):
        """测试产品必需字段"""
        product = Product(
            # 缺少name等必需字段
            sku="PROD-001"
        )

        test_db_session.add(product)

        with pytest.raises(Exception):  # SQLAlchemy IntegrityError
            test_db_session.commit()

    @pytest.mark.unit
    def test_product_sku_uniqueness(self, test_db_session):
        """测试产品SKU唯一性"""
        product1 = Product(
            sku="PROD-001",
            name="产品1",
            category="肉类",
            price=100.00,
            cost=50.00,
            stock=100,
            region="内蒙古",
            region_code="15"
        )

        test_db_session.add(product1)
        test_db_session.commit()

        # 创建相同SKU的产品
        product2 = Product(
            sku="PROD-001",
            name="产品2",
            category="肉类",
            price=100.00,
            cost=50.00,
            stock=100,
            region="内蒙古",
            region_code="15"
        )

        test_db_session.add(product2)

        with pytest.raises(Exception):  # SQLAlchemy IntegrityError
            test_db_session.commit()

    @pytest.mark.unit
    def test_product_with_all_fields(self, test_db_session):
        """测试产品包含所有字段"""
        product = Product(
            sku="PROD-001",
            name="内蒙古羊肉",
            short_name="羊肉",
            category="肉类",
            price=99.99,
            cost=50.00,
            stock=100,
            region="内蒙古",
            region_code="15",
            cultural_tags=["有机", "草原"],
            cultural_description="来自草原的优质羊肉",
            origin_story="传统畜牧产品",
            efficacy="营养丰富",
            usage="烤羊肉",
            status="published",
            is_featured=True
        )

        test_db_session.add(product)
        test_db_session.commit()

        retrieved = test_db_session.query(Product).first()
        assert retrieved.name == "内蒙古羊肉"
        assert retrieved.is_featured is True

    @pytest.mark.unit
    def test_product_default_values(self, test_db_session):
        """测试产品默认值"""
        product = Product(
            sku="PROD-001",
            name="测试产品",
            category="测试",
            price=100.00,
            cost=50.00,
            stock=10,
            region="测试",
            region_code="00"
        )

        test_db_session.add(product)
        test_db_session.commit()

        # 检查默认值
        assert product.product_uuid is not None
        assert product.status == "draft" or product.status is None
        assert product.created_at is not None
        assert product.updated_at is not None

    @pytest.mark.unit
    def test_product_to_dict(self, test_db_session):
        """测试产品to_dict()方法"""
        product = Product(
            sku="PROD-001",
            name="内蒙古羊肉",
            category="肉类",
            price=99.99,
            cost=50.00,
            stock=100,
            region="内蒙古",
            region_code="15",
            is_featured=True
        )

        test_db_session.add(product)
        test_db_session.commit()

        result = product.to_dict()

        assert result["name"] == "内蒙古羊肉"
        assert result["price"] == 99.99
        assert result["is_featured"] is True


# ==================== 模型字段验证 ====================

class TestModelFieldValidation:
    """模型字段验证测试"""

    @pytest.mark.unit
    def test_product_price_decimal(self, test_db_session):
        """测试产品价格小数"""
        product = Product(
            sku="PROD-001",
            name="测试",
            category="测试",
            price=99.99,
            cost=50.00,
            stock=100,
            region="测试",
            region_code="00"
        )

        test_db_session.add(product)
        test_db_session.commit()

        assert float(product.price) == 99.99

    @pytest.mark.unit
    def test_product_stock_integer(self, test_db_session):
        """测试产品库存为整数"""
        product = Product(
            sku="PROD-001",
            name="测试",
            category="测试",
            price=100.00,
            cost=50.00,
            stock=100,
            region="测试",
            region_code="00"
        )

        test_db_session.add(product)
        test_db_session.commit()

        assert isinstance(product.stock, int)
        assert product.stock == 100

    @pytest.mark.unit
    def test_user_phone_format(self, test_db_session):
        """测试用户电话号码格式"""
        user = User(
            user_uuid=generate_uuid(),
            username="testuser",
            phone="13800138000",
            password_hash="hashed",
            user_type="personal",
            status="active",
            role="user"
        )

        test_db_session.add(user)
        test_db_session.commit()

        assert user.phone == "13800138000"


# ==================== 模型关系测试 ====================

class TestModelRelationships:
    """模型关系映射测试"""

    @pytest.mark.unit
    def test_product_uuid_uniqueness(self, test_db_session):
        """测试产品UUID唯一性"""
        product1 = Product(
            sku="PROD-001",
            name="产品1",
            category="测试",
            price=100.00,
            cost=50.00,
            stock=10,
            region="测试",
            region_code="00"
        )

        test_db_session.add(product1)
        test_db_session.commit()

        # 重新查询并验证UUID
        retrieved = test_db_session.query(Product).filter_by(sku="PROD-001").first()
        assert retrieved.product_uuid is not None
        assert len(retrieved.product_uuid) == 36


# ==================== 模型方法测试 ====================

class TestModelMethods:
    """模型方法功能测试"""

    @pytest.mark.unit
    def test_model_repr(self, test_db_session):
        """测试模型__repr__方法"""
        product = Product(
            sku="PROD-001",
            name="测试",
            category="测试",
            price=100.00,
            cost=50.00,
            stock=10,
            region="测试",
            region_code="00"
        )

        test_db_session.add(product)
        test_db_session.commit()

        repr_str = repr(product)
        assert "Product" in repr_str or "id" in repr_str.lower()


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
