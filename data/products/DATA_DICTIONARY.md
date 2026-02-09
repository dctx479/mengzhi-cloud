# 产品数据字典 - 字段详细说明

## 表结构定义

### 表名: products
**说明**: 内蒙古地理标志产品基础信息表
**行数**: 10条
**字符集**: UTF-8MB4
**排序规则**: utf8mb4_unicode_ci

---

## 字段详细说明

### 1. id (INT)
- **类型**: 整数
- **约束**: PRIMARY KEY, AUTO_INCREMENT
- **说明**: 产品唯一标识符，自动递增
- **范围**: 1-10
- **示例**: 1, 2, 3...10

### 2. name (VARCHAR(100))
- **类型**: 变长字符串
- **约束**: NOT NULL
- **说明**: 产品的官方地理标志名称
- **索引**: 是（提高查询速度）
- **示例**: "乌兰察布马铃薯"

### 3. category (VARCHAR(50))
- **类型**: 变长字符串
- **约束**: NOT NULL
- **说明**: 产品分类，预定义值如下：
  - "农产品": 粮食、蔬菜等植物类产品
  - "畜产品": 肉类、奶制品、畜毛等动物类产品
  - "特产": 其他特殊产品类别
- **索引**: 是
- **示例**: "农产品", "畜产品"

### 4. province (VARCHAR(50))
- **类型**: 变长字符串
- **约束**: NOT NULL
- **说明**: 产品所属省份，本数据集均为内蒙古自治区
- **值**: "内蒙古自治区"
- **示例**: "内蒙古自治区"

### 5. region (VARCHAR(200))
- **类型**: 变长字符串
- **约束**: NOT NULL
- **说明**: 产品具体产地，包括盟市和主要旗县
- **索引**: 是
- **示例**: "乌兰察布市（分布于各旗县）", "锡林郭勒盟（苏尼特左旗、苏尼特右旗、二连浩特市）"
- **格式**: "盟市名（旗县详情）"

### 6. description (TEXT)
- **类型**: 长文本
- **约束**: 可为空
- **说明**: 产品的详细描述，包括产品特点、历史、发展现状等
- **字数**: 200-300字
- **内容包括**:
  - 产品基本特点
  - 产地优势条件
  - 认证信息简述
  - 品牌价值或市场地位
  - 历史沿革简介
- **示例**: 以乌兰察布马铃薯为例，包含产地条件、品质特点、认证时间和品牌价值

### 7. characteristics (JSON)
- **类型**: JSON数组
- **约束**: 可为空
- **说明**: 产品的核心特征，以数组形式存储
- **数组元素**: 字符串，4-5项
- **说明文本**: 具体的特征描述
- **示例**:
  ```json
  [
    "淀粉含量高（>17%）",
    "昼夜温差大利于营养积累",
    "种植规模大、产量高",
    "薯型整齐、品质稳定"
  ]
  ```
- **用途**: 快速了解产品的主要优势

### 8. cultural_background (TEXT)
- **类型**: 长文本
- **约束**: 可为空
- **说明**: 产品的文化背景和历史故事
- **字数**: 150-300字
- **内容包括**:
  - 历史渊源和年代
  - 文化意义和传统
  - 地方特色和民族特点
  - 产业发展历程
  - 与当地文化的关联
- **示例**: 乌兰察布马铃薯的"中国薯都"文化背景

### 9. certifications (JSON)
- **类型**: JSON数组
- **约束**: 可为空
- **说明**: 产品所获得的各类认证和荣誉
- **数组元素**: 字符串，3-5项
- **认证类型**:
  - 地理标志产品保护
  - 地理标志证明商标
  - 地理标志保护工程
  - 国家特色农产品优势区
  - 中欧地理标志协定保护
  - 国际奖项
  - 中国农业品牌
  - 驰名商标
- **示例**:
  ```json
  [
    "农产品地理标志登记保护（2008年农业部批准）",
    "地理标志证明商标（2011年注册）",
    "中国特色农产品优势区（2018年农业农村部）",
    "中国农民丰收节农产品百强榜（2020年）"
  ]
  ```

### 10. main_uses (JSON)
- **类型**: JSON数组
- **约束**: 可为空
- **说明**: 产品的主要用途和应用领域
- **数组元素**: 字符串，3-5项
- **用途分类**:
  - 直接食用
  - 原料生产
  - 工业加工
  - 出口贸易
  - 专业应用
- **示例**:
  ```json
  [
    "鲜食马铃薯",
    "淀粉生产原料",
    "种薯繁育",
    "食品工业原料",
    "饲料加工"
  ]
  ```

