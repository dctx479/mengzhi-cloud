# 产品API - 快速参考

## API 端点速查表

| 方法 | 端点 | 说明 | 权限 | 状态码 |
|------|------|------|------|--------|
| GET | /products | 产品列表（分页/搜索/筛选） | 公开 | 200 |
| GET | /products/{id} | 产品详情 | 公开 | 200/404 |
| POST | /products | 创建产品 | 管理员 | 201/403/409 |
| PUT | /products/{id} | 更新产品 | 管理员 | 200/404/403 |
| DELETE | /products/{id} | 删除产品 | 管理员 | 200/404/403 |
| GET | /products/{id}/cultural-info | 获取文化信息 | 公开 | 200/404 |

## 快速示例

### 获取产品列表
```bash
GET /api/v1/products?page=1&size=10&status=active&sort_by=price&sort_order=asc
```

### 创建产品
```bash
POST /api/v1/products
Authorization: Bearer {token}
Content-Type: application/json

{
  "sku": "PROD-001",
  "name": "产品名称",
  "category": "肉类",
  "price": 199.99,
  "stock": 100,
  "region": "内蒙古"
}
```

### 更新产品
```bash
PUT /api/v1/products/1
Authorization: Bearer {token}

{
  "price": 249.99,
  "stock": 150
}
```

### 删除产品
```bash
DELETE /api/v1/products/1
Authorization: Bearer {token}
```

## 文件清单

| 文件 | 行数 | 功能 |
|------|------|------|
| models/product.py | 150 | SQLAlchemy ORM模型 |
| schemas/products.py | 350 | Pydantic Schema |
| services/product_service.py | 400 | 业务逻辑服务 |
| api/products.py | 550 | FastAPI路由 |

总计约1450行代码，含文档字符串和注释。

## 关键配置

### 数据库
```
DATABASE_URL=mysql+pymysql://root:root123@localhost:3306/agri_platform
```

### 分页限制
- 最小页码：1
- 默认页码：1
- 默认数量：10
- 最大数量：100

### 排序字段
- created_at（默认）
- price
- name
- updated_at

## 验证规则速查

| 字段 | 约束 |
|------|------|
| sku | 1-50字符，唯一 |
| name | 1-255字符 |
| price | > 0 |
| stock | >= 0 |
| category | 1-100字符 |
| region | 1-100字符 |
| cultural_tags | 最多20个 |
| page | >= 1 |
| size | 1-100 |

## 错误码速查

| 码 | HTTP | 说明 |
|----|------|------|
| 10001 | 400 | 参数验证失败 |
| 10005 | 400 | 参数值无效 |
| 20020 | 403 | 权限不足 |
| 40010 | 404 | 产品不存在 |
| 40011 | 409 | SKU已存在 |
| 50000 | 500 | 系统错误 |

## 实现检查清单

- [ ] 注册路由到 main.py
- [ ] 实现数据库连接 (database.py)
- [ ] 实现JWT认证 (auth.py)
- [ ] 创建数据库表
- [ ] 配置环境变量 (.env)
- [ ] 运行单元测试
- [ ] 生成API文档

## 依赖项

```python
fastapi==0.104+
sqlalchemy==2.0+
pydantic==2.0+
pydantic-settings==2.0+
mysql-connector-python
python-jose
loguru
```

---

生成时间：[项目完成日期]
生成版本：1.0.0
