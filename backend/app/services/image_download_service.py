"""
图片下载服务 — 将外部CDN图片持久化到本地存储

支持:
- 单张图片下载 (async)
- 产品级批量下载 (备份原始URL + 替换为本地路径)
- 全库批量同步 (管理员操作)
"""

import os
import uuid
import asyncio
from pathlib import Path
from typing import Optional
from urllib.parse import urlparse

import httpx
from sqlalchemy.orm import Session

from app.core.logging_config import logger
from app.core.constants import PRODUCT_IMAGE_UPLOAD_DIR
from app.models.product import Product


ALLOWED_CONTENT_TYPES = frozenset({
    "image/jpeg", "image/png", "image/gif", "image/webp", "image/bmp",
})

EXTENSION_MAP = {
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/gif": ".gif",
    "image/webp": ".webp",
    "image/bmp": ".bmp",
}


class ImageDownloadService:

    MAX_CONCURRENT = 5
    TIMEOUT = 30
    MAX_SIZE = 10 * 1024 * 1024  # 10MB

    def __init__(self):
        self._semaphore = asyncio.Semaphore(self.MAX_CONCURRENT)

    async def download_single_image(self, url: str, product_id: int) -> Optional[str]:
        """Download a single image from URL to local storage.

        Returns local relative path (e.g., 'uploads/products/42_abc123.jpg') or None on failure.
        """
        if not url or not url.startswith("http"):
            return None

        async with self._semaphore:
            try:
                async with httpx.AsyncClient(
                    timeout=self.TIMEOUT,
                    follow_redirects=True,
                    headers={"User-Agent": "Mozilla/5.0 AgriPlatform/1.0"}
                ) as client:
                    resp = await client.get(url)
                    resp.raise_for_status()

                    content_type = resp.headers.get("content-type", "").split(";")[0].strip().lower()
                    if content_type not in ALLOWED_CONTENT_TYPES:
                        ext = _guess_extension_from_url(url)
                    else:
                        ext = EXTENSION_MAP.get(content_type, ".jpg")

                    body = resp.content
                    if len(body) > self.MAX_SIZE:
                        logger.warning(f"图片过大 ({len(body)} bytes), 跳过: {url}")
                        return None

                    upload_dir = Path(PRODUCT_IMAGE_UPLOAD_DIR)
                    upload_dir.mkdir(parents=True, exist_ok=True)

                    filename = f"{product_id}_{uuid.uuid4().hex[:8]}{ext}"
                    filepath = upload_dir / filename

                    filepath.write_bytes(body)

                    local_path = f"/{PRODUCT_IMAGE_UPLOAD_DIR}/{filename}"
                    logger.debug(f"下载图片成功: {url} -> {local_path}")
                    return local_path

            except Exception as e:
                logger.warning(f"下载图片失败 product_id={product_id}, url={url}: {e}")
                return None

    async def download_product_images(self, product: Product, db: Session) -> dict:
        """Download all external images for a single product.

        - Backs up original URLs to product.original_image_urls
        - Downloads each external URL to local storage
        - Updates image_urls and main_image_url to local paths
        - Keeps original URL if download fails
        """
        original_urls = list(product.image_urls or [])
        if product.main_image_url and product.main_image_url not in original_urls:
            original_urls.insert(0, product.main_image_url)

        # Skip if no external URLs
        external_urls = [u for u in original_urls if u and u.startswith("http")]
        if not external_urls:
            return {"downloaded": 0, "skipped": len(original_urls), "failed": 0}

        # Backup original URLs
        if not product.original_image_urls:
            product.original_image_urls = original_urls

        # Download
        downloaded = 0
        failed = 0
        new_image_urls = []

        for url in (product.image_urls or []):
            if not url or not url.startswith("http"):
                new_image_urls.append(url)
                continue

            local_path = await self.download_single_image(url, product.id)
            if local_path:
                new_image_urls.append(local_path)
                downloaded += 1
            else:
                new_image_urls.append(url)
                failed += 1

        product.image_urls = new_image_urls

        # Update main image
        if product.main_image_url and product.main_image_url.startswith("http"):
            local_main = await self.download_single_image(product.main_image_url, product.id)
            if local_main:
                product.main_image_url = local_main
                downloaded += 1
            else:
                failed += 1

        db.add(product)
        db.commit()

        return {
            "downloaded": downloaded,
            "skipped": len(original_urls) - len(external_urls),
            "failed": failed,
        }

    async def batch_download_all_products(self, db: Session) -> dict:
        """Download external images for ALL products that still have remote URLs."""
        products = (
            db.query(Product)
            .filter(Product.main_image_url.like("http%"))
            .all()
        )

        total = len(products)
        success = 0
        failed = 0
        skipped = 0

        for product in products:
            try:
                result = await self.download_product_images(product, db)
                if result["downloaded"] > 0:
                    success += 1
                elif result["failed"] > 0:
                    failed += 1
                else:
                    skipped += 1
            except Exception as e:
                logger.error(f"批量下载失败 product_id={product.id}: {e}")
                failed += 1

        return {
            "total": total,
            "success": success,
            "failed": failed,
            "skipped": skipped,
        }


def _guess_extension_from_url(url: str) -> str:
    """Guess file extension from URL path."""
    parsed = urlparse(url)
    path = parsed.path.lower()
    for ext in (".jpg", ".jpeg", ".png", ".gif", ".webp", ".bmp"):
        if path.endswith(ext):
            return ext if ext != ".jpeg" else ".jpg"
    return ".jpg"
