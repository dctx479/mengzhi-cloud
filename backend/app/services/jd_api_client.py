"""
京东联盟开放平台 API 客户端

文档: https://union.jd.com/openplatform/api
网关: https://api.jd.com/routerjson
签名: MD5(secretKey + ASCII排序参数键值对 + secretKey).upper()
业务参数键名: 360buy_param_json
"""

import hashlib
import json
import time
import asyncio
from datetime import datetime, timezone, timedelta
from typing import Any, Optional
from loguru import logger

import httpx

JD_API_GATEWAY = "https://api.jd.com/routerjson"
_DEFAULT_TIMEOUT = 10.0
# 基础权限: 10 QPS，用令牌桶限制到 8 QPS 留余量
_MIN_INTERVAL = 0.125  # 1/8 秒


class JdApiError(Exception):
    def __init__(self, code: str, message: str):
        self.code = code
        self.message = message
        super().__init__(f"[{code}] {message}")


class JdApiClient:
    """
    京东联盟 API 客户端（异步）

    使用方式:
        client = JdApiClient(app_key="xxx", secret_key="yyy")
        result = await client.call("jd.union.open.goods.search", {"keyword": "牛肉"})
    """

    def __init__(self, app_key: str, secret_key: str, access_token: Optional[str] = None):
        if not app_key or not secret_key:
            raise ValueError("app_key 和 secret_key 不能为空")
        self._app_key = app_key
        self._secret_key = secret_key
        self._access_token = access_token
        self._last_call_time = 0.0
        self._lock = asyncio.Lock()

    # ------------------------------------------------------------------
    # 签名
    # ------------------------------------------------------------------

    def _sign(self, params: dict[str, str]) -> str:
        """MD5 签名: secretKey + 按 ASCII 升序拼接 k+v + secretKey"""
        sorted_pairs = sorted(params.items())
        raw = self._secret_key + "".join(k + v for k, v in sorted_pairs) + self._secret_key
        return hashlib.md5(raw.encode("utf-8")).hexdigest().upper()

    def _build_params(self, method: str, biz_params: dict) -> dict[str, str]:
        params: dict[str, str] = {
            "v": "1.0",
            "method": method,
            "app_key": self._app_key,
            "timestamp": datetime.now(timezone(timedelta(hours=8))).strftime("%Y-%m-%d %H:%M:%S"),
            "format": "json",
            "sign_method": "md5",
            "360buy_param_json": json.dumps(biz_params, ensure_ascii=False),
        }
        if self._access_token:
            params["access_token"] = self._access_token
        params["sign"] = self._sign(params)
        return params

    # ------------------------------------------------------------------
    # 限流（令牌桶简化版）
    # ------------------------------------------------------------------

    async def _throttle(self) -> None:
        async with self._lock:
            now = time.monotonic()
            wait = _MIN_INTERVAL - (now - self._last_call_time)
            if wait > 0:
                await asyncio.sleep(wait)
            self._last_call_time = time.monotonic()

    # ------------------------------------------------------------------
    # 核心调用
    # ------------------------------------------------------------------

    async def call(self, method: str, biz_params: dict) -> Any:
        """
        调用京东联盟 API，返回业务数据（已解包 result 层）。
        失败时抛出 JdApiError。
        """
        await self._throttle()
        params = self._build_params(method, biz_params)

        async with httpx.AsyncClient(timeout=_DEFAULT_TIMEOUT) as client:
            resp = await client.get(JD_API_GATEWAY, params=params)
            resp.raise_for_status()
            body = resp.json()
        logger.debug(f"JD API {method} raw response: {body}")

        # 京东响应结构: { "<method_key>_response": { "result": "...", "code": 200 } }
        # 注意：京东部分接口返回 "responce"（拼写错误），需同时兼容
        method_key = method.replace(".", "_") + "_response"
        method_key_typo = method.replace(".", "_") + "_responce"  # 京东官方拼写错误
        actual_key = method_key if method_key in body else (method_key_typo if method_key_typo in body else None)
        if actual_key is None:
            # 顶层错误（签名失败等）
            err = body.get("error_response", {})
            code = str(err.get("error_code", ""))
            zh_desc = str(err.get("zh_desc", ""))
            en_desc = str(err.get("en_desc", ""))
            msg = zh_desc or en_desc or "京东API返回未知错误，请检查AppKey和签名配置"
            raise JdApiError(code or "API_ERROR", msg)

        response_obj = body[actual_key]
        code = response_obj.get("code", 0)
        # 京东部分接口用字符串 "0" 表示成功，整数 200 也表示成功
        code_ok = code in (200, "0", 0)
        if not code_ok:
            msg = response_obj.get("message") or response_obj.get("zh_desc") or f"API返回错误码 {code}"
            raise JdApiError(str(code), msg)

        result = response_obj.get("result", response_obj.get("queryResult", response_obj.get("data", {})))
        if isinstance(result, str):
            try:
                result = json.loads(result)
            except json.JSONDecodeError as e:
                raise JdApiError("PARSE_ERROR", f"无法解析API返回数据: {e}")

        # 解析后的 result 可能仍包含业务错误码（如 {"code":403,"message":"无访问权限"}）
        if isinstance(result, dict):
            inner_code = result.get("code")
            if inner_code and inner_code != 200 and inner_code != 0:
                inner_msg = result.get("message") or f"业务错误码 {inner_code}"
                raise JdApiError(str(inner_code), inner_msg)

        return result

    # ------------------------------------------------------------------
    # 业务封装
    # ------------------------------------------------------------------

    async def search_goods(
        self,
        keyword: str,
        page_index: int = 1,
        page_size: int = 30,
        sort_name: Optional[str] = None,
        sort: Optional[str] = None,
        price_from: Optional[int] = None,
        price_to: Optional[int] = None,
    ) -> dict:
        """
        关键词搜索商品。
        优先使用 goods.query（支持关键词搜索，需申请权限），
        权限不足时降级到 jingfen.query（精选商品 + 本地过滤）。
        返回: { "goodsResp": [...], "totalCount": N, "warning": str|None }
        """
        # 优先使用 goods.query（支持真正的关键词搜索）
        biz: dict[str, Any] = {
            "goodsReqDTO": {
                "keyword": keyword,
                "pageIndex": page_index,
                "pageSize": min(page_size, 30),
            }
        }
        if sort_name:
            biz["goodsReqDTO"]["sortName"] = sort_name
        if sort:
            biz["goodsReqDTO"]["sort"] = sort
        if price_from is not None:
            biz["goodsReqDTO"]["priceFrom"] = price_from
        if price_to is not None:
            biz["goodsReqDTO"]["priceTo"] = price_to

        try:
            result = await self.call("jd.union.open.goods.query", biz)
            goods_list = result.get("data") or result.get("goodsResp") or []
            return {"goodsResp": goods_list, "totalCount": result.get("totalCount", len(goods_list)), "warning": None}
        except JdApiError as e:
            if "50030" not in str(e.code) and "50200" not in str(e.code) and "无访问权限" not in str(e.message) and "403" not in str(e.code):
                raise
            logger.warning(f"goods.query 无权限 ({e.code}): {e.message}，降级到 jingfen.query")

        # 降级: jingfen.query（精选商品，不支持关键词，本地过滤）
        try:
            biz_jf: dict[str, Any] = {
                "goodsReqDTO": {
                    "eliteId": 22,
                    "pageIndex": page_index,
                    "pageSize": min(page_size, 30),
                }
            }
            result = await self.call("jd.union.open.goods.jingfen.query", biz_jf)
            goods_list = result.get("data") or result.get("goodsResp") or []
            if keyword:
                kw_lower = keyword.lower()
                goods_list = [
                    g for g in goods_list
                    if kw_lower in (g.get("skuName") or "").lower()
                    or kw_lower in (g.get("categoryInfo", {}).get("cid3Name") or "").lower()
                ]
            return {
                "goodsResp": goods_list,
                "totalCount": len(goods_list),
                "warning": "当前使用精选商品接口（结果有限），建议在京东联盟后台申请「商品查询」高级接口权限以获取完整搜索功能",
            }
        except JdApiError:
            raise JdApiError("403", "商品搜索需要京东联盟高级权限，请在联盟后台申请「商品查询」接口权限")

    async def get_goods_detail(self, sku_ids: list[int]) -> list[dict]:
        """
        批量查询商品详情，每次最多 10 个 SKU。
        返回商品列表。
        """
        if not sku_ids:
            return []

        results: list[dict] = []
        # 每批最多 10 个
        for i in range(0, len(sku_ids), 10):
            batch = sku_ids[i : i + 10]
            biz = {"skuIds": ",".join(str(s) for s in batch)}
            data = await self.call("jd.union.open.goods.detail.query", biz)
            items = data if isinstance(data, list) else data.get("goodsResp", [])
            results.extend(items)

        return results
