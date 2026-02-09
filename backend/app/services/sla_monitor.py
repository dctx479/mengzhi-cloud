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
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_

from app.models.sla import (
    SLAAgreement, SLAMetric, SLAViolation, PerformanceLog,
    MetricType, ViolationSeverity, SLALevel
)
from app.services.notification_service import NotificationService


class SLAMonitor:
    """SLA监控服务"""

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
        # 获取所有活跃的协议
        agreements = self.db.query(SLAAgreement).filter(
            SLAAgreement.is_active == True,
            SLAAgreement.deleted_at.is_(None)
        ).all()

        results = {
            "total_agreements": len(agreements),
            "compliant": 0,
            "violations": 0,
            "details": []
        }

        for agreement in agreements:
            # 监控单个协议
            result = self.monitor_agreement(agreement.id)
            results["details"].append(result)

            if result["is_compliant"]:
                results["compliant"] += 1
            else:
                results["violations"] += 1

        return results

    def monitor_agreement(self, agreement_id: int) -> Dict:
        """
        监控单个SLA协议

        Args:
            agreement_id: 协议ID

        Returns:
            Dict: 监控结果
        """
        # 获取协议
        agreement = self.db.query(SLAAgreement).filter(
            SLAAgreement.id == agreement_id
        ).first()

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
            violations.append({
                "metric": "availability",
                "target": agreement.availability_target,
                "actual": availability["actual"],
                "severity": self._calculate_severity(
                    agreement.availability_target,
                    availability["actual"],
                    "availability"
                )
            })
            is_compliant = False

        # 检查响应时间
        if response_time["avg"] > agreement.response_time_target:
            violations.append({
                "metric": "response_time",
                "target": agreement.response_time_target,
                "actual": response_time["avg"],
                "severity": self._calculate_severity(
                    agreement.response_time_target,
                    response_time["avg"],
                    "response_time"
                )
            })
            is_compliant = False

        # 检查错误率
        if error_rate["actual"] > agreement.error_rate_target:
            violations.append({
                "metric": "error_rate",
                "target": agreement.error_rate_target,
                "actual": error_rate["actual"],
                "severity": self._calculate_severity(
                    agreement.error_rate_target,
                    error_rate["actual"],
                    "error_rate"
                )
            })
            is_compliant = False

        # 记录违约
        if violations:
            for violation in violations:
                self._record_violation(agreement, violation, start_time, end_time)

        # 记录指标
        self._record_metrics(
            agreement,
            start_time,
            end_time,
            availability,
            response_time,
            error_rate,
            throughput,
            is_compliant
        )

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

    def _calculate_availability(
        self,
        start_time: datetime,
        end_time: datetime,
        agreement: SLAAgreement
    ) -> Dict:
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
        query = self.db.query(PerformanceLog).filter(
            PerformanceLog.timestamp >= start_time.isoformat(),
            PerformanceLog.timestamp <= end_time.isoformat(),
            PerformanceLog.deleted_at.is_(None)
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

    def _calculate_response_time(
        self,
        start_time: datetime,
        end_time: datetime,
        agreement: SLAAgreement
    ) -> Dict:
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
        query = self.db.query(PerformanceLog).filter(
            PerformanceLog.timestamp >= start_time.isoformat(),
            PerformanceLog.timestamp <= end_time.isoformat(),
            PerformanceLog.is_success == True,
            PerformanceLog.deleted_at.is_(None)
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

    def _calculate_error_rate(
        self,
        start_time: datetime,
        end_time: datetime,
        agreement: SLAAgreement
    ) -> Dict:
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
        query = self.db.query(PerformanceLog).filter(
            PerformanceLog.timestamp >= start_time.isoformat(),
            PerformanceLog.timestamp <= end_time.isoformat(),
            PerformanceLog.deleted_at.is_(None)
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

    def _calculate_throughput(
        self,
        start_time: datetime,
        end_time: datetime,
        agreement: SLAAgreement
    ) -> Dict:
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
        query = self.db.query(PerformanceLog).filter(
            PerformanceLog.timestamp >= start_time.isoformat(),
            PerformanceLog.timestamp <= end_time.isoformat(),
            PerformanceLog.deleted_at.is_(None)
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

    def _calculate_severity(
        self,
        target: float,
        actual: float,
        metric_type: str
    ) -> ViolationSeverity:
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
        if metric_type in ["availability", "throughput"]:
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
        self,
        agreement: SLAAgreement,
        violation: Dict,
        start_time: datetime,
        end_time: datetime
    ):
        """
        记录违约

        Args:
            agreement: SLA协议
            violation: 违约信息
            start_time: 开始时间
            end_time: 结束时间
        """
        metric_type_map = {
            "availability": MetricType.AVAILABILITY,
            "response_time": MetricType.RESPONSE_TIME,
            "error_rate": MetricType.ERROR_RATE,
            "throughput": MetricType.THROUGHPUT,
        }

        target = violation["target"]
        actual = violation["actual"]
        deviation = abs(actual - target)
        deviation_rate = (deviation / target) * 100

        # 创建违约记录
        violation_record = SLAViolation(
            agreement_id=agreement.id,
            metric_type=metric_type_map[violation["metric"]],
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
        self.db.commit()

        # 发送告警
        self._send_alert(agreement, violation_record)

    def _record_metrics(
        self,
        agreement: SLAAgreement,
        start_time: datetime,
        end_time: datetime,
        availability: Dict,
        response_time: Dict,
        error_rate: Dict,
        throughput: Dict,
        is_compliant: bool
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
        # 记录可用性指标
        availability_metric = SLAMetric(
            agreement_id=agreement.id,
            metric_type=MetricType.AVAILABILITY,
            metric_name="可用性",
            period_start=start_time.isoformat(),
            period_end=end_time.isoformat(),
            target_value=availability["target"],
            actual_value=availability["actual"],
            achievement_rate=(availability["actual"] / availability["target"]) * 100,
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
            period_start=start_time.isoformat(),
            period_end=end_time.isoformat(),
            target_value=response_time["target"],
            actual_value=response_time["avg"],
            achievement_rate=(response_time["target"] / max(response_time["avg"], 1)) * 100,
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
            period_start=start_time.isoformat(),
            period_end=end_time.isoformat(),
            target_value=error_rate["target"],
            actual_value=error_rate["actual"],
            achievement_rate=(error_rate["target"] / max(error_rate["actual"], 0.01)) * 100,
            total_requests=error_rate["total_requests"],
            failed_requests=error_rate["failed_requests"],
            is_compliant=error_rate["is_compliant"],
        )
        self.db.add(error_rate_metric)

        self.db.commit()

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

            # 发送通知（这里可以集成邮件、短信、钉钉等）
            print(f"[SLA ALERT] {message}")

            # TODO: 集成实际的通知服务
            # self.notification_service.send_alert(
            #     title="SLA违约告警",
            #     message=message,
            #     severity=violation.severity.value,
            #     recipients=[...]
            # )

        except Exception as e:
            print(f"Failed to send alert: {str(e)}")

    @staticmethod
    def _percentile(values: List[float], percentile: int) -> float:
        """
        计算百分位数

        Args:
            values: 已排序的数值列表
            percentile: 百分位（0-100）

        Returns:
            float: 百分位数值
        """
        if not values:
            return 0.0

        index = int(len(values) * (percentile / 100))
        index = min(index, len(values) - 1)
        return values[index]

    def get_realtime_metrics(self, agreement_id: int) -> Dict:
        """
        获取实时指标

        Args:
            agreement_id: 协议ID

        Returns:
            Dict: 实时指标数据
        """
        return self.monitor_agreement(agreement_id)

    def get_violation_history(
        self,
        agreement_id: int,
        days: int = 7
    ) -> List[Dict]:
        """
        获取违约历史

        Args:
            agreement_id: 协议ID
            days: 查询天数

        Returns:
            List[Dict]: 违约历史列表
        """
        start_time = datetime.utcnow() - timedelta(days=days)

        violations = self.db.query(SLAViolation).filter(
            SLAViolation.agreement_id == agreement_id,
            SLAViolation.violation_time >= start_time.isoformat(),
            SLAViolation.deleted_at.is_(None)
        ).order_by(SLAViolation.violation_time.desc()).all()

        return [v.to_dict() for v in violations]
