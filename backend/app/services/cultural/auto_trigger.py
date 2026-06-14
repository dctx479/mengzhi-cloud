"""
文化元素自动采集触发器
当产品匹配度低于阈值时自动触发文化元素采集任务

版本: 2.0
创建日期: 2026-06-12
更新日期: 2026-06-14 (移除 Celery，改为同步执行 + 数据库状态跟踪)
"""

import json
import uuid
from typing import Dict, List, Optional
from datetime import datetime
from sqlalchemy.orm import Session
from app.services.cultural import AdaptiveCulturalCollector
from app.core.config import settings


class CulturalCollectionTrigger:
    """文化元素采集触发器"""

    # 匹配度阈值配置（口径：0=P0，0<score≤40=P1，40<score<70=P2，score≥70=OK）
    THRESHOLDS = {
        "P0": 0,  # 无匹配 - 紧急
        "P1": 40,  # ≤40 低匹配 - 高优先级
        "P2": 70,  # 40< <70 中等匹配 - 中优先级（上界即 OK 阈值）
        "OK": 70,  # ≥70 良好匹配 - 无需采集
    }

    def __init__(self, db: Session):
        self.db = db
        self.collector = AdaptiveCulturalCollector()

    def check_and_trigger(self, product_info: Dict) -> Dict:
        """
        检查产品匹配度，必要时触发采集任务

        Args:
            product_info: 产品信息
                {
                    "id": 123,
                    "name": "阿拉善驼肉",
                    "origin": "阿拉善",
                    "category": "驼肉类",
                    "keywords": ["沙漠", "特色"]
                }

        Returns:
            检查结果字典
                {
                    "need_collection": bool,
                    "priority": "P0/P1/P2/OK",
                    "match_score": int,
                    "existing_matches": int,
                    "collection_targets": List[str],
                    "task_id": Optional[str],
                    "reason": str
                }
        """
        # 1. 获取现有匹配
        matches = self.collector.match_by_product(product_info)

        # 2. 计算最高匹配度
        best_score = matches[0]["score"] if matches else 0
        match_count = len(matches)

        # 3. 判断优先级
        priority = self._determine_priority(best_score)

        # 4. 确定采集目标
        collection_targets = self._determine_collection_targets(product_info, matches, priority)

        # 5. 触发采集任务
        task_id = None
        if priority in ["P0", "P1"]:
            task_id = self._trigger_collection_task(product_info, collection_targets, priority)

        return {
            "need_collection": priority in ["P0", "P1"],
            "priority": priority,
            "match_score": best_score,
            "existing_matches": match_count,
            "collection_targets": collection_targets,
            "task_id": task_id,
            "reason": self._generate_reason(best_score, match_count, priority),
        }

    def _determine_priority(self, score: int) -> str:
        """根据评分确定优先级（0=P0，0<score≤40=P1，40<score<70=P2，score≥70=OK）"""
        if score == 0:
            return "P0"  # 无匹配
        elif score <= self.THRESHOLDS["P1"]:
            return "P1"  # ≤40 低匹配
        elif score < self.THRESHOLDS["OK"]:
            return "P2"  # 40< <70 中等匹配
        else:
            return "OK"  # ≥70 良好匹配

    def _determine_collection_targets(self, product_info: Dict, matches: List[Dict], priority: str) -> List[str]:
        """
        确定需要采集的文化类别

        策略：
        - P0（无匹配）：采集 地理景观 + 传统工艺 + 畜牧知识
        - P1（低匹配）：采集 地理景观（优先产地相关）
        - P2（中等匹配）：建议采集但不强制
        """
        if priority == "P0":
            return ["地理景观", "传统工艺", "畜牧知识"]

        if priority == "P1":
            # 检查是否缺少地理景观类
            has_geo = any(m["element"].get("type") == "地理景观" for m in matches)
            if not has_geo:
                return ["地理景观"]

            # 检查是否缺少畜牧知识类
            has_livestock = any(m["element"].get("type") == "畜牧知识" for m in matches)
            if not has_livestock:
                return ["畜牧知识"]

            return ["地理景观"]  # 默认采集地理景观

        if priority == "P2":
            return []  # 中等匹配，建议采集但不触发

        return []

    def _trigger_collection_task(
        self, product_info: Dict, collection_targets: List[str], priority: str
    ) -> Optional[str]:
        """
        触发文化元素采集任务（同步执行，状态写入数据库）

        Args:
            product_info: 产品信息
            collection_targets: 采集目标类别列表
            priority: 优先级

        Returns:
            任务ID
        """
        from app.tasks.cultural import collect_cultural_elements

        # 构建任务参数
        task_params = {
            "product_id": product_info.get("id"),
            "product_name": product_info.get("name"),
            "origin": product_info.get("origin"),
            "category": product_info.get("category"),
            "targets": collection_targets,
            "priority": priority,
            "created_at": datetime.utcnow().isoformat(),
        }

        # 生成任务ID并先落库（status=pending），再同步执行采集
        task_id = f"cultural-{uuid.uuid4().hex[:16]}"
        self._save_collection_task(task_id, task_params)
        collect_cultural_elements(task_id, task_params)

        return task_id

    def _save_collection_task(self, task_id: str, task_params: Dict):
        """保存采集任务记录到数据库"""
        from app.models.cultural import CulturalCollectionTask

        task = CulturalCollectionTask(
            task_id=task_id,
            product_id=task_params.get("product_id"),
            # product_name/origin/category 为 NOT NULL 列，产品信息缺字段时兜底，避免 IntegrityError
            product_name=task_params.get("product_name") or "未知产品",
            origin=task_params.get("origin") or "未知产地",
            category=task_params.get("category") or "未知类别",
            targets=json.dumps(task_params.get("targets") or [], ensure_ascii=False),
            priority=task_params.get("priority") or "P2",
            status="pending",
            created_at=datetime.utcnow(),
        )

        self.db.add(task)
        self.db.commit()

    def _generate_reason(self, score: int, match_count: int, priority: str) -> str:
        """生成触发原因说明"""
        if priority == "P0":
            return f"无匹配文化元素（评分0分），立即采集"
        elif priority == "P1":
            return f"匹配度过低（评分{score}分，共{match_count}个元素），需要采集"
        elif priority == "P2":
            return f"匹配度中等（评分{score}分，共{match_count}个元素），建议采集"
        else:
            return f"匹配度良好（评分{score}分，共{match_count}个元素），无需采集"

    def get_task_status(self, task_id: str) -> Dict:
        """
        查询采集任务状态

        Args:
            task_id: 任务ID

        Returns:
            任务状态字典
        """
        from app.models.cultural import CulturalCollectionTask

        # 从数据库查询任务记录（状态全程由 collect_cultural_elements 写入）
        task = self.db.query(CulturalCollectionTask).filter(CulturalCollectionTask.task_id == task_id).first()

        if not task:
            return {"error": "任务不存在"}

        priority = task.priority.value if hasattr(task.priority, "value") else task.priority
        status = task.status.value if hasattr(task.status, "value") else task.status

        return {
            "task_id": task_id,
            "product_name": task.product_name,
            "origin": task.origin,
            "targets": json.loads(task.targets) if task.targets else [],
            "priority": priority,
            "status": status,
            "created_at": task.created_at.isoformat(),
            "updated_at": task.updated_at.isoformat() if task.updated_at else None,
            "result": json.loads(task.result) if task.result else None,
        }


