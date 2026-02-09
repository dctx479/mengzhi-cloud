# 4周编排执行计划（方案A+B混合）

**项目**: 内蒙古农畜产品品牌营销AI赋能云平台
**执行模式**: HIERARCHICAL + PARALLEL混合编排
**开始日期**: [项目完成日期]
**预计完成**: 2026-02-14（4周）
**开发者**: dctx479

---

## 📅 整体时间线

```
Week 1: 测试与文档 (SEQUENTIAL)
  └─ 确保现有功能稳定、文档完整

Week 2-3: 功能完善 (PARALLEL)
  ├─ Week 2: 后端核心API完善
  └─ Week 3: 前端核心页面完善

Week 4: AI能力增强 (PARALLEL)
  └─ 数据采集、算法优化
```

---

## 第1周: 测试与文档（SEQUENTIAL策略）

**目标**: 确保现有功能稳定，文档完整，为后续开发打好基础

**编排策略**: SEQUENTIAL（任务间有依赖，必须按序执行）

### 任务清单

| 序号 | 任务ID | 任务名称 | Agent类型 | 预计时间 | 依赖 | 优先级 |
|------|--------|---------|----------|---------|------|--------|
| 1.1 | BE-018 | API文档编写 | spec-writer | 8h | - | P0 |
| 1.2 | TEST-001 | 测试计划编写 | spec-writer | 4h | 1.1 | P0 |
| 1.3 | TEST-002 | 模块功能测试 | qa-reviewer | 8h | 1.2 | P0 |
| 1.4 | BE-019 | 后端单元测试 | general-purpose | 16h | 1.1 | P0 |
| 1.5 | FE-016 | 前端测试 | general-purpose | 12h | 1.1 | P0 |

**总计**: 48小时（约6个工作日）

### 详细任务说明

#### 1.1 API文档编写 (BE-018)
**Agent**: spec-writer
**输入**:
- 现有代码: `backend/app/api/*.py`
- API设计规范: `docs/api/api-design-spec.md`

**输出**:
- `docs/api/authentication-api.md` - 认证API文档
- `docs/api/products-api.md` - 产品API文档
- `docs/api/chat-api.md` - AI对话API文档
- `docs/api/api-index.md` - API索引

**验收标准**:
- [ ] 每个端点有完整的请求/响应示例
- [ ] 包含错误码说明
- [ ] 包含认证说明
- [ ] 可导出为Postman Collection

---

#### 1.2 测试计划编写 (TEST-001)
**Agent**: spec-writer
**输入**: API文档

**输出**:
- `docs/testing/test-plan.md` - 测试计划
- `docs/testing/test-cases.md` - 测试用例清单

**验收标准**:
- [ ] 覆盖所有23个API端点
- [ ] 包含正常和异常场景
- [ ] 定义测试数据准备方法

---

#### 1.3 模块功能测试 (TEST-002)
**Agent**: qa-reviewer
**输入**: 测试计划、现有代码

**输出**:
- `docs/testing/test-report-week1.md` - 测试报告
- `docs/testing/bug-list.md` - Bug清单

**验收标准**:
- [ ] 执行所有测试用例
- [ ] 记录发现的问题
- [ ] 评估功能完整性
- [ ] 给出质量评分

---

#### 1.4 后端单元测试 (BE-019)
**Agent**: general-purpose
**输入**: API代码、测试框架

**输出**:
- `backend/tests/test_auth_api.py` - 认证API测试
- `backend/tests/test_products_api.py` - 产品API测试
- `backend/tests/test_chat_api.py` - 对话API测试
- `backend/tests/test_services.py` - 服务层测试

**验收标准**:
- [ ] 测试覆盖率 > 70%
- [ ] 所有测试通过
- [ ] 包含Mock外部依赖（DeepSeek API、Redis等）

---

#### 1.5 前端测试 (FE-016)
**Agent**: general-purpose
**输入**: 前端组件代码

**输出**:
- `frontend/tests/unit/` - 单元测试
- `frontend/tests/e2e/` - E2E测试（可选）
- `frontend/tests/coverage-report.html` - 覆盖率报告

