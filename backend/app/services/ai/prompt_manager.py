"""
Prompt模板管理系统 - 模板渲染和管理

版本: 2.0
更新日期: 2026-01-17
"""

from typing import Dict, Any, Optional, List
from jinja2 import Template, TemplateError
from dataclasses import asdict
from optimized_prompt_templates import OptimizedPromptTemplates, CulturalContext, CopyStyle


class PromptTemplateManager:
    """Prompt模板管理器，负责模板渲染、验证和管理"""

    def __init__(self):
        self.templates: Dict[str, Dict[str, str]] = {
            'product_copy': {
                CopyStyle.PROFESSIONAL.value: OptimizedPromptTemplates.PRODUCT_COPY_PROFESSIONAL,
                CopyStyle.CASUAL.value: OptimizedPromptTemplates.PRODUCT_COPY_CASUAL,
                CopyStyle.EMOTIONAL.value: OptimizedPromptTemplates.PRODUCT_COPY_EMOTIONAL,
                CopyStyle.CREATIVE.value: OptimizedPromptTemplates.PRODUCT_COPY_CREATIVE,
            },
            'slogan': OptimizedPromptTemplates.SLOGAN_GENERATION,
            'xiaohongshu': OptimizedPromptTemplates.XIAOHONGSHU_COPY,
            'douyin': OptimizedPromptTemplates.DOUYIN_COPY,
            'weibo': OptimizedPromptTemplates.WEIBO_COPY,
            'short_video_script': OptimizedPromptTemplates.SHORT_VIDEO_SCRIPT,
            'marketing_strategy': OptimizedPromptTemplates.MARKETING_STRATEGY_COMPREHENSIVE,
        }
        self.cultural_context = OptimizedPromptTemplates.get_cultural_context()

    def render_prompt(self, template_type: str, style: Optional[str] = None, context: Dict[str, Any] = None) -> str:
        """
        渲染Prompt模板

        Args:
            template_type: 模板类型（product_copy, slogan, xiaohongshu等）
            style: 风格（当模板类型支持多个风格时）
            context: 渲染上下文参数字典

        Returns:
            渲染后的Prompt

        Raises:
            ValueError: 模板不存在或参数不完整
            TemplateError: 模板渲染失败
        """
        if not context:
            context = {}

        # 获取模板内容
        template_content = self._get_template_content(template_type, style)

        # 渲染模板
        try:
            rendered = OptimizedPromptTemplates.render_template(template_content, **context)
            return rendered
        except KeyError as e:
            missing_field = str(e).strip("'")
            raise ValueError(
                f"模板渲染失败: 缺少必需参数 '{missing_field}'。"
                f"请提供完整的上下文参数。"
            )
        except Exception as e:
            raise TemplateError(f"模板渲染出错: {str(e)}")

    def _get_template_content(self, template_type: str, style: Optional[str] = None) -> str:
        """获取指定类型和风格的模板内容"""
        if template_type not in self.templates:
            raise ValueError(f"未知的模板类型: {template_type}")

        if isinstance(self.templates[template_type], dict):
            # 有多个风格的模板
            if not style:
                raise ValueError(f"模板类型 '{template_type}' 需要指定style参数")
            if style not in self.templates[template_type]:
                raise ValueError(f"模板类型 '{template_type}' 不支持风格: {style}")
            return self.templates[template_type][style]
        else:
            # 单个模板
            return self.templates[template_type]

    def list_available_templates(self) -> Dict[str, Any]:
        """列出所有可用的模板"""
        result = {
            'templates': [],
            'total': 0
        }

        for template_type, template_content in self.templates.items():
            if isinstance(template_content, dict):
                # 有多个风格
                for style in template_content.keys():
                    result['templates'].append({
                        'type': template_type,
                        'style': style,
                        'name': f"{template_type}_{style}",
                        'description': self._get_template_description(template_type, style)
                    })
            else:
                # 单个模板
                result['templates'].append({
                    'type': template_type,
                    'style': None,
                    'name': template_type,
                    'description': self._get_template_description(template_type)
                })

        result['total'] = len(result['templates'])
        return result

    def _get_template_description(self, template_type: str, style: Optional[str] = None) -> str:
        """获取模板描述"""
        descriptions = {
            'product_copy': {
                'professional': '专业权威风格的产品文案，适合高端市场和官方渠道',
                'casual': '亲切友好风格，强调真实感和代入感，适合社交媒体',
                'emotional': '情感共鸣风格，通过故事化叙述建立品牌连接',
                'creative': '创意新颖风格，打破常规表达，突出产品独特性',
            },
            'slogan': '广告语生成模板，支持多种风格和创意角度',
            'xiaohongshu': '小红书种草笔记模板，强调真实体验和社区气氛',
            'douyin': '抖音短视频文案模板，快速吸引和传播',
            'weibo': '微博内容模板，强调话题和互动',
            'short_video_script': '短视频完整脚本模板，包含视觉、文案、音效等',
            'marketing_strategy': '完整的营销方案模板，从策略到执行'
        }

        if style:
            return descriptions.get(template_type, {}).get(style, '模板')
        else:
            return descriptions.get(template_type, '模板')

    def get_cultural_keywords(self, category: str = 'all') -> Dict[str, List[str]]:
        """获取内蒙古文化关键词

        Args:
            category: 分类（grassland/nomadic/quality_indicators/emotion_words/all）

        Returns:
            相应类别的关键词列表
        """
        context = self.cultural_context

        if category == 'grassland':
            return {'grassland': context.grassland_elements}
        elif category == 'nomadic':
            return {'nomadic': context.nomadic_tradition}
        elif category == 'quality_indicators':
            return {'quality_indicators': context.quality_indicators}
        elif category == 'emotion_words':
            return context.emotion_words
        elif category == 'all':
            return {
                'grassland': context.grassland_elements,
                'nomadic': context.nomadic_tradition,
                'quality_indicators': context.quality_indicators,
                'emotion_words': context.emotion_words
            }
        else:
            raise ValueError(f"未知的分类: {category}")

    def validate_context(self, template_type: str, context: Dict[str, Any]) -> tuple:
        """
        验证提供的上下文是否完整

        Args:
            template_type: 模板类型
            context: 提供的上下文

        Returns:
            (is_valid, missing_fields, error_message)
        """
        # 定义各类型模板的必需字段
        required_fields = {
            'product_copy': [
                'product_name', 'category', 'origin', 'features',
                'cultural_background', 'certifications', 'target_audience_description', 'word_count'
            ],
            'slogan': [
                'product_name', 'key_features', 'cultural_tags', 'target_audience',
                'brand_tone', 'count', 'style', 'emotion_trigger'
            ],
            'xiaohongshu': ['product_name', 'product_info', 'target_audience', 'product_category'],
            'douyin': ['product_name', 'product_info'],
            'weibo': ['product_name', 'product_info'],
            'short_video_script': [
                'product_name', 'duration', 'product_details',
                'visual_hook', 'text_hook', 'problem_visual', 'problem_text',
                'solution_visual', 'solution_text', 'trust_visual', 'trust_text',
                'cta_visual', 'cta_text'
            ],
            'marketing_strategy': [
                'product_name', 'channel', 'duration', 'product_details',
                'target_market', 'competition_analysis'
            ]
        }

        if template_type not in required_fields:
            return False, [], f"未知的模板类型: {template_type}"

        missing = [f for f in required_fields[template_type] if f not in context or not context[f]]

        if missing:
            return False, missing, f"缺少必需字段: {', '.join(missing)}"

        return True, [], "验证成功"

    def get_template_example(self, template_type: str, style: Optional[str] = None) -> Dict[str, Any]:
        """获取模板的使用示例

        Args:
            template_type: 模板类型
            style: 风格（可选）

        Returns:
            包含示例上下文和输出的字典
        """
        examples = {
            'product_copy': {
                'professional': {
                    'context': {
                        'product_name': '内蒙古有机黄油',
                        'category': '乳制品',
                        'origin': '内蒙古鄂尔多斯',
                        'features': '有机认证、无添加、天然黄油、富含营养',
                        'cultural_background': '源自传统游牧民族工艺，传承千年制作技艺',
                        'certifications': '有机认证、地理标志产品',
                        'special_process': '传统手工制作、低温工艺、无防腐剂',
                        'target_audience_description': '30-50岁高收入消费者，注重生活品质和健康，重视产品认证和来源',
                        'word_count': '300-500',
                        'example_output': '高端黄油的文案范例...'
                    },
                    'expected_output': '一段300-500字的专业权威风格的产品介绍...'
                },
                'casual': {
                    'context': {
                        'product_name': '内蒙古新鲜牛奶',
                        'category': '乳制品',
                        'origin': '呼和浩特',
                        'features': '鲜牛奶、营养丰富、顺滑口感、早上采集',
                        'cultural_background': '草原牧场的新鲜选择',
                        'target_audience_description': '20-40岁家庭主妇和健康消费者，关注食品安全和营养',
                        'word_count': '200-300',
                        'example_output': '亲切真实的文案范例...'
                    },
                    'expected_output': '一段200-300字的亲切友好风格的文案...'
                }
            },
            'slogan': {
                'context': {
                    'product_name': '内蒙古羊肉',
                    'count': 5,
                    'style': 'cultural',
                    'key_features': '天然草饲、肉质鲜嫩、无膻味、营养丰富',
                    'cultural_tags': '["草原", "游牧", "地理标志", "天然", "正宗"]',
                    'target_audience': '高端消费者、美食爱好者、家庭购买者',
                    'brand_tone': '品质、传统、现代、信任',
                    'differentiation': '与普通羊肉相比更嫩、更鲜、更健康',
                    'emotion_trigger': '品质、信任、健康'
                },
                'expected_output': '5条8-15字的文化风格广告语...'
            }
        }

        key = template_type if not style else f"{template_type}_{style}"
        if key in examples:
            return examples[key]
        else:
            return {'context': {}, 'expected_output': '暂无示例'}


