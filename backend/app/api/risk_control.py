"""
风控系统API接口

提供风险检查、规则管理、黑名单管理、事件查询等API接口。

版本: 1.0
更新日期: 2026-01-23
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

from ..database import get_db
from ..services.risk_control_service import get_risk_control_service, RiskControlService
from ..models.risk_control import (
    RiskRule, RiskEvent, RiskBlacklist,
    RiskLevel, RiskAction, RuleType, EventType, BlacklistType
)
from .deps import get_current_user, require_permission
from ..models.user import User

router = APIRouter(tags=["风控系统"])


# Pydantic 模型定义
class RiskCheckRequest(BaseModel):
    """风险检查请求"""
    event_type: str = Field(..., description="事件类型")
    user_id: str = Field(..., description="用户ID")
    event_data: Dict[str, Any] = Field(..., description="事件数据")
    context: Optional[Dict[str, Any]] = Field(None, description="上下文信息")


class RiskCheckResponse(BaseModel):
    """风险检查响应"""
    risk_score: int = Field(..., description="风险分数")
    risk_level: str = Field(..., description="风险等级")
    action: str = Field(..., description="处理动作")
    triggered_rules: List[Dict[str, Any]] = Field(..., description="触发的规则")
    blacklist_hits: List[Dict[str, Any]] = Field(..., description="黑名单命中")
    recommendations: List[str] = Field(..., description="处理建议")
    event_id: str = Field(..., description="事件ID")


class RuleCreateRequest(BaseModel):
    """创建规则请求"""
    name: str = Field(..., description="规则名称")
    description: Optional[str] = Field(None, description="规则描述")
    rule_type: str = Field(..., description="规则类型")
    conditions: Dict[str, Any] = Field(..., description="规则条件")
    risk_level: str = Field(..., description="风险等级")
    action: str = Field(..., description="处理动作")
    threshold_value: Optional[float] = Field(None, description="阈值")
    time_window: Optional[int] = Field(None, description="时间窗口(秒)")
    max_count: Optional[int] = Field(None, description="最大次数")
    priority: int = Field(100, description="优先级")


class RuleUpdateRequest(BaseModel):
    """更新规则请求"""
    name: Optional[str] = Field(None, description="规则名称")
    description: Optional[str] = Field(None, description="规则描述")
    conditions: Optional[Dict[str, Any]] = Field(None, description="规则条件")
    risk_level: Optional[str] = Field(None, description="风险等级")
    action: Optional[str] = Field(None, description="处理动作")
    threshold_value: Optional[float] = Field(None, description="阈值")
    time_window: Optional[int] = Field(None, description="时间窗口(秒)")
    max_count: Optional[int] = Field(None, description="最大次数")
    priority: Optional[int] = Field(None, description="优先级")
    is_active: Optional[bool] = Field(None, description="是否启用")


class BlacklistCreateRequest(BaseModel):
    """创建黑名单请求"""
    blacklist_type: str = Field(..., description="黑名单类型")
    value: str = Field(..., description="黑名单值")
    reason: Optional[str] = Field(None, description="加入原因")
    risk_level: str = Field(..., description="风险等级")
    expires_at: Optional[datetime] = Field(None, description="过期时间")


class EventProcessRequest(BaseModel):
    """事件处理请求"""
    result: str = Field(..., description="处理结果")


# API 接口实现
@router.post("/check", response_model=RiskCheckResponse, summary="风险检查")
async def check_risk(
    request: RiskCheckRequest,
    http_request: Request,
    risk_service: RiskControlService = Depends(get_risk_control_service),
    current_user: User = Depends(get_current_user)
):
    """
    实时风险检查接口

    对用户行为进行实时风险评估，返回风险等级和处理建议。
    """
    try:
        # 从HTTP请求中提取上下文信息
        context = request.context or {}
        context.update({
            "ip_address": http_request.client.host,
            "user_agent": http_request.headers.get("user-agent"),
        })

        # 执行风险检查
        result = risk_service.check_risk(
            event_type=request.event_type,
            user_id=request.user_id,
            event_data=request.event_data,
            context=context
        )

        return RiskCheckResponse(**result)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"风险检查失败: {str(e)}")


@router.get("/events", summary="查询风险事件")
async def get_risk_events(
    user_id: Optional[str] = Query(None, description="用户ID"),
    event_type: Optional[str] = Query(None, description="事件类型"),
    risk_level: Optional[str] = Query(None, description="风险等级"),
    start_date: Optional[datetime] = Query(None, description="开始时间"),
    end_date: Optional[datetime] = Query(None, description="结束时间"),
    skip: int = Query(0, ge=0, description="跳过数量"),
    limit: int = Query(100, ge=1, le=1000, description="返回数量"),
    risk_service: RiskControlService = Depends(get_risk_control_service),
    current_user: User = Depends(require_permission("risk", "read"))
):
    """
    查询风险事件列表

    支持按用户、事件类型、风险等级、时间范围等条件筛选。
    """
    try:
        events = risk_service.get_risk_events(
            user_id=user_id,
            event_type=event_type,
            risk_level=risk_level,
            start_date=start_date,
            end_date=end_date,
            skip=skip,
            limit=limit
        )

        return {
            "events": [event.to_dict() for event in events],
            "total": len(events)
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"查询风险事件失败: {str(e)}")


@router.post("/events/{event_id}/process", summary="处理风险事件")
async def process_risk_event(
    event_id: str,
    request: EventProcessRequest,
    risk_service: RiskControlService = Depends(get_risk_control_service),
    current_user: User = Depends(require_permission("risk", "write"))
):
    """
    处理风险事件

    标记事件为已处理状态，记录处理结果。
    """
    try:
        success = risk_service.process_risk_event(
            event_id=event_id,
            processed_by=current_user["user_id"],
            result=request.result
        )

        if not success:
            raise HTTPException(status_code=404, detail="风险事件不存在")

        return {"message": "事件处理成功"}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"处理风险事件失败: {str(e)}")


@router.post("/rules", summary="创建风控规则")
async def create_rule(
    request: RuleCreateRequest,
    risk_service: RiskControlService = Depends(get_risk_control_service),
    current_user: User = Depends(require_permission("risk", "write"))
):
    """
    创建新的风控规则

    支持频率限制、金额限制、行为分析等多种规则类型。
    """
    try:
        # 验证规则类型
        if request.rule_type not in [e.value for e in RuleType]:
            raise HTTPException(status_code=400, detail="无效的规则类型")

        # 验证风险等级
        if request.risk_level not in [e.value for e in RiskLevel]:
            raise HTTPException(status_code=400, detail="无效的风险等级")

        # 验证处理动作
        if request.action not in [e.value for e in RiskAction]:
            raise HTTPException(status_code=400, detail="无效的处理动作")

        rule_data = request.dict()
        rule_data["created_by"] = current_user["user_id"]

        rule = risk_service.create_rule(rule_data)

        return {
            "message": "规则创建成功",
            "rule": rule.to_dict()
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"创建规则失败: {str(e)}")


@router.get("/rules", summary="查询风控规则")
async def get_rules(
    skip: int = Query(0, ge=0, description="跳过数量"),
    limit: int = Query(100, ge=1, le=1000, description="返回数量"),
    risk_service: RiskControlService = Depends(get_risk_control_service),
    current_user: User = Depends(require_permission("risk", "read"))
):
    """
    查询风控规则列表

    返回系统中配置的所有风控规则。
    """
    try:
        rules = risk_service.get_rules(skip=skip, limit=limit)

        return {
            "rules": [rule.to_dict() for rule in rules],
            "total": len(rules)
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"查询规则失败: {str(e)}")


@router.put("/rules/{rule_id}", summary="更新风控规则")
async def update_rule(
    rule_id: str,
    request: RuleUpdateRequest,
    risk_service: RiskControlService = Depends(get_risk_control_service),
    current_user: User = Depends(require_permission("risk", "write"))
):
    """
    更新风控规则

    修改现有规则的配置参数。
    """
    try:
        # 验证可选字段
        if request.risk_level and request.risk_level not in [e.value for e in RiskLevel]:
            raise HTTPException(status_code=400, detail="无效的风险等级")

        if request.action and request.action not in [e.value for e in RiskAction]:
            raise HTTPException(status_code=400, detail="无效的处理动作")

        rule_data = {k: v for k, v in request.dict().items() if v is not None}

        rule = risk_service.update_rule(rule_id, rule_data)

        if not rule:
            raise HTTPException(status_code=404, detail="规则不存在")

        return {
            "message": "规则更新成功",
            "rule": rule.to_dict()
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"更新规则失败: {str(e)}")


@router.delete("/rules/{rule_id}", summary="删除风控规则")
async def delete_rule(
    rule_id: str,
    risk_service: RiskControlService = Depends(get_risk_control_service),
    current_user: User = Depends(require_permission("risk", "write"))
):
    """
    删除风控规则

    从系统中移除指定的风控规则。
    """
    try:
        success = risk_service.delete_rule(rule_id)

        if not success:
            raise HTTPException(status_code=404, detail="规则不存在")

        return {"message": "规则删除成功"}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"删除规则失败: {str(e)}")


@router.post("/blacklist", summary="添加黑名单")
async def add_to_blacklist(
    request: BlacklistCreateRequest,
    risk_service: RiskControlService = Depends(get_risk_control_service),
    current_user: User = Depends(require_permission("risk", "write"))
):
    """
    添加黑名单条目

    支持用户、IP、设备、手机号、邮箱、银行卡等类型的黑名单。
    """
    try:
        # 验证黑名单类型
        if request.blacklist_type not in [e.value for e in BlacklistType]:
            raise HTTPException(status_code=400, detail="无效的黑名单类型")

        # 验证风险等级
        if request.risk_level not in [e.value for e in RiskLevel]:
            raise HTTPException(status_code=400, detail="无效的风险等级")

        blacklist_data = request.dict()
        blacklist_data["created_by"] = current_user["user_id"]

        blacklist = risk_service.add_to_blacklist(blacklist_data)

        return {
            "message": "黑名单添加成功",
            "blacklist": blacklist.to_dict()
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"添加黑名单失败: {str(e)}")


@router.get("/blacklist", summary="查询黑名单")
async def get_blacklist(
    skip: int = Query(0, ge=0, description="跳过数量"),
    limit: int = Query(100, ge=1, le=1000, description="返回数量"),
    risk_service: RiskControlService = Depends(get_risk_control_service),
    current_user: User = Depends(require_permission("risk", "read"))
):
    """
    查询黑名单列表

    返回系统中配置的所有黑名单条目。
    """
    try:
        blacklist = risk_service.get_blacklist(skip=skip, limit=limit)

        return {
            "blacklist": [item.to_dict() for item in blacklist],
            "total": len(blacklist)
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"查询黑名单失败: {str(e)}")


@router.delete("/blacklist/{blacklist_id}", summary="移除黑名单")
async def remove_from_blacklist(
    blacklist_id: str,
    risk_service: RiskControlService = Depends(get_risk_control_service),
    current_user: User = Depends(require_permission("risk", "write"))
):
    """
    移除黑名单条目

    从系统中删除指定的黑名单条目。
    """
    try:
        success = risk_service.remove_from_blacklist(blacklist_id)

        if not success:
            raise HTTPException(status_code=404, detail="黑名单条目不存在")

        return {"message": "黑名单移除成功"}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"移除黑名单失败: {str(e)}")


@router.get("/statistics", summary="风险统计")
async def get_risk_statistics(
    start_date: Optional[datetime] = Query(None, description="开始时间"),
    end_date: Optional[datetime] = Query(None, description="结束时间"),
    risk_service: RiskControlService = Depends(get_risk_control_service),
    current_user: User = Depends(require_permission("risk", "read"))
):
    """
    获取风险统计数据

    提供指定时间范围内的风险事件统计信息。
    """
    try:
        # 默认查询最近7天的数据
        if not start_date:
            start_date = datetime.utcnow() - timedelta(days=7)
        if not end_date:
            end_date = datetime.utcnow()

        statistics = risk_service.get_risk_statistics(start_date, end_date)

        return {
            "statistics": statistics,
            "period": {
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat()
            }
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取统计数据失败: {str(e)}")


@router.get("/enums", summary="获取枚举值")
async def get_enums():
    """
    获取风控系统相关的枚举值

    返回风险等级、处理动作、规则类型等枚举定义。
    """
    return {
        "risk_levels": [e.value for e in RiskLevel],
        "risk_actions": [e.value for e in RiskAction],
        "rule_types": [e.value for e in RuleType],
        "event_types": [e.value for e in EventType],
        "blacklist_types": [e.value for e in BlacklistType]
    }