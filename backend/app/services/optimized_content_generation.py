"""
优化的内容生成服务 - AI-007 核心实现

功能：
- 集成RAG检索
- 自适应参数优化
- 多样性控制
- 质量评估
- 性能优化（缓存、批处理）

版本: 2.0 (优化版)
更新日期: 2026-01-17
"""

import asyncio
import json
import hashlib
import re
import threading
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from loguru import logger
from sqlalchemy.orm import Session
from tenacity import retry, stop_after_attempt, wait_exponential

from app.services.ai.deepseek_client import get_deepseek_client
from app.services.ai.prompt_templates import PromptTemplates
from app.services.rag_knowledge_base import CulturalKnowledgeBase, MarketingMaterialLibrary
from app.services.content_optimization import AdaptiveParameterOptimizer, DiversityController
from app.services.content_postprocessor import ContentPostProcessor, QualityAssessment
from app.models.content_record import ContentRecord, ContentType, Style, Platform, RecordStatus
from app.models.product import Product
from app.core.config import settings


class OptimizedContentGenerationService:
    """
    优化的内容生成服务 - AI-007 核心实现

    整合了：
    - RAG知识库检索
    - 自适应参数优化
    - 多样性控制
    - 质量评估
    - 性能缓存
    """

    # Class-level shared cache so all instances within the same process benefit
    _shared_cache: Dict[str, Any] = {}
    _cache_lock = threading.Lock()

    # Timeout for a single AI generation call (seconds)
    _AI_TIMEOUT = 30

    def __init__(self, db: Session):
        """初始化"""
        self.knowledge_base_initialized = False
        self.db = db
        self.deepseek_client = None
        self.knowledge_base = CulturalKnowledgeBase()
        self.marketing_library = MarketingMaterialLibrary()
        self.diversity_controller = DiversityController(db=db)

        # 缓存配置
        self.cache_enabled = settings.CACHE_ENABLED if hasattr(settings, 'CACHE_ENABLED') else True
        self.cache_ttl = 3600  # 1小时

    async def initialize(self):
        """异步初始化"""
        self.deepseek_client = await get_deepseek_client()

        # 构建知识库索引
        try:
            await self.knowledge_base.build_index(self.db)
            self.knowledge_base_initialized = True
        except Exception as e:
            logger.warning(f"知识库初始化失败，将使用备用检索: {str(e)}")

    async def generate_product_copy(
        self,
        product_id: int,
        content_type: ContentType = ContentType.COPY,
        style: Style = Style.CASUAL,
        platform: Platform = Platform.GENERAL,
        word_count: int = 200,
        **kwargs
    ) -> str:
        """
        生成产品文案（主入口）

        Args:
            product_id: 产品ID
            content_type: 内容类型
            style: 风格
            platform: 目标平台
            word_count: 目标字数
            **kwargs: 其他参数

        Returns:
            生成的内容
        """
        # 确保初始化完成
        if not self.deepseek_client:
            await self.initialize()

        try:
            # 1. 检索产品信息
            product = self.db.query(Product).filter_by(id=product_id).first()
            if not product:
                raise ValueError(f"产品ID {product_id} 不存在")

            # 2. 检查缓存
            cache_key = self._generate_cache_key(product_id, content_type, style, platform)
            if self.cache_enabled:
                cached_content = self._get_from_cache(cache_key)
                if cached_content:
                    logger.info(f"从缓存返回内容 (key: {cache_key})")
                    return cached_content

            # 3. 构建增强Prompt
            enhanced_prompt = await self._build_enhanced_prompt(
                product=product,
                content_type=content_type,
                style=style,
                platform=platform,
                word_count=word_count
            )

            # 4. 获取最优参数
            params = AdaptiveParameterOptimizer.get_optimal_parameters(
                content_type=content_type,
                style=style,
                platform=platform,
                quality_score=None
            )
            params['max_tokens'] = word_count * 2

            # 5. 调用DeepSeek生成
            generated_content = await self._generate_with_retry(
                prompt=enhanced_prompt,
                params=params
            )

            # 6. 后处理和质量检查
            final_content = await ContentPostProcessor.process(
                content=generated_content,
                style=style,
                platform=platform,
                target_word_count=word_count,
                content_type=content_type
            )

            # 7. 评估质量
            quality_score, quality_details = await QualityAssessment.assess_content(
                content=final_content,
                target_word_count=word_count,
                content_type=content_type,
                platform=platform
            )

            logger.info(f"内容生成完成: 质量分 {quality_score:.2f}, 长度 {len(final_content)}")

            # 8. 保存到缓存
            if self.cache_enabled:
                self._save_to_cache(cache_key, final_content)

            return final_content

        except Exception as e:
            logger.error(f"内容生成失败: {str(e)}")
            raise

    async def generate_multiple_variants(
        self,
        product_id: int,
        count: int = 3,
        content_type: ContentType = ContentType.COPY,
        style: Style = Style.CASUAL,
        platform: Platform = Platform.GENERAL,
        word_count: int = 200,
        **kwargs
    ) -> List[str]:
        """
        生成多个内容变体

        Args:
            product_id: 产品ID
            count: 生成数量
            content_type: 内容类型
            style: 风格
            platform: 目标平台
            word_count: 目标字数
            **kwargs: 其他参数

        Returns:
            内容列表
        """
        # 确保初始化完成
        if not self.deepseek_client:
            await self.initialize()

        logger.info(f"开始生成 {count} 个内容变体")

        try:
            # 获取产品
            product = self.db.query(Product).filter_by(id=product_id).first()
            if not product:
                raise ValueError(f"产品ID {product_id} 不存在")

            # 定义生成函数
            async def generation_func(temperature: float, attempt_number: int) -> str:
                prompt = await self._build_enhanced_prompt(
                    product=product,
                    content_type=content_type,
                    style=style,
                    platform=platform,
                    word_count=word_count,
                    attempt_number=attempt_number
                )

                params = AdaptiveParameterOptimizer.get_optimal_parameters(
                    content_type=content_type,
                    style=style,
                    platform=platform
                )
                params['temperature'] = temperature
                params['max_tokens'] = word_count * 2

                content = await self._generate_with_retry(prompt=prompt, params=params)

                final_content = await ContentPostProcessor.process(
                    content=content,
                    style=style,
                    platform=platform,
                    target_word_count=word_count,
                    content_type=content_type
                )

                return final_content

            # 使用多样性控制器生成变体
            variants = await self.diversity_controller.generate_diverse_variants(
                product_id=product_id,
                count=count,
                content_type=content_type,
                style=style,
                generation_func=generation_func,
                db=self.db
            )

            logger.info(f"成功生成 {len(variants)} 个变体")
            return variants

        except Exception as e:
            logger.error(f"生成变体失败: {str(e)}")
            raise

    @staticmethod
    def _sanitize_text(text: str, max_length: int = 500) -> str:
        """Strip control characters and truncate to prevent prompt injection."""
        if not text:
            return ""
        # Remove ASCII control chars except tab (\x09) and newline (\x0a, \x0d)
        text = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]', '', text)
        return text[:max_length].strip()

    async def _build_enhanced_prompt(
        self,
        product: Product,
        content_type: ContentType,
        style: Style,
        platform: Platform,
        word_count: int,
        attempt_number: int = 0
    ) -> str:
        """
        构建增强的Prompt（集成RAG）

        Args:
            product: 产品对象
            content_type: 内容类型
            style: 风格
            platform: 平台
            word_count: 字数
            attempt_number: 尝试次数

        Returns:
            构建的Prompt
        """
        # 1. 获取系统提示词
        system_prompt = PromptTemplates.get_system_prompt()

        # 2. RAG检索：获取文化背景
        cultural_context = await self.knowledge_base.retrieve_cultural_context(
            product=product,
            top_k=5
        )

        cultural_text = self._format_cultural_context(cultural_context)

        # 3. 检索营销素材
        marketing_materials = await self.knowledge_base.retrieve_marketing_materials(
            category=product.category,
            style=style.value,
            top_k=3
        )

        marketing_text = self._format_marketing_materials(marketing_materials)

        # 4. 构建用户提示 — sanitize all product fields to prevent prompt injection
        safe_name = self._sanitize_text(product.name or '', 100)
        safe_category = self._sanitize_text(product.category or '', 50)
        safe_province = self._sanitize_text(product.origin_province or '', 50)
        safe_city = self._sanitize_text(product.origin_city or '', 50)
        safe_description = self._sanitize_text(product.description or '暂无', 300)
        safe_features = ', '.join(
            self._sanitize_text(f, 50) for f in (product.features or [])
        ) or '暂无'

        user_prompt = f"""
请为以下农畜产品生成{self._get_content_type_name(content_type)}：

【产品信息】
名称：{safe_name}
类别：{safe_category}
产地：{safe_province} {safe_city}
描述：{safe_description}
特点：{safe_features}

【文化背景】
{cultural_text}

【营销参考】
{marketing_text}

【生成要求】
- 风格：{style.value}
- 平台：{platform.value}
- 字数：{word_count}字（±15%可接受）
- 融入文化元素和产品特点
- 吸引目标消费者
{f'- 尽量避免与之前的表达重复（第{attempt_number}次尝试）' if attempt_number > 0 else ''}

请直接输出内容，不需要额外说明。
"""

        return user_prompt

    async def _generate_with_retry(
        self,
        prompt: str,
        params: Dict[str, Any],
        max_retries: int = 3
    ) -> str:
        """
        带重试和质量检查的生成

        Args:
            prompt: Prompt
            params: 生成参数
            max_retries: 最大重试次数

        Returns:
            生成的内容
        """
        last_error = None

        for attempt in range(max_retries):
            try:
                logger.info(f"生成内容 (尝试 {attempt + 1}/{max_retries})")

                try:
                    response = await asyncio.wait_for(
                        self.deepseek_client.chat_completion(
                            messages=[{"role": "user", "content": prompt}],
                            system_prompt=PromptTemplates.get_system_prompt(),
                            **params
                        ),
                        timeout=self._AI_TIMEOUT
                    )
                except asyncio.TimeoutError:
                    raise RuntimeError(f"AI生成超时 (>{self._AI_TIMEOUT}s)")

                content = response['choices'][0]['message']['content']

                if content and len(content.strip()) > 50:
                    logger.info(f"生成成功 (长度: {len(content)})")
                    return content

                last_error = "生成内容过短"

            except Exception as e:
                logger.error(f"生成尝试 {attempt + 1} 失败: {str(e)}")
                last_error = str(e)

                if attempt < max_retries - 1:
                    # 调整参数重试
                    params = AdaptiveParameterOptimizer.adjust_for_retry(
                        params,
                        retry_count=attempt + 1
                    )
                    await asyncio.sleep(2 ** attempt)  # 指数退避

        raise RuntimeError(f"内容生成失败 (尝试 {max_retries} 次): {last_error}")

    def _format_cultural_context(self, context: List[Dict[str, Any]]) -> str:
        """格式化文化背景"""
        if not context:
            return "暂无文化背景信息"

        lines = []
        for item in context:
            lines.append(f"- [{item.get('type', '文化')}] {item.get('content', '')}")

        return '\n'.join(lines[:5])

    def _format_marketing_materials(self, materials: List[Dict[str, Any]]) -> str:
        """格式化营销素材"""
        if not materials:
            return "暂无营销参考"

        lines = []
        for item in materials:
            lines.append(f"- {item.get('content', '')}")

        return '\n'.join(lines)

    @staticmethod
    def _get_content_type_name(content_type: ContentType) -> str:
        """获取内容类型的中文名称"""
        type_names = {
            ContentType.COPY: "营销文案",
            ContentType.SCRIPT: "直播脚本",
            ContentType.VIDEO_COPY: "短视频文案",
            ContentType.SLOGAN: "广告标语",
            ContentType.STORY: "品牌故事",
        }
        return type_names.get(content_type, "内容")

    def _generate_cache_key(
        self,
        product_id: int,
        content_type: ContentType,
        style: Style,
        platform: Platform
    ) -> str:
        """生成缓存键"""
        key_str = f"{product_id}_{content_type.value}_{style.value}_{platform.value}"
        return hashlib.md5(key_str.encode(), usedforsecurity=False).hexdigest()

    def _get_from_cache(self, key: str) -> Optional[str]:
        """从共享缓存获取（线程安全）"""
        try:
            with self.__class__._cache_lock:
                entry = self.__class__._shared_cache.get(key)
                if entry is None:
                    return None
                if datetime.now() - entry['timestamp'] < timedelta(seconds=self.cache_ttl):
                    return entry['content']
                del self.__class__._shared_cache[key]
            return None
        except Exception as e:
            logger.warning(f"缓存读取异常，将跳过缓存: {str(e)}")
            return None

    def _save_to_cache(self, key: str, content: str) -> None:
        """保存到共享缓存（线程安全，最多保留100条）"""
        try:
            with self.__class__._cache_lock:
                cache = self.__class__._shared_cache
                cache[key] = {'content': content, 'timestamp': datetime.now()}
                if len(cache) > 100:
                    oldest_key = min(cache.keys(), key=lambda k: cache[k]['timestamp'])
                    del cache[oldest_key]
        except Exception as e:
            logger.warning(f"缓存保存异常: {str(e)}")


class ContentGenerationServiceFactory:
    """内容生成服务工厂"""

    _instance: Optional[OptimizedContentGenerationService] = None

    @classmethod
    async def get_service(cls, db: Session) -> OptimizedContentGenerationService:
        """获取或创建服务实例"""
        service = OptimizedContentGenerationService(db)
        await service.initialize()
        return service
