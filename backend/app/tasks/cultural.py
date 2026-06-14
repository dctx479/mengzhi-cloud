"""
文化元素采集任务
使用Agent并行采集文化元素

版本: 2.0
创建日期: 2026-06-12
更新日期: 2026-06-14 (移除 Celery，改为纯函数 + APScheduler 调度)
"""

import asyncio
from typing import Dict, List
import json
from datetime import datetime
from loguru import logger
from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.services.cultural import AdaptiveCulturalCollector


def collect_cultural_elements(task_id: str, task_params: Dict) -> Dict:
    """
    采集文化元素（同步执行，状态写入 CulturalCollectionTask 表）

    原 Celery 异步任务重构为纯函数，由调用方（auto_trigger / APScheduler）驱动。
    任务状态全程通过数据库表跟踪，不依赖外部任务队列。

    Args:
        task_id: 采集任务ID（由调用方生成并预先写入任务记录）
        task_params: 任务参数
            {
                "product_id": 123,
                "product_name": "阿拉善驼肉",
                "origin": "阿拉善",
                "category": "驼肉类",
                "targets": ["地理景观", "传统工艺"],
                "priority": "P0/P1/P2",
                "created_at": "2026-06-12T10:00:00"
            }

    Returns:
        采集结果字典
    """
    db = SessionLocal()

    try:
        # 1. 更新任务状态为"处理中"
        _update_task_status(db, task_id, "processing")

        # 2. 执行采集
        result = _execute_collection(task_params, db)

        # 3. 保存采集结果
        _save_collection_results(db, task_id, result)

        # 4. 更新任务状态为"完成"
        _update_task_status(db, task_id, "completed", result)

        # 5. 触发专家审核
        _trigger_expert_review(db, task_id, result)

        return result

    except Exception as e:
        error_msg = str(e)
        logger.error(f"⚠️ 文化元素采集任务失败 task_id={task_id}: {error_msg}")
        _update_task_status(db, task_id, "failed", {"error": error_msg})
        return {"status": "failed", "error": error_msg}

    finally:
        db.close()


def _execute_collection(task_params: Dict, db: Session) -> Dict:
    """
    执行文化元素采集

    策略：
    1. 优先从现有数据库查询相似产地的文化元素
    2. 如果不足，触发Agent采集新元素
    3. 采集完成后自动匹配到产品

    Returns:
        {
            "status": "success/partial/failed",
            "collected_count": 5,
            "new_elements": [...],
            "matched_elements": [...],
            "method": "existing/agent_collection"
        }
    """
    origin = task_params["origin"]
    category = task_params["category"]
    targets = task_params["targets"]

    # 1. 先尝试从现有数据中查找
    collector = AdaptiveCulturalCollector()
    existing_matches = []

    for target_type in targets:
        elements = collector.match_by_type(target_type)
        # 筛选匹配产地的元素
        region_matches = [e for e in elements if origin in e.get("origin_region", "")]
        existing_matches.extend(region_matches)

    # 2. 如果现有元素足够（≥3个），直接返回
    if len(existing_matches) >= 3:
        return {
            "status": "success",
            "collected_count": len(existing_matches),
            "new_elements": [],
            "matched_elements": existing_matches[:5],
            "method": "existing",
        }

    # 3. 否则触发Agent采集新元素
    new_elements = _trigger_agent_collection(task_params)

    # 4. 合并现有元素和新元素
    all_matches = existing_matches + new_elements

    return {
        "status": "success" if len(all_matches) >= 3 else "partial",
        "collected_count": len(all_matches),
        "new_elements": new_elements,
        "matched_elements": all_matches[:5],
        "method": "agent_collection",
    }


def _trigger_agent_collection(task_params: Dict) -> List[Dict]:
    """
    触发Agent采集新文化元素

    使用subprocess调用Claude Agent执行采集任务

    Returns:
        新采集的文化元素列表
    """
    origin = task_params["origin"]
    category = task_params["category"]
    targets = task_params["targets"]

    # 构建Agent Prompt
    prompt = f"""
你需要为新产地"{origin}"采集文化元素，产品类别为"{category}"。

**采集目标**：{', '.join(targets)}

**要求**：
1. 每个类别至少采集2个元素
2. 每个元素500-800字故事
3. 必须与产地"{origin}"直接相关
4. 关联产品必须包含"{category}"

**数据格式**：
```json
{{
  "name": "元素名称",
  "type": "类别（{targets[0]}等）",
  "story": "500-800字故事",
  "origin_region": "{origin}",
  "keywords": ["关键词1", "关键词2"],
  "metadata": {{
    "period": "时期",
    "related_products": ["{category}"],
    "cultural_significance": "文化意义",
    "usage_scenarios": ["品牌故事", "产品溯源"]
  }}
}}
```

请开始采集并将结果追加到 `backend/data/cultural_elements_extended.json`。
"""

    # 这里简化为返回空列表，实际应调用Agent
    # 实际实现可以使用 subprocess 或直接调用 Agent API
    # 例如：
    # result = subprocess.run([
    #     "claude", "agent", "run",
    #     "--prompt", prompt,
    #     "--output", "json"
    # ], capture_output=True, text=True)

    # 暂时返回空列表（实际应该调用Agent）
    return []


