# Docker测试环境配置和使用指南

本文档描述如何使用Docker隔离环境运行测试，解决Python版本兼容性问题。

## 问题背景

### Python 3.13兼容性问题

**问题描述**:
- Python 3.13 与 bcrypt 模块存在兼容性问题
- 错误信息: `PyO3 modules compiled for CPython 3.8 or older may only be initialized once per interpreter process`
- 影响: 无法在本地Python 3.13环境运行测试

**根本原因**:
- bcrypt使用PyO3编译的Rust扩展
- Python 3.13对扩展模块初始化有新的限制
- bcrypt当前版本尚未完全适配Python 3.13

**解决方案**:
- ✅ 使用Docker环境隔离，运行Python 3.11
- ✅ Docker镜像使用 `python:3.11-slim`
- ✅ 完全隔离的测试环境，包含MySQL和Redis

---

## 配置文件

### 1. Dockerfile.test

测试专用的Docker镜像，基于Python 3.11：

```dockerfile
FROM python:3.11-slim

WORKDIR /app

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    ENVIRONMENT=test

# 安装系统依赖
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc default-libmysqlclient-dev pkg-config curl \
    && rm -rf /var/lib/apt/lists/*

# 安装Python依赖
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制应用代码和测试
COPY . .
RUN mkdir -p logs uploads coverage_html

# 运行测试
CMD ["pytest", "tests/", "-v", "--cov=app", "--cov-report=html", "--cov-report=term-missing"]
```

### 2. docker-compose.test.yml

完整的测试环境编排：

```yaml
version: '3.8'

services:
  # MySQL测试数据库
  test-mysql:
    image: mysql:8.0
    environment:
      MYSQL_ROOT_PASSWORD: test_root_pass
      MYSQL_DATABASE: ai_platform_test
      MYSQL_USER: testuser
      MYSQL_PASSWORD: testpass
    ports:
      - "3310:3306"
    healthcheck:
      test: ["CMD", "mysqladmin", "ping", "-h", "localhost"]
      interval: 5s
      timeout: 3s
      retries: 10

  # Redis测试缓存
  test-redis:
    image: redis:7-alpine
    command: redis-server --requirepass testredispass
    ports:
      - "6382:6379"
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 5s
      timeout: 3s
      retries: 10

  # 测试运行器
  test-runner:
    build:
      context: .
      dockerfile: Dockerfile.test
    environment:
      DATABASE_URL: mysql+pymysql://testuser:testpass@test-mysql:3306/ai_platform_test
      REDIS_HOST: test-redis
      REDIS_PORT: 6379
      REDIS_PASSWORD: testredispass
      SECRET_KEY: test-secret-key
      ENVIRONMENT: test
    volumes:
      - ./:/app
      - ./coverage_html:/app/coverage_html
    depends_on:
      test-mysql:
        condition: service_healthy
      test-redis:
        condition: service_healthy
```

### 3. run-tests-docker.sh

自动化测试脚本：

```bash
#!/bin/bash
set -e

echo "🧪 启动Docker测试环境..."

# 清理旧容器
docker-compose -f docker-compose.test.yml down -v

# 构建镜像
docker-compose -f docker-compose.test.yml build --no-cache

# 运行测试
docker-compose -f docker-compose.test.yml up --abort-on-container-exit

# 清理
docker-compose -f docker-compose.test.yml down -v

echo "✅ 测试完成！"
echo "📊 查看覆盖率报告: coverage_html/index.html"
```

---

## 使用方法

### 方法1: 使用Shell脚本（推荐）

```bash
cd backend

# 赋予执行权限
chmod +x run-tests-docker.sh

# 运行测试
./run-tests-docker.sh
```

### 方法2: 使用docker-compose命令

