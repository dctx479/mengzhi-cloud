"""
客服意图与情绪分类器

功能：
- 意图分类（15类）：产品咨询/价格/配送/退款/投诉等
- 情绪识别（6类）：positive/neutral/confused/frustrated/angry/anxious/sad
- 规则匹配优先，LLM fallback

版本: 1.0
更新日期: 2026-05-25
"""

from typing import Optional, Dict, Any
from enum import Enum
from pydantic import BaseModel
from loguru import logger

import httpx
from app.core.config import settings


class EmotionType(str, Enum):
    POSITIVE = "positive"
    NEUTRAL = "neutral"
    CONFUSED = "confused"
    FRUSTRATED = "frustrated"
    ANGRY = "angry"
    ANXIOUS = "anxious"
    SAD = "sad"


class IntentType(str, Enum):
    GREETING = "greeting"
    PRODUCT_INQUIRY = "product_inquiry"
    PRICE_INQUIRY = "price_inquiry"
    REFUND = "refund"
    RETURN = "return"
    EXCHANGE = "exchange"
    WARRANTY = "warranty"
    DELIVERY = "delivery"
    TRACKING = "tracking"
    COMPLAINT = "complaint"
    ESCALATION = "escalation"
    ORDER_INQUIRY = "order_inquiry"
    QUALITY_FEEDBACK = "quality_feedback"
    BRAND_STORY = "brand_story"
    UNKNOWN = "unknown"


class RouteAction(str, Enum):
    GREETING = "greeting"
    RAG_QUERY = "rag_query"
    CREATE_TICKET = "create_ticket"
    ESCALATE = "escalate"
    TOOL_CALL = "tool_call"
    LLM_FALLBACK = "llm_fallback"


class EmotionAnalysis(BaseModel):
    emotion_type: EmotionType = EmotionType.NEUTRAL
    intensity: int = 3
    should_escalate: bool = False
    reason: str = ""


class IntentClassification(BaseModel):
    primary_intent: IntentType = IntentType.UNKNOWN
    confidence: float = 0.5
    summary: str = ""


class RoutingDecision(BaseModel):
    action: RouteAction
    reason: str
    priority: str = "normal"
    emotion_prefix: str = ""
    emotion: Optional[EmotionAnalysis] = None
    intent: Optional[IntentClassification] = None


