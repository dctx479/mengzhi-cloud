"""品牌故事生成器核心服务"""

import logging
from typing import Dict, List, Any, Optional
from sqlalchemy.orm import Session

from app.services.brand_story.prompts_fusion import build_brand_story_messages
from app.services.ai.deepseek_client import DeepSeekClient
from app.services.cultural.enhanced_collector import EnhancedCulturalCollector

logger = logging.getLogger(__name__)


class BrandStoryGenerator:
    """品牌故事生成器"""

    def __init__(self, db: Session, llm_client: Optional[Any] = None):
        """初始化生成器"""
        self.db = db
        self.llm_client = llm_client or DeepSeekClient()
        self._jimeng_client = None  # lazy-loaded on first use

        try:
            self.cultural_collector = EnhancedCulturalCollector(enable_kg=True)
            logger.info(f"Cultural collector initialized")
        except Exception as e:
            logger.warning(f"Failed to init cultural collector: {e}")
            self.cultural_collector = None

    async def generate_story(
        self,
        product_name: str,
        origin: str,
        features: str = "",
        purpose: str = "电商详情页",
        style: str = "现代简约",
        word_count: str = "300字左右",
        category: str = "",
        keywords: List[str] = None,
        use_culture: bool = True,
        temperature: float = 0.7,
        auto_generate_image: bool = False,
    ) -> Dict[str, Any]:
        """生成品牌故事"""
        try:
            # 构建产品信息
            product_info = {
                "name": product_name,
                "origin": origin,
                "features": features,
                "purpose": purpose,
                "style": style,
                "word_count": word_count,
            }

            # 查询文化元素
            cultural_elements = []
            cultural_context = ""
            if use_culture and self.cultural_collector:
                cultural_elements = self._query_cultural_elements(product_name, origin, category, keywords)
                if cultural_elements:
                    cultural_context = self._build_cultural_context(cultural_elements)

            # 构建消息
            messages = build_brand_story_messages(product_info, few_shot_limit=2)

            # 追加文化背景
            if cultural_context and messages:
                last_msg = messages[-1]
                if last_msg.get("role") == "user":
                    last_msg["content"] = last_msg["content"] + cultural_context

            # 调用LLM
            response = await self.llm_client.chat_completion(
                messages=messages,
                system_prompt="",
                temperature=temperature,
            )

            story = response["choices"][0]["message"]["content"]
            usage = response["usage"]
            cost = self.llm_client.calculate_cost(usage["prompt_tokens"], usage["completion_tokens"])

            result = {
                "story": story,
                "cultural_elements": cultural_elements,
                "tokens": {
                    "input": usage["prompt_tokens"],
                    "output": usage["completion_tokens"],
                    "total": usage["total_tokens"],
                },
                "cost": cost,
                "metadata": {
                    "product_name": product_name,
                    "origin": origin,
                    "style": style,
                },
                "image_url": None,
            }

            # 自动生成配图（如果启用且有 Jimeng 配置）
            if auto_generate_image:
                image_url = await self._generate_cover_image(product_name, origin, story)
                result["image_url"] = image_url

            return result

        except Exception as e:
            logger.error(f"Failed to generate: {e}")
            raise

    def _query_cultural_elements(
        self, product_name: str, origin: str, category: str, keywords: List[str], top_k: int = 2
    ) -> List[Dict[str, Any]]:
        """查询产品相关的文化元素"""
        if not self.cultural_collector:
            return []

        try:
            query_info = {
                "name": product_name,
                "origin": origin,
                "category": category or "",
                "keywords": keywords or [],
            }

            results = self.cultural_collector.intelligent_match(query_info, use_kg=True, top_k=top_k)

            formatted = []
            for result in results:
                element = result["element"]
                formatted.append(
                    {
                        "name": element["name"],
                        "type": element["type"],
                        "story": element["story"],
                        "origin_region": element.get("origin_region", ""),
                        "score": result["score"],
                        "match_reason": result["match_reason"],
                    }
                )

            return formatted

        except Exception as e:
            logger.error(f"Failed to query cultural elements: {e}")
            return []

    def _build_cultural_context(self, cultural_elements: List[Dict]) -> str:
        """构建文化元素上下文"""
        if not cultural_elements:
            return ""

        context = "\n\n**【文化背景资料】（请在创作中自然融入这些元素）**\n\n"

        for i, element in enumerate(cultural_elements, 1):
            context += f"{i}. **{element['name']}**（{element['type']}）\n"
            story = element.get("story", "")
            if len(story) > 200:
                story = story[:200] + "..."
            context += f"   {story}\n\n"

        return context

    async def _generate_cover_image(
        self,
        product_name: str,
        origin: str,
        story: str,
    ) -> Optional[str]:
        """使用即梦AI生成品牌故事配图，失败时静默返回 None"""
        try:
            from app.services.ai.multimedia_factory import MultimediaProviderFactory

            # enterprise_id=None: 保持原行为, 不限企业取任一 active jimeng 配置
            client = MultimediaProviderFactory.resolve_for_enterprise(self.db, None, "jimeng")
            if client is None:
                return None

            # 构建配图 prompt
            prompt = (
                f"中国传统文化风格产品宣传图，"
                f"产品：{product_name}，产地：{origin}，"
                f"画面唯美、色彩丰富、极简主义，无文字"
            )
            result = await client.generate_image(
                prompt=prompt,
                model="text-to-image-3.1",
                width=1024,
                height=1024,
            )
            return result.get("image_url")

        except Exception as e:
            logger.warning(f"Auto image generation skipped: {e}")
            return None
