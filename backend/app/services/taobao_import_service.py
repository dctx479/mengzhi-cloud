"""
淘宝联盟商品导入服务

职责:
- 将淘宝联盟 API 返回的商品数据映射到本平台 Product 模型
- 批量导入（去重、跳过已存在）
- 实时搜索代理（不写库，直接返回格式化结果）
"""

from __future__ import annotations

import asyncio
from typing import Optional
from loguru import logger
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models.product import Product, ProductStatus
from app.services.taobao_api_client import TaobaoApiClient, TaobaoApiError
from app.core.config import settings


# ------------------------------------------------------------------
# 字段映射
# ------------------------------------------------------------------

def _extract_item_info(item: dict) -> dict:
    """
    淘宝联盟商品结构有多种形态:
    - 升级版 API: { "item_basic_info": {...}, "price_promotion_info": {...} }
    - 旧版 API:   { "item_info": {...} } 或顶层直接包含字段
    统一提取并合并为扁平字典。
    """
    basic = item.get("item_basic_info") or item.get("item_info") or {}
    price = item.get("price_promotion_info") or {}
    if basic:
        merged = {**basic, **price}
        if "item_id" in item:
            merged.setdefault("item_id", item["item_id"])
        return merged
    return item


def _map_taobao_item_to_product(item: dict) -> dict:
    """
    将淘宝联盟商品字段映射到本平台 Product 字段。
    兼容升级版和旧版 API 字段。
    """
    info = _extract_item_info(item)

    # 图片
    main_image = info.get("pict_url", "")
    if main_image and main_image.startswith("//"):
        main_image = "https:" + main_image

    small_images_raw = info.get("small_images") or {}
    if isinstance(small_images_raw, dict):
        small_list = small_images_raw.get("string", [])
    elif isinstance(small_images_raw, list):
        small_list = small_images_raw
    else:
        small_list = []

    image_urls = []
    if main_image:
        image_urls.append(main_image)
    for url in small_list:
        if url and url.startswith("//"):
            url = "https:" + url
        if url and url not in image_urls:
            image_urls.append(url)

    # 价格（升级版用 final_promotion_price / zk_final_price，旧版用 zk_final_price）
    price_str = info.get("final_promotion_price") or info.get("zk_final_price") or info.get("reserve_price") or "0"
    try:
        price = float(price_str)
    except (ValueError, TypeError):
        price = 0.0

    # 地区 / 类目
    provcity = info.get("provcity", "") or ""
    province = provcity.split(" ")[0] if provcity else "未知"

    category_id = str(info.get("category_id", ""))
    category_name = info.get("category_name", "")
    shop_title = info.get("shop_title") or info.get("nick") or ""
    title = (info.get("title") or "").strip()
    # 升级版用加密的 item_id，旧版用 num_iid
    item_id = str(info.get("item_id") or info.get("num_iid", ""))
    # 销量：升级版用 annual_vol / tk_total_sales，旧版用 volume
    volume = info.get("annual_vol") or info.get("tk_total_sales") or info.get("volume")

    return {
        "name": title[:200] if title else f"TB-{item_id}",
        "description": title,
        "category": category_name or "淘宝商品",
        "sub_category": category_id[:100] if category_id else None,
        "origin_province": province[:50],
        "main_image_url": main_image,
        "image_urls": image_urls,
        "specifications": {
            "tb_num_iid": item_id,
            "shop_title": shop_title,
            "price": price,
            "provcity": provcity,
            "category_id": category_id,
            "volume": volume,
            "item_url": info.get("item_url", ""),
        },
        "status": ProductStatus.PUBLISHED,
        "_tb_num_iid": item_id,
        "_price": price,
    }


def _format_for_frontend(item: dict) -> dict:
    """将淘宝原始商品格式化为前端期望的结构（实时搜索用，不写库）。"""
    mapped = _map_taobao_item_to_product(item)
    info = _extract_item_info(item)
    return {
        "tb_num_iid": mapped["_tb_num_iid"],
        "name": mapped["name"],
        "category": mapped["category"],
        "sub_category": mapped["sub_category"],
        "price": mapped["_price"],
        "image": mapped["main_image_url"],
        "images": mapped["image_urls"],
        "shop_title": mapped["specifications"].get("shop_title", ""),
        "provcity": mapped["specifications"].get("provcity", ""),
        "volume": mapped["specifications"].get("volume"),
        "item_url": mapped["specifications"].get("item_url", ""),
        "source": "taobao",
    }


# ------------------------------------------------------------------
# 导入服务
# ------------------------------------------------------------------

