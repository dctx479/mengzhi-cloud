"""
SLA监控服务

功能：
1. 实时监控SLA指标
2. 计算SLA达成率
3. SLA违约检测
4. 自动告警

版本: 1.0
更新日期: 2026-01-22
"""

from datetime import datetime, timedelta
from typing import List, Dict, Optional
import asyncio
import threading
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_
from loguru import logger

from app.models.sla import (
    SLAAgreement,
    SLAMetric,
    SLAViolation,
    PerformanceLog,
    MetricType,
    ViolationSeverity,
    SLALevel,
)
from app.services.notification_service import NotificationService
from app.core.errors import BusinessException, ErrorCode


class SLAMonitor:
    """SLA监控服务"""

    # 类级别锁，防止定时任务并发重复执行 monitor_all_agreements
    _monitor_lock = threading.Lock()

    def __init__(self, db: Session):
        """
        初始化SLA监控服务

        Args:
            db: 数据库会话
        """
        self.db = db
        self.notification_service = NotificationService()

    def monitor_all_agreements(self) -> Dict:
        """
        监控所有活跃的SLA协议

        Returns:
            Dict: 监控结果
        """
        # 使用类级别锁防止定时任务并发重复执行
        if not SLAMonitor._monitor_lock.acquire(blocking=False):
            logger.warning("monitor_all_agreements is already running, skipping this invocation")
            return {"skipped": True, "reason": "concurrent execution prevented"}

        try:
            # 获取所有活跃的协议
            agreements = (
                self.db.query(SLAAgreement).filter(SLAAgreement.is_active == True, SLAAgreement.deleted_at.is_(None)).all()
            )

            results = {"total_agreements": len(agreements), "compliant": 0, "violations": 0, "details": []}

            for agreement in agreements:
                # 监控单个协议
                result = self.monitor_agreement(agreement.id)
                results["details"].append(result)

                if result.get("is_compliant"):
                    results["compliant"] += 1
                else:
                    results["violations"] += 1

            return results
        finally:
            SLAMonitor._monitor_lock.release()

    def monitor_agreement(self, agreement_id: int) -> Dict:
        """
        监控单个SLA协议

        Args:
            agreement_id: 协议ID

        Returns:
            Dict: 监控结果
        """
        # 获取协议
        agreement = self.db.query(SLAAgreement).filter(SLAAgreement.id == agreement_id).first()

        if not agreement:
            return {"error": "Agreement not found"}

        # 获取最近1小时的性能数据
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(hours=1)

        # 计算各项指标
        availability = self._calculate_availability(start_time, end_time, agreement)
        response_time = self._calculate_response_time(start_time, end_time, agreement)
        error_rate = self._calculate_error_rate(start_time, end_time, agreement)
        throughput = self._calculate_throughput(start_time, end_time, agreement)

        # 检查是否违约
        violations = []
        is_compliant = True

        # 检查可用性
        if availability["actual"] < agreement.availability_target:
            violations.append(
                {
                    "metric": "availability",
                    "target": agreement.availability_target,
                    "actual": availability["actual"],
                    "severity": self._calculate_severity(
                        agreement.availability_target, availability["actual"], "availability"
                    ),
                }
            )
            is_compliant = False

        # 检查响应时间
        if response_time["avg"] > agreement.response_time_target:
            violations.append(
                {
                    "metric": "response_time",
                    "target": agreement.response_time_target,
                    "actual": response_time["avg"],
                    "severity": self._calculate_severity(
                        agreement.response_time_target, response_time["avg"], "response_time"
                    ),
                }
            )
            is_compliant = False

        # 检查错误率
        if error_rate["actual"] > agreement.error_rate_target:
            violations.append(
                {
                    "metric": "error_rate",
                    "target": agreement.error_rate_target,
                    "actual": error_rate["actual"],
                    "severity": self._calculate_severity(
                        agreement.error_rate_target, error_rate["actual"], "error_rate"
                    ),
                }
            )
            is_compliant = False

        # P0-015修复: 添加事务管理，确保数据一致性
        # 收集待发送的告警，commit 成功后再发，避免"告警已发但记录未持久化"
        pending_alerts: List[tuple] = []  # (agreement, violation_record)
        try:
            if violations:
                for violation in violations:
                    violation_record = self._record_violation(agreement, violation, start_time, end_time)
                    if violation_record is not None:
                        pending_alerts.append((agreement, violation_record))

            # 记录指标
            self._record_metrics(
                agreement, start_time, end_time, availability, response_time, error_rate, throughput, is_compliant
            )

            # 提交事务（将所有flush的记录持久化）
            self.db.commit()
            logger.info(f"SLA evaluation completed for agreement {agreement_id}: is_compliant={is_compliant}")

        except Exception as e:
            # 回滚所有未提交的更改
            self.db.rollback()
            logger.error(f"SLA evaluation failed for agreement {agreement_id}: {str(e)}")
            raise BusinessException(
                code=ErrorCode.SYSTEM_ERROR,
                message="SLA evaluation failed"
            )

        # commit 成功后再发送告警，确保持久化与告警一致
        for alert_agreement, alert_violation in pending_alerts:
            self._send_alert(alert_agreement, alert_violation)

        return {
            "agreement_id": agreement_id,
            "agreement_name": agreement.name,
            "is_compliant": is_compliant,
            "metrics": {
                "availability": availability,
                "response_time": response_time,
                "error_rate": error_rate,
                "throughput": throughput,
            },
            "violations": violations,
        }

    def _calculate_availability(self, start_time: datetime, end_time: datetime, agreement: SLAAgreement) -> Dict:
        """
        计算可用性

        Args:
            start_time: 开始时间
            end_time: 结束时间
            agreement: SLA协议

        Returns:
            Dict: 可用性数据
        """
        # 查询性能日志
        # Note: PerformanceLog.timestamp is String field, stored as ISO format
        start_ts = start_time.isoformat()
        end_ts = end_time.isoformat()
        query = self.db.query(PerformanceLog).filter(
            PerformanceLog.timestamp >= start_ts,
            PerformanceLog.timestamp <= end_ts,
            PerformanceLog.deleted_at.is_(None),
        )

        # 如果协议关联了企业或用户，过滤数据
        if agreement.enterprise_id:
            query = query.filter(PerformanceLog.enterprise_id == agreement.enterprise_id)
        elif agreement.user_id:
            query = query.filter(PerformanceLog.user_id == agreement.user_id)

        total_requests = query.count()
        successful_requests = query.filter(PerformanceLog.is_success == True).count()

        if total_requests == 0:
            availability = 100.0
        else:
            availability = (successful_requests / total_requests) * 100

        return {
            "target": agreement.availability_target,
            "actual": round(availability, 2),
            "total_requests": total_requests,
            "successful_requests": successful_requests,
            "is_compliant": availability >= agreement.availability_target,
        }

    def _calculate_response_time(self, start_time: datetime, end_time: datetime, agreement: SLAAgreement) -> Dict:
        """
        计算响应时间

        Args:
            start_time: 开始时间
            end_time: 结束时间
            agreement: SLA协议

        Returns:
            Dict: 响应时间数据
        """
        # 查询性能日志
        # Note: PerformanceLog.timestamp is String field, stored as ISO format
        start_ts = start_time.isoformat()
        end_ts = end_time.isoformat()
        query = self.db.query(PerformanceLog).filter(
            PerformanceLog.timestamp >= start_ts,
            PerformanceLog.timestamp <= end_ts,
            PerformanceLog.is_success == True,
            PerformanceLog.deleted_at.is_(None),
        )

        # 如果协议关联了企业或用户，过滤数据
        if agreement.enterprise_id:
            query = query.filter(PerformanceLog.enterprise_id == agreement.enterprise_id)
        elif agreement.user_id:
            query = query.filter(PerformanceLog.user_id == agreement.user_id)

        logs = query.all()

        if not logs:
            return {
                "target": agreement.response_time_target,
                "avg": 0,
                "min": 0,
                "max": 0,
                "p50": 0,
                "p95": 0,
                "p99": 0,
                "is_compliant": True,
            }

        response_times = [log.response_time for log in logs]
        response_times.sort()

        avg_time = sum(response_times) / len(response_times)
        min_time = min(response_times)
        max_time = max(response_times)
        p50 = self._percentile(response_times, 50)
        p95 = self._percentile(response_times, 95)
        p99 = self._percentile(response_times, 99)

        return {
            "target": agreement.response_time_target,
            "avg": round(avg_time, 2),
            "min": round(min_time, 2),
            "max": round(max_time, 2),
            "p50": round(p50, 2),
            "p95": round(p95, 2),
            "p99": round(p99, 2),
            "is_compliant": avg_time <= agreement.response_time_target,
        }

    def _calculate_error_rate(self, start_time: datetime, end_time: datetime, agreement: SLAAgreement) -> Dict:
        """
        计算错误率

        Args:
            start_time: 开始时间
            end_time: 结束时间
            agreement: SLA协议

        Returns:
            Dict: 错误率数据
        """
        # 查询性能日志
        # Note: PerformanceLog.timestamp is String field, stored as ISO format
        start_ts = start_time.isoformat()
        end_ts = end_time.isoformat()
        query = self.db.query(PerformanceLog).filter(
            PerformanceLog.timestamp >= start_ts,
            PerformanceLog.timestamp <= end_ts,
            PerformanceLog.deleted_at.is_(None),
        )

        # 如果协议关联了企业或用户，过滤数据
        if agreement.enterprise_id:
            query = query.filter(PerformanceLog.enterprise_id == agreement.enterprise_id)
        elif agreement.user_id:
            query = query.filter(PerformanceLog.user_id == agreement.user_id)

        total_requests = query.count()
        failed_requests = query.filter(PerformanceLog.is_success == False).count()

        if total_requests == 0:
            error_rate = 0.0
        else:
            error_rate = (failed_requests / total_requests) * 100

        return {
            "target": agreement.error_rate_target,
            "actual": round(error_rate, 2),
            "total_requests": total_requests,
            "failed_requests": failed_requests,
            "is_compliant": error_rate <= agreement.error_rate_target,
        }

    def _calculate_throughput(self, start_time: datetime, end_time: datetime, agreement: SLAAgreement) -> Dict:
        """
        计算吞吐量

        Args:
            start_time: 开始时间
            end_time: 结束时间
            agreement: SLA协议

        Returns:
            Dict: 吞吐量数据
        """
        # 查询性能日志
        # Note: PerformanceLog.timestamp is String field, stored as ISO format
        start_ts = start_time.isoformat()
        end_ts = end_time.isoformat()
        query = self.db.query(PerformanceLog).filter(
            PerformanceLog.timestamp >= start_ts,
            PerformanceLog.timestamp <= end_ts,
            PerformanceLog.deleted_at.is_(None),
        )

        # 如果协议关联了企业或用户，过滤数据
        if agreement.enterprise_id:
            query = query.filter(PerformanceLog.enterprise_id == agreement.enterprise_id)
        elif agreement.user_id:
            query = query.filter(PerformanceLog.user_id == agreement.user_id)

        total_requests = query.count()

        # 计算时间差（秒）
        duration = (end_time - start_time).total_seconds()
        if duration == 0:
            throughput = 0
        else:
            throughput = total_requests / duration

        return {
            "target": agreement.throughput_target,
            "actual": round(throughput, 2),
            "total_requests": total_requests,
            "duration_seconds": duration,
            "is_compliant": throughput >= agreement.throughput_target,
        }

    def _calculate_severity(self, target: float, actual: float, metric_type: str) -> ViolationSeverity:
        """
        计算违约严重程度

        Args:
            target: 目标值
            actual: 实际值
            metric_type: 指标类型

        Returns:
            ViolationSeverity: 严重程度
        """
        # 计算偏差率
        if target == 0:
            # 目标为0时无法计算相对偏差，直接按绝对值判断
            deviation_rate = actual * 100 if metric_type not in ["availability", "throughput"] else 100.0
        elif metric_type in ["availability", "throughput"]:
            # 这些指标是越高越好
            deviation_rate = ((target - actual) / target) * 100
        else:
            # 这些指标是越低越好
            deviation_rate = ((actual - target) / target) * 100

        # 根据偏差率判断严重程度
        if deviation_rate >= 50:
            return ViolationSeverity.CRITICAL
        elif deviation_rate >= 20:
            return ViolationSeverity.HIGH
        elif deviation_rate >= 10:
            return ViolationSeverity.MEDIUM
        else:
            return ViolationSeverity.LOW

    def _record_violation(
        self, agreement: SLAAgreement, violation: Dict, start_time: datetime, end_time: datetime
    ) -> Optional[SLAViolation]:
        """
        记录违约（含去重：同一协议同一指标在同一时间窗口内不重复写入）

        Args:
            agreement: SLA协议
            violation: 违约信息
            start_time: 开始时间
            end_time: 结束时间

        Returns:
            新建的 SLAViolation 记录，若因去重跳过则返回 None
        """
        metric_type_map = {
            "availability": MetricType.AVAILABILITY,
            "response_time": MetricType.RESPONSE_TIME,
            "error_rate": MetricType.ERROR_RATE,
            "throughput": MetricType.THROUGHPUT,
        }

        metric_type = metric_type_map[violation["metric"]]
        start_ts = start_time.isoformat()
        end_ts = end_time.isoformat()

        # 去重：检查同一协议、同一指标、同一时间窗口内是否已有违约记录
        existing_violation = self.db.query(SLAViolation).filter(
            SLAViolation.agreement_id == agreement.id,
            SLAViolation.metric_type == metric_type,
            SLAViolation.violation_time >= start_ts,
            SLAViolation.violation_time <= end_ts,
            SLAViolation.deleted_at.is_(None),
        ).first()

        if existing_violation:
            logger.debug(
                f"Skipping duplicate violation for agreement={agreement.id}, "
                f"metric={violation['metric']}, window=[{start_ts}, {end_ts}]"
            )
            return None

        target = violation["target"]
        actual = violation["actual"]
        deviation = abs(actual - target)
        # Guard against zero target to avoid ZeroDivisionError
        deviation_rate = (deviation / target) * 100 if target != 0 else 0.0

        # 创建违约记录
        violation_record = SLAViolation(
            agreement_id=agreement.id,
            metric_type=metric_type,
            severity=violation["severity"],
            target_value=target,
            actual_value=actual,
            deviation=deviation,
            deviation_rate=round(deviation_rate, 2),
            violation_time=datetime.utcnow().isoformat(),
            duration=int((end_time - start_time).total_seconds()),
            description=f"{violation['metric']} violated: target={target}, actual={actual}",
        )

        self.db.add(violation_record)
        self.db.flush()  # Flush to generate ID; alert is sent by caller after commit
        return violation_record

    def _record_metrics(
        self,
        agreement: SLAAgreement,
        start_time: datetime,
        end_time: datetime,
        availability: Dict,
        response_time: Dict,
        error_rate: Dict,
        throughput: Dict,
        is_compliant: bool,
    ):
        """
        记录SLA指标

        Args:
            agreement: SLA协议
            start_time: 开始时间
            end_time: 结束时间
            availability: 可用性数据
            response_time: 响应时间数据
            error_rate: 错误率数据
            throughput: 吞吐量数据
            is_compliant: 是否达标
        """
        start_ts = start_time.isoformat()
        end_ts = end_time.isoformat()

        # 记录可用性指标
        availability_metric = SLAMetric(
            agreement_id=agreement.id,
            metric_type=MetricType.AVAILABILITY,
            metric_name="可用性",
            period_start=start_ts,
            period_end=end_ts,
            target_value=availability["target"],
            actual_value=availability["actual"],
            achievement_rate=(availability["actual"] / max(availability["target"], 0.01)) * 100,
            total_requests=availability["total_requests"],
            successful_requests=availability["successful_requests"],
            failed_requests=availability["total_requests"] - availability["successful_requests"],
            is_compliant=availability["is_compliant"],
        )
        self.db.add(availability_metric)

        # 记录响应时间指标
        response_time_metric = SLAMetric(
            agreement_id=agreement.id,
            metric_type=MetricType.RESPONSE_TIME,
            metric_name="响应时间",
            period_start=start_ts,
            period_end=end_ts,
            target_value=response_time["target"],
            actual_value=response_time["avg"],
            achievement_rate=min((response_time["target"] / max(response_time["avg"], 0.01)) * 100, 100),
            avg_response_time=response_time["avg"],
            min_response_time=response_time["min"],
            max_response_time=response_time["max"],
            p50_response_time=response_time["p50"],
            p95_response_time=response_time["p95"],
            p99_response_time=response_time["p99"],
            is_compliant=response_time["is_compliant"],
        )
        self.db.add(response_time_metric)

        # 记录错误率指标
        error_rate_metric = SLAMetric(
            agreement_id=agreement.id,
            metric_type=MetricType.ERROR_RATE,
            metric_name="错误率",
            period_start=start_ts,
            period_end=end_ts,
            target_value=error_rate["target"],
            actual_value=error_rate["actual"],
            achievement_rate=min((error_rate["target"] / max(error_rate["actual"], 0.01)) * 100, 100),
            total_requests=error_rate["total_requests"],
            failed_requests=error_rate["failed_requests"],
            is_compliant=error_rate["is_compliant"],
        )
        self.db.add(error_rate_metric)

        self.db.flush()  # Do not commit here; outer transaction handles it

    def _send_alert(self, agreement: SLAAgreement, violation: SLAViolation):
        """
        发送告警

        Args:
            agreement: SLA协议
            violation: 违约记录
        """
        try:
            # 构建告警消息
            message = f"""
SLA违约告警

协议: {agreement.name}
等级: {agreement.level.value}
指标: {violation.metric_type.value}
严重程度: {violation.severity.value}

目标值: {violation.target_value}
实际值: {violation.actual_value}
偏差: {violation.deviation} ({violation.deviation_rate}%)

时间: {violation.violation_time}
            """.strip()

            # 发送通知（通过 alert_manager 统一入口；按 severity 映射 level）
            logger.warning(f"[SLA ALERT] {message}")

            SEVERITY_TO_LEVEL = {
                "LOW": "info",
                "MEDIUM": "warning",
                "HIGH": "error",
                "CRITICAL": "critical",
            }
            alert_level = SEVERITY_TO_LEVEL.get(
                violation.severity.value if hasattr(violation.severity, 'value') else str(violation.severity),
                "warning",
            )

            # Fire-and-forget：异步发送告警，不阻塞 SLA 主流程
            try:
                from app.core.alerts import alert_manager
                coro = alert_manager.send_alert(
                    level=alert_level,
                    title=f"SLA违约: {agreement.name}",
                    message=message,
                    extra={
                        "agreement_id": getattr(agreement, 'id', None),
                        "agreement_uuid": getattr(agreement, 'agreement_uuid', None),
                        "violation_id": getattr(violation, 'id', None),
                        "metric_type": violation.metric_type.value if hasattr(violation.metric_type, 'value') else str(violation.metric_type),
                        "severity": violation.severity.value if hasattr(violation.severity, 'value') else str(violation.severity),
                        "deviation_rate": violation.deviation_rate,
                        "enterprise_id": getattr(agreement, 'enterprise_id', None),
                    },
                    enterprise_id=str(getattr(agreement, 'enterprise_id', '')) if getattr(agreement, 'enterprise_id', None) else None,
                )
                try:
                    loop = asyncio.get_running_loop()
                    loop.create_task(coro)
                except RuntimeError:
                    # 没有运行中的事件循环（同步上下文），降级为日志
                    logger.warning(
                        f"[SLA ALERT FALLBACK] level={alert_level} title=SLA违约: {agreement.name} "
                        f"deviation_rate={violation.deviation_rate}%"
                    )
            except Exception as alert_err:
                logger.error(f"集成 alert_manager 失败，回退到日志告警: {alert_err}")

        except Exception as e:
            logger.error(f"Failed to send alert: {str(e)}")

    @staticmethod
    def _percentile(values: List[float], percentile: int) -> float:
        """
        计算百分位数（线性插值法，与 numpy.percentile 默认行为一致）

        Args:
            values: 已排序的数值列表
            percentile: 百分位（0-100）

        Returns:
            float: 百分位数值
        """
        if not values:
            return 0.0

        n = len(values)
        # 线性插值：index = (p/100) * (n-1)
        idx = (percentile / 100) * (n - 1)
        lower = int(idx)
        upper = min(lower + 1, n - 1)
        fraction = idx - lower
        return values[lower] + fraction * (values[upper] - values[lower])

    def get_realtime_metrics(self, agreement_id: int) -> Dict:
        """
        获取实时指标

        Args:
            agreement_id: 协议ID

        Returns:
            Dict: 实时指标数据
        """
        return self.monitor_agreement(agreement_id)

    def get_violation_history(self, agreement_id: int, days: int = 7) -> List[Dict]:
        """
        获取违约历史

        Args:
            agreement_id: 协议ID
            days: 查询天数

        Returns:
            List[Dict]: 违约历史列表
        """
        start_time = datetime.utcnow() - timedelta(days=days)
        start_ts = start_time.isoformat()

        violations = (
            self.db.query(SLAViolation)
            .filter(
                SLAViolation.agreement_id == agreement_id,
                SLAViolation.violation_time >= start_ts,
                SLAViolation.deleted_at.is_(None),
            )
            .order_by(SLAViolation.violation_time.desc())
            .all()
        )

        return [v.to_dict() for v in violations]
