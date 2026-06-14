# 数据字典与接口协议
## Data Dictionary & Interface Protocol v1.0

**文档版本**: 1.0  
**创建日期**: 2026-06-11  
**强制遵守**: 所有开发人员

---

## 一、前后端接口协议

### 1.1 通用响应格式

**成功响应**:
```json
{
  "code": 200,
  "message": "success",
  "data": {...},
  "timestamp": "2026-06-11T10:30:00Z"
}
```

**错误响应**:
```json
{
  "code": 400,
  "message": "Invalid parameter: product_id is required",
  "data": null,
  "timestamp": "2026-06-11T10:30:00Z",
  "error_detail": {
    "field": "product_id",
    "reason": "required field missing"
  }
}
```

### 1.2 统一错误码

| 错误码 | 说明 | HTTP状态码 |
|-------|------|-----------|
| 200 | 成功 | 200 |
| 400 | 参数错误 | 400 |
| 401 | 未认证 | 401 |
| 403 | 无权限 | 403 |
| 404 | 资源不存在 | 404 |
| 409 | 资源冲突（如重复创建） | 409 |
| 429 | 请求频率过高 | 429 |
| 500 | 服务器内部错误 | 500 |
| 503 | 服务不可用（如LLM调用失败） | 503 |

**业务错误码**（4位数字）:
- 1xxx: 用户相关（1001=用户不存在，1002=密码错误）
- 2xxx: 产品相关（2001=产品不存在，2002=库存不足）
- 3xxx: IP Agent相关（3001=配额不足，3002=LLM调用失败）
- 4xxx: 订单相关（4001=订单不存在，4002=支付失败）

### 1.3 分页协议

**请求参数**:
```json
{
  "page": 1,      // 页码，从1开始
  "size": 20      // 每页数量，默认20，最大100
}
```

**响应格式**:
```json
{
  "code": 200,
  "data": {
    "items": [...],
    "total": 150,       // 总条数
    "page": 1,          // 当前页
    "size": 20,         // 每页数量
    "total_pages": 8    // 总页数
  }
}
```

### 1.4 日期时间格式

**统一使用ISO 8601**:
```
2026-06-11T10:30:00Z         # UTC时间
2026-06-11T18:30:00+08:00    # 东八区时间
```

**前端显示转换**:
```typescript
// 后端返回UTC时间
const timestamp = "2026-06-11T10:30:00Z"

// 前端转换为本地时间
const localTime = new Date(timestamp).toLocaleString('zh-CN')
// 输出: "2026/6/11 18:30:00"
```

---

## 二、核心实体字段说明

### 2.1 用户表 (users)

| 字段 | 类型 | 必填 | 说明 | 示例 |
|-----|------|------|------|------|
| id | BIGINT | ✅ | 主键ID | 1 |
| user_uuid | UUID | ✅ | 唯一标识符（API对外使用） | "a1b2c3d4-..." |
| username | VARCHAR(50) | ✅ | 用户名（唯一） | "zhangsan" |
| email | VARCHAR(100) | ❌ | 邮箱（唯一） | "test@example.com" |
| phone | VARCHAR(20) | ❌ | 手机号（唯一） | "13800138000" |
| password_hash | VARCHAR(255) | ✅ | bcrypt加密密码 | "$2b$12$..." |
| user_type | VARCHAR(20) | ✅ | individual/enterprise | "individual" |
| role | VARCHAR(20) | ✅ | user/admin | "user" |
| enterprise_id | BIGINT | ❌ | 所属企业ID | 10 |
| status | VARCHAR(20) | ✅ | active/disabled/deleted | "active" |
| created_at | TIMESTAMP | ✅ | 创建时间 | "2026-06-11 10:30:00" |

**业务规则**:
- `user_type=enterprise` 时 `enterprise_id` 必填
- `email` 和 `phone` 至少填一个
- 密码长度≥6位
- `status=deleted` 时不显示在列表

### 2.2 产品表 (products)

