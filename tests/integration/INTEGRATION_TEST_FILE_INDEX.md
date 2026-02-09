# 集成测试文件索引

## 文档信息
- **创建日期**: [项目完成日期]
- **项目**: 内蒙古农畜产品AI赋能云平台
- **测试范围**: 前后端完整集成测试

---

## 目录结构

```
tests/
├── integration/                          # 集成测试目录
│   ├── INTEGRATION_TEST_PLAN.md         # 集成测试计划（主文档）
│   ├── API_TEST_CHECKLIST.md            # API测试检查清单
│   ├── E2E_TEST_SCENARIOS.md            # 端到端测试场景
│   ├── PERFORMANCE_TEST_GUIDE.md        # 性能测试指南
│   ├── SECURITY_TEST_CHECKLIST.md       # 安全测试检查清单
│   ├── INTEGRATION_TEST_QUICK_REFERENCE.md  # 快速参考指南
│   ├── INTEGRATION_TEST_FILE_INDEX.md   # 本文件索引
│   │
│   └── scripts/                          # 测试脚本目录
│       ├── test_api_integration.py       # API集成测试脚本
│       ├── test_auth_flow.py             # 认证流程测试脚本
│       ├── test_content_generation.py    # 内容生成测试脚本
│       └── run_all_tests.sh              # 测试执行脚本
│
└── reports/                              # 测试报告目录
    ├── INTEGRATION_TEST_REPORT_TEMPLATE.md  # 测试报告模板
    ├── api_test_results_*.json           # API测试结果
    ├── auth_flow_test_results_*.json     # 认证测试结果
    └── content_generation_test_results_*.json  # 内容生成测试结果
```

---

## 文档说明

### 1. 测试计划文档

#### INTEGRATION_TEST_PLAN.md
**路径**: `tests/integration/INTEGRATION_TEST_PLAN.md`
**大小**: ~15KB
**用途**: 完整的集成测试计划和策略

**包含内容**:
- 测试概述和目标
- 测试环境配置
- 测试范围（56个API端点）
- 测试策略（API、前端、E2E、性能、安全）
- 测试用例编号规则
- 验收标准
- 风险与缓解措施
- 执行步骤

**适用人员**: 测试负责人、项目经理、开发团队

---

### 2. API测试文档

#### API_TEST_CHECKLIST.md
**路径**: `tests/integration/API_TEST_CHECKLIST.md`
**大小**: ~25KB
**用途**: 详细的API测试检查清单

**包含内容**:
- 8个认证授权端点测试（24个用例）
- 9个产品管理端点测试（35个用例）
- 6个AI对话端点测试（18个用例）
- 15个权限管理端点测试（30个用例）
- 12个文化标签端点测试（18个用例）
- 9个素材管理端点测试（16个用例）
- 测试执行指南
- 测试报告模板

**适用人员**: 测试工程师、后端开发

**使用方法**:
1. 按照检查清单逐项测试
2. 记录测试结果（✅/❌/⏸️）
3. 填写测试报告

---

### 3. 端到端测试文档

#### E2E_TEST_SCENARIOS.md
**路径**: `tests/integration/E2E_TEST_SCENARIOS.md`
**大小**: ~20KB
**用途**: 完整业务流程测试场景

**包含内容**:
- 场景1: 新用户注册登录流程（8个步骤）
- 场景2: 产品浏览和搜索流程（8个步骤）
- 场景3: AI对话咨询流程（8个步骤）
- 场景4: 内容生成工作流程（10个步骤）
- 场景5: 管理员管理流程（8个步骤）
- 异常场景测试
- 性能要求

**适用人员**: 测试工程师、产品经理、QA团队

**使用方法**:
1. 按照场景步骤逐一执行
2. 验证每个步骤的期望结果
3. 记录执行时间和问题
4. 截图保存证据

---

### 4. 性能测试文档

#### PERFORMANCE_TEST_GUIDE.md
**路径**: `tests/integration/PERFORMANCE_TEST_GUIDE.md`
**大小**: ~18KB
**用途**: 性能测试方法和工具指南

**包含内容**:
- 性能测试目标和指标
- 测试场景（产品列表、AI对话、内容生成、混合负载）
- 测试工具（Locust、Apache Bench、Browser DevTools、Lighthouse）
- 执行步骤
- 结果分析方法
- 优化建议

**适用人员**: 性能测试工程师、架构师

**使用方法**:
1. 安装测试工具
2. 准备测试环境
3. 执行负载测试
4. 分析性能指标
5. 生成性能报告

---

### 5. 安全测试文档

#### SECURITY_TEST_CHECKLIST.md
**路径**: `tests/integration/SECURITY_TEST_CHECKLIST.md`
**大小**: ~22KB
**用途**: 安全测试项目检查清单

**包含内容**:
- 认证安全（密码强度、Token安全）
- 授权安全（权限验证、越权访问）
- 输入验证（SQL注入、XSS、命令注入）
- 数据安全（敏感数据保护、传输安全）
- API安全（CORS、速率限制）
- 会话管理
- 文件上传安全
- 配置安全

**适用人员**: 安全测试工程师、安全审计员

**使用方法**:
1. 按照检查清单逐项测试
2. 使用安全测试工具（Burp Suite、OWASP ZAP）
3. 记录发现的漏洞
4. 评估风险等级（P0/P1/P2）
5. 生成安全报告

---

### 6. 快速参考文档

#### INTEGRATION_TEST_QUICK_REFERENCE.md
**路径**: `tests/integration/INTEGRATION_TEST_QUICK_REFERENCE.md`
**大小**: ~8KB
**用途**: 快速查找和执行测试

**包含内容**:
- 快速开始指南
- 文档索引
- 测试模块概览
- 测试数据
- 验收标准
- 常见问题
- 性能基准

