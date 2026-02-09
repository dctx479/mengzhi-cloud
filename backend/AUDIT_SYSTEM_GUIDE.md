# 审计日志系统使用指南

## 概述

完整的审计日志系统已实现，用于记录和追踪系统中的所有关键操作。

## 系统组件

### 1. 数据模型 (`backend/app/models/audit_log.py`)

审计日志表包含以下字段：

- **基本信息**
  - `id`: 日志ID（主键）
  - `user_id`: 操作用户ID
  - `username`: 操作用户名

- **操作信息**
  - `action`: 操作类型（create/update/delete/login/logout等）
  - `resource`: 资源类型（product/user/enterprise等）
  - `resource_id`: 资源ID

- **详细信息**
  - `details`: 操作详情
  - `changes`: 变更内容（JSON格式）
  - `before_data`: 操作前数据（JSON格式）
  - `after_data`: 操作后数据（JSON格式）

- **请求信息**
  - `ip_address`: 操作IP地址
  - `user_agent`: User-Agent
  - `request_method`: HTTP方法
  - `request_path`: 请求路径

- **结果信息**
  - `status_code`: 响应状态码
  - `is_success`: 是否成功
  - `error_message`: 错误消息

- **时间戳**
  - `created_at`: 操作时间

### 2. 审计服务 (`backend/app/services/audit_service.py`)

提供以下功能：

#### 记录日志
```python
from app.services.audit_service import AuditService

# 通用日志记录
AuditService.log(
    db=db,
    user_id=user.id,
    username=user.username,
    action="update",
    resource="product",
    resource_id=product_id,
    details="更新产品信息",
    changes={"name": {"old": "旧名称", "new": "新名称"}},
    before_data={"name": "旧名称", "price": 100},
    after_data={"name": "新名称", "price": 150},
    ip=request.client.host,
    user_agent=request.headers.get("user-agent")
)

# 快捷方法
AuditService.log_create(db, user_id, username, "product", product_id, "创建产品")
AuditService.log_update(db, user_id, username, "product", product_id, "更新产品", changes)
AuditService.log_delete(db, user_id, username, "product", product_id, "删除产品")
AuditService.log_login(db, user_id, username, ip, user_agent, is_success=True)
AuditService.log_logout(db, user_id, username, ip)
```

#### 查询日志
```python
# 查询日志列表（支持分页和过滤）
result = AuditService.query_logs(
    db=db,
    user_id=123,
    action="update",
    resource="product",
    start_date=datetime(2026, 1, 1),
    end_date=datetime(2026, 1, 31),
    page=1,
    page_size=20
)

# 获取单条日志详情
log = AuditService.get_log_by_id(db, log_id=456)
```

#### 统计信息
```python
# 获取统计信息
stats = AuditService.get_statistics(
    db=db,
    start_date=datetime(2026, 1, 1),
    end_date=datetime(2026, 1, 31)
)
# 返回：总操作数、成功率、按操作类型统计、按资源类型统计、活跃用户TOP10
```

#### 导出日志
```python
# 导出为JSON或CSV
result = AuditService.export_logs(
    db=db,
    format="csv",  # 或 "json"
    action="login",
    start_date=datetime(2026, 1, 1),
    limit=10000
)
```

### 3. 审计装饰器 (`backend/app/core/audit.py`)

自动记录API调用的审计日志：

#### 基本使用
```python
from app.core.audit import audit_log

@router.post("/products")
@audit_log(action="create", resource="product")
async def create_product(
    product_data: ProductCreate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # 创建产品逻辑
    return product
```

#### 高级使用
```python
@router.put("/products/{product_id}")
@audit_log(
    action="update",
    resource="product",
    get_resource_id=lambda kwargs: kwargs.get("product_id"),
    capture_request_body=True,  # 捕获请求体
    capture_response_body=True  # 捕获响应体
)
async def update_product(
    product_id: int,
    product_data: ProductUpdate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # 更新产品逻辑
    return updated_product
```

