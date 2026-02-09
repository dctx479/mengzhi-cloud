# 产品API文档

**产品管理相关API**

Base URL: `http://localhost:8000/api/v1/products`

---

## 目录

- [1. 获取产品列表](#1-获取产品列表)
- [2. 获取产品详情](#2-获取产品详情)
- [3. 创建产品](#3-创建产品)
- [4. 更新产品](#4-更新产品)
- [5. 删除产品](#5-删除产品)
- [6. 获取文化信息](#6-获取文化信息)
- [7. 获取分类列表](#7-获取分类列表)
- [8. 获取产地列表](#8-获取产地列表)
- [9. 获取统计信息](#9-获取统计信息)

---

## 1. 获取产品列表

获取产品列表，支持分页、搜索、筛选和排序。

### 端点信息

```
GET /api/v1/products
```

### 查询参数

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| page | integer | 否 | 1 | 页码，≥1 |
| size | integer | 否 | 10 | 每页数量，1-100 |
| search | string | 否 | - | 搜索关键词（名称、SKU）|
| category | string | 否 | - | 产品类别筛选 |
| region | string | 否 | - | 产地区域筛选 |
| status | string | 否 | - | 产品状态：draft/active/inactive |
| is_featured | boolean | 否 | - | 是否精选产品 |
| sort_by | string | 否 | created_at | 排序字段：created_at/price/name/updated_at |
| sort_order | string | 否 | desc | 排序顺序：asc/desc |

### 请求示例

#### curl

```bash
# 基础查询
curl -X GET "http://localhost:8000/api/v1/products?page=1&size=10"

# 带搜索和筛选
curl -X GET "http://localhost:8000/api/v1/products?search=牛肉&category=肉类&region=内蒙古&is_featured=true"

# 按价格排序
curl -X GET "http://localhost:8000/api/v1/products?sort_by=price&sort_order=asc"
```

#### JavaScript

```javascript
// 构建查询参数
const params = new URLSearchParams({
  page: 1,
  size: 10,
  search: '牛肉',
  category: '肉类',
  region: '内蒙古',
  is_featured: true,
  sort_by: 'price',
  sort_order: 'asc'
});

const response = await fetch(`http://localhost:8000/api/v1/products?${params}`);
const data = await response.json();
console.log(data);
```

#### Python

```python
import requests

url = 'http://localhost:8000/api/v1/products'
params = {
    'page': 1,
    'size': 10,
    'search': '牛肉',
    'category': '肉类',
    'region': '内蒙古',
    'is_featured': True,
    'sort_by': 'price',
    'sort_order': 'asc'
}

response = requests.get(url, params=params)
print(response.json())
```

### 响应示例

#### 成功响应（200 OK）

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
      },
      {
        "id": 2,
        "sku": "PROD-002",
        "name": "草原羊肉",
        "category": "肉类",
        "price": 149.99,
        "stock": 80,
        "region": "内蒙古锡林郭勒",
        "status": "active",
        "is_featured": false,
        "created_at": "[项目完成日期]T09:00:00"
      }
    ],
    "pagination": {
      "page": 1,
      "size": 10,
      "total": 50,
      "pages": 5,
      "has_next": true,
      "has_prev": false
    }
  },
  "timestamp": "[项目完成日期]T10:00:00"
}
```

### 错误码

| 错误码 | HTTP状态码 | 说明 |
|--------|-----------|------|
| 10005 | 400 | 参数值无效（排序字段不支持）|
| 50000 | 500 | 系统错误 |

### 注意事项

- 支持的排序字段：created_at, price, name, updated_at
- search字段会同时匹配产品名称和SKU
- 分页最大支持每页100条记录

---

## 2. 获取产品详情

根据产品ID获取详细信息。

### 端点信息

```
GET /api/v1/products/{product_id}
```

### 路径参数

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| product_id | integer | 是 | 产品ID |

### 请求示例

#### curl

```bash
curl -X GET "http://localhost:8000/api/v1/products/1"
```

#### JavaScript

```javascript
const productId = 1;
const response = await fetch(`http://localhost:8000/api/v1/products/${productId}`);
const data = await response.json();
console.log(data.data);
```

#### Python

```python
import requests

product_id = 1
url = f'http://localhost:8000/api/v1/products/{product_id}'

response = requests.get(url)
print(response.json())
```

### 响应示例

#### 成功响应（200 OK）

```json
{
  "code": 200,
  "message": "获取产品详情成功",
  "data": {
    "id": 1,
    "sku": "PROD-001",
    "name": "草原牛肉",
    "description": "来自内蒙古草原的优质牛肉，自然放牧，肉质鲜嫩",
    "category": "肉类",
    "price": 199.99,
    "cost": 100.0,
    "stock": 100,
    "region": "内蒙古呼伦贝尔",
    "region_code": "NMG-HLB",
    "cultural_tags": ["草原", "有机", "绿色"],
    "cultural_description": "传统草原养殖文化，牛群自由放牧于广袤草原",
    "origin_story": "草原牛自由放牧在呼伦贝尔大草原，以天然牧草为食...",
    "efficacy": "营养丰富，富含蛋白质和铁元素，易消化吸收",
    "usage": "适合烧烤、炖汤、炒菜等多种烹饪方式",
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

#### 失败响应（404 Not Found）

```json
{
  "code": 40010,
  "message": "记录不存在",
  "data": null,
  "timestamp": "[项目完成日期]T10:00:00",
  "request_id": "uuid-v4"
}
```

### 错误码

| 错误码 | HTTP状态码 | 说明 |
|--------|-----------|------|
| 40010 | 404 | 产品不存在 |
| 50000 | 500 | 系统错误 |

---

## 3. 创建产品

创建新产品（仅管理员）。

### 端点信息

```
POST /api/v1/products
```

### 请求Header

```
Authorization: Bearer {access_token}
```

### 请求参数

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| sku | string | 是 | 产品SKU，1-50字符 |
| name | string | 是 | 产品名称，1-255字符 |
| description | string | 否 | 产品描述，最长2000字符 |
| category | string | 是 | 产品类别，1-100字符 |
| price | number | 是 | 产品价格（元），>0 |
| cost | number | 否 | 产品成本（元），≥0 |
| stock | integer | 否 | 库存数量，≥0，默认0 |
| region | string | 是 | 产地区域，1-100字符 |
| region_code | string | 否 | 产地代码，最长20字符 |
| cultural_tags | array | 否 | 文化标签列表，最多20个 |
| cultural_description | string | 否 | 文化介绍，最长2000字符 |
| origin_story | string | 否 | 产品起源故事，最长3000字符 |
| efficacy | string | 否 | 产品功效说明，最长2000字符 |
| usage | string | 否 | 产品使用方法，最长2000字符 |
| status | string | 否 | 产品状态：draft/active/inactive，默认draft |
| is_featured | boolean | 否 | 是否精选产品，默认false |

### 请求示例

#### curl

```bash
curl -X POST "http://localhost:8000/api/v1/products" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..." \
  -H "Content-Type: application/json" \
  -d '{
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
    "is_featured": true
  }'
```

#### JavaScript

```javascript
const accessToken = localStorage.getItem('access_token');

const response = await fetch('http://localhost:8000/api/v1/products', {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${accessToken}`,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    sku: 'PROD-001',
    name: '草原牛肉',
    description: '来自内蒙古草原的优质牛肉',
    category: '肉类',
    price: 199.99,
    cost: 100.0,
    stock: 100,
    region: '内蒙古呼伦贝尔',
    region_code: 'NMG-HLB',
    cultural_tags: ['草原', '有机', '绿色'],
    status: 'active',
    is_featured: true
  })
});

const data = await response.json();
console.log(data);
```

#### Python

```python
import requests

url = 'http://localhost:8000/api/v1/products'
headers = {
    'Authorization': f'Bearer {access_token}',
    'Content-Type': 'application/json'
}
payload = {
    'sku': 'PROD-001',
    'name': '草原牛肉',
    'description': '来自内蒙古草原的优质牛肉',
    'category': '肉类',
    'price': 199.99,
    'cost': 100.0,
    'stock': 100,
    'region': '内蒙古呼伦贝尔',
    'region_code': 'NMG-HLB',
    'cultural_tags': ['草原', '有机', '绿色'],
    'status': 'active',
    'is_featured': True
}

response = requests.post(url, headers=headers, json=payload)
print(response.json())
```

### 响应示例

#### 成功响应（201 Created）

```json
{
  "code": 200,
  "message": "产品创建成功",
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

### 错误码

| 错误码 | HTTP状态码 | 说明 |
|--------|-----------|------|
| 10001 | 400 | 参数验证失败 |
| 20020 | 403 | 权限不足（非管理员）|
| 40011 | 409 | SKU已存在 |
| 50000 | 500 | 系统错误 |

---

## 4. 更新产品

更新现有产品信息（仅管理员）。

### 端点信息

```
PUT /api/v1/products/{product_id}
```

### 请求Header

```
Authorization: Bearer {access_token}
```

### 路径参数

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| product_id | integer | 是 | 产品ID |

### 请求参数

所有字段都是可选的，只更新提供的字段。参数定义参考"创建产品"接口。

### 请求示例

#### curl

```bash
curl -X PUT "http://localhost:8000/api/v1/products/1" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..." \
  -H "Content-Type: application/json" \
  -d '{
    "name": "高级草原牛肉",
    "price": 249.99,
    "stock": 150,
    "status": "active"
  }'
```

#### JavaScript

```javascript
const accessToken = localStorage.getItem('access_token');
const productId = 1;

const response = await fetch(`http://localhost:8000/api/v1/products/${productId}`, {
  method: 'PUT',
  headers: {
    'Authorization': `Bearer ${accessToken}`,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    name: '高级草原牛肉',
    price: 249.99,
    stock: 150,
    status: 'active'
  })
});

const data = await response.json();
console.log(data);
```

#### Python

```python
import requests

product_id = 1
url = f'http://localhost:8000/api/v1/products/{product_id}'
headers = {
    'Authorization': f'Bearer {access_token}',
    'Content-Type': 'application/json'
}
payload = {
    'name': '高级草原牛肉',
    'price': 249.99,
    'stock': 150,
    'status': 'active'
}

response = requests.put(url, headers=headers, json=payload)
print(response.json())
```

### 响应示例

#### 成功响应（200 OK）

```json
{
  "code": 200,
  "message": "产品更新成功",
  "data": {
    "id": 1,
    "sku": "PROD-001",
    "name": "高级草原牛肉",
    "price": 249.99,
    "stock": 150,
    "status": "active",
    "updated_at": "[项目完成日期]T11:00:00"
  },
  "timestamp": "[项目完成日期]T11:00:00"
}
```

### 错误码

| 错误码 | HTTP状态码 | 说明 |
|--------|-----------|------|
| 10000 | 400 | 请求体不能为空 |
| 10001 | 400 | 参数验证失败 |
| 20020 | 403 | 权限不足（非管理员）|
| 40010 | 404 | 产品不存在 |
| 50000 | 500 | 系统错误 |

---

## 5. 删除产品

删除产品（仅管理员）。

### 端点信息

```
DELETE /api/v1/products/{product_id}
```

### 请求Header

```
Authorization: Bearer {access_token}
```

### 路径参数

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| product_id | integer | 是 | 产品ID |

### 请求示例

#### curl

```bash
curl -X DELETE "http://localhost:8000/api/v1/products/1" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

#### JavaScript

```javascript
const accessToken = localStorage.getItem('access_token');
const productId = 1;

const response = await fetch(`http://localhost:8000/api/v1/products/${productId}`, {
  method: 'DELETE',
  headers: {
    'Authorization': `Bearer ${accessToken}`
  }
});

const data = await response.json();
console.log(data);
```

#### Python

```python
import requests

product_id = 1
url = f'http://localhost:8000/api/v1/products/{product_id}'
headers = {
    'Authorization': f'Bearer {access_token}'
}

response = requests.delete(url, headers=headers)
print(response.json())
```

### 响应示例

#### 成功响应（200 OK）

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

### 错误码

| 错误码 | HTTP状态码 | 说明 |
|--------|-----------|------|
| 20020 | 403 | 权限不足（非管理员）|
| 40010 | 404 | 产品不存在 |
| 50000 | 500 | 系统错误 |

### 注意事项

- 删除操作是软删除，数据不会真正删除
- 删除后产品状态变为"deleted"，不会在列表中显示

---

## 6. 获取文化信息

获取产品的文化相关信息。

### 端点信息

```
GET /api/v1/products/{product_id}/cultural-info
```

### 路径参数

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| product_id | integer | 是 | 产品ID |

### 请求示例

#### curl

```bash
curl -X GET "http://localhost:8000/api/v1/products/1/cultural-info"
```

#### JavaScript

```javascript
const productId = 1;
const response = await fetch(`http://localhost:8000/api/v1/products/${productId}/cultural-info`);
const data = await response.json();
console.log(data.data);
```

#### Python

```python
import requests

product_id = 1
url = f'http://localhost:8000/api/v1/products/{product_id}/cultural-info'

response = requests.get(url)
print(response.json())
```

### 响应示例

#### 成功响应（200 OK）

```json
{
  "code": 200,
  "message": "获取文化信息成功",
  "data": {
    "cultural_tags": ["草原", "有机", "绿色"],
    "cultural_description": "传统草原养殖文化，牛群自由放牧于广袤草原",
    "origin_story": "草原牛自由放牧在呼伦贝尔大草原，以天然牧草为食，遵循自然生长规律...",
    "efficacy": "营养丰富，富含蛋白质和铁元素，易消化吸收",
    "usage": "适合烧烤、炖汤、炒菜等多种烹饪方式",
    "region": "内蒙古呼伦贝尔",
    "region_code": "NMG-HLB"
  },
  "timestamp": "[项目完成日期]T10:00:00"
}
```

### 错误码

| 错误码 | HTTP状态码 | 说明 |
|--------|-----------|------|
| 40010 | 404 | 产品不存在 |
| 50000 | 500 | 系统错误 |

---

## 7. 获取分类列表

获取所有产品类别列表。

### 端点信息

```
GET /api/v1/products/categories/list
```

### 请求示例

#### curl

```bash
curl -X GET "http://localhost:8000/api/v1/products/categories/list"
```

#### JavaScript

```javascript
const response = await fetch('http://localhost:8000/api/v1/products/categories/list');
const data = await response.json();
console.log(data.data.categories);
```

#### Python

```python
import requests

url = 'http://localhost:8000/api/v1/products/categories/list'
response = requests.get(url)
print(response.json())
```

### 响应示例

#### 成功响应（200 OK）

```json
{
  "code": 200,
  "message": "获取类别列表成功",
  "data": {
    "categories": [
      "肉类",
      "奶制品",
      "粮食",
      "蔬菜",
      "水果",
      "特色食品"
    ]
  },
  "timestamp": "[项目完成日期]T10:00:00"
}
```

---

## 8. 获取产地列表

获取所有产地区域列表。

### 端点信息

```
GET /api/v1/products/regions/list
```

### 请求示例

#### curl

```bash
curl -X GET "http://localhost:8000/api/v1/products/regions/list"
```

#### JavaScript

```javascript
const response = await fetch('http://localhost:8000/api/v1/products/regions/list');
const data = await response.json();
console.log(data.data.regions);
```

#### Python

```python
import requests

url = 'http://localhost:8000/api/v1/products/regions/list'
response = requests.get(url)
print(response.json())
```

### 响应示例

#### 成功响应（200 OK）

```json
{
  "code": 200,
  "message": "获取地区列表成功",
  "data": {
    "regions": [
      "内蒙古呼和浩特",
      "内蒙古包头",
      "内蒙古呼伦贝尔",
      "内蒙古兴安盟",
      "内蒙古通辽",
      "内蒙古赤峰",
      "内蒙古锡林郭勒",
      "内蒙古乌兰察布",
      "内蒙古鄂尔多斯",
      "内蒙古巴彦淖尔",
      "内蒙古乌海",
      "内蒙古阿拉善"
    ]
  },
  "timestamp": "[项目完成日期]T10:00:00"
}
```

---

## 9. 获取统计信息

获取产品统计信息。

### 端点信息

```
GET /api/v1/products/statistics
```

### 请求示例

#### curl

```bash
curl -X GET "http://localhost:8000/api/v1/products/statistics"
```

#### JavaScript

```javascript
const response = await fetch('http://localhost:8000/api/v1/products/statistics');
const data = await response.json();
console.log(data.data);
```

#### Python

```python
import requests

url = 'http://localhost:8000/api/v1/products/statistics'
response = requests.get(url)
print(response.json())
```

### 响应示例

#### 成功响应（200 OK）

```json
{
  "code": 200,
  "message": "获取统计信息成功",
  "data": {
    "total_products": 150,
    "active_products": 120,
    "inactive_products": 20,
    "draft_products": 10,
    "featured_products": 30,
    "total_categories": 6,
    "total_regions": 12,
    "out_of_stock_products": 5,
    "low_stock_products": 15
  },
  "timestamp": "[项目完成日期]T10:00:00"
}
```

### 字段说明

| 字段 | 说明 |
|------|------|
| total_products | 总产品数 |
| active_products | 激活状态产品数 |
| inactive_products | 未激活产品数 |
| draft_products | 草稿状态产品数 |
| featured_products | 精选产品数 |
| total_categories | 产品类别数 |
| total_regions | 产地区域数 |
| out_of_stock_products | 缺货产品数 |
| low_stock_products | 库存不足产品数（<10）|

---

## 常见问题

### Q: 如何实现产品搜索？

A: 使用search参数，会同时匹配产品名称和SKU：

```javascript
const response = await fetch('/api/v1/products?search=牛肉');
```

### Q: 如何组合多个筛选条件？

A: 所有筛选参数都可以组合使用：

```javascript
const params = new URLSearchParams({
  category: '肉类',
  region: '内蒙古呼伦贝尔',
  is_featured: true,
  status: 'active',
  sort_by: 'price',
  sort_order: 'asc'
});

const response = await fetch(`/api/v1/products?${params}`);
```

### Q: 如何实现无限滚动？

A: 通过递增page参数，检查has_next判断是否还有数据：

```javascript
let page = 1;
let hasNext = true;

async function loadMore() {
  if (!hasNext) return;

  const response = await fetch(`/api/v1/products?page=${page}&size=20`);
  const data = await response.json();

  // 追加数据
  products.push(...data.data.items);

  // 更新状态
  hasNext = data.data.pagination.has_next;
  page++;
}
```

### Q: 管理员权限如何验证？

A: 通过JWT Token中的role字段验证，非admin角色无法访问创建/更新/删除接口。

---

**文档版本**: v1.0
**最后更新**: [项目完成日期]
