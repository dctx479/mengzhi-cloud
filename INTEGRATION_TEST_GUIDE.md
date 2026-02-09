# 集成测试执行指南

## 目录
- [快速开始](#快速开始)
- [环境准备](#环境准备)
- [测试执行](#测试执行)
- [测试报告](#测试报告)
- [常见问题](#常见问题)

---

## 快速开始

### 一键运行所有集成测试

```bash
# 在项目根目录执行
python scripts/run_integration_tests.py
```

这将自动执行：
1. ✅ 环境和服务检查
2. ✅ 后端API集成测试
3. ✅ 端到端业务流程测试
4. ✅ 前端环境检查
5. ✅ 生成详细测试报告

---

## 环境准备

### 1. 后端环境

#### 1.1 安装依赖

```bash
cd backend
pip install -r requirements.txt
pip install -r requirements-test.txt
```

#### 1.2 配置环境变量

```bash
# 复制环境变量模板
cp .env.example .env.development

# 编辑配置文件
# 必须配置:
# - DATABASE_URL (MySQL连接)
# - REDIS_URL (Redis连接)
# - SECRET_KEY (JWT密钥)
# 可选配置:
# - DEEPSEEK_API_KEY (AI功能需要)
```

#### 1.3 启动必要服务

**MySQL 8.0+**
```bash
# 方式1: Docker
docker run -d \
  --name mysql \
  -e MYSQL_ROOT_PASSWORD=root123 \
  -e MYSQL_DATABASE=agri_platform \
  -p 3306:3306 \
  mysql:8.0

# 方式2: 本地安装
# 确保MySQL服务运行在 localhost:3306
```

**Redis 7.0+**
```bash
# 方式1: Docker
docker run -d \
  --name redis \
  -p 6379:6379 \
  redis:7

# 方式2: 本地安装
redis-server
```

#### 1.4 初始化数据库

```bash
cd backend

# 运行数据库迁移
alembic upgrade head

# (可选) 导入测试数据
python scripts/init_db.py
```

#### 1.5 启动后端服务

```bash
cd backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

验证启动成功:
```bash
curl http://localhost:8000/health
# 应返回: {"status": "healthy", ...}
```

### 2. 前端环境

#### 2.1 安装依赖

```bash
cd frontend
npm install
```

#### 2.2 配置环境变量

```bash
# 编辑 .env.development
VITE_API_BASE_URL=http://localhost:8000
VITE_APP_NAME=AI赋能云平台
```

#### 2.3 启动前端服务

```bash
cd frontend
npm run dev
```

验证启动成功:
```bash
# 浏览器访问
http://localhost:5173
```

---

## 测试执行

### 方式1: 自动化测试（推荐）

运行主测试脚本，自动执行所有测试：

```bash
python scripts/run_integration_tests.py
```

### 方式2: 手动分步测试

#### 步骤1: 环境检查

```bash
cd backend
python -m pytest tests/integration/test_environment.py -v -s
```

预期结果：
- ✅ Python版本检查通过
- ✅ 环境变量配置正确
- ✅ MySQL连接成功
- ✅ Redis连接成功
- ✅ 数据表已创建
- ✅ 上传目录可写

#### 步骤2: API集成测试

```bash
cd backend
python -m pytest tests/integration/test_api_integration.py -v -s
```

测试覆盖：
- ✅ 健康检查端点 (4个)
- ✅ 认证模块 (8个端点)
- ✅ 产品模块 (9个端点)
- ✅ AI对话模块 (6个端点)
- ✅ RBAC权限 (15个端点)

#### 步骤3: 端到端流程测试

```bash
cd backend
python -m pytest tests/integration/test_e2e_flows.py -v -s
```

测试场景：
- ✅ 新用户完整业务流程 (9步)
- ✅ 企业用户内容生成 (7步)
- ✅ 管理员管理流程 (5步)

#### 步骤4: 前端环境检查

```bash
cd frontend
npm run test -- tests/integration/environment.test.ts
```

检查项：
- ✅ 项目配置
- ✅ 依赖安装
- ✅ 目录结构
- ✅ TypeScript/Vite配置

---

## 测试报告

测试完成后，将生成以下报告文件：

### 主报告
- **`INTEGRATION_TEST_REPORT.md`** - 完整测试报告
  - 测试总结（通过率、失败数）
  - 环境和服务状态
  - 后端API测试结果
  - 前端测试结果
  - 发现的问题（按优先级）
  - 验收状态
  - 下一步行动

### 详细日志
测试执行过程中的所有输出将实时显示在终端。

---

## 常见问题

### Q1: MySQL连接失败

**错误**: `pymysql.err.OperationalError: (2003, "Can't connect to MySQL server")`

**解决方案**:
1. 确认MySQL服务正在运行
   ```bash
   # Windows
   net start MySQL80

   # Linux
   sudo systemctl start mysql

   # Docker
   docker start mysql
   ```

2. 检查连接配置
   ```bash
   # .env.development
   DATABASE_URL=mysql+pymysql://root:root123@localhost:3306/agri_platform?charset=utf8mb4
   ```

3. 测试连接
   ```bash
   mysql -h localhost -P 3306 -u root -p
   ```

### Q2: Redis连接失败

**错误**: `redis.exceptions.ConnectionError`

**解决方案**:
1. 启动Redis服务
   ```bash
   # Windows
   redis-server

   # Linux
   sudo systemctl start redis

   # Docker
   docker start redis
   ```

2. 测试连接
   ```bash
   redis-cli ping
   # 应返回: PONG
   ```

### Q3: 数据表不存在

**错误**: `sqlalchemy.exc.ProgrammingError: (pymysql.err.ProgrammingError) (1146, "Table 'agri_platform.users' doesn't exist")`

**解决方案**:
```bash
cd backend
alembic upgrade head
```

### Q4: DeepSeek API调用失败

**错误**: AI相关测试失败

**解决方案**:
1. 配置API密钥
   ```bash
   # .env.development
   DEEPSEEK_API_KEY=sk-your-actual-api-key
   ```

2. 如果暂时不测试AI功能，可以跳过相关测试
   ```bash
   pytest -k "not ai and not chat" tests/integration/
   ```

### Q5: 端口被占用

**错误**: `OSError: [Errno 48] Address already in use`

**解决方案**:
1. 查找占用进程
   ```bash
   # Windows
   netstat -ano | findstr :8000

   # Linux/Mac
   lsof -i :8000
   ```

2. 终止进程或更换端口
   ```bash
   # 更换端口
   uvicorn app.main:app --port 8001
   ```

### Q6: 前端依赖安装失败

**错误**: `npm ERR! code ERESOLVE`

**解决方案**:
```bash
cd frontend

# 清除缓存
rm -rf node_modules package-lock.json

# 重新安装
npm install --legacy-peer-deps
```

### Q7: 测试超时

**错误**: `TimeoutError: Test execution timed out`

**解决方案**:
1. 增加超时时间
   ```bash
   pytest --timeout=300 tests/integration/
   ```

2. 检查服务是否正常响应
   ```bash
   curl -X POST http://localhost:8000/api/v1/auth/login \
     -H "Content-Type: application/json" \
     -d '{"username": "test", "password": "test123"}'
   ```

---

## 性能测试（可选）

### 使用Locust进行压力测试

```bash
# 安装Locust
pip install locust

# 创建locustfile.py
# (参考 scripts/locustfile.py)

# 启动压力测试
locust -f scripts/locustfile.py --host=http://localhost:8000

# 访问Web UI
http://localhost:8089
```

### 性能指标目标

- **API响应时间**: p95 < 500ms
- **吞吐量**: > 100 req/s
- **错误率**: < 1%
- **并发用户**: 支持100+

---

## 安全测试（可选）

### 基础安全检查

```bash
# SQL注入测试
curl "http://localhost:8000/api/v1/products?category=' OR '1'='1"

# XSS测试
curl "http://localhost:8000/api/v1/products?search=<script>alert('XSS')</script>"

# 未授权访问测试
curl http://localhost:8000/api/v1/auth/me
# 应返回 401 Unauthorized
```

---

## 持续集成配置

### GitHub Actions示例

创建 `.github/workflows/integration-tests.yml`:

```yaml
name: Integration Tests

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main, develop ]

jobs:
  test:
    runs-on: ubuntu-latest

    services:
      mysql:
        image: mysql:8.0
        env:
          MYSQL_ROOT_PASSWORD: root123
          MYSQL_DATABASE: agri_platform
        ports:
          - 3306:3306

      redis:
        image: redis:7
        ports:
          - 6379:6379

    steps:
    - uses: actions/checkout@v3

    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'

    - name: Install backend dependencies
      run: |
        cd backend
        pip install -r requirements.txt
        pip install -r requirements-test.txt

    - name: Run integration tests
      run: |
        python scripts/run_integration_tests.py
      env:
        DATABASE_URL: mysql+pymysql://root:root123@localhost:3306/agri_platform
        REDIS_URL: redis://localhost:6379/0

    - name: Upload test report
      uses: actions/upload-artifact@v3
      with:
        name: integration-test-report
        path: INTEGRATION_TEST_REPORT.md
```

---

## 联系支持

如遇到其他问题：
- 📧 邮箱: b150w4942@163.com
- 📋 提交Issue: [GitHub Issues](https://github.com/your-repo/issues)

---

**最后更新**: [项目完成日期]
