"""
Prompt模板管理API接口

支持：
- 获取可用模板列表
- 验证和渲染Prompt
- 获取文化关键词
- 获取模板示例

版本: 2.0
更新日期: 2026-01-17
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel, Field
from typing import Dict, Any, Optional, List
from enum import Enum

# 导入服务
from app.services.ai.prompt_manager import PromptTemplateManager, PromptContextBuilder


# ==================== Pydantic模型 ====================

class TemplateListResponse(BaseModel):
    """模板列表响应"""
    templates: List[Dict[str, Any]]
    total: int


class PromptRenderRequest(BaseModel):
    """Prompt渲染请求"""
    template_type: str = Field(..., description="模板类型，如: product_copy, slogan等")
    style: Optional[str] = Field(None, description="模板风格（可选）")
    context: Dict[str, Any] = Field(..., description="渲染上下文参数")

    class Config:
        json_schema_extra = {
            "example": {
                "template_type": "product_copy",
                "style": "professional",
                "context": {
                    "product_name": "内蒙古有机黄油",
                    "category": "乳制品",
                    "origin": "内蒙古鄂尔多斯",
                    "features": "有机认证、无添加、天然黄油",
                    "cultural_background": "源自传统游牧民族工艺",
                    "certifications": "有机认证、地理标志",
                    "target_audience_description": "高端消费者，注重品质",
                    "word_count": "300-400"
                }
            }
        }


class PromptRenderResponse(BaseModel):
    """Prompt渲染响应"""
    success: bool
    prompt: Optional[str] = Field(None, description="生成的Prompt")
    error: Optional[str] = Field(None, description="错误信息")
    validation_warnings: Optional[List[str]] = Field(None, description="验证警告")


class ContextValidationRequest(BaseModel):
    """上下文验证请求"""
    template_type: str
    context: Dict[str, Any]


class ContextValidationResponse(BaseModel):
    """上下文验证响应"""
    is_valid: bool
    missing_fields: List[str]
    message: str


class CulturalKeywordsRequest(BaseModel):
    """获取文化关键词请求"""
    category: str = Field("all", description="分类: grassland/nomadic/quality_indicators/emotion_words/all")


class CulturalKeywordsResponse(BaseModel):
    """获取文化关键词响应"""
    keywords: Dict[str, Any]


class TemplateExampleRequest(BaseModel):
    """获取模板示例请求"""
    template_type: str
    style: Optional[str] = None


class TemplateExampleResponse(BaseModel):
    """获取模板示例响应"""
    template_type: str
    style: Optional[str]
    example_context: Dict[str, Any]
    expected_output_description: str


class ProductCopySuggestionRequest(BaseModel):
    """产品文案生成快速请求"""
    product_name: str = Field(..., description="产品名称")
    category: str = Field(..., description="产品分类")
    key_features: List[str] = Field(..., description="核心卖点列表")
    target_segment: str = Field(..., description="目标市场段")
    style: str = Field("professional", description="文案风格")
    word_count: int = Field(300, description="目标字数")


class SloganSuggestionRequest(BaseModel):
    """广告语快速生成请求"""
    product_name: str
    key_feature: str
    count: int = Field(5, description="生成数量")
    style: str = Field("creative", description="风格")


# ==================== 路由 ====================

router = APIRouter(
    prefix="/api/v1/prompts",
    tags=["Prompt Management"],
    responses={404: {"description": "Not found"}}
)


def get_template_manager() -> PromptTemplateManager:
    """依赖注入：获取模板管理器实例"""
    return PromptTemplateManager()


@router.get(
    "/templates",
    response_model=TemplateListResponse,
    summary="获取所有可用模板列表",
    description="返回所有可用的Prompt模板及其基本信息"
)
async def list_templates(
    manager: PromptTemplateManager = Depends(get_template_manager)
):
    """获取所有可用的Prompt模板"""
    try:
        result = manager.list_available_templates()
        return TemplateListResponse(**result)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"获取模板列表失败: {str(e)}"
        )


@router.post(
    "/render",
    response_model=PromptRenderResponse,
    summary="渲染Prompt模板",
    description="使用提供的参数渲染指定的Prompt模板"
)
async def render_prompt(
    request: PromptRenderRequest,
    manager: PromptTemplateManager = Depends(get_template_manager)
):
    """渲染Prompt模板"""
    try:
        # 验证上下文
        is_valid, missing_fields, message = manager.validate_context(
            request.template_type,
            request.context
        )

        if not is_valid:
            # 如果缺少字段，返回详细的错误信息
            return PromptRenderResponse(
                success=False,
                error=f"上下文验证失败: {message}",
                validation_warnings=missing_fields
            )

        # 渲染模板
        prompt = manager.render_prompt(
            template_type=request.template_type,
            style=request.style,
            context=request.context
        )

        return PromptRenderResponse(
            success=True,
            prompt=prompt
        )

    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"模板渲染失败: {str(e)}"
        )


@router.post(
    "/validate",
    response_model=ContextValidationResponse,
    summary="验证上下文完整性",
    description="检查提供的上下文是否包含所有必需字段"
)
async def validate_context(
    request: ContextValidationRequest,
    manager: PromptTemplateManager = Depends(get_template_manager)
):
    """验证上下文是否完整"""
    try:
        is_valid, missing_fields, message = manager.validate_context(
            request.template_type,
            request.context
        )

        return ContextValidationResponse(
            is_valid=is_valid,
            missing_fields=missing_fields,
            message=message
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )


@router.get(
    "/cultural-keywords",
    response_model=CulturalKeywordsResponse,
    summary="获取内蒙古文化关键词",
    description="获取用于文案创作的内蒙古文化相关关键词"
)
async def get_cultural_keywords(
    category: str = Query("all", description="分类"),
    manager: PromptTemplateManager = Depends(get_template_manager)
):
    """获取文化关键词"""
    try:
        keywords = manager.get_cultural_keywords(category)
        return CulturalKeywordsResponse(keywords=keywords)
    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )


@router.post(
    "/examples",
    response_model=TemplateExampleResponse,
    summary="获取模板使用示例",
    description="获取指定模板的使用示例和参考输出"
)
async def get_template_example(
    request: TemplateExampleRequest,
    manager: PromptTemplateManager = Depends(get_template_manager)
):
    """获取模板示例"""
    try:
        example = manager.get_template_example(
            request.template_type,
            request.style
        )

        return TemplateExampleResponse(
            template_type=request.template_type,
            style=request.style,
            example_context=example.get('context', {}),
            expected_output_description=example.get('expected_output', '')
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )


@router.post(
    "/product-copy/quick",
    response_model=PromptRenderResponse,
    summary="快速生成产品文案Prompt",
    description="使用简化的参数快速生成产品文案Prompt"
)
async def quick_product_copy(
    request: ProductCopySuggestionRequest,
    manager: PromptTemplateManager = Depends(get_template_manager)
):
    """快速生成产品文案"""
    try:
        # 构建完整的上下文
        context = PromptContextBuilder.build_product_copy_context(
            product_name=request.product_name,
            category=request.category,
            origin="内蒙古",
            features=", ".join(request.key_features),
            cultural_background="内蒙古特色产品",
            target_audience=f"目标市场: {request.target_segment}",
            word_count=request.word_count
        )

        # 渲染模板
        prompt = manager.render_prompt(
            template_type='product_copy',
            style=request.style,
            context=context
        )

        return PromptRenderResponse(
            success=True,
            prompt=prompt
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )


@router.post(
    "/slogan/quick",
    response_model=PromptRenderResponse,
    summary="快速生成广告语Prompt",
    description="使用简化的参数快速生成广告语Prompt"
)
async def quick_slogan(
    request: SloganSuggestionRequest,
    manager: PromptTemplateManager = Depends(get_template_manager)
):
    """快速生成广告语"""
    try:
        # 构建上下文
        context = PromptContextBuilder.build_slogan_context(
            product_name=request.product_name,
            count=request.count,
            style=request.style,
            key_features=request.key_feature,
            cultural_tags=['内蒙古', '正宗', '品质'],
            target_audience='所有消费者',
            brand_tone='品质、信任',
            emotion_trigger='品质、信任'
        )

        # 渲染模板
        prompt = manager.render_prompt(
            template_type='slogan',
            context=context
        )

        return PromptRenderResponse(
            success=True,
            prompt=prompt
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )


@router.get(
    "/templates/{template_type}",
    summary="获取特定模板类型的详细信息",
    description="获取指定模板类型的所有可用风格和信息"
)
async def get_template_details(
    template_type: str,
    manager: PromptTemplateManager = Depends(get_template_manager)
):
    """获取特定模板的详细信息"""
    try:
        templates = manager.list_available_templates()
        matching = [t for t in templates['templates'] if t['type'] == template_type]

        if not matching:
            raise HTTPException(
                status_code=404,
                detail=f"模板类型 '{template_type}' 不存在"
            )

        return {
            "template_type": template_type,
            "variants": matching,
            "count": len(matching)
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )


@router.get(
    "/health",
    summary="健康检查",
    description="检查Prompt服务的可用性"
)
async def health_check(
    manager: PromptTemplateManager = Depends(get_template_manager)
):
    """健康检查"""
    try:
        templates = manager.list_available_templates()
        return {
            "status": "healthy",
            "available_templates": templates['total'],
            "message": "Prompt服务正常运行"
        }
    except Exception as e:
        raise HTTPException(
            status_code=503,
            detail=f"服务不可用: {str(e)}"
        )


# 路由导出
__all__ = ['router']
