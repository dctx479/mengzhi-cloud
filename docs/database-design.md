### 3.4 常用查询示例

---

## 4. Qdrant向量数据库设计

### 4.1 Collection配置

| 配置项 | 值 | 说明 |
|--------|-----|------|
| collection_name | product_knowledge | 产品知识向量集合 |
| vector_size | 1536 | text-embedding-3-small维度 |
| distance | Cosine | 余弦相似度 |
| on_disk | true | 大数据量时启用磁盘存储 |
| hnsw_config.m | 16 | HNSW图连接数 |
| hnsw_config.ef_construct | 100 | 构建时搜索范围 |

### 4.2 Python代码实现

**创建Collection:**

### 4.3 Payload结构定义

| 字段 | 类型 | 说明 |
|------|------|------|
| id | string | 向量唯一标识 |
| type | string | 内容类型: product_description/cultural_story/craft_intro/region_info |
| product_uuid | string | 关联产品UUID |
| product_name | string | 产品名称 |
| category | string | 产品类别 |
| sub_category | string | 产品子类别 |
| chunk_index | int | 分块索引 |
| chunk_total | int | 总分块数 |
| text | string | 原始文本内容 |
| source | string | 数据来源 |
| created_at | string | 创建时间(ISO 8601) |



---

## 4. Qdrant向量数据库设计

### 4.1 集合配置

| 配置项 | 值 | 说明 |
|-------|-----|------|
| collection_name | product_knowledge | 集合名称 |
| vector_size | 1536 | 向量维度(text-embedding-3-small) |
| distance | Cosine | 距离度量方式 |

### 4.2 创建集合



### 4.3 Payload结构定义



### 4.4 向量化与插入



### 4.5 向量检索


### 6.2 数据库索引说明

#### 6.2.1 MySQL索引策略

| 表名 | 索引名 | 索引字段 | 索引类型 | 用途 |
|------|--------|----------|----------|------|
| users | uk_user_uuid | user_uuid | UNIQUE | UUID唯一性 |
| users | uk_username | username | UNIQUE | 用户名唯一性 |
| users | uk_email | email | UNIQUE | 邮箱唯一性 |
| users | idx_user_type | user_type | BTREE | 用户类型查询 |
| users | idx_status | status | BTREE | 状态筛选 |
| users | idx_enterprise_id | enterprise_id | BTREE | 企业关联查询 |
| products | uk_product_uuid | product_uuid | UNIQUE | UUID唯一性 |
| products | idx_category | category | BTREE | 分类查询 |
| products | idx_origin_province | origin_province | BTREE | 产地查询 |
| products | ft_name_description | name, description | FULLTEXT | 全文搜索 |
| content_records | idx_user_id | user_id | BTREE | 用户记录查询 |
| content_records | idx_content_type | content_type | BTREE | 内容类型筛选 |
| ai_conversations | idx_user_id | user_id | BTREE | 用户对话查询 |
| ai_messages | idx_conversation_id | conversation_id | BTREE | 对话消息查询 |

#### 6.2.2 Neo4j索引策略

| 节点/关系 | 索引属性 | 索引类型 | 用途 |
|----------|----------|----------|------|
| Product | uuid | UNIQUE | 唯一标识 |
| Product | name | BTREE | 名称查询 |
| Product | category | BTREE | 分类查询 |
| Region | uuid | UNIQUE | 唯一标识 |
| Region | name | BTREE | 名称查询 |
| Culture | uuid | UNIQUE | 唯一标识 |
| Culture | type | BTREE | 类型查询 |

---

## 7. 附录

### 7.1 数据库版本要求

| 数据库 | 最低版本 | 推荐版本 | 说明 |
|--------|----------|----------|------|
| MySQL | 8.0.0 | 8.0.35+ | 需支持JSON字段和全文索引 |
| Neo4j | 5.0.0 | 5.15+ | 社区版即可 |
| Qdrant | 1.7.0 | 1.7.4+ | 支持HNSW索引 |
| Redis | 7.0.0 | 7.2+ | 支持新数据结构 |

### 7.2 连接配置示例

**MySQL连接:**
**Neo4j连接:**
**Qdrant连接:**
**Redis连接:**
### 7.3 数据库维护建议

#### 7.3.1 MySQL维护

- **定期备份**: 每日全量备份，每小时增量备份
- **索引优化**: 每月执行ANALYZE TABLE
- **慢查询监控**: 开启slow_query_log，阈值设为1秒
- **表优化**: 大表考虑分区（按月分区content_records表）

#### 7.3.2 Neo4j维护

- **定期备份**: 使用neo4j-admin backup
- **索引维护**: 定期重建索引
- **查询优化**: 使用PROFILE分析查询计划

#### 7.3.3 Qdrant维护

- **快照备份**: 定期创建collection快照
- **索引优化**: 数据量变化大时重建索引
- **内存监控**: 关注向量加载状态

#### 7.3.4 Redis维护

- **持久化**: 开启RDB和AOF双持久化
- **内存监控**: 设置maxmemory和淘汰策略
- **定期清理**: 清理过期key

---

**文档版本**: v1.0  
**最后更新**: [项目完成日期]  
**维护者**: AI赋能云平台技术团队
