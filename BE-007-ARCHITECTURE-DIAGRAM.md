# 文化标签管理系统架构图

## 系统架构总览

```
┌─────────────────────────────────────────────────────────────────┐
│                         前端应用层                               │
│  Vue.js / React / 小程序                                         │
│  - 标签选择器                                                     │
│  - 产品标签管理                                                   │
│  - 标签推荐展示                                                   │
└────────────────────────┬────────────────────────────────────────┘
                         │ HTTP/JSON
                         │
┌────────────────────────▼────────────────────────────────────────┐
│                       API网关层                                  │
│  FastAPI                                                         │
│  - 路由注册                                                       │
│  - 认证/鉴权                                                      │
│  - 错误处理                                                       │
└────────────────────────┬────────────────────────────────────────┘
                         │
          ┌──────────────┼──────────────┐
          │              │              │
          ▼              ▼              ▼
┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│文化标签API   │  │产品标签API   │  │统计分析API   │
│cultural_tags │  │products      │  │statistics    │
│9个端点       │  │3个端点       │  │内置端点      │
└──────┬───────┘  └──────┬───────┘  └──────┬───────┘
       │                 │                 │
       │                 │                 │
       └────────┬────────┴────────┬────────┘
                │                 │
                ▼                 ▼
┌───────────────────────────────────────────────────────────────┐
│                      业务逻辑层                                │
│  CulturalTagService                                           │
│  ┌─────────────┬──────────────┬──────────────┬──────────────┐│
│  │ CRUD操作    │ 标签推荐     │ 产品关联     │ 统计分析     ││
│  │ - create    │ - by_product │ - assign     │ - statistics ││
│  │ - read      │ - by_keyword │ - remove     │ - by_category││
│  │ - update    │ - popular    │ - get_tags   │              ││
│  │ - delete    │              │              │              ││
│  └─────────────┴──────────────┴──────────────┴──────────────┘│
└────────────────────────┬──────────────────────────────────────┘
                         │ SQLAlchemy ORM
                         │
┌────────────────────────▼──────────────────────────────────────┐
│                      数据模型层                                │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐        │
│  │CulturalTag   │  │Product       │  │product_tags  │        │
│  │文化标签      │  │产品          │  │关联表        │        │
│  │- id          │  │- id          │  │- product_id  │        │
│  │- name        │  │- name        │  │- tag_id      │        │
│  │- category    │  │- category    │  │- created_at  │        │
│  │- keywords    │  │- ...         │  │              │        │
│  │- usage_count │  │              │  │              │        │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘        │
│         │                 │                 │                │
│         └────────┬────────┴────────┬────────┘                │
│                  │  many-to-many   │                         │
└──────────────────┼─────────────────┼─────────────────────────┘
                   │                 │
┌──────────────────▼─────────────────▼─────────────────────────┐
│                      数据存储层                                │
│  MySQL 8.0+                                                   │
│  ┌─────────────────┐  ┌─────────────────┐                   │
│  │cultural_tags    │  │product_tags     │                   │
│  │表               │  │关联表           │                   │
│  │- 主键索引       │  │- 复合主键       │                   │
│  │- 6个辅助索引    │  │- 2个索引        │                   │
│  │- 外键约束       │  │- 级联删除       │                   │
│  └─────────────────┘  └─────────────────┘                   │
└───────────────────────────────────────────────────────────────┘
```

## 数据流图

### 1. 标签查询流程

```
用户请求
   │
   ▼
GET /api/v1/cultural-tags?category=geo&page=1
   │
   ▼
API Router (cultural_tags.py)
   │
   ├─ 参数验证 (Pydantic Schema)
   ├─ 权限检查 (无需认证)
   │
   ▼
CulturalTagService.list_tags()
   │
   ├─ 构建查询条件
   ├─ 分类筛选 (category=geo)
   ├─ 关键词搜索 (LIKE)
   ├─ 排序 (usage_count DESC)
   ├─ 分页 (offset/limit)
   │
   ▼
SQLAlchemy Query
   │
   ▼
MySQL Database
   │ (使用索引: idx_cultural_tag_category)
   │
   ▼
返回结果集
   │
   ▼
转换为Schema (CulturalTagListItemResponse)
   │
   ▼
分页响应 (PaginatedResponse)
   │
   ▼
JSON响应返回给用户
```

### 2. 标签推荐流程（协同过滤）

```
用户请求推荐
   │
   ▼
GET /api/v1/cultural-tags/recommend?product_id=1
   │
   ▼
CulturalTagService.recommend_tags_by_product()
   │
   ├─ 获取当前产品信息
   ├─ 获取当前产品已有标签
   │
   ▼
查找同类产品 (相同category或region)
   │
   ├─ 限制50个产品
   │
   ▼
统计同类产品使用的标签频率
   │
   ├─ tag_frequency = {tag_id: count}
   ├─ 排除已有标签
   │
   ▼
按频率排序
   │
   ▼
返回Top 10推荐标签
   │
   ▼
JSON响应返回给用户
```