| 字段 | 类型 | 必填 | 说明 | 示例 |
|-----|------|------|------|------|
| id | BIGINT | ✅ | 主键ID | 1 |
| name | VARCHAR(200) | ✅ | 产品名称 | "锡林郭勒羊肉" |
| category_id | BIGINT | ✅ | 品类ID | 1 |
| origin_id | BIGINT | ✅ | 产地ID | 2 |
| description | TEXT | ❌ | 产品描述 | "草原散养..." |
| images | JSONB | ❌ | 图片URL数组 | ["url1", "url2"] |
| selling_points | JSONB | ❌ | 卖点数组 | ["草原散养", "肉质紧实"] |
| cultural_tags | JSONB | ❌ | 文化标签数组 | ["那达慕", "手把肉"] |
| price | DECIMAL(10,2) | ❌ | 价格（元） | 299.00 |
| stock | INT | ✅ | 库存 | 100 |
| status | VARCHAR(20) | ✅ | active/disabled/out_of_stock | "active" |
| view_count | INT | ✅ | 浏览次数 | 1230 |
| created_at | TIMESTAMP | ✅ | 创建时间 | "2026-06-11 10:30:00" |

**业务规则**:
- `images` 最多5张
- `selling_points` 最多10个
- `cultural_tags` 最多5个
- `price` 为null表示面议

### 2.3 IP对话记录 (ip_conversations)

| 字段 | 类型 | 必填 | 说明 | 示例 |
|-----|------|------|------|------|
| id | BIGINT | ✅ | 主键ID | 1 |
| session_id | VARCHAR(64) | ✅ | 会话ID | "sess_abc123" |
| user_id | BIGINT | ❌ | 用户ID（游客为null） | 123 |
| ip_type | VARCHAR(20) | ✅ | xiaoshu/xiaoshang | "xiaoshu" |
| role | VARCHAR(20) | ✅ | user/assistant | "user" |
| user_message | TEXT | ❌ | 用户消息 | "推荐一款羊肉" |
| ai_response | TEXT | ❌ | AI回复 | "咱们草原上的羊肉..." |
| intent_type | VARCHAR(50) | ❌ | 意图类型 | "product_inquiry" |
| emotion_type | VARCHAR(20) | ❌ | 情绪 | "positive" |
| cultural_elements_mentioned | JSONB | ❌ | 提及文化元素 | ["那达慕"] |
| suggestions | JSONB | ❌ | 建议追问 | ["这款有什么特点？"] |
| tokens_used | INT | ❌ | 消耗Token数 | 856 |
| latency_ms | INT | ❌ | 响应延迟（毫秒） | 1234 |
| cached | BOOLEAN | ✅ | 是否缓存命中 | false |
| created_at | TIMESTAMP | ✅ | 创建时间 | "2026-06-11 10:30:00" |

**业务规则**:
- `role=user` 时 `user_message` 必填
- `role=assistant` 时 `ai_response` 必填
- `session_id` 格式: `sess_{timestamp}_{random}`

### 2.4 文化元素表 (cultural_elements)

| 字段 | 类型 | 必填 | 说明 | 示例 |
|-----|------|------|------|------|
| id | BIGINT | ✅ | 主键ID | 1 |
| name | VARCHAR(100) | ✅ | 名称（唯一） | "那达慕" |
| type | VARCHAR(50) | ✅ | festival/skill/food/story/custom | "festival" |
| story | TEXT | ✅ | 文化故事（200-500字） | "蒙古族传统盛会..." |
| origin_region | VARCHAR(100) | ❌ | 起源地域 | "锡林郭勒" |
| hot_score | INT | ✅ | 热度分（0-100） | 95 |
| metadata | JSONB | ❌ | 扩展信息 | {"time": "农历六月初四"} |
| view_count | INT | ✅ | 查看次数 | 3456 |
| created_at | TIMESTAMP | ✅ | 创建时间 | "2026-06-11 10:30:00" |

**业务规则**:
- `type` 枚举值固定6个
- `hot_score` 每天凌晨根据查看次数更新
- `story` 长度200-500字

---

## 三、枚举值定义

### 3.1 用户类型 (user_type)

```typescript
enum UserType {
  INDIVIDUAL = 'individual',    // 个人用户
  ENTERPRISE = 'enterprise'     // 企业用户
}
```

### 3.2 用户角色 (role)

```typescript
enum UserRole {
  USER = 'user',      // 普通用户
  ADMIN = 'admin'     // 管理员
}
```

### 3.3 IP类型 (ip_type)

