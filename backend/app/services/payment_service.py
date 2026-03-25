"""
支付服务层

版本: 1.0
创建日期: 2026-01-23
"""

from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from datetime import datetime
from loguru import logger
import json
import secrets
import hashlib
from decimal import Decimal
import time
import asyncio

from app.models.payment import Payment, PaymentMethod, PaymentStatus
from app.models.order import Order, OrderStatus
from app.models.user import User
from app.core.errors import BusinessException, ErrorCode, RecordNotFoundError
from app.core.config import settings
from app.core.metrics import (
    track_payment_request,
    track_payment_success,
    track_payment_failure,
    track_payment_duration,
    track_payment_callback,
    track_signature_verification,
    track_amount_verification,
    track_quota_grant,
    track_order_creation,
    track_order_completion,
    increment_concurrent_payments,
    decrement_concurrent_payments
)

# 导入风控服务
from app.services.risk_control_service import get_risk_control_service
from app.models.risk_control import EventType, RiskAction


class PaymentService:
    """支付服务类

    提供支付相关的业务逻辑操作:
    - 创建支付
    - 查询支付状态
    - 处理支付回调
    - 支付成功后的订单处理
    """

    def __init__(self, db: Session) -> None:
        """初始化服务

        Args:
            db: SQLAlchemy数据库会话
        """
        self.db = db

    def create_payment(
        self,
        order_id: int,
        payment_method: str,
        user_id: int,
        context: Optional[Dict[str, Any]] = None
    ) -> Payment:
        """创建支付

        Args:
            order_id: 订单ID
            payment_method: 支付方式(alipay/wechat/balance)
            user_id: 用户ID
            context: 请求上下文信息(IP、设备指纹等)

        Returns:
            创建的支付对象

        Raises:
            BusinessException: 订单不存在、订单状态不正确、风险检查不通过等
        """
        start_time = time.time()
        increment_concurrent_payments()

        try:
            # P1-11: 使用悲观锁防止并发创建多个支付记录
            # 获取订单并加锁
            order = self.db.query(Order).filter(Order.id == order_id).with_for_update().first()
            if not order:
                # P2-14: 订单不存在是正常的查询结果，使用info级别
                logger.info(f"订单不存在: {order_id}")
                track_payment_request(payment_method, "order_not_found")
                raise RecordNotFoundError("订单")

            # 验证订单所有权
            if order.user_id != user_id:
                logger.warning(f"用户{user_id}无权支付订单{order_id}")
                track_payment_request(payment_method, "permission_denied")
                raise BusinessException(
                    code=ErrorCode.PERMISSION_DENIED,
                    message="无权支付此订单"
                )

            # 验证订单状态
            if not order.can_pay():
                logger.warning(f"订单{order_id}状态不允许支付: {order.status}")
                track_payment_request(payment_method, "invalid_order_status")
                raise BusinessException(
                    code=ErrorCode.PARAM_ERROR,
                    message="订单状态不允许支付"
                )

            # 验证支付方式
            try:
                payment_method_enum = PaymentMethod(payment_method)
            except ValueError:
                logger.warning(f"不支持的支付方式: {payment_method}")
                track_payment_request(payment_method, "invalid_payment_method")
                raise BusinessException(
                    code=ErrorCode.PARAM_VALUE_INVALID,
                    message="不支持的支付方式"
                )

            # 风险检查
            risk_result = self._check_payment_risk(order, user_id, payment_method, context)

            # 根据风险检查结果决定是否继续
            if risk_result["action"] == RiskAction.BLOCK.value:
                logger.warning(f"支付被风控拦截: order_id={order_id}, user_id={user_id}, risk_score={risk_result['risk_score']}")
                track_payment_request(payment_method, "risk_blocked")
                raise BusinessException(
                    code=ErrorCode.RISK_CONTROL_BLOCKED,
                    message="支付存在风险，已被系统拦截"
                )
            elif risk_result["action"] == RiskAction.REVIEW.value:
                logger.info(f"支付需要人工审核: order_id={order_id}, user_id={user_id}, risk_score={risk_result['risk_score']}")
                track_payment_request(payment_method, "risk_review")
                # 创建待审核的支付记录
                return self._create_pending_review_payment(order, payment_method_enum, risk_result)
            elif risk_result["action"] == RiskAction.DELAY.value:
                logger.info(f"支付延迟处理: order_id={order_id}, user_id={user_id}, risk_score={risk_result['risk_score']}")
                track_payment_request(payment_method, "risk_delay")
                # 延迟一段时间后继续处理
                # P0-001修复: 使用异步事件循环执行延迟，避免阻塞请求线程
                try:
                    loop = asyncio.get_event_loop()
                    if loop.is_running():
                        # 在已运行的事件循环中，创建任务但不阻塞
                        logger.info(f"风控延迟处理: 记录延迟标记，后续异步处理")
                    else:
                        loop.run_until_complete(asyncio.sleep(2))
                except RuntimeError:
                    # 没有事件循环时，使用同步延迟（仅用于非异步上下文）
                    logger.warning("无法使用异步延迟，使用同步延迟（非生产环境）")
                    time.sleep(2)

            try:
                # 检查是否已有待支付的支付记录（使用悲观锁防止并发重复创建）
                existing_payment = self.db.query(Payment).filter(
                    Payment.order_id == order_id,
                    Payment.status == PaymentStatus.PENDING
                ).with_for_update().first()

                if existing_payment:
                    logger.info(f"订单{order_id}已有待支付记录，返回现有支付")
                    track_payment_request(payment_method, "existing_pending")
                    return existing_payment

                # 生成支付单号
                payment_no = self._generate_payment_no()

                # 创建支付记录
                payment = Payment(
                    payment_no=payment_no,
                    order_id=order_id,
                    amount=order.amount,
                    payment_method=payment_method_enum,
                    status=PaymentStatus.PENDING
                )

                self.db.add(payment)
                self.db.commit()
                self.db.refresh(payment)

                logger.info(f"支付创建成功: {payment.payment_no} (order_id={order_id}, method={payment_method}, risk_score={risk_result['risk_score']})")
                track_payment_request(payment_method, "created")

                # 根据支付方式处理
                if settings.PAYMENT_DEV_MODE:
                    # 开发模式：自动完成支付
                    logger.info(f"开发模式：自动完成支付 {payment.payment_no}")
                    self._process_dev_payment(payment, order)
                else:
                    # 生产模式：调用第三方支付
                    if payment_method == "alipay":
                        self._process_alipay(payment, order)
                    elif payment_method == "wechat":
                        self._process_wechat(payment, order)
                    elif payment_method == "balance":
                        self._process_balance(payment, order, user_id)

                return payment

            except Exception as e:
                self.db.rollback()
                logger.error(f"创建支付失败: {str(e)}")
                track_payment_failure(payment_method, "creation_failed")
                raise BusinessException(
                    code=ErrorCode.DB_INSERT_FAILED,
                    message="创建支付失败"
                )
        finally:
            duration = time.time() - start_time
            track_payment_duration(payment_method, "create_payment", duration)
            decrement_concurrent_payments()

    def get_payment_status(self, order_id: int, user_id: int) -> Dict[str, Any]:
        """查询支付状态

        Args:
            order_id: 订单ID
            user_id: 用户ID

        Returns:
            支付状态信息
        """
        # 获取订单
        order = self.db.query(Order).filter(Order.id == order_id).first()
        if not order:
            raise RecordNotFoundError("订单")

        # 验证订单所有权
        if order.user_id != user_id:
            raise BusinessException(
                code=ErrorCode.PERMISSION_DENIED,
                message="无权查询此订单"
            )

        # 获取最新的支付记录
        payment = self.db.query(Payment).filter(
            Payment.order_id == order_id
        ).order_by(Payment.created_at.desc()).first()

        if not payment:
            return {
                "order_id": order_id,
                "order_status": order.status.value,
                "payment_status": None,
                "paid": False
            }

        return {
            "order_id": order_id,
            "order_status": order.status.value,
            "payment_id": payment.id,
            "payment_no": payment.payment_no,
            "payment_method": payment.payment_method.value,
            "payment_status": payment.status.value,
            "amount": float(payment.amount),
            "paid": payment.is_success(),
            "paid_at": payment.paid_at.isoformat() if payment.paid_at else None,
            "transaction_id": payment.transaction_id
        }

    def handle_payment_callback(
        self,
        payment_no: str,
        callback_data: Dict[str, Any]
    ) -> bool:
        """处理支付回调

        Args:
            payment_no: 支付单号
            callback_data: 回调数据

        Returns:
            是否处理成功
        """
        start_time = time.time()

        payment = self.db.query(Payment).filter(
            Payment.payment_no == payment_no
        ).with_for_update().first()

        if not payment:
            # P2-14: 支付记录不存在是正常的查询结果，使用info级别
            logger.info(f"支付记录不存在: {payment_no}")
            return False

        payment_method = payment.payment_method.value

        # 如果已经支付成功，直接返回
        if payment.is_success():
            logger.info(f"支付{payment_no}已经成功，跳过处理")
            duration = time.time() - start_time
            track_payment_callback(payment_method, "already_success", duration)
            return True

        try:
            # 验证回调签名（生产环境需要实现）
            if not settings.PAYMENT_DEV_MODE:
                if payment.payment_method == PaymentMethod.ALIPAY:
                    if not self._verify_alipay_callback(callback_data):
                        logger.error(f"支付宝回调签名验证失败: {payment_no}")
                        track_signature_verification(payment_method, "failure")
                        duration = time.time() - start_time
                        track_payment_callback(payment_method, "signature_failed", duration)
                        return False
                    track_signature_verification(payment_method, "success")
                elif payment.payment_method == PaymentMethod.WECHAT:
                    if not self._verify_wechat_callback(callback_data):
                        logger.error(f"微信回调签名验证失败: {payment_no}")
                        track_signature_verification(payment_method, "failure")
                        duration = time.time() - start_time
                        track_payment_callback(payment_method, "signature_failed", duration)
                        return False
                    track_signature_verification(payment_method, "success")

            # P0-4: 验证订单金额
            if not self._verify_payment_amount(payment, callback_data):
                logger.error(f"支付金额验证失败: {payment_no}")
                track_amount_verification("mismatch", payment_method)
                # 标记支付失败
                payment.mark_as_failed("支付金额不匹配")
                self.db.commit()
                track_payment_failure(payment_method, "amount_mismatch")
                duration = time.time() - start_time
                track_payment_callback(payment_method, "amount_mismatch", duration)
                return False

            track_amount_verification("success", payment_method)

            # 更新支付状态
            payment.mark_as_success(callback_data.get("transaction_id"))
            payment.channel_response = json.dumps(callback_data)

            # 记录支付成功
            track_payment_success(payment_method, float(payment.amount))

            # 获取订单
            order = self.db.query(Order).filter(Order.id == payment.order_id).first()
            if order:
                # 更新订单状态
                order.mark_as_paid()

                # 创建保存点保护配额发放
                savepoint = self.db.begin_nested()
                try:
                    # 发放配额
                    self._grant_quota(order)

                    # 标记订单完成
                    order.mark_as_completed()
                    track_order_completion(order.package_type if order.package_type else 'unknown')

                    # 提交嵌套事务
                    savepoint.commit()
                except Exception as quota_error:
                    # 配额发放失败，回滚保存点
                    savepoint.rollback()
                    logger.error(f"支付回调: 配额发放失败，订单未完成 payment_no={payment_no}, error={str(quota_error)}")
                    # 标记支付失败并回滚
                    payment.mark_as_failed(f"配额发放失败: {str(quota_error)}")
                    self.db.commit()
                    track_payment_failure(payment_method, "quota_grant_failed")
                    duration = time.time() - start_time
                    track_payment_callback(payment_method, "quota_failed", duration)
                    return False

            self.db.commit()
            logger.info(f"支付回调处理成功: {payment_no}")

            duration = time.time() - start_time
            track_payment_callback(payment_method, "success", duration)
            return True

        except Exception as e:
            self.db.rollback()
            logger.error(f"处理支付回调失败: {str(e)}")
            track_payment_failure(payment_method, "callback_processing_failed")
            duration = time.time() - start_time
            track_payment_callback(payment_method, "failed", duration)
            return False

    def _process_dev_payment(self, payment: Payment, order: Order) -> None:
        """处理开发模式支付（自动成功）

        P1-5: 使用嵌套事务保护，配额发放失败时回滚到保存点

        Args:
            payment: 支付对象
            order: 订单对象
        """
        try:
            # 标记支付成功
            payment.mark_as_success(f"DEV_{payment.payment_no}")
            payment.channel_response = json.dumps({"mode": "development", "auto_success": True})

            # 更新订单状态
            order.mark_as_paid()

            logger.info(f"开发模式支付: 支付和订单状态已更新 payment_no={payment.payment_no}")

            # P1-5: 创建保存点，用于配额发放失败时回滚
            savepoint = self.db.begin_nested()

            try:
                # 发放配额
                self._grant_quota(order)

                # 标记订单完成
                order.mark_as_completed()

                # 提交嵌套事务
                savepoint.commit()
                logger.info(f"开发模式支付: 配额发放成功 payment_no={payment.payment_no}")

                # 提交主事务（配额发放成功时）
                self.db.commit()

            except Exception as quota_error:
                # 配额发放失败，回滚到保存点
                savepoint.rollback()
                logger.error(f"开发模式支付: 配额发放失败，回滚事务 payment_no={payment.payment_no}, error={str(quota_error)}")

                # 标记支付失败
                payment.mark_as_failed(f"配额发放失败: {str(quota_error)}")

                # 回滚订单完成状态，重设为已支付状态
                order.status = OrderStatus.PAID
                order.completed_at = None

                # 提交失败状态到数据库
                self.db.commit()

                # 重新抛出异常
                raise BusinessException(
                    code=ErrorCode.SYSTEM_ERROR,
                    message="配额发放失败，支付已回滚"
                )

            logger.info(f"开发模式支付完成: {payment.payment_no}")

        except BusinessException:
            # 业务异常直接抛出
            raise
        except Exception as e:
            self.db.rollback()
            logger.error(f"开发模式支付处理失败: {str(e)}")
            raise

    def _process_alipay(self, payment: Payment, order: Order) -> None:
        """处理支付宝支付

        Args:
            payment: 支付对象
            order: 订单对象

        Raises:
            BusinessException: 支付宝支付功能尚未实现

        Note:
            P0-002: 此功能处于预发布阶段，生产环境请使用开发模式(PAYMENT_DEV_MODE=true)
            实现计划:
            1. 集成支付宝SDK (python-alipay-sdk)
            2. 配置应用公钥/私钥
            3. 调用 alipay.trade.precreate 创建预支付订单
            4. 返回支付二维码URL
        """
        logger.warning(f"支付宝支付功能未实现 [预发布]: payment_no={payment.payment_no}")
        raise BusinessException(
            code=ErrorCode.SERVICE_UNAVAILABLE,
            message="支付宝支付功能正在开发中，请使用其他支付方式或联系客服"
        )

    def _process_wechat(self, payment: Payment, order: Order) -> None:
        """处理微信支付

        Args:
            payment: 支付对象
            order: 订单对象

        Raises:
            BusinessException: 微信支付功能尚未实现

        Note:
            P0-002: 此功能处于预发布阶段，生产环境请使用开发模式(PAYMENT_DEV_MODE=true)
            实现计划:
            1. 集成微信支付SDK (wechatpy)
            2. 配置商户号/API密钥
            3. 调用统一下单接口
            4. 返回支付二维码或小程序支付参数
        """
        logger.warning(f"微信支付功能未实现 [预发布]: payment_no={payment.payment_no}")
        raise BusinessException(
            code=ErrorCode.SERVICE_UNAVAILABLE,
            message="微信支付功能正在开发中，请使用其他支付方式或联系客服"
        )

    def _process_balance(self, payment: Payment, order: Order, user_id: int) -> None:
        """处理余额支付

        Args:
            payment: 支付对象
            order: 订单对象
            user_id: 用户ID

        Raises:
            BusinessException: 余额支付功能尚未实现

        Note:
            P0-002: 此功能处于预发布阶段
            实现计划:
            1. 查询用户余额
            2. 验证余额充足
            3. 原子扣减余额
            4. 更新支付状态为成功
        """
        logger.warning(f"余额支付功能未实现 [预发布]: payment_no={payment.payment_no}, user_id={user_id}")
        raise BusinessException(
            code=ErrorCode.SERVICE_UNAVAILABLE,
            message="余额支付功能暂未开放"
        )

    def _grant_quota(self, order: Order) -> None:
        """发放配额

        P1-6: 改进异常处理，用户不存在时抛出异常，记录详细日志

        Args:
            order: 订单对象

        Raises:
            BusinessException: 用户不存在或配额发放失败
        """
        start_time = time.time()

        try:
            # P1-6: 验证用户存在性
            user = self.db.query(User).filter(User.id == order.user_id).first()
            if not user:
                error_msg = f"配额发放失败: 用户不存在 user_id={order.user_id}, order_id={order.id}"
                logger.error(error_msg)
                track_quota_grant("all", "user_not_found", time.time() - start_time)
                raise BusinessException(
                    code=ErrorCode.RECORD_NOT_FOUND,
                    message="用户不存在，无法发放配额"
                )

            # 记录配额发放前的值
            logger.info(
                f"配额发放前: user_id={order.user_id}, "
                f"chat_quota={user.chat_quota}, "
                f"generation_quota={user.generation_quota}, "
                f"token_quota={user.token_quota}, "
                f"storage_quota_mb={user.storage_quota_mb}"
            )

            # 增加配额
            quota_changes = []
            if order.chat_quota > 0:
                user.chat_quota += order.chat_quota
                quota_changes.append(f"chat_quota +{order.chat_quota}")
                track_quota_grant("chat", "success", time.time() - start_time)
            if order.generation_quota > 0:
                user.generation_quota += order.generation_quota
                quota_changes.append(f"generation_quota +{order.generation_quota}")
                track_quota_grant("generation", "success", time.time() - start_time)
            if order.token_quota > 0:
                user.token_quota += order.token_quota
                quota_changes.append(f"token_quota +{order.token_quota}")
                track_quota_grant("token", "success", time.time() - start_time)
            if order.storage_quota_mb > 0:
                user.storage_quota_mb += order.storage_quota_mb
                quota_changes.append(f"storage_quota_mb +{order.storage_quota_mb}")
                track_quota_grant("storage", "success", time.time() - start_time)

            # P1-6: 使用flush而不是commit，让外层事务控制提交
            self.db.flush()

            # 记录配额发放后的值
            logger.info(
                f"配额发放成功: user_id={order.user_id}, order_id={order.id}, "
                f"changes=[{', '.join(quota_changes)}], "
                f"new_values: chat={user.chat_quota}, generation={user.generation_quota}, "
                f"token={user.token_quota}, storage={user.storage_quota_mb}MB"
            )

        except BusinessException:
            # 业务异常直接抛出
            raise
        except Exception as e:
            error_msg = f"配额发放异常: user_id={order.user_id}, order_id={order.id}, error={str(e)}"
            logger.error(error_msg)
            track_quota_grant("all", "failed", time.time() - start_time)
            raise BusinessException(
                code=ErrorCode.SYSTEM_ERROR,
                message="配额发放失败"
            )

    def _verify_payment_amount(self, payment: Payment, callback_data: Dict[str, Any]) -> bool:
        """验证支付金额

        Args:
            payment: 支付对象
            callback_data: 回调数据

        Returns:
            是否验证通过
        """
        try:
            # 从回调数据中提取金额
            callback_amount = None

            # 支付宝回调金额字段
            if payment.payment_method == PaymentMethod.ALIPAY:
                # 支付宝使用 total_amount 字段
                callback_amount_str = callback_data.get('total_amount') or callback_data.get('buyer_pay_amount')
                if callback_amount_str:
                    callback_amount = Decimal(str(callback_amount_str))

            # 微信回调金额字段
            elif payment.payment_method == PaymentMethod.WECHAT:
                # 微信使用 total_fee 字段（单位：分）
                callback_amount_fen = callback_data.get('total_fee')
                if callback_amount_fen:
                    callback_amount = Decimal(str(callback_amount_fen)) / 100

            # 如果无法提取金额，记录警告但不阻止（开发模式）
            if callback_amount is None:
                if settings.PAYMENT_DEV_MODE:
                    logger.warning(f"无法从回调数据中提取金额，开发模式跳过验证")
                    return True
                else:
                    logger.error(f"无法从回调数据中提取金额: {callback_data}")
                    return False

            # 转换支付金额为Decimal
            payment_amount = Decimal(str(payment.amount))

            # 比较金额（允许0.01元误差）
            amount_diff = abs(callback_amount - payment_amount)
            tolerance = Decimal('0.01')

            if amount_diff > tolerance:
                logger.error(
                    f"支付金额不匹配: payment_no={payment.payment_no}, "
                    f"expected={payment_amount}, got={callback_amount}, diff={amount_diff}"
                )
                return False

            logger.info(
                f"支付金额验证通过: payment_no={payment.payment_no}, "
                f"amount={payment_amount}, callback_amount={callback_amount}"
            )
            return True

        except Exception as e:
            logger.error(f"支付金额验证异常: {str(e)}")
            return False

    def _verify_alipay_callback(self, callback_data: Dict[str, Any]) -> bool:
        """验证支付宝回调签名

        Args:
            callback_data: 回调数据

        Returns:
            是否验证通过
        """
        try:
            # 提取签名
            sign = callback_data.get('sign')
            if not sign:
                logger.error("支付宝回调缺少签名参数")
                return False

            # 提取签名类型
            sign_type = callback_data.get('sign_type', 'RSA2')

            # 移除sign和sign_type参数
            params = {k: v for k, v in callback_data.items() if k not in ['sign', 'sign_type']}

            # 按字典序排序并拼接
            sorted_params = sorted(params.items())
            unsigned_string = '&'.join([f"{k}={v}" for k, v in sorted_params])

            # 使用支付宝SDK验证签名
            try:
                from alipay.aop.api.util.SignatureUtils import verify_with_rsa

                # 获取支付宝公钥
                alipay_public_key = settings.ALIPAY_PUBLIC_KEY
                if not alipay_public_key:
                    logger.error("支付宝公钥未配置")
                    return False

                # 验证签名
                is_valid = verify_with_rsa(alipay_public_key, unsigned_string, sign)

                if not is_valid:
                    logger.error(f"支付宝签名验证失败: unsigned_string={unsigned_string[:100]}...")
                    return False

                logger.info("支付宝签名验证成功")
                return True

            except ImportError:
                logger.error("支付宝SDK未安装，无法验证签名")
                return False

        except Exception as e:
            logger.error(f"支付宝签名验证异常: {str(e)}")
            return False

    def _verify_wechat_callback(self, callback_data: Dict[str, Any]) -> bool:
        """验证微信回调签名

        Args:
            callback_data: 回调数据

        Returns:
            是否验证通过
        """
        try:
            # 提取签名
            sign = callback_data.get('sign')
            if not sign:
                logger.error("微信回调缺少签名参数")
                return False

            # 移除sign参数
            params = {k: v for k, v in callback_data.items() if k != 'sign'}

            # 按字典序排序并拼接
            sorted_params = sorted(params.items())
            sign_string = '&'.join([f"{k}={v}" for k, v in sorted_params])

            # 添加API密钥
            api_key = settings.WECHAT_API_KEY
            if not api_key:
                logger.error("微信API密钥未配置")
                return False

            sign_string += f"&key={api_key}"

            # 计算MD5签名
            # Note: MD5 is required by WeChat Pay API specification and cannot be changed
            # This is not used for cryptographic security, but for API signature verification
            calculated_sign = hashlib.md5(sign_string.encode('utf-8'), usedforsecurity=False).hexdigest().upper()

            # 使用常量时间比较防止时序攻击
            if not secrets.compare_digest(calculated_sign, sign.upper()):
                logger.error(f"微信签名验证失败: expected={calculated_sign[:10]}..., got={sign[:10]}...")
                return False

            logger.info("微信签名验证成功")
            return True

        except Exception as e:
            logger.error(f"微信签名验证异常: {str(e)}")
            return False

    def _generate_payment_no(self) -> str:
        """生成支付单号

        格式: PAY + YYYYMMDD + 8位安全随机十六进制
        使用secrets模块生成密码学安全的随机数

        Returns:
            支付单号
        """
        date_str = datetime.utcnow().strftime("%Y%m%d")

        # 尝试生成唯一的支付单号（最多重试10次）
        max_retries = 10
        for attempt in range(max_retries):
            # 使用secrets生成8位安全随机十六进制字符串
            random_str = secrets.token_hex(4).upper()  # 4字节 = 8个十六进制字符
            payment_no = f"PAY{date_str}{random_str}"

            # 检查唯一性
            existing = self.db.query(Payment).filter(
                Payment.payment_no == payment_no
            ).first()

            if not existing:
                return payment_no

            logger.warning(f"支付单号冲突，重试 {attempt + 1}/{max_retries}: {payment_no}")

        # 如果重试失败，使用UUID作为后备方案
        import uuid
        fallback_id = uuid.uuid4().hex[:8].upper()
        payment_no = f"PAY{date_str}{fallback_id}"
        logger.warning(f"使用UUID后备方案生成支付单号: {payment_no}")
        return payment_no

    def _check_payment_risk(
        self,
        order: Order,
        user_id: int,
        payment_method: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """检查支付风险

        Args:
            order: 订单对象
            user_id: 用户ID
            payment_method: 支付方式
            context: 请求上下文

        Returns:
            风险检查结果
        """
        try:
            # 获取风控服务
            risk_service = get_risk_control_service(self.db)

            # 构建事件数据
            event_data = {
                "order_id": order.id,
                "amount": float(order.amount),
                "payment_method": payment_method,
                "package_id": getattr(order, 'package_id', None),
                "package_name": getattr(order, 'package_name', None)
            }

            # 执行风险检查
            risk_result = risk_service.check_risk(
                event_type=EventType.PAYMENT.value,
                user_id=str(user_id),
                event_data=event_data,
                context=context
            )

            return risk_result

        except Exception as e:
            logger.error(f"风险检查失败: {str(e)}")
            # 风险检查失败时采用保守策略
            return {
                "risk_score": 50,
                "risk_level": "medium",
                "action": RiskAction.REVIEW.value,
                "triggered_rules": [],
                "blacklist_hits": [],
                "recommendations": ["风险检查服务异常，建议人工审核"],
                "error": str(e)
            }

    def _create_pending_review_payment(
        self,
        order: Order,
        payment_method_enum: PaymentMethod,
        risk_result: Dict[str, Any]
    ) -> Payment:
        """创建待审核的支付记录

        Args:
            order: 订单对象
            payment_method_enum: 支付方式枚举
            risk_result: 风险检查结果

        Returns:
            待审核的支付对象
        """
        try:
            # 生成支付单号
            payment_no = self._generate_payment_no()

            # 创建支付记录，状态为待审核
            payment = Payment(
                payment_no=payment_no,
                order_id=order.id,
                amount=order.amount,
                payment_method=payment_method_enum,
                status=PaymentStatus.PENDING  # 可以考虑添加REVIEW状态
            )

            # 添加风险信息到支付记录的备注中
            risk_info = {
                "risk_score": risk_result["risk_score"],
                "risk_level": risk_result["risk_level"],
                "triggered_rules": risk_result["triggered_rules"],
                "blacklist_hits": risk_result["blacklist_hits"],
                "event_id": risk_result.get("event_id")
            }
            payment.remark = json.dumps(risk_info, ensure_ascii=False)

            self.db.add(payment)
            self.db.commit()
            self.db.refresh(payment)

            logger.info(f"创建待审核支付记录: {payment.payment_no} (risk_score={risk_result['risk_score']})")
            return payment

        except Exception as e:
            self.db.rollback()
            logger.error(f"创建待审核支付记录失败: {str(e)}")
            raise BusinessException(
                code=ErrorCode.DB_INSERT_FAILED,
                message="创建支付记录失败"
            )
