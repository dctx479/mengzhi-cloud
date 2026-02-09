"""
审计日志API路由

提供审计日志的查询、统计和导出功能

版本: 1.0
创建日期: 2026-01-22
"""

from fastapi import APIRouter, Depends, Query, status
from fastapi.responses import JSONResponse, StreamingResponse
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime
import io

from app.api.deps import get_db, get_current_user, require_admin
from app.services.audit_service import AuditService
from app.core.responses import success_response, error_response
from app.core.errors import ErrorCode
from app.core.logging_config import logger

router = APIRouter()


@router.get("/audit-logs", response_model=dict, tags=["审计日志"])
async def list_audit_logs(
    user_id: Optional[int] = Query(None, description="用户ID"),
    username: Optional[str] = Query(None, description="用户名（模糊搜索）"),
    action: Optional[str] = Query(None, description="操作类型"),
    resource: Optional[str] = Query(None, description="资源类型"),
    resource_id: Optional[int] = Query(None, description="资源ID"),
    is_success: Optional[bool] = Query(None, description="是否成功"),
    start_date: Optional[str] = Query(None, description="开始日期（ISO格式）"),
    end_date: Optional[str] = Query(None, description="结束日期（ISO格式）"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    current_user: dict = Depends(require_admin),
    db: Session = Depends(get_db)
) -> dict:
    """
    获取审计日志列表

    需要管理员权限

    参数:
        user_id: 用户ID（可选）
        username: 用户名，支持模糊搜索（可选）
        action: 操作类型（可选）
        resource: 资源类型（可选）
        resource_id: 资源ID（可选）
        is_success: 是否成功（可选）
        start_date: 开始日期（可选）
        end_date: 结束日期（可选）
        page: 页码，默认1
        page_size: 每页数量，默认20，最大100

    返回:
        审计日志列表和分页信息

    示例:
        GET /api/audit-logs?action=login&page=1&page_size=20
        GET /api/audit-logs?username=admin&start_date=2026-01-01T00:00:00
    """
    try:
        # 解析日期
        start_datetime = None
        end_datetime = None

        if start_date:
            try:
                start_datetime = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
            except ValueError:
                return JSONResponse(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    content=error_response(
                        code=ErrorCode.INVALID_PARAMS,
                        message="开始日期格式不正确，请使用ISO格式"
                    ).dict()
                )

        if end_date:
            try:
                end_datetime = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
            except ValueError:
                return JSONResponse(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    content=error_response(
                        code=ErrorCode.INVALID_PARAMS,
                        message="结束日期格式不正确，请使用ISO格式"
                    ).dict()
                )

        # 查询日志
        result = AuditService.query_logs(
            db=db,
            user_id=user_id,
            username=username,
            action=action,
            resource=resource,
            resource_id=resource_id,
            is_success=is_success,
            start_date=start_datetime,
            end_date=end_datetime,
            page=page,
            page_size=page_size
        )

        return success_response(
            data=result,
            message="查询成功"
        ).dict()

    except Exception as e:
        logger.error(f"查询审计日志失败: {str(e)}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=error_response(
                code=ErrorCode.SYSTEM_ERROR,
                message=f"查询失败: {str(e)}"
            ).dict()
        )


@router.get("/audit-logs/{log_id}", response_model=dict, tags=["审计日志"])
async def get_audit_log(
    log_id: int,
    current_user: dict = Depends(require_admin),
    db: Session = Depends(get_db)
) -> dict:
    """
    获取审计日志详情

    需要管理员权限

    参数:
        log_id: 日志ID

    返回:
        审计日志详情

    示例:
        GET /api/audit-logs/123
    """
    try:
        log = AuditService.get_log_by_id(db, log_id)

        if not log:
            return JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                content=error_response(
                    code=ErrorCode.RECORD_NOT_FOUND,
                    message="审计日志不存在"
                ).dict()
            )

        return success_response(
            data=log,
            message="查询成功"
        ).dict()

    except Exception as e:
        logger.error(f"获取审计日志详情失败: {str(e)}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=error_response(
                code=ErrorCode.SYSTEM_ERROR,
                message=f"查询失败: {str(e)}"
            ).dict()
        )


@router.get("/audit-logs/stats/summary", response_model=dict, tags=["审计日志"])
async def get_audit_statistics(
    start_date: Optional[str] = Query(None, description="开始日期（ISO格式）"),
    end_date: Optional[str] = Query(None, description="结束日期（ISO格式）"),
    current_user: dict = Depends(require_admin),
    db: Session = Depends(get_db)
) -> dict:
    """
    获取审计日志统计信息

    需要管理员权限

    参数:
        start_date: 开始日期（可选）
        end_date: 结束日期（可选）

    返回:
        统计信息，包括：
        - 总操作数
        - 成功/失败数量和比率
        - 按操作类型统计
        - 按资源类型统计
        - 活跃用户TOP10

    示例:
        GET /api/audit-logs/stats/summary
        GET /api/audit-logs/stats/summary?start_date=2026-01-01T00:00:00&end_date=2026-01-31T23:59:59
    """
    try:
        # 解析日期
        start_datetime = None
        end_datetime = None

        if start_date:
            try:
                start_datetime = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
            except ValueError:
                return JSONResponse(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    content=error_response(
                        code=ErrorCode.INVALID_PARAMS,
                        message="开始日期格式不正确，请使用ISO格式"
                    ).dict()
                )

        if end_date:
            try:
                end_datetime = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
            except ValueError:
                return JSONResponse(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    content=error_response(
                        code=ErrorCode.INVALID_PARAMS,
                        message="结束日期格式不正确，请使用ISO格式"
                    ).dict()
                )

        # 获取统计信息
        stats = AuditService.get_statistics(
            db=db,
            start_date=start_datetime,
            end_date=end_datetime
        )

        return success_response(
            data=stats,
            message="统计成功"
        ).dict()

    except Exception as e:
        logger.error(f"获取审计日志统计失败: {str(e)}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=error_response(
                code=ErrorCode.SYSTEM_ERROR,
                message=f"统计失败: {str(e)}"
            ).dict()
        )


