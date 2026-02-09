# API设计规范

> **文档版本**: v1.0  
> **更新日期**: [项目完成日期]  
> **适用项目**: 内蒙古农畜产品品牌营销AI赋能云平台

---

## 目录

1. [基础规范](#1-基础规范)
2. [认证机制](#2-认证机制)
3. [统一响应格式](#3-统一响应格式)
4. [错误码体系](#4-错误码体系)
5. [分页规范](#5-分页规范)
6. [MVP核心接口定义](#6-mvp核心接口定义)

---

## 1. 基础规范

### 1.1 API版本控制

所有API采用URL路径版本控制方式：

```
https://api.example.com/api/v1/...
```

**版本升级策略**：
- 小版本更新（向后兼容）：不改变版本号
- 大版本更新（不兼容改动）：增加版本号 v1 -> v2
- 旧版本支持至少6个月后废弃

### 1.2 请求格式

| 项目 | 规范 |
|------|------|
| 协议 | HTTPS（强制） |
| 数据格式 | JSON |
| 字符编码 | UTF-8 |
| 时间格式 | ISO 8601（`[项目完成日期]T10:00:00Z`） |
| 时区 | UTC（客户端自行转换本地时区） |

### 1.3 HTTP方法语义

| 方法 | 语义 | 幂等性 | 示例 |
|------|------|--------|------|
| GET | 获取资源 | 是 | 获取产品列表 |
| POST | 创建资源 | 否 | 创建新用户 |
| PUT | 完整更新资源 | 是 | 更新用户信息 |
| PATCH | 部分更新资源 | 是 | 修改用户昵称 |
| DELETE | 删除资源 | 是 | 删除内容记录 |

### 1.4 URL命名规范

- 使用小写字母
- 使用连字符（-）分隔单词
- 使用名词复数表示资源集合
- 避免使用动词（动作通过HTTP方法表达）

```
# 正确示例
GET  /api/v1/products
GET  /api/v1/products/{id}
POST /api/v1/products
GET  /api/v1/users/{id}/orders

# 错误示例
GET  /api/v1/getProducts
POST /api/v1/createUser
```

### 1.5 请求头规范

**必需请求头**：

| Header | 说明 | 示例值 |
|--------|------|--------|
| Content-Type | 请求内容类型 | `application/json; charset=utf-8` |
| Accept | 接受的响应类型 | `application/json` |
| Authorization | 认证令牌 | `Bearer eyJhbGciOiJIUzI1...` |
| X-Request-ID | 请求追踪ID | `uuid-v4` |

**可选请求头**：

| Header | 说明 | 示例值 |
|--------|------|--------|
| Accept-Language | 语言偏好 | `zh-CN` |
| X-Device-ID | 设备标识 | `device-uuid` |
| X-Platform | 平台类型 | `web` / `miniprogram` / `app` |
| X-Version | 客户端版本 | `1.0.0` |

---

## 2. 认证机制

### 2.1 JWT认证方案

采用JWT（JSON Web Token）双Token机制：
- **Access Token**: 短期有效，用于API访问认证
- **Refresh Token**: 长期有效，用于刷新Access Token

### 2.2 Access Token

**有效期**: 30分钟

**Token结构（Header）**:
```json
{
  "alg": "HS256",
  "typ": "JWT"
}
```

**Token结构（Payload）**:
```json
{
  "sub": "user_123456",
  "iss": "ai-marketing-platform",
  "iat": 1705478400,
  "exp": 1705480200,
  "nbf": 1705478400,
  "jti": "uuid-v4",
  "type": "access",
  "user_type": "enterprise",
  "role": "admin",
  "tenant_id": "tenant_001"
}
```

**字段说明**：
- `sub`: 用户ID
- `iss`: 签发者
- `iat`: 签发时间（Unix时间戳）
- `exp`: 过期时间（30分钟后）
- `nbf`: 生效时间
- `jti`: Token唯一ID
- `type`: Token类型
- `user_type`: 用户类型（personal/enterprise）
- `role`: 用户角色
- `tenant_id`: 租户ID（企业用户）

**生成代码（Python）**:

```python
import jwt
from datetime import datetime, timedelta
from typing import Optional
import uuid

SECRET_KEY = "your-256-bit-secret-key-here"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

def create_access_token(
    user_id: str,
    user_type: str,
    role: str,
    tenant_id: Optional[str] = None
) -> str:
    """生成Access Token"""
    now = datetime.utcnow()
    payload = {
        "sub": user_id,
        "iss": "ai-marketing-platform",
        "iat": now,
        "exp": now + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
        "nbf": now,
        "jti": str(uuid.uuid4()),
        "type": "access",
        "user_type": user_type,
        "role": role,
    }
    if tenant_id:
        payload["tenant_id"] = tenant_id
    
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
```

### 2.3 Refresh Token

**有效期**: 7天

**Token结构（Payload）**:
```json
{
  "sub": "user_123456",
  "iss": "ai-marketing-platform",
  "iat": 1705478400,
  "exp": 1706083200,
  "jti": "uuid-v4",
  "type": "refresh",
  "device_id": "device-uuid",
  "ip_hash": "sha256-hash-prefix"
}
```

**生成代码（Python）**:

```python
REFRESH_TOKEN_EXPIRE_DAYS = 7

def create_refresh_token(
    user_id: str,
    device_id: Optional[str] = None,
    ip_address: Optional[str] = None
) -> str:
    """生成Refresh Token"""
    now = datetime.utcnow()
    payload = {
        "sub": user_id,
        "iss": "ai-marketing-platform",
        "iat": now,
        "exp": now + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS),
        "jti": str(uuid.uuid4()),
        "type": "refresh",
    }
    if device_id:
        payload["device_id"] = device_id
    if ip_address:
        import hashlib
        payload["ip_hash"] = hashlib.sha256(ip_address.encode()).hexdigest()[:16]
    
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
```

### 2.4 Token刷新流程

```
Client                          API Server                       Redis
  |                                 |                               |
  |-- 1. API请求(Access Token) ---->|                               |
  |                                 |-- 2. 验证Token --------------->|
  |                                 |<-- Token有效 ------------------|
  |<-- 3. 401 Token过期 ------------|                               |
  |                                 |                               |
  |-- 4. 刷新请求(Refresh Token) -->|                               |
  |                                 |-- 5. 验证Refresh Token ------>|
  |                                 |-- 6. 检查黑名单 -------------->|
  |                                 |<-- 验证通过 -------------------|
  |                                 |                               |
  |<-- 7. 新Token对 ----------------|-- 8. 旧Token加入黑名单 ------>|
  |                                 |                               |
```

**刷新Token实现代码**:

```python
from fastapi import HTTPException, status
import redis

redis_client = redis.Redis(host='localhost', port=6379, db=0)

def refresh_tokens(refresh_token: str) -> dict:
    """刷新Token对"""
    try:
        # 1. 解码Refresh Token
        payload = jwt.decode(refresh_token, SECRET_KEY, algorithms=[ALGORITHM])
        
        # 2. 验证Token类型
        if payload.get("type") != "refresh":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token type"
            )
        
        # 3. 检查黑名单
        jti = payload.get("jti")
        if redis_client.exists(f"token_blacklist:{jti}"):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has been revoked"
            )
        
        # 4. 获取用户信息（从数据库）
        user_id = payload.get("sub")
        user = get_user_by_id(user_id)
        
        # 5. 生成新Token对
        new_access_token = create_access_token(
            user_id=user.id,
            user_type=user.user_type,
            role=user.role,
            tenant_id=user.tenant_id
        )
        new_refresh_token = create_refresh_token(
            user_id=user.id,
            device_id=payload.get("device_id")
        )
        
        # 6. 将旧Refresh Token加入黑名单
        ttl = payload.get("exp") - int(datetime.utcnow().timestamp())
        if ttl > 0:
            redis_client.setex(f"token_blacklist:{jti}", ttl, "revoked")
        
        return {
            "access_token": new_access_token,
            "refresh_token": new_refresh_token,
            "token_type": "Bearer",
            "expires_in": ACCESS_TOKEN_EXPIRE_MINUTES * 60
        }
        
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token has expired"
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )
```

### 2.5 Token存储建议

**客户端存储**:
- Web: HttpOnly Cookie（推荐）或 localStorage（注意XSS防护）
- 小程序: wx.setStorageSync
- APP: Secure Storage / Keychain

**服务端存储（Redis）**:
```
# Refresh Token白名单（可选，用于单设备登录）
user:{user_id}:refresh_tokens -> Set<jti>

# Token黑名单（用于登出、刷新后作废）
token_blacklist:{jti} -> "revoked" (TTL = token过期时间)

# 用户Session信息（可选）
session:{user_id}:{device_id} -> {user_agent, ip, login_time, last_active}
```

---

## 3. 统一响应格式

### 3.1 成功响应

```json
{
  "code": 200,
  "message": "success",
  "data": {
    // 业务数据
  },
  "timestamp": "[项目完成日期]T10:00:00Z"
}
```

### 3.2 分页响应

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "items": [...],
    "pagination": {
      "page": 1,
      "size": 20,
      "total": 100,
      "pages": 5,
      "has_next": true,
      "has_prev": false
    }
  },
  "timestamp": "[项目完成日期]T10:00:00Z"
}
```

### 3.3 错误响应

```json
{
  "code": 10001,
  "message": "参数验证失败",
  "data": null,
  "errors": [
    {
      "field": "email",
      "message": "邮箱格式不正确"
    },
    {
      "field": "password",
      "message": "密码长度至少8位"
    }
  ],
  "timestamp": "[项目完成日期]T10:00:00Z",
  "request_id": "uuid-v4"
}
```

### 3.4 响应模型（Python/Pydantic）

```python
from pydantic import BaseModel
from typing import TypeVar, Generic, Optional, List, Any
from datetime import datetime

T = TypeVar("T")

class PaginationInfo(BaseModel):
    """分页信息"""
    page: int
    size: int
    total: int
    pages: int
    has_next: bool
    has_prev: bool

class FieldError(BaseModel):
    """字段错误"""
    field: str
    message: str

class APIResponse(BaseModel, Generic[T]):
    """统一API响应"""
    code: int = 200
    message: str = "success"
    data: Optional[T] = None
    timestamp: datetime = None
    
    def __init__(self, **kwargs):
        if 'timestamp' not in kwargs:
            kwargs['timestamp'] = datetime.utcnow()
        super().__init__(**kwargs)

class ErrorResponse(BaseModel):
    """错误响应"""
    code: int
    message: str
    data: None = None
    errors: Optional[List[FieldError]] = None
    timestamp: datetime = None
    request_id: Optional[str] = None

class PaginatedData(BaseModel, Generic[T]):
    """分页数据"""
    items: List[T]
    pagination: PaginationInfo

def success_response(data: Any = None, message: str = "success") -> APIResponse:
    return APIResponse(code=200, message=message, data=data)

def error_response(
    code: int,
    message: str,
    errors: List[FieldError] = None,
    request_id: str = None
) -> ErrorResponse:
    return ErrorResponse(
        code=code,
        message=message,
        errors=errors,
        request_id=request_id,
        timestamp=datetime.utcnow()
    )
```

---

## 4. 错误码体系

### 4.1 错误码分类

| 错误码范围 | 分类 | 说明 |
|-----------|------|------|
| 10000-19999 | 参数错误 | 请求参数验证失败 |
| 20000-29999 | 认证授权错误 | 登录、权限相关 |
| 30000-39999 | AI服务错误 | AI调用、生成相关 |
| 40000-49999 | 数据库错误 | 数据操作相关 |
| 50000-59999 | 系统错误 | 服务器内部错误 |

### 4.2 详细错误码定义

#### 10xxx - 参数错误

| 错误码 | 错误名称 | HTTP状态码 | 说明 |
|--------|----------|-----------|------|
| 10000 | PARAM_ERROR | 400 | 通用参数错误 |
| 10001 | PARAM_VALIDATION_FAILED | 400 | 参数验证失败 |
| 10002 | PARAM_MISSING | 400 | 缺少必要参数 |
| 10003 | PARAM_TYPE_ERROR | 400 | 参数类型错误 |
| 10004 | PARAM_FORMAT_ERROR | 400 | 参数格式错误 |
| 10005 | PARAM_VALUE_INVALID | 400 | 参数值无效 |
| 10006 | PARAM_LENGTH_EXCEEDED | 400 | 参数长度超限 |
| 10007 | PARAM_DUPLICATE | 400 | 参数重复 |
| 10008 | FILE_TYPE_NOT_ALLOWED | 400 | 文件类型不允许 |
| 10009 | FILE_SIZE_EXCEEDED | 400 | 文件大小超限 |
| 10010 | JSON_PARSE_ERROR | 400 | JSON解析错误 |

#### 20xxx - 认证授权错误

| 错误码 | 错误名称 | HTTP状态码 | 说明 |
|--------|----------|-----------|------|
| 20000 | AUTH_ERROR | 401 | 通用认证错误 |
| 20001 | TOKEN_MISSING | 401 | Token缺失 |
| 20002 | TOKEN_INVALID | 401 | Token无效 |
| 20003 | TOKEN_EXPIRED | 401 | Token已过期 |
| 20004 | TOKEN_REVOKED | 401 | Token已撤销 |
| 20005 | REFRESH_TOKEN_INVALID | 401 | Refresh Token无效 |
| 20006 | REFRESH_TOKEN_EXPIRED | 401 | Refresh Token已过期 |
| 20010 | USER_NOT_FOUND | 404 | 用户不存在 |
| 20011 | PASSWORD_INCORRECT | 401 | 密码错误 |
| 20012 | ACCOUNT_DISABLED | 403 | 账号已禁用 |
| 20013 | ACCOUNT_LOCKED | 403 | 账号已锁定 |
| 20014 | LOGIN_TOO_FREQUENT | 429 | 登录过于频繁 |
| 20015 | VERIFICATION_CODE_INVALID | 400 | 验证码无效 |
| 20016 | VERIFICATION_CODE_EXPIRED | 400 | 验证码已过期 |
| 20020 | PERMISSION_DENIED | 403 | 权限不足 |
| 20021 | RESOURCE_ACCESS_DENIED | 403 | 资源访问被拒绝 |
| 20022 | ROLE_NOT_ALLOWED | 403 | 角色不允许此操作 |
| 20030 | OAUTH_ERROR | 401 | 第三方登录错误 |
| 20031 | WECHAT_AUTH_FAILED | 401 | 微信授权失败 |
| 20032 | DOUYIN_AUTH_FAILED | 401 | 抖音授权失败 |

#### 30xxx - AI服务错误

| 错误码 | 错误名称 | HTTP状态码 | 说明 |
|--------|----------|-----------|------|
| 30000 | AI_ERROR | 500 | 通用AI服务错误 |
| 30001 | AI_SERVICE_UNAVAILABLE | 503 | AI服务不可用 |
| 30002 | AI_REQUEST_TIMEOUT | 504 | AI请求超时 |
| 30003 | AI_RATE_LIMITED | 429 | AI调用频率受限 |
| 30004 | AI_QUOTA_EXCEEDED | 429 | AI配额已用尽 |
| 30005 | AI_CONTENT_FILTERED | 400 | 内容被安全过滤 |
| 30006 | AI_GENERATION_FAILED | 500 | 内容生成失败 |
| 30007 | AI_MODEL_ERROR | 500 | 模型调用错误 |
| 30010 | RAG_RETRIEVAL_FAILED | 500 | RAG检索失败 |
| 30011 | RAG_NO_RELEVANT_DOCS | 404 | 未找到相关文档 |
| 30012 | KNOWLEDGE_BASE_ERROR | 500 | 知识库错误 |
| 30020 | VECTOR_SEARCH_FAILED | 500 | 向量搜索失败 |
| 30021 | EMBEDDING_FAILED | 500 | 向量化失败 |
| 30030 | SENSITIVE_CONTENT_DETECTED | 400 | 检测到敏感内容 |
| 30031 | CONTENT_TOO_LONG | 400 | 内容长度超限 |

#### 40xxx - 数据库错误

| 错误码 | 错误名称 | HTTP状态码 | 说明 |
|--------|----------|-----------|------|
| 40000 | DB_ERROR | 500 | 通用数据库错误 |
| 40001 | DB_CONNECTION_FAILED | 503 | 数据库连接失败 |
| 40002 | DB_QUERY_FAILED | 500 | 数据库查询失败 |
| 40003 | DB_INSERT_FAILED | 500 | 数据插入失败 |
| 40004 | DB_UPDATE_FAILED | 500 | 数据更新失败 |
| 40005 | DB_DELETE_FAILED | 500 | 数据删除失败 |
| 40006 | DB_DUPLICATE_ENTRY | 409 | 数据重复 |
| 40007 | DB_FOREIGN_KEY_ERROR | 409 | 外键约束错误 |
| 40010 | RECORD_NOT_FOUND | 404 | 记录不存在 |
| 40011 | RECORD_ALREADY_EXISTS | 409 | 记录已存在 |
| 40020 | NEO4J_ERROR | 500 | Neo4j错误 |
| 40021 | NEO4J_CONNECTION_FAILED | 503 | Neo4j连接失败 |
| 40030 | REDIS_ERROR | 500 | Redis错误 |
| 40031 | REDIS_CONNECTION_FAILED | 503 | Redis连接失败 |
| 40040 | MILVUS_ERROR | 500 | Milvus错误 |
| 40041 | MILVUS_CONNECTION_FAILED | 503 | Milvus连接失败 |

#### 50xxx - 系统错误

| 错误码 | 错误名称 | HTTP状态码 | 说明 |
|--------|----------|-----------|------|
| 50000 | SYSTEM_ERROR | 500 | 通用系统错误 |
| 50001 | INTERNAL_ERROR | 500 | 内部服务器错误 |
| 50002 | SERVICE_UNAVAILABLE | 503 | 服务不可用 |
| 50003 | SERVICE_TIMEOUT | 504 | 服务超时 |
| 50004 | MAINTENANCE_MODE | 503 | 系统维护中 |
| 50010 | FILE_UPLOAD_FAILED | 500 | 文件上传失败 |
| 50011 | FILE_DOWNLOAD_FAILED | 500 | 文件下载失败 |
| 50012 | OSS_ERROR | 500 | 对象存储错误 |
| 50020 | CELERY_TASK_FAILED | 500 | 异步任务失败 |
| 50021 | TASK_NOT_FOUND | 404 | 任务不存在 |
| 50030 | RATE_LIMIT_EXCEEDED | 429 | 请求频率超限 |
| 50031 | DAILY_LIMIT_EXCEEDED | 429 | 日请求上限 |

### 4.3 错误码Python实现

```python
from enum import IntEnum

class ErrorCode(IntEnum):
    """错误码枚举"""
    
    # 参数错误 10xxx
    PARAM_ERROR = 10000
    PARAM_VALIDATION_FAILED = 10001
    PARAM_MISSING = 10002
    PARAM_TYPE_ERROR = 10003
    PARAM_FORMAT_ERROR = 10004
    PARAM_VALUE_INVALID = 10005
    PARAM_LENGTH_EXCEEDED = 10006
    PARAM_DUPLICATE = 10007
    FILE_TYPE_NOT_ALLOWED = 10008
    FILE_SIZE_EXCEEDED = 10009
    JSON_PARSE_ERROR = 10010
    
    # 认证授权错误 20xxx
    AUTH_ERROR = 20000
    TOKEN_MISSING = 20001
    TOKEN_INVALID = 20002
    TOKEN_EXPIRED = 20003
    TOKEN_REVOKED = 20004
    REFRESH_TOKEN_INVALID = 20005
    REFRESH_TOKEN_EXPIRED = 20006
    USER_NOT_FOUND = 20010
    PASSWORD_INCORRECT = 20011
    ACCOUNT_DISABLED = 20012
    ACCOUNT_LOCKED = 20013
    LOGIN_TOO_FREQUENT = 20014
    VERIFICATION_CODE_INVALID = 20015
    VERIFICATION_CODE_EXPIRED = 20016
    PERMISSION_DENIED = 20020
    RESOURCE_ACCESS_DENIED = 20021
    ROLE_NOT_ALLOWED = 20022
    OAUTH_ERROR = 20030
    WECHAT_AUTH_FAILED = 20031
    DOUYIN_AUTH_FAILED = 20032
    
    # AI服务错误 30xxx
    AI_ERROR = 30000
    AI_SERVICE_UNAVAILABLE = 30001
    AI_REQUEST_TIMEOUT = 30002
    AI_RATE_LIMITED = 30003
    AI_QUOTA_EXCEEDED = 30004
    AI_CONTENT_FILTERED = 30005
    AI_GENERATION_FAILED = 30006
    AI_MODEL_ERROR = 30007
    RAG_RETRIEVAL_FAILED = 30010
    RAG_NO_RELEVANT_DOCS = 30011
    KNOWLEDGE_BASE_ERROR = 30012
    VECTOR_SEARCH_FAILED = 30020
    EMBEDDING_FAILED = 30021
    SENSITIVE_CONTENT_DETECTED = 30030
    CONTENT_TOO_LONG = 30031
    
    # 数据库错误 40xxx
    DB_ERROR = 40000
    DB_CONNECTION_FAILED = 40001
    DB_QUERY_FAILED = 40002
    DB_INSERT_FAILED = 40003
    DB_UPDATE_FAILED = 40004
    DB_DELETE_FAILED = 40005
    DB_DUPLICATE_ENTRY = 40006
    DB_FOREIGN_KEY_ERROR = 40007
    RECORD_NOT_FOUND = 40010
    RECORD_ALREADY_EXISTS = 40011
    NEO4J_ERROR = 40020
    NEO4J_CONNECTION_FAILED = 40021
    REDIS_ERROR = 40030
    REDIS_CONNECTION_FAILED = 40031
    MILVUS_ERROR = 40040
    MILVUS_CONNECTION_FAILED = 40041
    
    # 系统错误 50xxx
    SYSTEM_ERROR = 50000
    INTERNAL_ERROR = 50001
    SERVICE_UNAVAILABLE = 50002
    SERVICE_TIMEOUT = 50003
    MAINTENANCE_MODE = 50004
    FILE_UPLOAD_FAILED = 50010
    FILE_DOWNLOAD_FAILED = 50011
    OSS_ERROR = 50012
    CELERY_TASK_FAILED = 50020
    TASK_NOT_FOUND = 50021
    RATE_LIMIT_EXCEEDED = 50030
    DAILY_LIMIT_EXCEEDED = 50031


# 错误码对应的HTTP状态码映射
ERROR_HTTP_STATUS = {
    ErrorCode.PARAM_ERROR: 400,
    ErrorCode.PARAM_VALIDATION_FAILED: 400,
    ErrorCode.TOKEN_EXPIRED: 401,
    ErrorCode.PERMISSION_DENIED: 403,
    ErrorCode.RECORD_NOT_FOUND: 404,
    ErrorCode.DB_DUPLICATE_ENTRY: 409,
    ErrorCode.AI_QUOTA_EXCEEDED: 429,
    ErrorCode.RATE_LIMIT_EXCEEDED: 429,
    ErrorCode.SYSTEM_ERROR: 500,
    ErrorCode.SERVICE_UNAVAILABLE: 503,
    ErrorCode.SERVICE_TIMEOUT: 504,
    # ... 其他映射
}

# 错误码对应的默认消息
ERROR_MESSAGES = {
    ErrorCode.PARAM_ERROR: "参数错误",
    ErrorCode.PARAM_VALIDATION_FAILED: "参数验证失败",
    ErrorCode.PARAM_MISSING: "缺少必要参数",
    ErrorCode.TOKEN_EXPIRED: "登录已过期，请重新登录",
    ErrorCode.PERMISSION_DENIED: "权限不足",
    ErrorCode.AI_QUOTA_EXCEEDED: "AI配额已用尽，请明日再试或升级套餐",
    ErrorCode.RECORD_NOT_FOUND: "记录不存在",
    # ... 其他消息
}
```

---

## 5. 分页规范

### 5.1 分页参数

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| page | int | 1 | 页码，从1开始 |
| size | int | 20 | 每页数量，最大100 |
| sort_by | string | created_at | 排序字段 |
| sort_order | string | desc | 排序方向：asc/desc |

### 5.2 分页请求示例

```http
GET /api/v1/products?page=1&size=20&sort_by=created_at&sort_order=desc
```

### 5.3 分页响应示例

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "items": [
      {
        "id": "prod_001",
        "name": "乌兰察布马铃薯",
        "category": "蔬菜",
        "region": "乌兰察布市"
      }
    ],
    "pagination": {
      "page": 1,
      "size": 20,
      "total": 37,
      "pages": 2,
      "has_next": true,
      "has_prev": false
    }
  },
  "timestamp": "[项目完成日期]T10:00:00Z"
}
```

### 5.4 分页实现代码

```python
from fastapi import Query
from typing import TypeVar, Generic, List
from pydantic import BaseModel
from sqlalchemy.orm import Query as SQLAlchemyQuery

T = TypeVar("T")

class PaginationParams:
    """分页参数"""
    def __init__(
        self,
        page: int = Query(1, ge=1, description="页码"),
        size: int = Query(20, ge=1, le=100, description="每页数量"),
        sort_by: str = Query("created_at", description="排序字段"),
        sort_order: str = Query("desc", regex="^(asc|desc)$", description="排序方向")
    ):
        self.page = page
        self.size = size
        self.sort_by = sort_by
        self.sort_order = sort_order
    
    @property
    def offset(self) -> int:
        return (self.page - 1) * self.size

def paginate(
    query: SQLAlchemyQuery,
    params: PaginationParams,
    model_class
) -> dict:
    """执行分页查询"""
    # 获取总数
    total = query.count()
    
    # 排序
    sort_column = getattr(model_class, params.sort_by, None)
    if sort_column:
        if params.sort_order == "desc":
            query = query.order_by(sort_column.desc())
        else:
            query = query.order_by(sort_column.asc())
    
    # 分页
    items = query.offset(params.offset).limit(params.size).all()
    
    # 计算分页信息
    pages = (total + params.size - 1) // params.size
    
    return {
        "items": items,
        "pagination": {
            "page": params.page,
            "size": params.size,
            "total": total,
            "pages": pages,
            "has_next": params.page < pages,
            "has_prev": params.page > 1
        }
    }
```

---

## 6. MVP核心接口定义

### 6.1 用户认证接口

#### 6.1.1 用户注册

**接口**: `POST /api/v1/auth/register`

**描述**: 注册新用户账号

**请求头**:
```http
Content-Type: application/json
```

**请求参数**:

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| username | string | 是 | 用户名，3-50字符 |
| email | string | 否 | 邮箱（邮箱和手机号至少填一个） |
| phone | string | 否 | 手机号（邮箱和手机号至少填一个） |
| password | string | 是 | 密码，8-32字符，必须包含字母和数字 |
| user_type | string | 是 | 用户类型：personal/enterprise |
| verification_code | string | 是 | 验证码 |
| enterprise_name | string | 条件必填 | 企业名称（企业用户必填） |
| enterprise_license | string | 条件必填 | 营业执照号（企业用户必填） |

**请求示例**:

```json
{
  "username": "zhangsan",
  "email": "zhangsan@example.com",
  "phone": "13800138000",
  "password": "Password123",
  "user_type": "enterprise",
  "verification_code": "123456",
  "enterprise_name": "内蒙古草原牧业有限公司",
  "enterprise_license": "91150100MA0N1234X5"
}
```

**响应示例（成功）**:

```json
{
  "code": 200,
  "message": "注册成功",
  "data": {
    "user_id": "user_123456",
    "username": "zhangsan",
    "email": "zhangsan@example.com",
    "user_type": "enterprise",
    "created_at": "[项目完成日期]T10:00:00Z"
  },
  "timestamp": "[项目完成日期]T10:00:00Z"
}
```

**响应示例（失败）**:

```json
{
  "code": 10001,
  "message": "参数验证失败",
  "data": null,
  "errors": [
    {
      "field": "email",
      "message": "该邮箱已被注册"
    }
  ],
  "timestamp": "[项目完成日期]T10:00:00Z"
}
```

**错误码**:

| 错误码 | 说明 |
|--------|------|
| 10001 | 参数验证失败 |
| 20015 | 验证码无效 |
| 20016 | 验证码已过期 |
| 40011 | 用户名/邮箱/手机号已存在 |


---

#### 6.3.3 产品智能搜索

**接口**: POST /api/v1/products/search

**描述**: 使用向量语义搜索产品

**请求参数**:

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| query | string | 是 | 搜索查询文本 |
| search_type | string | 否 | 搜索类型：keyword/semantic/hybrid，默认hybrid |
| filters | object | 否 | 筛选条件 |
| top_k | int | 否 | 返回结果数量，默认10，最大50 |
| include_score | boolean | 否 | 是否返回相似度分数，默认false |

**请求示例**:

**响应示例**:

---

### 6.4 内容生成接口

#### 6.4.1 生成营销内容

**接口**: POST /api/v1/content/generate

**描述**: 生成产品营销内容（文案、脚本等）

**请求参数**:

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| product_id | string | 是 | 产品ID |
| content_type | string | 是 | 内容类型：copy/script/video_copy |
| platform | string | 是 | 目标平台：douyin/xiaohongshu/wechat/weibo |
| style | string | 否 | 风格：formal/casual/humorous/emotional |
| length | string | 否 | 长度：short/medium/long |
| keywords | array | 否 | 要包含的关键词 |

**请求示例**:

**响应示例**:

#### 6.4.2 获取生成记录

**接口**: GET /api/v1/content/{id}

**描述**: 获取单条内容生成记录

#### 6.4.3 批量生成内容

**接口**: POST /api/v1/content/batch

**描述**: 批量生成多个产品的营销内容（异步任务）

---

### 6.5 用户管理接口

#### 6.5.1 获取用户信息

**接口**: GET /api/v1/users/profile

**描述**: 获取当前登录用户的详细信息

#### 6.5.2 获取用户配额

**接口**: GET /api/v1/users/quota

**描述**: 获取当前用户的配额使用情况

---

## 7. 附录

### 7.1 HTTP状态码使用规范

| 状态码 | 说明 | 使用场景 |
|--------|------|----------|
| 200 | OK | 请求成功 |
| 201 | Created | 资源创建成功 |
| 204 | No Content | 删除成功 |
| 400 | Bad Request | 参数错误 |
| 401 | Unauthorized | 未认证 |
| 403 | Forbidden | 无权限 |
| 404 | Not Found | 资源不存在 |
| 409 | Conflict | 资源冲突 |
| 429 | Too Many Requests | 请求过于频繁 |
| 500 | Internal Server Error | 服务器内部错误 |
| 503 | Service Unavailable | 服务不可用 |

### 7.2 接口版本演进记录

| 版本 | 发布日期 | 主要变更 |
|------|----------|----------|
| v1.0 | [项目完成日期] | 初始版本，包含MVP核心接口 |

---

**文档版本**: v1.0  
**最后更新**: [项目完成日期]  
**维护者**: AI赋能云平台技术团队
