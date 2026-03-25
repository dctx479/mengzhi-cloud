"""
SLA API端点

功能：
1. SLA协议管理
2. 实时指标查询
3. SLA报告生成
4. 违约记录查询

版本: 1.0
更新日期: 2026-01-22
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Path, Body
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

from app.api.deps import get_db, get_current_user
from app.models.user import User
from app.models.sla import (
    SLAAgreement, SLAMetric, SLAViolation,
    SLALevel, MetricType, ViolationSeverity
)
from app.services.sla_monitor import SLAMonitor
from app.services.sla_report import SLAReportService


def _get_user_obj(current_user: dict, db: Session) -> User:
    """从current_user dict获取User ORM对象（含enterprise_id等字段）"""
    user = db.query(User).filter(User.user_uuid == current_user["user_id"]).first()
    if not user:
        raise HTTPException(status_code=401, detail="用户不存在")
    return user


router = APIRouter(tags=["SLA"])


# ==================== Pydantic模型 ====================

class SLAAgreementCreate(BaseModel):
    """创建SLA协议"""
    name: str = Field(..., description="协议名称")
    level: SLALevel = Field(SLALevel.STANDARD, description="SLA等级")
    description: Optional[str] = Field(None, description="协议描述")
    start_date: str = Field(..., description="开始日期")
    end_date: str = Field(..., description="结束日期")
    availability_target: float = Field(99.5, description="可用性目标(%)")
    response_time_target: int = Field(2000, description="响应时间目标(ms)")
    error_rate_target: float = Field(0.1, description="错误率目标(%)")
    throughput_target: int = Field(100, description="吞吐量目标(req/s)")
    compensation_enabled: bool = Field(True, description="是否启用补偿")
    compensation_rules: Optional[dict] = Field(None, description="补偿规则")


class SLAAgreementUpdate(BaseModel):
    """更新SLA协议"""
    name: Optional[str] = None
    level: Optional[SLALevel] = None
    description: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    availability_target: Optional[float] = None
    response_time_target: Optional[int] = None
    error_rate_target: Optional[float] = None
    throughput_target: Optional[int] = None
    compensation_enabled: Optional[bool] = None
    compensation_rules: Optional[dict] = None
    is_active: Optional[bool] = None


class SLAAgreementResponse(BaseModel):
    """SLA协议响应"""
    id: int
    agreement_uuid: str
    name: str
    level: str
    description: Optional[str]
    start_date: str
    end_date: str
    availability_target: float
    response_time_target: int
    error_rate_target: float
    throughput_target: int
    compensation_enabled: bool
    is_active: bool
    created_at: str

    class Config:
        from_attributes = True


# ==================== SLA协议管理 ====================

@router.post("/agreements", response_model=SLAAgreementResponse)
async def create_agreement(
    agreement: SLAAgreementCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    创建SLA协议

    权限：管理员或企业管理员
    """
    # 检查权限
    if current_user["role"] not in ["admin", "enterprise_admin"]:
        raise HTTPException(status_code=403, detail="权限不足")

    # 查询用户ORM对象以获取enterprise_id和id
    user_obj = _get_user_obj(current_user, db)

    # 创建协议
    new_agreement = SLAAgreement(
        enterprise_id=user_obj.enterprise_id if current_user["user_type"] == "enterprise" else None,
        user_id=user_obj.id if current_user["user_type"] == "personal" else None,
        name=agreement.name,
        level=agreement.level,
        description=agreement.description,
        start_date=agreement.start_date,
        end_date=agreement.end_date,
        availability_target=agreement.availability_target,
        response_time_target=agreement.response_time_target,
        error_rate_target=agreement.error_rate_target,
        throughput_target=agreement.throughput_target,
        compensation_enabled=agreement.compensation_enabled,
        compensation_rules=agreement.compensation_rules,
    )

    db.add(new_agreement)
    db.commit()
    db.refresh(new_agreement)

    return new_agreement


