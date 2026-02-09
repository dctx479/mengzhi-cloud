# RBAC权限系统 - 快速使用指南

## 1. 快速开始

### 1.1 运行数据库迁移

```bash
cd backend
alembic upgrade head
```

### 1.2 启动应用

```bash
python -m uvicorn app.main:app --reload
```

应用启动时会自动初始化默认角色和权限。

### 1.3 访问API文档

打开浏览器访问: http://localhost:8000/docs

在Swagger UI中找到"权限管理 - RBAC"标签。

---

## 2. 在代码中使用权限系统

### 2.1 保护API端点（推荐方式）

```python
from fastapi import APIRouter, Depends
from app.api.deps import require_permission, get_db
from sqlalchemy.orm import Session

router = APIRouter()

@router.post("/products")
async def create_product(
    product_data: ProductCreate,
    current_user: dict = Depends(require_permission("product", "create")),
    db: Session = Depends(get_db)
):
    """创建产品 - 需要product:create权限"""
    # 只有拥有权限的用户才能执行到这里
    ...

@router.delete("/products/{product_id}")
async def delete_product(
    product_id: int,
    current_user: dict = Depends(require_permission("product", "delete")),
    db: Session = Depends(get_db)
):
    """删除产品 - 需要product:delete权限"""
    ...
```

### 2.2 在Service层检查权限

```python
from app.models import User

def process_sensitive_data(user: User, db: Session):
    # 检查用户是否有权限
    if not user.has_permission("data", "process"):
        raise PermissionError("无权处理敏感数据")

    # 执行操作
    ...
```

### 2.3 编程式权限检查

```python
from app.api.deps import check_permission

def some_function(user_id: int, db: Session):
    if check_permission(user_id, "report", "export", db):
        # 导出报表
        ...
    else:
        # 显示错误
        ...
```

---

## 3. 常用管理操作

### 3.1 创建自定义角色

**API调用**:
```bash
curl -X POST "http://localhost:8000/api/v1/rbac/roles" \
  -H "Authorization: Bearer YOUR_ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "内容编辑",
    "code": "CONTENT_EDITOR",
    "description": "负责内容编辑和发布",
    "permission_ids": [13, 14, 15]
  }'
```

**Python代码**:
```python
from app.services.permission_service import PermissionService

service = PermissionService(db)
role = service.create_role(
    name="内容编辑",
    code="CONTENT_EDITOR",
    description="负责内容编辑和发布",
    permission_ids=[13, 14, 15]
)
```

### 3.2 为用户分配角色

**API调用**:
```bash
curl -X POST "http://localhost:8000/api/v1/rbac/users/123/roles" \
  -H "Authorization: Bearer YOUR_ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "role_ids": [1, 2]
  }'
```

**Python代码**:
```python
service = PermissionService(db)
service.assign_roles_to_user(
    user_id=123,
    role_ids=[1, 2]  # ADMIN和CONTENT_EDITOR角色
)
```

### 3.3 查询用户权限

**API调用**:
```bash
# 查询指定用户的权限
curl -X GET "http://localhost:8000/api/v1/rbac/users/123/permissions" \
  -H "Authorization: Bearer YOUR_TOKEN"

# 查询当前用户的权限
curl -X GET "http://localhost:8000/api/v1/rbac/users/me/permissions" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**Python代码**:
```python
# 获取用户所有权限
permissions = user.get_all_permissions()
# 返回: [{"id": 1, "resource": "product", "action": "create", ...}, ...]

# 检查特定权限
if user.has_permission("product", "delete"):
    print("用户可以删除产品")
