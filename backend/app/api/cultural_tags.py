"""
文化标签管理API路由

版本: 1.0
更新日期: 2026-01-17

端点：
- GET /api/v1/cultural-tags - 获取文化标签列表
- GET /api/v1/cultural-tags/categories - 获取标签分类列表
- GET /api/v1/cultural-tags/recommend - 推荐标签
- GET /api/v1/cultural-tags/statistics - 获取标签统计
- GET /api/v1/cultural-tags/{tag_id} - 获取标签详情
- GET /api/v1/cultural-tags/{tag_id}/products - 获取使用该标签的产品
- POST /api/v1/cultural-tags - 创建文化标签（管理员）
- PUT /api/v1/cultural-tags/{tag_id} - 更新标签（管理员）
- DELETE /api/v1/cultural-tags/{tag_id} - 删除标签（管理员）
"""

from fastapi import APIRouter, Depends, Query, HTTPException, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from sqlalchemy import func
from loguru import logger
from typing import Optional, List

from app.schemas.cultural_tags import (
    CulturalTagCreate,
    CulturalTagUpdate,
    CulturalTagResponse,
    CulturalTagListItemResponse,
    CulturalTagListQuery,
    CulturalTagRecommendQuery,
    TagCategoryResponse,
    TagStatisticsResponse
)
from app.schemas.products import ProductListItemResponse
from app.services.cultural_tag_service import CulturalTagService
from app.core.errors import BusinessException, ErrorCode
from app.core.responses import success_response, error_response, paginated_response
from app.core.constants import TAG_CATEGORIES
from app.api.deps import get_db, require_admin, get_optional_user
from app.models.cultural_tag import CulturalTag, product_tags

# 创建路由器
router = APIRouter()


# ============ 获取标签列表 ============

@router.get("/cultural-tags", response_model=dict, tags=["文化标签"])
async def list_tags(
    category: Optional[str] = Query(None, description="按分类筛选"),
    keyword: Optional[str] = Query(None, max_length=100, description="关键词搜索"),
    is_active: bool = Query(True, description="是否只显示启用的标签"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(50, ge=1, le=100, description="每页数量"),
    db: Session = Depends(get_db)
) -> dict:
    """获取文化标签列表

    支持：
    - 按分类筛选
    - 关键词搜索（标签名称、描述、关键词）
    - 启用状态筛选
    - 分页查询

    返回：
        分页的标签列表
    """
    try:
        service = CulturalTagService(db)

        # 构建查询参数
        query = CulturalTagListQuery(
            category=category,
            keyword=keyword,
            is_active=is_active,
            page=page,
            page_size=page_size
        )

        # 查询标签
        tags, total = service.list_tags(query)

        # 转换为响应对象
        items = [CulturalTagListItemResponse.from_orm(tag) for tag in tags]

        # 返回分页响应
        response = paginated_response(
            items=[item.dict() for item in items],
            page=page,
            size=page_size,
            total=total,
            message="获取文化标签列表成功"
        )

        return response.dict()

    except BusinessException as e:
        logger.error(f"获取文化标签列表失败: {e.message}")
        return JSONResponse(
            status_code=e.get_http_status(),
            content=error_response(code=e.code, message=e.message).dict()
        )
    except Exception as e:
        logger.error(f"获取文化标签列表异常: {str(e)}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=error_response(
                code=ErrorCode.SYSTEM_ERROR,
                message="系统错误"
            ).dict()
        )


# ============ 获取标签分类列表 ============

@router.get("/cultural-tags/categories", response_model=dict, tags=["文化标签"])
async def get_categories(
    db: Session = Depends(get_db)
) -> dict:
    """获取标签分类列表

    返回所有文化标签分类及其统计信息

    返回：
        分类列表
    """
    try:
        # 统计每个分类的标签数量
        category_counts = {}
        for category_info in TAG_CATEGORIES:
            code = category_info['code']
            count = db.query(func.count(CulturalTag.id)).filter(
                CulturalTag.category == code,
                CulturalTag.is_active == True
            ).scalar()
            category_counts[code] = count

        # 构建响应
        categories = []
        for category_info in TAG_CATEGORIES:
            code = category_info['code']
            categories.append({
                "code": code,
                "name": category_info['name'],
                "icon": category_info['icon'],
                "description": category_info['description'],
                "tag_count": category_counts.get(code, 0)
            })

        return success_response(
            data={"categories": categories},
            message="获取标签分类列表成功"
        ).dict()

    except Exception as e:
        logger.error(f"获取标签分类列表异常: {str(e)}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=error_response(
                code=ErrorCode.SYSTEM_ERROR,
                message="系统错误"
            ).dict()
        )


