# 测试环境配置指南

**项目**: 内蒙古农畜产品品牌营销AI赋能云平台
**更新时间**: [项目完成日期]

---

## 📊 测试环境概览

本项目支持**三种测试环境**，满足不同测试场景需求：

| 环境类型 | 数据库 | 缓存 | 外部API | Docker需求 | 使用场景 |
|---------|-------|------|---------|-----------|----------|
| **单元测试** | SQLite内存 | fakeredis | Mock | ❌ 不需要 | 快速验证逻辑 |
| **集成测试** | MySQL Docker | Redis Docker | Mock | ✅ 需要 | 验证模块协作 |
| **手动测试** | MySQL Docker | Redis Docker | 真实API | ✅ 需要 | 完整功能验证 |

---

## 🚀 方式1: 单元测试（推荐，无需Docker）

### 适用场景
- ✅ 日常开发中的快速测试
- ✅ CI/CD流水线
- ✅ 验证业务逻辑
- ✅ 覆盖率报告生成

### 环境准备
```bash
cd backend
pip install -r requirements-test.txt
```

### 运行测试
```bash
# 方法1: Makefile（推荐）
make test              # 运行所有测试
make coverage          # 查看覆盖率报告

# 方法2: 直接Pytest
pytest tests/ -v
pytest --cov=app --cov-report=html

# 按模块运行
pytest -m auth         # 只运行认证测试
pytest -m products     # 只运行产品测试
```

### Mock依赖说明

**SQLite内存数据库**（`conftest.py:32`）:
```python
SQLALCHEMY_TEST_DATABASE_URL = "sqlite:///:memory:"
```
- 测试启动时自动创建
- 测试结束后自动销毁
- 每个测试独立事务

**fakeredis**:
```python
from fakeredis import FakeRedis
redis_client = FakeRedis()
```
- 完全模拟Redis命令
- 无需真实Redis服务

**DeepSeek AI Mock**:
```python
@patch('app.services.ai_service.DeepSeekAPI')
def test_chat(mock_deepseek):
    mock_deepseek.return_value.chat.return_value = "模拟回复"
```

### 优点
- ⚡ **速度快**: 内存数据库，秒级完成
- 🔧 **零配置**: 无需安装MySQL/Redis
- 🔄 **完全隔离**: 每个测试独立环境
- 💰 **低成本**: 无需外部API调用
- ☁️ **CI友好**: 适合GitHub Actions

### 当前状态
✅ 已完成 - Agent 9ddaa6a2已生成155+测试用例

---

## 🐳 方式2: 集成测试（需要Docker）

### 适用场景
- ✅ 验证真实数据库交互
- ✅ 测试Redis缓存逻辑
- ✅ 端到端业务流程测试
- ⚠️ 发布前的完整验证

### 环境准备

**步骤1: 启动Docker服务**
```bash
cd deploy/docker
docker-compose up -d
```

验证服务:
```bash
docker-compose ps

# 应该看到:
# agri-mysql   ... Up   0.0.0.0:3306->3306/tcp
# agri-redis   ... Up   0.0.0.0:6379->6379/tcp
```

**步骤2: 配置环境变量**
```bash
cd backend
cp .env.example .env.test
```

编辑 `.env.test`:
```ini
# 数据库配置（指向Docker）
DATABASE_URL=mysql+pymysql://root:root123@localhost:3306/agri_platform_test
REDIS_URL=redis://localhost:6379/1

# DeepSeek API（仍使用Mock或配置真实Key）
DEEPSEEK_API_KEY=your_test_key_or_mock
```

**步骤3: 初始化测试数据库**
```bash
# 创建测试数据库
docker exec -it agri-mysql mysql -uroot -proot123 -e "CREATE DATABASE IF NOT EXISTS agri_platform_test;"

# 运行迁移
export ENV_FILE=.env.test
alembic upgrade head

# 导入种子数据
python scripts/seed_data.py --env test
```

### 运行集成测试

```bash
# 设置环境变量
export ENV_FILE=.env.test
export TEST_MODE=integration

# 运行集成测试（需标记为@pytest.mark.integration）
pytest tests/ -m integration -v

# 完整测试套件（单元+集成）
pytest tests/ -v --cov=app
```

### 清理环境
```bash
# 测试完成后
docker-compose down        # 停止容器（保留数据）
docker-compose down -v     # 停止并删除数据卷
```

### 优点
- 🎯 **真实性**: 使用真实MySQL/Redis
- 🔍 **发现Bug**: 检测ORM、事务、缓存问题
- 📊 **性能测试**: 真实数据库性能
- 🚀 **生产模拟**: 接近生产环境

### 当前状态
⏸️ 待开发 - 计划在Week 1完成后添加

---

## 🖐️ 方式3: 手动测试（需要Docker + 完整环境）

### 适用场景
- 🎨 前端开发联调
- 🔧 Bug复现和调试
- 👤 用户验收测试（UAT）
- 📱 端到端流程验证

### 环境准备

**步骤1: 启动完整环境**
```bash
# 启动数据库和缓存
cd deploy/docker
docker-compose up -d

# 启动后端服务
cd ../../backend
uvicorn app.main:app --reload --port 8000

# 启动前端服务（新终端）
cd ../frontend
npm run dev
```

