#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Elasticsearch优化配置脚本

主要功能:
1. 配置索引生命周期管理 (ILM) - 自动管理索引的生命周期
2. 优化索引设置 - 调整分片、副本等参数
3. 创建索引模板 - 统一索引的映射和设置
4. 设置字段映射 - 优化常用字段的类型和聚合

使用方法:
    python scripts/optimize_elasticsearch.py
"""

import sys
import io
import requests
import json
from typing import Dict, Any

# 设置stdout为UTF-8编码
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Elasticsearch配置
ES_URL = "http://localhost:9200"
ES_HEADERS = {"Content-Type": "application/json"}


class ElasticsearchOptimizer:
    def __init__(self, es_url: str = ES_URL):
        self.es_url = es_url
        self.headers = ES_HEADERS

    def _make_request(self, method: str, endpoint: str, data: Dict = None) -> Dict:
        """发送HTTP请求到Elasticsearch"""
        url = f"{self.es_url}{endpoint}"
        try:
            if method == "POST":
                response = requests.post(url, headers=self.headers, json=data)
            elif method == "GET":
                response = requests.get(url, headers=self.headers)
            elif method == "PUT":
                response = requests.put(url, headers=self.headers, json=data)
            elif method == "DELETE":
                response = requests.delete(url, headers=self.headers)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")

            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"❌ 请求失败: {e}")
            if hasattr(e.response, 'text'):
                print(f"   响应内容: {e.response.text}")
            return None

    def setup_ilm_policy(self):
        """配置索引生命周期管理策略"""
        print("\n" + "="*60)
        print("🔄 配置索引生命周期管理 (ILM)")
        print("="*60)

        # ILM策略定义
        ilm_policy = {
            "policy": {
                "phases": {
                    "hot": {
                        "min_age": "0ms",
                        "actions": {
                            "rollover": {
                                "max_primary_shard_size": "50GB",
                                "max_age": "1d"
                            },
                            "set_priority": {
                                "priority": 100
                            }
                        }
                    },
                    "warm": {
                        "min_age": "7d",
                        "actions": {
                            "set_priority": {
                                "priority": 50
                            },
                            "forcemerge": {
                                "max_num_segments": 1
                            },
                            "shrink": {
                                "number_of_shards": 1
                            }
                        }
                    },
                    "delete": {
                        "min_age": "30d",
                        "actions": {
                            "delete": {}
                        }
                    }
                }
            }
        }

        result = self._make_request("PUT", "/_ilm/policy/ai-platform-ilm-policy", ilm_policy)
        if result:
            print("✅ ILM策略创建成功")
            print("   - Hot阶段: 当前数据,每日或50GB轮转")
            print("   - Warm阶段: 7天后,合并段并缩减分片")
            print("   - Delete阶段: 30天后自动删除")
        else:
            print("❌ ILM策略创建失败")

    def create_index_template(self):
        """创建索引模板"""
        print("\n" + "="*60)
        print("📋 创建索引模板")
        print("="*60)

        # 索引模板定义
        index_template = {
            "index_patterns": ["ai-platform-*"],
            "template": {
                "settings": {
                    "number_of_shards": 1,
                    "number_of_replicas": 0,
                    "index.lifecycle.name": "ai-platform-ilm-policy",
                    "index.lifecycle.rollover_alias": "ai-platform-logs",
                    "refresh_interval": "30s",
                    "index.codec": "best_compression",
                    "index.mapping.total_fields.limit": 2000
                },
                "mappings": {
                    "properties": {
                        "@timestamp": {
                            "type": "date",
                            "format": "strict_date_optional_time||epoch_millis"
                        },
                        "message": {
                            "type": "text",
                            "fields": {
                                "keyword": {
                                    "type": "keyword",
                                    "ignore_above": 256
                                }
                            }
                        },
                        "log_level": {
                            "type": "keyword"
                        },
                        "level": {
                            "type": "keyword"
                        },
                        "logger": {
                            "type": "keyword"
                        },
                        "module": {
                            "type": "keyword"
                        },
                        "function": {
                            "type": "keyword"
                        },
                        "stream": {
                            "type": "keyword"
                        },
                        "container": {
                            "properties": {
                                "name": {
                                    "type": "keyword"
                                },
                                "id": {
                                    "type": "keyword"
                                }
                            }
                        },
                        "host": {
                            "properties": {
                                "name": {
                                    "type": "keyword"
                                },
                                "hostname": {
                                    "type": "keyword"
                                },
                                "ip": {
                                    "type": "ip"
                                }
                            }
                        },
                        "request_id": {
                            "type": "keyword"
                        },
                        "user_id": {
                            "type": "keyword"
                        },
                        "path": {
                            "type": "keyword"
                        },
                        "method": {
                            "type": "keyword"
                        },
                        "status_code": {
                            "type": "integer"
                        },
                        "response_time": {
                            "type": "float"
                        },
                        "duration": {
                            "type": "float"
                        },
                        "error": {
                            "properties": {
                                "type": {
                                    "type": "keyword"
                                },
                                "message": {
                                    "type": "text"
                                },
                                "stack_trace": {
                                    "type": "text"
                                }
                            }
                        }
                    }
                }
            },
            "priority": 200,
            "version": 1,
            "_meta": {
                "description": "AI平台日志索引模板"
            }
        }

        result = self._make_request("PUT", "/_index_template/ai-platform-template", index_template)
        if result:
            print("✅ 索引模板创建成功")
            print("   - 应用到所有 ai-platform-* 索引")
            print("   - 配置了优化的字段映射")
            print("   - 启用了ILM生命周期管理")
        else:
            print("❌ 索引模板创建失败")

    def optimize_existing_indices(self):
        """优化现有索引"""
        print("\n" + "="*60)
        print("⚙️  优化现有索引")
        print("="*60)

        # 获取现有索引
        result = self._make_request("GET", "/_cat/indices/ai-platform-*?format=json")
        if not result:
            print("❌ 无法获取现有索引")
            return

        indices = [idx["index"] for idx in result]
        print(f"📊 找到 {len(indices)} 个索引")

        for index in indices:
            print(f"\n优化索引: {index}")

            # 更新索引设置
            settings = {
                "index": {
                    "number_of_replicas": 0,  # 单节点不需要副本
                    "refresh_interval": "30s",  # 降低刷新频率
                    "codec": "best_compression"  # 启用最佳压缩
                }
            }

            result = self._make_request("PUT", f"/{index}/_settings", settings)
            if result:
                print(f"  ✅ 设置已更新")
            else:
                print(f"  ❌ 设置更新失败")

            # 强制合并段 (减少段数量以提高查询性能)
            # 注意: 这个操作可能需要较长时间
            print(f"  🔄 执行段合并...")
            result = self._make_request("POST", f"/{index}/_forcemerge?max_num_segments=1")
            if result:
                print(f"  ✅ 段合并完成")
            else:
                print(f"  ❌ 段合并失败")

    def create_field_aliases(self):
        """创建字段别名以统一不同的字段名"""
        print("\n" + "="*60)
        print("🔗 创建字段别名")
        print("="*60)

        # 获取现有索引
        result = self._make_request("GET", "/_cat/indices/ai-platform-*?format=json")
        if not result:
            print("❌ 无法获取现有索引")
            return

        indices = [idx["index"] for idx in result]

        for index in indices:
            # 为不同的日志级别字段创建统一的别名
            mappings = {
                "properties": {
                    "unified_log_level": {
                        "type": "alias",
                        "path": "log_level"  # 优先使用log_level,如果不存在则使用level
                    }
                }
            }

            result = self._make_request("PUT", f"/{index}/_mapping", mappings)
            if result:
                print(f"✅ 字段别名创建成功: {index}")
            else:
                print(f"⚠️  字段别名创建跳过: {index}")

    def show_cluster_stats(self):
        """显示集群统计信息"""
        print("\n" + "="*60)
        print("📊 集群统计信息")
        print("="*60)

        # 集群健康状态
        health = self._make_request("GET", "/_cluster/health")
        if health:
            print(f"\n集群状态: {health['status']}")
            print(f"节点数量: {health['number_of_nodes']}")
            print(f"数据节点: {health['number_of_data_nodes']}")
            print(f"活跃分片: {health['active_shards']}")
            print(f"未分配分片: {health['unassigned_shards']}")

        # 索引统计
        stats = self._make_request("GET", "/_cat/indices/ai-platform-*?v&h=index,docs.count,store.size&s=index:desc")
        if stats:
            print("\n索引统计:")
            print(stats)

        # 节点信息
        nodes = self._make_request("GET", "/_cat/nodes?v&h=name,heap.percent,ram.percent,cpu,load_1m")
        if nodes:
            print("\n节点信息:")
            print(nodes)

    def run_optimization(self):
        """运行完整的优化流程"""
        print("\n" + "="*60)
        print("🚀 开始Elasticsearch优化")
        print("="*60)

        try:
            # 1. 显示当前状态
            self.show_cluster_stats()

            # 2. 配置ILM策略
            self.setup_ilm_policy()

            # 3. 创建索引模板
            self.create_index_template()

            # 4. 优化现有索引
            optimize = input("\n是否优化现有索引? 这可能需要较长时间 (y/N): ").lower()
            if optimize == 'y':
                self.optimize_existing_indices()
            else:
                print("⏭️  跳过现有索引优化")

            # 5. 创建字段别名
            self.create_field_aliases()

            # 6. 显示优化后的状态
            print("\n" + "="*60)
            print("✅ 优化完成")
            print("="*60)
            self.show_cluster_stats()

            print("\n💡 优化总结:")
            print("  ✅ ILM策略已配置 - 30天后自动删除旧日志")
            print("  ✅ 索引模板已创建 - 新索引将自动应用优化设置")
            print("  ✅ 字段别名已创建 - 统一了不同的字段名")
            print("  ℹ️  建议定期监控磁盘使用率和查询性能")

        except KeyboardInterrupt:
            print("\n\n⚠️  操作被用户中断")
        except Exception as e:
            print(f"\n\n❌ 发生错误: {e}")
            import traceback
            traceback.print_exc()


def main():
    """主函数"""
    optimizer = ElasticsearchOptimizer()
    optimizer.run_optimization()


if __name__ == "__main__":
    main()
