"""
增强的监控指标收集器
"""
from prometheus_client import Counter, Histogram, Gauge, generate_latest
from functools import wraps
import time

# HTTP请求指标
http_requests_total = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status']
)

http_request_duration = Histogram(
    'http_request_duration_seconds',
    'HTTP request duration',
    ['method', 'endpoint']
)

# 数据库指标
db_query_duration = Histogram(
    'db_query_duration_seconds',
    'Database query duration',
    ['operation']
)

db_connection_pool = Gauge(
    'db_connection_pool_usage',
    'Database connection pool usage'
)

# AI API指标
ai_api_calls_total = Counter(
    'ai_api_calls_total',
    'Total AI API calls',
    ['provider', 'status']
)

ai_api_duration = Histogram(
    'ai_api_duration_seconds',
    'AI API call duration',
    ['provider']
)

# 配额指标
quota_usage = Gauge(
    'quota_usage_percentage',
    'Quota usage percentage',
    ['enterprise_id', 'quota_type']
)

# 业务指标
active_users = Gauge('active_users_total', 'Total active users')
active_enterprises = Gauge('active_enterprises_total', 'Total active enterprises')

# ==================== 支付系统指标 ====================

# 支付请求指标
payment_requests_total = Counter(
    'payment_requests_total',
    'Total payment requests',
    ['payment_method', 'status']
)

payment_success_total = Counter(
    'payment_success_total',
    'Total successful payments',
    ['payment_method']
)

payment_failure_total = Counter(
    'payment_failure_total',
    'Total failed payments',
    ['payment_method', 'failure_reason']
)

# 支付金额指标
payment_amount_total = Counter(
    'payment_amount_total',
    'Total payment amount in yuan',
    ['payment_method']
)

payment_amount_histogram = Histogram(
    'payment_amount_histogram',
    'Payment amount distribution',
    ['payment_method'],
    buckets=[10, 50, 100, 200, 500, 1000, 2000, 5000, 10000]
)

# 支付响应时间
payment_duration_seconds = Histogram(
    'payment_duration_seconds',
    'Payment processing duration',
    ['payment_method', 'operation'],
    buckets=[0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0, 60.0]
)

# 支付回调指标
payment_callback_total = Counter(
    'payment_callback_total',
    'Total payment callbacks received',
    ['payment_method', 'status']
)

payment_callback_duration_seconds = Histogram(
    'payment_callback_duration_seconds',
    'Payment callback processing duration',
    ['payment_method']
)

# 签名验证指标
payment_signature_verification_total = Counter(
    'payment_signature_verification_total',
    'Total signature verifications',
    ['payment_method', 'result']
)

payment_signature_verification_failures = Counter(
    'payment_signature_verification_failures',
    'Total signature verification failures',
    ['payment_method']
)

# 支付金额验证指标
payment_amount_verification_total = Counter(
    'payment_amount_verification_total',
    'Total amount verifications',
    ['result']
)

payment_amount_mismatch_total = Counter(
    'payment_amount_mismatch_total',
    'Total amount mismatches detected',
    ['payment_method']
)

# 配额发放指标
quota_grant_total = Counter(
    'quota_grant_total',
    'Total quota grants',
    ['quota_type', 'status']
)

quota_grant_duration_seconds = Histogram(
    'quota_grant_duration_seconds',
    'Quota grant processing duration',
    ['quota_type']
)

# 支付状态指标
payment_pending_gauge = Gauge(
    'payment_pending_total',
    'Current number of pending payments'
)

payment_processing_gauge = Gauge(
    'payment_processing_total',
    'Current number of processing payments'
)

# 支付成功率（滑动窗口）
payment_success_rate = Gauge(
    'payment_success_rate',
    'Payment success rate (percentage)',
    ['payment_method']
)

# 订单相关指标
order_creation_total = Counter(
    'order_creation_total',
    'Total orders created',
    ['product_type']
)

order_completion_total = Counter(
    'order_completion_total',
    'Total orders completed',
    ['product_type']
)

# 并发支付指标
concurrent_payment_requests = Gauge(
    'concurrent_payment_requests',
    'Current number of concurrent payment requests'
)

