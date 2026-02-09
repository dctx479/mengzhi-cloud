"""
文件上传服务 - BUG-022, BUG-024 修复

负责处理文件上传、验证、存储
支持头像上传和产品图片上传

版本: 1.0
创建日期: 2026-01-17
"""

import os
import uuid
import aiofiles
from typing import Optional, Tuple
from datetime import datetime
from pathlib import Path

from fastapi import UploadFile, HTTPException, status
from app.core.constants import (
    MAX_AVATAR_SIZE,
    MAX_IMAGE_SIZE,
    ALLOWED_IMAGE_TYPES,
    ALLOWED_IMAGE_EXTENSIONS,
    AVATAR_UPLOAD_DIR,
    PRODUCT_IMAGE_UPLOAD_DIR
)
from app.core.errors import FileOperationError, ValidationError
from app.core.logging_config import logger


class FileService:
    """文件上传服务"""

    @staticmethod
    def validate_image_file(
        file: UploadFile,
        max_size: int = MAX_IMAGE_SIZE
    ) -> None:
        """验证图片文件
        
        参数:
            file: 上传的文件
            max_size: 最大文件大小（字节）
            
        异常:
            ValidationError: 文件验证失败
        """
        # 验证文件类型
        if file.content_type not in ALLOWED_IMAGE_TYPES:
            raise ValidationError(
                f"不支持的文件类型: {file.content_type}。"
                f"支持的类型: {', '.join(ALLOWED_IMAGE_TYPES)}"
            )
        
        # 验证文件扩展名
        ext = os.path.splitext(file.filename)[1].lower()
        if ext not in ALLOWED_IMAGE_EXTENSIONS:
            raise ValidationError(
                f"不支持的文件扩展名: {ext}。"
                f"支持的扩展名: {', '.join(ALLOWED_IMAGE_EXTENSIONS)}"
            )

    @staticmethod
    def generate_unique_filename(original_filename: str, prefix: str = "") -> str:
        """生成唯一文件名
        
        参数:
            original_filename: 原始文件名
            prefix: 文件名前缀
            
        返回:
            唯一文件名
        """
        ext = os.path.splitext(original_filename)[1].lower()
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        unique_id = uuid.uuid4().hex[:8]
        
        if prefix:
            return f"{prefix}_{timestamp}_{unique_id}{ext}"
        return f"{timestamp}_{unique_id}{ext}"

    @staticmethod
    async def save_file(
        file: UploadFile,
        save_dir: str,
        filename: Optional[str] = None
    ) -> str:
        """保存文件到指定目录
        
        参数:
            file: 上传的文件
            save_dir: 保存目录
            filename: 文件名（可选，不提供则自动生成）
            
        返回:
            文件相对路径
            
        异常:
            FileOperationError: 文件保存失败
        """
        try:
            # 确保目录存在
            os.makedirs(save_dir, exist_ok=True)
            
            # 生成文件名
            if filename is None:
                filename = FileService.generate_unique_filename(file.filename)
            
            # 完整文件路径
            filepath = os.path.join(save_dir, filename)
            
            # 异步写入文件
            async with aiofiles.open(filepath, 'wb') as f:
                content = await file.read()
                await f.write(content)
            
            # 返回相对路径（用于URL）
            relative_path = filepath.replace("\\", "/")
            logger.info(f"文件保存成功: {relative_path}")
            return relative_path
            
        except Exception as e:
            logger.error(f"文件保存失败: {str(e)}")
            raise FileOperationError(f"文件保存失败: {str(e)}")

    @staticmethod
    async def upload_avatar(
        file: UploadFile,
        user_id: int
    ) -> str:
        """上传用户头像
        
        参数:
            file: 上传的头像文件
            user_id: 用户ID
            
        返回:
            头像URL路径
            
        异常:
            ValidationError: 文件验证失败
            FileOperationError: 文件保存失败
        """
        # 验证文件
        FileService.validate_image_file(file, max_size=MAX_AVATAR_SIZE)
        
        # 生成文件名
        filename = FileService.generate_unique_filename(
            file.filename,
            prefix=f"avatar_{user_id}"
        )
        
        # 保存文件
        filepath = await FileService.save_file(
            file,
            AVATAR_UPLOAD_DIR,
            filename
        )
        
        # 返回URL路径
        url_path = f"/{filepath}"
        logger.info(f"头像上传成功: user_id={user_id}, path={url_path}")
        return url_path

    @staticmethod
    async def upload_product_image(
        file: UploadFile,
        product_id: int
    ) -> str:
        """上传产品图片
        
        参数:
            file: 上传的图片文件
            product_id: 产品ID
            
        返回:
            图片URL路径
            
        异常:
            ValidationError: 文件验证失败
            FileOperationError: 文件保存失败
        """
        # 验证文件
        FileService.validate_image_file(file, max_size=MAX_IMAGE_SIZE)
        
        # 生成文件名
        filename = FileService.generate_unique_filename(
            file.filename,
            prefix=f"product_{product_id}"
        )
        
        # 保存文件
        filepath = await FileService.save_file(
            file,
            PRODUCT_IMAGE_UPLOAD_DIR,
            filename
        )
        
        # 返回URL路径
        url_path = f"/{filepath}"
        logger.info(f"产品图片上传成功: product_id={product_id}, path={url_path}")
        return url_path

    @staticmethod
    def delete_file(filepath: str) -> bool:
        """删除文件
        
        参数:
            filepath: 文件路径
            
        返回:
            是否删除成功
        """
        try:
            if os.path.exists(filepath):
                os.remove(filepath)
                logger.info(f"文件删除成功: {filepath}")
                return True
            else:
                logger.warning(f"文件不存在: {filepath}")
                return False
        except Exception as e:
            logger.error(f"文件删除失败: {str(e)}")
            return False