**验收标准**:
- [ ] 关键组件有单元测试
- [ ] 关键用户流程有E2E测试
- [ ] 测试覆盖率 > 60%

---

## 第2周: 后端核心API完善（PARALLEL策略）

**目标**: 完善后端核心功能，增强系统能力

**编排策略**: PARALLEL（3个任务可并行执行）

### 任务清单

| 序号 | 任务ID | 任务名称 | Agent类型 | 预计时间 | 依赖 | 优先级 |
|------|--------|---------|----------|---------|------|--------|
| 2.1 | BE-005 | 权限管理系统完善 | general-purpose | 16h | Week1 | P0 |
| 2.2 | BE-007 | 文化标签管理 | general-purpose | 12h | Week1 | P1 |
| 2.3 | BE-008 | 多模态素材管理 | general-purpose | 20h | Week1 | P1 |

**总计**: 48小时（可并行执行，实际约2-3天）

### 详细任务说明

#### 2.1 权限管理系统完善 (BE-005)
**Agent**: general-purpose

**当前状态**: 30%完成（有基础的admin权限检查）

**待完成内容**:
- RBAC角色权限模型（Role, Permission表）
- 权限装饰器（@require_permission）
- 权限管理API（角色CRUD、权限分配）
- 权限缓存机制（Redis）

**输出文件**:
- `backend/app/models/role.py` - 角色模型
- `backend/app/models/permission.py` - 权限模型
- `backend/app/api/permissions.py` - 权限管理API
- `backend/app/core/permissions.py` - 权限装饰器
- `backend/alembic/versions/002_add_rbac.py` - 数据库迁移

**验收标准**:
- [ ] 支持至少3种角色（admin, enterprise, user）
- [ ] 支持动态权限分配
- [ ] API端点都有权限控制
- [ ] 有权限管理界面的API

---

#### 2.2 文化标签管理 (BE-007)
**Agent**: general-purpose

**当前状态**: 40%完成（Product表有cultural_tags字段）

**待完成内容**:
- 标签CRUD API
- 标签分类管理（地理、工艺、历史等）
- 标签推荐算法
- 标签统计API

**输出文件**:
- `backend/app/models/culture_tag.py` - 标签模型
- `backend/app/api/culture_tags.py` - 标签API
- `backend/app/services/culture_tag_service.py` - 标签服务
- `backend/alembic/versions/003_add_culture_tags.py` - 迁移

**验收标准**:
- [ ] 标签CRUD完整
- [ ] 支持标签分类
- [ ] 产品可关联多个标签
- [ ] 有标签热度统计

---

#### 2.3 多模态素材管理 (BE-008)
**Agent**: general-purpose

**当前状态**: 0%（全新功能）

**待完成内容**:
- 文件上传API（支持图片、视频）
- OSS集成（阿里云OSS或MinIO）
- 素材库管理API
- 图片处理（压缩、裁剪）

**输出文件**:
- `backend/app/models/media.py` - 媒体模型
- `backend/app/api/media.py` - 媒体API
- `backend/app/services/oss_service.py` - OSS服务
- `backend/app/services/image_service.py` - 图片处理
- `backend/alembic/versions/004_add_media.py` - 迁移

**验收标准**:
- [ ] 支持图片上传（JPG/PNG，最大10MB）
- [ ] 支持视频上传（MP4，最大100MB）
- [ ] 自动生成缩略图
- [ ] 返回CDN地址

---

## 第3周: 前端核心页面完善（PARALLEL策略）

**目标**: 完善前端用户体验，增加核心业务功能

**编排策略**: PARALLEL（4个任务可并行执行）

### 任务清单

| 序号 | 任务ID | 任务名称 | Agent类型 | 预计时间 | 依赖 | 优先级 |
|------|--------|---------|----------|---------|------|--------|
| 3.1 | FE-007 | 用户中心模块完善 | general-purpose | 16h | Week2 | P0 |
| 3.2 | FE-008 | 智能对话界面优化 | general-purpose | 12h | Week2 | P0 |
| 3.3 | FE-009 | 内容生成工作台 | general-purpose | 20h | Week2 | P1 |
| 3.4 | FE-010 | 产品浏览功能完善 | general-purpose | 12h | Week2 | P1 |

