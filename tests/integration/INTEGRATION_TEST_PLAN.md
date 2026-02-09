# 前后端完整集成测试计划

## 文档信息
- **版本**: 1.0
- **创建日期**: [项目完成日期]
- **项目**: 内蒙古农畜产品AI赋能云平台
- **测试范围**: 前后端完整集成测试

## 目录
1. [测试概述](#测试概述)
2. [测试环境](#测试环境)
3. [测试范围](#测试范围)
4. [测试策略](#测试策略)
5. [测试用例](#测试用例)
6. [验收标准](#验收标准)
7. [风险与缓解](#风险与缓解)

---

## 测试概述

### 测试目标
验证前后端系统的完整集成，确保所有功能模块正常协作，满足业务需求和性能指标。

### 测试类型
- **API集成测试**: 验证56个后端API端点
- **前端集成测试**: 验证25+个Vue组件和页面
- **端到端测试**: 验证完整业务流程
- **性能测试**: 验证响应时间和吞吐量
- **安全测试**: 验证认证授权和数据安全
- **兼容性测试**: 验证浏览器和设备兼容性

### 已完成功能模块
- Week 1: API文档、测试计划、单元测试（500+测试用例）
- Week 2: 权限管理（RBAC）、文化标签管理、素材管理（36个API）
- Week 3: 用户中心、对话界面、内容生成、产品浏览（25+组件）
- Week 4: 产品数据（1047个）、Prompt模板（20+）、RAG算法

---

## 测试环境

### 后端环境
```yaml
运行环境:
  - Python: 3.11+
  - FastAPI: 最新版
  - MySQL: 8.0
  - Redis: 7.0
  - DeepSeek API: 已配置

依赖服务:
  - 数据库: MySQL (localhost:3306)
  - 缓存: Redis (localhost:6379)
  - AI服务: DeepSeek API

环境变量:
  - DATABASE_URL: mysql+pymysql://user:pass@localhost:3306/agri_ai
  - REDIS_URL: redis://localhost:6379/0
  - DEEPSEEK_API_KEY: sk-xxx
  - JWT_SECRET_KEY: xxx
```

### 前端环境
```yaml
运行环境:
  - Node.js: 18+
  - Vue: 3.4+
  - Vite: 5.0+
  - Element Plus: 2.5+

开发服务器:
  - URL: http://localhost:5173
  - API代理: http://localhost:8000

构建配置:
  - 输出目录: dist/
  - 资源路径: /assets/
```

### 测试数据
```yaml
用户数据:
  - 管理员: admin@test.com / Admin123!
  - 普通用户: user@test.com / User123!
  - 企业用户: enterprise@test.com / Enterprise123!

产品数据:
  - 总数: 1047个产品
  - 类别: 肉类、乳制品、粮食、中药材等
  - 地区: 内蒙古12个盟市

文化标签:
  - 总数: 50+个标签
  - 分类: 地域文化、历史传承、工艺特色等
```

---

## 测试范围

### 1. 认证授权模块（8个端点）

#### API端点
- `POST /api/v1/auth/register` - 用户注册
- `POST /api/v1/auth/login` - 用户登录
- `POST /api/v1/auth/logout` - 用户登出
- `POST /api/v1/auth/refresh` - 刷新Token
- `POST /api/v1/auth/change-password` - 修改密码
- `POST /api/v1/auth/reset-password` - 重置密码
- `GET /api/v1/auth/verify` - 验证Token
- `GET /api/v1/auth/captcha` - 获取验证码

#### 测试重点
- 注册流程完整性
- 登录认证正确性
- Token生成和验证
- 密码加密安全性
- 验证码防刷机制
- 权限验证准确性

### 2. 产品管理模块（9个端点）

#### API端点
- `GET /api/v1/products` - 获取产品列表（分页、搜索、筛选）
- `GET /api/v1/products/{id}` - 获取产品详情
- `POST /api/v1/products` - 创建产品（管理员）
- `PUT /api/v1/products/{id}` - 更新产品（管理员）
- `DELETE /api/v1/products/{id}` - 删除产品（管理员）
- `GET /api/v1/products/{id}/cultural-info` - 获取文化信息
- `GET /api/v1/products/categories/list` - 获取类别列表
- `GET /api/v1/products/regions/list` - 获取地区列表
- `GET /api/v1/products/statistics` - 获取统计信息

#### 测试重点
- 分页功能正确性
- 搜索功能准确性
- 筛选条件有效性
- 排序功能正确性
- CRUD操作完整性
- 权限控制准确性

### 3. AI对话模块（6个端点）

#### API端点
- `POST /api/v1/chat/message` - 发送消息（非流式）
- `POST /api/v1/chat/stream` - 发送消息（流式SSE）
- `GET /api/v1/chat/conversations` - 获取对话列表
- `GET /api/v1/chat/conversations/{id}` - 获取对话详情
- `DELETE /api/v1/chat/conversations/{id}` - 删除对话
- `PATCH /api/v1/chat/conversations/{id}` - 更新对话

#### 测试重点
- DeepSeek API集成
- 流式响应正确性
- 对话上下文管理
- Token计数准确性
- 错误处理完整性
- 并发请求处理

### 4. 内容生成模块（9个端点）

#### API端点
- `POST /api/v1/content/generate` - 生成内容（RAG）
- `POST /api/v1/content/batch-generate` - 批量生成
- `GET /api/v1/content/tasks` - 获取任务列表
- `GET /api/v1/content/tasks/{id}` - 获取任务详情
- `POST /api/v1/content/score` - 内容评分
- `POST /api/v1/content/export` - 导出内容
- `GET /api/v1/content/templates` - 获取模板列表
- `POST /api/v1/content/templates` - 创建模板
- `PUT /api/v1/content/templates/{id}` - 更新模板

#### 测试重点
- RAG算法准确性
- 批量生成性能
- 任务状态管理
- 评分算法合理性
- 导出格式正确性
- 模板管理完整性

### 5. 权限管理模块（15个端点）

#### API端点
**角色管理**:
- `GET /api/v1/rbac/roles` - 获取角色列表
- `POST /api/v1/rbac/roles` - 创建角色
- `PUT /api/v1/rbac/roles/{id}` - 更新角色
- `DELETE /api/v1/rbac/roles/{id}` - 删除角色
- `GET /api/v1/rbac/roles/{id}/permissions` - 获取角色权限

**权限管理**:
- `GET /api/v1/rbac/permissions` - 获取权限列表
- `POST /api/v1/rbac/permissions` - 创建权限
- `PUT /api/v1/rbac/permissions/{id}` - 更新权限
- `DELETE /api/v1/rbac/permissions/{id}` - 删除权限

**用户角色**:
- `GET /api/v1/rbac/user-roles/{user_id}` - 获取用户角色
- `POST /api/v1/rbac/user-roles` - 分配角色
- `DELETE /api/v1/rbac/user-roles` - 移除角色

**权限验证**:
- `GET /api/v1/rbac/check-permission` - 检查权限
- `GET /api/v1/rbac/user-permissions/{user_id}` - 获取用户所有权限
- `POST /api/v1/rbac/roles/{id}/permissions` - 分配权限给角色

#### 测试重点
- RBAC模型正确性
- 角色继承关系
- 权限验证准确性
- 用户角色分配
- 权限缓存机制

### 6. 文化标签模块（12个端点）

#### API端点
- `GET /api/v1/cultural-tags` - 获取标签列表
- `GET /api/v1/cultural-tags/{id}` - 获取标签详情
- `POST /api/v1/cultural-tags` - 创建标签
- `PUT /api/v1/cultural-tags/{id}` - 更新标签
- `DELETE /api/v1/cultural-tags/{id}` - 删除标签
- `GET /api/v1/cultural-tags/categories` - 获取标签分类
- `POST /api/v1/products/{id}/tags` - 为产品分配标签
- `DELETE /api/v1/products/{id}/tags/{tag_id}` - 移除产品标签
- `GET /api/v1/products/{id}/tags` - 获取产品标签
- `GET /api/v1/cultural-tags/{id}/products` - 获取标签关联产品
- `POST /api/v1/cultural-tags/batch-assign` - 批量分配标签
- `GET /api/v1/cultural-tags/statistics` - 获取标签统计

#### 测试重点
- 标签分类管理
- 产品标签关联
- 批量操作性能
- 标签统计准确性

### 7. 素材管理模块（9个端点）

#### API端点
- `GET /api/v1/media` - 获取素材列表
- `GET /api/v1/media/{id}` - 获取素材详情
- `POST /api/v1/media/upload` - 上传素材
- `DELETE /api/v1/media/{id}` - 删除素材
- `PUT /api/v1/media/{id}` - 更新素材信息
- `GET /api/v1/media/types` - 获取素材类型
- `POST /api/v1/media/batch-upload` - 批量上传
- `POST /api/v1/media/process` - 处理素材（压缩、裁剪）
- `GET /api/v1/media/statistics` - 获取素材统计

#### 测试重点
- 文件上传功能
- 图片处理功能
- 文件类型验证
- 存储空间管理
- 批量上传性能

---

## 测试策略

### 1. API集成测试策略

#### 测试方法
- 使用pytest + httpx进行自动化测试
- 每个端点至少3个测试用例（正常、异常、边界）
- 使用测试数据库和测试数据
- 测试前清理数据，测试后恢复

#### 测试覆盖
- **正常场景**: 验证正常输入的正确输出
- **异常场景**: 验证错误处理和错误消息
- **边界场景**: 验证边界值和极限情况
- **权限场景**: 验证认证和授权控制

#### 测试顺序
1. 健康检查和基础端点
2. 认证授权模块
3. 产品管理模块
4. AI对话模块
5. 内容生成模块
6. 权限管理模块
7. 文化标签和素材模块

### 2. 前端集成测试策略

#### 测试方法
- 使用Vitest + Vue Test Utils
- 组件单元测试 + 集成测试
- 模拟API响应
- 测试用户交互

#### 测试覆盖
- **组件渲染**: 验证组件正确渲染
- **用户交互**: 验证点击、输入等交互
- **状态管理**: 验证Pinia状态更新
- **路由导航**: 验证页面跳转
- **API调用**: 验证API请求和响应处理

### 3. 端到端测试策略

#### 测试场景
1. **新用户注册登录流程**
2. **产品浏览和搜索流程**
3. **AI对话咨询流程**
4. **内容生成工作流程**
5. **管理员管理流程**

#### 测试方法
- 手动测试 + 自动化脚本
- 模拟真实用户操作
- 验证完整业务流程
- 记录测试结果和截图

### 4. 性能测试策略

#### 测试指标
- **API响应时间**: p50, p95, p99
- **吞吐量**: 请求/秒
- **并发用户**: 10, 50, 100用户
- **错误率**: < 1%

#### 测试工具
- Locust: 负载测试
- Apache Bench: 简单压测
- 浏览器DevTools: 前端性能

### 5. 安全测试策略

#### 测试项目
- **认证安全**: Token验证、会话管理
- **授权安全**: 权限控制、越权访问
- **输入验证**: SQL注入、XSS攻击
- **数据安全**: 密码加密、敏感数据保护
- **API安全**: CORS配置、速率限制

---

## 测试用例

### 用例编号规则
- **AUTH-xxx**: 认证授权测试
- **PROD-xxx**: 产品管理测试
- **CHAT-xxx**: AI对话测试
- **CONT-xxx**: 内容生成测试
- **RBAC-xxx**: 权限管理测试
- **TAG-xxx**: 文化标签测试
- **MEDIA-xxx**: 素材管理测试
- **E2E-xxx**: 端到端测试
- **PERF-xxx**: 性能测试
- **SEC-xxx**: 安全测试

### 优先级定义
- **P0**: 核心功能，必须通过
- **P1**: 重要功能，应该通过
- **P2**: 一般功能，可以延后
- **P3**: 边缘场景，可选

详细测试用例请参考：
- [API测试检查清单](./API_TEST_CHECKLIST.md)
- [端到端测试场景](./E2E_TEST_SCENARIOS.md)
- [性能测试指南](./PERFORMANCE_TEST_GUIDE.md)
- [安全测试检查清单](./SECURITY_TEST_CHECKLIST.md)

---

## 验收标准

### 必须通过（P0）
- ✅ 所有核心API端点可访问（200/201响应）
- ✅ 认证授权正常工作（登录、Token验证）
- ✅ 产品CRUD操作正常
- ✅ AI对话功能正常（非流式和流式）
- ✅ 内容生成功能正常（RAG集成）
- ✅ 权限验证准确（RBAC）
- ✅ 前端页面正常渲染
- ✅ 核心业务流程无阻塞
- ✅ 无P0级别Bug

### 期望达成（P1）
- 📊 API响应时间 p95 < 500ms
- 📊 前端FCP < 1.8s
- 📊 前端LCP < 2.5s
- 📊 API吞吐量 > 100 req/s
- 📊 错误率 < 1%
- 🔒 安全测试0高危漏洞
- 🌐 浏览器兼容性100%（Chrome, Firefox, Safari, Edge）
- 📱 移动端响应式正常

### 可接受（P2）
- API响应时间 p99 < 1s
- 前端TTI < 3.8s
- 前端CLS < 0.1
- 并发100用户无崩溃
- 无P1级别Bug

---

## 风险与缓解

### 技术风险

#### 1. DeepSeek API不稳定
**风险**: API超时、限流、服务中断
**影响**: AI对话和内容生成功能不可用
**缓解措施**:
- 实现重试机制（3次重试）
- 添加超时控制（30秒）
- 提供降级方案（缓存响应）
- 监控API健康状态

#### 2. 数据库性能瓶颈
**风险**: 大量数据查询导致响应慢
**影响**: 产品列表、搜索功能慢
**缓解措施**:
- 添加数据库索引
- 实现Redis缓存
- 优化SQL查询
- 分页限制数据量

#### 3. 文件上传失败
**风险**: 大文件上传超时、存储空间不足
**影响**: 素材管理、产品图片上传
**缓解措施**:
- 限制文件大小（10MB）
- 实现分片上传
- 监控存储空间
- 提供清理机制

### 环境风险

#### 1. 测试环境不稳定
**风险**: MySQL、Redis服务中断
**影响**: 测试无法进行
**缓解措施**:
- 使用Docker容器化
- 自动健康检查
- 快速重启机制

#### 2. 测试数据污染
**风险**: 测试数据影响生产数据
**影响**: 数据不一致
**缓解措施**:
- 使用独立测试数据库
- 测试前后清理数据
- 禁止测试环境访问生产

### 进度风险

#### 1. 测试时间不足
**风险**: 无法完成所有测试
**影响**: 质量无法保证
**缓解措施**:
- 优先测试P0用例
- 自动化测试脚本
- 并行执行测试

#### 2. Bug修复延迟
**风险**: 发现Bug后修复慢
**影响**: 测试进度延迟
**缓解措施**:
- 快速反馈机制
- 优先修复P0 Bug
- 记录已知问题

---

## 测试执行

### 执行步骤

#### 1. 环境准备
```bash
# 后端环境
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# 启动MySQL和Redis
docker-compose up -d mysql redis

# 初始化数据库
python scripts/init_db.py
python scripts/seed_data.py

# 启动后端服务
uvicorn app.main:app --reload --port 8000
```

#### 2. 前端环境
```bash
# 前端环境
cd frontend
npm install

# 启动开发服务器
npm run dev
```

#### 3. 执行测试
```bash
# API集成测试
cd tests/integration
python scripts/test_api_integration.py

# 认证流程测试
python scripts/test_auth_flow.py

# 内容生成测试
python scripts/test_content_generation.py

# 执行所有测试
bash scripts/run_all_tests.sh
```

#### 4. 生成报告
```bash
# 生成测试报告
python scripts/generate_report.py

# 查看报告
open tests/reports/integration_test_report.html
```

### 测试时间估算
- 环境准备: 30分钟
- API集成测试: 2小时
- 前端集成测试: 1.5小时
- 端到端测试: 2小时
- 性能测试: 1小时
- 安全测试: 1小时
- 报告生成: 30分钟
- **总计**: 约8.5小时

---

## 附录

### A. 测试工具
- **pytest**: Python测试框架
- **httpx**: HTTP客户端
- **Vitest**: Vue测试框架
- **Locust**: 性能测试工具
- **OWASP ZAP**: 安全测试工具

### B. 参考文档
- [API文档](http://localhost:8000/docs)
- [前端组件文档](../frontend/COMPONENT_API.md)
- [数据库Schema](../backend/docs/database-schema.md)
- [部署指南](../deploy/README.md)

### C. 联系方式
- 技术负责人: [联系方式]
- 测试负责人: [联系方式]
- 紧急联系: [联系方式]

---

**文档版本**: 1.0
**最后更新**: [项目完成日期]
**下次审查**: 2026-02-17
