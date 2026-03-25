"""
对话API路由 - 处理HTTP请求和响应

版本: 1.0
更新日期: 2026-01-17
"""

import json
import uuid
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Header, Request
from fastapi.responses import StreamingResponse
from sqlalchemy import text
from sqlalchemy.orm import Session
from loguru import logger

from app.schemas.chat import (
    SendMessageRequest,
    StreamMessageRequest,
    MessageResponse,
    ConversationCreate,
    ConversationUpdate,
    ConversationResponse,
    ConversationListResponse,
    ConversationDetailResponse,
    ChatStreamRequest,
    ChatNonStreamRequest,
    ChatNonStreamResponse,
    FeedbackRequest,
    FeedbackResponse,
    ErrorResponse,
)
from app.services.chat_service import ChatService
from app.core.config import settings
from app.core.errors import BusinessException, ErrorCode
from app.api.deps import get_db, get_current_user

# 创建路由
router = APIRouter()


# 依赖注入：获取用户ID（从header或token）
async def get_user_id(
    authorization: Optional[str] = Header(None, description="Bearer token"), db: Session = Depends(get_db)
) -> int:
    """
    从认证头获取用户整数ID（users.id）

    Args:
        authorization: Authorization header
        db: 数据库会话

    Returns:
        用户整数ID (users.id)
    """
    if not authorization:
        raise HTTPException(status_code=401, detail="Missing authorization header")

    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid authorization header format")

    token = authorization[7:]  # Remove "Bearer " prefix

    try:
        from app.services.auth_service import AuthService
        from app.models.user import User

        auth_service = AuthService(db)
        payload = auth_service.decode_token(token)

        user_uuid = payload.get("sub")
        if not user_uuid:
            raise HTTPException(status_code=401, detail="Invalid token payload")

        # JWT sub 存的是 user_uuid (字符串), 需要查出整数 id
        user = db.query(User).filter(User.user_uuid == user_uuid).first()
        if not user:
            raise HTTPException(status_code=401, detail="User not found")

        return user.id
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Token verification failed: {str(e)}")
        raise HTTPException(status_code=401, detail="Invalid or expired token")


@router.post("/message", response_model=ChatNonStreamResponse)
async def send_message(
    request: ChatNonStreamRequest, user_id: int = Depends(get_user_id), db: Session = Depends(get_db)
):
    """
    发送消息（非流式）

    Args:
        request: 聊天请求
        user_id: 用户ID
        db: 数据库会话

    Returns:
        对话响应
    """
    try:
        service = ChatService(db)

        conversation_id, response_text, input_tokens, output_tokens, cost = await service.send_message(
            user_id=user_id, content=request.content, conversation_id=request.conversation_id, temperature=0.7
        )

        # 构建响应消息
        response_message = MessageResponse(
            id=0,
            message_uuid=str(uuid.uuid4()),
            conversation_id=conversation_id,
            role="assistant",
            content=response_text,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            total_tokens=input_tokens + output_tokens,
            cost=cost,
            model="deepseek-chat",
            finish_reason="stop",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )

        return ChatNonStreamResponse(
            id=str(uuid.uuid4()),
            conversation_id=conversation_id,
            message=response_message,
            usage={
                "prompt_tokens": input_tokens,
                "completion_tokens": output_tokens,
                "total_tokens": input_tokens + output_tokens,
            },
        )

    except BusinessException as e:
        logger.error(f"Business error: {e.message}")
        raise HTTPException(status_code=e.get_http_status(), detail=e.message)
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/stream")
async def send_message_stream(
    request: ChatStreamRequest, user_id: int = Depends(get_user_id), db: Session = Depends(get_db)
):
    """
    发送消息（流式SSE）

    Args:
        request: 聊天请求
        user_id: 用户ID
        db: 数据库会话

    Returns:
        流式响应（SSE）
    """
    try:
        service = ChatService(db)

        async def event_generator():
            """生成SSE事件流"""
            try:
                async for chunk in service.send_message_stream(
                    user_id=user_id, content=request.content, conversation_id=request.conversation_id, temperature=0.7
                ):
                    # 发送数据块
                    yield f"data: {chunk}\n\n"

                # 发送完成信号
                yield f"data: {json.dumps({'status': 'completed'})}\n\n"

            except BusinessException as e:
                logger.error(f"Stream error: {e.message}")
                error_data = json.dumps({"error": True, "code": e.code, "message": e.message})
                yield f"data: {error_data}\n\n"
            except Exception as e:
                logger.error(f"Stream unexpected error: {str(e)}")
                error_data = json.dumps(
                    {"error": True, "code": ErrorCode.SYSTEM_ERROR, "message": "Stream processing failed"}
                )
                yield f"data: {error_data}\n\n"

        return StreamingResponse(
            event_generator(),
            media_type="text/event-stream",
            headers={"Cache-Control": "no-cache", "Connection": "keep-alive", "X-Accel-Buffering": "no"},
        )

    except Exception as e:
        logger.error(f"Stream setup error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to setup stream")