**总计**: 60小时（可并行执行，实际约3-4天）

### 详细任务说明

#### 3.1 用户中心模块完善 (FE-007)
**Agent**: general-purpose

**当前状态**: 50%完成（有基础的Profile页面）

**待完成内容**:
- 订单历史页面
- 配额管理页面（查看剩余配额、充值）
- 账号设置页面（修改密码、绑定第三方）
- 我的收藏页面

**输出文件**:
- `frontend/src/views/user/Orders.vue` - 订单历史
- `frontend/src/views/user/Quota.vue` - 配额管理
- `frontend/src/views/user/Settings.vue` - 账号设置
- `frontend/src/views/user/Favorites.vue` - 我的收藏

**验收标准**:
- [ ] 所有页面响应式设计
- [ ] 有loading和空状态
- [ ] 数据实时刷新
- [ ] 操作有确认提示

---

#### 3.2 智能对话界面优化 (FE-008)
**Agent**: general-purpose

**当前状态**: 60%完成（基础对话功能已实现）

**待完成内容**:
- 文件上传功能（图片、PDF）
- 多轮对话上下文显示
- 消息编辑和重新生成
- 对话导出功能
- 快捷指令面板

**输出文件**:
- 更新 `frontend/src/views/chat/ChatPage.vue`
- 新增 `frontend/src/components/chat/FileUpload.vue`
- 新增 `frontend/src/components/chat/QuickCommands.vue`
- 新增 `frontend/src/components/chat/ExportDialog.vue`

**验收标准**:
- [ ] 支持拖拽上传文件
- [ ] 显示完整对话历史
- [ ] 可编辑已发送消息
- [ ] 可导出为Markdown/PDF

---

#### 3.3 内容生成工作台 (FE-009)
**Agent**: general-purpose

**当前状态**: 0%（全新功能）

**待完成内容**:
- 文案生成界面（标题、描述、广告语）
- 直播脚本生成界面
- 批量生成任务管理
- 生成历史管理
- 模板选择器

**输出文件**:
- `frontend/src/views/generation/Workspace.vue` - 工作台主页
- `frontend/src/views/generation/CopywritingGen.vue` - 文案生成
- `frontend/src/views/generation/LiveScriptGen.vue` - 直播脚本
- `frontend/src/views/generation/TaskManager.vue` - 任务管理
- `frontend/src/components/generation/TemplateSelector.vue` - 模板选择

**验收标准**:
- [ ] 支持选择产品和模板
- [ ] 实时预览生成结果
- [ ] 可编辑和保存结果
- [ ] 批量任务有进度显示

---

#### 3.4 产品浏览功能完善 (FE-010)
**Agent**: general-purpose

**当前状态**: 70%完成（基础列表和详情已实现）

**待完成内容**:
- 高级筛选面板（多维度筛选）
- 地图展示模式（按产地分布）
- 产品对比功能
- 推荐相关产品

**输出文件**:
- 更新 `frontend/src/views/products/ProductList.vue`
- 新增 `frontend/src/components/products/FilterPanel.vue`
- 新增 `frontend/src/components/products/MapView.vue`
- 新增 `frontend/src/components/products/CompareDialog.vue`

**验收标准**:
- [ ] 支持按价格、地区、认证等筛选
- [ ] 地图模式显示产地标记
- [ ] 可同时对比3个产品
- [ ] 详情页显示相关推荐

---

## 第4周: AI能力增强（PARALLEL策略）

**目标**: 增强AI功能，补充数据，优化算法

**编排策略**: PARALLEL（3个任务可并行执行）

### 任务清单