**步骤2: 配置真实API Key**
```bash
# backend/.env
DEEPSEEK_API_KEY=your_real_api_key
REDIS_URL=redis://localhost:6379/0
DATABASE_URL=mysql+pymysql://root:root123@localhost:3306/agri_platform
```

**步骤3: 导入测试数据**
```bash
cd backend
python scripts/seed_data.py
```

### 访问应用
- 🌐 前端: http://localhost:5173
- 🔌 后端API: http://localhost:8000
- 📚 API文档: http://localhost:8000/docs

### 测试账号
参考 `docs/testing/test-data.md`:
```
管理员: admin@test.com / Admin123!
企业用户: enterprise@test.com / Enterprise123!
普通用户: user1@test.com / User123!
```

### 优点
- 👁️ **可视化**: 浏览器中查看效果
- 🐛 **调试**: 使用浏览器开发工具
- 📸 **截图**: 生成测试报告
- 🎭 **演示**: 向团队展示功能

---

## 🎯 推荐测试流程

### 日常开发（不使用Docker）
```bash
1. 编写代码
2. 运行单元测试: make test
3. 检查覆盖率: make coverage
4. 提交代码
```

### 功能开发完成（使用Docker）
```bash
1. 启动Docker: docker-compose up -d
2. 运行集成测试: pytest -m integration
3. 手动验证: 启动前后端，浏览器测试
4. 停止Docker: docker-compose down
```

### 发布前验证（完整流程）
```bash
1. 运行所有测试: pytest tests/ -v
2. 检查覆盖率: ≥70%
3. QA审查: 运行qa-reviewer agent
4. 修复P0/P1缺陷
5. 重新测试
6. 打包发布
```

---

## 📊 Docker服务说明

### MySQL配置
```yaml
端口: 3306
用户: root
密码: root123
数据库: agri_platform
字符集: utf8mb4
时区: Asia/Shanghai
```

### Redis配置
```yaml
端口: 6379
持久化: AOF
数据目录: redis_data volume
```

### 数据卷
```
mysql_data - MySQL数据持久化
redis_data - Redis数据持久化
```

### 网络
```
agri-network - 桥接网络
```

---

## 🔧 故障排查

### 问题1: pytest找不到模块
```bash
# 确保安装了测试依赖
pip install -r requirements-test.txt

# 确保在backend目录
cd backend
pytest tests/
```

### 问题2: Docker容器无法启动
```bash
# 检查端口占用
netstat -ano | findstr "3306"
netstat -ano | findstr "6379"

# 修改docker-compose.yml端口映射
ports:
  - "13306:3306"  # 使用其他端口
```

### 问题3: 测试覆盖率不足
```bash
# 查看未覆盖代码
pytest --cov=app --cov-report=html
open coverage_html/index.html  # 查看详细报告
```

### 问题4: 集成测试失败
```bash
# 检查Docker服务状态
docker-compose ps
docker-compose logs mysql
docker-compose logs redis

# 重新初始化数据库
docker-compose down -v
docker-compose up -d
alembic upgrade head
```

---

## 📝 快速参考

### 单元测试命令
```bash
make test              # 运行所有测试
make coverage          # 查看覆盖率
pytest -m auth         # 认证模块
pytest -m products     # 产品模块
pytest -k "test_login" # 特定测试
```

### Docker命令
```bash
docker-compose up -d           # 启动服务
docker-compose down            # 停止服务
docker-compose logs -f mysql   # 查看MySQL日志
docker-compose restart redis   # 重启Redis
```

### 数据库命令
```bash
# 进入MySQL容器
docker exec -it agri-mysql mysql -uroot -proot123

# 执行SQL
docker exec -it agri-mysql mysql -uroot -proot123 agri_platform -e "SELECT * FROM users;"

# 备份数据库
docker exec agri-mysql mysqldump -uroot -proot123 agri_platform > backup.sql
```

---

## ✅ 验收清单

### 单元测试环境
- [ ] 安装测试依赖 `pip install -r requirements-test.txt`
- [ ] 运行测试通过 `make test`
- [ ] 覆盖率≥70% `make coverage`
- [ ] 所有fixtures工作正常

### Docker环境
- [ ] Docker和Docker Compose已安装
- [ ] `docker-compose up -d` 成功启动
- [ ] MySQL可连接（端口3306）
- [ ] Redis可连接（端口6379）
- [ ] 数据库迁移成功 `alembic upgrade head`

### 集成测试环境
- [ ] `.env.test`配置正确
- [ ] 测试数据库创建成功
- [ ] 种子数据导入成功
- [ ] 集成测试通过 `pytest -m integration`

---

## 🎓 总结

**推荐使用方式**:
1. **日常开发**: 单元测试（无Docker） - 快速反馈
2. **功能完成**: 集成测试（Docker） - 全面验证
3. **发布前**: 手动测试（Docker + 前端） - 最终确认

**当前项目状态**:
- ✅ 单元测试环境已完成（155+用例）
- ⏸️ Docker环境已配置但未测试
- ⏸️ 集成测试待开发

---

**文档维护**: 测试环境配置
**最后更新**: [项目完成日期]
**下次审查**: Week 1完成后