```typescript
enum IPType {
  XIAOSHU = 'xiaoshu',      // 小数（文化传承者）
  XIAOSHANG = 'xiaoshang'   // 小商（营销顾问）
}
```

### 3.4 文化元素类型 (culture_type)

```typescript
enum CultureType {
  FESTIVAL = 'festival',    // 节日
  SKILL = 'skill',          // 技艺
  FOOD = 'food',            // 美食
  STORY = 'story',          // 故事
  CUSTOM = 'custom',        // 习俗
  CRAFT = 'craft'           // 工艺
}
```

### 3.5 意图类型 (intent_type)

```typescript
enum IntentType {
  PRODUCT_INQUIRY = 'product_inquiry',          // 产品咨询
  BRAND_STORY = 'brand_story',                  // 品牌故事
  LIVE_SCRIPT = 'live_script',                  // 直播脚本
  CULTURAL_TRACE = 'cultural_trace',            // 文化溯源
  PURCHASE_ADVICE = 'purchase_advice',          // 选购建议
  MARKETING_STRATEGY = 'marketing_strategy',    // 营销策略
  PLATFORM_ADAPTATION = 'platform_adaptation'   // 平台适配
}
```

### 3.6 订单状态 (order_status)

```typescript
enum OrderStatus {
  PENDING = 'pending',          // 待支付
  PAID = 'paid',                // 已支付
  SHIPPING = 'shipping',        // 配送中
  COMPLETED = 'completed',      // 已完成
  CANCELLED = 'cancelled',      // 已取消
  REFUNDED = 'refunded'         // 已退款
}
```

---

## 四、字段命名约定

### 4.1 数据库字段

**通用规则**:
- 使用 `snake_case`
- 主键统一为 `id`
- 外键格式: `{关联表单数}_id`（如 `user_id`, `product_id`）
- 时间戳字段: `created_at`, `updated_at`, `deleted_at`
- 状态字段: `status`
- 布尔字段前缀 `is_` 或 `has_`（如 `is_active`, `has_paid`）

### 4.2 API响应字段

**前端使用 camelCase**:
```json
{
  "userId": 123,
  "userName": "zhangsan",
  "createdAt": "2026-06-11T10:30:00Z"
}
```

**后端Pydantic模型配置**:
```python
class UserResponse(BaseModel):
    user_id: int = Field(alias="userId")
    user_name: str = Field(alias="userName")
    created_at: datetime = Field(alias="createdAt")
    
    class Config:
        populate_by_name = True  # 支持snake_case和camelCase
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
```

---

## 五、JSONB字段规范

### 5.1 产品图片 (images)

```json
[
  "https://cdn.mengzhi.cloud/products/product1.jpg",
  "https://cdn.mengzhi.cloud/products/product2.jpg"
]
```

**约束**:
- 数组长度≤5
- URL必须以https开头
- 支持格式: jpg, png, webp

### 5.2 产品卖点 (selling_points)

```json
[
  "草原散养",
  "肉质紧实",
  "无膻味",
  "营养丰富"
]
```

**约束**:
- 数组长度≤10
- 每个卖点≤20字

### 5.3 文化标签 (cultural_tags)

```json
[
  "那达慕",
  "手把肉",
  "敖包祭祀"
]
```

**约束**:
- 数组长度≤5
- 必须是 `cultural_elements` 表中存在的名称

### 5.4 直播脚本 (script_content)

```json
[
  {
    "phase": "开场",
    "start": "0:00",
    "end": "0:30",
    "scene": "草原风景空镜 + 产品展示",
    "script": "老铁们好！欢迎来到直播间..."
  },
  {
    "phase": "痛点引入",
    "start": "0:30",
    "end": "1:30",
    "scene": "主播近景",
    "script": "大家都知道，买羊肉最怕的就是..."
  }
]
```

**约束**:
- 每个phase字段: 开场/痛点引入/卖点讲解/促单/收尾
- start/end格式: MM:SS
- scene≤50字
- script≤500字

---

## 六、数据验证规则

### 6.1 用户注册

```python
from pydantic import BaseModel, Field, EmailStr, validator

class UserRegisterRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=50, pattern=r'^[a-zA-Z0-9_]+$')
    email: EmailStr
    password: str = Field(..., min_length=6, max_length=100)
    
    @validator('password')
    def password_strength(cls, v):
        if not any(c.isupper() for c in v):
            raise ValueError('密码必须包含大写字母')
        if not any(c.isdigit() for c in v):
            raise ValueError('密码必须包含数字')
        return v
```

