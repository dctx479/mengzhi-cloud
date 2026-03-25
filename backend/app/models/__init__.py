"""
SQLAlchemy ORM模型导出

该模块导出所有数据模型和基类，便于其他模块导入。

版本: 1.0
更新日期: 2026-01-17
"""

from .base import BaseModel, generate_uuid

# 用户相关模型
from .user import User, UserType, UserStatus, UserRole, Gender

# 企业模型
from .enterprise import Enterprise, EnterpriseScale, VerifyStatus, PlanType

# 产品模型
from .product import Product, ProductStatus

# 文化标签模型
from .cultural_tag import CulturalTag, product_tags

# 媒体素材模型
from .media import Media, MediaType, MediaCategory

# 对话和消息模型
from .conversation import Conversation, AgentType, ConversationStatus, ContentType
from .message import Message, MessageRole

# 内容生成相关模型
from .content_record import ContentRecord, Platform, Style, LengthType, RecordStatus
from .generation_template import GenerationTemplate, TemplateContentType, TemplatePlatform

# 配额模型
from .user_quota import UserQuota, QuotaType
from .quota import TenantQuota, QuotaUsage, QuotaResourceType, QuotaPeriodType, QuotaAlertLevel

# 配额支付系统模型
from .quota_package import QuotaPackage, PackageType, PackagePeriod
from .order import Order, OrderStatus
from .payment import Payment, PaymentMethod, PaymentStatus
from .quota_log import QuotaLog, QuotaLogType, QuotaLogStatus
from .billing_transaction import BillingTransaction, BillingStatus

# RBAC权限管理模型
from .role import Role
from .permission import Permission
from .associations import role_permissions, user_roles

# SLA保障系统模型
from .sla import SLAAgreement, SLAMetric, SLAViolation, PerformanceLog, SLALevel, MetricType, ViolationSeverity

# 对账系统模型
from .reconciliation import (
    ReconciliationRecord,
    ReconciliationDifference,
    ReconciliationStatus,
    ReconciliationType,
    DifferenceType,
    DifferenceStatus,
)

# 风控系统模型
from .risk_control import (
    RiskRule,
    RiskEvent,
    RiskBlacklist,
    RiskStatistics,
    RiskLevel,
    RiskAction,
    RuleType,
    EventType,
    BlacklistType,
)

# 租户AI配置模型
from .tenant_ai_config import TenantAIConfig, HealthStatus

# 系统配置模型
from .system_config import SystemConfig

# 导出所有模型
__all__ = [
    # 基类
    "BaseModel",
    "generate_uuid",
    # 用户相关
    "User",
    "UserType",
    "UserStatus",
    "UserRole",
    "Gender",
    # 企业
    "Enterprise",
    "EnterpriseScale",
    "VerifyStatus",
    "PlanType",
    # 产品
    "Product",
    "ProductStatus",
    # 文化标签
    "CulturalTag",
    "product_tags",
    # 媒体素材
    "Media",
    "MediaType",
    "MediaCategory",
    # 对话和消息
    "Conversation",
    "AgentType",
    "ConversationStatus",
    "ContentType",
    "Message",
    "MessageRole",
    # 内容生成
    "ContentRecord",
    "Platform",
    "Style",
    "LengthType",
    "RecordStatus",
    "GenerationTemplate",
    "TemplateContentType",
    "TemplatePlatform",
    # 配额
    "UserQuota",
    "QuotaType",
    "TenantQuota",
    "QuotaUsage",
    "QuotaResourceType",
    "QuotaPeriodType",
    "QuotaAlertLevel",
    # 配额支付系统
    "QuotaPackage",
    "PackageType",
    "PackagePeriod",
    "Order",
    "OrderStatus",
    "Payment",
    "PaymentMethod",
    "PaymentStatus",
    "QuotaLog",
    "QuotaLogType",
    "QuotaLogStatus",
    "BillingTransaction",
    "BillingStatus",
    # RBAC权限管理
    "Role",
    "Permission",
    "role_permissions",
    "user_roles",
    # SLA保障系统
    "SLAAgreement",
    "SLAMetric",
    "SLAViolation",
    "PerformanceLog",
    "SLALevel",
    "MetricType",
    "ViolationSeverity",
    # 对账系统
    "ReconciliationRecord",
    "ReconciliationDifference",
    "ReconciliationStatus",
    "ReconciliationType",
    "DifferenceType",
    "DifferenceStatus",
    # 风控系统
    "RiskRule",
    "RiskEvent",
    "RiskBlacklist",
    "RiskStatistics",
    "RiskLevel",
    "RiskAction",
    "RuleType",
    "EventType",
    "BlacklistType",
    # 租户AI配置
    "TenantAIConfig",
    "HealthStatus",
    # 系统配置
    "SystemConfig",
]
