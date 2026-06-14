# 技术架构设计
## Technical Architecture v1.0

**文档版本**: 1.0  
**创建日期**: 2026-06-11  
**架构师**: [待填写]

---

## 一、系统架构总览

### 1.1 三层架构设计

```
┌─────────────────────────────────────────────────────────────┐
│                   表现层 (Presentation Layer)                 │
│              Vue 3 + Element Plus + TypeScript               │
│  ┌──────────┬──────────┬──────────┬──────────┬──────────┐  │
│  │ IP对话页 │ 营销工具 │ 产品管理 │ 数据看板 │ 用户中心 │  │
│  └──────────┴──────────┴──────────┴──────────┴──────────┘  │
└───────────────────────────┬─────────────────────────────────┘
                            ↓ HTTP/REST
┌─────────────────────────────────────────────────────────────┐
│              业务逻辑层 (Business Logic Layer)                │
│            FastAPI + Pydantic + SQLAlchemy 2.x               │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  业务服务层 (Services)                               │   │
│  │  • 产品服务 (ProductService)                         │   │
│  │  • 订单服务 (OrderService)                           │   │
│  │  • 用户服务 (UserService)                            │   │
│  └─────────────────────────────────────────────────────┘   │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  AI能力层 (AI Layer)                                 │   │
│  │  • IP Agent (xiaoshu/xiaoshang)                     │   │
│  │  • 知识图谱服务 (KG Service)                         │   │
│  │  • 内容生成服务 (Content Generator)                  │   │
│  └─────────────────────────────────────────────────────┘   │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  数据访问层 (Data Access Layer)                      │   │
│  │  • Repository模式 (CRUD封装)                         │   │
│  └─────────────────────────────────────────────────────┘   │
└───────────────────────────┬─────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                   数据层 (Data Layer)                         │
│  ┌──────────┬──────────┬──────────┬────────────────────┐   │
│  │PostgreSQL│  Redis   │  MinIO   │ Anthropic Claude   │   │
│  │ (主数据) │  (缓存)  │ (对象存储)│     (LLM API)      │   │
│  └──────────┴──────────┴──────────┴────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

### 1.2 服务拓扑图

```
[用户浏览器] 
    ↓
