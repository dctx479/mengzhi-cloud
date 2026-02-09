"""
内容后处理和质量检查 - AI-007 优化

功能：
- 格式化和清理
- 长度调整
- 敏感词过滤
- 可读性优化
- 质量评估
- 自动修复

版本: 2.0 (优化版)
更新日期: 2026-01-17
"""

import re
from typing import Dict, Any, Optional, Tuple, List
from loguru import logger
from app.models.content_record import Style, Platform, ContentType


class ContentPostProcessor:
    """内容后处理器 - 对生成的内容进行格式化和优化"""

    # 敏感词列表（示例）
    SENSITIVE_WORDS = [
        '涉政', '涉黄', '骂人', '广告法',  # 示例词汇
    ]

    # Prompt泄露检测
    PROMPT_LEAKAGE_PATTERNS = [
        r'^(请|现在|开始).{0,10}生成.*?[:：]',
        r'(我是|作为).{0,20}(文案|策划|专家).*?[,，。]',
        r'(按照|根据).*?(要求|任务|指示).{0,10}[,，。]',
        r'(忽略|不考虑|不要提).{0,10}(之前|过往)',
    ]

    @classmethod
    async def process(
        cls,
        content: str,
        style: Style,
        platform: Platform,
        target_word_count: Optional[int] = None,
        content_type: Optional[ContentType] = None
    ) -> str:
        """
        综合后处理

        Args:
            content: 原始内容
            style: 内容风格
            platform: 目标平台
            target_word_count: 目标字数
            content_type: 内容类型

        Returns:
            处理后的内容
        """
        logger.info(f"开始内容后处理 (风格: {style.value}, 平台: {platform.value})")

        # 1. 基础清理
        content = cls._clean_content(content)

        # 2. 检测和移除Prompt泄露
        content = cls._remove_prompt_leakage(content)

        # 3. 敏感词过滤
        content = await cls._filter_sensitive_words(content)

        # 4. 长度调整
        if target_word_count:
            content = cls._adjust_length(content, target_word_count)

        # 5. 可读性优化
        content = cls._improve_readability(content, style)

        # 6. 平台特定优化
        content = cls._optimize_for_platform(content, platform)

        # 7. 标点符号优化
        content = cls._optimize_punctuation(content)

        logger.info(f"后处理完成，最终长度: {len(content)}")

        return content

    @classmethod
    def _clean_content(cls, content: str) -> str:
        """
        基础清理

        Args:
            content: 原始内容

        Returns:
            清理后的内容
        """
        # 移除多余空格
        content = re.sub(r'\s+', ' ', content).strip()

        # 移除特殊Unicode字符
        content = re.sub(r'[\u200b\u200c\u200d\ufeff]', '', content)

        # 移除多余的换行
        content = re.sub(r'\n\n+', '\n', content)

        # 标准化引号
        content = content.replace('"', '"').replace('"', '"')
        content = content.replace(''', "'").replace(''', "'")

        return content

    @classmethod
    def _remove_prompt_leakage(cls, content: str) -> str:
        """
        移除可能的Prompt泄露

        Args:
            content: 原始内容

        Returns:
            清理后的内容
        """
        for pattern in cls.PROMPT_LEAKAGE_PATTERNS:
            content = re.sub(pattern, '', content)

        return content.strip()

    @classmethod
    async def _filter_sensitive_words(cls, content: str) -> str:
        """
        过滤敏感词

        Args:
            content: 原始内容

        Returns:
            过滤后的内容
        """
        # 这里应该集成真实的敏感词库
        # 暂时使用简单的示例

        for word in cls.SENSITIVE_WORDS:
            if word in content:
                # 替换为通用表述
                content = content.replace(word, '[内容优化]')
                logger.warning(f"检测到敏感词: {word}")

        return content

    @classmethod
    def _adjust_length(cls, content: str, target_word_count: int) -> str:
        """
        智能调整长度

        Args:
            content: 原始内容
            target_word_count: 目标字数

        Returns:
            调整后的内容
        """
        current_length = len(content)
        tolerance = target_word_count * 0.15  # 15%容差

        if abs(current_length - target_word_count) <= tolerance:
            return content

        if current_length > target_word_count * 1.2:
            # 过长 - 智能截断
            logger.info(f"内容过长，从 {current_length} 字截断到 {target_word_count} 字")

            # 按句子截断以保持完整性
            sentences = re.split(r'[。！？\n]', content)
            result = []
            current_len = 0

            for sentence in sentences:
                if not sentence.strip():
                    continue

                if current_len + len(sentence) <= target_word_count:
                    result.append(sentence)
                    current_len += len(sentence) + 1  # +1 for punctuation
                else:
                    # 最后一句可能需要截断
                    remaining = target_word_count - current_len
                    if remaining > 20:  # 至少保留20个字
                        result.append(sentence[:remaining])
                    break

            # 重新添加结尾标点
            processed = '。'.join(result)
            if processed and not processed.endswith(('。', '！', '？')):
                processed += '。'

            return processed

        return content

    @classmethod
    def _improve_readability(cls, content: str, style: Style) -> str:
        """
        提升可读性

        Args:
            content: 原始内容
            style: 风格

        Returns:
            优化后的内容
        """
        if style == Style.CASUAL:
            # 轻松风格 - 适当添加表情符号/感叹号
            # 替换一些平淡的词汇
            replacements = {
                '很好': '不错呢',
                '非常好': '超级棒',
                '不错': '还行',
                '可以': '不妨',
                '需要': '想要',
            }

            for old, new in replacements.items():
                content = content.replace(old, new)

        elif style == Style.PROFESSIONAL:
            # 专业风格 - 使用更正式的词汇
            replacements = {
                '很好': '优质',
                '很棒': '出色',
                '不错': '良好',
                '好吃': '美味',
                '舒服': '舒适',
            }

            for old, new in replacements.items():
                content = content.replace(old, new)

        elif style == Style.EMOTIONAL:
            # 情感风格 - 增加情感表达
            replacements = {
                '很好': '极其美妙',
                '喜欢': '深深喜爱',
                '想': '梦想',
                '需要': '渴望',
            }

            for old, new in replacements.items():
                content = content.replace(old, new)

        return content

    @classmethod
    def _optimize_for_platform(cls, content: str, platform: Platform) -> str:
        """
        针对平台优化

        Args:
            content: 原始内容
            platform: 目标平台

        Returns:
            优化后的内容
        """
        if platform == Platform.DOUYIN:
            # 抖音：更短更活泼
            # 添加热门词汇
            if len(content) > 280 and '。' in content:
                sentences = content.split('。')
                content = '。'.join(sentences[:2]) + '。'

            # 添加互动元素
            if '吗？' not in content and '呢？' not in content:
                content = content.rstrip('。') + '，你觉得呢？'

        elif platform == Platform.XIAOHONGSHU:
            # 小红书：强调生活方式和分享感
            content = content.replace('产品', '好物').replace('商品', '宝贝')

        elif platform == Platform.WECHAT:
            # 微信公众号：更学术和可信
            # 可添加链接提示等
            pass

        elif platform == Platform.WEIBO:
            # 微博：简洁、有观点
            if len(content) > 200:
                content = content[:200] + '...'

        return content

    @classmethod
    def _optimize_punctuation(cls, content: str) -> str:
        """
        优化标点符号

        Args:
            content: 原始内容

        Returns:
            优化后的内容
        """
        # 移除多余的标点
        content = re.sub(r'[。！？]{2,}', lambda m: m.group(0)[0], content)

        # 空格和标点的标准化
        content = re.sub(r'\s+[。，！？；：]', lambda m: m.group(0).strip(), content)

        # 确保以正确的标点结尾
        if content and not content.endswith(('。', '！', '？', '"', "'", '"')):
            # 添加适当的结尾标点
            if content.endswith(' '):
                content = content.rstrip() + '。'
            else:
                content = content + '。'

        return content


