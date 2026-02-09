# 多AI服务商与多租户系统实施文档

**版本**: 2.0
**日期**: 2026-01-22
**状态**: ✅ 已完成

---

## 📋 实施概览

本次实施成功完成了以下核心功能：

1. ✅ **多AI服务商支持** - 支持DeepSeek、OpenAI等多个AI服务商
2. ✅ **增强多租户功能** - 企业级AI配置、数据隔离
3. ✅ **完善权限控制** - RBAC权限系统、管理员面板
4. ✅ **注册流程分离** - 企业和个人用户独立注册

---

## 🎯 核心功能

### 1. 多AI服务商支持

#### 架构设计
```
AIProviderFactory
    ├── DeepSeekProvider
    ├── OpenAIProvider
    └── [可扩展更多Provider]
```

#### 实现文件
- `backend/app/services/ai/base_provider.py` - 抽象基类
- `backend/app/services/ai/providers/deepseek_provider.py` - DeepSeek实现
- `backend/app/services/ai/providers/openai_provider.py` - OpenAI实现
- `backend/app/services/ai/factory.py` - Provider工厂

#### 使用示例
```python
from app.services.ai import AIProviderFactory, ChatCompletionRequest, ChatMessage

# 创建Provider
provider = AIProviderFactory.create(
    provider_type="deepseek",
    api_key="sk-xxx",
    base_url="https://api.deepseek.com"  # 可选
)

# 调用AI
request = ChatCompletionRequest(
    messages=[ChatMessage(role="user", content="Hello")],
    temperature=0.7
)
response = await provider.chat(request)
```

---

### 2. 租户AI配置管理

#### 数据模型
**表**: `tenant_ai_configs`

| 字段 | 类型 | 说明 |
|------|------|------|
| id | BIGINT | 主键 |
| enterprise_id | BIGINT | 企业ID（外键） |
| provider | VARCHAR(50) | AI服务商 |
| api_key_encrypted | TEXT | 加密的API密钥 |
| base_url | VARCHAR(255) | 自定义API地址 |
| default_model | VARCHAR(100) | 默认模型 |
| is_active | BOOLEAN | 是否启用 |

#### API端点
```
GET    /api/enterprises/{enterprise_id}/ai-configs       # 列表
POST   /api/enterprises/{enterprise_id}/ai-configs       # 创建
PATCH  /api/enterprises/{enterprise_id}/ai-configs/{id}  # 更新
DELETE /api/enterprises/{enterprise_id}/ai-configs/{id}  # 删除
POST   /api/enterprises/{enterprise_id}/ai-configs/{id}/test  # 测试
```

#### 安全特性
- ✅ API密钥使用Fernet加密存储
- ✅ 仅企业Owner/Admin可管理配置
- ✅ 配置验证（测试API连接）

---

### 3. 权限控制系统

#### 权限装饰器
**文件**: `backend/app/core/permissions.py`

```python
from app.core.permissions import require_permission, require_admin, require_enterprise_owner

# RBAC权限检查
@router.post("/products")
async def create_product(
    current_user: dict = Depends(require_permission("product", "create"))
):
    ...

# 管理员权限
@router.delete("/users/{user_id}")
async def delete_user(
    current_user: dict = Depends(require_admin())
):
    ...

# 企业管理员权限
@router.patch("/enterprise/settings")
async def update_settings(
    current_user: dict = Depends(require_enterprise_owner())
):
    ...
```

#### 租户上下文
**文件**: `backend/app/core/tenant_context.py`

```python
from app.core.tenant_context import get_current_tenant, TenantContext

@router.get("/data")
async def get_data(
    tenant: TenantContext = Depends(get_current_tenant),
    db: Session = Depends(get_db)
):
    # 使用 tenant.tenant_id 进行数据隔离
    data = db.query(Model).filter(Model.tenant_id == tenant.tenant_id).all()
    ...
```

---

### 4. 管理员面板

#### API端点
**文件**: `backend/app/api/admin.py`

**用户管理**:
```
GET    /api/admin/users              # 用户列表
PATCH  /api/admin/users/{id}         # 更新用户
DELETE /api/admin/users/{id}         # 删除用户
```

