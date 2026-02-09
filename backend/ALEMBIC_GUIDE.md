# Alembic 数据库迁移配置指南

## 概述

本项目使用 **Alembic** 进行数据库版本管理和迁移。Alembic是SQLAlchemy的迁移工具，可以自动检测模型变更并生成迁移脚本。

**版本**: 1.0
**更新日期**: [项目完成日期]

## 目录结构

```
backend/
├── alembic.ini                    # Alembic配置文件
├── alembic/
│   ├── __init__.py               # 包标记
│   ├── env.py                    # 迁移环境配置（关键）
│   ├── script.py.mako            # 迁移脚本模板
│   └── versions/
│       ├── __init__.py
│       └── 001_initial.py        # 初始迁移脚本
├── app/
│   ├── models/
│   │   ├── base.py               # 基类（定义Base）
│   │   ├── user.py               # 用户模型
│   │   ├── product.py            # 产品模型
│   │   └── conversation.py       # 对话和消息模型
│   ├── database.py               # 数据库连接
│   └── core/
│       └── config.py             # 配置（数据库URL）
└── scripts/
    ├── init_db.py                # 数据库初始化脚本
    ├── seed_data.py              # 种子数据脚本
    └── db_migrate.py             # 迁移管理脚本
```

## 快速开始

### 1. 首次设置

```bash
# 1. 初始化数据库表
python -m scripts.init_db

# 2. 创建种子数据（可选）
python -m scripts.init_db --seed

# 3. 验证迁移状态
python -m scripts.db_migrate status
```

### 2. 查看迁移状态

```bash
# 查看当前迁移版本
python -m scripts.db_migrate status

# 查看迁移历史
python -m scripts.db_migrate history

# 查看当前版本
python -m scripts.db_migrate current

# 查看最新版本
python -m scripts.db_migrate heads
```

### 3. 执行迁移

```bash
# 升级到最新版本
python -m scripts.db_migrate upgrade

# 升级到指定版本
python -m scripts.db_migrate upgrade 001_initial

# 回滚一个版本
python -m scripts.db_migrate downgrade

# 回滚到指定版本
python -m scripts.db_migrate downgrade 001_initial
```

## 配置文件详解

### alembic.ini

主要配置项：

```ini
[alembic]
scriptdir = alembic              # 迁移脚本目录
prepend_sys_path = .             # 添加当前目录到Python路径

[sqlalchemy]
sqlalchemy.url = mysql+pymysql://user:password@host:port/database
```

**重要**: 数据库URL从环境变量或 `app.core.config` 读取，不应硬编码。

### env.py

关键功能：

1. **导入所有模型**
   ```python
   from app.models.user import User
   from app.models.product import Product
   from app.models.conversation import Conversation, Message
   ```

2. **自动检测变更**
   ```python
   target_metadata = Base.metadata
   compare_type=True               # 比较列类型
   compare_server_default=True     # 比较服务器默认值
   ```

3. **支持在线和离线迁移**
   - **在线模式**: 连接到数据库，生成SQL并执行
   - **离线模式**: 只生成SQL脚本，不执行

## 初始迁移脚本 (001_initial.py)

创建了以下表：

### users（用户表）
- 主键: id (BIGINT)
- 唯一字段: user_uuid, username, email, phone
- 索引: user_type, status, enterprise_id, created_at, deleted_at
- 约束: 所有UNIQUE和NOT NULL约束

### products（产品表）
- 主键: id (Integer)
- 唯一字段: sku
- 索引: 按类别、区域、状态分组的复合索引
- JSON字段: cultural_tags

### conversations（对话表）
- 主键: id (String/UUID)
- 外键: user_id (字符串，对应users的UUID)
- 索引: (user_id, created_at), (user_id, status)

### messages（消息表）
- 主键: id (String/UUID)
- 外键: conversation_id (指向conversations.id)
- 索引: (conversation_id, role), created_at

## 模型和迁移的关系

### BaseModel 字段

所有模型自动继承以下字段（通过 `BaseModel`）：

```python
created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
updated_at = Column(DateTime, onupdate=datetime.utcnow, nullable=False)
deleted_at = Column(DateTime, nullable=True)  # 软删除
```

