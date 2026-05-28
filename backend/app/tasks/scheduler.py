"""
对账任务调度器

版本: 1.0
创建日期: 2026-01-23
"""

import asyncio
from datetime import datetime, time
from typing import Dict, Any
from loguru import logger
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.jobstores.memory import MemoryJobStore
from apscheduler.executors.asyncio import AsyncIOExecutor

from app.tasks.reconciliation_tasks import (
    run_daily_reconciliation,
    run_check_pending_differences,
    run_health_check
)
from app.core.config import settings


class ReconciliationScheduler:
    """对账任务调度器

    管理对账相关的定时任务:
    - 每日凌晨2点自动对账
    - 每4小时检查待处理差异
    - 每天上午9点健康检查
    - 每20小时检查并刷新淘宝联盟 Session
    """

    def __init__(self):
        """初始化调度器"""
        jobstores = {
            'default': MemoryJobStore()
        }
        executors = {
            'default': AsyncIOExecutor()
        }
        job_defaults = {
            'coalesce': False,
            'max_instances': 1,
            'misfire_grace_time': 300
        }

        self.scheduler = AsyncIOScheduler(
            jobstores=jobstores,
            executors=executors,
            job_defaults=job_defaults,
            timezone='Asia/Shanghai'
        )

        self._setup_jobs()

    def _setup_jobs(self):
        """设置定时任务"""

        # 1. 每日凌晨2点自动对账
        self.scheduler.add_job(
            func=run_daily_reconciliation,
            trigger=CronTrigger(hour=2, minute=0),
            id='daily_reconciliation',
            name='每日自动对账',
            replace_existing=True,
            max_instances=1
        )
        logger.info("已添加每日对账任务: 每天凌晨2:00执行")

        # 2. 每4小时检查待处理差异
        self.scheduler.add_job(
            func=run_check_pending_differences,
            trigger=IntervalTrigger(hours=4),
            id='check_pending_differences',
            name='检查待处理差异',
            replace_existing=True,
            max_instances=1
        )
        logger.info("已添加差异检查任务: 每4小时执行一次")

        # 3. 每天上午9点健康检查
        self.scheduler.add_job(
            func=run_health_check,
            trigger=CronTrigger(hour=9, minute=0),
            id='reconciliation_health_check',
            name='对账系统健康检查',
            replace_existing=True,
            max_instances=1
        )
        logger.info("已添加健康检查任务: 每天上午9:00执行")

        # 4. 每20小时检查并刷新淘宝联盟 Session（有效期1天，提前4小时刷新）
        from app.tasks.taobao_token_refresh import refresh_taobao_session_if_needed
        self.scheduler.add_job(
            func=refresh_taobao_session_if_needed,
            trigger=IntervalTrigger(hours=20),
            id='taobao_session_refresh',
            name='淘宝联盟 Session 自动刷新',
            replace_existing=True,
            max_instances=1,
        )
        logger.info("已添加淘宝 Session 刷新任务: 每20小时检查一次")

    def start(self):
        """启动调度器"""
        try:
            self.scheduler.start()
            logger.info("对账任务调度器已启动")

            # 打印已注册的任务
            jobs = self.scheduler.get_jobs()
            logger.info(f"已注册 {len(jobs)} 个定时任务:")
            for job in jobs:
                logger.info(f"  - {job.name} (ID: {job.id})")

        except Exception as e:
            logger.error(f"启动调度器失败: {str(e)}")
            raise

    def stop(self):
        """停止调度器"""
        try:
            self.scheduler.shutdown(wait=True)
            logger.info("对账任务调度器已停止")
        except Exception as e:
            logger.error(f"停止调度器失败: {str(e)}")
            raise

    def get_job_status(self) -> Dict[str, Any]:
        """获取任务状态

        Returns:
            任务状态信息
        """
        jobs = self.scheduler.get_jobs()

        status = {
            "scheduler_running": self.scheduler.running,
            "total_jobs": len(jobs),
            "jobs": []
        }

        for job in jobs:
            job_info = {
                "id": job.id,
                "name": job.name,
                "next_run_time": job.next_run_time.isoformat() if job.next_run_time else None,
                "trigger": str(job.trigger),
                "max_instances": job.max_instances,
                "pending": job.pending
            }
            status["jobs"].append(job_info)

        return status

    def pause_job(self, job_id: str):
        """暂停任务

        Args:
            job_id: 任务ID
        """
        try:
            self.scheduler.pause_job(job_id)
            logger.info(f"任务已暂停: {job_id}")
        except Exception as e:
            logger.error(f"暂停任务失败: {job_id}, error: {str(e)}")
            raise

    def resume_job(self, job_id: str):
        """恢复任务

        Args:
            job_id: 任务ID
        """
        try:
            self.scheduler.resume_job(job_id)
            logger.info(f"任务已恢复: {job_id}")
        except Exception as e:
            logger.error(f"恢复任务失败: {job_id}, error: {str(e)}")
            raise

    def run_job_now(self, job_id: str):
        """立即执行任务

        Args:
            job_id: 任务ID
        """
        try:
            job = self.scheduler.get_job(job_id)
            if job:
                self.scheduler.modify_job(job_id, next_run_time=datetime.now())
                logger.info(f"任务已安排立即执行: {job_id}")
            else:
                raise ValueError(f"任务不存在: {job_id}")
        except Exception as e:
            logger.error(f"立即执行任务失败: {job_id}, error: {str(e)}")
            raise

    def add_one_time_reconciliation(self, target_date: str, run_time: datetime):
        """添加一次性对账任务

        Args:
            target_date: 对账日期 (YYYY-MM-DD)
            run_time: 执行时间
        """
        try:
            from app.tasks.reconciliation_tasks import manual_reconciliation

            job_id = f"manual_reconciliation_{target_date}_{int(run_time.timestamp())}"

            self.scheduler.add_job(
                func=manual_reconciliation,
                args=[target_date],
                trigger='date',
                run_date=run_time,
                id=job_id,
                name=f'手动对账 - {target_date}',
                max_instances=1
            )

            logger.info(f"已添加一次性对账任务: {target_date}, 执行时间: {run_time}")
            return job_id

        except Exception as e:
            logger.error(f"添加一次性对账任务失败: {str(e)}")
            raise


