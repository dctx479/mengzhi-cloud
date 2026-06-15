"""
文化元素相关数据库模型
包含：采集任务、审核任务、审核记录等

版本: 1.0
创建日期: 2026-06-12
"""

from sqlalchemy import Column, Integer, String, Text, DateTime, JSON, ForeignKey, Enum
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

from app.core.database import Base


class TaskPriority(str, enum.Enum):
    """任务优先级"""

    P0 = "P0"  # 紧急
    P1 = "P1"  # 高
    P2 = "P2"  # 中


class TaskStatus(str, enum.Enum):
    """任务状态"""

    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    ASSIGNED = "assigned"


class ReviewDecision(str, enum.Enum):
    """审核决定"""

    APPROVED = "approved"
    REJECTED = "rejected"
    NEEDS_CORRECTION = "needs_correction"


class ElementStatus(str, enum.Enum):
    """元素状态"""

    PENDING_REVIEW = "pending_review"
    NEEDS_CORRECTION = "needs_correction"
    APPROVED = "approved"
    REJECTED = "rejected"


class CulturalCollectionTask(Base):
    """文化元素采集任务表"""

    __tablename__ = "cultural_collection_tasks"
    __table_args__ = {"extend_existing": True}

    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(String(50), unique=True, index=True, comment="采集任务ID")

    # 产品信息
    product_id = Column(Integer, ForeignKey("products.id"), nullable=True)
    product_name = Column(String(200), nullable=False)
    origin = Column(String(100), nullable=False)
    category = Column(String(100), nullable=False)

    # 采集配置
    targets = Column(Text, comment="采集目标类别（JSON数组）")
    priority = Column(Enum(TaskPriority), default=TaskPriority.P2)

    # 任务状态
    status = Column(Enum(TaskStatus), default=TaskStatus.PENDING)
    result = Column(Text, nullable=True, comment="采集结果（JSON）")

    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, onupdate=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)

    # 关联关系
    product = relationship("Product", back_populates="cultural_tasks")
    review_task = relationship("CulturalReviewTask", back_populates="collection_task", uselist=False)
    elements = relationship("CulturalElement", back_populates="collection_task")


class CulturalElement(Base):
    """文化元素表"""

    __tablename__ = "cultural_elements"
    __table_args__ = {"extend_existing": True}

    id = Column(Integer, primary_key=True, index=True)

    # 基础信息
    name = Column(String(200), nullable=False, index=True)
    type = Column(String(50), nullable=False, index=True, comment="地理景观/传统工艺等")
    story = Column(Text, nullable=False)
    origin_region = Column(String(100), nullable=False)
    keywords = Column(Text, comment="关键词（JSON数组）")
    element_metadata = Column(Text, comment="元数据（JSON对象）")

    # 采集信息
    collection_task_id = Column(String(50), ForeignKey("cultural_collection_tasks.task_id"))
    source = Column(String(50), default="agent", comment="来源：agent/manual/import")

    # 审核状态
    status = Column(Enum(ElementStatus), default=ElementStatus.PENDING_REVIEW, index=True)
    reviewed_at = Column(DateTime, nullable=True)
    reviewed_by = Column(Integer, ForeignKey("users.id"), nullable=True)

    # 审核结果
    approved_at = Column(DateTime, nullable=True)
    approved_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    rejected_at = Column(DateTime, nullable=True)
    rejected_by = Column(Integer, ForeignKey("users.id"), nullable=True)

    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, onupdate=datetime.utcnow)

    # 关联关系
    collection_task = relationship("CulturalCollectionTask", back_populates="elements")
    reviews = relationship("CulturalReview", back_populates="element")
    reviewer = relationship("User", foreign_keys=[reviewed_by])
    approver = relationship("User", foreign_keys=[approved_by])
    rejecter = relationship("User", foreign_keys=[rejected_by])


class CulturalReviewTask(Base):
    """文化元素审核任务表"""

    __tablename__ = "cultural_review_tasks"
    __table_args__ = {"extend_existing": True}

    id = Column(Integer, primary_key=True, index=True)

    # 关联采集任务
    collection_task_id = Column(String(50), ForeignKey("cultural_collection_tasks.task_id"))

    # 任务信息
    element_count = Column(Integer, default=0, comment="待审核元素数量")
    priority = Column(Enum(TaskPriority), default=TaskPriority.P2)
    status = Column(Enum(TaskStatus), default=TaskStatus.PENDING)

    # 分配信息
    assigned_expert_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    assigned_at = Column(DateTime, nullable=True)

    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)

    # 关联关系
    collection_task = relationship("CulturalCollectionTask", back_populates="review_task")
    assigned_expert = relationship("User")


