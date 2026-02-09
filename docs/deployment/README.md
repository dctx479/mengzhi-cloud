# 部署文档

内蒙古农畜产品AI平台完整部署指南。

## 文档目录

- [环境要求](./requirements.md) - 系统和软件版本要求
- [本地开发部署](./local-development.md) - 开发环境搭建
- [Docker部署](./docker-deployment.md) - 使用Docker Compose部署
- [生产环境部署](./production-deployment.md) - 生产环境配置和优化
- [环境变量配置](./environment-variables.md) - 所有环境变量说明
- [数据库迁移](./database-migration.md) - Alembic迁移指南
- [故障排查](./troubleshooting.md) - 常见问题和解决方案

## 快速开始

### Docker部署（推荐）

```bash
# 克隆项目
git clone <repository-url>
cd AI赋能云平台

# 启动所有服务
cd deploy/docker
docker-compose up -d

# 访问应用
# 前端: http://localhost
# 后端API: http://localhost:8000
# API文档: http://localhost:8000/docs
```

### 本地开发

```bash
# 后端
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload

# 前端
cd frontend
npm install
npm run dev
```

## 系统架构

```
┌─────────────┐
│   Nginx     │ (前端静态文件 + 反向代理)
│   Port 80   │
└──────┬──────┘
       │
       ├─────────────────┐
       │                 │
┌──────▼──────┐   ┌──────▼──────┐
│   Frontend  │   │   Backend   │
│  Vue 3 SPA  │   │   FastAPI   │
│  Port 5173  │   │  Port 8000  │
└─────────────┘   └──────┬──────┘
                         │
                  ┌──────┴──────┐
                  │             │
           ┌──────▼──────┐ ┌───▼────┐
           │    MySQL    │ │ Redis  │
           │  Port 3306  │ │  6379  │
           └─────────────┘ └────────┘
```

## 技术栈

**后端**
- Python 3.11+
- FastAPI 0.109.0
- SQLAlchemy 2.0.25
- MySQL 8.0
- Redis 7

**前端**
- Node.js 20+
- Vue 3.4
- TypeScript 5.3
- Vite 5.0
- Element Plus 2.5

## 支持

如遇问题，请查看[故障排查文档](./troubleshooting.md)或提交Issue。