### 3. 产品标签分配流程

```
管理员请求
   │
   ▼
POST /api/v1/products/1/tags
Authorization: Bearer {token}
Body: {"tag_ids": [1, 2, 3]}
   │
   ▼
API Router (products.py)
   │
   ├─ JWT认证
   ├─ 管理员权限验证
   ├─ 参数验证 (tag_ids唯一性)
   │
   ▼
CulturalTagService.assign_tags_to_product()
   │
   ├─ 验证产品存在
   ├─ 验证标签存在且启用
   │
   ▼
计算标签变更
   │
   ├─ new_tag_ids = 新增的标签
   ├─ removed_tag_ids = 移除的标签
   │
   ▼
更新usage_count
   │
   ├─ 新增标签: usage_count += 1
   ├─ 移除标签: usage_count -= 1
   │
   ▼
更新product_tags关联表
   │
   ├─ 删除旧关联
   ├─ 插入新关联
   │
   ▼
事务提交 (DB Commit)
   │
   ▼
返回更新后的产品标签列表
   │
   ▼
JSON响应返回给管理员
```

## 标签推荐算法详解

### 协同过滤算法

```
输入: product_id = 1

步骤1: 获取产品信息
┌─────────────────────┐
│ Product #1          │
│ category: "畜产品"  │
│ region: "锡林郭勒"  │
│ current_tags: [1,2] │
└─────────────────────┘
         │
         ▼
步骤2: 查找同类产品
┌─────────────────────┐
│ WHERE category =    │
│   "畜产品" OR       │
│ region = "锡林郭勒" │
│ LIMIT 50            │
└─────────────────────┘
         │
         ▼
步骤3: 统计标签频率
┌─────────────────────┐
│ Product #2: [1,3,6] │ → tag 3: +1, tag 6: +1
│ Product #3: [2,3,7] │ → tag 3: +1, tag 7: +1
│ Product #4: [3,6,8] │ → tag 3: +1, tag 6: +1, tag 8: +1
│ ...                 │
└─────────────────────┘
         │
         ▼
tag_frequency = {
  3: 3次,    ← 最常用
  6: 2次,
  7: 1次,
  8: 1次
}
         │
         ▼
步骤4: 排除已有标签
移除 tag 1, 2 (已有)
         │
         ▼
步骤5: 排序并返回Top 10
[3, 6, 7, 8, ...]
```

### 关键词推荐算法

```
输入: keywords = "羊肉 草原"

步骤1: 分词
["羊肉", "草原"]
         │
         ▼
步骤2: 构建搜索条件
┌─────────────────────────────────────┐
│ WHERE (                             │
│   name LIKE '%羊肉%' OR             │
│   description LIKE '%羊肉%' OR      │
│   keywords LIKE '%羊肉%'            │
│ ) OR (                              │
│   name LIKE '%草原%' OR             │
│   description LIKE '%草原%' OR      │
│   keywords LIKE '%草原%'            │
│ )                                   │
│ AND is_active = true                │
└─────────────────────────────────────┘
         │
         ▼
步骤3: 执行查询
┌─────────────────────────────────────┐
│ 匹配标签:                           │
│ - "锡林郭勒羊肉" (包含"羊肉")       │
│ - "草原文化" (包含"草原")          │
│ - "游牧文化" (keywords包含"草原")   │
└─────────────────────────────────────┘
         │
         ▼
步骤4: 按usage_count排序
[锡林郭勒羊肉(15次), 草原文化(10次), 游牧文化(8次)]
         │
         ▼
步骤5: 返回Top 10
```

## 数据库索引优化

### 索引设计

```sql
-- cultural_tags表索引
CREATE INDEX idx_cultural_tag_name ON cultural_tags(name);
  → 用于: 名称查询、去重检查

CREATE INDEX idx_cultural_tag_category ON cultural_tags(category);
  → 用于: 分类筛选 (WHERE category = 'geo')

CREATE INDEX idx_cultural_tag_is_active ON cultural_tags(is_active);
  → 用于: 启用状态筛选 (WHERE is_active = true)

CREATE INDEX idx_cultural_tag_usage_count ON cultural_tags(usage_count);
  → 用于: 热门标签排序 (ORDER BY usage_count DESC)

CREATE INDEX idx_cultural_tag_parent_id ON cultural_tags(parent_id);
  → 用于: 层级查询 (WHERE parent_id = ?)

CREATE INDEX idx_cultural_tag_created_at ON cultural_tags(created_at);
  → 用于: 时间排序 (ORDER BY created_at DESC)

-- product_tags关联表索引
CREATE INDEX idx_product_tags_product_id ON product_tags(product_id);
  → 用于: 查询产品的标签 (WHERE product_id = ?)

CREATE INDEX idx_product_tags_tag_id ON product_tags(tag_id);
  → 用于: 查询标签的产品 (WHERE tag_id = ?)
```

