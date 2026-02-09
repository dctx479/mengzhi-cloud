"""
文化标签服务单元测试

测试覆盖：
- 标签CRUD操作
- 标签推荐算法
- 产品标签关联管理
- 标签统计分析

版本: 1.0
更新日期: 2026-01-17
"""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models.base import Base
from app.models.cultural_tag import CulturalTag
from app.models.product import Product, ProductStatus
from app.services.cultural_tag_service import CulturalTagService
from app.schemas.cultural_tags import CulturalTagCreate, CulturalTagUpdate
from app.core.errors import BusinessException


# 测试数据库配置
TEST_DATABASE_URL = "sqlite:///:memory:"


@pytest.fixture(scope="function")
def db_session():
    """创建测试数据库会话"""
    engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)

    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = TestingSessionLocal()

    yield session

    session.close()
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def service(db_session):
    """创建服务实例"""
    return CulturalTagService(db_session)


@pytest.fixture
def sample_tag_data():
    """示例标签数据"""
    return CulturalTagCreate(
        name="锡林郭勒羊肉",
        category="geo",
        description="锡林郭勒盟特产，国家地理标志产品",
        keywords="羊肉,地理标志,锡林郭勒"
    )


@pytest.fixture
def sample_product(db_session):
    """创建示例产品"""
    product = Product(
        product_uuid="test-uuid-001",
        name="测试产品",
        category="畜产品",
        origin_province="内蒙古",
        origin_city="锡林郭勒盟",
        status=ProductStatus.PUBLISHED,
        created_by=1
    )
    db_session.add(product)
    db_session.commit()
    db_session.refresh(product)
    return product


# ==================== 标签CRUD测试 ====================

def test_create_tag(service, sample_tag_data):
    """测试创建标签"""
    tag = service.create_tag(sample_tag_data)

    assert tag.id is not None
    assert tag.name == sample_tag_data.name
    assert tag.category == sample_tag_data.category
    assert tag.usage_count == 0
    assert tag.is_active is True


def test_create_duplicate_tag(service, sample_tag_data):
    """测试创建重复标签"""
    service.create_tag(sample_tag_data)

    with pytest.raises(BusinessException) as exc_info:
        service.create_tag(sample_tag_data)

    assert "已存在" in str(exc_info.value.message)


def test_get_tag_by_id(service, sample_tag_data):
    """测试根据ID获取标签"""
    created_tag = service.create_tag(sample_tag_data)
    retrieved_tag = service.get_tag_by_id(created_tag.id)

    assert retrieved_tag.id == created_tag.id
    assert retrieved_tag.name == created_tag.name


def test_get_nonexistent_tag(service):
    """测试获取不存在的标签"""
    with pytest.raises(BusinessException) as exc_info:
        service.get_tag_by_id(999)

    assert "不存在" in str(exc_info.value.message)


def test_update_tag(service, sample_tag_data):
    """测试更新标签"""
    tag = service.create_tag(sample_tag_data)

    update_data = CulturalTagUpdate(
        description="更新后的描述",
        keywords="新关键词"
    )

    updated_tag = service.update_tag(tag.id, update_data)

    assert updated_tag.description == "更新后的描述"
    assert updated_tag.keywords == "新关键词"
    assert updated_tag.name == sample_tag_data.name  # 未更新的字段保持不变


def test_delete_unused_tag(service, sample_tag_data):
    """测试删除未使用的标签（硬删除）"""
    tag = service.create_tag(sample_tag_data)
    tag_id = tag.id

    service.delete_tag(tag_id)

    with pytest.raises(BusinessException):
        service.get_tag_by_id(tag_id)


def test_delete_used_tag(service, sample_tag_data, sample_product):
    """测试删除已使用的标签（软删除）"""
    tag = service.create_tag(sample_tag_data)

    # 将标签分配给产品
    service.assign_tags_to_product(sample_product.id, [tag.id])

    # 删除标签（应该是软删除）
    service.delete_tag(tag.id)

    # 标签仍然存在，但is_active为False
    deleted_tag = service.get_tag_by_id(tag.id)
    assert deleted_tag.is_active is False


# ==================== 产品标签关联测试 ====================

