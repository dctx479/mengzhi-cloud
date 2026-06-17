"""对账单解析器模块

提供微信/支付宝对账单文件解析能力。

支持的格式：
- WechatBillParser: 微信支付 CSV（GBK 编码）
- AlipayBillParser: 支付宝 CSV（UTF-8 BOM）
- GenericCSVParser: 通用 CSV 兜底解析器

设计原则：
- 单行解析失败不中断整体（graceful degradation）
- 编码自适应（UTF-8 BOM → UTF-8 → GBK）
- 文件大小保护（≤50MB）
- 安全：仅接受 reconciliation_bills/ 目录下的文件
"""
import csv
import os
from abc import ABC, abstractmethod
from datetime import datetime
from decimal import Decimal, InvalidOperation
from typing import List, Dict, Optional
from loguru import logger

from app.services.reconciliation_service import RemoteTransaction


MAX_FILE_SIZE_MB = 50
ALLOWED_DIR_PREFIX = "reconciliation_bills"


def _safe_open_bill_file(file_path: str) -> str:
    """安全打开对账单文件，校验路径与大小"""
    # 路径安全：禁止 .. 或绝对路径
    if ".." in file_path or os.path.isabs(file_path):
        raise ValueError(f"Invalid bill file path: {file_path}")
    if ALLOWED_DIR_PREFIX not in file_path:
        raise ValueError(f"Bill file must be under {ALLOWED_DIR_PREFIX}/")

    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Bill file not found: {file_path}")

    size_mb = os.path.getsize(file_path) / (1024 * 1024)
    if size_mb > MAX_FILE_SIZE_MB:
        raise ValueError(f"Bill file too large: {size_mb:.1f}MB > {MAX_FILE_SIZE_MB}MB")

    return file_path


class BillParser(ABC):
    """对账单解析器抽象基类"""

    @abstractmethod
    def parse(self, file_path: str) -> List[RemoteTransaction]:
        """解析对账文件为 RemoteTransaction 列表"""


class WechatBillParser(BillParser):
    """微信对账单 CSV 解析器

    微信账单字段（实际列名）：
    - 交易时间
    - 微信订单号
    - 商户订单号
    - 用户标识
    - 交易类型
    - 交易状态
    - 订单金额
    - 退款金额
    """

    def parse(self, file_path: str) -> List[RemoteTransaction]:
        """解析微信对账单

        微信账单使用 GBK 编码，字段顺序固定。
        """
        _safe_open_bill_file(file_path)

        results: List[RemoteTransaction] = []
        try:
            with open(file_path, "r", encoding="gbk", errors="replace") as f:
                reader = csv.DictReader(f)
                for line_no, row in enumerate(reader, start=2):
                    try:
                        # 微信订单号
                        transaction_id = (row.get("微信订单号") or "").strip()
                        if not transaction_id:
                            continue
                        order_no = (row.get("商户订单号") or "").strip()
                        # 订单金额（元）
                        amount_str = (row.get("订单金额") or "0").strip().replace("¥", "").replace(",", "")
                        try:
                            amount = Decimal(amount_str or "0")
                        except InvalidOperation:
                            logger.warning(f"[WechatBillParser] L{line_no} invalid amount: {amount_str}")
                            amount = Decimal("0")
                        # 退款金额
                        refund_str = (row.get("退款金额") or "0").strip().replace("¥", "").replace(",", "")
                        try:
                            refund = Decimal(refund_str or "0")
                            amount = amount - refund
                        except InvalidOperation:
                            pass
                        # 交易状态
                        status_raw = (row.get("交易状态") or "").strip()
                        status = "SUCCESS" if "成功" in status_raw or "已支付" in status_raw else "FAILED"
                        # 支付时间
                        paid_at_str = (row.get("交易时间") or "").strip()
                        try:
                            paid_at = datetime.strptime(paid_at_str, "%Y-%m-%d %H:%M:%S")
                        except ValueError:
                            paid_at = datetime.utcnow()

                        results.append(RemoteTransaction(
                            transaction_id=transaction_id,
                            order_no=order_no,
                            amount=amount,
                            status=status,
                            paid_at=paid_at,
                            channel="wechat",
                            raw_data=dict(row),
                        ))
                    except Exception as e:
                        logger.warning(f"[WechatBillParser] L{line_no} parse error, skipping: {e}")
                        continue
        except UnicodeDecodeError:
            logger.warning(f"[WechatBillParser] GBK decode failed, trying UTF-8")
            return self._parse_utf8_fallback(file_path)
        except Exception as e:
            logger.error(f"[WechatBillParser] failed to parse {file_path}: {e}")

        logger.info(f"[WechatBillParser] parsed {len(results)} transactions from {file_path}")
        return results

    def _parse_utf8_fallback(self, file_path: str) -> List[RemoteTransaction]:
        """UTF-8 fallback 解析（部分微信账单可能是 UTF-8）"""
        results: List[RemoteTransaction] = []
        try:
            with open(file_path, "r", encoding="utf-8", errors="replace") as f:
                reader = csv.DictReader(f)
                for line_no, row in enumerate(reader, start=2):
                    try:
                        transaction_id = (row.get("微信订单号") or "").strip()
                        if not transaction_id:
                            continue
                        results.append(RemoteTransaction(
                            transaction_id=transaction_id,
                            order_no=(row.get("商户订单号") or "").strip(),
                            amount=Decimal((row.get("订单金额") or "0").strip() or "0"),
                            status="SUCCESS" if "成功" in (row.get("交易状态") or "") else "FAILED",
                            paid_at=datetime.utcnow(),
                            channel="wechat",
                            raw_data=dict(row),
                        ))
                    except Exception as e:
                        logger.warning(f"[WechatBillParser][UTF8] L{line_no} parse error: {e}")
        except Exception as e:
            logger.error(f"[WechatBillParser][UTF8 fallback] {e}")
        return results


