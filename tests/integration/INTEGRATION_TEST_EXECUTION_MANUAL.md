# 集成测试执行手册

## 📖 文档信息
- **版本**: 1.0
- **创建日期**: [项目完成日期]
- **适用人员**: 测试工程师、QA团队、开发人员
- **预计阅读时间**: 15分钟

---

## 🎯 手册目的

本手册提供**逐步指导**，帮助您快速上手并执行完整的集成测试。无论您是新手还是有经验的测试工程师，都能通过本手册高效完成测试工作。

---

## 📋 前置准备清单

### 环境要求
- [ ] Python 3.11+ 已安装
- [ ] Node.js 18+ 已安装
- [ ] MySQL 8.0 运行中
- [ ] Redis 7.0 运行中
- [ ] Git 已安装

### 软件依赖
- [ ] httpx (Python包)
- [ ] asyncio (Python包)
- [ ] curl (命令行工具)
- [ ] bash (Shell环境)

### 测试数据
- [ ] 测试用户已创建
- [ ] 测试产品已导入
- [ ] 数据库已初始化

---

## 🚀 第一次执行（30分钟）

### 步骤1: 克隆项目（5分钟）

```bash
# 如果还没有克隆项目
git clone <repository-url>
cd AI赋能云平台

# 检查测试文件
ls -la tests/integration/
```

**预期结果**:
```
✓ 看到8个.md文档
✓ 看到scripts/目录
✓ 看到reports/目录
```

### 步骤2: 安装依赖（10分钟）

#### 后端依赖
```bash
cd backend

# 创建虚拟环境
python -m venv venv

# 激活虚拟环境
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt

# 验证安装
python -c "import httpx; print('httpx installed')"
```

**预期结果**:
```
✓ 虚拟环境创建成功
✓ 所有依赖安装完成
✓ httpx可以导入
```

#### 前端依赖（可选）
```bash
cd frontend

# 安装依赖
npm install

# 验证安装
npm list vue
```

### 步骤3: 启动服务（5分钟）

#### 启动数据库服务
```bash
# 使用Docker Compose
cd backend
docker-compose up -d mysql redis

# 验证服务状态
docker-compose ps

# 应该看到mysql和redis都是Up状态
```

**预期结果**:
```
✓ MySQL运行在3306端口
✓ Redis运行在6379端口
```

#### 初始化数据库
```bash
cd backend

# 初始化数据库表
python scripts/init_db.py

# 导入测试数据
python scripts/seed_data.py
```

**预期结果**:
```
✓ 数据库表创建成功
✓ 测试数据导入成功
✓ 看到"1047个产品"的提示
```

#### 启动后端服务
```bash
cd backend

# 启动FastAPI服务
uvicorn app.main:app --reload --port 8000

# 在新终端验证
curl http://localhost:8000/health
```

**预期结果**:
```json
{
  "status": "healthy",
  "service": "agri-ai-platform",
  "timestamp": "[项目完成日期]T..."
}
```

#### 启动前端服务（可选）
```bash
cd frontend

# 启动开发服务器
npm run dev

# 在浏览器访问
# http://localhost:5173
```

### 步骤4: 执行测试（10分钟）

```bash
# 进入测试目录
cd tests/integration/scripts

# 执行所有测试
bash run_all_tests.sh
```

**预期输出**:
```
========================================
集成测试执行脚本
========================================

检查后端服务...
✓ 后端服务运行正常

检查前端服务...
✓ 前端服务运行正常

检查Python依赖...
✓ Python依赖已安装

========================================
执行API集成测试
========================================
✅ HEALTH-001: 根路径
✅ HEALTH-002: 健康检查
✅ AUTH-001-01: 正常注册
...

========================================
测试结果汇总
========================================
总用例数: 50
✅ 通过: 48
❌ 失败: 2
⏸️  跳过: 0
通过率: 96.00%
```

---

## 📊 日常测试流程（15分钟）

### 场景1: 测试特定模块

```bash
# 只测试认证模块
cd tests/integration/scripts
python test_api_integration.py --module auth

# 只测试产品模块
python test_api_integration.py --module products

# 只测试对话模块
python test_api_integration.py --module chat
```

### 场景2: 测试认证流程

```bash
# 执行完整认证流程测试
cd tests/integration/scripts
python test_auth_flow.py
```

**测试内容**:
- ✅ 用户注册
- ✅ 用户登录
- ✅ Token验证
- ✅ 访问受保护资源
- ✅ 权限控制
- ✅ 登出

