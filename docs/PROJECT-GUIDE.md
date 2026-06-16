# 项目文档导航

> 蒙智云 — 内蒙古农畜产品 AI 赋能云平台文档索引

最后更新: 2026-06-16

---

## 📚 快速导航

### 🚀 新手必读 (按顺序阅读)

1. [README.md](../README.md) - 项目总览（5分钟）
2. [快速启动指南](planning/快速启动指南.md) - 快速上手（30分钟）
3. [项目主计划](project-planning/00-PROJECT-MASTER-PLAN.md) - 12周实施计划（30分钟）
4. [待办事项清单](TODO-LIST.md) - 当前任务与优先级（10分钟）

### 👨‍💻 开发必备

- [API设计规范](api/api-design-spec.md) - 前后端接口约定
- [数据库详细设计](design/database-design.md) - 数据模型定义
- [数据安全方案](design/security-design.md) - 安全规范
- [编码规范](CODING-STANDARDS.md) - 代码风格与最佳实践

### 📋 规划与管理

- [项目主计划](project-planning/00-PROJECT-MASTER-PLAN.md) - 12周实施计划
- [待办事项清单](TODO-LIST.md) - 当前任务与优先级
- [项目任务清单](planning/项目任务清单.md) - 79项详细任务
- [技术栈选型方案](planning/技术栈选型方案.md) - 技术决策

### 🤖 AI 功能文档

- [双IP智能体架构](technical/IP-AGENT-ARCHITECTURE.md) - 小数/小商技术设计
- [双IP智能体快速开始](technical/IP-AGENT-QUICKSTART.md) - 集成指南
- [文化元素系统](../backend/docs/CULTURAL-SYSTEM-INTEGRATION-REPORT.md) - 智能匹配与知识图谱
- [品牌故事生成器](../backend/docs/BRAND-STORY-INTEGRATION-REPORT.md) - 3种风格自动生成
- [多媒体Provider](../backend/docs/JIMENG-INTEGRATION-REPORT.md) - 即梦AI集成
- [批量内容生成](../backend/docs/BE-008-多模态素材管理系统.md) - 批量任务系统

---

## 📂 完整文档目录

### 根目录文档

| 文档 | 说明 | 优先级 | 字数 |
|------|------|--------|------|
| [README.md](../README.md) | 项目总览和快速开始 | 🔴 必读 | 5千 |
| [TODO-LIST.md](TODO-LIST.md) | 待办事项清单 | 🔴 必读 | 3千 |
| [.gitignore](../.gitignore) | Git忽略配置 | 🟢 参考 | - |

---

### 📝 规划文档 (docs/planning/ & docs/project-planning/)

| 文档 | 说明 | 目标读者 | 字数 | 预计阅读 |
|------|------|----------|------|---------|
| [00-PROJECT-MASTER-PLAN.md](project-planning/00-PROJECT-MASTER-PLAN.md) | 12周项目实施主计划 | 全体成员 | 1.5万 | 30分钟 |
| [01-REQUIREMENTS-SPECIFICATION.md](project-planning/01-REQUIREMENTS-SPECIFICATION.md) | 需求规格说明 | 产品/开发 | 2万 | 45分钟 |
| [02-TECHNICAL-ARCHITECTURE.md](project-planning/02-TECHNICAL-ARCHITECTURE.md) | 技术架构设计 | 技术团队 | 2.5万 | 60分钟 |
| [03-DEVELOPMENT-ROADMAP.md](project-planning/03-DEVELOPMENT-ROADMAP.md) | 开发路线图 | 开发团队 | 1.2万 | 20分钟 |
| [项目任务清单.md](planning/项目任务清单.md) | 79项详细任务分解 | 开发团队 | 3万 | 30分钟 |
| [技术栈选型方案.md](planning/技术栈选型方案.md) | 完整的技术选型分析 | 技术负责人 | 2.5万 | 45分钟 |
| [快速启动指南.md](planning/快速启动指南.md) | 快速上手指南 | 新成员 | 1.5万 | 30分钟 |

**阅读建议**:
- 项目负责人: 按顺序全部阅读
- 开发成员: 快速启动指南 → 项目任务清单 → 项目分析报告(选读)
- 新加入成员: README → 快速启动指南 → 相关任务文档

---

### 🎨 设计文档 (docs/design/)

