# 测试文档索引

**项目**: 内蒙古农畜产品品牌营销AI赋能云平台
**版本**: v1.0.0
**最后更新**: [项目完成日期]

---

## 文档概览

本目录包含项目的完整测试文档，覆盖单元测试、接口测试、集成测试、性能测试和安全测试。

---

## 核心文档

### 1. [测试计划](./test-plan.md)
**文件**: `test-plan.md`
**内容**:
- 测试概述和目标
- 测试环境配置
- 测试数据准备
- 测试工具和框架
- 测试执行计划
- 缺陷管理流程
- 测试报告模板

**适用人群**: 项目经理、QA负责人、测试团队

---

### 2. [API测试用例](./test-cases.md)
**文件**: `test-cases.md`
**内容**:
- 认证API测试用例（45个）
- 产品API测试用例（36个）
- AI对话API测试用例（27个）
- 共计108个详细测试用例

**覆盖**:
- 23个API端点100%覆盖
- 正常流程和异常流程
- 边界值和特殊场景

**适用人群**: QA测试工程师、后端开发人员

---

### 3. [前端测试用例](./frontend-test-cases.md)
**文件**: `frontend-test-cases.md`
**内容**:
- 页面级测试用例（6个页面）
- 组件级测试用例（5个核心组件）
- 路由测试用例
- 状态管理测试用例
- API集成测试用例

**测试框架**: Vitest + React Testing Library

**适用人群**: 前端开发人员、QA工程师

---

### 4. [集成测试用例](./integration-test-cases.md)
**文件**: `integration-test-cases.md`
**内容**:
- 用户业务流程测试（3个流程）
- AI对话业务流程测试（3个流程）
- 管理员业务流程测试（2个流程）
- 跨模块集成测试（3个场景）

**特点**: 端到端业务流程验证

**适用人群**: QA团队、产品经理

---

### 5. [性能测试计划](./performance-test-plan.md)
**文件**: `performance-test-plan.md`
**内容**:
- 性能测试目标和指标
- 接口性能测试（10个关键接口）
- 并发压力测试（3个场景）
- 数据库性能测试
- 前端性能测试

**工具**: Locust、JMeter、Lighthouse

**适用人群**: 性能测试工程师、运维团队

---

### 6. [安全测试清单](./security-test-checklist.md)
**文件**: `security-test-checklist.md`
**内容**:
- 认证和授权安全（8项）
- 注入攻击防护（3项）
- XSS和CSRF防护（3项）
- 敏感数据保护（4项）
- API安全（5项）
- 会话管理安全（2项）
- 文件上传安全（2项）
- 安全配置检查（4项）

**共计31项安全检查**

**适用人群**: 安全团队、QA工程师

---

### 7. [测试数据准备](./test-data.md)
**文件**: `test-data.md`
**内容**:
- 用户测试数据（10个账号）
- 产品测试数据（30个产品）
- AI对话测试数据（20个对话）
- 数据加载脚本
- 数据清理脚本

**脚本位置**: `backend/scripts/`

**适用人群**: 测试团队、开发人员

---

## 文档结构

```
docs/testing/
├── README.md                      # 本文件（文档索引）
├── test-plan.md                   # 测试计划
├── test-cases.md                  # API测试用例
├── frontend-test-cases.md         # 前端测试用例
├── integration-test-cases.md      # 集成测试用例
├── performance-test-plan.md       # 性能测试计划
├── security-test-checklist.md     # 安全测试清单
├── test-data.md                   # 测试数据准备
└── reports/                       # 测试报告目录（运行时生成）
    ├── daily/                     # 日报
    ├── weekly/                    # 周报
    └── summary/                   # 总结报告
```

---

## 快速开始

### 1. 环境准备

#### 后端环境
```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

#### 前端环境
```bash
cd frontend
npm install
```

#### 数据库准备
```bash
mysql -u root -p
CREATE DATABASE ai_platform_test CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

---

### 2. 加载测试数据

```bash
# 方式1: Python脚本
python backend/scripts/seed_data.py

# 方式2: SQL脚本
mysql -u root -p ai_platform_test < backend/scripts/seed_data.sql

# 方式3: 一键脚本
./backend/scripts/setup_test_data.sh
```

---

### 3. 运行测试

#### 后端API测试
```bash
cd backend

# 运行所有测试
pytest tests/ -v

# 运行认证测试
pytest tests/test_auth.py -v

# 生成覆盖率报告
pytest --cov=app --cov-report=html
```

#### 前端测试
```bash
cd frontend

# 运行所有测试
npm run test

# 运行UI模式
npm run test:ui

# 生成覆盖率报告
npm run test:coverage
```

#### 集成测试
```bash
# 确保后端和前端都在运行
# 运行集成测试脚本
python backend/tests/integration/test_user_flow.py
```

#### 性能测试
```bash
# 使用Locust
cd backend/tests/performance
locust -f locustfile.py --host=http://localhost:8000

# 访问Web UI
open http://localhost:8089
```

#### 安全测试
```bash
# 使用OWASP ZAP（需先安装）
# 或手动执行安全测试清单中的检查项
```

---

## 测试指标

### 覆盖率目标

