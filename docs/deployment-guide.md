# 蒙智云平台 (mengzhi-cloud) 部署指南

## 项目概览

| 组件 | 技术栈 | 容器名 | 端口 |
|------|--------|--------|------|
| 前端 | Vue 3 + Vite + Nginx | agri-frontend | 80 (HTTP) / 443 (HTTPS) |
| 后端 | Python FastAPI + Uvicorn | agri-backend | 8000 |
| 数据库 | MySQL 8.0 | agri-mysql | 3307 (外部) → 3306 (内部) |
| 缓存 | Redis 7 Alpine | agri-redis | 6380 (外部) → 6379 (内部) |

域名：`shushang.online`

---

## 一、环境要求

- **操作系统**：Ubuntu 22.04+ / CentOS 8+ / Debian 11+
- **Docker**：20.10+
- **Docker Compose**：v2.0+
- **内存**：建议 2GB+
- **磁盘**：建议 20GB+

```bash
# 验证环境
docker --version
docker compose version
```

---

## 二、获取代码

```bash
cd /home/ubuntu
git clone <仓库地址> mengzhi-cloud
cd mengzhi-cloud
```

---

## 三、环境变量配置

```bash
cp .env.docker.example .env.docker
vim .env.docker
```

**必须修改的配置项（生产环境）：**

```bash
# ---- MySQL ----
MYSQL_ROOT_PASSWORD=<强密码>
MYSQL_DATABASE=agri_platform
MYSQL_USER=agri_user
MYSQL_PASSWORD=<强密码>

# ---- 应用安全 ----
ENVIRONMENT=production
SECRET_KEY=<生成方法: python -c "import secrets; print(secrets.token_urlsafe(48))">
ENCRYPTION_KEY=<随机强密钥>

# ---- DeepSeek AI API ----
DEEPSEEK_API_KEY=<你的密钥>

# ---- 京东联盟 (可选) ----
JD_APP_KEY=<你的APP KEY>
JD_SECRET_KEY=<你的密钥>
JD_OAUTH_REDIRECT_URI=https://shushang.online/api/v1/jd/oauth/callback

# ---- 淘宝联盟 (可选) ----
TAOBAO_APP_KEY=<你的APP KEY>
TAOBAO_APP_SECRET=<你的密钥>
TAOBAO_SESSION=<会话TOKEN>
TAOBAO_ADZONE_ID=<推广位ID>
TAOBAO_OAUTH_REDIRECT_URI=https://shushang.online/api/v1/taobao/oauth/callback

# ---- 端口映射 ----
FRONTEND_PORT=80
BACKEND_PORT=8000
MYSQL_PORT=3307
REDIS_HOST_PORT=6380
```

---

## 四、SSL 证书部署（详细指南）

### 4.1 证书文件说明

SSL 证书通常包含以下文件：

| 文件 | 说明 | 是否必须 |
|------|------|----------|
| `*.key` | 私钥文件，申请证书时生成 | 是 |
| `*_bundle.pem` | 证书文件 + 中间证书链（PEM 格式，Nginx 专用） | 是 |
| `*_bundle.crt` | 同上，仅扩展名不同（PEM 格式） | 否（与 .pem 二选一） |
| `*.csr` | 证书签名请求，部署时不需要 | 否 |

> **关键**：Nginx 需要的是**包含完整证书链**的文件（`_bundle.pem` 或 `_bundle.crt`），而不是单独的域名证书。缺少中间证书链会导致部分浏览器/客户端无法验证证书。

### 4.2 获取证书

#### 方式一：云平台免费证书（推荐）

从腾讯云/阿里云申请免费 DV 证书，下载时选择 **Nginx** 格式：

- 腾讯云：SSL 证书管理 → 申请免费证书 → 下载（选 Nginx）
- 阿里云：数字证书管理 → 免费证书 → 下载（选 Nginx/Tengine）

