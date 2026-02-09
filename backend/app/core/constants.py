"""
应用常量定义 - BUG-020修复

避免硬编码的魔法数字和字符串，所有常量在此集中定义

版本: 1.0
更新日期: 2026-01-17
"""

# ==================== 认证相关常量 ====================

# Token相关
TOKEN_TYPE_ACCESS = "access"
TOKEN_TYPE_REFRESH = "refresh"
TOKEN_JTI_PREFIX = "token_blacklist:"
VERIFY_CODE_PREFIX = "verify_code:"

# 登录安全
MAX_LOGIN_ATTEMPTS = 5  # 最大登录尝试次数
LOGIN_LOCK_MINUTES = 30  # 账号锁定时长（分钟）
VERIFICATION_CODE_TTL = 300  # 验证码有效期（秒）

# bcrypt密码加密轮次
BCRYPT_ROUNDS = 12

# ==================== 分页相关常量 ====================

DEFAULT_PAGE_SIZE = 10
MAX_PAGE_SIZE = 100
MIN_PAGE_SIZE = 1
DEFAULT_PAGE_NUMBER = 1

# ==================== 产品相关常量 ====================

# 允许的排序字段
ALLOWED_SORT_FIELDS = ['created_at', 'price', 'name', 'updated_at']
DEFAULT_SORT_FIELD = 'created_at'
ALLOWED_SORT_ORDERS = ['asc', 'desc']
DEFAULT_SORT_ORDER = 'desc'

# 产品缓存
PRODUCT_CACHE_TTL = 300  # 产品列表缓存时长（秒）
PRODUCT_CACHE_KEY = "products:list:{page}:{size}:{filters}"
PRODUCT_DETAIL_CACHE_KEY = "product:detail:{id}"

# ==================== 文化标签相关常量 ====================

# 文化标签分类代码
TAG_CATEGORY_GEO = "geo"              # 地理标志
TAG_CATEGORY_ETHNICITY = "ethnicity"   # 民族文化
TAG_CATEGORY_HISTORY = "history"       # 历史传承
TAG_CATEGORY_CRAFT = "craft"           # 工艺特色
TAG_CATEGORY_FESTIVAL = "festival"     # 节日习俗
TAG_CATEGORY_NUTRITION = "nutrition"   # 营养价值
TAG_CATEGORY_STORY = "story"           # 文化故事

# 文化标签分类定义
TAG_CATEGORIES = [
    {"code": TAG_CATEGORY_GEO, "name": "地理标志", "icon": "🗺️", "description": "地理标志产品认证"},
    {"code": TAG_CATEGORY_ETHNICITY, "name": "民族文化", "icon": "🎭", "description": "蒙古族等民族传统文化"},
    {"code": TAG_CATEGORY_HISTORY, "name": "历史传承", "icon": "📜", "description": "历史渊源与文化传承"},
    {"code": TAG_CATEGORY_CRAFT, "name": "工艺特色", "icon": "🛠️", "description": "传统制作工艺特色"},
    {"code": TAG_CATEGORY_FESTIVAL, "name": "节日习俗", "icon": "🎉", "description": "节日庆典与习俗"},
    {"code": TAG_CATEGORY_NUTRITION, "name": "营养价值", "icon": "💪", "description": "营养成分与功效"},
    {"code": TAG_CATEGORY_STORY, "name": "文化故事", "icon": "📖", "description": "产品背后的文化故事"},
]

# 标签缓存
TAG_CACHE_TTL = 600  # 标签缓存时长（秒）
TAG_LIST_CACHE_KEY = "tags:list:{category}:{keyword}"
TAG_RECOMMEND_CACHE_KEY = "tags:recommend:{product_id}"
POPULAR_TAGS_CACHE_KEY = "tags:popular:{limit}"

# ==================== 文件上传相关常量 ====================

# 文件大小限制（字节）
MAX_AVATAR_SIZE = 5 * 1024 * 1024  # 5MB
MAX_IMAGE_SIZE = 10 * 1024 * 1024  # 10MB
MAX_FILE_SIZE = 100 * 1024 * 1024  # 100MB

