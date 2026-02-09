# Alembic 数据库迁移配置总结

**配置时间**: [项目完成日期]
**版本**: 1.0
**项目**: 内蒙古农畜产品AI平台

## 已完成的任务

### ✓ 1. 配置文件

#### alembic.ini
- 数据库连接配置
- 迁移脚本目录设置
- 日志配置
- 支持环境变量

#### alembic/env.py
- 导入所有模型（User, Product, Conversation, Message）
- 自动检测模型变更
- 支持在线和离线模式
- 使用BaseModel定义的共同字段

#### alembic/script.py.mako
- 迁移脚本模板
- 标准upgrade()和downgrade()函数

### ✓ 2. 迁移脚本

#### alembic/versions/001_initial.py
创建了初始数据库架构：

**users 表**:
- id (BIGINT, 主键)
- user_uuid, username, email, phone (唯一)
- password_hash, user_type, status, role
- wechat_openid, douyin_openid (社交登录)
- created_at, updated_at, deleted_at
- 9个索引

**products 表**:
- id (Integer, 主键)
- sku (唯一)
- name, description, category
- price, cost, stock
- region, cultural_tags, cultural_description
- origin_story, efficacy, usage
- status, is_featured
- 8个索引

**conversations 表**:
- id (UUID, 主键)
- user_id (对话所有者)
- title, description
- message_count, total_tokens, total_cost
- status, is_favorited
- 3个索引

**messages 表**:
- id (UUID, 主键)
- conversation_id (外键)
- role, content
- input_tokens, output_tokens, total_tokens, cost
- model, finish_reason
- rating, feedback
- 3个索引

### ✓ 3. 辅助脚本

#### scripts/init_db.py
初始化数据库脚本：
- 检查数据库连接
- 创建所有表
- 验证表结构
- 可选：创建种子数据
- 可选：删除现有表后重建

用法:
```bash
python -m scripts.init_db                # 创建表
python -m scripts.init_db --seed         # 创建表+种子数据
python -m scripts.init_db --drop --seed  # 删除重建+种子数据
```

#### scripts/seed_data.py
种子数据脚本：
- 创建1个管理员账户 (admin / admin123456)
- 创建5个测试用户 (testuser001-005 / password123)
- 创建10个示例产品（内蒙古特色产品）
- 创建3个示例对话和消息记录

用法:
```bash
python -m scripts.seed_data                          # 默认数据
python -m scripts.seed_data --users 10 --products 20 # 自定义数量
python -m scripts.seed_data --clear                  # 清空后重建
```

#### scripts/db_migrate.py
迁移管理脚本：
- status: 查看迁移状态
- history: 查看迁移历史
- upgrade: 升级到指定版本
- downgrade: 回滚到指定版本
- current: 查看当前版本
- heads: 查看最新版本

用法:
```bash
python -m scripts.db_migrate status                 # 查看状态
python -m scripts.db_migrate upgrade                # 升级
python -m scripts.db_migrate downgrade              # 回滚
```

### ✓ 4. 文档

#### ALEMBIC_GUIDE.md
完整的Alembic配置指南：
- 概述和目录结构
- 快速开始
- 配置文件详解
- 模型和迁移关系
- 常见操作
- 最佳实践
- 故障排除
- 生产环境部署

#### MIGRATION_COMMANDS.md
快速命令参考：
- 初始化和设置
- 查看状态
- 创建迁移
- 执行迁移
- 回滚迁移
- 种子数据管理
- 完整工作流程

## 文件结构

```
E:\项目\数商\AI赋能云平台\backend\
├── alembic.ini                          # Alembic配置文件
├── ALEMBIC_GUIDE.md                     # 完整指南
├── MIGRATION_COMMANDS.md                # 快速参考
├── alembic/
│   ├── __init__.py
│   ├── env.py                           # 迁移环境配置
│   ├── script.py.mako                   # 迁移脚本模板
│   └── versions/
│       ├── __init__.py
│       └── 001_initial.py               # 初始迁移脚本
├── app/
│   ├── models/
│   │   ├── base.py                      # BaseModel（包含created_at等）
│   │   ├── user.py                      # User模型
│   │   ├── product.py                   # Product模型
│   │   └── conversation.py              # Conversation, Message模型
│   ├── database.py                      # SQLAlchemy引擎配置
│   └── core/
│       └── config.py                    # Settings（包含DATABASE_URL）
└── scripts/
    ├── init_db.py                       # 初始化脚本
    ├── seed_data.py                     # 种子数据脚本
    └── db_migrate.py                    # 迁移管理脚本
```

