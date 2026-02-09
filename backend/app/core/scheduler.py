"""
定时任务调度器
"""
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
import yaml
from pathlib import Path
from loguru import logger

class TaskScheduler:
    def __init__(self):
        self.scheduler = AsyncIOScheduler(timezone="Asia/Shanghai")
        self.jobs = {}

    def load_config(self):
        """加载配置文件"""
        config_path = Path(__file__).parent.parent / "config" / "scheduler.yaml"
        with open(config_path) as f:
            return yaml.safe_load(f)

    def start(self):
        """启动调度器"""
        config = self.load_config()

        if not config.get("scheduler", {}).get("enabled", True):
            logger.info("定时任务调度器已禁用")
            return

        # 添加任务
        for job_config in config.get("jobs", []):
            if not job_config.get("enabled", True):
                continue

            job_id = job_config["name"]
            schedule = job_config["schedule"]
            func_path = job_config["function"]

            # 动态导入函数
            module_path, func_name = func_path.rsplit(".", 1)
            module = __import__(module_path, fromlist=[func_name])
            func = getattr(module, func_name)

            # 添加任务
            self.scheduler.add_job(
                func,
                CronTrigger.from_crontab(schedule),
                id=job_id,
                name=job_config.get("description", job_id),
                replace_existing=True
            )

            logger.info(f"添加定时任务: {job_id} ({schedule})")

        self.scheduler.start()
        logger.info("定时任务调度器已启动")

    def stop(self):
        """停止调度器"""
        self.scheduler.shutdown()
        logger.info("定时任务调度器已停止")

# 全局调度器实例
scheduler = TaskScheduler()
