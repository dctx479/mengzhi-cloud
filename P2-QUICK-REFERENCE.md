# P2修复快速参考

## 新增API端点速查

### 用户
```
POST   /api/v1/users/avatar          上传头像
GET    /api/v1/users/me              获取用户信息
```

### 产品
```
POST   /api/v1/products/{id}/images  上传产品图片
DELETE /api/v1/products/{id}/images  删除产品图片
POST   /api/v1/products/batch-delete 批量删除
PUT    /api/v1/products/batch-update 批量更新
```

### 导出
```
GET    /api/v1/export/products?format=csv    CSV导出
GET    /api/v1/export/products?format=excel  Excel导出
GET    /api/v1/export/products/template      下载模板
```

---

## 服务使用速查

### 文件上传
```python
from app.services.file_service import FileService

# 上传头像
avatar_url = await FileService.upload_avatar(file, user_id)

# 上传产品图片
image_url = await FileService.upload_product_image(file, product_id)
```

### 邮件服务
```python
from app.services.notification_service import email_service

# 发送验证码
email_service.send_verification_email(
    to="user@example.com",
    code="123456",
    username="张三"
)

# 发送密码重置
email_service.send_password_reset_email(
    to="user@example.com",
    reset_link="https://...",
    username="张三"
)
```

### 审计日志
```python
from app.services.audit_service import AuditService

# 记录创建
AuditService.log_create(
    db, user_id, username, "product", product_id, 
    "创建产品", ip
)

# 记录更新
AuditService.log_update(
    db, user_id, username, "product", product_id,
    "更新产品", changes, ip
)

# 记录登录
AuditService.log_login(
    db, user_id, username, ip, user_agent, 
    is_success=True
)
```

---

## 常用命令

### 开发
```bash
# 启动后端
uvicorn app.main:app --reload

# 启动前端
cd frontend && npm run dev

# 运行测试
pytest

# 数据库迁移
alembic upgrade head
```

### 部署
```bash
# 安装依赖
pip install -r requirements.txt

# 生产运行
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

---

## 配置清单

### 必需配置
```env
DATABASE_URL=mysql+pymysql://...
SECRET_KEY=...
```

### 可选配置
```env
# 邮件
SMTP_SERVER=smtp.example.com
SMTP_PORT=587
SMTP_USER=...
SMTP_PASSWORD=...

# 存储（未来）
OSS_ENDPOINT=...
OSS_BUCKET=...
```

---

## 问题排查

### 文件上传失败
1. 检查 uploads/ 目录权限
2. 检查文件大小限制
3. 检查文件类型

### 邮件发送失败
1. 检查SMTP配置
2. 检查网络连接
3. 查看日志: logs/app.log

### 数据库迁移失败
1. 检查数据库连接
2. 回滚: alembic downgrade -1
3. 重新迁移: alembic upgrade head

---

**版本**: 1.0
**更新**: [项目完成日期]
