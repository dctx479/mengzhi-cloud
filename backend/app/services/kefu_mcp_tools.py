"""
客服 MCP 工具集

使用 LangChain @tool 装饰器暴露客服工具，
供主平台 DeepSeek Agent 通过 MCP Client 调用。

版本: 1.0
更新日期: 2026-05-25
"""

from typing import Optional, List, Dict, Any
from loguru import logger

from sqlalchemy.orm import Session

try:
    from langchain_core.tools import tool, create_schema_from_function
    HAS_LANGCHAIN = True
except ImportError:
    HAS_LANGCHAIN = False
    logger.warning("langchain-core not installed, MCP tools unavailable")

from .kefu_classifier import KefuClassifier, IntentType, EmotionType
from .kefu_rag import KefuKnowledgeBase
from .kefu_ticket import KefuTicketService
from .kefu_tools import (
    query_order, query_product, query_user_quota,
    get_refund_policy, get_shipping_info, query_logistics
)


# 全局单例
_classifier: Optional[KefuClassifier] = None
_rag: Optional[KefuKnowledgeBase] = None


def get_classifier() -> KefuClassifier:
    global _classifier
    if _classifier is None:
        _classifier = KefuClassifier()
    return _classifier


def get_rag() -> KefuKnowledgeBase:
    global _rag
    if _rag is None:
        _rag = KefuKnowledgeBase()
    return _rag


def get_ticket_service(db: Session) -> KefuTicketService:
    return KefuTicketService(db)


# ============================================================
# LangChain Tools（供 MCP 调用）
# ============================================================

if HAS_LANGCHAIN:

    @tool
    def classify_intent_emotion(message: str) -> str:
        """
        分析用户消息的意图和情绪。

        Args:
            message: 用户发送的消息内容

        Returns:
            JSON格式的分类结果，包含 intent、emotion、emotion_intensity、should_escalate、reason
        """
        classifier = get_classifier()
        decision = classifier.classify(message)

        import json
        return json.dumps({
            "intent": decision.intent.primary_intent.value if decision.intent else "unknown",
            "emotion": decision.emotion.emotion_type.value if decision.emotion else "neutral",
            "emotion_intensity": decision.emotion.intensity if decision.emotion else 3,
            "should_escalate": decision.emotion.should_escalate if decision.emotion else False,
            "action": decision.action.value if decision.action else "unknown",
            "reason": decision.reason,
            "priority": decision.priority,
        }, ensure_ascii=False)

    @tool
    def query_knowledge_base(question: str, top_k: int = 3) -> str:
        """
        在内蒙古农畜产品知识库中检索相关答案。

        Args:
            question: 用户的问题
            top_k: 返回的参考条数（默认3条）

        Returns:
            检索到的知识库片段列表（JSON格式）
        """
        rag = get_rag()
        import asyncio
        results = asyncio.run(rag.query(question, top_k)) if hasattr(rag, 'query') else []

        if not results:
            return "未找到相关知识库内容"

        import json
        return json.dumps(results, ensure_ascii=False, indent=2)

    @tool
    def create_support_ticket(
        title: str,
        description: str,
        category: str = "inquiry",
        priority: str = "normal",
        user_id: int = 0,
        db_session: str = None,
    ) -> str:
        """
        为用户创建一个客服工单。

        Args:
            title: 工单标题
            description: 工单描述（用户问题详情）
            category: 工单类别 (inquiry/product/refund/return/exchange/complaint/quality/delivery/other)
            priority: 优先级 (low/normal/high/urgent)
            user_id: 用户ID
            db_session: 数据库会话（内部使用）

        Returns:
            JSON格式的工单创建结果
        """
        # category 映射
        from app.models import TicketCategory, TicketPriority
        cat_map = {
            "inquiry": TicketCategory.INQUIRY,
            "product": TicketCategory.PRODUCT,
            "refund": TicketCategory.REFUND,
            "return": TicketCategory.RETURN,
            "exchange": TicketCategory.EXCHANGE,
            "complaint": TicketCategory.COMPLAINT,
            "quality": TicketCategory.QUALITY,
            "delivery": TicketCategory.DELIVERY,
        }
        pri_map = {
            "low": TicketPriority.LOW,
            "normal": TicketPriority.NORMAL,
            "high": TicketPriority.HIGH,
            "urgent": TicketPriority.URGENT,
        }

        cat = cat_map.get(category, TicketCategory.INQUIRY)
        pri = pri_map.get(priority, TicketPriority.NORMAL)

        # 通过全局 db session（实际通过 request 注入）
        # 此处返回创建指引，由 API 层真正执行
        import json
        return json.dumps({
            "status": "pending_db_commit",
            "title": title,
            "category": cat.value,
            "priority": pri.value,
            "message": "工单创建参数已准备好，等待API层提交数据库"
        }, ensure_ascii=False)

    @tool
    def query_product_info(product_name: str, db_session: str = None) -> str:
        """
        查询平台产品信息。

        Args:
            product_name: 产品名称关键词（如"羊肉"、"奶酪"、"藜麦"）
            db_session: 数据库会话（内部使用）

        Returns:
            产品列表（JSON格式）
        """
        # 实际通过 db_session 执行
        import json
        return json.dumps({
            "product_name": product_name,
            "note": "请通过 API 层传入真实 db_session 执行查询",
            "fallback": f"查询产品: {product_name}"
        }, ensure_ascii=False)

    @tool
    def query_order_status(user_id: int, order_id: str = None, db_session: str = None) -> str:
        """
        查询用户订单状态。

        Args:
            user_id: 用户ID
            order_id: 订单号（可选，不填则返回所有订单）
            db_session: 数据库会话（内部使用）

        Returns:
            订单信息（JSON格式）
        """
        import json
        return json.dumps({
            "user_id": user_id,
            "order_id": order_id,
            "note": "请通过 API 层传入真实 db_session 执行查询"
        }, ensure_ascii=False)

    @tool
    def check_refund_policy() -> str:
        """
        查询退款退货政策。

        Returns:
            退款政策信息（JSON格式）
        """
        result = get_refund_policy()
        import json
        return json.dumps(result, ensure_ascii=False, indent=2)

    @tool
    def check_shipping_info(product_name: str = None) -> str:
        """
        查询配送政策。

        Args:
            product_name: 产品名称（可选）

        Returns:
            配送信息（JSON格式）
        """
        result = get_shipping_info(product_name)
        import json
        return json.dumps(result, ensure_ascii=False, indent=2)


# ============================================================
# MCP 工具注册表（供 Agent 发现工具）
# ============================================================

def get_mcp_tools() -> List:
    """获取所有 MCP 工具列表"""
    if not HAS_LANGCHAIN:
        return []

    return [
        classify_intent_emotion,
        query_knowledge_base,
        create_support_ticket,
        query_product_info,
        query_order_status,
        check_refund_policy,
        check_shipping_info,
    ]


def get_mcp_tools_schemas() -> List[Dict[str, Any]]:
    """获取所有 MCP 工具的 schema（用于 Agent 注册）"""
    tools = get_mcp_tools()
    schemas = []
    for t in tools:
        try:
            schemas.append({
                "name": t.name,
                "description": t.description,
                "parameters": t.args_schema.schema() if hasattr(t.args_schema, 'schema') else {},
            })
        except Exception as e:
            logger.warning(f"Failed to get schema for tool {t.name}: {e}")
    return schemas