@router.post("/conversations", response_model=ConversationResponse)
async def create_conversation(
    request: ConversationCreate, user_id: int = Depends(get_user_id), db: Session = Depends(get_db)
):
    """
    创建新对话

    Returns:
        新创建的对话
    """
    try:
        service = ChatService(db)
        conv = service._get_or_create_conversation(user_id, None)
        if request and request.title:
            conv.title = request.title
            db.commit()
            db.refresh(conv)
        return ConversationResponse.model_validate(conv)
    except BusinessException as e:
        logger.error(f"Business error: {e.message}")
        raise HTTPException(status_code=e.get_http_status(), detail=e.message)
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/conversations", response_model=ConversationListResponse)
async def get_conversations(
    page: int = 1,
    page_size: int = 20,
    status: str = "active",
    user_id: int = Depends(get_user_id),
    db: Session = Depends(get_db),
):
    """
    获取对话列表

    Args:
        page: 页码
        page_size: 每页数量
        status: 状态过滤
        user_id: 用户ID
        db: 数据库会话

    Returns:
        对话列表
    """
    try:
        if page < 1:
            page = 1
        if page_size < 1 or page_size > 100:
            page_size = 20

        service = ChatService(db)
        total, conversations = service.get_conversations(user_id=user_id, page=page, page_size=page_size, status=status)

        return ConversationListResponse(
            total=total, page=page, page_size=page_size, items=[ConversationResponse.model_validate(conv) for conv in conversations]
        )

    except BusinessException as e:
        logger.error(f"Business error: {e.message}")
        raise HTTPException(status_code=e.get_http_status(), detail=e.message)
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/conversations/{conversation_id}", response_model=ConversationDetailResponse)
async def get_conversation(conversation_id: str, user_id: int = Depends(get_user_id), db: Session = Depends(get_db)):
    """
    获取对话详情

    Args:
        conversation_id: 对话ID
        user_id: 用户ID
        db: 数据库会话

    Returns:
        对话详情
    """
    try:
        service = ChatService(db)
        conversation = service.get_conversation_detail(conversation_id=conversation_id, user_id=user_id)

        return ConversationDetailResponse.model_validate(conversation)

    except BusinessException as e:
        logger.error(f"Business error: {e.message}")
        raise HTTPException(status_code=e.get_http_status(), detail=e.message)
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.delete("/conversations/{conversation_id}")
async def delete_conversation(conversation_id: str, user_id: int = Depends(get_user_id), db: Session = Depends(get_db)):
    """
    删除对话

    Args:
        conversation_id: 对话ID
        user_id: 用户ID
        db: 数据库会话

    Returns:
        删除结果
    """
    try:
        service = ChatService(db)
        service.delete_conversation(conversation_id=conversation_id, user_id=user_id)

        return {"success": True, "message": "Conversation deleted successfully"}

    except BusinessException as e:
        logger.error(f"Business error: {e.message}")
        raise HTTPException(status_code=e.get_http_status(), detail=e.message)
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/conversations/{conversation_id}/clear")
async def clear_conversation(conversation_id: str, user_id: int = Depends(get_user_id), db: Session = Depends(get_db)):
    """
    清空对话消息（保留对话，删除所有消息）

    Args:
        conversation_id: 对话ID
        user_id: 用户ID
        db: 数据库会话

    Returns:
        操作结果
    """
    try:
        from app.models.conversation import Conversation
        from app.models.message import Message

        conv = (
            db.query(Conversation)
            .filter(Conversation.id == int(conversation_id), Conversation.user_id == user_id)
            .first()
        )

        if not conv:
            raise HTTPException(status_code=404, detail="对话不存在")

        db.query(Message).filter(Message.conversation_id == conv.id).delete()
        conv.message_count = 0
        db.commit()

        return {"success": True, "message": "对话已清空"}

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Clear conversation error: {str(e)}")
        raise HTTPException(status_code=500, detail="清空对话失败")


@router.delete("/conversations/{conversation_id}/messages/{message_id}")
async def delete_message(
    conversation_id: str, message_id: str, user_id: int = Depends(get_user_id), db: Session = Depends(get_db)
):
    """
    删除单条消息

    Args:
        conversation_id: 对话ID
        message_id: 消息ID
        user_id: 用户ID
        db: 数据库会话

    Returns:
        操作结果
    """
    try:
        from app.models.conversation import Conversation
        from app.models.message import Message

        conv = (
            db.query(Conversation)
            .filter(Conversation.id == int(conversation_id), Conversation.user_id == user_id)
            .first()
        )

        if not conv:
            raise HTTPException(status_code=404, detail="对话不存在")

        msg = db.query(Message).filter(Message.id == int(message_id), Message.conversation_id == conv.id).first()

        if not msg:
            raise HTTPException(status_code=404, detail="消息不存在")

        db.delete(msg)
        if conv.message_count and conv.message_count > 0:
            conv.message_count -= 1
        db.commit()

        return {"success": True, "message": "消息已删除"}

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Delete message error: {str(e)}")
        raise HTTPException(status_code=500, detail="删除消息失败")


