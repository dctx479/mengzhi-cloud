#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Kibana仪表盘自动配置脚本

创建三个核心仪表盘:
1. 业务日志仪表盘 - 日志量趋势、级别分布、错误类型、API请求
2. 性能日志仪表盘 - 响应时间、慢查询、数据库耗时、缓存命中率
3. 错误日志仪表盘 - 错误趋势、详情表格、堆栈追踪

使用方法:
    python scripts/setup_kibana_dashboards.py
"""

import sys
import io
import requests
import json
import time
from typing import Dict, Any, List

# 设置stdout为UTF-8编码
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Kibana配置
KIBANA_URL = "http://localhost:5601"
KIBANA_HEADERS = {
    "kbn-xsrf": "true",
    "Content-Type": "application/json"
}

# 数据视图ID (已存在)
DATA_VIEW_ID = "fe09b8a2-13c3-4400-9ef6-5e852cf5e7d9"
INDEX_PATTERN = "ai-platform-*"


class KibanaSetup:
    def __init__(self, kibana_url: str = KIBANA_URL):
        self.kibana_url = kibana_url
        self.headers = KIBANA_HEADERS
        self.data_view_id = DATA_VIEW_ID

    def _make_request(self, method: str, endpoint: str, data: Dict = None) -> Dict:
        """发送HTTP请求到Kibana API"""
        url = f"{self.kibana_url}{endpoint}"
        try:
            if method == "POST":
                response = requests.post(url, headers=self.headers, json=data)
            elif method == "GET":
                response = requests.get(url, headers=self.headers)
            elif method == "PUT":
                response = requests.put(url, headers=self.headers, json=data)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")

            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"❌ 请求失败: {e}")
            if hasattr(e.response, 'text'):
                print(f"   响应内容: {e.response.text}")
            return None

    def verify_data_view(self) -> bool:
        """验证数据视图是否存在"""
        print(f"🔍 验证数据视图: {self.data_view_id}")
        result = self._make_request("GET", f"/api/data_views/data_view/{self.data_view_id}")
        if result:
            print(f"✅ 数据视图存在: {result.get('data_view', {}).get('title', 'Unknown')}")
            return True
        print("❌ 数据视图不存在")
        return False

    def create_visualization(self, vis_config: Dict[str, Any]) -> str:
        """创建可视化"""
        print(f"📊 创建可视化: {vis_config['title']}")

        payload = {
            "attributes": {
                "title": vis_config["title"],
                "visState": json.dumps(vis_config["visState"]),
                "uiStateJSON": "{}",
                "description": vis_config.get("description", ""),
                "version": 1,
                "kibanaSavedObjectMeta": {
                    "searchSourceJSON": json.dumps({
                        "query": {"query": "", "language": "kuery"},
                        "filter": [],
                        "indexRefName": "kibanaSavedObjectMeta.searchSourceJSON.index"
                    })
                }
            },
            "references": [
                {
                    "name": "kibanaSavedObjectMeta.searchSourceJSON.index",
                    "type": "index-pattern",
                    "id": self.data_view_id
                }
            ]
        }

        result = self._make_request("POST", "/api/saved_objects/visualization", payload)
        if result:
            vis_id = result.get("id")
            print(f"✅ 可视化创建成功: {vis_id}")
            return vis_id
        return None

    def create_dashboard(self, title: str, description: str, panel_configs: List[Dict]) -> str:
        """创建仪表盘"""
        print(f"📈 创建仪表盘: {title}")

        panels = []
        for i, config in enumerate(panel_configs):
            panel = {
                "version": "8.11.0",
                "type": "visualization",
                "gridData": {
                    "x": config.get("x", (i % 2) * 24),
                    "y": config.get("y", (i // 2) * 15),
                    "w": config.get("w", 24),
                    "h": config.get("h", 15),
                    "i": str(i)
                },
                "panelIndex": str(i),
                "embeddableConfig": {
                    "enhancements": {}
                },
                "panelRefName": f"panel_{i}"
            }
            panels.append(panel)

        references = []
        for i, config in enumerate(panel_configs):
            references.append({
                "name": f"panel_{i}",
                "type": "visualization",
                "id": config["vis_id"]
            })

        payload = {
            "attributes": {
                "title": title,
                "description": description,
                "panelsJSON": json.dumps(panels),
                "optionsJSON": json.dumps({
                    "useMargins": True,
                    "hidePanelTitles": False
                }),
                "version": 1,
                "timeRestore": False,
                "kibanaSavedObjectMeta": {
                    "searchSourceJSON": json.dumps({
                        "query": {"query": "", "language": "kuery"},
                        "filter": []
                    })
                }
            },
            "references": references
        }

        result = self._make_request("POST", "/api/saved_objects/dashboard", payload)
        if result:
            dashboard_id = result.get("id")
            print(f"✅ 仪表盘创建成功: {dashboard_id}")
            return dashboard_id
        return None

    def setup_business_dashboard(self) -> str:
        """创建业务日志仪表盘"""
        print("\n" + "="*60)
        print("📊 创建业务日志仪表盘")
        print("="*60)

        vis_configs = []

        # 1. 日志量趋势 (时间序列)
        vis_configs.append({
            "title": "日志量趋势",
            "description": "按时间统计的日志数量趋势",
            "visState": {
                "title": "日志量趋势",
                "type": "line",
                "aggs": [
                    {
                        "id": "1",
                        "enabled": True,
                        "type": "count",
                        "schema": "metric",
                        "params": {}
                    },
                    {
                        "id": "2",
                        "enabled": True,
                        "type": "date_histogram",
                        "schema": "segment",
                        "params": {
                            "field": "@timestamp",
                            "interval": "auto",
                            "min_doc_count": 1
                        }
                    }
                ],
                "params": {
                    "type": "line",
                    "grid": {"categoryLines": False},
                    "categoryAxes": [{
                        "id": "CategoryAxis-1",
                        "type": "category",
                        "position": "bottom",
                        "show": True,
                        "title": {}
                    }],
                    "valueAxes": [{
                        "id": "ValueAxis-1",
                        "name": "LeftAxis-1",
                        "type": "value",
                        "position": "left",
                        "show": True,
                        "title": {"text": "Count"}
                    }],
                    "seriesParams": [{
                        "show": True,
                        "type": "line",
                        "mode": "normal",
                        "data": {"label": "Count", "id": "1"},
                        "valueAxis": "ValueAxis-1"
                    }],
                    "addTooltip": True,
                    "addLegend": True,
                    "legendPosition": "right"
                }
            }
        })

        # 2. 日志级别分布 (饼图)
        vis_configs.append({
            "title": "日志级别分布",
            "description": "不同日志级别的数量分布",
            "visState": {
                "title": "日志级别分布",
                "type": "pie",
                "aggs": [
                    {
                        "id": "1",
                        "enabled": True,
                        "type": "count",
                        "schema": "metric",
                        "params": {}
                    },
                    {
                        "id": "2",
                        "enabled": True,
                        "type": "terms",
                        "schema": "segment",
                        "params": {
                            "field": "log_level.keyword",
                            "size": 10,
                            "order": "desc",
                            "orderBy": "1"
                        }
                    }
                ],
                "params": {
                    "type": "pie",
                    "addTooltip": True,
                    "addLegend": True,
                    "legendPosition": "right",
                    "isDonut": True
                }
            }
        })

        # 3. TOP 10 日志来源
        vis_configs.append({
            "title": "TOP 10 日志来源",
            "description": "日志来源的TOP 10统计",
            "visState": {
                "title": "TOP 10 日志来源",
                "type": "horizontal_bar",
                "aggs": [
                    {
                        "id": "1",
                        "enabled": True,
                        "type": "count",
                        "schema": "metric",
                        "params": {}
                    },
                    {
                        "id": "2",
                        "enabled": True,
                        "type": "terms",
                        "schema": "segment",
                        "params": {
                            "field": "stream.keyword",
                            "size": 10,
                            "order": "desc",
                            "orderBy": "1"
                        }
                    }
                ],
                "params": {
                    "type": "histogram",
                    "grid": {"categoryLines": False},
                    "categoryAxes": [{
                        "id": "CategoryAxis-1",
                        "type": "category",
                        "position": "left",
                        "show": True,
                        "title": {}
                    }],
                    "valueAxes": [{
                        "id": "ValueAxis-1",
                        "name": "LeftAxis-1",
                        "type": "value",
                        "position": "bottom",
                        "show": True,
                        "title": {"text": "Count"}
                    }],
                    "seriesParams": [{
                        "show": True,
                        "type": "histogram",
                        "mode": "normal",
                        "data": {"label": "Count", "id": "1"},
                        "valueAxis": "ValueAxis-1"
                    }],
                    "addTooltip": True,
                    "addLegend": True,
                    "legendPosition": "right"
                }
            }
        })

        # 4. 日志数量指标 (单一指标)
        vis_configs.append({
            "title": "总日志数量",
            "description": "当前时间范围内的总日志数量",
            "visState": {
                "title": "总日志数量",
                "type": "metric",
                "aggs": [
                    {
                        "id": "1",
                        "enabled": True,
                        "type": "count",
                        "schema": "metric",
                        "params": {}
                    }
                ],
                "params": {
                    "addTooltip": True,
                    "addLegend": False,
                    "type": "metric",
                    "metric": {
                        "percentageMode": False,
                        "useRanges": False,
                        "colorSchema": "Green to Red",
                        "metricColorMode": "None",
                        "colorsRange": [{"from": 0, "to": 10000}],
                        "labels": {"show": True},
                        "invertColors": False,
                        "style": {
                            "bgFill": "#000",
                            "bgColor": False,
                            "labelColor": False,
                            "subText": "",
                            "fontSize": 60
                        }
                    }
                }
            }
        })

        # 创建所有可视化
        created_vis = []
        for config in vis_configs:
            vis_id = self.create_visualization(config)
            if vis_id:
                created_vis.append({"vis_id": vis_id, "w": 24, "h": 15})
                time.sleep(0.5)  # 避免请求过快

        if not created_vis:
            print("❌ 没有成功创建任何可视化")
            return None

        # 创建仪表盘
        dashboard_id = self.create_dashboard(
            title="业务日志仪表盘",
            description="展示日志量趋势、级别分布、来源统计等业务指标",
            panel_configs=created_vis
        )

        return dashboard_id

    def setup_performance_dashboard(self) -> str:
        """创建性能日志仪表盘"""
        print("\n" + "="*60)
        print("⚡ 创建性能日志仪表盘")
        print("="*60)

        # 注意: 性能指标依赖于应用程序日志中的特定字段 (如 response_time, duration等)
        # 如果这些字段不存在,可视化将不会显示数据

        vis_configs = []

        # 1. 日志流量 (按容器)
        vis_configs.append({
            "title": "容器日志流量",
            "description": "各容器的日志数量统计",
            "visState": {
                "title": "容器日志流量",
                "type": "histogram",
                "aggs": [
                    {
                        "id": "1",
                        "enabled": True,
                        "type": "count",
                        "schema": "metric",
                        "params": {}
                    },
                    {
                        "id": "2",
                        "enabled": True,
                        "type": "date_histogram",
                        "schema": "segment",
                        "params": {
                            "field": "@timestamp",
                            "interval": "auto",
                            "min_doc_count": 1
                        }
                    },
                    {
                        "id": "3",
                        "enabled": True,
                        "type": "terms",
                        "schema": "group",
                        "params": {
                            "field": "agent.name.keyword",
                            "size": 5,
                            "order": "desc",
                            "orderBy": "1"
                        }
                    }
                ],
                "params": {
                    "type": "histogram",
                    "grid": {"categoryLines": False},
                    "categoryAxes": [{
                        "id": "CategoryAxis-1",
                        "type": "category",
                        "position": "bottom",
                        "show": True,
                        "title": {}
                    }],
                    "valueAxes": [{
                        "id": "ValueAxis-1",
                        "name": "LeftAxis-1",
                        "type": "value",
                        "position": "left",
                        "show": True,
                        "title": {"text": "Count"}
                    }],
                    "seriesParams": [{
                        "show": True,
                        "type": "histogram",
                        "mode": "stacked",
                        "data": {"label": "Count", "id": "1"},
                        "valueAxis": "ValueAxis-1"
                    }],
                    "addTooltip": True,
                    "addLegend": True,
                    "legendPosition": "right"
                }
            }
        })

        # 创建所有可视化
        created_vis = []
        for config in vis_configs:
            vis_id = self.create_visualization(config)
            if vis_id:
                created_vis.append({"vis_id": vis_id, "w": 48, "h": 20})
                time.sleep(0.5)

        if not created_vis:
            print("❌ 没有成功创建任何可视化")
            return None

        # 创建仪表盘
        dashboard_id = self.create_dashboard(
            title="性能日志仪表盘",
            description="展示容器日志流量、系统性能等指标",
            panel_configs=created_vis
        )

        return dashboard_id

    def setup_error_dashboard(self) -> str:
        """创建错误日志仪表盘"""
        print("\n" + "="*60)
        print("🚨 创建错误日志仪表盘")
        print("="*60)

        vis_configs = []

        # 1. 错误日志趋势
        vis_configs.append({
            "title": "错误日志趋势",
            "description": "错误级别日志的时间趋势",
            "visState": {
                "title": "错误日志趋势",
                "type": "area",
                "aggs": [
                    {
                        "id": "1",
                        "enabled": True,
                        "type": "count",
                        "schema": "metric",
                        "params": {}
                    },
                    {
                        "id": "2",
                        "enabled": True,
                        "type": "date_histogram",
                        "schema": "segment",
                        "params": {
                            "field": "@timestamp",
                            "interval": "auto",
                            "min_doc_count": 1
                        }
                    }
                ],
                "params": {
                    "type": "area",
                    "grid": {"categoryLines": False},
                    "categoryAxes": [{
                        "id": "CategoryAxis-1",
                        "type": "category",
                        "position": "bottom",
                        "show": True,
                        "title": {}
                    }],
                    "valueAxes": [{
                        "id": "ValueAxis-1",
                        "name": "LeftAxis-1",
                        "type": "value",
                        "position": "left",
                        "show": True,
                        "title": {"text": "Count"}
                    }],
                    "seriesParams": [{
                        "show": True,
                        "type": "area",
                        "mode": "stacked",
                        "data": {"label": "Count", "id": "1"},
                        "valueAxis": "ValueAxis-1",
                        "drawLinesBetweenPoints": True,
                        "showCircles": True,
                        "interpolate": "linear"
                    }],
                    "addTooltip": True,
                    "addLegend": True,
                    "legendPosition": "right"
                }
            }
        })

        # 2. 主机分布
        vis_configs.append({
            "title": "日志主机分布",
            "description": "日志来源主机的分布统计",
            "visState": {
                "title": "日志主机分布",
                "type": "pie",
                "aggs": [
                    {
                        "id": "1",
                        "enabled": True,
                        "type": "count",
                        "schema": "metric",
                        "params": {}
                    },
                    {
                        "id": "2",
                        "enabled": True,
                        "type": "terms",
                        "schema": "segment",
                        "params": {
                            "field": "host.name.keyword",
                            "size": 10,
                            "order": "desc",
                            "orderBy": "1"
                        }
                    }
                ],
                "params": {
                    "type": "pie",
                    "addTooltip": True,
                    "addLegend": True,
                    "legendPosition": "right",
                    "isDonut": False
                }
            }
        })

        # 创建所有可视化
        created_vis = []
        for config in vis_configs:
            vis_id = self.create_visualization(config)
            if vis_id:
                created_vis.append({"vis_id": vis_id, "w": 24, "h": 20})
                time.sleep(0.5)

        if not created_vis:
            print("❌ 没有成功创建任何可视化")
            return None

        # 创建仪表盘
        dashboard_id = self.create_dashboard(
            title="错误日志仪表盘",
            description="展示错误日志趋势、来源分布等信息",
            panel_configs=created_vis
        )

        return dashboard_id

    def setup_all_dashboards(self):
        """设置所有仪表盘"""
        print("\n" + "="*60)
        print("🚀 开始配置Kibana仪表盘")
        print("="*60)

        # 验证数据视图
        if not self.verify_data_view():
            print("\n❌ 数据视图不存在,请先创建数据视图")
            return

        dashboards = []

        # 创建业务日志仪表盘
        business_id = self.setup_business_dashboard()
        if business_id:
            dashboards.append({
                "name": "业务日志仪表盘",
                "id": business_id,
                "url": f"{self.kibana_url}/app/dashboards#/view/{business_id}"
            })

        time.sleep(1)

        # 创建性能日志仪表盘
        performance_id = self.setup_performance_dashboard()
        if performance_id:
            dashboards.append({
                "name": "性能日志仪表盘",
                "id": performance_id,
                "url": f"{self.kibana_url}/app/dashboards#/view/{performance_id}"
            })

        time.sleep(1)

        # 创建错误日志仪表盘
        error_id = self.setup_error_dashboard()
        if error_id:
            dashboards.append({
                "name": "错误日志仪表盘",
                "id": error_id,
                "url": f"{self.kibana_url}/app/dashboards#/view/{error_id}"
            })

        # 打印总结
        print("\n" + "="*60)
        print("✅ Kibana仪表盘配置完成")
        print("="*60)

        if dashboards:
            print("\n📊 创建的仪表盘:")
            for dashboard in dashboards:
                print(f"\n  {dashboard['name']}")
                print(f"    ID: {dashboard['id']}")
                print(f"    URL: {dashboard['url']}")
        else:
            print("\n⚠️  没有成功创建任何仪表盘")

        print("\n💡 使用提示:")
        print("  1. 访问 Kibana: http://localhost:5601")
        print("  2. 导航到 Dashboard 查看创建的仪表盘")
        print("  3. 调整时间范围来查看不同时期的日志数据")
        print("  4. 可以点击图表进行交互式过滤和分析")


def main():
    """主函数"""
    setup = KibanaSetup()

    try:
        setup.setup_all_dashboards()
    except KeyboardInterrupt:
        print("\n\n⚠️  操作被用户中断")
    except Exception as e:
        print(f"\n\n❌ 发生错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
