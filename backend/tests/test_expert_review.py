"""
文化元素专家审核系统测试

测试覆盖：
- 待审核任务获取
- 任务分配
- 单个元素审核
- 批量审核
- 审核历史查询
- 审核统计
- 修正建议应用

版本: 1.0
创建日期: 2026-06-12
"""

import pytest
import json
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.database import Base
from app.models.cultural import (
    CulturalElement,
    CulturalReviewTask,
    CulturalReview,
    CulturalCollectionTask,
    TaskPriority,
    TaskStatus,
    ElementStatus,
    ReviewDecision,
)
from app.services.cultural.expert_review import CulturalExpertReviewSystem

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
def review_system(db_session):
    """创建审核系统实例"""
    return CulturalExpertReviewSystem(db_session)


@pytest.fixture
def sample_collection_task(db_session):
    """创建示例采集任务"""
    task = CulturalCollectionTask(
        task_id="task-001",
        product_id=1,
        product_name="测试产品",
        origin="测试产地",
        category="测试类别",
        targets='["地理景观"]',
        priority=TaskPriority.P0,
        status=TaskStatus.COMPLETED,
        created_at=datetime.utcnow(),
    )
    db_session.add(task)
    db_session.commit()
    db_session.refresh(task)
    return task


@pytest.fixture
def sample_elements(db_session, sample_collection_task):
    """创建示例文化元素"""
    elements = []

    for i in range(3):
        element = CulturalElement(
            name=f"文化元素{i+1}",
            type="地理景观",
            story=f"这是文化元素{i+1}的故事...",
            origin_region="测试产地",
            keywords=json.dumps(["关键词1", "关键词2"], ensure_ascii=False),
            element_metadata=json.dumps({"period": "现代"}, ensure_ascii=False),
            collection_task_id=sample_collection_task.task_id,
            source="agent",
            status=ElementStatus.PENDING_REVIEW,
            created_at=datetime.utcnow(),
        )
        db_session.add(element)
        elements.append(element)

    db_session.commit()

    for element in elements:
        db_session.refresh(element)

    return elements


@pytest.fixture
def sample_review_task(db_session, sample_collection_task, sample_elements):
    """创建示例审核任务"""
    review_task = CulturalReviewTask(
        collection_task_id=sample_collection_task.task_id,
        element_count=len(sample_elements),
        priority=TaskPriority.P0,
        status=TaskStatus.PENDING,
        created_at=datetime.utcnow(),
    )
    db_session.add(review_task)
    db_session.commit()
    db_session.refresh(review_task)
    return review_task


# ==================== 待审核任务获取测试 ====================


def test_get_pending_reviews(review_system, sample_review_task, sample_elements):
    """测试获取待审核任务列表"""
    tasks = review_system.get_pending_reviews(limit=10)

    assert len(tasks) == 1
    task = tasks[0]

    assert task["review_task_id"] == sample_review_task.id
    assert task["priority"] == "P0"
    assert task["element_count"] == 3
    assert len(task["elements"]) == 3


def test_get_pending_reviews_by_priority(review_system, sample_review_task):
    """测试按优先级过滤待审核任务"""
    tasks = review_system.get_pending_reviews(priority="P0", limit=10)

    assert len(tasks) == 1
    assert tasks[0]["priority"] == "P0"

    # 查询P1优先级应该返回空
    tasks_p1 = review_system.get_pending_reviews(priority="P1", limit=10)
    assert len(tasks_p1) == 0


def test_get_pending_reviews_empty(review_system):
    """测试获取待审核任务（无任务）"""
    tasks = review_system.get_pending_reviews(limit=10)

    assert len(tasks) == 0


# ==================== 任务分配测试 ====================


def test_assign_review_task(review_system, sample_review_task):
    """测试分配审核任务"""
    expert_id = 100

    result = review_system.assign_review_task(sample_review_task.id, expert_id)

    assert result["success"] is True
    assert result["review_task_id"] == sample_review_task.id
    assert result["expert_id"] == expert_id
    assert "assigned_at" in result


def test_assign_nonexistent_task(review_system):
    """测试分配不存在的任务"""
    result = review_system.assign_review_task(999, 100)

    assert "error" in result
    assert "不存在" in result["error"]


def test_assign_already_processed_task(review_system, db_session, sample_review_task):
    """测试分配已处理的任务"""
    # 修改任务状态为已完成
    sample_review_task.status = TaskStatus.COMPLETED
    db_session.commit()

    result = review_system.assign_review_task(sample_review_task.id, 100)

    assert "error" in result
    assert "已被处理" in result["error"]