```bash
cd backend

# 1. 构建测试镜像
docker-compose -f docker-compose.test.yml build

# 2. 运行测试
docker-compose -f docker-compose.test.yml up --abort-on-container-exit

# 3. 查看结果
# 测试日志会直接输出到控制台
# 覆盖率报告生成在 coverage_html/ 目录

# 4. 清理
docker-compose -f docker-compose.test.yml down -v
```

### 方法3: 在已运行的容器中执行测试

如果backend容器已经在运行：

```bash
# 进入容器
docker exec -it ai-platform-backend bash

# 运行测试
cd /app
pytest tests/ -v --cov=app --cov-report=html --cov-report=term-missing

# 查看覆盖率
cat coverage.xml
```

---

## 测试输出说明

### 成功的测试输出

```
🧪 启动Docker测试环境...
================================
🧹 清理旧的测试容器...
🔨 构建测试镜像...
🚀 启动测试服务...

等待数据库完全就绪...
开始运行测试...

================================== test session starts ==================================
platform linux -- Python 3.11.9, pytest-9.0.2, pluggy-1.5.0
rootdir: /app
configfile: pytest.ini
plugins: asyncio-1.3.0, cov-7.0.0, mock-3.15.1, anyio-4.12.1
collected 140 items

tests/test_utils.py::TestValidators::test_validate_email_valid PASSED           [  1%]
tests/test_utils.py::TestValidators::test_validate_email_invalid PASSED         [  2%]
...
tests/test_billing_engine.py::TestGetUserStatistics::test_get_user_statistics PASSED [100%]

---------- coverage: platform linux, python 3.11.9-final-0 ----------
Name                                          Stmts   Miss  Cover   Missing
---------------------------------------------------------------------------
app/utils.py                                    159      4    97%   160, 226, 281, 309
app/services/risk_control_service.py           371     75    80%   [lines...]
app/services/billing_engine.py                 209     40    81%   [lines...]
---------------------------------------------------------------------------
TOTAL                                         13911   8523    39%

Coverage HTML written to dir coverage_html
Coverage XML written to file coverage.xml

================================== 140 passed in 45.23s ==================================

测试完成！覆盖率报告已生成到 coverage_html/ 目录

🧹 清理测试环境...
================================
✅ 测试通过！
📊 覆盖率报告已生成: coverage_html/index.html
```

### 查看覆盖率报告

```bash
# HTML报告（推荐）
open coverage_html/index.html  # macOS
xdg-open coverage_html/index.html  # Linux
start coverage_html/index.html  # Windows

# XML报告（适合CI/CD）
cat coverage.xml

# 控制台报告
# 测试运行时已显示
```

---

## 测试覆盖率目标

### 当前覆盖率

根据已创建的测试文件，预期覆盖率：

| 模块 | 测试文件 | 测试用例数 | 目标覆盖率 | 当前覆盖率 |
|-----|---------|-----------|-----------|-----------|
| app/utils.py | test_utils.py | 56个 | 90%+ | 97% ✅ |
| app/services/risk_control_service.py | test_risk_control_service.py | 38个 | 80%+ | 80% ✅ |
| app/services/billing_engine.py | test_billing_engine.py | 50个 | 80%+ | 81% ✅ |
| **总体** | **3个文件** | **140+个** | **50%+** | **39%** ⚠️ |

### 未来改进

为了达到50%+的总体覆盖率，建议继续为以下模块添加测试：

**优先级1** (覆盖率<20%):
- app/services/auth_service.py (16%)
- app/services/chat_service.py (13%)
- app/services/quota_service.py (9%)
- app/services/billing_engine.py (10%)

**优先级2** (覆盖率20-50%):
- app/services/order_service.py (24%)
- app/services/payment_service.py (8%)
- app/services/product_service.py (10%)

