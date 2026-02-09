# Alembic 配置架构图

## 整体架构

```
┌─────────────────────────────────────────────────────────────┐
│                     应用程序 (FastAPI)                       │
│                    app/main.py                              │
└────────────────────────┬────────────────────────────────────┘
                         │
         ┌───────────────┼───────────────┐
         │               │               │
         ▼               ▼               ▼
    ┌─────────┐    ┌─────────┐    ┌─────────┐
    │ models/ │    │database │    │  api/   │
    │User     │    │SessionLocal   │Endpoints
    │Product  │    │engine        │
    │Convo    │    └─────────┘    └─────────┘
    │Message  │        ▲
    └────┬────┘        │
         │         ┌───────────────┐
         │         │ alembic/env.py│
         │         │ 导入所有模型    │
         │         └───────┬────────┘
         │                 │
    ┌────┴─────────────────┴──────┐
    │                             │
    ▼                             ▼
┌────────────────┐     ┌──────────────────┐
│ alembic.ini    │     │ alembic/versions/│
│ 配置文件        │     │ 001_initial.py   │
│ DATABASE_URL   │     │ 迁移脚本          │
└────────────────┘     └──────────────────┘
    │                             │
    └────────────┬────────────────┘
                 ▼
         ┌──────────────────┐
         │   MySQL数据库     │
         │ agri_platform    │
         │                  │
         │ users ────┐      │
         │ products  │      │
         │ conversations    │
         │ messages  │      │
         │ alembic_version  │
         └──────────────────┘
```

## 文件关系图

```
backend/
│
├── alembic.ini ─────────────────┐
│                                │
├── alembic/                      │
│   │                             │
│   ├── env.py ◄───────────┐      │
│   │   导入: ↓             │      │
│   │   - User              │      │
│   │   - Product           │      │
│   │   - Conversation      │      │
│   │   - Message           │      │
│   │                       │      │
│   ├── script.py.mako      │      │
│   │   (模板)              │      │
│   │                       │      │
│   └── versions/           │      │
│       │                   │      │
│       └── 001_initial.py ◄┤      │
│                           │      │
├── app/                         │
│   ├── models/                  │
│   │   ├── base.py              │
│   │   │   (BaseModel)           │
│   │   ├── user.py  ────────┐    │
│   │   ├── product.py        ├──┤
│   │   └── conversation.py ──┘   │
│   │                            │
│   ├── database.py              │
│   │   (engine, SessionLocal)   │
│   │                            │
│   └── core/                    │
│       └── config.py            │
│           (DATABASE_URL) ──────┴─┐
│                                  │
├── scripts/                        │
│   ├── init_db.py  ────┐          │
│   ├── seed_data.py    ├──────────┼──┐
│   └── db_migrate.py ──┘          │  │
│                                  ▼  ▼
└─────────────────────────────────────MySQL────┐
                                    Server      │
                                                ▼
                                    agri_platform
                                    Database
```

## 迁移工作流程

```
1. 修改模型
   ┌──────────────────────┐
   │ app/models/user.py   │
   │ 添加新字段            │
   └──────────┬───────────┘
              │
              ▼
2. 生成迁移脚本
   ┌──────────────────────────────────┐
   │ alembic revision --autogenerate  │
   │ -m "add field"                   │
   └──────────┬───────────────────────┘
              │
              ▼ 创建
   ┌────────────────────────────┐
   │ alembic/versions/          │
   │ 002_add_field.py           │
   │ ├── def upgrade()          │
   │ └── def downgrade()        │
   └──────────┬─────────────────┘
              │
              ▼
3. 审查迁移脚本
   ┌─────────────┐
   │ 检查SQL语法 │
   │ 验证逻辑    │
   └──────┬──────┘
          │
          ▼
4. 执行迁移
   ┌──────────────────┐
   │ alembic upgrade  │
   │ head             │
   └──────┬───────────┘
          │
          ▼
5. 更新数据库
   ┌──────────────────────┐
   │ MySQL数据库          │
   │ - 创建新列           │
   │ - 更新索引           │
   │ - 记录版本           │
   │ (alembic_version)    │
   └──────────────────────┘
```

## 初始迁移创建的表

