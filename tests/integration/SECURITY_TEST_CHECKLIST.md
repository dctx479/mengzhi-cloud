# 安全测试检查清单

## 文档信息
- **版本**: 1.0
- **创建日期**: [项目完成日期]
- **测试类型**: 安全性测试
- **风险等级**: P0 (高危), P1 (中危), P2 (低危)

## 目录
1. [认证安全](#认证安全)
2. [授权安全](#授权安全)
3. [输入验证](#输入验证)
4. [数据安全](#数据安全)
5. [API安全](#api安全)
6. [会话管理](#会话管理)
7. [文件上传安全](#文件上传安全)
8. [配置安全](#配置安全)

---

## 认证安全

### AUTH-SEC-001: 密码强度验证
**风险等级**: P0

| 测试项 | 测试方法 | 期望结果 | 状态 |
|--------|---------|---------|------|
| 最小长度 | 注册时使用6位密码 | 拒绝，提示至少8位 | ⏳ |
| 复杂度要求 | 使用纯数字密码 | 拒绝，要求包含字母+数字+特殊字符 | ⏳ |
| 常见密码 | 使用"password123" | 拒绝，提示密码过于简单 | ⏳ |
| 用户名相似 | 密码包含用户名 | 拒绝或警告 | ⏳ |

**测试脚本**:
```python
# 测试弱密码
weak_passwords = [
    "123456",           # 纯数字
    "password",         # 纯字母
    "abc123",           # 过短
    "qwerty123",        # 常见密码
]

for pwd in weak_passwords:
    response = requests.post("/api/v1/auth/register", json={
        "email": "test@example.com",
        "password": pwd,
        "username": "testuser"
    })
    assert response.status_code == 400
```

### AUTH-SEC-002: 密码存储安全
**风险等级**: P0

| 测试项 | 测试方法 | 期望结果 | 状态 |
|--------|---------|---------|------|
| 密码加密 | 查看数据库密码字段 | 使用bcrypt/argon2加密 | ⏳ |
| 盐值使用 | 检查相同密码的哈希 | 每个用户盐值不同 | ⏳ |
| 明文禁止 | 搜索日志和数据库 | 无明文密码 | ⏳ |

**验证方法**:
```sql
-- 检查密码字段
SELECT id, email, password FROM users LIMIT 5;
-- 密码应该是哈希值，如: $2b$12$...

-- 检查相同密码的哈希是否不同
SELECT password FROM users WHERE email IN ('user1@test.com', 'user2@test.com');
```

### AUTH-SEC-003: 登录失败处理
**风险等级**: P0

| 测试项 | 测试方法 | 期望结果 | 状态 |
|--------|---------|---------|------|
| 错误消息 | 使用错误密码登录 | 不泄露用户是否存在 | ⏳ |
| 登录限流 | 连续失败5次 | 账号临时锁定或验证码 | ⏳ |
| 暴力破解防护 | 使用脚本快速尝试 | IP限流或封禁 | ⏳ |
| 失败日志 | 查看日志 | 记录失败尝试 | ⏳ |

**测试脚本**:
```python
# 测试登录限流
for i in range(10):
    response = requests.post("/api/v1/auth/login", json={
        "email": "test@example.com",
        "password": "WrongPassword123!"
    })
    print(f"尝试 {i+1}: {response.status_code}")
    if response.status_code == 429:
        print("✓ 限流生效")
        break
```

### AUTH-SEC-004: Token安全
**风险等级**: P0

| 测试项 | 测试方法 | 期望结果 | 状态 |
|--------|---------|---------|------|
| Token签名 | 修改Token内容 | 验证失败 | ⏳ |
| Token过期 | 使用过期Token | 401错误 | ⏳ |
| Token刷新 | 刷新Token机制 | 正确生成新Token | ⏳ |
| Token撤销 | 登出后使用Token | 401错误 | ⏳ |

**测试脚本**:
```python
# 测试Token篡改
token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
tampered_token = token[:-10] + "XXXXXXXXXX"

response = requests.get("/api/v1/auth/verify",
    headers={"Authorization": f"Bearer {tampered_token}"})
assert response.status_code == 401
```

---

## 授权安全

### AUTHZ-SEC-001: 权限验证
**风险等级**: P0

| 测试项 | 测试方法 | 期望结果 | 状态 |
|--------|---------|---------|------|
| 未授权访问 | 普通用户访问管理端点 | 403 Forbidden | ⏳ |
| 越权访问 | 用户A访问用户B的数据 | 403 Forbidden | ⏳ |
| 角色验证 | 检查RBAC实现 | 正确验证角色权限 | ⏳ |
| 权限缓存 | 修改权限后测试 | 权限立即生效 | ⏳ |

**测试脚本**:
```python
# 测试越权访问
user_a_token = login("usera@test.com", "password")
user_b_id = get_user_id("userb@test.com")

# 用户A尝试访问用户B的对话
response = requests.get(f"/api/v1/chat/conversations/{user_b_conversation_id}",
    headers={"Authorization": f"Bearer {user_a_token}"})
assert response.status_code == 403
```

### AUTHZ-SEC-002: 资源访问控制
**风险等级**: P0

| 测试项 | 测试方法 | 期望结果 | 状态 |
|--------|---------|---------|------|
| 对话隔离 | 访问他人对话 | 403错误 | ⏳ |
| 内容隔离 | 访问他人生成内容 | 403错误 | ⏳ |
| 产品管理 | 普通用户创建产品 | 403错误 | ⏳ |
| 用户管理 | 非管理员管理用户 | 403错误 | ⏳ |

---

## 输入验证

### INPUT-SEC-001: SQL注入防护
**风险等级**: P0

| 测试项 | 测试方法 | 期望结果 | 状态 |
|--------|---------|---------|------|
| 搜索框注入 | 输入`' OR '1'='1` | 参数化查询，无注入 | ⏳ |
| 登录注入 | 邮箱输入SQL语句 | 正确转义，无注入 | ⏳ |
| 排序注入 | sort_by参数注入 | 白名单验证 | ⏳ |
| 批量操作注入 | IDs数组注入 | 类型验证 | ⏳ |

**测试脚本**:
```python
# SQL注入测试
sql_payloads = [
    "' OR '1'='1",
    "'; DROP TABLE users; --",
    "1' UNION SELECT * FROM users--",
    "admin'--",
]

for payload in sql_payloads:
    response = requests.get("/api/v1/products", params={
        "search": payload
    })
    # 应该返回空结果或错误，不应该执行SQL
    assert response.status_code in [200, 400]
    if response.status_code == 200:
        data = response.json()
        # 不应该返回所有产品
        assert len(data.get("data", {}).get("items", [])) < 100
```

### INPUT-SEC-002: XSS防护
**风险等级**: P0

| 测试项 | 测试方法 | 期望结果 | 状态 |
|--------|---------|---------|------|
| 存储型XSS | 产品名称输入`<script>alert(1)</script>` | HTML转义 | ⏳ |
| 反射型XSS | URL参数包含脚本 | 正确转义 | ⏳ |
| DOM型XSS | 前端渲染用户输入 | 使用安全API | ⏳ |
| Markdown注入 | 对话内容包含恶意Markdown | 安全渲染 | ⏳ |

**测试脚本**:
```python
# XSS测试
xss_payloads = [
    "<script>alert('XSS')</script>",
    "<img src=x onerror=alert('XSS')>",
    "javascript:alert('XSS')",
    "<svg onload=alert('XSS')>",
]

for payload in xss_payloads:
    response = requests.post("/api/v1/products",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={
            "name": payload,
            "sku": "TEST-001",
            "category": "测试",
            "price": 99.99
        })

    if response.status_code == 201:
        product_id = response.json()["data"]["id"]
        # 获取产品详情
        detail = requests.get(f"/api/v1/products/{product_id}")
        # 检查是否正确转义
        assert "<script>" not in detail.text
```

### INPUT-SEC-003: 命令注入防护
**风险等级**: P0

| 测试项 | 测试方法 | 期望结果 | 状态 |
|--------|---------|---------|------|
| 文件名注入 | 上传文件名包含`;ls` | 正确验证 | ⏳ |
| 路径遍历 | 文件路径包含`../` | 拒绝访问 | ⏳ |
| 模板注入 | 内容模板包含`{{7*7}}` | 不执行代码 | ⏳ |

---

## 数据安全

### DATA-SEC-001: 敏感数据保护
**风险等级**: P0

| 测试项 | 测试方法 | 期望结果 | 状态 |
|--------|---------|---------|------|
| 密码不返回 | 获取用户信息 | 响应不包含密码 | ⏳ |
| Token不记录 | 查看日志 | 日志不包含完整Token | ⏳ |
| API密钥保护 | 查看配置 | 使用环境变量 | ⏳ |
| 数据库加密 | 检查敏感字段 | 加密存储 | ⏳ |

**验证方法**:
```python
# 检查用户信息响应
response = requests.get("/api/v1/users/me",
    headers={"Authorization": f"Bearer {token}"})
data = response.json()
assert "password" not in str(data)
assert "password_hash" not in str(data)
```

### DATA-SEC-002: 数据传输安全
**风险等级**: P0

| 测试项 | 测试方法 | 期望结果 | 状态 |
|--------|---------|---------|------|
| HTTPS强制 | 访问HTTP端点 | 重定向到HTTPS | ⏳ |
| TLS版本 | 检查TLS配置 | TLS 1.2+ | ⏳ |
| 敏感头部 | 检查响应头 | 包含安全头部 | ⏳ |

**检查命令**:
```bash
# 检查TLS版本
openssl s_client -connect localhost:443 -tls1_2

# 检查安全头部
curl -I https://localhost:443
# 应该包含:
# Strict-Transport-Security
# X-Content-Type-Options
# X-Frame-Options
# Content-Security-Policy
```

---

## API安全

### API-SEC-001: CORS配置
**风险等级**: P1

| 测试项 | 测试方法 | 期望结果 | 状态 |
|--------|---------|---------|------|
| 允许来源 | 检查CORS配置 | 白名单模式 | ⏳ |
| 凭证处理 | 跨域请求携带Cookie | 正确配置 | ⏳ |
| 预检请求 | OPTIONS请求 | 正确响应 | ⏳ |

**测试脚本**:
```python
# 测试CORS
response = requests.options("/api/v1/products",
    headers={
        "Origin": "http://evil.com",
        "Access-Control-Request-Method": "GET"
    })

# 检查是否拒绝恶意来源
assert "http://evil.com" not in response.headers.get("Access-Control-Allow-Origin", "")
```

### API-SEC-002: 速率限制
**风险等级**: P1

| 测试项 | 测试方法 | 期望结果 | 状态 |
|--------|---------|---------|------|
| 全局限流 | 快速发送100个请求 | 429错误 | ⏳ |
| 端点限流 | 登录端点限流 | 5次失败后限制 | ⏳ |
| IP限流 | 同IP大量请求 | 临时封禁 | ⏳ |
| 用户限流 | 单用户大量请求 | 配额限制 | ⏳ |

**测试脚本**:
```python
# 测试速率限制
import asyncio
import httpx

async def test_rate_limit():
    async with httpx.AsyncClient() as client:
        tasks = [
            client.get("http://localhost:8000/api/v1/products")
            for _ in range(100)
        ]
        responses = await asyncio.gather(*tasks)

        # 检查是否有429响应
        status_codes = [r.status_code for r in responses]
        assert 429 in status_codes, "速率限制未生效"

asyncio.run(test_rate_limit())
```

### API-SEC-003: 请求验证
**风险等级**: P1

| 测试项 | 测试方法 | 期望结果 | 状态 |
|--------|---------|---------|------|
| Content-Type验证 | 发送错误类型 | 415错误 | ⏳ |
| 请求大小限制 | 发送超大请求 | 413错误 | ⏳ |
| 参数类型验证 | 发送错误类型参数 | 422错误 | ⏳ |
| 必填字段验证 | 缺少必填字段 | 422错误 | ⏳ |

---

## 会话管理

### SESSION-SEC-001: 会话安全
**风险等级**: P0

| 测试项 | 测试方法 | 期望结果 | 状态 |
|--------|---------|---------|------|
| 会话超时 | Token过期时间 | 合理的超时时间 | ⏳ |
| 会话固定 | 登录前后Token不同 | 登录后生成新Token | ⏳ |
| 并发会话 | 多设备登录 | 支持或限制 | ⏳ |
| 会话撤销 | 登出后Token失效 | 无法继续使用 | ⏳ |

---

## 文件上传安全

### FILE-SEC-001: 文件上传验证
**风险等级**: P0

| 测试项 | 测试方法 | 期望结果 | 状态 |
|--------|---------|---------|------|
| 文件类型验证 | 上传.exe文件 | 拒绝 | ⏳ |
| 文件大小限制 | 上传100MB文件 | 拒绝 | ⏳ |
| 文件名验证 | 文件名包含`../` | 拒绝或清理 | ⏳ |
| 病毒扫描 | 上传恶意文件 | 检测并拒绝 | ⏳ |
| 图片验证 | 上传伪装的图片 | 验证真实格式 | ⏳ |

**测试脚本**:
```python
# 测试文件类型验证
malicious_files = [
    ("test.exe", b"MZ\x90\x00", "application/x-msdownload"),
    ("test.php", b"<?php system($_GET['cmd']); ?>", "application/x-php"),
    ("test.jsp", b"<% Runtime.getRuntime().exec(request.getParameter(\"cmd\")); %>", "text/plain"),
]

for filename, content, content_type in malicious_files:
    files = {"file": (filename, content, content_type)}
    response = requests.post("/api/v1/media/upload",
        headers={"Authorization": f"Bearer {token}"},
        files=files)
    assert response.status_code in [400, 415], f"应该拒绝 {filename}"
```

---

## 配置安全

### CONFIG-SEC-001: 配置安全
**风险等级**: P0

| 测试项 | 测试方法 | 期望结果 | 状态 |
|--------|---------|---------|------|
| 调试模式 | 检查生产配置 | DEBUG=False | ⏳ |
| 错误信息 | 触发错误 | 不泄露敏感信息 | ⏳ |
| 默认密钥 | 检查SECRET_KEY | 不使用默认值 | ⏳ |
| 环境变量 | 检查配置文件 | 敏感信息用环境变量 | ⏳ |

**检查清单**:
```bash
# 检查配置文件
grep -r "DEBUG.*=.*True" backend/
grep -r "SECRET_KEY.*=.*'secret'" backend/
grep -r "password.*=.*'password'" backend/

# 检查环境变量
env | grep -i "key\|secret\|password"
```

---

## 测试执行

### 自动化安全测试

```python
# security_tests.py
import requests

BASE_URL = "http://localhost:8000"

def test_sql_injection():
    """测试SQL注入"""
    payloads = ["' OR '1'='1", "'; DROP TABLE users; --"]
    for payload in payloads:
        response = requests.get(f"{BASE_URL}/api/v1/products",
            params={"search": payload})
        assert response.status_code in [200, 400]

def test_xss():
    """测试XSS"""
    payload = "<script>alert('XSS')</script>"
    # 测试各个输入点
    pass

def test_authentication():
    """测试认证安全"""
    # 测试弱密码
    # 测试登录限流
    # 测试Token安全
    pass

if __name__ == "__main__":
    test_sql_injection()
    test_xss()
    test_authentication()
    print("✓ 所有安全测试通过")
```

### 手动安全测试

1. **使用Burp Suite**
   - 拦截和修改请求
   - 测试各种注入攻击
   - 检查响应头

2. **使用OWASP ZAP**
   - 自动扫描漏洞
   - 生成安全报告

3. **使用SQLMap**
   - 测试SQL注入
   ```bash
   sqlmap -u "http://localhost:8000/api/v1/products?search=test" --batch
   ```

---

## 安全测试报告模板

### 安全测试报告

**测试日期**: [项目完成日期]
**测试人员**: [姓名]
**测试范围**: 全系统安全测试

#### 测试摘要
- 总测试项: 50
- 通过: 45
- 失败: 3
- 跳过: 2

#### 高危漏洞 (P0)
| 编号 | 漏洞描述 | 影响 | 状态 |
|------|---------|------|------|
| SEC-001 | SQL注入漏洞 | 数据泄露 | ❌ 未修复 |

#### 中危漏洞 (P1)
| 编号 | 漏洞描述 | 影响 | 状态 |
|------|---------|------|------|
| SEC-010 | CORS配置过于宽松 | 跨域攻击 | ⚠️ 待修复 |

#### 低危漏洞 (P2)
| 编号 | 漏洞描述 | 影响 | 状态 |
|------|---------|------|------|
| SEC-020 | 缺少安全响应头 | 信息泄露 | ✅ 已修复 |

#### 修复建议
1. 立即修复所有P0漏洞
2. 1周内修复P1漏洞
3. 1个月内修复P2漏洞

---

**文档版本**: 1.0
**最后更新**: [项目完成日期]