### 在迁移脚本中引用这些字段

```python
# 创建表时自动包含基础字段
sa.Column('created_at', sa.DateTime(), nullable=False),
sa.Column('updated_at', sa.DateTime(), nullable=False),
sa.Column('deleted_at', sa.DateTime(), nullable=True),
```

## 常见操作

### 创建新迁移

当修改模型后：

```bash
# 1. 修改 app/models/*.py
# 2. 生成自动迁移
alembic revision --autogenerate -m "add new column to users"

# 3. 检查生成的迁移脚本 (alembic/versions/xxx_add_new_column_to_users.py)
# 4. 根据需要手动调整

# 5. 执行迁移
alembic upgrade head
```

### 手动创建迁移

如果自动生成不准确，手动创建：

```bash
# 创建空的迁移脚本
alembic revision -m "custom migration"

# 编辑生成的文件，添加upgrade()和downgrade()内容
```

### 回滚更改

```bash
# 查看历史
alembic history

# 回滚一个版本
alembic downgrade -1

# 回滚到某个特定版本
alembic downgrade 001_initial

# 回滚所有
alembic downgrade base
```

### 导出SQL（不执行）

```bash
# 生成升级SQL
alembic upgrade head --sql

# 生成回滚SQL
alembic downgrade -1 --sql
```

## 数据库初始化脚本

### init_db.py

```bash
# 创建表
python -m scripts.init_db

# 创建表并填充种子数据
python -m scripts.init_db --seed

# 删除现有表后重建
python -m scripts.init_db --drop

# 显示详细输出
python -m scripts.init_db --verbose
```

**功能**：
- 检查数据库连接
- 显示现有表
- 创建所有表（通过Alembic迁移）
- 验证表结构
- 可选：创建种子数据

### seed_data.py

```bash
# 创建默认种子数据（5个用户，10个产品）
python -m scripts.seed_data

# 创建指定数量的数据
python -m scripts.seed_data --users 10 --products 20

# 先清空再创建
python -m scripts.seed_data --clear

# 组合使用
python -m scripts.seed_data --clear --users 5 --products 10
```

**创建的数据**：
- 1个管理员账户 (username: admin, password: admin123456)
- 5个测试用户 (testuser001-testuser005, password: password123)
- 10个示例产品（内蒙古特色产品）
- 3个示例对话（带消息记录）

## 迁移管理脚本

### db_migrate.py

```bash
# 查看迁移状态
python -m scripts.db_migrate status

# 查看迁移历史
python -m scripts.db_migrate history

# 升级到最新
python -m scripts.db_migrate upgrade

# 升级到指定版本
python -m scripts.db_migrate upgrade 001_initial

# 回滚一个版本
python -m scripts.db_migrate downgrade

# 回滚到指定版本
python -m scripts.db_migrate downgrade 001_initial

# 查看最新版本
python -m scripts.db_migrate heads

# 查看当前版本
python -m scripts.db_migrate current

# 查看分支信息
python -m scripts.db_migrate branches
```

## 数据库URL配置

### 方式1: 环境变量（推荐）

创建 `.env` 文件：

```ini
DATABASE_URL=mysql+pymysql://user:password@localhost:3306/agri_platform?charset=utf8mb4
```

### 方式2: 直接修改配置

编辑 `app/core/config.py`：

```python
DATABASE_URL: str = "mysql+pymysql://root:root123@localhost:3306/agri_platform?charset=utf8mb4"
```

### 数据库URL格式

```
mysql+pymysql://用户名:密码@主机:端口/数据库名?charset=utf8mb4
```

- **用户名**: 数据库用户
- **密码**: 数据库密码
- **主机**: localhost 或 IP地址
- **端口**: 默认3306
- **数据库名**: agri_platform
- **charset**: utf8mb4（支持emoji）

## 最佳实践

### 1. 创建迁移前

```bash
# 确保所有改动都已提交
git status

# 创建新分支（可选）
git checkout -b feature/db-migration
```

### 2. 编写迁移

```bash
# 修改模型
# 编辑 app/models/*.py

# 生成迁移
alembic revision --autogenerate -m "descriptive message"

# 验证迁移
cat alembic/versions/xxx_descriptive_message.py
```

