"""
文化元素自动触发器测试

测试覆盖：
- 触发条件判断（P0/P1/P2/OK）
- Celery任务创建
- 采集目标策略
- 任务优先级映射
- 任务状态查询

版本: 1.0
创建日期: 2026-06-12
"""

import pytest
from unittest.mock import Mock, MagicMock, patch
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.database import Base
from app.services.cultural.auto_trigger import CulturalCollectionTrigger
from app.models.cultural import CulturalCollectionTask, TaskPriority, TaskStatus

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
def mock_collector():
    """模拟AdaptiveCulturalCollector"""
    collector = MagicMock()

    # 默认返回低匹配度结果
    collector.match_by_product.return_value = [
        {"element": {"name": "元素1", "type": "地理景观"}, "score": 25, "reason": "低匹配"}
    ]

    return collector


@pytest.fixture
def trigger(db_session, mock_collector):
    """创建触发器实例"""
    with patch("app.services.cultural.auto_trigger.AdaptiveCulturalCollector", return_value=mock_collector):
        return CulturalCollectionTrigger(db_session)


# ==================== 优先级判断测试 ====================


def test_determine_priority_p0(trigger):
    """测试P0优先级判断（无匹配）"""
    priority = trigger._determine_priority(0)
    assert priority == "P0"


def test_determine_priority_p1(trigger):
    """测试P1优先级判断（低匹配）"""
    priority = trigger._determine_priority(25)
    assert priority == "P1"


def test_determine_priority_p2(trigger):
    """测试P2优先级判断（中等匹配）"""
    priority = trigger._determine_priority(45)
    assert priority == "P2"


def test_determine_priority_ok(trigger):
    """测试OK状态判断（良好匹配）"""
    priority = trigger._determine_priority(75)
    assert priority == "OK"


def test_priority_thresholds_boundary(trigger):
    """测试优先级边界值"""
    assert trigger._determine_priority(0) == "P0"
    assert trigger._determine_priority(29) == "P1"
    assert trigger._determine_priority(30) == "P1"
    assert trigger._determine_priority(49) == "P2"
    assert trigger._determine_priority(50) == "P2"
    assert trigger._determine_priority(69) == "P2"
    assert trigger._determine_priority(70) == "OK"


# ==================== 采集目标策略测试 ====================


def test_collection_targets_p0(trigger):
    """测试P0优先级的采集目标（无匹配，全采集）"""
    product_info = {"name": "新产品", "origin": "新产地", "category": "新类别"}

    matches = []
    targets = trigger._determine_collection_targets(product_info, matches, "P0")

    # P0应该采集所有类别
    assert "地理景观" in targets
    assert "传统工艺" in targets
    assert "畜牧知识" in targets
    assert len(targets) == 3


def test_collection_targets_p1_no_geography(trigger):
    """测试P1优先级的采集目标（缺少地理景观）"""
    product_info = {"name": "产品", "origin": "产地", "category": "类别"}

    matches = [{"element": {"type": "传统工艺"}, "score": 25}]

    targets = trigger._determine_collection_targets(product_info, matches, "P1")

    # 缺少地理景观，应该优先采集
    assert "地理景观" in targets


def test_collection_targets_p1_no_livestock(trigger):
    """测试P1优先级的采集目标（缺少畜牧知识）"""
    product_info = {"name": "产品", "origin": "产地", "category": "类别"}

    matches = [{"element": {"type": "地理景观"}, "score": 25}]

    targets = trigger._determine_collection_targets(product_info, matches, "P1")

    # 缺少畜牧知识，应该补充采集
    assert "畜牧知识" in targets


def test_collection_targets_p2(trigger):
    """测试P2优先级的采集目标（中等匹配，不触发）"""
    product_info = {"name": "产品", "origin": "产地", "category": "类别"}

    matches = [{"element": {"type": "地理景观"}, "score": 45}, {"element": {"type": "传统工艺"}, "score": 40}]

    targets = trigger._determine_collection_targets(product_info, matches, "P2")

    # P2不应该触发采集
    assert targets == []


# ==================== 触发检查测试 ====================


@patch("app.tasks.cultural.collect_cultural_elements")
def test_check_and_trigger_p0(mock_collect, trigger, mock_collector):
    """测试P0产品触发采集"""
    # 模拟无匹配
    mock_collector.match_by_product.return_value = []

    product_info = {"id": 1, "name": "新产品", "origin": "新产地", "category": "新类别", "keywords": []}

    result = trigger.check_and_trigger(product_info)

    # 验证触发结果
    assert result["need_collection"] is True
    assert result["priority"] == "P0"
    assert result["match_score"] == 0
    assert result["task_id"].startswith("cultural-")
    assert len(result["collection_targets"]) == 3

    # 验证采集函数被同步调用
    mock_collect.assert_called_once()


@patch("app.tasks.cultural.collect_cultural_elements")
def test_check_and_trigger_p1(mock_collect, trigger, mock_collector):
    """测试P1产品触发采集"""
    # 模拟低匹配
    mock_collector.match_by_product.return_value = [{"element": {"type": "传统工艺"}, "score": 25, "reason": "低匹配"}]

    product_info = {"id": 2, "name": "产品", "origin": "产地", "category": "类别", "keywords": []}

    result = trigger.check_and_trigger(product_info)

    # 验证触发结果
    assert result["need_collection"] is True
    assert result["priority"] == "P1"
    assert result["match_score"] == 25
    assert result["task_id"].startswith("cultural-")

    # P1应该采集地理景观
    assert "地理景观" in result["collection_targets"]