```
┌────────────────────────────────────────────┐
│              users                         │
├────────────────┬──────────────────────────┤
│ id (PK)        │ BIGINT AUTO_INCREMENT   │
│ user_uuid (UK) │ VARCHAR(36)             │
│ username (UK)  │ VARCHAR(50)             │
│ email (UK)     │ VARCHAR(100)            │
│ phone (UK)     │ VARCHAR(20)             │
│ password_hash  │ VARCHAR(255)            │
│ user_type      │ ENUM                    │
│ status         │ ENUM                    │
│ role           │ ENUM                    │
│ enterprise_id  │ BIGINT                  │
│ ...            │ ...                     │
│ created_at     │ DATETIME                │
│ updated_at     │ DATETIME                │
│ deleted_at     │ DATETIME (NULL)         │
├────────────────┴──────────────────────────┤
│ Indexes: 9                                │
│ Keys: 8 unique, 6 regular                 │
└────────────────────────────────────────────┘

┌────────────────────────────────────────────┐
│              products                      │
├────────────────┬──────────────────────────┤
│ id (PK)        │ INTEGER AUTO_INCREMENT  │
│ sku (UK)       │ VARCHAR(50)             │
│ name           │ VARCHAR(255)            │
│ description    │ TEXT                    │
│ category       │ VARCHAR(100)            │
│ price          │ FLOAT                   │
│ cost           │ FLOAT                   │
│ stock          │ INTEGER                 │
│ region         │ VARCHAR(100)            │
│ cultural_tags  │ JSON                    │
│ ...            │ ...                     │
│ created_at     │ DATETIME                │
│ updated_at     │ DATETIME                │
├────────────────┴──────────────────────────┤
│ Indexes: 8                                │
│ Composite indexes on (category,status),   │
│ (region,status)                           │
└────────────────────────────────────────────┘

┌────────────────────────────────────────────┐
│              conversations                 │
├────────────────┬──────────────────────────┤
│ id (PK)        │ VARCHAR(36)             │
│ user_id        │ VARCHAR(36)             │
│ title          │ VARCHAR(255)            │
│ description    │ TEXT                    │
│ message_count  │ INTEGER                 │
│ total_tokens   │ INTEGER                 │
│ total_cost     │ FLOAT                   │
│ status         │ VARCHAR(20)             │
│ is_favorited   │ BOOLEAN                 │
│ created_at     │ DATETIME                │
│ updated_at     │ DATETIME                │
│ last_message_at│ DATETIME (NULL)         │
├────────────────┴──────────────────────────┤
│ Indexes: 3                                │
│ Foreign keys: 0 (实际上应该有)            │
│ Composite indexes on (user_id,created_at),│
│ (user_id,status)                          │
└────────────────────────────────────────────┘
     ▲
     │ has many
     │
┌────────────────────────────────────────────┐
│              messages                      │
├────────────────┬──────────────────────────┤
│ id (PK)        │ VARCHAR(36)             │
│ conversation_id│ VARCHAR(36) (FK)        │
│ role           │ VARCHAR(20)             │
│ content        │ TEXT                    │
│ input_tokens   │ INTEGER                 │
│ output_tokens  │ INTEGER                 │
│ total_tokens   │ INTEGER                 │
│ cost           │ FLOAT                   │
│ model          │ VARCHAR(100)            │
│ finish_reason  │ VARCHAR(50)             │
│ rating         │ INTEGER (NULL)          │
│ feedback       │ TEXT (NULL)             │
│ created_at     │ DATETIME                │
│ updated_at     │ DATETIME                │
├────────────────┴──────────────────────────┤
│ Indexes: 3                                │
│ Foreign keys: 1 (conversation_id)         │
│ Composite index on (conversation_id,role) │
└────────────────────────────────────────────┘
```

## 脚本执行流程

### init_db.py
```
启动
  │
  ├─► 检查数据库连接 ◄── DATABASE_URL
  │   ├─ 连接失败 → 退出
  │   └─ 连接成功 ↓
  │
  ├─► 显示现有表
  │
  ├─► [可选] 删除现有表 (--drop)
  │
  ├─► 创建表 (通过alembic迁移)
  │   └─► 运行 001_initial.py
  │       ├─ CREATE TABLE users
  │       ├─ CREATE TABLE products
  │       ├─ CREATE TABLE conversations
  │       └─ CREATE TABLE messages
  │
  ├─► 验证表结构
  │
  └─► [可选] 创建种子数据 (--seed)
      └─► 运行 seed_data.py
          ├─ CREATE admin user
          ├─ CREATE test users
          ├─ CREATE sample products
          └─ CREATE sample conversations
```

