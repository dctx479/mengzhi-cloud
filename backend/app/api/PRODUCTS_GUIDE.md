# 产品模型 API 使用指南

本文档提供关键文件的使用和集成方法。

## 文件概览

### 1. models/product.py - 数据模型

定义SQLAlchemy ORM模型，对应数据库表。

**主要特性:**
- SQLAlchemy declarative base
- 自动时间戳（created_at, updated_at）
- JSON字段支持（cultural_tags）
- 复合索引优化查询性能

**关键方法:**
```python
product = Product(...)  # 创建实例
product.to_dict()       # 转换为字典
```

### 2. schemas/products.py - 请求/响应Schema

使用Pydantic定义API请求和响应格式。

**Schema分类:**
- `ProductCreateRequest` - 创建请求
- `ProductUpdateRequest` - 更新请求
- `ProductDetailResponse` - 详情响应
- `ProductListItemResponse` - 列表响应
- `CulturalInfoResponse` - 文化信息响应
- `ProductListQuery` - 查询参数

**特点:**
- 完整的字段验证
- JSON schema示例
- 自动文档生成

### 3. services/product_service.py - 业务逻辑

核心业务逻辑实现。

**方法分类:**

**CRUD操作:**
- `create_product()` - 创建
- `get_product_by_id()` - 获取单个
- `update_product()` - 更新
- `delete_product()` - 删除

**查询操作:**
- `list_products()` - 列表查询
- `get_featured_products()` - 精选产品
- `get_products_by_category()` - 分类查询
- `get_products_by_region()` - 地区查询

**统计操作:**
- `get_product_statistics()` - 统计信息
- `get_categories()` - 分类列表
- `get_regions()` - 地区列表

### 4. api/products.py - API路由

FastAPI路由定义，实现RESTful端点。

**6个主要端点:**
1. GET /api/v1/products
2. GET /api/v1/products/{id}
3. POST /api/v1/products
4. PUT /api/v1/products/{id}
5. DELETE /api/v1/products/{id}
6. GET /api/v1/products/{id}/cultural-info

**附加端点:**
- GET /api/v1/products/categories/list
- GET /api/v1/products/regions/list
- GET /api/v1/products/statistics

## 集成步骤

### Step 1: 注册路由

在 `backend/app/main.py` 中添加：

```python
from app.api import products

# 注册产品路由
app.include_router(products.router, prefix="/api/v1", tags=["产品"])
```

### Step 2: 实现依赖项

#### 数据库连接

```python
# backend/app/core/database.py (新建)
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from app.core.config import settings

engine = create_engine(settings.DATABASE_URL, echo=False)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db() -> Session:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

在 `products.py` 中：

```python
from app.core.database import get_db

# 已在依赖项中定义
```

#### JWT认证

```python
# backend/app/core/auth.py (新建)
from fastapi import HTTPException, status
from jose import JWTError, jwt
from app.core.config import settings

def get_current_user_id(token: str) -> int:
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        user_id = payload.get("user_id")
        if user_id is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)
        return user_id
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)
```

在 `products.py` 中更新：

```python
from fastapi import Header

async def get_current_user_id(authorization: str = Header(None)) -> int:
    if not authorization:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)

    token = authorization.replace("Bearer ", "")
    # 解析token获取user_id
    return user_id
```

#### 管理员权限

```python
async def verify_admin(user_id: int = Depends(get_current_user_id)) -> int:
    # 从数据库查询用户角色
    # 判断是否为管理员
    return user_id
```

### Step 3: 初始化数据库

```python
# backend/app/core/database.py
from app.models.product import Base

# 在应用启动时创建表
Base.metadata.create_all(bind=engine)
```

或使用Alembic迁移：

```bash
alembic init
alembic revision --autogenerate -m "Create product table"
alembic upgrade head
```

### Step 4: 环境配置

在 `.env` 文件中配置：

```env
DATABASE_URL=mysql+pymysql://root:root123@localhost:3306/agri_platform?charset=utf8mb4
DEEPSEEK_API_KEY=your_key
SECRET_KEY=your-secret-key-min-32-chars
ALGORITHM=HS256
```

## 使用示例

### 示例1: 创建产品

```python
from app.services.product_service import ProductService
from app.schemas.products import ProductCreateRequest

# 创建请求对象
request = ProductCreateRequest(
    sku="PROD-001",
    name="草原牛肉",
    description="优质牛肉",
    category="肉类",
    price=199.99,
    cost=100.0,
    stock=100,
    region="内蒙古呼伦贝尔",
    cultural_tags=["草原", "有机"]
)

# 使用服务创建
service = ProductService(db)
product = service.create_product(request, user_id=1)
```

### 示例2: 查询产品列表

```python
service = ProductService(db)

# 获取第1页，每页10条，按价格升序排列的活跃产品
products, total = service.list_products(
    page=1,
    size=10,
    status="active",
    sort_by="price",
    sort_order="asc"
)