下载后得到 zip 包，如 `shushang.online_nginx.zip`。

#### 方式二：Let's Encrypt 免费证书

```bash
# 安装 certbot
sudo apt install certbot

# 申请证书（需先停止占用 80 端口的服务）
docker compose stop frontend
sudo certbot certonly --standalone -d shushang.online

# 证书文件位置
# /etc/letsencrypt/live/shushang.online/fullchain.pem  → 证书+链
# /etc/letsencrypt/live/shushang.online/privkey.pem    → 私钥

# 复制到项目目录
mkdir -p ssl/
sudo cp /etc/letsencrypt/live/shushang.online/fullchain.pem ssl/shushang.online_bundle.pem
sudo cp /etc/letsencrypt/live/shushang.online/privkey.pem ssl/shushang.online.key
sudo chown ubuntu:ubuntu ssl/*

# 恢复前端服务
docker compose up -d frontend
```

#### 方式三：付费商业证书

从 DigiCert、Sectigo 等 CA 购买，按提供商指引下载 Nginx 格式证书包。

### 4.3 安装证书文件

#### 步骤一：创建证书目录并解压

```bash
cd /home/ubuntu/mengzhi-cloud

# 创建 ssl 目录
mkdir -p ssl/

# 解压证书 zip 包
unzip shushang.online_nginx.zip -d /tmp/

# 查看解压后的文件
ls -la /tmp/shushang.online_nginx/
# shushang.online.csr              ← 不需要
# shushang.online_bundle.crt       ← 证书链（与 .pem 内容相同）
# shushang.online_bundle.pem       ← 证书链（推荐使用此文件）
# shushang.online.key              ← 私钥
```

#### 步骤二：复制必要文件

```bash
# 只需复制两个文件
cp /tmp/shushang.online_nginx/shushang.online_bundle.pem ssl/
cp /tmp/shushang.online_nginx/shushang.online.key ssl/

# 设置安全权限（私钥仅 owner 可读）
chmod 644 ssl/shushang.online_bundle.pem
chmod 600 ssl/shushang.online.key
```

#### 步骤三：验证文件完整性

```bash
# 验证证书信息
openssl x509 -in ssl/shushang.online_bundle.pem -noout -subject -issuer -dates

# 预期输出：
# subject=CN = shushang.online
# issuer=C = CN, O = "TrustAsia Technologies, Inc.", CN = TrustAsia DV TLS RSA CA 2025
# notBefore=May 26 00:00:00 2026 GMT
# notAfter=Dec 10 23:59:59 2026 GMT

# 验证私钥与证书是否匹配（两个输出的 MD5 必须一致）
openssl x509 -noout -modulus -in ssl/shushang.online_bundle.pem | openssl md5
openssl rsa -noout -modulus -in ssl/shushang.online.key | openssl md5
```

#### 最终目录结构

```
mengzhi-cloud/
└── ssl/
    ├── shushang.online_bundle.pem   # 证书文件（含中间证书链）4459 字节
    └── shushang.online.key          # RSA 私钥              1700 字节
```

### 4.4 当前证书信息

| 项目 | 值 |
|------|-----|
| 域名 | shushang.online |
| 颁发机构 | TrustAsia DV TLS RSA CA 2025 |
| 生效日期 | 2026-05-26 |
| 过期日期 | 2026-12-10 |
| 证书类型 | DV（域名验证） |

### 4.5 Nginx 配置详解

配置文件位于 `frontend/nginx.conf`，包含两个 server 块：

#### HTTP Server（端口 80）— 强制跳转 HTTPS

```nginx
server {
    listen 80;
    server_name shushang.online;
    return 301 https://$host$request_uri;
}
```

- `listen 80` — 监听 HTTP 端口
- `server_name shushang.online` — 仅匹配该域名的请求
- `return 301` — 永久重定向到 HTTPS，浏览器会缓存此跳转

#### HTTPS Server（端口 443）— SSL 主配置

