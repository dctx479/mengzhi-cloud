"""
对账系统API接口

版本: 1.0
创建日期: 2026-01-23
"""

from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, status, Query, Path
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from datetime import datetime

from app.api.deps import get_db, get_current_user, require_admin
from app.models.user import User
from app.models.reconciliation import (
    ReconciliationRecord, ReconciliationDifference,
    ReconciliationStatus, ReconciliationType,
    DifferenceType, DifferenceStatus
)
from app.services.reconciliation_service import ReconciliationService
from app.core.errors import BusinessException, RecordNotFoundError, ErrorCode
from app.core.responses import success_response, error_response


router = APIRouter(tags=["对账系统"])


# ==================== 请求模型 ====================

class StartReconciliationRequest(BaseModel):
    """启动对账请求"""
    reconciliation_date: str = Field(..., description="对账日期 (YYYY-MM-DD)")
    reconciliation_type: ReconciliationType = Field(
        default=ReconciliationType.MANUAL,
        description="对账类型"
    )
    force: bool = Field(default=False, description="是否强制重新对账")


class FixDifferenceRequest(BaseModel):
    """修复差异请求"""
    action: str = Field(..., description="修复动作 (auto_supplement, manual_supplement, ignore)")
    remark: Optional[str] = Field(None, description="备注")


class ReconciliationRecordQuery(BaseModel):
    """对账记录查询参数"""
    page: int = Field(default=1, ge=1, description="页码")
    page_size: int = Field(default=20, ge=1, le=100, description="每页大小")
    status: Optional[ReconciliationStatus] = Field(None, description="对账状态")
    start_date: Optional[str] = Field(None, description="开始日期")
    end_date: Optional[str] = Field(None, description="结束日期")


class ReconciliationDifferenceQuery(BaseModel):
    """差异记录查询参数"""
    page: int = Field(default=1, ge=1, description="页码")
    page_size: int = Field(default=20, ge=1, le=100, description="每页大小")
    reconciliation_id: Optional[int] = Field(None, description="对账记录ID")
    status: Optional[DifferenceStatus] = Field(None, description="差异状态")
    difference_type: Optional[DifferenceType] = Field(None, description="差异类型")


# ==================== 响应模型 ====================

class ReconciliationRecordResponse(BaseModel):
    """对账记录响应"""
    id: int
    batch_no: str
    reconciliation_date: str
    reconciliation_type: str
    status: str
    start_time: Optional[str]
    end_time: Optional[str]
    statistics: dict
    execution: dict
    error_message: Optional[str]
    remark: Optional[str]
    created_at: str
    updated_at: str

    class Config:
        from_attributes = True


class ReconciliationDifferenceResponse(BaseModel):
    """差异记录响应"""
    id: int
    reconciliation_id: int
    difference_type: str
    status: str
    transaction_info: dict
    amount_info: dict
    status_info: dict
    time_info: dict
    processing: dict
    description: Optional[str]
    remark: Optional[str]
    created_at: str
    updated_at: str

    class Config:
        from_attributes = True