| 文档 | 说明 | 状态 | 字数 | 完成度 |
|------|------|------|------|--------|
| [database-design.md](design/database-design.md) | MySQL/Neo4j/Qdrant详细设计 | ✅ 完成 | 3.8万 | 100% |
| [security-design.md](design/security-design.md) | 数据安全和合规方案 | ✅ 完成 | 1.8万 | 100% |

**包含内容**:
- **数据库设计**: 8张MySQL表、Neo4j图谱Schema、Qdrant向量库、Redis缓存设计
- **安全方案**: 敏感数据分级、加密策略、RBAC权限、安全检查清单

---

### 🔌 API文档 (docs/api/)

| 文档 | 说明 | 状态 | 字数 | 完成度 |
|------|------|------|------|--------|
| [api-design-spec.md](api/api-design-spec.md) | RESTful API完整规范 | ✅ 完成 | 2.7万 | 100% |
| [00-overview.md](api/00-overview.md) | API总览 | ✅ 完成 | - | 100% |
| [01-authentication.md](api/01-authentication.md) | 认证API | ✅ 完成 | - | 100% |
| [02-products.md](api/02-products.md) | 产品管理API | ✅ 完成 | - | 100% |
| [03-chat.md](api/03-chat.md) | 智能客服API | ✅ 完成 | - | 100% |
| [04-content-generation.md](api/04-content-generation.md) | 内容生成API | ✅ 完成 | - | 100% |
| [05-user-center.md](api/05-user-center.md) | 用户中心API | ✅ 完成 | - | 100% |
| [06-error-codes.md](api/06-error-codes.md) | 错误码定义 | ✅ 完成 | - | 100% |

**待补充**:
- [ ] 07-ip-agent.md - 双IP智能体API
- [ ] 08-cultural-elements.md - 文化元素API
- [ ] 09-brand-story.md - 品牌故事API
- [ ] 10-batch-generation.md - 批量任务API

**包含内容**:
- JWT双Token认证机制
- 统一响应格式
- 错误码体系(10xxx-50xxx)
- MVP核心接口定义(认证、产品、内容生成、用户管理)
- 完整请求/响应示例

---

### 🚀 部署文档

| 文档 | 说明 | 状态 |
|------|------|------|
| [DOCKER_DEPLOYMENT.md](DOCKER_DEPLOYMENT.md) | Docker 部署指南 | ✅ 完成 |
| [deployment-guide.md](deployment-guide.md) | 生产环境部署指南 | ✅ 完成 |
| [devops-guide.md](devops-guide.md) | 自动化运维系统指南 | ✅ 完成 |

### 🧪 测试文档 (docs/testing/)

| 文档 | 说明 | 状态 |
|------|------|------|
| [test-plan.md](testing/test-plan.md) | 测试计划 | ✅ 完成 |
| [test-cases.md](testing/test-cases.md) | 测试用例 | ✅ 完成 |
| [CULTURAL-SYSTEM-TEST-REPORT.md](testing/CULTURAL-SYSTEM-TEST-REPORT.md) | 文化系统测试报告 | ✅ 完成 |

**待补充**:
- [ ] IP智能体测试用例
- [ ] 批量内容生成测试用例
- [ ] 多媒体Provider测试用例

---

### 📖 用户手册 (docs/user-guide/)

| 文档 | 说明 | 状态 |
|------|------|------|
| - | 暂无 | 🟡 待创建 |

**待创建文档**:
- [ ] 用户使用手册
- [ ] 管理员手册
- [ ] FAQ常见问题

---

## 📊 文档统计

### 已完成文档

| 类别 | 文档数 | 总字数 | 总行数 | 完成度 |
|------|--------|--------|--------|--------|
| 规划文档 | 8 | 16万+ | - | 100% |
| 设计文档 | 2 | 5.6万 | 1589 | 100% |
| API文档 | 8 | 3万+ | 1500+ | 80% |
| AI功能文档 | 6 | 4万+ | - | 100% |
| 测试文档 | 3 | 2万+ | - | 70% |
| 部署文档 | 3 | 2万+ | - | 100% |
| **总计** | **30+** | **32万+** | **3000+** | **85%** |

### 待补充文档 (优先级排序)

| 优先级 | 文档 | 预计完成 | 责任人 |
|--------|------|---------|--------|
| 🔴 P0 | IP智能体API文档 | 1周内 | 后端负责人 |
| 🔴 P0 | 文化元素API文档 | 1周内 | 后端负责人 |
| 🔴 P0 | 品牌故事API文档 | 1周内 | 后端负责人 |
| 🟡 P1 | 批量任务API文档 | 2周内 | 后端负责人 |
| 🟡 P1 | 用户使用手册 | Phase 3 | 产品经理 |
| 🟢 P2 | 管理员手册 | Phase 3 | 产品经理 |