### 6.2 产品创建

```python
class ProductCreateRequest(BaseModel):
    name: str = Field(..., min_length=2, max_length=200)
    category_id: int = Field(..., gt=0)
    origin_id: int = Field(..., gt=0)
    description: str = Field(None, max_length=2000)
    images: List[str] = Field(default_factory=list, max_items=5)
    selling_points: List[str] = Field(default_factory=list, max_items=10)
    cultural_tags: List[str] = Field(default_factory=list, max_items=5)
    price: Decimal = Field(None, ge=0, decimal_places=2)
    stock: int = Field(0, ge=0)
    
    @validator('images')
    def validate_images(cls, v):
        for url in v:
            if not url.startswith('https://'):
                raise ValueError(f'图片URL必须使用HTTPS: {url}')
        return v
```

---

## 七、缓存键命名规范

### 7.1 Redis Key格式

```
{模块}:{功能}:{标识符}
```

**示例**:
```
llm:cache:a1b2c3d4                    # LLM响应缓存
session:sess_123:history               # 会话历史
rate_limit:user:123:chat:20260611     # 速率限制
quota:user:123:chat                    # 配额使用
hot_rank:cultural_elements             # 热度排行
```

### 7.2 缓存TTL规范

| 数据类型 | TTL | 说明 |
|---------|-----|------|
| LLM响应 | 3600s (1h) | 高频查询 |
| 会话历史 | 7200s (2h) | 对话上下文 |
| 用户Session | 1800s (30min) | JWT Refresh Token |
| 配额计数 | 86400s (1d) | 每日重置 |
| 热度排行 | 300s (5min) | 频繁更新 |

---

## 八、前后端数据类型映射

| 数据库类型 | Python类型 | TypeScript类型 | 说明 |
|-----------|-----------|---------------|------|
| BIGINT | int | number | 整数 |
| VARCHAR | str | string | 字符串 |
| TEXT | str | string | 长文本 |
| BOOLEAN | bool | boolean | 布尔值 |
| DECIMAL | Decimal | number | 精确小数 |
| TIMESTAMP | datetime | string (ISO 8601) | 时间戳 |
| JSONB | dict/list | object/array | JSON数据 |
| UUID | UUID | string | 唯一标识符 |

**注意事项**:
- `BIGINT` 可能超过JavaScript安全整数范围（2^53-1），前端接收为字符串
- `DECIMAL` 金额字段前端用字符串传输，避免精度丢失
- `TIMESTAMP` 后端统一返回UTC时间，前端本地化显示

---

## 九、敏感信息处理

### 9.1 不可返回字段

**用户表**:
- `password_hash`: 绝不返回
- `api_key_encrypted`: 仅管理员可见（脱敏显示）

**日志**:
- 所有密码、API Key、Token字段自动脱敏

### 9.2 脱敏规则

```python
def mask_sensitive_field(value: str, mask_char: str = "*") -> str:
    """脱敏显示"""
    if len(value) <= 8:
        return mask_char * len(value)
    
    # 显示前4位和后4位
    return value[:4] + mask_char * (len(value) - 8) + value[-4:]

# 示例
mask_sensitive_field("sk-ant-api-1234567890abcdef")
# 输出: "sk-a**********cdef"
```

---

## 十、接口版本控制

### 10.1 URL版本

```
https://api.mengzhi.cloud/v1/products      # 当前版本
https://api.mengzhi.cloud/v2/products      # 未来版本
```

### 10.2 字段废弃

**响应中标记废弃字段**:
```json
{
  "userId": 123,
  "userName": "test",
  "userType": "individual",  // @deprecated 使用 user_type 替代
  "user_type": "individual"
}
```

**文档标注**:
```python
class UserResponse(BaseModel):
    user_type: str = Field(..., description="用户类型")
    # DEPRECATED: 使用 user_type 替代，将在 v2 移除
    userType: str = Field(None, deprecated=True)
```

---

**文档结束**

> 数据字典是前后端协作的基础，任何修改必须同步更新此文档并通知相关人员。