@router.get("/agreements", response_model=List[SLAAgreementResponse])
async def list_agreements(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    level: Optional[SLALevel] = None,
    is_active: Optional[bool] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    获取SLA协议列表

    权限：所有用户（只能看到自己的协议）
    """
    query = db.query(SLAAgreement).filter(SLAAgreement.deleted_at.is_(None))

    # 根据用户类型过滤
    if current_user["role"] == "admin":
        # 管理员可以看到所有协议
        pass
    elif current_user["user_type"] == "enterprise":
        # 企业用户只能看到自己企业的协议
        user_obj = _get_user_obj(current_user, db)
        query = query.filter(SLAAgreement.enterprise_id == user_obj.enterprise_id)
    else:
        # 个人用户只能看到自己的协议
        user_obj = _get_user_obj(current_user, db)
        query = query.filter(SLAAgreement.user_id == user_obj.id)

    # 应用过滤条件
    if level:
        query = query.filter(SLAAgreement.level == level)
    if is_active is not None:
        query = query.filter(SLAAgreement.is_active == is_active)

    # 分页
    agreements = query.offset(skip).limit(limit).all()

    return agreements


@router.get("/agreements/{agreement_id}", response_model=SLAAgreementResponse)
async def get_agreement(
    agreement_id: int = Path(..., description="协议ID"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    获取SLA协议详情

    权限：协议所有者或管理员
    """
    agreement = db.query(SLAAgreement).filter(
        SLAAgreement.id == agreement_id,
        SLAAgreement.deleted_at.is_(None)
    ).first()

    if not agreement:
        raise HTTPException(status_code=404, detail="协议不存在")

    # 检查权限
    if current_user["role"] != "admin":
        user_obj = _get_user_obj(current_user, db)
        if current_user["user_type"] == "enterprise":
            if agreement.enterprise_id != user_obj.enterprise_id:
                raise HTTPException(status_code=403, detail="权限不足")
        else:
            if agreement.user_id != user_obj.id:
                raise HTTPException(status_code=403, detail="权限不足")

    return agreement


@router.put("/agreements/{agreement_id}", response_model=SLAAgreementResponse)
async def update_agreement(
    agreement_id: int = Path(..., description="协议ID"),
    agreement_update: SLAAgreementUpdate = Body(..., description="更新数据"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    更新SLA协议

    权限：协议所有者或管理员
    """
    agreement = db.query(SLAAgreement).filter(
        SLAAgreement.id == agreement_id,
        SLAAgreement.deleted_at.is_(None)
    ).first()

    if not agreement:
        raise HTTPException(status_code=404, detail="协议不存在")

    # 检查权限：管理员可以更新所有协议，非管理员必须是协议所有者
    if current_user["role"] != "admin":
        user_obj = _get_user_obj(current_user, db)
        if current_user["user_type"] == "enterprise":
            if agreement.enterprise_id != user_obj.enterprise_id:
                raise HTTPException(status_code=403, detail="权限不足")
        else:
            if agreement.user_id != user_obj.id:
                raise HTTPException(status_code=403, detail="权限不足")

    # 更新字段
    update_data = agreement_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(agreement, field, value)

    db.commit()
    db.refresh(agreement)

    return agreement


@router.delete("/agreements/{agreement_id}")
async def delete_agreement(
    agreement_id: int = Path(..., description="协议ID"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    删除SLA协议（软删除）

    权限：管理员
    """
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="权限不足")

    agreement = db.query(SLAAgreement).filter(
        SLAAgreement.id == agreement_id,
        SLAAgreement.deleted_at.is_(None)
    ).first()

    if not agreement:
        raise HTTPException(status_code=404, detail="协议不存在")

    # 软删除
    from datetime import datetime
    agreement.deleted_at = datetime.utcnow()
    db.commit()

    return {"message": "协议已删除"}


# ==================== 实时指标 ====================

@router.get("/metrics/realtime/{agreement_id}")
async def get_realtime_metrics(
    agreement_id: int = Path(..., description="协议ID"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    获取实时SLA指标

    权限：协议所有者或管理员
    """
    # 检查协议是否存在和权限
    agreement = db.query(SLAAgreement).filter(
        SLAAgreement.id == agreement_id,
        SLAAgreement.deleted_at.is_(None)
    ).first()

    if not agreement:
        raise HTTPException(status_code=404, detail="协议不存在")

    # 检查权限
    if current_user["role"] != "admin":
        user_obj = _get_user_obj(current_user, db)
        if current_user["user_type"] == "enterprise":
            if agreement.enterprise_id != user_obj.enterprise_id:
                raise HTTPException(status_code=403, detail="权限不足")
        else:
            if agreement.user_id != user_obj.id:
                raise HTTPException(status_code=403, detail="权限不足")

    # 获取实时指标
    monitor = SLAMonitor(db)
    metrics = monitor.get_realtime_metrics(agreement_id)

    return metrics


@router.get("/metrics/history/{agreement_id}")
async def get_metrics_history(
    agreement_id: int = Path(..., description="协议ID"),
    days: int = Query(7, ge=1, le=90, description="查询天数"),
    metric_type: Optional[MetricType] = Query(None, description="指标类型"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    获取历史指标数据

    权限：协议所有者或管理员
    """
    # 检查协议是否存在和权限
    agreement = db.query(SLAAgreement).filter(
        SLAAgreement.id == agreement_id,
        SLAAgreement.deleted_at.is_(None)
    ).first()

    if not agreement:
        raise HTTPException(status_code=404, detail="协议不存在")

    # 检查权限
    if current_user["role"] != "admin":
        user_obj = _get_user_obj(current_user, db)
        if current_user["user_type"] == "enterprise":
            if agreement.enterprise_id != user_obj.enterprise_id:
                raise HTTPException(status_code=403, detail="权限不足")
        else:
            if agreement.user_id != user_obj.id:
                raise HTTPException(status_code=403, detail="权限不足")

    # 查询历史指标
    from datetime import datetime, timedelta
    start_time = datetime.utcnow() - timedelta(days=days)

    query = db.query(SLAMetric).filter(
        SLAMetric.agreement_id == agreement_id,
        SLAMetric.period_start >= start_time.isoformat(),
        SLAMetric.deleted_at.is_(None)
    )

    if metric_type:
        query = query.filter(SLAMetric.metric_type == metric_type)

    metrics = query.order_by(SLAMetric.period_start).all()

    return [m.to_dict() for m in metrics]


# ==================== 违约记录 ====================

@router.get("/violations/{agreement_id}")
async def get_violations(
    agreement_id: int = Path(..., description="协议ID"),
    days: int = Query(7, ge=1, le=90, description="查询天数"),
    severity: Optional[ViolationSeverity] = Query(None, description="严重程度"),
    is_resolved: Optional[bool] = Query(None, description="是否已解决"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    获取违约记录

    权限：协议所有者或管理员
    """
    # 检查协议是否存在和权限
    agreement = db.query(SLAAgreement).filter(
        SLAAgreement.id == agreement_id,
        SLAAgreement.deleted_at.is_(None)
    ).first()

    if not agreement:
        raise HTTPException(status_code=404, detail="协议不存在")

    # 检查权限
    if current_user["role"] != "admin":
        user_obj = _get_user_obj(current_user, db)
        if current_user["user_type"] == "enterprise":
            if agreement.enterprise_id != user_obj.enterprise_id:
                raise HTTPException(status_code=403, detail="权限不足")
        else:
            if agreement.user_id != user_obj.id:
                raise HTTPException(status_code=403, detail="权限不足")

    # 查询违约记录
    monitor = SLAMonitor(db)
    violations = monitor.get_violation_history(agreement_id, days)

    # 应用过滤条件
    if severity:
        violations = [v for v in violations if v["severity"] == severity.value]
    if is_resolved is not None:
        violations = [v for v in violations if v["is_resolved"] == is_resolved]

    return violations


# ==================== SLA报告 ====================

@router.get("/reports/daily/{agreement_id}")
async def get_daily_report(
    agreement_id: int = Path(..., description="协议ID"),
    date: Optional[str] = Query(None, description="日期(YYYY-MM-DD)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    获取日报

    权限：协议所有者或管理员
    """
    agreement = db.query(SLAAgreement).filter(
        SLAAgreement.id == agreement_id,
        SLAAgreement.deleted_at.is_(None)
    ).first()
    if not agreement:
        raise HTTPException(status_code=404, detail="协议不存在")
    if current_user["role"] != "admin":
        user_obj = _get_user_obj(current_user, db)
        if current_user["user_type"] == "enterprise":
            if agreement.enterprise_id != user_obj.enterprise_id:
                raise HTTPException(status_code=403, detail="权限不足")
        else:
            if agreement.user_id != user_obj.id:
                raise HTTPException(status_code=403, detail="权限不足")

    report_service = SLAReportService(db)
    report = report_service.generate_daily_report(agreement_id, date)

    return report


@router.get("/reports/weekly/{agreement_id}")
async def get_weekly_report(
    agreement_id: int = Path(..., description="协议ID"),
    week_start: Optional[str] = Query(None, description="周开始日期(YYYY-MM-DD)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    获取周报

    权限：协议所有者或管理员
    """
    agreement = db.query(SLAAgreement).filter(
        SLAAgreement.id == agreement_id,
        SLAAgreement.deleted_at.is_(None)
    ).first()
    if not agreement:
        raise HTTPException(status_code=404, detail="协议不存在")
    if current_user["role"] != "admin":
        user_obj = _get_user_obj(current_user, db)
        if current_user["user_type"] == "enterprise":
            if agreement.enterprise_id != user_obj.enterprise_id:
                raise HTTPException(status_code=403, detail="权限不足")
        else:
            if agreement.user_id != user_obj.id:
                raise HTTPException(status_code=403, detail="权限不足")

    report_service = SLAReportService(db)
    report = report_service.generate_weekly_report(agreement_id, week_start)

    return report


@router.get("/reports/monthly/{agreement_id}")
async def get_monthly_report(
    agreement_id: int = Path(..., description="协议ID"),
    year: Optional[int] = Query(None, description="年份"),
    month: Optional[int] = Query(None, ge=1, le=12, description="月份"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    获取月报

    权限：协议所有者或管理员
    """
    agreement = db.query(SLAAgreement).filter(
        SLAAgreement.id == agreement_id,
        SLAAgreement.deleted_at.is_(None)
    ).first()
    if not agreement:
        raise HTTPException(status_code=404, detail="协议不存在")
    if current_user["role"] != "admin":
        user_obj = _get_user_obj(current_user, db)
        if current_user["user_type"] == "enterprise":
            if agreement.enterprise_id != user_obj.enterprise_id:
                raise HTTPException(status_code=403, detail="权限不足")
        else:
            if agreement.user_id != user_obj.id:
                raise HTTPException(status_code=403, detail="权限不足")

    report_service = SLAReportService(db)
    report = report_service.generate_monthly_report(agreement_id, year, month)

    return report


@router.get("/reports/achievement/{agreement_id}")
async def get_achievement_summary(
    agreement_id: int = Path(..., description="协议ID"),
    days: int = Query(30, ge=1, le=365, description="统计天数"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    获取达成率汇总

    权限：协议所有者或管理员
    """
    agreement = db.query(SLAAgreement).filter(
        SLAAgreement.id == agreement_id,
        SLAAgreement.deleted_at.is_(None)
    ).first()
    if not agreement:
        raise HTTPException(status_code=404, detail="协议不存在")
    if current_user["role"] != "admin":
        user_obj = _get_user_obj(current_user, db)
        if current_user["user_type"] == "enterprise":
            if agreement.enterprise_id != user_obj.enterprise_id:
                raise HTTPException(status_code=403, detail="权限不足")
        else:
            if agreement.user_id != user_obj.id:
                raise HTTPException(status_code=403, detail="权限不足")

    report_service = SLAReportService(db)
    summary = report_service.get_achievement_summary(agreement_id, days)

    return summary


# ==================== 监控和告警 ====================

@router.post("/monitor/run")
async def run_monitor(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    手动触发SLA监控

    权限：管理员
    """
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="权限不足")

    monitor = SLAMonitor(db)
    results = monitor.monitor_all_agreements()

    return results


@router.get("/dashboard/overview")
async def get_dashboard_overview(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    获取SLA仪表盘概览

    权限：所有用户
    """
    # 获取用户的协议
    query = db.query(SLAAgreement).filter(
        SLAAgreement.is_active == True,
        SLAAgreement.deleted_at.is_(None)
    )

    if current_user["role"] != "admin":
        if current_user["user_type"] == "enterprise":
            user_obj = _get_user_obj(current_user, db)
            query = query.filter(SLAAgreement.enterprise_id == user_obj.enterprise_id)
        else:
            user_obj = _get_user_obj(current_user, db)
            query = query.filter(SLAAgreement.user_id == user_obj.id)

    agreements = query.all()

    # 统计数据
    total_agreements = len(agreements)
    compliant_count = 0
    violation_count = 0

    for agreement in agreements:
        # 获取最近的违约记录
        from datetime import datetime, timedelta
        recent_violations = db.query(SLAViolation).filter(
            SLAViolation.agreement_id == agreement.id,
            SLAViolation.violation_time >= (datetime.utcnow() - timedelta(hours=24)).isoformat(),
            SLAViolation.deleted_at.is_(None)
        ).count()

        if recent_violations == 0:
            compliant_count += 1
        else:
            violation_count += recent_violations

    return {
        "total_agreements": total_agreements,
        "compliant_agreements": compliant_count,
        "violation_count": violation_count,
        "compliance_rate": round((compliant_count / total_agreements * 100) if total_agreements > 0 else 0, 2),
    }
