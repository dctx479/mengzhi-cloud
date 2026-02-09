#!/usr/bin/env python3
"""
HTTP端点测试脚本
测试实际的/metrics端点和其他API端点
"""

import requests
import time
import sys

def test_metrics_endpoint_http():
    """测试HTTP /metrics端点"""
    print("=== 测试HTTP /metrics端点 ===")

    base_url = "http://localhost:8000"

    try:
        # 测试/metrics端点
        response = requests.get(f"{base_url}/metrics", timeout=10)

        if response.status_code == 200:
            print(f"[OK] /metrics端点响应成功")
            print(f"Status Code: {response.status_code}")
            print(f"Content-Type: {response.headers.get('content-type')}")
            print(f"Content-Length: {len(response.text)}")

            # 检查关键指标
            content = response.text
            key_metrics = [
                'http_requests_total',
                'payment_requests_total',
                'active_users_total',
                'order_creation_total'
            ]

            found_metrics = []
            for metric in key_metrics:
                if metric in content:
                    found_metrics.append(metric)

            print(f"找到关键指标: {len(found_metrics)}/{len(key_metrics)}")
            for metric in found_metrics:
                print(f"  - {metric}")

            # 显示部分内容
            print("\n--- 指标内容示例 ---")
            lines = content.split('\n')
            for line in lines[:10]:
                if line.strip() and not line.startswith('#'):
                    print(line)

            return True
        else:
            print(f"[ERROR] /metrics端点响应失败: {response.status_code}")
            return False

    except requests.exceptions.ConnectionError:
        print("[WARNING] 无法连接到服务器，请确保应用正在运行")
        print("提示: 运行 'uvicorn app.main:app --host 0.0.0.0 --port 8000' 启动服务")
        return False
    except Exception as e:
        print(f"[ERROR] 请求失败: {e}")
        return False

def test_other_endpoints():
    """测试其他端点以生成指标"""
    print("\n=== 测试其他端点生成指标 ===")

    base_url = "http://localhost:8000"

    endpoints = [
        ("GET", "/", "根路径"),
        ("GET", "/health", "健康检查"),
        ("GET", "/docs", "API文档"),
    ]

    results = []

    for method, path, desc in endpoints:
        try:
            if method == "GET":
                response = requests.get(f"{base_url}{path}", timeout=5)

            print(f"[{response.status_code}] {method} {path} - {desc}")
            results.append((path, response.status_code))

        except requests.exceptions.ConnectionError:
            print(f"[CONN] {method} {path} - 连接失败")
            results.append((path, "CONN_ERROR"))
        except Exception as e:
            print(f"[ERROR] {method} {path} - {str(e)}")
            results.append((path, "ERROR"))

    return results

def generate_sample_metrics():
    """生成示例指标数据"""
    print("\n=== 生成示例指标数据 ===")

    try:
        from app.core.metrics import (
            track_payment_request,
            track_payment_success,
            track_order_creation,
            track_order_completion,
            active_users,
            active_enterprises
        )

        # 模拟支付活动
        print("模拟支付活动...")
        track_payment_request("alipay", "success")
        track_payment_request("wechat", "success")
        track_payment_request("alipay", "failed")
        track_payment_success("alipay", 299.00)
        track_payment_success("wechat", 199.00)

        # 模拟订单活动
        print("模拟订单活动...")
        track_order_creation("quota_package")
        track_order_creation("ai_service")
        track_order_completion("quota_package")

        # 更新用户统计
        print("更新用户统计...")
        active_users.set(156)
        active_enterprises.set(28)

        print("[OK] 示例指标数据生成完成")
        return True

    except Exception as e:
        print(f"[ERROR] 生成示例指标失败: {e}")
        return False

def main():
    """主函数"""
    print("开始HTTP端点测试")
    print("=" * 50)

    # 首先生成一些示例指标
    generate_sample_metrics()

    # 测试其他端点
    test_other_endpoints()

    # 等待一下让指标更新
    time.sleep(1)

    # 测试metrics端点
    success = test_metrics_endpoint_http()

    print("\n" + "=" * 50)
    if success:
        print("[SUCCESS] HTTP端点测试完成")
        print("\n使用方法:")
        print("1. 启动应用: uvicorn app.main:app --host 0.0.0.0 --port 8000")
        print("2. 访问指标: http://localhost:8000/metrics")
        print("3. 配置Prometheus: 添加target 'localhost:8000'")
        return 0
    else:
        print("[INFO] 请先启动应用再运行此测试")
        return 1

if __name__ == "__main__":
    sys.exit(main())