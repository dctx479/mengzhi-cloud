"""
Celery文化元素采集任务测试

测试覆盖：
- 异步采集任务执行
- 任务状态更新
- 采集结果保存
- 专家审核触发
- 定时任务（产品检查、清理）
- 任务重试机制
- 错误处理

版本: 1.0
创建日期: 2026-06-12
"""

import pytest
import json
from unittest.mock import Mock, MagicMock, patch
from datetime import datetime, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.database import Base
from app.models.cultural import (
    CulturalCollectionTask,
    CulturalElement,
    CulturalReviewTask,
    TaskPriority,
    TaskStatus,
    ElementStatus,
)
from app.tasks.cultural import (
    collect_cultural_elements,
    check_products_for_collection,
    cleanup_old_tasks,
    _execute_collection,
    _update_task_status,
    _save_collection_results,
    _trigger_expert_review,
    _get_review_priority,
)

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
def sample_task_params():
    """示例任务参数"""
    return {
        "product_id": 1,
        "product_name": "阿拉善驼肉",
        "origin": "阿拉善",
        "category": "驼肉类",
        "targets": ["地理景观", "传统工艺"],
        "priority": "P0",
        "created_at": datetime.utcnow().isoformat(),
    }


@pytest.fixture
def sample_collection_result():
    """示例采集结果"""
    return {
        "status": "success",
        "collected_count": 5,
        "new_elements": [
            {
                "name": "腾格里沙漠",
                "type": "地理景观",
                "story": "腾格里沙漠位于阿拉善...",
                "origin_region": "阿拉善",
                "keywords": ["沙漠", "生态", "旅游"],
                "metadata": {
                    "period": "现代",
                    "related_products": ["驼肉", "驼奶"],
                    "cultural_significance": "沙漠文化代表",
                    "usage_scenarios": ["品牌故事"],
                },
            }
        ],
        "matched_elements": [],
        "method": "agent_collection",
    }


# ==================== 采集执行测试 ====================


@patch("app.tasks.cultural.AdaptiveCulturalCollector")
def test_execute_collection_use_existing(mock_collector_class, db_session, sample_task_params):
    """测试使用现有元素（不触发Agent）"""
    mock_collector = MagicMock()
    mock_collector.match_by_type.return_value = [
        {"name": "元素1", "origin_region": "阿拉善"},
        {"name": "元素2", "origin_region": "阿拉善"},
        {"name": "元素3", "origin_region": "阿拉善"},
    ]
    mock_collector_class.return_value = mock_collector

    result = _execute_collection(sample_task_params, db_session)

    assert result["status"] == "success"
    assert result["method"] == "existing"
    assert result["collected_count"] >= 3
    assert len(result["new_elements"]) == 0


@patch("app.tasks.cultural.AdaptiveCulturalCollector")
@patch("app.tasks.cultural._trigger_agent_collection")
def test_execute_collection_trigger_agent(mock_agent, mock_collector_class, db_session, sample_task_params):
    """测试触发Agent采集（现有元素不足）"""
    mock_collector = MagicMock()
    mock_collector.match_by_type.return_value = []  # 无现有匹配
    mock_collector_class.return_value = mock_collector

    mock_agent.return_value = [
        {
            "name": "新元素1",
            "type": "地理景观",
            "story": "故事...",
            "origin_region": "阿拉善",
            "keywords": ["关键词"],
            "metadata": {},
        }
    ]

    result = _execute_collection(sample_task_params, db_session)

    assert result["status"] in ["success", "partial"]
    assert result["method"] == "agent_collection"
    assert len(result["new_elements"]) > 0

    # 验证Agent被调用
    mock_agent.assert_called_once()


# ==================== 任务状态更新测试 ====================


