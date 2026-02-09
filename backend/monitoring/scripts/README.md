# Grafana仪表盘导入工具

自动导入社区仪表盘和自定义仪表盘到Grafana。

## 目录结构

```
monitoring/
├── grafana/
│   ├── dashboards/              # 自定义仪表盘 (自动加载)
│   │   ├── ai-platform-overview.json
│   │   ├── api-performance.json
│   │   ├── service-availability.json
│   │   ├── resource-utilization.json
│   │   └── payment-dashboard.json
│   └── provisioning/
│       ├── dashboards/
│       │   └── default.yml      # 仪表盘provisioning配置
│       └── datasources/
│           └── prometheus.yml   # Prometheus数据源配置
└── scripts/
    ├── import-community-dashboards.sh   # Linux/Mac导入脚本
    ├── import-community-dashboards.bat  # Windows导入脚本
    ├── import-community-dashboards.py   # Python跨平台脚本(推荐)
    └── README.md                        # 本文档
```

## 自定义仪表盘 (已自动加载)

这些仪表盘通过Grafana provisioning机制自动加载,无需手动导入:

### 1. API性能监控 (api-performance.json)
- **QPS**: 每秒请求数
- **响应时间**: P50/P95/P99分位数
- **错误率**: 4xx和5xx错误百分比
- **状态码分布**: HTTP状态码统计
- **慢端点分析**: Top 10最慢的API端点
- **数据库性能**: 查询响应时间和缓存命中率

### 2. 服务可用性监控 (service-availability.json)
- **服务健康状态**: Backend/MySQL/Redis连接状态
- **SLA达标率**: 可用性目标跟踪(99.9%)
- **容器重启次数**: 容器稳定性监控
- **数据库连接池**: MySQL连接池状态
- **外部API**: 第三方服务调用成功率
- **错误日志**: 近期错误日志查看

### 3. 资源利用率监控 (resource-utilization.json)
- **CPU使用率**: 系统和容器CPU利用率
- **内存使用率**: 内存消耗和Swap使用
- **磁盘使用率**: 磁盘空间和I/O性能
- **网络流量**: 网络带宽和数据包统计
- **容器资源**: Top 10容器CPU/内存/网络使用

### 4. AI平台监控概览 (ai-platform-overview.json)
- 平台核心指标概览

### 5. 支付系统监控 (payment-dashboard.json)
- 支付成功率和失败率
- 支付响应时间
- 配额发放监控
- 支付回调状态

## 社区仪表盘 (需要导入)

以下仪表盘需要使用导入脚本从Grafana.com获取:

