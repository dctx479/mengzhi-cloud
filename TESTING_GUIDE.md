# 业务流程测试指南

## 概述

本文档提供完整的业务流程自动化测试指南，包括测试环境准备、测试执行、结果分析等。

## 测试覆盖范围

### 1. 用户注册和登录
- 个人用户注册
- 企业用户注册
- 多种方式登录（用户名/邮箱/手机号）
- Token生成和验证
- 用户信息管理

### 2. 企业AI配置
- 添加DeepSeek配置
- 查询配置列表
- 更新配置
- 删除配置
- 测试连接

### 3. AI对话功能
- 创建对话
- 发送消息
- 查询对话历史
- 消息列表管理

### 4. 配额使用和统计
- 查询用户配额
- 配额使用记录
- 配额统计信息
- 预警机制

### 5. 审计日志记录
- 查询审计日志
- 多维度筛选
- 统计分析
- 日志导出

### 6. 管理员功能
- 用户管理
- 企业管理
- 系统统计
- 权限控制

## 环境准备

### 1. 启动后端服务

```bash
cd backend

# 安装依赖
pip install -r requirements.txt

# 配置环境变量
cp .env.example .env
# 编辑 .env 文件，配置数据库和Redis

# 数据库迁移
alembic upgrade head

# 启动服务
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 2. 启动数据库和Redis

```bash
# 使用Docker Compose
docker-compose -f docker-compose.dev.yml up -d mysql redis

# 或手动启动
# MySQL: 端口3306
# Redis: 端口6379
```

### 3. 验证服务

```bash
# 检查后端服务
curl http://localhost:8000/

# 检查API文档
# 访问: http://localhost:8000/docs
```

## 执行测试

### 方式1: 使用测试脚本（推荐）

```bash
# 在项目根目录执行
./run_business_tests.sh
```

### 方式2: 使用pytest

```bash
cd backend

# 运行E2E测试
python -m pytest tests/e2e/test_complete_flow.py -v -s --asyncio-mode=auto

# 运行所有测试
python -m pytest tests/ -v

# 生成覆盖率报告
python -m pytest tests/ -v --cov=app --cov-report=html
```

### 方式3: 运行单个测试

```bash
cd backend

# 运行特定测试
python -m pytest tests/e2e/test_complete_flow.py::TestBusinessFlow::test_01_registration_login -v -s
```

## 测试输出

### 控制台输出示例

```
================================================================================
测试1: 用户注册和登录
================================================================================

[1.1] 个人用户注册
✓ 注册成功: test_1737543210

[1.2] 用户登录
✓ 登录成功

[1.3] 获取用户信息
✓ 用户信息: test_1737543210

✅ 测试1完成
```

### 测试报告

测试完成后会生成以下报告：

1. **TEST_REPORT.md**: 测试执行报告
   - 测试概要
   - 测试详情
   - 通过率统计

2. **htmlcov/index.html**: 代码覆盖率报告（如果使用--cov参数）
   - 文件覆盖率
   - 行覆盖率
   - 分支覆盖率

## 测试结果分析

### 成功标准

- ✅ 所有核心功能测试通过
- ✅ 通过率 ≥ 90%
- ✅ 无P0/P1级别错误

### 失败处理

如果测试失败，检查以下内容：

1. **服务状态**
   ```bash
   # 检查后端服务
   curl http://localhost:8000/
   
   # 检查数据库连接
   mysql -h localhost -u root -p
   
   # 检查Redis连接
   redis-cli ping
   ```

2. **日志查看**
   ```bash
   # 后端日志
   tail -f backend/logs/app.log
   
   # 测试日志
   # 在pytest输出中查看详细错误信息
   ```

3. **常见问题**
   - 数据库连接失败: 检查.env配置
   - Redis连接失败: 确保Redis服务运行
   - 端口占用: 更改服务端口
   - 权限不足: 检查数据库用户权限

## 测试数据清理

测试会创建临时数据，建议定期清理：

```bash
# 清理测试用户（可选）
# 测试用户名格式: test_*, ent_*, chat_*, quota_*

# 使用SQL清理
mysql -u root -p << EOF
USE agri_ai_platform;
DELETE FROM users WHERE username LIKE 'test_%' OR username LIKE 'ent_%' OR username LIKE 'chat_%' OR username LIKE 'quota_%';
DELETE FROM enterprises WHERE name LIKE '测试企业_%' OR name LIKE '企业%' OR name LIKE 'AI企业_%';