# 允许的文件类型
ALLOWED_IMAGE_TYPES = ['image/jpeg', 'image/png', 'image/gif', 'image/webp']
ALLOWED_IMAGE_EXTENSIONS = ['.jpg', '.jpeg', '.png', '.gif', '.webp']
ALLOWED_DOCUMENT_TYPES = ['application/pdf', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document']
ALLOWED_DOCUMENT_EXTENSIONS = ['.pdf', '.docx']

# 上传路径
UPLOAD_DIR = "uploads"
AVATAR_UPLOAD_DIR = "uploads/avatars"
PRODUCT_IMAGE_UPLOAD_DIR = "uploads/products"

# ==================== 数据库相关常量 ====================

# 数据库连接池
DB_POOL_SIZE = 10
DB_MAX_OVERFLOW = 20
DB_POOL_TIMEOUT = 30  # 连接超时（秒）

# Redis连接
REDIS_POOL_SIZE = 10
REDIS_POOL_TIMEOUT = 5

# ==================== 日志相关常量 ====================

LOG_FORMAT = "<level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>"
LOG_LEVEL = "INFO"
LOG_FILE_PATH = "logs/app.log"
LOG_ROTATION = "500 MB"
LOG_RETENTION = "10 days"

# ==================== 业务逻辑常量 ====================

# 用户类型
USER_TYPE_INDIVIDUAL = "individual"  # 个人用户
USER_TYPE_ENTERPRISE = "enterprise"  # 企业用户
USER_TYPE_ADMIN = "admin"  # 管理员

# 用户角色
ROLE_USER = "user"
ROLE_ADMIN = "admin"
ROLE_ENTERPRISE_ADMIN = "enterprise_admin"

# 账号状态
ACCOUNT_STATUS_ACTIVE = "active"
ACCOUNT_STATUS_INACTIVE = "inactive"
ACCOUNT_STATUS_BANNED = "banned"
ACCOUNT_STATUS_SUSPENDED = "suspended"

# 日期相关
DATE_FORMAT = "%Y-%m-%d"
DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"
ISO_DATETIME_FORMAT = "%Y-%m-%dT%H:%M:%S.%fZ"

# ==================== 邮件/短信常量 ====================

# 邮件模板
EMAIL_TEMPLATE_REGISTER = "register"
EMAIL_TEMPLATE_RESET_PASSWORD = "reset_password"
EMAIL_TEMPLATE_VERIFY_EMAIL = "verify_email"

# 短信模板
SMS_TEMPLATE_REGISTER = "register"
SMS_TEMPLATE_RESET_PASSWORD = "reset_password"
SMS_TEMPLATE_VERIFY_PHONE = "verify_phone"

# ==================== API相关常量 ====================

API_VERSION = "v1"
API_PREFIX = f"/api/{API_VERSION}"
REQUEST_TIMEOUT = 30  # 请求超时（秒）

# ==================== 频率限制常量 (P1-6修复) ====================

# 登录频率限制
RATE_LIMIT_LOGIN_MAX_REQUESTS = 5  # 5次登录尝试
RATE_LIMIT_LOGIN_WINDOW_SECONDS = 300  # 5分钟窗口

# 注册频率限制
RATE_LIMIT_REGISTER_MAX_REQUESTS = 3  # 3次注册尝试
RATE_LIMIT_REGISTER_WINDOW_SECONDS = 3600  # 1小时窗口

# 验证码频率限制
RATE_LIMIT_CAPTCHA_MAX_REQUESTS = 10  # 10次验证码请求
RATE_LIMIT_CAPTCHA_WINDOW_SECONDS = 3600  # 1小时窗口

# API调用频率限制
RATE_LIMIT_API_MAX_REQUESTS = 100  # 100次API调用
RATE_LIMIT_API_WINDOW_SECONDS = 60  # 1分钟窗口

# 密码重置频率限制
RATE_LIMIT_PASSWORD_RESET_MAX_REQUESTS = 3  # 3次密码重置
RATE_LIMIT_PASSWORD_RESET_WINDOW_SECONDS = 3600  # 1小时窗口

# ==================== 错误消息 ====================

ERROR_MESSAGE_INVALID_TOKEN = "无效的认证令牌"
ERROR_MESSAGE_TOKEN_EXPIRED = "认证令牌已过期，请重新登录"
ERROR_MESSAGE_PERMISSION_DENIED = "权限不足"
ERROR_MESSAGE_RESOURCE_NOT_FOUND = "请求的资源不存在"
ERROR_MESSAGE_DUPLICATE_RECORD = "记录已存在"
ERROR_MESSAGE_INVALID_PARAMETERS = "参数无效"
