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


def _parse_date_range(
    start_date: Optional[str],
    end_date: Optional[str]
) -> tuple:
    """解析并验证时间范围参数，返回 (start_datetime, end_datetime) 或抛出 ValueError。

    返回:
        (start_datetime, end_datetime) — 均可为 None
    异常:
        ValueError: 格式错误或 start > end
    """
    start_datetime = None
    end_datetime = None

    if start_date:
        start_datetime = datetime.fromisoformat(start_date.replace('Z', '+00:00'))

    if end_date:
        end_datetime = datetime.fromisoformat(end_date.replace('Z', '+00:00'))

    if start_datetime and end_datetime and start_datetime > end_datetime:
        raise ValueError("开始日期不能晚于结束日期")

    return start_datetime, end_datetime


@router.get("/", response_model=dict, tags=["审计日志"])
async def list_audit_logs(
    user_id: Optional[int] = Query(None, description="用户ID"),
    username: Optional[str] = Query(None, max_length=100, description="用户名（模糊搜索）"),
    action: Optional[str] = Query(None, max_length=50, description="操作类型"),
    resource: Optional[str] = Query(None, max_length=50, description="资源类型"),
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
    """
    try:
        # 解析并验证日期范围
        try:
            start_datetime, end_datetime = _parse_date_range(start_date, end_date)
        except ValueError as e:
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content=error_response(
                    code=ErrorCode.INVALID_PARAMS,
                    message=str(e) if str(e) else "日期格式不正确，请使用ISO格式"
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
                message="查询失败"
            ).dict()
        )


@router.get("/stats", response_model=dict, tags=["审计日志"])
async def get_audit_statistics(
    start_date: Optional[str] = Query(None, description="开始日期（ISO格式）"),
    end_date: Optional[str] = Query(None, description="结束日期（ISO格式）"),
    current_user: dict = Depends(require_admin),
    db: Session = Depends(get_db)
) -> dict:
    """
    获取审计日志统计信息

    需要管理员权限
    """
    try:
        # 解析并验证日期范围
        try:
            start_datetime, end_datetime = _parse_date_range(start_date, end_date)
        except ValueError as e:
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content=error_response(
                    code=ErrorCode.INVALID_PARAMS,
                    message=str(e) if str(e) else "日期格式不正确，请使用ISO格式"
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
                message="统计失败"
            ).dict()
        )


@router.get("/export", tags=["审计日志"])
async def export_audit_logs(
    format: str = Query("json", pattern="^(json|csv)$", description="导出格式（json/csv）"),
    user_id: Optional[int] = Query(None, description="用户ID"),
    action: Optional[str] = Query(None, max_length=50, description="操作类型"),
    resource: Optional[str] = Query(None, max_length=50, description="资源类型"),
    start_date: Optional[str] = Query(None, description="开始日期（ISO格式）"),
    end_date: Optional[str] = Query(None, description="结束日期（ISO格式）"),
    limit: int = Query(5000, ge=1, le=10000, description="最大导出数量（上限10000）"),
    current_user: dict = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    导出审计日志

    需要管理员权限
    """
    try:
        # 解析并验证日期范围
        try:
            start_datetime, end_datetime = _parse_date_range(start_date, end_date)
        except ValueError as e:
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content=error_response(
                    code=ErrorCode.INVALID_PARAMS,
                    message=str(e) if str(e) else "日期格式不正确，请使用ISO格式"
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
                message="导出失败"
            ).dict()
        )


@router.get("/user/{user_id}", response_model=dict, tags=["审计日志"])
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
                message="查询失败"
            ).dict()
        )


@router.get("/resource/{resource}/{resource_id}", response_model=dict, tags=["审计日志"])
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
                message="查询失败"
            ).dict()
        )


@router.get("/action-types", response_model=dict, tags=["审计日志"])
async def get_action_types(current_user: dict = Depends(get_current_user)):
    """获取可用的操作类型列表"""
    return success_response(
        data=[
            {"value": "login", "label": "登录"},
            {"value": "logout", "label": "登出"},
            {"value": "create", "label": "创建"},
            {"value": "update", "label": "更新"},
            {"value": "delete", "label": "删除"},
            {"value": "export", "label": "导出"},
            {"value": "import", "label": "导入"},
            {"value": "query", "label": "查询"},
            {"value": "config_change", "label": "配置变更"},
            {"value": "permission_change", "label": "权限变更"},
        ],
        message="获取操作类型成功"
    ).dict()


@router.get("/resource-types", response_model=dict, tags=["审计日志"])
async def get_resource_types(current_user: dict = Depends(get_current_user)):
    """获取可用的资源类型列表"""
    return success_response(
        data=[
            {"value": "user", "label": "用户"},
            {"value": "enterprise", "label": "企业"},
            {"value": "product", "label": "产品"},
            {"value": "order", "label": "订单"},
            {"value": "quota", "label": "配额"},
            {"value": "ai_config", "label": "AI配置"},
            {"value": "content", "label": "内容"},
            {"value": "billing", "label": "计费"},
            {"value": "system", "label": "系统"},
        ],
        message="获取资源类型成功"
    ).dict()


@router.get("/{log_id}", response_model=dict, tags=["审计日志"])
async def get_audit_log(
    log_id: int,
    current_user: dict = Depends(require_admin),
    db: Session = Depends(get_db)
) -> dict:
    """
    获取审计日志详情

    需要管理员权限
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
                message="查询失败"
            ).dict()
        )
