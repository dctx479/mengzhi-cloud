---

## 4. 访问控制

### 4.1 RBAC权限模型

#### 4.1.1 角色定义

| 角色 | 代码 | 说明 | 权限范围 |
|------|------|------|----------|
| 系统管理员 | admin | 平台管理员 | 全部权限 |
| 企业管理员 | enterprise_admin | 企业管理者 | 企业内全部权限 |
| 企业成员 | enterprise_user | 企业普通成员 | 企业内操作权限 |
| 个人用户 | personal_user | 个人注册用户 | 个人数据权限 |
| 访客 | guest | 未登录用户 | 公开数据只读 |

#### 4.1.2 权限矩阵

| 资源 | admin | enterprise_admin | enterprise_user | personal_user | guest |
|------|-------|------------------|-----------------|---------------|-------|
| 用户管理 | CRUD | R(企业内) | - | R(自己) | - |
| 企业管理 | CRUD | RU(自己企业) | R(自己企业) | - | - |
| 产品管理 | CRUD | CRUD(企业内) | CRU(企业内) | CRUD(自己) | R(公开) |
| 内容生成 | CRUD | CRUD(企业内) | CRUD(企业内) | CRUD(自己) | - |
| AI对话 | CRUD | CRUD(企业内) | CRUD(企业内) | CRUD(自己) | - |
| 数据分析 | R(全部) | R(企业内) | R(自己) | R(自己) | - |
| 系统配置 | CRUD | - | - | - | - |
| 模板管理 | CRUD | CRU(企业内) | R | R(公开) | R(公开) |

**权限说明**: C=创建, R=读取, U=更新, D=删除

### 4.2 多租户隔离

#### 4.2.1 数据隔离策略

- 所有业务数据通过 enterprise_id 字段进行租户隔离
- 查询时自动注入租户过滤条件
- 跨租户访问需要特殊授权

#### 4.2.2 Python实现



### 4.3 API访问控制

#### 4.3.1 接口权限配置

| 接口 | 方法 | 需要认证 | 需要权限 |
|------|------|----------|----------|
| /api/v1/auth/login | POST | 否 | - |
| /api/v1/auth/register | POST | 否 | - |
| /api/v1/auth/refresh | POST | 是 | - |
| /api/v1/users/profile | GET | 是 | user:read:self |
| /api/v1/products | GET | 否 | product:read |
| /api/v1/products | POST | 是 | product:create |
| /api/v1/products/{id} | PUT | 是 | product:update |
| /api/v1/products/{id} | DELETE | 是 | product:delete |
| /api/v1/content/generate | POST | 是 | content:create |
| /api/v1/chat/send | POST | 是 | chat:create |
| /api/v1/admin/* | * | 是 | admin:* |

---

## 3. 加密策略

### 3.1 传输层加密

#### 3.1.1 TLS配置

| 配置项 | 值 | 说明 |
|--------|-----|------|
| 最低版本 | TLS 1.2 | 禁用TLS 1.0/1.1 |
| 推荐版本 | TLS 1.3 | 优先使用 |
| 证书类型 | RSA 2048 或 ECDSA P-256 | Lets Encrypt或商业证书 |
| HSTS | max-age=31536000 | 强制HTTPS |

### 3.2 存储层加密

#### 3.2.1 密码加密（bcrypt）

- 算法: bcrypt
- Cost Factor: 12
- 输出格式: \...

**Python实现:**

#### 3.2.2 敏感数据加密（AES-256-GCM）

- 算法: AES-256-GCM
- Nonce: 96-bit随机
- 输出: Base64(nonce + ciphertext)

#### 3.2.3 API请求签名（HMAC-SHA256）

### 3.3 密钥管理

| 密钥类型 | 存储位置 | 轮换周期 |
|----------|----------|----------|
| JWT签名密钥 | 环境变量/KMS | 90天 |
| 数据加密密钥 | KMS | 180天 |
| 数据库密码 | 配置中心 | 30天 |
| API密钥 | 数据库(加密) | 按需 |

---

## 3. 加密策略

### 3.1 传输层加密

#### 3.1.1 TLS配置

| 配置项 | 值 | 说明 |
|--------|-----|------|
| 最低版本 | TLS 1.2 | 禁用TLS 1.0/1.1 |
| 推荐版本 | TLS 1.3 | 优先使用 |
| 证书类型 | RSA 2048 或 ECDSA P-256 | Let"s Encrypt或商业证书 |
| HSTS | max-age=31536000 | 强制HTTPS |

**Nginx TLS配置示例:**

### 3.2 存储层加密

#### 3.2.1 密码加密（bcrypt）

#### 3.2.2 敏感数据加密（AES-256-GCM）

#### 3.2.3 API密钥加密（HMAC-SHA256）

### 3.3 密钥管理

#### 3.3.1 密钥存储规范

| 密钥类型 | 存储位置 | 访问方式 | 轮换周期 |
|----------|----------|----------|----------|
| JWT签名密钥 | 环境变量/密钥管理服务 | 应用启动时加载 | 90天 |
| 数据加密密钥 | 密钥管理服务(KMS) | API调用 | 180天 |
| 数据库密码 | 环境变量/配置中心 | 应用启动时加载 | 30天 |
| API密钥 | 数据库（加密存储） | 运行时查询 | 按需 |

#### 3.3.2 密钥轮换流程