class ReconciliationListResponse(BaseModel):
    """对账记录列表响应"""
    records: List[ReconciliationRecordResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class DifferenceListResponse(BaseModel):
    """差异记录列表响应"""
    differences: List[ReconciliationDifferenceResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


# ==================== API接口 ====================

@router.post("/start", summary="手动触发对账")
async def start_reconciliation(
    request: StartReconciliationRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """
    手动触发对账流程

    权限要求: 管理员

    参数:
    - reconciliation_date: 对账日期 (YYYY-MM-DD)
    - reconciliation_type: 对账类型 (daily, manual, retry)
    - force: 是否强制重新对账

    返回:
    - 对账记录信息
    """
    try:
        service = ReconciliationService(db)
        record = service.start_reconciliation(
            reconciliation_date=request.reconciliation_date,
            reconciliation_type=request.reconciliation_type,
            force=request.force
        )

        return success_response(
            data=ReconciliationRecordResponse(**record.to_dict()),
            message="对账已启动"
        )

    except BusinessException as e:
        return error_response(
            code=e.code,
            message=e.message
        )
    except Exception as e:
        return error_response(
            code=ErrorCode.INTERNAL_ERROR,
            message=f"启动对账失败: {str(e)}"
        )


@router.get("/records", summary="查询对账记录")
async def get_reconciliation_records(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页大小"),
    status: Optional[ReconciliationStatus] = Query(None, description="对账状态"),
    start_date: Optional[str] = Query(None, description="开始日期"),
    end_date: Optional[str] = Query(None, description="结束日期"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """
    查询对账记录列表

    权限要求: 管理员

    参数:
    - page: 页码
    - page_size: 每页大小
    - status: 对账状态过滤
    - start_date: 开始日期过滤
    - end_date: 结束日期过滤

    返回:
    - 对账记录列表和分页信息
    """
    try:
        service = ReconciliationService(db)
        records, total = service.get_reconciliation_records(
            page=page,
            page_size=page_size,
            status=status,
            start_date=start_date,
            end_date=end_date
        )

        # 转换为响应模型
        record_responses = [
            ReconciliationRecordResponse(**record.to_dict())
            for record in records
        ]

        response_data = ReconciliationListResponse(
            records=record_responses,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=(total + page_size - 1) // page_size
        )

        return success_response(data=response_data)

    except Exception as e:
        return error_response(
            code=ErrorCode.INTERNAL_ERROR,
            message=f"查询对账记录失败: {str(e)}"
        )


@router.get("/records/{record_id}", summary="获取对账记录详情")
async def get_reconciliation_record(
    record_id: int = Path(..., description="对账记录ID"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """
    获取对账记录详情

    权限要求: 管理员

    参数:
    - record_id: 对账记录ID

    返回:
    - 对账记录详细信息
    """
    try:
        record = db.query(ReconciliationRecord).filter(
            ReconciliationRecord.id == record_id
        ).first()

        if not record:
            return error_response(
                code=ErrorCode.RECORD_NOT_FOUND,
                message="对账记录不存在"
            )

        return success_response(
            data=ReconciliationRecordResponse(**record.to_dict())
        )

    except Exception as e:
        return error_response(
            code=ErrorCode.INTERNAL_ERROR,
            message=f"获取对账记录失败: {str(e)}"
        )


@router.get("/differences", summary="查询差异记录")
async def get_reconciliation_differences(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页大小"),
    reconciliation_id: Optional[int] = Query(None, description="对账记录ID"),
    status: Optional[DifferenceStatus] = Query(None, description="差异状态"),
    difference_type: Optional[DifferenceType] = Query(None, description="差异类型"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """
    查询差异记录列表

    权限要求: 管理员

    参数:
    - page: 页码
    - page_size: 每页大小
    - reconciliation_id: 对账记录ID过滤
    - status: 差异状态过滤
    - difference_type: 差异类型过滤

    返回:
    - 差异记录列表和分页信息
    """
    try:
        service = ReconciliationService(db)
        differences, total = service.get_reconciliation_differences(
            reconciliation_id=reconciliation_id,
            status=status,
            difference_type=difference_type,
            page=page,
            page_size=page_size
        )

        # 转换为响应模型
        difference_responses = [
            ReconciliationDifferenceResponse(**diff.to_dict())
            for diff in differences
        ]

        response_data = DifferenceListResponse(
            differences=difference_responses,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=(total + page_size - 1) // page_size
        )

        return success_response(data=response_data)

    except Exception as e:
        return error_response(
            code=ErrorCode.INTERNAL_ERROR,
            message=f"查询差异记录失败: {str(e)}"
        )


@router.get("/differences/{difference_id}", summary="获取差异记录详情")
async def get_reconciliation_difference(
    difference_id: int = Path(..., description="差异记录ID"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """
    获取差异记录详情

    权限要求: 管理员

    参数:
    - difference_id: 差异记录ID

    返回:
    - 差异记录详细信息
    """
    try:
        difference = db.query(ReconciliationDifference).filter(
            ReconciliationDifference.id == difference_id
        ).first()

        if not difference:
            return error_response(
                code=ErrorCode.RECORD_NOT_FOUND,
                message="差异记录不存在"
            )

        return success_response(
            data=ReconciliationDifferenceResponse(**difference.to_dict())
        )

    except Exception as e:
        return error_response(
            code=ErrorCode.INTERNAL_ERROR,
            message=f"获取差异记录失败: {str(e)}"
        )


@router.post("/differences/{difference_id}/fix", summary="修复差异")
async def fix_difference(
    difference_id: int = Path(..., description="差异记录ID"),
    request: FixDifferenceRequest = ...,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """
    修复差异记录

    权限要求: 管理员

    参数:
    - difference_id: 差异记录ID
    - action: 修复动作 (auto_supplement, manual_supplement, ignore)
    - remark: 备注

    返回:
    - 修复后的差异记录信息
    """
    try:
        service = ReconciliationService(db)
        difference = service.fix_difference(
            difference_id=difference_id,
            action=request.action,
            processed_by=current_user.get("user_id", "unknown"),
            remark=request.remark
        )

        return success_response(
            data=ReconciliationDifferenceResponse(**difference.to_dict()),
            message="差异修复成功"
        )

    except RecordNotFoundError as e:
        return error_response(
            code=ErrorCode.RECORD_NOT_FOUND,
            message=str(e)
        )
    except BusinessException as e:
        return error_response(
            code=e.code,
            message=e.message
        )
    except Exception as e:
        return error_response(
            code=ErrorCode.INTERNAL_ERROR,
            message=f"修复差异失败: {str(e)}"
        )


@router.get("/records/{record_id}/report", summary="生成对账报告")
async def generate_reconciliation_report(
    record_id: int = Path(..., description="对账记录ID"),
    format_type: str = Query("json", description="报告格式 (json, excel, pdf)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """
    生成对账报告

    权限要求: 管理员

    参数:
    - record_id: 对账记录ID
    - format_type: 报告格式 (json, excel, pdf)

    返回:
    - 对账报告数据
    """
    try:
        service = ReconciliationService(db)
        report = service.generate_reconciliation_report(
            reconciliation_id=record_id,
            format_type=format_type
        )

        return success_response(
            data=report,
            message="对账报告生成成功"
        )

    except RecordNotFoundError as e:
        return error_response(
            code=ErrorCode.RECORD_NOT_FOUND,
            message=str(e)
        )
    except Exception as e:
        return error_response(
            code=ErrorCode.INTERNAL_ERROR,
            message=f"生成对账报告失败: {str(e)}"
        )


@router.get("/status/{target_date}", summary="获取指定日期对账状态")
async def get_daily_reconciliation_status(
    target_date: str = Path(..., description="目标日期 (YYYY-MM-DD)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """
    获取指定日期的对账状态

    权限要求: 管理员

    参数:
    - target_date: 目标日期 (YYYY-MM-DD)

    返回:
    - 对账状态信息
    """
    try:
        service = ReconciliationService(db)
        record = service.get_daily_reconciliation_status(target_date)

        if record:
            return success_response(
                data=ReconciliationRecordResponse(**record.to_dict())
            )
        else:
            return success_response(
                data=None,
                message=f"日期 {target_date} 尚未进行对账"
            )

    except Exception as e:
        return error_response(
            code=ErrorCode.INTERNAL_ERROR,
            message=f"获取对账状态失败: {str(e)}"
        )


@router.post("/records/{record_id}/retry", summary="重试失败的对账")
async def retry_failed_reconciliation(
    record_id: int = Path(..., description="对账记录ID"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """
    重试失败的对账

    权限要求: 管理员

    参数:
    - record_id: 对账记录ID

    返回:
    - 新的对账记录信息
    """
    try:
        service = ReconciliationService(db)
        new_record = service.retry_failed_reconciliation(record_id)

        return success_response(
            data=ReconciliationRecordResponse(**new_record.to_dict()),
            message="对账重试已启动"
        )

    except RecordNotFoundError as e:
        return error_response(
            code=ErrorCode.RECORD_NOT_FOUND,
            message=str(e)
        )
    except BusinessException as e:
        return error_response(
            code=e.code,
            message=e.message
        )
    except Exception as e:
        return error_response(
            code=ErrorCode.INTERNAL_ERROR,
            message=f"重试对账失败: {str(e)}"
        )


@router.get("/statistics", summary="获取对账统计信息")
async def get_reconciliation_statistics(
    start_date: Optional[str] = Query(None, description="开始日期"),
    end_date: Optional[str] = Query(None, description="结束日期"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """
    获取对账统计信息

    权限要求: 管理员

    参数:
    - start_date: 开始日期 (可选)
    - end_date: 结束日期 (可选)

    返回:
    - 对账统计信息
    """
    try:
        # 构建查询条件
        query = db.query(ReconciliationRecord)

        if start_date:
            query = query.filter(ReconciliationRecord.reconciliation_date >= start_date)
        if end_date:
            query = query.filter(ReconciliationRecord.reconciliation_date <= end_date)

        records = query.all()

        # 计算统计信息
        statistics = {
            "total_reconciliations": len(records),
            "success_count": sum(1 for r in records if r.status == ReconciliationStatus.SUCCESS),
            "partial_count": sum(1 for r in records if r.status == ReconciliationStatus.PARTIAL),
            "failed_count": sum(1 for r in records if r.status == ReconciliationStatus.FAILED),
            "total_differences": sum(r.difference_count for r in records),
            "total_matched_amount": float(sum(r.matched_amount for r in records if r.matched_amount)),
            "total_difference_amount": float(sum(r.difference_amount for r in records if r.difference_amount)),
            "average_match_rate": 0
        }

        # 计算平均匹配率
        if records:
            total_local_count = sum(r.total_local_count for r in records)
            total_matched_count = sum(r.matched_count for r in records)
            if total_local_count > 0:
                statistics["average_match_rate"] = round(
                    total_matched_count / total_local_count * 100, 2
                )

        return success_response(data=statistics)

    except Exception as e:
        return error_response(
            code=ErrorCode.INTERNAL_ERROR,
            message=f"获取统计信息失败: {str(e)}"
        )