class QualityAssessment:
    """质量评估 - 对生成内容进行质量评分"""

    # 评估权重
    WEIGHTS = {
        'length': 0.15,  # 长度是否符合
        'completeness': 0.25,  # 内容完整性
        'coherence': 0.20,  # 逻辑连贯性
        'readability': 0.15,  # 可读性
        'cultural_richness': 0.15,  # 文化融入度
        'no_errors': 0.10,  # 无明显错误
    }

    @classmethod
    async def assess_content(
        cls,
        content: str,
        target_word_count: Optional[int] = None,
        content_type: Optional[ContentType] = None,
        platform: Optional[Platform] = None
    ) -> Tuple[float, Dict[str, Any]]:
        """
        综合评估内容质量

        Args:
            content: 内容
            target_word_count: 目标字数
            content_type: 内容类型
            platform: 平台

        Returns:
            (总分 0-1, 详细评分)
        """
        scores = {}

        # 1. 长度评估
        scores['length'] = cls._assess_length(content, target_word_count)

        # 2. 完整性评估
        scores['completeness'] = cls._assess_completeness(content)

        # 3. 连贯性评估
        scores['coherence'] = cls._assess_coherence(content)

        # 4. 可读性评估
        scores['readability'] = cls._assess_readability(content)

        # 5. 文化融入度
        scores['cultural_richness'] = cls._assess_cultural_richness(content)

        # 6. 错误检查
        scores['no_errors'] = cls._assess_error_free(content)

        # 计算加权总分
        total_score = sum(
            scores[key] * cls.WEIGHTS.get(key, 0)
            for key in scores
        )

        return total_score, scores

    @classmethod
    def _assess_length(cls, content: str, target: Optional[int] = None) -> float:
        """评估长度"""
        if target is None:
            # 没有目标长度要求，只检查是否为空
            return 0.8 if content else 0.0

        current_length = len(content)
        tolerance_low = target * 0.85
        tolerance_high = target * 1.15

        if tolerance_low <= current_length <= tolerance_high:
            return 1.0

        # 根据偏差程度扣分
        if current_length < tolerance_low:
            return max(0.4, 1.0 - (tolerance_low - current_length) / target)
        else:
            return max(0.4, 1.0 - (current_length - tolerance_high) / target)

    @classmethod
    def _assess_completeness(cls, content: str) -> float:
        """评估完整性 - 检查是否有开头、正文、结尾"""
        if not content:
            return 0.0

        score = 0.5  # 基础分

        # 检查是否有适当的开头
        if len(content) > 10:
            score += 0.2

        # 检查是否有结尾标点
        if content.rstrip().endswith(('。', '！', '？')):
            score += 0.2

        # 检查内容丰富度（多个句子）
        sentence_count = len(re.split(r'[。！？\n]', content)) - 1
        if sentence_count >= 2:
            score += 0.1

        return min(1.0, score)

    @classmethod
    def _assess_coherence(cls, content: str) -> float:
        """评估逻辑连贯性"""
        if not content:
            return 0.0

        # 简单的启发式方法
        score = 0.6  # 基础分

        # 检查是否有逻辑连接词
        logical_connectors = ['因此', '所以', '但是', '而且', '虽然', '然而', '此外', '接着']
        has_connectors = any(conn in content for conn in logical_connectors)

        if has_connectors or len(content) < 200:
            score += 0.2

        # 检查重复词汇过多
        words = re.findall(r'[\u4e00-\u9fff]+', content)
        if len(words) > 10:
            unique_words = len(set(words))
            word_diversity = unique_words / len(words)
            score += 0.2 * word_diversity

        return min(1.0, score)

    @classmethod
    def _assess_readability(cls, content: str) -> float:
        """评估可读性"""
        if not content:
            return 0.0

        score = 0.5

        # 段落长度不过长
        lines = content.split('\n')
        avg_line_length = sum(len(line) for line in lines) / len(lines) if lines else 0

        if avg_line_length < 100:
            score += 0.25
        elif avg_line_length < 150:
            score += 0.15

        # 使用了排版
        if '\n' in content or '、' in content:
            score += 0.25

        return min(1.0, score)

    @classmethod
    def _assess_cultural_richness(cls, content: str) -> float:
        """评估文化融入度"""
        # 检查是否包含文化相关词汇
        cultural_keywords = [
            '文化', '传统', '民族', '历史', '故事', '工艺',
            '蒙古', '内蒙', '草原', '游牧', '手工', '非遗',
            '习俗', '节日', '传承', '工艺', '底蕴'
        ]

        score = 0.3
        keyword_count = sum(1 for kw in cultural_keywords if kw in content)

        if keyword_count >= 3:
            score += 0.4
        elif keyword_count >= 1:
            score += 0.2

        return min(1.0, score)

    @classmethod
    def _assess_error_free(cls, content: str) -> float:
        """评估无错误程度"""
        score = 1.0

        # 检查明显的错误
        error_patterns = [
            r'[\u4e00-\u9fff]{1,3}[a-zA-Z]{2,}',  # 中英混乱
            r'[^。！？\n]\s{3,}[^。！？\n]',  # 多余空格
        ]

        for pattern in error_patterns:
            if re.search(pattern, content):
                score -= 0.1

        return max(0.5, score)
