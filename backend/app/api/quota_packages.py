"""
配额套餐API路由

版本: 1.0
创建日期: 2026-01-23

端点:
- GET /api/v1/quota-packages - 获取套餐列表
- GET /api/v1/quota-packages/{id} - 获取套餐详情
"""

from fastapi import APIRouter, Depends, Query, HTTPException, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from loguru import logger
from typing import Optional, List

from app.schemas.quota_packages import (
    QuotaPackageListItemResponse,
    QuotaPackageDetailResponse
)
from app.services.quota_package_service import QuotaPackageService
from app.core.errors import BusinessException, ErrorCode
from app.core.responses import success_response, error_response
from app.api.deps import get_db, get_optional_user

# 创建路由器
router = APIRouter()


@router.get("/quota-packages", response_model=dict, tags=["配额套餐"])
async def list_quota_packages(
    is_active: Optional[bool] = Query(None, description="是否启用"),
    package_type: Optional[str] = Query(None, description="套餐类型"),
    period: Optional[str] = Query(None, description="套餐周期"),
    db: Session = Depends(get_db)
) -> dict:
    """获取配额套餐列表

    路径: GET /api/v1/quota-packages

    参数:
        is_active: 是否启用(默认返回所有)
        package_type: 套餐类型(basic/standard/professional/enterprise)
        period: 套餐周期(monthly/quarterly/yearly/lifetime)

    返回:
        套餐列表
    """
    try:
        service = QuotaPackageService(db)
        packages = service.list_packages(
            is_active=is_active,
            package_type=package_type,
            period=period
        )

        # 转换为响应对象
        items = []
        for package in packages:
            item_dict = {
                "id": package.id,
                "name": package.name,
                "package_type": package.package_type.value if package.package_type else None,
                "period": package.period.value if package.period else None,
                "price": str(package.price) if package.price is not None else "0",
                "original_price": str(package.original_price) if package.original_price is not None else None,
                "discount_percentage": package.get_discount_percentage(),
                "chat_quota": package.chat_quota,
                "generation_quota": package.generation_quota,
                "token_quota": package.token_quota,
                "storage_quota_mb": package.storage_quota_mb,
                "validity_days": package.validity_days,
                "is_active": package.is_active,
                "is_recommended": package.is_recommended,
                "sort_order": package.sort_order,
                "created_at": package.created_at.isoformat() if package.created_at else None
            }
            items.append(item_dict)

        return success_response(
            data={"items": items, "total": len(items)},
            message="获取套餐列表成功"
        ).model_dump(mode='json')

    except BusinessException as e:
        logger.error(f"获取套餐列表失败: {e.message}")
        return JSONResponse(
            status_code=e.get_http_status(),
            content=error_response(
                code=e.code,
                message=e.message
            ).model_dump(mode='json')
        )
    except Exception as e:
        logger.error(f"获取套餐列表异常: {str(e)}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=error_response(
                code=ErrorCode.SYSTEM_ERROR,
                message="系统错误"
            ).model_dump(mode='json')
        )


@router.get("/quota-packages/{package_id}", response_model=dict, tags=["配额套餐"])
async def get_quota_package(
    package_id: int,
    db: Session = Depends(get_db)
) -> dict:
    """获取配额套餐详情

    路径: GET /api/v1/quota-packages/{package_id}

    参数:
        package_id: 套餐ID

    返回:
        套餐详细信息
    """
    try:
        service = QuotaPackageService(db)
        package = service.get_package_by_id(package_id)

        # 转换为响应对象
        response_data = {
            "id": package.id,
            "name": package.name,
            "package_type": package.package_type.value if package.package_type else None,
            "period": package.period.value if package.period else None,
            "price": str(package.price) if package.price is not None else "0",
            "original_price": str(package.original_price) if package.original_price is not None else None,
            "discount_percentage": package.get_discount_percentage(),
            "quotas": {
                "chat": package.chat_quota,
                "generation": package.generation_quota,
                "token": package.token_quota,
                "storage_mb": package.storage_quota_mb
            },
            "validity_days": package.validity_days,
            "description": package.description,
            "features": package.features,
            "is_active": package.is_active,
            "is_recommended": package.is_recommended,
            "sort_order": package.sort_order,
            "created_at": package.created_at.isoformat() if package.created_at else None,
            "updated_at": package.updated_at.isoformat() if package.updated_at else None
        }

        return success_response(
            data=response_data,
            message="获取套餐详情成功"
        ).model_dump(mode='json')

    except BusinessException as e:
        logger.warning(f"获取套餐详情失败: {e.message}")
        return JSONResponse(
            status_code=e.get_http_status(),
            content=error_response(
                code=e.code,
                message=e.message
            ).model_dump(mode='json')
        )
    except Exception as e:
        logger.error(f"获取套餐详情异常: {str(e)}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=error_response(
                code=ErrorCode.SYSTEM_ERROR,
                message="系统错误"
            ).model_dump(mode='json')
        )