# ==================== 单个元素审核测试 ====================


def test_review_element_approved(review_system, sample_elements):
    """测试审核通过元素"""
    element = sample_elements[0]
    expert_id = 100

    result = review_system.review_element(
        element_id=element.id, expert_id=expert_id, decision="approved", comments="文化准确性良好"
    )

    assert result["success"] is True
    assert result["element_id"] == element.id
    assert result["decision"] == "approved"
    assert result["new_status"] == "approved"


def test_review_element_rejected(review_system, sample_elements):
    """测试拒绝元素"""
    element = sample_elements[0]
    expert_id = 100

    result = review_system.review_element(
        element_id=element.id, expert_id=expert_id, decision="rejected", comments="文化准确性不足"
    )

    assert result["success"] is True
    assert result["new_status"] == "rejected"


def test_review_element_needs_correction(review_system, sample_elements):
    """测试需要修正的元素"""
    element = sample_elements[0]
    expert_id = 100

    corrections = {"story": "修正后的故事文本", "keywords": ["修正关键词1", "修正关键词2"]}

    result = review_system.review_element(
        element_id=element.id,
        expert_id=expert_id,
        decision="needs_correction",
        comments="需要优化故事叙述",
        corrections=corrections,
    )

    assert result["success"] is True
    # 提供 corrections 时，_apply_corrections 会在应用修正后将元素重置为 pending_review 以便复审
    assert result["new_status"] == "pending_review"


def test_review_nonexistent_element(review_system):
    """测试审核不存在的元素"""
    result = review_system.review_element(element_id=999, expert_id=100, decision="approved")

    assert "error" in result
    assert "不存在" in result["error"]


def test_review_already_reviewed_element(review_system, db_session, sample_elements):
    """测试审核已审核的元素"""
    element = sample_elements[0]
    element.status = ElementStatus.APPROVED
    db_session.commit()

    result = review_system.review_element(element_id=element.id, expert_id=100, decision="approved")

    assert "error" in result
    assert "无法审核" in result["error"]


# ==================== 修正建议应用测试 ====================


def test_apply_corrections_story(review_system, db_session, sample_elements):
    """测试应用故事修正"""
    element = sample_elements[0]

    corrections = {"story": "这是修正后的完整故事..."}

    review_system._apply_corrections(element, corrections)
    db_session.commit()
    db_session.refresh(element)

    assert element.story == "这是修正后的完整故事..."
    assert element.status == ElementStatus.PENDING_REVIEW  # 重置为待审核


def test_apply_corrections_keywords(review_system, db_session, sample_elements):
    """测试应用关键词修正"""
    element = sample_elements[0]

    corrections = {"keywords": ["新关键词1", "新关键词2", "新关键词3"]}

    review_system._apply_corrections(element, corrections)
    db_session.commit()
    db_session.refresh(element)

    keywords = json.loads(element.keywords)
    assert keywords == ["新关键词1", "新关键词2", "新关键词3"]


def test_apply_corrections_metadata(review_system, db_session, sample_elements):
    """测试应用元数据修正"""
    element = sample_elements[0]

    corrections = {"cultural_significance": "修正后的文化意义说明"}

    review_system._apply_corrections(element, corrections)
    db_session.commit()
    db_session.refresh(element)

    metadata = json.loads(element.element_metadata)
    assert metadata["cultural_significance"] == "修正后的文化意义说明"


# ==================== 批量审核测试 ====================


def test_batch_review_approved(review_system, sample_elements):
    """测试批量审核通过"""
    element_ids = [e.id for e in sample_elements]

    result = review_system.batch_review(
        element_ids=element_ids, expert_id=100, decision="approved", comments="批量通过"
    )

    assert result["total"] == 3
    assert result["success"] == 3
    assert result["failed"] == 0


def test_batch_review_partial_success(review_system, db_session, sample_elements):
    """测试批量审核部分成功"""
    # 将第一个元素设为已审核
    sample_elements[0].status = ElementStatus.APPROVED
    db_session.commit()

    element_ids = [e.id for e in sample_elements]

    result = review_system.batch_review(element_ids=element_ids, expert_id=100, decision="approved")

    assert result["total"] == 3
    assert result["success"] == 2
    assert result["failed"] == 1


# ==================== 审核历史查询测试 ====================


def test_get_review_history_by_element(review_system, db_session, sample_elements):
    """测试查询指定元素的审核历史"""
    element = sample_elements[0]
    expert_id = 100

    # 先创建审核记录
    review_system.review_element(element_id=element.id, expert_id=expert_id, decision="approved", comments="测试审核")

    # 查询历史
    history = review_system.get_review_history(element_id=element.id)

    assert len(history) == 1
    assert history[0]["element_name"] == element.name
    assert history[0]["decision"] == "approved"