### 最近更新的功能模块

| 功能模块 | 完成日期 | 文档位置 | 状态 |
|---------|---------|---------|------|
| 双IP智能体 | 2026-06-12 | technical/IP-AGENT-* | ✅ 完成 |
| 文化元素系统 | 2026-06-12 | backend/docs/CULTURAL-* | ✅ 完成 |
| 品牌故事生成 | 2026-06-12 | backend/docs/BRAND-STORY-* | ✅ 完成 |
| 批量内容生成 Phase 2 | 2026-06-15 | backend/docs/BE-008-* | ✅ 完成 |
| 多媒体Provider | 2026-06-14 | backend/docs/*-INTEGRATION-REPORT.md | ✅ 完成 |

---

## 🎯 按角色推荐阅读

### 项目经理/负责人

**必读** (合计约2小时):
1. README.md (5分钟)
2. 项目主计划 00-PROJECT-MASTER-PLAN.md (30分钟)
3. 待办事项清单 TODO-LIST.md (10分钟)
4. 项目任务清单.md (30分钟)
5. 技术栈选型方案.md (45分钟)

**选读**:
- 开源项目参考与可扩展性架构分析.md (深入了解技术架构)

---

### 前端开发工程师

**必读** (合计约1.5小时):
1. README.md (5分钟)
2. 快速启动指南.md (30分钟)
3. API设计规范.md - 前端相关接口 (20分钟)
4. IP智能体快速开始 IP-AGENT-QUICKSTART.md (20分钟)
5. 项目任务清单.md - FE任务部分 (10分钟)
6. TODO-LIST.md - 前端待办任务 (10分钟)

**参考**:
- 数据安全方案.md - 前端安全规范章节
- 技术栈选型方案.md - 前端技术栈章节

---

### 后端开发工程师

**必读** (合计约3小时):
1. README.md (5分钟)
2. 快速启动指南.md (30分钟)
3. API设计规范.md (30分钟)
4. 数据库详细设计.md (40分钟)
5. 数据安全方案.md (30分钟)
6. IP智能体架构 IP-AGENT-ARCHITECTURE.md (30分钟)
7. 文化元素系统集成报告 (20分钟)
8. 项目任务清单.md - BE任务部分 (15分钟)
9. TODO-LIST.md - 后端待办任务 (15分钟)

**参考**:
- 开源项目参考与可扩展性架构分析.md - FastAPI最佳实践

---

### AI/算法工程师

**必读** (合计约3小时):
1. README.md (5分钟)
2. 快速启动指南.md (30分钟)
3. 项目主计划 - AI功能章节 (20分钟)
4. 双IP智能体架构 IP-AGENT-ARCHITECTURE.md (40分钟)
5. 文化元素智能匹配系统 (30分钟)
6. 品牌故事生成器集成报告 (20分钟)
7. 数据库详细设计.md - Neo4j/Qdrant章节 (30分钟)
8. 项目任务清单.md - AI任务部分 (10分钟)
9. TODO-LIST.md - AI优化任务 (10分钟)

**参考**:
- 技术栈选型方案.md - AI技术栈章节
- Prompt优化对比报告 PROMPT-COMPARISON-REPORT.md

---

### 测试工程师

**必读** (合计约1.5小时):
1. README.md (5分钟)
2. 快速启动指南.md (30分钟)
3. API设计规范.md - 接口定义 (20分钟)
4. 文化系统测试报告 CULTURAL-SYSTEM-TEST-REPORT.md (20分钟)
5. 项目任务清单.md - 测试任务部分 (10分钟)
6. TODO-LIST.md - 测试待办任务 (10分钟)

**参考**:
- 测试策略文档 testing/test-plan.md

---

### 数据采集/运营人员

**必读** (合计约1.5小时):
1. README.md (5分钟)
2. 项目分析报告.md - 数据采集章节 (30分钟)
3. 数据库详细设计.md - 产品表设计 (20分钟)
4. 项目任务清单.md - 数据采集任务 (10分钟)
5. 数据安全方案.md - 合规要求章节 (20分钟)

---

## 🔍 按需快速查找

### 我想了解...

| 问题 | 推荐文档 | 章节 |
|------|----------|------|
| 项目是什么？ | README.md | 项目简介 |
| 当前有哪些待办任务？ | TODO-LIST.md | 全文 |
| 如何开始开发？ | 快速启动指南.md | 全文 |
| 12周实施计划？ | 00-PROJECT-MASTER-PLAN.md | 全文 |
| 有哪些任务？ | 项目任务清单.md | 任务分解表 |
| 用什么技术栈？ | 技术栈选型方案.md | 全文 |
| API怎么设计？ | API设计规范.md | 全文 |
| 数据库怎么设计？ | 数据库详细设计.md | 全文 |
| 如何部署？ | DOCKER_DEPLOYMENT.md | 全文 |
| 如何保证安全？ | 数据安全方案.md | 全文 |
| 双IP智能体如何工作？ | IP-AGENT-ARCHITECTURE.md | 全文 |
| 如何集成IP智能体？ | IP-AGENT-QUICKSTART.md | 前端集成章节 |
| 文化元素如何匹配？ | CULTURAL-SYSTEM-INTEGRATION-REPORT.md | 智能匹配算法 |
| 如何生成品牌故事？ | BRAND-STORY-INTEGRATION-REPORT.md | API使用示例 |
| 如何批量生成内容？ | BE-008-多模态素材管理系统.md | 批量任务API |

---

### 常用命令速查

| 操作 | 命令 |
|------|------|
| 启动前端 | `cd frontend && pnpm dev` |
| 启动后端 | `cd backend && uvicorn app.main:app --reload` |
| 启动Docker | `docker compose -f docker-compose.dev.yml up -d` |
| 运行测试 | `cd backend && pytest` |
| 格式化代码 | `npm run format` / `black .` |
| 类型检查 | `npm run typecheck` / `mypy .` |

详细命令参考: [快速启动指南.md](planning/快速启动指南.md)

---

## 📅 文档维护计划

### 定期更新

| 文档 | 更新频率 | 负责人 |
|------|----------|--------|
| README.md | 每月 | 项目经理 |
| 项目任务清单.md | 每周 | 项目经理 |
| API设计规范.md | 按需 | 后端负责人 |
| 数据库设计.md | 按需 | 后端负责人 |

### 版本记录

| 版本 | 日期 | 主要变更 |
|------|------|---------|
| V1.0 | [项目日期] | 初始版本，完成项目分析 |
| V2.0 | [项目完成日期] | 补充P0级设计文档，创建项目目录结构 |

---

## 💡 使用建议

### 如何高效使用文档

1. **先总后分**: 从README开始，再深入具体文档
2. **按需阅读**: 根据角色和任务选择性阅读
3. **关注更新**: 定期查看文档更新日志
4. **提出问题**: 通过Issue反馈文档问题
5. **贡献内容**: 遇到新问题及时补充文档

### 文档编写规范

1. **Markdown格式**: 使用标准Markdown语法
2. **清晰标题**: 使用层级标题结构
3. **代码示例**: 提供可执行的代码示例
4. **图表说明**: 复杂概念配图说明
5. **版本标注**: 标注文档版本和更新日期

---

## 📞 文档反馈

如果您发现文档有以下问题，请及时反馈：

- ❌ 内容错误或过时
- 📝 表述不清或有歧义
- 🔍 缺少关键信息
- 💡 有更好的组织方式

**反馈方式**:
- 提交Issue: [GitHub Issues](https://github.com/your-repo/issues)
- 邮箱: b150w4942@163.com
- 项目群讨论

---

## 🎉 总结

当前项目文档体系已基本完善，包含：

✅ **30+份核心文档** (32万+字)
✅ **完整的12周实施计划** (00-PROJECT-MASTER-PLAN.md)
✅ **清晰的待办任务清单** (TODO-LIST.md)
✅ **P0级设计文档全部完成** (API、数据库、安全)
✅ **双IP智能体完整文档** (架构、快速开始、实施总结)
✅ **文化元素系统文档** (智能匹配、知识图谱)
✅ **内容生成工具链文档** (品牌故事、批量任务)
✅ **完整的项目目录结构**
✅ **清晰的阅读路径**

**项目进度**: Phase 2 完成 (85%), Phase 3 进行中

后续重点：
- 🔴 IP智能体前端集成 (Week 2)
- 🔴 支付系统生产对接 (P0)
- 🔴 告警通知系统实现 (P0)
- 🟡 补充API文档 (IP智能体、文化元素等)
- 🟡 用户使用手册编写

---

*文档导航最后更新: 2026-06-16*