```

---

## 4. 默认角色说明

### 4.1 ADMIN - 超级管理员

- **权限**: 所有权限
- **适用**: 系统管理员
- **特点**: 自动拥有所有权限，即使没有显式分配

### 4.2 ENTERPRISE - 企业用户

- **权限**:
  - 产品管理: create, read, update, delete, list, export
  - 对话管理: create, read, delete, list
  - 内容生成: create, read, export
  - 企业管理: create, read, update, delete, manage
- **适用**: 企业账户

### 4.3 PERSONAL - 个人用户

- **权限**:
  - 产品查看: read, list
  - 产品创建: create（自己的产品）
  - 对话使用: create, read, list
  - 内容生成: create, read
- **适用**: 个人用户

---

## 5. 权限命名规范

### 5.1 资源命名

使用**小写字母**和**下划线**:
- ✅ `product`
- ✅ `user_profile`
- ✅ `chat_message`
- ❌ `Product`
- ❌ `user-profile`

### 5.2 操作命名

标准操作（推荐）:
- `create` - 创建
- `read` - 读取/查看
- `update` - 更新
- `delete` - 删除
- `list` - 列表查询
- `export` - 导出
- `import` - 导入
- `manage` - 综合管理

### 5.3 权限代码格式

权限代码格式: `resource:action`

示例:
- `product:create` - 创建产品
- `user:delete` - 删除用户
- `chat:read` - 查看对话
- `report:export` - 导出报表

---

## 6. 常见问题

### Q1: 如何让管理员拥有所有权限？

A: 管理员（`user.role == "admin"`）会自动拥有所有权限，无需显式分配。

### Q2: 如何创建新的权限？

A: 调用API或使用Service:
```python
service = PermissionService(db)
perm = service.create_permission(
    resource="report",
    action="export",
    name="导出报表",
    description="导出各类统计报表"
)
```

### Q3: 能否给一个用户分配多个角色？

A: 可以！用户可以拥有多个角色，权限会自动合并（去重）。

### Q4: 如何修改现有角色的权限？

A: 使用"为角色分配权限"接口（覆盖式）:
```python
service.assign_permissions_to_role(
    role_id=role.id,
    permission_ids=[1, 2, 3, 4, 5]  # 新的权限列表
)
```

### Q5: 系统角色可以删除吗？

A: 不可以。系统角色（`is_system=True`）受保护，不能删除或修改代码。

### Q6: 如何为现有用户批量分配角色？

A: 使用SQL批量插入:
```sql
INSERT INTO user_roles (user_id, role_id, created_at)
SELECT u.id, r.id, NOW()
FROM users u, roles r
WHERE u.user_type = 'enterprise' AND r.code = 'ENTERPRISE';
```

---

## 7. 性能优化建议

### 7.1 使用权限缓存

```python
# 在用户登录时缓存权限到Session或Redis
def login_user(user_id, db):
    user = db.query(User).filter(User.id == user_id).first()
    permissions = user.get_all_permissions()

    # 缓存到Redis（推荐）
    redis_client.setex(
        f"user:{user_id}:permissions",
        3600,  # 1小时过期
        json.dumps(permissions)
    )
```

### 7.2 预加载关系

```python
# 使用selectin或joinedload预加载
from sqlalchemy.orm import selectinload

user = db.query(User).options(
    selectinload(User.roles).selectinload(Role.permissions)
).filter(User.id == user_id).first()

# 现在访问user.roles和role.permissions不会触发额外查询
```

---

## 8. 安全最佳实践

### 8.1 最小权限原则

只分配用户真正需要的权限，避免过度授权。

### 8.2 定期审计

定期检查用户权限分配，移除不再需要的权限。

### 8.3 敏感操作双重验证

对于特别敏感的操作（如删除用户、修改权限），考虑添加二次验证:

```python
@router.delete("/users/{user_id}")
async def delete_user(
    user_id: int,
    confirmation: str = Body(...),
    current_user: dict = Depends(require_permission("user", "delete")),
    db: Session = Depends(get_db)
):
    if confirmation != "DELETE":
        raise HTTPException(400, "需要输入确认文本")

    # 执行删除
    ...
```

### 8.4 记录权限变更

在修改权限时记录审计日志:

```python
from app.services.audit_service import AuditService

audit = AuditService(db)
audit.log_action(
    user_id=current_user["user_id"],
    action="assign_role",
    resource="user",
    resource_id=user_id,
    details={"role_ids": role_ids}
)
```

---

## 9. 测试

### 9.1 运行测试

```bash
# 运行RBAC测试
pytest backend/tests/test_rbac.py -v

# 运行所有测试
pytest backend/tests/ -v

# 生成覆盖率报告
pytest backend/tests/ --cov=app.services.permission_service
```

### 9.2 手动测试

1. 访问 http://localhost:8000/docs
2. 使用管理员账户登录获取token
3. 在Swagger UI中测试RBAC接口
4. 验证权限验证是否正常工作

---

## 10. 故障排查

### 问题1: 用户明明有权限但提示权限不足

**检查步骤**:
1. 确认用户已分配角色: `GET /api/v1/rbac/users/{user_id}/roles`
2. 确认角色包含所需权限: `GET /api/v1/rbac/roles/{role_id}`
3. 确认权限名称正确: `require_permission("product", "create")`
4. 刷新用户Session或重新登录

### 问题2: 数据库迁移失败

**解决方法**:
```bash
# 检查当前版本
alembic current

# 如果卡在旧版本，先降级再升级
alembic downgrade -1
alembic upgrade head

# 如果完全失败，重新初始化
alembic stamp head
```

### 问题3: 默认角色未创建

**解决方法**:
```python
# 手动初始化
from app.services.permission_service import PermissionService
from app.api.deps import get_db

db = next(get_db())
PermissionService.initialize_default_roles(db)
db.close()
```

---

## 11. 更多资源

- **完整文档**: `RBAC-IMPLEMENTATION-REPORT.md`
- **API文档**: http://localhost:8000/docs
- **测试文件**: `backend/tests/test_rbac.py`
- **代码示例**: 见各API文件的docstring

---

**最后更新**: [项目完成日期]