**适用人员**: 所有测试人员

**使用方法**:
- 快速查找需要的文档
- 快速执行测试命令
- 快速解决常见问题

---

## 测试脚本说明

### 1. API集成测试脚本

#### test_api_integration.py
**路径**: `tests/integration/scripts/test_api_integration.py`
**大小**: ~12KB
**语言**: Python 3.11+
**依赖**: httpx, asyncio

**功能**:
- 测试所有API端点
- 支持模块化测试
- 自动生成测试报告
- 支持并发测试

**使用方法**:
```bash
# 测试所有模块
python test_api_integration.py

# 测试特定模块
python test_api_integration.py --module auth
python test_api_integration.py --module products
python test_api_integration.py --module chat

# 详细输出
python test_api_integration.py --verbose
```

**测试模块**:
- HealthTests: 健康检查
- AuthTests: 认证授权
- ProductTests: 产品管理
- ChatTests: AI对话

---

### 2. 认证流程测试脚本

#### test_auth_flow.py
**路径**: `tests/integration/scripts/test_auth_flow.py`
**大小**: ~8KB
**语言**: Python 3.11+
**依赖**: httpx, asyncio

**功能**:
- 测试完整认证流程
- 测试Token生命周期
- 测试权限验证
- 测试密码安全

**使用方法**:
```bash
python test_auth_flow.py
```

**测试用例**:
1. 注册新用户
2. 使用凭证登录
3. 验证Token
4. 访问受保护资源
5. 无Token访问
6. 使用无效Token
7. 错误密码登录
8. 重复注册
9. 弱密码注册
10. 登出

---

### 3. 内容生成测试脚本

#### test_content_generation.py
**路径**: `tests/integration/scripts/test_content_generation.py`
**大小**: ~10KB
**语言**: Python 3.11+
**依赖**: httpx, asyncio

**功能**:
- 测试内容生成功能
- 测试RAG知识库集成
- 测试批量生成
- 测试内容评分和导出

**使用方法**:
```bash
python test_content_generation.py
```

**测试用例**:
1. 生成内容
2. 使用RAG生成内容
3. 批量生成
4. 内容评分
5. 导出Markdown
6. 导出Word
7. 获取模板列表
8. 获取任务列表
9. 无效产品ID
10. 缺少配置参数

---

### 4. 测试执行脚本

#### run_all_tests.sh
**路径**: `tests/integration/scripts/run_all_tests.sh`
**大小**: ~5KB
**语言**: Bash
**依赖**: bash, curl, python

**功能**:
- 一键执行所有测试
- 检查环境状态
- 生成测试报告
- 支持模块化执行

**使用方法**:
```bash
# 执行所有测试
bash run_all_tests.sh

# 仅执行API测试
bash run_all_tests.sh --api-only

# 仅执行认证测试
bash run_all_tests.sh --auth-only

# 查看帮助
bash run_all_tests.sh --help
```

**执行流程**:
1. 检查后端服务
2. 检查前端服务
3. 检查Python依赖
4. 执行API集成测试
5. 执行认证流程测试
6. 执行内容生成测试
7. 生成测试报告

---

## 测试报告说明

### 1. 测试报告模板

#### INTEGRATION_TEST_REPORT_TEMPLATE.md
**路径**: `tests/reports/INTEGRATION_TEST_REPORT_TEMPLATE.md`
**大小**: ~18KB
**用途**: 标准化测试报告格式

**包含内容**:
- 执行摘要
- 测试环境
- 测试执行详情
- 端到端测试结果
- 性能测试结果
- 安全测试结果
- Bug汇总
- 改进建议
- 验收结论

**使用方法**:
1. 复制模板
2. 填写实际测试数据
3. 替换YYYY-MM-DD为实际日期
4. 更新测试结果
5. 生成最终报告

---

### 2. JSON测试结果

#### api_test_results_*.json
**路径**: `tests/reports/api_test_results_YYYYMMDD_HHMMSS.json`
**格式**: JSON
**生成**: 自动生成

**内容结构**:
```json
{
  "timestamp": "[项目完成日期]T10:30:00",
  "results": {
    "total": 168,
    "passed": 160,
    "failed": 5,
    "skipped": 3,
    "errors": [
      "AUTH-004-01: Token刷新功能异常"
    ]
  }
}
```

---

## 使用流程

### 新手入门
1. 阅读 `INTEGRATION_TEST_QUICK_REFERENCE.md`
2. 准备测试环境
3. 执行 `run_all_tests.sh`
4. 查看测试报告

### 日常测试
1. 执行特定模块测试
2. 记录测试结果
3. 更新测试报告

### 完整测试
1. 阅读 `INTEGRATION_TEST_PLAN.md`
2. 按照 `API_TEST_CHECKLIST.md` 测试API
3. 按照 `E2E_TEST_SCENARIOS.md` 测试业务流程
4. 执行性能测试和安全测试
5. 生成完整测试报告

---

## 维护说明

### 文档更新
- 每次添加新功能时更新相应文档
- 每月审查一次文档准确性
- 版本号遵循语义化版本规范

### 脚本维护
- 定期更新依赖包
- 添加新的测试用例
- 优化测试性能

### 报告归档
- 每周归档测试报告
- 保留最近3个月的报告
- 重要报告永久保存

---

## 相关资源

### 内部文档
- API文档: http://localhost:8000/docs
- 前端组件文档: `frontend/COMPONENT_API.md`
- 数据库Schema: `backend/docs/database-schema.md`

### 外部资源
- FastAPI文档: https://fastapi.tiangolo.com/
- Vue 3文档: https://vuejs.org/
- Locust文档: https://docs.locust.io/

---

**文档版本**: 1.0
**最后更新**: [项目完成日期]
**维护人**: [姓名]