**企业管理**:
```
GET    /api/admin/enterprises        # 企业列表
PATCH  /api/admin/enterprises/{id}   # 更新企业
DELETE /api/admin/enterprises/{id}   # 删除企业
```

**统计数据**:
```
GET    /api/admin/stats              # 平台统计
GET    /api/admin/ai-usage           # AI使用统计
```

#### 功能特性
- ✅ 分页、搜索、筛选
- ✅ 用户状态管理（激活/禁用）
- ✅ 企业套餐管理
- ✅ 平台统计数据
- ✅ AI使用量统计

---

### 5. 注册流程分离

#### 个人用户注册
**端点**: `POST /api/v1/auth/register`

```json
{
  "username": "user123",
  "email": "user@example.com",
  "password": "password123",
  "user_type": "personal"
}
```

**流程**:
1. 创建用户账号
2. 用户角色设置为 `user`
3. `enterprise_id` 为 NULL

#### 企业用户注册
**端点**: `POST /api/v1/auth/register`

```json
{
  "username": "admin",
  "email": "admin@company.com",
  "password": "password123",
  "user_type": "enterprise",
  "enterprise_name": "公司名称",
  "enterprise_license": "营业执照号"
}
```

**流程**:
1. 创建企业记录（状态：待审核）
2. 创建用户账号
3. 用户角色设置为 `enterprise_admin`
4. 关联用户到企业

---

## 📊 数据库变更

### 新增表

#### 1. tenant_ai_configs
```sql
CREATE TABLE tenant_ai_configs (
  id BIGINT PRIMARY KEY AUTO_INCREMENT,
  enterprise_id BIGINT NOT NULL,
  provider VARCHAR(50) NOT NULL,
  api_key_encrypted TEXT NOT NULL,
  base_url VARCHAR(255),
  default_model VARCHAR(100),
  is_active BOOLEAN DEFAULT TRUE,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  deleted_at TIMESTAMP NULL,
  FOREIGN KEY (enterprise_id) REFERENCES enterprises(id) ON DELETE CASCADE,
  UNIQUE KEY idx_enterprise_provider (enterprise_id, provider),
  KEY idx_is_active (is_active)
);
```

### 扩展字段

#### users表
```sql
ALTER TABLE users ADD COLUMN is_admin BOOLEAN DEFAULT FALSE NOT NULL;
ALTER TABLE users ADD INDEX idx_is_admin (is_admin);
```

---

## 🔐 安全设计

### 1. API密钥加密
- 使用 **Fernet** 对称加密
- 密钥通过环境变量管理
- 加密后存储，API响应不暴露

### 2. 权限控制
- **RBAC模型**: 基于角色的访问控制
- **最小权限原则**: 用户仅能访问授权资源
- **管理员隔离**: 系统管理员与企业管理员分离

### 3. 数据隔离
- **行级隔离**: 通过 `enterprise_id` 过滤
- **租户上下文**: 自动注入租户信息
- **双重校验**: 应用层 + 数据库层

---

## 🚀 部署指南

### 1. 环境准备

```bash
# 安装依赖
cd backend
pip install cryptography  # 用于API密钥加密
```

### 2. 数据库迁移

```bash
# 执行迁移
cd backend
alembic upgrade head
```

如果遇到编码问题，手动执行SQL：
```sql
-- 创建 tenant_ai_configs 表
-- 添加 users.is_admin 字段
-- 参考: backend/alembic/versions/004_add_multi_tenant_ai_support.py
```

### 3. 环境变量配置

```env
# backend/.env

# 加密密钥（用于API密钥加密）
ENCRYPTION_KEY=your-32-byte-base64-encoded-key

# AI服务商配置（可选，用于系统默认）
DEEPSEEK_API_KEY=sk-xxx
DEEPSEEK_API_BASE=https://api.deepseek.com

OPENAI_API_KEY=sk-xxx
OPENAI_API_BASE=https://api.openai.com/v1
```

### 4. 创建管理员账号

```sql
-- 方式1: 直接SQL
UPDATE users SET is_admin = TRUE WHERE email = 'admin@example.com';

-- 方式2: 通过API（需要先有一个管理员）
PATCH /api/admin/users/{id}
{
  "is_admin": true
}
```