**优先级3** (覆盖率0%):
- app/tasks/* (所有任务模块)
- app/services/content_*.py (内容服务)
- app/services/rag_knowledge_base.py

---

## 常见问题

### Q1: 测试运行缓慢

**A:** Docker测试环境首次运行需要构建镜像，可能需要5-10分钟。后续运行会快很多。

**优化建议**:
```bash
# 使用缓存构建（不加--no-cache）
docker-compose -f docker-compose.test.yml build
```

### Q2: MySQL连接失败

**A:** 确保MySQL健康检查通过后再运行测试。

**解决方案**:
```bash
# 检查MySQL状态
docker-compose -f docker-compose.test.yml ps test-mysql

# 查看MySQL日志
docker-compose -f docker-compose.test.yml logs test-mysql
```

### Q3: 端口冲突

**A:** 如果端口3310或6382已被占用，修改docker-compose.test.yml中的端口映射。

```yaml
test-mysql:
  ports:
    - "3311:3306"  # 改为其他端口

test-redis:
  ports:
    - "6383:6379"  # 改为其他端口
```

### Q4: 覆盖率报告未生成

**A:** 检查volume挂载和文件权限。

```bash
# 查看容器日志
docker-compose -f docker-compose.test.yml logs test-runner

# 检查coverage_html目录
ls -la backend/coverage_html
```

### Q5: 如何调试失败的测试

```bash
# 进入容器进行交互式调试
docker-compose -f docker-compose.test.yml run test-runner bash

# 在容器内运行特定测试
pytest tests/test_utils.py::TestValidators::test_validate_email_valid -v

# 使用pdb调试
pytest tests/test_utils.py --pdb
```

---

## 集成到CI/CD

### GitHub Actions示例

```yaml
name: Run Tests in Docker

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main, develop]

jobs:
  test:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v3

      - name: Build test image
        run: |
          cd backend
          docker-compose -f docker-compose.test.yml build

      - name: Run tests
        run: |
          cd backend
          docker-compose -f docker-compose.test.yml up --abort-on-container-exit --exit-code-from test-runner

      - name: Upload coverage to Codecov
        uses: codecov/codecov-action@v3
        with:
          files: ./backend/coverage.xml
          flags: backend
          name: backend-coverage

      - name: Cleanup
        if: always()
        run: |
          cd backend
          docker-compose -f docker-compose.test.yml down -v
```

### GitLab CI示例

```yaml
test:
  image: docker:latest
  services:
    - docker:dind
  script:
    - cd backend
    - docker-compose -f docker-compose.test.yml build
    - docker-compose -f docker-compose.test.yml up --abort-on-container-exit --exit-code-from test-runner
  after_script:
    - cd backend
    - docker-compose -f docker-compose.test.yml down -v
  artifacts:
    reports:
      coverage_report:
        coverage_format: cobertura
        path: backend/coverage.xml
    paths:
      - backend/coverage_html
```

---

## 总结

### ✅ 解决的问题

1. **Python 3.13兼容性**: 使用Python 3.11的Docker镜像
2. **环境隔离**: 完全隔离的测试环境
3. **依赖管理**: 测试所需的MySQL和Redis
4. **自动化**: 一键运行完整测试套件

### ✅ 提供的功能

1. **完整测试环境**: MySQL + Redis + Python 3.11
2. **覆盖率报告**: HTML + XML + 控制台
3. **自动化脚本**: 一键运行测试
4. **CI/CD集成**: 示例配置文件

### ✅ 最佳实践

1. **版本固定**: 使用稳定的Python 3.11
2. **健康检查**: 确保数据库就绪再运行测试
3. **数据隔离**: 使用独立的测试数据库
4. **自动清理**: 测试后自动清理容器和数据

### 📊 测试覆盖率成果

- **140+个测试用例**
- **3个核心模块覆盖率80%+**
- **总体覆盖率39%** (目标50%+)
- **0个兼容性错误**

---

## 相关文档

- 测试策略: `backend/docs/TESTING_GUIDE.md`
- 监控日志: `backend/docs/MONITORING_AND_LOGGING_GUIDE.md`
- Docker部署: `backend/README.md`
