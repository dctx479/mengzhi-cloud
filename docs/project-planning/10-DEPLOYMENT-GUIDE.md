# 部署指南
## Deployment Guide v1.0

**文档版本**: 1.0  
**创建日期**: 2026-06-11  
**适用阶段**: Sprint 6 (Week 11-12) + 生产环境

---

## 一、部署架构

### 1.1 生产环境架构

```
                    Internet
                       ↓
              ┌────────────────┐
              │  域名/DNS解析  │
              │ mengzhi.cloud  │
              └────────┬───────┘
                       ↓
              ┌────────────────┐
              │  阿里云服务器  │
              │   2C4G 40GB    │
              │  Ubuntu 22.04  │
              └────────┬───────┘
                       ↓
              ┌────────────────┐
              │  Nginx :80/443 │
              │  SSL/HTTPS     │
              └─────┬────┬─────┘
                    │    │
           前端静态资源│  │后端API代理
                    ↓    ↓
            ┌────────┐  ┌─────────────┐
            │ Vue 3  │  │ FastAPI:8000│
            │  SPA   │  │  (Docker)   │
            └────────┘  └──────┬──────┘
                               ↓
              ┌────────────────┴────────────┐
              ↓                ↓            ↓
        ┌──────────┐  ┌──────────┐  ┌──────────┐
        │PostgreSQL│  │ Redis:6379│  │MinIO:9000│
        │  :5432   │  │  (Docker) │  │ (Docker) │
        └──────────┘  └──────────┘  └──────────┘
                               ↓
                      ┌────────────────┐
                      │ Anthropic API  │
                      │  (Claude SDK)  │
                      └────────────────┘
```

### 1.2 服务器配置要求

**最低配置**:
- CPU: 2核
- 内存: 4GB
- 硬盘: 40GB SSD
- 带宽: 3Mbps

**推荐配置**（100+ DAU）:
- CPU: 4核
- 内存: 8GB
- 硬盘: 80GB SSD
- 带宽: 5Mbps

---

## 二、服务器准备

### 2.1 购买云服务器

**阿里云ECS**:
```bash
# 推荐配置
实例规格: ecs.c6.large (2C4G)
镜像: Ubuntu 22.04 LTS
磁盘: 40GB ESSD
网络: 按量计费 3Mbps
地域: 华北2（北京）
```

**域名备案**:
1. 购买域名（mengzhi.cloud）
2. 提交ICP备案（7-20个工作日）
3. 配置DNS解析到服务器IP

### 2.2 初始化服务器

```bash
# SSH登录
ssh root@<服务器IP>

# 更新系统
apt update && apt upgrade -y

# 创建部署用户
adduser deploy
usermod -aG sudo deploy
su - deploy

# 安装基础工具
sudo apt install -y git curl wget vim htop
```

### 2.3 安装Docker

```bash
# 安装Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# 添加当前用户到docker组
sudo usermod -aG docker $USER
newgrp docker

# 安装Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/download/v2.20.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# 验证安装
docker --version
docker-compose --version
```

### 2.4 配置防火墙

```bash
# 安装UFW
sudo apt install -y ufw

# 开放端口
sudo ufw allow 22/tcp    # SSH
sudo ufw allow 80/tcp    # HTTP
sudo ufw allow 443/tcp   # HTTPS

# 启动防火墙
sudo ufw enable

# 查看状态
sudo ufw status
```

---

## 三、代码部署

### 3.1 克隆代码

```bash
# 创建项目目录
mkdir -p /home/deploy/apps
cd /home/deploy/apps

# 克隆仓库（使用部署密钥）
git clone git@github.com:your-org/mengzhi-cloud.git
cd mengzhi-cloud
```

### 3.2 配置环境变量

**后端环境变量**:
```bash
# backend/.env.prod
DATABASE_URL=postgresql://mengzhi:password@localhost:5432/mengzhi
REDIS_URL=redis://localhost:6379/0
MINIO_ENDPOINT=localhost:9000
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=minioadmin

# 敏感信息（加密存储）
ANTHROPIC_API_KEY=sk-ant-xxxxx
SECRET_KEY=<生成强随机密钥>
JWT_SECRET_KEY=<生成强随机密钥>

# 生成密钥
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

**前端环境变量**:
```bash
# frontend/.env.production
VITE_API_BASE_URL=https://api.mengzhi.cloud
VITE_MINIO_ENDPOINT=https://cdn.mengzhi.cloud
```

### 3.3 构建项目

**后端构建**:
```bash
cd backend

# 构建Docker镜像
docker build -t mengzhi-backend:latest .
```

**前端构建**:
```bash
cd frontend

# 安装依赖
npm ci

# 生产构建
npm run build

# 输出目录: dist/
```

---

## 四、Docker部署

### 4.1 docker-compose配置

```yaml
# docker-compose.prod.yml
version: '3.8'

