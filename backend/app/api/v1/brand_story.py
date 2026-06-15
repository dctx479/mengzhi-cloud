"""
品牌故事生成API端点

提供品牌故事生成服务的REST API

版本: 1.0
创建日期: 2026-06-12
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field
import logging

from app.api.deps import get_db, get_current_user
from app.models.user import User
from app.models.content_record import ContentRecord, ContentType, Platform, Style, LengthType, RecordStatus
from app.services.brand_story.generator import BrandStoryGenerator

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/brand-story", tags=["品牌故事 - Brand Story"])


# =============================================================================
# Request/Response Models
# =============================================================================


class BrandStoryGenerateRequest(BaseModel):
    """品牌故事生成请求"""

    product_name: str = Field(..., description="产品名称", min_length=1, max_length=100)
    origin: str = Field(..., description="产地", min_length=1, max_length=100)
    features: str = Field(default="", description="产品特点", max_length=500)
    purpose: str = Field(default="电商详情页", description="使用场景", max_length=50)
    style: str = Field(default="现代简约", description="故事风格（现代简约/传统深沉/情感共鸣）")
    word_count: str = Field(default="300字左右", description="字数要求")
    category: str = Field(default="", description="产品类别", max_length=50)
    keywords: List[str] = Field(default_factory=list, description="关键词列表")
    use_culture: bool = Field(default=True, description="是否使用文化元素")
    product_id: Optional[int] = Field(default=None, description="关联的产品ID")
    save_record: bool = Field(default=True, description="是否保存生成记录")
    auto_generate_image: bool = Field(default=False, description="是否自动生成即梦AI配图")


class BrandStoryGenerateResponse(BaseModel):
    """品牌故事生成响应"""

    story: str = Field(..., description="生成的品牌故事")
    cultural_elements: List[Dict[str, Any]] = Field(default_factory=list, description="使用的文化元素")
    tokens: Dict[str, int] = Field(..., description="Token使用统计")
    cost: float = Field(..., description="成本（元）")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="元数据")
    record_id: Optional[int] = Field(default=None, description="记录ID（如果保存）")
    image_url: Optional[str] = Field(default=None, description="即梦AI生成的配图URL")


class BrandStoryRecordResponse(BaseModel):
    """品牌故事记录响应"""

    id: int
    product_name: str
    origin: str
    style: str
    story: str
    cultural_elements: List[Dict]
    tokens_used: int
    cost: float
    created_at: str
    status: str


# =============================================================================
# API Endpoints
# =============================================================================


@router.post("/generate", response_model=BrandStoryGenerateResponse, summary="生成品牌故事")
async def generate_brand_story(
    request: BrandStoryGenerateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    生成品牌故事

    根据产品信息和要求，生成定制化品牌故事。

    **风格选项**:
    - 现代简约: 200-300字，节奏快，画面感强
    - 传统深沉: 400-600字，文化底蕴深，叙事完整
    - 情感共鸣: 300-400字，触发回忆，引发共鸣

    **支持功能**:
    - 自动匹配文化元素（知识图谱）
    - 记录生成历史
    - Token和成本统计
    """
    try:
        # 创建生成器
        generator = BrandStoryGenerator(db)

        # 生成品牌故事
        result = await generator.generate_story(
            product_name=request.product_name,
            origin=request.origin,
            features=request.features,
            purpose=request.purpose,
            style=request.style,
            word_count=request.word_count,
            category=request.category,
            keywords=request.keywords,
            use_culture=request.use_culture,
            auto_generate_image=request.auto_generate_image,
        )

        # 保存记录（如果需要）
        record_id = None
        if request.save_record:
            user_obj = db.query(User).filter(User.user_uuid == current_user.get("user_id")).first()
            if user_obj:
                record_id = _save_generation_record(db, user_obj.id, request, result)

        return BrandStoryGenerateResponse(
            story=result["story"],
            cultural_elements=result["cultural_elements"],
            tokens=result["tokens"],
            cost=result["cost"],
            metadata=result["metadata"],
            record_id=record_id,
            image_url=result.get("image_url"),
        )

    except Exception as e:
        logger.error(f"Failed to generate brand story: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"品牌故事生成失败: {str(e)}",
        )