class PromptContextBuilder:
    """Prompt上下文构建器，帮助生成完整的渲染上下文"""

    @staticmethod
    def build_product_copy_context(
        product_name: str,
        category: str,
        origin: str,
        features: str,
        cultural_background: str,
        certifications: str = '',
        special_process: str = '',
        target_audience: str = '',
        word_count: int = 300,
        brand_story: str = '',
        custom_fields: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """构建产品文案的上下文"""
        context = {
            'product_name': product_name,
            'category': category,
            'origin': origin,
            'features': features,
            'cultural_background': cultural_background,
            'certifications': certifications,
            'special_process': special_process,
            'target_audience_description': target_audience,
            'word_count': f"{word_count-word_count//10}-{word_count+word_count//10}",
            'brand_story': brand_story,
            'example_output': ''
        }

        if custom_fields:
            context.update(custom_fields)

        return context

    @staticmethod
    def build_slogan_context(
        product_name: str,
        count: int = 5,
        style: str = 'creative',
        key_features: str = '',
        cultural_tags: List[str] = None,
        target_audience: str = '',
        brand_tone: str = '',
        differentiation: str = '',
        emotion_trigger: str = '品质、信任',
        custom_fields: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """构建广告语的上下文"""
        context = {
            'product_name': product_name,
            'count': count,
            'style': style,
            'key_features': key_features,
            'cultural_tags': ', '.join(cultural_tags) if cultural_tags else '',
            'target_audience': target_audience,
            'brand_tone': brand_tone,
            'differentiation': differentiation,
            'emotion_trigger': emotion_trigger,
            'style_specific_requirements': PromptContextBuilder._get_style_requirements(style)
        }

        if custom_fields:
            context.update(custom_fields)

        return context

    @staticmethod
    def _get_style_requirements(style: str) -> str:
        """获取特定风格的要求说明"""
        requirements = {
            'classic': '采用四字成语、对仗结构，体现传统文化底蕴和气势恢宏',
            'modern': '简洁有力，融入现代消费理念，强调品质和生活方式',
            'cultural': '深度融入内蒙古特色元素，表现地域文化特征和民族特性',
            'emotional': '触发深层情感共鸣，强调品牌与消费者的精神连接'
        }
        return requirements.get(style, '')


# 使用示例代码
if __name__ == '__main__':
    # 初始化模板管理器
    manager = PromptTemplateManager()

    # 列出所有可用模板
    templates = manager.list_available_templates()
    print(f"可用模板总数: {templates['total']}")

    # 生成专业产品文案
    product_context = PromptContextBuilder.build_product_copy_context(
        product_name='内蒙古有机黄油',
        category='乳制品',
        origin='内蒙古鄂尔多斯',
        features='有机认证、无添加、天然黄油',
        cultural_background='源自传统游牧民族工艺',
        certifications='有机认证、地理标志',
        target_audience='高端消费者，注重品质和健康',
        word_count=300
    )

    # 验证上下文
    is_valid, missing, message = manager.validate_context('product_copy', product_context)
    print(f"上下文验证: {message}")

    # 渲染Prompt
    if is_valid:
        prompt = manager.render_prompt('product_copy', style='professional', context=product_context)
        print("\n=== 生成的Prompt ===")
        print(prompt[:500] + "...")

    # 获取文化关键词
    keywords = manager.get_cultural_keywords('grassland')
    print(f"\n草原文化关键词: {keywords['grassland']}")