class KefuClassifier:
    """客服意图与情绪分类器"""

    def __init__(self):
        self._emotion_keywords = {
            EmotionType.ANGRY: ["垃圾", "破", "投诉", "骗子", "退款", "滚", "废物", "恶心", "太差", "怒", "气愤", "无良", "黑心"],
            EmotionType.FRUSTRATED: ["慢", "等了", "还没", "多次", "又坏了", "什么破", "烦", "累", "失望", "不靠谱"],
            EmotionType.ANXIOUS: ["急", "快点", "赶紧", "什么时候", "催", "赶时间", "着急", "火速"],
            EmotionType.SAD: ["失望", "难过", "伤心", "心寒", "无奈", "悲哀"],
            EmotionType.CONFUSED: ["怎么", "不知道", "看不懂", "不会", "怎么办", "迷茫", "啥意思"],
            EmotionType.POSITIVE: ["好的", "谢谢", "满意", "不错", "好用", "棒", "喜欢", "好", "赞", "优秀"],
        }

        self._intent_keywords = {
            IntentType.REFUND: ["退款", "退钱", "不想要了", "申请退款", "要退"],
            IntentType.RETURN: ["退货", "退回", "寄回去", "申请退货"],
            IntentType.EXCHANGE: ["换货", "换成", "更换", "申请换货"],
            IntentType.WARRANTY: ["保修", "质保", "维修", "坏了"],
            IntentType.DELIVERY: ["发货", "配送", "什么时候发", "还没到"],
            IntentType.TRACKING: ["物流", "到哪了", "快递", "单号", "查快递"],
            IntentType.PRODUCT_INQUIRY: ["产品", "功能", "怎么样", "好吗", "介绍", "有什么"],
            IntentType.PRICE_INQUIRY: ["价格", "多少钱", "优惠", "便宜", "折扣", "特价"],
            IntentType.COMPLAINT: ["投诉", "不满", "太差", "垃圾", "差评", "举报"],
            IntentType.PRODUCT_INQUIRY: ["产品", "功能", "怎么样", "好吗", "介绍", "有什么"],
            IntentType.PRICE_INQUIRY: ["价格", "多少钱", "优惠", "便宜", "折扣", "特价"],
            IntentType.COMPLAINT: ["投诉", "不满", "太差", "垃圾", "差评", "举报", "坏了", "故障", "问题", "异常", "不能用"],
            IntentType.ORDER_INQUIRY: ["订单", "查订单", "我的订单", "下单"],
            IntentType.GREETING: ["你好", "您好", "在吗", "hello", "hi", "打扰", "请问"],
            IntentType.ESCALATION: ["转人工", "客服", "经理", "投诉", "找真人"],
            IntentType.QUALITY_FEEDBACK: ["质量", "品质", "口感", "新鲜", "变质", "有问题"],
            IntentType.BRAND_STORY: ["品牌", "故事", "来历", "产地", "怎么来", "背景"],
        }

    def classify(self, message: str) -> RoutingDecision:
        """
        核心分类入口：先规则匹配，复杂场景才调用 LLM

        Args:
            message: 用户消息

        Returns:
            RoutingDecision: 路由决策
        """
        emotion = self._detect_emotion(message)
        intent = self._detect_intent(message)
        return self._make_routing_decision(message, emotion, intent)

    def _detect_emotion(self, message: str) -> EmotionAnalysis:
        """规则匹配检测情绪"""
        detected = EmotionType.NEUTRAL
        max_count = 0

        for emotion, keywords in self._emotion_keywords.items():
            count = sum(1 for kw in keywords if kw in message)
            if count > max_count:
                max_count = count
                detected = emotion

        intensity = min(10, max_count * 3 + 3) if max_count > 0 else 3
        should_escalate = detected in [EmotionType.ANGRY] and intensity >= 7

        return EmotionAnalysis(
            emotion_type=detected,
            intensity=intensity,
            should_escalate=should_escalate,
            reason="关键词匹配" if max_count > 0 else "默认中性"
        )

    def _detect_intent(self, message: str) -> IntentClassification:
        """规则匹配检测意图"""
        for intent, keywords in self._intent_keywords.items():
            if any(kw in message for kw in keywords):
                return IntentClassification(
                    primary_intent=intent,
                    confidence=0.8,
                    summary=f"关键词匹配: {intent.value}"
                )

        return IntentClassification(
            primary_intent=IntentType.UNKNOWN,
            confidence=0.3,
            summary="无法识别具体意图"
        )

    def _make_routing_decision(
        self,
        message: str,
        emotion: EmotionAnalysis,
        intent: IntentClassification
    ) -> RoutingDecision:
        """根据情绪和意图做路由决策"""

        # 问候
        if intent.primary_intent == IntentType.GREETING:
            return RoutingDecision(
                action=RouteAction.GREETING,
                reason="用户问候",
                priority="normal",
                emotion=emotion,
                intent=intent,
            )

        # 高情绪自动转人工
        if emotion.should_escalate:
            return RoutingDecision(
                action=RouteAction.ESCALATE,
                reason=f"检测到{_intensity_text(emotion.intensity)}情绪，建议转人工",
                priority="high",
                emotion_prefix=_get_emotion_prefix(emotion.emotion_type),
                emotion=emotion,
                intent=intent,
            )

        # 明确要求转人工
        if intent.primary_intent == IntentType.ESCALATION:
            return RoutingDecision(
                action=RouteAction.ESCALATE,
                reason="用户明确要求转人工",
                priority="high",
                emotion=emotion,
                intent=intent,
            )

        # 需要创建工单的场景
        is_action_request = any(kw in message for kw in [
            "我要", "帮我", "申请", "办理", "处理", "解决", "退钱", "退款", "退货", "换货", "投诉"
        ])

        if intent.primary_intent in [
            IntentType.REFUND, IntentType.RETURN,
            IntentType.EXCHANGE, IntentType.COMPLAINT
        ]:
            if is_action_request:
                return RoutingDecision(
                    action=RouteAction.CREATE_TICKET,
                    reason=f"意图为{intent.primary_intent.value}，用户需要办理业务，创建工单",
                    priority="normal",
                    emotion=emotion,
                    intent=intent,
                )
            else:
                return RoutingDecision(
                    action=RouteAction.RAG_QUERY,
                    reason=f"用户询问{intent.primary_intent.value}流程，先查询知识库",
                    priority="normal",
                    emotion=emotion,
                    intent=intent,
                )

        # 订单/物流/产品查询 → 工具调用
        if intent.primary_intent in [
            IntentType.ORDER_INQUIRY, IntentType.TRACKING,
            IntentType.DELIVERY, IntentType.PRICE_INQUIRY
        ]:
            return RoutingDecision(
                action=RouteAction.TOOL_CALL,
                reason=f"意图为{intent.primary_intent.value}，调用工具获取信息",
                priority="normal",
                emotion=emotion,
                intent=intent,
            )

        # 默认走 RAG 知识库
        return RoutingDecision(
            action=RouteAction.RAG_QUERY,
            reason=f"意图为{intent.primary_intent.value}，通过知识库回答",
            priority="normal",
            emotion=emotion,
            intent=intent,
        )

    async def _llm_fallback_classify(self, message: str) -> IntentClassification:
        """LLM fallback 用于复杂语义（可选）"""
        try:
            prompt = f"""你是一个客服场景的意图分类专家。

用户消息: {message}

可选意图: greeting, product_inquiry, price_inquiry, refund, return, exchange,
warranty, delivery, tracking, complaint, escalation, order_inquiry,
quality_feedback, brand_story, unknown

返回JSON格式: {{"intent": "xxx", "confidence": 0.0-1.0, "summary": "..."}}
只返回JSON。"""

            async with httpx.AsyncClient(timeout=30.0) as client:
                resp = await client.post(
                    f"{settings.DEEPSEEK_API_BASE}/chat/completions",
                    headers={
                        "Authorization": f"Bearer {settings.DEEPSEEK_API_KEY}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": "deepseek-chat",
                        "messages": [{"role": "user", "content": prompt}],
                        "temperature": 0.3,
                        "max_tokens": 200,
                    }
                )
                result = resp.json()
                content = result.get("choices", [{}])[0].get("message", {}).get("content", "")
                import json as _json
                parsed = _json.loads(content)
                return IntentClassification(
                    primary_intent=IntentType(parsed.get("intent", "unknown")),
                    confidence=float(parsed.get("confidence", 0.5)),
                    summary=parsed.get("summary", ""),
                )
        except Exception as e:
            logger.warning(f"LLM fallback classify failed: {e}")
            return IntentClassification(primary_intent=IntentType.UNKNOWN, confidence=0.3)


def _intensity_text(intensity: int) -> str:
    if intensity >= 8:
        return "强烈"
    elif intensity >= 5:
        return "中等"
    return "轻微"


def _get_emotion_prefix(emotion: EmotionType) -> str:
    prefixes = {
        EmotionType.ANGRY: "我理解您现在很生气，非常抱歉给您带来不好的体验。",
        EmotionType.FRUSTRATED: "我理解您很烦恼，我们会尽快帮您解决问题。",
        EmotionType.ANXIOUS: "我理解您很着急，请放心，我们会尽快处理。",
        EmotionType.SAD: "很抱歉给您带来困扰，我们会认真对待您的问题。",
        EmotionType.CONFUSED: "我理解您可能有不清楚的地方，让我为您详细说明。",
    }
    return prefixes.get(emotion, "")