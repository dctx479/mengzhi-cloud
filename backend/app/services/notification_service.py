"""
通知服务 - BUG-023修复

支持邮件和短信通知功能

版本: 1.0
创建日期: 2026-01-17
"""

import html as html_lib
import json
import smtplib
import time
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from threading import Lock
from typing import Optional, List, Dict
from datetime import datetime

from app.core.config import settings
from app.core.logging_config import logger
from app.core.errors import ExternalServiceError


class EmailService:
    """邮件服务"""

    # Class-level deduplication cache — prevents duplicate sends within the TTL window
    _dedup_cache: Dict[str, float] = {}
    _dedup_lock: Lock = Lock()
    _dedup_ttl: int = 60  # seconds

    def __init__(self):
        """初始化邮件服务配置"""
        self.smtp_server = settings.SMTP_SERVER
        self.smtp_port = settings.SMTP_PORT
        self.smtp_user = settings.SMTP_USER
        self.smtp_password = settings.SMTP_PASSWORD
        self.from_email = settings.SMTP_FROM_EMAIL
        self.from_name = settings.SMTP_FROM_NAME
        self.dev_mode = settings.EMAIL_DEV_MODE

    def _is_duplicate_send(self, key: str) -> bool:
        """Idempotency guard: returns True if this notification was recently sent."""
        with self.__class__._dedup_lock:
            now = time.time()
            expired = [k for k, ts in list(self.__class__._dedup_cache.items())
                       if now - ts > self.__class__._dedup_ttl]
            for k in expired:
                del self.__class__._dedup_cache[k]
            if key in self.__class__._dedup_cache:
                logger.warning(f"⚠️ WARNING: Duplicate email suppressed (key={key})")
                return True
            self.__class__._dedup_cache[key] = now
            return False

    def _create_message(
        self,
        to: str,
        subject: str,
        body: str,
        html: bool = False,
        cc: Optional[List[str]] = None,
        bcc: Optional[List[str]] = None
    ) -> MIMEMultipart:
        """创建邮件消息
        
        参数:
            to: 收件人邮箱
            subject: 邮件主题
            body: 邮件内容
            html: 是否为HTML格式
            cc: 抄送列表
            bcc: 密送列表
            
        返回:
            邮件消息对象
        """
        msg = MIMEMultipart('alternative')
        msg['From'] = f"{self.from_name} <{self.from_email}>"
        msg['To'] = to
        msg['Subject'] = subject
        msg['Date'] = datetime.utcnow().strftime("%a, %d %b %Y %H:%M:%S +0000")

        if cc:
            msg['Cc'] = ', '.join(cc)
        if bcc:
            msg['Bcc'] = ', '.join(bcc)

        # 添加邮件内容
        if html:
            msg.attach(MIMEText(body, 'html', 'utf-8'))
        else:
            msg.attach(MIMEText(body, 'plain', 'utf-8'))

        return msg

    def send_email(
        self,
        to: str,
        subject: str,
        body: str,
        html: bool = False,
        cc: Optional[List[str]] = None,
        bcc: Optional[List[str]] = None
    ) -> bool:
        """发送邮件

        参数:
            to: 收件人邮箱
            subject: 邮件主题
            body: 邮件内容
            html: 是否为HTML格式
            cc: 抄送列表
            bcc: 密送列表

        返回:
            是否发送成功

        异常:
            ExternalServiceError: 邮件发送失败
        """
        # 开发模式：仅打印日志
        if self.dev_mode:
            logger.info(f"[开发模式-邮件] To: {to}, Subject: {subject}")
            logger.debug(f"[开发模式-邮件] Body: {body[:200]}...")
            return True

        try:
            # 创建邮件消息
            msg = self._create_message(to, subject, body, html, cc, bcc)

            # 连接SMTP服务器并发送
            with smtplib.SMTP(self.smtp_server, self.smtp_port, timeout=10) as server:
                server.starttls()
                if self.smtp_user and self.smtp_password:
                    server.login(self.smtp_user, self.smtp_password)

                recipients = [to]
                if cc:
                    recipients.extend(cc)
                if bcc:
                    recipients.extend(bcc)

                server.send_message(msg, to_addrs=recipients)

            logger.info(f"邮件发送成功: to={to}, subject={subject}")
            return True

        except Exception as e:
            logger.error(f"邮件发送失败: {str(e)}")
            raise ExternalServiceError(f"邮件发送失败: {str(e)}")

    def send_verification_email(self, to: str, code: str, username: str = "") -> bool:
        """发送验证码邮件"""
        # Idempotency: suppress duplicate sends within 60 s
        if self._is_duplicate_send(f"verify:{to}:{code}"):
            return True

        safe_username = html_lib.escape(username)
        safe_code = html_lib.escape(code)
        subject = "邮箱验证码 - 内蒙古农畜产品平台"

        body = f"""
        <html>
        <body style="font-family: Arial, sans-serif; padding: 20px;">
            <h2>邮箱验证码</h2>
            <p>{'尊敬的 ' + safe_username + ',' if safe_username else '您好,'}</p>
            <p>您的验证码是:</p>
            <h1 style="color: #4CAF50; letter-spacing: 5px;">{safe_code}</h1>
            <p>验证码有效期为5分钟，请勿泄露给他人。</p>
            <p>如果这不是您的操作，请忽略此邮件。</p>
            <hr>
            <p style="color: #999; font-size: 12px;">
                此邮件由系统自动发送，请勿回复。<br>
                内蒙古农畜产品品牌营销AI赋能云平台
            </p>
        </body>
        </html>
        """

        try:
            return self.send_email(to, subject, body, html=True)
        except Exception as e:
            logger.error(f"发送验证码邮件失败，不影响主流程: to={to}, error={e}")
            return False

    def send_password_reset_email(self, to: str, reset_link: str, username: str = "") -> bool:
        """发送密码重置邮件"""
        # Validate URL scheme to prevent javascript: injection in href
        if not reset_link.startswith(('https://', 'http://')):
            logger.error(f"send_password_reset_email: invalid reset_link scheme, refusing to send")
            raise ValueError("reset_link must be an http/https URL")

        safe_username = html_lib.escape(username)
        safe_link_text = html_lib.escape(reset_link)  # for text display only; href uses validated original
        subject = "密码重置 - 内蒙古农畜产品平台"

        body = f"""
        <html>
        <body style="font-family: Arial, sans-serif; padding: 20px;">
            <h2>密码重置请求</h2>
            <p>{'尊敬的 ' + safe_username + ',' if safe_username else '您好,'}</p>
            <p>我们收到了您的密码重置请求。请点击下面的链接重置密码:</p>
            <p>
                <a href="{reset_link}"
                   style="display: inline-block; padding: 10px 20px;
                          background-color: #4CAF50; color: white;
                          text-decoration: none; border-radius: 5px;">
                    重置密码
                </a>
            </p>
            <p>或复制以下链接到浏览器:</p>
            <p style="color: #666;">{safe_link_text}</p>
            <p>此链接将在1小时后失效。</p>
            <p>如果这不是您的操作，请忽略此邮件。</p>
            <hr>
            <p style="color: #999; font-size: 12px;">
                此邮件由系统自动发送，请勿回复。<br>
                内蒙古农畜产品品牌营销AI赋能云平台
            </p>
        </body>
        </html>
        """

        try:
            return self.send_email(to, subject, body, html=True)
        except Exception as e:
            logger.error(f"发送密码重置邮件失败，不影响主流程: to={to}, error={e}")
            return False

    def send_welcome_email(self, to: str, username: str) -> bool:
        """发送欢迎邮件"""
        safe_username = html_lib.escape(username)
        subject = "欢迎加入内蒙古农畜产品平台"

        body = f"""
        <html>
        <body style="font-family: Arial, sans-serif; padding: 20px;">
            <h2>欢迎加入！</h2>
            <p>尊敬的 {safe_username},</p>
            <p>欢迎加入内蒙古农畜产品品牌营销AI赋能云平台！</p>
            <p>我们的平台致力于:</p>
            <ul>
                <li>展示优质的内蒙古农畜产品</li>
                <li>利用AI技术赋能品牌营销</li>
                <li>连接生产者和消费者</li>
            </ul>
            <p>开始探索平台功能，发现更多可能！</p>
            <hr>
            <p style="color: #999; font-size: 12px;">
                此邮件由系统自动发送，请勿回复。<br>
                内蒙古农畜产品品牌营销AI赋能云平台
            </p>
        </body>
        </html>
        """

        try:
            return self.send_email(to, subject, body, html=True)
        except Exception as e:
            logger.error(f"发送欢迎邮件失败，不影响主流程: to={to}, error={e}")
            return False