def test_get_review_history_by_expert(review_system, sample_elements):
    """测试查询指定专家的审核历史"""
    expert_id = 100

    # 创建多个审核记录
    for element in sample_elements[:2]:
        review_system.review_element(element_id=element.id, expert_id=expert_id, decision="approved")

    history = review_system.get_review_history(expert_id=expert_id)

    assert len(history) == 2


def test_get_review_history_empty(review_system):
    """测试查询空审核历史"""
    history = review_system.get_review_history()

    assert len(history) == 0


# ==================== 审核统计测试 ====================


def test_get_review_statistics(review_system, sample_elements):
    """测试获取审核统计"""
    expert_id = 100

    # 创建不同决定的审核记录
    review_system.review_element(element_id=sample_elements[0].id, expert_id=expert_id, decision="approved")

    review_system.review_element(element_id=sample_elements[1].id, expert_id=expert_id, decision="rejected")

    review_system.review_element(element_id=sample_elements[2].id, expert_id=expert_id, decision="needs_correction")

    stats = review_system.get_review_statistics(expert_id=expert_id)

    assert stats["total_reviewed"] == 3
    assert stats["approved"] == 1
    assert stats["rejected"] == 1
    assert stats["needs_correction"] == 1
    assert "地理景观" in stats["by_type"]


def test_get_review_statistics_empty(review_system):
    """测试获取空统计"""
    stats = review_system.get_review_statistics()

    assert stats["total_reviewed"] == 0
    assert stats["approved"] == 0
    assert stats["rejected"] == 0
    assert stats["needs_correction"] == 0


# ==================== 任务完成检查测试 ====================


def test_check_review_task_completion(review_system, db_session, sample_review_task, sample_elements):
    """测试审核任务完成检查"""
    expert_id = 100

    # 审核所有元素
    for element in sample_elements:
        review_system.review_element(element_id=element.id, expert_id=expert_id, decision="approved")

    # 刷新审核任务
    db_session.refresh(sample_review_task)

    # 验证审核任务状态变为完成
    assert sample_review_task.status == TaskStatus.COMPLETED
    assert sample_review_task.completed_at is not None


def test_check_review_task_partial_completion(review_system, db_session, sample_review_task, sample_elements):
    """测试审核任务部分完成"""
    expert_id = 100

    # 只审核部分元素
    review_system.review_element(element_id=sample_elements[0].id, expert_id=expert_id, decision="approved")

    db_session.refresh(sample_review_task)

    # 审核任务应该还是pending状态
    assert sample_review_task.status == TaskStatus.PENDING


# ==================== 辅助方法测试 ====================


def test_element_to_dict(review_system, sample_elements):
    """测试元素转字典方法"""
    element = sample_elements[0]

    element_dict = review_system._element_to_dict(element)

    assert element_dict["id"] == element.id
    assert element_dict["name"] == element.name
    assert element_dict["type"] == element.type
    assert element_dict["story"] == element.story
    assert "story_length" in element_dict
    assert isinstance(element_dict["keywords"], list)
    assert isinstance(element_dict["metadata"], dict)


# ==================== 边界条件测试 ====================


def test_review_with_empty_comments(review_system, sample_elements):
    """测试空审核意见"""
    element = sample_elements[0]

    result = review_system.review_element(element_id=element.id, expert_id=100, decision="approved", comments="")

    assert result["success"] is True


def test_review_with_long_comments(review_system, sample_elements):
    """测试超长审核意见"""
    element = sample_elements[0]

    long_comments = "这是一段非常长的审核意见..." * 100

    result = review_system.review_element(
        element_id=element.id, expert_id=100, decision="approved", comments=long_comments
    )

    assert result["success"] is True


def test_batch_review_empty_list(review_system):
    """测试批量审核空列表"""
    result = review_system.batch_review(element_ids=[], expert_id=100, decision="approved")

    assert result["total"] == 0
    assert result["success"] == 0


def test_review_with_special_characters(review_system, sample_elements):
    """测试包含特殊字符的审核"""
    element = sample_elements[0]

    corrections = {"story": "包含特殊字符：<>\"'&\n\t的故事", "keywords": ["关键词<1>", '关键词"2"']}

    result = review_system.review_element(
        element_id=element.id, expert_id=100, decision="needs_correction", corrections=corrections
    )

    assert result["success"] is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