```nginx
server {
    listen 443 ssl;
    server_name shushang.online;

    # ---- SSL 证书路径（容器内路径）----
    ssl_certificate /etc/nginx/ssl/shushang.online_bundle.pem;
    ssl_certificate_key /etc/nginx/ssl/shushang.online.key;

    # ---- TLS 协议版本 ----
    # 仅启用 TLS 1.2 和 1.3，禁用不安全的 TLS 1.0/1.1
    ssl_protocols TLSv1.2 TLSv1.3;

    # ---- 加密套件 ----
    # 仅使用 ECDHE + AES-GCM，兼顾安全性和性能
    ssl_ciphers ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384;

    # ---- 优先使用服务端加密套件 ----
    ssl_prefer_server_ciphers on;

    # ---- SSL 会话缓存 ----
    # 10MB 共享缓存，约可存储 4 万个会话，减少 TLS 握手开销
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 10m;

    # ---- 安全响应头 ----
    # HSTS: 强制浏览器在 1 年内始终使用 HTTPS 访问
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    # 防止页面被嵌入 iframe（防止点击劫持）
    add_header X-Frame-Options "SAMEORIGIN" always;
    # 防止浏览器猜测 MIME 类型
    add_header X-Content-Type-Options "nosniff" always;
    # 启用 XSS 过滤
    add_header X-XSS-Protection "1; mode=block" always;

    # ---- 反向代理到后端 API ----
    resolver 127.0.0.11 valid=10s ipv6=off;  # Docker 内置 DNS
    set $backend_host "backend:8000";

    location /api/ {
        proxy_pass http://$backend_host;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;  # 传递 https 协议信息给后端
    }

    # ... 其余 location 块
}
```

**各配置项作用：**

| 配置项 | 值 | 作用 |
|--------|-----|------|
| `ssl_protocols` | TLSv1.2 TLSv1.3 | 禁用 TLS 1.0/1.1（已知不安全） |
| `ssl_ciphers` | ECDHE+AES-GCM | 仅允许前向保密的强加密套件 |
| `ssl_prefer_server_ciphers` | on | 服务端选择加密套件，防止客户端降级 |
| `ssl_session_cache` | shared:SSL:10m | 减少重复 TLS 握手，提升性能 |
| `Strict-Transport-Security` | max-age=31536000 | 浏览器 1 年内自动将 HTTP 升级为 HTTPS |
| `X-Forwarded-Proto` | $scheme | 后端可通过此头判断请求是否来自 HTTPS |

### 4.6 Docker 配置详解

#### docker-compose.yml 中的前端服务

```yaml
frontend:
  build:
    context: ./frontend
    dockerfile: Dockerfile
  container_name: agri-frontend
  ports:
    - "${FRONTEND_PORT:-80}:80"   # HTTP 端口映射
    - "443:443"                    # HTTPS 端口映射
  volumes:
    - ./ssl:/etc/nginx/ssl:ro      # 挂载 SSL 证书（只读模式）
  depends_on:
    - backend
  networks:
    - agri-network
  restart: unless-stopped
```

**关键配置说明：**

| 配置 | 说明 |
|------|------|
| `"443:443"` | 将宿主机 443 端口映射到容器 443 端口 |
| `./ssl:/etc/nginx/ssl:ro` | 将本地 `ssl/` 目录挂载到容器内 `/etc/nginx/ssl/`，`:ro` 表示只读 |

> **为什么用 volume 挂载而不是 COPY 到镜像？**
> 证书更换时只需替换 `ssl/` 目录中的文件并重启容器，无需重新构建镜像。

#### Dockerfile 中的变更

```dockerfile
# 暴露 HTTP 和 HTTPS 端口
EXPOSE 80 443

# 健康检查使用 HTTPS（因为 HTTP 会 301 跳转）
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD wget --no-check-certificate -qO /dev/null https://127.0.0.1/ || exit 1
```