### db_migrate.py
```
选择命令
  │
  ├─► status
  │   ├─ alembic current (当前版本)
  │   ├─ alembic heads (最新版本)
  │   └─ alembic history (历史)
  │
  ├─► upgrade [target]
  │   └─► alembic upgrade [target]
  │       └─ 执行upgrade()函数
  │           └─ 更新数据库
  │
  ├─► downgrade [target]
  │   └─► alembic downgrade [target]
  │       └─ 执行downgrade()函数
  │           └─ 回滚数据库
  │
  └─► 其他命令...
```

## 数据类型映射

```
Python/SQLAlchemy          MySQL
─────────────────────────────────────
BIGINT(unsigned=True)  →  BIGINT UNSIGNED
Integer                →  INT
VARCHAR(50)            →  VARCHAR(50) CHARACTER SET utf8mb4
Text                   →  TEXT CHARACTER SET utf8mb4
Float                  →  FLOAT
DateTime               →  DATETIME
Enum                   →  ENUM('value1','value2')
JSON                   →  JSON
Boolean                →  BOOLEAN (TINYINT)
```

## 环境配置

```
┌──────────────────────────────────────┐
│  环境变量 / 配置文件                  │
├──────────────────────────────────────┤
│                                      │
│  DATABASE_URL=                       │
│  mysql+pymysql://user:pass@          │
│  host:port/database?charset=utf8mb4  │
│                                      │
│  DEBUG=True                          │
│  APP_NAME=...                        │
│                                      │
└──────────────────────────────────────┘
               ↓ 读取
┌──────────────────────────────────────┐
│  app/core/config.py                  │
│  Settings 类                         │
└──────────────────────────────────────┘
               ↓ 传递
┌──────────────────────────────────────┐
│  alembic/env.py                      │
│  使用 settings.DATABASE_URL          │
└──────────────────────────────────────┘
               ↓ 连接
┌──────────────────────────────────────┐
│  MySQL 数据库                        │
└──────────────────────────────────────┘
```

## 版本控制

```
alembic_version 表
┌───────────────────────────┐
│ version_num (VARCHAR(32)) │
├───────────────────────────┤
│ 001_initial               │ ◄─ 当前版本
└───────────────────────────┘

升级序列:
base → 001_initial → 002_xxx → 003_yyy → ...

每次升级:
1. 执行 upgrade() 函数
2. 更新 alembic_version 表
3. 提交事务

每次回滚:
1. 执行 downgrade() 函数
2. 更新 alembic_version 表
3. 提交事务
```

## 命令执行路径

```
用户命令
  │
  ├─► python -m scripts.init_db
  │   └─► init_db.py
  │       ├─ engine.connect() (来自 app/database.py)
  │       ├─ init_db() (创建表)
  │       └─ seed_database() (可选)
  │
  ├─► python -m scripts.db_migrate status
  │   └─► db_migrate.py
  │       └─► run_alembic_command(['current'])
  │
  ├─► alembic revision --autogenerate
  │   └─► alembic/env.py
  │       ├─ 导入models
  │       ├─ 连接数据库
  │       └─ 比较schemas
  │
  └─► alembic upgrade head
      └─► alembic/env.py
          └─ 执行 versions/001_initial.py 的 upgrade()
```

## 错误处理流程

```
执行 alembic upgrade
  │
  ├─► 连接失败 → 显示错误 → 退出
  │
  ├─► SQL执行失败
  │   ├─ 回滚事务
  │   ├─ 显示错误信息
  │   └─ 版本号不变
  │
  ├─► 成功执行
  │   ├─ 提交事务
  │   ├─ 更新版本号
  │   └─ 显示成功信息
  │
  └─► 已是最新版本
      └─ 显示"已是最新版本"提示
```

---

**完整流程说明**: 详见 `ALEMBIC_GUIDE.md`
**快速命令参考**: 详见 `MIGRATION_COMMANDS.md`
