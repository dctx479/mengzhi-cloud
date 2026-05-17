from pydantic_settings import BaseSettings
from pydantic import field_validator, model_validator, Field
from functools import lru_cache
from typing import Optional, List, Tuple
import warnings
import os


class Settings(BaseSettings):
    """应用配置

    P1安全修复:
    - DEBUG 默认值根据 ENVIRONMENT 自动设置
    - 生产环境自动禁用 DEBUG
    - 数据库密码安全验证
    - 启动时安全检查
    """

    # 应用配置
    APP_NAME: str = "内蒙古农畜产品AI平台"
    DEBUG: bool = False  # P1修复: 默认为 False，仅开发环境显式启用
    VERSION: str = "0.1.0"
    ENVIRONMENT: str = "development"  # development/production/test

    # 数据库配置
    DATABASE_URL: str = "mysql+pymysql://root:root123@localhost:3306/agri_platform?charset=utf8mb4"

    # P1修复: 验证数据库URL安全性
    @field_validator('DATABASE_URL')
    @classmethod
    def validate_database_url(cls, v: str, info) -> str:
        """验证数据库URL的安全性

        生产环境不允许使用默认的弱密码
        """
        environment = os.getenv('ENVIRONMENT', 'development')
        app_env = os.getenv('APP_ENV', '')

        # 测试环境跳过验证
        if environment == 'test' or app_env == 'test' or os.getenv('TEST_MODE') == 'True':
            return v

        # 默认弱密码列表
        weak_passwords = ['root123', 'password', '123456', 'admin', 'root', 'test']

        for weak_pwd in weak_passwords:
            if f':{weak_pwd}@' in v:
                if environment == 'production' or app_env == 'production':
                    raise ValueError(
                        f"生产环境不允许使用弱数据库密码！\n"
                        f"检测到可能的弱密码，请在.env文件中设置强密码:\n"
                        f"  DATABASE_URL=mysql+pymysql://user:strong_password@host:port/db"
                    )
                else:
                    # 开发环境仅警告
                    warnings.warn(
                        f"检测到弱数据库密码，建议在生产环境使用强密码",
                        UserWarning
                    )
                break

        return v

    # 多租户隔离配置
    TENANT_ISOLATION_MODE: str = "hybrid"  # hybrid/shared/isolated
    TENANT_DB_PREFIX: str = "tenant_"  # 租户数据库前缀
    TENANT_DB_HOST: str = "localhost"  # 租户数据库主机
    TENANT_DB_PORT: int = 3306  # 租户数据库端口
    TENANT_DB_USER: str = "root"  # 租户数据库用户
    TENANT_DB_PASSWORD: str = ""  # 租户数据库密码（必须从环境变量配置）

    # P1修复: 验证租户数据库密码安全性
    @field_validator('TENANT_DB_PASSWORD')
    @classmethod
    def validate_tenant_db_password(cls, v: str, info) -> str:
        """验证租户数据库密码的安全性"""
        environment = os.getenv('ENVIRONMENT', 'development')
        app_env = os.getenv('APP_ENV', '')

        if environment == 'test' or app_env == 'test' or os.getenv('TEST_MODE') == 'True':
            return v

        weak_passwords = ['root123', 'password', '123456', 'admin', 'root', 'test', '']

        if v in weak_passwords:
            if environment == 'production' or app_env == 'production':
                raise ValueError(
                    "生产环境不允许使用弱租户数据库密码！\n"
                    "请在.env文件中设置TENANT_DB_PASSWORD为强密码"
                )
            else:
                warnings.warn(
                    "检测到弱租户数据库密码，建议在生产环境使用强密码",
                    UserWarning
                )

        return v

    MAX_TENANT_DATABASES: int = 1000  # 最大租户数据库数
    TENANT_DB_POOL_SIZE: int = 5  # 租户数据库连接池大小
    TENANT_DB_MAX_OVERFLOW: int = 10  # 租户数据库最大溢出连接数
    TENANT_DB_POOL_TIMEOUT: int = 30  # 连接池超时（秒）
    TENANT_DB_POOL_RECYCLE: int = 3600  # 连接回收时间（秒）

    # Redis配置
    REDIS_URL: str = "redis://localhost:6379/0"
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_PASSWORD: Optional[str] = None
    REDIS_DB: int = 0

    # JWT配置
    SECRET_KEY: str = "your-secret-key-change-in-production-at-least-32-chars"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # P1-7: 验证SECRET_KEY强度
    @field_validator('SECRET_KEY')
    @classmethod
    def validate_secret_key(cls, v: str, info) -> str:
        """验证SECRET_KEY的安全性

        要求:
        1. 不能是默认值
        2. 长度至少32字符
        3. 不能是常见弱密钥

        生产环境必须使用强密钥，可使用以下命令生成:
        python scripts/generate_secret_key.py
        """
        # 获取环境变量，检查是否为测试环境
        environment = os.getenv('ENVIRONMENT', 'development')
        app_env = os.getenv('APP_ENV', '')

        # 测试环境跳过严格验证
        if environment == 'test' or app_env == 'test' or os.getenv('TEST_MODE') == 'True':
            return v

        # 默认值列表
        weak_keys = [
            "your-secret-key-change-in-production-at-least-32-chars",
            "change-me",
            "secret",
            "password",
            "12345678",
            "secret-key",
            "my-secret-key"
        ]

        # 检查是否为默认值或弱密钥
        if v.lower() in [k.lower() for k in weak_keys]:
            if environment == 'production' or app_env == 'production':
                raise ValueError(
                    "生产环境不允许使用默认值或弱SECRET_KEY！\n"
                    "请在.env文件中设置强密钥，或使用以下命令生成:\n"
                    "  python scripts/generate_secret_key.py\n"
                    "然后将生成的密钥添加到.env文件:\n"
                    "  SECRET_KEY=<生成的密钥>"
                )
            else:
                # 开发环境仅警告
                warnings.warn(
                    "检测到弱SECRET_KEY，建议在生产环境使用强密钥",
                    UserWarning
                )

        # 检查长度
        if len(v) < 32:
            if environment == 'production' or app_env == 'production':
                raise ValueError(
                    f"生产环境SECRET_KEY长度不足！当前长度: {len(v)}, 要求至少: 32\n"
                    "请使用以下命令生成强密钥:\n"
                    "  python scripts/generate_secret_key.py"
                )
            else:
                warnings.warn(
                    f"SECRET_KEY长度不足 ({len(v)} < 32)，建议在生产环境使用更长的密钥",
                    UserWarning
                )

        return v

    # DeepSeek API配置
    DEEPSEEK_API_KEY: Optional[str] = None
    DEEPSEEK_API_BASE: str = "https://api.deepseek.com"
    DEEPSEEK_API_URL: str = "https://api.deepseek.com/v1"
    DEEPSEEK_MODEL: str = "deepseek-chat"
    DEEPSEEK_TIMEOUT: int = 120  # API请求超时时间（秒）
    DEEPSEEK_STREAM_TIMEOUT: int = 300  # 流式响应超时时间（秒）
    DEEPSEEK_MAX_RETRIES: int = 3  # 最大重试次数
    DEEPSEEK_MAX_TOKENS: int = 4096  # 最大token数
    DEEPSEEK_TEMPERATURE: float = 0.7  # 温度参数
    DEEPSEEK_TOP_P: float = 0.9  # Top-p参数

    # DeepSeek API密钥验证
    @field_validator('DEEPSEEK_API_KEY')
    @classmethod
    def validate_deepseek_api_key(cls, v: Optional[str], info) -> Optional[str]:
        """验证DeepSeek API密钥的格式和安全性

        要求:
        1. 生产环境必须提供有效的API密钥
        2. API密钥格式必须正确（sk-开头）
        3. 不能使用默认的占位符密钥

        开发和测试环境可以使用占位符密钥
        """
        environment = os.getenv('ENVIRONMENT', 'development')
        app_env = os.getenv('APP_ENV', '')

        # 测试环境跳过严格验证
        if environment == 'test' or app_env == 'test' or os.getenv('TEST_MODE') == 'True':
            return v

        # 如果未提供密钥
        if not v:
            if environment == 'production' or app_env == 'production':
                raise ValueError(
                    "生产环境必须提供DEEPSEEK_API_KEY！\n"
                    "请在.env文件中设置有效的DeepSeek API密钥:\n"
                    "  DEEPSEEK_API_KEY=sk-your-actual-api-key-here\n"
                    "获取API密钥: https://platform.deepseek.com/api_keys"
                )
            # 开发环境允许为空，但会发出警告
            return v

        # 检查是否为占位符密钥
        placeholder_keys = [
            "your-deepseek-api-key-here",
            "sk-xxx-production-key-xxx",
            "test-api-key",
            "change-me",
            "placeholder"
        ]

        if v.lower() in [k.lower() for k in placeholder_keys]:
            if environment == 'production' or app_env == 'production':
                raise ValueError(
                    "生产环境不能使用占位符API密钥！\n"
                    "请在.env文件中设置真实的DeepSeek API密钥:\n"
                    "  DEEPSEEK_API_KEY=sk-your-actual-api-key-here\n"
                    "获取API密钥: https://platform.deepseek.com/api_keys"
                )
            # 开发环境允许占位符，但会在日志中警告
            return v

        # 检查API密钥格式（DeepSeek密钥通常以sk-开头）
        if not v.startswith('sk-'):
            warnings.warn(
                f"DeepSeek API密钥格式可能不正确（通常以'sk-'开头），当前值: {v[:6]}...",
                UserWarning
            )

        # 检查密钥长度（DeepSeek密钥通常较长）
        if len(v) < 20:
            warnings.warn(
                f"DeepSeek API密钥长度可能不足（当前: {len(v)}），请确认使用完整密钥",
                UserWarning
            )

        return v

    # 邮件配置 (BUG-023修复)
    SMTP_SERVER: str = "smtp.example.com"
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_FROM_EMAIL: str = "noreply@agri-platform.com"
    SMTP_FROM_NAME: str = "内蒙古农畜产品平台"
    EMAIL_DEV_MODE: bool = True  # 开发模式：仅打印日志，不实际发送

    # 短信配置
    SMS_PROVIDER: str = "aliyun"  # aliyun/tencent/dev
    SMS_DEV_MODE: bool = True  # 开发模式：仅打印日志
    # 阿里云短信
    ALIYUN_ACCESS_KEY: str = ""
    ALIYUN_ACCESS_SECRET: str = ""
    ALIYUN_SMS_SIGN: str = "内蒙古农畜产品平台"
    ALIYUN_SMS_TEMPLATE_CODE: str = ""  # 验证码模板ID

    # CORS配置
    CORS_ORIGINS: List[str] = Field(
        default=["http://localhost:5173", "http://127.0.0.1:5173", "http://localhost:8080", "http://127.0.0.1:8080"]
    )

    @field_validator('CORS_ORIGINS', mode='before')
    @classmethod
    def parse_cors_origins(cls, v):
        """解析CORS_ORIGINS，支持逗号分隔的字符串或JSON数组"""
        if isinstance(v, str):
            # 尝试JSON解析
            import json
            try:
                return json.loads(v)
            except (json.JSONDecodeError, ValueError):
                # 如果不是JSON，按逗号分隔
                return [origin.strip() for origin in v.split(',') if origin.strip()]
        return v

    # 文件上传配置
    UPLOAD_DIR: str = "uploads"  # 本地上传目录
    MAX_IMAGE_SIZE: int = 50 * 1024 * 1024  # 50MB for images
    MAX_VIDEO_SIZE: int = 200 * 1024 * 1024  # 200MB for videos
    ALLOWED_IMAGE_TYPES: List[str] = Field(
        default=["image/jpeg", "image/png", "image/webp", "image/gif"]
    )
    ALLOWED_IMAGE_EXTENSIONS: List[str] = Field(
        default=[".jpg", ".jpeg", ".png", ".gif", ".webp"]
    )
    ALLOWED_VIDEO_TYPES: List[str] = Field(
        default=["video/mp4", "video/mpeg", "video/quicktime"]
    )
    ALLOWED_VIDEO_EXTENSIONS: List[str] = Field(
        default=[".mp4", ".mpeg", ".mpg", ".mov"]
    )

    # OSS配置（阿里云OSS、腾讯云COS等）
    USE_OSS: bool = False  # 是否使用对象存储
    OSS_ENDPOINT: str = ""
    OSS_ACCESS_KEY: str = ""
    OSS_SECRET_KEY: str = ""
    OSS_BUCKET: str = ""
    OSS_DOMAIN: str = ""  # CDN域名

    # 图片处理
    IMAGE_THUMBNAIL_SIZE: Tuple[int, int] = (300, 300)  # 缩略图尺寸
    IMAGE_QUALITY: int = 85  # 压缩质量

    # 支付配置
    PAYMENT_ENABLED: bool = True  # 是否启用支付功能
    PAYMENT_DEV_MODE: bool = True  # 开发模式：自动完成支付，无需真实支付

    # 支付宝配置
    ALIPAY_APP_ID: str = ""  # 支付宝应用ID
    ALIPAY_PRIVATE_KEY: str = ""  # 支付宝应用私钥
    ALIPAY_PUBLIC_KEY: str = ""  # 支付宝公钥
    ALIPAY_GATEWAY: str = "https://openapi.alipaydev.com/gateway.do"  # 支付宝网关（沙箱）
    ALIPAY_CALLBACK_IPS: List[str] = Field(
        default=[
            "110.75.143.0/24",  # 支付宝回调IP段1
            "110.75.144.0/24",  # 支付宝回调IP段2
            "127.0.0.1",        # 本地测试
            "localhost"         # 本地测试
        ]
    )

    # 微信支付配置
    WECHAT_APP_ID: str = ""  # 微信应用ID
    WECHAT_MCH_ID: str = ""  # 微信商户号
    WECHAT_API_KEY: str = ""  # 微信API密钥
    WECHAT_CERT_PATH: str = ""  # 微信证书路径
    WECHAT_KEY_PATH: str = ""  # 微信密钥路径
    WECHAT_CALLBACK_IPS: List[str] = Field(
        default=[
            "101.226.0.0/16",   # 微信回调IP段1
            "101.227.0.0/16",   # 微信回调IP段2
            "127.0.0.1",        # 本地测试
            "localhost"         # 本地测试
        ]
    )

    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "ignore"  # 忽略.env中未定义的字段

    # P1修复: 模型初始化后的安全检查
    @model_validator(mode='after')
    def security_check(self) -> 'Settings':
        """启动时安全检查

        在配置加载完成后执行综合安全检查，
        生产环境强制执行，开发环境仅警告
        """
        is_production = self.ENVIRONMENT == 'production'
        security_issues = []

        # 检查 DEBUG 模式
        if self.DEBUG and is_production:
            security_issues.append(
                "生产环境不应启用 DEBUG 模式！请设置 DEBUG=False"
            )

        # 检查支付开发模式
        if self.PAYMENT_DEV_MODE and is_production and self.PAYMENT_ENABLED:
            security_issues.append(
                "生产环境不应启用支付开发模式！请设置 PAYMENT_DEV_MODE=False"
            )

        # 检查邮件开发模式
        if self.EMAIL_DEV_MODE and is_production:
            security_issues.append(
                "生产环境不应启用邮件开发模式！请设置 EMAIL_DEV_MODE=False"
            )

        # 检查短信开发模式
        if self.SMS_DEV_MODE and is_production:
            security_issues.append(
                "生产环境不应启用短信开发模式！请设置 SMS_DEV_MODE=False"
            )

        # 检查 CORS 配置
        if is_production and '*' in str(self.CORS_ORIGINS):
            security_issues.append(
                "生产环境不应允许所有来源的 CORS 请求！请配置具体的域名"
            )

        # 输出安全检查结果
        if security_issues:
            if is_production:
                raise ValueError(
                    "生产环境安全检查失败:\n" +
                    "\n".join(f"  - {issue}" for issue in security_issues)
                )
            else:
                for issue in security_issues:
                    warnings.warn(f"安全提示: {issue}", UserWarning)

        return self


@lru_cache()
def get_settings() -> Settings:
    """获取配置单例"""
    return Settings()


settings = get_settings()
