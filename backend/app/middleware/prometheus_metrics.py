"""
Prometheus监控中间件

提供FastAPI应用的Prometheus指标收集：
- HTTP请求计数
- 请求延迟（直方图）
- 活跃请求数
- 自定义业务指标

使用方法:
    from app.middleware.prometheus_metrics import setup_prometheus_metrics

    app = FastAPI()
    setup_prometheus_metrics(app)
"""

import time
from typing import Callable
from fastapi import FastAPI, Request, Response
from prometheus_client import Counter, Histogram, Gauge, make_asgi_app
from prometheus_client import CollectorRegistry, REGISTRY


# 创建指标
http_requests_total = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status']
)

http_request_duration_seconds = Histogram(
    'http_request_duration_seconds',
    'HTTP request duration in seconds',
    ['method', 'endpoint'],
    buckets=(0.01, 0.05, 0.1, 0.5, 1.0, 2.0, 5.0, 10.0)
)

http_requests_in_progress = Gauge(
    'http_requests_in_progress',
    'Number of HTTP requests in progress',
    ['method', 'endpoint']
)

# 业务指标
active_users = Gauge(
    'active_users',
    'Number of active users'
)

api_calls_by_user = Counter(
    'api_calls_by_user_total',
    'Total API calls by user',
    ['user_id']
)

tokens_consumed = Counter(
    'tokens_consumed_total',
    'Total tokens consumed',
    ['user_id', 'model']
)

billing_amount = Counter(
    'billing_amount_total',
    'Total billing amount in CNY',
    ['user_id']
)

risk_events = Counter(
    'risk_events_total',
    'Total risk events',
    ['risk_level', 'action']
)

# 健康检查指标
health_check_status = Gauge(
    'health_check_status',
    'Health check status (1=healthy, 0=unhealthy)'
)


async def prometheus_middleware(request: Request, call_next: Callable) -> Response:
    """
    Prometheus监控中间件

    记录每个HTTP请求的指标：
    - 请求计数
    - 请求延迟
    - 进行中的请求数
    """
    # 跳过metrics端点本身
    if request.url.path == "/metrics":
        return await call_next(request)

    method = request.method
    endpoint = request.url.path

    # 增加进行中的请求数
    http_requests_in_progress.labels(method=method, endpoint=endpoint).inc()

    start_time = time.time()

    try:
        response = await call_next(request)
        status_code = response.status_code
    except Exception as e:
        # 如果发生异常，记录为500错误
        status_code = 500
        # 重新抛出异常
        raise
    finally:
        # 计算请求延迟
        duration = time.time() - start_time

        # 记录指标
        http_requests_total.labels(
            method=method,
            endpoint=endpoint,
            status=status_code
        ).inc()

        http_request_duration_seconds.labels(
            method=method,
            endpoint=endpoint
        ).observe(duration)

        # 减少进行中的请求数
        http_requests_in_progress.labels(method=method, endpoint=endpoint).dec()

    return response


def setup_prometheus_metrics(app: FastAPI):
    """
    设置Prometheus指标收集

    参数:
        app: FastAPI应用实例

    示例:
        app = FastAPI()
        setup_prometheus_metrics(app)
    """
    # 添加中间件
    app.middleware("http")(prometheus_middleware)

    # 挂载/metrics端点
    metrics_app = make_asgi_app()
    app.mount("/metrics", metrics_app)

    print("✅ Prometheus metrics enabled at /metrics")


# 业务指标记录函数
def record_api_call(user_id: str):
    """记录API调用"""
    api_calls_by_user.labels(user_id=user_id).inc()


def record_token_usage(user_id: str, model: str, tokens: int):
    """记录Token使用"""
    tokens_consumed.labels(user_id=user_id, model=model).inc(tokens)


def record_billing(user_id: str, amount: float):
    """记录计费金额"""
    billing_amount.labels(user_id=user_id).inc(amount)


def record_risk_event(risk_level: str, action: str):
    """记录风险事件"""
    risk_events.labels(risk_level=risk_level, action=action).inc()


def update_active_users(count: int):
    """更新活跃用户数"""
    active_users.set(count)


def set_health_status(is_healthy: bool):
    """设置健康检查状态"""
    health_check_status.set(1 if is_healthy else 0)