@router.patch("/conversations/{conversation_id}", response_model=ConversationResponse)
async def update_conversation(
    conversation_id: str,
    request: ConversationUpdate,
    user_id: int = Depends(get_user_id),
    db: Session = Depends(get_db),
):
    """
    更新对话信息

    Args:
        conversation_id: 对话ID
        request: 更新请求
        user_id: 用户ID
        db: 数据库会话

    Returns:
        更新后的对话
    """
    try:
        service = ChatService(db)
        conversation = service.update_conversation(
            conversation_id=conversation_id, user_id=user_id, title=request.title, is_favorited=request.is_favorited
        )

        return ConversationResponse.model_validate(conversation)

    except BusinessException as e:
        logger.error(f"Business error: {e.message}")
        raise HTTPException(status_code=e.get_http_status(), detail=e.message)
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/feedback", response_model=FeedbackResponse)
async def add_feedback(request: FeedbackRequest, user_id: int = Depends(get_user_id), db: Session = Depends(get_db)):
    """
    添加消息反馈

    Args:
        request: 反馈请求
        user_id: 用户ID
        db: 数据库会话

    Returns:
        反馈信息
    """
    try:
        service = ChatService(db)

        # 从message_id查找conversation_id
        from app.models.message import Message

        message = db.query(Message).filter(Message.id == request.message_id).first()

        if not message:
            raise BusinessException(code=ErrorCode.RECORD_NOT_FOUND, message="Message not found")

        feedback = service.add_feedback(
            message_id=request.message_id,
            conversation_id=message.conversation_id,
            user_id=user_id,
            rating=request.rating,
            feedback=request.feedback,
        )

        return FeedbackResponse(**feedback)

    except BusinessException as e:
        logger.error(f"Business error: {e.message}")
        raise HTTPException(status_code=e.get_http_status(), detail=e.message)
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/health")
async def health_check(db: Session = Depends(get_db)):
    """
    健康检查

    Returns:
        健康状态
    """
    try:
        # 尝试连接数据库
        db.execute(text("SELECT 1"))

        # 检查DeepSeek API
        from app.services.ai import get_deepseek_client

        client = await get_deepseek_client()
        api_healthy = await client.health_check()

        return {
            "status": "healthy" if api_healthy else "degraded",
            "timestamp": datetime.utcnow().isoformat(),
            "services": {"database": "connected", "deepseek_api": "connected" if api_healthy else "degraded"},
        }

    except Exception as e:
        logger.error(f"Health check error: {str(e)}")
        return {"status": "unhealthy", "timestamp": datetime.utcnow().isoformat(), "error": str(e)}


# ==================== Stub 端点（前端已调用，后端尚未完整实现） ====================


@router.post("/conversations/{conversation_id}/messages/{message_id}/regenerate")
async def regenerate_message(
    conversation_id: int,
    message_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """重新生成消息（stub）"""
    raise HTTPException(status_code=501, detail="消息重新生成功能尚未实现")


@router.get("/conversations/{conversation_id}/export")
async def export_conversation_json(
    conversation_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """导出对话为JSON（stub）"""
    from app.models.conversation import Conversation

    conv = db.query(Conversation).filter(Conversation.id == conversation_id).first()
    if not conv:
        raise HTTPException(status_code=404, detail="对话不存在")
    data = conv.to_dict()
    data["messages"] = [m.to_dict() for m in conv.messages] if hasattr(conv, "messages") else []
    return data


@router.get("/conversations/{conversation_id}/export/markdown")
async def export_conversation_markdown(
    conversation_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """导出对话为Markdown（stub）"""
    from app.models.conversation import Conversation

    conv = db.query(Conversation).filter(Conversation.id == conversation_id).first()
    if not conv:
        raise HTTPException(status_code=404, detail="对话不存在")
    lines = [f"# {conv.title or '对话记录'}\n"]
    for msg in (conv.messages if hasattr(conv, "messages") else []):
        role = msg.role.value if hasattr(msg.role, "value") else str(msg.role)
        lines.append(f"**{role}**: {msg.content}\n")
    from fastapi.responses import PlainTextResponse

    return PlainTextResponse("\n".join(lines), media_type="text/markdown")


@router.post("/conversations/{conversation_id}/messages/{message_id}/favorite")
async def toggle_message_favorite(
    conversation_id: int,
    message_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """收藏/取消收藏消息（stub）"""
    raise HTTPException(status_code=501, detail="消息收藏功能尚未实现")
