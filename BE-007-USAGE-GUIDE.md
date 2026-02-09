# 文化标签管理系统使用指南

## 快速开始

### 1. 数据库迁移

```bash
cd backend
alembic upgrade head
```

### 2. 初始化默认标签

```bash
python scripts/init_cultural_tags.py
```

输出示例:
```
开始初始化默认文化标签...
默认文化标签初始化完成！创建了 25 个标签
标签统计:
  - 总标签数: 25
  - 启用标签数: 25
  - 分类分布:
    * 地理标志: 5 个
    * 民族文化: 3 个
    * 历史传承: 3 个
    * 工艺特色: 4 个
    * 节日习俗: 3 个
    * 营养价值: 4 个
    * 文化故事: 3 个
```

---

## API使用示例

### 基础URL
```
开发环境: http://localhost:8000/api/v1
生产环境: https://your-domain.com/api/v1
```

### 1. 获取标签分类列表

**请求**:
```http
GET /api/v1/cultural-tags/categories
```

**响应**:
```json
{
  "code": 200,
  "message": "获取标签分类列表成功",
  "data": {
    "categories": [
      {
        "code": "geo",
        "name": "地理标志",
        "icon": "🗺️",
        "description": "地理标志产品认证",
        "tag_count": 5
      },
      {
        "code": "ethnicity",
        "name": "民族文化",
        "icon": "🎭",
        "description": "蒙古族等民族传统文化",
        "tag_count": 3
      }
    ]
  }
}
```

### 2. 获取标签列表（分页、搜索、筛选）

**请求**:
```http
GET /api/v1/cultural-tags?category=geo&keyword=羊肉&page=1&page_size=20&is_active=true
```

**参数说明**:
- `category` (可选): 标签分类，可选值: geo/ethnicity/history/craft/festival/nutrition/story
- `keyword` (可选): 搜索关键词（在标签名称、描述、关键词中搜索）
- `is_active` (可选): 是否只显示启用的标签，默认true
- `page` (可选): 页码，默认1
- `page_size` (可选): 每页数量，默认50，最大100

**响应**:
```json
{
  "code": 200,
  "message": "获取文化标签列表成功",
  "data": [
    {
      "id": 1,
      "name": "锡林郭勒羊肉",
      "category": "geo",
      "usage_count": 15,
      "is_active": true
    }
  ],
  "pagination": {
    "page": 1,
    "page_size": 20,
    "total": 1,
    "total_pages": 1,
    "has_next": false,
    "has_prev": false
  }
}
```

### 3. 获取标签详情

**请求**:
```http
GET /api/v1/cultural-tags/1
```

**响应**:
```json
{
  "code": 200,
  "message": "获取标签详情成功",
  "data": {
    "id": 1,
    "name": "锡林郭勒羊肉",
    "category": "geo",
    "description": "锡林郭勒盟特产，国家地理标志产品，以肉质鲜嫩、无膻味著称",
    "keywords": "羊肉,地理标志,锡林郭勒,草原",
    "parent_id": null,
    "usage_count": 15,
    "is_active": true,
    "created_at": "[项目完成日期]T14:00:00Z",
    "updated_at": "[项目完成日期]T14:00:00Z"
  }
}
```

### 4. 推荐标签

#### 方式1: 基于产品推荐（协同过滤）
```http
GET /api/v1/cultural-tags/recommend?product_id=1&limit=10
```

#### 方式2: 基于关键词推荐
```http
GET /api/v1/cultural-tags/recommend?keywords=羊肉 草原&limit=10
```

#### 方式3: 热门标签（不提供参数）
```http
GET /api/v1/cultural-tags/recommend?limit=10
```

**响应**:
```json
{
  "code": 200,
  "message": "标签推荐成功",
  "data": {
    "tags": [
      {
        "id": 6,
        "name": "蒙古族传统",
        "category": "ethnicity",
        "usage_count": 10,
        "is_active": true
      }
    ]
  }
}
```