### 11. nutrition (JSON)
- **类型**: JSON对象（包含子字段）
- **约束**: 可为空
- **说明**: 产品的营养价值信息
- **子字段**:

#### 11.1 nutrition.key_nutrients (JSON数组)
- **说明**: 关键营养成分列表
- **数组元素**: 字符串，4-7项
- **内容**: 营养成分名称及百分比（如适用）
- **示例**:
  ```json
  [
    "淀粉（主要成分）",
    "蛋白质",
    "维生素B、C",
    "矿物质（钾、磷、镁）",
    "纤维素"
  ]
  ```

#### 11.2 nutrition.health_benefits (字符串)
- **说明**: 产品对健康的益处和功效
- **字数**: 100-200字
- **内容**: 营养价值、健康功效、适用人群等
- **示例**: 描述产品如何促进代谢、增强免疫等

### 12. production_process (TEXT)
- **类型**: 长文本
- **约束**: 可为空
- **说明**: 产品的传统和现代生产工艺
- **字数**: 150-200字
- **内容包括**:
  - 原料选择
  - 种植/饲养方式
  - 关键工序
  - 质量控制
  - 传统工艺要素
- **示例**: 从种子选择、土壤条件、水肥管理到收获后处理的完整过程

### 13. cultural_tags (JSON)
- **类型**: JSON数组
- **约束**: 可为空
- **说明**: 与产品相关的文化、地理、产业标签
- **数组元素**: 字符串，4-5项
- **标签类型**:
  - 地理特征标签（如"草原"、"黄河"）
  - 文化标签（如"游牧文化"、"农业文明"）
  - 产业标签（如"现代农业"、"品牌农业"）
  - 品质标签（如"绿色食品"、"有机产品"）
- **示例**:
  ```json
  [
    "蒙古草原",
    "游牧文化",
    "高端肉类",
    "品牌农业",
    "绿色畜产品"
  ]
  ```

### 14. market_price_range (VARCHAR(100))
- **类型**: 变长字符串
- **约束**: 可为空
- **说明**: 市场上的价格范围（基于2024-2025年数据）
- **格式**: "最低价-最高价单位"
- **单位**: 元/斤、元/克、元/升等
- **示例**: "80-120元/斤（冷鲜羊肉）"、"3.5-5.5元/斤（原粮）"
- **说明**: 价格仅供参考，实际市场价格可能波动

### 15. best_season (VARCHAR(100))
- **类型**: 变长字符串
- **约束**: 可为空
- **说明**: 产品的最佳生产、销售或食用季节
- **格式**: "月份范围（季节说明）"或"全年"
- **示例**:
  - "10月-次年3月（冬季最佳）"
  - "6月-12月（夏季收获上市）"
  - "5月-9月（春夏季最佳）"
  - "全年均可，秋冬季最佳"
- **应用**: 指导消费者的购买时机和食用时机

### 16. storage_method (TEXT)
- **类型**: 长文本
- **约束**: 可为空
- **说明**: 产品的储存方法和保存条件
- **字数**: 100-150字
- **内容包括**:
  - 温度要求
  - 湿度要求
  - 存储环境（通风、黑暗等）
  - 防护措施（防虫、防霉等）
  - 保质期
- **示例**: "冷冻保存于-18℃以下，可保存6-12个月；冷鲜保存于0-4℃，可保存5-7天"

### 17. cooking_suggestions (JSON)
- **类型**: JSON数组
- **约束**: 可为空
- **说明**: 产品的推荐烹饪或使用方法
- **数组元素**: 字符串，4-5项
- **内容类型**:
  - 烹饪方法（煮、炖、烤、炸等）
  - 食用方式（鲜食、加工等）
  - 搭配建议
  - 食用场景
- **示例**:
  ```json
  [
    "涮羊肉（切薄片）",
    "烤羊肉串",
    "炖羊肉汤",
    "红烧羊肉块",
    "羊肉面食"
  ]
  ```

### 18. created_at (TIMESTAMP)
- **类型**: 时间戳
- **约束**: DEFAULT CURRENT_TIMESTAMP
- **说明**: 记录创建时间，自动设置为当前时间
- **格式**: YYYY-MM-DD HH:MM:SS
- **示例**: "[项目完成日期] 10:30:45"

### 19. updated_at (TIMESTAMP)
- **类型**: 时间戳
- **约束**: DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
- **说明**: 记录更新时间，修改时自动更新
- **格式**: YYYY-MM-DD HH:MM:SS
- **示例**: "[项目完成日期] 10:30:45"