def test_assign_tags_to_product(service, sample_tag_data, sample_product):
    """测试为产品分配标签"""
    tag1 = service.create_tag(sample_tag_data)

    tag2_data = CulturalTagCreate(
        name="蒙古族传统",
        category="ethnicity",
        description="蒙古族传统文化",
        keywords="蒙古族,传统"
    )
    tag2 = service.create_tag(tag2_data)

    product = service.assign_tags_to_product(sample_product.id, [tag1.id, tag2.id])

    assert len(product.tags) == 2
    tag_ids = {tag.id for tag in product.tags}
    assert tag1.id in tag_ids
    assert tag2.id in tag_ids


def test_assign_tags_updates_usage_count(service, sample_tag_data, sample_product):
    """测试分配标签更新使用次数"""
    tag = service.create_tag(sample_tag_data)
    initial_usage = tag.usage_count

    service.assign_tags_to_product(sample_product.id, [tag.id])

    updated_tag = service.get_tag_by_id(tag.id)
    assert updated_tag.usage_count == initial_usage + 1


def test_remove_tag_from_product(service, sample_tag_data, sample_product):
    """测试从产品移除标签"""
    tag = service.create_tag(sample_tag_data)
    service.assign_tags_to_product(sample_product.id, [tag.id])

    product = service.remove_tag_from_product(sample_product.id, tag.id)

    assert len(product.tags) == 0


def test_remove_tag_decrements_usage_count(service, sample_tag_data, sample_product):
    """测试移除标签减少使用次数"""
    tag = service.create_tag(sample_tag_data)
    service.assign_tags_to_product(sample_product.id, [tag.id])

    initial_usage = service.get_tag_by_id(tag.id).usage_count

    service.remove_tag_from_product(sample_product.id, tag.id)

    updated_tag = service.get_tag_by_id(tag.id)
    assert updated_tag.usage_count == initial_usage - 1


# ==================== 标签推荐测试 ====================

def test_get_popular_tags(service, db_session):
    """测试获取热门标签"""
    # 创建多个标签，设置不同的usage_count
    tags_data = [
        ("标签A", 10),
        ("标签B", 5),
        ("标签C", 15),
        ("标签D", 3),
    ]

    for name, usage_count in tags_data:
        tag = CulturalTag(
            name=name,
            category="geo",
            usage_count=usage_count,
            is_active=True
        )
        db_session.add(tag)

    db_session.commit()

    popular_tags = service.get_popular_tags(limit=3)

    assert len(popular_tags) == 3
    # 应该按usage_count降序排列
    assert popular_tags[0].name == "标签C"
    assert popular_tags[1].name == "标签A"
    assert popular_tags[2].name == "标签B"


def test_recommend_tags_by_keywords(service, db_session):
    """测试基于关键词推荐标签"""
    # 创建包含不同关键词的标签
    tags_data = [
        ("锡林郭勒羊肉", "geo", "羊肉,地理标志,锡林郭勒"),
        ("科尔沁牛肉", "geo", "牛肉,地理标志,科尔沁"),
        ("蒙古族传统", "ethnicity", "蒙古族,传统,文化"),
    ]

    for name, category, keywords in tags_data:
        tag = CulturalTag(
            name=name,
            category=category,
            keywords=keywords,
            is_active=True
        )
        db_session.add(tag)

    db_session.commit()

    # 搜索包含"羊肉"的标签
    recommended = service.recommend_tags_by_keywords("羊肉", limit=10)

    assert len(recommended) >= 1
    assert any(tag.name == "锡林郭勒羊肉" for tag in recommended)


# ==================== 统计分析测试 ====================

def test_get_tag_statistics(service, db_session):
    """测试获取标签统计"""
    # 创建不同分类的标签
    tags_data = [
        ("标签1", "geo", True),
        ("标签2", "geo", True),
        ("标签3", "ethnicity", True),
        ("标签4", "history", False),  # 未启用
    ]

    for name, category, is_active in tags_data:
        tag = CulturalTag(
            name=name,
            category=category,
            is_active=is_active
        )
        db_session.add(tag)

    db_session.commit()

    stats = service.get_tag_statistics()

    assert stats['total_tags'] == 4
    assert stats['active_tags'] == 3
    assert stats['category_distribution']['geo']['count'] == 2
    assert stats['category_distribution']['ethnicity']['count'] == 1


def test_initialize_default_tags(db_session):
    """测试初始化默认标签"""
    created_count = CulturalTagService.initialize_default_tags(db_session)

    assert created_count > 0

    # 验证标签已创建
    tags = db_session.query(CulturalTag).all()
    assert len(tags) == created_count

    # 验证不会重复创建
    second_count = CulturalTagService.initialize_default_tags(db_session)
    assert second_count == 0