# =============================================================================
# 产品服务集成示例
# =============================================================================


def on_product_create(product_info: Dict, db: Session) -> Dict:
    """
    产品创建时的钩子函数
    自动检查文化元素匹配度并触发采集

    Args:
        product_info: 产品信息
        db: 数据库会话

    Returns:
        检查结果
    """
    trigger = CulturalCollectionTrigger(db)
    result = trigger.check_and_trigger(product_info)

    if result["need_collection"]:
        print(f"✅ 已触发文化元素采集任务: {result['task_id']}")
        print(f"   优先级: {result['priority']}")
        print(f"   采集目标: {', '.join(result['collection_targets'])}")
    else:
        print(f"✅ 匹配度良好（{result['match_score']}分），无需采集")

    return result


def check_pending_collections(db: Session) -> List[Dict]:
    """
    检查所有待采集的任务

    Returns:
        待采集任务列表
    """
    from app.models.cultural import CulturalCollectionTask

    pending_tasks = (
        db.query(CulturalCollectionTask).filter(CulturalCollectionTask.status.in_(["pending", "processing"])).all()
    )

    return [
        {
            "task_id": task.task_id,
            "product_name": task.product_name,
            "origin": task.origin,
            "priority": task.priority,
            "status": task.status,
            "created_at": task.created_at.isoformat(),
        }
        for task in pending_tasks
    ]


# =============================================================================
# 使用示例
# =============================================================================

if __name__ == "__main__":
    from app.core.database import SessionLocal

    db = SessionLocal()

    # 测试：新产品检查
    new_product = {
        "id": 999,
        "name": "阿拉善驼肉",
        "origin": "阿拉善",
        "category": "驼肉类",
        "keywords": ["沙漠", "特色"],
    }

    print("=== 文化元素匹配检查 ===")
    print(f"产品: {new_product['name']}")
    print(f"产地: {new_product['origin']}")
    print()

    result = on_product_create(new_product, db)

    print("\n=== 检查结果 ===")
    print(f"需要采集: {result['need_collection']}")
    print(f"优先级: {result['priority']}")
    print(f"当前匹配度: {result['match_score']}分")
    print(f"现有匹配: {result['existing_matches']}个")
    print(f"原因: {result['reason']}")

    if result["need_collection"]:
        print(f"\n采集目标类别: {', '.join(result['collection_targets'])}")
        print(f"任务ID: {result['task_id']}")

    db.close()