> `--no-check-certificate` 是必要的，因为容器内部通过 `127.0.0.1` 访问，与证书域名 `shushang.online` 不匹配。

### 4.7 部署与验证

#### 步骤一：重建并启动前端容器

```bash
cd /home/ubuntu/mengzhi-cloud
docker compose up -d --build frontend
```

#### 步骤二：等待健康检查通过

```bash
# 等待约 30 秒后检查状态
docker compose ps

# 预期：agri-frontend 状态为 Up (healthy)
# 端口：0.0.0.0:80->80/tcp, 0.0.0.0:443->443/tcp
```

#### 步骤三：本地验证 HTTPS

```bash
# 测试 HTTPS 是否返回 200
curl -skI https://localhost
# 预期：HTTP/1.1 200 OK
# 预期包含：Strict-Transport-Security: max-age=31536000; includeSubDomains

# 测试 HTTP 是否 301 跳转到 HTTPS
curl -sI http://localhost
# 预期：HTTP/1.1 301 Moved Permanently
# 预期：Location: https://localhost/

# 测试 API 代理是否正常
curl -sk https://localhost/health
# 预期：返回后端健康检查 JSON
```

#### 步骤四：远程验证（需 DNS 已解析）

```bash
# 验证证书详情
openssl s_client -connect shushang.online:443 -servername shushang.online </dev/null 2>/dev/null | openssl x509 -noout -subject -issuer -dates

# 验证证书链完整性
openssl s_client -connect shushang.online:443 -servername shushang.online </dev/null 2>&1 | grep "Verify return code"
# 预期：Verify return code: 0 (ok)

# 测试 Nginx 配置语法
docker exec agri-frontend nginx -t
# 预期：nginx: the configuration file /etc/nginx/nginx.conf syntax is ok
```

#### 步骤五：浏览器验证

访问 `https://shushang.online`，确认：

- 地址栏显示锁图标（证书有效）
- 点击锁图标可查看证书信息
- 访问 `http://shushang.online` 自动跳转到 HTTPS

### 4.8 证书续期（更换证书）

当前证书有效期至 **2026-12-10**，到期前需更换。

#### 手动续期步骤

```bash
cd /home/ubuntu/mengzhi-cloud

# 1. 从证书提供商下载新证书（Nginx 格式），解压
unzip new_cert_nginx.zip -d /tmp/new_cert/

# 2. 备份旧证书
cp -r ssl/ ssl.bak.$(date +%Y%m%d)/

# 3. 替换证书文件
cp /tmp/new_cert/shushang.online_bundle.pem ssl/
cp /tmp/new_cert/shushang.online.key ssl/

# 4. 验证新证书
openssl x509 -in ssl/shushang.online_bundle.pem -noout -dates
# 确认 notAfter 为新的过期日期

# 5. 验证密钥匹配
openssl x509 -noout -modulus -in ssl/shushang.online_bundle.pem | openssl md5
openssl rsa -noout -modulus -in ssl/shushang.online.key | openssl md5
# 两个 MD5 必须一致

# 6. 重启前端容器（无需重新构建，volume 挂载会自动读取新文件）
docker compose restart frontend

# 7. 验证新证书生效
curl -svk https://localhost 2>&1 | grep "expire date"
```

> **注意**：由于证书是通过 volume 挂载的，替换文件后只需 `restart`，无需 `--build` 重新构建镜像。

#### Let's Encrypt 自动续期

如果使用 Let's Encrypt 证书，可设置 crontab 自动续期：

```bash
# 编辑 crontab
crontab -e

# 添加每月 1 号凌晨 3 点自动续期
0 3 1 * * cd /home/ubuntu/mengzhi-cloud && docker compose stop frontend && certbot renew --quiet && cp /etc/letsencrypt/live/shushang.online/fullchain.pem ssl/shushang.online_bundle.pem && cp /etc/letsencrypt/live/shushang.online/privkey.pem ssl/shushang.online.key && docker compose up -d frontend
```

