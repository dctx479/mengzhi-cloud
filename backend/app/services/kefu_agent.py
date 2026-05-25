"""
客服 Agent 核心

编排意图分类 → RAG检索/工具调用/工单创建 → 回复生成

版本: 1.0
更新日期: 2026-05-25
"""

import uuid
import time
from typing import Dict, Any, Optional
from loguru import logger

from sqlalchemy.orm import Session

from .kefu_classifier import (
    KefuClassifier,
    RoutingDecision,
    RouteAction,
    EmotionAnalysis,
    IntentClassification,
    _get_emotion_prefix,
    IntentType,
)
from app.models import TicketCategory, TicketPriority
from .kefu_memory import KefuMemory
from .kefu_rag import KefuKnowledgeBase
from .kefu_ticket import KefuTicketService
from .kefu_tools import (
    query_order,
    query_product,
    query_user_quota,
    get_refund_policy,
    get_shipping_info,
    query_logistics,
)

GREETING_REPLIES = [
    "您好！我是内蒙古农畜产品平台的智能客服，有什么可以帮您的吗？",
    "您好呀！欢迎来到内蒙古农畜产品平台，请问有什么问题想问我的吗？",
    "您好！请问是咨询产品、查询订单，还是了解配送政策呢？",
]


class KefuAgent:
    """客服 Agent"""

    def __init__(self, db: Session):
        self.db = db
        self.classifier = KefuClassifier()
        self.memory = KefuMemory(db)
        self.rag = KefuKnowledgeBase()
        self.ticket_service = KefuTicketService(db)
        self.profile_service = None  # 延迟初始化
        self._profile_context = ""   # 用户画像上下文

    def _get_profile_service(self):
        """延迟获取 UserProfileService（避免循环导入）"""
        if self.profile_service is None:
            from app.services.user_profile_service import UserProfileService
            self.profile_service = UserProfileService(self.db)
        return self.profile_service

    def _load_profile(self, user_id: int) -> None:
        """加载用户画像上下文（用于个性化回复）"""
        try:
            svc = self._get_profile_service()
            self._profile_context = svc.build_prompt_context(user_id)
        except Exception as e:
            logger.debug(f"加载用户画像失败: {e}")
            self._profile_context = ""

    def process(
        self,
        session_id: str,
        user_id: int,
        user_message: str,
        user_name: str = None,
        role: str = "user",
    ) -> Dict[str, Any]:
        """
        处理用户消息

        Returns:
            {
                "reply": str,
                "session_id": str,
                "emotion": str,
                "intent": str,
                "action": str,
                "ticket_id": str,
                "confidence": float,
            }
        """
        start_time = time.time()

        # 加载用户画像（用于个性化回复）
        self._load_profile(user_id)

        # 确保会话存在
        self.memory.get_or_create_conversation(session_id, user_id, user_name)

        # 意图+情绪分类
        decision = self.classifier.classify(user_message)
        emotion = decision.emotion
        intent = decision.intent

        reply = ""
        ticket_id = None

        # 根据路由动作处理
        if decision.action == RouteAction.GREETING:
            reply = self._greeting()
        elif decision.action == RouteAction.RAG_QUERY:
            reply = self._handle_rag(user_message)
        elif decision.action == RouteAction.CREATE_TICKET:
            ticket_id, reply = self._handle_create_ticket(user_id, user_message, intent, emotion, user_name)
        elif decision.action == RouteAction.ESCALATE:
            ticket_id, reply = self._handle_escalate(session_id, user_id, user_message, intent, emotion, user_name)
        elif decision.action == RouteAction.TOOL_CALL:
            reply = self._handle_tool(intent, user_message, user_id)
        elif decision.action == RouteAction.LLM_FALLBACK:
            reply = self._handle_llm_fallback(user_message)
        else:
            reply = self._handle_rag(user_message)

        # 添加情绪安抚前缀
        if decision.emotion_prefix and not reply.startswith(decision.emotion_prefix):
            reply = decision.emotion_prefix + reply

        # 保存对话历史
        self.memory.save_message(
            session_id=session_id,
            user_id=user_id,
            role="user",
            content=user_message,
            emotion=emotion.emotion_type.value if emotion else None,
            intent=intent.primary_intent.value if intent else None,
            confidence=int(intent.confidence * 100) if intent else None,
            action=decision.action.value if decision.action else None,
            user_name=user_name,
        )
        self.memory.save_message(
            session_id=session_id,
            user_id=user_id,
            role="agent",
            content=reply,
            emotion=emotion.emotion_type.value if emotion else None,
            intent=intent.primary_intent.value if intent else None,
            action=decision.action.value if decision.action else None,
        )

        # 自动蒸馏：每 5 条用户消息触发一次 Session Summary
        self._maybe_distill(session_id, user_id)

        processing_time = (time.time() - start_time) * 1000

        return {
            "reply": reply,
            "session_id": session_id,
            "emotion": emotion.emotion_type.value if emotion else "neutral",
            "emotion_intensity": emotion.intensity if emotion else 3,
            "emotion_should_escalate": emotion.should_escalate if emotion else False,
            "intent": intent.primary_intent.value if intent else "unknown",
            "intent_confidence": intent.confidence if intent else 0.0,
            "action": decision.action.value if decision.action else "unknown",
            "priority": decision.priority,
            "ticket_id": ticket_id,
            "confidence": intent.confidence if intent else 0.0,
            "processing_time_ms": round(processing_time, 1),
        }

    def _greeting(self) -> str:
        import random

        return random.choice(GREETING_REPLIES)

    def _maybe_distill(self, session_id: str, user_id: int) -> None:
        """每 5 条用户消息自动触发 Session Summary 蒸馏"""
        try:
            from app.models.kefu_conversation import KefuConversation, KefuMessage

            conv = self.db.query(KefuConversation).filter(
                KefuConversation.session_id == session_id
            ).first()
            if not conv:
                return

            user_msg_count = self.db.query(KefuMessage).filter(
                KefuMessage.conversation_id == conv.id,
                KefuMessage.role == "user",
            ).count()

            if user_msg_count > 0 and user_msg_count % 5 == 0:
                messages = self.memory.get_conversation_history(session_id, limit=20)
                svc = self._get_profile_service()
                svc.distill_session(session_id, user_id, messages)
                logger.info(f"Auto-distilled session {session_id} at {user_msg_count} user messages")

        except Exception as e:
            logger.debug(f"Auto-distill failed: {e}")

    def _handle_rag(self, user_message: str) -> str:
        """RAG 知识库检索回答"""
        try:
            reply = self.rag.answer(user_message)
            if reply:
                return reply
        except Exception as e:
            logger.error(f"RAG 回答失败: {e}")

        return self._handle_llm_fallback(user_message)

    def _handle_create_ticket(
        self,
        user_id: int,
        user_message: str,
        intent: IntentClassification,
        emotion: EmotionAnalysis,
        user_name: str,
    ) -> tuple:
        """创建工单"""
        category = _intent_to_category(intent.primary_intent)
        priority = (
            TicketPriority.HIGH
            if emotion and emotion.emotion_type.value in ["angry", "frustrated"]
            else TicketPriority.NORMAL
        )

        ticket = self.ticket_service.create_ticket(
            user_id=user_id,
            title=f"{category.value}: {user_message[:80]}",
            description=user_message,
            category=category,
            priority=priority,
            emotion=emotion.emotion_type.value if emotion else None,
            emotion_intensity=emotion.intensity if emotion else None,
            intent=intent.primary_intent.value if intent else None,
            user_name=user_name,
        )

        reply = f"我已经为您创建了工单（#{ticket.ticket_uuid[:8]}），我们的工作人员会尽快处理您的问题。如有疑问可以随时查看工单进度。"

        if category == TicketCategory.REFUND:
            reply += " 退款申请已提交，预计3-5个工作日内处理。"
        elif category == TicketCategory.COMPLAINT:
            reply += " 您的反馈已记录，我们会安排专人跟进处理。"

        return ticket.ticket_uuid, reply

    def _handle_escalate(
        self,
        session_id: str,
        user_id: int,
        user_message: str,
        intent: IntentClassification,
        emotion: EmotionAnalysis,
        user_name: str,
    ) -> tuple:
        """转人工"""
        escalation_uuid = str(uuid.uuid4())

        # 同样创建一个工单用于追踪
        ticket = self.ticket_service.create_ticket(
            user_id=user_id,
            title=f"[转人工] {user_message[:80]}",
            description=f"用户要求转人工。\n原始消息: {user_message}",
            category=TicketCategory.COMPLAINT,
            priority=TicketPriority.HIGH,
            emotion=emotion.emotion_type.value if emotion else None,
            emotion_intensity=emotion.intensity if emotion else None,
            intent=intent.primary_intent.value if intent else None,
            user_name=user_name,
        )

        reply = (
            "您的问题需要人工客服来处理，我已经为您记录并转接。"
            "人工客服会尽快与您联系，请保持联系方式畅通。\n"
            f"工单号: #{ticket.ticket_uuid[:8]}\n"
            "如需紧急帮助，请拨打客服热线。"
        )

        return ticket.ticket_uuid, reply

    def _handle_tool(self, intent: IntentClassification, user_message: str, user_id: int) -> str:
        """工具调用"""
        primary = intent.primary_intent

        if primary == IntentType.ORDER_INQUIRY:
            result = query_order(user_id, self.db)
            if result.get("found"):
                lines = ["以下是您的订单信息："]
                for o in result["orders"][:5]:
                    lines.append(f"• 订单 {o['order_no']} | {o['status']} | ¥{o['amount']}")
                return "\n".join(lines)
            return "未找到您的订单信息，您可以在「我的订单」页面查看。"

        if primary == IntentType.TRACKING:
            result = query_logistics(None, self.db)
            return f"物流查询：{result.get('tracking_hint', '请前往订单页面查看物流详情')}"

        if primary == IntentType.PRICE_INQUIRY:
            # 提取产品名
            result = query_product(user_message, self.db)
            if result.get("found"):
                lines = ["以下是相关产品："]
                for p in result["products"][:5]:
                    lines.append(f"• {p['name']} | ¥{p['price']}")
                return "\n".join(lines)
            return "未找到相关产品信息，欢迎咨询客服了解。"

        if primary == IntentType.PRODUCT_INQUIRY:
            result = query_product(user_message, self.db)
            if result.get("found"):
                lines = ["以下是相关产品："]
                for p in result["products"][:5]:
                    lines.append(f"• {p['name']} | ¥{p['price']}\n  {p.get('description', '')[:100]}")
                return "\n".join(lines)
            return self._handle_rag(user_message)

        return self._handle_rag(user_message)

    def _handle_llm_fallback(self, user_message: str) -> str:
        """DeepSeek LLM 生成回答（同步调用，无运行时 event loop 依赖）"""
        import httpx

        system_prompt = """你是一个内蒙古农畜产品平台的智能客服助手，名字叫"小蒙".""" + self._profile_context + """

## 你的职责
- 回答关于内蒙古牛羊肉、奶制品、藜麦、杂粮等农畜产品的咨询
- 介绍品牌故事、配送政策、售后服务
- 帮助用户了解产品信息和下单流程
- 根据用户画像调整回复策略：高价值用户重点推荐，潜力用户引导体验

## 回答规范
- 语气亲切、专业，像经验丰富的客服
- 3句话以内，除非用户追问
- 如涉及具体产品/价格/订单，建议用户查看平台或联系人工客服
- 不要编造具体价格和产品信息

## 平台信息
- 配送：顺丰冷链，原产地直发
- 客服热线：400-xxx-xxxx"""

        try:
            from app.core.config import settings

            with httpx.Client(timeout=30.0) as client:
                resp = client.post(
                    f"{settings.DEEPSEEK_API_BASE}/chat/completions",
                    headers={
                        "Authorization": f"Bearer {settings.DEEPSEEK_API_KEY}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "model": "deepseek-chat",
                        "messages": [
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": user_message},
                        ],
                        "temperature": 0.7,
                        "max_tokens": 500,
                    },
                )
                result = resp.json()
                return result.get("choices", [{}])[0].get("message", {}).get("content", "")
        except Exception as e:
            logger.error(f"LLM fallback failed: {e}")
            return "抱歉，我暂时无法回答您的问题，请联系客服热线 400-xxx-xxxx。"


def _intent_to_category(intent) -> TicketCategory:
    """意图到工单类别的映射"""
    mapping = {
        IntentType.REFUND: TicketCategory.REFUND,
        IntentType.RETURN: TicketCategory.RETURN,
        IntentType.EXCHANGE: TicketCategory.EXCHANGE,
        IntentType.COMPLAINT: TicketCategory.COMPLAINT,
        IntentType.WARRANTY: TicketCategory.REPAIR,
        IntentType.DELIVERY: TicketCategory.DELIVERY,
        IntentType.PRODUCT_INQUIRY: TicketCategory.PRODUCT,
        IntentType.QUALITY_FEEDBACK: TicketCategory.QUALITY,
    }
    return mapping.get(intent, TicketCategory.OTHER)
