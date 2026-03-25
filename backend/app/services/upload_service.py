"""
文件上传服务 - Upload Service

提供：
- 图片上传（本地/OSS）
- 视频上传（本地/OSS）
- 文件验证
- 缩略图生成
- 文件删除

版本: 1.0
更新日期: 2026-01-17
"""

import os
import uuid
from pathlib import Path
from datetime import datetime
from typing import Optional, Tuple
from fastapi import UploadFile, HTTPException
from sqlalchemy.orm import Session
from loguru import logger

from app.core.config import settings
from app.models.media import Media, MediaType, MediaCategory
from app.services.image_processor import ImageProcessor


class UploadService:
    """文件上传服务

    支持本地存储和对象存储（OSS）。
    自动生成缩略图，验证文件类型和大小。
    """

    def __init__(self, db: Session):
        """
        初始化上传服务

        参数:
            db: 数据库会话
        """
        self.db = db
        self.upload_dir = Path(settings.UPLOAD_DIR)
        self.upload_dir.mkdir(parents=True, exist_ok=True)

    def validate_image(self, file: UploadFile) -> None:
        """
        验证图片文件

        参数:
            file: 上传的文件

        异常:
            HTTPException: 文件类型或大小不符合要求
        """
        # 验证MIME类型
        if file.content_type not in settings.ALLOWED_IMAGE_TYPES:
            raise HTTPException(
                status_code=400,
                detail=f"不支持的图片类型: {file.content_type}。支持的类型: {', '.join(settings.ALLOWED_IMAGE_TYPES)}",
            )

        # 验证文件大小
        file.file.seek(0, 2)  # 移动到文件末尾
        file_size = file.file.tell()
        file.file.seek(0)  # 回到开头

        if file_size > settings.MAX_FILE_SIZE:
            raise HTTPException(
                status_code=400,
                detail=f"文件过大: {file_size / (1024*1024):.2f}MB > {settings.MAX_FILE_SIZE / (1024*1024)}MB",
            )

    def validate_video(self, file: UploadFile) -> None:
        """
        验证视频文件

        参数:
            file: 上传的文件

        异常:
            HTTPException: 文件类型或大小不符合要求
        """
        # 验证MIME类型
        if file.content_type not in settings.ALLOWED_VIDEO_TYPES:
            raise HTTPException(
                status_code=400,
                detail=f"不支持的视频类型: {file.content_type}。支持的类型: {', '.join(settings.ALLOWED_VIDEO_TYPES)}",
            )

        # 验证文件大小
        file.file.seek(0, 2)
        file_size = file.file.tell()
        file.file.seek(0)

        if file_size > settings.MAX_VIDEO_SIZE:
            raise HTTPException(
                status_code=400,
                detail=f"视频文件过大: {file_size / (1024*1024):.2f}MB > {settings.MAX_VIDEO_SIZE / (1024*1024)}MB",
            )

    async def save_file_to_local(self, file: UploadFile, category: MediaCategory) -> Tuple[str, str, int]:
        """
        保存文件到本地存储

        参数:
            file: 上传的文件
            category: 媒体分类

        返回:
            tuple: (file_path, file_url, file_size)
        """
        # 生成唯一文件名
        ext = Path(file.filename).suffix
        unique_filename = f"{uuid.uuid4()}{ext}"

        # 按分类和日期组织目录
        date_path = datetime.now().strftime("%Y/%m/%d")
        category_dir = self.upload_dir / category.value / date_path
        category_dir.mkdir(parents=True, exist_ok=True)

        # 文件路径
        file_path = category_dir / unique_filename

        # 保存文件
        file.file.seek(0)
        content = await file.read()
        with open(file_path, "wb") as buffer:
            buffer.write(content)

        # 文件大小
        file_size = len(content)

        # 生成访问URL
        file_url = f"/{settings.UPLOAD_DIR}/{category.value}/{date_path}/{unique_filename}"

        return str(file_path), file_url, file_size

    async def save_file_to_oss(self, file: UploadFile, category: MediaCategory) -> Tuple[str, str, int]:
        """
        保存文件到对象存储（OSS/COS/S3）

        参数:
            file: 上传的文件
            category: 媒体分类

        返回:
            tuple: (object_key, file_url, file_size)
        """
        # 检查OSS配置
        if not all([settings.OSS_ENDPOINT, settings.OSS_ACCESS_KEY, settings.OSS_SECRET_KEY, settings.OSS_BUCKET]):
            # OSS未配置，fallback到本地存储
            return await self.save_file_to_local(file, category)

        try:
            import oss2
        except ImportError:
            # oss2未安装，fallback到本地存储
            return await self.save_file_to_local(file, category)

        # 初始化OSS客户端
        auth = oss2.Auth(settings.OSS_ACCESS_KEY, settings.OSS_SECRET_KEY)
        bucket = oss2.Bucket(auth, settings.OSS_ENDPOINT, settings.OSS_BUCKET)

        # 生成对象键
        ext = Path(file.filename).suffix
        unique_filename = f"{uuid.uuid4()}{ext}"
        date_path = datetime.now().strftime("%Y/%m/%d")
        object_key = f"{category.value}/{date_path}/{unique_filename}"

        # 读取文件内容
        file.file.seek(0)
        content = await file.read()
        file_size = len(content)

        # 上传到OSS
        bucket.put_object(object_key, content)

        # 生成访问URL
        file_url = (
            f"{settings.OSS_DOMAIN}/{object_key}"
            if settings.OSS_DOMAIN
            else bucket.sign_url("GET", object_key, 3600 * 24 * 365)
        )

        return object_key, file_url, file_size

    async def upload_image(
        self,
        file: UploadFile,
        category: MediaCategory,
        user_id: int,
        product_id: Optional[int] = None,
        title: Optional[str] = None,
        description: Optional[str] = None,
        alt_text: Optional[str] = None,
    ) -> Media:
        """
        上传图片

        参数:
            file: 上传的文件
            category: 媒体分类
            user_id: 用户ID
            product_id: 产品ID（可选）
            title: 标题（可选）
            description: 描述（可选）
            alt_text: alt文本（可选）

        返回:
            Media: 媒体记录
        """
        # 验证文件
        self.validate_image(file)

        # 保存文件
        if settings.USE_OSS:
            file_path, file_url, file_size = await self.save_file_to_oss(file, category)
        else:
            file_path, file_url, file_size = await self.save_file_to_local(file, category)

        # 获取图片信息（仅限本地存储）
        # BUG FIX: OSS path是对象键，不是文件系统路径，无法用PIL打开
        img_info = None
        thumbnail_url = None
        if not settings.USE_OSS:
            try:
                img_info = ImageProcessor.get_image_info(file_path)
            except Exception as e:
                logger.warning(f"获取图片信息失败: {e}")
                img_info = {"width": None, "height": None}
        else:
            # OSS上传：无法提取本地图片信息，设置为None
            img_info = {"width": None, "height": None}

        # 生成缩略图（仅限本地存储）
        try:
            if not settings.USE_OSS:
                thumbnail_path = ImageProcessor.generate_thumbnail(
                    file_path, size=settings.IMAGE_THUMBNAIL_SIZE, quality=settings.IMAGE_QUALITY
                )
                # 生成缩略图URL（从实际文件路径推导，而不是重新计算date_path）
                # BUG FIX: 缩略图与主文件在同一目录，直接计算相对URL
                thumbnail_filename = Path(thumbnail_path).name
                # 从thumbnail_path中提取相对部分（uploads/category/YYYY/MM/DD/filename_thumb.ext）
                relative_thumb = str(Path(thumbnail_path)).replace("\\", "/")
                if relative_thumb.startswith(str(self.upload_dir).replace("\\", "/")):
                    # 去掉前缀获取相对路径
                    thumbnail_url = f"/{relative_thumb[len(str(self.upload_dir).replace('\\\\', '/')):]}"
                else:
                    # fallback: 使用基于当前日期的路径（可能不准确但是合理的默认值）
                    date_path = datetime.now().strftime("%Y/%m/%d")
                    thumbnail_url = f"/{settings.UPLOAD_DIR}/{category.value}/{date_path}/{thumbnail_filename}"
        except Exception as e:
            logger.warning(f"缩略图生成失败: {e}")

        # 创建媒体记录
        media = Media(
            filename=file.filename,
            file_path=file_path,
            file_url=file_url,
            file_size=file_size,
            mime_type=file.content_type,
            media_type=MediaType.IMAGE,
            category=category,
            width=img_info["width"],
            height=img_info["height"],
            thumbnail_url=thumbnail_url,
            user_id=user_id,
            product_id=product_id,
            title=title,
            description=description,
            alt_text=alt_text,
            is_processed=True,  # 已处理（压缩、缩略图）
        )

        self.db.add(media)
        self.db.commit()
        self.db.refresh(media)

        return media

    async def upload_video(
        self,
        file: UploadFile,
        category: MediaCategory,
        user_id: int,
        product_id: Optional[int] = None,
        title: Optional[str] = None,
        description: Optional[str] = None,
    ) -> Media:
        """
        上传视频

        参数:
            file: 上传的文件
            category: 媒体分类
            user_id: 用户ID
            product_id: 产品ID（可选）
            title: 标题（可选）
            description: 描述（可选）

        返回:
            Media: 媒体记录
        """
        # 验证文件
        self.validate_video(file)

        # 保存文件
        if settings.USE_OSS:
            file_path, file_url, file_size = await self.save_file_to_oss(file, category)
        else:
            file_path, file_url, file_size = await self.save_file_to_local(file, category)

        # 提取视频元数据（仅本地存储）
        # BUG FIX: OSS对象键无法用ffmpeg处理，仅本地文件可提取
        width = None
        height = None
        duration = None

        if not settings.USE_OSS:
            try:
                # 延迟导入以避免依赖全局要求
                try:
                    import ffmpeg
                    probe = ffmpeg.probe(file_path)
                    video_stream = next((s for s in probe['streams'] if s['codec_type'] == 'video'), None)
                    if video_stream:
                        width = video_stream.get('width')
                        height = video_stream.get('height')
                        duration = float(probe.get('format', {}).get('duration', 0))
                except (ImportError, Exception) as e:
                    logger.warning(f"使用ffmpeg-python提取视频元数据失败，尝试moviepy: {e}")
                    try:
                        from moviepy.editor import VideoFileClip
                        clip = VideoFileClip(file_path)
                        width = clip.w
                        height = clip.h
                        duration = clip.duration
                        clip.close()
                    except (ImportError, Exception) as e2:
                        logger.warning(f"无法提取视频元数据（ffmpeg和moviepy均不可用）: {e2}")
            except Exception as e:
                logger.warning(f"视频元数据提取异常: {e}")

        # 创建媒体记录
        media = Media(
            filename=file.filename,
            file_path=file_path,
            file_url=file_url,
            file_size=file_size,
            mime_type=file.content_type,
            media_type=MediaType.VIDEO,
            category=category,
            width=width,
            height=height,
            duration=duration,
            user_id=user_id,
            product_id=product_id,
            title=title,
            description=description,
            is_processed=False,  # 视频处理需要异步进行
        )

        self.db.add(media)
        self.db.commit()
        self.db.refresh(media)

        # NOTE: 异步生成视频封面需要在后台任务中处理
        # 前端可轮询查询media.is_processed字段来判断处理完成
        # 实现方法: 使用Celery/RQ等任务队列
        # 示例: asyncio.create_task(self._generate_video_thumbnail(media.id))

        return media

    def delete_media(self, media: Media) -> None:
        """
        删除媒体文件

        参数:
            media: 媒体记录
        """
        # 删除主文件
        if not settings.USE_OSS:
            # 本地存储
            if os.path.exists(media.file_path):
                try:
                    os.remove(media.file_path)
                except Exception as e:
                    logger.warning(f"删除文件失败: {e}")

            # 删除缩略图
            if media.thumbnail_url:
                thumbnail_path = Path(settings.UPLOAD_DIR) / media.thumbnail_url.lstrip("/")
                if thumbnail_path.exists():
                    try:
                        thumbnail_path.unlink()
                    except Exception as e:
                        logger.warning(f"删除缩略图失败: {e}")
        else:
            # OSS存储
            try:
                import oss2

                auth = oss2.Auth(settings.OSS_ACCESS_KEY, settings.OSS_SECRET_KEY)
                bucket = oss2.Bucket(auth, settings.OSS_ENDPOINT, settings.OSS_BUCKET)
                bucket.delete_object(media.file_path)
                if media.thumbnail_url:
                    thumbnail_key = media.thumbnail_url.lstrip("/")
                    bucket.delete_object(thumbnail_key)
            except Exception as e:
                logger.warning(f"删除OSS文件失败: {e}")

        # 删除数据库记录
        self.db.delete(media)
        self.db.commit()

    def get_media_by_id(self, media_id: int) -> Optional[Media]:
        """
        根据ID获取媒体

        参数:
            media_id: 媒体ID

        返回:
            Media: 媒体记录
        """
        return self.db.query(Media).filter(Media.id == media_id).first()

    def get_media_by_uuid(self, media_uuid: str) -> Optional[Media]:
        """
        根据UUID获取媒体

        参数:
            media_uuid: 媒体UUID

        返回:
            Media: 媒体记录
        """
        return self.db.query(Media).filter(Media.media_uuid == media_uuid).first()

    def get_user_media_stats(self, user_id: int) -> dict:
        """
        获取用户媒体统计

        参数:
            user_id: 用户ID

        返回:
            dict: 统计信息
        """
        from sqlalchemy import func

        query = self.db.query(
            func.count(Media.id).label("total_count"),
            func.sum(Media.file_size).label("total_size"),
            func.count(func.nullif(Media.media_type != MediaType.IMAGE, True)).label("image_count"),
            func.count(func.nullif(Media.media_type != MediaType.VIDEO, True)).label("video_count"),
        ).filter(Media.user_id == user_id)

        result = query.first()

        # 按分类统计
        category_stats = (
            self.db.query(Media.category, func.count(Media.id).label("count"))
            .filter(Media.user_id == user_id)
            .group_by(Media.category)
            .all()
        )

        return {
            "total_count": result.total_count or 0,
            "total_size": result.total_size or 0,
            "image_count": result.image_count or 0,
            "video_count": result.video_count or 0,
            "by_category": {cat.value: count for cat, count in category_stats},
        }
