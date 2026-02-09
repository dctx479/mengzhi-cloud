# 集成测试快速参考

> **一页纸快速参考** - 打印或保存以供快速查阅

---

## 🚀 快速启动（5分钟）

### 1. 启动服务

```bash
# 终端1: 启动MySQL和Redis (Docker)
docker run -d --name mysql -e MYSQL_ROOT_PASSWORD=root123 -e MYSQL_DATABASE=agri_platform -p 3306:3306 mysql:8.0
docker run -d --name redis -p 6379:6379 redis:7

# 终端2: 启动后端
cd backend
alembic upgrade head
uvicorn app.main:app --reload

# 终端3: 启动前端
cd frontend
npm run dev
```

### 2. 运行测试

```bash
# 一键运行所有测试
python scripts/run_integration_tests.py

# 或分步执行
cd backend
pytest tests/integration/test_environment.py -v
pytest tests/integration/test_api_integration.py -v
pytest tests/integration/test_e2e_flows.py -v
```

### 3. 查看报告

```bash
cat INTEGRATION_TEST_REPORT.md
```

---

## ✅ 测试前检查清单

### 环境检查
- [ ] Python 3.11+ 已安装
- [ ] Node.js 18+ 已安装
- [ ] MySQL 8.0+ 运行中（端口3306）
- [ ] Redis 7.0+ 运行中（端口6379）
- [ ] 后端依赖已安装（`pip install -r requirements.txt`）
- [ ] 前端依赖已安装（`npm install`）

### 配置检查
- [ ] `backend/.env.development` 已配置
- [ ] `frontend/.env.development` 已配置
- [ ] 数据库已初始化（`alembic upgrade head`）
- [ ] 上传目录可写（`uploads/`）

### 服务检查
- [ ] 后端健康检查通过：`curl http://localhost:8000/health`
- [ ] 前端可访问：浏览器打开 `http://localhost:5173`
- [ ] API文档可访问：`http://localhost:8000/docs`

---

## 📊 测试覆盖速查

| 模块 | 端点数 | 测试用例 | 文件 |
|------|--------|----------|------|
| 健康检查 | 4 | 4 | test_api_integration.py |
| 认证模块 | 8 | 7 | test_api_integration.py |
| 产品模块 | 9 | 7 | test_api_integration.py |
| AI对话 | 6 | 4 | test_api_integration.py |
| RBAC权限 | 15 | 3 | test_api_integration.py |
| E2E流程 | - | 3场景 | test_e2e_flows.py |
| 前端环境 | - | 11 | environment.test.ts |
| **总计** | **56+** | **49+** | **5个文件** |

---

## 🐛 常见问题速查

| 问题 | 快速解决 |
|------|----------|
| 连接MySQL失败 | `docker start mysql` 或检查DATABASE_URL |
| 连接Redis失败 | `docker start redis` 或 `redis-server` |
| 表不存在 | `cd backend && alembic upgrade head` |
| Token无效 | 重新登录获取新Token |
| AI测试失败 | 配置DEEPSEEK_API_KEY或跳过AI测试 |
| 端口被占用 | `lsof -i :8000` 找到进程并kill |
| 前端依赖错误 | `rm -rf node_modules && npm install` |
| 测试超时 | 增加timeout或检查服务响应 |

---

## 🎯 性能测试速查

```bash
# 基础测试 (100用户，10秒启动)
locust -f scripts/locustfile.py --host=http://localhost:8000 -u 100 -r 10

# 压力测试 (500用户)
locust -f scripts/locustfile.py --host=http://localhost:8000 -u 500 -r 50

# 无界面5分钟测试
locust -f scripts/locustfile.py --host=http://localhost:8000 -u 100 -r 10 --headless -t 5m --html=report.html
```

**目标指标**:
- 平均响应: < 200ms
- P95响应: < 500ms
- 吞吐量: > 100 req/s
- 错误率: < 1%

---

## 📁 文件位置速查

```
测试脚本:
├─ backend/tests/integration/test_environment.py        # 环境检查
├─ backend/tests/integration/test_api_integration.py   # API测试
├─ backend/tests/integration/test_e2e_flows.py         # E2E流程
├─ frontend/tests/integration/environment.test.ts      # 前端环境
└─ scripts/locustfile.py                               # 性能测试

执行工具:
└─ scripts/run_integration_tests.py                    # 主执行脚本

文档:
├─ INTEGRATION_TEST_GUIDE.md                           # 详细指南
├─ INTEGRATION_TEST_REPORT.md                          # 测试报告
└─ INTEGRATION_BUGS.md                                 # Bug清单
```

---

## 🔍 调试技巧

### 1. 查看后端日志
```bash
# 开发模式自动显示日志
uvicorn app.main:app --reload --log-level debug
```

### 2. 查看数据库
```bash
mysql -u root -p
use agri_platform;
show tables;
select * from users;
```

### 3. 查看Redis
```bash
redis-cli
keys *
get some_key
```

### 4. 测试单个端点
```bash
# 登录
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"test","password":"test123"}'

# 获取产品列表
curl http://localhost:8000/api/v1/products
```

### 5. Python调试
```bash
# 在测试中添加断点
import pdb; pdb.set_trace()

# 或使用pytest调试
pytest tests/integration/test_api_integration.py::TestAuthentication::test_login_success -s --pdb
```

---

## 📞 获取帮助

- 📖 详细指南: `INTEGRATION_TEST_GUIDE.md`
- 🐛 Bug清单: `INTEGRATION_BUGS.md`
- 📊 完整报告: `INTEGRATION_TEST_REPORT.md`
- 📧 邮箱: b150w4942@163.com

---

## 🎓 测试最佳实践

1. **测试前准备**
   - 确保所有服务正常运行
   - 使用干净的数据库
   - 检查环境变量配置

2. **测试执行**
   - 先运行环境检查
   - 按模块逐步测试
   - 记录失败原因

3. **测试后清理**
   - 清理测试数据
   - 关闭测试服务
   - 保存测试报告

4. **持续改进**
   - 定期运行测试
   - 更新测试用例
   - 监控性能指标
   - 修复发现的问题

---

**版本**: v1.0.0 | **更新**: [项目完成日期]
