"""
SLA报告服务

功能：
1. 生成日报/周报/月报
2. SLA达成率统计
3. 违约事件记录
4. 趋势分析

版本: 1.0
更新日期: 2026-01-22
"""

from datetime import datetime, timedelta
from typing import List, Dict, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func, and_

from app.models.sla import (
    SLAAgreement, SLAMetric, SLAViolation, PerformanceLog,
    MetricType, ViolationSeverity, SLALevel
)


class SLAReportService:
    """SLA报告服务"""

    def __init__(self, db: Session):
        """
        初始化SLA报告服务

        Args:
            db: 数据库会话
        """
        self.db = db

    def generate_daily_report(self, agreement_id: int, date: str = None) -> Dict:
        """
        生成日报

        Args:
            agreement_id: 协议ID
            date: 日期（YYYY-MM-DD），默认为今天

        Returns:
            Dict: 日报数据
        """
        if date is None:
            target_date = datetime.utcnow().date()
        else:
            target_date = datetime.strptime(date, "%Y-%m-%d").date()

        start_time = datetime.combine(target_date, datetime.min.time())
        end_time = datetime.combine(target_date, datetime.max.time())

        return self._generate_report(
            agreement_id=agreement_id,
            start_time=start_time,
            end_time=end_time,
            report_type="daily",
            period_name=target_date.strftime("%Y-%m-%d")
        )

    def generate_weekly_report(self, agreement_id: int, week_start: str = None) -> Dict:
        """
        生成周报

        Args:
            agreement_id: 协议ID
            week_start: 周开始日期（YYYY-MM-DD），默认为本周一

        Returns:
            Dict: 周报数据
        """
        if week_start is None:
            today = datetime.utcnow().date()
            start_date = today - timedelta(days=today.weekday())
        else:
            start_date = datetime.strptime(week_start, "%Y-%m-%d").date()

        start_time = datetime.combine(start_date, datetime.min.time())
        end_time = start_time + timedelta(days=7)

        return self._generate_report(
            agreement_id=agreement_id,
            start_time=start_time,
            end_time=end_time,
            report_type="weekly",
            period_name=f"{start_date.strftime('%Y-%m-%d')} ~ {(start_date + timedelta(days=6)).strftime('%Y-%m-%d')}"
        )

    def generate_monthly_report(self, agreement_id: int, year: int = None, month: int = None) -> Dict:
        """
        生成月报

        Args:
            agreement_id: 协议ID
            year: 年份，默认为当前年
            month: 月份，默认为当前月

        Returns:
            Dict: 月报数据
        """
        if year is None or month is None:
            today = datetime.utcnow()
            year = today.year
            month = today.month

        start_time = datetime(year, month, 1)
        if month == 12:
            end_time = datetime(year + 1, 1, 1)
        else:
            end_time = datetime(year, month + 1, 1)

        return self._generate_report(
            agreement_id=agreement_id,
            start_time=start_time,
            end_time=end_time,
            report_type="monthly",
            period_name=f"{year}-{month:02d}"
        )

    def _generate_report(
        self,
        agreement_id: int,
        start_time: datetime,
        end_time: datetime,
        report_type: str,
        period_name: str
    ) -> Dict:
        """
        生成报告

        Args:
            agreement_id: 协议ID
            start_time: 开始时间
            end_time: 结束时间
            report_type: 报告类型
            period_name: 周期名称

        Returns:
            Dict: 报告数据
        """
        # 获取协议
        agreement = self.db.query(SLAAgreement).filter(
            SLAAgreement.id == agreement_id
        ).first()

        if not agreement:
            return {"error": "Agreement not found"}

        start_ts = start_time.isoformat()
        end_ts = end_time.isoformat()

        # 获取指标数据
        metrics = self.db.query(SLAMetric).filter(
            SLAMetric.agreement_id == agreement_id,
            SLAMetric.period_start >= start_ts,
            SLAMetric.period_end <= end_ts,
            SLAMetric.deleted_at.is_(None)
        ).all()

        # 获取违约记录
        violations = self.db.query(SLAViolation).filter(
            SLAViolation.agreement_id == agreement_id,
            SLAViolation.violation_time >= start_ts,
            SLAViolation.violation_time <= end_ts,
            SLAViolation.deleted_at.is_(None)
        ).all()

        # 统计各类指标
        availability_metrics = [m for m in metrics if m.metric_type == MetricType.AVAILABILITY]
        response_time_metrics = [m for m in metrics if m.metric_type == MetricType.RESPONSE_TIME]
        error_rate_metrics = [m for m in metrics if m.metric_type == MetricType.ERROR_RATE]

        # 计算总体达成率
        total_metrics = len(metrics)
        compliant_metrics = len([m for m in metrics if m.is_compliant])
        overall_achievement_rate = (compliant_metrics / total_metrics * 100) if total_metrics > 0 else 0

        # 构建报告
        report = {
            "report_type": report_type,
            "period": period_name,
            "generated_at": datetime.utcnow().isoformat(),
            "agreement": {
                "id": agreement.id,
                "name": agreement.name,
                "level": agreement.level.value,
            },
            "summary": {
                "overall_achievement_rate": round(overall_achievement_rate, 2),
                "total_metrics": total_metrics,
                "compliant_metrics": compliant_metrics,
                "violation_count": len(violations),
                "is_compliant": len(violations) == 0,
            },
            "metrics": {
                "availability": self._aggregate_metrics(availability_metrics, agreement.availability_target),
                "response_time": self._aggregate_metrics(response_time_metrics, agreement.response_time_target),
                "error_rate": self._aggregate_metrics(error_rate_metrics, agreement.error_rate_target),
            },
            "violations": self._summarize_violations(violations),
            "trends": self._analyze_trends(agreement_id, start_time, end_time),
            "recommendations": self._generate_recommendations(metrics, violations),
        }

        return report

    def _aggregate_metrics(self, metrics: List[SLAMetric], target: float) -> Dict:
        """
        聚合指标数据

        Args:
            metrics: 指标列表
            target: 目标值

        Returns:
            Dict: 聚合数据
        """
        if not metrics:
            return {
                "target": target,
                "avg_actual": 0,
                "min_actual": 0,
                "max_actual": 0,
                "achievement_rate": 0,
                "compliant_count": 0,
                "total_count": 0,
                "compliance_rate": 0,
            }

        actual_values = [m.actual_value for m in metrics]
        compliant_count = len([m for m in metrics if m.is_compliant])

        return {
            "target": target,
            "avg_actual": round(sum(actual_values) / len(actual_values), 2),
            "min_actual": round(min(actual_values), 2),
            "max_actual": round(max(actual_values), 2),
            "achievement_rate": round(sum(m.achievement_rate for m in metrics) / len(metrics), 2),
            "compliant_count": compliant_count,
            "total_count": len(metrics),
            "compliance_rate": round((compliant_count / len(metrics)) * 100, 2),
        }

    def _summarize_violations(self, violations: List[SLAViolation]) -> Dict:
        """
        汇总违约信息

        Args:
            violations: 违约列表

        Returns:
            Dict: 违约汇总
        """
        if not violations:
            return {
                "total_count": 0,
                "by_severity": {},
                "by_metric": {},
                "recent_violations": [],
            }

        # 按严重程度分组
        by_severity = {}
        for severity in ViolationSeverity:
            count = len([v for v in violations if v.severity == severity])
            if count > 0:
                by_severity[severity.value] = count

        # 按指标类型分组
        by_metric = {}
        for metric_type in MetricType:
            count = len([v for v in violations if v.metric_type == metric_type])
            if count > 0:
                by_metric[metric_type.value] = count

        # 最近的违约记录（最多10条）
        recent_violations = sorted(violations, key=lambda v: v.violation_time, reverse=True)[:10]

        return {
            "total_count": len(violations),
            "by_severity": by_severity,
            "by_metric": by_metric,
            "recent_violations": [v.to_dict() for v in recent_violations],
        }

    def _analyze_trends(
        self,
        agreement_id: int,
        start_time: datetime,
        end_time: datetime
    ) -> Dict:
        """
        分析趋势

        Args:
            agreement_id: 协议ID
            start_time: 开始时间
            end_time: 结束时间

        Returns:
            Dict: 趋势分析
        """
        # 获取历史数据（过去30天）
        history_start = start_time - timedelta(days=30)
        history_start_ts = history_start.isoformat()

        metrics = self.db.query(SLAMetric).filter(
            SLAMetric.agreement_id == agreement_id,
            SLAMetric.period_start >= history_start_ts,
            SLAMetric.deleted_at.is_(None)
        ).order_by(SLAMetric.period_start).all()

        if not metrics:
            return {
                "availability_trend": "stable",
                "response_time_trend": "stable",
                "error_rate_trend": "stable",
                "overall_trend": "stable",
            }

        # 分析可用性趋势
        availability_metrics = [m for m in metrics if m.metric_type == MetricType.AVAILABILITY]
        availability_trend = self._calculate_trend([m.actual_value for m in availability_metrics])

        # 分析响应时间趋势
        response_time_metrics = [m for m in metrics if m.metric_type == MetricType.RESPONSE_TIME]
        response_time_trend = self._calculate_trend([m.actual_value for m in response_time_metrics])

        # 分析错误率趋势
        error_rate_metrics = [m for m in metrics if m.metric_type == MetricType.ERROR_RATE]
        error_rate_trend = self._calculate_trend([m.actual_value for m in error_rate_metrics])

        # 综合趋势
        trends = [availability_trend, response_time_trend, error_rate_trend]
        if "deteriorating" in trends:
            overall_trend = "deteriorating"
        elif "improving" in trends:
            overall_trend = "improving"
        else:
            overall_trend = "stable"

        return {
            "availability_trend": availability_trend,
            "response_time_trend": response_time_trend,
            "error_rate_trend": error_rate_trend,
            "overall_trend": overall_trend,
        }

    def _calculate_trend(self, values: List[float]) -> str:
        """
        计算趋势

        Args:
            values: 数值列表

        Returns:
            str: 趋势（improving/stable/deteriorating）
        """
        if len(values) < 2:
            return "stable"

        # 简单的线性趋势分析
        first_half = values[:len(values)//2]
        second_half = values[len(values)//2:]

        avg_first = sum(first_half) / len(first_half)
        avg_second = sum(second_half) / len(second_half)

        # Safe division: if avg_first is 0, treat as stable
        if avg_first == 0:
            return "stable"

        change_rate = ((avg_second - avg_first) / avg_first) * 100

        if change_rate > 5:
            return "improving"
        elif change_rate < -5:
            return "deteriorating"
        else:
            return "stable"

    def _generate_recommendations(
        self,
        metrics: List[SLAMetric],
        violations: List[SLAViolation]
    ) -> List[str]:
        """
        生成建议

        Args:
            metrics: 指标列表
            violations: 违约列表

        Returns:
            List[str]: 建议列表
        """
        recommendations = []

        # 检查违约情况
        if len(violations) > 0:
            recommendations.append("检测到SLA违约，建议立即调查根本原因并采取纠正措施。")

            # 按严重程度分析
            critical_violations = [v for v in violations if v.severity == ViolationSeverity.CRITICAL]
            if critical_violations:
                recommendations.append("存在严重违约事件，建议启动应急响应流程。")

        # 检查可用性
        availability_metrics = [m for m in metrics if m.metric_type == MetricType.AVAILABILITY]
        if availability_metrics:
            avg_availability = sum(m.actual_value for m in availability_metrics) / len(availability_metrics)
            if avg_availability < 99.0:
                recommendations.append("可用性低于99%，建议检查系统稳定性和容错机制。")

        # 检查响应时间
        response_time_metrics = [m for m in metrics if m.metric_type == MetricType.RESPONSE_TIME]
        if response_time_metrics:
            avg_response_time = sum(m.actual_value for m in response_time_metrics) / len(response_time_metrics)
            if avg_response_time > 2000:
                recommendations.append("平均响应时间超过2秒，建议进行性能优化。")

        # 检查错误率
        error_rate_metrics = [m for m in metrics if m.metric_type == MetricType.ERROR_RATE]
        if error_rate_metrics:
            avg_error_rate = sum(m.actual_value for m in error_rate_metrics) / len(error_rate_metrics)
            if avg_error_rate > 1.0:
                recommendations.append("错误率超过1%，建议加强错误处理和监控。")

        # 如果没有问题
        if not recommendations:
            recommendations.append("所有SLA指标均达标，系统运行良好。")

        return recommendations

    def get_achievement_summary(self, agreement_id: int, days: int = 30) -> Dict:
        """
        获取达成率汇总

        Args:
            agreement_id: 协议ID
            days: 统计天数

        Returns:
            Dict: 达成率汇总
        """
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(days=days)
        start_ts = start_time.isoformat()

        metrics = self.db.query(SLAMetric).filter(
            SLAMetric.agreement_id == agreement_id,
            SLAMetric.period_start >= start_ts,
            SLAMetric.deleted_at.is_(None)
        ).all()

        if not metrics:
            return {
                "period_days": days,
                "overall_achievement_rate": 0,
                "by_metric": {},
            }

        # 总体达成率
        compliant_count = len([m for m in metrics if m.is_compliant])
        overall_achievement_rate = (compliant_count / len(metrics)) * 100

        # 按指标类型统计
        by_metric = {}
        for metric_type in MetricType:
            type_metrics = [m for m in metrics if m.metric_type == metric_type]
            if type_metrics:
                type_compliant = len([m for m in type_metrics if m.is_compliant])
                by_metric[metric_type.value] = {
                    "achievement_rate": round((type_compliant / len(type_metrics)) * 100, 2),
                    "total_count": len(type_metrics),
                    "compliant_count": type_compliant,
                }

        return {
            "period_days": days,
            "overall_achievement_rate": round(overall_achievement_rate, 2),
            "by_metric": by_metric,
        }

    def export_report(self, report: Dict, format: str = "json") -> str:
        """
        导出报告

        Args:
            report: 报告数据
            format: 导出格式（json/csv/pdf）

        Returns:
            str: 导出的报告内容

        Raises:
            ValueError: 不支持的导出格式
        """
        if format == "json":
            import json
            return json.dumps(report, indent=2, ensure_ascii=False)

        elif format == "csv":
            # CSV导出: 转换为表格格式
            import csv
            import io

            output = io.StringIO()
            writer = csv.writer(output)

            # 写入头部信息
            writer.writerow(["报告类型", report.get("report_type", "N/A")])
            writer.writerow(["统计周期", report.get("period", "N/A")])
            writer.writerow(["生成时间", report.get("generated_at", "N/A")])
            writer.writerow([])

            # 写入汇总信息
            summary = report.get("summary", {})
            writer.writerow(["总体达成率(%)", summary.get("overall_achievement_rate", 0)])
            writer.writerow(["总指标数", summary.get("total_metrics", 0)])
            writer.writerow(["达标指标数", summary.get("compliant_metrics", 0)])
            writer.writerow(["违约次数", summary.get("violation_count", 0)])
            writer.writerow([])

            # 写入建议信息
            recommendations = report.get("recommendations", [])
            for i, rec in enumerate(recommendations, 1):
                writer.writerow([f"建议{i}", rec])

            return output.getvalue()

        elif format == "pdf":
            # PDF导出: 建议使用第三方库（reportlab、pypdf等）
            # 这里返回JSON内容作为临时方案，生产环境应集成真实PDF库
            raise NotImplementedError("PDF export requires reportlab library. Use json or csv format instead.")

        else:
            raise ValueError(f"Unsupported format: {format}")
