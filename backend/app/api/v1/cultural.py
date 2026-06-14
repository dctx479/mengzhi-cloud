"""
文化元素API路由
提供文化元素CRUD、智能匹配、知识图谱查询等接口

版本: 1.0
创建日期: 2026-06-12
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional, Dict
import json

from app.api.deps import get_db, get_current_user
from app.core.responses import success_response
from app.services.cultural.enhanced_collector import EnhancedCulturalCollector
from app.services.cultural.knowledge_graph import CulturalKnowledgeGraph
from app.services.cultural.auto_trigger import CulturalCollectionTrigger
from app.services.cultural.expert_review import CulturalExpertReviewSystem
from app.models.cultural import CulturalElement, CulturalCollectionTask, TaskStatus

router = APIRouter()


# =============================================================================
# 文化元素基础CRUD
# =============================================================================

@router.get("/elements")
async def list_cultural_elements(
    type: Optional[str] = None,
    origin_region: Optional[str] = None,
    keyword: Optional[str] = None,
    status: Optional[str] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """
    获取文化元素列表

    Query参数:
        type: 元素类型过滤
        origin_region: 产地过滤
        keyword: 关键词过滤
        status: 状态过滤
        page: 页码
        page_size: 每页数量
    """
    query = db.query(CulturalElement)

    # 过滤条件
    if type:
        query = query.filter(CulturalElement.type == type)

    if origin_region:
        query = query.filter(CulturalElement.origin_region.contains(origin_region))

    if keyword:
        query = query.filter(CulturalElement.keywords.contains(keyword))

    if status:
        query = query.filter(CulturalElement.status == status)

    # 分页
    total = query.count()
    elements = query.offset((page - 1) * page_size).limit(page_size).all()

    return success_response(data={
        "elements": [
            {
                "id": e.id,
                "name": e.name,
                "type": e.type,
                "origin_region": e.origin_region,
                "story_preview": e.story[:100] + "..." if len(e.story) > 100 else e.story,
                "keywords": json.loads(e.keywords) if e.keywords else [],
                "status": e.status,
                "created_at": e.created_at.isoformat() if e.created_at else None
            }
            for e in elements
        ],
        "pagination": {
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": (total + page_size - 1) // page_size
        }
    }).dict()


@router.get("/elements/{element_id}")
async def get_cultural_element(
    element_id: int,
    db: Session = Depends(get_db)
):
    """获取单个文化元素详情"""
    element = db.query(CulturalElement).filter(CulturalElement.id == element_id).first()

    if not element:
        raise HTTPException(status_code=404, detail="文化元素不存在")

    return success_response(data={
        "id": element.id,
        "name": element.name,
        "type": element.type,
        "story": element.story,
        "origin_region": element.origin_region,
        "keywords": json.loads(element.keywords) if element.keywords else [],
        "metadata": json.loads(element.element_metadata) if element.element_metadata else {},
        "source": element.source,
        "status": element.status,
        "created_at": element.created_at.isoformat() if element.created_at else None,
        "reviewed_at": element.reviewed_at.isoformat() if element.reviewed_at else None
    }).dict()


# =============================================================================
# 智能匹配接口
# =============================================================================

@router.post("/match")
async def match_cultural_elements(
    product_name: str,
    origin: str,
    category: str = "",
    keywords: List[str] = [],
    use_knowledge_graph: bool = True,
    top_k: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db)
):
    """
    智能匹配文化元素

    Body:
        product_name: 产品名称
        origin: 产地
        category: 产品类别
        keywords: 关键词列表
        use_knowledge_graph: 是否使用知识图谱
        top_k: 返回前K个结果

    Returns:
        匹配的文化元素列表及评分详情
    """
    try:
        # 初始化增强版采集器
        collector = EnhancedCulturalCollector(enable_kg=use_knowledge_graph)

        # 构建产品信息
        product_info = {
            "name": product_name,
            "origin": origin,
            "category": category,
            "keywords": keywords
        }

        # 执行智能匹配
        results = collector.intelligent_match(
            product_info,
            use_kg=use_knowledge_graph,
            top_k=top_k
        )

        # 格式化返回结果
        matched_elements = []
        for result in results:
            element = result["element"]
            matched_elements.append({
                "element": {
                    "name": element["name"],
                    "type": element["type"],
                    "story": element["story"],
                    "origin_region": element["origin_region"],
                    "keywords": element.get("keywords", [])
                },
                "score": round(result["score"], 2),
                "match_reason": result["match_reason"],
                "score_breakdown": {
                    "exact_match": round(result["score_breakdown"]["exact_match"], 2),
                    "knowledge_graph": round(result["score_breakdown"]["knowledge_graph"], 2)
                },
                "path_info": result.get("path_info")
            })

        return success_response(data={
            "matched_elements": matched_elements,
            "total_count": len(matched_elements),
            "query": product_info
        }).dict()

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"匹配失败: {str(e)}")


@router.get("/match/product/{product_id}")
async def match_by_product_id(
    product_id: int,
    use_knowledge_graph: bool = True,
    top_k: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db)
):
    """根据产品ID智能匹配文化元素"""
    from app.models.product import Product

    # 查询产品
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="产品不存在")

    # 初始化采集器
    collector = EnhancedCulturalCollector(enable_kg=use_knowledge_graph)

    # 构建产品信息
    product_info = {
        "id": product.id,
        "name": product.name,
        "origin": product.origin_province or product.origin_city or "",
        "category": product.category,
        "keywords": product.keywords.split(",") if product.keywords else []
    }

    # 执行匹配
    results = collector.intelligent_match(product_info, use_kg=use_knowledge_graph, top_k=top_k)

    # 格式化返回
    matched_elements = []
    for result in results:
        element = result["element"]
        matched_elements.append({
            "element": {
                "name": element["name"],
                "type": element["type"],
                "story": element["story"],
                "origin_region": element["origin_region"],
                "keywords": element.get("keywords", [])
            },
            "score": round(result["score"], 2),
            "match_reason": result["match_reason"],
            "score_breakdown": result["score_breakdown"]
        })

    return success_response(data={
        "product_id": product_id,
        "product_name": product.name,
        "matched_elements": matched_elements,
        "total_count": len(matched_elements)
    }).dict()


# =============================================================================
# 采集任务管理
# =============================================================================

@router.post("/collect/trigger")
async def trigger_collection(
    product_id: Optional[int] = None,
    product_name: str = "",
    origin: str = "",
    category: str = "",
    keywords: List[str] = [],
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    手动触发文化元素采集

    Body:
        product_id: 产品ID（可选）
        product_name: 产品名称
        origin: 产地
        category: 类别
        keywords: 关键词
    """
    try:
        trigger = CulturalCollectionTrigger(db)

        product_info = {
            "id": product_id,
            "name": product_name,
            "origin": origin,
            "category": category,
            "keywords": keywords
        }

        result = trigger.check_and_trigger(product_info)

        return success_response(data=result).dict()

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"触发采集失败: {str(e)}")


