"""
产品管理API路由

版本: 1.0
更新日期: 2026-01-17

端点：
- GET /api/v1/products - 获取产品列表
- GET /api/v1/products/{id} - 获取产品详情
- POST /api/v1/products - 创建产品（管理员）
- PUT /api/v1/products/{id} - 更新产品（管理员）
- DELETE /api/v1/products/{id} - 删除产品（管理员）
- GET /api/v1/products/{id}/cultural-info - 获取产品文化信息
"""

from fastapi import APIRouter, Depends, Query, HTTPException, status, UploadFile, File
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from loguru import logger
from typing import Optional, List

from app.schemas.products import (
    ProductCreateRequest,
    ProductUpdateRequest,
    ProductListQuery,
    ProductDetailResponse,
    ProductListItemResponse,
    CulturalInfoResponse,
    ProductStatus
)
from pydantic import BaseModel
from typing import List as TypingList, Dict, Any
from app.services.product_service import ProductService
from app.services.file_service import FileService
from app.core.errors import BusinessException, ErrorCode
from app.core.responses import (
    success_response,
    error_response,
    paginated_response
)
from app.api.deps import get_db, require_admin, get_current_user, get_optional_user

# 创建路由器
router = APIRouter()


# ============ 辅助端点 ============

# 注意：这些端点使用查询参数来避免与 /products/{product_id} 路由冲突
# 前端需要调用 /products?action=categories 而不是 /products/categories

@router.get("/products-categories", response_model=dict, tags=["产品"])
async def get_categories(
    db: Session = Depends(get_db)
) -> dict:
    """获取所有产品类别

    路径: GET /api/v1/products-categories

    返回:
        类别列表
    """
    try:
        service = ProductService(db)
        categories = service.get_categories()

        return success_response(
            data={"categories": categories},
            message="获取类别列表成功"
        ).dict()

    except Exception as e:
        logger.error(f"获取类别列表异常: {str(e)}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=error_response(
                code=ErrorCode.SYSTEM_ERROR,
                message="系统错误"
            ).dict()
        )


@router.get("/products-popular", response_model=dict, tags=["产品"])
async def get_popular_products(
    limit: int = Query(10, ge=1, le=50, description="返回数量"),
    db: Session = Depends(get_db)
) -> dict:
    """获取热门产品（按浏览次数排序）

    路径: GET /api/v1/products-popular?limit=10

    参数:
        limit: 返回数量（默认10，最大50）

    返回:
        热门产品列表
    """
    try:
        service = ProductService(db)
        products = service.get_popular_products(limit=limit)

        # 转换为响应对象
        items = [ProductListItemResponse.from_orm(p) for p in products]

        return success_response(
            data={"items": [item.dict() for item in items]},
            message="获取热门产品成功"
        ).dict()

    except Exception as e:
        logger.error(f"获取热门产品异常: {str(e)}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=error_response(
                code=ErrorCode.SYSTEM_ERROR,
                message="系统错误"
            ).dict()
        )


@router.get("/products-regions", response_model=dict, tags=["产品"])
async def get_regions(
    db: Session = Depends(get_db)
) -> dict:
    """获取所有产地区域

    路径: GET /api/v1/products-regions

    返回:
        地区列表
    """
    try:
        service = ProductService(db)
        regions = service.get_regions()

        return success_response(
            data={"regions": regions},
            message="获取地区列表成功"
        ).dict()

    except Exception as e:
        logger.error(f"获取地区列表异常: {str(e)}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=error_response(
                code=ErrorCode.SYSTEM_ERROR,
                message="系统错误"
            ).dict()
        )


@router.get("/products-statistics", response_model=dict, tags=["产品"])
async def get_statistics(
    db: Session = Depends(get_db)
) -> dict:
    """获取产品统计信息

    路径: GET /api/v1/products-statistics

    返回:
        统计数据
    """
    try:
        service = ProductService(db)
        stats = service.get_product_statistics()

        return success_response(
            data=stats,
            message="获取统计信息成功"
        ).dict()

    except Exception as e:
        logger.error(f"获取统计信息异常: {str(e)}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=error_response(
                code=ErrorCode.SYSTEM_ERROR,
                message="系统错误"
            ).dict()
        )


# ============ 列表查询 ============

