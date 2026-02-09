# 本地开发部署

本文档介绍如何在本地搭建开发环境。

## 前置条件

确保已安装：
- Python 3.11+
- Node.js 20+
- MySQL 8.0+
- Redis 7+

详见[环境要求](./requirements.md)。

## 1. 克隆项目

```bash
git clone <repository-url>
cd AI赋能云平台
```

## 2. 数据库准备

### 启动MySQL

```bash
# Linux/macOS
sudo systemctl start mysql
# 或
sudo service mysql start

# macOS (Homebrew)
brew services start mysql

# Windows
# 从服务管理器启动MySQL服务
```

### 创建数据库

```bash
mysql -u root -p
```

```sql
-- 创建数据库
CREATE DATABASE agri_platform CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- 创建用户（可选，推荐）
CREATE USER 'agri_user'@'localhost' IDENTIFIED BY 'your_password';
GRANT ALL PRIVILEGES ON agri_platform.* TO 'agri_user'@'localhost';
FLUSH PRIVILEGES;

-- 退出
EXIT;
```

## 3. Redis准备

### 启动Redis

```bash
# Linux
sudo systemctl start redis
# 或
sudo service redis-server start

# macOS
brew services start redis

# Windows (WSL2)
sudo service redis-server start
```

### 验证Redis

```bash
redis-cli ping
# 应返回: PONG
```

## 4. 后端部署

### 进入后端目录

```bash
cd backend
```

### 创建虚拟环境

```bash
# Linux/macOS
python3 -m venv venv
source venv/bin/activate

# Windows
python -m venv venv
venv\Scripts\activate
```

### 安装依赖

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### 配置环境变量

```bash
# 复制环境变量模板
cp .env.example .env

# 编辑 .env 文件
nano .env  # 或使用其他编辑器
```

关键配置项：
```bash
# 数据库连接
DATABASE_URL=mysql+pymysql://root:root123@localhost:3306/agri_platform?charset=utf8mb4

# Redis连接
REDIS_URL=redis://localhost:6379/0

# JWT密钥（必须修改）
SECRET_KEY=your-secret-key-at-least-32-characters-long

# DeepSeek API
DEEPSEEK_API_KEY=your-deepseek-api-key-here
```

详见[环境变量配置](./environment-variables.md)。

### 数据库迁移

```bash
# 初始化数据库（首次运行）
alembic upgrade head

# 如果需要创建新迁移
alembic revision --autogenerate -m "描述"
alembic upgrade head
```

详见[数据库迁移](./database-migration.md)。

### 启动后端服务

```bash
# 开发模式（热重载）
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# 或使用简化命令
python -m uvicorn app.main:app --reload
```

### 验证后端

访问以下URL：
- API文档: http://localhost:8000/docs
- 健康检查: http://localhost:8000/health
- OpenAPI规范: http://localhost:8000/openapi.json

## 5. 前端部署

### 打开新终端，进入前端目录

```bash
cd frontend
```

### 安装依赖

```bash
npm install
# 或使用 yarn
yarn install
```

### 配置环境变量

```bash
# 复制环境变量模板
cp .env.example .env.development

# 编辑 .env.development
nano .env.development
```

配置内容：
```bash
# API基础URL（开发环境使用代理）
VITE_API_BASE_URL=/api

# 应用配置
VITE_APP_TITLE=内蒙古农畜产品AI平台
VITE_ENABLE_DEBUG=true
```

### 启动前端服务

```bash
npm run dev
```

### 验证前端

访问: http://localhost:5173

## 6. 验证完整系统

### 测试API连接

在浏览器中打开前端，尝试：
1. 注册新用户
2. 登录系统
3. 访问各个功能模块

### 测试AI功能

1. 进入"内容生成"模块
2. 输入产品信息
3. 生成营销文案
4. 验证DeepSeek API是否正常工作

## 7. 开发工具

### 后端开发

```bash
# 运行测试
cd backend
pytest

# 代码格式化
black app/
isort app/

# 类型检查
mypy app/
```

### 前端开发

```bash
# 运行测试
npm run test

# 类型检查
npm run build  # 会执行 vue-tsc

# 代码检查
npm run lint
```

## 8. 常见开发任务

### 添加新的API端点

1. 在 `backend/app/api/` 创建路由文件
2. 在 `backend/app/models/` 定义数据模型
3. 在 `backend/app/schemas/` 定义Pydantic模型
4. 在 `backend/app/main.py` 注册路由

### 添加新的前端页面

1. 在 `frontend/src/views/` 创建页面组件
2. 在 `frontend/src/router/index.ts` 添加路由
3. 在 `frontend/src/api/` 添加API调用
4. 更新导航菜单

### 数据库Schema变更

```bash
cd backend

# 1. 修改 app/models/ 中的模型
# 2. 生成迁移文件
alembic revision --autogenerate -m "描述变更"

# 3. 检查生成的迁移文件
# 4. 应用迁移
alembic upgrade head

# 5. 如需回滚
alembic downgrade -1
```

## 9. 调试技巧

### 后端调试

```python
# 在代码中添加断点
import pdb; pdb.set_trace()

# 或使用 loguru
from loguru import logger
logger.debug("调试信息")
```

### 前端调试

```javascript
// 使用 Vue DevTools
// Chrome扩展: Vue.js devtools

// 控制台调试
console.log('调试信息')
debugger  // 断点
```

### 数据库调试

```bash
# 查看SQL日志
# 在 .env 中设置
DEBUG=True

# 直接连接数据库
mysql -u root -p agri_platform
```

## 10. 停止服务

```bash
# 停止后端: Ctrl+C

# 停止前端: Ctrl+C

# 停止MySQL
sudo systemctl stop mysql

# 停止Redis
sudo systemctl stop redis
```

## 故障排查

遇到问题？查看[故障排查文档](./troubleshooting.md)。

## 下一步

- [Docker部署](./docker-deployment.md) - 使用容器化部署
- [生产环境部署](./production-deployment.md) - 生产环境配置
