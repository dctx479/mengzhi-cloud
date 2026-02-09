# 产品管理API

## 概述

完整的产品管理API系统，包含6个RESTful端点，支持分页、搜索、筛选等功能。

## 系统架构

```
API Layer (FastAPI)
    ↓
Service Layer (业务逻辑)
    ↓
Data Layer (SQLAlchemy ORM)
    ↓
Database (MySQL)
```

## 生成文件结构

```
backend/app/
├── api/
│   └── products.py          # 产品路由 (6个端点)
├── models/
│   └── product.py           # 产品数据模型 (SQLAlchemy)
├── schemas/
│   └── products.py          # Pydantic Schema (请求/响应)
└── services/
    └── product_service.py   # 产品业务服务
```

## API端点

### 1. GET /api/v1/products - 获取产品列表

获取产品列表，支持分页、搜索、筛选和排序。

**查询参数:**

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `page` | int | 1 | 页码（从1开始） |
| `size` | int | 10 | 每页数量（1-100） |
| `search` | string | - | 搜索关键词（名称、SKU） |
| `category` | string | - | 产品类别筛选 |
| `region` | string | - | 产地区域筛选 |
| `status` | string | - | 产品状态筛选 (draft/active/inactive) |
| `is_featured` | boolean | - | 是否精选产品 |
| `sort_by` | string | created_at | 排序字段 (created_at/price/name) |
| `sort_order` | string | desc | 排序顺序 (asc/desc) |

**请求示例:**

```bash
curl -X GET "http://localhost:8000/api/v1/products?page=1&size=10&category=肉类&status=active&sort_by=price&sort_order=asc"
```

**响应示例 (200):**

```json
{
  "code": 200,
  "message": "获取产品列表成功",
  "data": {
    "items": [
      {
        "id": 1,
        "sku": "PROD-001",
        "name": "草原牛肉",
        "category": "肉类",
        "price": 199.99,
        "stock": 100,
        "region": "内蒙古呼伦贝尔",
        "status": "active",
        "is_featured": true,
        "created_at": "[项目完成日期]T10:00:00"
      }
    ],
    "pagination": {
      "page": 1,
      "size": 10,
      "total": 25,
      "pages": 3,
      "has_next": true,
      "has_prev": false
    }
  },
  "timestamp": "[项目完成日期]T10:00:00"
}
```

### 2. GET /api/v1/products/{id} - 获取产品详情

获取单个产品的完整信息。

**路径参数:**

| 参数 | 类型 | 说明 |
|------|------|------|
| `id` | int | 产品ID |

**请求示例:**

```bash
curl -X GET "http://localhost:8000/api/v1/products/1"
```

**响应示例 (200):**

```json
{
  "code": 200,
  "message": "获取产品详情成功",
  "data": {
    "id": 1,
    "sku": "PROD-001",
    "name": "草原牛肉",
    "description": "来自内蒙古草原的优质牛肉",
    "category": "肉类",
    "price": 199.99,
    "cost": 100.0,
    "stock": 100,
    "region": "内蒙古呼伦贝尔",
    "region_code": "NMG-HLB",
    "cultural_tags": ["草原", "有机", "绿色"],
    "cultural_description": "传统草原养殖文化",
    "origin_story": "草原牛自由放牧...",
    "efficacy": "营养丰富，易消化",
    "usage": "烧烤、炖汤、炒菜",
    "status": "active",
    "is_featured": true,
    "created_at": "[项目完成日期]T10:00:00",
    "updated_at": "[项目完成日期]T10:00:00",
    "created_by": 1,
    "updated_by": 1
  },
  "timestamp": "[项目完成日期]T10:00:00"
}
```

**错误响应 (404):**

```json
{
  "code": 40010,
  "message": "产品不存在",
  "data": null,
  "timestamp": "[项目完成日期]T10:00:00"
}
```

### 3. POST /api/v1/products - 创建产品

创建新产品（仅管理员）。

**请求头:**

```
Authorization: Bearer {token}
Content-Type: application/json
```

**请求体:**