#### 装饰器参数说明
- `action`: 操作类型（必需）
- `resource`: 资源类型（必需）
- `get_resource_id`: 从函数参数中提取资源ID的回调函数（可选）
- `capture_request_body`: 是否捕获请求体（可选，默认False）
- `capture_response_body`: 是否捕获响应体（可选，默认False）

### 4. 审计日志API (`backend/app/api/audit_logs.py`)

提供以下端点（需要管理员权限）：

#### GET /api/audit-logs
获取审计日志列表

**查询参数：**
- `user_id`: 用户ID（可选）
- `username`: 用户名，支持模糊搜索（可选）
- `action`: 操作类型（可选）
- `resource`: 资源类型（可选）
- `resource_id`: 资源ID（可选）
- `is_success`: 是否成功（可选）
- `start_date`: 开始日期，ISO格式（可选）
- `end_date`: 结束日期，ISO格式（可选）
- `page`: 页码，默认1
- `page_size`: 每页数量，默认20，最大100

**示例：**
```bash
GET /api/audit-logs?action=login&page=1&page_size=20
GET /api/audit-logs?username=admin&start_date=2026-01-01T00:00:00
```

#### GET /api/audit-logs/{log_id}
获取审计日志详情

**示例：**
```bash
GET /api/audit-logs/123
```

#### GET /api/audit-logs/stats/summary
获取审计日志统计信息

**查询参数：**
- `start_date`: 开始日期（可选）
- `end_date`: 结束日期（可选）

**返回：**
- 总操作数
- 成功/失败数量和比率
- 按操作类型统计
- 按资源类型统计
- 活跃用户TOP10

**示例：**
```bash
GET /api/audit-logs/stats/summary
GET /api/audit-logs/stats/summary?start_date=2026-01-01T00:00:00&end_date=2026-01-31T23:59:59
```

#### GET /api/audit-logs/export
导出审计日志

**查询参数：**
- `format`: 导出格式，json或csv（必需）
- `user_id`: 用户ID（可选）
- `action`: 操作类型（可选）
- `resource`: 资源类型（可选）
- `start_date`: 开始日期（可选）
- `end_date`: 结束日期（可选）
- `limit`: 最大导出数量，默认10000，最大50000

**示例：**
```bash
GET /api/audit-logs/export?format=csv&action=login
GET /api/audit-logs/export?format=json&start_date=2026-01-01T00:00:00
```

#### GET /api/audit-logs/user/{user_id}
获取指定用户的审计日志

**示例：**
```bash
GET /api/audit-logs/user/123
GET /api/audit-logs/user/123?action=update&resource=product
```

#### GET /api/audit-logs/resource/{resource}/{resource_id}
获取指定资源的审计日志

**示例：**
```bash
GET /api/audit-logs/resource/product/123
GET /api/audit-logs/resource/user/456?action=update
```

### 5. 数据库迁移 (`backend/alembic/versions/007_add_audit_logs_data_fields.py`)

添加 `before_data` 和 `after_data` 字段到审计日志表。

**运行迁移：**
```bash
cd backend
alembic upgrade head
```

## 使用场景

### 1. 自动记录API操作

在需要审计的API端点上添加装饰器：

```python
from app.core.audit import audit_log

@router.delete("/products/{product_id}")
@audit_log(
    action="delete",
    resource="product",
    get_resource_id=lambda kwargs: kwargs.get("product_id")
)
async def delete_product(
    product_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # 删除产品逻辑
    pass
```

### 2. 手动记录业务操作

在业务逻辑中手动记录：

```python
from app.services.audit_service import AuditService

# 在更新操作前获取旧数据
old_product = db.query(Product).filter(Product.id == product_id).first()
before_data = {
    "name": old_product.name,
    "price": old_product.price,
    "status": old_product.status
}

# 执行更新
product.name = new_name
product.price = new_price
db.commit()

# 获取新数据
after_data = {
    "name": product.name,
    "price": product.price,
    "status": product.status
}

# 记录审计日志
AuditService.log(
    db=db,
    user_id=current_user["user_id"],
    username=current_user["username"],
    action="update",
    resource="product",
    resource_id=product_id,
    details=f"更新产品 {product.name}",
    before_data=before_data,
    after_data=after_data,
    ip=request.client.host
)
```