## 快速开始

### 1. 首次初始化

```bash
# 创建所有表
python -m scripts.init_db

# 或者创建表+种子数据
python -m scripts.init_db --seed
```

### 2. 查看状态

```bash
# 检查迁移状态
python -m scripts.db_migrate status

# 查看迁移历史
python -m scripts.db_migrate history
```

### 3. 执行迁移

```bash
# 升级到最新
alembic upgrade head

# 回滚一个版本
alembic downgrade -1
```

## 关键特点

### 自动化
- 自动检测模型变更
- 自动生成迁移脚本
- 自动验证表结构

### 灵活性
- 支持自动和手动迁移
- 支持在线和离线模式
- 支持环境变量配置

### 可靠性
- 包含完整的upgrade()和downgrade()
- 外键约束正确设置
- 索引优化完整

### 可维护性
- 模块化的脚本结构
- 详细的代码注释
- 完整的文档

## 数据库URL配置

### 当前配置
```
mysql+pymysql://root:root123@localhost:3306/agri_platform?charset=utf8mb4
```

### 修改方式

**方式1: 环境变量（推荐）**
```bash
export DATABASE_URL=mysql+pymysql://user:password@host:port/database
```

**方式2: .env文件**
```
DATABASE_URL=mysql+pymysql://user:password@host:port/database
```

**方式3: 代码配置**
编辑 `app/core/config.py`:
```python
DATABASE_URL: str = "mysql+pymysql://user:password@host:port/database"
```

## 模型导入

所有模型已在 `alembic/env.py` 中导入：

```python
from app.models.base import Base
from app.models.user import User
from app.models.product import Product
from app.models.conversation import Conversation, Message
```

当添加新模型时，需要：
1. 在 `alembic/env.py` 中导入新模型
2. 确保新模型继承自 `BaseModel`
3. 生成新的迁移脚本

## 常见命令

### 初始化
```bash
python -m scripts.init_db --seed
```

### 迁移
```bash
alembic revision --autogenerate -m "description"  # 生成
alembic upgrade head                              # 升级
alembic downgrade -1                              # 回滚
```

### 管理
```bash
python -m scripts.db_migrate status               # 查看状态
python -m scripts.db_migrate history              # 查看历史
python -m scripts.seed_data --clear               # 清空数据
```

## 验证

### 检查表创建
```bash
# 使用MySQL命令行
mysql -u root -p agri_platform -e "SHOW TABLES;"

# 或使用Python脚本
python -m scripts.db_migrate status
```

### 检查索引
```bash
mysql -u root -p agri_platform -e "SHOW INDEXES FROM users;"
```

### 检查迁移记录
```bash
mysql -u root -p agri_platform -e "SELECT * FROM alembic_version;"
```

## 故障排除

### 无法连接到数据库
- 检查MySQL服务是否运行
- 检查DATABASE_URL配置
- 检查用户名和密码

### 迁移失败
- 查看详细错误信息
- 检查SQL语法
- 回滚到上个版本

### 模型导入错误
- 检查模型文件路径
- 检查alembic/env.py中的导入
- 检查Python路径配置

## 下一步

1. **运行初始化脚本**
   ```bash
   python -m scripts.init_db --seed
   ```

2. **验证数据库**
   ```bash
   python -m scripts.db_migrate status
   ```

3. **开始开发**
   - 修改模型
   - 生成迁移
   - 执行迁移

4. **部署到生产**
   - 备份数据库
   - 执行迁移
   - 验证结果

## 支持文档

- **完整指南**: `ALEMBIC_GUIDE.md`
- **快速参考**: `MIGRATION_COMMANDS.md`
- **Alembic官方**: https://alembic.sqlalchemy.org/
- **SQLAlchemy ORM**: https://docs.sqlalchemy.org/en/20/orm/

## 许可和贡献

配置版本: 1.0
创建日期: [项目完成日期]

---

**提示**: 所有脚本都包含详细的帮助信息，使用 `--help` 参数查看:
```bash
python -m scripts.init_db --help
python -m scripts.seed_data --help
python -m scripts.db_migrate --help
```
