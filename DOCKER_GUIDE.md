# Docker环境快速启动指南

## 前置要求

- Docker Desktop 已安装并运行
- 至少 4GB 可用内存
- 至少 10GB 可用磁盘空间

## 快速启动

### 1. 启动开发环境

```bash
# 启动所有服务
docker-compose -f docker-compose.dev.yml up -d

# 查看服务状态
docker-compose -f docker-compose.dev.yml ps

# 查看日志
docker-compose -f docker-compose.dev.yml logs -f
```

### 2. 访问服务

- 前端: http://localhost:5173
- 后端API: http://localhost:8000
- API文档: http://localhost:8000/docs
- MySQL: localhost:3306
- Redis: localhost:6379

### 3. 在容器中运行检查

```bash
# 前端检查
docker-compose -f docker-compose.dev.yml exec frontend sh -c "
  npm run lint &&
  npm run build &&
  npm run test
"

# 后端检查
docker-compose -f docker-compose.dev.yml exec backend sh -c "
  pytest &&
  flake8 app/ &&
  mypy app/
"
```

### 4. 停止服务

```bash
# 停止所有服务
docker-compose -f docker-compose.dev.yml down

# 停止并删除数据卷
docker-compose -f docker-compose.dev.yml down -v
```

## 生产环境部署

```bash
# 构建生产镜像
docker-compose -f docker-compose.yml build

# 启动生产环境
docker-compose -f docker-compose.yml up -d
```

## 常用命令

```bash
# 重启单个服务
docker-compose -f docker-compose.dev.yml restart backend

# 进入容器
docker-compose -f docker-compose.dev.yml exec backend bash
docker-compose -f docker-compose.dev.yml exec frontend sh

# 查看资源使用
docker stats

# 清理未使用的镜像
docker system prune -a
```

## 故障排查

### 端口冲突
如果端口被占用，修改 docker-compose.dev.yml 中的端口映射。

### 数据库连接失败
等待 MySQL 完全启动（约30秒），或查看日志：
```bash
docker-compose -f docker-compose.dev.yml logs mysql
```

### 前端热重载不工作
确保 volumes 配置正确，node_modules 已正确挂载。
