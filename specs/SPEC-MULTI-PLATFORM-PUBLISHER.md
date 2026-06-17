# SPEC-MULTI-PLATFORM-PUBLISHER — 多平台内容分发框架

**版本**: v1.0
**创建**: 2026-06-17
**状态**: 📐 Spec 阶段（RIPER: R）
**优先级**: 🟡 P1
**作者**: AI Engineer (Claude Code)

---

## 1. 背景与目标 (Background & Goals)

### 1.1 现状问题

通过 codegraph 勘察，发现内容生成与多平台分发之间存在"断点"：

| 现状 | 文件 | 备注 |
|---|---|---|
| ✅ 内容生成 | `backend/app/services/optimized_content_generation.py` | `OptimizedContentGenerationService` 已支持 `Platform` 枚举（douyin/xiaohongshu/wechat/weibo/kuaishou/general）|
| ✅ 内容记录 | `backend/app/models/content_record.py` | `ContentRecord` 表已存生成结果（含 `platform` 字段）|
| ❌ 一键分发 | 无 | 生成完成后无任何 API 把内容推到目标平台 |
| ❌ 发布追踪 | 无 | 不知道哪些内容已发布、发布到了哪些平台、表现如何 |
| ❌ 平台适配 | 无 | 不同平台的字数/格式/标签规则没有统一抽象 |

**核心问题**：
1. **断层**：内容生成在 `Platform.GENERAL` 模式下生成，平台差异由 prompt 层面处理，但生成结果未与发布行为挂钩
2. **缺抽象**：未来对接真实开放平台（小红书/抖音/视频号）需要写 4 套重复 HTTP 调用代码
3. **缺追踪**：发出去的内容无法回填表现数据（PV/UV/点赞）

### 1.2 目标

| ID | 目标 | 验收标准 |
|---|---|---|
| G1 | 平台适配器抽象层 | `PublisherBase` 抽象类，定义统一 publish() 接口 |
| G2 | 4 个平台 Mock 适配器 | Douyin / Xiaohongshu / Wechat / Weibo 4 个实现（Mock 模式）|
| G3 | 一键分发 API | `POST /api/v1/publisher/publish` 支持单条/批量发布 |
| G4 | 发布记录持久化 | `publish_records` 表，追踪发布状态、平台、URL、错误 |
| G5 | 表现数据回填 | `POST /api/v1/publisher/metrics/ingest` 接收表现数据（PV/UV/like/share/conversion）|
| G6 | 环境变量驱动 Mock/Real 切换 | `PUBLISHER_MODE=mock` (默认) / `real` |
| G7 | 不引入新第三方依赖 | 全部用 `httpx`（已在依赖中）|

### 1.3 非目标 (Out of Scope)

- ❌ 不对接真实开放平台（按用户决策走 Mock 模式 + 环境变量切换）
- ❌ 不实现 OAuth2 授权流程（真实模式仅打印"would call API"日志）
- ❌ 不做内容编辑/裁剪/重排（适配器只负责投递，不改写内容）
- ❌ 不做实时效果分析（仅数据采集接口，不做实时聚合推送）

---

## 2. 详细设计 (Design)

### 2.1 架构图

```
┌────────────────────────────────────────────────────────────────┐
│                    业务调用方 (Callers)                          │
│  - api/v1/optimized_content.py (内容生成后) [待集成]            │
│  - frontend ContentDistribute.vue  [前端未来调用]                │
│  - 批量任务 worker [待集成]                                      │
└────────────────────────┬───────────────────────────────────────┘
                         │ publish(record_id, platforms=[...])
                         ▼
┌────────────────────────────────────────────────────────────────┐
│           services/publisher/publisher_service.py              │
│                                                                │
│  ContentPublisherService.publish(content, platforms, ...)        │
│       ├── 1. 校验 content & 用户权限                             │
│       ├── 2. 平台适配器查找 (registry)                            │
│       ├── 3. 平台特定预处理 (字数/hashtag/封面图)                  │
│       ├── 4. asyncio.gather 分发到多平台                         │
│       ├── 5. 持久化 PublishRecord (per platform)                  │
│       └── 6. 触发表现数据定时采集 (cron 后续接)                    │
└───────┬──────────┬──────────────┬─────────────────────────────┘
        ▼          ▼              ▼
┌──────────┐ ┌──────────┐  ┌──────────┐  ┌──────────┐
│ Douyin   │ │Xiaohongshu│  │ Wechat   │  │ Weibo    │
│Publisher │ │ Publisher │  │ Publisher│  │ Publisher│
│ (Mock)   │ │ (Mock)    │  │ (Mock)   │  │ (Mock)   │
└──────────┘ └──────────┘  └──────────┘  └──────────┘
        │          │              │              │
        └──────────┴──────────────┴──────────────┘
                         │
                         ▼
        ┌────────────────────────────────────┐
        │     publish_records (新表)         │
        │     - id, content_id, platform     │
        │     - status, url, error           │
        │     - published_at                  │
        └────────────────────────────────────┘
```