[Nginx反向代理:80/443]
    ├─→ [前端静态资源] (Vue 3 SPA)
    │     └─ index.html / assets/*.js,css
    │
    └─→ [FastAPI后端:8000]
          ├─→ [PostgreSQL:5432] (持久化数据)
          ├─→ [Redis:6379] (缓存+Session)
          ├─→ [MinIO:9000] (图片/文件)
          └─→ [Anthropic API] (Claude Sonnet 4.6)
```

---

## 二、技术选型决策

### 2.1 后端框架选型

| 候选方案 | 优势 | 劣势 | 评分 | 决策 |
|---------|------|------|------|------|
| **FastAPI** | 原生异步/类型提示/自动文档/高性能 | 社区相对Django小 | 9/10 | ✅ 选用 |
| Django | 生态成熟/ORM强大/Admin后台 | 同步模型/响应慢 | 6/10 | ❌ |
| Flask | 轻量/灵活 | 缺少异步支持/手动配置多 | 5/10 | ❌ |

**决策理由**: FastAPI原生支持异步，适合LLM长时调用场景；Pydantic自动校验提升开发效率；自动生成OpenAPI文档。

### 2.2 数据库选型

**主数据库: PostgreSQL 15**
- **选型理由**: 
  - JSONB支持（存储文化标签/卖点）
  - 全文搜索能力（GIN索引）
  - 成熟稳定，社区活跃
  - 支持地理位置数据（产地经纬度）
- **替代方案**: MySQL（JSONB支持较弱）

**缓存数据库: Redis 7**
- **用途**:
  - LLM响应缓存（TTL 1小时）
  - Session存储（JWT刷新令牌）
  - 速率限制计数器
  - 实时排行榜（文化元素热度）

**图数据库: Neo4j（Phase 2可选）**
- **用途**: 知识图谱升级（复杂关系查询优化）
- **迁移策略**: Phase 1用PostgreSQL，Phase 2评估后迁移

### 2.3 前端框架选型

| 技术 | 版本 | 选型理由 |
|-----|------|---------|
| **Vue 3** | 3.4+ | 组合式API/响应式系统/TypeScript支持好 |
| **Element Plus** | 2.5+ | 企业级组件库/开箱即用/中文文档 |
| **Vite** | 5.0+ | 快速HMR/原生ESM/插件生态 |
| **TypeScript** | 5.3+ | 类型安全/智能提示 |
| **Pinia** | 2.1+ | Vue 3官方推荐状态管理 |

**决策理由**: Vue 3生态成熟，Element Plus组件丰富，Vite构建速度快。

### 2.4 AI服务商选型

**多服务商策略**:
```
┌──────────────────────────────────────────────────┐
│            AI服务统一管理层                        │
│         (AI Provider Manager)                    │
└──────────────────────────────────────────────────┘
    │              │              │            │
    ▼              ▼              ▼            ▼
┌─────────┐  ┌──────────┐  ┌──────────┐  ┌─────────┐
│DeepSeek │  │火山引擎   │  │  MinIO   │  │ Claude  │
│(主LLM)  │  │(图/视频)  │  │ (存储)   │  │(备选LLM)│
└─────────┘  └──────────┘  └──────────┘  └─────────┘
```

| 服务商 | 能力 | 成本 | 决策 |
|-------|------|------|------|
| **DeepSeek** | 文本生成 | ¥0.001/千tokens | ✅ 主力LLM |
| **火山引擎即梦AI** | 图像生成 | ¥0.1/张 | ✅ 图像 |
| **火山引擎即梦AI** | 视频生成 | ¥2/分钟 | ✅ 视频 |
| **Claude Sonnet** | 文本生成（备选） | $3/M tokens | 🔄 降级 |
| **MinIO** | 媒体存储 | ¥0.12/GB | ✅ 存储 |

**DeepSeek选型理由**:
- ✅ **成本优势**: ¥0.001/千tokens，约为Claude的1/100
- ✅ **中文能力强**: 草原文化理解好，适合IP对话
- ✅ **API兼容**: OpenAI兼容接口，迁移成本低
- ✅ **响应速度**: P95延迟<2s

**火山引擎即梦AI选型理由**:
- ✅ **中国大陆服务**: 延迟低，无需翻墙
- ✅ **价格透明**: 按张/分钟计费
- ✅ **质量高**: 支持高清4K，视频稳定性好
- ✅ **企业支持**: 字节跳动技术支持

**成本对比**（每月10万次对话 + 500张图 + 10个视频）:
```
DeepSeek方案:  10万 × 2K × ¥0.001/千 + 500 × ¥0.1 + 10 × ¥2 = ¥270/月
Claude方案:    10万 × 2K × $15/M × 7.2 = ¥2,160/月

节省: 87%
```

---

## 三、核心模块设计

### 3.1 IP智能体模块

**目录结构**:
```
backend/app/services/ip_agent/
├── __init__.py
├── configs.py              # IP配置（人设/关键词）
├── prompt_templates.py     # Prompt模板库
├── xiaoshu_agent.py        # 小数Agent实现
├── xiaoshang_agent.py      # 小商Agent实现
├── ip_router.py            # 意图识别与路由
├── llm_client.py           # Claude API封装
└── context_manager.py      # 上下文管理（5轮历史）
```

**关键设计**:

**IPRouter（意图识别）**:
```python
class IPRouter:
    INTENT_KEYWORDS = {
        IPType.XIAOSHU: ["故事", "文化", "产地", "推荐", "怎么选"],
        IPType.XIAOSHANG: ["营销", "直播", "文案", "脚本", "运营"]
    }
    
    def route(self, user_message: str) -> IPType:
        """基于关键词命中数路由到合适的IP"""
        scores = {
            ip: sum(1 for kw in keywords if kw in user_message)
            for ip, keywords in self.INTENT_KEYWORDS.items()
        }
        return max(scores, key=scores.get)
```

**LLMClient（多服务商支持）**:
```python
class AIProviderManager:
    async def chat_with_fallback(self, messages: List[Dict]) -> str:
        # 1. 按优先级获取活跃的LLM服务商
        providers = await self._get_active_providers(provider_type="llm")
        
        # 2. 依次尝试（降级策略）
        for provider_config in providers:
            try:
                if provider_config.provider == "deepseek":
                    client = DeepSeekClient(...)
                    return await client.chat(messages)
                elif provider_config.provider == "claude":
                    client = ClaudeClient(...)
                    return await client.chat(messages)
            except Exception as e:
                logger.warning(f"{provider_config.provider} failed: {e}")
                continue
        
        raise Exception("All LLM providers failed")
```

**ContextManager（上下文）**:
```python
class ContextManager:
    MAX_HISTORY = 5
    
    async def get_context(self, session_id: str) -> List[Dict]:
        """获取最近5轮对话"""
        key = f"session:{session_id}:history"
        history = await self.redis.lrange(key, -self.MAX_HISTORY, -1)
        return [json.loads(h) for h in history]
```

### 3.2 知识图谱模块

**目录结构**:
```
backend/app/services/knowledge_graph/
├── __init__.py
├── kg_service.py           # 图谱查询服务
├── trace_engine.py         # 溯源引擎
├── recommend_engine.py     # 文化元素推荐
└── graph_builder.py        # 图谱构建工具
```

**数据模型（Phase 1 - PostgreSQL）**:
```
产品 (products)
  ├─ origin_id → 产地 (origins)
  │                └─ 文化元素关联 (origin_culture_links)
  └─ cultural_tags (JSONB) ['那达慕', '手把肉']

溯源查询 = 三表JOIN + JSONB聚合
```

**溯源引擎**:
```python
class TraceEngine:
    async def trace_product(self, product_id: int) -> Dict:
        """产品文化溯源"""
        query = text("""
            SELECT 
              p.name AS product_name,
              o.name AS origin_name,
              JSON_AGG(
                JSON_BUILD_OBJECT(
                  'name', ce.name,
                  'type', ce.type,
                  'story', ce.story
                )
              ) AS cultures
            FROM products p
            JOIN origins o ON p.origin_id = o.id
            JOIN product_culture_links pcl ON p.id = pcl.product_id
            JOIN cultural_elements ce ON pcl.culture_id = ce.id
            WHERE p.id = :product_id
            GROUP BY p.id, o.id
        """)
        result = await self.db.execute(query, {"product_id": product_id})
        return result.first()._asdict()
```

### 3.3 媒体生成模块

**目录结构**:
```
backend/app/services/media/
├── __init__.py
├── volcengine_image_client.py   # 火山引擎图像生成
├── volcengine_video_client.py   # 火山引擎视频生成
├── minio_service.py              # MinIO对象存储
└── prompt_enhancer.py            # Prompt增强（融合文化元素）
```

**图像生成服务**:
```python
class ImageGenerationService:
    async def generate_marketing_image(
        self,
        prompt: str,
        product_id: int = None,
        style: str = "realistic"
    ) -> Dict:
        """生成产品营销图片"""
        # 1. Prompt增强（融合草原文化）
        if product_id:
            cultures = await self.kg_service.get_product_cultures(product_id)
            enhanced_prompt = self._enhance_with_culture(prompt, cultures)
        else:
            enhanced_prompt = prompt
        
        # 2. 调用火山引擎
        result = await self.volcengine_client.text_to_image(
            prompt=enhanced_prompt,
            style=style,
            width=1024,
            height=1024
        )
        
        # 3. 上传到MinIO
        image_url = await self.minio_service.upload_from_url(
            result["image_url"],
            bucket="marketing-images"
        )
        
        return {
            "image_url": image_url,
            "prompt": enhanced_prompt,
            "cost": result["cost"]
        }
```

**视频生成服务**:
```python
class VideoGenerationService:
    async def generate_promo_video(
        self,
        prompt: str,
        duration: int = 5,
        resolution: str = "1080p"
    ) -> Dict:
        """生成产品宣传视频（异步任务）"""
        # 1. 提交任务到火山引擎
        task = await self.volcengine_client.text_to_video(
            prompt=prompt,
            duration=duration,
            resolution=resolution
        )
        
        # 2. 返回任务ID（前端轮询状态）
        return {
            "task_id": task["task_id"],
            "status": "processing",
            "estimated_time": duration * 60  # 秒
        }
    
    async def check_video_status(self, task_id: str) -> Dict:
        """查询视频生成状态"""
        status = await self.volcengine_client.get_task_status(task_id)
        
        if status["status"] == "completed":
            # 上传到MinIO
            video_url = await self.minio_service.upload_from_url(
                status["video_url"],
                bucket="promo-videos"
            )
            return {
                "status": "completed",
                "video_url": video_url,
                "thumbnail_url": status["thumbnail_url"]
            }
        
        return status
```

### 3.4 营销工具模块

**目录结构**:
```
backend/app/services/marketing/
├── __init__.py
├── brand_story_generator.py    # 品牌故事生成
├── live_script_generator.py    # 直播脚本生成
└── platform_adapter.py         # 平台内容适配
```

**品牌故事生成器**:
```python
class BrandStoryGenerator:
    async def generate(
        self,
        product_name: str,
        origin: str,
        selling_points: List[str],
        target_audience: str
    ) -> Dict:
        """生成品牌故事"""
        # 1. 查询相关文化元素
        cultures = await self.kg_service.recommend_cultures(product_name, origin)
        
        # 2. 构建Prompt
        prompt = self._build_prompt(product_name, origin, selling_points, cultures)
        
        # 3. 调用LLM
        story = await self.llm_client.call_with_cache(prompt)
        
        return {
            "story_content": story,
            "cultural_elements": [c["name"] for c in cultures],
            "word_count": len(story)
        }
```

---

## 四、安全架构

### 4.1 认证授权

**JWT双Token机制**:
```
Access Token:
  - 有效期: 2小时
  - 存储: 内存（不持久化）
  - 用途: API调用认证

Refresh Token:
  - 有效期: 30天
  - 存储: Redis（可撤销）
  - 用途: 刷新Access Token
```

**RBAC权限模型**:
```
角色层级:
  admin > enterprise_admin > enterprise_user > individual_user

权限矩阵:
  ┌──────────────┬──────┬──────┬──────┬──────┐
  │ 资源/操作    │ admin│ ent_a│ ent_u│ indiv│
  ├──────────────┼──────┼──────┼──────┼──────┤
  │ 查看所有用户 │  ✅  │  ❌  │  ❌  │  ❌  │
  │ 管理文化元素 │  ✅  │  ❌  │  ❌  │  ❌  │
  │ IP对话       │  ✅  │  ✅  │  ✅  │  ✅  │
  │ 创建子账号   │  ✅  │  ✅  │  ❌  │  ❌  │
  │ 查看企业报表 │  ✅  │  ✅  │  ✅  │  ❌  │
  └──────────────┴──────┴──────┴──────┴──────┘
```

### 4.2 数据安全

**传输层安全**:
- HTTPS (TLS 1.3)
- HSTS强制HTTPS
- 证书: Let's Encrypt自动续期

**存储层安全**:
- 敏感字段加密: AES-256-GCM
  - 加密范围: API Key, 密码（bcrypt）
- 数据库访问: 最小权限原则
- 备份加密: GPG加密备份文件

**应用层安全**:
- SQL注入防护: SQLAlchemy参数化查询
- XSS防护: 前端自动转义（Vue 3默认）
- CSRF防护: SameSite Cookie + CSRF Token

### 4.3 API安全

**速率限制**:
```python
# 基于Redis滑动窗口算法
@limiter.limit("100/day")  # 免费用户
async def chat_endpoint():
    pass
```

**CORS配置**:
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://mengzhi.cloud"],  # 生产域名白名单
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)
```

**API签名验证（企业API）**:
```
签名算法: HMAC-SHA256
签名内容: HTTP_METHOD + URL + TIMESTAMP + BODY
有效期: 5分钟
```

---

## 五、部署架构

### 5.1 开发环境

**Docker Compose一键启动**:
```yaml
services:
  backend:
    build: ./backend
    ports: ["8000:8000"]
    volumes: ["./backend:/app"]
    command: uvicorn app.main:app --reload
  
  frontend:
    build: ./frontend
    ports: ["5173:5173"]
    volumes: ["./frontend:/app"]
    command: npm run dev
  
  postgres:
    image: postgres:15
    ports: ["5432:5432"]
  
  redis:
    image: redis:7
    ports: ["6379:6379"]
```

### 5.2 生产环境

**服务器配置**:
- 云平台: 阿里云/腾讯云
- 规格: 2C4G, 40GB SSD
- 系统: Ubuntu 22.04 LTS
- 端口: 22(SSH), 80(HTTP), 443(HTTPS), 8000(API)

**Nginx配置**:
```nginx
server {
    listen 443 ssl http2;
    server_name api.mengzhi.cloud;
    
    # 前端静态资源
    location / {
        root /var/www/frontend/dist;
        try_files $uri /index.html;
    }
    
    # 后端API代理
    location /api/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header X-Real-IP $remote_addr;
    }
    
    # 静态资源缓存
    location ~* \.(js|css|png|jpg|jpeg|gif|ico)$ {
        expires 7d;
        add_header Cache-Control "public, immutable";
    }
}
```

**Docker部署**:
```bash
# 构建镜像
docker compose -f docker-compose.prod.yml build

# 启动服务
docker compose -f docker-compose.prod.yml up -d

# 健康检查
curl http://localhost:8000/health
```

### 5.3 监控体系

**应用监控: Prometheus + Grafana**:
```python
# FastAPI集成Prometheus
from prometheus_fastapi_instrumentator import Instrumentator

app = FastAPI()
Instrumentator().instrument(app).expose(app)
```

**指标监控**:
- API响应时间（P50/P95/P99）
- QPS/错误率
- LLM Token消耗
- Redis缓存命中率
- 数据库慢查询

**日志收集**:
```python
# 结构化日志
import structlog

logger = structlog.get_logger()
logger.info("ip_chat_request", 
    user_id=user_id, 
    ip_type=ip_type, 
    latency_ms=latency
)
```

**错误追踪: Sentry**:
```python
import sentry_sdk

sentry_sdk.init(
    dsn="https://xxx@sentry.io/xxx",
    traces_sample_rate=0.1
)
```

---

## 六、可扩展性设计

### 6.1 水平扩展策略

**无状态API设计**:
- Session存Redis（不依赖本地内存）
- 上传文件走MinIO（不存本地磁盘）
- 支持多实例负载均衡

**数据库读写分离（Phase 3）**:
```
写操作 → Master
读操作 → Slave1, Slave2 (轮询)
```

**CDN加速**:
- 静态资源: 阿里云CDN
- 图片: MinIO + CDN

### 6.2 插件化设计

**文化元素插件化**:
```sql
-- 新增地域只需插入数据
INSERT INTO cultural_elements (name, type, story, origin_region)
VALUES ('鄂尔多斯婚礼', 'custom', '...', '鄂尔多斯');
```

**IP Agent插件化（Phase 3）**:
```python
# 未来可扩展新IP
class XiaoxiaoAgent(BaseAgent):  # 小小（儿童向）
    def get_system_prompt(self) -> str:
        return "你是小小，儿童科普员..."
```

**营销工具插件化**:
```python
# 新平台适配器
class KuaishouAdapter(BasePlatformAdapter):
    def adapt_content(self, content: str) -> str:
        # 快手平台话术适配
        return content
```

### 6.3 多租户架构预留

**数据隔离**:
```sql
-- 所有业务表添加tenant_id
ALTER TABLE products ADD COLUMN tenant_id BIGINT;
CREATE INDEX idx_tenant ON products(tenant_id);
```

**配额隔离**:
```python
# 租户级别配额控制
class TenantQuota:
    def __init__(self, tenant_id: str):
        self.tenant_id = tenant_id
    
    async def check_quota(self, resource_type: str) -> bool:
        key = f"quota:{self.tenant_id}:{resource_type}"
        used = await redis.get(key)
        return used < self.get_limit(resource_type)
```

---

## 七、技术债务管理

### 7.1 已知技术债

| 技术债 | 影响 | 偿还计划 |
|-------|------|---------|
| MySQL实现知识图谱 | 复杂查询性能差 | Sprint 4评估Neo4j |
| 无全文搜索 | 产品搜索体验差 | Sprint 5引入Elasticsearch |
| 单机部署 | 可用性风险 | Phase 3高可用集群 |
| 手动数据库迁移 | 易出错 | 完善Alembic脚本 |

### 7.2 技术选型复盘机制

**每2个Sprint复盘一次**:
1. 技术选型是否合理？
2. 是否遇到不可克服的限制？
3. 是否有更优替代方案？
4. 决策是否需要调整？

---

## 八、架构演进路线

```
Phase 1 (Week 1-12): MVP
  ├─ 单体架构
  ├─ PostgreSQL知识图谱
  └─ 单机部署

Phase 2 (Month 4-6): 优化
  ├─ Neo4j图数据库
  ├─ Elasticsearch全文搜索
  └─ Redis集群

Phase 3 (Month 7-12): SaaS化
  ├─ 微服务拆分
  ├─ 多租户架构
  ├─ 高可用集群
  └─ 自动扩缩容
```

---

**文档结束**

> 架构设计应随项目演进持续优化，每个Sprint结束后评审一次。
