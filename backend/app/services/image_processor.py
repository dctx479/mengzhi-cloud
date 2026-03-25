"""
图片处理服务 - Image Processing Service

提供：
- 图片压缩
- 缩略图生成
- 图片格式转换
- 图片尺寸调整
- 获取图片元数据

版本: 1.0
更新日期: 2026-01-17
"""

from PIL import Image
import io
import os
from pathlib import Path
from typing import Tuple, Optional, Dict, Any
from app.core.config import settings


class ImageProcessor:
    """图片处理服务

    使用Pillow进行图片处理，支持压缩、缩略图生成等功能。
    """

    @staticmethod
    def get_image_info(image_path: str) -> Dict[str, Any]:
        """
        获取图片元数据

        参数:
            image_path: 图片路径

        返回:
            dict: 包含宽度、高度、格式等信息
        """
        with Image.open(image_path) as img:
            return {
                "width": img.width,
                "height": img.height,
                "format": img.format,
                "mode": img.mode,
                "size": os.path.getsize(image_path),
            }

    @staticmethod
    def compress_image(
        image_path: str,
        quality: int = 85,
        output_path: Optional[str] = None
    ) -> str:
        """
        压缩图片

        参数:
            image_path: 原始图片路径
            quality: 压缩质量 (1-100)
            output_path: 输出路径（如果为None，覆盖原文件）

        返回:
            str: 压缩后的图片路径
        """
        if output_path is None:
            output_path = image_path

        with Image.open(image_path) as img:
            # 转换RGBA为RGB（用于JPEG）
            if img.mode == 'RGBA' and output_path.lower().endswith('.jpg'):
                # 创建白色背景
                background = Image.new('RGB', img.size, (255, 255, 255))
                background.paste(img, mask=img.split()[3])  # 使用alpha通道作为mask
                img = background

            # 保存压缩后的图片
            img.save(output_path, quality=quality, optimize=True)

        return output_path

    @staticmethod
    def generate_thumbnail(
        image_path: str,
        size: Tuple[int, int] = (300, 300),
        quality: int = 85
    ) -> str:
        """
        生成缩略图

        参数:
            image_path: 原始图片路径
            size: 缩略图尺寸 (width, height)
            quality: 压缩质量

        返回:
            str: 缩略图路径
        """
        # 生成缩略图文件名
        path_obj = Path(image_path)
        thumbnail_path = str(
            path_obj.parent / f"{path_obj.stem}_thumb{path_obj.suffix}"
        )

        with Image.open(image_path) as img:
            # 保持宽高比的缩略图
            img.thumbnail(size, Image.Resampling.LANCZOS)

            # 处理RGBA图片
            if img.mode == 'RGBA' and thumbnail_path.lower().endswith('.jpg'):
                background = Image.new('RGB', img.size, (255, 255, 255))
                background.paste(img, mask=img.split()[3])
                img = background

            # 保存缩略图
            img.save(thumbnail_path, quality=quality, optimize=True)

        return thumbnail_path

    @staticmethod
    def resize_image(
        image_path: str,
        width: Optional[int] = None,
        height: Optional[int] = None,
        keep_aspect_ratio: bool = True,
        output_path: Optional[str] = None
    ) -> str:
        """
        调整图片尺寸

        参数:
            image_path: 原始图片路径
            width: 目标宽度
            height: 目标高度
            keep_aspect_ratio: 是否保持宽高比
            output_path: 输出路径

        返回:
            str: 调整后的图片路径
        """
        if output_path is None:
            output_path = image_path

        with Image.open(image_path) as img:
            original_width, original_height = img.size

            # 计算新尺寸
            if keep_aspect_ratio:
                if width and not height:
                    # 仅指定宽度，按比例缩放高度
                    height = int(original_height * (width / original_width))
                elif height and not width:
                    # 仅指定高度，按比例缩放宽度
                    width = int(original_width * (height / original_height))
                elif width and height:
                    # 同时指定宽高，取较小的缩放比例
                    ratio = min(width / original_width, height / original_height)
                    width = int(original_width * ratio)
                    height = int(original_height * ratio)
            else:
                # 不保持宽高比
                if not width:
                    width = original_width
                if not height:
                    height = original_height

            # 调整尺寸
            resized_img = img.resize((width, height), Image.Resampling.LANCZOS)

            # 保存
            resized_img.save(output_path, quality=settings.IMAGE_QUALITY, optimize=True)

        return output_path

    @staticmethod
    def convert_format(
        image_path: str,
        target_format: str,
        output_path: Optional[str] = None
    ) -> str:
        """
        转换图片格式

        参数:
            image_path: 原始图片路径
            target_format: 目标格式 (如 'JPEG', 'PNG', 'WEBP')
            output_path: 输出路径

        返回:
            str: 转换后的图片路径
        """
        if output_path is None:
            path_obj = Path(image_path)
            ext = '.' + target_format.lower().replace('jpeg', 'jpg')
            output_path = str(path_obj.parent / f"{path_obj.stem}{ext}")

        with Image.open(image_path) as img:
            # 处理RGBA和调色板模式
            if target_format.upper() == 'JPEG':
                if img.mode in ('RGBA', 'LA', 'P'):
                    # 转换为RGB
                    background = Image.new('RGB', img.size, (255, 255, 255))
                    if img.mode == 'P':
                        img = img.convert('RGBA')
                    background.paste(img, mask=img.split()[-1] if img.mode in ('RGBA', 'LA') else None)
                    img = background

            # 保存
            img.save(output_path, format=target_format, quality=settings.IMAGE_QUALITY, optimize=True)

        return output_path

    @staticmethod
    def validate_image(image_path: str) -> bool:
        """
        验证是否为有效的图片文件

        参数:
            image_path: 图片路径

        返回:
            bool: 是否为有效图片
        """
        try:
            with Image.open(image_path) as img:
                img.verify()
            return True
        except Exception:
            return False

    @staticmethod
    def create_square_thumbnail(
        image_path: str,
        size: int = 300,
        quality: int = 85
    ) -> str:
        """
        创建正方形缩略图（居中裁剪）

        参数:
            image_path: 原始图片路径
            size: 正方形边长
            quality: 压缩质量

        返回:
            str: 缩略图路径
        """
        path_obj = Path(image_path)
        thumbnail_path = str(
            path_obj.parent / f"{path_obj.stem}_square{path_obj.suffix}"
        )

        with Image.open(image_path) as img:
            # 计算裁剪区域（居中）
            width, height = img.size
            if width > height:
                left = (width - height) // 2
                top = 0
                right = left + height
                bottom = height
            else:
                left = 0
                top = (height - width) // 2
                right = width
                bottom = top + width

            # 裁剪为正方形
            img_cropped = img.crop((left, top, right, bottom))

            # 缩放到目标尺寸
            img_resized = img_cropped.resize((size, size), Image.Resampling.LANCZOS)

            # 保存
            img_resized.save(thumbnail_path, quality=quality, optimize=True)

        return thumbnail_path