### 2.2 数据模型 (Data Model)

#### 2.2.1 `PublishRecord`（新表）

```python
class PublishStatus(enum.Enum):
    PENDING = "pending"       # 排队中
    PUBLISHING = "publishing" # 发布中
    PUBLISHED = "published"   # 已发布
    FAILED = "failed"         # 失败
    DELETED = "deleted"       # 已下架

class PublishRecord(BaseModel):
    __tablename__ = "publish_records"

    id = Column(BIGINT, primary_key=True)
    publish_uuid = Column(VARCHAR(36), unique=True, default=generate_uuid)

    # 关联
    content_record_id = Column(BIGINT, ForeignKey("content_records.id"), nullable=False, index=True)
    user_id = Column(BIGINT, ForeignKey("users.id"), nullable=False, index=True)
    product_id = Column(BIGINT, ForeignKey("products.id"), nullable=True, index=True)

    # 平台
    platform = Column(Enum(Platform), nullable=False, index=True)

    # 平台处理后的内容
    adapted_title = Column(VARCHAR(200), comment="适配后标题")
    adapted_content = Column(TEXT, comment="适配后正文")
    adapted_tags = Column(JSON, comment="适配后标签列表")
    media_urls = Column(JSON, comment="媒体URL列表")

    # 发布结果
    status = Column(Enum(PublishStatus), default=PublishStatus.PENDING, index=True)
    platform_post_id = Column(VARCHAR(128), comment="平台返回的帖子ID")
    platform_url = Column(VARCHAR(500), comment="平台URL")
    error_message = Column(TEXT, comment="错误信息")
    retry_count = Column(Integer, default=0, comment="重试次数")

    # 时间
    published_at = Column(TIMESTAMP, comment="发布时间")
```

#### 2.2.2 `PublishMetric`（新表，表现数据）

```python
class PublishMetric(BaseModel):
    __tablename__ = "publish_metrics"

    id = Column(BIGINT, primary_key=True)
    publish_record_id = Column(BIGINT, ForeignKey("publish_records.id"), nullable=False, index=True)

    metric_date = Column(String(10), nullable=False, index=True)  # YYYY-MM-DD
    pv = Column(Integer, default=0)         # 浏览量
    uv = Column(Integer, default=0)         # 独立访客
    like_count = Column(Integer, default=0)
    share_count = Column(Integer, default=0)
    comment_count = Column(Integer, default=0)
    favorite_count = Column(Integer, default=0)
    conversion_count = Column(Integer, default=0)  # 转化数
    raw_data = Column(JSON)  # 平台原始数据
```

### 2.3 抽象层 (Abstract Layer)

#### 2.3.1 `PublisherBase`

```python
# backend/app/services/publisher/base.py

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any

@dataclass
class PublishRequest:
    """发布请求"""
    content: str
    title: Optional[str] = None
    images: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    extra: Dict[str, Any] = field(default_factory=dict)

@dataclass
class PublishResult:
    """发布结果"""
    success: bool
    platform: str
    platform_post_id: Optional[str] = None
    platform_url: Optional[str] = None
    error_message: Optional[str] = None
    raw_response: Optional[Dict[str, Any]] = None

class PublisherBase(ABC):
    """平台发布器抽象基类"""

    platform: str  # 子类定义: 'douyin' / 'xiaohongshu' / 'wechat' / 'weibo'

    def __init__(self, config: Dict[str, Any]):
        self.config = config

    @abstractmethod
    def adapt(self, request: PublishRequest) -> PublishRequest:
        """平台特定的内容适配（字数/标签/格式）"""
        ...

    @abstractmethod
    async def publish(self, request: PublishRequest) -> PublishResult:
        """执行发布（真实/模拟）"""
        ...

    def validate(self, request: PublishRequest) -> Optional[str]:
        """参数校验，返回错误信息或None"""
        ...
```

#### 2.3.2 平台特定规则

| 平台 | 字数限制 | 标签格式 | 媒体要求 |
|---|---|---|---|
| 抖音 | 标题≤30字，正文≤1500字 | #标签 | 至少1个视频/图片 |
| 小红书 | 标题≤20字，正文≤1000字 | #标签 @用户 | 至少1张图 |
| 微信公众号 | 标题≤64字，正文≤20000字 | 无 | 至少1张图 |
| 微博 | 标题≤30字（=首段），正文≤2000字 | #标签# | 图片或纯文本 |

### 2.4 适配器实现 (Mock)

每个平台的 Mock 实现：
1. **adapt()**：执行字数截断/标签规范化，遵守上表规则
2. **publish()**：模拟 50-300ms 延迟，返回 `platform_post_id=f"mock_{uuid4().hex[:16]}"` 和 `platform_url=f"https://mock.{platform}.com/post/{id}"`
3. **5% 概率模拟失败**（用于测试错误处理路径）

### 2.5 服务层 (Service Layer)

