"""
淘宝联盟开放平台 API 客户端

文档: https://open.taobao.com/api.htm?docId=24515&docType=2
网关: https://eco.taobao.com/router/rest
签名: HMAC-MD5(secretKey, ASCII排序参数键值对拼接)，结果转大写十六进制

主要接口:
  taobao.tbk.dg.item.search   — 商品搜索（需申请权限）
  taobao.tbk.item.info.get    — 商品详情
  taobao.tbk.dg.optimus.material — 智能物料推荐（无需额外权限）
"""

import hashlib
import hmac
import json
import time
import asyncio
from datetime import datetime, timezone, timedelta
from typing import Any, Optional
from loguru import logger

import httpx

TAOBAO_API_GATEWAY = "https://eco.taobao.com/router/rest"
_DEFAULT_TIMEOUT = 15.0
# 淘宝联盟基础权限: 10 QPS，限制到 8 QPS
_MIN_INTERVAL = 0.125


class TaobaoApiError(Exception):
    def __init__(self, code: str, message: str, sub_code: str = "", sub_msg: str = ""):
        self.code = code
        self.message = message
        self.sub_code = sub_code
        self.sub_msg = sub_msg
        super().__init__(f"[{code}] {message}" + (f" ({sub_code}: {sub_msg})" if sub_code else ""))


