"""
AI对话Schema - Pydantic数据验证模型

版本: 1.0
更新日期: 2026-01-17
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, ConfigDict


# ==================== 请求Schema ====================

class SendMessageRequest(BaseModel):
    """发送消息请求"""
    model_config = ConfigDict(from_attributes=True)

    content: str = Field(..., min_length=1, max_length=10000, description="消息内容")
    conversation_id: Optional[int] = Field(None, description="对话ID（为空则创建新对话）")
    agent_type: Optional[str] = Field(
        "assistant",
        description="代理类型: xiaoshu/xiaoshang/assistant"
    )


class StreamMessageRequest(SendMessageRequest):
    """流式消息请求"""
    pass


class UpdateConversationRequest(BaseModel):
    """更新对话请求"""
    model_config = ConfigDict(from_attributes=True)

    title: Optional[str] = Field(None, max_length=200, description="对话标题")
    is_favorited: Optional[bool] = Field(None, description="是否收藏")


class AddFeedbackRequest(BaseModel):
    """添加反馈请求"""
    model_config = ConfigDict(from_attributes=True)

    message_id: int = Field(..., description="消息ID")
    rating: int = Field(..., ge=1, le=5, description="评分（1-5）")
    feedback: Optional[str] = Field(None, max_length=1000, description="反馈内容")
    feedback_type: Optional[str] = Field(
        None,
        description="反馈类型: helpful/unhelpful/incorrect"
    )


# ==================== 响应Schema ====================

class MessageResponse(BaseModel):
    """消息响应"""
    model_config = ConfigDict(from_attributes=True)

    id: int
    message_uuid: str
    conversation_id: int
    role: str
    content: str
    input_tokens: int = 0
    output_tokens: int = 0
    total_tokens: int = 0
    cost: float = 0.0
    model: str = "deepseek-chat"
    finish_reason: Optional[str] = None
    rating: Optional[int] = None
    feedback: Optional[str] = None
    feedback_type: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class ConversationResponse(BaseModel):
    """对话响应"""
    model_config = ConfigDict(from_attributes=True)

    id: int
    conversation_uuid: str
    user_id: int
    title: Optional[str] = None
    agent_type: str
    context_product_id: Optional[int] = None
    message_count: int = 0
    total_tokens: int = 0
    status: str = "active"
    last_message_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime


class ConversationDetailResponse(ConversationResponse):
    """对话详情响应（包含消息）"""
    messages: List[MessageResponse] = []


class ConversationListResponse(BaseModel):
    """对话列表响应"""
    total: int
    page: int
    page_size: int
    items: List[ConversationResponse]


class SendMessageResponse(BaseModel):
    """发送消息响应"""
    model_config = ConfigDict(from_attributes=True)

    id: str  # 响应ID
    conversation_id: int
    message: MessageResponse
    usage: Dict[str, int] = Field(
        default_factory=dict,
        description="Token使用情况"
    )


class FeedbackResponse(BaseModel):
    """反馈响应"""
    message_id: int
    rating: int
    feedback: Optional[str]
    feedback_type: Optional[str]
    updated_at: datetime


class ErrorResponse(BaseModel):
    """错误响应"""
    code: int
    message: str
    errors: Optional[List[Dict[str, Any]]] = None
    request_id: Optional[str] = None


class HealthCheckResponse(BaseModel):
    """健康检查响应"""
    status: str
    timestamp: datetime
    services: Optional[Dict[str, str]] = None


# ==================== 类别名（兼容性） ====================

# 为了兼容旧代码，提供类别名
ConversationCreate = UpdateConversationRequest
ConversationUpdate = UpdateConversationRequest
ChatStreamRequest = StreamMessageRequest
ChatNonStreamRequest = SendMessageRequest
ChatNonStreamResponse = SendMessageResponse
FeedbackRequest = AddFeedbackRequest