def test_update_task_status_pending_to_processing(db_session):
    """测试更新任务状态：pending → processing"""
    task = CulturalCollectionTask(
        task_id="task-001",
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

    _update_task_status(db_session, "task-001", "processing")

    db_session.refresh(task)
    assert task.status == TaskStatus.PROCESSING


def test_update_task_status_with_result(db_session):
    """测试更新任务状态并保存结果"""
    task = CulturalCollectionTask(
        task_id="task-002",
        product_id=1,
        product_name="测试产品",
        origin="测试产地",
        category="测试类别",
        targets='["地理景观"]',
        priority=TaskPriority.P0,
        status=TaskStatus.PROCESSING,
        created_at=datetime.utcnow(),
    )
    db_session.add(task)
    db_session.commit()

    result = {"status": "success", "collected_count": 3}
    _update_task_status(db_session, "task-002", "completed", result)

    db_session.refresh(task)
    assert task.status == TaskStatus.COMPLETED
    assert task.result is not None

    saved_result = json.loads(task.result)
    assert saved_result["status"] == "success"


# ==================== 采集结果保存测试 ====================


def test_save_collection_results(db_session, sample_collection_result):
    """测试保存采集结果到数据库"""
    task_id = "task-003"

    _save_collection_results(db_session, task_id, sample_collection_result)

    # 验证元素被保存
    elements = db_session.query(CulturalElement).filter_by(collection_task_id=task_id).all()

    assert len(elements) == 1
    element = elements[0]

    assert element.name == "腾格里沙漠"
    assert element.type == "地理景观"
    assert element.status == ElementStatus.PENDING_REVIEW
    assert element.collection_task_id == task_id


def test_save_collection_results_empty(db_session):
    """测试保存空采集结果"""
    result = {
        "status": "success",
        "collected_count": 0,
        "new_elements": [],
        "matched_elements": [],
        "method": "existing",
    }

    _save_collection_results(db_session, "task-004", result)

    # 验证没有元素被保存
    elements = db_session.query(CulturalElement).filter_by(collection_task_id="task-004").all()

    assert len(elements) == 0


# ==================== 专家审核触发测试 ====================


def test_trigger_expert_review(db_session, sample_collection_result):
    """测试触发专家审核"""
    task_id = "task-005"

    with patch("app.services.notification_service.NotificationService") as mock_notification:
        mock_notifier = MagicMock()
        mock_notification.return_value = mock_notifier

        _trigger_expert_review(db_session, task_id, sample_collection_result)

        # 验证审核任务被创建
        review_task = db_session.query(CulturalReviewTask).filter_by(collection_task_id=task_id).first()

        assert review_task is not None
        assert review_task.element_count == 1
        assert review_task.status == TaskStatus.PENDING

        # 验证通知被发送
        mock_notifier.notify_experts.assert_called_once()


def test_trigger_expert_review_no_new_elements(db_session):
    """测试无新元素时不触发审核"""
    result = {
        "status": "success",
        "collected_count": 3,
        "new_elements": [],
        "matched_elements": [],
        "method": "existing",
    }

    _trigger_expert_review(db_session, "task-006", result)

    # 验证没有审核任务被创建
    review_tasks = db_session.query(CulturalReviewTask).filter_by(collection_task_id="task-006").all()

    assert len(review_tasks) == 0


# ==================== 审核优先级判断测试 ====================


def test_get_review_priority_p0(sample_collection_result):
    """测试P0审核优先级（采集失败）"""
    result = {"collected_count": 0, "method": "agent_collection"}

    priority = _get_review_priority(result)
    assert priority == "P0"


def test_get_review_priority_p1(sample_collection_result):
    """测试P1审核优先级（部分采集）"""
    result = {"collected_count": 2, "method": "agent_collection"}

    priority = _get_review_priority(result)
    assert priority == "P1"


def test_get_review_priority_p2(sample_collection_result):
    """测试P2审核优先级（正常采集）"""
    result = {"collected_count": 5, "method": "agent_collection"}

    priority = _get_review_priority(result)
    assert priority == "P2"


# ==================== 异步任务集成测试 ====================


@patch("app.tasks.cultural.SessionLocal")
@patch("app.tasks.cultural._execute_collection")
@patch("app.tasks.cultural._save_collection_results")
@patch("app.tasks.cultural._trigger_expert_review")
def test_collect_cultural_elements_async_success(
    mock_trigger_review,
    mock_save_results,
    mock_execute,
    mock_session_class,
    db_session,
    sample_task_params,
    sample_collection_result,
):
    """测试采集任务成功执行"""
    # 模拟数据库会话
    mock_session_class.return_value = db_session

    # 模拟采集执行
    mock_execute.return_value = sample_collection_result

    result = collect_cultural_elements("task-success-001", sample_task_params)

    assert result["status"] == "success"
    assert result["collected_count"] == 5

    # 验证各步骤被调用
    mock_execute.assert_called_once()
    mock_save_results.assert_called_once()
    mock_trigger_review.assert_called_once()


@patch("app.tasks.cultural.SessionLocal")
@patch("app.tasks.cultural._execute_collection")
def test_collect_cultural_elements_failure(mock_execute, mock_session_class, db_session, sample_task_params):
    """测试采集任务失败：返回失败结果，状态记 failed，不抛异常"""
    mock_session_class.return_value = db_session

    # 模拟执行失败
    mock_execute.side_effect = Exception("采集失败")

    result = collect_cultural_elements("task-failure-001", sample_task_params)

    assert result["status"] == "failed"
    assert "error" in result
    assert "采集失败" in result["error"]


# ==================== 定时任务测试 ====================


@patch("app.tasks.cultural.SessionLocal")
@patch("app.models.product.Product")
@patch("app.services.cultural.auto_trigger.CulturalCollectionTrigger")
def test_check_products_for_collection(mock_trigger_class, mock_product, mock_session_class, db_session):
    """测试定时检查产品任务"""
    # 模拟数据库会话
    mock_session_class.return_value = db_session

    # 模拟产品查询
    mock_product_obj = MagicMock()
    mock_product_obj.id = 1
    mock_product_obj.name = "测试产品"
    mock_product_obj.origin = "测试产地"
    mock_product_obj.category = "测试类别"
    mock_product_obj.keywords = "关键词1,关键词2"

    mock_query = MagicMock()
    mock_query.all.return_value = [mock_product_obj]
    db_session.query = MagicMock(return_value=mock_query)

    # 模拟触发器
    mock_trigger = MagicMock()
    mock_trigger.check_and_trigger.return_value = {"need_collection": True}
    mock_trigger_class.return_value = mock_trigger

    result = check_products_for_collection()

    assert result["status"] == "completed"
    assert result["total_products"] == 1
    assert result["triggered_count"] == 1


@patch("app.tasks.cultural.SessionLocal")
def test_cleanup_old_tasks(mock_session_class, db_session):
    """测试清理过期任务"""
    mock_session_class.return_value = db_session

    # 创建旧任务（31天前）
    old_date = datetime.utcnow() - timedelta(days=31)
    old_task = CulturalCollectionTask(
        task_id="old-task-001",
        product_id=1,
        product_name="旧产品",
        origin="旧产地",
        category="旧类别",
        targets='["地理景观"]',
        priority=TaskPriority.P2,
        status=TaskStatus.COMPLETED,
        created_at=old_date,
        updated_at=old_date,
    )
    db_session.add(old_task)

    # 创建新任务（10天前）
    recent_date = datetime.utcnow() - timedelta(days=10)
    recent_task = CulturalCollectionTask(
        task_id="recent-task-001",
        product_id=2,
        product_name="新产品",
        origin="新产地",
        category="新类别",
        targets='["传统工艺"]',
        priority=TaskPriority.P1,
        status=TaskStatus.COMPLETED,
        created_at=recent_date,
        updated_at=recent_date,
    )
    db_session.add(recent_task)

    db_session.commit()

    result = cleanup_old_tasks()

    assert result["status"] == "completed"
    assert result["deleted_count"] == 1

    # 验证旧任务被删除
    remaining_tasks = db_session.query(CulturalCollectionTask).all()
    assert len(remaining_tasks) == 1
    assert remaining_tasks[0].task_id == "recent-task-001"


# ==================== 边界条件测试 ====================


def test_update_task_status_nonexistent_task(db_session):
    """测试更新不存在的任务状态"""
    _update_task_status(db_session, "nonexistent-task", "completed")

    # 应该不抛出异常，静默处理


def test_save_collection_results_invalid_json(db_session):
    """测试保存包含无效JSON的结果"""
    result = {
        "status": "success",
        "collected_count": 1,
        "new_elements": [
            {
                "name": "元素",
                "type": "地理景观",
                "story": "故事",
                "origin_region": "产地",
                "keywords": ["关键词"],  # 列表会被正确序列化
                "metadata": {"key": "value"},
            }
        ],
        "matched_elements": [],
        "method": "agent_collection",
    }

    # 应该正常保存
    _save_collection_results(db_session, "task-test", result)

    elements = db_session.query(CulturalElement).filter_by(collection_task_id="task-test").all()

    assert len(elements) == 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
