"""
客服 API 路由

端点：
- POST /chat              发送消息（支持流式 SSE）
- GET /sessions           会话列表
- POST /sessions          创建会话
- GET /sessions/{id}      会话详情
- DELETE /sessions/{id}  删除会话
- GET /tickets            工单列表
- POST /tickets           创建工单
- GET /tickets/{id}       工单详情
- PATCH /tickets/{id}     更新工单
- GET /stats              统计数据（Admin）
- POST /kb/rebuild        重建知识库（Admin）
- GET /mcp/tools          MCP 工具列表

版本: 1.0
更新日期: 2026-05-25
"""

import json
import uuid
from datetime import datetime
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse, JSONResponse
from sqlalchemy.orm import Session
from loguru import logger

from app.api.deps import get_db, get_current_user, require_admin
from app.core.responses import success_response, paginated_response
from app.services.kefu_agent import KefuAgent
from app.services.kefu_memory import KefuMemory
from app.services.kefu_ticket import KefuTicketService
from app.services.kefu_rag import KefuKnowledgeBase
from app.services.kefu_mcp_tools import get_mcp_tools, get_mcp_tools_schemas
from app.models import KefuConversation, KefuTicket, TicketStatus, TicketCategory, TicketPriority

router = APIRouter()


# ============================================================
# Request/Response Schemas
# ============================================================

class ChatRequest(BaseModel):
    session_id: Optional[str] = Field(None, description="会话ID，不传则创建新会话")
    message: str = Field(..., description="用户消息")
    user_name: Optional[str] = None


class ChatResponse(BaseModel):
    reply: str
    session_id: str
    emotion: str
    emotion_intensity: int
    emotion_should_escalate: bool
    intent: str
    intent_confidence: float
    action: str
    priority: str
    ticket_id: Optional[str] = None
    confidence: float
    processing_time_ms: float


class TicketCreate(BaseModel):
    title: str
    description: str
    category: str = "inquiry"
    priority: str = "normal"
    emotion: Optional[str] = None
    emotion_intensity: Optional[int] = None
    intent: Optional[str] = None


class TicketUpdate(BaseModel):
    status: Optional[str] = None
    priority: Optional[str] = None
    assigned_to: Optional[str] = None
    add_message: Optional[str] = None


class SessionCreate(BaseModel):
    title: Optional[str] = None
    user_name: Optional[str] = None


# ============================================================
# Chat Endpoints
# ============================================================

@router.post("/chat", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    处理客服消息（核心端点）
    """
    user_id_str = current_user["user_id"]
    # user_id 是 UUID 字符串，需要查数据库获取整数 id
    from app.models import User
    user_obj = db.query(User).filter(User.user_uuid == user_id_str).first()
    if not user_obj:
        raise HTTPException(status_code=404, detail="用户不存在")

    session_id = request.session_id
    if not session_id:
        session_id = str(uuid.uuid4())

    agent = KefuAgent(db)
    result = agent.process(
        session_id=session_id,
        user_id=user_obj.id,
        user_message=request.message,
        user_name=request.user_name or current_user.get("username", ""),
        role=current_user.get("role", "user"),
    )

    return ChatResponse(**result)


@router.post("/chat/stream")
async def chat_stream(
    request: ChatRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    处理客服消息（流式 SSE）
    """
    user_id_str = current_user["user_id"]
    from app.models import User
    user_obj = db.query(User).filter(User.user_uuid == user_id_str).first()
    if not user_obj:
        raise HTTPException(status_code=404, detail="用户不存在")

    session_id = request.session_id or str(uuid.uuid4())

    async def event_generator():
        agent = KefuAgent(db)
        result = agent.process(
            session_id=session_id,
            user_id=user_obj.id,
            user_message=request.message,
            user_name=request.user_name or current_user.get("username", ""),
            role=current_user.get("role", "user"),
        )

        # 先发送路由信息
        meta = {
            "type": "meta",
            "session_id": result["session_id"],
            "emotion": result["emotion"],
            "emotion_intensity": result["emotion_intensity"],
            "intent": result["intent"],
            "action": result["action"],
            "priority": result["priority"],
            "ticket_id": result.get("ticket_id"),
            "processing_time_ms": result["processing_time_ms"],
        }
        yield f"data: {json.dumps(meta, ensure_ascii=False)}\n\n"

        # 流式发送回复
        reply = result["reply"]
        for i in range(0, len(reply), 20):
            chunk = reply[i:i+20]
            yield f"data: {json.dumps({'type': 'chunk', 'content': chunk}, ensure_ascii=False)}\n\n"

        yield f"data: {json.dumps({'type': 'done'}, ensure_ascii=False)}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache"},
    )


