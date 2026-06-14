# 知识图谱数据库迁移 - 完成总结

## ✅ 已完成任务

### 1. 创建 Alembic 迁移文件

**文件**: `alembic/versions/5a100c74baa3_add_cultural_elements_tables.py`

- ✅ 迁移ID: `5a100c74baa3`
- ✅ 依赖版本: `013_add_sku`
- ✅ 创建时间: 2026-06-12 16:23:08

**包含内容**:
- `cultural_elements` 表（10个字段 + 4个索引）
- `product_culture_links` 表（5个字段 + 4个索引）
- `origin_culture_links` 表（4个字段 + 3个索引）
- 完整的 upgrade() 和 downgrade() 函数
- 外键级联策略（CASCADE）

### 2. 创建初始化脚本

**文件**: `scripts/init_cultural_elements.py`

**功能特性**:
- ✅ UTF-8 编码支持（Windows 兼容）
- ✅ 事务管理和错误处理
- ✅ 去重检查（按 name 唯一键）
- ✅ 三种运行模式：
  - `--dry-run`: 预览数据，不插入
  - `--verify`: 仅验证表是否存在
  - 默认: 执行插入
- ✅ 详细的进度输出和统计信息
- ✅ 健壮的数据库连接错误处理

### 3. 准备种子数据

**文件**: `data/cultural_elements_seed.json`

**数据内容** (15个文化元素):

**内蒙古地方特色** (5个):
1. 锡林郭勒草原（地理） - 详细历史文化背景
2. 蒙古族游牧文化（民族） - 游牧智慧与文化传承
3. 那达慕大会（节日） - 非物质文化遗产
4. 马头琴（艺术） - 草原音乐象征
5. 蒙古包（建筑） - 游牧建筑智慧

**通用中华文化** (10个):
6. 京剧（戏曲）
7. 茶文化（饮食）
8. 故宫（建筑）
9. 兵马俑（历史遗迹）
10. 长城（建筑）
11. 西湖（自然景观）
12. 丝绸之路（历史）
13. 书法（艺术）
14. 国画（艺术）
15. 瓷器（工艺）

### 4. 创建说明文档

**文件**: `database/README_CULTURAL_ELEMENTS.md`

**包含内容**:
- 表结构详细说明
- 执行迁移步骤
- 初始化数据指南
- 验证方法
- 常见问题解答
- 性能优化建议
- 典型查询示例
- 后续开发方向

## 📋 使用指南

### 快速开始

```bash
# 1. 进入后端目录
cd backend

# 2. 执行迁移
alembic upgrade head

# 3. 验证表创建成功
python scripts/init_cultural_elements.py --verify

# 4. 预览种子数据（可选）
python scripts/init_cultural_elements.py --dry-run

# 5. 插入种子数据
python scripts/init_cultural_elements.py
```

### 预期输出

```
============================================================
知识图谱文化元素数据初始化脚本
============================================================

√ cultural_elements 表已存在
√ 成功加载 15 条文化元素数据

开始插入数据...

√ 插入成功: 锡林郭勒草原 (地理)
√ 插入成功: 蒙古族游牧文化 (民族)
√ 插入成功: 那达慕大会 (节日)
√ 插入成功: 马头琴 (艺术)
√ 插入成功: 蒙古包 (建筑)
√ 插入成功: 京剧 (戏曲)
√ 插入成功: 茶文化 (饮食)
√ 插入成功: 故宫 (建筑)
√ 插入成功: 兵马俑 (历史遗迹)
√ 插入成功: 长城 (建筑)
√ 插入成功: 西湖 (自然景观)
√ 插入成功: 丝绸之路 (历史)
√ 插入成功: 书法 (艺术)
√ 插入成功: 国画 (艺术)
√ 插入成功: 瓷器 (工艺)

============================================================
√ 数据初始化完成
  - 成功插入: 15 条
  - 跳过 (已存在): 0 条
  - 错误: 0 条
============================================================
```

## 🔍 验证迁移

### SQL 验证命令

```sql
-- 1. 检查表是否创建
SHOW TABLES LIKE 'cultural%';
SHOW TABLES LIKE '%culture%';

-- 预期输出:
-- cultural_elements
-- product_culture_links
-- origin_culture_links

-- 2. 检查表结构
DESCRIBE cultural_elements;
DESCRIBE product_culture_links;
DESCRIBE origin_culture_links;

-- 3. 检查索引
SHOW INDEX FROM cultural_elements;
SHOW INDEX FROM product_culture_links;
SHOW INDEX FROM origin_culture_links;

-- 4. 验证数据
SELECT COUNT(*) as total FROM cultural_elements;
-- 预期: 15

SELECT type, COUNT(*) as count 
FROM cultural_elements 
GROUP BY type 
ORDER BY count DESC;
-- 预期分布:
-- 艺术: 3, 建筑: 3, 地理: 1, 民族: 1, 节日: 1, ...

-- 5. 查看热度排名
SELECT name, type, hot_score 
FROM cultural_elements 
ORDER BY hot_score DESC 
LIMIT 5;
```

## 📊 数据库 ER 关系

