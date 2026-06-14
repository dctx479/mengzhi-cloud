# 项目启动检查清单
## Project Kickoff Checklist

**文档版本**: 1.0  
**创建日期**: 2026-06-11  
**适用场景**: Sprint 1启动前必须完成的准备工作

---

## 📋 总览

本检查清单确保项目启动前所有必要条件已就绪。**所有标记为[必须]的项目必须在Sprint 1 Day 1前完成**。

**完成进度**: 0/25 项

---

## 一、团队与组织 (0/5)

### 1.1 人员到位
- [ ] [必须] 项目负责人确定并签署项目承诺书
- [ ] [必须] 后端工程师到位（至少1人）
- [ ] [必须] 前端工程师到位（至少1人）
- [ ] [推荐] AI工程师到位
- [ ] [推荐] 产品/测试人员到位

**负责人**: [项目负责人]  
**截止时间**: Sprint 1 Day 1

### 1.2 角色分工
- [ ] [必须] 制作团队通讯录（姓名、角色、联系方式）
- [ ] [必须] 明确各角色职责边界
- [ ] [推荐] 制定团队协作规范

**负责人**: [项目负责人]  
**截止时间**: Week 1

---

## 二、技术环境 (0/8)

### 2.1 开发工具
- [ ] [必须] 所有成员安装IDE（VS Code/PyCharm/WebStorm）
- [ ] [必须] 安装Git并配置SSH Key
- [ ] [必须] 安装Docker Desktop
- [ ] [必须] 安装Postman/Insomnia（API测试）
- [ ] [推荐] 安装Redis Client（RedisInsight）
- [ ] [推荐] 安装数据库客户端（DBeaver/pgAdmin）

**负责人**: [技术负责人]  
**截止时间**: Sprint 1 Day 1

### 2.2 账号与权限
- [ ] [必须] 申请Claude API Key（Anthropic账号）
  - 访问: https://console.anthropic.com
  - 创建API Key
  - 设置每月预算上限（建议$50）
  - **将Key保存到团队密码管理器**

- [ ] [必须] 购买云服务器（阿里云/腾讯云）
  - 配置: 2C4G，40GB SSD
  - 系统: Ubuntu 22.04 LTS
  - 开放端口: 22, 80, 443, 8000, 5173
  - **记录IP地址和SSH登录信息**

- [ ] [推荐] 申请域名（可选）
  - 域名: mengzhi.cloud 或类似
  - DNS解析到服务器IP

**负责人**: [技术负责人]  
**截止时间**: Week 1

### 2.3 代码仓库
- [ ] [必须] 创建Git仓库（GitHub/GitLab/Gitee）
  - 仓库名: mengzhi-cloud
  - 可见性: Private（开发阶段）
  - 添加所有成员为Collaborators

- [ ] [必须] 配置分支保护规则
  ```
  master/main 分支:
  - 禁止直接push
  - 要求Pull Request
  - 至少1人Code Review
  - CI通过后才能合并
  ```

- [ ] [必须] 创建初始目录结构
  ```
  mengzhi-cloud/
  ├── backend/          # 后端代码
  ├── frontend/         # 前端代码
  ├── docs/             # 文档（包含本规划文档）
  ├── scripts/          # 脚本工具
  ├── docker-compose.yml
  └── README.md
  ```

**负责人**: [技术负责人]  
**截止时间**: Sprint 1 Day 1

---

## 三、项目管理工具 (0/4)

### 3.1 项目管理平台
- [ ] [必须] 选择项目管理工具
  - 推荐: JIRA / Notion / 飞书项目
  - 创建项目空间
  - 添加所有成员

- [ ] [必须] 创建Sprint看板
  ```
  看板列:
  - Todo（待办）
  - In Progress（进行中）
  - Code Review（审查中）
  - Testing（测试中）
  - Done（已完成）
  ```

- [ ] [必须] 录入Sprint 1任务
  - 从 `03-DEVELOPMENT-ROADMAP.md` 提取任务
  - 拆分为可执行的子任务（每个≤1天）
  - 分配负责人
  - 设置优先级