### 查询优化示例

```sql
-- 查询1: 获取地理标志类标签（使用组合索引）
EXPLAIN SELECT * FROM cultural_tags
WHERE category = 'geo' AND is_active = true
ORDER BY usage_count DESC
LIMIT 20;

→ 使用索引: idx_cultural_tag_category + idx_cultural_tag_is_active
→ 执行时间: < 10ms

-- 查询2: 获取产品的标签（使用关联表索引）
EXPLAIN SELECT ct.* FROM cultural_tags ct
JOIN product_tags pt ON ct.id = pt.tag_id
WHERE pt.product_id = 1;

→ 使用索引: idx_product_tags_product_id
→ 执行时间: < 5ms

-- 查询3: 搜索标签（使用LIKE，性能一般）
EXPLAIN SELECT * FROM cultural_tags
WHERE name LIKE '%羊肉%' OR keywords LIKE '%羊肉%'
AND is_active = true;

→ 全表扫描（建议使用ElasticSearch）
→ 执行时间: < 100ms (小数据量)
```

## 缓存策略设计

```
┌─────────────────────────────────────────────────────────────┐
│                       应用层                                 │
└────────────────────────┬────────────────────────────────────┘
                         │
          ┌──────────────┼──────────────┐
          │              │              │
          ▼              ▼              ▼
  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐
  │ 热门标签缓存 │ │ 分类统计缓存 │ │ 推荐结果缓存 │
  │ TTL: 10min   │ │ TTL: 1hour   │ │ TTL: 5min    │
  └──────┬───────┘ └──────┬───────┘ └──────┬───────┘
         │                │                │
         └────────┬───────┴────────┬───────┘
                  │ Redis缓存层    │
                  │                │
┌─────────────────▼────────────────▼───────────────────────────┐
│  Redis                                                        │
│  ┌─────────────────────────────────────────────────────────┐│
│  │ Key: tags:popular:10                                    ││
│  │ Value: [{"id":1,"name":"锡林郭勒羊肉",...}]             ││
│  │ TTL: 600秒                                              ││
│  ├─────────────────────────────────────────────────────────┤│
│  │ Key: tags:categories:stats                              ││
│  │ Value: {"geo":5,"ethnicity":3,...}                      ││
│  │ TTL: 3600秒                                             ││
│  ├─────────────────────────────────────────────────────────┤│
│  │ Key: tags:recommend:product:1                           ││
│  │ Value: [{"id":3,"name":"蒙古族传统",...}]               ││
│  │ TTL: 300秒                                              ││
│  └─────────────────────────────────────────────────────────┘│
└───────────────────────────────────────────────────────────────┘
                         │
                         │ 缓存失效时
                         ▼
┌───────────────────────────────────────────────────────────────┐
│  MySQL                                                        │
│  - 执行SQL查询                                                │
│  - 返回结果                                                   │
│  - 更新缓存                                                   │
└───────────────────────────────────────────────────────────────┘
```

## 部署架构图

```
                    ┌──────────────┐
                    │   用户端     │
                    │  Browser/App │
                    └──────┬───────┘
                           │ HTTPS
                           │
                    ┌──────▼───────┐
                    │  Nginx反向   │
                    │  代理/负载   │
                    │  均衡器      │
                    └──────┬───────┘
                           │
          ┌────────────────┼────────────────┐
          │                │                │
    ┌─────▼─────┐    ┌─────▼─────┐    ┌─────▼─────┐
    │ FastAPI   │    │ FastAPI   │    │ FastAPI   │
    │ Instance1 │    │ Instance2 │    │ Instance3 │
    │ Port 8000 │    │ Port 8001 │    │ Port 8002 │
    └─────┬─────┘    └─────┬─────┘    └─────┬─────┘
          │                │                │
          └────────────────┼────────────────┘
                           │
          ┌────────────────┼────────────────┐
          │                │                │
    ┌─────▼─────┐    ┌─────▼─────┐    ┌─────▼─────┐
    │  MySQL    │    │  Redis    │    │ 文件存储  │
    │  主从复制 │    │  缓存层   │    │  (可选)   │
    │  数据库   │    │           │    │           │
    └───────────┘    └───────────┘    └───────────┘
```

---

**文档版本**: 1.0
**创建日期**: [项目完成日期]
**维护者**: 开发团队