### 3. 测试迁移

```bash
# 升级
alembic upgrade head

# 验证
python -m scripts.db_migrate status

# 回滚（测试downgrade）
alembic downgrade -1

# 再升级
alembic upgrade head
```

### 4. 文档化

```bash
# 查看迁移历史
alembic history

# 导出为文档
alembic history > MIGRATION_HISTORY.txt
```

## 故障排除

### 问题1: 无法连接到数据库

**原因**: 数据库URL错误或数据库服务未启动

**解决**:
```bash
# 检查数据库服务
mysql -u root -p

# 检查URL配置
echo $DATABASE_URL
```

### 问题2: 模型导入错误

**原因**: env.py 中缺少模型导入

**解决**:
```python
# 在 alembic/env.py 中添加
from app.models.user import User
from app.models.product import Product
from app.models.conversation import Conversation, Message
```

### 问题3: 自动迁移生成不准确

**原因**: 某些数据库变更Alembic无法自动检测

**解决**:
```bash
# 手动创建迁移
alembic revision -m "manual migration"

# 编辑生成的脚本
# 在upgrade()和downgrade()函数中手动编写SQL

# 例如：
def upgrade():
    op.execute("ALTER TABLE users ADD COLUMN new_field VARCHAR(100)")

def downgrade():
    op.execute("ALTER TABLE users DROP COLUMN new_field")
```

### 问题4: 忘记迁移某个版本

**查看哪些版本未执行**:
```bash
# 查看当前版本
alembic current

# 查看最新版本
alembic heads

# 如果不同，说明有未执行的迁移
alembic upgrade head
```

## 生产环境部署

### 部署前清单

- [ ] 所有迁移脚本已测试
- [ ] 有数据库备份
- [ ] 迁移脚本已代码审查
- [ ] 回滚计划已准备

### 部署步骤

```bash
# 1. 备份数据库
mysqldump -u root -p agri_platform > backup_$(date +%Y%m%d_%H%M%S).sql

# 2. 运行迁移
alembic upgrade head

# 3. 验证
python -m scripts.db_migrate status

# 4. 回滚计划
# 如果出现问题，运行：
# alembic downgrade -1
```

## 相关文件

- **配置**: `alembic.ini`, `alembic/env.py`
- **迁移脚本**: `alembic/versions/`
- **模型定义**: `app/models/`
- **脚本**: `scripts/init_db.py`, `scripts/seed_data.py`, `scripts/db_migrate.py`
- **数据库配置**: `app/core/config.py`, `app/database.py`

## 参考链接

- [Alembic官方文档](https://alembic.sqlalchemy.org/)
- [SQLAlchemy ORM教程](https://docs.sqlalchemy.org/en/20/orm/)
- [MySQL字符集](https://dev.mysql.com/doc/refman/8.0/en/charset.html)

## 常见问题

**Q: 如何撤销已发布的迁移？**

A: 创建新的迁移脚本来撤销变更，不要修改或删除现有迁移。

**Q: 如何在不同环境使用不同的数据库？**

A: 通过环境变量设置不同的DATABASE_URL：
```bash
# 开发环境
export DATABASE_URL=mysql+pymysql://root:pass@localhost:3306/dev_db

# 测试环境
export DATABASE_URL=mysql+pymysql://root:pass@test-server:3306/test_db

# 生产环境
export DATABASE_URL=mysql+pymysql://prod_user:pass@prod-server:3306/prod_db
```

**Q: 如何处理数据库中的数据？**

A: 迁移脚本可以包含数据操作逻辑：
```python
def upgrade():
    # 创建表
    op.create_table(...)
    # 迁移数据
    op.execute("INSERT INTO new_table SELECT ... FROM old_table")
    # 删除旧表
    op.drop_table('old_table')

def downgrade():
    # 反向操作
    op.create_table(...)
    op.execute("INSERT INTO old_table SELECT ... FROM new_table")
    op.drop_table('new_table')
```

**Q: 如何实现零停机迁移？**

A: 使用分阶段的迁移：
1. 添加新列但不删除旧列
2. 在应用中更新代码以使用新列
3. 在后续迁移中删除旧列

这样可以保证向后兼容。
