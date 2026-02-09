# 产品API

## 获取产品列表

**GET** `/v1/products`

### 查询参数

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| page | number | 否 | 1 | 页码 |
| pageSize | number | 否 | 20 | 每页数量 |
| category | string | 否 | - | 分类ID |
| keyword | string | 否 | - | 搜索关键词 |
| sortBy | string | 否 | newest | 排序方式: newest, popular, priceHigh, priceLow |
| priceMin | number | 否 | - | 最低价格 |
| priceMax | number | 否 | - | 最高价格 |
| regions | string[] | 否 | - | 产地筛选 |
| culturalTags | string[] | 否 | - | 文化标签筛选 |
| certifications | string[] | 否 | - | 认证筛选 |

### 响应示例

```json
{
  "data": [
    {
      "id": "prod_123",
      "name": "有机苹果",
      "description": "来自山东烟台的优质有机苹果",
      "price": 29.9,
      "originalPrice": 39.9,
      "image": "https://example.com/apple.jpg",
      "images": [
        "https://example.com/apple1.jpg",
        "https://example.com/apple2.jpg"
      ],
      "category": "水果",
      "categoryId": "cat_001",
      "rating": 4.8,
      "reviewCount": 128,
      "inStock": true,
      "stockCount": 500,
      "origin": "山东烟台",
      "region": "华东",
      "location": {
        "latitude": 37.5365,
        "longitude": 121.3998
      },
      "culturalTags": [
        {
          "id": "tag_001",
          "name": "地理标志",
          "icon": "🏷️",
          "description": "国家地理标志产品"
        }
      ],
      "hasOrganic": true,
      "hasGeo": true,
      "hasQuality": true,
      "unit": "斤",
      "supplier": "烟台果业",
      "createdAt": "2024-01-01T00:00:00Z",
      "updatedAt": "2024-01-01T00:00:00Z"
    }
  ],
  "total": 100,
  "page": 1,
  "pageSize": 20
}
```

### cURL示例

```bash
# 基础查询
curl -X GET "http://localhost:3000/api/v1/products?page=1&pageSize=20"

# 分类筛选
curl -X GET "http://localhost:3000/api/v1/products?category=cat_001"

# 价格区间筛选
curl -X GET "http://localhost:3000/api/v1/products?priceMin=10&priceMax=50"

# 关键词搜索
curl -X GET "http://localhost:3000/api/v1/products?keyword=苹果"

# 综合筛选
curl -X GET "http://localhost:3000/api/v1/products?category=cat_001&priceMin=20&priceMax=100&sortBy=popular"
```

---

## 获取产品详情

**GET** `/v1/products/:id`

### 路径参数

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| id | string | 是 | 产品ID |

### 响应示例

```json
{
  "id": "prod_123",
  "name": "有机苹果",
  "description": "来自山东烟台的优质有机苹果，口感脆甜，营养丰富",
  "price": 29.9,
  "originalPrice": 39.9,
  "image": "https://example.com/apple.jpg",
  "images": [
    "https://example.com/apple1.jpg",
    "https://example.com/apple2.jpg",
    "https://example.com/apple3.jpg"
  ],
  "category": "水果",
  "categoryId": "cat_001",
  "rating": 4.8,
  "reviewCount": 128,
  "inStock": true,
  "stockCount": 500,
  "origin": "山东烟台",
  "region": "华东",
  "location": {
    "latitude": 37.5365,
    "longitude": 121.3998
  },
  "culturalTags": [
    {
      "id": "tag_001",
      "name": "地理标志",
      "icon": "🏷️",
      "description": "国家地理标志产品"
    }
  ],
  "hasOrganic": true,
  "hasGeo": true,
  "hasQuality": true,
  "unit": "斤",
  "supplier": "烟台果业",
  "specifications": {
    "产地": "山东烟台",
    "规格": "5斤/箱",
    "保质期": "7天",
    "储存方式": "冷藏"
  },
  "tags": ["有机", "新鲜", "地理标志"],
  "benefits": [
    "富含维生素C",
    "有机认证",
    "产地直供"
  ],
  "relatedProducts": [
    {
      "id": "prod_124",
      "name": "有机梨",
      "price": 24.9,
      "image": "https://example.com/pear.jpg"
    }
  ],
  "createdAt": "2024-01-01T00:00:00Z",
  "updatedAt": "2024-01-01T00:00:00Z"
}
```