@router.get("/products", response_model=dict, tags=["产品"])
async def list_products(
    page: int = Query(1, ge=1, description="页码"),
    size: int = Query(10, ge=1, le=100, description="每页数量"),
    search: Optional[str] = Query(None, max_length=100, description="搜索关键词"),
    category: Optional[str] = Query(None, max_length=100, description="产品类别"),
    region: Optional[str] = Query(None, max_length=100, description="产地区域"),
    status: Optional[str] = Query(None, description="产品状态"),
    is_featured: Optional[bool] = Query(None, description="是否精选"),
    sort_by: str = Query("created_at", description="排序字段"),
    sort_order: str = Query("desc", description="排序顺序"),
    db: Session = Depends(get_db)
) -> dict:
    """获取产品列表 (分页、搜索、筛选)

    支持:
    - 分页: page, size
    - 搜索: search (名称、SKU)
    - 筛选: category, region, status, is_featured
    - 排序: sort_by, sort_order

    返回:
        产品列表和分页信息
    """
    try:
        # 参数验证
        if sort_by not in ['created_at', 'price', 'name', 'updated_at']:
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content=error_response(
                    code=ErrorCode.PARAM_VALUE_INVALID,
                    message="排序字段不支持"
                ).dict()
            )

        if sort_order not in ['asc', 'desc']:
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content=error_response(
                    code=ErrorCode.PARAM_VALUE_INVALID,
                    message="排序顺序不支持"
                ).dict()
            )

        # 创建服务实例
        service = ProductService(db)

        # 查询产品
        products, total = service.list_products(
            page=page,
            size=size,
            search=search,
            category=category,
            region=region,
            status=status,
            is_featured=is_featured,
            sort_by=sort_by,
            sort_order=sort_order
        )

        # 转换为响应对象
        items = [ProductListItemResponse.from_orm(p) for p in products]

        # 返回分页响应
        response = paginated_response(
            items=[item.dict() for item in items],
            page=page,
            size=size,
            total=total,
            message="获取产品列表成功"
        )

        return response.dict()

    except BusinessException as e:
        logger.error(f"获取产品列表失败: {e.message}")
        return JSONResponse(
            status_code=e.get_http_status(),
            content=error_response(
                code=e.code,
                message=e.message
            ).dict()
        )
    except Exception as e:
        logger.error(f"获取产品列表异常: {str(e)}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=error_response(
                code=ErrorCode.SYSTEM_ERROR,
                message="系统错误"
            ).dict()
        )


# ============ 获取详情 ============

@router.get("/products/{product_id}", response_model=dict, tags=["产品"])
async def get_product(
    product_id: int,
    db: Session = Depends(get_db)
) -> dict:
    """获取产品详情

    参数:
        product_id: 产品ID

    返回:
        产品详细信息
    """
    try:
        service = ProductService(db)
        product = service.get_product_by_id(product_id)

        # 转换为响应对象
        response_data = ProductDetailResponse.from_orm(product)

        return success_response(
            data=response_data.dict(),
            message="获取产品详情成功"
        ).dict()

    except BusinessException as e:
        logger.warning(f"获取产品详情失败: {e.message}")
        return JSONResponse(
            status_code=e.get_http_status(),
            content=error_response(
                code=e.code,
                message=e.message
            ).dict()
        )
    except Exception as e:
        logger.error(f"获取产品详情异常: {str(e)}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=error_response(
                code=ErrorCode.SYSTEM_ERROR,
                message="系统错误"
            ).dict()
        )


# ============ 获取文化信息 ============

@router.get("/products/{product_id}/cultural-info", response_model=dict, tags=["产品"])
async def get_cultural_info(
    product_id: int,
    db: Session = Depends(get_db)
) -> dict:
    """获取产品文化信息

    参数:
        product_id: 产品ID

    返回:
        产品文化信息
    """
    try:
        service = ProductService(db)
        product = service.get_product_by_id(product_id)

        # 构建文化信息响应（映射模型字段到响应字段）
        cultural_info = CulturalInfoResponse(
            cultural_tags=product.cultural_tags,
            cultural_story=product.cultural_story,
            historical_origin=product.historical_origin,
            origin_province=product.origin_province,
            origin_city=product.origin_city,
            origin_district=product.origin_district
        )

        return success_response(
            data=cultural_info.dict(),
            message="获取文化信息成功"
        ).dict()

    except BusinessException as e:
        logger.warning(f"获取文化信息失败: {e.message}")
        return JSONResponse(
            status_code=e.get_http_status(),
            content=error_response(
                code=e.code,
                message=e.message
            ).dict()
        )
    except Exception as e:
        logger.error(f"获取文化信息异常: {str(e)}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=error_response(
                code=ErrorCode.SYSTEM_ERROR,
                message="系统错误"
            ).dict()
        )


