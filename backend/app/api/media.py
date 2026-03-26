"""
媒体素材管理 API - Media Management Endpoints

提供：
- 图片/视频上传
- 媒体列表查询
- 媒体详情获取
- 媒体更新和删除
- 媒体统计

版本: 1.1
更新日期: 2026-03-25
"""

import os
from fastapi import APIRouter, File, UploadFile, Form, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional, List

from app.api.deps import get_db, get_current_user, require_admin
from app.schemas.media import (
    MediaResponse,
    MediaListResponse,
    MediaUpdate,
    MediaUploadResponse,
    MediaStatsResponse,
    MediaCategory,
    MediaType as MediaTypeSchema
)
from app.models.media import Media, MediaType
from app.models.user import User
from app.services.upload_service import UploadService


router = APIRouter(prefix="/media", tags=["媒体素材管理"])

# --- File upload security constants ---
MAX_IMAGE_UPLOAD_SIZE = 50 * 1024 * 1024    # 50 MB for images
MAX_VIDEO_UPLOAD_SIZE = 200 * 1024 * 1024   # 200 MB for videos

ALLOWED_IMAGE_MIME_TYPES = {"image/jpeg", "image/png", "image/webp", "image/gif"}
ALLOWED_IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".webp"}

ALLOWED_VIDEO_MIME_TYPES = {"video/mp4", "video/mpeg", "video/quicktime"}
ALLOWED_VIDEO_EXTENSIONS = {".mp4", ".mpeg", ".mpg", ".mov"}


def _validate_upload_file(
    file: UploadFile,
    content: bytes,
    allowed_mime_types: set,
    allowed_extensions: set,
    max_size: int,
) -> None:
    """Validate uploaded file size, MIME type, and extension.

    Raises HTTPException on validation failure.
    """
    # 1. Size check
    if len(content) > max_size:
        max_mb = max_size / (1024 * 1024)
        actual_mb = len(content) / (1024 * 1024)
        raise HTTPException(
            status_code=413,
            detail=f"文件过大: {actual_mb:.2f}MB，最大允许 {max_mb:.0f}MB",
        )

    # 2. MIME type check
    if file.content_type not in allowed_mime_types:
        raise HTTPException(
            status_code=400,
            detail=(
                f"不支持的文件类型: {file.content_type}。"
                f"支持的类型: {', '.join(sorted(allowed_mime_types))}"
            ),
        )

    # 3. Extension check
    ext = os.path.splitext(file.filename or "")[1].lower()
    if ext not in allowed_extensions:
        raise HTTPException(
            status_code=400,
            detail=(
                f"不支持的文件扩展名: {ext}。"
                f"支持的扩展名: {', '.join(sorted(allowed_extensions))}"
            ),
        )


def _get_user_int_id(current_user: dict, db: Session) -> int:
    """从current_user dict获取用户整数数据库ID"""
    user_id = current_user.get("user_id")
    if not user_id:
        raise HTTPException(status_code=401, detail="无法识别用户身份")
    user = db.query(User).filter(User.user_uuid == user_id).first()
    if not user:
        raise HTTPException(status_code=401, detail="用户不存在")
    return user.id


def get_upload_service(db: Session = Depends(get_db)) -> UploadService:
    """获取上传服务实例"""
    return UploadService(db)


@router.post("/upload/image", response_model=MediaUploadResponse, status_code=201)
async def upload_image(
    file: UploadFile = File(..., description="图片文件"),
    category: MediaCategory = Form(..., description="媒体分类"),
    product_id: Optional[int] = Form(None, description="关联产品ID"),
    title: Optional[str] = Form(None, description="标题"),
    description: Optional[str] = Form(None, description="描述"),
    alt_text: Optional[str] = Form(None, description="图片alt文本"),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
    upload_service: UploadService = Depends(get_upload_service)
):
    """
    上传图片

    - 支持格式：JPEG、PNG、WebP、GIF
    - 最大文件大小：50MB
    - 自动生成缩略图
    - 自动压缩优化
    """
    try:
        # --- Security: validate file before processing ---
        content = await file.read()
        _validate_upload_file(
            file, content,
            ALLOWED_IMAGE_MIME_TYPES, ALLOWED_IMAGE_EXTENSIONS,
            MAX_IMAGE_UPLOAD_SIZE,
        )
        # Reset file position so downstream service can read it again
        await file.seek(0)

        media = await upload_service.upload_image(
            file=file,
            category=category,
            user_id=_get_user_int_id(current_user, db),
            product_id=product_id,
            title=title,
            description=description,
            alt_text=alt_text
        )

        return {
            "success": True,
            "message": "图片上传成功",
            "data": media
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail="上传失败")


@router.post("/upload/video", response_model=MediaUploadResponse, status_code=201)
async def upload_video(
    file: UploadFile = File(..., description="视频文件"),
    category: MediaCategory = Form(..., description="媒体分类"),
    product_id: Optional[int] = Form(None, description="关联产品ID"),
    title: Optional[str] = Form(None, description="标题"),
    description: Optional[str] = Form(None, description="描述"),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
    upload_service: UploadService = Depends(get_upload_service)
):
    """
    上传视频

    - 支持格式：MP4、MPEG、MOV
    - 最大文件大小：200MB
    """
    try:
        # --- Security: validate file before processing ---
        content = await file.read()
        _validate_upload_file(
            file, content,
            ALLOWED_VIDEO_MIME_TYPES, ALLOWED_VIDEO_EXTENSIONS,
            MAX_VIDEO_UPLOAD_SIZE,
        )
        # Reset file position so downstream service can read it again
        await file.seek(0)

        media = await upload_service.upload_video(
            file=file,
            category=category,
            user_id=_get_user_int_id(current_user, db),
            product_id=product_id,
            title=title,
            description=description
        )

        return {
            "success": True,
            "message": "视频上传成功",
            "data": media
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail="上传失败")