def _update_task_status(db: Session, task_id: str, status: str, result: Dict = None):
    """更新任务状态"""
    from app.models.cultural import CulturalCollectionTask

    task = db.query(CulturalCollectionTask).filter(CulturalCollectionTask.task_id == task_id).first()

    if task:
        task.status = status
        task.updated_at = datetime.utcnow()

        if result:
            task.result = json.dumps(result, ensure_ascii=False)

        db.commit()


def _save_collection_results(db: Session, task_id: str, result: Dict):
    """保存采集结果到数据库"""
    from app.models.cultural import CulturalElement

    new_elements = result.get("new_elements", [])

    for element_data in new_elements:
        element = CulturalElement(
            name=element_data["name"],
            type=element_data["type"],
            story=element_data["story"],
            origin_region=element_data["origin_region"],
            keywords=json.dumps(element_data["keywords"], ensure_ascii=False),
            element_metadata=json.dumps(element_data["metadata"], ensure_ascii=False),
            status="pending_review",  # 待审核状态
            collection_task_id=task_id,
            created_at=datetime.utcnow(),
        )

        db.add(element)

    db.commit()


def _trigger_expert_review(db: Session, task_id: str, result: Dict):
    """
    触发专家审核流程

    将新采集的元素加入审核队列，通知专家审核
    """
    from app.models.cultural import CulturalReviewTask
    from app.services.notification_service import NotificationService

    new_count = len(result.get("new_elements", []))

    if new_count == 0:
        return  # 没有新元素，无需审核

    # 1. 创建审核任务
    review_task = CulturalReviewTask(
        collection_task_id=task_id,
        element_count=new_count,
        status="pending",
        priority=_get_review_priority(result),
        created_at=datetime.utcnow(),
    )

    db.add(review_task)
    db.commit()

    # 2. 通知专家（notify_experts 尚未在 NotificationService 实现，缺失时优雅降级为 WARNING）
    notification = NotificationService()
    if hasattr(notification, "notify_experts"):
        notification.notify_experts(
            title=f"新文化元素待审核（{new_count}个）",
            message=f"采集任务 {task_id} 已完成，请审核新增的 {new_count} 个文化元素",
            review_task_id=review_task.id,
        )
    else:
        logger.warning(
            f"⚠️ NotificationService 未实现 notify_experts，跳过专家通知 "
            f"(review_task_id={review_task.id}, 待审核 {new_count} 个元素)"
        )


def _get_review_priority(result: Dict) -> str:
    """
    根据采集结果确定审核优先级

    规则：
    - 完全新产地（无现有元素）: P0
    - 部分采集（<3个元素）: P1
    - 充分采集（≥3个元素）: P2
    """
    collected_count = result.get("collected_count", 0)
    method = result.get("method", "")

    if method == "agent_collection" and collected_count == 0:
        return "P0"  # 采集失败
    elif collected_count < 3:
        return "P1"  # 部分采集
    else:
        return "P2"  # 正常采集


# =============================================================================
# 定时任务：检查待采集的产品
# =============================================================================


def check_products_for_collection():
    """
    定时任务：检查所有产品的文化元素匹配度
    对于匹配度低的产品，自动触发采集

    建议频率：每天凌晨3点执行（由 APScheduler 调度）
    """
    from app.models.product import Product
    from app.services.cultural.auto_trigger import CulturalCollectionTrigger

    db = SessionLocal()

    try:
        # 获取所有产品
        products = db.query(Product).all()

        triggered_count = 0

        for product in products:
            product_info = {
                "id": product.id,
                "name": product.name,
                # Product 无 origin/keywords 列，映射到实际字段：origin_province / cultural_tags(JSON)
                "origin": product.origin_province or "",
                "category": product.category,
                "keywords": product.cultural_tags if isinstance(product.cultural_tags, list) else [],
            }

            # 检查并触发采集
            trigger = CulturalCollectionTrigger(db)
            result = trigger.check_and_trigger(product_info)

            if result["need_collection"]:
                triggered_count += 1

        return {"status": "completed", "total_products": len(products), "triggered_count": triggered_count}

    finally:
        db.close()


# =============================================================================
# 定时任务：清理过期任务
# =============================================================================


def cleanup_old_tasks():
    """
    定时任务：清理30天前的已完成任务

    建议频率：每周执行一次（由 APScheduler 调度）
    """
    from app.models.cultural import CulturalCollectionTask
    from datetime import timedelta

    db = SessionLocal()

    try:
        threshold_date = datetime.utcnow() - timedelta(days=30)

        deleted_count = (
            db.query(CulturalCollectionTask)
            .filter(CulturalCollectionTask.status == "completed", CulturalCollectionTask.updated_at < threshold_date)
            .delete()
        )

        db.commit()

        return {"status": "completed", "deleted_count": deleted_count}

    finally:
        db.close()


# =============================================================================
# APScheduler 异步包装器（同步任务体放入线程池执行，避免阻塞事件循环）
# =============================================================================


async def run_check_products_for_collection():
    """APScheduler 入口：每日检查产品文化元素匹配度并触发采集"""
    return await asyncio.to_thread(check_products_for_collection)


async def run_cleanup_old_tasks():
    """APScheduler 入口：每周清理过期采集任务"""
    return await asyncio.to_thread(cleanup_old_tasks)
