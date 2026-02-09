"""
内容生成模板数据模型 - SQLAlchemy ORM

包含：
- 模板基本信息
- 分类标签
- 模板内容（Prompt）
- 变量定义
- 配置参数
- 使用统计

版本: 1.0
更新日期: 2026-01-17
"""

from sqlalchemy import (
    Column, BIGINT, VARCHAR, Enum, Integer, Boolean, DECIMAL, TEXT, JSON,
    Index, UniqueConstraint, ForeignKey
)
from sqlalchemy.orm import relationship
from datetime import datetime
from typing import Optional, Dict, Any, List
import enum

from .base import BaseModel, generate_uuid


class TemplateContentType(enum.Enum):
    """模板内容类型枚举"""
    COPY = "copy"  # 营销文案
    SCRIPT = "script"  # 直播脚本
    VIDEO_COPY = "video_copy"  # 短视频文案
    SLOGAN = "slogan"  # 广告标语
    STORY = "story"  # 品牌故事


class TemplatePlatform(enum.Enum):
    """模板适用平台枚举"""
    DOUYIN = "douyin"  # 抖音
    XIAOHONGSHU = "xiaohongshu"  # 小红书
    WECHAT = "wechat"  # 微信公众号
    WEIBO = "weibo"  # 微博
    KUAISHOU = "kuaishou"  # 快手
    GENERAL = "general"  # 通用