class CulturalReview(Base):
    """文化元素审核记录表"""

    __tablename__ = "cultural_reviews"
    __table_args__ = {"extend_existing": True}

    id = Column(Integer, primary_key=True, index=True)

    # 关联元素
    element_id = Column(Integer, ForeignKey("cultural_elements.id"))

    # 审核人
    expert_id = Column(Integer, ForeignKey("users.id"))

    # 审核决定
    decision = Column(Enum(ReviewDecision), nullable=False)
    comments = Column(Text, nullable=True, comment="审核意见")
    corrections = Column(Text, nullable=True, comment="修正建议（JSON）")

    # 时间戳
    reviewed_at = Column(DateTime, default=datetime.utcnow)

    # 关联关系
    element = relationship("CulturalElement", back_populates="reviews")
    expert = relationship("User")


# =============================================================================
# Alembic 迁移脚本示例
# =============================================================================

"""
# 创建迁移文件
alembic revision -m "add_cultural_collection_tables"

# 迁移脚本内容
\"\"\"add cultural collection tables

Revision ID: xxx
Revises: yyy
Create Date: 2026-06-12

\"\"\"
from alembic import op
import sqlalchemy as sa


def upgrade():
    # 创建采集任务表
    op.create_table(
        'cultural_collection_tasks',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('task_id', sa.String(50), nullable=False),
        sa.Column('product_id', sa.Integer(), nullable=True),
        sa.Column('product_name', sa.String(200), nullable=False),
        sa.Column('origin', sa.String(100), nullable=False),
        sa.Column('category', sa.String(100), nullable=False),
        sa.Column('targets', sa.Text(), nullable=True),
        sa.Column('priority', sa.Enum('P0', 'P1', 'P2', name='taskpriority'), nullable=True),
        sa.Column('status', sa.Enum('pending', 'processing', 'completed', 'failed', 'assigned', name='taskstatus'), nullable=True),
        sa.Column('result', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['product_id'], ['products.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_cultural_collection_tasks_task_id', 'cultural_collection_tasks', ['task_id'], unique=True)

    # 创建文化元素表
    op.create_table(
        'cultural_elements',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(200), nullable=False),
        sa.Column('type', sa.String(50), nullable=False),
        sa.Column('story', sa.Text(), nullable=False),
        sa.Column('origin_region', sa.String(100), nullable=False),
        sa.Column('keywords', sa.Text(), nullable=True),
        sa.Column('metadata', sa.Text(), nullable=True),
        sa.Column('collection_task_id', sa.String(50), nullable=True),
        sa.Column('source', sa.String(50), nullable=True),
        sa.Column('status', sa.Enum('pending_review', 'needs_correction', 'approved', 'rejected', name='elementstatus'), nullable=True),
        sa.Column('reviewed_at', sa.DateTime(), nullable=True),
        sa.Column('reviewed_by', sa.Integer(), nullable=True),
        sa.Column('approved_at', sa.DateTime(), nullable=True),
        sa.Column('approved_by', sa.Integer(), nullable=True),
        sa.Column('rejected_at', sa.DateTime(), nullable=True),
        sa.Column('rejected_by', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['collection_task_id'], ['cultural_collection_tasks.task_id'], ),
        sa.ForeignKeyConstraint(['reviewed_by'], ['users.id'], ),
        sa.ForeignKeyConstraint(['approved_by'], ['users.id'], ),
        sa.ForeignKeyConstraint(['rejected_by'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_cultural_elements_name', 'cultural_elements', ['name'])
    op.create_index('ix_cultural_elements_type', 'cultural_elements', ['type'])

    # 创建审核任务表
    op.create_table(
        'cultural_review_tasks',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('collection_task_id', sa.String(50), nullable=True),
        sa.Column('element_count', sa.Integer(), nullable=True),
        sa.Column('priority', sa.Enum('P0', 'P1', 'P2', name='taskpriority'), nullable=True),
        sa.Column('status', sa.Enum('pending', 'processing', 'completed', 'failed', 'assigned', name='taskstatus'), nullable=True),
        sa.Column('assigned_expert_id', sa.Integer(), nullable=True),
        sa.Column('assigned_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['collection_task_id'], ['cultural_collection_tasks.task_id'], ),
        sa.ForeignKeyConstraint(['assigned_expert_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

    # 创建审核记录表
    op.create_table(
        'cultural_reviews',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('element_id', sa.Integer(), nullable=True),
        sa.Column('expert_id', sa.Integer(), nullable=True),
        sa.Column('decision', sa.Enum('approved', 'rejected', 'needs_correction', name='reviewdecision'), nullable=False),
        sa.Column('comments', sa.Text(), nullable=True),
        sa.Column('corrections', sa.Text(), nullable=True),
        sa.Column('reviewed_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['element_id'], ['cultural_elements.id'], ),
        sa.ForeignKeyConstraint(['expert_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )


def downgrade():
    op.drop_table('cultural_reviews')
    op.drop_table('cultural_review_tasks')
    op.drop_table('cultural_elements')
    op.drop_table('cultural_collection_tasks')

    op.execute('DROP TYPE IF EXISTS reviewdecision')
    op.execute('DROP TYPE IF EXISTS elementstatus')
    op.execute('DROP TYPE IF EXISTS taskstatus')
    op.execute('DROP TYPE IF EXISTS taskpriority')
\"\"\"
"""