### 3. 查询和分析日志

```python
# 查询特定用户的所有操作
user_logs = AuditService.query_logs(
    db=db,
    user_id=123,
    page=1,
    page_size=50
)

# 查询失败的登录尝试
failed_logins = AuditService.query_logs(
    db=db,
    action="login",
    is_success=False,
    start_date=datetime.now() - timedelta(days=7)
)

# 获取统计报告
stats = AuditService.get_statistics(
    db=db,
    start_date=datetime(2026, 1, 1),
    end_date=datetime(2026, 1, 31)
)
print(f"总操作数: {stats['total_operations']}")
print(f"成功率: {stats['success_rate']}%")
```

### 4. 导出审计报告

```python
# 导出CSV格式
csv_data = AuditService.export_logs(
    db=db,
    format="csv",
    start_date=datetime(2026, 1, 1),
    end_date=datetime(2026, 1, 31),
    limit=10000
)

# 保存到文件
with open("audit_report.csv", "w", encoding="utf-8-sig") as f:
    f.write(csv_data["data"])
```

## 最佳实践

### 1. 关键操作必须记录
- 用户登录/登出
- 数据创建/更新/删除
- 权限变更
- 配置修改
- 敏感数据访问

### 2. 记录足够的上下文信息
- 操作前后的数据对比
- 操作原因（如果适用）
- 相关的业务对象ID

### 3. 保护敏感信息
- 不要在日志中记录密码、密钥等敏感信息
- 对敏感字段进行脱敏处理

### 4. 定期清理和归档
- 设置日志保留策略
- 定期归档历史日志
- 监控日志表大小

### 5. 监控和告警
- 监控失败操作的频率
- 设置异常行为告警
- 定期审查审计日志

## 常见操作类型

- `create`: 创建资源
- `read`: 读取资源
- `update`: 更新资源
- `delete`: 删除资源
- `login`: 用户登录
- `logout`: 用户登出
- `export`: 导出数据
- `import`: 导入数据
- `approve`: 审批操作
- `reject`: 拒绝操作
- `enable`: 启用功能
- `disable`: 禁用功能

## 常见资源类型

- `user`: 用户
- `product`: 产品
- `enterprise`: 企业
- `role`: 角色
- `permission`: 权限
- `config`: 配置
- `auth`: 认证
- `media`: 媒体文件
- `chat`: 对话
- `content`: 内容

## 故障排查

### 日志未记录
1. 检查装饰器是否正确应用
2. 确认数据库连接正常
3. 查看应用日志中的错误信息

### 查询性能问题
1. 确保索引已创建
2. 使用日期范围限制查询
3. 考虑分页查询大量数据

### 导出超时
1. 减少导出数量限制
2. 使用更精确的过滤条件
3. 考虑异步导出大量数据

## 文件清单

1. **模型**: `E:\项目\数商\AI赋能云平台\backend\app\models\audit_log.py`
2. **服务**: `E:\项目\数商\AI赋能云平台\backend\app\services\audit_service.py`
3. **装饰器**: `E:\项目\数商\AI赋能云平台\backend\app\core\audit.py`
4. **API**: `E:\项目\数商\AI赋能云平台\backend\app\api\audit_logs.py`
5. **迁移**: `E:\项目\数商\AI赋能云平台\backend\alembic\versions\007_add_audit_logs_data_fields.py`
6. **路由注册**: `E:\项目\数商\AI赋能云平台\backend\app\main.py` (第190-196行)

## 总结

完整的审计日志系统已实现，包括：
- ✅ 数据模型（包含before_data和after_data字段）
- ✅ 审计服务（记录、查询、统计、导出）
- ✅ 审计装饰器（自动记录API调用）
- ✅ 审计日志API（完整的REST接口）
- ✅ 数据库迁移（版本007）
- ✅ 路由注册（已集成到主应用）

系统支持：
- 自动记录所有关键操作
- 支持日志查询和过滤
- 支持日志导出（CSV/JSON）
- 保留操作前后数据对比
- 完整的统计分析功能