class GenerationTemplate(BaseModel):
    """内容生成模板模型

    模板包含：
    - 基本信息（名称、描述）
    - 分类（内容类型、平台、类别）
    - 提示词（系统提示和用户提示模板）
    - 变量定义
    - 模型配置
    - 状态和统计
    - 创建者信息
    """

    __tablename__ = "generation_templates"

    # 主键
    id = Column(
        BIGINT,
        primary_key=True,
        autoincrement=True,
        comment="模板ID"
    )

    # UUID标识
    template_uuid = Column(
        VARCHAR(36),
        nullable=False,
        unique=True,
        index=True,
        default=generate_uuid,
        comment="模板UUID"
    )

    # 基本信息
    name = Column(
        VARCHAR(100),
        nullable=False,
        comment="模板名称"
    )
    description = Column(
        TEXT,
        nullable=True,
        comment="模板描述"
    )

    # 分类
    content_type = Column(
        Enum(TemplateContentType),
        nullable=False,
        index=True,
        comment="内容类型"
    )
    platform = Column(
        Enum(TemplatePlatform),
        nullable=False,
        default=TemplatePlatform.GENERAL,
        index=True,
        comment="适用平台"
    )
    category = Column(
        VARCHAR(100),
        nullable=True,
        comment="模板分类"
    )

    # 模板内容
    system_prompt = Column(
        TEXT,
        nullable=False,
        comment="系统提示词"
    )
    user_prompt_template = Column(
        TEXT,
        nullable=False,
        comment="用户提示词模板"
    )
    variables = Column(
        JSON,
        nullable=False,
        comment="变量定义(JSON数组)"
    )
    example_output = Column(
        TEXT,
        nullable=True,
        comment="示例输出"
    )

    # 配置
    model_config = Column(
        JSON,
        nullable=True,
        comment="模型配置(temperature等)"
    )
    max_tokens = Column(
        Integer,
        default=2000,
        comment="最大Token数"
    )

    # 状态
    is_system = Column(
        Boolean,
        default=False,
        comment="是否系统模板"
    )
    is_active = Column(
        Boolean,
        default=True,
        index=True,
        comment="是否启用"
    )

    # 统计
    use_count = Column(
        Integer,
        default=0,
        comment="使用次数"
    )
    avg_rating = Column(
        DECIMAL(3, 2),
        nullable=True,
        comment="平均评分"
    )

    # 创建者
    created_by = Column(
        BIGINT,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        comment="创建人ID(NULL表示系统)"
    )

    # 关系
    creator = relationship(
        "User",
        foreign_keys=[created_by]
    )

    # 索引定义
    __table_args__ = (
        UniqueConstraint("template_uuid", name="uk_template_uuid"),
        Index("idx_content_type", "content_type"),
        Index("idx_platform", "platform"),
        Index("idx_is_system", "is_system"),
        Index("idx_is_active", "is_active"),
        Index("idx_created_by", "created_by"),
    )

    def __repr__(self) -> str:
        return f"<GenerationTemplate(id={self.id}, name={self.name}, content_type={self.content_type.value})>"

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "id": self.id,
            "template_uuid": self.template_uuid,
            "name": self.name,
            "description": self.description,
            "content_type": self.content_type.value if self.content_type else None,
            "platform": self.platform.value if self.platform else None,
            "category": self.category,
            "system_prompt": self.system_prompt,
            "user_prompt_template": self.user_prompt_template,
            "variables": self.variables,
            "example_output": self.example_output,
            "model_config": self.model_config,
            "max_tokens": self.max_tokens,
            "is_system": self.is_system,
            "is_active": self.is_active,
            "use_count": self.use_count,
            "avg_rating": float(self.avg_rating) if self.avg_rating else None,
            "created_by": self.created_by,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    def get_variables(self) -> List[Dict[str, Any]]:
        """获取模板变量列表"""
        return self.variables if isinstance(self.variables, list) else []

    def get_variable_names(self) -> List[str]:
        """获取模板变量名列表"""
        variables = self.get_variables()
        return [var.get("name") for var in variables if isinstance(var, dict)]

    def get_model_config(self) -> Dict[str, Any]:
        """获取模型配置"""
        return self.model_config if isinstance(self.model_config, dict) else {}

    def validate_variables(self, input_dict: Dict[str, Any]) -> tuple:
        """验证输入变量是否完整

        Returns:
            (is_valid: bool, missing_vars: List[str])
        """
        required_vars = self.get_variable_names()
        provided_vars = set(input_dict.keys())
        missing_vars = [var for var in required_vars if var not in provided_vars]

        return len(missing_vars) == 0, missing_vars

    def render_user_prompt(self, variables: Dict[str, Any]) -> str:
        """使用变量渲染用户Prompt"""
        prompt = self.user_prompt_template
        for key, value in variables.items():
            placeholder = "{" + key + "}"
            prompt = prompt.replace(placeholder, str(value))
        return prompt

    def is_published(self) -> bool:
        """检查模板是否已发布"""
        return self.is_active and self.id is not None

    def get_popularity(self) -> str:
        """获取模板热度等级"""
        if self.use_count >= 1000:
            return "hot"
        elif self.use_count >= 100:
            return "popular"
        elif self.use_count >= 10:
            return "normal"
        else:
            return "new"

    def increment_use_count(self) -> int:
        """增加使用计数"""
        self.use_count += 1
        return self.use_count

    def update_rating(self, new_rating: float) -> float:
        """更新平均评分"""
        if self.avg_rating is None:
            self.avg_rating = new_rating
        else:
            # 简化的评分更新（实际应该考虑历史评分数据）
            self.avg_rating = (float(self.avg_rating) * self.use_count + new_rating) / (self.use_count + 1)
        return float(self.avg_rating)

    @classmethod
    def get_by_uuid(cls, template_uuid: str) -> Optional["GenerationTemplate"]:
        """根据UUID获取模板"""
        pass

    @classmethod
    def get_by_type_and_platform(
        cls,
        content_type: str,
        platform: str,
        active_only: bool = True
    ) -> List["GenerationTemplate"]:
        """按内容类型和平台获取模板"""
        pass

    @classmethod
    def get_system_templates(cls, active_only: bool = True) -> List["GenerationTemplate"]:
        """获取所有系统模板"""
        pass

    @classmethod
    def get_user_templates(cls, user_id: int) -> List["GenerationTemplate"]:
        """获取用户创建的模板"""
        pass

    @classmethod
    def get_popular_templates(cls, limit: int = 10) -> List["GenerationTemplate"]:
        """获取热门模板"""
        pass