### cURL示例

```bash
curl -X GET http://localhost:3000/api/v1/products/prod_123
```

---

## 获取产品分类

**GET** `/v1/products/categories`

### 响应示例

```json
[
  {
    "id": "cat_001",
    "name": "水果",
    "icon": "🍎",
    "description": "新鲜水果",
    "productCount": 150
  },
  {
    "id": "cat_002",
    "name": "蔬菜",
    "icon": "🥬",
    "description": "有机蔬菜",
    "productCount": 200
  },
  {
    "id": "cat_003",
    "name": "粮油",
    "icon": "🌾",
    "description": "优质粮油",
    "productCount": 80
  }
]
```

### cURL示例

```bash
curl -X GET http://localhost:3000/api/v1/products/categories
```

---

## 搜索产品

**GET** `/v1/products/search`

### 查询参数

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| keyword | string | 是 | 搜索关键词 |

### 响应示例

```json
[
  {
    "id": "prod_123",
    "name": "有机苹果",
    "description": "来自山东烟台的优质有机苹果",
    "price": 29.9,
    "image": "https://example.com/apple.jpg",
    "category": "水果",
    "categoryId": "cat_001",
    "rating": 4.8,
    "reviewCount": 128,
    "inStock": true
  }
]
```

### cURL示例

```bash
curl -X GET "http://localhost:3000/api/v1/products/search?keyword=苹果"
```

---

## 获取热门产品

**GET** `/v1/products/popular`

### 查询参数

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| limit | number | 否 | 10 | 返回数量 |

### 响应示例

```json
[
  {
    "id": "prod_123",
    "name": "有机苹果",
    "price": 29.9,
    "image": "https://example.com/apple.jpg",
    "rating": 4.8,
    "reviewCount": 128
  }
]
```

### cURL示例

```bash
curl -X GET "http://localhost:3000/api/v1/products/popular?limit=10"
```

---

## 获取产品评价

**GET** `/v1/products/:id/reviews`

### 路径参数

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| id | string | 是 | 产品ID |

### 查询参数

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| page | number | 否 | 1 | 页码 |
| pageSize | number | 否 | 10 | 每页数量 |

### 响应示例

```json
{
  "data": [
    {
      "id": "review_001",
      "productId": "prod_123",
      "userId": "user_123",
      "userName": "张三",
      "userAvatar": "https://example.com/avatar.jpg",
      "rating": 5,
      "comment": "非常好吃，新鲜又甜！",
      "createdAt": "2024-01-01T00:00:00Z"
    }
  ],
  "total": 128
}
```

### cURL示例

```bash
curl -X GET "http://localhost:3000/api/v1/products/prod_123/reviews?page=1&pageSize=10"
```

---

## 添加产品评价

**POST** `/v1/products/:id/reviews`

需要认证。

### 路径参数

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| id | string | 是 | 产品ID |

### 请求参数

```json
{
  "rating": 5,
  "comment": "非常好吃，新鲜又甜！"
}
```

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| rating | number | 是 | 评分 (1-5) |
| comment | string | 是 | 评价内容 |

### 响应示例

```json
{
  "id": "review_001",
  "productId": "prod_123",
  "userId": "user_123",
  "userName": "张三",
  "userAvatar": "https://example.com/avatar.jpg",
  "rating": 5,
  "comment": "非常好吃，新鲜又甜！",
  "createdAt": "2024-01-01T00:00:00Z"
}
```

### cURL示例

```bash
curl -X POST http://localhost:3000/api/v1/products/prod_123/reviews \
  -H "Authorization: Bearer <your_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "rating": 5,
    "comment": "非常好吃，新鲜又甜！"
  }'
```

---

## 错误处理

### 常见错误

| 错误码 | HTTP状态码 | 说明 |
|--------|-----------|------|
| PRODUCT_NOT_FOUND | 404 | 产品不存在 |
| INVALID_CATEGORY | 400 | 无效的分类 |
| INVALID_PRICE_RANGE | 400 | 价格区间无效 |
| REVIEW_EXISTS | 409 | 已评价过该产品 |
| INVALID_RATING | 400 | 评分必须在1-5之间 |