class TaobaoImportService:

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
        page_size: int = 40,
        created_by_id: Optional[int] = None,
        adzone_id: Optional[str] = None,
    ) -> dict:
        """
        按关键词批量拉取淘宝联盟商品并写入数据库。
        返回 { "imported": N, "skipped": N, "errors": N }
        """
        if self._client is None:
            raise RuntimeError("淘宝联盟 API 未配置，请在环境变量中设置 TAOBAO_APP_KEY 和 TAOBAO_APP_SECRET")

        imported = skipped = errors = 0

        for page in range(1, max_pages + 1):
            try:
                data = await self._client.search_items(
                    keyword=keyword,
                    page_no=page,
                    page_size=page_size,
                    adzone_id=adzone_id or getattr(settings, "TAOBAO_ADZONE_ID", None),
                )
            except TaobaoApiError as e:
                logger.error(f"淘宝联盟 API 搜索失败 page={page}: {e}")
                errors += 1
                break

            items = data.get("items") or []
            if not items:
                break

            for item in items:
                try:
                    result = self._upsert_product(item, created_by_id=created_by_id)
                    if result == "imported":
                        imported += 1
                    else:
                        skipped += 1
                except Exception as e:
                    info = _extract_item_info(item)
                    logger.warning(f"导入商品失败 num_iid={info.get('num_iid')}: {e}")
                    errors += 1

            self._db.commit()

            total = data.get("total_count", 0)
            if page * page_size >= total:
                break

            await asyncio.sleep(0.2)

        logger.info(f"淘宝联盟导入完成: keyword={keyword}, imported={imported}, skipped={skipped}, errors={errors}")
        return {"imported": imported, "skipped": skipped, "errors": errors}

    def _upsert_product(self, item: dict, created_by_id: Optional[int] = None) -> str:
        """插入或跳过（已存在则跳过）。返回 "imported" 或 "skipped"。"""
        mapped = _map_taobao_item_to_product(item)
        tb_num_iid = mapped.pop("_tb_num_iid")
        mapped.pop("_price", None)

        existing = (
            self._db.query(Product)
            .filter(
                func.json_unquote(
                    func.json_extract(Product.specifications, "$.tb_num_iid")
                ) == tb_num_iid
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
            status=mapped["status"],
            created_by=created_by_id,
        )
        self._db.add(product)
        return "imported"

    # ------------------------------------------------------------------
    # 实时搜索代理（不写库）
    # ------------------------------------------------------------------

    async def search_realtime(
        self,
        keyword: str,
        page: int = 1,
        page_size: int = 20,
        adzone_id: Optional[str] = None,
    ) -> dict:
        """
        实时搜索淘宝联盟商品，格式化后直接返回，不写库。
        返回 { "items": [...], "total": N, "page": N, "page_size": N, "warning": str|None }
        """
        if self._client is None:
            raise RuntimeError("淘宝联盟 API 未配置")

        data = await self._client.search_items(
            keyword=keyword,
            page_no=page,
            page_size=min(page_size, 40),
            adzone_id=adzone_id or getattr(settings, "TAOBAO_ADZONE_ID", None),
        )
        items = [_format_for_frontend(it) for it in (data.get("items") or [])]

        return {
            "items": items,
            "total": data.get("total_count", len(items)),
            "page": page,
            "page_size": page_size,
            "warning": data.get("warning"),
        }


# ------------------------------------------------------------------
# 客户端单例（懒加载）
# ------------------------------------------------------------------

_client_instance: Optional[TaobaoApiClient] = None


def _client_instance_reset() -> None:
    """重置客户端单例，下次调用 _get_client() 时用最新配置重建。"""
    global _client_instance
    _client_instance = None


def _get_client(db=None) -> Optional[TaobaoApiClient]:
    global _client_instance
    if _client_instance is not None:
        return _client_instance

    app_key = getattr(settings, "TAOBAO_APP_KEY", None)
    app_secret = getattr(settings, "TAOBAO_APP_SECRET", None)
    if not app_key or not app_secret:
        return None

    # DB 优先读取 session（管理员可在前端通过 OAuth2 授权更新），其次 .env
    session = getattr(settings, "TAOBAO_SESSION", None) or None
    if db is not None:
        try:
            from app.models.system_config import SystemConfig
            row = db.query(SystemConfig).filter(SystemConfig.config_key == "taobao_session").first()
            if row and isinstance(row.config_value, dict):
                db_session = row.config_value.get("session")
                if db_session:
                    session = db_session
        except Exception:
            pass

    _client_instance = TaobaoApiClient(
        app_key=app_key,
        app_secret=app_secret,
        session=session,
    )
    return _client_instance