print(f"总数: {total}, 当前页数据: {len(products)}")
```

### 示例3: 获取分类列表

```python
service = ProductService(db)
categories = service.get_categories()
# ['肉类', '乳制品', '农产品', ...]
```

### 示例4: 获取精选产品

```python
featured = service.get_featured_products(limit=5)
```

### 示例5: 更新产品

```python
from app.schemas.products import ProductUpdateRequest

request = ProductUpdateRequest(
    price=249.99,
    stock=150
)

service = ProductService(db)
product = service.update_product(product_id=1, request=request, user_id=1)
```

## API使用示例

### 使用curl

**创建产品:**
```bash
curl -X POST "http://localhost:8000/api/v1/products" \
  -H "Authorization: Bearer token123" \
  -H "Content-Type: application/json" \
  -d '{
    "sku": "PROD-001",
    "name": "草原牛肉",
    "category": "肉类",
    "price": 199.99,
    "stock": 100,
    "region": "内蒙古"
  }'
```

**获取列表:**
```bash
curl "http://localhost:8000/api/v1/products?category=肉类&status=active"
```

**获取详情:**
```bash
curl "http://localhost:8000/api/v1/products/1"
```

### 使用Python requests

```python
import requests

# 获取产品列表
response = requests.get(
    "http://localhost:8000/api/v1/products",
    params={"page": 1, "size": 10, "category": "肉类"}
)
print(response.json())

# 创建产品
response = requests.post(
    "http://localhost:8000/api/v1/products",
    headers={"Authorization": f"Bearer {token}"},
    json={
        "sku": "PROD-001",
        "name": "草原牛肉",
        "price": 199.99,
        "stock": 100,
        "region": "内蒙古"
    }
)
print(response.status_code, response.json())
```

## 错误处理

### 捕获业务异常

```python
from app.core.errors import BusinessException

try:
    product = service.get_product_by_id(999)
except BusinessException as e:
    print(f"错误码: {e.code}, 消息: {e.message}")
    http_status = e.get_http_status()
```

### API错误响应

```python
from app.core.responses import error_response
from app.core.errors import ErrorCode

response = error_response(
    code=ErrorCode.RECORD_NOT_FOUND,
    message="产品不存在"
)
```

## 验证规则

### SKU验证
- 长度：1-50字符
- 必须唯一
- 不能包含特殊字符（推荐：字母、数字、连字符）

### 价格验证
- 必须 > 0
- 支持小数（最多2位）

### 库存验证
- 必须 >= 0
- 必须是整数

### 文化标签验证
- 最多20个标签
- 自动去重
- 自动过滤空值

### 分页验证
- page >= 1
- 1 <= size <= 100

## 性能考虑

### 查询优化

1. **使用分页**
   ```python
   products, total = service.list_products(page=1, size=10)
   ```

2. **精确筛选**
   ```python
   products, total = service.list_products(
       status="active",
       category="肉类"
   )
   ```

3. **避免N+1查询**
   - 已在服务层优化

### 缓存建议

```python
from functools import lru_cache
import redis

redis_client = redis.Redis(host='localhost', port=6379, db=0)

# 缓存分类列表
def get_categories_cached():
    cached = redis_client.get('product_categories')
    if cached:
        return json.loads(cached)

    categories = service.get_categories()
    redis_client.setex('product_categories', 3600, json.dumps(categories))
    return categories
```

## 扩展功能

### 添加图片支持

```python
# models/product.py 中添加：
class Product(Base):
    # ...
    image_url = Column(String(500), nullable=True)
    images = Column(JSON, nullable=True)  # 多张图片
```

### 添加评论和评分

```python
class ProductReview(Base):
    __tablename__ = "product_reviews"

    id = Column(Integer, primary_key=True)
    product_id = Column(Integer, ForeignKey('products.id'))
    user_id = Column(Integer)
    rating = Column(Integer)  # 1-5
    comment = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
```

### 库存预警

```python
def check_low_stock(threshold: int = 10):
    service = ProductService(db)
    low_stock = db.query(Product).filter(Product.stock < threshold).all()
    # 发送预警通知
```

## 常见问题

### Q: 如何批量导入产品？

A: 创建批量导入端点：

```python
@router.post("/products/batch", response_model=dict)
async def batch_import(
    file: UploadFile = File(...),
    user_id: int = Depends(verify_admin),
    db: Session = Depends(get_db)
):
    # 读取CSV/Excel文件
    # 批量创建产品
    pass
```

### Q: 如何导出产品列表？

A: 创建导出端点：

```python
@router.get("/products/export", response_class=FileResponse)
async def export_products(db: Session = Depends(get_db)):
    # 生成CSV/Excel文件
    # 返回文件
    pass
```

### Q: 如何实现产品搜索自动完成？

A: 添加搜索端点：

```python
@router.get("/products/search/autocomplete")
async def autocomplete(
    q: str = Query(..., min_length=1),
    db: Session = Depends(get_db)
):
    service = ProductService(db)
    # 搜索SKU和名称
    products = service.list_products(search=q, size=5)
    return {"suggestions": [p.name for p in products]}
```