class SMSService:
    """短信服务"""

    # Class-level deduplication cache
    _dedup_cache: Dict[str, float] = {}
    _dedup_lock: Lock = Lock()
    _dedup_ttl: int = 60  # seconds

    def __init__(self):
        """初始化短信服务配置"""
        self.provider = settings.SMS_PROVIDER
        self.dev_mode = settings.SMS_DEV_MODE

        if self.provider == "aliyun" and not self.dev_mode:
            self.access_key = settings.ALIYUN_ACCESS_KEY
            self.access_secret = settings.ALIYUN_ACCESS_SECRET
            self.sign_name = settings.ALIYUN_SMS_SIGN
            self.template_code = settings.ALIYUN_SMS_TEMPLATE_CODE

    def _is_duplicate_send(self, key: str) -> bool:
        """Idempotency guard: returns True if this SMS was recently sent."""
        with self.__class__._dedup_lock:
            now = time.time()
            expired = [k for k, ts in list(self.__class__._dedup_cache.items())
                       if now - ts > self.__class__._dedup_ttl]
            for k in expired:
                del self.__class__._dedup_cache[k]
            if key in self.__class__._dedup_cache:
                logger.warning(f"⚠️ WARNING: Duplicate SMS suppressed (key={key})")
                return True
            self.__class__._dedup_cache[key] = now
            return False

    def _send_aliyun_sms(self, phone: str, template_param: dict) -> bool:
        """发送阿里云短信

        参数:
            phone: 手机号
            template_param: 模板参数

        返回:
            是否发送成功
        """
        try:
            from alibabacloud_dysmsapi20170525.client import Client
            from alibabacloud_tea_openapi import models as open_api_models
            from alibabacloud_dysmsapi20170525 import models as dysmsapi_models

            config = open_api_models.Config(
                access_key_id=self.access_key,
                access_key_secret=self.access_secret,
                endpoint='dysmsapi.aliyuncs.com'
            )
            client = Client(config)

            request = dysmsapi_models.SendSmsRequest(
                phone_numbers=phone,
                sign_name=self.sign_name,
                template_code=self.template_code,
                template_param=json.dumps(template_param, ensure_ascii=False)
            )

            response = client.send_sms(request)

            if response.body.code == 'OK':
                logger.info(f"阿里云短信发送成功: phone={phone}")
                return True
            else:
                logger.error(f"阿里云短信发送失败: {response.body.message}")
                return False

        except ImportError:
            logger.error("阿里云SDK未安装，请运行: pip install alibabacloud_dysmsapi20170525")
            raise ExternalServiceError("短信服务未配置")
        except Exception as e:
            logger.error(f"阿里云短信发送失败: {str(e)}")
            raise ExternalServiceError(f"短信发送失败: {str(e)}")

    def send_sms(self, phone: str, message: str) -> bool:
        """发送短信

        参数:
            phone: 手机号
            message: 短信内容

        返回:
            是否发送成功
        """
        # 开发模式：仅打印日志
        if self.dev_mode:
            logger.info(f"[开发模式-短信] To: {phone}, Message: {message}")
            return True

        logger.warning("通用短信发送未实现，请使用 send_verification_sms")
        return False

    def send_verification_sms(self, phone: str, code: str) -> bool:
        """发送验证码短信"""
        # Idempotency: suppress duplicate sends within 60 s
        if self._is_duplicate_send(f"verify:{phone}:{code}"):
            return True

        # 开发模式：仅打印日志
        if self.dev_mode:
            logger.info(f"[开发模式-短信验证码] To: {phone}, Code: {code}")
            return True

        # 阿里云短信
        if self.provider == "aliyun":
            return self._send_aliyun_sms(phone, {"code": code})

        logger.error(f"不支持的短信服务商: {self.provider}")
        return False


class NotificationService:
    """通知服务统一接口"""

    def __init__(self, db=None):
        """初始化通知服务

        参数:
            db: 数据库会话（可选，用于记录通知历史）
        """
        self.db = db
        self.email_service = EmailService()
        self.sms_service = SMSService()

    def send_email(self, to: str, subject: str, body: str, html: bool = False) -> bool:
        """发送邮件"""
        return self.email_service.send_email(to, subject, body, html)

    def send_sms(self, phone: str, message: str) -> bool:
        """发送短信"""
        return self.sms_service.send_sms(phone, message)

    def send_verification_email(self, to: str, code: str, username: str = "") -> bool:
        """发送验证码邮件"""
        return self.email_service.send_verification_email(to, code, username)

    def send_verification_sms(self, phone: str, code: str) -> bool:
        """发送验证码短信"""
        return self.sms_service.send_verification_sms(phone, code)


# 全局实例
email_service = EmailService()
sms_service = SMSService()
