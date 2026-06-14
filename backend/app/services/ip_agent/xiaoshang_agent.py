"""
小商Agent - 品牌营销顾问

专注于营销策略、内容创作、平台运营
"""

from typing import Dict, List, Any
from sqlalchemy.orm import Session
import logging

from .base_ip_agent import BaseIPAgent
from .prompts_fusion import get_xiaoshang_prompt_fusion, get_xiaoshang_examples_fusion

logger = logging.getLogger(__name__)


class XiaoshangAgent(BaseIPAgent):
    """小商 - 品牌营销顾问（融合版Prompt）"""

    def __init__(self, db: Session, llm_client: Any):
        super().__init__(db, llm_client)
        self.ip_name = "小商"
        self.ip_type = "xiaoshang"

    def _get_system_prompt(self) -> str:
        """获取融合版System Prompt"""
        return get_xiaoshang_prompt_fusion()

    def _get_few_shot_examples(self) -> List[Dict[str, str]]:
        """获取融合版Few-shot示例"""
        return get_xiaoshang_examples_fusion()

    # 保留原有的意图分析方法
    def _analyze_marketing_intent(self, message: str) -> List[str]:
        """
        分析营销意图类型

        Args:
            message: 用户消息

        Returns:
            List[str]: 意图类型列表
        """
        intent_keywords = {
            "content_creation": ["文案", "脚本", "视频", "图文", "内容", "写"],
            "platform_strategy": ["抖音", "小红书", "公众号", "平台", "运营"],
            "brand_story": ["品牌", "故事", "定位", "slogan", "名字"],
            "data_analysis": ["数据", "分析", "效果", "转化", "优化"],
            "live_streaming": ["直播", "带货", "主播"],
            "activity_planning": ["活动", "促销", "营销", "策划"],
        }

        detected_intents = []
        message_lower = message.lower()

        for intent, keywords in intent_keywords.items():
            if any(kw in message_lower for kw in keywords):
                detected_intents.append(intent)

        return detected_intents

    def _extract_metadata(self, user_message: str, assistant_response: str) -> Dict[str, Any]:
        """提取小商专属元数据"""
        metadata = super()._extract_metadata(user_message, assistant_response)

        # 分析营销意图类型
        marketing_intents = self._analyze_marketing_intent(user_message)
        if marketing_intents:
            metadata["marketing_intents"] = marketing_intents

        return metadata
