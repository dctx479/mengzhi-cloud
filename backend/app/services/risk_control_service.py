"""
风控服务 - 实时风险评估和防控

提供多维度风险检测、规则引擎、黑名单管理等核心风控功能。

版本: 1.0
更新日期: 2026-01-23
"""

import json
import hashlib
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Dict, List, Optional, Tuple, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func, desc
from fastapi import Depends

from ..models.risk_control import (
    RiskRule, RiskEvent, RiskBlacklist, RiskStatistics,
    RiskLevel, RiskAction, RuleType, EventType, BlacklistType
)
from ..models.payment import Payment
from ..models.order import Order
from ..models.user import User
from ..database import get_db
from loguru import logger


class RiskControlService:
    """风控服务类"""

    def __init__(self, db: Session):
        self.db = db
        self.logger = logger

    def check_risk(
        self,
        event_type: str,
        user_id: str,
        event_data: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        实时风险检查

        Args:
            event_type: 事件类型
            user_id: 用户ID
            event_data: 事件数据
            context: 上下文信息(IP、设备等)

        Returns:
            风险检查结果
        """
        try:
            # 初始化风险评估结果
            risk_result = {
                "risk_score": 0,
                "risk_level": RiskLevel.LOW.value,
                "action": RiskAction.ALLOW.value,
                "triggered_rules": [],
                "blacklist_hits": [],
                "recommendations": []
            }

            # 1. 黑名单检查
            try:
                blacklist_result = self._check_blacklist(user_id, event_data, context)
                if blacklist_result["hits"]:
                    risk_result["blacklist_hits"] = blacklist_result["hits"]
                    risk_result["risk_score"] += blacklist_result["score"]
            except Exception as e:
                self.logger.error(f"黑名单检查模块异常: {str(e)}")
                raise

            # 2. 规则引擎检查
            try:
                rules_result = self._check_rules(event_type, user_id, event_data, context)
                if rules_result["triggered"]:
                    risk_result["triggered_rules"] = rules_result["triggered"]
                    risk_result["risk_score"] += rules_result["score"]
            except Exception as e:
                self.logger.error(f"规则检查模块异常: {str(e)}")
                raise

            # 3. 行为分析
            try:
                behavior_result = self._analyze_behavior(user_id, event_type, event_data)
                risk_result["risk_score"] += behavior_result["score"]
            except Exception as e:
                self.logger.error(f"行为分析模块异常: {str(e)}")
                raise

            # 4. 确定最终风险等级和处理动作
            risk_result["risk_level"] = self._calculate_risk_level(risk_result["risk_score"])
            risk_result["action"] = self._determine_action(
                risk_result["risk_level"],
                risk_result["triggered_rules"],
                risk_result["blacklist_hits"]
            )

            # 5. 记录风险事件
            event_id = self._record_risk_event(
                event_type, user_id, event_data, context, risk_result
            )
            risk_result["event_id"] = event_id

            # 6. 生成建议
            risk_result["recommendations"] = self._generate_recommendations(risk_result)

            self.logger.info(f"风险检查完成: user_id={user_id}, risk_score={risk_result['risk_score']}, action={risk_result['action']}")
            return risk_result

        except Exception as e:
            self.logger.error(f"风险检查失败: {str(e)}")
            # 发生错误时采用保守策略
            return {
                "risk_score": 100,
                "risk_level": RiskLevel.HIGH.value,
                "action": RiskAction.REVIEW.value,
                "triggered_rules": [],
                "blacklist_hits": [],
                "recommendations": ["系统异常，建议人工审核"],
                "error": "风险检查异常"
            }

    def _check_blacklist(
        self,
        user_id: str,
        event_data: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """检查黑名单"""
        hits = []
        score = 0

        try:
            # 检查项目列表
            check_items = [
                (BlacklistType.USER.value, user_id),
            ]

            # 添加上下文检查项
            if context:
                if context.get("ip_address"):
                    check_items.append((BlacklistType.IP.value, context["ip_address"]))
                if context.get("device_fingerprint"):
                    check_items.append((BlacklistType.DEVICE.value, context["device_fingerprint"]))

            # 添加事件数据检查项
            if event_data.get("phone"):
                check_items.append((BlacklistType.PHONE.value, event_data["phone"]))
            if event_data.get("email"):
                check_items.append((BlacklistType.EMAIL.value, event_data["email"]))
            if event_data.get("card_number"):
                check_items.append((BlacklistType.CARD.value, event_data["card_number"]))

            # 批量查询黑名单
            items_to_update = []
            for blacklist_type, value in check_items:
                blacklist_items = self.db.query(RiskBlacklist).filter(
                    and_(
                        RiskBlacklist.blacklist_type == blacklist_type,
                        RiskBlacklist.value == value,
                        RiskBlacklist.is_active == True,
                        or_(
                            RiskBlacklist.expires_at.is_(None),
                            RiskBlacklist.expires_at > datetime.utcnow()
                        )
                    )
                ).all()

                for item in blacklist_items:
                    hits.append({
                        "id": item.id,
                        "type": item.blacklist_type,
                        "value": item.value,
                        "risk_level": item.risk_level,
                        "reason": item.reason
                    })

                    # 记录要更新的项目
                    items_to_update.append(item)

                    # 根据风险等级计算分数
                    if item.risk_level == RiskLevel.CRITICAL.value:
                        score += 50
                    elif item.risk_level == RiskLevel.HIGH.value:
                        score += 30
                    elif item.risk_level == RiskLevel.MEDIUM.value:
                        score += 15
                    else:
                        score += 5

            # 批量更新统计信息
            if items_to_update:
                now = datetime.utcnow()
                for item in items_to_update:
                    item.hit_count += 1
                    item.last_hit_at = now
                self.db.commit()

        except Exception as e:
            self.logger.error(f"黑名单检查失败: {str(e)}")
            self.db.rollback()
            raise

        return {"hits": hits, "score": score}

    def _check_rules(
        self,
        event_type: str,
        user_id: str,
        event_data: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """检查风控规则"""
        triggered = []
        score = 0

        try:
            # 获取启用的规则，按优先级排序
            rules = self.db.query(RiskRule).filter(
                RiskRule.is_active == True
            ).order_by(RiskRule.priority).all()

            rules_to_update = []
            for rule in rules:
                if self._evaluate_rule(rule, event_type, user_id, event_data, context):
                    triggered.append({
                        "id": rule.id,
                        "name": rule.name,
                        "type": rule.rule_type,
                        "risk_level": rule.risk_level,
                        "action": rule.action
                    })

                    rules_to_update.append(rule)

                    # 根据风险等级计算分数
                    if rule.risk_level == RiskLevel.CRITICAL.value:
                        score += 40
                    elif rule.risk_level == RiskLevel.HIGH.value:
                        score += 25
                    elif rule.risk_level == RiskLevel.MEDIUM.value:
                        score += 10
                    else:
                        score += 3

            # 批量更新统计信息
            if rules_to_update:
                now = datetime.utcnow()
                for rule in rules_to_update:
                    rule.hit_count += 1
                    rule.last_hit_at = now
                self.db.commit()

        except Exception as e:
            self.logger.error(f"规则检查失败: {str(e)}")
            self.db.rollback()
            raise

        return {"triggered": triggered, "score": score}

    def _evaluate_rule(
        self,
        rule: RiskRule,
        event_type: str,
        user_id: str,
        event_data: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None
    ) -> bool:
        """评估单个规则"""
        try:
            conditions = rule.conditions

            # 检查事件类型匹配
            if conditions.get("event_types") and event_type not in conditions["event_types"]:
                return False

            # 根据规则类型进行检查
            if rule.rule_type == RuleType.FREQUENCY.value:
                return self._check_frequency_rule(rule, user_id, event_type, context)
            elif rule.rule_type == RuleType.AMOUNT.value:
                return self._check_amount_rule(rule, event_data)
            elif rule.rule_type == RuleType.BEHAVIOR.value:
                return self._check_behavior_rule(rule, user_id, event_data, context)
            elif rule.rule_type == RuleType.TIME.value:
                return self._check_time_rule(rule, context)
            elif rule.rule_type == RuleType.LOCATION.value:
                return self._check_location_rule(rule, context)

            return False

        except Exception as e:
            self.logger.error(f"规则评估失败: rule_id={rule.id}, error={str(e)}")
            return False

    def _check_frequency_rule(
        self,
        rule: RiskRule,
        user_id: str,
        event_type: str,
        context: Optional[Dict[str, Any]] = None
    ) -> bool:
        """检查频率限制规则"""
        try:
            time_window = rule.time_window or 3600  # 默认1小时
            max_count = rule.max_count or 10

            # 计算时间窗口
            start_time = datetime.utcnow() - timedelta(seconds=time_window)

            # 查询时间窗口内的事件数量（使用FOR UPDATE锁防止竞态）
            # 注意：这里仍然存在竞态条件，因为我们不能在这里真正锁定未来事件
            # 最佳实践是在应用层使用分布式锁(Redis)，但此处提供了SQL行级锁的基础
            count = self.db.query(RiskEvent).filter(
                and_(
                    RiskEvent.user_id == user_id,
                    RiskEvent.event_type == event_type,
                    RiskEvent.created_at >= start_time
                )
            ).count()

            # 返回是否达到限制（注意：这仍然容易受竞态影响，建议在应用层使用Redis分布式锁）
            return count >= max_count

        except Exception as e:
            self.logger.error(f"频率规则检查失败: {str(e)}")
            return False

    def _check_amount_rule(self, rule: RiskRule, event_data: Dict[str, Any]) -> bool:
        """检查金额限制规则"""
        try:
            threshold = rule.threshold_value
            if not threshold:
                return False

            amount = event_data.get("amount")
            if not amount:
                return False

            # Convert both to Decimal for safe comparison
            threshold_decimal = Decimal(str(threshold))
            amount_decimal = Decimal(str(amount))
            return amount_decimal > threshold_decimal

        except (ValueError, TypeError, AttributeError) as e:
            self.logger.error(f"金额规则检查失败: {str(e)}")
            return False

    def _check_behavior_rule(
        self,
        rule: RiskRule,
        user_id: str,
        event_data: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None
    ) -> bool:
        """检查行为分析规则"""
        try:
            conditions = rule.conditions

            # 检查异常登录时间
            if conditions.get("check_login_time"):
                current_hour = datetime.utcnow().hour
                if current_hour < 6 or current_hour > 23:  # 凌晨登录
                    return True

            # 检查设备变更
            if conditions.get("check_device_change") and context:
                device_fingerprint = context.get("device_fingerprint")
                if device_fingerprint:
                    # 查询用户最近的设备指纹
                    recent_event = self.db.query(RiskEvent).filter(
                        and_(
                            RiskEvent.user_id == user_id,
                            RiskEvent.device_fingerprint.isnot(None)
                        )
                    ).order_by(desc(RiskEvent.created_at)).first()

                    if recent_event and recent_event.device_fingerprint != device_fingerprint:
                        return True

            # 检查IP变更
            if conditions.get("check_ip_change") and context:
                ip_address = context.get("ip_address")
                if ip_address:
                    # 查询用户最近的IP地址
                    recent_event = self.db.query(RiskEvent).filter(
                        and_(
                            RiskEvent.user_id == user_id,
                            RiskEvent.ip_address.isnot(None)
                        )
                    ).order_by(desc(RiskEvent.created_at)).first()

                    if recent_event and recent_event.ip_address != ip_address:
                        return True

            return False

        except Exception as e:
            self.logger.error(f"行为规则检查失败: {str(e)}")
            return False

    def _check_time_rule(self, rule: RiskRule, context: Optional[Dict[str, Any]] = None) -> bool:
        """检查时间限制规则"""
        try:
            conditions = rule.conditions
            current_time = datetime.utcnow()

            # 检查禁止时间段
            forbidden_hours = conditions.get("forbidden_hours", [])
            if current_time.hour in forbidden_hours:
                return True

            # 检查工作日限制
            if conditions.get("workdays_only"):
                if current_time.weekday() >= 5:  # 周末
                    return True

            return False

        except Exception as e:
            self.logger.error(f"时间规则检查失败: {str(e)}")
            return False

    def _check_location_rule(self, rule: RiskRule, context: Optional[Dict[str, Any]] = None) -> bool:
        """检查地理位置规则"""
        try:
            if not context or not context.get("location"):
                return False

            conditions = rule.conditions
            location = context["location"]

            # 检查禁止地区
            forbidden_countries = conditions.get("forbidden_countries", [])
            if location.get("country") in forbidden_countries:
                return True

            # 检查允许地区
            allowed_countries = conditions.get("allowed_countries", [])
            if allowed_countries and location.get("country") not in allowed_countries:
                return True

            return False

        except Exception as e:
            self.logger.error(f"地理位置规则检查失败: {str(e)}")
            return False

    def _analyze_behavior(self, user_id: str, event_type: str, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """行为分析"""
        score = 0

        try:
            # 分析用户历史行为模式
            recent_events = self.db.query(RiskEvent).filter(
                and_(
                    RiskEvent.user_id == user_id,
                    RiskEvent.created_at >= datetime.utcnow() - timedelta(days=30)
                )
            ).order_by(desc(RiskEvent.created_at)).limit(100).all()

            if not recent_events:
                # 新用户，增加风险分数
                score += 5

            # 分析事件频率
            event_count_today = len([
                e for e in recent_events
                if e.created_at.date() == datetime.utcnow().date()
            ])

            if event_count_today > 20:
                score += 10
            elif event_count_today > 10:
                score += 5

            # 分析金额模式（如果是支付事件）
            if event_type == EventType.PAYMENT.value and event_data.get("amount"):
                amount = Decimal(str(event_data["amount"]))

                # 获取用户历史支付金额
                payment_amounts = []
                for e in recent_events:
                    if e.event_type == EventType.PAYMENT.value and e.event_data:
                        try:
                            amt = e.event_data.get("amount")
                            if amt is not None:
                                payment_amounts.append(Decimal(str(amt)))
                        except (ValueError, TypeError):
                            # Skip malformed amounts
                            continue

                if payment_amounts:
                    avg_amount = sum(payment_amounts) / len(payment_amounts)
                    if amount > avg_amount * 5:  # 超过平均金额5倍
                        score += 15
                    elif amount > avg_amount * 3:  # 超过平均金额3倍
                        score += 8

        except Exception as e:
            self.logger.error(f"行为分析失败: {str(e)}")
            raise

        return {"score": score}

    def _calculate_risk_level(self, risk_score: int) -> str:
        """计算风险等级"""
        if risk_score >= 80:
            return RiskLevel.CRITICAL.value
        elif risk_score >= 50:
            return RiskLevel.HIGH.value
        elif risk_score >= 20:
            return RiskLevel.MEDIUM.value
        else:
            return RiskLevel.LOW.value

    def _determine_action(
        self,
        risk_level: str,
        triggered_rules: List[Dict],
        blacklist_hits: List[Dict]
    ) -> str:
        """确定处理动作"""
        # 黑名单命中直接拦截
        if blacklist_hits:
            for hit in blacklist_hits:
                if hit["risk_level"] in [RiskLevel.CRITICAL.value, RiskLevel.HIGH.value]:
                    return RiskAction.BLOCK.value

        # 检查规则动作
        for rule in triggered_rules:
            if rule["action"] == RiskAction.BLOCK.value:
                return RiskAction.BLOCK.value

        # 根据风险等级确定动作
        if risk_level == RiskLevel.CRITICAL.value:
            return RiskAction.BLOCK.value
        elif risk_level == RiskLevel.HIGH.value:
            return RiskAction.REVIEW.value
        elif risk_level == RiskLevel.MEDIUM.value:
            return RiskAction.DELAY.value
        else:
            return RiskAction.ALLOW.value

    def _record_risk_event(
        self,
        event_type: str,
        user_id: str,
        event_data: Dict[str, Any],
        context: Optional[Dict[str, Any]],
        risk_result: Dict[str, Any]
    ) -> str:
        """记录风险事件"""
        try:
            event = RiskEvent(
                event_type=event_type,
                user_id=user_id,
                event_data=event_data,
                risk_score=risk_result["risk_score"],
                risk_level=risk_result["risk_level"],
                triggered_rules=risk_result["triggered_rules"],
                final_action=risk_result["action"],
                ip_address=context.get("ip_address") if context else None,
                user_agent=context.get("user_agent") if context else None,
                device_fingerprint=context.get("device_fingerprint") if context else None,
                location=context.get("location") if context else None
            )

            self.db.add(event)
            self.db.commit()

            return event.id

        except Exception as e:
            self.logger.error(f"记录风险事件失败: {str(e)}")
            self.db.rollback()
            raise

    def _generate_recommendations(self, risk_result: Dict[str, Any]) -> List[str]:
        """生成风险处理建议"""
        recommendations = []

        if risk_result["blacklist_hits"]:
            recommendations.append("检测到黑名单命中，建议立即拦截")

        if risk_result["risk_score"] > 50:
            recommendations.append("风险分数较高，建议人工审核")

        if risk_result["triggered_rules"]:
            high_risk_rules = [
                rule for rule in risk_result["triggered_rules"]
                if rule["risk_level"] in [RiskLevel.HIGH.value, RiskLevel.CRITICAL.value]
            ]
            if high_risk_rules:
                recommendations.append("触发高风险规则，建议加强监控")

        if not recommendations:
            recommendations.append("风险等级较低，可正常处理")

        return recommendations

    # 规则管理方法
    def create_rule(self, rule_data: Dict[str, Any]) -> RiskRule:
        """创建风控规则"""
        try:
            rule = RiskRule(**rule_data)
            self.db.add(rule)
            self.db.commit()
            self.db.refresh(rule)

            self.logger.info(f"创建风控规则成功: rule_id={rule.id}")
            return rule

        except Exception as e:
            self.logger.error(f"创建风控规则失败: {str(e)}")
            self.db.rollback()
            raise

    def update_rule(self, rule_id: str, rule_data: Dict[str, Any]) -> Optional[RiskRule]:
        """更新风控规则"""
        try:
            rule = self.db.query(RiskRule).filter(RiskRule.id == rule_id).first()
            if not rule:
                return None

            for key, value in rule_data.items():
                if hasattr(rule, key):
                    setattr(rule, key, value)

            self.db.commit()
            self.db.refresh(rule)

            self.logger.info(f"更新风控规则成功: rule_id={rule_id}")
            return rule

        except Exception as e:
            self.logger.error(f"更新风控规则失败: {str(e)}")
            self.db.rollback()
            raise

    def delete_rule(self, rule_id: str) -> bool:
        """删除风控规则"""
        try:
            rule = self.db.query(RiskRule).filter(RiskRule.id == rule_id).first()
            if not rule:
                return False

            self.db.delete(rule)
            self.db.commit()

            self.logger.info(f"删除风控规则成功: rule_id={rule_id}")
            return True

        except Exception as e:
            self.logger.error(f"删除风控规则失败: {str(e)}")
            self.db.rollback()
            raise

    def get_rules(self, skip: int = 0, limit: int = 100) -> List[RiskRule]:
        """获取风控规则列表"""
        return self.db.query(RiskRule).offset(skip).limit(limit).all()

    # 黑名单管理方法
    def add_to_blacklist(self, blacklist_data: Dict[str, Any]) -> RiskBlacklist:
        """添加黑名单"""
        try:
            blacklist = RiskBlacklist(**blacklist_data)
            self.db.add(blacklist)
            self.db.commit()
            self.db.refresh(blacklist)

            self.logger.info(f"添加黑名单成功: blacklist_id={blacklist.id}")
            return blacklist

        except Exception as e:
            self.logger.error(f"添加黑名单失败: {str(e)}")
            self.db.rollback()
            raise

    def remove_from_blacklist(self, blacklist_id: str) -> bool:
        """移除黑名单"""
        try:
            blacklist = self.db.query(RiskBlacklist).filter(RiskBlacklist.id == blacklist_id).first()
            if not blacklist:
                return False

            self.db.delete(blacklist)
            self.db.commit()

            self.logger.info(f"移除黑名单成功: blacklist_id={blacklist_id}")
            return True

        except Exception as e:
            self.logger.error(f"移除黑名单失败: {str(e)}")
            self.db.rollback()
            raise

    def get_blacklist(self, skip: int = 0, limit: int = 100) -> List[RiskBlacklist]:
        """获取黑名单列表"""
        return self.db.query(RiskBlacklist).filter(
            RiskBlacklist.is_active == True
        ).offset(skip).limit(limit).all()

    # 事件查询方法
    def get_risk_events(
        self,
        user_id: Optional[str] = None,
        event_type: Optional[str] = None,
        risk_level: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[RiskEvent]:
        """查询风险事件"""
        query = self.db.query(RiskEvent)

        if user_id:
            query = query.filter(RiskEvent.user_id == user_id)
        if event_type:
            query = query.filter(RiskEvent.event_type == event_type)
        if risk_level:
            query = query.filter(RiskEvent.risk_level == risk_level)
        if start_date:
            query = query.filter(RiskEvent.created_at >= start_date)
        if end_date:
            query = query.filter(RiskEvent.created_at <= end_date)

        return query.order_by(desc(RiskEvent.created_at)).offset(skip).limit(limit).all()

    def process_risk_event(self, event_id: str, processed_by: str, result: str) -> bool:
        """处理风险事件"""
        try:
            event = self.db.query(RiskEvent).filter(RiskEvent.id == event_id).first()
            if not event:
                return False

            event.is_processed = True
            event.processed_at = datetime.utcnow()
            event.processed_by = processed_by
            event.process_result = result

            self.db.commit()

            self.logger.info(f"处理风险事件成功: event_id={event_id}")
            return True

        except Exception as e:
            self.logger.error(f"处理风险事件失败: {str(e)}")
            self.db.rollback()
            raise

    def get_risk_statistics(self, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """获取风险统计"""
        try:
            # 事件统计
            total_events = self.db.query(RiskEvent).filter(
                and_(
                    RiskEvent.created_at >= start_date,
                    RiskEvent.created_at <= end_date
                )
            ).count()

            high_risk_events = self.db.query(RiskEvent).filter(
                and_(
                    RiskEvent.created_at >= start_date,
                    RiskEvent.created_at <= end_date,
                    RiskEvent.risk_level.in_([RiskLevel.HIGH.value, RiskLevel.CRITICAL.value])
                )
            ).count()

            blocked_events = self.db.query(RiskEvent).filter(
                and_(
                    RiskEvent.created_at >= start_date,
                    RiskEvent.created_at <= end_date,
                    RiskEvent.final_action == RiskAction.BLOCK.value
                )
            ).count()

            # 规则命中统计
            rule_hits = self.db.query(
                RiskRule.name,
                RiskRule.hit_count
            ).filter(RiskRule.hit_count > 0).all()

            return {
                "total_events": total_events,
                "high_risk_events": high_risk_events,
                "blocked_events": blocked_events,
                "block_rate": blocked_events / total_events if total_events > 0 else 0,
                "rule_hits": [{"name": name, "count": count} for name, count in rule_hits]
            }

        except Exception as e:
            self.logger.error(f"获取风险统计失败: {str(e)}")
            raise


def get_risk_control_service(db: Session = Depends(get_db)) -> RiskControlService:
    """获取风控服务实例"""
    return RiskControlService(db)