# ============ 创建产品 ============

@router.post("/products", response_model=dict, tags=["产品"])
async def create_product(
    request: ProductCreateRequest,
    current_user: dict = Depends(require_admin),
    db: Session = Depends(get_db)
) -> dict:
    """创建产品 (仅管理员)

    参数:
        request: 产品创建请求
        current_user: 当前用户（需要管理员权限）
        db: 数据库会话

    返回:
        创建的产品信息
    """
    try:
        from app.models import User

        service = ProductService(db)
        # 从current_user中获取数据库用户ID
        user = db.query(User).filter(User.user_uuid == current_user["user_id"]).first()
        if not user:
            return JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                content=error_response(
                    code=ErrorCode.USER_NOT_FOUND,
                    message="用户不存在"
                ).dict()
            )

        product = service.create_product(request, user.id)

        # 转换为响应对象
        response_data = ProductDetailResponse.from_orm(product)

        return JSONResponse(
            status_code=status.HTTP_201_CREATED,
            content=success_response(
                data=response_data.dict(),
                message="产品创建成功"
            ).dict()
        )

    except BusinessException as e:
        logger.warning(f"产品创建失败: {e.message}")
        return JSONResponse(
            status_code=e.get_http_status(),
            content=error_response(
                code=e.code,
                message=e.message
            ).dict()
        )
    except Exception as e:
        logger.error(f"产品创建异常: {str(e)}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=error_response(
                code=ErrorCode.SYSTEM_ERROR,
                message="系统错误"
            ).dict()
        )


# ============ 更新产品 ============

@router.put("/products/{product_id}", response_model=dict, tags=["产品"])
async def update_product(
    product_id: int,
    request: ProductUpdateRequest,
    current_user: dict = Depends(require_admin),
    db: Session = Depends(get_db)
) -> dict:
    """更新产品 (仅管理员)

    参数:
        product_id: 产品ID
        request: 产品更新请求
        current_user: 当前用户（需要管理员权限）
        db: 数据库会话

    返回:
        更新后的产品信息
    """
    try:
        # 验证请求体不为空
        if not request.dict(exclude_unset=True):
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content=error_response(
                    code=ErrorCode.PARAM_ERROR,
                    message="请求体不能为空"
                ).dict()
            )

        from app.models import User

        service = ProductService(db)
        # 从current_user中获取数据库用户ID
        user = db.query(User).filter(User.user_uuid == current_user["user_id"]).first()
        if not user:
            return JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                content=error_response(
                    code=ErrorCode.USER_NOT_FOUND,
                    message="用户不存在"
                ).dict()
            )

        product = service.update_product(product_id, request, user.id)

        # 转换为响应对象
        response_data = ProductDetailResponse.from_orm(product)

        return success_response(
            data=response_data.dict(),
            message="产品更新成功"
        ).dict()

    except BusinessException as e:
        logger.warning(f"产品更新失败: {e.message}")
        return JSONResponse(
            status_code=e.get_http_status(),
            content=error_response(
                code=e.code,
                message=e.message
            ).dict()
        )
    except Exception as e:
        logger.error(f"产品更新异常: {str(e)}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=error_response(
                code=ErrorCode.SYSTEM_ERROR,
                message="系统错误"
            ).dict()
        )


# ============ 删除产品 ============

@router.delete("/products/{product_id}", response_model=dict, tags=["产品"])
async def delete_product(
    product_id: int,
    current_user: dict = Depends(require_admin),
    db: Session = Depends(get_db)
) -> dict:
    """删除产品 (仅管理员)

    参数:
        product_id: 产品ID
        current_user: 当前用户（需要管理员权限）
        db: 数据库会话

    返回:
        删除结果
    """
    try:
        service = ProductService(db)
        service.delete_product(product_id)

        return success_response(
            data={"id": product_id},
            message="产品删除成功"
        ).dict()

    except BusinessException as e:
        logger.warning(f"产品删除失败: {e.message}")
        return JSONResponse(
            status_code=e.get_http_status(),
            content=error_response(
                code=e.code,
                message=e.message
            ).dict()
        )
    except Exception as e:
        logger.error(f"产品删除异常: {str(e)}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=error_response(
                code=ErrorCode.SYSTEM_ERROR,
                message="系统错误"
            ).dict()
        )