@router.get("/", response_model=MediaListResponse)
async def list_media(
    media_type: Optional[MediaTypeSchema] = Query(None, description="媒体类型筛选"),
    category: Optional[MediaCategory] = Query(None, description="分类筛选"),
    user_id: Optional[int] = Query(None, description="用户ID筛选（仅管理员）"),
    product_id: Optional[int] = Query(None, description="产品ID筛选"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页大小"),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    获取媒体列表

    - 普通用户只能查看自己的媒体
    - 管理员可以查看所有媒体
    - 支持按类型、分类、产品筛选
    """
    query = db.query(Media)

    # 权限过滤
    if current_user.get("role", "") != "admin":
        query = query.filter(Media.user_id == _get_user_int_id(current_user, db))
    elif user_id:
        # 管理员可以筛选特定用户
        query = query.filter(Media.user_id == user_id)

    # 条件过滤
    if media_type:
        query = query.filter(Media.media_type == MediaType[media_type.value.upper()])
    if category:
        query = query.filter(Media.category == category)
    if product_id:
        query = query.filter(Media.product_id == product_id)

    # 排序（最新优先）
    query = query.order_by(Media.created_at.desc())

    # 分页
    total = query.count()
    items = query.offset((page - 1) * page_size).limit(page_size).all()

    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "items": items
    }


@router.get("/stats", response_model=MediaStatsResponse)
async def get_media_stats(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
    upload_service: UploadService = Depends(get_upload_service)
):
    """
    获取用户媒体统计信息

    - 总数、总大小
    - 按类型统计
    - 按分类统计
    """
    stats = upload_service.get_user_media_stats(_get_user_int_id(current_user, db))
    return stats


@router.get("/{media_id}", response_model=MediaResponse)
async def get_media(
    media_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
    upload_service: UploadService = Depends(get_upload_service)
):
    """
    获取媒体详情

    - 普通用户只能查看自己的媒体
    - 管理员可以查看所有媒体
    """
    media = upload_service.get_media_by_id(media_id)

    if not media:
        raise HTTPException(status_code=404, detail="媒体不存在")

    # 权限验证
    if media.user_id != _get_user_int_id(current_user, db) and current_user.get("role", "") != "admin":
        raise HTTPException(status_code=403, detail="无权访问此媒体")

    return media


@router.put("/{media_id}", response_model=MediaResponse)
async def update_media(
    media_id: int,
    media_update: MediaUpdate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
    upload_service: UploadService = Depends(get_upload_service)
):
    """
    更新媒体信息

    - 可更新标题、描述、alt文本、公开状态
    - 普通用户只能更新自己的媒体
    - 管理员可以更新所有媒体
    """
    media = upload_service.get_media_by_id(media_id)

    if not media:
        raise HTTPException(status_code=404, detail="媒体不存在")

    # 权限验证
    if media.user_id != _get_user_int_id(current_user, db) and current_user.get("role", "") != "admin":
        raise HTTPException(status_code=403, detail="无权修改此媒体")

    # 更新字段
    update_data = media_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(media, field, value)

    db.commit()
    db.refresh(media)

    return media


@router.delete("/{media_id}", status_code=204)
async def delete_media(
    media_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
    upload_service: UploadService = Depends(get_upload_service)
):
    """
    删除媒体

    - 物理删除文件和数据库记录
    - 普通用户只能删除自己的媒体
    - 管理员可以删除所有媒体
    """
    media = upload_service.get_media_by_id(media_id)

    if not media:
        raise HTTPException(status_code=404, detail="媒体不存在")

    # 权限验证
    if media.user_id != _get_user_int_id(current_user, db) and current_user.get("role", "") != "admin":
        raise HTTPException(status_code=403, detail="无权删除此媒体")

    # 删除媒体
    upload_service.delete_media(media)

    return None


@router.post("/{media_id}/assign-product/{product_id}", response_model=MediaResponse)
async def assign_media_to_product(
    media_id: int,
    product_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
    upload_service: UploadService = Depends(get_upload_service)
):
    """
    将媒体关联到产品

    - 企业用户和管理员可以关联自己的媒体到产品
    - 验证产品所有权
    """
    from app.models.product import Product

    media = upload_service.get_media_by_id(media_id)
    if not media:
        raise HTTPException(status_code=404, detail="媒体不存在")

    # 验证媒体所有权
    if media.user_id != _get_user_int_id(current_user, db) and current_user.get("role", "") != "admin":
        raise HTTPException(status_code=403, detail="无权操作此媒体")

    # 验证产品存在
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="产品不存在")

    # 验证产品所有权
    if product.created_by != _get_user_int_id(current_user, db) and current_user.get("role", "") != "admin":
        raise HTTPException(status_code=403, detail="无权操作此产品")

    # 关联产品
    media.product_id = product_id
    db.commit()
    db.refresh(media)

    return media


@router.delete("/{media_id}/unassign-product", response_model=MediaResponse)
async def unassign_media_from_product(
    media_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
    upload_service: UploadService = Depends(get_upload_service)
):
    """
    取消媒体与产品的关联
    """
    media = upload_service.get_media_by_id(media_id)
    if not media:
        raise HTTPException(status_code=404, detail="媒体不存在")

    # 权限验证
    if media.user_id != _get_user_int_id(current_user, db) and current_user.get("role", "") != "admin":
        raise HTTPException(status_code=403, detail="无权操作此媒体")

    # 取消关联
    media.product_id = None
    db.commit()
    db.refresh(media)

    return media
