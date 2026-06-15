"""
小数Agent - 草原文化传承者

专注于产品咨询、文化故事、选购建议

版本: 2.0
更新日期: 2026-06-12
新增: 文化元素智能匹配集成
"""

from typing import Dict, List, Any, Optional
from sqlalchemy.orm import Session
import logging

from .base_ip_agent import BaseIPAgent
from .prompts_fusion import get_xiaoshu_prompt_fusion, get_xiaoshu_examples_fusion
from ..cultural.enhanced_collector import EnhancedCulturalCollector

logger = logging.getLogger(__name__)


class XiaoshuAgent(BaseIPAgent):
    """小数 - 草原文化传承者（融合版Prompt + 文化元素智能匹配）"""

    def __init__(self, db: Session, llm_client: Any):
        super().__init__(db, llm_client)
        self.ip_name = "小数"
        self.ip_type = "xiaoshu"

        # 初始化文化元素采集器
        try:
            self.cultural_collector = EnhancedCulturalCollector(enable_kg=True)
            logger.info(
                f"[{self.ip_type}] Cultural collector initialized with {len(self.cultural_collector.elements)} elements"
            )
        except Exception as e:
            logger.warning(f"[{self.ip_type}] Failed to initialize cultural collector: {str(e)}")
            self.cultural_collector = None

    def _get_system_prompt(self) -> str:
        """获取融合版System Prompt"""
        return get_xiaoshu_prompt_fusion()

    def _get_few_shot_examples(self) -> List[Dict[str, str]]:
        """获取融合版Few-shot示例"""
        return get_xiaoshu_examples_fusion()

    def query_cultural_elements(
        self, product_name: str, origin: str, category: str = "", keywords: List[str] = None, top_k: int = 3
    ) -> List[Dict[str, Any]]:
        """
        查询与产品相关的文化元素

        Args:
            product_name: 产品名称
            origin: 产地
            category: 产品类别
            keywords: 关键词列表
            top_k: 返回前K个结果

        Returns:
            List[Dict]: 匹配的文化元素列表
                [
                    {
                        "name": str,
                        "type": str,
                        "story": str,
                        "score": float,
                        "match_reason": str
                    },
                    ...
                ]
        """
        if not self.cultural_collector:
            logger.warning(f"[{self.ip_type}] Cultural collector not available")
            return []

        try:
            product_info = {"name": product_name, "origin": origin, "category": category, "keywords": keywords or []}

            results = self.cultural_collector.intelligent_match(product_info, use_kg=True, top_k=top_k)

            formatted_results = []
            for result in results:
                element = result["element"]
                formatted_results.append(
                    {
                        "name": element["name"],
                        "type": element["type"],
                        "story": element["story"],
                        "origin_region": element.get("origin_region", ""),
                        "keywords": element.get("keywords", []),
                        "score": result["score"],
                        "match_reason": result["match_reason"],
                    }
                )

            logger.info(
                f"[{self.ip_type}] Found {len(formatted_results)} cultural elements for product: {product_name}"
            )

            return formatted_results

        except Exception as e:
            logger.error(f"[{self.ip_type}] Failed to query cultural elements: {str(e)}")
            return []

    def enrich_response_with_culture(
        self, base_response: str, product_name: str, origin: str, category: str = "", keywords: List[str] = None
    ) -> str:
        """
        用文化元素丰富响应内容

        Args:
            base_response: 基础响应内容
            product_name: 产品名称
            origin: 产地
            category: 产品类别
            keywords: 关键词列表

        Returns:
            str: 丰富后的响应内容
        """
        if not self.cultural_collector:
            return base_response

        try:
            cultural_elements = self.query_cultural_elements(product_name, origin, category, keywords, top_k=2)

            if not cultural_elements:
                return base_response

            # 构建文化元素补充内容
            cultural_supplement = "\n\n---\n\n"
            cultural_supplement += "**相关文化背景**\n\n"

            for i, element in enumerate(cultural_elements[:2], 1):
                cultural_supplement += f"{i}. **{element['name']}** ({element['type']})\n"
                # 提取故事前150字
                story_preview = element["story"][:150] + "..." if len(element["story"]) > 150 else element["story"]
                cultural_supplement += f"   {story_preview}\n\n"

            enriched_response = base_response + cultural_supplement

            logger.info(f"[{self.ip_type}] Enriched response with {len(cultural_elements)} cultural elements")

            return enriched_response

        except Exception as e:
            logger.error(f"[{self.ip_type}] Failed to enrich response: {str(e)}")
            return base_response

    def _retrieve_relevant_elements(
        self, user_message: str, top_k: int = 2, min_score: float = 10.0
    ) -> List[Dict[str, Any]]:
        """
        检索与用户消息相关的文化元素（用于回答时的知识增强）

        Args:
            user_message: 用户消息
            top_k: 最多返回的元素数
            min_score: 最低相关度阈值，过滤无关元素
                （intelligent_match 总分为 0-60 量纲：L1精确匹配×0.4 + L3知识图谱×0.2）

        Returns:
            List[Dict]: 达到相关度阈值的文化元素
        """
        if not self.cultural_collector:
            return []

        keywords = self._extract_cultural_elements(user_message)
        elements = self.query_cultural_elements(
            product_name=user_message, origin="", category="", keywords=keywords, top_k=top_k
        )
        return [e for e in elements if e.get("score", 0) >= min_score]

    def _inject_knowledge_context(self, user_message: str, messages: List[Dict[str, str]]) -> List[Dict[str, str]]:
        """
        为小数注入文化元素知识上下文（RAG）

        在当前用户消息前拼接检索到的文化元素故事，让回答基于真实文化知识库。
        检索失败时静默降级（记 WARNING），不影响正常对话。
        """
        try:
            elements = self._retrieve_relevant_elements(user_message, top_k=2)
            if not elements:
                return messages

            context_lines = ["【相关文化背景知识，回答时请自然融入，不要生硬罗列】"]
            for el in elements:
                story = el["story"][:200]
                context_lines.append(f"- {el['name']}（{el['type']}）：{story}")
            context_block = "\n".join(context_lines)

            if messages:
                last = messages[-1]
                messages[-1] = {
                    "role": last["role"],
                    "content": f"{context_block}\n\n用户问题：{last['content']}",
                }
            logger.info(f"[{self.ip_type}] 已注入 {len(elements)} 个文化元素作为回答上下文")
        except Exception as e:
            logger.warning(f"[{self.ip_type}] 文化知识注入跳过: {str(e)}")

        return messages

    def _extract_metadata(self, user_message: str, assistant_response: str) -> Dict[str, Any]:
        """提取小数专属元数据（增强版：包含匹配的文化元素）"""
        metadata = super()._extract_metadata(user_message, assistant_response)

        # 提取文化元素关键词
        cultural_elements = self._extract_cultural_elements(user_message + assistant_response)
        if cultural_elements:
            metadata["cultural_elements"] = cultural_elements

        return metadata

    def _extract_cultural_elements(self, text: str) -> List[str]:
        """
        提取文化元素关键词

        Args:
            text: 待分析文本

        Returns:
            List[str]: 文化元素列表
        """
        cultural_keywords = [
            "草原",
            "蒙古",
            "那达慕",
            "敖包",
            "马头琴",
            "蒙古包",
            "游牧",
            "锡林郭勒",
            "呼伦贝尔",
            "额吉",
            "乌兰牧骑",
            "成吉思汗",
            "风干肉",
            "奶茶",
            "马奶酒",
        ]

        found_elements = []
        text_lower = text.lower()

        for keyword in cultural_keywords:
            if keyword in text_lower:
                found_elements.append(keyword)

        # 去重
        return list(set(found_elements))