@router.get("/records", response_model=List[BrandStoryRecordResponse], summary="查询生成记录")
def get_brand_story_records(
    skip: int = 0,
    limit: int = 20,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    查询用户的品牌故事生成记录

    支持分页查询。
    """
    try:
        user_obj = db.query(User).filter(User.user_uuid == current_user.get("user_id")).first()
        if not user_obj:
            return []
        records = (
            db.query(ContentRecord)
            .filter(
                ContentRecord.user_id == user_obj.id,
                ContentRecord.content_type == ContentType.STORY,
            )
            .order_by(ContentRecord.created_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )

        return [
            BrandStoryRecordResponse(
                id=record.id,
                product_name=(record.input_params or {}).get("product_name", ""),
                origin=(record.input_params or {}).get("origin", ""),
                style=(record.input_params or {}).get("style", ""),
                story=record.generated_content or "",
                cultural_elements=(record.input_params or {}).get("cultural_elements", []),
                tokens_used=record.total_tokens or 0,
                cost=0.0,
                created_at=record.created_at.isoformat(),
                status=record.status.value,
            )
            for record in records
        ]

    except Exception as e:
        logger.error(f"Failed to fetch records: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"查询记录失败: {str(e)}",
        )


@router.get("/records/{record_id}", response_model=BrandStoryRecordResponse, summary="查询单个记录")
def get_brand_story_record(
    record_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    查询指定的品牌故事生成记录
    """
    try:
        user_obj = db.query(User).filter(User.user_uuid == current_user.get("user_id")).first()
        if not user_obj:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="用户不存在")

        record = (
            db.query(ContentRecord)
            .filter(
                ContentRecord.id == record_id,
                ContentRecord.user_id == user_obj.id,
                ContentRecord.content_type == ContentType.STORY,
            )
            .first()
        )

        if not record:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="记录不存在",
            )

        return BrandStoryRecordResponse(
            id=record.id,
            product_name=(record.input_params or {}).get("product_name", ""),
            origin=(record.input_params or {}).get("origin", ""),
            style=(record.input_params or {}).get("style", ""),
            story=record.generated_content or "",
            cultural_elements=(record.input_params or {}).get("cultural_elements", []),
            tokens_used=record.total_tokens or 0,
            cost=0.0,
            created_at=record.created_at.isoformat(),
            status=record.status.value,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to fetch record: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"查询记录失败: {str(e)}",
        )


# =============================================================================
# Helper Functions
# =============================================================================


def _save_generation_record(
    db: Session,
    user_id: int,
    request: BrandStoryGenerateRequest,
    result: Dict[str, Any],
) -> int:
    """
    保存生成记录到数据库

    Args:
        db: 数据库会话
        user_id: 用户ID
        request: 请求参数
        result: 生成结果

    Returns:
        记录ID
    """
    try:
        # 映射style到Style枚举
        style_map = {
            "现代简约": Style.CASUAL,
            "传统深沉": Style.FORMAL,
            "情感共鸣": Style.EMOTIONAL,
        }
        style_enum = style_map.get(request.style, Style.CASUAL)

        # 映射word_count到LengthType枚举
        length_map = {
            "200": LengthType.SHORT,
            "300": LengthType.SHORT,
            "400": LengthType.MEDIUM,
            "500": LengthType.MEDIUM,
            "600": LengthType.MEDIUM,
        }
        # 提取数字
        word_num = "".join(filter(str.isdigit, request.word_count))
        length_enum = length_map.get(word_num, LengthType.MEDIUM)

        record = ContentRecord(
            user_id=user_id,
            product_id=request.product_id,
            content_type=ContentType.STORY,
            platform=Platform.GENERAL,
            style=style_enum,
            length_type=length_enum,
            input_params={
                "product_name": request.product_name,
                "origin": request.origin,
                "features": request.features,
                "purpose": request.purpose,
                "style": request.style,
                "word_count": request.word_count,
                "category": request.category,
                "keywords": request.keywords,
                "cultural_elements": result.get("cultural_elements", []),
            },
            generated_content=result["story"],
            prompt_tokens=result.get("tokens", {}).get("input", 0),
            completion_tokens=result.get("tokens", {}).get("output", 0),
            total_tokens=result.get("tokens", {}).get("total", 0),
            model_name="deepseek-chat",
            status=RecordStatus.COMPLETED,
        )

        db.add(record)
        db.commit()
        db.refresh(record)

        logger.info(f"Brand story record saved: id={record.id}, user_id={user_id}")
        return record.id

    except Exception as e:
        db.rollback()
        logger.error(f"Failed to save record: {str(e)}")
        raise
