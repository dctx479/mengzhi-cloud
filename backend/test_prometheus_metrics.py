#!/usr/bin/env python3
"""
Prometheus指标测试脚本
测试关键指标的采集和暴露功能
"""

import sys
import time
import requests
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST

def test_metrics_import():
    """测试指标模块导入"""
    print("=== 测试指标模块导入 ===")
    try:
        from app.core.metrics import (
            # HTTP指标
            http_requests_total,
            http_request_duration,

            # 数据库指标
            db_query_duration,
            db_connection_pool,

            # AI API指标
            ai_api_calls_total,
            ai_api_duration,

            # 业务指标
            active_users,
            active_enterprises,

            # 支付指标
            payment_requests_total,
            payment_success_total,
            payment_failure_total,
            payment_amount_total,
            payment_duration_seconds,

            # 订单指标
            order_creation_total,
            order_completion_total,

            # 配额指标
            quota_usage,
            quota_grant_total,

            # 辅助函数
            track_payment_request,
            track_payment_success,
            track_payment_failure,
            track_order_creation,
            track_order_completion
        )
        print("✅ 指标模块导入成功")
        return True
    except Exception as e:
        print(f"❌ 指标模块导入失败: {e}")
        return False

def test_metrics_generation():
    """测试指标生成"""
    print("\n=== 测试指标生成 ===")
    try:
        from app.core.metrics import (
            http_requests_total,
            payment_requests_total,
            payment_success_total,
            order_creation_total,
            active_users,
            track_payment_request,
            track_payment_success,
            track_order_creation
        )

        # 模拟一些指标数据
        print("生成测试指标数据...")

        # HTTP请求指标
        http_requests_total.labels(method="GET", endpoint="/api/v1/products", status="200").inc()
        http_requests_total.labels(method="POST", endpoint="/api/v1/orders", status="201").inc()
        http_requests_total.labels(method="GET", endpoint="/api/v1/users", status="200").inc(3)

        # 支付指标
        track_payment_request("alipay", "success")
        track_payment_request("wechat", "success")
        track_payment_request("alipay", "failed")

        track_payment_success("alipay", 199.00)
        track_payment_success("wechat", 299.00)

        # 订单指标
        track_order_creation("quota_package")
        track_order_creation("quota_package")
        track_order_creation("ai_service")

        # 用户指标
        active_users.set(150)

        print("✅ 测试指标数据生成成功")
        return True
    except Exception as e:
        print(f"❌ 测试指标数据生成失败: {e}")
        return False

def test_prometheus_format():
    """测试Prometheus格式输出"""
    print("\n=== 测试Prometheus格式输出 ===")
    try:
        metrics_output = generate_latest()

        # 检查输出格式
        if isinstance(metrics_output, bytes):
            metrics_text = metrics_output.decode('utf-8')
        else:
            metrics_text = str(metrics_output)

        print(f"指标输出长度: {len(metrics_text)} 字符")

        # 检查关键指标是否存在
        expected_metrics = [
            'http_requests_total',
            'payment_requests_total',
            'payment_success_total',
            'order_creation_total',
            'active_users_total'
        ]

        missing_metrics = []
        for metric in expected_metrics:
            if metric not in metrics_text:
                missing_metrics.append(metric)

        if missing_metrics:
            print(f"❌ 缺少指标: {missing_metrics}")
            return False

        print("✅ Prometheus格式输出正常")

        # 显示部分指标内容
        print("\n--- 指标内容预览 ---")
        lines = metrics_text.split('\n')
        for line in lines[:20]:  # 显示前20行
            if line.strip() and not line.startswith('#'):
                print(line)

        if len(lines) > 20:
            print("...")
            print(f"(总共 {len(lines)} 行)")

        return True
    except Exception as e:
        print(f"❌ Prometheus格式输出测试失败: {e}")
        return False

def test_metrics_endpoint_simulation():
    """模拟/metrics端点功能"""
    print("\n=== 模拟/metrics端点功能 ===")
    try:
        from app.core.metrics import (
            active_users, active_enterprises,
            payment_pending_gauge, payment_processing_gauge
        )

        # 模拟更新实时指标
        active_users.set(150)
        active_enterprises.set(25)
        payment_pending_gauge.set(5)
        payment_processing_gauge.set(2)

        # 生成指标输出
        metrics_output = generate_latest()

        print(f"✅ /metrics端点模拟成功")
        print(f"Content-Type: {CONTENT_TYPE_LATEST}")
        print(f"Content-Length: {len(metrics_output)}")

        return True
    except Exception as e:
        print(f"❌ /metrics端点模拟失败: {e}")
        return False

def test_key_business_metrics():
    """测试关键业务指标"""
    print("\n=== 测试关键业务指标 ===")
    try:
        from app.core.metrics import (
            track_payment_request,
            track_payment_success,
            track_payment_failure,
            track_order_creation,
            track_order_completion,
            track_quota_grant,
            update_payment_success_rate
        )

        print("测试支付指标...")
        # 支付成功场景
        track_payment_request("alipay", "success")
        track_payment_success("alipay", 199.00)

        # 支付失败场景
        track_payment_request("wechat", "failed")
        track_payment_failure("wechat", "insufficient_balance")

        print("测试订单指标...")
        # 订单创建和完成
        track_order_creation("quota_package")
        track_order_completion("quota_package")

        print("测试配额指标...")
        # 配额发放
        track_quota_grant("ai_calls", "success", 0.5)

        print("测试支付成功率...")
        # 支付成功率
        update_payment_success_rate("alipay", 95.5)
        update_payment_success_rate("wechat", 92.3)

        print("✅ 关键业务指标测试成功")
        return True
    except Exception as e:
        print(f"❌ 关键业务指标测试失败: {e}")
        return False

def main():
    """主测试函数"""
    print("开始Prometheus指标测试")
    print("=" * 50)

    tests = [
        test_metrics_import,
        test_metrics_generation,
        test_prometheus_format,
        test_metrics_endpoint_simulation,
        test_key_business_metrics
    ]

    passed = 0
    total = len(tests)

    for test in tests:
        if test():
            passed += 1
        time.sleep(0.5)  # 短暂延迟

    print("\n" + "=" * 50)
    print(f"测试结果: {passed}/{total} 通过")

    if passed == total:
        print("所有测试通过！Prometheus指标集成成功")
        return 0
    else:
        print("部分测试失败，请检查配置")
        return 1

if __name__ == "__main__":
    sys.exit(main())