# Docker 部署指南

## 服务架构

```
┌──────────────┐
│  Frontend    │ :80 (生产) / :5173 (开发)
│  Nginx / Vite│
└──────┬───────┘
       │ /api/* 反向代理
┌──────▼───────┐     ┌──────────┐     ┌──────────┐
│  Backend     │────▶│ MySQL 8  │     │ Redis 7  │
│  FastAPI     │     │ :3306    │     │ :6379    │
│  :8000       │────▶│          │     │          │
└──────────────┘     └──────────┘     └──────────┘
```

| 服务 | 镜像 | 容器内端口 | 默认宿主机端口 | 说明 |
|------|------|-----------|---------------|------|
| frontend | nginx:alpine / node:20-alpine | 80 / 5173 | 80 / 5173 | SPA + 反向代理 |
| backend | python:3.11-slim | 8000 | 8001 | FastAPI + Uvicorn |
| mysql | mysql:8.0 | 3306 | 3307 | 数据库 |
| redis | redis:7-alpine | 6379 | 6380 | 缓存 + Token 黑名单 |

---

## Compose 文件说明

| 文件 | 用途 | 前端模式 | 后端模式 |
|------|------|---------|---------|
| `docker-compose.yml` | 生产部署 | Nginx 静态文件 | Gunicorn/Uvicorn |
| `docker-compose.dev.yml` | 开发环境 | Vite 热重载 (:5173) | Uvicorn --reload |
| `docker-compose.test.yml` | 测试 | 不含 | 不含（仅 MySQL + Redis） |

---

## 开发环境

```bash
# 1. 配置环境变量
cp .env.docker.example .env.docker
# 编辑 .env.docker，填入 DEEPSEEK_API_KEY 等

# 2. 启动
docker compose -f docker-compose.dev.yml up -d

# 3. 访问
# 前端:      http://localhost:5173
# 后端 API:  http://localhost:8001
# Swagger:   http://localhost:8001/docs
# 默认管理员: admin / admin123

# 4. 查看日志
docker compose -f docker-compose.dev.yml logs -f backend
```

开发模式特点：
- 后端挂载 `./backend` 源码目录，代码变更自动重载
- 前端挂载 `./frontend` 源码目录，Vite HMR 即时刷新
- MySQL 使用 root 用户（简化开发）

---

## 生产部署

### 1. 准备环境变量

```bash
cp .env.docker.example .env.docker
```

编辑 `.env.docker`，至少修改以下项：

```env
# 必须修改（安全）
ENVIRONMENT=production
SECRET_KEY=<使用 python -c "import secrets; print(secrets.token_urlsafe(48))" 生成>
ENCRYPTION_KEY=<生成另一个强密钥>
MYSQL_PASSWORD=<强数据库密码>

# 可选（AI 功能）
DEEPSEEK_API_KEY=<你的 DeepSeek API Key>

# 可选（京东联盟商品导入）
JD_APP_KEY=<京东联盟 AppKey>
JD_SECRET_KEY=<京东联盟 Secret>
JD_OAUTH_REDIRECT_URI=https://你的域名/api/v1/jd/oauth/callback

# 可选（淘宝联盟商品导入）
TAOBAO_APP_KEY=<淘宝联盟 AppKey>
TAOBAO_APP_SECRET=<淘宝联盟 Secret>
TAOBAO_OAUTH_REDIRECT_URI=https://你的域名/api/v1/taobao/oauth/callback
```

### 2. 构建并启动

```bash
docker compose up -d --build
```

### 3. 验证

```bash
# 检查服务状态
docker compose ps

# 健康检查
curl http://localhost/api/v1/health

# 查看日志
docker compose logs -f backend
```

### 4. 配置 HTTPS（推荐 Caddy）

```
# /etc/caddy/Caddyfile
shushang.online {
    reverse_proxy localhost:80
}
```

或使用 Nginx + Let's Encrypt：

```nginx
server {
    listen 443 ssl;
    server_name shushang.online;

    ssl_certificate     /etc/letsencrypt/live/shushang.online/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/shushang.online/privkey.pem;

    location / {
        proxy_pass http://127.0.0.1:80;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

---

## 常用命令

```bash
# 服务管理
docker compose up -d                    # 启动
docker compose down                     # 停止
docker compose restart backend          # 重启单个服务
docker compose ps                       # 查看状态
docker compose logs -f backend          # 查看日志

# 数据库
docker exec agri-mysql mysqldump -u agri_user -p agri_platform > backup.sql
docker exec -i agri-mysql mysql -u agri_user -p agri_platform < backup.sql

# 进入容器
docker exec -it agri-backend bash
docker exec -it agri-mysql mysql -u root -p

# 资源监控
docker stats
```

---

## 数据持久化

Docker 命名卷：

| 卷名 | 用途 |
|------|------|
| `mysql_data` | MySQL 数据文件 |
| `redis_data` | Redis AOF 持久化 |
| `backend_logs` | 应用日志 |
| `backend_uploads` | 用户上传文件 |

数据卷在 `docker compose down` 时保留，`docker compose down -v` 会删除。

---

## 定时任务

后端启动时自动注册 APScheduler 定时任务：

| 任务 | 调度 | 说明 |
|------|------|------|
| 每日对账 | 每天 02:00 | 自动核验订单对账 |
| 差异检查 | 每 4 小时 | 检查待处理对账差异 |
| 健康检查 | 每天 09:00 | 对账系统自检 |
| 淘宝 Session 刷新 | 每 20 小时 | 自动刷新淘宝 OAuth2 Session（有效期 1 天） |

---

## OAuth2 授权配置

京东和淘宝商品导入需要 OAuth2 授权。流程：

1. 在开放平台创建应用，获取 AppKey / Secret
2. 在 `.env.docker` 中配置 AppKey、Secret 和回调地址
3. 在开放平台「应用设置」中注册回调地址
4. 启动服务后，登录管理后台 → 系统管理 → 京东/淘宝导入 → 点击「OAuth2 授权」按钮
5. 在弹出窗口中完成授权，Session 自动保存到数据库

| 平台 | OAuth2 回调地址 | Session 有效期 | 自动刷新 |
|------|----------------|---------------|---------|
| 京东联盟 | `/api/v1/jd/oauth/callback` | 30 天 | 不需要 |
| 淘宝联盟 | `/api/v1/taobao/oauth/callback` | 1 天 | 每 20 小时自动刷新 |

---

## 故障排查

| 问题 | 排查方法 |
|------|---------|
| 后端启动失败 | `docker compose logs backend` 查看错误 |
| 数据库连接失败 | 检查 MySQL 健康状态：`docker compose ps`，确认 `service_healthy` |
| 前端 API 404 | 确认 Nginx 反向代理配置，检查 `/api/` 路径 |
| 京东/淘宝授权失败 | 确认回调地址与开放平台注册一致，检查 HTTPS 配置 |
| 淘宝 Session 过期 | 管理后台点击「刷新 Session」，或重新授权 |