# 全局调度器实例
reconciliation_scheduler = ReconciliationScheduler()


# 调度器管理函数
def start_reconciliation_scheduler():
    """启动对账调度器"""
    reconciliation_scheduler.start()


def stop_reconciliation_scheduler():
    """停止对账调度器"""
    reconciliation_scheduler.stop()


def get_scheduler_status():
    """获取调度器状态"""
    return reconciliation_scheduler.get_job_status()


# 任务管理API函数
def pause_reconciliation_job(job_id: str):
    """暂停对账任务"""
    reconciliation_scheduler.pause_job(job_id)


def resume_reconciliation_job(job_id: str):
    """恢复对账任务"""
    reconciliation_scheduler.resume_job(job_id)


def run_reconciliation_job_now(job_id: str):
    """立即执行对账任务"""
    reconciliation_scheduler.run_job_now(job_id)


def schedule_manual_reconciliation(target_date: str, run_time: datetime) -> str:
    """安排手动对账任务"""
    return reconciliation_scheduler.add_one_time_reconciliation(target_date, run_time)


if __name__ == "__main__":
    # 用于测试
    import time

    def test_scheduler():
        """测试调度器"""
        print("启动调度器...")
        start_reconciliation_scheduler()

        print("调度器状态:")
        status = get_scheduler_status()
        for job in status["jobs"]:
            print(f"  - {job['name']}: {job['next_run_time']}")

        print("等待10秒...")
        time.sleep(10)

        print("停止调度器...")
        stop_reconciliation_scheduler()

    test_scheduler()