# 知识图谱迁移 - 快速测试指南

## ✅ 已创建文件检查清单

```bash
# 验证所有文件已创建
ls -lh backend/alembic/versions/5a100c74baa3_add_cultural_elements_tables.py  # 6.5K
ls -lh backend/scripts/init_cultural_elements.py                                # 6.5K
ls -lh backend/data/cultural_elements_seed.json                                 # 23K
ls -lh backend/database/README_CULTURAL_ELEMENTS.md                             # 7.4K
ls -lh backend/database/MIGRATION_SUMMARY.md                                    # 11K
```

**所有文件已创建 ✅**

---

## 🧪 测试步骤（假设数据库已存在并可连接）

### 第 1 步：验证语法

```bash
cd backend

# 验证迁移文件语法
python -m py_compile alembic/versions/5a100c74baa3_add_cultural_elements_tables.py
echo $?  # 应返回 0

# 验证初始化脚本语法
python -m py_compile scripts/init_cultural_elements.py
echo $?  # 应返回 0

# 验证 JSON 格式
python -m json.tool data/cultural_elements_seed.json > /dev/null
echo $?  # 应返回 0
```

**预期结果**: 所有命令返回 0，无错误输出 ✅

---

### 第 2 步：查看迁移链

```bash
alembic history
```

**预期输出**:
```
013_add_sku -> 5a100c74baa3 (head), add_cultural_elements_tables
```

---

### 第 3 步：执行迁移（Dry Run）

```bash
# 查看将执行的 SQL（不实际执行）
alembic upgrade head --sql > /tmp/migration.sql
cat /tmp/migration.sql | grep -E "CREATE TABLE|CREATE INDEX"
```

**预期输出**: 应看到 3 个 CREATE TABLE 和 11 个 CREATE INDEX 语句

---

### 第 4 步：执行迁移（实际执行）

```bash
alembic upgrade head
```

**预期输出**:
```
INFO  [alembic.runtime.migration] Running upgrade 013_add_sku -> 5a100c74baa3, add_cultural_elements_tables
```

**无错误即成功 ✅**

---

### 第 5 步：验证表创建

```bash
python scripts/init_cultural_elements.py --verify
```

**预期输出**:
```
============================================================
知识图谱文化元素数据初始化脚本
============================================================

√ cultural_elements 表已存在
```

**退出码应为 0 ✅**

---

### 第 6 步：预览种子数据

```bash
python scripts/init_cultural_elements.py --dry-run
```

**预期输出**:
```
=== 预览模式 - 不会实际插入数据 ===

1. 锡林郭勒草原 (地理) - 热度: (无)
2. 蒙古族游牧文化 (民族) - 热度: (无)
3. 那达慕大会 (节日) - 热度: (无)
4. 马头琴 (艺术) - 热度: (无)
5. 蒙古包 (建筑) - 热度: (无)
6. 京剧 (戏曲) - 热度: 70
7. 茶文化 (饮食) - 热度: 88
8. 故宫 (建筑) - 热度: 92
9. 兵马俑 (历史遗迹) - 热度: 89
10. 长城 (建筑) - 热度: 93
11. 西湖 (自然景观) - 热度: 86
12. 丝绸之路 (历史) - 热度: 82
13. 书法 (艺术) - 热度: 77
14. 国画 (艺术) - 热度: 74
15. 瓷器 (工艺) - 热度: 84

共 15 条数据
```

---

### 第 7 步：插入种子数据

```bash
python scripts/init_cultural_elements.py
```

**预期输出**:
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

---

### 第 8 步：SQL 验证

连接数据库执行以下 SQL：

```sql
-- 1. 检查表是否创建
SHOW TABLES LIKE '%culture%';
-- 预期: cultural_elements, product_culture_links, origin_culture_links

-- 2. 检查数据行数
SELECT COUNT(*) FROM cultural_elements;
-- 预期: 15

-- 3. 检查类型分布
SELECT type, COUNT(*) as count 
FROM cultural_elements 
GROUP BY type 
ORDER BY count DESC;
-- 预期: 艺术 3, 建筑 3, 地理 1, 民族 1, 节日 1, 戏曲 1, 饮食 1, ...

-- 4. 检查热度排名
SELECT name, type, hot_score 
FROM cultural_elements 
ORDER BY hot_score DESC 
LIMIT 5;
-- 预期 Top 5:
-- 1. 长城 (建筑) - 93
-- 2. 故宫 (建筑) - 92
-- 3. 兵马俑 (历史遗迹) - 89
-- 4. 茶文化 (饮食) - 88
-- 5. 西湖 (自然景观) - 86

-- 5. 检查索引
SHOW INDEX FROM cultural_elements;
-- 预期: 至少 5 个索引 (PRIMARY + 4个业务索引)

SHOW INDEX FROM product_culture_links;
-- 预期: 至少 5 个索引 (PRIMARY + 4个业务索引)

SHOW INDEX FROM origin_culture_links;
-- 预期: 至少 4 个索引 (PRIMARY + 3个业务索引)

-- 6. 检查外键约束
SELECT 
    TABLE_NAME,
    COLUMN_NAME,
    CONSTRAINT_NAME,
    REFERENCED_TABLE_NAME,
    REFERENCED_COLUMN_NAME
FROM information_schema.KEY_COLUMN_USAGE
WHERE TABLE_SCHEMA = DATABASE()
AND TABLE_NAME IN ('product_culture_links', 'origin_culture_links');
-- 预期: 4 个外键约束

-- 7. 测试 JSON metadata 查询
SELECT name, JSON_EXTRACT(metadata, '$.keywords') as keywords
FROM cultural_elements
WHERE type = '艺术'
LIMIT 3;
-- 预期: 返回马头琴、书法、国画的 keywords
```