# ============ 标签推荐 ============

@router.get("/cultural-tags/recommend", response_model=dict, tags=["文化标签"])
async def recommend_tags(
    product_id: Optional[int] = Query(None, description="基于产品推荐"),
    keywords: Optional[str] = Query(None, max_length=200, description="基于关键词推荐"),
    limit: int = Query(10, ge=1, le=50, description="推荐数量"),
    db: Session = Depends(get_db)
) -> dict:
    """推荐文化标签

    支持两种推荐方式：
    1. 基于产品推荐：根据同类产品常用标签推荐
    2. 基于关键词推荐：根据关键词匹配推荐

    如果都不提供，返回热门标签

    返回：
        推荐的标签列表
    """
    try:
        service = CulturalTagService(db)

        if product_id:
            # 基于产品推荐
            tags = service.recommend_tags_by_product(product_id, limit)
        elif keywords:
            # 基于关键词推荐
            tags = service.recommend_tags_by_keywords(keywords, limit)
        else:
            # 返回热门标签
            tags = service.get_popular_tags(limit)

        # 转换为响应对象
        items = [CulturalTagListItemResponse.from_orm(tag) for tag in tags]

        return success_response(
            data={"tags": [item.dict() for item in items]},
            message="标签推荐成功"
        ).dict()

    except BusinessException as e:
        logger.error(f"标签推荐失败: {e.message}")
        return JSONResponse(
            status_code=e.get_http_status(),
            content=error_response(code=e.code, message=e.message).dict()
        )
    except Exception as e:
        logger.error(f"标签推荐异常: {str(e)}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=error_response(
                code=ErrorCode.SYSTEM_ERROR,
                message="系统错误"
            ).dict()
        )


# ============ 获取标签统计 ============

@router.get("/cultural-tags/statistics", response_model=dict, tags=["文化标签"])
async def get_statistics(
    db: Session = Depends(get_db)
) -> dict:
    """获取标签统计信息

    返回：
        统计数据（总标签数、启用标签数、分类分布、热门标签）
    """
    try:
        service = CulturalTagService(db)
        stats = service.get_tag_statistics()

        # 转换popular_tags为响应格式
        popular_tags = [
            CulturalTagListItemResponse.from_orm(tag).dict()
            for tag in stats['popular_tags']
        ]

        return success_response(
            data={
                "total_tags": stats['total_tags'],
                "active_tags": stats['active_tags'],
                "category_distribution": stats['category_distribution'],
                "popular_tags": popular_tags
            },
            message="获取标签统计成功"
        ).dict()

    except Exception as e:
        logger.error(f"获取标签统计异常: {str(e)}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=error_response(
                code=ErrorCode.SYSTEM_ERROR,
                message="系统错误"
            ).dict()
        )


# ============ 获取标签详情 ============

@router.get("/cultural-tags/{tag_id}", response_model=dict, tags=["文化标签"])
async def get_tag(
    tag_id: int,
    db: Session = Depends(get_db)
) -> dict:
    """获取标签详情

    参数:
        tag_id: 标签ID

    返回:
        标签详细信息
    """
    try:
        service = CulturalTagService(db)
        tag = service.get_tag_by_id(tag_id)

        response_data = CulturalTagResponse.from_orm(tag)

        return success_response(
            data=response_data.dict(),
            message="获取标签详情成功"
        ).dict()

    except BusinessException as e:
        logger.warning(f"获取标签详情失败: {e.message}")
        return JSONResponse(
            status_code=e.get_http_status(),
            content=error_response(code=e.code, message=e.message).dict()
        )
    except Exception as e:
        logger.error(f"获取标签详情异常: {str(e)}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=error_response(
                code=ErrorCode.SYSTEM_ERROR,
                message="系统错误"
            ).dict()
        )


# ============ 获取使用该标签的产品 ============