**负责人**: [项目经理/产品经理]  
**截止时间**: Sprint 1 Day 1

### 3.2 沟通工具
- [ ] [必须] 创建团队沟通群
  - 微信群/钉钉群/飞书群
  - 命名: "蒙智云开发团队"
  - 固定群公告（会议时间、文档链接）

**负责人**: [项目负责人]  
**截止时间**: Sprint 1 Day 1

---

## 四、文档与规范 (0/5)

### 4.1 核心文档
- [ ] [必须] 确认所有团队成员已阅读以下文档
  - [ ] 00-PROJECT-MASTER-PLAN.md（项目总规划）
  - [ ] 03-DEVELOPMENT-ROADMAP.md（开发路线图）
  - [ ] 04-IP-AGENT-IMPLEMENTATION.md（IP智能体实施）
  - [ ] 06-API-SPECIFICATION.md（API接口规范）

**负责人**: [项目负责人]  
**截止时间**: Week 1

### 4.2 开发规范
- [ ] [必须] 制定Git Commit规范
  ```
  格式: <type>(<scope>): <subject>
  
  示例:
  feat(ip-agent): 实现小数对话功能
  fix(api): 修复IP切换时上下文丢失
  docs(readme): 更新部署说明
  test(ip-agent): 添加小数Agent单元测试
  
  type类型:
  - feat: 新功能
  - fix: Bug修复
  - docs: 文档
  - test: 测试
  - refactor: 重构
  - style: 代码格式
  - chore: 构建/工具配置
  ```

- [ ] [推荐] 制定Code Review规范
  - Review重点: 功能正确性、代码可读性、安全性
  - Review时间: 提交PR后24小时内
  - 至少1人Approve才能合并

**负责人**: [技术负责人]  
**截止时间**: Week 1

---

## 五、基础设施搭建 (0/3)

### 5.1 开发环境
- [ ] [必须] 使用Docker Compose启动本地开发环境
  ```bash
  # 克隆仓库
  git clone <repo_url>
  cd mengzhi-cloud
  
  # 启动所有服务
  docker compose up -d
  
  # 验证服务
  curl http://localhost:8000/health  # 后端
  curl http://localhost:5173         # 前端
  ```

- [ ] [必须] 配置环境变量
  ```bash
  # backend/.env
  ANTHROPIC_API_KEY=sk-ant-xxxxx
  DATABASE_URL=postgresql://user:pass@localhost:5432/mengzhi
  REDIS_URL=redis://localhost:6379/0
  SECRET_KEY=<生成随机密钥>
  
  # frontend/.env
  VITE_API_BASE_URL=http://localhost:8000
  ```

- [ ] [必须] 初始化数据库
  ```bash
  cd backend
  alembic upgrade head
  python scripts/init_data.py  # 插入测试数据
  ```

**负责人**: [后端工程师]  
**截止时间**: Sprint 1 Day 2

---

## 六、第一次会议 (0/1)

### 6.1 Sprint 1 Planning会议
- [ ] [必须] 召开Sprint 1规划会议（2小时）

**会议议程**:
```
1. 项目背景与目标回顾（15分钟）
   - 项目负责人讲解项目定位、价值
   - 回顾12周路线图

2. Sprint 1目标与任务（30分钟）
   - 明确Sprint 1目标: IP智能体MVP上线
   - 逐一讲解任务卡片
   - 确认任务优先级

3. 任务认领与工作量估算（45分钟）
   - 团队成员认领任务
   - 估算工作量（人日）
   - 识别依赖关系

4. 技术方案讨论（20分钟）
   - IP Agent架构设计
   - Prompt设计策略
   - LLM调用与缓存

5. 风险识别与应对（10分钟）
   - 识别潜在风险
   - 制定应对措施

6. Q&A与行动计划（10分钟）
```

**会议输出**:
- Sprint 1任务看板（已分配）
- 风险清单
- 下一次会议时间（Daily Standup）

**负责人**: [项目负责人]  
**时间**: Sprint 1 Day 1下午

---

## 七、验收标准

### ✅ 完成标准

