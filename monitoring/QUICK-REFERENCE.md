# 监控系统快速参考

## 快速启动

```bash
# Windows
cd E:\项目\数商\AI赋能云平台\monitoring
start.bat

# Linux/Mac
cd /path/to/monitoring
./start.sh
```

## 访问地址

| 服务 | URL | 默认账号 |
|------|-----|----------|
| Prometheus | http://localhost:9090 | - |
| Grafana | http://localhost:3000 | admin/admin123 |
| Alertmanager | http://localhost:9093 | - |

## 常用命令

```bash
# 查看服务状态
docker-compose ps

# 查看日志
docker-compose logs -f [service_name]

# 重启服务
docker-compose restart [service_name]

# 停止所有服务
docker-compose down

# 停止并删除数据
docker-compose down -v
```

## 关键指标

| 指标 | 说明 | 正常范围 |
|------|------|----------|
| payment_success_rate | 支付成功率 | > 95% |
| payment_duration_seconds (P95) | 支付响应时间 | < 2秒 |
| payment_signature_verification_failures | 签名验证失败 | 0次/分钟 |
| concurrent_payment_requests | 并发支付请求 | < 100 |
| payment_pending_total | 待支付订单 | < 1000 |

## 告警级别

| 级别 | 响应时间 | 通知方式 |
|------|----------|----------|
| emergency | 立即 | Email + Webhook + 电话 |
| critical | 5分钟内 | Email + Webhook |
| warning | 30分钟内 | Email |
| info | 无需响应 | 记录日志 |

## 常见问题

### Prometheus 无法抓取指标

```bash
# 检查后端服务
docker-compose ps backend

# 测试 metrics 端点
curl http://localhost:8000/metrics

# 查看 Prometheus 日志
docker-compose logs prometheus
```

### Grafana 无数据

```bash
# 测试 Prometheus 连接
curl http://localhost:9090/api/v1/query?query=up

# 重启 Grafana
docker-compose restart grafana
```

### 告警未触发

```bash
# 检查告警规则状态
# 访问: http://localhost:9090/alerts

# 查看 Alertmanager 日志
docker-compose logs alertmanager
```

## 紧急联系

- 技术支持: ops@example.com
- 紧急联系: emergency@example.com

## 更多信息

详细文档: [README.md](./README.md)
交付总结: [DELIVERY-SUMMARY.md](./DELIVERY-SUMMARY.md)