### 4.9 SSL 故障排查

#### 问题一：浏览器提示"证书不受信任"

```bash
# 检查证书链是否完整
openssl s_client -connect shushang.online:443 -servername shushang.online </dev/null 2>&1 | grep -E "depth|verify"

# 如果显示 "unable to get local issuer certificate"，说明缺少中间证书
# 解决：确保使用 _bundle.pem（包含中间证书链），而非单独的域名证书
```

#### 问题二：Nginx 启动失败 "cannot load certificate"

```bash
# 查看错误日志
docker logs agri-frontend 2>&1 | tail -20

# 常见原因及解决：
# 1. 证书路径错误 → 检查 nginx.conf 中路径与 volume 挂载是否一致
# 2. 证书文件格式错误 → 确保是 PEM 格式（以 -----BEGIN CERTIFICATE----- 开头）
# 3. 私钥有密码保护 → Nginx 不支持加密私钥，需移除密码：
openssl rsa -in ssl/shushang.online.key -out ssl/shushang.online.key
```

#### 问题三：私钥与证书不匹配

```bash
# 比较 MD5，如果不同则不匹配
openssl x509 -noout -modulus -in ssl/shushang.online_bundle.pem | openssl md5
openssl rsa -noout -modulus -in ssl/shushang.online.key | openssl md5

# 解决：重新从证书提供商下载完整的证书包（key + pem 必须是同一次申请生成的）
```

#### 问题四：健康检查失败 (unhealthy)

```bash
# HTTP 80 端口已改为 301 跳转，健康检查必须使用 HTTPS
# 检查 Dockerfile 中健康检查命令是否正确：
# CMD wget --no-check-certificate -qO /dev/null https://127.0.0.1/ || exit 1

# 如果修改了 Dockerfile，需要重新构建：
docker compose up -d --build frontend
```

#### 问题五：证书即将过期检查

```bash
# 查看证书剩余天数
openssl x509 -in ssl/shushang.online_bundle.pem -noout -enddate
# 或远程检查
echo | openssl s_client -connect shushang.online:443 -servername shushang.online 2>/dev/null | openssl x509 -noout -enddate
```

### 4.10 涉及的文件变更汇总

本次 SSL 部署共修改/新增了以下文件：

| 文件 | 变更类型 | 变更内容 |
|------|----------|----------|
| `ssl/shushang.online_bundle.pem` | 新增 | SSL 证书 + 中间证书链 |
| `ssl/shushang.online.key` | 新增 | RSA 私钥 |
| `frontend/nginx.conf` | 修改 | 新增 HTTP→HTTPS 重定向 server 块；新增 443 SSL server 块，配置证书路径、TLS 协议、加密套件、安全头 |
| `frontend/Dockerfile` | 修改 | `EXPOSE 80` → `EXPOSE 80 443`；健康检查改为 `https://127.0.0.1/` |
| `docker-compose.yml` | 修改 | frontend 新增 `443:443` 端口映射；新增 `./ssl:/etc/nginx/ssl:ro` volume 挂载 |

---

## 五、启动部署

### 5.1 一键启动

```bash
# 方式一：使用启动脚本
bash start-docker.sh

# 方式二：手动启动
docker compose up -d --build
```

### 5.2 验证服务状态

```bash
# 查看容器状态（全部应为 healthy）
docker compose ps

# 预期输出：
# agri-mysql      Up (healthy)    0.0.0.0:3307->3306/tcp
# agri-redis      Up (healthy)    0.0.0.0:6380->6379/tcp
# agri-backend    Up (healthy)    0.0.0.0:8000->8000/tcp
# agri-frontend   Up (healthy)    0.0.0.0:80->80/tcp, 0.0.0.0:443->443/tcp
```

### 5.3 验证 HTTPS