### 5. 获取标签统计信息

**请求**:
```http
GET /api/v1/cultural-tags/statistics
```

**响应**:
```json
{
  "code": 200,
  "message": "获取标签统计成功",
  "data": {
    "total_tags": 25,
    "active_tags": 25,
    "category_distribution": {
      "geo": {
        "name": "地理标志",
        "count": 5
      },
      "ethnicity": {
        "name": "民族文化",
        "count": 3
      }
    },
    "popular_tags": [
      {
        "id": 1,
        "name": "锡林郭勒羊肉",
        "category": "geo",
        "usage_count": 15,
        "is_active": true
      }
    ]
  }
}
```

### 6. 获取使用某标签的产品列表

**请求**:
```http
GET /api/v1/cultural-tags/1/products?page=1&page_size=20
```

**响应**:
```json
{
  "code": 200,
  "message": "获取标签「锡林郭勒羊肉」的产品列表成功",
  "data": [
    {
      "id": 1,
      "name": "优质锡林郭勒羔羊肉",
      "category": "畜产品",
      "status": "published"
    }
  ],
  "pagination": {
    "page": 1,
    "page_size": 20,
    "total": 15
  }
}
```

### 7. 创建标签（管理员）

**请求**:
```http
POST /api/v1/cultural-tags
Authorization: Bearer {admin_token}
Content-Type: application/json

{
  "name": "阿拉善驼绒",
  "category": "geo",
  "description": "阿拉善盟特产驼绒，品质优良，世界顶级",
  "keywords": "驼绒,地理标志,阿拉善,特产",
  "parent_id": null
}
```

**响应**:
```json
{
  "code": 200,
  "message": "文化标签创建成功",
  "data": {
    "id": 26,
    "name": "阿拉善驼绒",
    "category": "geo",
    "description": "阿拉善盟特产驼绒，品质优良，世界顶级",
    "keywords": "驼绒,地理标志,阿拉善,特产",
    "parent_id": null,
    "usage_count": 0,
    "is_active": true,
    "created_at": "[项目完成日期]T14:30:00Z",
    "updated_at": "[项目完成日期]T14:30:00Z"
  }
}
```

### 8. 更新标签（管理员）

**请求**:
```http
PUT /api/v1/cultural-tags/26
Authorization: Bearer {admin_token}
Content-Type: application/json

{
  "description": "更新后的描述：阿拉善盟特产驼绒，稀有珍贵",
  "keywords": "驼绒,地理标志,阿拉善,稀有,珍贵"
}
```

**响应**:
```json
{
  "code": 200,
  "message": "文化标签更新成功",
  "data": {
    "id": 26,
    "name": "阿拉善驼绒",
    "category": "geo",
    "description": "更新后的描述：阿拉善盟特产驼绒，稀有珍贵",
    "keywords": "驼绒,地理标志,阿拉善,稀有,珍贵",
    "usage_count": 0,
    "is_active": true
  }
}
```

### 9. 删除标签（管理员）

**请求**:
```http
DELETE /api/v1/cultural-tags/26
Authorization: Bearer {admin_token}
```

**响应**:
```json
{
  "code": 200,
  "message": "文化标签删除成功",
  "data": {
    "id": 26
  }
}
```

**注意**:
- 如果标签被产品使用，会执行软删除（is_active=false）
- 如果标签未被使用，会执行硬删除

---

## 产品标签管理

### 1. 为产品分配标签

**请求**:
```http
POST /api/v1/products/1/tags
Authorization: Bearer {admin_token}
Content-Type: application/json

{
  "tag_ids": [1, 2, 3, 6]
}
```

**响应**:
```json
{
  "code": 200,
  "message": "产品标签分配成功",
  "data": {
    "product_id": 1,
    "tags": [
      {
        "id": 1,
        "name": "锡林郭勒羊肉",
        "category": "geo",
        "usage_count": 16,
        "is_active": true
      },
      {
        "id": 2,
        "name": "科尔沁牛肉",
        "category": "geo",
        "usage_count": 11,
        "is_active": true
      }
    ]
  }
}
```