| 序号 | 任务ID | 任务名称 | Agent类型 | 预计时间 | 依赖 | 优先级 |
|------|--------|---------|----------|---------|------|--------|
| 4.1 | AI-001 | 补充产品数据采集 | general-purpose | 20h | - | P0 |
| 4.2 | AI-006 | Prompt模板优化 | general-purpose | 12h | - | P1 |
| 4.3 | AI-007 | 内容生成算法优化 | general-purpose | 16h | 4.2 | P1 |

**总计**: 48小时（可并行执行，实际约2-3天）

### 详细任务说明

#### 4.1 补充产品数据采集 (AI-001)
**Agent**: general-purpose

**当前状态**: 30%完成（已有10个产品）

**待完成内容**:
- 采集剩余27个地理标志产品
- 补充文化背景资料
- 补充市场数据（价格、销量）
- 补充图片素材

**输出文件**:
- `data/products/batch2.json` - 第二批15个产品
- `data/products/batch3.json` - 第三批12个产品
- `data/products/market-data.json` - 市场数据
- `data/products/images/` - 产品图片

**验收标准**:
- [ ] 总共37个产品数据完整
- [ ] 每个产品有至少3张图片
- [ ] 文化背景字数 > 300字
- [ ] 市场数据真实可靠

---

#### 4.2 Prompt模板优化 (AI-006)
**Agent**: general-purpose

**当前状态**: 40%完成（已有7个基础模板）

**待完成内容**:
- 补充营销场景模板（20+个）
- 优化现有模板效果
- 添加变量和示例
- 模板分类管理

**输出文件**:
- 更新 `backend/app/services/ai/prompt_templates.py`
- `backend/app/models/prompt_template.py` - 模板模型
- `data/prompts/marketing-templates.json` - 营销模板库

**验收标准**:
- [ ] 至少20个营销场景模板
- [ ] 每个模板有使用示例
- [ ] 模板可动态变量替换
- [ ] 有模板效果评分

---

#### 4.3 内容生成算法优化 (AI-007)
**Agent**: general-purpose

**当前状态**: 0%（全新功能）

**待完成内容**:
- 文案质量评估机制
- A/B测试框架
- 内容去重算法
- 敏感词过滤

**输出文件**:
- `backend/app/services/ai/content_evaluator.py` - 质量评估
- `backend/app/services/ai/ab_test.py` - A/B测试
- `backend/app/services/ai/content_filter.py` - 内容过滤
- `backend/app/services/ai/deduplication.py` - 去重

**验收标准**:
- [ ] 可自动评估文案质量（0-100分）
- [ ] 支持多个版本A/B测试
- [ ] 自动过滤敏感词
- [ ] 生成内容去重率 > 90%

---

## 📊 总体工作量

| 周次 | 任务数 | 总工时 | 并行度 | 实际天数 |
|------|--------|--------|--------|---------|
| Week 1 | 5 | 48h | 1x (串行) | 6天 |
| Week 2 | 3 | 48h | 3x (并行) | 2-3天 |
| Week 3 | 4 | 60h | 4x (并行) | 3-4天 |
| Week 4 | 3 | 48h | 3x (并行) | 2-3天 |
| **总计** | **15** | **204h** | - | **13-16天** |

**预计完成时间**: 2-3周（如果全职开发）

---

## 🎯 执行监控

### 进度跟踪
- 使用TodoWrite工具实时更新任务状态
- 每周五生成进度报告
- 遇到阻塞及时调整计划

### 质量保证
- 每个任务完成后由qa-reviewer审查
- 代码提交前通过测试
- 文档同步更新

### 风险管理
- 第三方API不稳定 → 使用Mock数据测试
- 任务超时 → 降低优先级或简化实现
- 资源不足 → 调整并行度

---

## 📄 输出成果

### 文档
- API文档（完整）
- 测试报告
- 开发文档
- 部署文档

### 代码
- 后端新增3个核心模块
- 前端新增4个完整页面
- 数据库新增4个迁移
- 测试覆盖率提升至70%+

### 数据
- 37个完整产品数据
- 20+个Prompt模板
- 市场数据和图片素材

---

**准备启动编排执行！**