class AlipayBillParser(BillParser):
    """支付宝对账单 CSV 解析器

    支付宝账单字段：
    - 交易号
    - 商户订单号
    - 订单金额（元）
    - 退款金额（元）
    - 交易状态
    - 支付时间
    """

    def parse(self, file_path: str) -> List[RemoteTransaction]:
        _safe_open_bill_file(file_path)

        results: List[RemoteTransaction] = []
        try:
            # 支付宝常用 UTF-8-sig（带 BOM）
            with open(file_path, "r", encoding="utf-8-sig", errors="replace") as f:
                reader = csv.DictReader(f)
                for line_no, row in enumerate(reader, start=2):
                    try:
                        transaction_id = (row.get("交易号") or "").strip()
                        if not transaction_id:
                            continue
                        order_no = (row.get("商户订单号") or "").strip()
                        amount_str = (row.get("订单金额（元）") or "0").strip().replace(",", "")
                        try:
                            amount = Decimal(amount_str or "0")
                        except InvalidOperation:
                            amount = Decimal("0")
                        refund_str = (row.get("退款金额（元）") or "0").strip().replace(",", "")
                        try:
                            refund = Decimal(refund_str or "0")
                            amount = amount - refund
                        except InvalidOperation:
                            pass
                        status_raw = (row.get("交易状态") or "").strip()
                        status = "SUCCESS" if "成功" in status_raw or "已收款" in status_raw else "FAILED"
                        paid_at_str = (row.get("支付时间") or "").strip()
                        try:
                            paid_at = datetime.strptime(paid_at_str, "%Y-%m-%d %H:%M:%S")
                        except ValueError:
                            paid_at = datetime.utcnow()

                        results.append(RemoteTransaction(
                            transaction_id=transaction_id,
                            order_no=order_no,
                            amount=amount,
                            status=status,
                            paid_at=paid_at,
                            channel="alipay",
                            raw_data=dict(row),
                        ))
                    except Exception as e:
                        logger.warning(f"[AlipayBillParser] L{line_no} parse error, skipping: {e}")
                        continue
        except Exception as e:
            logger.error(f"[AlipayBillParser] failed to parse {file_path}: {e}")

        logger.info(f"[AlipayBillParser] parsed {len(results)} transactions from {file_path}")
        return results


