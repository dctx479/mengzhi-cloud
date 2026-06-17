"""告警模块 - 统一告警管理器

支持的告警渠道：
- Email (SMTP)
- DingTalk (Webhook + HMAC-SHA256 签名)
- SMS (阿里云短信 API v3)

设计原则：
- 单一入口：所有业务代码调用 alert_manager.send_alert()
- 向后兼容：原 4 参签名不变，新增 3 个可选参数
- 优雅降级：凭证缺失时 skip 而非抛错
- 频率限制：同一 alert_key 在 cooldown_period 内只发送一次
"""
import asyncio
import hmac
import hashlib
import base64
import time
import uuid
import json
import urllib.parse
from typing import Dict, Any, List, Optional
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


# 阿里云短信 v3 API 公共参数
ALIYUN_SMS_ENDPOINT = "https://dysmsapi.aliyuncs.com/"


def _percent_encode(value: str) -> str:
    """阿里云 API v3 签名专用百分号编码（RFC 3986 子集）"""
    # 加号、空格、星号、%7E 等需要特殊处理
    encoded = urllib.parse.quote(value, safe='')
    # 阿里云规范: 星号编码为 %2A，加号编码为 %20，%7E 还原为 ~
    encoded = encoded.replace('+', '%20').replace('*', '%2A').replace('%7E', '~')
    return encoded


def _build_aliyun_sms_signature(params: Dict[str, str], access_key_secret: str) -> str:
    """构造阿里云 API v3 签名

    签名步骤：
    1. 参数按字典序排序
    2. 构造规范化查询字符串（percent-encode）
    3. 构造待签名字符串：METHOD + "\n" + 规范化URI + "\n" + 规范化查询 + "\n"
    4. HMAC-SHA1 签名 → base64
    """
    sorted_params = sorted(params.items())
    canonicalized_query = '&'.join(
        f'{_percent_encode(k)}={_percent_encode(v)}'
        for k, v in sorted_params
    )
    string_to_sign = f"POST&{_percent_encode('/')}&{_percent_encode(canonicalized_query)}"
    hmac_code = hmac.new(
        (access_key_secret + '&').encode('utf-8'),
        string_to_sign.encode('utf-8'),
        digestmod=hashlib.sha1
    ).digest()
    return base64.b64encode(hmac_code).decode('utf-8')


def get_alert_recipients(enterprise_id: Optional[str] = None) -> Dict[str, List[str]]:
    """获取告警接收人配置

    Args:
        enterprise_id: 企业 ID（非空时优先查企业级配置）

    Returns:
        {
            "email": [str],
            "dingtalk": [str],   # webhook URLs
            "sms": [str],        # phone numbers
        }
    """
    # 未来扩展：若 TenantConfig.alert_config 字段存在，从 DB 读取
    # 当前实现：全部走 monitoring_config 全局配置
    return {
        "email": list(monitoring_config.ALERT_EMAIL_TO or []),
        "dingtalk": [monitoring_config.ALERT_DINGTALK_WEBHOOK] if monitoring_config.ALERT_DINGTALK_WEBHOOK else [],
        "sms": list(monitoring_config.ALERT_SMS_PHONES or []),
    }


