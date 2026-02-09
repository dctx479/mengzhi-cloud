# 错误码文档

**完整的错误码列表和说明**

版本: v1.0
更新日期: [项目完成日期]

---

## 目录

- [错误码体系](#错误码体系)
- [参数错误 (10xxx)](#参数错误-10xxx)
- [认证授权错误 (20xxx)](#认证授权错误-20xxx)
- [数据库错误 (40xxx)](#数据库错误-40xxx)
- [系统错误 (50xxx)](#系统错误-50xxx)
- [HTTP状态码映射](#http状态码映射)
- [错误处理最佳实践](#错误处理最佳实践)

---

## 错误码体系

### 分类规则

| 范围 | 分类 | 说明 |
|------|------|------|
| 200 | 成功 | 请求成功 |
| 10xxx | 参数错误 | 请求参数验证失败 |
| 20xxx | 认证授权错误 | 身份验证或权限问题 |
| 40xxx | 数据库错误 | 数据库操作失败 |
| 50xxx | 系统错误 | 服务器内部错误 |

### 响应格式

```json
{
  "code": 10001,
  "message": "参数验证失败",
  "data": null,
  "errors": [
    {
      "field": "email",
      "message": "邮箱格式不正确"
    }
  ],
  "timestamp": "[项目完成日期]T10:00:00",
  "request_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

---

## 参数错误 (10xxx)

### 10000 - 参数错误

**HTTP状态码**: 400 Bad Request

**说明**: 通用参数错误

**常见原因**:
- 参数类型不匹配
- 参数值不在允许范围内
- 请求体为空

**示例**:
```json
{
  "code": 10000,
  "message": "参数错误",
  "data": null
}
```

**解决方法**:
- 检查请求参数类型
- 验证参数值是否符合要求
- 确保必填参数不为空

---

### 10001 - 参数验证失败

**HTTP状态码**: 400 Bad Request

**说明**: Pydantic模型验证失败

**常见原因**:
- 字段格式不正确
- 字段长度超限
- 自定义验证规则不通过

**示例**:
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
      "message": "密码必须同时包含字母和数字"
    }
  ]
}
```

**解决方法**:
- 查看errors字段获取具体错误
- 修正对应字段的值
- 参考API文档中的参数说明

---

### 10002 - 缺少必要参数

**HTTP状态码**: 400 Bad Request

**说明**: 必填参数未提供

**示例**:
```json
{
  "code": 10002,
  "message": "缺少必要参数",
  "data": null,
  "errors": [
    {
      "field": "username",
      "message": "用户名为必填项"
    }
  ]
}
```

---

### 10003 - 参数类型错误

**HTTP状态码**: 400 Bad Request

**说明**: 参数类型不匹配

**示例**:
```json
{
  "code": 10003,
  "message": "参数类型错误",
  "data": null,
  "errors": [
    {
      "field": "price",
      "message": "价格必须为数字类型"
    }
  ]
}
```

---

### 10004 - 参数格式错误

**HTTP状态码**: 400 Bad Request

**说明**: 参数格式不符合要求

**常见场景**:
- 邮箱格式不正确
- 手机号格式不正确
- 日期格式不正确

---

### 10005 - 参数值无效

**HTTP状态码**: 400 Bad Request

**说明**: 参数值不在允许的范围内

**示例**:
```json
{
  "code": 10005,
  "message": "参数值无效",
  "data": null,
  "errors": [
    {
      "field": "sort_by",
      "message": "排序字段必须为: created_at, price, name, updated_at"
    }
  ]
}
```

---

### 10006 - 参数长度超限

**HTTP状态码**: 400 Bad Request

**说明**: 参数长度超过最大限制

---

### 10007 - 参数重复

**HTTP状态码**: 400 Bad Request

**说明**: 参数值重复（如用户名已存在）

---

### 10008 - 文件类型不允许

**HTTP状态码**: 400 Bad Request

**说明**: 上传文件类型不在允许列表中

---

### 10009 - 文件大小超限

**HTTP状态码**: 400 Bad Request

**说明**: 上传文件超过大小限制

---

### 10010 - JSON解析错误

**HTTP状态码**: 400 Bad Request

**说明**: 请求体JSON格式错误

**示例**:
```json
{
  "code": 10010,
  "message": "JSON解析错误",
  "data": null
}
```

---

## 认证授权错误 (20xxx)

### 20000 - 认证错误

**HTTP状态码**: 401 Unauthorized

**说明**: 通用认证错误

---

### 20001 - Token缺失

**HTTP状态码**: 401 Unauthorized

**说明**: 未提供认证令牌

**示例**:
```json
{
  "code": 20001,
  "message": "未提供认证令牌",
  "data": null
}
```

**解决方法**:
```bash
# 添加Authorization Header
curl -H "Authorization: Bearer {access_token}" ...
```

---

### 20002 - Token无效

**HTTP状态码**: 401 Unauthorized

**说明**: 认证令牌无效

**常见原因**:
- Token格式错误
- Token签名验证失败
- Token被篡改

**解决方法**:
- 重新登录获取新Token
- 检查Token格式是否正确

---

### 20003 - Token已过期

**HTTP状态码**: 401 Unauthorized

**说明**: 认证令牌已过期

**示例**:
```json
{
  "code": 20003,
  "message": "认证令牌已过期，请重新登录",
  "data": null
}
```

**解决方法**:
- 使用refresh_token刷新Token
- 重新登录

**自动刷新示例**:
```javascript
async function refreshToken() {
  const refreshToken = localStorage.getItem('refresh_token');

  const response = await fetch('/api/v1/auth/refresh', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ refresh_token: refreshToken })
  });

  const data = await response.json();

  if (data.code === 200) {
    localStorage.setItem('access_token', data.data.access_token);
    localStorage.setItem('refresh_token', data.data.refresh_token);
    return true;
  }

  return false;
}
```

---

### 20004 - Token已被撤销

**HTTP状态码**: 401 Unauthorized

**说明**: 认证令牌已被加入黑名单

**常见原因**:
- 用户已登出
- 管理员强制下线
- 安全策略撤销

---

### 20005 - Refresh Token无效

**HTTP状态码**: 401 Unauthorized

**说明**: 刷新令牌无效

---

### 20006 - Refresh Token已过期

**HTTP状态码**: 401 Unauthorized

**说明**: 刷新令牌已过期（超过7天）

**解决方法**:
- 重新登录

---

### 20010 - 用户不存在

**HTTP状态码**: 404 Not Found

**说明**: 指定用户不存在

**示例**:
```json
{
  "code": 20010,
  "message": "用户不存在",
  "data": null
}
```

---

### 20011 - 密码错误

**HTTP状态码**: 401 Unauthorized

**说明**: 密码不正确

**注意事项**:
- 密码错误5次后账号会被锁定30分钟
- 锁定期间无法登录

---

### 20012 - 账号已禁用

**HTTP状态码**: 403 Forbidden

**说明**: 账号已被管理员禁用

**解决方法**:
- 联系管理员解除禁用

---

### 20013 - 账号已锁定

**HTTP状态码**: 403 Forbidden

**说明**: 账号已锁定（密码错误次数过多）

**示例**:
```json
{
  "code": 20013,
  "message": "账号已锁定，请稍后再试",
  "data": null
}
```

**解决方法**:
- 等待30分钟后自动解锁
- 联系管理员手动解锁

---

### 20014 - 登录过于频繁

**HTTP状态码**: 429 Too Many Requests

**说明**: 登录请求过于频繁

**解决方法**:
- 等待一段时间后重试

---

### 20015 - 验证码无效

**HTTP状态码**: 400 Bad Request

**说明**: 验证码不正确

---

### 20016 - 验证码已过期

**HTTP状态码**: 400 Bad Request

**说明**: 验证码已超过有效期（通常5分钟）

---

### 20020 - 权限不足

**HTTP状态码**: 403 Forbidden

**说明**: 当前用户无权执行此操作

**示例**:
```json
{
  "code": 20020,
  "message": "权限不足",
  "data": null
}
```

**常见场景**:
- 非管理员访问管理接口
- 访问其他用户的私有数据

---

### 20021 - 资源访问被拒绝

**HTTP状态码**: 403 Forbidden

**说明**: 无权访问该资源

---

### 20022 - 角色不允许

**HTTP状态码**: 403 Forbidden

**说明**: 当前角色不允许执行此操作

---

## 数据库错误 (40xxx)

### 40000 - 数据库错误

**HTTP状态码**: 500 Internal Server Error

**说明**: 通用数据库错误

---

### 40001 - 数据库连接失败

**HTTP状态码**: 503 Service Unavailable

**说明**: 无法连接到数据库

---

### 40002 - 数据库查询失败

**HTTP状态码**: 500 Internal Server Error

**说明**: SQL查询执行失败

---

### 40003 - 数据库插入失败

**HTTP状态码**: 500 Internal Server Error

**说明**: 数据插入失败

---

### 40004 - 数据库更新失败

**HTTP状态码**: 500 Internal Server Error

**说明**: 数据更新失败

---

### 40005 - 数据库删除失败

**HTTP状态码**: 500 Internal Server Error

**说明**: 数据删除失败

---

### 40006 - 数据库重复条目

**HTTP状态码**: 409 Conflict

**说明**: 违反唯一约束

**常见场景**:
- SKU重复
- 用户名重复

---

### 40010 - 记录不存在

**HTTP状态码**: 404 Not Found

**说明**: 指定记录不存在

**示例**:
```json
{
  "code": 40010,
  "message": "记录不存在",
  "data": null
}
```

---

### 40011 - 记录已存在

**HTTP状态码**: 409 Conflict

**说明**: 记录已存在（如用户名/邮箱/手机号已被注册）

**示例**:
```json
{
  "code": 40011,
  "message": "用户名/邮箱/手机号已被注册",
  "data": null,
  "errors": [
    {
      "field": "username",
      "message": "该用户名已被注册"
    }
  ]
}
```

---

## 系统错误 (50xxx)

### 50000 - 系统错误

**HTTP状态码**: 500 Internal Server Error

**说明**: 通用系统错误

**示例**:
```json
{
  "code": 50000,
  "message": "系统错误，请稍后再试",
  "data": null,
  "request_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

**解决方法**:
- 记录request_id
- 联系技术支持
- 稍后重试

---

### 50001 - 内部错误

**HTTP状态码**: 500 Internal Server Error

**说明**: 服务器内部错误

---

### 50002 - 服务不可用

**HTTP状态码**: 503 Service Unavailable

**说明**: 服务暂时不可用

**常见原因**:
- 服务器维护
- 负载过高
- 依赖服务不可用

---

## HTTP状态码映射

| 错误码 | HTTP状态码 | 说明 |
|--------|-----------|------|
| 200 | 200 | 成功 |
| 10000-10999 | 400 | 参数错误 |
| 20001-20002 | 401 | 未授权 |
| 20003 | 401 | Token过期 |
| 20012-20013 | 403 | 禁止访问 |
| 20020-20022 | 403 | 权限不足 |
| 20010 | 404 | 用户不存在 |
| 40010 | 404 | 记录不存在 |
| 40006 | 409 | 数据重复 |
| 40011 | 409 | 记录已存在 |
| 20014 | 429 | 请求过于频繁 |
| 50000-50001 | 500 | 服务器错误 |
| 40001 | 503 | 数据库连接失败 |
| 50002 | 503 | 服务不可用 |

---

## 错误处理最佳实践

### 1. 客户端错误处理

#### JavaScript示例

```javascript
async function apiCall(url, options = {}) {
  try {
    const response = await fetch(url, options);
    const data = await response.json();

    // 检查业务错误码
    if (data.code !== 200) {
      // Token过期，自动刷新
      if (data.code === 20003) {
        const refreshed = await refreshToken();
        if (refreshed) {
          // 重试请求
          return apiCall(url, options);
        } else {
          // 刷新失败，跳转登录
          redirectToLogin();
        }
      }

      // 参数验证错误，显示具体字段错误
      if (data.code === 10001 && data.errors) {
        data.errors.forEach(error => {
          showFieldError(error.field, error.message);
        });
      } else {
        // 显示通用错误消息
        showError(data.message);
      }

      throw new Error(data.message);
    }

    return data.data;
  } catch (error) {
    // 网络错误
    if (error instanceof TypeError) {
      showError('网络连接失败，请检查网络');
    }
    throw error;
  }
}
```

#### Python示例

```python
import requests
from typing import Dict, Any

class APIError(Exception):
    def __init__(self, code: int, message: str, errors: list = None):
        self.code = code
        self.message = message
        self.errors = errors
        super().__init__(message)

def api_call(url: str, **kwargs) -> Dict[str, Any]:
    try:
        response = requests.request(**kwargs, url=url)
        data = response.json()

        if data['code'] != 200:
            # Token过期，自动刷新
            if data['code'] == 20003:
                refresh_token()
                # 重试请求
                return api_call(url, **kwargs)

            # 抛出业务异常
            raise APIError(
                code=data['code'],
                message=data['message'],
                errors=data.get('errors')
            )

        return data['data']

    except requests.RequestException as e:
        raise APIError(50000, '网络请求失败')
```

### 2. 错误日志记录

```javascript
// 记录详细错误信息
function logError(error, context = {}) {
  console.error({
    timestamp: new Date().toISOString(),
    code: error.code,
    message: error.message,
    request_id: error.request_id,
    context: context,
    stack: error.stack
  });

  // 发送到错误追踪服务（如Sentry）
  if (window.Sentry) {
    Sentry.captureException(error, {
      extra: context
    });
  }
}
```

### 3. 用户友好的错误提示

```javascript
// 将错误码转换为用户友好的消息
const ERROR_MESSAGES = {
  10001: '您输入的信息有误，请检查后重试',
  20003: '登录已过期，请重新登录',
  20011: '密码错误，请重试',
  20013: '账号已被锁定，请30分钟后再试',
  40010: '数据不存在',
  50000: '系统繁忙，请稍后重试'
};

function showUserFriendlyError(code) {
  const message = ERROR_MESSAGES[code] || '操作失败，请稍后重试';
  alert(message);
}
```

### 4. 错误重试策略

```javascript
// 自动重试（适用于网络错误或服务不可用）
async function retryableApiCall(url, options, maxRetries = 3) {
  for (let i = 0; i < maxRetries; i++) {
    try {
      return await apiCall(url, options);
    } catch (error) {
      // 最后一次重试失败，抛出错误
      if (i === maxRetries - 1) {
        throw error;
      }

      // 只重试特定错误
      if (error.code === 50002 || error.code === 40001) {
        // 指数退避
        const delay = Math.pow(2, i) * 1000;
        await new Promise(resolve => setTimeout(resolve, delay));
      } else {
        // 其他错误不重试
        throw error;
      }
    }
  }
}
```

---

## 常见问题

### Q: 为什么会返回200状态码但code不是200？

A: HTTP状态码表示请求本身是否成功，code表示业务逻辑是否成功。例如参数验证失败会返回HTTP 400，但业务code可能是10001。

### Q: 如何区分哪些错误需要重试？

A:
- 50002（服务不可用）: 应该重试
- 40001（数据库连接失败）: 应该重试
- 10001（参数验证失败）: 不应重试，修正参数
- 20003（Token过期）: 刷新Token后重试
- 20011（密码错误）: 不应重试，提示用户

### Q: errors字段什么时候有值？

A: 参数验证失败（code=10001）时，errors字段包含具体的字段错误列表。

---

**文档版本**: v1.0
**最后更新**: [项目完成日期]
**维护团队**: AI赋能云平台技术团队