---

## 📖 使用指南

### 企业配置AI服务商

1. **企业管理员登录**
2. **访问AI配置页面**
3. **添加AI配置**:
   ```
   POST /api/enterprises/{enterprise_id}/ai-configs
   {
     "provider": "deepseek",
     "api_key": "sk-xxx",
     "base_url": "https://api.deepseek.com",  // 可选
     "default_model": "deepseek-chat"  // 可选
   }
   ```
4. **测试配置**:
   ```
   POST /api/enterprises/{enterprise_id}/ai-configs/{id}/test
   ```
5. **启用配置**:
   ```
   PATCH /api/enterprises/{enterprise_id}/ai-configs/{id}
   {
     "is_active": true
   }
   ```

### 管理员管理平台

1. **查看平台统计**:
   ```
   GET /api/admin/stats
   ```

2. **管理用户**:
   ```
   GET /api/admin/users?page=1&page_size=20&search=keyword
   PATCH /api/admin/users/{id} { "status": "active" }
   ```

3. **管理企业**:
   ```
   GET /api/admin/enterprises?page=1&page_size=20
   PATCH /api/admin/enterprises/{id} { "plan_type": "pro" }
   ```

4. **查看AI使用统计**:
   ```
   GET /api/admin/ai-usage?days=30
   ```

---

## 🧪 测试

### 1. 测试AI Provider

```python
import asyncio
from app.services.ai import AIProviderFactory, ChatCompletionRequest, ChatMessage

async def test_provider():
    provider = AIProviderFactory.create(
        provider_type="deepseek",
        api_key="sk-xxx"
    )

    request = ChatCompletionRequest(
        messages=[ChatMessage(role="user", content="Hello")],
        max_tokens=100
    )

    response = await provider.chat(request)
    print(response.content)

asyncio.run(test_provider())
```

### 2. 测试权限控制

```bash
# 测试管理员权限
curl -X GET http://localhost:8001/api/admin/stats \
  -H "Authorization: Bearer {admin_token}"

# 测试企业管理员权限
curl -X POST http://localhost:8001/api/enterprises/1/ai-configs \
  -H "Authorization: Bearer {enterprise_admin_token}" \
  -d '{"provider": "deepseek", "api_key": "sk-xxx"}'
```

---

## 📝 API文档

完整API文档可通过以下方式访问：

- **Swagger UI**: http://localhost:8001/docs
- **ReDoc**: http://localhost:8001/redoc

---

## 🎉 实施总结

### 完成功能

✅ **多AI服务商支持**
- DeepSeek、OpenAI Provider实现
- 统一接口抽象
- 工厂模式管理

✅ **租户AI配置**
- 企业级配置管理
- API密钥加密存储
- 配置验证和测试

✅ **权限控制系统**
- RBAC权限装饰器
- 租户上下文管理
- 管理员权限隔离

✅ **管理员面板**
- 用户管理
- 企业管理
- 平台统计
- AI使用统计

✅ **注册流程分离**
- 个人用户注册
- 企业用户注册
- 企业信息验证

### 技术亮点

- **最小化实现**: 代码简洁，易于维护
- **安全设计**: 加密存储、权限隔离、数据隔离
- **可扩展性**: 易于添加新的AI服务商
- **向后兼容**: 保持现有功能不受影响

### 性能指标

- **代码行数**: ~1500行（新增）
- **API端点**: +13个
- **数据表**: +1个
- **实施时间**: ~8小时（并行开发）

---

## 🔮 后续优化建议

### 短期（1-2周）
1. 前端UI实现（企业配置页面、管理员面板）
2. 完善单元测试和集成测试
3. 添加API使用量监控和告警

### 中期（1-2月）
1. 支持更多AI服务商（Qwen、Claude等）
2. 实现配额管理和计费系统
3. 添加审计日志功能

### 长期（3-6月）
1. 多租户数据完全隔离（独立数据库）
2. AI服务商故障转移和负载均衡
3. 企业级SLA保障

---

**文档版本**: 2.0
**最后更新**: 2026-01-22
**维护者**: AI赋能云平台开发团队