```bash
# 测试 HTTPS 是否正常
curl -skI https://localhost

# 测试 HTTP 301 跳转
curl -sI http://localhost
# 应返回: HTTP/1.1 301 Moved Permanently, Location: https://...

# 测试后端 API 健康检查
curl -sk https://localhost/health
```

---

## 六、架构说明

```
                    ┌─────────────────────────────────────┐
                    │           Docker Network            │
                    │          (agri-network)             │
                    │                                     │
  用户浏览器        │  ┌──────────────┐                   │
  ──── :80 ────────►│  │              │  301 重定向       │
  ──── :443 ───────►│  │   Nginx      │                   │
                    │  │  (frontend)  │                   │
                    │  │              │                   │
                    │  │  静态文件     │                   │
                    │  │  /api/* ─────┼──► ┌───────────┐  │
                    │  └──────────────┘    │  FastAPI   │  │
                    │                      │ (backend)  │  │
                    │                      │  :8000     │  │
                    │                      └─────┬──┬──┘  │
                    │                            │  │     │
                    │                ┌───────────┘  └──┐  │
                    │                ▼                  ▼  │
                    │         ┌──────────┐      ┌───────┐ │
                    │         │  MySQL   │      │ Redis │ │
                    │         │  :3306   │      │ :6379 │ │
                    │         └──────────┘      └───────┘ │
                    └─────────────────────────────────────┘
```

**请求流程：**

1. 用户访问 `http://shushang.online` → Nginx 301 重定向到 HTTPS
2. 用户访问 `https://shushang.online` → Nginx 返回 Vue SPA 静态文件
3. 前端 JS 请求 `/api/*` → Nginx 反向代理到 `backend:8000`
4. 后端连接 MySQL (`mysql:3306`) 和 Redis (`redis:6379`)

---

## 七、数据持久化

| Docker Volume | 用途 | 说明 |
|---------------|------|------|
| `mysql_data` | MySQL 数据 | 数据库文件 |
| `redis_data` | Redis 数据 | AOF 持久化 |
| `backend_logs` | 后端日志 | 应用运行日志 |
| `backend_uploads` | 上传文件 | 用户上传的文件 |
| `./ssl` (bind mount) | SSL 证书 | 只读挂载到 Nginx 容器 |

数据库初始化脚本位于 `init/mysql/`，首次启动时自动执行：

- `01-init.sql` — 基础表结构
- `02-kefu.sql` — 客服模块数据

---

## 八、日常运维

### 查看日志

```bash
# 全部服务日志
docker compose logs -f

# 单个服务日志
docker compose logs -f frontend
docker compose logs -f backend
docker compose logs -f mysql
```

### 重启服务

```bash
# 重启全部
docker compose restart

# 重启单个服务
docker compose restart backend

# 重建并重启（代码有更新时）
docker compose up -d --build
```

### 停止服务

```bash
# 停止（保留数据卷）
docker compose down

# 停止并删除数据卷（危险！会丢失数据库数据）
docker compose down -v
```

### 更新部署

```bash
cd /home/ubuntu/mengzhi-cloud
git pull origin main
docker compose up -d --build
```

---

## 九、防火墙配置

确保服务器安全组/防火墙开放以下端口：

| 端口 | 协议 | 用途 | 是否必须 |
|------|------|------|----------|
| 80 | TCP | HTTP（自动跳转 HTTPS） | 是 |
| 443 | TCP | HTTPS | 是 |
| 22 | TCP | SSH 管理 | 是 |
| 8000 | TCP | 后端 API 直连 | 否（可关闭，通过 Nginx 代理访问） |
| 3307 | TCP | MySQL 外部访问 | 否（建议关闭） |
| 6380 | TCP | Redis 外部访问 | 否（建议关闭） |

**生产环境建议**：仅开放 80、443、22 端口，其余端口通过 Docker 内部网络通信。

---

## 十、DNS 配置