# ============ 产品图片上传 (BUG-024修复) ============

@router.post("/products/{product_id}/images", response_model=dict, tags=["产品"])
async def upload_product_image(
    product_id: int,
    file: UploadFile = File(..., description="产品图片文件"),
    current_user: dict = Depends(require_admin),
    db: Session = Depends(get_db)
) -> dict:
    """上传产品图片（仅管理员）

    参数:
        product_id: 产品ID
        file: 图片文件（支持 JPG, PNG, GIF, WEBP）
        current_user: 当前用户（需要管理员权限）
        db: 数据库会话

    返回:
        图片URL

    示例:
        POST /api/v1/products/1/images
        Content-Type: multipart/form-data

        file: <binary data>
    """
    try:
        from app.models.product import Product

        # 验证产品是否存在
        service = ProductService(db)
        product = service.get_product_by_id(product_id)

        # 上传图片
        image_url = await FileService.upload_product_image(file, product_id)

        # 更新产品图片（使用image_urls JSON字段）
        if product.image_urls:
            # 如果已有图片，添加到列表
            images = product.image_urls if isinstance(product.image_urls, list) else []
            images.append(image_url)
            product.image_urls = images
        else:
            # 如果没有图片，直接设置
            product.image_urls = [image_url]

        # 如果没有主图，设置为主图
        if not product.main_image_url:
            product.main_image_url = image_url

        db.commit()
        db.refresh(product)

        return success_response(
            data={"image_url": image_url, "all_images": product.image_urls or []},
            message="产品图片上传成功"
        ).dict()

    except BusinessException as e:
        logger.warning(f"产品图片上传失败: {e.message}")
        return JSONResponse(
            status_code=e.get_http_status(),
            content=error_response(
                code=e.code,
                message=e.message
            ).dict()
        )
    except Exception as e:
        logger.error(f"产品图片上传异常: {str(e)}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=error_response(
                code=ErrorCode.SYSTEM_ERROR,
                message=f"产品图片上传失败: {str(e)}"
            ).dict()
        )


@router.delete("/products/{product_id}/images", response_model=dict, tags=["产品"])
async def delete_product_image(
    product_id: int,
    image_url: str = Query(..., description="要删除的图片URL"),
    current_user: dict = Depends(require_admin),
    db: Session = Depends(get_db)
) -> dict:
    """删除产品图片（仅管理员）

    参数:
        product_id: 产品ID
        image_url: 图片URL
        current_user: 当前用户（需要管理员权限）
        db: 数据库会话

    返回:
        删除结果
    """
    try:
        from app.models.product import Product

        # 验证产品是否存在
        service = ProductService(db)
        product = service.get_product_by_id(product_id)

        if not product.image_urls:
            return JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                content=error_response(
                    code=ErrorCode.RECORD_NOT_FOUND,
                    message="产品没有图片"
                ).dict()
            )

        # 从产品图片列表中移除
        images = product.image_urls if isinstance(product.image_urls, list) else []
        if image_url not in images:
            return JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                content=error_response(
                    code=ErrorCode.RECORD_NOT_FOUND,
                    message="图片不存在"
                ).dict()
            )

        images.remove(image_url)
        product.image_urls = images if images else None

        # 如果删除的是主图，更新主图
        if product.main_image_url == image_url:
            product.main_image_url = images[0] if images else None

        # 删除文件
        if image_url.startswith("/uploads"):
            filepath = image_url.lstrip("/")
            FileService.delete_file(filepath)

        db.commit()

        return success_response(
            data={"remaining_images": images},
            message="产品图片删除成功"
        ).dict()

    except BusinessException as e:
        logger.warning(f"产品图片删除失败: {e.message}")
        return JSONResponse(
            status_code=e.get_http_status(),
            content=error_response(
                code=e.code,
                message=e.message
            ).dict()
        )
    except Exception as e:
        logger.error(f"产品图片删除异常: {str(e)}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=error_response(
                code=ErrorCode.SYSTEM_ERROR,
                message="产品图片删除失败"
            ).dict()
        )


# ============ 批量操作 (BUG-027修复) ============

class BatchDeleteRequest(BaseModel):
    """批量删除请求"""
    ids: TypingList[int]

