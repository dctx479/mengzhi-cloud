# 知识图谱数据库迁移说明

## 概述

本迁移创建知识图谱系统的核心表结构，用于存储和管理文化元素数据及其与产品、产地的关联关系。

## 迁移文件

**文件**: `alembic/versions/5a100c74baa3_add_cultural_elements_tables.py`

**依赖**: `013_add_sku` (需要先完成产品表和产地表的创建)

## 表结构

### 1. cultural_elements (文化元素表)

存储各类文化元素的基础信息。

| 字段 | 类型 | 说明 |
|------|------|------|
| id | BIGINT | 主键，自增 |
| name | VARCHAR(100) | 文化元素名称，唯一 |
| type | VARCHAR(50) | 文化类型：节日/传说/工艺/饮食/建筑等 |
| story | TEXT | 文化故事或背景描述 |
| origin_region | VARCHAR(100) | 起源地区 |
| hot_score | INT | 热度分数 0-100，默认 50 |
| metadata | JSON | 扩展元数据（图片、关键词等） |
| view_count | INT | 浏览次数，默认 0 |
| created_at | TIMESTAMP | 创建时间 |
| updated_at | TIMESTAMP | 更新时间，自动更新 |

**索引**:
- `idx_cultural_elements_type` - 按类型查询
- `idx_cultural_elements_hot_score` - 按热度排序
- `idx_cultural_elements_region` - 按地区查询
- `idx_cultural_elements_created_at` - 按创建时间排序

### 2. product_culture_links (产品-文化关联表)

多对多关联表，连接产品与文化元素。

| 字段 | 类型 | 说明 |
|------|------|------|
| product_id | BIGINT | 产品ID，外键 → products.id |
| culture_id | BIGINT | 文化元素ID，外键 → cultural_elements.id |
| relevance_score | DECIMAL(3,2) | 关联度分数 0.00-1.00，默认 0.50 |
| link_type | VARCHAR(50) | 关联类型：manual/ai/curated，默认 manual |
| created_at | TIMESTAMP | 创建时间 |

**主键**: (product_id, culture_id)

**外键级联**: 
- 删除产品时级联删除关联 (CASCADE)
- 删除文化元素时级联删除关联 (CASCADE)

**索引**:
- `idx_product_culture_product` - 查询产品的文化标签
- `idx_product_culture_culture` - 查询文化元素关联的产品
- `idx_product_culture_relevance` - 按关联度排序
- `idx_product_culture_link_type` - 按关联类型筛选

### 3. origin_culture_links (产地-文化关联表)

多对多关联表，连接产地与文化元素。

| 字段 | 类型 | 说明 |
|------|------|------|
| origin_id | BIGINT | 产地ID，外键 → origins.id |
| culture_id | BIGINT | 文化元素ID，外键 → cultural_elements.id |
| strength | DECIMAL(3,2) | 关联强度 0.00-1.00，默认 1.00 |
| created_at | TIMESTAMP | 创建时间 |

**主键**: (origin_id, culture_id)

**外键级联**: 删除时级联删除 (CASCADE)

**索引**:
- `idx_origin_culture_origin` - 查询产地的文化元素
- `idx_origin_culture_culture` - 查询文化元素关联的产地
- `idx_origin_culture_strength` - 按关联强度排序

## 执行迁移

### 1. 运行迁移

```bash
cd backend
alembic upgrade head
```

### 2. 验证迁移

```bash
# 验证表是否创建成功
python scripts/init_cultural_elements.py --verify
```

预期输出：
```
√ cultural_elements 表已存在
```

## 初始化数据

### 1. 预览种子数据

```bash
python scripts/init_cultural_elements.py --dry-run
```

会显示所有待插入的文化元素列表（不会实际插入）。

### 2. 插入种子数据

```bash
python scripts/init_cultural_elements.py
```

预期输出：
```
============================================================
知识图谱文化元素数据初始化脚本
============================================================

√ cultural_elements 表已存在
√ 成功加载 15 条文化元素数据

开始插入数据...

√ 插入成功: 春节 (节日)
√ 插入成功: 端午节 (节日)
√ 插入成功: 中秋节 (节日)
...

============================================================
√ 数据初始化完成
  - 成功插入: 15 条
  - 跳过 (已存在): 0 条
  - 错误: 0 条
============================================================
```

