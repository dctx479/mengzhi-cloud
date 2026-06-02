"""
京东联盟商品导入服务

职责:
- 将京东联盟 API 返回的商品数据映射到本平台 Product 模型
- 批量导入（去重、更新）
- 实时搜索代理（不写库，直接返回格式化结果）
"""

from __future__ import annotations

import asyncio
from typing import Optional
from loguru import logger
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models.product import Product, ProductStatus
from app.services.jd_api_client import JdApiClient, JdApiError
from app.core.config import settings


# ------------------------------------------------------------------
# 字段映射
# ------------------------------------------------------------------

def _map_jd_goods_to_product(item: dict) -> dict:
    """
    将京东联盟商品字段映射到本平台 Product 字段。

    京东字段参考:
      skuId, skuName, imageInfo.imageList[0].url,
      priceInfo.price / lowestPrice,
      categoryInfo.cid1Name / cid2Name / cid3Name,
      shopInfo.shopName
    """
    image_info = item.get("imageInfo") or {}
    image_list = image_info.get("imageList") or []
    image_urls = []
    for img in image_list:
        url = img.get("url", "")
        if url and url.startswith("//"):
            url = "https:" + url
        if url:
            image_urls.append(url)
    main_image = image_urls[0] if image_urls else ""

    price_info = item.get("priceInfo") or {}
    price_str = price_info.get("lowestPrice") or price_info.get("price") or "0"
    try:
        price = float(price_str)
    except (ValueError, TypeError):
        price = 0.0

    category_info = item.get("categoryInfo") or {}
    cid1_name = category_info.get("cid1Name", "")
    cid2_name = category_info.get("cid2Name", "")
    cid3_name = category_info.get("cid3Name", "")
    category = cid1_name or "其他"
    sub_category = cid3_name or cid2_name or None

    shop_info = item.get("shopInfo") or {}
    shop_name = shop_info.get("shopName", "")

    sku_id = str(item.get("skuId", ""))
    sku_name = item.get("skuName", "").strip()

    return {
        "name": sku_name[:200] if sku_name else f"JD-{sku_id}",
        "description": sku_name,
        "category": category[:100],
        "sub_category": sub_category[:100] if sub_category else None,
        "origin_province": "未知",
        "main_image_url": main_image,
        "image_urls": image_urls,
        "price": price,
        "specifications": {
            "jd_sku_id": sku_id,
            "shop_name": shop_name,
            "price": price,
            "cid1": category_info.get("cid1Name"),
            "cid2": category_info.get("cid2Name"),
            "cid3": category_info.get("cid3Name"),
        },
        "status": ProductStatus.PUBLISHED,
        "_jd_sku_id": sku_id,
        "_price": price,
    }


def _format_for_frontend(item: dict) -> dict:
    """将京东原始商品格式化为前端期望的结构（实时搜索用，不写库）。"""
    mapped = _map_jd_goods_to_product(item)
    return {
        "jd_sku_id": mapped["_jd_sku_id"],
        "name": mapped["name"],
        "category": mapped["category"],
        "sub_category": mapped["sub_category"],
        "price": mapped["_price"],
        "image": mapped["main_image_url"],
        "images": mapped["image_urls"],
        "shop_name": mapped["specifications"].get("shop_name", ""),
        "source": "jd",
    }


# ------------------------------------------------------------------
# 导入服务
# ------------------------------------------------------------------