class TaobaoApiClient:
    """
    淘宝联盟 API 客户端（异步）

    使用方式:
        client = TaobaoApiClient(app_key="xxx", app_secret="yyy", session="zzz")
        result = await client.call("taobao.tbk.dg.item.search", {"q": "牛肉"})
    """

    def __init__(self, app_key: str, app_secret: str, session: Optional[str] = None):
        if not app_key or not app_secret:
            raise ValueError("app_key 和 app_secret 不能为空")
        self._app_key = app_key
        self._app_secret = app_secret
        self._session = session  # access_token（淘宝称为 session）
        self._last_call_time = 0.0
        self._lock = asyncio.Lock()

    # ------------------------------------------------------------------
    # 签名
    # ------------------------------------------------------------------

    def _sign(self, params: dict[str, str]) -> str:
        """
        HMAC-MD5 签名:
        1. 按参数名 ASCII 升序排列
        2. 拼接: key1value1key2value2...
        3. HMAC-MD5(app_secret, 拼接串)，结果转大写十六进制
        """
        sorted_pairs = sorted(params.items())
        raw = "".join(k + v for k, v in sorted_pairs)
        digest = hmac.new(
            self._app_secret.encode("utf-8"),
            raw.encode("utf-8"),
            hashlib.md5,
        ).hexdigest().upper()
        return digest

    def _build_params(self, method: str, biz_params: dict) -> dict[str, str]:
        """构建公共参数 + 业务参数，并附加签名。"""
        now = datetime.now(timezone(timedelta(hours=8)))
        params: dict[str, str] = {
            "method": method,
            "app_key": self._app_key,
            "sign_method": "hmac",
            "timestamp": now.strftime("%Y-%m-%d %H:%M:%S"),
            "format": "json",
            "v": "2.0",
            "partner_id": "apidoc",
        }
        if self._session:
            params["session"] = self._session

        # 业务参数展开到顶层（淘宝 TOP 协议）
        for k, v in biz_params.items():
            if isinstance(v, (dict, list)):
                params[k] = json.dumps(v, ensure_ascii=False)
            else:
                params[k] = str(v)

        params["sign"] = self._sign(params)
        return params

    # ------------------------------------------------------------------
    # 限流
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
        调用淘宝联盟 API，返回业务数据（已解包 result 层）。
        失败时抛出 TaobaoApiError。
        """
        await self._throttle()
        params = self._build_params(method, biz_params)

        async with httpx.AsyncClient(timeout=_DEFAULT_TIMEOUT) as client:
            resp = await client.post(TAOBAO_API_GATEWAY, data=params)
            resp.raise_for_status()
            body = resp.json()

        logger.debug(f"Taobao API {method} raw response: {body}")

        # 顶层错误（签名失败、参数错误等）
        if "error_response" in body:
            err = body["error_response"]
            code = str(err.get("code", ""))
            msg = err.get("zh_desc") or err.get("msg") or "淘宝API返回未知错误"
            sub_code = str(err.get("sub_code", ""))
            sub_msg = str(err.get("sub_msg", ""))
            raise TaobaoApiError(code, msg, sub_code, sub_msg)

        # 正常响应: { "<method_key>_response": { ... } }
        method_key = method.replace(".", "_") + "_response"
        if method_key not in body:
            raise TaobaoApiError("PARSE_ERROR", f"响应中缺少 {method_key} 字段，原始响应: {body}")

        return body[method_key]

    # ------------------------------------------------------------------
    # 业务封装
    # ------------------------------------------------------------------

    async def search_items(
        self,
        keyword: str,
        page_no: int = 1,
        page_size: int = 40,
        sort: Optional[str] = None,
        cat: Optional[str] = None,
        adzone_id: Optional[str] = None,
    ) -> dict:
        """
        关键词搜索淘宝联盟商品。
        优先使用 tbk.dg.item.search（需申请权限），
        权限不足时降级到 tbk.dg.optimus.material（智能物料，无需额外权限）。

        返回: { "items": [...], "total_count": N, "warning": str|None }
        """
        biz: dict[str, Any] = {
            "q": keyword,
            "page_no": page_no,
            "page_size": min(page_size, 100),
            "fields": "num_iid,title,pict_url,small_images,reserve_price,zk_final_price,user_type,provcity,item_url,seller_id,volume,nick,shop_title,category_id",
        }
        if sort:
            biz["sort"] = sort
        if cat:
            biz["cat"] = cat
        if adzone_id:
            biz["adzone_id"] = adzone_id

        try:
            result = await self.call("taobao.tbk.dg.item.search", biz)
            result_list = result.get("result", {})
            items = result_list.get("result_list", {}).get("map_data", []) if isinstance(result_list, dict) else []
            total = result_list.get("total_results", len(items)) if isinstance(result_list, dict) else len(items)
            return {"items": items, "total_count": total, "warning": None}
        except TaobaoApiError as e:
            # 权限不足时降级
            no_perm = (
                e.sub_code in ("invalid-sessionkey", "permission-api-app-not-apply", "permission-api-app-not-open")
                or "permission" in e.sub_code.lower()
                or "27" in e.code  # 27 = 无权限
            )
            if not no_perm:
                raise
            logger.warning(f"tbk.dg.item.search 无权限 ({e.code}/{e.sub_code})，降级到 optimus.material")

        # 降级: 智能物料推荐（不支持关键词，本地过滤）
        try:
            biz_opt: dict[str, Any] = {
                "adzone_id": adzone_id or "0",
                "page_no": page_no,
                "page_size": min(page_size, 20),
                "material_id": "6",  # 6 = 猜你喜欢
            }
            result = await self.call("taobao.tbk.dg.optimus.material", biz_opt)
            result_list = result.get("result", {})
            items = result_list.get("result_list", {}).get("map_data", []) if isinstance(result_list, dict) else []
            if keyword:
                kw_lower = keyword.lower()
                items = [
                    it for it in items
                    if kw_lower in (it.get("item_info", {}).get("title") or "").lower()
                ]
            return {
                "items": items,
                "total_count": len(items),
                "warning": "当前使用智能物料接口（结果有限），建议在淘宝联盟后台申请「商品搜索」接口权限以获取完整搜索功能",
            }
        except TaobaoApiError:
            raise TaobaoApiError(
                "PERMISSION",
                "商品搜索需要淘宝联盟接口权限，请在开放平台申请「taobao.tbk.dg.item.search」接口权限",
            )

    async def get_item_detail(self, num_iids: list[int], adzone_id: Optional[str] = None) -> list[dict]:
        """
        批量查询商品详情，每次最多 40 个。
        返回商品列表。
        """
        if not num_iids:
            return []

        results: list[dict] = []
        for i in range(0, len(num_iids), 40):
            batch = num_iids[i: i + 40]
            biz: dict[str, Any] = {
                "num_iids": ",".join(str(n) for n in batch),
                "fields": "num_iid,title,pict_url,small_images,reserve_price,zk_final_price,user_type,provcity,item_url,seller_id,volume,nick,shop_title,category_id",
            }
            if adzone_id:
                biz["adzone_id"] = adzone_id
            data = await self.call("taobao.tbk.item.info.get", biz)
            items = data.get("result", {}).get("result_list", {}).get("map_data", [])
            results.extend(items if isinstance(items, list) else [])

        return results