### 3. 验证数据

```sql
-- 检查文化元素总数
SELECT COUNT(*) FROM cultural_elements;

-- 查看各类型分布
SELECT type, COUNT(*) as count 
FROM cultural_elements 
GROUP BY type 
ORDER BY count DESC;

-- 查看热度 Top 5
SELECT name, type, hot_score 
FROM cultural_elements 
ORDER BY hot_score DESC 
LIMIT 5;
```

## 种子数据

初始数据包含 15 个中华文化元素：

**节日类** (3个):
- 春节 (热度: 95)
- 端午节 (热度: 85)
- 中秋节 (热度: 90)

**工艺类** (3个):
- 景泰蓝 (热度: 75)
- 苏绣 (热度: 80)
- 瓷器 (热度: 84)

**建筑/遗迹类** (3个):
- 故宫 (热度: 92)
- 长城 (热度: 93)
- 兵马俑 (热度: 89)

**艺术/文化类** (5个):
- 京剧 (热度: 70)
- 茶文化 (热度: 88)
- 书法 (热度: 77)
- 国画 (热度: 74)
- 丝绸之路 (热度: 82)

**自然景观类** (1个):
- 西湖 (热度: 86)

数据文件: `backend/data/cultural_elements_seed.json`

## 回滚迁移

如需回滚到上一版本：

```bash
alembic downgrade -1
```

这将删除以下内容：
- origin_culture_links 表
- product_culture_links 表
- cultural_elements 表
- 所有相关索引和外键

## 常见问题

### Q: 迁移时报错 "Unknown database"

**A**: 请确保数据库已创建，并检查 `.env` 文件中的 `DATABASE_URL` 配置。

### Q: 初始化脚本报错 "cultural_elements 表不存在"

**A**: 先运行迁移：`alembic upgrade head`

### Q: 如何添加更多文化元素？

**A**: 
1. 编辑 `backend/data/cultural_elements_seed.json`
2. 重新运行 `python scripts/init_cultural_elements.py`
3. 已存在的元素会自动跳过

### Q: metadata 字段存储什么内容？

**A**: JSON 格式的扩展信息，例如：
```json
{
  "keywords": ["团圆", "红包", "春联"],
  "related_products": ["年货礼盒", "红包"],
  "image_url": "https://example.com/image.jpg",
  "external_links": ["https://baike.baidu.com/..."]
}
```

## 性能优化建议

1. **热度查询优化**: 已创建 `hot_score` 降序索引
2. **类型筛选优化**: 已创建 `type` 索引
3. **关联查询优化**: 关联表的双向索引支持高效查询

### 典型查询示例

```sql
-- 查询某产品的所有文化标签（按关联度排序）
SELECT ce.*, pcl.relevance_score
FROM cultural_elements ce
JOIN product_culture_links pcl ON ce.id = pcl.culture_id
WHERE pcl.product_id = ?
ORDER BY pcl.relevance_score DESC;

-- 查询某文化元素关联的所有产品
SELECT p.*
FROM products p
JOIN product_culture_links pcl ON p.id = pcl.product_id
WHERE pcl.culture_id = ?
AND pcl.relevance_score >= 0.7;

-- 查询某产地的文化元素
SELECT ce.*
FROM cultural_elements ce
JOIN origin_culture_links ocl ON ce.id = ocl.culture_id
WHERE ocl.origin_id = ?
ORDER BY ocl.strength DESC;
```

## 后续开发

1. **API 端点开发**: 
   - `GET /api/v1/cultural-elements` - 列表查询
   - `GET /api/v1/cultural-elements/{id}` - 详情查询
   - `POST /api/v1/products/{id}/cultures` - 关联文化标签
   
2. **AI 推荐引擎**:
   - 基于产品描述自动推荐文化标签
   - 计算关联度分数 (relevance_score)
   
3. **知识图谱可视化**:
   - 文化元素网络图
   - 产品-文化关联图谱

## 相关文件

- 迁移文件: `alembic/versions/5a100c74baa3_add_cultural_elements_tables.py`
- 初始化脚本: `scripts/init_cultural_elements.py`
- 种子数据: `data/cultural_elements_seed.json`
- SQL Schema: `database/init_schema.sql` (第 135-182 行)
