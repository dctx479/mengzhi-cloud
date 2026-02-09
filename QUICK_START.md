# AI赋能云平台 - 快速启动指南

## 一、快速启动

### 1.1 启动所有服务

```bash
cd "E:\项目\数商\AI赋能云平台"
docker compose up -d
```

### 1.2 检查服务状态

```bash
docker compose ps
```

预期输出:
```
NAME            STATUS
agri-backend    Up (healthy)
agri-frontend   Up (healthy)
agri-mysql      Up (healthy)
agri-redis      Up (healthy)
```

### 1.3 访问服务

- **前端**: http://localhost:5173
- **后端API**: http://localhost:5000
- **API文档**: http://localhost:5000/docs
- **健康检查**: http://localhost:5000/health

---

## 二、常用命令

### 2.1 容器管理

```bash
# 启动服务
docker compose up -d

# 停止服务
docker compose down

# 重启服务
docker compose restart

# 查看日志
docker compose logs -f

# 查看特定服务日志
docker compose logs backend -f

# 重新构建并启动
docker compose up -d --build
```

### 2.2 数据库操作

```bash
# 连接MySQL
docker exec -it agri-mysql mysql -uagri_user -pagri_pass agri_platform

# 查看数据表
docker exec agri-mysql mysql -uagri_user -pagri_pass -e "USE agri_platform; SHOW TABLES;"

# 备份数据库
docker exec agri-mysql mysqldump -uagri_user -pagri_pass agri_platform > backup.sql

# 测试Redis
docker exec agri-redis redis-cli PING
```

### 2.3 API测试

```bash
# 健康检查
curl http://localhost:5000/health

# 获取产品列表
curl http://localhost:5000/api/v1/products
```

---

## 三、故障排查

### 3.1 查看日志

```bash
# 查看所有日志
docker compose logs

# 查看Backend日志
docker compose logs backend --tail=100

# 实时查看日志
docker compose logs -f
```

### 3.2 重启服务

```bash
# 重启所有服务
docker compose restart

# 重启特定服务
docker compose restart backend
```

---

## 四、更多信息

详细测试报告请查看: `TEST_REPORT.md`

**最后更新**: 2026-01-23