class GenericCSVParser(BillParser):
    """通用 CSV 兜底解析器

    按列名约定识别字段：
    - transaction_id / 交易号 / 微信订单号
    - order_no / 商户订单号
    - amount / 金额 / 订单金额
    - status / 交易状态
    - paid_at / 支付时间 / 交易时间
    """

    TRANSACTION_ID_KEYS = ["transaction_id", "交易号", "微信订单号", "支付宝交易号"]
    ORDER_NO_KEYS = ["order_no", "商户订单号", "out_trade_no"]
    AMOUNT_KEYS = ["amount", "金额", "订单金额", "订单金额（元）"]
    STATUS_KEYS = ["status", "交易状态", "支付状态"]
    PAID_AT_KEYS = ["paid_at", "支付时间", "交易时间", "付款时间"]

    def parse(self, file_path: str) -> List[RemoteTransaction]:
        _safe_open_bill_file(file_path)

        results: List[RemoteTransaction] = []
        # 尝试多种编码
        for encoding in ["utf-8-sig", "utf-8", "gbk"]:
            try:
                with open(file_path, "r", encoding=encoding, errors="replace") as f:
                    reader = csv.DictReader(f)
                    rows = list(reader)
                    if not rows:
                        return []
                    # 自动探测列名
                    fieldnames = reader.fieldnames or []
                    tx_key = self._find_key(fieldnames, self.TRANSACTION_ID_KEYS)
                    order_key = self._find_key(fieldnames, self.ORDER_NO_KEYS)
                    amount_key = self._find_key(fieldnames, self.AMOUNT_KEYS)
                    status_key = self._find_key(fieldnames, self.STATUS_KEYS)
                    paid_at_key = self._find_key(fieldnames, self.PAID_AT_KEYS)

                    if not tx_key:
                        logger.warning(f"[GenericCSVParser] No transaction_id column found in {file_path}")
                        return []

                    for line_no, row in enumerate(rows, start=2):
                        try:
                            transaction_id = (row.get(tx_key) or "").strip()
                            if not transaction_id:
                                continue
                            try:
                                amount = Decimal((row.get(amount_key) or "0").strip() or "0")
                            except (InvalidOperation, AttributeError):
                                amount = Decimal("0")
                            try:
                                paid_at = datetime.strptime(
                                    (row.get(paid_at_key) or "").strip(),
                                    "%Y-%m-%d %H:%M:%S",
                                )
                            except (ValueError, AttributeError):
                                paid_at = datetime.utcnow()
                            status_raw = (row.get(status_key) or "").strip()
                            status = "SUCCESS" if any(k in status_raw for k in ["成功", "Success", "已支付", "已收款"]) else "FAILED"

                            results.append(RemoteTransaction(
                                transaction_id=transaction_id,
                                order_no=(row.get(order_key) or "").strip(),
                                amount=amount,
                                status=status,
                                paid_at=paid_at,
                                channel="generic",
                                raw_data=dict(row),
                            ))
                        except Exception as e:
                            logger.warning(f"[GenericCSVParser] L{line_no} parse error: {e}")
                break  # 编码成功，跳出循环
            except UnicodeDecodeError:
                continue
            except Exception as e:
                logger.error(f"[GenericCSVParser] {encoding} failed: {e}")
                continue

        logger.info(f"[GenericCSVParser] parsed {len(results)} transactions from {file_path}")
        return results

    @staticmethod
    def _find_key(fieldnames: List[str], candidates: List[str]) -> Optional[str]:
        for candidate in candidates:
            for field in fieldnames:
                if candidate.lower() == field.lower():
                    return field
        return None


def get_parser(channel: str) -> BillParser:
    """根据渠道获取对应解析器

    Args:
        channel: wechat / alipay / generic
    """
    channel = (channel or "").lower().strip()
    if channel == "wechat":
        return WechatBillParser()
    if channel == "alipay":
        return AlipayBillParser()
    return GenericCSVParser()