# 蒙智云 MengZhi Cloud

> 内蒙古农畜产品 AI 赋能云平台 — 集成智能客服、用户画像蒸馏、RAG 知识库与全链路电商运营

[![Python](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/)
[![Vue](https://img.shields.io/badge/vue-3.4+-green.svg)](https://vuejs.org/)
[![FastAPI](https://img.shields.io/badge/fastapi-0.109-green.svg)](https://fastapi.tiangolo.com/)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

---

## 平台定位

蒙智云是面向内蒙古草原农畜产品产业的 **AI 赋能 SaaS 平台**，为牛羊肉、奶制品、藜麦、杂粮等特色农产品提供从品牌营销、智能客服到订单履约的一站式数字化解决方案。

**核心理念**：让 AI 真正深入业务——不是简单的问答机器人，而是能理解用户情绪、记住用户偏好、自主创建工单、个性化推荐产品的智能 Agent。

---

## 功能全景

```
┌─────────────────────────────────────────────────────────┐
│                      蒙 智 云                            │
├──────────┬──────────┬──────────┬──────────┬──────────────┤
│  AI 客服  │ 用户画像  │ 电商运营  │ 内容营销  │  管理后台    │
├──────────┼──────────┼──────────┼──────────┼──────────────┤
│ 意图分类  │ 5层Persona│ 产品管理  │ AI内容生成│  用户管理    │
│ 情绪识别  │ 对话蒸馏  │ 订单管理  │ 媒体生成  │  多租户      │
│ RAG知识库 │ 策略翻译  │ 配额计费  │ 提示词模板│  RBAC权限    │
│ 工单系统  │ 纠正机制  │ 京东导入  │ 文化标签  │  审计日志    │
│ 转人工    │ 增量Merge │ 对账管理  │ 产品溯源  │  风控/SLA    │
│ MCP工具   │ 评分体系  │ 支付回调  │          │  系统监控    │
└──────────┴──────────┴──────────┴──────────┴──────────────┘
```

### AI 智能客服

- **15 类意图识别**：产品咨询、价格查询、退款/退货/换货、物流追踪、投诉等
- **7 类情绪分析**：积极、中性、困惑、烦躁、愤怒、焦虑、悲伤
- **6 种路由策略**：问候 → RAG 检索 → 工具调用 → 工单创建 → 转人工 → LLM 兜底
- **RAG 知识库**：FAISS 向量检索 + MiniLM 多语言嵌入，覆盖产品、政策、物流、品牌等 7 大知识领域
- **MCP 工具**：7 个 LangChain @tool，支持主平台 Agent 发现和调用
- **情绪安抚**：高负面情绪自动注入安抚前缀，超阈值自动转人工

### 5 层用户画像（Persona 蒸馏模型）

借鉴蒸馏 Skill 的分层结构与"记忆自然流露"原则：

| 层级 | 名称 | 数据来源 |
|------|------|---------|
| Layer 0 | 身份锚定 | 注册信息、会员天数、用户类型 |
| Layer 1 | 购买风格 | 订单模式、偏好品类、消费水平、活跃度 |
| Layer 2 | 沟通偏好 | 消息长度、活跃时段、话题分布、表达风格 |
| Layer 3 | 情绪模式 | 情绪分布、升级倾向、负面比例 |
| Layer 4 | 服务历史 | 工单模式、解决率、满意度 |

- **综合评分**（0-100）→ 高价值 / 活跃 / 潜力 / 普通 四级用户
- **策略翻译**：标签自动映射为客服话术规则（语气、推荐策略、情绪应对）
- **Session Summary**：每 5 条消息自动蒸馏对话摘要，增量 merge 到用户档案
- **Correction 纠正**：用户可反馈意图/情绪/回答错误，持续优化画像精度

### 电商与运营

- 产品管理（支持京东 API 批量导入）
- 订单全生命周期管理
- 配额计费 & 套餐包
- 多租户隔离（企业级 SaaS）
- RBAC 细粒度权限控制
- 审计日志 & 风控 & SLA 监控

---

## 技术架构

```
                    ┌──────────────┐
                    │   Nginx/CDN  │
                    └──────┬───────┘
                           │
              ┌────────────┴────────────┐
              │                         │
     ┌────────▼────────┐    ┌──────────▼──────────┐
     │   Vue 3 前端     │    │   FastAPI 后端       │
     │ Element Plus     │    │ SQLAlchemy + Alembic │
     │ Pinia + Router   │    │ LangChain + DeepSeek │
     │ ECharts          │    │ FAISS RAG            │
     │ TypeScript       │    │ Prometheus           │
     └─────────────────┘    └───┬─────────┬────────┘
                                │         │
                        ┌───────▼──┐  ┌───▼────┐
                        │ MySQL 8  │  │ Redis 7│
                        └──────────┘  └────────┘
```

### 技术栈

| 层级 | 技术 |
|------|------|
| **前端** | Vue 3.4 · TypeScript 5 · Element Plus 2.5 · Vite 5 · Pinia · ECharts 6 |
| **后端** | FastAPI 0.109 · SQLAlchemy 2.0 · Pydantic · Uvicorn |
| **AI/ML** | LangChain · DeepSeek API · FAISS · sentence-transformers · scikit-learn |
| **数据** | MySQL 8.0 · Redis 7 · Alembic |
| **部署** | Docker Compose · Nginx |
| **监控** | Prometheus · Loguru · APScheduler |

---

## 快速开始

### 环境要求

- Docker & Docker Compose
- （可选）DeepSeek API Key — 用于 LLM 智能回答
- （可选）京东开放平台 API Key — 用于商品导入

### 一键启动

```bash
# 克隆项目
git clone https://github.com/your-org/mengzhi-cloud.git
cd mengzhi-cloud

# 配置环境变量（可选）
cp .env.docker .env
# 编辑 .env，填入 DEEPSEEK_API_KEY 等

# 启动所有服务
docker compose -f docker-compose.dev.yml up -d

# 等待服务就绪（约 30 秒）
# 前端:  http://localhost:5173
# 后端:  http://localhost:8001
# 文档:  http://localhost:8001/docs
# 默认管理员: admin / admin123
```

### 本地开发

```bash
# 后端
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000

# 前端
cd frontend
pnpm install
pnpm dev
```

---

## 客服 Agent 处理流程

```
用户消息
  │
  ├─→ 加载用户画像 (5层 Persona → 策略注入 system prompt)
  │
  ├─→ 意图分类 + 情绪识别 (规则优先 → LLM 兜底)
  │
  ├─→ 路由分发
  │     ├── 问候 ──────→ 随机欢迎语
  │     ├── RAG 查询 ──→ FAISS 检索 → LLM 生成回答
  │     ├── 工具调用 ──→ 查订单/查产品/查物流
  │     ├── 创建工单 ──→ 自动归类 + 优先级判定
  │     ├── 转人工 ────→ 创建高优工单 + 通知
  │     └── LLM 兜底 ──→ DeepSeek 生成回答
  │
  ├─→ 情绪安抚前缀注入 (愤怒/焦虑/困惑 → 共情话术)
  │
  ├─→ 保存对话历史
  │
  └─→ 每 5 条消息 → 自动蒸馏 Session Summary → 增量 Merge
```

---

## 项目结构

```
mengzhi-cloud/
├── backend/
│   ├── app/
│   │   ├── api/                # API 路由（25+ 模块）
│   │   │   ├── auth.py         #   认证登录
│   │   │   ├── kefu.py         #   智能客服
│   │   │   ├── products.py     #   产品管理
│   │   │   ├── orders.py       #   订单管理
│   │   │   └── ...
│   │   ├── core/               # 核心配置
│   │   │   ├── config.py       #   应用配置
│   │   │   ├── database.py     #   数据库连接
│   │   │   └── redis_client.py
│   │   ├── models/             # ORM 模型（33 个）
│   │   ├── services/           # 业务服务层
│   │   │   ├── kefu_agent.py          # 客服 Agent 编排
│   │   │   ├── kefu_classifier.py     # 意图/情绪分类器
│   │   │   ├── kefu_rag.py            # RAG 知识库
│   │   │   ├── user_profile_service.py    # 5 层用户画像
│   │   │   └── ...
│   │   └── data/kefu_kb/       # 知识库文档（7 篇）
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── api/                # API 客户端
│   │   ├── views/              # 页面组件
│   │   │   ├── kefu/           #   客服聊天 & 工单
│   │   │   ├── admin/          #   管理后台
│   │   │   └── user/           #   用户中心
│   │   ├── stores/             # Pinia 状态管理
│   │   ├── router/             # 路由配置
│   │   └── components/         # 公共组件
│   ├── package.json
│   └── vite.config.ts
├── deploy/docker/              # 部署配置
│   ├── docker-compose.yml
│   └── init/mysql/             # 数据库初始化脚本
├── docker-compose.dev.yml      # 开发环境
└── README.md
```

---

## API 概览

| 模块 | 端点前缀 | 说明 |
|------|---------|------|
| 认证 | `/api/v1/auth` | 登录、注册、JWT 刷新、登出 |
| 客服 | `/api/v1/kefu` | 聊天、会话、工单、蒸馏、画像、纠正 |
| 产品 | `/api/v1/products` | 产品 CRUD、搜索 |
| 订单 | `/api/v1/orders` | 订单管理 |
| 配额 | `/api/v1/quotas` | 使用量统计、套餐包 |
| 计费 | `/api/v1/billing` | 账单、发票 |
| 内容 | `/api/v1/content-generation` | AI 内容生成 |
| 管理 | `/api/admin` | 用户管理、统计、AI 配额 |
| 审计 | `/api/v1/audit-logs` | 操作日志查询、导出 |

完整 API 文档访问：`http://localhost:8001/docs`（Swagger UI）

---

## 环境变量

| 变量 | 必填 | 说明 |
|------|------|------|
| `DATABASE_URL` | 是 | MySQL 连接串 |
| `REDIS_HOST` | 是 | Redis 主机地址 |
| `SECRET_KEY` | 是 | JWT 签名密钥（生产环境必须修改） |
| `DEEPSEEK_API_KEY` | 否 | DeepSeek API 密钥（LLM 智能回答） |
| `DEEPSEEK_API_BASE` | 否 | DeepSeek API 地址，默认 `https://api.deepseek.com` |
| `JD_APP_KEY` | 否 | 京东开放平台 AppKey（商品导入） |
| `JD_SECRET_KEY` | 否 | 京东开放平台 Secret |

---

## 数据库

平台共包含 **33+ 张数据表**，核心表如下：

| 分组 | 表名 | 说明 |
|------|------|------|
| 用户 | `users`, `roles`, `permissions` | 用户体系 + RBAC |
| 产品 | `products`, `cultural_tags` | 产品与文化标签 |
| 订单 | `orders`, `payments`, `billing_records` | 交易链路 |
| AI | `conversations`, `messages`, `content_records` | AI 对话与内容 |
| 客服 | `kefu_conversations`, `kefu_messages`, `kefu_tickets` | 客服系统 |
| 配额 | `user_quotas`, `quota_packages`, `quota_logs` | 用量计费 |
| 运维 | `audit_logs`, `system_configs` | 审计与配置 |

---

## 安全特性

- JWT 认证 + Token 黑名单（Redis）
- bcrypt 密码加密
- SQL 注入防护（SQLAlchemy 参数化查询）
- CORS 白名单
- 操作审计日志
- 细粒度 RBAC 权限控制

---

## 致谢

- [SKILL-kefu](https://github.com/liangdabiao/SKILL-kefu) — 智能客服系统参考架构
- [yourself-skill](https://github.com/notdog1998/yourself-skill) — 5 层 Persona 分层模型 & 标签翻译表
- [ex-skill](https://github.com/therealXiaomanChu/ex-skill) — Session Summary 蒸馏 & 增量 Merge & Correction 机制
- [DeepSeek](https://www.deepseek.com) — 大语言模型 API
- [LangChain](https://langchain.com) — AI Agent 工具链

---

## 许可证

MIT License