**说明**:
- 会自动更新标签的`usage_count`
- 覆盖式分配（之前的标签会被替换）
- 自动验证标签是否存在和启用

### 2. 获取产品的标签

**请求**:
```http
GET /api/v1/products/1/tags
```

**响应**:
```json
{
  "code": 200,
  "message": "获取产品标签成功",
  "data": {
    "product_id": 1,
    "tags": [
      {
        "id": 1,
        "name": "锡林郭勒羊肉",
        "category": "geo",
        "usage_count": 16,
        "is_active": true
      }
    ]
  }
}
```

### 3. 移除产品的单个标签

**请求**:
```http
DELETE /api/v1/products/1/tags/2
Authorization: Bearer {admin_token}
```

**响应**:
```json
{
  "code": 200,
  "message": "产品标签移除成功",
  "data": {
    "product_id": 1,
    "remaining_tags": [
      {
        "id": 1,
        "name": "锡林郭勒羊肉",
        "category": "geo",
        "usage_count": 16,
        "is_active": true
      }
    ]
  }
}
```

---

## Python代码示例

### 使用requests库调用API

```python
import requests

BASE_URL = "http://localhost:8000/api/v1"
ADMIN_TOKEN = "your_admin_token_here"

# 1. 获取标签列表
response = requests.get(f"{BASE_URL}/cultural-tags", params={
    "category": "geo",
    "page": 1,
    "page_size": 20
})
tags = response.json()["data"]
print(f"找到 {len(tags)} 个地理标志标签")

# 2. 创建标签（管理员）
headers = {"Authorization": f"Bearer {ADMIN_TOKEN}"}
new_tag = {
    "name": "新标签",
    "category": "geo",
    "description": "描述",
    "keywords": "关键词1,关键词2"
}
response = requests.post(
    f"{BASE_URL}/cultural-tags",
    headers=headers,
    json=new_tag
)
created_tag = response.json()["data"]
print(f"创建标签成功，ID: {created_tag['id']}")

# 3. 为产品分配标签
product_id = 1
tag_ids = [1, 2, 3]
response = requests.post(
    f"{BASE_URL}/products/{product_id}/tags",
    headers=headers,
    json={"tag_ids": tag_ids}
)
print(f"产品 {product_id} 已分配 {len(tag_ids)} 个标签")

# 4. 推荐标签
response = requests.get(
    f"{BASE_URL}/cultural-tags/recommend",
    params={"product_id": product_id, "limit": 5}
)
recommended_tags = response.json()["data"]["tags"]
print(f"为产品推荐了 {len(recommended_tags)} 个标签")
```

---

## 前端集成示例

### Vue.js示例

