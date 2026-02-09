"""
SQLAlchemy数据模型文档

该文档描述了所有SQLAlchemy ORM模型的结构、关系和使用方法。

版本: 1.0
更新日期: [项目完成日期]
"""

# SQLAlchemy 数据模型完整指南

## 目录

1. [模型架构](#模型架构)
2. [核心模型](#核心模型)
3. [模型关系](#模型关系)
4. [使用示例](#使用示例)
5. [最佳实践](#最佳实践)

---

## 模型架构

### 项目结构

```
backend/app/
├── models/
│   ├── __init__.py              # 模型导出
│   ├── base.py                  # 基类和通用方法
│   ├── user.py                  # 用户模型
│   ├── enterprise.py            # 企业模型
│   ├── product.py               # 产品模型
│   ├── conversation.py          # AI对话模型
│   ├── message.py               # 对话消息模型
│   ├── content_record.py        # 内容生成记录模型
│   ├── user_quota.py            # 用户配额模型
│   └── generation_template.py   # 生成模板模型
└── core/
    └── database.py              # 数据库连接和初始化
```

### 基类设计

所有模型继承自 `BaseModel`，提供通用功能：

```python
class BaseModel(Base):
    # 时间戳字段
    created_at: datetime          # 创建时间（自动）
    updated_at: datetime          # 更新时间（自动）
    deleted_at: Optional[datetime]  # 软删除时间

    # 通用方法
    def to_dict() -> Dict             # 转换为字典
    def to_dict_exclude() -> Dict     # 排除指定字段的字典转换
    @classmethod
    def from_dict(data) -> Model      # 从字典创建实例
```

---

## 核心模型

### 1. User（用户模型）

**表名**: `users`

**主要字段**:
- `id`: 主键（自增）
- `user_uuid`: 用户唯一标识（UUID）
- `username`: 用户名（唯一）
- `email`: 邮箱（唯一）
- `phone`: 手机号（唯一）
- `password_hash`: 密码哈希值（bcrypt）
- `user_type`: 用户类型（PERSONAL/ENTERPRISE）
- `status`: 账号状态（ACTIVE/INACTIVE/BANNED/PENDING）
- `role`: 用户角色（ADMIN/ENTERPRISE_ADMIN/USER）
- `enterprise_id`: 所属企业ID（FK）

**关键方法**:
```python
user.is_locked()              # 检查账户是否被锁定
user.is_active()              # 检查账户是否激活
user.to_dict_safe()           # 返回不含敏感信息的字典
```

**关系**:
- `enterprise`: 所属企业（多对一）
- `conversations`: 对话列表（一对多）
- `content_records`: 内容生成记录（一对多）
- `quotas`: 配额列表（一对多）
- `products`: 创建的产品（一对多）

---

### 2. Enterprise（企业模型）

**表名**: `enterprises`

**主要字段**:
- `id`: 主键（自增）
- `enterprise_uuid`: 企业唯一标识（UUID）
- `name`: 企业名称
- `license_no`: 营业执照号（唯一）
- `verify_status`: 认证状态（PENDING/VERIFIED/REJECTED）
- `plan_type`: 订阅套餐（FREE/BASIC/PRO/ENTERPRISE）
- `plan_expires_at`: 套餐过期时间

**关键方法**:
```python
enterprise.is_verified()      # 检查是否已认证
enterprise.is_plan_active()   # 检查订阅是否有效
enterprise.get_plan_quota()   # 获取套餐配额
```

**套餐配额对应关系**:
- `FREE`: 每日50次对话，20次生成，100k Token
- `BASIC`: 每日200次对话，100次生成，1M Token
- `PRO`: 每日1000次对话，500次生成，10M Token
- `ENTERPRISE`: 无限制

---

### 3. Product（产品模型）

**表名**: `products`

**主要字段**:
- `id`: 主键（自增）
- `product_uuid`: 产品唯一标识（UUID）
- `name`: 产品名称
- `category`: 产品类别
- `origin_province`: 产地省份
- `certification_type`: 认证类型
- `status`: 产品状态（DRAFT/PENDING/PUBLISHED/OFFLINE）
- `enterprise_id`: 所属企业ID（FK）
- `created_by`: 创建人ID（FK）
- `features`: 产品特点（JSON）
- `cultural_tags`: 文化标签（JSON）

**关键方法**:
```python
product.is_published()        # 检查是否已发布
product.is_certified()        # 检查是否已认证
product.get_location()        # 获取位置信息
```

---

### 4. Conversation（AI对话模型）

**表名**: `ai_conversations`

**主要字段**:
- `id`: 主键（自增）
- `conversation_uuid`: 对话唯一标识（UUID）
- `user_id`: 用户ID（FK）
- `agent_type`: AI代理类型（XIAOSHU/XIAOSHANG/ASSISTANT）
- `status`: 对话状态（ACTIVE/ARCHIVED/DELETED）
- `message_count`: 消息总数
- `total_tokens`: Token总消耗

**关键方法**:
```python
conversation.is_active()      # 检查对话是否活跃
conversation.get_message_summary()  # 获取消息摘要
```

---

### 5. Message（对话消息模型）

**表名**: `ai_messages`

**主要字段**:
- `id`: 主键（自增）
- `message_uuid`: 消息唯一标识（UUID）
- `conversation_id`: 对话ID（FK）
- `role`: 消息角色（USER/ASSISTANT/SYSTEM）
- `content`: 消息内容
- `content_type`: 内容类型（TEXT/IMAGE/AUDIO/FILE）
- `prompt_tokens`: Prompt Token数
- `completion_tokens`: 生成Token数

**关键方法**:
```python
message.is_user_message()     # 检查是否为用户消息
message.is_assistant_message()  # 检查是否为助手消息
message.has_attachments()     # 检查是否有附件
message.get_token_usage()     # 获取Token使用统计
```

---

### 6. ContentRecord（内容生成记录模型）

**表名**: `content_records`

**主要字段**:
- `id`: 主键（自增）
- `record_uuid`: 记录唯一标识（UUID）
- `user_id`: 用户ID（FK）
- `product_id`: 产品ID（FK）
- `content_type`: 内容类型（COPY/SCRIPT/VIDEO_COPY/SLOGAN/STORY）
- `platform`: 目标平台（DOUYIN/XIAOHONGSHU/WECHAT/WEIBO/KUAISHOU/GENERAL）
- `style`: 风格（FORMAL/CASUAL/HUMOROUS/EMOTIONAL/PROFESSIONAL）
- `status`: 状态（GENERATING/COMPLETED/FAILED/CANCELLED）
- `generated_content`: 生成的内容
- `quality_score`: 质量评分（0-5）
- `user_rating`: 用户评分（1-5）

**关键方法**:
```python
record.is_completed()         # 检查是否生成完成
record.is_failed()            # 检查是否生成失败
record.get_token_cost()       # 获取Token消耗
record.get_usage_count()      # 获取使用计数
```

---

### 7. UserQuota（用户配额模型）

**表名**: `user_quotas`

**主要字段**:
- `id`: 主键（自增）
- `user_id`: 用户ID（FK）
- `quota_type`: 配额类型（DAILY/MONTHLY/TOTAL）
- `chat_limit/chat_used`: 对话配额
- `generation_limit/generation_used`: 生成配额
- `token_limit/token_used`: Token配额
- `storage_limit_mb/storage_used_mb`: 存储配额
- `period_start/period_end`: 配额周期

**关键方法**:
```python
quota.can_chat()              # 检查是否可对话
quota.can_generate()          # 检查是否可生成
quota.can_use_tokens(tokens)  # 检查是否有足够Token
quota.can_use_storage(mb)     # 检查是否有足够存储

quota.get_chat_usage()        # 获取对话配额使用情况
quota.get_generation_usage()  # 获取生成配额使用情况
quota.get_token_usage()       # 获取Token配额使用情况

quota.increment_chat_usage()  # 增加对话计数
quota.increment_token_usage(tokens)  # 增加Token使用
```

---

### 8. GenerationTemplate（生成模板模型）

**表名**: `generation_templates`

**主要字段**:
- `id`: 主键（自增）
- `template_uuid`: 模板唯一标识（UUID）
- `name`: 模板名称
- `content_type`: 内容类型（COPY/SCRIPT/VIDEO_COPY/SLOGAN/STORY）
- `platform`: 适用平台（DOUYIN/XIAOHONGSHU/WECHAT/WEIBO/KUAISHOU/GENERAL）
- `system_prompt`: 系统提示词
- `user_prompt_template`: 用户提示词模板
- `variables`: 变量定义（JSON）
- `is_system`: 是否系统模板
- `is_active`: 是否启用
- `use_count`: 使用次数
- `avg_rating`: 平均评分

**关键方法**:
```python
template.get_variables()      # 获取模板变量
template.get_variable_names()  # 获取变量名列表
template.validate_variables(input)  # 验证输入变量
template.render_user_prompt(vars)   # 渲染用户Prompt
template.get_popularity()     # 获取热度等级
```

---

## 模型关系

### 关系图

```
User (1) ──── (M) Conversation
  │
  ├─── (1) Enterprise (1) ──── (M) Product (created_by) ← User
  │
  ├─── (1) Product ──── (M) ContentRecord
  │
  └─── (1) UserQuota
       (1) ──── (M) QuotaType

Conversation (1) ──── (M) Message
               └──── (1) Product (context)

GenerationTemplate ──── (1) User (created_by)
```

### 外键关系

| 表 | 外键 | 指向表 | 删除策略 |
|---|---|---|---|
| users | enterprise_id | enterprises.id | CASCADE |
| products | enterprise_id | enterprises.id | SET NULL |
| products | created_by | users.id | RESTRICT |
| ai_conversations | user_id | users.id | CASCADE |
| ai_conversations | context_product_id | products.id | SET NULL |
| ai_messages | conversation_id | ai_conversations.id | CASCADE |
| content_records | user_id | users.id | CASCADE |
| content_records | product_id | products.id | SET NULL |
| user_quotas | user_id | users.id | CASCADE |
| generation_templates | created_by | users.id | SET NULL |

---

## 使用示例

### 1. 创建用户

```python
from sqlalchemy.orm import Session
from app.models import User, UserType, UserStatus, UserRole
from app.core.database import SessionLocal
from app.utils.security import hash_password

db = SessionLocal()

# 创建个人用户
user = User(
    username="john_doe",
    email="john@example.com",
    phone="13800138000",
    password_hash=hash_password("password123"),
    user_type=UserType.PERSONAL,
    status=UserStatus.ACTIVE,
    role=UserRole.USER,
    nickname="John Doe",
)
db.add(user)
db.commit()
db.refresh(user)
print(user.to_dict_safe())
```

### 2. 创建企业和企业用户

```python
# 创建企业
enterprise = Enterprise(
    name="内蒙古农业公司",
    license_no="91150000123456789",
    industry="农业",
    verify_status=VerifyStatus.PENDING,
    plan_type=PlanType.BASIC,
)
db.add(enterprise)
db.commit()

# 创建企业管理员
admin_user = User(
    username="enterprise_admin",
    email="admin@company.com",
    password_hash=hash_password("admin123"),
    user_type=UserType.ENTERPRISE,
    status=UserStatus.ACTIVE,
    role=UserRole.ENTERPRISE_ADMIN,
    enterprise_id=enterprise.id,
)
db.add(admin_user)
db.commit()
```

### 3. 创建产品

```python
from app.models import Product, ProductStatus

product = Product(
    name="乌兰察布马铃薯",
    category="农产品",
    origin_province="内蒙古自治区",
    origin_city="乌兰察布市",
    description="优质马铃薯，口感绵软",
    status=ProductStatus.DRAFT,
    enterprise_id=enterprise.id,
    created_by=admin_user.id,
    features=["淀粉含量高", "口感绵软", "绿色无污染"],
    cultural_tags=["农耕传统", "地域特色"],
)
db.add(product)
db.commit()
```

### 4. 创建对话

```python
from app.models import Conversation, AgentType

conversation = Conversation(
    user_id=user.id,
    title="关于马铃薯的对话",
    agent_type=AgentType.XIAOSHU,
    context_product_id=product.id,
)
db.add(conversation)
db.commit()
```

### 5. 添加消息

```python
from app.models import Message, MessageRole

# 添加用户消息
user_msg = Message(
    conversation_id=conversation.id,
    role=MessageRole.USER,
    content="请介绍一下这个产品的特点",
    prompt_tokens=50,
)
db.add(user_msg)
db.commit()

# 添加助手消息
assistant_msg = Message(
    conversation_id=conversation.id,
    role=MessageRole.ASSISTANT,
    content="这个马铃薯具有以下特点：1. 淀粉含量高，2. 口感绵软...",
    completion_tokens=100,
)
db.add(assistant_msg)
db.commit()

# 更新对话统计
conversation.message_count = 2
conversation.total_tokens = 150
db.commit()
```

### 6. 创建内容生成记录

```python
from app.models import ContentRecord, ContentType, Platform, Style, RecordStatus

record = ContentRecord(
    user_id=user.id,
    product_id=product.id,
    content_type=ContentType.VIDEO_COPY,
    platform=Platform.DOUYIN,
    style=Style.HUMOROUS,
    input_params={
        "product_name": "乌兰察布马铃薯",
        "target_audience": "年轻人",
        "duration": "15秒"
    },
    generated_content="你们想要的薯条升级版来啦！乌兰察布马铃薯，一口爆浆，口感绝了！",
    status=RecordStatus.COMPLETED,
    prompt_tokens=100,
    completion_tokens=80,
)
db.add(record)
db.commit()
```

### 7. 管理用户配额

```python
from datetime import date, timedelta
from app.models import UserQuota, QuotaType

# 创建每日配额
today = date.today()
tomorrow = today + timedelta(days=1)

quota = UserQuota(
    user_id=user.id,
    quota_type=QuotaType.DAILY,
    chat_limit=50,
    generation_limit=20,
    token_limit=100000,
    storage_limit_mb=100,
    period_start=today,
    period_end=tomorrow,
)
db.add(quota)
db.commit()

# 检查配额
if quota.can_chat():
    quota.increment_chat_usage()
    db.commit()

if quota.can_generate():
    quota.increment_generation_usage()
    db.commit()

if quota.can_use_tokens(100):
    quota.increment_token_usage(100)
    db.commit()

# 获取配额使用情况
print(quota.get_chat_usage())
print(quota.get_token_usage())
```

### 8. 查询示例

```python
# 获取用户的所有对话
conversations = db.query(Conversation).filter_by(user_id=user.id).all()

# 获取活跃对话
active_conversations = db.query(Conversation).filter(
    Conversation.user_id == user.id,
    Conversation.status == ConversationStatus.ACTIVE
).all()

# 获取对话的所有消息
messages = db.query(Message).filter_by(conversation_id=conversation.id).order_by(
    Message.created_at
).all()

# 获取用户最近的内容生成记录
recent_records = db.query(ContentRecord).filter(
    ContentRecord.user_id == user.id,
    ContentRecord.status == RecordStatus.COMPLETED
).order_by(ContentRecord.created_at.desc()).limit(10).all()

# 获取热门产品
hot_products = db.query(Product).filter(
    Product.status == ProductStatus.PUBLISHED
).order_by(Product.view_count.desc()).limit(10).all()
```

---

## 最佳实践

### 1. 会话管理

```python
from app.core.database import SessionLocal

def create_user(username: str, email: str) -> User:
    """函数内创建会话"""
    db = SessionLocal()
    try:
        user = User(username=username, email=email)
        db.add(user)
        db.commit()
        db.refresh(user)
        return user
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


# FastAPI中使用依赖注入
from fastapi import Depends
from app.core.database import get_db

@app.get("/users/{user_id}")
def get_user(user_id: int, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    return user
```

### 2. 错误处理

```python
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session

def create_user_safe(db: Session, username: str, email: str):
    try:
        user = User(username=username, email=email)
        db.add(user)
        db.commit()
        return user
    except IntegrityError:
        db.rollback()
        # 处理唯一约束冲突
        raise ValueError(f"用户名或邮箱已存在")
    except SQLAlchemyError as e:
        db.rollback()
        # 处理其他SQL错误
        raise ValueError(f"数据库错误: {str(e)}")
```

### 3. 关系加载

```python
# 立即加载（Eager Loading）
from sqlalchemy.orm import joinedload

user = db.query(User).options(
    joinedload(User.enterprise),
    joinedload(User.conversations)
).filter_by(id=user_id).first()

# 延迟加载（Lazy Loading）- 默认
user = db.query(User).filter_by(id=user_id).first()
# 访问关系时才加载
conversations = user.conversations
```

### 4. 批量操作

```python
# 批量插入
users = [
    User(username=f"user{i}", email=f"user{i}@example.com")
    for i in range(1000)
]
db.bulk_insert_mappings(User, users)
db.commit()

# 批量更新
db.query(User).filter(User.status == UserStatus.PENDING).update(
    {User.status: UserStatus.ACTIVE}
)
db.commit()

# 批量删除
db.query(ContentRecord).filter(
    ContentRecord.created_at < datetime.now() - timedelta(days=30)
).delete()
db.commit()
```

### 5. 分页查询

```python
def paginate(db: Session, model, skip: int = 0, limit: int = 10):
    return db.query(model).offset(skip).limit(limit).all()

# 使用
users = paginate(db, User, skip=0, limit=20)
```

---

## 常见问题

**Q: 如何处理并发访问？**
A: SQLAlchemy的连接池会自动处理并发。使用 `get_db()` 依赖注入确保每个请求有独立的会话。

**Q: 如何进行事务处理？**
A: SQLAlchemy自动为每个操作创建事务。使用 `db.commit()` 提交，`db.rollback()` 回滚。

**Q: 如何性能优化？**
A: 1) 使用索引，2) 使用 `joinedload` 避免N+1查询，3) 使用批量操作，4) 适当使用缓存。

---

最后更新: [项目完成日期]