### 场景3: 测试内容生成

```bash
# 执行内容生成测试
cd tests/integration/scripts
python test_content_generation.py
```

**测试内容**:
- ✅ 单次生成
- ✅ RAG生成
- ✅ 批量生成
- ✅ 内容评分
- ✅ 导出功能

---

## 🔍 手动测试指南

### 端到端测试场景1: 新用户注册登录

#### 步骤1: 访问首页
```
操作: 打开浏览器，访问 http://localhost:5173
验证:
  ✓ 页面正常加载
  ✓ 显示登录/注册按钮
  ✓ 显示产品列表
```

#### 步骤2: 注册新用户
```
操作: 点击"注册"按钮
输入:
  - 邮箱: test_manual_001@example.com
  - 用户名: ManualTest001
  - 密码: Test123!@#
  - 确认密码: Test123!@#

验证:
  ✓ 表单验证正常
  ✓ 注册成功提示
  ✓ 自动跳转到登录页
```

#### 步骤3: 登录
```
操作: 输入刚注册的账号密码
验证:
  ✓ 登录成功
  ✓ 显示用户名
  ✓ 可以访问用户中心
```

#### 步骤4: 浏览产品
```
操作: 点击产品列表中的产品
验证:
  ✓ 显示产品详情
  ✓ 显示产品图片
  ✓ 显示文化标签
  ✓ 显示"AI咨询"按钮
```

#### 步骤5: 退出登录
```
操作: 点击"退出登录"
验证:
  ✓ 退出成功
  ✓ 跳转到登录页
  ✓ 无法访问用户中心
```

**记录结果**:
```
测试场景: 新用户注册登录流程
执行时间: [项目完成日期] 10:30
执行人: [您的姓名]
结果: ✅ 通过 / ❌ 失败
问题: [如有问题，详细描述]
```

---

## 🐛 问题排查指南

### 问题1: 后端服务无法启动

**症状**:
```
ERROR: Could not connect to MySQL
```

**解决方案**:
```bash
# 1. 检查MySQL是否运行
docker-compose ps

# 2. 如果未运行，启动MySQL
docker-compose up -d mysql

# 3. 检查数据库连接配置
cat backend/.env | grep DATABASE

# 4. 测试数据库连接
mysql -h localhost -u root -p
```

### 问题2: 测试失败 - 401 Unauthorized

**症状**:
```
❌ AUTH-002-01: 正常登录
   状态码 401
```

**解决方案**:
```bash
# 1. 检查测试用户是否存在
cd backend
python -c "
from app.database import SessionLocal
from app.models.user import User
db = SessionLocal()
user = db.query(User).filter_by(email='test@example.com').first()
print(f'User exists: {user is not None}')
"

# 2. 如果用户不存在，重新导入数据
python scripts/seed_data.py

# 3. 重新执行测试
cd tests/integration/scripts
python test_auth_flow.py
```

### 问题3: DeepSeek API调用失败

**症状**:
```
❌ CHAT-001-01: 新对话
   DeepSeek API error
```

**解决方案**:
```bash
# 1. 检查API密钥
echo $DEEPSEEK_API_KEY

# 2. 如果未设置，添加到.env
cd backend
echo "DEEPSEEK_API_KEY=sk-your-key-here" >> .env

# 3. 重启后端服务
# Ctrl+C 停止服务
uvicorn app.main:app --reload --port 8000

# 4. 测试API连接
curl -X POST http://localhost:8000/api/v1/chat/message \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"content":"测试"}'
```

### 问题4: 测试脚本权限错误

**症状**:
```
bash: ./run_all_tests.sh: Permission denied
```

**解决方案**:
```bash
# 添加执行权限
chmod +x tests/integration/scripts/run_all_tests.sh

# 重新执行
bash tests/integration/scripts/run_all_tests.sh
```

### 问题5: Python模块导入错误

**症状**:
```
ModuleNotFoundError: No module named 'httpx'
```

**解决方案**:
```bash
# 1. 确认虚拟环境已激活
which python
# 应该显示venv路径

# 2. 如果未激活，激活虚拟环境
cd backend
source venv/bin/activate  # Linux/Mac
# 或
venv\Scripts\activate  # Windows

# 3. 安装缺失的模块
pip install httpx

# 4. 验证安装
python -c "import httpx; print('OK')"
```

---

## 📈 测试报告生成