class BatchUpdateRequest(BaseModel):
    """批量更新请求"""
    ids: TypingList[int]
    data: Dict[str, Any]


@router.post("/products/batch-delete", response_model=dict, tags=["产品"])
async def batch_delete_products(
    request: BatchDeleteRequest,
    current_user: dict = Depends(require_admin),
    db: Session = Depends(get_db)
) -> dict:
    """批量删除产品（仅管理员）

    参数:
        request: 批量删除请求（包含产品ID列表）
        current_user: 当前用户（需要管理员权限）
        db: 数据库会话

    返回:
        删除结果

    示例:
        POST /api/v1/products/batch-delete
        {
            "ids": [1, 2, 3, 4, 5]
        }
    """
    try:
        from app.models.product import Product
        from datetime import datetime

        if not request.ids:
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content=error_response(
                    code=ErrorCode.PARAM_ERROR,
                    message="产品ID列表不能为空"
                ).dict()
            )

        # 硬删除产品
        deleted_count = db.query(Product)\
            .filter(Product.id.in_(request.ids))\
            .delete(synchronize_session=False)

        db.commit()

        logger.info(f"批量删除产品成功: ids={request.ids}, count={deleted_count}")

        return success_response(
            data={
                "deleted_count": deleted_count,
                "requested_ids": request.ids
            },
            message=f"成功删除 {deleted_count} 个产品"
        ).dict()

    except Exception as e:
        logger.error(f"批量删除产品异常: {str(e)}")
        db.rollback()
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=error_response(
                code=ErrorCode.SYSTEM_ERROR,
                message=f"批量删除失败: {str(e)}"
            ).dict()
        )


@router.put("/products/batch-update", response_model=dict, tags=["产品"])
async def batch_update_products(
    request: BatchUpdateRequest,
    current_user: dict = Depends(require_admin),
    db: Session = Depends(get_db)
) -> dict:
    """批量更新产品（仅管理员）

    参数:
        request: 批量更新请求（包含产品ID列表和更新数据）
        current_user: 当前用户（需要管理员权限）
        db: 数据库会话

    返回:
        更新结果

    示例:
        PUT /api/v1/products/batch-update
        {
            "ids": [1, 2, 3],
            "data": {
                "status": "inactive",
                "is_featured": false
            }
        }
    """
    try:
        from app.models.product import Product
        from datetime import datetime

        if not request.ids:
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content=error_response(
                    code=ErrorCode.PARAM_ERROR,
                    message="产品ID列表不能为空"
                ).dict()
            )

        if not request.data:
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content=error_response(
                    code=ErrorCode.PARAM_ERROR,
                    message="更新数据不能为空"
                ).dict()
            )

        # 允许批量更新的字段白名单
        allowed_fields = ['status', 'is_featured', 'category', 'region', 'price']
        update_data = {}

        for key, value in request.data.items():
            if key in allowed_fields:
                update_data[key] = value

        if not update_data:
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content=error_response(
                    code=ErrorCode.PARAM_ERROR,
                    message=f"没有可更新的字段。允许的字段: {', '.join(allowed_fields)}"
                ).dict()
            )

        # 添加更新时间
        update_data['updated_at'] = datetime.utcnow()

        # 执行批量更新
        updated_count = db.query(Product)\
            .filter(Product.id.in_(request.ids))\
            .update(update_data, synchronize_session=False)

        db.commit()

        logger.info(f"批量更新产品成功: ids={request.ids}, data={update_data}, count={updated_count}")

        return success_response(
            data={
                "updated_count": updated_count,
                "requested_ids": request.ids,
                "update_fields": list(update_data.keys())
            },
            message=f"成功更新 {updated_count} 个产品"
        ).dict()

    except Exception as e:
        logger.error(f"批量更新产品异常: {str(e)}")
        db.rollback()
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=error_response(
                code=ErrorCode.SYSTEM_ERROR,
                message=f"批量更新失败: {str(e)}"
            ).dict()
        )


# ============ 产品标签管理 (BE-007新增) ============

