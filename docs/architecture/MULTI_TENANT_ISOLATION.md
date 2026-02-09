# 多租户完全隔离架构设计

## 概述

本文档描述了AI赋能云平台的多租户数据隔离架构，支持两种隔离模式：
- **企业级隔离**：独立数据库（Database per Tenant）
- **个人用户**：共享数据库，独立表空间（Shared Database）

## 架构设计

### 1. 隔离模式

#### 1.1 企业级隔离（Database per Tenant）

**适用场景**：
- 企业用户（Enterprise）
- 专业版及以上套餐
- 需要数据完全隔离的场景

**优势**：
- 数据完全隔离，安全性最高
- 性能隔离，互不影响
- 独立备份和恢复
- 支持定制化Schema
- 便于数据迁移和导出

**实现方式**：
```
主数据库（agri_platform）
├── users（用户表）
├── enterprises（企业表）
└── tenant_metadata（租户元数据）

租户数据库（tenant_<enterprise_id>）
├── products（产品表）
├── conversations（对话表）
├── messages（消息表）
├── content_records（内容记录表）
└── ... （其他业务表）
```

#### 1.2 个人用户共享模式（Shared Database）

**适用场景**：
- 个人用户（Personal）
- 免费版和基础版用户
- 数据量较小的场景

**优势**：
- 资源利用率高
- 管理成本低
- 适合大量小用户

**实现方式**：
```
主数据库（agri_platform）
├── users（用户表）
├── enterprises（企业表）
├── products（产品表，包含user_id/enterprise_id）
├── conversations（对话表，包含user_id）
└── ... （所有业务表，通过user_id/enterprise_id隔离）
```

### 2. 数据库路由

#### 2.1 路由策略

```python
def get_tenant_database(tenant_context: TenantContext) -> Session:
    """
    根据租户上下文路由到正确的数据库

    路由规则：
    1. 企业用户 + 独立数据库模式 -> 租户数据库
    2. 个人用户 -> 主数据库
    3. 企业用户 + 共享模式 -> 主数据库
    """
    if tenant_context.isolation_mode == "isolated":
        return get_tenant_db_session(tenant_context.tenant_id)
    else:
        return get_main_db_session()
```

#### 2.2 连接池管理

每个租户数据库维护独立的连接池：
- 初始连接数：5
- 最大连接数：20
- 连接超时：30秒
- 连接回收：3600秒

### 3. 租户元数据

#### 3.1 Enterprise表扩展

```python
class Enterprise(BaseModel):
    # ... 现有字段

    # 隔离模式
    isolation_mode = Column(
        Enum(IsolationMode),
        default=IsolationMode.SHARED,
        comment="隔离模式：shared共享/isolated独立"
    )

    # 数据库信息
    database_name = Column(
        VARCHAR(100),
        nullable=True,
        comment="独立数据库名称"
    )

    database_created_at = Column(
        TIMESTAMP,
        nullable=True,
        comment="数据库创建时间"
    )
```

#### 3.2 租户元数据表

```sql
CREATE TABLE tenant_metadata (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    enterprise_id BIGINT NOT NULL,
    isolation_mode ENUM('shared', 'isolated') NOT NULL,
    database_name VARCHAR(100),
    database_host VARCHAR(255),
    database_port INT,
    connection_pool_size INT DEFAULT 10,
    max_connections INT DEFAULT 20,
    status ENUM('active', 'migrating', 'inactive') NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_enterprise_id (enterprise_id),
    INDEX idx_status (status)
);
```

### 4. 数据迁移

#### 4.1 从共享到独立

```
1. 创建租户数据库
2. 初始化表结构
3. 复制数据（按enterprise_id过滤）
4. 验证数据完整性
5. 更新租户元数据
6. 切换路由
7. 删除原数据（可选）
```

#### 4.2 从独立到共享

```
1. 验证主数据库容量
2. 复制数据到主数据库
3. 添加enterprise_id字段
4. 验证数据完整性
5. 更新租户元数据
6. 切换路由
7. 删除租户数据库（可选）
```

### 5. 备份和恢复

#### 5.1 独立数据库备份