---

## 索引定义

### 主键索引
```sql
PRIMARY KEY (id)
```
- 唯一标识每条记录
- 自动递增

### 普通索引

#### idx_name
```sql
INDEX idx_name (name)
```
- **字段**: name
- **用途**: 按产品名称快速查询
- **查询示例**: WHERE name = '乌兰察布马铃薯'

#### idx_category
```sql
INDEX idx_category (category)
```
- **字段**: category
- **用途**: 按产品分类快速查询
- **查询示例**: WHERE category = '农产品'

#### idx_region
```sql
INDEX idx_region (region)
```
- **字段**: region
- **用途**: 按产地快速查询
- **查询示例**: WHERE region LIKE '%锡林郭勒%'

---

## 数据类型说明

| 类型 | 说明 | 存储空间 | 最大值 |
|------|------|---------|--------|
| INT | 整数 | 4字节 | 2,147,483,647 |
| VARCHAR(100) | 可变长字符串 | 最长100字符 | 100个汉字 |
| VARCHAR(200) | 可变长字符串 | 最长200字符 | 200个汉字 |
| VARCHAR(50) | 可变长字符串 | 最长50字符 | 50个汉字 |
| TEXT | 长文本 | 最长64KB | 约21,000个汉字 |
| JSON | JSON数据 | 可变 | 受TEXT大小限制 |
| TIMESTAMP | 时间戳 | 4字节 | 2038-01-19 |

---

## JSON字段的操作示例

### 查询JSON数组元素
```sql
-- 查询包含某个特征的产品
SELECT * FROM products
WHERE JSON_CONTAINS(characteristics, JSON_QUOTE('淀粉含量高'));

-- 获取第一个特征
SELECT JSON_EXTRACT(characteristics, '$[0]') FROM products WHERE id = 1;
```

### 修改JSON字段
```sql
-- 添加新的特征
UPDATE products
SET characteristics = JSON_ARRAY_APPEND(characteristics, '$', '新特征')
WHERE id = 1;

-- 修改特定元素
UPDATE products
SET characteristics = JSON_SET(characteristics, '$[0]', '新描述')
WHERE id = 1;
```

### 搜索JSON字段
```sql
-- 搜索包含特定标签的产品
SELECT * FROM products
WHERE JSON_SEARCH(cultural_tags, 'one', '草原') IS NOT NULL;
```

---

## 数据验证规则

### 必填字段
- id (系统自动)
- name
- category
- province
- region

### 可选字段
- 其他所有字段

### 字段值验证

#### name
- 长度: 1-100字符
- 必须是产品的官方地理标志名称
- 不允许重复

#### category
- 允许值: '农产品', '畜产品', '特产'
- 其他值将被拒绝

#### province
- 本数据集固定值: '内蒙古自治区'

#### market_price_range
- 格式: "数字-数字单位"
- 示例: "2.5-4.5元/斤"

#### JSON字段
- 必须是有效的JSON格式
- 数组元素必须是字符串
- 不允许嵌套过深

---

## 常见查询模式

### 1. 按分类查询
```sql
SELECT name, region, market_price_range
FROM products
WHERE category = '农产品'
ORDER BY name;
```

### 2. 按地区查询
```sql
SELECT * FROM products
WHERE region LIKE '%通辽%'
ORDER BY name;
```

### 3. 按价格范围查询
```sql
SELECT name, market_price_range
FROM products
WHERE market_price_range LIKE '%元%'
ORDER BY name;
```

### 4. 获取完整产品信息
```sql
SELECT id, name, category, region, description,
       market_price_range, best_season
FROM products
WHERE id = 1;
```

### 5. 统计产品分布
```sql
SELECT category, COUNT(*) as count
FROM products
GROUP BY category;
```

---

## 导出和备份

### 导出为CSV
```sql
SELECT id, name, category, region, market_price_range
FROM products
INTO OUTFILE '/path/to/export.csv'
FIELDS TERMINATED BY ','
ENCLOSED BY '"'
LINES TERMINATED BY '\n';
```

### 备份表结构
```bash
mysqldump -u user -p database_name products --no-data > backup_structure.sql
```

### 完整备份
```bash
mysqldump -u user -p database_name products > backup_full.sql
```

---

**文档版本**: 1.0
**最后更新**: [项目完成日期]
**兼容数据库**: MySQL 5.7+, MySQL 8.0+, MariaDB 10.4+