# ============================================================
# Session Endpoints
# ============================================================

@router.get("/sessions", response_model=dict)
async def list_sessions(
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """列出用户的客服会话"""
    user_id_str = current_user["user_id"]
    from app.models import User
    user_obj = db.query(User).filter(User.user_uuid == user_id_str).first()
    if not user_obj:
        raise HTTPException(status_code=404, detail="用户不存在")

    memory = KefuMemory(db)
    sessions = memory.list_user_conversations(user_obj.id, limit=limit)
    return success_response(data={
        "sessions": [s.to_dict() for s in sessions],
        "total": len(sessions),
    }).dict()


@router.post("/sessions", response_model=dict)
async def create_session(
    request: SessionCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """创建新会话"""
    user_id_str = current_user["user_id"]
    from app.models import User
    user_obj = db.query(User).filter(User.user_uuid == user_id_str).first()
    if not user_obj:
        raise HTTPException(status_code=404, detail="用户不存在")

    session_id = str(uuid.uuid4())
    memory = KefuMemory(db)
    conv = memory.get_or_create_conversation(
        session_id=session_id,
        user_id=user_obj.id,
        user_name=request.user_name or current_user.get("username", ""),
    )

    return success_response(data={
        "session_id": session_id,
        "created_at": conv.created_at.isoformat() if conv.created_at else None,
    }).dict()


@router.get("/sessions/{session_id}", response_model=dict)
async def get_session(
    session_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """获取会话详情（包含消息历史）"""
    user_id_str = current_user["user_id"]
    from app.models import User
    user_obj = db.query(User).filter(User.user_uuid == user_id_str).first()
    if not user_obj:
        raise HTTPException(status_code=404, detail="用户不存在")

    memory = KefuMemory(db)
    messages = memory.get_conversation_history(session_id, limit=50)
    conv = memory.get_or_create_conversation(session_id, user_obj.id)

    return success_response(data={
        **conv.to_dict(),
        "messages": messages,
    }).dict()


@router.delete("/sessions/{session_id}", response_model=dict)
async def delete_session(
    session_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """删除会话（删除前自动蒸馏 Session Summary）"""
    user_id_str = current_user["user_id"]
    from app.models import User
    user_obj = db.query(User).filter(User.user_uuid == user_id_str).first()
    if user_obj:
        from app.services.user_profile_service import UserProfileService
        memory = KefuMemory(db)
        messages = memory.get_conversation_history(session_id, limit=50)
        if messages:
            svc = UserProfileService(db, user_id=user_obj.id)
            svc.distill_session(session_id, user_obj.id, messages)

    memory = KefuMemory(db)
    memory.delete_conversation(session_id)
    return success_response(data={"deleted": True}).dict()


@router.post("/sessions/{session_id}/distill", response_model=dict)
async def distill_session(
    session_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """手动触发 Session Summary 蒸馏"""
    user_id_str = current_user["user_id"]
    from app.models import User
    from app.services.user_profile_service import UserProfileService

    user_obj = db.query(User).filter(User.user_uuid == user_id_str).first()
    if not user_obj:
        raise HTTPException(status_code=404, detail="用户不存在")

    memory = KefuMemory(db)
    messages = memory.get_conversation_history(session_id, limit=50)
    if not messages:
        raise HTTPException(status_code=404, detail="会话无消息")

    svc = UserProfileService(db, user_id=user_obj.id)
    summary = svc.distill_session(session_id, user_obj.id, messages)

    return success_response(data=summary).dict()


# ============================================================
# Ticket Endpoints
# ============================================================

@router.get("/tickets", response_model=dict)
async def list_tickets(
    status: Optional[str] = Query(None, description="工单状态筛选"),
    category: Optional[str] = Query(None, description="工单类别筛选"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """列出工单（用户看自己的，Admin看全部）"""
    user_id_str = current_user["user_id"]
    from app.models import User
    user_obj = db.query(User).filter(User.user_uuid == user_id_str).first()
    if not user_obj:
        raise HTTPException(status_code=404, detail="用户不存在")

    role = current_user.get("role", "user")

    status_enum = TicketStatus(status) if status else None
    category_enum = TicketCategory(category) if category else None

    service = KefuTicketService(db)
    result = service.list_tickets(
        user_id=user_obj.id,
        role=role,
        status=status_enum,
        category=category_enum,
        page=page,
        page_size=page_size,
    )

    return success_response(data=result).dict()


@router.post("/tickets", response_model=dict)
async def create_ticket(
    request: TicketCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """创建工单"""
    user_id_str = current_user["user_id"]
    from app.models import User
    user_obj = db.query(User).filter(User.user_uuid == user_id_str).first()
    if not user_obj:
        raise HTTPException(status_code=404, detail="用户不存在")

    # 映射 category/priority
    cat_map = {
        "inquiry": TicketCategory.INQUIRY,
        "product": TicketCategory.PRODUCT,
        "refund": TicketCategory.REFUND,
        "return": TicketCategory.RETURN,
        "exchange": TicketCategory.EXCHANGE,
        "complaint": TicketCategory.COMPLAINT,
        "quality": TicketCategory.QUALITY,
        "delivery": TicketCategory.DELIVERY,
        "other": TicketCategory.OTHER,
    }
    pri_map = {
        "low": TicketPriority.LOW,
        "normal": TicketPriority.NORMAL,
        "high": TicketPriority.HIGH,
        "urgent": TicketPriority.URGENT,
    }

    service = KefuTicketService(db)
    ticket = service.create_ticket(
        user_id=user_obj.id,
        title=request.title[:200],
        description=request.description,
        category=cat_map.get(request.category, TicketCategory.INQUIRY),
        priority=pri_map.get(request.priority, TicketPriority.NORMAL),
        emotion=request.emotion,
        emotion_intensity=request.emotion_intensity,
        intent=request.intent,
        user_name=current_user.get("username", ""),
    )

    return success_response(data=ticket.to_dict()).dict()


@router.get("/tickets/{ticket_id}", response_model=dict)
async def get_ticket(
    ticket_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """获取工单详情（含消息历史）"""
    user_id_str = current_user["user_id"]
    from app.models import User
    user_obj = db.query(User).filter(User.user_uuid == user_id_str).first()
    if not user_obj:
        raise HTTPException(status_code=404, detail="用户不存在")

    role = current_user.get("role", "user")
    service = KefuTicketService(db)

    ticket = service.get_ticket(ticket_id, user_obj.id, role)
    if not ticket:
        raise HTTPException(status_code=404, detail="工单不存在或无权访问")

    messages = service.get_ticket_messages(ticket_id, user_obj.id, role)

    return success_response(data={
        **ticket.to_dict(),
        "messages": messages,
    }).dict()


@router.patch("/tickets/{ticket_id}", response_model=dict)
async def update_ticket(
    ticket_id: int,
    request: TicketUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """更新工单（状态、优先级、指派、添加消息）"""
    user_id_str = current_user["user_id"]
    from app.models import User
    user_obj = db.query(User).filter(User.user_uuid == user_id_str).first()
    if not user_obj:
        raise HTTPException(status_code=404, detail="用户不存在")

    role = current_user.get("role", "user")

    status_enum = TicketStatus(request.status) if request.status else None
    priority_enum = TicketPriority(request.priority) if request.priority else None

    service = KefuTicketService(db)
    ticket = service.update_ticket(
        ticket_id=ticket_id,
        user_id=user_obj.id,
        role=role,
        status=status_enum,
        priority=priority_enum,
        assigned_to=request.assigned_to,
        add_message=request.add_message,
    )

    if not ticket:
        raise HTTPException(status_code=404, detail="工单不存在或无权访问")

    return success_response(data=ticket.to_dict()).dict()


# ============================================================
# Stats & Admin
# ============================================================

@router.get("/stats", response_model=dict)
async def get_stats(
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_admin),
):
    """获取客服统计（Admin 可见）"""
    user_id_str = current_user["user_id"]
    from app.models import User
    user_obj = db.query(User).filter(User.user_uuid == user_id_str).first()
    if not user_obj:
        raise HTTPException(status_code=404, detail="用户不存在")

    service = KefuTicketService(db)
    stats = service.get_stats(user_id=None, role="admin")

    return success_response(data=stats).dict()


@router.post("/kb/rebuild", response_model=dict)
async def rebuild_knowledge_base(
    current_user: dict = Depends(require_admin),
):
    """重建客服知识库索引（Admin）"""
    rag = KefuKnowledgeBase()
    success = await rag.build_index()

    if success:
        return success_response(data={"message": "知识库重建成功"}).dict()
    else:
        return JSONResponse(
            status_code=500,
            content={"code": 500, "message": "知识库重建失败，可能是 FAISS 未安装", "data": None},
        )


@router.get("/mcp/tools", response_model=dict)
async def list_mcp_tools(
    current_user: dict = Depends(get_current_user),
):
    """获取 MCP 工具列表（供主平台 Agent 发现工具）"""
    schemas = get_mcp_tools_schemas()
    return success_response(data={
        "tools": schemas,
        "total": len(schemas),
    }).dict()


# ============================================================
# User Profile Endpoints（用户画像 + 客服联动）
# ============================================================

@router.get("/profile", response_model=dict)
async def get_user_profile(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    获取当前用户的画像摘要
    供客服 Agent 在对话中个性化回复
    """
    from app.models import User
    from app.services.user_profile_service import UserProfileService

    user_id_str = current_user["user_id"]
    user_obj = db.query(User).filter(User.user_uuid == user_id_str).first()
    if not user_obj:
        raise HTTPException(status_code=404, detail="用户不存在")

    service = UserProfileService(db, user_id=user_obj.id)
    summary = service.get_profile_summary()

    return success_response(data=summary).dict()


class CorrectionRequest(BaseModel):
    session_id: str
    correction_type: str = Field(..., description="emotion | intent | answer | profile")
    original: str
    corrected: str


@router.post("/profile/correction", response_model=dict)
async def record_correction(
    request: CorrectionRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """记录用户纠正（当客服回复被否定时）"""
    from app.models import User
    from app.services.user_profile_service import UserProfileService

    user_id_str = current_user["user_id"]
    user_obj = db.query(User).filter(User.user_uuid == user_id_str).first()
    if not user_obj:
        raise HTTPException(status_code=404, detail="用户不存在")

    if request.correction_type not in ("emotion", "intent", "answer", "profile"):
        raise HTTPException(status_code=400, detail="correction_type must be emotion|intent|answer|profile")

    svc = UserProfileService(db, user_id=user_obj.id)
    svc.record_correction(
        session_id=request.session_id,
        user_id=user_obj.id,
        correction_type=request.correction_type,
        original=request.original,
        corrected=request.corrected,
    )

    return success_response(data={"recorded": True}).dict()