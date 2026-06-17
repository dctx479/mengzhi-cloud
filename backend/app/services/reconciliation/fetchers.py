"""对账单下载器模块

提供微信/支付宝对账单下载能力。

模式：
- Mock（默认）：返回示例账单路径，不实际下载
- 真实：通过 HTTP API 调用（环境变量配置密钥后启用）

环境变量：
- WECHAT_BILL_API_KEY: 微信账单 API 密钥（非空时启用真实模式）
- ALIPAY_BILL_API_KEY: 支付宝账单 API 密钥（非空时启用真实模式）
"""
import os
import hashlib
from abc import ABC, abstractmethod
from datetime import date
from typing import Optional
from loguru import logger

from app.core.config import settings


BILLS_DIR = "backend/data/reconciliation_bills"


class BillFetcher(ABC):
    """对账单获取器抽象基类"""

    @abstractmethod
    def fetch(self, bill_date: date) -> Optional[str]:
        """下载对账文件到本地，返回文件路径；失败返回 None"""

    @abstractmethod
    def query_transaction(self, transaction_id: str) -> Optional[str]:
        """查询第三方交易状态，返回状态字符串（SUCCESS/FAILED/PENDING）"""


class WechatBillFetcher(BillFetcher):
    """微信对账单下载器"""

    def __init__(self):
        self.api_key = os.getenv("WECHAT_BILL_API_KEY", "")
        self.real_mode = bool(self.api_key)

    def fetch(self, bill_date: date) -> Optional[str]:
        if self.real_mode:
            return self._fetch_real(bill_date)
        return self._fetch_mock(bill_date)

    def _fetch_mock(self, bill_date: date) -> Optional[str]:
        """Mock 模式：返回示例账单路径（若文件不存在则跳过）"""
        sample_path = os.path.join(BILLS_DIR, "wechat_sample.csv")
        if os.path.exists(sample_path):
            logger.info(f"[WechatBillFetcher][MOCK] Using sample bill: {sample_path}")
            return sample_path
        logger.info(f"[WechatBillFetcher][MOCK] No sample bill, returning None")
        return None

    def _fetch_real(self, bill_date: date) -> Optional[str]:
        """真实模式：调用微信账单 API（框架代码，未实际发送）"""
        logger.warning(
            f"[WechatBillFetcher][REAL] Would call WeChat bill API for date={bill_date} "
            f"api_key=***{self.api_key[-4:] if len(self.api_key) >= 4 else '****'}"
        )
        # TODO (production): 实际 HTTP 调用实现：
        # 1. 构造请求：date, mch_id, sign(MD5(key+date))
        # 2. POST https://api.mch.weixin.qq.com/v3/bill/tradebill
        # 3. 下载 zip → 解压 → 解析 csv
        # 当前实现：仅日志 + 返回 None
        return None

    def query_transaction(self, transaction_id: str) -> Optional[str]:
        if self.real_mode:
            logger.warning(
                f"[WechatBillFetcher][REAL] Would query WeChat transaction {transaction_id}"
            )
            # TODO (production): 调用微信查询订单 API
            return None
        logger.info(
            f"[WechatBillFetcher][MOCK] Query transaction {transaction_id}: SUCCESS"
        )
        return "SUCCESS"


class AlipayBillFetcher(BillFetcher):
    """支付宝对账单下载器"""

    def __init__(self):
        self.api_key = os.getenv("ALIPAY_BILL_API_KEY", "")
        self.real_mode = bool(self.api_key)

    def fetch(self, bill_date: date) -> Optional[str]:
        if self.real_mode:
            return self._fetch_real(bill_date)
        return self._fetch_mock(bill_date)

    def _fetch_mock(self, bill_date: date) -> Optional[str]:
        sample_path = os.path.join(BILLS_DIR, "alipay_sample.csv")
        if os.path.exists(sample_path):
            logger.info(f"[AlipayBillFetcher][MOCK] Using sample bill: {sample_path}")
            return sample_path
        return None

    def _fetch_real(self, bill_date: date) -> Optional[str]:
        logger.warning(
            f"[AlipayBillFetcher][REAL] Would call Alipay bill API for date={bill_date} "
            f"api_key=***{self.api_key[-4:] if len(self.api_key) >= 4 else '****'}"
        )
        # TODO (production): 调用支付宝账单查询接口
        return None

    def query_transaction(self, transaction_id: str) -> Optional[str]:
        if self.real_mode:
            logger.warning(
                f"[AlipayBillFetcher][REAL] Would query Alipay transaction {transaction_id}"
            )
            return None
        logger.info(
            f"[AlipayBillFetcher][MOCK] Query transaction {transaction_id}: SUCCESS"
        )
        return "SUCCESS"


def get_fetcher(channel: str) -> BillFetcher:
    """根据渠道获取对应下载器"""
    channel = (channel or "").lower().strip()
    if channel == "wechat":
        return WechatBillFetcher()
    if channel == "alipay":
        return AlipayBillFetcher()
    raise ValueError(f"Unknown bill channel: {channel}")