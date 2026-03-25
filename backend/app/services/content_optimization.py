"""
内容生成参数优化和多样性控制 - AI-007 优化

功能：
- 自适应参数调整 (temperature, top_p等)
- 多样性控制和检测
- 相似度计算和管理
- 内容变体生成

版本: 2.0 (优化版)
更新日期: 2026-01-17
"""

import asyncio
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
from loguru import logger
from sqlalchemy.orm import Session
from app.models.content_record import ContentRecord, ContentType, Style, Platform

try:
    from sentence_transformers import SentenceTransformer, util
    import numpy as np
    HAS_EMBEDDINGS = True
except ImportError:
    HAS_EMBEDDINGS = False


class AdaptiveParameterOptimizer:
    """自适应参数优化器 - 根据内容类型和风格调整生成参数"""

    # 参数映射表
    PARAMETER_PRESETS = {
        # 内容类型 -> 参数配置
        ContentType.COPY: {
            Style.PROFESSIONAL: {'temperature': 0.5, 'top_p': 0.85, 'max_tokens': 500},
            Style.CASUAL: {'temperature': 0.7, 'top_p': 0.9, 'max_tokens': 400},
            Style.EMOTIONAL: {'temperature': 0.75, 'top_p': 0.92, 'max_tokens': 450},
            Style.HUMOROUS: {'temperature': 0.8, 'top_p': 0.95, 'max_tokens': 350},
        },
        ContentType.SLOGAN: {
            Style.PROFESSIONAL: {'temperature': 0.4, 'top_p': 0.8, 'max_tokens': 100},
            Style.CASUAL: {'temperature': 0.6, 'top_p': 0.88, 'max_tokens': 80},
            Style.EMOTIONAL: {'temperature': 0.7, 'top_p': 0.9, 'max_tokens': 100},
            Style.HUMOROUS: {'temperature': 0.75, 'top_p': 0.92, 'max_tokens': 100},
        },
        ContentType.SCRIPT: {
            Style.PROFESSIONAL: {'temperature': 0.6, 'top_p': 0.88, 'max_tokens': 1000},
            Style.CASUAL: {'temperature': 0.7, 'top_p': 0.9, 'max_tokens': 900},
            Style.EMOTIONAL: {'temperature': 0.8, 'top_p': 0.93, 'max_tokens': 1000},
            Style.HUMOROUS: {'temperature': 0.85, 'top_p': 0.95, 'max_tokens': 1000},
        },
        ContentType.VIDEO_COPY: {
            Style.PROFESSIONAL: {'temperature': 0.6, 'top_p': 0.88, 'max_tokens': 300},
            Style.CASUAL: {'temperature': 0.7, 'top_p': 0.9, 'max_tokens': 280},
            Style.EMOTIONAL: {'temperature': 0.75, 'top_p': 0.92, 'max_tokens': 300},
            Style.HUMOROUS: {'temperature': 0.8, 'top_p': 0.95, 'max_tokens': 300},
        },
        ContentType.STORY: {
            Style.PROFESSIONAL: {'temperature': 0.6, 'top_p': 0.88, 'max_tokens': 600},
            Style.CASUAL: {'temperature': 0.7, 'top_p': 0.9, 'max_tokens': 600},
            Style.EMOTIONAL: {'temperature': 0.8, 'top_p': 0.93, 'max_tokens': 700},
            Style.HUMOROUS: {'temperature': 0.75, 'top_p': 0.92, 'max_tokens': 600},
        },
    }

    # 平台特定调整
    PLATFORM_ADJUSTMENTS = {
        Platform.DOUYIN: {'temperature': +0.1, 'max_tokens': -100},  # 短视频需要更活泼、更短
        Platform.XIAOHONGSHU: {'temperature': +0.05, 'max_tokens': 0},  # 小红书稍活泼
        Platform.WECHAT: {'temperature': -0.05, 'max_tokens': +100},  # 微信公众号更严谨
        Platform.WEIBO: {'temperature': 0, 'max_tokens': -50},  # 微博中等
        Platform.KUAISHOU: {'temperature': +0.1, 'max_tokens': -100},  # 快手短视频
        Platform.GENERAL: {'temperature': 0, 'max_tokens': 0},  # 通用不调整
    }

    @classmethod
    def get_optimal_parameters(
        cls,
        content_type: ContentType,
        style: Style,
        platform: Optional[Platform] = None,
        quality_score: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        获取最优参数配置

        Args:
            content_type: 内容类型
            style: 内容风格
            platform: 目标平台
            quality_score: 上一次生成的质量分 (0-1)

        Returns:
            参数配置字典
        """
        # 1. 获取基础参数
        params = cls.PARAMETER_PRESETS.get(content_type, {}).get(
            style,
            {'temperature': 0.7, 'top_p': 0.9, 'max_tokens': 500}
        ).copy()

        # 2. 应用平台调整
        if platform in cls.PLATFORM_ADJUSTMENTS:
            adjustment = cls.PLATFORM_ADJUSTMENTS[platform]
            params['temperature'] = max(0, min(1, params['temperature'] + adjustment.get('temperature', 0)))
            params['max_tokens'] = max(100, params['max_tokens'] + adjustment.get('max_tokens', 0))

        # 3. 基于质量分数动态调整
        if quality_score is not None:
            if quality_score < 0.6:  # 质量较差
                # 降低temperature以提高稳定性
                params['temperature'] = max(0.3, params['temperature'] - 0.15)
                params['top_p'] = max(0.7, params.get('top_p', 0.9) - 0.1)
            elif quality_score > 0.9:  # 质量优秀
                # 可以提高temperature增加多样性
                params['temperature'] = min(1.0, params['temperature'] + 0.1)

        logger.info(f"生成最优参数: {content_type.value}/{style.value} -> {params}")

        return params

    @classmethod
    def adjust_for_retry(
        cls,
        current_params: Dict[str, Any],
        retry_count: int = 1
    ) -> Dict[str, Any]:
        """
        为重试调整参数

        Args:
            current_params: 当前参数
            retry_count: 重试次数

        Returns:
            调整后的参数
        """
        adjusted = current_params.copy()

        # 逐次尝试增加diversity
        temperature_increase = min(0.3, retry_count * 0.1)
        adjusted['temperature'] = min(1.0, adjusted.get('temperature', 0.7) + temperature_increase)
        adjusted['top_p'] = min(0.99, adjusted.get('top_p', 0.9) + retry_count * 0.03)

        logger.info(f"重试参数调整 (第{retry_count}次): {adjusted}")

        return adjusted


class DiversityController:
    """多样性控制器 - 管理内容多样性和防止重复"""

    def __init__(self, db: Optional[Session] = None, similarity_threshold: float = 0.85):
        """
        初始化

        Args:
            db: 数据库会话
            similarity_threshold: 相似度阈值
        """
        self.db = db
        self.similarity_threshold = similarity_threshold
        # 延迟初始化编码器以避免阻塞，在需要时调用 _ensure_encoder()
        self._encoder = None
        self._encoder_initialized = False

    def _ensure_encoder(self):
        """惰性初始化编码器"""
        if not self._encoder_initialized and HAS_EMBEDDINGS and not self._encoder:
            self._encoder = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')
            self._encoder_initialized = True
        return self._encoder

    @property
    def encoder(self):
        """获取编码器，需要时初始化"""
        return self._ensure_encoder()

    async def generate_diverse_variants(
        self,
        product_id: int,
        count: int,
        content_type: ContentType,
        style: Style,
        generation_func,
        db: Session
    ) -> List[str]:
        """
        生成多样化的内容变体

        Args:
            product_id: 产品ID
            count: 生成数量
            content_type: 内容类型
            style: 风格
            generation_func: 内容生成函数
            db: 数据库会话

        Returns:
            内容列表
        """
        variants = []
        attempted = 0
        max_attempts = count * 3  # 最多尝试3倍

        # 检索最近生成的内容作为对比基准
        existing_contents = await self._get_recent_contents(
            product_id, content_type, limit=5, db=db
        )

        for attempt in range(max_attempts):
            if len(variants) >= count:
                break

            attempted += 1

            # 动态调整参数以增加多样性
            temperature_boost = (attempt // count) * 0.1
            current_temp = min(1.0, AdaptiveParameterOptimizer.PARAMETER_PRESETS
                             .get(content_type, {})
                             .get(style, {})
                             .get('temperature', 0.7) + temperature_boost)

            try:
                # 生成内容
                content = await generation_func(
                    temperature=current_temp,
                    attempt_number=attempt
                )

                # 检查是否与现有内容过于相似
                if await self._is_too_similar(content, variants + existing_contents):
                    logger.debug(f"第 {attempt + 1} 次尝试：内容相似度过高，跳过")
                    continue

                # 检查开头和结尾的多样性
                if not await self._has_opening_diversity(content, variants):
                    logger.debug(f"第 {attempt + 1} 次尝试：开头方式重复，跳过")
                    continue

                variants.append(content)
                logger.info(f"生成第 {len(variants)} 个多样化变体")

            except Exception as e:
                logger.error(f"生成变体失败 (尝试 {attempt + 1}): {str(e)}")
                continue

        if len(variants) < count:
            logger.warning(f"仅生成了 {len(variants)} 个变体，少于请求的 {count} 个")

        return variants[:count]

    async def _is_too_similar(
        self,
        content: str,
        existing_contents: List[str],
        threshold: Optional[float] = None
    ) -> bool:
        """
        检查内容相似度

        Args:
            content: 新内容
            existing_contents: 现有内容列表
            threshold: 相似度阈值

        Returns:
            是否过于相似
        """
        if not HAS_EMBEDDINGS or self.encoder is None or not existing_contents:
            return False

        threshold = threshold or self.similarity_threshold

        try:
            new_embedding = self.encoder.encode([content])[0]

            for existing in existing_contents:
                existing_embedding = self.encoder.encode([existing])[0]

                # 使用余弦相似度
                similarity = util.pytorch_cos_sim(new_embedding, existing_embedding).item()

                if similarity > threshold:
                    logger.debug(f"相似度: {similarity:.4f} (阈值: {threshold})")
                    return True

            return False

        except Exception as e:
            logger.error(f"相似度检查失败: {str(e)}")
            return False

    async def _has_opening_diversity(
        self,
        content: str,
        existing_variants: List[str]
    ) -> bool:
        """
        检查开头多样性

        Args:
            content: 新内容
            existing_variants: 现有变体

        Returns:
            是否有足够的开头多样性
        """
        if not existing_variants:
            return True

        # 获取前10个字作为开头特征
        opening = content[:10]

        # 检查是否与任何现有变体的开头相同
        for variant in existing_variants:
            if variant[:10] == opening:
                return False

        return True

    async def _get_recent_contents(
        self,
        product_id: int,
        content_type: ContentType,
        limit: int = 5,
        db: Optional[Session] = None
    ) -> List[str]:
        """
        获取最近生成的内容

        Args:
            product_id: 产品ID
            content_type: 内容类型
            limit: 数量限制
            db: 数据库会话

        Returns:
            内容列表
        """
        if not db:
            return []

        try:
            # 获取最近7天的内容记录
            recent_time = datetime.now() - timedelta(days=7)

            records = db.query(ContentRecord).filter(
                ContentRecord.product_id == product_id,
                ContentRecord.content_type == content_type,
                ContentRecord.created_at >= recent_time,
                ContentRecord.generated_content.isnot(None)
            ).order_by(
                ContentRecord.created_at.desc()
            ).limit(limit).all()

            return [r.generated_content for r in records]

        except Exception as e:
            logger.error(f"获取最近内容失败: {str(e)}")
            return []

    def calculate_content_similarity(
        self,
        content1: str,
        content2: str
    ) -> float:
        """
        计算两个内容的相似度

        Args:
            content1: 内容1
            content2: 内容2

        Returns:
            相似度 (0-1)
        """
        if not HAS_EMBEDDINGS or self.encoder is None:
            # 备用：基于字符串相似度
            return self._string_similarity(content1, content2)

        try:
            embedding1 = self.encoder.encode([content1])[0]
            embedding2 = self.encoder.encode([content2])[0]

            similarity = util.pytorch_cos_sim(embedding1, embedding2).item()
            return float(similarity)

        except Exception as e:
            logger.error(f"相似度计算失败: {str(e)}")
            return 0.0

    @staticmethod
    def _string_similarity(s1: str, s2: str) -> float:
        """
        基于字符串编辑距离的相似度计算

        Args:
            s1: 字符串1
            s2: 字符串2

        Returns:
            相似度 (0-1)
        """
        from difflib import SequenceMatcher
        return SequenceMatcher(None, s1, s2).ratio()


class ContentVariationManager:
    """内容变体管理器 - 生成和管理不同版本的内容"""

    def __init__(self, db: Session):
        """初始化"""
        self.db = db
        self.diversity_controller = DiversityController(db=db)

    async def create_variations(
        self,
        base_content: str,
        variation_count: int = 3,
        variation_types: Optional[List[str]] = None
    ) -> List[Dict[str, str]]:
        """
        基于原始内容生成变体

        Args:
            base_content: 原始内容
            variation_count: 变体数量
            variation_types: 变体类型列表

        Returns:
            变体列表
        """
        variations = []

        if not variation_types:
            variation_types = ['formal', 'casual', 'concise', 'extended']

        try:
            for vtype in variation_types[:variation_count]:
                variation = await self._generate_variation(base_content, vtype)
                if variation:
                    variations.append({
                        'type': vtype,
                        'content': variation
                    })

            return variations

        except Exception as e:
            logger.error(f"生成变体失败: {str(e)}")
            return []

    async def _generate_variation(
        self,
        base_content: str,
        variation_type: str
    ) -> Optional[str]:
        """
        生成特定类型的变体

        Args:
            base_content: 原始内容
            variation_type: 变体类型

        Returns:
            变体内容
        """
        # 这里应该调用AI服务生成变体
        # 暂时返回简单的处理
        try:
            if variation_type == 'concise':
                # 简化版本：取前70%
                return base_content[:int(len(base_content) * 0.7)]
            elif variation_type == 'extended':
                # 扩展版本（实际应该由AI生成）
                return base_content + "。此外，这个产品还具有独特的文化价值。"
            else:
                return base_content

        except Exception as e:
            logger.error(f"生成 {variation_type} 变体失败: {str(e)}")
            return None
