# Alembic 快速命令参考

## 初始化和设置

```bash
# 初始化数据库（创建所有表）
python -m scripts.init_db

# 初始化并创建种子数据
python -m scripts.init_db --seed

# 删除现有表后重建
python -m scripts.init_db --drop --seed

# 显示详细信息
python -m scripts.init_db --verbose
```

## 查看状态

```bash
# 完整状态报告
python -m scripts.db_migrate status

# 查看当前版本
python -m scripts.db_migrate current

# 查看最新版本
python -m scripts.db_migrate heads

# 查看迁移历史
python -m scripts.db_migrate history

# 查看分支信息
python -m scripts.db_migrate branches
```

## 创建迁移

```bash
# 修改模型后，自动生成迁移
alembic revision --autogenerate -m "add new column"

# 手动创建空迁移
alembic revision -m "manual migration"
```

## 执行迁移

```bash
# 升级到最新版本
alembic upgrade head

# 升级N个版本
alembic upgrade +2

# 升级到指定版本
alembic upgrade 001_initial

# 查看升级SQL（不执行）
alembic upgrade head --sql
```

## 回滚迁移

```bash
# 回滚一个版本
alembic downgrade -1

# 回滚N个版本
alembic downgrade -2

# 回滚到指定版本
alembic downgrade 001_initial

# 回滚所有（返回初始状态）
alembic downgrade base

# 查看回滚SQL（不执行）
alembic downgrade -1 --sql
```

## 种子数据管理

```bash
# 创建默认种子数据
python -m scripts.seed_data

# 创建指定数量数据
python -m scripts.seed_data --users 10 --products 20

# 清空所有数据后重建
python -m scripts.seed_data --clear --users 5 --products 10
```

## 完整工作流程

### 开发新功能

```bash
# 1. 修改模型
#    编辑 app/models/user.py 等

# 2. 生成迁移
alembic revision --autogenerate -m "add user role field"

# 3. 审查迁移脚本
cat alembic/versions/*_add_user_role_field.py

# 4. 测试升级
alembic upgrade head

# 5. 测试回滚
alembic downgrade -1

# 6. 再升级
alembic upgrade head

# 7. 验证
python -m scripts.db_migrate status
```

### 部署到生产

```bash
# 1. 备份数据库
mysqldump -u root -p agri_platform > backup.sql

# 2. 检查待执行的迁移
alembic current
alembic heads

# 3. 执行迁移
alembic upgrade head

# 4. 验证
python -m scripts.db_migrate status

# 5. 如需回滚（出现问题）
alembic downgrade -1
# 恢复备份
mysql -u root -p agri_platform < backup.sql
```

## 调试命令

```bash
# 显示环境信息
alembic current
alembic heads
alembic branches

# 显示迁移历史（详细）
alembic history --verbose

# 显示迁移历史（一行）
alembic history --oneline

# 离线模式生成SQL
alembic upgrade head --sql
alembic downgrade -1 --sql

# 验证分支一致性
alembic branches

# 检查依赖关系
alembic heads
```

## 常见组合

```bash
# 从零开始
python -m scripts.init_db --drop --seed

# 更新到最新
alembic upgrade head

# 看看改了什么
alembic history

# 完整检查
alembic current && alembic heads

# 安全回滚
alembic downgrade -1 && alembic upgrade head
```

## 环境变量

```bash
# 设置数据库URL
export DATABASE_URL=mysql+pymysql://root:password@localhost:3306/agri_platform?charset=utf8mb4

# 显示当前设置
echo $DATABASE_URL

# 验证连接
python -c "from app.database import engine; print('Connected!' if engine.connect() else 'Failed')"
```

## 故障排除命令

```bash
# 检查数据库连接
python -c "
from app.database import engine
try:
    conn = engine.connect()
    print('✓ 数据库连接成功')
    conn.close()
except Exception as e:
    print(f'✗ 连接失败: {e}')
"

# 检查表
mysql -u root -p agri_platform -e "SHOW TABLES;"

# 检查迁移记录
mysql -u root -p agri_platform -e "SELECT * FROM alembic_version;"

# 检查表结构
mysql -u root -p agri_platform -e "DESCRIBE users;"

# 查看所有索引
mysql -u root -p agri_platform -e "SHOW INDEXES FROM users;"
```

## 性能优化命令

```bash
# 生成所有索引的创建语句
alembic revision --autogenerate -m "optimize indexes"

# 查看数据库大小
mysql -u root -p -e "SELECT table_name, ROUND(((data_length + index_length) / 1024 / 1024), 2) AS size_mb FROM information_schema.TABLES WHERE table_schema = 'agri_platform' ORDER BY size_mb DESC;"

# 清理碎片
mysql -u root -p agri_platform -e "OPTIMIZE TABLE users, products, conversations, messages;"
```

## 配置更新

```bash
# 检查配置
grep -r "DATABASE_URL" app/core/config.py

# 验证alembic.ini
grep "sqlalchemy.url" alembic.ini

# 查看当前的迁移环境配置
head -50 alembic/env.py
```

## 有用的别名（添加到 .bashrc 或 .zshrc）

```bash
alias amig-status="python -m scripts.db_migrate status"
alias amig-history="python -m scripts.db_migrate history"
alias amig-up="alembic upgrade head"
alias amig-down="alembic downgrade -1"
alias amig-init="python -m scripts.init_db --seed"
alias amig-seed="python -m scripts.seed_data"
```

## 更多信息

详见 `ALEMBIC_GUIDE.md` 完整文档。