### 1. Node Exporter Full (ID: 1860)
- **描述**: 全面的系统监控仪表盘
- **指标**: CPU、内存、磁盘、网络、系统负载
- **来源**: [Grafana.com](https://grafana.com/grafana/dashboards/1860)

### 2. Docker Container & Host Metrics (ID: 179)
- **描述**: Docker容器和宿主机监控
- **指标**: 容器资源、网络、存储、宿主机状态
- **来源**: [Grafana.com](https://grafana.com/grafana/dashboards/179)

## 导入社区仪表盘

### 方法1: Python脚本 (推荐)

**优点**: 跨平台、可靠、易于调试

```bash
# 确保Python 3和requests库已安装
pip install requests

# 运行导入脚本
cd backend/monitoring/scripts
python import-community-dashboards.py

# 自定义参数
python import-community-dashboards.py \
    --url http://localhost:3000 \
    --user admin \
    --password admin123 \
    --datasource Prometheus
```

### 方法2: Bash脚本 (Linux/Mac)

```bash
cd backend/monitoring/scripts
chmod +x import-community-dashboards.sh
./import-community-dashboards.sh
```

**环境变量配置**:
```bash
export GRAFANA_URL=http://localhost:3000
export GRAFANA_USER=admin
export GRAFANA_PASSWORD=admin123
./import-community-dashboards.sh
```

### 方法3: Windows批处理

```cmd
cd backend\monitoring\scripts
import-community-dashboards.bat
```

**环境变量配置**:
```cmd
set GRAFANA_URL=http://localhost:3000
set GRAFANA_USER=admin
set GRAFANA_PASSWORD=admin123
import-community-dashboards.bat
```

### 方法4: 手动导入 (备选)

如果脚本导入失败,可以手动导入:

1. 访问Grafana: http://localhost:3000
2. 登录 (admin/admin123)
3. 点击左侧菜单 "+" → "Import"
4. 输入仪表盘ID:
   - Node Exporter Full: `1860`
   - Docker Container & Host Metrics: `179`
5. 选择Prometheus数据源
6. 点击"Import"

## 验证仪表盘

### 1. 检查自定义仪表盘加载

```bash
# 访问Grafana
http://localhost:3000

# 查看仪表盘列表
# 左侧菜单 → Dashboards → Browse

# 应该看到以下仪表盘:
# - AI平台监控概览
# - API性能监控
# - 服务可用性监控
# - 资源利用率监控
# - 支付系统监控仪表板
```

### 2. 检查社区仪表盘导入

```bash
# 运行导入脚本后,应该看到:
# - Node Exporter Full
# - Docker Container & Host Metrics
```

### 3. 验证数据刷新

- 打开任意仪表盘
- 检查右上角刷新间隔: 应为 "30s"
- 观察图表是否有数据更新
- 如果没有数据,检查:
  - Prometheus是否运行: http://localhost:9090
  - 数据源配置是否正确
  - Targets是否健康: http://localhost:9090/targets

## 故障排查

### 问题1: 仪表盘未自动加载

**症状**: 访问Grafana看不到自定义仪表盘

**解决方案**:
```bash
# 1. 检查volume挂载
docker-compose -f docker-compose.monitoring.yml config | grep dashboards

# 应该看到:
# - ./monitoring/grafana/dashboards:/var/lib/grafana/dashboards:ro

# 2. 检查provisioning配置
cat backend/monitoring/grafana/provisioning/dashboards/default.yml

# path应该是: /var/lib/grafana/dashboards

# 3. 重启Grafana容器
docker-compose -f docker-compose.monitoring.yml restart grafana

# 4. 检查Grafana日志
docker-compose -f docker-compose.monitoring.yml logs grafana | grep -i dashboard
```

### 问题2: 社区仪表盘导入失败

**症状**: 脚本报错或仪表盘未出现

**解决方案**:
```bash
# 1. 检查Grafana是否运行
curl http://localhost:3000/api/health

# 2. 检查网络连接
curl https://grafana.com/api/dashboards/1860/revisions/latest/download

# 3. 使用手动导入方式(见上文)

# 4. 检查Grafana API日志
docker-compose -f docker-compose.monitoring.yml logs grafana | tail -100
```

### 问题3: 仪表盘无数据

**症状**: 仪表盘加载但图表为空

**解决方案**:
```bash
# 1. 检查Prometheus运行状态
docker-compose -f docker-compose.monitoring.yml ps prometheus

# 2. 检查Prometheus targets
curl http://localhost:9090/api/v1/targets | jq '.data.activeTargets[] | {job: .labels.job, health: .health}'

# 3. 检查数据源配置
# Grafana → Configuration → Data Sources → Prometheus
# URL应该是: http://prometheus:9090

# 4. 测试Prometheus查询
curl -G http://localhost:9090/api/v1/query --data-urlencode 'query=up'

# 5. 检查backend指标暴露
curl http://localhost:8000/metrics
```

### 问题4: 权限错误

**症状**: "Access denied" 或 "Unauthorized"

**解决方案**:
```bash
# 1. 确认Grafana凭据正确
# 默认: admin/admin123

# 2. 检查是否需要修改密码
# 首次登录可能要求修改密码

# 3. 使用环境变量
export GRAFANA_USER=admin
export GRAFANA_PASSWORD=your_password
python import-community-dashboards.py
```

## 自定义配置

### 修改默认凭据

编辑 `docker-compose.monitoring.yml`:

```yaml
grafana:
  environment:
    - GF_SECURITY_ADMIN_USER=your_user
    - GF_SECURITY_ADMIN_PASSWORD=your_password
```

### 修改刷新间隔

编辑仪表盘JSON文件,修改 `refresh` 字段:

```json
{
  "dashboard": {
    "refresh": "30s"  // 可选: 5s, 10s, 30s, 1m, 5m, 15m, 30m, 1h
  }
}
```

### 添加自定义仪表盘

1. 在Grafana UI中创建仪表盘
2. 导出JSON:
   - Dashboard settings → JSON Model → Copy to clipboard
3. 保存到 `backend/monitoring/grafana/dashboards/your-dashboard.json`
4. 添加以下包装结构:
   ```json
   {
     "dashboard": {
       // 粘贴导出的JSON内容
     },
     "overwrite": true
   }
   ```
5. 重启Grafana:
   ```bash
   docker-compose -f docker-compose.monitoring.yml restart grafana
   ```

## 相关文档

- [Grafana Provisioning文档](https://grafana.com/docs/grafana/latest/administration/provisioning/)
- [Grafana仪表盘导入API](https://grafana.com/docs/grafana/latest/http_api/dashboard/)
- [Grafana.com仪表盘库](https://grafana.com/grafana/dashboards/)
- [Prometheus查询语法](https://prometheus.io/docs/prometheus/latest/querying/basics/)

## 维护建议

1. **定期更新社区仪表盘**:
   ```bash
   # 每月运行一次导入脚本
   python import-community-dashboards.py
   ```

2. **备份自定义仪表盘**:
   ```bash
   # 导出所有仪表盘
   cd backend/monitoring/grafana/dashboards
   git add *.json
   git commit -m "Update dashboards"
   ```

3. **监控仪表盘性能**:
   - 避免在仪表盘中使用过于复杂的查询
   - 合理设置时间范围和刷新间隔
   - 定期检查Grafana日志

4. **版本管理**:
   - 仪表盘JSON文件纳入Git版本控制
   - 重大修改前先导出备份
   - 使用版本号标记重要变更