```vue
<template>
  <div class="cultural-tags">
    <!-- 标签分类选择 -->
    <div class="category-selector">
      <button
        v-for="category in categories"
        :key="category.code"
        @click="selectCategory(category.code)"
        :class="{ active: selectedCategory === category.code }"
      >
        {{ category.icon }} {{ category.name }} ({{ category.tag_count }})
      </button>
    </div>

    <!-- 标签列表 -->
    <div class="tag-list">
      <div
        v-for="tag in tags"
        :key="tag.id"
        class="tag-item"
        @click="selectTag(tag)"
      >
        <span class="tag-name">{{ tag.name }}</span>
        <span class="tag-count">使用 {{ tag.usage_count }} 次</span>
      </div>
    </div>

    <!-- 分页 -->
    <div class="pagination">
      <button @click="prevPage" :disabled="page === 1">上一页</button>
      <span>第 {{ page }} / {{ totalPages }} 页</span>
      <button @click="nextPage" :disabled="!hasNext">下一页</button>
    </div>
  </div>
</template>

<script>
import axios from 'axios';

export default {
  data() {
    return {
      categories: [],
      tags: [],
      selectedCategory: null,
      page: 1,
      pageSize: 20,
      totalPages: 1,
      hasNext: false
    };
  },

  async mounted() {
    await this.loadCategories();
    await this.loadTags();
  },

  methods: {
    async loadCategories() {
      const response = await axios.get('/api/v1/cultural-tags/categories');
      this.categories = response.data.data.categories;
    },

    async loadTags() {
      const params = {
        page: this.page,
        page_size: this.pageSize
      };

      if (this.selectedCategory) {
        params.category = this.selectedCategory;
      }

      const response = await axios.get('/api/v1/cultural-tags', { params });
      this.tags = response.data.data;
      this.totalPages = response.data.pagination.total_pages;
      this.hasNext = response.data.pagination.has_next;
    },

    selectCategory(code) {
      this.selectedCategory = code;
      this.page = 1;
      this.loadTags();
    },

    selectTag(tag) {
      this.$emit('tag-selected', tag);
    },

    prevPage() {
      if (this.page > 1) {
        this.page--;
        this.loadTags();
      }
    },

    nextPage() {
      if (this.hasNext) {
        this.page++;
        this.loadTags();
      }
    }
  }
};
</script>

<style scoped>
.tag-item {
  display: inline-block;
  padding: 8px 16px;
  margin: 4px;
  background: #f0f0f0;
  border-radius: 4px;
  cursor: pointer;
}

.tag-item:hover {
  background: #e0e0e0;
}
</style>
```

---

## 常见问题

### Q1: 如何批量为多个产品分配相同的标签？

目前API仅支持单个产品分配标签。如需批量操作，可以在前端循环调用:

```python
product_ids = [1, 2, 3, 4, 5]
tag_ids = [1, 2, 3]

for product_id in product_ids:
    response = requests.post(
        f"{BASE_URL}/products/{product_id}/tags",
        headers=headers,
        json={"tag_ids": tag_ids}
    )
```

### Q2: 推荐算法如何工作？

1. **基于产品推荐**: 查找同类产品（相同category或region），统计它们常用的标签
2. **基于关键词推荐**: 在标签名称、描述、关键词中模糊搜索
3. **热门标签**: 按usage_count降序返回

### Q3: 删除标签会影响已关联的产品吗？

- 如果标签被产品使用，执行**软删除**（is_active=false），产品关联保留
- 如果标签未被使用，执行**硬删除**，从数据库中移除

### Q4: 如何搜索标签？

使用`keyword`参数:
```http
GET /api/v1/cultural-tags?keyword=羊肉
```

搜索范围包括：标签名称、描述、关键词字段。

### Q5: 标签使用次数如何统计？

`usage_count`字段自动维护:
- 分配标签到产品时 +1
- 从产品移除标签时 -1
- 不需要手动更新

---

## 性能优化建议

### 1. 启用缓存（可选）

在生产环境中，可以为以下接口启用Redis缓存:
- 标签分类列表（TTL: 1小时）
- 热门标签（TTL: 10分钟）
- 标签列表（TTL: 5分钟）

### 2. 减少API调用

前端可以缓存标签分类和常用标签，避免重复请求。

### 3. 使用分页

标签列表查询务必使用分页，避免一次加载过多数据。

---

## 权限说明

| 操作 | 权限要求 |
|------|----------|
| 查询标签 | 无需认证 |
| 推荐标签 | 无需认证 |
| 创建标签 | 管理员 |
| 更新标签 | 管理员 |
| 删除标签 | 管理员 |
| 分配产品标签 | 管理员 |
| 移除产品标签 | 管理员 |

---

## 技术支持

如有问题，请查看:
- API文档: http://localhost:8000/docs
- 实现报告: BE-007-IMPLEMENTATION-REPORT.md
- 源代码: backend/app/api/cultural_tags.py