```
┌─────────────────────┐
│   cultural_elements │
│─────────────────────│
│ id (PK)             │
│ name (UK)           │
│ type                │◄────┐
│ story               │     │
│ origin_region       │     │
│ hot_score           │     │
│ metadata (JSON)     │     │
│ view_count          │     │
└─────────────────────┘     │
         ▲                  │
         │                  │
         │                  │
    ┌────┴──────────────────┴──────┐
    │                               │
┌───┴─────────────────────┐  ┌─────┴──────────────────┐
│ product_culture_links   │  │ origin_culture_links   │
│─────────────────────────│  │────────────────────────│
│ product_id (PK, FK)     │  │ origin_id (PK, FK)     │
│ culture_id (PK, FK)     │  │ culture_id (PK, FK)    │
│ relevance_score         │  │ strength               │
│ link_type               │  │ created_at             │
│ created_at              │  │                        │
└────────┬────────────────┘  └───────┬────────────────┘
         │                           │
         │                           │
         ▼                           ▼
┌─────────────────────┐     ┌────────────────────┐
│     products        │     │      origins       │
│─────────────────────│     │────────────────────│
│ id (PK)             │     │ id (PK)            │
│ ...                 │     │ ...                │
└─────────────────────┘     └────────────────────┘
```

## 🎯 技术亮点

1. **索引优化**:
   - 热度查询: `hot_score DESC` 索引
   - 类型筛选: `type` 索引
   - 地区查询: `origin_region` 索引
   - 关联度排序: `relevance_score` 索引

2. **数据完整性**:
   - 唯一约束: `name` 字段
   - 外键级联: `ON DELETE CASCADE`
   - 复合主键: 关联表防重复

3. **扩展性设计**:
   - JSON metadata 字段存储灵活数据
   - link_type 支持多种关联方式（manual/ai/curated）
   - relevance_score 支持 AI 推荐算法

4. **脚本健壮性**:
   - Windows UTF-8 编码兼容
   - 数据库连接错误处理
   - 去重检查避免重复插入
   - 事务管理保证数据一致性

## 📁 输出文件清单

```
backend/
├── alembic/versions/
│   └── 5a100c74baa3_add_cultural_elements_tables.py  ✅ 迁移文件
├── scripts/
│   └── init_cultural_elements.py                     ✅ 初始化脚本
├── data/
│   └── cultural_elements_seed.json                   ✅ 种子数据（15条）
└── database/
    ├── README_CULTURAL_ELEMENTS.md                   ✅ 使用说明
    └── MIGRATION_SUMMARY.md                          ✅ 本文件
```

## 🚀 后续开发建议

### API 端点开发

```python
# backend/app/api/v1/cultural_elements.py

@router.get("/cultural-elements")
async def list_cultural_elements(
    type: Optional[str] = None,
    region: Optional[str] = None,
    min_hot_score: int = 0,
    page: int = 1,
    page_size: int = 20
):
    """列表查询，支持类型、地区、热度筛选"""
    pass

@router.get("/cultural-elements/{id}")
async def get_cultural_element(id: int):
    """获取详情，包含关联的产品和产地"""
    pass

@router.post("/products/{product_id}/cultures")
async def link_product_culture(
    product_id: int,
    culture_id: int,
    relevance_score: float = 0.5,
    link_type: str = "manual"
):
    """创建产品-文化关联"""
    pass

@router.get("/products/{product_id}/cultures")
async def get_product_cultures(product_id: int):
    """查询产品的文化标签"""
    pass
```

### AI 推荐引擎

```python
# backend/app/services/culture_recommender.py

class CultureRecommender:
    """基于产品描述自动推荐文化标签"""
    
    async def recommend(self, product_description: str) -> List[Dict]:
        """
        返回: [
            {"culture_id": 1, "relevance_score": 0.85, "reason": "..."},
            {"culture_id": 5, "relevance_score": 0.72, "reason": "..."}
        ]
        """
        pass
```

### 知识图谱可视化

前端使用 ECharts / D3.js 实现：
- 文化元素网络图
- 产品-文化关联图谱
- 热度趋势分析

## ⚠️ 注意事项

1. **数据库必须存在**: 运行迁移前确保数据库已创建
2. **依赖迁移**: 必须先完成 `013_add_sku` 迁移（需要 products 和 origins 表）
3. **重复运行**: 初始化脚本支持重复运行，已存在的数据会自动跳过
4. **编码问题**: Windows 用户如遇乱码，脚本已自动处理 UTF-8 输出

## 📞 问题排查

### 问题 1: Unknown database 'xxx'

**解决**: 检查 `.env` 文件中的 `DATABASE_URL`，确保数据库已创建。

### 问题 2: Foreign key constraint fails

**解决**: 先执行依赖迁移 `alembic upgrade 013_add_sku`。

### 问题 3: 初始化脚本 UnicodeEncodeError

**解决**: 脚本已修复，使用 UTF-8 编码。如仍有问题，运行：
```bash
chcp 65001  # Windows 切换到 UTF-8
python scripts/init_cultural_elements.py
```

---

**创建时间**: 2026-06-12  
**创建者**: Database Engineer Agent  
**状态**: ✅ 完成并已验证语法
