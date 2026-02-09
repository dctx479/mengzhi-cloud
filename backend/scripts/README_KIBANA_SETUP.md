# Kibana仪表盘配置脚本

## 概述

本目录包含自动配置Kibana日志分析仪表盘的Python脚本。这些脚本会自动创建可视化和仪表盘，并优化Elasticsearch索引配置。

## 脚本列表

### 1. setup_kibana_dashboards.py

**功能**: 自动创建Kibana仪表盘和可视化

**创建的仪表盘**:
- **业务日志仪表盘** - 日志量趋势、级别分布、来源统计、总日志数
- **性能日志仪表盘** - 容器日志流量、性能指标
- **错误日志仪表盘** - 错误趋势、主机分布

**前置条件**:
- Elasticsearch运行在 http://localhost:9200
- Kibana运行在 http://localhost:5601
- 数据视图已创建 (ID: fe09b8a2-13c3-4400-9ef6-5e852cf5e7d9)

**使用方法**:
```bash
cd backend
python scripts/setup_kibana_dashboards.py
```

**输出**:
- 创建多个可视化
- 创建3个仪表盘
- 打印仪表盘访问URL

### 2. optimize_elasticsearch.py

**功能**: 优化Elasticsearch配置以提高性能和节省存储空间

**执行的操作**:
1. **配置ILM策略** - 自动管理索引生命周期
   - Hot阶段: 当前数据，每日或50GB轮转
   - Warm阶段: 7天后，合并段并缩减分片
   - Delete阶段: 30天后自动删除

2. **创建索引模板** - 为新索引应用优化设置
   - 单分片配置（适合单节点）
   - 0副本（单节点无需副本）
   - 最佳压缩编码
   - 优化的字段映射

3. **优化现有索引**（可选）
   - 更新索引设置
   - 强制合并段以提高查询性能

4. **创建字段别名** - 统一不同的字段名

**前置条件**:
- Elasticsearch运行在 http://localhost:9200

**使用方法**:
```bash
cd backend
python scripts/optimize_elasticsearch.py
```

**交互式选项**:
- 脚本会询问是否优化现有索引（可能需要较长时间）
- 输入 `y` 执行优化，输入 `N` 跳过

## 快速开始

### 完整配置流程

```bash
# 1. 确保监控服务正在运行
docker-compose -f docker-compose.monitoring.yml ps

# 2. 优化Elasticsearch配置
python scripts/optimize_elasticsearch.py

# 3. 创建Kibana仪表盘
python scripts/setup_kibana_dashboards.py

# 4. 访问Kibana查看仪表盘
# 浏览器打开: http://localhost:5601
```

### 验证配置

```bash
# 检查Elasticsearch健康状态
curl http://localhost:9200/_cluster/health?pretty

# 检查ILM策略
curl http://localhost:9200/_ilm/policy/ai-platform-ilm-policy?pretty

# 检查索引模板
curl http://localhost:9200/_index_template/ai-platform-template?pretty

# 查看索引列表
curl http://localhost:9200/_cat/indices/ai-platform-*?v
```

## 依赖项

脚本需要以下Python包：

```bash
pip install requests
```

或者使用现有的虚拟环境：

```bash
# 激活虚拟环境
cd backend
source venv/bin/activate  # Linux/Mac
# 或
venv\Scripts\activate     # Windows

# 安装依赖
pip install requests
```

## 配置说明

### Kibana API配置

在 `setup_kibana_dashboards.py` 中：

```python
KIBANA_URL = "http://localhost:5601"  # Kibana地址
DATA_VIEW_ID = "fe09b8a2-13c3-4400-9ef6-5e852cf5e7d9"  # 数据视图ID
INDEX_PATTERN = "ai-platform-*"  # 索引模式
```

### Elasticsearch配置

在 `optimize_elasticsearch.py` 中：

```python
ES_URL = "http://localhost:9200"  # Elasticsearch地址
```

## 自定义配置

### 修改ILM保留时间

编辑 `optimize_elasticsearch.py` 中的 `setup_ilm_policy` 方法：

```python
"delete": {
    "min_age": "90d",  # 改为90天后删除
    "actions": {
        "delete": {}
    }
}
```

### 添加新的可视化

编辑 `setup_kibana_dashboards.py` 中的仪表盘方法（如 `setup_business_dashboard`），添加新的 `vis_configs`:

```python
vis_configs.append({
    "title": "你的可视化标题",
    "description": "描述",
    "visState": {
        # 可视化配置
    }
})
```

### 修改索引设置

编辑 `optimize_elasticsearch.py` 中的 `create_index_template` 方法，调整 `settings`:

