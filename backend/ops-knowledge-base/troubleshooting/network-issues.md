# 网络问题故障排查手册

## 概述

### 问题描述
服务间网络通信异常,包括连接超时、DNS解析失败、网络隔离、防火墙阻止等问题。

### 影响范围
- **影响级别**: Warning/Critical
- **影响用户**: 根据网络分区决定
- **业务影响**: 服务间调用失败、外部API不可达
- **优先级**: 高优先级

---

## 症状识别

### 监控告警
```
AlertName: NetworkConnectivityIssue
Severity: Critical
Description: Cannot reach dependent services
Services Affected: postgres, redis, external-api
```

### 常见错误信息
- `Connection refused`
- `Connection timeout`
- `No route to host`
- `Name or service not known` (DNS)
- `Network is unreachable`

---

## 快速诊断

### Step 1: 检查容器网络

```bash
# 查看容器网络配置
docker network ls
docker network inspect ai-platform_default

# 测试容器间网络
docker exec backend ping -c 3 postgres
docker exec backend ping -c 3 redis

# 测试DNS解析
docker exec backend nslookup postgres
docker exec backend nslookup redis

# 测试端口连通性
docker exec backend telnet postgres 5432
docker exec backend nc -zv postgres 5432
```

### Step 2: 检查防火墙和路由

```bash
# 查看路由表
docker exec backend ip route

# 查看防火墙规则
sudo iptables -L -n
sudo iptables -t nat -L -n

# 测试外网连通性
docker exec backend ping -c 3 8.8.8.8
docker exec backend curl -I https://www.google.com
```

---

## 常见问题和修复

### 问题1: Docker网络故障

**修复**:
```bash
# 重建Docker网络
docker-compose down
docker network prune
docker-compose up -d
```

### 问题2: DNS解析失败

**修复**:
```yaml
# docker-compose.yml
services:
  backend:
    dns:
      - 8.8.8.8
      - 8.8.4.4
```

### 问题3: 跨主机通信问题

**修复**: 使用overlay网络或配置external网络

---

## 相关文档

- [服务不可用排查](./service-down.md)
- [网络配置指南](../runbooks/network-config.md)