services:
  postgres:
    image: postgres:15
    container_name: mengzhi-postgres
    environment:
      POSTGRES_DB: mengzhi
      POSTGRES_USER: mengzhi
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"
    restart: unless-stopped
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U mengzhi"]
      interval: 10s
      timeout: 5s
      retries: 5

  redis:
    image: redis:7-alpine
    container_name: mengzhi-redis
    command: redis-server --appendonly yes --requirepass ${REDIS_PASSWORD}
    volumes:
      - redis_data:/data
    ports:
      - "6379:6379"
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 3s
      retries: 5

  minio:
    image: minio/minio:latest
    container_name: mengzhi-minio
    command: server /data --console-address ":9001"
    environment:
      MINIO_ROOT_USER: ${MINIO_ACCESS_KEY}
      MINIO_ROOT_PASSWORD: ${MINIO_SECRET_KEY}
    volumes:
      - minio_data:/data
    ports:
      - "9000:9000"
      - "9001:9001"
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:9000/minio/health/live"]
      interval: 30s
      timeout: 20s
      retries: 3

  backend:
    image: mengzhi-backend:latest
    container_name: mengzhi-backend
    env_file: backend/.env.prod
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
    ports:
      - "8000:8000"
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3

volumes:
  postgres_data:
  redis_data:
  minio_data:
```

### 4.2 启动服务

```bash
# 启动所有服务
docker-compose -f docker-compose.prod.yml up -d

# 查看日志
docker-compose -f docker-compose.prod.yml logs -f backend

# 检查健康状态
docker ps
curl http://localhost:8000/health
```

### 4.3 数据库初始化

```bash
# 进入后端容器
docker exec -it mengzhi-backend bash

# 执行数据库迁移
alembic upgrade head

# 初始化数据
python scripts/init_data.py

# 创建管理员账号
python scripts/create_admin.py
```

---

## 五、Nginx配置

### 5.1 安装Nginx

```bash
sudo apt install -y nginx
```

### 5.2 配置SSL证书

**申请Let's Encrypt证书**:
```bash
# 安装Certbot
sudo apt install -y certbot python3-certbot-nginx

# 申请证书
sudo certbot --nginx -d mengzhi.cloud -d api.mengzhi.cloud

# 自动续期（已配置cron）
sudo certbot renew --dry-run
```

### 5.3 Nginx配置文件

```nginx
# /etc/nginx/sites-available/mengzhi

# 后端API
upstream backend {
    server 127.0.0.1:8000 max_fails=3 fail_timeout=30s;
}

# HTTP重定向到HTTPS
server {
    listen 80;
    server_name mengzhi.cloud api.mengzhi.cloud;
    return 301 https://$server_name$request_uri;
}

# 主站（前端）
server {
    listen 443 ssl http2;
    server_name mengzhi.cloud;

    # SSL证书
    ssl_certificate /etc/letsencrypt/live/mengzhi.cloud/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/mengzhi.cloud/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;

    # 安全头
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;

    # 前端静态资源
    root /home/deploy/apps/mengzhi-cloud/frontend/dist;
    index index.html;

    # SPA路由
    location / {
        try_files $uri $uri/ /index.html;
    }

    # 静态资源缓存
    location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2|ttf)$ {
        expires 7d;
        add_header Cache-Control "public, immutable";
    }

    # 压缩
    gzip on;
    gzip_types text/plain text/css application/json application/javascript text/xml application/xml;
    gzip_min_length 1000;
}

# API服务
server {
    listen 443 ssl http2;
    server_name api.mengzhi.cloud;

    ssl_certificate /etc/letsencrypt/live/mengzhi.cloud/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/mengzhi.cloud/privkey.pem;

    # 代理到后端
    location / {
        proxy_pass http://backend;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # 超时设置（LLM调用可能较慢）
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;

        # WebSocket支持
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }

    # 健康检查端点不限流
    location /health {
        proxy_pass http://backend;
    }
}
```

### 5.4 启用配置

```bash
# 软链接到启用目录
sudo ln -s /etc/nginx/sites-available/mengzhi /etc/nginx/sites-enabled/

# 测试配置
sudo nginx -t

# 重启Nginx
sudo systemctl restart nginx

# 开机自启
sudo systemctl enable nginx
```

---

## 六、监控与日志

### 6.1 日志管理

**Nginx日志**:
```bash
# 访问日志
tail -f /var/log/nginx/access.log

# 错误日志
tail -f /var/log/nginx/error.log
```

**应用日志**:
```bash
# 后端日志（Docker）
docker logs -f mengzhi-backend

# 持久化日志（挂载卷）
docker run -v /var/log/mengzhi:/app/logs ...
```

### 6.2 监控指标

**系统监控**:
```bash
# 安装htop
sudo apt install -y htop

# 查看资源使用
htop
df -h
free -h
```

**应用监控**（推荐Prometheus + Grafana）:
```yaml
# docker-compose.prod.yml 添加监控服务
services:
  prometheus:
    image: prom/prometheus:latest
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml
      - prometheus_data:/prometheus
    ports:
      - "9090:9090"

  grafana:
    image: grafana/grafana:latest
    volumes:
      - grafana_data:/var/lib/grafana
    ports:
      - "3000:3000"
    environment:
      GF_SECURITY_ADMIN_PASSWORD: ${GRAFANA_PASSWORD}