```json
{
  "sku": "PROD-002",
  "name": "羊肉",
  "description": "新鲜羊肉",
  "category": "肉类",
  "price": 149.99,
  "cost": 75.0,
  "stock": 50,
  "region": "内蒙古锡林郭勒",
  "region_code": "NMG-XLGL",
  "cultural_tags": ["草原", "有机"],
  "cultural_description": "草原羊文化",
  "origin_story": "草原羊的故事...",
  "efficacy": "温阳补气",
  "usage": "炖汤、烤肉",
  "status": "active",
  "is_featured": false
}
```

**请求示例:**

```bash
curl -X POST "http://localhost:8000/api/v1/products" \
  -H "Authorization: Bearer {token}" \
  -H "Content-Type: application/json" \
  -d '{...}'
```

**响应示例 (201):**

```json
{
  "code": 200,
  "message": "产品创建成功",
  "data": {
    "id": 2,
    "sku": "PROD-002",
    "name": "羊肉",
    ...
  },
  "timestamp": "[项目完成日期]T10:00:00"
}
```

**错误响应 (403):**

```json
{
  "code": 20020,
  "message": "权限不足",
  "data": null,
  "timestamp": "[项目完成日期]T10:00:00"
}
```

**错误响应 (409):**

```json
{
  "code": 40011,
  "message": "产品SKU已存在: PROD-002",
  "data": null,
  "timestamp": "[项目完成日期]T10:00:00"
}
```

### 4. PUT /api/v1/products/{id} - 更新产品

更新产品信息（仅管理员）。

**路径参数:**

| 参数 | 类型 | 说明 |
|------|------|------|
| `id` | int | 产品ID |

**请求体（可选字段）:**

```json
{
  "name": "高级羊肉",
  "price": 169.99,
  "stock": 75,
  "status": "active"
}
```

**请求示例:**

```bash
curl -X PUT "http://localhost:8000/api/v1/products/1" \
  -H "Authorization: Bearer {token}" \
  -H "Content-Type: application/json" \
  -d '{
    "price": 249.99,
    "stock": 150
  }'
```

**响应示例 (200):**

```json
{
  "code": 200,
  "message": "产品更新成功",
  "data": {
    "id": 1,
    "sku": "PROD-001",
    "name": "草原牛肉",
    "price": 249.99,
    "stock": 150,
    ...
  },
  "timestamp": "[项目完成日期]T10:00:00"
}
```

### 5. DELETE /api/v1/products/{id} - 删除产品

删除产品（仅管理员）。

**路径参数:**

| 参数 | 类型 | 说明 |
|------|------|------|
| `id` | int | 产品ID |

**请求示例:**

```bash
curl -X DELETE "http://localhost:8000/api/v1/products/1" \
  -H "Authorization: Bearer {token}"
```

**响应示例 (200):**

```json
{
  "code": 200,
  "message": "产品删除成功",
  "data": {
    "id": 1
  },
  "timestamp": "[项目完成日期]T10:00:00"
}
```

### 6. GET /api/v1/products/{id}/cultural-info - 获取产品文化信息

获取产品的文化相关信息。

**路径参数:**

| 参数 | 类型 | 说明 |
|------|------|------|
| `id` | int | 产品ID |

**请求示例:**

```bash
curl -X GET "http://localhost:8000/api/v1/products/1/cultural-info"
```

**响应示例 (200):**

```json
{
  "code": 200,
  "message": "获取文化信息成功",
  "data": {
    "cultural_tags": ["草原", "有机", "绿色"],
    "cultural_description": "传统草原养殖文化",
    "origin_story": "草原牛自由放牧，采食天然草料，生长周期长，肉质紧实...",
    "efficacy": "营养丰富，易消化，补气养血",
    "usage": "烧烤、炖汤、炒菜、红烧",
    "region": "内蒙古呼伦贝尔",
    "region_code": "NMG-HLB"
  },
  "timestamp": "[项目完成日期]T10:00:00"
}
```

## 数据模型

### Product (产品表)

**表名:** `products`