| 指标 | 目标 | 当前 |
|------|------|------|
| API测试覆盖率 | 100% | ___ |
| 单元测试覆盖率 | ≥70% | ___ |
| 集成测试覆盖 | 核心流程 | ___ |
| 前端组件覆盖率 | ≥80% | ___ |

### 质量门禁

发布前必须满足:
- [ ] API测试覆盖率100%
- [ ] 单元测试覆盖率≥70%
- [ ] 无P0级别缺陷
- [ ] P1级别缺陷≤2个
- [ ] 核心业务流程集成测试通过
- [ ] 关键接口性能达标
- [ ] 安全测试无高危漏洞

---

## 测试执行时间表

### 阶段1: 单元测试（3天）
- Day 1: 后端服务层单元测试
- Day 2: 前端组件单元测试
- Day 3: 数据库模型单元测试

### 阶段2: API接口测试（4天）
- Day 4: 认证API测试
- Day 5: 产品API测试
- Day 6: AI对话API测试
- Day 7: API测试汇总

### 阶段3: 集成测试（2天）
- Day 8: 用户业务流程
- Day 9: AI对话流程

### 阶段4: 性能测试（2天）
- Day 10: 接口性能测试
- Day 11: 并发压力测试

### 阶段5: 安全测试（2天）
- Day 12: 自动化安全扫描
- Day 13: 手动安全测试

### 阶段6: 回归测试（1天）
- Day 14: 全量回归测试

**总计**: 14个工作日

---

## 缺陷管理

### 缺陷分级

- **P0（严重）**: 阻塞核心功能，必须立即修复
- **P1（重要）**: 影响主要功能，优先修复
- **P2（一般）**: 次要问题，正常修复
- **P3（轻微）**: 建议改进，可延后

### 缺陷跟踪

缺陷列表位置: `docs/testing/reports/bug-list.md`

---

## 测试报告

### 报告类型

1. **日报**: 每日测试进度和发现的问题
2. **周报**: 本周测试总结和统计
3. **测试总结报告**: 测试阶段结束的完整报告

### 报告模板

参见: `test-plan.md` 第7章

---

## 常见问题

### Q: 如何重置测试数据？

A:
```bash
python backend/scripts/clear_test_data.py
python backend/scripts/seed_data.py
```

---

### Q: 测试失败如何调试？

A:
1. 检查测试日志
2. 使用`-s`参数查看print输出: `pytest tests/test_auth.py -s`
3. 使用debugger: `pytest tests/test_auth.py --pdb`
4. 查看数据库状态

---

### Q: 如何生成测试覆盖率报告？

A:
```bash
# 后端
pytest --cov=app --cov-report=html
open htmlcov/index.html

# 前端
npm run test:coverage
open coverage/index.html
```

---

### Q: 性能测试建议的并发数是多少？

A:
- 接口测试: 50-100并发
- 压力测试: 100-200并发
- 极限测试: 递增至系统崩溃

---

### Q: 如何执行单个测试用例？

A:
```bash
# pytest
pytest tests/test_auth.py::TestRegister::test_register_personal_user_success -v

# vitest
npm run test -- --testNamePattern="renders login form"
```

---

## 相关资源

### 内部文档
- [API文档](../api/api-index.md)
- [数据库设计](../database/schema.md)
- [项目架构](../architecture/system-design.md)

### 测试工具文档
- [Pytest文档](https://docs.pytest.org/)
- [Vitest文档](https://vitest.dev/)
- [Locust文档](https://docs.locust.io/)
- [OWASP ZAP指南](https://www.zaproxy.org/docs/)

### 最佳实践
- [测试驱动开发(TDD)](https://testdriven.io/)
- [行为驱动开发(BDD)](https://cucumber.io/docs/bdd/)
- [API测试最佳实践](https://www.postman.com/api-testing/)

---

## 联系方式

### 测试团队

- **QA负责人**: [姓名]
- **邮箱**: qa@example.com
- **缺陷报告**: bug-report@example.com

### 技术支持

遇到问题请：
1. 查看相关测试文档
2. 检查FAQ部分
3. 联系测试团队

---

## 变更日志

### v1.0.0 ([项目完成日期])
- 初始版本发布
- 完成测试计划
- 完成108个API测试用例
- 完成前端测试用例
- 完成集成测试用例
- 完成性能测试计划
- 完成安全测试清单
- 完成测试数据准备

---

## 附录

### A. 测试用例编号规则

```
TC-{模块}-{类型}-{序号}

模块:
- AUTH: 认证
- PRODUCT: 产品
- CHAT: AI对话
- FE: 前端
- INT: 集成
- PERF: 性能
- SEC: 安全

类型:
- 001-099: 功能测试
- 101-199: 性能测试
- 201-299: 安全测试

示例: TC-AUTH-001, TC-PERF-API-001
```

### B. 测试数据命名规则

- 测试用户: `test_*`, `user*`, `admin`, `*@test.com`
- 测试产品: `PROD-*`
- 测试对话: `conv-uuid-*`
- 测试消息: `msg-uuid-*`

### C. 测试环境地址

| 环境 | URL | 数据库 |
|------|-----|--------|
| 本地 | http://localhost:8000 | ai_platform_dev |
| 测试 | http://qa.example.com | ai_platform_test |
| 预发布 | http://staging.example.com | ai_platform_staging |

---

**文档版本**: v1.0
**最后更新**: [项目完成日期]
**维护团队**: QA团队
