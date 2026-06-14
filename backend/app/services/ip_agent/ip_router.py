"""
IP路由器 - 意图识别与智能分发

根据用户消息自动选择合适的IP Agent
"""

from typing import Optional, List, Dict
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class IPType(str, Enum):
    """IP类型枚举"""

    XIAOSHU = "xiaoshu"  # 小数 - 草原文化传承者
    XIAOSHANG = "xiaoshang"  # 小商 - 品牌营销顾问


class IPRouter:
    """IP智能体路由器 - 意图识别与分发"""

    # 意图关键词映射
    INTENT_KEYWORDS = {
        IPType.XIAOSHU: [
            # 产品咨询类
            "故事",
            "历史",
            "文化",
            "产地",
            "草原",
            "推荐",
            "选购",
            "哪个好",
            "怎么选",
            "怎么吃",
            "怎么保存",
            "传说",
            "蒙古",
            # 产品类别
            "羊肉",
            "牛肉",
            "奶制品",
            "奶豆腐",
            "奶皮子",
            "马奶酒",
            "特产",
            "杂粮",
            # 文化元素
            "习俗",
            "节日",
            "那达慕",
            "敖包",
            "蒙古包",
            "马头琴",
            "呼麦",
            # 地域
            "呼伦贝尔",
            "锡林郭勒",
            "科尔沁",
            "鄂尔多斯",
        ],
        IPType.XIAOSHANG: [
            # 营销动作
            "营销",
            "推广",
            "直播",
            "带货",
            "文案",
            "脚本",
            "策划",
            "活动",
            "促销",
            # 平台相关
            "平台",
            "抖音",
            "小红书",
            "公众号",
            "视频号",
            "淘宝",
            "京东",
            # 运营相关
            "运营",
            "策略",
            "内容",
            "怎么卖",
            "怎么推",
            "吸粉",
            "涨粉",
            # 数据分析
            "效果",
            "数据",
            "分析",
            "转化",
            "ROI",
            "复购",
            # 品牌相关
            "品牌",
            "slogan",
            "定位",
            "名字",
            "logo",
        ],
    }

    def route(self, user_message: str, conversation_history: Optional[List[Dict]] = None) -> IPType:
        """
        根据用户消息路由到合适的IP

        算法：
        1. 统计关键词命中数
        2. 考虑对话历史的IP倾向 (连续性加权)
        3. 返回得分最高的IP
        4. 默认返回小数 (通用咨询)

        Args:
            user_message: 用户消息
            conversation_history: 对话历史 (可选)
                格式: [{"role": "user", "content": "...", "ip_type": "xiaoshu"}, ...]

        Returns:
            IPType: xiaoshu 或 xiaoshang
        """
        message_lower = user_message.lower()

        # 1. 统计关键词命中
        scores = {ip_type: 0 for ip_type in IPType}

        for ip_type, keywords in self.INTENT_KEYWORDS.items():
            score = sum(1 for kw in keywords if kw in message_lower)
            scores[ip_type] = score

        # 2. 对话历史加权 (如果最近3轮都是同一个IP，加权+2)
        if conversation_history and len(conversation_history) >= 3:
            recent_ips = []
            for msg in conversation_history[-3:]:
                if isinstance(msg, dict) and "ip_type" in msg:
                    recent_ips.append(msg["ip_type"])

            # 检查是否连续使用同一IP
            if len(set(recent_ips)) == 1 and recent_ips[0]:
                try:
                    continuous_ip = IPType(recent_ips[0])
                    scores[continuous_ip] += 2
                    logger.info(f"[IPRouter] Continuous IP detected: {continuous_ip.value}, adding weight +2")
                except ValueError:
                    pass

        # 3. 日志记录
        logger.info(f"[IPRouter] Message: '{user_message[:50]}...' | Scores: {scores}")

        # 4. 返回得分最高的IP
        if scores[IPType.XIAOSHANG] > scores[IPType.XIAOSHU]:
            logger.info(f"[IPRouter] Routed to: {IPType.XIAOSHANG.value}")
            return IPType.XIAOSHANG

        logger.info(f"[IPRouter] Routed to: {IPType.XIAOSHU.value} (default)")
        return IPType.XIAOSHU  # 默认小数

    def get_route_explanation(self, user_message: str, routed_ip: IPType) -> str:
        """
        获取路由决策解释 (用于调试和日志)

        Args:
            user_message: 用户消息
            routed_ip: 路由结果

        Returns:
            str: 解释说明
        """
        message_lower = user_message.lower()
        matched_keywords = []

        for keyword in self.INTENT_KEYWORDS[routed_ip]:
            if keyword in message_lower:
                matched_keywords.append(keyword)

        if matched_keywords:
            return f"匹配关键词: {', '.join(matched_keywords[:5])}"
        else:
            return "无明确关键词匹配，使用默认路由"