| 列名 | 类型 | 约束 | 说明 |
|------|------|------|------|
| `id` | int | PK, AI | 产品ID |
| `sku` | varchar(50) | UNI, NNL, IDX | 产品SKU |
| `name` | varchar(255) | NNL, IDX | 产品名称 |
| `description` | text | - | 产品描述 |
| `category` | varchar(100) | NNL, IDX | 产品类别 |
| `price` | float | NNL | 价格（元） |
| `cost` | float | - | 成本（元） |
| `stock` | int | - | 库存数量 |
| `region` | varchar(100) | NNL, IDX | 产地区域 |
| `region_code` | varchar(20) | - | 产地代码 |
| `cultural_tags` | json | - | 文化标签列表 |
| `cultural_description` | text | - | 文化介绍 |
| `origin_story` | text | - | 产品起源故事 |
| `efficacy` | text | - | 产品功效说明 |
| `usage` | text | - | 产品使用方法 |
| `status` | varchar(20) | IDX, DEFAULT='draft' | 状态 |
| `is_featured` | bool | DEFAULT=false | 是否精选 |
| `created_at` | datetime | NNL, IDX, DEFAULT=now | 创建时间 |
| `updated_at` | datetime | DEFAULT=now | 更新时间 |
| `created_by` | int | - | 创建者ID |
| `updated_by` | int | - | 更新者ID |

**索引:**

- `ix_sku` - SKU唯一索引
- `ix_name` - 名称索引（用于搜索）
- `ix_category` - 类别索引
- `ix_region` - 地区索引
- `ix_status` - 状态索引
- `ix_category_status` - 类别+状态复合索引
- `ix_region_status` - 地区+状态复合索引
- `ix_created_at` - 创建时间索引（用于排序）

**产品状态枚举:**

- `draft` - 草稿
- `active` - 上架
- `inactive` - 下架

### cultural_tags JSON字段

存储文化标签列表：

```json
["草原", "有机", "绿色", "传统工艺"]
```

## Schema定义

### 请求Schema

#### ProductCreateRequest

```python
{
  "sku": str,                      # 产品SKU (1-50字符)
  "name": str,                     # 产品名称 (1-255字符)
  "description": str | null,       # 产品描述
  "category": str,                 # 产品类别 (1-100字符)
  "price": float,                  # 价格 (> 0)
  "cost": float | null,            # 成本 (>= 0)
  "stock": int,                    # 库存 (>= 0)
  "region": str,                   # 产地 (1-100字符)
  "region_code": str | null,       # 产地代码
  "cultural_tags": [str] | null,   # 文化标签 (最多20个)
  "cultural_description": str | null,
  "origin_story": str | null,
  "efficacy": str | null,
  "usage": str | null,
  "status": "draft" | "active" | "inactive",
  "is_featured": bool
}
```

#### ProductUpdateRequest

与创建请求相同，但所有字段均为可选。

### 响应Schema

#### ProductDetailResponse

完整的产品信息响应。

#### ProductListItemResponse

列表简化版响应（不包含详细的文化信息）。

#### CulturalInfoResponse

仅包含文化相关信息的响应。

## 服务层方法

### ProductService

```python
# CRUD 操作
create_product(request, user_id) -> Product
get_product_by_id(product_id) -> Product
get_product_by_sku(sku) -> Product | None
update_product(product_id, request, user_id) -> Product
delete_product(product_id) -> bool

# 查询操作
list_products(page, size, search, category, region, status, is_featured, sort_by, sort_order) -> (List[Product], int)
get_featured_products(limit) -> List[Product]
get_products_by_category(category, limit) -> List[Product]
get_products_by_region(region, limit) -> List[Product]

# 统计操作
get_product_statistics() -> dict
get_categories() -> List[str]
get_regions() -> List[str]
```

## 错误处理

### 常见错误码

| 错误码 | HTTP | 说明 |
|--------|------|------|
| 10000 | 400 | 参数错误 |
| 10001 | 400 | 参数验证失败 |
| 10005 | 400 | 参数值无效 |
| 20020 | 403 | 权限不足 |
| 40010 | 404 | 记录不存在 |
| 40011 | 409 | 记录已存在 |
| 40003 | 500 | 数据库插入失败 |
| 40004 | 500 | 数据库更新失败 |
| 40005 | 500 | 数据库删除失败 |
| 50000 | 500 | 系统错误 |