在域名服务商处添加 A 记录：

| 主机记录 | 类型 | 值 |
|----------|------|-----|
| `@` | A | `<服务器公网 IP>` |
| `www` | CNAME | `shushang.online` |

---

## 十一、故障排查

```bash
# 1. 容器未启动
docker compose ps
docker compose logs <服务名>

# 2. 后端持续重启
docker logs agri-backend --tail 50

# 3. Nginx 配置测试
docker exec agri-frontend nginx -t

# 4. 验证 SSL 证书
openssl s_client -connect shushang.online:443 -servername shushang.online </dev/null 2>/dev/null | openssl x509 -noout -dates

# 5. 检查端口占用
ss -tlnp | grep -E '80|443|8000|3307|6380'

# 6. MySQL 连接测试
docker exec agri-mysql mysql -u agri_user -p -e "SHOW DATABASES;"

# 7. Redis 连接测试
docker exec agri-redis redis-cli ping
```

---

## 十二、淘宝联盟 API 集成

### 12.1 API 版本说明

淘宝联盟 API 已从旧版迁移到升级版：

| 项目 | 旧版（已弃用） | 当前使用 |
|------|---------------|---------|
| 商品搜索 | `taobao.tbk.dg.item.search` | `taobao.tbk.dg.material.optional.upgrade` |
| 物料精选（降级） | `taobao.tbk.dg.optimus.material` | `taobao.tbk.dg.material.recommend` |
| API 网关 | `https://eco.taobao.com/router/rest` | `http://gw.api.taobao.com/router/rest` |

### 12.2 必需环境变量

在 `.env` 或 `.env.docker` 中配置：

```bash
TAOBAO_APP_KEY=<应用AppKey>
TAOBAO_APP_SECRET=<应用Secret>
TAOBAO_ADZONE_ID=<推广位ID，从PID最后一段获取>
TAOBAO_OAUTH_REDIRECT_URI=https://shushang.online/api/v1/taobao/oauth/callback
```

**获取推广位 ID**：登录 [pub.alimama.com](https://pub.alimama.com) → 推广管理 → 推广位管理 → 新建推广位。PID 格式为 `mm_xxx_xxx_yyyyyyy`，最后一段 `yyyyyyy` 即为 `TAOBAO_ADZONE_ID`。

### 12.3 OAuth 授权

搜索 API（`dg.*`）需要 OAuth Session 才能调用：

1. 在前端管理后台进入「淘宝联盟商品导入」页面
2. 点击「淘宝授权」按钮，在弹窗中完成授权
3. Session 自动存入数据库，有效期约 24 小时
4. 后端定时任务每 20 小时自动刷新 Session（使用 refresh_token）

### 12.4 权限申请

在 [aff-open.taobao.com](https://aff-open.taobao.com) 确保应用已获得以下 API 包权限：

- `16516` — 淘宝客【推广者】物料搜索
- `16518` — 淘宝客【推广者】物料精选
- `16189` — 淘宝客【公用】物料信息查询

---

## 十三、关键文件清单

```
mengzhi-cloud/
├── docker-compose.yml          # Docker 编排主文件
├── .env.docker                 # 环境变量（不提交到 Git）
├── .env.docker.example         # 环境变量模板
├── start-docker.sh             # 一键启动脚本
├── ssl/                        # SSL 证书目录
│   ├── shushang.online_bundle.pem
│   └── shushang.online.key
├── frontend/
│   ├── Dockerfile              # 前端多阶段构建
│   ├── nginx.conf              # Nginx 配置（含 SSL + 反向代理）
│   └── src/                    # Vue 源码
├── backend/
│   ├── Dockerfile              # 后端构建
│   ├── requirements.txt        # Python 依赖
│   └── app/                    # FastAPI 应用
└── init/mysql/                 # 数据库初始化脚本
    ├── 01-init.sql
    └── 02-kefu.sql
```