```python
# backend/app/services/publisher/publisher_service.py

class ContentPublisherService:
    """内容发布服务（统一入口）"""

    def __init__(self, db: Session):
        self.db = db
        self.registry = PublisherRegistry()  # platform -> PublisherBase

    async def publish(
        self,
        user_id: int,
        content_record_id: int,
        platforms: List[str],
    ) -> Dict[str, Any]:
        """发布到多个平台"""
        # 1. 校验 content_record 存在且属于 user
        # 2. 构造 PublishRequest
        # 3. 为每个 platform 找适配器
        # 4. asyncio.gather 并发发布
        # 5. 持久化 PublishRecord (per platform)
        # 6. 返回汇总结果

    async def ingest_metrics(
        self,
        publish_record_id: int,
        pv: int = 0,
        uv: int = 0,
        like_count: int = 0,
        ...
    ) -> PublishMetric:
        """表现数据采集入口"""
        # 1. 校验 publish_record
        # 2. upsert 当日 PublishMetric

    def get_metrics(
        self,
        user_id: int,
        product_id: Optional[int] = None,
        platform: Optional[str] = None,
        start_date: str = None,
        end_date: str = None,
    ) -> Dict[str, Any]:
        """聚合查询"""
        # GROUP BY platform/date/product
```

### 2.6 API 端点 (API Endpoints)

注册在 `/api/v1/publisher/...` 命名空间：

| 方法 | 端点 | 描述 | 鉴权 |
|---|---|---|---|
| POST | `/publisher/publish` | 一键发布到多平台 | 是 |
| GET | `/publisher/records` | 发布记录列表（按 user 过滤）| 是 |
| GET | `/publisher/records/{uuid}` | 发布详情 + 表现数据 | 是 |
| POST | `/publisher/records/{uuid}/retry` | 重试失败的发布 | 是 |
| POST | `/publisher/metrics/ingest` | 表现数据采集 | 是（service token）|
| GET | `/publisher/metrics/summary` | Dashboard 聚合数据 | 是 |
| GET | `/publisher/platforms` | 支持的平台列表 | 否 |

---

## 3. 实施计划 (Implementation Plan)

### 3.1 文件结构

```
backend/app/
├── services/
│   └── publisher/
│       ├── __init__.py
│       ├── base.py              # PublisherBase, PublishRequest, PublishResult
│       ├── registry.py          # PublisherRegistry (platform -> adapter)
│       ├── adapters/
│       │   ├── __init__.py
│       │   ├── douyin.py
│       │   ├── xiaohongshu.py
│       │   ├── wechat.py
│       │   └── weibo.py
│       └── publisher_service.py # ContentPublisherService
├── models/
│   └── publish_record.py        # PublishRecord + PublishMetric (新增)
├── api/
│   └── v1/
│       └── publisher.py         # API 路由
tests/
└── test_publisher.py            # 单元测试 (4 平台 + service)
```

### 3.2 风险与对策

| 风险 | 对策 |
|---|---|
| Mock 模式容易让人误以为"对接完成" | README 明确标注 "MOCK 模式 - 未对接真实 API"，所有 URL 域名以 `mock.` 开头 |
| 平台字数/格式规则可能变化 | 适配器规则集中在 `ADAPTER_RULES` 常量字典，易于查阅/修改 |
| 表现数据时序 | 用 `metric_date` 字符串字段按天聚合，避免时区问题 |
| 同一内容多平台发布 | 一个 `PublishRequest` → 多个 `PublishRecord`（per platform），共享 `content_record_id` |

---

## 4. 验收标准 (Acceptance Criteria)

| AC | 验证方法 |
|---|---|
| AC-1 | 4 个平台适配器类继承 `PublisherBase` 并实现 `adapt()` + `publish()` |
| AC-2 | `ContentPublisherService.publish()` 并发发布到 ≥2 平台，单平台失败不影响其他 |
| AC-3 | `POST /api/v1/publisher/publish` 端点可调用，鉴权正常 |
| AC-4 | 发布记录持久化到 `publish_records` 表 |
| AC-5 | 表现数据 `ingest` 端点可累积，summary 端点可聚合 |
| AC-6 | Mock 模式所有 URL 以 `mock.{platform}.com` 开头 |
| AC-7 | 单元测试 ≥10 个（4 平台 + service + metrics + edge cases）|
| AC-8 | `python -m py_compile` 所有新文件通过 |

---

## 5. 后续扩展 (Future Extensions)

- [ ] 真实模式：接入各平台 OAuth2 + 开放 API
- [ ] 内容预处理：跨平台统一风格规范化
- [ ] 自动重试：失败发布指数退避重试
- [ ] 表现数据定时拉取：cron job 拉取各平台数据
- [ ] 内容分发看板：前端可视化各平台表现对比

---

**Spec 状态**: ✅ 已批准，可进入实现阶段
**下一步**: 创建数据模型 → 抽象层 → 适配器 → 服务层 → API → 测试