### 错误响应格式

```json
{
  "code": 40010,
  "message": "产品不存在",
  "data": null,
  "errors": null,
  "timestamp": "[项目完成日期]T10:00:00",
  "request_id": "uuid-v4"
}
```

## 集成指南

### 1. 注册路由

在 `backend/app/main.py` 中：

```python
from app.api import products

app.include_router(products.router, prefix="/api/v1", tags=["产品"])
```

### 2. 实现依赖项

需要实现以下依赖项：

```python
# 数据库连接
def get_db() -> Session:
    # 实现SQLAlchemy会话管理
    pass

# 用户认证
def get_current_user_id() -> int:
    # 实现JWT解析和用户获取
    pass

# 管理员权限验证
def verify_admin(user_id: int = Depends(get_current_user_id)) -> int:
    # 实现权限检查
    pass
```

### 3. 数据库初始化

创建数据库表：

```python
from app.models.product import Base
from app.core.database import engine

Base.metadata.create_all(bind=engine)
```

### 4. 环境配置

在 `.env` 文件中配置：

```
DATABASE_URL=mysql+pymysql://user:password@localhost:3306/dbname
```

## 验证规则

### SKU验证

- 长度：1-50字符
- 唯一性：必须唯一
- 格式：自由格式（推荐 `PROD-XXX`）

### 价格验证

- 必须 > 0
- 小数点后最多2位（数据库存储为float）

### 库存验证

- 必须 >= 0
- 整数

### 文化标签验证

- 最多20个标签
- 自动去重和空值过滤
- 每个标签最多255字符

### 状态验证

- 仅允许：`draft`, `active`, `inactive`

## 性能优化

### 数据库索引

- 单列索引用于常见查询（SKU、名称、类别、地区）
- 复合索引用于高频查询（类别+状态、地区+状态）
- 排序索引（created_at、updated_at）

### 查询优化

- 列表查询使用分页（默认10条/页，最多100条）
- 搜索使用LIKE模糊匹配
- 排序字段限制在预定义范围内

### 缓存建议

- 使用Redis缓存热门产品列表
- 缓存分类和地区列表（变化不频繁）
- TTL设置为1小时

## 测试示例

### 创建产品

```bash
curl -X POST "http://localhost:8000/api/v1/products" \
  -H "Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGc..." \
  -H "Content-Type: application/json" \
  -d '{
    "sku": "PROD-001",
    "name": "草原牛肉",
    "category": "肉类",
    "price": 199.99,
    "stock": 100,
    "region": "内蒙古",
    "status": "active"
  }'
```

### 获取产品列表

```bash
curl "http://localhost:8000/api/v1/products?page=1&size=10&category=肉类&sort_by=price&sort_order=asc"
```

### 获取产品详情

```bash
curl "http://localhost:8000/api/v1/products/1"
```

### 更新产品

```bash
curl -X PUT "http://localhost:8000/api/v1/products/1" \
  -H "Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGc..." \
  -H "Content-Type: application/json" \
  -d '{
    "price": 249.99,
    "stock": 150
  }'
```

### 删除产品

```bash
curl -X DELETE "http://localhost:8000/api/v1/products/1" \
  -H "Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGc..."
```

## 相关文件

- **模型:** `/backend/app/models/product.py`
- **Schema:** `/backend/app/schemas/products.py`
- **服务:** `/backend/app/services/product_service.py`
- **路由:** `/backend/app/api/products.py`
- **文档:** 此文件

## TODO

- [ ] 实现数据库连接管理
- [ ] 实现JWT认证和管理员权限验证
- [ ] 添加请求日志和错误日志
- [ ] 实现Redis缓存层
- [ ] 添加单元测试和集成测试
- [ ] 实现图片上传功能
- [ ] 添加产品评论和评分功能
- [ ] 实现库存管理和预警功能
