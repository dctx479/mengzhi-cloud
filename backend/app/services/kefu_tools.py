"""
客服工具集

提供 MCP 工具调用：查订单/物流/产品/配额/政策

版本: 1.0
更新日期: 2026-05-25
"""

from typing import Dict, Any, Optional, List
from loguru import logger

from sqlalchemy.orm import Session

from app.models import Order, Product, UserQuota
from app.models.order import OrderStatus


def query_order(user_id: int, db: Session, order_id: str = None) -> Dict[str, Any]:
    """
    查询用户订单

    Args:
        user_id: 用户ID
        db: 数据库会话
        order_id: 订单号（可选）

    Returns:
        订单信息 dict
    """
    try:
        query = db.query(Order).filter(Order.user_id == user_id)
        if order_id:
            query = query.filter(Order.order_no == order_id)

        orders = query.order_by(Order.created_at.desc()).limit(10).all()
        if not orders:
            return {"found": False, "message": "未找到订单"}

        return {
            "found": True,
            "orders": [
                {
                    "order_no": o.order_no,
                    "status": o.status.value if hasattr(o.status, 'value') else str(o.status),
                    "amount": float(o.total_amount) if o.total_amount else 0,
                    "created_at": o.created_at.isoformat() if o.created_at else None,
                }
                for o in orders
            ]
        }
    except Exception as e:
        logger.error(f"查询订单失败: {e}")
        return {"found": False, "error": str(e)}


def query_product(product_name: str, db: Session, limit: int = 5) -> Dict[str, Any]:
    """
    查询产品信息

    Args:
        product_name: 产品名称关键词
        db: 数据库会话
        limit: 返回数量

    Returns:
        产品列表
    """
    try:
        query = db.query(Product)
        if product_name:
            query = query.filter(Product.name.ilike(f"%{product_name}%"))

        products = query.limit(limit).all()
        if not products:
            return {"found": False, "message": f"未找到产品: {product_name}"}

        return {
            "found": True,
            "products": [
                {
                    "id": p.id,
                    "name": p.name,
                    "price": float(p.price) if p.price else 0,
                    "category": p.category or "",
                    "origin": p.origin_province or "",
                    "status": p.status.value if hasattr(p.status, 'value') else str(p.status),
                    "description": p.description[:200] if p.description else "",
                    "main_image": p.main_image_url or "",
                }
                for p in products
            ]
        }
    except Exception as e:
        logger.error(f"查询产品失败: {e}")
        return {"found": False, "error": str(e)}


def query_user_quota(user_id: int, db: Session) -> Dict[str, Any]:
    """
    查询用户配额

    Args:
        user_id: 用户ID
        db: 数据库会话

    Returns:
        配额信息
    """
    try:
        quotas = db.query(UserQuota).filter(UserQuota.user_id == user_id).all()
        if not quotas:
            return {"found": False, "message": "未找到配额信息"}

        result = {}
        for q in quotas:
            resource = q.resource_type.value if hasattr(q.resource_type, 'value') else str(q.resource_type)
            result[resource] = {
                "used": q.used_quota,
                "limit": q.total_quota,
                "remaining": max(0, q.total_quota - q.used_quota),
            }

        return {"found": True, "quotas": result}
    except Exception as e:
        logger.error(f"查询配额失败: {e}")
        return {"found": False, "error": str(e)}


def get_refund_policy() -> Dict[str, Any]:
    """
    获取退款政策

    Returns:
        退款政策信息
    """
    return {
        "found": True,
        "policy": {
            "return_period": "7天无理由退货",
            "exchange_period": "15天质量问题换货",
            "warranty_period": "1年官方保修（肉类产品以冷链保鲜为主，退换货请参照食品安全法规）",
            "refund_processing": "3-5个工作日到账",
            "special_notes": [
                "生鲜产品（肉类、乳制品）因涉及食品安全，不支持7天无理由退货",
                "如收到产品有质量问题（变质、破损），请在24小时内联系客服处理",
                "退货时请保持产品原包装及冷链包装完整",
            ],
            "contact": "客服热线: 400-xxx-xxxx",
        }
    }


def get_shipping_info(product_name: str = None) -> Dict[str, Any]:
    """
    获取配送信息

    Returns:
        配送政策
    """
    info = {
        "found": True,
        "shipping": {
            "default_method": "顺丰冷链配送",
            "time": "下单后1-3个工作日发货",
            "free_threshold": "订单满299元免运费",
            "tracking": "支持实时物流追踪",
            "cold_chain": "全程冷链配送，确保产品新鲜",
            "notes": [
                "内蒙古原产地直发，保证产品正宗",
                "偏远地区可能使用京东冷链",
                "夏季高温期间增加冰袋保鲜",
            ]
        }
    }

    if product_name:
        info["shipping"]["note"] = f"您查询的「{product_name}」支持冷链配送"

    return info


def query_logistics(order_no: str, db: Session) -> Dict[str, Any]:
    """
    查询物流信息（stub）

    Returns:
        物流信息
    """
    # 实际项目中对接物流API
    return {
        "found": True,
        "order_no": order_no,
        "status": "在途",
        "courier": "顺丰速运",
        "tracking_hint": "物流信息请前往「我的订单」页面查看",
    }