@router.post("/products/{product_id}/tags", response_model=dict, tags=["产品"])
async def assign_tags_to_product(
    product_id: int,
    tag_ids: List[int],
    current_user: dict = Depends(require_admin),
    db: Session = Depends(get_db)
) -> dict:
    """为产品分配文化标签（仅管理员）

    参数:
        product_id: 产品ID
        tag_ids: 标签ID列表
        current_user: 当前用户（需要管理员权限）
        db: 数据库会话

    返回:
        更新后的产品标签列表

    示例:
        POST /api/v1/products/1/tags
        {
            "tag_ids": [1, 2, 3]
        }
    """
    try:
        from app.services.cultural_tag_service import CulturalTagService
        from app.schemas.cultural_tags import CulturalTagListItemResponse

        if not tag_ids:
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content=error_response(
                    code=ErrorCode.PARAM_ERROR,
                    message="标签ID列表不能为空"
                ).dict()
            )

        # 验证标签ID列表唯一性
        if len(tag_ids) != len(set(tag_ids)):
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content=error_response(
                    code=ErrorCode.PARAM_ERROR,
                    message="标签ID列表中存在重复"
                ).dict()
            )

        service = CulturalTagService(db)
        product = service.assign_tags_to_product(product_id, tag_ids)

        # 转换为响应对象
        tags_response = [CulturalTagListItemResponse.from_orm(tag).dict() for tag in product.tags]

        return success_response(
            data={
                "product_id": product_id,
                "tags": tags_response
            },
            message="产品标签分配成功"
        ).dict()

    except BusinessException as e:
        logger.warning(f"产品标签分配失败: {e.message}")
        return JSONResponse(
            status_code=e.get_http_status(),
            content=error_response(
                code=e.code,
                message=e.message
            ).dict()
        )
    except Exception as e:
        logger.error(f"产品标签分配异常: {str(e)}")
        db.rollback()
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=error_response(
                code=ErrorCode.SYSTEM_ERROR,
                message=f"产品标签分配失败: {str(e)}"
            ).dict()
        )


@router.delete("/products/{product_id}/tags/{tag_id}", response_model=dict, tags=["产品"])
async def remove_tag_from_product(
    product_id: int,
    tag_id: int,
    current_user: dict = Depends(require_admin),
    db: Session = Depends(get_db)
) -> dict:
    """从产品移除文化标签（仅管理员）

    参数:
        product_id: 产品ID
        tag_id: 标签ID
        current_user: 当前用户（需要管理员权限）
        db: 数据库会话

    返回:
        移除结果
    """
    try:
        from app.services.cultural_tag_service import CulturalTagService
        from app.schemas.cultural_tags import CulturalTagListItemResponse

        service = CulturalTagService(db)
        product = service.remove_tag_from_product(product_id, tag_id)

        # 转换为响应对象
        tags_response = [CulturalTagListItemResponse.from_orm(tag).dict() for tag in product.tags]

        return success_response(
            data={
                "product_id": product_id,
                "remaining_tags": tags_response
            },
            message="产品标签移除成功"
        ).dict()

    except BusinessException as e:
        logger.warning(f"产品标签移除失败: {e.message}")
        return JSONResponse(
            status_code=e.get_http_status(),
            content=error_response(
                code=e.code,
                message=e.message
            ).dict()
        )
    except Exception as e:
        logger.error(f"产品标签移除异常: {str(e)}")
        db.rollback()
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=error_response(
                code=ErrorCode.SYSTEM_ERROR,
                message="产品标签移除失败"
            ).dict()
        )


@router.get("/products/{product_id}/tags", response_model=dict, tags=["产品"])
async def get_product_tags(
    product_id: int,
    db: Session = Depends(get_db)
) -> dict:
    """获取产品的所有文化标签

    参数:
        product_id: 产品ID
        db: 数据库会话

    返回:
        产品的标签列表
    """
    try:
        from app.services.cultural_tag_service import CulturalTagService
        from app.schemas.cultural_tags import CulturalTagListItemResponse

        service = CulturalTagService(db)
        tags = service.get_product_tags(product_id)

        # 转换为响应对象
        tags_response = [CulturalTagListItemResponse.from_orm(tag).dict() for tag in tags]

        return success_response(
            data={
                "product_id": product_id,
                "tags": tags_response
            },
            message="获取产品标签成功"
        ).dict()

    except BusinessException as e:
        logger.warning(f"获取产品标签失败: {e.message}")
        return JSONResponse(
            status_code=e.get_http_status(),
            content=error_response(
                code=e.code,
                message=e.message
            ).dict()
        )
    except Exception as e:
        logger.error(f"获取产品标签异常: {str(e)}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=error_response(
                code=ErrorCode.SYSTEM_ERROR,
                message="系统错误"
            ).dict()
        )
