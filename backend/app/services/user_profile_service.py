"""
用户画像服务 — 5 层 Persona 蒸馏模型

灵感来源:
- yourself-skill: 5 层 Persona 分层结构 + 标签→行为翻译表
- ex-skill: Session Summary 对话蒸馏 + 增量 Merge + Correction 纠正
- 构建用户画像 VOC: 三阶段蒸馏管道（归纳→分类→综合）

架构:
  Layer 0: 身份锚定 — 基本信息、注册天数、用户类型
  Layer 1: 购买风格 — 订单模式、偏好品类、消费水平
  Layer 2: 沟通偏好 — 消息特征、活跃时段、话题分布
  Layer 3: 情绪模式 — 情绪分布、升级倾向、满意度趋势
  Layer 4: 服务历史 — 工单模式、解决率、常见问题
"""

from __future__ import annotations

import json
from collections import Counter
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any

from loguru import logger
from sqlalchemy import func, desc, extract
from sqlalchemy.orm import Session


# ============================================================
# 标签 → 客服策略翻译表（借鉴 yourself-skill persona_analyzer.md）
# ============================================================
LEVEL_STRATEGY_MAP = {
    "高价值用户": {
        "tone": "尊敬、专属",
        "rules": [
            "使用尊称（如'尊敬的会员'），语气更正式",
            "主动推荐高端/限量产品，提供会员专属优惠",
            "问题优先级最高，承诺更短的处理时间",
            "主动询问是否需要其他帮助，体现关怀",
        ],
    },
    "活跃用户": {
        "tone": "亲切、专业",
        "rules": [
            "语气亲切自然，像老朋友一样",
            "基于购买历史推荐同品类/关联产品",
            "引导参与复购优惠、会员活动",
            "适当提及历史购买记录表示记住对方",
        ],
    },
    "潜力用户": {
        "tone": "热情、引导",
        "rules": [
            "热情介绍平台特色和优势",
            "推荐入门款/性价比高的产品",
            "主动提供首单优惠、新人礼包",
            "用场景化描述吸引兴趣（如'适合送礼/聚餐'）",
        ],
    },
    "普通用户": {
        "tone": "友好、耐心",
        "rules": [
            "耐心解答基础问题，不假设用户了解平台",
            "引导了解核心功能（下单/配送/售后）",
            "推荐明星产品和好评产品",
            "简洁明了，避免信息过载",
        ],
    },
}

EMOTION_STRATEGY_MAP = {
    "angry": "先道歉、共情安抚，不争辩，优先解决问题，必要时升级",
    "frustrated": "表达理解，明确告知解决步骤和时间预期",
    "anxious": "给出确定性信息，提供进度查询方式，减少不确定感",
    "sad": "表达关心，温和引导，不催促",
    "confused": "条理清晰地解释，分步骤引导，确认理解",
    "positive": "回应热情，趁机推荐相关产品或服务",
    "neutral": "正常专业回复",
}