### 自动生成报告

测试脚本会自动生成JSON格式的报告：

```bash
# 报告位置
tests/reports/

# 查看最新报告
ls -lt tests/reports/ | head -5

# 查看报告内容
cat tests/reports/api_test_results_20260117_103000.json
```

**报告格式**:
```json
{
  "timestamp": "[项目完成日期]T10:30:00",
  "results": {
    "total": 50,
    "passed": 48,
    "failed": 2,
    "skipped": 0,
    "errors": [
      "AUTH-004-01: Token刷新功能异常"
    ]
  }
}
```

### 手动生成报告

使用报告模板生成完整报告：

```bash
# 1. 复制模板
cp tests/reports/INTEGRATION_TEST_REPORT_TEMPLATE.md \
   tests/reports/integration_test_report_20260117.md

# 2. 编辑报告，填写实际数据
vim tests/reports/integration_test_report_20260117.md

# 3. 替换占位符
# - YYYY-MM-DD → 实际日期
# - [姓名] → 您的姓名
# - X/Y/Z → 实际数字
```

---

## 📝 测试记录模板

### 每日测试记录

```markdown
# 测试记录 - [项目完成日期]

## 基本信息
- 测试人员: [姓名]
- 测试时间: 10:00 - 11:30
- 测试环境: 开发环境
- 测试版本: v1.0

## 测试执行
- [ ] API集成测试
- [ ] 认证流程测试
- [ ] 内容生成测试
- [ ] 端到端测试

## 测试结果
- 总用例数: 50
- 通过数: 48
- 失败数: 2
- 通过率: 96%

## 发现的问题
1. Bug #001: Token刷新功能异常
   - 严重程度: P1
   - 描述: 使用refresh_token刷新时返回500错误
   - 复现步骤: [详细步骤]
   - 截图: [附件]

2. Bug #002: 批量删除部分失败
   - 严重程度: P2
   - 描述: 批量删除100个产品时，3个失败
   - 复现步骤: [详细步骤]

## 备注
- DeepSeek API偶尔超时，需要重试
- 测试数据需要定期清理
```

---

## 🎓 最佳实践

### 测试前
1. ✅ 检查所有服务是否运行
2. ✅ 确认测试数据已准备
3. ✅ 清理上次测试的临时数据
4. ✅ 备份重要数据

### 测试中
1. ✅ 按照文档逐步执行
2. ✅ 记录每个步骤的结果
3. ✅ 截图保存证据
4. ✅ 详细记录错误信息

### 测试后
1. ✅ 生成测试报告
2. ✅ 提交Bug报告
3. ✅ 清理测试数据
4. ✅ 归档测试记录

---

## 🔄 持续改进

### 每周
- 📊 审查测试结果
- 📊 更新测试用例
- 📊 优化测试脚本
- 📊 培训团队成员

### 每月
- 📈 分析测试趋势
- 📈 评估测试覆盖率
- 📈 改进测试流程
- 📈 更新测试文档

### 每季度
- 🎯 制定测试目标
- 🎯 评估测试效果
- 🎯 引入新工具
- 🎯 优化测试策略

---

## 📞 获取帮助

### 文档资源
- 📖 快速参考: `INTEGRATION_TEST_QUICK_REFERENCE.md`
- 📖 文件索引: `INTEGRATION_TEST_FILE_INDEX.md`
- 📖 测试计划: `INTEGRATION_TEST_PLAN.md`

### 常见问题
- ❓ 查看各文档的"常见问题"章节
- ❓ 搜索项目Issue
- ❓ 查看测试日志

### 技术支持
- 💬 联系测试负责人
- 💬 提交Issue
- 💬 查看项目Wiki

---

## ✅ 检查清单

### 测试前检查
- [ ] MySQL运行正常
- [ ] Redis运行正常
- [ ] 后端服务启动
- [ ] 前端服务启动（如需要）
- [ ] 测试数据已准备
- [ ] Python依赖已安装

### 测试执行检查
- [ ] 所有测试脚本可执行
- [ ] 测试结果正确记录
- [ ] 错误信息详细记录
- [ ] 截图证据已保存

### 测试后检查
- [ ] 测试报告已生成
- [ ] Bug已提交
- [ ] 测试数据已清理
- [ ] 测试记录已归档

---

**手册版本**: 1.0
**最后更新**: [项目完成日期]
**维护人**: [姓名]

**祝测试顺利！** 🎉
