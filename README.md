# 内蒙古农畜产品品牌营销AI赋能云平台

> 基于AI技术的农畜产品品牌营销智能化平台，助力内蒙古特色农畜产品走向全国

[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/)
[![Vue](https://img.shields.io/badge/vue-3.4+-green.svg)](https://vuejs.org/)
[![FastAPI](https://img.shields.io/badge/fastapi-0.109-green.svg)](https://fastapi.tiangolo.com/)

---

## 📖 项目简介

本平台是一个面向内蒙古农畜产品的AI赋能营销云平台，通过人工智能技术帮助企业和个人：

- 🤖 **AI智能对话** - 基于DeepSeek的智能客服和产品咨询
- 📝 **内容智能生成** - 自动生成营销文案、产品描述、推广方案
- 🔍 **产品智能检索** - RAG技术支持的语义搜索和推荐
- 📊 **数据分析洞察** - 产品数据分析和市场趋势预测
- 🎨 **多平台适配** - 支持小红书、抖音、微信等多平台内容生成

---

## ✨ 核心功能

### 1. AI智能对话系统
- 多Agent对话支持（助手、营销专家、文化顾问）
- 流式响应，实时交互
- 对话历史管理和导出
- 文件上传和多模态对话

### 2. 产品管理系统
- 产品CRUD和批量操作
- 高级搜索和筛选
- 产品分类和标签管理
- 文化标签和故事关联

### 3. 内容生成工作室
- 多种内容类型（文案、视频脚本、直播脚本）
- 多平台风格适配
- 批量生成和任务管理
- 内容优化和质量评估

### 4. 用户中心
- 个人信息管理
- 配额和订单管理
- 安全设置（密码、手机、邮箱）
- 操作历史和审计日志

### 5. 权限管理系统
- RBAC角色权限控制
- 细粒度资源权限
- 操作审计和日志追踪

---

## 🛠️ 技术栈

### 后端技术
- **框架**: FastAPI 0.109 (异步高性能)
- **数据库**: MySQL 8.0 + SQLAlchemy 2.0
- **缓存**: Redis 5.0
- **AI集成**: DeepSeek API + sentence-transformers
- **向量检索**: FAISS 1.7
- **认证**: JWT (python-jose)
- **任务队列**: Celery (可选)

### 前端技术
- **框架**: Vue 3.4 (Composition API)
- **构建工具**: Vite 5.0
- **UI组件**: Element Plus 2.5
- **状态管理**: Pinia 2.1
- **路由**: Vue Router 4.2
- **HTTP客户端**: Axios 1.6
- **类型检查**: TypeScript 5.3

### 基础设施
- **容器化**: Docker + Docker Compose
- **Web服务器**: Nginx
- **应用服务器**: Uvicorn (ASGI)
- **数据库迁移**: Alembic

---

## 🚀 快速开始

### 前置要求

- Python 3.9+
- Node.js 18+
- MySQL 8.0+
- Redis 5.0+
- Docker (可选)

### 方式一：Docker部署（推荐）

```bash
# 1. 克隆项目
git clone <repository-url>
cd AI赋能云平台

# 2. 配置环境变量
cp backend/.env.example backend/.env
# 编辑 backend/.env，配置数据库和API密钥

# 3. 启动服务
cd deploy/docker
docker-compose up -d

# 4. 访问应用
# 前端: http://localhost
# 后端API: http://localhost/api
# API文档: http://localhost/api/docs
```

### 方式二：本地开发

**后端启动**:
```bash
cd backend

# 安装依赖
pip install -r requirements.txt

# 配置环境变量
cp .env.example .env
# 编辑 .env 文件

# 数据库迁移
alembic upgrade head

# 启动服务
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**前端启动**:
```bash
cd frontend

# 安装依赖
npm install

# 配置环境变量
cp .env.example .env
# 编辑 .env 文件

# 启动开发服务器
npm run dev
```

访问 http://localhost:5173

---

## 📁 项目结构

```
AI赋能云平台/
├── backend/                 # 后端应用
│   ├── app/
│   │   ├── api/            # API路由层 (13个模块)
│   │   ├── services/       # 业务逻辑层 (16个服务)
│   │   ├── models/         # 数据模型层 (16个模型)
│   │   ├── schemas/        # 数据验证层
│   │   ├── core/           # 核心配置和工具
│   │   └── utils.py        # 工具函数
│   ├── tests/              # 测试
│   ├── alembic/            # 数据库迁移
│   └── requirements.txt    # Python依赖
│
├── frontend/               # 前端应用
│   ├── src/
│   │   ├── api/           # API客户端 (9个模块)
│   │   ├── components/    # Vue组件 (35+个)
│   │   ├── views/         # 页面组件 (8+个)
│   │   ├── stores/        # Pinia状态管理 (5个)
│   │   ├── router/        # 路由配置
│   │   ├── types/         # TypeScript类型
│   │   └── utils/         # 工具函数
│   ├── tests/             # 测试
│   └── package.json       # Node依赖
│
├── deploy/                # 部署配置
│   ├── docker/           # Docker配置
│   └── nginx/            # Nginx配置
│
├── docs/                  # 文档
│   ├── api/              # API文档
│   ├── deployment/       # 部署文档
│   └── testing/          # 测试文档
│
└── data/                  # 数据文件
    ├── products/         # 产品数据
    └── cultural/         # 文化数据
```

---

## 📚 文档

- [API文档](docs/api/00-overview.md) - 完整的API接口文档
- [部署指南](docs/deployment/DEPLOYMENT.md) - 部署和运维指南
- [开发指南](docs/development/DEVELOPMENT.md) - 开发规范和最佳实践
- [测试报告](docs/testing/TEST_REPORT.md) - 测试覆盖和质量报告

---

## 🔧 开发指南

### 代码规范

- **Python**: PEP 8 + Black格式化
- **TypeScript**: ESLint + Prettier
- **提交信息**: Conventional Commits

### 测试

```bash
# 后端测试
cd backend
pytest tests/ -v --cov=app

# 前端测试
cd frontend
npm run test
npm run test:e2e
```

### 数据库迁移

```bash
# 创建迁移
alembic revision --autogenerate -m "描述"

# 执行迁移
alembic upgrade head

# 回滚迁移
alembic downgrade -1
```

---

## 🌟 核心特性

### 性能优化
- ✅ 数据库连接池 (20个连接)
- ✅ Redis缓存 (80%+命中率)
- ✅ N+1查询优化
- ✅ 虚拟滚动列表
- ✅ 图片懒加载和压缩

### 安全特性
- ✅ JWT认证和Token黑名单
- ✅ 密码加密 (bcrypt)
- ✅ CORS白名单
- ✅ SQL注入防护
- ✅ XSS防护
- ✅ 操作审计日志

### 可扩展性
- ✅ 微服务架构设计
- ✅ 可插拔的存储后端 (本地/OSS)
- ✅ 可配置的AI服务商
- ✅ 多租户支持 (预留)

---

## 📊 项目状态

### 当前版本: v1.0.0

- ✅ 核心功能完整实现
- ✅ API可用率 100%
- ✅ 代码质量评分 90/100
- ⚠️ 测试覆盖率 37% (目标80%)
- ⚠️ 文档完整度 80%

### 近期更新 (2026-01-21)

- ✅ 修复P0阻塞问题 (3个)
- ✅ 完善后端核心模块 (10个)
- ✅ 提升代码质量和性能 (15个优化)
- ✅ 补充邮件和短信服务
- ✅ 生成完整API文档

---

## 🤝 贡献指南

欢迎贡献代码、报告问题或提出建议！

1. Fork本仓库
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启Pull Request

---

## 📄 许可证

本项目采用 MIT 许可证 - 详见 [LICENSE](LICENSE) 文件

---

## 👥 团队

- **项目负责人**: [姓名]
- **后端开发**: [团队成员]
- **前端开发**: [团队成员]
- **产品设计**: [团队成员]

---

## 📞 联系我们

- **项目主页**: [项目网站]
- **问题反馈**: [GitHub Issues]
- **邮箱**: [联系邮箱]
- **微信**: [微信号]

---

**⭐ 如果这个项目对你有帮助，请给我们一个Star！**
