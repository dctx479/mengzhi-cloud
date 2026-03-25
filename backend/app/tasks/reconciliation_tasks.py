"""
对账定时任务

版本: 1.0
创建日期: 2026-01-23
"""

import asyncio
from datetime import datetime, date, timedelta
from typing import Optional
from loguru import logger
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models.reconciliation import ReconciliationType
from app.services.reconciliation_service import ReconciliationService
from app.services.notification_service import NotificationService
from app.core.config import settings


class ReconciliationTasks:
    """对账定时任务类

    提供对账相关的定时任务:
    - 每日自动对账
    - 对账结果通知
    - 差异处理提醒
    """

    def __init__(self):
        """初始化任务"""
        self.notification_service = None

    def get_db(self) -> Session:
        """获取数据库会话"""
        return SessionLocal()

    async def daily_reconciliation_task(self, target_date: Optional[str] = None) -> None:
        """每日自动对账任务

        Args:
            target_date: 目标日期，默认为昨天 (YYYY-MM-DD)
        """
        db = self.get_db()

        try:
            # 确定对账日期
            if target_date is None:
                # 默认对账昨天的数据
                yesterday = date.today() - timedelta(days=1)
                target_date = yesterday.strftime("%Y-%m-%d")

            logger.info(f"开始执行每日对账任务: {target_date}")

            # 检查是否已经对账
            service = ReconciliationService(db)
            existing_record = service.get_daily_reconciliation_status(target_date)

            if existing_record and existing_record.is_success():
                logger.info(f"日期 {target_date} 已完成对账，跳过")
                return

            # 执行对账
            record = service.start_reconciliation(
                reconciliation_date=target_date,
                reconciliation_type=ReconciliationType.DAILY,
                force=False
            )

            logger.info(f"每日对账任务完成: {record.batch_no}")

            # 发送通知
            await self._send_reconciliation_notification(record)

        except Exception as e:
            logger.error(f"每日对账任务失败: {str(e)}")
            # 发送失败通知，即使失败也继续抛出原始异常
            try:
                await self._send_failure_notification(target_date, str(e))
            except Exception as notify_err:
                logger.error(f"发送失败通知也失败了: {str(notify_err)}")
            raise
        finally:
            db.close()

    async def _send_reconciliation_notification(self, record) -> None:
        """发送对账结果通知

        Args:
            record: 对账记录
        """
        try:
            if not self.notification_service:
                self.notification_service = NotificationService()

            # 构建通知内容
            if record.is_success():
                title = f"✅ 对账成功 - {record.reconciliation_date}"
                content = f"""
对账批次: {record.batch_no}
对账日期: {record.reconciliation_date}
本地交易: {record.total_local_count} 笔
第三方交易: {record.total_remote_count} 笔
匹配成功: {record.matched_count} 笔
匹配金额: ¥{record.matched_amount}
执行时长: {record.duration_seconds}秒
                """.strip()
            elif record.status.value == "partial":
                title = f"⚠️ 对账完成(有差异) - {record.reconciliation_date}"
                content = f"""
对账批次: {record.batch_no}
对账日期: {record.reconciliation_date}
本地交易: {record.total_local_count} 笔
第三方交易: {record.total_remote_count} 笔
匹配成功: {record.matched_count} 笔
差异数量: {record.difference_count} 笔
差异金额: ¥{record.difference_amount}
执行时长: {record.duration_seconds}秒

⚠️ 请及时处理差异记录
                """.strip()
            else:
                title = f"❌ 对账失败 - {record.reconciliation_date}"
                content = f"""
对账批次: {record.batch_no}
对账日期: {record.reconciliation_date}
失败原因: {record.error_message}
                """.strip()

            # 发送通知给管理员
            await self.notification_service.send_admin_notification(
                title=title,
                content=content,
                notification_type="reconciliation"
            )

            logger.info(f"对账通知已发送: {record.batch_no}")

        except Exception as e:
            logger.error(f"发送对账通知失败: {str(e)}")

    async def _send_failure_notification(self, target_date: str, error_message: str) -> None:
        """发送对账失败通知

        Args:
            target_date: 目标日期
            error_message: 错误信息
        """
        try:
            if not self.notification_service:
                self.notification_service = NotificationService()

            title = f"❌ 对账任务执行失败 - {target_date}"
            content = f"""
对账日期: {target_date}
失败时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
错误信息: {error_message}

请检查系统状态并手动执行对账。
            """.strip()

            await self.notification_service.send_admin_notification(
                title=title,
                content=content,
                notification_type="system_error"
            )

            logger.info(f"对账失败通知已发送: {target_date}")

        except Exception as e:
            logger.error(f"发送失败通知失败: {str(e)}")

    async def check_pending_differences_task(self) -> None:
        """检查待处理差异任务

        定期检查是否有长时间未处理的差异记录，发送提醒通知
        """
        db = self.get_db()

        try:
            logger.info("开始检查待处理差异")

            service = ReconciliationService(db)

            # 查询待处理的差异记录
            from app.models.reconciliation import DifferenceStatus
            differences, total = service.get_reconciliation_differences(
                status=DifferenceStatus.PENDING,
                page=1,
                page_size=100
            )

            if not differences:
                logger.info("没有待处理的差异记录")
                return

            # 检查是否有超过24小时未处理的差异
            now = datetime.utcnow()
            overdue_differences = []

            for diff in differences:
                hours_since_created = (now - diff.created_at).total_seconds() / 3600
                if hours_since_created > 24:  # 超过24小时
                    overdue_differences.append(diff)

            if overdue_differences:
                await self._send_overdue_differences_notification(overdue_differences)

            logger.info(f"差异检查完成: 总计{total}条，超期{len(overdue_differences)}条")

        except Exception as e:
            logger.error(f"检查待处理差异失败: {str(e)}")
            raise
        finally:
            db.close()

    async def _send_overdue_differences_notification(self, differences) -> None:
        """发送超期差异提醒通知

        Args:
            differences: 超期差异记录列表
        """
        try:
            if not self.notification_service:
                self.notification_service = NotificationService()

            title = f"⏰ 差异处理提醒 - {len(differences)}条超期"

            content_lines = [
                f"发现 {len(differences)} 条超过24小时未处理的差异记录：",
                ""
            ]

            for diff in differences[:10]:  # 最多显示10条
                hours_overdue = int((datetime.utcnow() - diff.created_at).total_seconds() / 3600)
                content_lines.append(
                    f"• ID:{diff.id} | 类型:{diff.difference_type.value} | 超期:{hours_overdue}小时"
                )

            if len(differences) > 10:
                content_lines.append(f"... 还有 {len(differences) - 10} 条记录")

            content_lines.extend([
                "",
                "请及时登录系统处理这些差异记录。"
            ])

            content = "\n".join(content_lines)

            await self.notification_service.send_admin_notification(
                title=title,
                content=content,
                notification_type="reminder"
            )

            logger.info(f"超期差异提醒已发送: {len(differences)}条")

        except Exception as e:
            logger.error(f"发送超期差异提醒失败: {str(e)}")

    async def reconciliation_health_check_task(self) -> None:
        """对账系统健康检查任务

        检查对账系统的运行状态，包括:
        - 最近几天是否正常对账
        - 差异处理情况
        - 系统性能指标
        """
        db = self.get_db()

        try:
            logger.info("开始对账系统健康检查")

            service = ReconciliationService(db)

            # 检查最近7天的对账情况
            end_date = date.today()
            start_date = end_date - timedelta(days=7)

            records, total = service.get_reconciliation_records(
                page=1,
                page_size=100,
                start_date=start_date.strftime("%Y-%m-%d"),
                end_date=end_date.strftime("%Y-%m-%d")
            )

            # 分析健康状态
            health_report = self._analyze_reconciliation_health(records)

            # 如果发现问题，发送告警
            if health_report["issues"]:
                await self._send_health_alert(health_report)

            logger.info(f"健康检查完成: {health_report['status']}")

        except Exception as e:
            logger.error(f"健康检查失败: {str(e)}")
            raise
        finally:
            db.close()

    def _analyze_reconciliation_health(self, records) -> dict:
        """分析对账健康状态

        Args:
            records: 对账记录列表

        Returns:
            健康报告字典
        """
        issues = []

        # 检查是否有连续失败
        failed_count = 0
        for record in sorted(records, key=lambda x: x.reconciliation_date, reverse=True):
            if record.is_failed():
                failed_count += 1
            else:
                break

        if failed_count >= 2:
            issues.append(f"连续{failed_count}天对账失败")

        # 检查差异率
        if records:
            total_transactions = sum(r.total_local_count for r in records)
            total_differences = sum(r.difference_count for r in records)

            if total_transactions > 0:
                difference_rate = total_differences / total_transactions * 100
                if difference_rate > 5:  # 差异率超过5%
                    issues.append(f"差异率过高: {difference_rate:.2f}%")

        # 检查是否有缺失的对账
        expected_dates = []
        current_date = date.today() - timedelta(days=1)
        for i in range(7):
            expected_dates.append(current_date.strftime("%Y-%m-%d"))
            current_date -= timedelta(days=1)

        actual_dates = {r.reconciliation_date for r in records}
        missing_dates = set(expected_dates) - actual_dates

        if missing_dates:
            issues.append(f"缺失对账日期: {', '.join(sorted(missing_dates))}")

        return {
            "status": "healthy" if not issues else "warning",
            "issues": issues,
            "total_records": len(records),
            "failed_records": sum(1 for r in records if r.is_failed()),
            "records_with_differences": sum(1 for r in records if r.has_differences())
        }

    async def _send_health_alert(self, health_report: dict) -> None:
        """发送健康告警通知

        Args:
            health_report: 健康报告
        """
        try:
            if not self.notification_service:
                self.notification_service = NotificationService()

            title = "🚨 对账系统健康告警"

            content_lines = [
                "对账系统健康检查发现以下问题：",
                ""
            ]

            for issue in health_report["issues"]:
                content_lines.append(f"• {issue}")

            content_lines.extend([
                "",
                f"统计信息:",
                f"• 总对账记录: {health_report['total_records']}",
                f"• 失败记录: {health_report['failed_records']}",
                f"• 有差异记录: {health_report['records_with_differences']}",
                "",
                "请及时检查并处理相关问题。"
            ])

            content = "\n".join(content_lines)

            await self.notification_service.send_admin_notification(
                title=title,
                content=content,
                notification_type="alert"
            )

            logger.info("健康告警通知已发送")

        except Exception as e:
            logger.error(f"发送健康告警失败: {str(e)}")


# 全局任务实例
reconciliation_tasks = ReconciliationTasks()


# 任务函数（供调度器调用）
async def run_daily_reconciliation():
    """运行每日对账任务"""
    await reconciliation_tasks.daily_reconciliation_task()


async def run_check_pending_differences():
    """运行检查待处理差异任务"""
    await reconciliation_tasks.check_pending_differences_task()


async def run_health_check():
    """运行健康检查任务"""
    await reconciliation_tasks.reconciliation_health_check_task()


# 手动执行任务的函数
async def manual_reconciliation(target_date: str):
    """手动执行指定日期的对账

    Args:
        target_date: 目标日期 (YYYY-MM-DD)
    """
    await reconciliation_tasks.daily_reconciliation_task(target_date)


if __name__ == "__main__":
    # 用于测试
    import asyncio

    async def test_tasks():
        """测试任务"""
        print("测试每日对账任务...")
        await run_daily_reconciliation()

        print("测试差异检查任务...")
        await run_check_pending_differences()

        print("测试健康检查任务...")
        await run_health_check()

    asyncio.run(test_tasks())