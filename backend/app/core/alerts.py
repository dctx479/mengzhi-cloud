"""告警模块"""
import asyncio
import hmac
import hashlib
import base64
import time
from typing import Dict, Any, List
from datetime import datetime
import httpx
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from loguru import logger
from config.monitoring import monitoring_config

class AlertLevel:
    """告警级别"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"

class AlertManager:
    """告警管理器"""

    def __init__(self):
        self.alert_history: List[Dict] = []
        self.alert_cooldown: Dict[str, float] = {}  # 防止告警风暴
        self.cooldown_period = 300  # 5分钟冷却期

    async def send_alert(self, level: str, title: str, message: str, extra: Dict = None):
        """发送告警"""
        alert_key = f"{level}:{title}"

        # 检查冷却期
        if alert_key in self.alert_cooldown:
            if time.time() - self.alert_cooldown[alert_key] < self.cooldown_period:
                logger.debug(f"Alert in cooldown: {alert_key}")
                return

        self.alert_cooldown[alert_key] = time.time()

        alert_data = {
            'level': level,
            'title': title,
            'message': message,
            'extra': extra or {},
            'timestamp': datetime.now().isoformat()
        }

        self.alert_history.append(alert_data)
        logger.info(f"Sending alert: {level} - {title}")

        # 并发发送多种告警
        tasks = []
        if monitoring_config.ALERT_EMAIL_ENABLED:
            tasks.append(self._send_email_alert(alert_data))
        if monitoring_config.ALERT_DINGTALK_ENABLED:
            tasks.append(self._send_dingtalk_alert(alert_data))
        if monitoring_config.ALERT_SMS_ENABLED and level in [AlertLevel.ERROR, AlertLevel.CRITICAL]:
            tasks.append(self._send_sms_alert(alert_data))

        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)

    async def _send_email_alert(self, alert_data: Dict):
        """发送邮件告警"""
        try:
            msg = MIMEMultipart()
            msg['From'] = monitoring_config.ALERT_EMAIL_FROM
            msg['To'] = ', '.join(monitoring_config.ALERT_EMAIL_TO)
            msg['Subject'] = f"[{alert_data['level'].upper()}] {alert_data['title']}"

            body = f"""
告警级别: {alert_data['level'].upper()}
告警标题: {alert_data['title']}
告警时间: {alert_data['timestamp']}

详细信息:
{alert_data['message']}

额外数据:
{alert_data['extra']}
            """

            msg.attach(MIMEText(body, 'plain'))

            with smtplib.SMTP(monitoring_config.ALERT_EMAIL_SMTP_HOST,
                            monitoring_config.ALERT_EMAIL_SMTP_PORT) as server:
                server.starttls()
                server.login(monitoring_config.ALERT_EMAIL_USERNAME,
                           monitoring_config.ALERT_EMAIL_PASSWORD)
                server.send_message(msg)

            logger.info("Email alert sent successfully")
        except Exception as e:
            logger.error(f"Failed to send email alert: {e}")

    async def _send_dingtalk_alert(self, alert_data: Dict):
        """发送钉钉告警"""
        try:
            timestamp = str(round(time.time() * 1000))
            secret = monitoring_config.ALERT_DINGTALK_SECRET

            # 生成签名
            secret_enc = secret.encode('utf-8')
            string_to_sign = f'{timestamp}\n{secret}'
            string_to_sign_enc = string_to_sign.encode('utf-8')
            hmac_code = hmac.new(secret_enc, string_to_sign_enc, digestmod=hashlib.sha256).digest()
            sign = base64.b64encode(hmac_code).decode('utf-8')

            # 构建消息
            level_emoji = {
                AlertLevel.INFO: "ℹ️",
                AlertLevel.WARNING: "⚠️",
                AlertLevel.ERROR: "❌",
                AlertLevel.CRITICAL: "🔥"
            }

            markdown_text = f"""
### {level_emoji.get(alert_data['level'], '📢')} {alert_data['title']}

**告警级别**: {alert_data['level'].upper()}

**告警时间**: {alert_data['timestamp']}

**详细信息**:

{alert_data['message']}
            """

            payload = {
                "msgtype": "markdown",
                "markdown": {
                    "title": alert_data['title'],
                    "text": markdown_text
                }
            }

            url = f"{monitoring_config.ALERT_DINGTALK_WEBHOOK}&timestamp={timestamp}&sign={sign}"

            async with httpx.AsyncClient() as client:
                response = await client.post(url, json=payload)
                response.raise_for_status()

            logger.info("DingTalk alert sent successfully")
        except Exception as e:
            logger.error(f"Failed to send DingTalk alert: {e}")

    async def _send_sms_alert(self, alert_data: Dict):
        """发送短信告警"""
        try:
            # 这里以阿里云短信为例
            logger.info(f"SMS alert would be sent to: {monitoring_config.ALERT_SMS_PHONES}")
            # 实际实现需要集成阿里云SDK
        except Exception as e:
            logger.error(f"Failed to send SMS alert: {e}")

alert_manager = AlertManager()