def test_check_and_trigger_ok_no_collection(trigger, mock_collector):
    """测试OK产品不触发采集"""
    # 模拟高匹配
    mock_collector.match_by_product.return_value = [{"element": {"type": "地理景观"}, "score": 80, "reason": "高匹配"}]

    product_info = {"id": 3, "name": "产品", "origin": "产地", "category": "类别", "keywords": []}

    result = trigger.check_and_trigger(product_info)

    # 验证不触发
    assert result["need_collection"] is False
    assert result["priority"] == "OK"
    assert result["match_score"] == 80
    assert result["task_id"] is None
    assert result["collection_targets"] == []


# ==================== 任务记录保存测试 ====================


@patch("app.tasks.cultural.collect_cultural_elements")
def test_save_collection_task(mock_collect, trigger, db_session, mock_collector):
    """测试保存采集任务记录"""
    mock_collector.match_by_product.return_value = []

    product_info = {"id": 10, "name": "测试产品", "origin": "测试产地", "category": "测试类别", "keywords": []}

    result = trigger.check_and_trigger(product_info)

    # 任务ID 由 uuid 生成，按 product_id 查询落库记录
    task = db_session.query(CulturalCollectionTask).filter_by(product_id=10).first()

    assert task is not None
    assert task.task_id == result["task_id"]
    assert task.product_name == "测试产品"
    assert task.origin == "测试产地"
    assert task.category == "测试类别"
    assert task.priority == TaskPriority.P0
    assert task.status == TaskStatus.PENDING


# ==================== 任务状态查询测试 ====================


def test_get_task_status_success(trigger, db_session):
    """测试查询任务状态（任务存在）"""
    # 创建测试任务
    task = CulturalCollectionTask(
        task_id="task-100",
        product_id=1,
        product_name="测试产品",
        origin="测试产地",
        category="测试类别",
        targets='["地理景观"]',
        priority=TaskPriority.P0,
        status=TaskStatus.PENDING,
        created_at=datetime.utcnow(),
    )
    db_session.add(task)
    db_session.commit()

    status = trigger.get_task_status("task-100")

    assert status["task_id"] == "task-100"
    assert status["product_name"] == "测试产品"
    assert status["origin"] == "测试产地"
    assert status["priority"] == "P0"
    assert status["status"] == "pending"
    assert status["result"] is None


def test_get_task_status_not_found(trigger):
    """测试查询不存在的任务"""
    status = trigger.get_task_status("nonexistent-task")

    assert "error" in status
    assert "不存在" in status["error"]


# ==================== 原因生成测试 ====================


def test_generate_reason_p0(trigger):
    """测试P0原因生成"""
    reason = trigger._generate_reason(0, 0, "P0")

    assert "无匹配" in reason
    assert "立即采集" in reason


def test_generate_reason_p1(trigger):
    """测试P1原因生成"""
    reason = trigger._generate_reason(25, 2, "P1")

    assert "25分" in reason
    assert "2个元素" in reason
    assert "需要采集" in reason


def test_generate_reason_ok(trigger):
    """测试OK原因生成"""
    reason = trigger._generate_reason(75, 5, "OK")

    assert "75分" in reason
    assert "5个元素" in reason
    assert "无需采集" in reason


# ==================== 边界条件测试 ====================


@patch("app.tasks.cultural.collect_cultural_elements")
def test_empty_product_info(mock_collect, trigger, mock_collector):
    """测试空产品信息（mock 采集，隔离真实 DB 调用）"""
    mock_collector.match_by_product.return_value = []

    result = trigger.check_and_trigger({})

    # 应该返回有效结果，不崩溃
    assert "need_collection" in result
    assert "priority" in result


@patch("app.tasks.cultural.collect_cultural_elements")
def test_missing_product_fields(mock_collect, trigger, mock_collector):
    """测试缺少字段的产品信息（mock 采集，隔离真实 DB 调用）"""
    mock_collector.match_by_product.return_value = []

    product_info = {
        "name": "产品"
        # 缺少 origin, category, keywords
    }

    result = trigger.check_and_trigger(product_info)

    # 应该正常处理
    assert isinstance(result, dict)


@patch("app.tasks.cultural.collect_cultural_elements")
def test_collection_execution_failure(mock_collect, trigger, mock_collector):
    """测试采集执行抛异常时向上传播"""
    mock_collector.match_by_product.return_value = []

    # 模拟采集函数抛出异常
    mock_collect.side_effect = Exception("采集执行失败")

    product_info = {"id": 1, "name": "产品", "origin": "产地", "category": "类别", "keywords": []}

    # 异常应向上传播（由 API 层捕获为 500）
    with pytest.raises(Exception):
        trigger.check_and_trigger(product_info)


# ==================== 集成测试 ====================


@patch("app.tasks.cultural.collect_cultural_elements")
def test_full_workflow_p0_to_p1(mock_collect, trigger, mock_collector, db_session):
    """测试完整工作流：P0产品触发 → 采集 → 匹配提升到P1"""
    # 第一次检查：P0（无匹配）
    mock_collector.match_by_product.return_value = []

    product_info = {"id": 1, "name": "新产品", "origin": "新产地", "category": "新类别", "keywords": []}

    result1 = trigger.check_and_trigger(product_info)

    assert result1["priority"] == "P0"
    assert result1["need_collection"] is True

    # 模拟采集后有了匹配
    mock_collector.match_by_product.return_value = [
        {"element": {"type": "地理景观"}, "score": 35, "reason": "中等匹配"}
    ]

    # 第二次检查：P1（低匹配）
    result2 = trigger.check_and_trigger(product_info)

    assert result2["priority"] == "P1"
    assert result2["match_score"] == 35


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