@router.get("/audit-logs/export", tags=["审计日志"])
async def export_audit_logs(
    format: str = Query("json", pattern="^(json|csv)$", description="导出格式（json/csv）"),
    user_id: Optional[int] = Query(None, description="用户ID"),
    action: Optional[str] = Query(None, description="操作类型"),
    resource: Optional[str] = Query(None, description="资源类型"),
    start_date: Optional[str] = Query(None, description="开始日期（ISO格式）"),
    end_date: Optional[str] = Query(None, description="结束日期（ISO格式）"),
    limit: int = Query(10000, ge=1, le=50000, description="最大导出数量"),
    current_user: dict = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    导出审计日志

    需要管理员权限

    参数:
        format: 导出格式，json或csv
        user_id: 用户ID（可选）
        action: 操作类型（可选）
        resource: 资源类型（可选）
        start_date: 开始日期（可选）
        end_date: 结束日期（可选）
        limit: 最大导出数量，默认10000，最大50000

    返回:
        JSON或CSV格式的审计日志数据

    示例:
        GET /api/audit-logs/export?format=csv&action=login
        GET /api/audit-logs/export?format=json&start_date=2026-01-01T00:00:00
    """
    try:
        # 解析日期
        start_datetime = None
        end_datetime = None

        if start_date:
            try:
                start_datetime = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
            except ValueError:
                return JSONResponse(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    content=error_response(
                        code=ErrorCode.INVALID_PARAMS,
                        message="开始日期格式不正确，请使用ISO格式"
                    ).dict()
                )

        if end_date:
            try:
                end_datetime = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
            except ValueError:
                return JSONResponse(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    content=error_response(
                        code=ErrorCode.INVALID_PARAMS,
                        message="结束日期格式不正确，请使用ISO格式"
                    ).dict()
                )

        # 导出日志
        result = AuditService.export_logs(
            db=db,
            format=format,
            user_id=user_id,
            action=action,
            resource=resource,
            start_date=start_datetime,
            end_date=end_datetime,
            limit=limit
        )

        if "error" in result:
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content=error_response(
                    code=ErrorCode.SYSTEM_ERROR,
                    message=f"导出失败: {result['error']}"
                ).dict()
            )

        # 根据格式返回不同的响应
        if format == "csv":
            # 返回CSV文件
            output = io.BytesIO(result["data"].encode("utf-8-sig"))  # 使用UTF-8 BOM以支持Excel
            return StreamingResponse(
                output,
                media_type="text/csv",
                headers={
                    "Content-Disposition": f"attachment; filename=audit_logs_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
                }
            )
        else:
            # 返回JSON
            return success_response(
                data={
                    "logs": result["data"],
                    "count": result["count"]
                },
                message="导出成功"
            ).dict()

    except Exception as e:
        logger.error(f"导出审计日志失败: {str(e)}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=error_response(
                code=ErrorCode.SYSTEM_ERROR,
                message=f"导出失败: {str(e)}"
            ).dict()
        )


@router.get("/audit-logs/user/{user_id}", response_model=dict, tags=["审计日志"])
async def get_user_audit_logs(
    user_id: int,
    action: Optional[str] = Query(None, description="操作类型"),
    resource: Optional[str] = Query(None, description="资源类型"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    current_user: dict = Depends(require_admin),
    db: Session = Depends(get_db)
) -> dict:
    """
    获取指定用户的审计日志

    需要管理员权限

    参数:
        user_id: 用户ID
        action: 操作类型（可选）
        resource: 资源类型（可选）
        page: 页码，默认1
        page_size: 每页数量，默认20，最大100

    返回:
        用户的审计日志列表

    示例:
        GET /api/audit-logs/user/123
        GET /api/audit-logs/user/123?action=update&resource=product
    """
    try:
        result = AuditService.query_logs(
            db=db,
            user_id=user_id,
            action=action,
            resource=resource,
            page=page,
            page_size=page_size
        )

        return success_response(
            data=result,
            message="查询成功"
        ).dict()

    except Exception as e:
        logger.error(f"查询用户审计日志失败: {str(e)}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=error_response(
                code=ErrorCode.SYSTEM_ERROR,
                message=f"查询失败: {str(e)}"
            ).dict()
        )


@router.get("/audit-logs/resource/{resource}/{resource_id}", response_model=dict, tags=["审计日志"])
async def get_resource_audit_logs(
    resource: str,
    resource_id: int,
    action: Optional[str] = Query(None, description="操作类型"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    current_user: dict = Depends(require_admin),
    db: Session = Depends(get_db)
) -> dict:
    """
    获取指定资源的审计日志

    需要管理员权限

    参数:
        resource: 资源类型
        resource_id: 资源ID
        action: 操作类型（可选）
        page: 页码，默认1
        page_size: 每页数量，默认20，最大100

    返回:
        资源的审计日志列表

    示例:
        GET /api/audit-logs/resource/product/123
        GET /api/audit-logs/resource/user/456?action=update
    """
    try:
        result = AuditService.query_logs(
            db=db,
            resource=resource,
            resource_id=resource_id,
            action=action,
            page=page,
            page_size=page_size
        )

        return success_response(
            data=result,
            message="查询成功"
        ).dict()

    except Exception as e:
        logger.error(f"查询资源审计日志失败: {str(e)}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=error_response(
                code=ErrorCode.SYSTEM_ERROR,
                message=f"查询失败: {str(e)}"
            ).dict()
        )
