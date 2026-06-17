"""
文化元素知识图谱查询 API

提供:
- GET  /cultural/graph/path?source_id=X&target_id=Y  路径查询 (BFS, 最多 3 跳)
- GET  /cultural/graph/recommend?element_id=X        关系推荐 (共同邻居)
- GET  /cultural/graph/related-products?element_id=X  关联产品
- GET  /cultural/graph/stats                         图谱统计 (节点/边/密度)

版本: 1.0
创建日期: 2026-06-17
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional
import logging

from app.core.database import get_db
from app.core.responses import success_response
from app.services.graph_query_service import CulturalGraphQueryService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/cultural/graph", tags=["文化图谱 - Graph Query"])


@router.get("/path")
async def find_path(
    source_id: int = Query(..., gt=0, description="源元素ID"),
    target_id: int = Query(..., gt=0, description="目标元素ID"),
    max_hops: int = Query(3, ge=1, le=5, description="最大跳数"),
    db: Session = Depends(get_db),
):
    """查找两个文化元素之间的关联路径 (BFS, 最多 5 跳)

    边定义: 共享 origin_region / type / 至少 1 个 keyword
    """
    try:
        service = CulturalGraphQueryService(db)
        result = service.find_path(source_id, target_id, max_hops)
        return success_response(data=result)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"⚠️ WARNING: find_path failed: {e}")
        raise HTTPException(status_code=500, detail=f"路径查询失败: {str(e)}")


@router.get("/recommend")
async def recommend_related(
    element_id: int = Query(..., gt=0),
    top_k: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db),
):
    """基于共同邻居的元素推荐

    返回与指定元素共享最多邻居/属性的元素列表
    """
    try:
        service = CulturalGraphQueryService(db)
        results = service.recommend_related(element_id, top_k)
        return success_response(
            data={"element_id": element_id, "recommendations": results, "count": len(results)}
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"⚠️ WARNING: recommend_related failed: {e}")
        raise HTTPException(status_code=500, detail=f"推荐失败: {str(e)}")


@router.get("/related-products")
async def related_products(
    element_id: int = Query(..., gt=0),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """通过文化元素查找关联产品 (按产地/类别模糊匹配)"""
    try:
        service = CulturalGraphQueryService(db)
        results = service.get_related_products(element_id, limit)
        return success_response(
            data={"element_id": element_id, "products": results, "count": len(results)}
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"⚠️ WARNING: related_products failed: {e}")
        raise HTTPException(status_code=500, detail=f"查询失败: {str(e)}")


@router.get("/stats")
async def graph_stats(db: Session = Depends(get_db)):
    """知识图谱统计 (节点/边/密度)"""
    try:
        service = CulturalGraphQueryService(db)
        stats = service.get_graph_stats()
        return success_response(data=stats)
    except Exception as e:
        logger.error(f"⚠️ WARNING: graph_stats failed: {e}")
        raise HTTPException(status_code=500, detail=f"统计失败: {str(e)}")
