# 蒙智云 MengZhi Cloud

> 内蒙古农畜产品 AI 赋能云平台 — 集成智能客服、用户画像蒸馏、RAG 知识库与全链路电商运营

[![Python](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/)
[![Vue](https://img.shields.io/badge/vue-3.4+-green.svg)](https://vuejs.org/)
[![FastAPI](https://img.shields.io/badge/fastapi-0.109-green.svg)](https://fastapi.tiangolo.com/)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

---

## 平台定位

蒙智云是面向内蒙古草原农畜产品产业的 **AI 赋能 SaaS 平台**，为牛羊肉、奶制品、藜麦、杂粮等特色农产品提供从品牌营销、智能客服到订单履约的一站式数字化解决方案。

**核心理念**：让 AI 真正深入业务——不是简单的问答机器人，而是能理解用户情绪、记住用户偏好、自主创建工单、个性化推荐产品的智能 Agent。

**创新亮点**：
- 🎭 **双IP智能体**：小数（文化传承者）+ 小商（营销顾问），草原文化特色AI代言人
- 🌐 **知识图谱赋能**：630节点文化知识图谱，产品-文化深度关联
- 🎨 **内容生成工具链**：品牌故事（3种风格）+ 直播脚本 + 批量生成 + 多媒体AI
- 📊 **5层用户画像**：从身份锚定到服务历史，全方位用户理解

---

## 功能全景

```
┌───────────────────────────────────────────────────────────────────┐
│                           蒙 智 云                                 │
├──────────┬──────────┬──────────┬──────────┬──────────┬──────────┤
│  AI客服   │ 双IP智能体│ 用户画像  │ 电商运营  │ 内容营销  │ 管理后台 │
├──────────┼──────────┼──────────┼──────────┼──────────┼──────────┤
│ 意图分类  │ 小数IP   │ 5层画像  │ 产品管理  │批量生成  │用户管理  │
│ 情绪识别  │ 小商IP   │ 对话蒸馏 │ 订单管理  │品牌故事  │多租户    │
│RAG知识库 │ 智能路由 │ 策略翻译 │ 配额计费  │直播脚本  │RBAC权限  │
│ 工单系统  │文化融入  │ 纠正机制 │ 京东导入  │多媒体AI  │审计日志  │
│ 转人工    │人格一致  │增量Merge │ 淘宝导入  │文化溯源  │风控/SLA  │
│ MCP工具   │场景适配  │ 评分体系 │ 对账管理  │平台适配  │系统监控  │
│          │          │          │ 支付回调  │          │          │
└──────────┴──────────┴──────────┴──────────┴──────────┴──────────┘
```

### AI 智能客服

- **15 类意图识别**：产品咨询、价格查询、退款/退货/换货、物流追踪、投诉等
- **7 类情绪分析**：积极、中性、困惑、烦躁、愤怒、焦虑、悲伤
- **6 种路由策略**：问候 → RAG 检索 → 工具调用 → 工单创建 → 转人工 → LLM 兜底
- **RAG 知识库**：FAISS 向量检索 + MiniLM 多语言嵌入，覆盖产品、政策、物流、品牌等 7 大知识领域
- **MCP 工具**：7 个 LangChain @tool，支持主平台 Agent 发现和调用
- **情绪安抚**：高负面情绪自动注入安抚前缀，超阈值自动转人工

### 🎭 双IP智能体系统（✨ 核心创新）

**小数 & 小商** — 草原文化特色AI代言人，行业首创文化IP + 营销顾问双智能体协同模式

| IP | 角色定位 | 核心能力 | 文化融入 |
|-----|---------|---------|---------|
| **小数** | 草原文化传承者 | 文化溯源、产地故事、传统工艺讲解 | 蒙古族谚语、草原生活场景、文化元素关联 |
| **小商** | 品牌营销顾问 | 品牌故事生成、直播脚本、营销策略 | 文化差异化卖点、情感共鸣、现代营销语言 |

**技术架构**:
- **智能路由**：基于对话意图自动选择最合适的IP角色
- **人格一致性**：Few-shot Prompt + 文化背景注入，确保对话风格稳定
- **文化知识图谱**：66个文化元素 + 630节点知识图谱，智能匹配产品关联
- **场景适配**：支持产品咨询、品牌营销、文化传播等多种对话场景

📖 **详细文档**:
- [双IP智能体架构设计](docs/technical/IP-AGENT-ARCHITECTURE.md)
- [快速开始指南](docs/technical/IP-AGENT-QUICKSTART.md)
- [实施总结](backend/app/services/ip_agent/README.md)

### 5 层用户画像（Persona 蒸馏模型）

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

- 产品管理（支持京东联盟、淘宝联盟 API 批量导入）
- 订单全生命周期管理
- 配额计费 & 套餐包
- 多租户隔离（企业级 SaaS）
- RBAC 细粒度权限控制
- 审计日志 & 风控 & SLA 监控
- 对账系统 & 定时任务调度

### 🎨 内容营销工具链（✨ 核心创新）

#### 1. 文化元素智能匹配系统
- **知识图谱**：630节点（66个文化元素 + 29个地区 + 335个关键词）
- **智能评分**：多层次评分模型（地域匹配40% + 知识图谱20%）
- **自动采集**：产品创建/更新时自动触发文化元素采集
- **专家审核**：4级审核流程（待审核 → 通过 → 拒绝 → 需补充）

📖 **详细文档**: [文化元素系统集成报告](backend/docs/CULTURAL-SYSTEM-INTEGRATION-REPORT.md)

#### 2. 品牌故事生成器
- **3种风格**：现代简约（200-300字）/ 传统深沉（400-600字）/ 情感共鸣（300-400字）
- **文化融入**：自动匹配文化元素，自然融入故事叙事
- **自动配图**：集成即梦AI，生成品牌视觉素材
- **一键导出**：支持文本/图片/视频多种格式

📖 **详细文档**: [品牌故事生成器集成报告](backend/docs/BRAND-STORY-INTEGRATION-REPORT.md)

#### 3. 直播脚本生成器
- **3种场景**：产品展示 / 促销活动 / 品牌故事
- **结构化输出**：开场白 → 产品介绍 → 互动环节 → 促销话术 → 结束语
- **文化特色**：融入草原文化元素，增强地域特色

#### 4. 批量内容生成系统
- **批量任务**：一次创建，批量生成多个产品的内容
- **并行执行**：Semaphore(10) 并发控制，10x提速
- **进度追踪**：实时进度更新，支持取消/重试
- **流式导出**：TXT/DOCX/PDF 多格式导出，真流式 StreamingResponse
- **健壮性**：心跳超时检测，自动清理僵尸任务

📖 **详细文档**: [批量内容生成系统](backend/docs/BE-008-多模态素材管理系统.md)

#### 5. 多媒体 Provider 抽象
- **即梦AI**：文生图、图生图，支持多种艺术风格
- **火山引擎**：视频生成、语音合成（预留接口）
- **统一接口**：Provider 抽象层，轻松扩展新的AI服务

📖 **详细文档**: [即梦AI集成报告](backend/docs/JIMENG-INTEGRATION-REPORT.md) / [火山引擎集成报告](backend/docs/VOLCENGINE-INTEGRATION-REPORT.md)

### 第三方平台集成

| 平台 | 功能 | 授权方式 |
|------|------|---------|
| **京东联盟** | 商品搜索、批量导入、佣金追踪 | OAuth2 授权码 |
| **淘宝联盟** | 商品搜索、批量导入、推广位管理 | OAuth2 授权码 |
| **DeepSeek** | LLM 智能回答、内容生成、意图分类 | API Key |
| **即梦AI** | 文生图、图生图、多风格艺术创作 | API Key |
| **火山引擎** | 视频生成、语音合成（预留） | API Key |

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
     │ TypeScript       │    │ APScheduler          │
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
| **多媒体AI** | 即梦AI (图像生成) · 火山引擎 (视频/语音) |
| **知识图谱** | NetworkX · PostgreSQL (关系存储) |
| **数据** | MySQL 8.0 · Redis 7 · Alembic |
| **部署** | Docker Compose · Nginx · APScheduler |
| **监控** | Prometheus · Loguru |

---

## 快速开始

### 环境要求

- Docker & Docker Compose (v2)
- （可选）DeepSeek API Key — 用于 LLM 智能回答
- （可选）即梦AI API Key — 用于图像生成
- （可选）京东开放平台 API Key — 用于京东商品导入
- （可选）淘宝开放平台 API Key — 用于淘宝商品导入

### Docker 一键启动（开发环境）

```bash
# 克隆项目
git clone https://github.com/dctx479/mengzhi-cloud.git
cd mengzhi-cloud

# 配置环境变量
cp .env.docker.example .env.docker
# 编辑 .env.docker，填入 DEEPSEEK_API_KEY、JD/淘宝密钥等

# 启动所有服务
docker compose -f docker-compose.dev.yml up -d

# 等待服务就绪（约 30 秒）
# 前端:  http://localhost:5173
# 后端:  http://localhost:8001
# API 文档:  http://localhost:8001/docs
# 默认管理员: admin / admin123
```

### Docker 生产部署

```bash
# 配置生产环境变量
cp .env.docker.example .env.docker
# 编辑 .env.docker:
#   - ENVIRONMENT=production
#   - SECRET_KEY=<生成强密钥>
#   - MYSQL_PASSWORD=<强密码>
#   - 填入各 API Key 和 OAuth2 回调地址

# 启动生产服务
docker compose up -d --build

# 验证服务状态
docker compose ps
curl http://localhost/api/v1/health
```

**生产环境注意事项**：
- 务必修改 `SECRET_KEY` 和 `MYSQL_PASSWORD`
- 配置 HTTPS 反向代理（Nginx / Caddy）
- 设置 `CORS_ORIGINS` 为实际域名
- JD/淘宝 OAuth2 回调地址需与开放平台注册的回调地址一致

### 本地开发（不使用 Docker）

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

需要本地 MySQL 8.0 和 Redis 7 服务，配置 `backend/.env` 中的连接信息。

---

## 项目结构

```
mengzhi-cloud/
├── backend/
│   ├── app/
│   │   ├── api/                # API 路由
│   │   │   ├── auth.py         #   认证登录
│   │   │   ├── kefu.py         #   智能客服
│   │   │   ├── products.py     #   产品管理
│   │   │   ├── orders.py       #   订单管理
│   │   │   ├── jd_import.py    #   京东联盟导入
│   │   │   ├── taobao_import.py#   淘宝联盟导入
│   │   │   └── v1/
│   │   │       ├── router.py           # 集中路由注册
│   │   │       ├── ip_chat.py          # 双IP智能体API
│   │   │       ├── cultural_elements.py# 文化元素API
│   │   │       ├── brand_story.py      # 品牌故事API
│   │   │       └── batch_content.py    # 批量任务API
│   │   ├── core/               # 核心配置
│   │   ├── models/             # ORM 模型（40+）
│   │   ├── services/           # 业务服务层
│   │   │   ├── kefu_agent.py          # 客服 Agent 编排
│   │   │   ├── kefu_classifier.py     # 意图/情绪分类器
│   │   │   ├── kefu_rag.py            # RAG 知识库
│   │   │   ├── user_profile_service.py# 5 层用户画像
│   │   │   ├── ip_agent/              # 双IP智能体模块
│   │   │   │   ├── base_ip_agent.py   #   基类
│   │   │   │   ├── xiaoshu_agent.py   #   小数IP
│   │   │   │   ├── xiaoshang_agent.py #   小商IP
│   │   │   │   ├── ip_router.py       #   智能路由
│   │   │   │   └── ip_agent_factory.py#   工厂模式
│   │   │   ├── cultural/              # 文化元素模块
│   │   │   │   ├── enhanced_collector.py# 智能匹配引擎
│   │   │   │   ├── knowledge_graph.py   # 知识图谱
│   │   │   │   └── expert_review.py     # 专家审核
│   │   │   ├── brand_story/           # 品牌故事生成器
│   │   │   ├── livestream_script/     # 直播脚本生成器
│   │   │   ├── media_provider/        # 多媒体Provider抽象
│   │   │   │   ├── base.py            #   基类
│   │   │   │   ├── jimeng.py          #   即梦AI
│   │   │   │   └── volcengine.py      #   火山引擎
│   │   │   ├── jd_api_client.py       # 京东 API 客户端
│   │   │   ├── taobao_api_client.py   # 淘宝 API 客户端
│   │   │   └── ...
│   │   ├── tasks/              # 定时任务
│   │   │   ├── scheduler.py           # APScheduler 调度器
│   │   │   ├── reconciliation_tasks.py# 对账任务
│   │   │   └── taobao_token_refresh.py# 淘宝 Session 自动刷新
│   │   └── data/
│   │       ├── kefu_kb/               # 知识库文档（7 篇）
│   │       └── cultural_elements_extended.json # 文化元素库（66个）
│   ├── docs/                   # 技术文档（20+）
│   ├── tests/                  # 测试用例
│   ├── Dockerfile              # 生产镜像
│   ├── Dockerfile.dev          # 开发镜像（热重载）
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── api/                # API 客户端
│   │   ├── views/              # 页面组件
│   │   │   ├── kefu/           #   客服聊天 & 工单
│   │   │   ├── admin/          #   管理后台（含 JD/淘宝导入）
│   │   │   ├── user/           #   用户中心
│   │   │   ├── billing/        #   计费管理
│   │   │   └── enterprise/     #   企业配置
│   │   ├── stores/             # Pinia 状态管理
│   │   └── components/         # 公共组件
│   ├── Dockerfile              # 生产镜像（多阶段构建）
│   ├── Dockerfile.dev          # 开发镜像（Vite 热重载）
│   └── nginx.conf              # 前端 Nginx 配置
├── docker-compose.yml          # 生产环境
├── docker-compose.dev.yml      # 开发环境
├── docker-compose.test.yml     # 测试环境（仅 MySQL + Redis）
├── .env.docker.example         # Docker 环境变量模板
├── .env.example                # 本地开发环境变量模板
└── docs/                       # 项目文档
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

## API 概览

| 模块 | 端点前缀 | 说明 |
|------|---------|------|
| 认证 | `/api/v1/auth` | 登录、注册、JWT 刷新、登出 |
| 客服 | `/api/v1/kefu` | 聊天、会话、工单、蒸馏、画像、纠正 |
| 产品 | `/api/v1/products` | 产品 CRUD、搜索 |
| 订单 | `/api/v1/orders` | 订单管理 |
| 配额 | `/api/v1/quotas` | 使用量统计、套餐包 |
| 计费 | `/api/v1/billing` | 账单、发票 |
| 内容 | `/api/v1/content-generation` | AI 内容生成（5 种模板） |
| 京东导入 | `/api/v1/jd` | 京东联盟商品搜索、批量导入、OAuth2 |
| 淘宝导入 | `/api/v1/taobao` | 淘宝联盟商品搜索、批量导入、OAuth2 |
| SLA | `/api/v1/sla` | SLA 监控仪表板 |
| 审计 | `/api/v1/audit-logs` | 操作日志查询、导出 |
| 管理 | `/api/admin` | 用户管理、企业管理、统计 |

完整 API 文档：启动后访问 `/docs`（Swagger UI）或 `/redoc`

---

## 环境变量

| 变量 | 必填 | 说明 |
|------|------|------|
| `DATABASE_URL` | 是 | MySQL 连接串 |
| `REDIS_HOST` | 是 | Redis 主机地址 |
| `SECRET_KEY` | 是 | JWT 签名密钥（生产环境必须修改） |
| `ENCRYPTION_KEY` | 是 | 数据加密密钥 |
| `DEEPSEEK_API_KEY` | 否 | DeepSeek API 密钥（LLM 智能回答） |
| `DEEPSEEK_API_BASE` | 否 | DeepSeek API 地址，默认 `https://api.deepseek.com` |
| `JD_APP_KEY` | 否 | 京东联盟 AppKey |
| `JD_SECRET_KEY` | 否 | 京东联盟 Secret |
| `JD_OAUTH_REDIRECT_URI` | 否 | 京东 OAuth2 回调地址 |
| `TAOBAO_APP_KEY` | 否 | 淘宝联盟 AppKey |
| `TAOBAO_APP_SECRET` | 否 | 淘宝联盟 Secret |
| `TAOBAO_ADZONE_ID` | 否 | 淘宝推广位 ID |
| `TAOBAO_OAUTH_REDIRECT_URI` | 否 | 淘宝 OAuth2 回调地址 |

详细配置参考 `.env.docker.example` 和 `backend/.env.example`。

---

## 定时任务

平台通过 APScheduler 管理后台定时任务，在应用启动时自动注册：

| 任务 | 调度 | 说明 |
|------|------|------|
| 每日对账 | 每天 02:00 | 自动执行对账核验 |
| 差异检查 | 每 4 小时 | 检查待处理对账差异 |
| 健康检查 | 每天 09:00 | 对账系统健康检查 |
| 淘宝 Session 刷新 | 每 20 小时 | 自动刷新即将过期的淘宝 OAuth2 Session |

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
- CORS 白名单（按环境动态配置）
- 操作审计日志
- 细粒度 RBAC 权限控制
- OAuth2 CSRF State 校验（京东/淘宝授权）

---

## 部署参考

### 服务架构

```
┌──────────────┐
│  Frontend    │ :80 (Nginx)
│  Vue 3 SPA   │
└──────┬───────┘
       │ /api/* 反向代理
┌──────▼───────┐     ┌──────────┐     ┌──────────┐
│  Backend     │────▶│ MySQL 8  │     │ Redis 7  │
│  FastAPI     │     │ :3306    │     │ :6379    │
│  :8000       │────▶│          │     │          │
└──────────────┘     └──────────┘     └──────────┘
```

### 端口映射

| 服务 | 容器内端口 | 默认宿主机端口 | 环境变量 |
|------|-----------|---------------|---------|
| 前端 (Nginx) | 80 | 80 | `FRONTEND_PORT` |
| 后端 (Uvicorn) | 8000 | 8001 | `BACKEND_PORT` |
| MySQL | 3306 | 3307 | `MYSQL_PORT` |
| Redis | 6379 | 6380 | `REDIS_HOST_PORT` |

### 生产部署清单

1. 配置域名 DNS 解析到服务器 IP
2. 配置 HTTPS（Let's Encrypt / 商业证书）
3. 在外层 Nginx 或 Caddy 配置反向代理到 Docker 前端容器
4. 修改 `.env.docker` 中的 `ENVIRONMENT=production`、强密钥、CORS 域名
5. 在京东/淘宝开放平台注册 OAuth2 回调地址
6. 执行 `docker compose up -d --build`
7. 访问 `/docs` 验证后端 API
8. 登录管理后台，前往「系统管理 → 京东/淘宝导入」完成 OAuth2 授权

---

## 致谢

- [DeepSeek](https://www.deepseek.com) — 大语言模型 API
- [LangChain](https://langchain.com) — AI Agent 工具链

---

## 许可证

MIT License