```

---

## 七、备份与恢复

### 7.1 数据库备份

**每日自动备份**:
```bash
# /home/deploy/scripts/backup_db.sh
#!/bin/bash

BACKUP_DIR="/home/deploy/backups"
DATE=$(date +%Y%m%d_%H%M%S)
FILENAME="mengzhi_${DATE}.sql.gz"

# 备份数据库
docker exec mengzhi-postgres pg_dump -U mengzhi mengzhi | gzip > "${BACKUP_DIR}/${FILENAME}"

# 删除7天前的备份
find ${BACKUP_DIR} -name "mengzhi_*.sql.gz" -mtime +7 -delete

echo "Backup completed: ${FILENAME}"
```

**配置定时任务**:
```bash
# 编辑crontab
crontab -e

# 每天凌晨2点备份
0 2 * * * /home/deploy/scripts/backup_db.sh >> /home/deploy/logs/backup.log 2>&1
```

### 7.2 数据恢复

```bash
# 停止应用
docker-compose -f docker-compose.prod.yml stop backend

# 恢复数据库
gunzip -c /home/deploy/backups/mengzhi_20260610.sql.gz | \
  docker exec -i mengzhi-postgres psql -U mengzhi mengzhi

# 重启应用
docker-compose -f docker-compose.prod.yml start backend
```

---

## 八、CI/CD自动化

### 8.1 GitHub Actions配置

```yaml
# .github/workflows/deploy.yml
name: Deploy to Production

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Setup SSH
        uses: webfactory/ssh-agent@v0.7.0
        with:
          ssh-private-key: ${{ secrets.DEPLOY_SSH_KEY }}
      
      - name: Deploy to server
        run: |
          ssh deploy@${{ secrets.SERVER_IP }} << 'EOF'
            cd /home/deploy/apps/mengzhi-cloud
            git pull origin main
            docker-compose -f docker-compose.prod.yml build backend
            docker-compose -f docker-compose.prod.yml up -d backend
            cd frontend && npm ci && npm run build
            sudo systemctl reload nginx
          EOF
```

### 8.2 部署回滚

```bash
# 查看Docker镜像历史
docker images mengzhi-backend

# 回滚到上一个版本
docker tag mengzhi-backend:latest mengzhi-backend:backup
docker tag mengzhi-backend:previous mengzhi-backend:latest
docker-compose -f docker-compose.prod.yml up -d backend
```

---

## 九、性能优化

### 9.1 数据库优化

```bash
# PostgreSQL配置优化
# /etc/postgresql/15/main/postgresql.conf

shared_buffers = 1GB           # 25% of RAM
effective_cache_size = 3GB     # 75% of RAM
maintenance_work_mem = 256MB
checkpoint_completion_target = 0.9
wal_buffers = 16MB
max_connections = 100
```

### 9.2 Redis优化

```bash
# Redis配置
# /etc/redis/redis.conf

maxmemory 512mb
maxmemory-policy allkeys-lru
```

### 9.3 CDN加速

**阿里云CDN配置**:
1. 添加加速域名（cdn.mengzhi.cloud）
2. 源站配置（MinIO域名）
3. 缓存规则（图片7天，JS/CSS 1天）

---

## 十、安全加固

### 10.1 SSH加固

```bash
# /etc/ssh/sshd_config
PermitRootLogin no
PasswordAuthentication no
PubkeyAuthentication yes
Port 22222  # 修改默认端口

# 重启SSH
sudo systemctl restart sshd
```

### 10.2 Fail2Ban防暴力破解

```bash
# 安装Fail2Ban
sudo apt install -y fail2ban

# 配置
sudo cp /etc/fail2ban/jail.conf /etc/fail2ban/jail.local

# 启动
sudo systemctl enable fail2ban
sudo systemctl start fail2ban
```

---

## 十一、故障排查

### 11.1 常见问题

**问题1: 502 Bad Gateway**
```bash
# 检查后端服务
docker ps | grep backend
docker logs mengzhi-backend

# 检查端口监听
netstat -tlnp | grep 8000
```

**问题2: 数据库连接失败**
```bash
# 检查PostgreSQL
docker exec -it mengzhi-postgres psql -U mengzhi

# 检查网络
docker network inspect mengzhi_default
```

**问题3: LLM调用超时**
```bash
# 检查API Key
cat backend/.env.prod | grep ANTHROPIC_API_KEY

# 测试网络连通性
curl -I https://api.anthropic.com
```

---

## 十二、验收标准

| 检查项 | 标准 | 验证方法 |
|-------|------|---------|
| 服务可访问 | HTTPS正常 | curl https://mengzhi.cloud |
| API响应 | 200状态码 | curl https://api.mengzhi.cloud/health |
| 数据库连接 | 成功 | 测试IP对话功能 |
| SSL证书 | 有效 | 浏览器无警告 |
| 自动备份 | 每日执行 | 检查备份目录 |
| 日志记录 | 正常 | 查看nginx/应用日志 |

---

**文档结束**

> 部署后持续监控系统状态，定期检查日志和备份。