```bash
# 单个租户备份
mysqldump -u root -p tenant_<enterprise_id> > backup_<enterprise_id>_<date>.sql

# 自动化备份脚本
python scripts/backup_tenant.py --enterprise-id <id> --output-dir backups/
```

#### 5.2 共享数据库备份

```bash
# 全量备份
mysqldump -u root -p agri_platform > backup_main_<date>.sql

# 按租户导出
mysqldump -u root -p agri_platform \
  --where="enterprise_id=<id>" \
  products conversations messages > backup_<enterprise_id>_<date>.sql
```

### 6. 性能优化

#### 6.1 连接池优化

- 使用连接池避免频繁创建连接
- 实现连接预热机制
- 监控连接池使用情况
- 动态调整连接池大小

#### 6.2 查询优化

- 为enterprise_id/user_id添加索引
- 使用分区表（按时间或租户）
- 实现查询缓存
- 使用读写分离

#### 6.3 缓存策略

```python
# 租户数据库连接缓存
tenant_db_cache = {
    "tenant_123": {
        "engine": engine,
        "session_factory": SessionLocal,
        "last_used": datetime.now()
    }
}

# 租户元数据缓存
tenant_metadata_cache = {
    "tenant_123": {
        "isolation_mode": "isolated",
        "database_name": "tenant_123",
        "ttl": 3600
    }
}
```

### 7. 安全性

#### 7.1 数据库权限

```sql
-- 为每个租户创建独立的数据库用户
CREATE USER 'tenant_123'@'%' IDENTIFIED BY 'secure_password';
GRANT ALL PRIVILEGES ON tenant_123.* TO 'tenant_123'@'%';
FLUSH PRIVILEGES;
```

#### 7.2 访问控制

- 租户只能访问自己的数据库
- 使用中间件验证租户身份
- 记录所有跨租户访问尝试
- 实现审计日志

### 8. 监控和告警

#### 8.1 监控指标

- 数据库连接数
- 查询响应时间
- 数据库大小
- 备份状态
- 迁移进度

#### 8.2 告警规则

- 连接池耗尽
- 查询超时
- 数据库空间不足
- 备份失败
- 迁移异常

### 9. 成本分析

#### 9.1 独立数据库模式

**优势**：
- 性能隔离，不受其他租户影响
- 数据安全性高
- 便于定制化

**成本**：
- 数据库实例成本高
- 管理复杂度高
- 适合付费企业用户

#### 9.2 共享数据库模式

**优势**：
- 资源利用率高
- 管理成本低
- 适合大量小用户

**成本**：
- 单点故障风险
- 性能可能受影响
- 适合免费/个人用户

### 10. 最佳实践

#### 10.1 租户创建

1. 验证企业信息
2. 选择隔离模式（根据套餐）
3. 创建租户数据库（如需要）
4. 初始化表结构
5. 创建默认数据
6. 更新租户元数据
7. 测试连接

#### 10.2 租户删除

1. 备份租户数据
2. 通知相关用户
3. 软删除（标记为inactive）
4. 等待确认期（30天）
5. 硬删除数据库
6. 清理元数据
7. 记录审计日志

#### 10.3 租户迁移

1. 评估迁移影响
2. 创建迁移计划
3. 通知用户（维护窗口）
4. 执行数据迁移
5. 验证数据完整性
6. 切换路由
7. 监控迁移后性能
8. 清理旧数据

## 实现清单

### 核心组件

- [x] 架构文档
- [ ] 数据库路由器（tenant_database.py）
- [ ] 租户数据库管理器（tenant_db_manager.py）
- [ ] 租户上下文增强（tenant_context.py）
- [ ] 配置管理（config.py）
- [ ] 租户管理API（tenant_management.py）
- [ ] 数据迁移工具（migrate_to_isolated.py）
- [ ] Enterprise模型更新

### 辅助工具

- [ ] 备份脚本
- [ ] 监控脚本
- [ ] 性能测试
- [ ] 文档和示例

## 参考资料

- [Multi-Tenancy Architecture Patterns](https://docs.microsoft.com/en-us/azure/architecture/guide/multitenant/overview)
- [Database per Tenant Pattern](https://martinfowler.com/articles/multi-tenant-saas.html)
- [SQLAlchemy Multi-Database Support](https://docs.sqlalchemy.org/en/14/core/engines.html)
