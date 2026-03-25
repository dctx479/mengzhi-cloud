"""
Prompt模板 - AI对话系统提示词

版本: 1.0
更新日期: 2026-01-17
"""


class PromptTemplates:
    """提示词模板集合"""

    # 系统角色定义
    SYSTEM_PROMPT = """你是一个专业的农畜产品营销顾问助手，名叫"小数"。你代表内蒙古农畜产品AI赋能云平台为用户提供服务。

你的核心职责：
1. 提供农畜产品品牌营销咨询
2. 帮助企业分析市场机遇
3. 制定数字化营销策略
4. 推荐产品销售渠道
5. 协助完成商务对接

你的特点：
- 专业且友好，用语规范
- 深入理解内蒙古农畜产品特色
- 了解最新的数字营销趋势
- 提供基于数据的建议
- 保持高效的沟通风格

在回答时：
- 逻辑清晰，分点阐述
- 提供具体案例和数据支持
- 根据用户需求深入分析
- 必要时提出后续建议"""

    # 知识库注入模板
    KNOWLEDGE_INJECT = """
根据以下产品信息提供咨询：

【产品信息】
{product_info}

【市场数据】
{market_data}

【行业趋势】
{industry_trends}

请基于上述信息回答用户的问题。
"""

    # 对话上下文模板
    CONTEXT_TEMPLATE = """【对话背景】
用户ID: {user_id}
对话主题: {topic}
之前讨论过的内容摘要: {summary}

基于以上背景，继续为用户提供服务。"""

    # 分析报告生成模板
    ANALYSIS_PROMPT = """请生成一份专业的分析报告，内容包括：

1. 现状分析
   - 目标市场状况
   - 竞争格局
   - 机遇与挑战

2. 策略建议
   - 核心定位
   - 营销策略
   - 渠道选择

3. 实施计划
   - 阶段性目标
   - 执行步骤
   - 关键指标

请使用专业的商务语言，数据支持，逻辑严谨。"""

    # 品牌定位咨询模板
    BRAND_POSITIONING = """请帮助分析品牌定位：

【企业信息】
企业名称: {company_name}
产品类型: {product_type}
目标市场: {target_market}
核心优势: {advantages}

请提供：
1. 市场定位分析
2. 目标消费者画像
3. 品牌价值主张
4. 竞争差异化策略
5. 品牌传播建议"""

    # 渠道推荐模板
    CHANNEL_RECOMMENDATION = """请推荐最适合的销售渠道：

【产品信息】
产品名称: {product_name}
产品特点: {product_features}
目标客户: {target_customers}
销售预算: {budget}

分析维度：
1. 各渠道适配度评分
2. 渠道成本-收益分析
3. 实施难度评估
4. 时间周期预估
5. 风险识别
6. 综合推荐方案"""

    # 营销策略制定模板
    MARKETING_STRATEGY = """请制定营销策略方案：

【背景信息】
企业现状: {company_status}
产品优势: {product_advantages}
竞争环境: {competition}
目标销售额: {target_revenue}
执行周期: {timeline}

策略内容：
1. 目标客户定位
2. 核心卖点提炼
3. 营销渠道组合
4. 推广方案详细
5. 预算分配建议
6. 效果评估指标"""

    # 用户问题分类提示词
    CLASSIFY_QUESTION = """请分析用户的问题类型。

问题: {question}

可能的分类：
- 品牌咨询
- 渠道推荐
- 营销策略
- 市场分析
- 产品定位
- 成功案例
- 其他咨询

请返回分类结果和置信度（0-1）。"""

    @staticmethod
    def _sanitize_input(text: str, max_length: int = 1000) -> str:
        """
        SECURITY FIX: Sanitize user input to prevent prompt injection.
        
        Prevents attackers from breaking out of template placeholders by:
        1. Truncating overly long inputs
        2. Escaping special characters that could break template formatting
        
        Args:
            text: Input text to sanitize
            max_length: Maximum allowed length (default 1000 chars)
            
        Returns:
            Sanitized text safe for template insertion
        """
        if not isinstance(text, str):
            text = str(text)
        
        # Truncate to max length to prevent injection attacks
        text = text[:max_length]
        
        # Escape curly braces which can be used for prompt injection
        # by breaking out of format placeholders
        text = text.replace('{', '{{').replace('}', '}}')
        
        return text

    @staticmethod
    def get_system_prompt(role: str = "assistant") -> str:
        """
        获取系统提示词

        Args:
            role: 角色类型，目前支持 'assistant'

        Returns:
            系统提示词
        """
        if role == "assistant":
            return PromptTemplates.SYSTEM_PROMPT
        return PromptTemplates.SYSTEM_PROMPT

    @staticmethod
    def inject_knowledge(product_info: str, market_data: str = "", industry_trends: str = "") -> str:
        """
        注入知识到提示词

        Args:
            product_info: 产品信息
            market_data: 市场数据
            industry_trends: 行业趋势

        Returns:
            包含知识的完整提示词
        """
        # SECURITY FIX: Sanitize all user inputs before template formatting
        return PromptTemplates.KNOWLEDGE_INJECT.format(
            product_info=PromptTemplates._sanitize_input(product_info),
            market_data=PromptTemplates._sanitize_input(market_data or "暂无具体数据"),
            industry_trends=PromptTemplates._sanitize_input(industry_trends or "暂无具体数据")
        )

    @staticmethod
    def build_context_aware_prompt(user_id: str, topic: str = "", summary: str = "") -> str:
        """
        构建上下文感知的提示词

        Args:
            user_id: 用户ID
            topic: 对话主题
            summary: 之前讨论内容摘要

        Returns:
            上下文感知的提示词
        """
        # SECURITY FIX: Sanitize all user inputs before template formatting
        return PromptTemplates.CONTEXT_TEMPLATE.format(
            user_id=PromptTemplates._sanitize_input(user_id),
            topic=PromptTemplates._sanitize_input(topic or "营销咨询"),
            summary=PromptTemplates._sanitize_input(summary or "这是第一条消息")
        )

    @staticmethod
    def generate_analysis_prompt() -> str:
        """生成分析报告提示词"""
        return PromptTemplates.ANALYSIS_PROMPT

    @staticmethod
    def brand_positioning_prompt(
        company_name: str,
        product_type: str,
        target_market: str,
        advantages: str
    ) -> str:
        """生成品牌定位咨询提示词"""
        # SECURITY FIX: Sanitize all user inputs before template formatting
        return PromptTemplates.BRAND_POSITIONING.format(
            company_name=PromptTemplates._sanitize_input(company_name),
            product_type=PromptTemplates._sanitize_input(product_type),
            target_market=PromptTemplates._sanitize_input(target_market),
            advantages=PromptTemplates._sanitize_input(advantages)
        )

    @staticmethod
    def channel_recommendation_prompt(
        product_name: str,
        product_features: str,
        target_customers: str,
        budget: str
    ) -> str:
        """生成渠道推荐提示词"""
        # SECURITY FIX: Sanitize all user inputs before template formatting
        return PromptTemplates.CHANNEL_RECOMMENDATION.format(
            product_name=PromptTemplates._sanitize_input(product_name),
            product_features=PromptTemplates._sanitize_input(product_features),
            target_customers=PromptTemplates._sanitize_input(target_customers),
            budget=PromptTemplates._sanitize_input(budget)
        )

    @staticmethod
    def marketing_strategy_prompt(
        company_status: str,
        product_advantages: str,
        competition: str,
        target_revenue: str,
        timeline: str
    ) -> str:
        """生成营销策略提示词"""
        # SECURITY FIX: Sanitize all user inputs before template formatting
        return PromptTemplates.MARKETING_STRATEGY.format(
            company_status=PromptTemplates._sanitize_input(company_status),
            product_advantages=PromptTemplates._sanitize_input(product_advantages),
            competition=PromptTemplates._sanitize_input(competition),
            target_revenue=PromptTemplates._sanitize_input(target_revenue),
            timeline=PromptTemplates._sanitize_input(timeline)
        )