```python
"settings": {
    "number_of_shards": 2,  # 增加分片数
    "number_of_replicas": 1,  # 增加副本数
    "refresh_interval": "10s",  # 更频繁的刷新
    # ...
}
```

## 故障排查

### 脚本报错: "Connection refused"

**原因**: Elasticsearch或Kibana未运行

**解决**:
```bash
# 启动监控服务
docker-compose -f docker-compose.monitoring.yml up -d

# 检查服务状态
docker-compose -f docker-compose.monitoring.yml ps
```

### 脚本报错: "Data view not found"

**原因**: 数据视图不存在

**解决**:
1. 访问 Kibana: http://localhost:5601
2. 导航到 Management → Stack Management → Data Views
3. 创建数据视图，索引模式为 `ai-platform-*`
4. 记下数据视图ID，更新脚本中的 `DATA_VIEW_ID`

### Unicode编码错误 (Windows)

**原因**: Windows终端默认使用GBK编码

**解决**: 脚本已添加UTF-8编码支持，如果仍有问题：
```bash
# 在PowerShell中设置UTF-8编码
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
chcp 65001

# 然后运行脚本
python scripts/setup_kibana_dashboards.py
```

### 可视化不显示数据

**原因**:
1. 时间范围内没有数据
2. 字段映射不匹配
3. 查询条件错误

**解决**:
1. 在Kibana中调整时间范围到"Last 7 days"
2. 在Discover中验证数据存在
3. 检查可视化使用的字段是否在日志中存在

### ILM策略未生效

**原因**: 现有索引不会自动应用新的ILM策略

**解决**:
```bash
# 手动为现有索引设置ILM策略
curl -X PUT "http://localhost:9200/ai-platform-*/_settings" \
  -H "Content-Type: application/json" \
  -d '{
    "index.lifecycle.name": "ai-platform-ilm-policy"
  }'
```

## 性能调优建议

### 对于高负载场景

1. **增加分片数**:
   ```python
   "number_of_shards": 3  # 在索引模板中
   ```

2. **调整刷新间隔**:
   ```python
   "refresh_interval": "60s"  # 降低刷新频率
   ```

3. **使用批量索引**:
   - 在Logstash中增加 `pipeline.batch.size`

### 对于存储空间有限

1. **减少保留时间**:
   ```python
   "delete": {
       "min_age": "14d"  # 14天后删除
   }
   ```

2. **启用最佳压缩**:
   ```python
   "index.codec": "best_compression"
   ```

3. **定期清理不用的索引**:
   ```bash
   curl -X DELETE "http://localhost:9200/ai-platform-2026.01.01"
   ```

## 监控和维护

### 定期检查

```bash
# 检查索引大小
curl "http://localhost:9200/_cat/indices/ai-platform-*?v&h=index,docs.count,store.size&s=index:desc"

# 检查ILM执行状态
curl "http://localhost:9200/_ilm/status?pretty"

# 检查集群健康
curl "http://localhost:9200/_cluster/health?pretty"
```

### 备份仪表盘配置

```bash
# 导出所有仪表盘
curl -X POST "http://localhost:5601/api/saved_objects/_export" \
  -H "kbn-xsrf: true" \
  -H "Content-Type: application/json" \
  -d '{"type": "dashboard"}' \
  -o dashboards_backup.ndjson

# 导出所有可视化
curl -X POST "http://localhost:5601/api/saved_objects/_export" \
  -H "kbn-xsrf: true" \
  -H "Content-Type: application/json" \
  -d '{"type": "visualization"}' \
  -o visualizations_backup.ndjson
```

### 恢复仪表盘配置

```bash
# 导入仪表盘
curl -X POST "http://localhost:5601/api/saved_objects/_import" \
  -H "kbn-xsrf: true" \
  --form file=@dashboards_backup.ndjson
```

## 相关文档

- [Kibana仪表盘使用指南](../docs/KIBANA_DASHBOARD_GUIDE.md)
- [监控和日志系统指南](../docs/MONITORING_AND_LOGGING_GUIDE.md)
- [Kibana API文档](https://www.elastic.co/guide/en/kibana/current/api.html)
- [Elasticsearch ILM文档](https://www.elastic.co/guide/en/elasticsearch/reference/current/index-lifecycle-management.html)

## 技术支持

如遇到问题，请：

1. 查看脚本输出的错误信息
2. 检查Elasticsearch和Kibana日志
3. 参考故障排查部分
4. 查阅相关文档

## 更新日志

- **2026-01-23**: 初始版本
  - 添加setup_kibana_dashboards.py
  - 添加optimize_elasticsearch.py
  - 支持自动创建3个核心仪表盘
  - 配置ILM策略和索引模板