**必须项全部完成（13/13）**:
- 团队成员到位并明确分工
- 开发工具全部安装
- Claude API Key已申请
- 代码仓库已创建并配置
- 项目管理工具已搭建
- 核心文档已阅读
- Git Commit规范已制定
- 开发环境已启动
- 数据库已初始化
- Sprint 1 Planning会议已召开

**推荐项完成（≥5/12）**:
- AI工程师、产品/测试人员到位
- 团队协作规范已制定
- Redis Client、数据库客户端已安装
- 域名已申请
- Code Review规范已制定
- ...

### 🚀 启动信号

当满足以下条件时，项目正式启动：

```
✅ 所有[必须]项完成
✅ Sprint 1 Planning会议结束
✅ 至少3人开始执行Sprint 1任务
✅ 第一次Daily Standup已召开
```

---

## 八、常见问题FAQ

### Q1: Claude API Key如何申请？
**A**: 
1. 访问 https://console.anthropic.com
2. 注册账号（需要国外手机号或邮箱）
3. 进入API Keys页面，点击"Create Key"
4. 复制API Key，**妥善保存**（只显示一次）
5. 设置预算上限（Settings → Billing）

### Q2: 开发环境启动失败怎么办？
**A**:
```bash
# 检查Docker是否运行
docker ps

# 查看日志
docker compose logs

# 常见问题:
# 1. 端口被占用 → 修改docker-compose.yml端口映射
# 2. 内存不足 → 关闭其他应用，增加Docker内存限制
# 3. 网络问题 → 配置镜像加速器
```

### Q3: Git分支策略是什么？
**A**:
```
master/main     - 生产环境（保护分支）
    ↑
  develop       - 开发主分支（保护分支）
    ↑
  feature/*     - 功能分支（开发者创建）
  bugfix/*      - Bug修复分支
  hotfix/*      - 紧急修复分支

工作流:
1. 从develop创建feature分支
2. 开发完成后提交PR到develop
3. Code Review通过后合并
4. 定期从develop合并到master发布
```

### Q4: 如何进行Code Review？
**A**:
```
提交者:
1. 完成功能开发并自测
2. 提交PR，填写PR描述
3. 请求至少1人Review

审查者:
1. 检查功能是否正确
2. 检查代码可读性
3. 检查是否有安全问题
4. 提出修改建议或Approve
5. 24小时内完成Review

合并:
- 至少1人Approve
- CI通过
- 无冲突
```

### Q5: 遇到技术问题怎么办？
**A**:
```
优先级排序:
1. 查文档（本规划文档 + 官方文档）
2. 搜索（Google + Stack Overflow）
3. 问团队（微信群/钉钉群）
4. 求助外部（GitHub Issue / 社区论坛）

技术栈支持渠道:
- FastAPI: https://fastapi.tiangolo.com
- Vue 3: https://vuejs.org
- Claude API: https://docs.anthropic.com
```

---

## 九、检查清单签字确认

| 角色 | 姓名 | 签字确认 | 日期 |
|-----|------|---------|------|
| 项目负责人 | | [ ] 已完成所有检查项 | |
| 技术负责人 | | [ ] 已完成技术环境搭建 | |
| 后端工程师 | | [ ] 已完成后端环境配置 | |
| 前端工程师 | | [ ] 已完成前端环境配置 | |

---

## 十、下一步行动

### 立即执行（今天）
1. [ ] 项目负责人召集团队成员，分发本检查清单
2. [ ] 每人认领检查项，设置完成时间
3. [ ] 建立每日进度跟踪机制

### 明天执行
1. [ ] 技术负责人带领团队搭建开发环境
2. [ ] 后端工程师初始化数据库
3. [ ] 前端工程师配置项目脚手架

### 本周内执行
1. [ ] 召开Sprint 1 Planning会议
2. [ ] 开始Sprint 1开发
3. [ ] 建立Daily Standup机制

---

**检查清单最后更新**: 2026-06-11  
**状态**: 🟡 待启动

> 💡 **重要提示**: 本检查清单是项目成功的第一步。请认真对待每一项，确保团队在统一的基础上启动项目。

> 📞 **如有疑问**: 请联系项目负责人 [待填写联系方式]