"""
文化元素专家审核系统
支持在线审核、批量审核、审核历史追踪

版本: 1.0
创建日期: 2026-06-12
"""

from typing import Dict, List, Optional
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
import json


class CulturalExpertReviewSystem:
    """文化元素专家审核系统"""

    def __init__(self, db: Session):
        self.db = db

    # =========================================================================
    # 审核任务管理
    # =========================================================================

    def get_pending_reviews(
        self, expert_id: Optional[int] = None, priority: Optional[str] = None, limit: int = 20
    ) -> List[Dict]:
        """
        获取待审核任务列表

        Args:
            expert_id: 专家ID（可选，用于分配制）
            priority: 优先级过滤（P0/P1/P2）
            limit: 返回数量限制

        Returns:
            待审核任务列表
        """
        from app.models.cultural import CulturalReviewTask, CulturalElement

        query = self.db.query(CulturalReviewTask).filter(CulturalReviewTask.status == "pending")

        if expert_id:
            query = query.filter(CulturalReviewTask.assigned_expert_id == expert_id)

        if priority:
            query = query.filter(CulturalReviewTask.priority == priority)

        # 按优先级排序：P0 > P1 > P2
        priority_order = {"P0": 0, "P1": 1, "P2": 2}
        tasks = query.order_by(CulturalReviewTask.created_at.desc()).limit(limit).all()

        # 获取每个任务的待审核元素
        result = []
        for task in tasks:
            elements = (
                self.db.query(CulturalElement)
                .filter(
                    and_(
                        CulturalElement.collection_task_id == task.collection_task_id,
                        CulturalElement.status == "pending_review",
                    )
                )
                .all()
            )

            result.append(
                {
                    "review_task_id": task.id,
                    "collection_task_id": task.collection_task_id,
                    "priority": task.priority,
                    "element_count": len(elements),
                    "elements": [self._element_to_dict(e) for e in elements],
                    "created_at": task.created_at.isoformat(),
                    "assigned_expert": task.assigned_expert_id,
                }
            )

        return result

    def assign_review_task(self, review_task_id: int, expert_id: int) -> Dict:
        """
        分配审核任务给专家

        Args:
            review_task_id: 审核任务ID
            expert_id: 专家ID

        Returns:
            分配结果
        """
        from app.models.cultural import CulturalReviewTask

        task = self.db.query(CulturalReviewTask).filter(CulturalReviewTask.id == review_task_id).first()

        if not task:
            return {"error": "审核任务不存在"}

        if task.status != "pending":
            return {"error": "任务已被处理"}

        task.assigned_expert_id = expert_id
        task.status = "assigned"
        task.assigned_at = datetime.utcnow()

        self.db.commit()

        return {
            "success": True,
            "review_task_id": review_task_id,
            "expert_id": expert_id,
            "assigned_at": task.assigned_at.isoformat(),
        }

    # =========================================================================
    # 单个元素审核
    # =========================================================================

    def review_element(
        self,
        element_id: int,
        expert_id: int,
        decision: str,
        comments: Optional[str] = None,
        corrections: Optional[Dict] = None,
    ) -> Dict:
        """
        审核单个文化元素

        Args:
            element_id: 元素ID
            expert_id: 审核专家ID
            decision: 审核决定（approved/rejected/needs_correction）
            comments: 审核意见
            corrections: 修正建议（JSON格式）
                {
                    "story": "修正后的故事文本",
                    "keywords": ["修正后的关键词"],
                    "cultural_significance": "修正后的文化意义"
                }

        Returns:
            审核结果
        """
        from app.models.cultural import CulturalElement, CulturalReview

        # 1. 获取元素
        element = self.db.query(CulturalElement).filter(CulturalElement.id == element_id).first()

        if not element:
            return {"error": "元素不存在"}

        if element.status not in ["pending_review", "needs_correction"]:
            return {"error": f"元素当前状态为 {element.status}，无法审核"}

        # 2. 创建审核记录
        review = CulturalReview(
            element_id=element_id,
            expert_id=expert_id,
            decision=decision,
            comments=comments,
            corrections=json.dumps(corrections, ensure_ascii=False) if corrections else None,
            reviewed_at=datetime.utcnow(),
        )

        self.db.add(review)

        # 3. 更新元素状态
        if decision == "approved":
            element.status = "approved"
            element.approved_at = datetime.utcnow()
            element.approved_by = expert_id

        elif decision == "rejected":
            element.status = "rejected"
            element.rejected_at = datetime.utcnow()
            element.rejected_by = expert_id

        elif decision == "needs_correction":
            element.status = "needs_correction"
            # 如果提供了修正建议，自动应用
            if corrections:
                self._apply_corrections(element, corrections)

        element.reviewed_at = datetime.utcnow()
        element.reviewed_by = expert_id

        self.db.commit()

        # 4. 检查是否所有元素都已审核
        self._check_review_task_completion(element.collection_task_id)

        return {"success": True, "element_id": element_id, "decision": decision, "new_status": element.status}

    def _apply_corrections(self, element, corrections: Dict):
        """应用专家的修正建议"""
        if "story" in corrections:
            element.story = corrections["story"]

        if "keywords" in corrections:
            element.keywords = json.dumps(corrections["keywords"], ensure_ascii=False)

        if "cultural_significance" in corrections:
            metadata = json.loads(element.element_metadata)
            metadata["cultural_significance"] = corrections["cultural_significance"]
            element.element_metadata = json.dumps(metadata, ensure_ascii=False)

        # 应用修正后重置为待审核状态
        element.status = "pending_review"

    # =========================================================================
    # 批量审核
    # =========================================================================

    def batch_review(
        self, element_ids: List[int], expert_id: int, decision: str, comments: Optional[str] = None
    ) -> Dict:
        """
        批量审核多个元素

        Args:
            element_ids: 元素ID列表
            expert_id: 审核专家ID
            decision: 统一的审核决定
            comments: 审核意见

        Returns:
            批量审核结果
        """
        results = {"total": len(element_ids), "success": 0, "failed": 0, "details": []}

        for element_id in element_ids:
            result = self.review_element(
                element_id=element_id, expert_id=expert_id, decision=decision, comments=comments
            )

            if result.get("success"):
                results["success"] += 1
            else:
                results["failed"] += 1

            results["details"].append({"element_id": element_id, "result": result})

        return results

    # =========================================================================
    # 审核历史查询
    # =========================================================================

    def get_review_history(
        self,
        element_id: Optional[int] = None,
        expert_id: Optional[int] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 50,
    ) -> List[Dict]:
        """
        查询审核历史

        Args:
            element_id: 元素ID（可选）
            expert_id: 专家ID（可选）
            start_date: 开始日期（可选）
            end_date: 结束日期（可选）
            limit: 返回数量限制

        Returns:
            审核历史列表
        """
        from app.models.cultural import CulturalReview, CulturalElement
        from app.models.user import User

        query = self.db.query(CulturalReview)

        if element_id:
            query = query.filter(CulturalReview.element_id == element_id)

        if expert_id:
            query = query.filter(CulturalReview.expert_id == expert_id)

        if start_date:
            query = query.filter(CulturalReview.reviewed_at >= start_date)

        if end_date:
            query = query.filter(CulturalReview.reviewed_at <= end_date)

        reviews = query.order_by(CulturalReview.reviewed_at.desc()).limit(limit).all()

        # 关联元素和专家信息
        result = []
        for review in reviews:
            element = self.db.query(CulturalElement).filter(CulturalElement.id == review.element_id).first()

            expert = self.db.query(User).filter(User.id == review.expert_id).first()

            result.append(
                {
                    "review_id": review.id,
                    "element_name": element.name if element else "未知",
                    "element_type": element.type if element else "未知",
                    "expert_name": expert.username if expert else "未知",
                    "decision": review.decision,
                    "comments": review.comments,
                    "corrections": json.loads(review.corrections) if review.corrections else None,
                    "reviewed_at": review.reviewed_at.isoformat(),
                }
            )

        return result

    # =========================================================================
    # 审核统计
    # =========================================================================

    def get_review_statistics(
        self,
        expert_id: Optional[int] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> Dict:
        """
        获取审核统计数据

        Args:
            expert_id: 专家ID（可选，用于个人统计）
            start_date: 开始日期（可选）
            end_date: 结束日期（可选）

        Returns:
            统计数据字典
        """
        from app.models.cultural import CulturalReview, CulturalElement

        query = self.db.query(CulturalReview)

        if expert_id:
            query = query.filter(CulturalReview.expert_id == expert_id)

        if start_date:
            query = query.filter(CulturalReview.reviewed_at >= start_date)

        if end_date:
            query = query.filter(CulturalReview.reviewed_at <= end_date)

        reviews = query.all()

        # 统计各状态数量
        stats = {
            "total_reviewed": len(reviews),
            "approved": 0,
            "rejected": 0,
            "needs_correction": 0,
            "by_type": {},
            "average_review_time": None,
        }

        for review in reviews:
            if review.decision == "approved":
                stats["approved"] += 1
            elif review.decision == "rejected":
                stats["rejected"] += 1
            elif review.decision == "needs_correction":
                stats["needs_correction"] += 1

            # 按元素类型统计
            element = self.db.query(CulturalElement).filter(CulturalElement.id == review.element_id).first()

            if element:
                element_type = element.type
                if element_type not in stats["by_type"]:
                    stats["by_type"][element_type] = 0
                stats["by_type"][element_type] += 1

        return stats

    # =========================================================================
    # 辅助方法
    # =========================================================================

    def _element_to_dict(self, element) -> Dict:
        """将元素对象转换为字典"""
        return {
            "id": element.id,
            "name": element.name,
            "type": element.type,
            "story": element.story,
            "story_length": len(element.story),
            "origin_region": element.origin_region,
            "keywords": json.loads(element.keywords),
            "metadata": json.loads(element.element_metadata),
            "status": element.status,
            "created_at": element.created_at.isoformat(),
        }

    def _check_review_task_completion(self, collection_task_id: str):
        """检查采集任务的所有元素是否都已审核完成"""
        from app.models.cultural import CulturalReviewTask, CulturalElement

        # 查询该采集任务的所有元素
        elements = self.db.query(CulturalElement).filter(CulturalElement.collection_task_id == collection_task_id).all()

        # 检查是否全部审核完成
        all_reviewed = all(e.status in ["approved", "rejected"] for e in elements)

        if all_reviewed:
            # 更新审核任务状态为完成
            review_task = (
                self.db.query(CulturalReviewTask)
                .filter(CulturalReviewTask.collection_task_id == collection_task_id)
                .first()
            )

            if review_task:
                review_task.status = "completed"
                review_task.completed_at = datetime.utcnow()
                self.db.commit()


# =============================================================================
# FastAPI 路由集成示例
# =============================================================================

"""
# backend/app/api/v1/cultural_review.py

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.deps import get_db, get_current_user
from app.services.cultural.expert_review import CulturalExpertReviewSystem
from app.schemas.cultural import ReviewDecisionRequest, BatchReviewRequest

router = APIRouter()


@router.get("/pending")
async def get_pending_reviews(
    priority: Optional[str] = None,
    limit: int = 20,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    \"\"\"获取待审核任务列表\"\"\"
    # 检查用户是否有审核权限
    if not current_user.has_permission("cultural_review"):
        raise HTTPException(403, "无审核权限")

    review_system = CulturalExpertReviewSystem(db)
    tasks = review_system.get_pending_reviews(
        expert_id=current_user.id,
        priority=priority,
        limit=limit
    )

    return {"tasks": tasks, "total": len(tasks)}


@router.post("/assign/{review_task_id}")
async def assign_review_task(
    review_task_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    \"\"\"领取审核任务\"\"\"
    review_system = CulturalExpertReviewSystem(db)
    result = review_system.assign_review_task(review_task_id, current_user.id)

    if "error" in result:
        raise HTTPException(400, result["error"])

    return result


@router.post("/review/{element_id}")
async def review_element(
    element_id: int,
    request: ReviewDecisionRequest,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    \"\"\"审核单个元素\"\"\"
    review_system = CulturalExpertReviewSystem(db)
    result = review_system.review_element(
        element_id=element_id,
        expert_id=current_user.id,
        decision=request.decision,
        comments=request.comments,
        corrections=request.corrections
    )

    if "error" in result:
        raise HTTPException(400, result["error"])

    return result


@router.post("/batch-review")
async def batch_review(
    request: BatchReviewRequest,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    \"\"\"批量审核\"\"\"
    review_system = CulturalExpertReviewSystem(db)
    result = review_system.batch_review(
        element_ids=request.element_ids,
        expert_id=current_user.id,
        decision=request.decision,
        comments=request.comments
    )

    return result


@router.get("/history")
async def get_review_history(
    element_id: Optional[int] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    limit: int = 50,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    \"\"\"查询审核历史\"\"\"
    review_system = CulturalExpertReviewSystem(db)

    history = review_system.get_review_history(
        element_id=element_id,
        expert_id=current_user.id,
        limit=limit
    )

    return {"history": history, "total": len(history)}


@router.get("/statistics")
async def get_statistics(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    \"\"\"获取审核统计\"\"\"
    review_system = CulturalExpertReviewSystem(db)

    stats = review_system.get_review_statistics(
        expert_id=current_user.id
    )

    return stats
"""