---

## 🔄 重复运行测试

```bash
# 再次运行初始化脚本
python scripts/init_cultural_elements.py
```

**预期输出**:
```
开始插入数据...

o 跳过 (已存在): 锡林郭勒草原
o 跳过 (已存在): 蒙古族游牧文化
...

============================================================
√ 数据初始化完成
  - 成功插入: 0 条
  - 跳过 (已存在): 15 条
  - 错误: 0 条
============================================================
```

**所有数据应被跳过，无重复插入 ✅**

---

## 🔙 回滚测试

```bash
# 回滚迁移
alembic downgrade -1
```

**预期输出**:
```
INFO  [alembic.runtime.migration] Running downgrade 5a100c74baa3 -> 013_add_sku, add_cultural_elements_tables
```

**验证表已删除**:
```bash
python scripts/init_cultural_elements.py --verify
# 预期输出: × cultural_elements 表不存在
```

**重新升级**:
```bash
alembic upgrade head
python scripts/init_cultural_elements.py --verify
# 预期输出: √ cultural_elements 表已存在
```

---

## 📊 性能测试

```sql
-- 测试索引性能（EXPLAIN）

-- 1. 按类型查询（应使用 idx_cultural_elements_type）
EXPLAIN SELECT * FROM cultural_elements WHERE type = '艺术';

-- 2. 按热度排序（应使用 idx_cultural_elements_hot_score）
EXPLAIN SELECT * FROM cultural_elements ORDER BY hot_score DESC LIMIT 10;

-- 3. 按地区查询（应使用 idx_cultural_elements_region）
EXPLAIN SELECT * FROM cultural_elements WHERE origin_region = '内蒙古全境';

-- 4. 产品-文化关联查询（应使用索引）
EXPLAIN SELECT ce.* 
FROM cultural_elements ce
JOIN product_culture_links pcl ON ce.id = pcl.culture_id
WHERE pcl.product_id = 1;
```

**预期**: 所有查询应显示 `possible_keys` 包含相应索引

---

## ✅ 完整验收清单

- [ ] 迁移文件语法通过
- [ ] 初始化脚本语法通过
- [ ] JSON 种子数据格式有效
- [ ] Alembic history 显示新迁移
- [ ] 迁移执行成功（upgrade）
- [ ] 表创建验证成功（--verify）
- [ ] 种子数据预览正常（--dry-run）
- [ ] 种子数据插入成功（15条）
- [ ] SQL 验证所有表和索引存在
- [ ] 数据查询正常返回
- [ ] 重复运行去重正常（0 插入，15 跳过）
- [ ] 回滚成功（downgrade）
- [ ] 重新升级成功（upgrade）
- [ ] 索引性能符合预期（EXPLAIN）

**全部通过即迁移成功 ✅**

---

## 🚨 常见错误处理

### 错误 1: `pymysql.err.OperationalError: Unknown database`

**原因**: 数据库不存在

**解决**:
```bash
# 连接 MySQL 创建数据库
mysql -u root -p
CREATE DATABASE agri_platform CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
exit

# 或检查 .env 中的 DATABASE_URL 配置
```

### 错误 2: `Foreign key constraint fails`

**原因**: 缺少依赖表（products, origins）

**解决**:
```bash
# 查看当前迁移版本
alembic current

# 确保 013_add_sku 已执行
alembic upgrade 013_add_sku

# 再执行知识图谱迁移
alembic upgrade head
```

### 错误 3: `Duplicate entry for key 'uk_cultural_element_name'`

**原因**: 数据已存在，尝试重复插入

**解决**: 这是正常的，脚本会自动跳过。如果希望重新插入：
```sql
-- 清空表数据（保留表结构）
TRUNCATE TABLE product_culture_links;
TRUNCATE TABLE origin_culture_links;
TRUNCATE TABLE cultural_elements;
```

---

**文档版本**: v1.0  
**创建时间**: 2026-06-12  
**适用环境**: 开发/测试环境
