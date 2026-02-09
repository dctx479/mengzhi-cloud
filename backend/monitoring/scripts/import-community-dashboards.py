#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Grafana社区仪表盘导入工具
自动从Grafana.com下载并导入社区仪表盘到本地Grafana实例
"""

import os
import sys
import time
import json
import argparse
import requests
from typing import Dict, List, Tuple
from urllib.parse import urljoin

# 设置UTF-8编码输出 (修复Windows控制台编码问题)
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

# ANSI颜色代码 (Windows可能不支持,所以在Windows上禁用)
class Colors:
    if sys.platform == 'win32' and not os.environ.get('TERM'):
        GREEN = ''
        YELLOW = ''
        RED = ''
        NC = ''
    else:
        GREEN = '\033[0;32m'
        YELLOW = '\033[1;33m'
        RED = '\033[0;31m'
        NC = '\033[0m'

# 社区仪表盘配置
COMMUNITY_DASHBOARDS = [
    {
        "id": 1860,
        "name": "Node Exporter Full",
        "description": "系统监控 - CPU, 内存, 磁盘, 网络",
    },
    {
        "id": 179,
        "name": "Docker Container & Host Metrics",
        "description": "容器监控 - Docker容器和宿主机指标",
    },
]

def log_info(message: str):
    """打印信息日志"""
    print(f"{Colors.GREEN}[INFO]{Colors.NC} {message}")

def log_warn(message: str):
    """打印警告日志"""
    print(f"{Colors.YELLOW}[WARN]{Colors.NC} {message}")

def log_error(message: str):
    """打印错误日志"""
    print(f"{Colors.RED}[ERROR]{Colors.NC} {message}")

class GrafanaClient:
    """Grafana API客户端"""

    def __init__(self, url: str, username: str, password: str):
        self.url = url.rstrip('/')
        self.auth = (username, password)
        self.session = requests.Session()
        self.session.auth = self.auth

    def check_health(self, max_retries: int = 30, retry_interval: int = 2) -> bool:
        """检查Grafana服务健康状态"""
        log_info("检查Grafana服务状态...")

        for i in range(max_retries):
            try:
                response = self.session.get(urljoin(self.url, '/api/health'), timeout=5)
                if response.status_code == 200:
                    log_info("Grafana服务已就绪")
                    return True
            except requests.RequestException:
                pass

            log_warn(f"Grafana未就绪, 重试 {i + 1}/{max_retries}...")
            time.sleep(retry_interval)

        log_error("Grafana服务未就绪, 超时退出")
        return False

    def download_dashboard(self, dashboard_id: int) -> Dict:
        """从Grafana.com下载仪表盘JSON"""
        log_info(f"从Grafana.com下载仪表盘 (ID: {dashboard_id})...")

        try:
            url = f"https://grafana.com/api/dashboards/{dashboard_id}/revisions/latest/download"
            response = requests.get(url, timeout=30)
            response.raise_for_status()

            dashboard_json = response.json()
            if not dashboard_json:
                raise ValueError("下载的仪表盘为空")

            return dashboard_json
        except Exception as e:
            log_error(f"下载仪表盘失败: {e}")
            raise

    def import_dashboard(self, dashboard_json: Dict, datasource_name: str = "Prometheus") -> Tuple[bool, str]:
        """导入仪表盘到Grafana"""
        log_info("导入仪表盘到Grafana...")

        # 构造导入payload
        import_payload = {
            "dashboard": dashboard_json,
            "overwrite": True,
            "inputs": [
                {
                    "name": "DS_PROMETHEUS",
                    "type": "datasource",
                    "pluginId": "prometheus",
                    "value": datasource_name
                }
            ]
        }

        try:
            response = self.session.post(
                urljoin(self.url, '/api/dashboards/import'),
                json=import_payload,
                timeout=30
            )

            response.raise_for_status()
            result = response.json()

            if 'uid' in result:
                uid = result['uid']
                dashboard_url = f"{self.url}/d/{uid}"
                return True, dashboard_url
            else:
                return False, str(result)

        except Exception as e:
            log_error(f"导入失败: {e}")
            return False, str(e)

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='Grafana社区仪表盘导入工具')
    parser.add_argument('--url', default=os.getenv('GRAFANA_URL', 'http://localhost:3000'),
                        help='Grafana URL (默认: http://localhost:3000)')
    parser.add_argument('--user', default=os.getenv('GRAFANA_USER', 'admin'),
                        help='Grafana用户名 (默认: admin)')
    parser.add_argument('--password', default=os.getenv('GRAFANA_PASSWORD', 'admin123'),
                        help='Grafana密码 (默认: admin123)')
    parser.add_argument('--datasource', default='Prometheus',
                        help='Prometheus数据源名称 (默认: Prometheus)')

    args = parser.parse_args()

    # 打印标题
    print("=" * 50)
    print("Grafana社区仪表盘导入工具")
    print("=" * 50)
    print(f"Grafana URL: {args.url}")
    print()

    # 创建Grafana客户端
    client = GrafanaClient(args.url, args.user, args.password)

    # 检查Grafana健康状态
    if not client.check_health():
        sys.exit(1)

    # 导入仪表盘
    print()
    log_info("开始导入社区仪表盘...")
    print()

    success_count = 0
    fail_count = 0

    for dashboard_config in COMMUNITY_DASHBOARDS:
        dashboard_id = dashboard_config['id']
        dashboard_name = dashboard_config['name']
        dashboard_desc = dashboard_config['description']

        print(f"{'='*50}")
        log_info(f"仪表盘: {dashboard_name}")
        log_info(f"ID: {dashboard_id}")
        log_info(f"描述: {dashboard_desc}")
        print()

        try:
            # 下载仪表盘
            dashboard_json = client.download_dashboard(dashboard_id)

            # 导入仪表盘
            success, result = client.import_dashboard(dashboard_json, args.datasource)

            if success:
                log_info(f"[OK] 成功导入仪表盘: {dashboard_name}")
                log_info(f"  访问地址: {result}")
                success_count += 1
            else:
                log_error(f"[FAIL] 导入仪表盘失败: {dashboard_name}")
                log_error(f"  错误: {result}")
                fail_count += 1

        except Exception as e:
            log_error(f"[FAIL] 处理仪表盘失败: {dashboard_name}")
            log_error(f"  错误: {e}")
            fail_count += 1

        print()

    # 打印汇总
    print("=" * 50)
    print("导入完成")
    print("=" * 50)
    print(f"成功: {success_count}")
    print(f"失败: {fail_count}")
    print()

    if fail_count == 0:
        log_info("所有仪表盘导入成功!")
        log_info(f"访问Grafana查看: {args.url}")
        sys.exit(0)
    else:
        log_warn("部分仪表盘导入失败, 请检查日志")
        sys.exit(1)

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print()
        log_warn("用户中断操作")
        sys.exit(130)
    except Exception as e:
        log_error(f"未预期的错误: {e}")
        sys.exit(1)