@router.get("/cultural-tags/{tag_id}/products", response_model=dict, tags=["文化标签"])
async def get_tag_products(
    tag_id: int,
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    db: Session = Depends(get_db)
) -> dict:
    """获取使用该标签的产品列表

    参数:
        tag_id: 标签ID
        page: 页码
        page_size: 每页数量

    返回:
        产品列表
    """
    try:
        service = CulturalTagService(db)

        # 验证标签存在
        tag = service.get_tag_by_id(tag_id)

        # 获取关联的产品
        from app.models.product import Product

        query = db.query(Product).join(
            product_tags,
            Product.id == product_tags.c.product_id
        ).filter(
            product_tags.c.tag_id == tag_id
        )

        total = query.count()

        offset = (page - 1) * page_size
        products = query.offset(offset).limit(page_size).all()

        # 转换为响应对象
        items = [ProductListItemResponse.from_orm(p) for p in products]

        response = paginated_response(
            items=[item.dict() for item in items],
            page=page,
            size=page_size,
            total=total,
            message=f"获取标签「{tag.name}」的产品列表成功"
        )

        return response.dict()

    except BusinessException as e:
        logger.warning(f"获取标签产品列表失败: {e.message}")
        return JSONResponse(
            status_code=e.get_http_status(),
            content=error_response(code=e.code, message=e.message).dict()
        )
    except Exception as e:
        logger.error(f"获取标签产品列表异常: {str(e)}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=error_response(
                code=ErrorCode.SYSTEM_ERROR,
                message="系统错误"
            ).dict()
        )


# ============ 创建标签 ============

@router.post("/cultural-tags", response_model=dict, tags=["文化标签"])
async def create_tag(
    tag: CulturalTagCreate,
    current_user: dict = Depends(require_admin),
    db: Session = Depends(get_db)
) -> dict:
    """创建文化标签（仅管理员）

    参数:
        tag: 标签创建数据
        current_user: 当前用户（需要管理员权限）
        db: 数据库会话

    返回:
        创建的标签信息
    """
    try:
        service = CulturalTagService(db)
        created_tag = service.create_tag(tag)

        response_data = CulturalTagResponse.from_orm(created_tag)

        return JSONResponse(
            status_code=status.HTTP_201_CREATED,
            content=success_response(
                data=response_data.dict(),
                message="文化标签创建成功"
            ).dict()
        )

    except BusinessException as e:
        logger.warning(f"创建文化标签失败: {e.message}")
        return JSONResponse(
            status_code=e.get_http_status(),
            content=error_response(code=e.code, message=e.message).dict()
        )
    except Exception as e:
        logger.error(f"创建文化标签异常: {str(e)}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=error_response(
                code=ErrorCode.SYSTEM_ERROR,
                message="系统错误"
            ).dict()
        )


# ============ 更新标签 ============

@router.put("/cultural-tags/{tag_id}", response_model=dict, tags=["文化标签"])
async def update_tag(
    tag_id: int,
    tag: CulturalTagUpdate,
    current_user: dict = Depends(require_admin),
    db: Session = Depends(get_db)
) -> dict:
    """更新文化标签（仅管理员）

    参数:
        tag_id: 标签ID
        tag: 标签更新数据
        current_user: 当前用户（需要管理员权限）
        db: 数据库会话

    返回:
        更新后的标签信息
    """
    try:
        # 验证请求体不为空
        if not tag.dict(exclude_unset=True):
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content=error_response(
                    code=ErrorCode.PARAM_ERROR,
                    message="请求体不能为空"
                ).dict()
            )

        service = CulturalTagService(db)
        updated_tag = service.update_tag(tag_id, tag)

        response_data = CulturalTagResponse.from_orm(updated_tag)

        return success_response(
            data=response_data.dict(),
            message="文化标签更新成功"
        ).dict()

    except BusinessException as e:
        logger.warning(f"更新文化标签失败: {e.message}")
        return JSONResponse(
            status_code=e.get_http_status(),
            content=error_response(code=e.code, message=e.message).dict()
        )
    except Exception as e:
        logger.error(f"更新文化标签异常: {str(e)}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=error_response(
                code=ErrorCode.SYSTEM_ERROR,
                message="系统错误"
            ).dict()
        )


# ============ 删除标签 ============

@router.delete("/cultural-tags/{tag_id}", response_model=dict, tags=["文化标签"])
async def delete_tag(
    tag_id: int,
    current_user: dict = Depends(require_admin),
    db: Session = Depends(get_db)
) -> dict:
    """删除文化标签（仅管理员）

    如果标签被产品使用，则软删除（设置is_active=False）
    否则硬删除

    参数:
        tag_id: 标签ID
        current_user: 当前用户（需要管理员权限）
        db: 数据库会话

    返回:
        删除结果
    """
    try:
        service = CulturalTagService(db)
        service.delete_tag(tag_id)

        return success_response(
            data={"id": tag_id},
            message="文化标签删除成功"
        ).dict()

    except BusinessException as e:
        logger.warning(f"删除文化标签失败: {e.message}")
        return JSONResponse(
            status_code=e.get_http_status(),
            content=error_response(code=e.code, message=e.message).dict()
        )
    except Exception as e:
        logger.error(f"删除文化标签异常: {str(e)}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=error_response(
                code=ErrorCode.SYSTEM_ERROR,
                message="系统错误"
            ).dict()
        )