@router.get("/collect/tasks")
async def list_collection_tasks(
    status: Optional[str] = None,
    priority: Optional[str] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """获取采集任务列表"""
    query = db.query(CulturalCollectionTask)

    if status:
        query = query.filter(CulturalCollectionTask.status == status)

    if priority:
        query = query.filter(CulturalCollectionTask.priority == priority)

    total = query.count()
    tasks = query.order_by(CulturalCollectionTask.created_at.desc()).offset((page - 1) * page_size).limit(page_size).all()

    return success_response(data={
        "tasks": [
            {
                "task_id": t.task_id,
                "product_name": t.product_name,
                "origin": t.origin,
                "priority": t.priority,
                "status": t.status,
                "targets": json.loads(t.targets) if t.targets else [],
                "created_at": t.created_at.isoformat() if t.created_at else None,
                "completed_at": t.completed_at.isoformat() if t.completed_at else None
            }
            for t in tasks
        ],
        "pagination": {
            "total": total,
            "page": page,
            "page_size": page_size
        }
    }).dict()


@router.get("/collect/tasks/{task_id}")
async def get_collection_task_status(
    task_id: str,
    db: Session = Depends(get_db)
):
    """查询采集任务状态"""
    trigger = CulturalCollectionTrigger(db)
    status = trigger.get_task_status(task_id)

    if "error" in status:
        raise HTTPException(status_code=404, detail=status["error"])

    return success_response(data=status).dict()


# =============================================================================
# 知识图谱查询
# =============================================================================

@router.get("/graph/statistics")
async def get_graph_statistics():
    """获取知识图谱统计信息"""
    try:
        kg = CulturalKnowledgeGraph()
        stats = kg.get_graph_statistics()

        return success_response(data=stats).dict()

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"查询失败: {str(e)}")


@router.get("/graph/elements/by-region/{region}")
async def find_elements_by_region(
    region: str,
    include_synonyms: bool = True
):
    """根据地域查找文化元素（知识图谱）"""
    try:
        kg = CulturalKnowledgeGraph()
        element_indices = kg.find_elements_by_region(region, include_synonyms)

        # 加载完整元素数据
        collector = EnhancedCulturalCollector(enable_kg=False)
        elements = [collector.elements[idx] for idx in element_indices]

        return success_response(data={
            "region": region,
            "count": len(elements),
            "elements": [
                {
                    "name": e["name"],
                    "type": e["type"],
                    "story_preview": e["story"][:100] + "...",
                    "keywords": e.get("keywords", [])
                }
                for e in elements
            ]
        }).dict()

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"查询失败: {str(e)}")