class JdImportService:

    def __init__(self, db: Session):
        self._db = db
        self._client = _get_client(db=db)

    # ------------------------------------------------------------------
    # 批量导入
    # ------------------------------------------------------------------

    async def import_by_keyword(
        self,
        keyword: str,
        max_pages: int = 5,
        page_size: int = 30,
        created_by_id: Optional[int] = None,
    ) -> dict:
        """
        按关键词批量拉取京东商品并写入数据库。
        返回 { "imported": N, "skipped": N, "errors": N }
        """
        if self._client is None:
            raise RuntimeError("京东联盟 API 未配置，请在环境变量中设置 JD_APP_KEY 和 JD_SECRET_KEY")

        imported = skipped = errors = 0
        new_products = []

        for page in range(1, max_pages + 1):
            try:
                data = await self._client.search_goods(
                    keyword=keyword,
                    page_index=page,
                    page_size=page_size,
                )
            except JdApiError as e:
                logger.error(f"JD API 搜索失败 page={page}: {e}")
                errors += 1
                break

            goods_list = data.get("goodsResp") or data.get("data") or []
            if not goods_list:
                break

            for item in goods_list:
                try:
                    result = self._upsert_product(item, created_by_id=created_by_id)
                    if result == "skipped":
                        skipped += 1
                    else:
                        imported += 1
                        new_products.append(result)
                except Exception as e:
                    logger.warning(f"导入商品失败 skuId={item.get('skuId')}: {e}")
                    errors += 1

            self._db.commit()

            total = data.get("totalCount", 0)
            if page * page_size >= total:
                break

            await asyncio.sleep(0.2)

        # 导入完成后异步下载图片到本地
        if new_products:
            try:
                from app.services.image_download_service import ImageDownloadService
                image_svc = ImageDownloadService()
                for product in new_products:
                    try:
                        await image_svc.download_product_images(product, self._db)
                    except Exception as e:
                        logger.warning(f"图片下载失败 product_id={product.id}: {e}")
            except Exception as e:
                logger.warning(f"图片下载服务初始化失败: {e}")

        logger.info(f"JD 导入完成: keyword={keyword}, imported={imported}, skipped={skipped}, errors={errors}")
        return {"imported": imported, "skipped": skipped, "errors": errors}

    def _upsert_product(self, item: dict, created_by_id: Optional[int] = None):
        """插入或跳过（已存在则跳过）。返回 Product 对象或 "skipped"。"""
        mapped = _map_jd_goods_to_product(item)
        jd_sku_id = mapped.pop("_jd_sku_id")
        mapped.pop("_price", None)

        existing = (
            self._db.query(Product)
            .filter(
                func.json_unquote(
                    func.json_extract(Product.specifications, "$.jd_sku_id")
                ) == jd_sku_id
            )
            .first()
        )
        if existing:
            return "skipped"

        if created_by_id is None:
            raise ValueError("created_by_id is required to create a Product")

        product = Product(
            name=mapped["name"],
            description=mapped["description"],
            category=mapped["category"],
            sub_category=mapped["sub_category"],
            origin_province=mapped["origin_province"],
            main_image_url=mapped["main_image_url"],
            image_urls=mapped["image_urls"],
            specifications=mapped["specifications"],
            price=mapped.get("price", 0),
            status=mapped["status"],
            created_by=created_by_id,
        )

        self._db.add(product)
        return product

    # ------------------------------------------------------------------
    # 实时搜索代理（不写库）
    # ------------------------------------------------------------------

    async def search_realtime(
        self,
        keyword: str,
        page: int = 1,
        page_size: int = 20,
    ) -> dict:
        """
        实时搜索京东商品，格式化后直接返回，不写库。
        返回 { "items": [...], "total": N, "page": N, "page_size": N, "warning": str|None }
        """
        if self._client is None:
            raise RuntimeError("京东联盟 API 未配置")

        data = await self._client.search_goods(
            keyword=keyword,
            page_index=page,
            page_size=min(page_size, 30),
        )
        goods_list = data.get("goodsResp") or data.get("data") or []
        items = [_format_for_frontend(g) for g in goods_list]

        return {
            "items": items,
            "total": data.get("totalCount", len(items)),
            "page": page,
            "page_size": page_size,
            "warning": data.get("warning"),
        }


# ------------------------------------------------------------------
# 客户端单例（懒加载）
# ------------------------------------------------------------------

_client_instance: Optional[JdApiClient] = None


def _client_instance_reset() -> None:
    """重置客户端单例，下次调用 _get_client() 时用最新 token 重建。"""
    global _client_instance
    _client_instance = None


def _get_client(db=None) -> Optional[JdApiClient]:
    global _client_instance
    if _client_instance is not None:
        return _client_instance

    app_key = getattr(settings, "JD_APP_KEY", None)
    secret_key = getattr(settings, "JD_SECRET_KEY", None)
    if not app_key or not secret_key:
        return None

    # DB 优先读取 AccessToken（管理员可在前端更新），其次 .env
    access_token = getattr(settings, "JD_ACCESS_TOKEN", None) or None
    if db is not None:
        try:
            from app.models.system_config import SystemConfig
            row = db.query(SystemConfig).filter(SystemConfig.config_key == "jd_access_token").first()
            if row and row.config_value:
                val = row.config_value
                db_token = val.get("token") if isinstance(val, dict) else (val if isinstance(val, str) else None)
                if db_token:
                    access_token = db_token
        except Exception:
            pass

    _client_instance = JdApiClient(
        app_key=app_key,
        secret_key=secret_key,
        access_token=access_token,
    )
    return _client_instance