class UserProfileService:
    """5 层 Persona 用户画像服务"""

    def __init__(self, db: Session, user_id: int = None):
        self._db = db
        self._user_id = user_id

    def get_profile_summary(self, user_id: int = None) -> Dict[str, Any]:
        uid = user_id or self._user_id
        if uid is None:
            return {"error": "user_id is required"}
        self._user_id = uid

        layers = {
            "layer_0_identity": self._layer_0_identity(),
            "layer_1_purchase": self._layer_1_purchase(),
            "layer_2_communication": self._layer_2_communication(),
            "layer_3_emotion": self._layer_3_emotion(),
            "layer_4_service": self._layer_4_service(),
        }

        score_data = self._calculate_engagement_score(layers)
        strategy = self._translate_to_strategy(score_data, layers)
        insights = self._generate_insights(layers, score_data)

        return {
            "user_id": uid,
            "persona_version": "2.0",
            "generated_at": datetime.now().isoformat(),
            **layers,
            "engagement_score": score_data,
            "strategy": strategy,
            "insights": insights,
        }

    # ============================================================
    # Layer 0: 身份锚定
    # ============================================================
    def _layer_0_identity(self) -> Dict[str, Any]:
        from app.models.user import User

        user = self._db.query(User).filter(User.id == self._user_id).first()
        if not user:
            return {"username": "未知用户", "member_days": 0, "user_type": "unknown"}

        created = user.created_at or datetime.now()
        days = (datetime.now() - created).days

        return {
            "username": user.username or "未知",
            "email": user.email or "",
            "member_days": days,
            "member_since": created.strftime("%Y-%m-%d"),
            "user_type": _enum_value(user.user_type),
            "role": _enum_value(user.role),
            "status": _enum_value(user.status),
        }

    # ============================================================
    # Layer 1: 购买风格
    # ============================================================
    def _layer_1_purchase(self) -> Dict[str, Any]:
        from app.models.order import Order

        orders = (
            self._db.query(Order)
            .filter(Order.user_id == self._user_id)
            .order_by(desc(Order.created_at))
            .all()
        )

        if not orders:
            return {
                "total_orders": 0,
                "total_spent": 0,
                "avg_order_value": 0,
                "consumption_level": "无",
                "purchase_frequency": "无购买记录",
                "categories": [],
                "last_purchase_days_ago": None,
                "recency": "从未购买",
            }

        total = sum(float(o.total_amount or 0) for o in orders)
        count = len(orders)
        avg = round(total / count, 2) if count > 0 else 0

        categories = Counter()
        for o in orders:
            cat = getattr(o, "category", None) or ""
            if cat:
                categories[cat] += 1

        last_order = orders[0]
        last_days = (datetime.now() - (last_order.created_at or datetime.now())).days

        if last_days <= 7:
            recency = "近期活跃"
        elif last_days <= 30:
            recency = "本月购买"
        elif last_days <= 90:
            recency = "近三月购买"
        else:
            recency = "沉睡用户"

        if avg >= 500:
            consumption = "高消费"
        elif avg >= 100:
            consumption = "中等消费"
        else:
            consumption = "低消费"

        freq_desc = "无"
        if count >= 10:
            freq_desc = "高频购买（10+单）"
        elif count >= 5:
            freq_desc = "中频购买（5-9单）"
        elif count >= 2:
            freq_desc = "低频购买（2-4单）"
        else:
            freq_desc = "首单用户"

        return {
            "total_orders": count,
            "total_spent": round(total, 2),
            "avg_order_value": avg,
            "consumption_level": consumption,
            "purchase_frequency": freq_desc,
            "categories": [{"name": k, "count": v} for k, v in categories.most_common(5)],
            "last_purchase_days_ago": last_days,
            "recency": recency,
        }

    # ============================================================
    # Layer 2: 沟通偏好
    # ============================================================
    def _layer_2_communication(self) -> Dict[str, Any]:
        from app.models.kefu_conversation import KefuMessage

        messages = (
            self._db.query(KefuMessage)
            .join(KefuMessage.conversation)
            .filter(
                KefuMessage.role == "user",
                KefuMessage.conversation.has(user_id=self._user_id),
            )
            .order_by(desc(KefuMessage.created_at))
            .limit(50)
            .all()
        )

        if not messages:
            return {
                "message_count": 0,
                "avg_message_length": 0,
                "style": "未知",
                "active_hours": [],
                "topic_distribution": [],
            }

        lengths = [len(m.content or "") for m in messages]
        avg_len = sum(lengths) / len(lengths) if lengths else 0

        if avg_len > 100:
            style = "详细描述型"
        elif avg_len > 30:
            style = "简洁表达型"
        else:
            style = "极简型"

        hour_counts = Counter()
        for m in messages:
            if m.created_at:
                hour_counts[m.created_at.hour] += 1

        top_hours = [h for h, _ in hour_counts.most_common(3)]

        intent_counts = Counter()
        for m in messages:
            if m.intent:
                intent_counts[m.intent] += 1

        topic_dist = [
            {"topic": _intent_label(k), "count": v, "intent": k}
            for k, v in intent_counts.most_common(5)
        ]

        return {
            "message_count": len(messages),
            "avg_message_length": round(avg_len, 1),
            "style": style,
            "active_hours": top_hours,
            "topic_distribution": topic_dist,
        }

    # ============================================================
    # Layer 3: 情绪模式
    # ============================================================
    def _layer_3_emotion(self) -> Dict[str, Any]:
        from app.models.kefu_conversation import KefuMessage

        messages = (
            self._db.query(KefuMessage)
            .join(KefuMessage.conversation)
            .filter(
                KefuMessage.role == "user",
                KefuMessage.conversation.has(user_id=self._user_id),
            )
            .order_by(desc(KefuMessage.created_at))
            .limit(50)
            .all()
        )

        emotion_counts = Counter()
        intensity_sum: Dict[str, int] = {}
        intensity_n: Dict[str, int] = {}
        recent_emotions = []

        for m in messages:
            em = m.emotion or "neutral"
            emotion_counts[em] += 1
            if m.emotion_intensity:
                intensity_sum[em] = intensity_sum.get(em, 0) + m.emotion_intensity
                intensity_n[em] = intensity_n.get(em, 0) + 1
            if len(recent_emotions) < 5:
                recent_emotions.append(em)

        total = sum(emotion_counts.values()) or 1
        distribution = {
            k: {"count": v, "ratio": round(v / total, 2)}
            for k, v in emotion_counts.most_common()
        }

        dominant = emotion_counts.most_common(1)[0][0] if emotion_counts else "neutral"
        negative_ratio = sum(
            emotion_counts.get(e, 0) for e in ["angry", "frustrated", "sad", "anxious"]
        ) / total

        if negative_ratio > 0.5:
            escalation_tendency = "高"
        elif negative_ratio > 0.2:
            escalation_tendency = "中"
        else:
            escalation_tendency = "低"

        return {
            "dominant_emotion": dominant,
            "distribution": distribution,
            "escalation_tendency": escalation_tendency,
            "negative_ratio": round(negative_ratio, 2),
            "recent_emotions": recent_emotions,
            "emotion_strategy": EMOTION_STRATEGY_MAP.get(dominant, EMOTION_STRATEGY_MAP["neutral"]),
        }

    # ============================================================
    # Layer 4: 服务历史
    # ============================================================
    def _layer_4_service(self) -> Dict[str, Any]:
        from app.models.kefu_ticket import KefuTicket
        from app.models.kefu_escalation import KefuEscalation

        tickets = (
            self._db.query(KefuTicket)
            .filter(KefuTicket.user_id == self._user_id)
            .all()
        )

        open_count = sum(1 for t in tickets if _enum_value(t.status) in ("pending", "processing"))
        resolved_count = sum(1 for t in tickets if _enum_value(t.status) in ("resolved", "closed"))
        total_tickets = len(tickets)

        escalated = self._db.query(func.count(KefuEscalation.id)).filter(
            KefuEscalation.user_id == self._user_id,
        ).scalar() or 0

        category_counts = Counter()
        for t in tickets:
            cat = _enum_value(t.category)
            if cat:
                category_counts[cat] += 1

        resolution_rate = round(resolved_count / total_tickets, 2) if total_tickets > 0 else 1.0

        if escalated > 3:
            satisfaction = "不满意（多次升级）"
        elif escalated > 0:
            satisfaction = "需要关注"
        elif resolution_rate >= 0.8:
            satisfaction = "满意"
        else:
            satisfaction = "一般"

        return {
            "total_tickets": total_tickets,
            "open_tickets": open_count,
            "resolved_tickets": resolved_count,
            "resolution_rate": resolution_rate,
            "escalated_count": escalated,
            "satisfaction": satisfaction,
            "common_issues": [
                {"category": k, "count": v}
                for k, v in category_counts.most_common(3)
            ],
        }

    # ============================================================
    # 综合评分
    # ============================================================
    def _calculate_engagement_score(self, layers: Dict) -> Dict[str, Any]:
        score = 20  # 基础分

        purchase = layers.get("layer_1_purchase", {})
        order_count = purchase.get("total_orders", 0)
        score += min(order_count * 8, 25)

        recency = purchase.get("recency", "从未购买")
        recency_bonus = {"近期活跃": 15, "本月购买": 10, "近三月购买": 5}.get(recency, 0)
        score += recency_bonus

        comm = layers.get("layer_2_communication", {})
        msg_count = comm.get("message_count", 0)
        score += min(msg_count * 2, 15)

        service = layers.get("layer_4_service", {})
        resolution_rate = service.get("resolution_rate", 1.0)
        score += int(resolution_rate * 10)

        emotion = layers.get("layer_3_emotion", {})
        neg_ratio = emotion.get("negative_ratio", 0)
        score -= int(neg_ratio * 15)

        score = max(0, min(100, score))

        if score >= 80:
            level = "高价值用户"
        elif score >= 60:
            level = "活跃用户"
        elif score >= 40:
            level = "潜力用户"
        else:
            level = "普通用户"

        return {
            "score": score,
            "level": level,
            "breakdown": {
                "base": 20,
                "purchase": min(order_count * 8, 25),
                "recency": recency_bonus,
                "engagement": min(msg_count * 2, 15),
                "resolution": int(resolution_rate * 10),
                "emotion_penalty": -int(neg_ratio * 15),
            },
        }

    # ============================================================
    # 标签 → 策略翻译（借鉴 yourself-skill 标签翻译表）
    # ============================================================
    def _translate_to_strategy(self, score_data: Dict, layers: Dict) -> Dict[str, Any]:
        level = score_data.get("level", "普通用户")
        level_strategy = LEVEL_STRATEGY_MAP.get(level, LEVEL_STRATEGY_MAP["普通用户"])

        emotion = layers.get("layer_3_emotion", {})
        dominant = emotion.get("dominant_emotion", "neutral")
        emotion_rule = EMOTION_STRATEGY_MAP.get(dominant, EMOTION_STRATEGY_MAP["neutral"])

        purchase = layers.get("layer_1_purchase", {})
        recency = purchase.get("recency", "从未购买")

        recency_rules = []
        if recency == "沉睡用户":
            recency_rules.append("已久未购买，用关怀话术唤醒（'好久没见您了'）")
            recency_rules.append("推荐当季新品或限时优惠")
        elif recency == "近期活跃":
            recency_rules.append("刚购买过，可能在等物流，主动提供物流信息")

        return {
            "level_tone": level_strategy["tone"],
            "level_rules": level_strategy["rules"],
            "emotion_rule": emotion_rule,
            "recency_rules": recency_rules,
        }

    # ============================================================
    # 洞察生成
    # ============================================================
    def _generate_insights(self, layers: Dict, score_data: Dict) -> List[str]:
        insights = []

        purchase = layers.get("layer_1_purchase", {})
        order_count = purchase.get("total_orders", 0)
        if order_count == 0:
            insights.append("新用户，暂无购买记录，重点引导首单体验")
        elif order_count >= 5:
            cats = [c["name"] for c in purchase.get("categories", [])[:2]]
            if cats:
                insights.append(f"忠实用户，偏好{'/'.join(cats)}品类，推荐关联产品")
            else:
                insights.append("忠实用户，可基于购买历史推荐")

        emotion = layers.get("layer_3_emotion", {})
        if emotion.get("escalation_tendency") == "高":
            insights.append("情绪敏感用户，对话中优先安抚，避免模板化回复")
        elif emotion.get("dominant_emotion") == "positive":
            insights.append("正向情绪用户，适合推荐新品和活动")

        service = layers.get("layer_4_service", {})
        if service.get("escalated_count", 0) > 2:
            insights.append("多次转人工，需关注服务质量，考虑专人跟进")
        if service.get("open_tickets", 0) > 0:
            insights.append(f"有{service['open_tickets']}个未解决工单，优先处理")

        recency = purchase.get("recency", "")
        if recency == "沉睡用户":
            insights.append("超过90天未购买，建议唤醒营销")

        return insights

    # ============================================================
    # Session Summary 蒸馏（借鉴 ex-skill session_summary.md）
    # ============================================================
    def distill_session(
        self,
        session_id: str,
        user_id: int,
        messages: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """
        对话结束后蒸馏 Session Summary

        借鉴 ex-skill 的 session_summary.md：
        - 聊了什么（2-3句话概括）
        - 情绪基调
        - 关键发现（新的用户偏好/痛点/需求）
        - 下次可以接着聊的话题

        Returns:
            蒸馏后的 session summary dict
        """
        if not messages:
            return {}

        user_msgs = [m for m in messages if m.get("role") == "user"]
        agent_msgs = [m for m in messages if m.get("role") == "agent"]

        intents = Counter()
        emotions = Counter()
        topics = []

        for m in user_msgs:
            if m.get("intent"):
                intents[m["intent"]] += 1
            if m.get("emotion"):
                emotions[m["emotion"]] += 1
            topics.append(m.get("content", "")[:50])

        dominant_intent = intents.most_common(1)[0][0] if intents else "unknown"
        dominant_emotion = emotions.most_common(1)[0][0] if emotions else "neutral"

        neg_emotions = {"angry", "frustrated", "sad", "anxious"}
        pos_emotions = {"positive"}
        if dominant_emotion in neg_emotions:
            mood = "负面"
        elif dominant_emotion in pos_emotions:
            mood = "正面"
        else:
            mood = "平和"

        discoveries = []
        for m in user_msgs:
            content = m.get("content", "")
            if any(kw in content for kw in ["不满", "差评", "退", "投诉", "问题"]):
                discoveries.append({"type": "pain_point", "text": content[:80]})
            elif any(kw in content for kw in ["喜欢", "好吃", "推荐", "还会买"]):
                discoveries.append({"type": "preference", "text": content[:80]})
            elif any(kw in content for kw in ["有没有", "能不能", "什么时候", "希望"]):
                discoveries.append({"type": "unmet_need", "text": content[:80]})

        has_ticket = any(m.get("action") == "create_ticket" for m in messages)
        has_escalation = any(m.get("action") == "escalate" for m in messages)

        summary = {
            "session_id": session_id,
            "user_id": user_id,
            "distilled_at": datetime.now().isoformat(),
            "turn_count": len(messages),
            "user_message_count": len(user_msgs),
            "topic_summary": _intent_label(dominant_intent),
            "mood": mood,
            "dominant_emotion": dominant_emotion,
            "dominant_intent": dominant_intent,
            "discoveries": discoveries[:5],
            "had_ticket": has_ticket,
            "had_escalation": has_escalation,
            "followup_topics": _suggest_followup(dominant_intent, has_ticket),
        }

        self._merge_session_to_profile(summary)

        return summary

    # ============================================================
    # 增量 Merge（借鉴 yourself-skill/ex-skill merger.md）
    # ============================================================
    def _merge_session_to_profile(self, summary: Dict[str, Any]) -> None:
        """
        将 session summary 增量 merge 到会话的 extra_data 中

        原则（来自 merger.md）:
        1. 增量不覆盖：追加到已有内容后面
        2. 冲突标注：矛盾信息标记 [conflict]
        3. 证据升级：充分证据强化已有结论的置信度
        """
        from app.models.kefu_conversation import KefuConversation

        try:
            conv = (
                self._db.query(KefuConversation)
                .filter(KefuConversation.session_id == summary["session_id"])
                .first()
            )
            if not conv:
                return

            existing = conv.extra_data or {}
            distill_history = existing.get("distill_history", [])

            distill_entry = {
                "distilled_at": summary["distilled_at"],
                "mood": summary["mood"],
                "topic": summary["topic_summary"],
                "discoveries": summary["discoveries"],
                "had_ticket": summary["had_ticket"],
            }
            distill_history.append(distill_entry)

            if len(distill_history) > 20:
                distill_history = distill_history[-20:]

            existing["distill_history"] = distill_history
            existing["last_distilled"] = summary["distilled_at"]
            existing["total_distilled"] = len(distill_history)

            conv.extra_data = existing
            self._db.commit()

        except Exception as e:
            logger.warning(f"Session merge failed: {e}")
            self._db.rollback()

    # ============================================================
    # Correction 纠正（借鉴 yourself-skill correction_handler.md）
    # ============================================================
    def record_correction(
        self,
        session_id: str,
        user_id: int,
        correction_type: str,
        original: str,
        corrected: str,
    ) -> None:
        """
        记录用户纠正（当客服回复被否定时）

        correction_type: "emotion" | "intent" | "answer" | "profile"
        """
        from app.models.kefu_conversation import KefuConversation

        try:
            conv = (
                self._db.query(KefuConversation)
                .filter(KefuConversation.session_id == session_id)
                .first()
            )
            if not conv:
                return

            existing = conv.extra_data or {}
            corrections = existing.get("corrections", [])

            corrections.append({
                "at": datetime.now().isoformat(),
                "type": correction_type,
                "original": original[:200],
                "corrected": corrected[:200],
            })

            if len(corrections) > 50:
                corrections = corrections[-50:]

            existing["corrections"] = corrections
            existing["corrections_count"] = len(corrections)
            conv.extra_data = existing
            self._db.commit()

        except Exception as e:
            logger.warning(f"Correction record failed: {e}")
            self._db.rollback()

    # ============================================================
    # 生成 Prompt 上下文（供 KefuAgent 注入 system prompt）
    # ============================================================
    def build_prompt_context(self, user_id: int = None) -> str:
        """
        生成适合注入 LLM system prompt 的用户画像上下文

        借鉴 ex-skill 的「记忆自然流露」原则:
        不说"根据画像分析..."，而是用自然的方式让 Agent 知道用户特征
        """
        try:
            summary = self.get_profile_summary(user_id)
        except Exception as e:
            logger.debug(f"Build prompt context failed: {e}")
            return ""

        identity = summary.get("layer_0_identity", {})
        purchase = summary.get("layer_1_purchase", {})
        emotion = summary.get("layer_3_emotion", {})
        score = summary.get("engagement_score", {})
        strategy = summary.get("strategy", {})
        insights = summary.get("insights", [])

        level = score.get("level", "普通用户")
        tone = strategy.get("level_tone", "友好")
        rules = strategy.get("level_rules", [])
        emotion_rule = strategy.get("emotion_rule", "")

        lines = [
            f"\n\n## 当前用户画像（{level}）",
            f"- 会员天数: {identity.get('member_days', 0)}天",
            f"- 购买记录: {purchase.get('total_orders', 0)}单, 共¥{purchase.get('total_spent', 0)}",
            f"- 购买活跃度: {purchase.get('recency', '未知')}",
            f"- 情绪倾向: {emotion.get('dominant_emotion', 'neutral')}, 升级风险: {emotion.get('escalation_tendency', '低')}",
            f"\n## 客服策略（语气: {tone}）",
        ]

        for r in rules[:3]:
            lines.append(f"- {r}")

        if emotion_rule:
            lines.append(f"- 情绪应对: {emotion_rule}")

        if insights:
            lines.append("\n## 洞察")
            for i in insights[:3]:
                lines.append(f"- {i}")

        return "\n".join(lines)


# ============================================================
# Helpers
# ============================================================

def _enum_value(v) -> str:
    return str(v.value if hasattr(v, "value") else v).lower() if v else ""


def _intent_label(intent: str) -> str:
    mapping = {
        "product_inquiry": "产品咨询",
        "price_inquiry": "价格咨询",
        "refund": "退款",
        "return": "退货",
        "exchange": "换货",
        "delivery": "配送",
        "tracking": "物流查询",
        "complaint": "投诉",
        "order_inquiry": "订单查询",
        "greeting": "问候",
        "brand_story": "品牌咨询",
        "quality_feedback": "品质反馈",
        "warranty": "保修",
        "escalation": "转人工",
        "unknown": "其他",
    }
    return mapping.get(intent, intent)


def _suggest_followup(intent: str, had_ticket: bool) -> List[str]:
    suggestions = []
    if had_ticket:
        suggestions.append("工单处理进度跟进")
    if intent in ("product_inquiry", "price_inquiry"):
        suggestions.append("产品体验反馈")
    if intent in ("refund", "return", "exchange"):
        suggestions.append("售后处理结果确认")
    if intent == "delivery":
        suggestions.append("签收后使用体验")
    if not suggestions:
        suggestions.append("产品推荐")
    return suggestions
