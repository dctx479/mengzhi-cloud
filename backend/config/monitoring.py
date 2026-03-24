"""监控配置模块"""

from pydantic_settings import BaseSettings
from typing import List, Dict


class MonitoringConfig(BaseSettings):
    """监控系统配置"""

    # APM配置
    APM_ENABLED: bool = True
    APM_SERVICE_NAME: str = "ai-platform-backend"
    APM_ENVIRONMENT: str = "production"

    # 数据库监控
    DB_MONITOR_ENABLED: bool = True
    DB_SLOW_QUERY_THRESHOLD: float = 1.0  # 秒
    DB_CONNECTION_POOL_SIZE: int = 20

    # 服务器资源监控
    RESOURCE_MONITOR_ENABLED: bool = True
    CPU_THRESHOLD: float = 80.0  # 百分比
    MEMORY_THRESHOLD: float = 85.0  # 百分比
    DISK_THRESHOLD: float = 90.0  # 百分比

    # 告警配置
    ALERT_ENABLED: bool = True
    ALERT_EMAIL_ENABLED: bool = True
    ALERT_DINGTALK_ENABLED: bool = True
    ALERT_SMS_ENABLED: bool = False

    # 邮件告警
    ALERT_EMAIL_SMTP_HOST: str = "smtp.example.com"
    ALERT_EMAIL_SMTP_PORT: int = 587
    ALERT_EMAIL_USERNAME: str = ""
    ALERT_EMAIL_PASSWORD: str = ""
    ALERT_EMAIL_FROM: str = "alert@example.com"
    ALERT_EMAIL_TO: List[str] = ["admin@example.com"]

    # 钉钉告警
    ALERT_DINGTALK_WEBHOOK: str = ""
    ALERT_DINGTALK_SECRET: str = ""

    # 短信告警
    ALERT_SMS_PROVIDER: str = "aliyun"
    ALERT_SMS_ACCESS_KEY: str = ""
    ALERT_SMS_SECRET_KEY: str = ""
    ALERT_SMS_SIGN_NAME: str = ""
    ALERT_SMS_TEMPLATE_CODE: str = ""
    ALERT_SMS_PHONES: List[str] = []

    # Prometheus配置
    PROMETHEUS_ENABLED: bool = True
    PROMETHEUS_PORT: int = 9090
    PROMETHEUS_METRICS_PATH: str = "/metrics"

    # 日志监控
    LOG_MONITOR_ENABLED: bool = True
    LOG_ERROR_THRESHOLD: int = 10  # 每分钟错误数

    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "ignore"


monitoring_config = MonitoringConfig()