# 支付重试指标
payment_retry_total = Counter(
    'payment_retry_total',
    'Total payment retries',
    ['payment_method', 'retry_count']
)

def track_request_metrics(func):
    """装饰器：跟踪HTTP请求指标"""
    @wraps(func)
    async def wrapper(*args, **kwargs):
        start_time = time.time()
        try:
            response = await func(*args, **kwargs)
            http_requests_total.labels(
                method=kwargs.get('method', 'GET'),
                endpoint=kwargs.get('path', '/'),
                status=response.status_code
            ).inc()
            return response
        finally:
            duration = time.time() - start_time
            http_request_duration.labels(
                method=kwargs.get('method', 'GET'),
                endpoint=kwargs.get('path', '/')
            ).observe(duration)
    return wrapper

def track_db_metrics(operation: str):
    """装饰器：跟踪数据库查询指标"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                return await func(*args, **kwargs)
            finally:
                duration = time.time() - start_time
                db_query_duration.labels(operation=operation).observe(duration)
        return wrapper
    return decorator


# ==================== 支付指标辅助函数 ====================

def track_payment_request(payment_method: str, status: str):
    """记录支付请求"""
    payment_requests_total.labels(
        payment_method=payment_method,
        status=status
    ).inc()


def track_payment_success(payment_method: str, amount: float):
    """记录支付成功"""
    payment_success_total.labels(payment_method=payment_method).inc()
    payment_amount_total.labels(payment_method=payment_method).inc(amount)
    payment_amount_histogram.labels(payment_method=payment_method).observe(amount)


def track_payment_failure(payment_method: str, failure_reason: str):
    """记录支付失败"""
    payment_failure_total.labels(
        payment_method=payment_method,
        failure_reason=failure_reason
    ).inc()


def track_payment_duration(payment_method: str, operation: str, duration: float):
    """记录支付处理时间"""
    payment_duration_seconds.labels(
        payment_method=payment_method,
        operation=operation
    ).observe(duration)


def track_payment_callback(payment_method: str, status: str, duration: float):
    """记录支付回调"""
    payment_callback_total.labels(
        payment_method=payment_method,
        status=status
    ).inc()
    payment_callback_duration_seconds.labels(
        payment_method=payment_method
    ).observe(duration)


def track_signature_verification(payment_method: str, result: str):
    """记录签名验证"""
    payment_signature_verification_total.labels(
        payment_method=payment_method,
        result=result
    ).inc()

    if result == "failure":
        payment_signature_verification_failures.labels(
            payment_method=payment_method
        ).inc()


def track_amount_verification(result: str, payment_method: str = None):
    """记录金额验证"""
    payment_amount_verification_total.labels(result=result).inc()

    if result == "mismatch" and payment_method:
        payment_amount_mismatch_total.labels(
            payment_method=payment_method
        ).inc()


def track_quota_grant(quota_type: str, status: str, duration: float):
    """记录配额发放"""
    quota_grant_total.labels(
        quota_type=quota_type,
        status=status
    ).inc()
    quota_grant_duration_seconds.labels(quota_type=quota_type).observe(duration)


def track_order_creation(product_type: str):
    """记录订单创建"""
    order_creation_total.labels(product_type=product_type).inc()


def track_order_completion(product_type: str):
    """记录订单完成"""
    order_completion_total.labels(product_type=product_type).inc()


def update_payment_pending_count(count: int):
    """更新待支付订单数"""
    payment_pending_gauge.set(count)


def update_payment_processing_count(count: int):
    """更新处理中支付数"""
    payment_processing_gauge.set(count)


def update_payment_success_rate(payment_method: str, rate: float):
    """更新支付成功率"""
    payment_success_rate.labels(payment_method=payment_method).set(rate)


def increment_concurrent_payments():
    """增加并发支付计数"""
    concurrent_payment_requests.inc()


def decrement_concurrent_payments():
    """减少并发支付计数"""
    concurrent_payment_requests.dec()


def track_payment_retry(payment_method: str, retry_count: int):
    """记录支付重试"""
    payment_retry_total.labels(
        payment_method=payment_method,
        retry_count=str(retry_count)
    ).inc()