class AlertManager:
    """统一告警管理器"""

    def __init__(self):
        self.alert_history: List[Dict] = []
        self.alert_cooldown: Dict[str, float] = {}
        self.cooldown_period = 300  # 5分钟冷却期

    def _truncate(self, text: str, max_len: int = 1000) -> str:
        """输入校验：截断超长字段，避免日志/邮件/SMS 异常"""
        if not isinstance(text, str):
            text = str(text)
        if len(text) > max_len:
            return text[:max_len - 3] + "..."
        return text

    async def send_alert(
        self,
        level: str,
        title: str,
        message: str,
        extra: Optional[Dict] = None,
        channels: Optional[List[str]] = None,
        enterprise_id: Optional[str] = None,
    ) -> Dict[str, bool]:
        """发送告警（统一入口）

        Args:
            level: info | warning | error | critical
            title: 告警标题（≤1000 字符）
            message: 告警详情（≤1000 字符）
            extra: 额外元数据（dict，可选）
            channels: 显式指定渠道（email/dingtalk/sms）；None 时按配置自动选择
            enterprise_id: 企业 ID（用于企业级路由）

        Returns:
            {channel: success_bool} 各渠道发送结果
        """
        title = self._truncate(title, 1000)
        message = self._truncate(message, 1000)

        alert_key = f"{level}:{title}"

        # 频率限制
        if alert_key in self.alert_cooldown:
            if time.time() - self.alert_cooldown[alert_key] < self.cooldown_period:
                logger.debug(f"Alert in cooldown: {alert_key}")
                return {}

        self.alert_cooldown[alert_key] = time.time()

        alert_data = {
            'level': level,
            'title': title,
            'message': message,
            'extra': extra or {},
            'timestamp': datetime.now().isoformat(),
        }

        self.alert_history.append(alert_data)
        logger.info(f"Sending alert: {level} - {title}")

        # 选择渠道
        tasks = []
        selected = []
        if channels is None:
            channels = []
            if monitoring_config.ALERT_EMAIL_ENABLED:
                channels.append('email')
            if monitoring_config.ALERT_DINGTALK_ENABLED:
                channels.append('dingtalk')
            if monitoring_config.ALERT_SMS_ENABLED and level in [AlertLevel.ERROR, AlertLevel.CRITICAL]:
                channels.append('sms')

        if 'email' in channels and monitoring_config.ALERT_EMAIL_ENABLED:
            tasks.append(('email', self._send_email_alert(alert_data)))
        if 'dingtalk' in channels and monitoring_config.ALERT_DINGTALK_ENABLED:
            tasks.append(('dingtalk', self._send_dingtalk_alert(alert_data, enterprise_id)))
        if 'sms' in channels and monitoring_config.ALERT_SMS_ENABLED and level in [AlertLevel.ERROR, AlertLevel.CRITICAL]:
            tasks.append(('sms', self._send_sms_alert(alert_data)))

        results: Dict[str, bool] = {}
        if tasks:
            outcomes = await asyncio.gather(
                *(t[1] for t in tasks),
                return_exceptions=True,
            )
            for (channel, _), outcome in zip(tasks, outcomes):
                if isinstance(outcome, Exception):
                    logger.error(f"Alert channel {channel} raised: {outcome}")
                    results[channel] = False
                else:
                    results[channel] = bool(outcome)

        return results

    async def _send_email_alert(self, alert_data: Dict) -> bool:
        """发送邮件告警（在线程池中执行同步 SMTP 调用）"""
        try:
            await asyncio.to_thread(self._send_email_sync, alert_data)
            logger.info("Email alert sent successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to send email alert: {e}")
            return False

    def _send_email_sync(self, alert_data: Dict):
        """同步发送邮件"""
        if not monitoring_config.ALERT_EMAIL_SMTP_HOST or not monitoring_config.ALERT_EMAIL_USERNAME:
            raise ValueError("Email SMTP credentials not configured")

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

        with smtplib.SMTP(
            monitoring_config.ALERT_EMAIL_SMTP_HOST,
            monitoring_config.ALERT_EMAIL_SMTP_PORT,
        ) as server:
            server.starttls()
            server.login(monitoring_config.ALERT_EMAIL_USERNAME, monitoring_config.ALERT_EMAIL_PASSWORD)
            server.send_message(msg)

    async def _send_dingtalk_alert(self, alert_data: Dict, enterprise_id: Optional[str] = None) -> bool:
        """发送钉钉告警"""
        try:
            webhook_url = monitoring_config.ALERT_DINGTALK_WEBHOOK
            secret = monitoring_config.ALERT_DINGTALK_SECRET

            if not webhook_url:
                logger.warning("DingTalk webhook URL not configured, skipping")
                return False

            # 仅当配置了加签密钥时才签名
            sign = ""
            if secret:
                timestamp = str(round(time.time() * 1000))
                secret_enc = secret.encode('utf-8')
                string_to_sign = f'{timestamp}\n{secret}'
                string_to_sign_enc = string_to_sign.encode('utf-8')
                hmac_code = hmac.new(secret_enc, string_to_sign_enc, digestmod=hashlib.sha256).digest()
                sign = base64.b64encode(hmac_code).decode('utf-8')
                url = f"{webhook_url}&timestamp={timestamp}&sign={sign}"
            else:
                url = webhook_url

            level_emoji = {
                AlertLevel.INFO: "ℹ️",
                AlertLevel.WARNING: "⚠️",
                AlertLevel.ERROR: "❌",
                AlertLevel.CRITICAL: "🔥",
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
                    "text": markdown_text,
                },
            }

            # 透传 @手机号（如果 extra 中指定）
            at_mobiles = (alert_data.get('extra') or {}).get('at_mobiles')
            if at_mobiles:
                payload["at"] = {"atMobiles": at_mobiles, "isAtAll": False}

            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(url, json=payload)
                response.raise_for_status()

            logger.info("DingTalk alert sent successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to send DingTalk alert: {e}")
            return False

    async def _send_sms_alert(self, alert_data: Dict) -> bool:
        """发送阿里云短信告警

        阿里云短信 API v3：
        - Endpoint: https://dysmsapi.aliyuncs.com/
        - Action: SendSms
        - 签名算法: HMAC-SHA1
        - 返回 errCode="OK" 表示成功
        """
        try:
            access_key = monitoring_config.ALERT_SMS_ACCESS_KEY
            secret_key = monitoring_config.ALERT_SMS_SECRET_KEY
            sign_name = monitoring_config.ALERT_SMS_SIGN_NAME
            template_code = monitoring_config.ALERT_SMS_TEMPLATE_CODE
            phones = monitoring_config.ALERT_SMS_PHONES or []

            if not all([access_key, secret_key, sign_name, template_code, phones]):
                logger.warning("SMS credentials not fully configured, skipping")
                return False

            # 阿里云公共参数 + 业务参数
            params = {
                "AccessKeyId": access_key,
                "Action": "SendSms",
                "Format": "JSON",
                "PhoneNumbers": ",".join(phones),
                "RegionId": "cn-hangzhou",
                "SignName": sign_name,
                "SignatureMethod": "HMAC-SHA1",
                "SignatureNonce": str(uuid.uuid4()),
                "SignatureVersion": "1.0",
                "TemplateCode": template_code,
                "TemplateParam": json.dumps({
                    "level": alert_data['level'],
                    "title": alert_data['title'][:50],
                    "message": alert_data['message'][:200],
                }, ensure_ascii=False),
                "Timestamp": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
                "Version": "2017-05-25",
            }

            params["Signature"] = _build_aliyun_sms_signature(params, secret_key)

            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(ALIYUN_SMS_ENDPOINT, data=params)
                response.raise_for_status()
                result = response.json()

                if result.get("Code") == "OK":
                    logger.info(f"SMS alert sent successfully to {len(phones)} phone(s)")
                    return True
                else:
                    logger.error(f"SMS alert failed: Code={result.get('Code')}, Message={result.get('Message')}")
                    return False
        except Exception as e:
            logger.error(f"Failed to send SMS alert: {e}")
            return False


alert_manager = AlertManager()