@router.get("/graph/elements/by-scenario/{scenario}")
async def find_elements_by_scenario(scenario: str):
    """根据使用场景查找文化元素"""
    try:
        kg = CulturalKnowledgeGraph()
        element_indices = kg.find_elements_by_scenario(scenario)

        collector = EnhancedCulturalCollector(enable_kg=False)
        elements = [collector.elements[idx] for idx in element_indices]

        return success_response(data={
            "scenario": scenario,
            "count": len(elements),
            "elements": [
                {
                    "name": e["name"],
                    "type": e["type"],
                    "story_preview": e["story"][:100] + "...",
                    "usage_scenarios": e.get("metadata", {}).get("usage_scenarios", [])
                }
                for e in elements
            ]
        }).dict()

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"查询失败: {str(e)}")


# =============================================================================
# 审核系统接口
# =============================================================================

@router.get("/review/pending")
async def get_pending_reviews(
    priority: Optional[str] = None,
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """获取待审核任务列表"""
    review_system = CulturalExpertReviewSystem(db)

    # 检查用户是否有审核权限
    # if not current_user.get("role") in ["admin", "expert"]:
    #     raise HTTPException(status_code=403, detail="无审核权限")

    tasks = review_system.get_pending_reviews(
        priority=priority,
        limit=limit
    )

    return success_response(data={
        "tasks": tasks,
        "total": len(tasks)
    }).dict()


@router.post("/review/assign/{review_task_id}")
async def assign_review_task(
    review_task_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """领取审核任务"""
    review_system = CulturalExpertReviewSystem(db)

    expert_id = current_user.get("user_id")  # 使用JWT中的user_id
    result = review_system.assign_review_task(review_task_id, expert_id)

    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])

    return success_response(data=result).dict()


@router.post("/review/element/{element_id}")
async def review_element(
    element_id: int,
    decision: str,
    comments: Optional[str] = "",
    corrections: Optional[Dict] = None,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """审核单个文化元素"""
    review_system = CulturalExpertReviewSystem(db)

    expert_id = current_user.get("user_id")
    result = review_system.review_element(
        element_id=element_id,
        expert_id=expert_id,
        decision=decision,
        comments=comments,
        corrections=corrections
    )

    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])

    return success_response(data=result).dict()


@router.get("/review/history")
async def get_review_history(
    element_id: Optional[int] = None,
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """查询审核历史"""
    review_system = CulturalExpertReviewSystem(db)

    expert_id = current_user.get("user_id")
    history = review_system.get_review_history(
        element_id=element_id,
        expert_id=expert_id,
        limit=limit
    )

    return success_response(data={
        "history": history,
        "total": len(history)
    }).dict()


@router.get("/review/statistics")
async def get_review_statistics(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """获取审核统计"""
    review_system = CulturalExpertReviewSystem(db)

    expert_id = current_user.get("user_id")
    stats = review_system.get_review_statistics(expert_id=expert_id)

    return success_response(data=stats).dict()


# =============================================================================
# 统计分析
# =============================================================================

@router.get("/statistics/overview")
async def get_cultural_statistics(db: Session = Depends(get_db)):
    """获取文化元素统计概览"""
    # 总数统计
    total_elements = db.query(CulturalElement).count()
    approved_elements = db.query(CulturalElement).filter(
        CulturalElement.status == "approved"
    ).count()
    pending_elements = db.query(CulturalElement).filter(
        CulturalElement.status == "pending_review"
    ).count()

    # 按类型统计
    from sqlalchemy import func
    type_stats = db.query(
        CulturalElement.type,
        func.count(CulturalElement.id).label("count")
    ).group_by(CulturalElement.type).all()

    # 采集任务统计
    total_tasks = db.query(CulturalCollectionTask).count()
    completed_tasks = db.query(CulturalCollectionTask).filter(
        CulturalCollectionTask.status == TaskStatus.COMPLETED
    ).count()

    return success_response(data={
        "elements": {
            "total": total_elements,
            "approved": approved_elements,
            "pending": pending_elements
        },
        "by_type": {t: c for t, c in type_stats},
        "tasks": {
            "total": total_tasks,
            "completed": completed_tasks,
            "success_rate": round(completed_tasks / total_tasks * 100, 2) if total_tasks > 0 else 0
        }
    }).dict()
