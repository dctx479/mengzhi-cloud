# 开发规范与工作流
## Development Standards & Workflow v1.0

**文档版本**: 1.0  
**创建日期**: 2026-06-11  
**强制执行**: Sprint 1 Day 1起

---

## 一、代码规范

### 1.1 Python代码规范

**遵循PEP 8**:
```python
# 导入顺序
import os  # 标准库
import sys

from fastapi import FastAPI  # 第三方库
from sqlalchemy import create_engine

from app.models import User  # 本地模块
from app.services import UserService


# 命名规范
class UserService:  # 类名: PascalCase
    def get_user_by_id(self, user_id: int):  # 方法: snake_case
        MAX_RETRY = 3  # 常量: UPPER_SNAKE_CASE
        user_name = "test"  # 变量: snake_case
        return user


# 类型注解（强制）
def create_user(name: str, age: int) -> User:
    pass


# 文档字符串
def calculate_price(quantity: int, unit_price: float) -> float:
    """计算总价格
    
    Args:
        quantity: 数量
        unit_price: 单价
    
    Returns:
        总价格
    
    Raises:
        ValueError: 当数量或单价为负数时
    """
    if quantity < 0 or unit_price < 0:
        raise ValueError("数量和单价必须为正数")
    return quantity * unit_price
```

**禁止事项**:
```python
# ❌ 禁止裸except
try:
    do_something()
except:  # 太宽泛
    pass

# ✅ 正确做法
try:
    do_something()
except ValueError as e:
    logger.error(f"Value error: {e}")
    raise


# ❌ 禁止可变默认参数
def append_item(item, items=[]):  # 危险！
    items.append(item)
    return items

# ✅ 正确做法
def append_item(item, items=None):
    if items is None:
        items = []
    items.append(item)
    return items


# ❌ 禁止硬编码敏感信息
api_key = "sk-ant-xxxxx"  # 危险！

# ✅ 正确做法
api_key = os.getenv("ANTHROPIC_API_KEY")
```

### 1.2 TypeScript代码规范

**ESLint配置**:
```json
{
  "extends": [
    "plugin:vue/vue3-recommended",
    "@vue/typescript/recommended",
    "prettier"
  ],
  "rules": {
    "no-console": "warn",
    "no-debugger": "error",
    "@typescript-eslint/explicit-function-return-type": "warn",
    "vue/multi-word-component-names": "error"
  }
}
```

**命名规范**:
```typescript
// 接口: PascalCase, 前缀I
interface IUser {
  id: number
  name: string
}

// 类型别名: PascalCase
type UserRole = 'admin' | 'user'

// 组件: PascalCase
export default defineComponent({
  name: 'MessageItem'
})

// 变量/函数: camelCase
const userName = 'test'
function getUserById(id: number): IUser | null {
  return null
}

// 常量: UPPER_SNAKE_CASE
const MAX_RETRY_COUNT = 3
```

### 1.3 SQL规范

```sql
-- 表名: snake_case, 复数形式
CREATE TABLE users (
  id BIGSERIAL PRIMARY KEY,
  user_name VARCHAR(50) NOT NULL,  -- 字段名: snake_case
  created_at TIMESTAMP DEFAULT NOW()
);

-- 索引命名: idx_{表名}_{字段名}
CREATE INDEX idx_users_user_name ON users(user_name);

-- 外键命名: fk_{表名}_{关联表}
ALTER TABLE orders ADD CONSTRAINT fk_orders_users 
  FOREIGN KEY (user_id) REFERENCES users(id);
```

---

## 二、Git工作流

### 2.1 分支策略

```
master/main (生产环境，保护分支)
    ↑
  develop (开发主分支，保护分支)
    ↑
  ├─ feature/ip-chat (功能分支)
  ├─ feature/knowledge-graph
  ├─ bugfix/login-error (Bug修复)
  └─ hotfix/critical-security (紧急修复)
```

**分支命名规范**:
- `feature/{功能名}`: 新功能开发
- `bugfix/{问题描述}`: Bug修复
- `hotfix/{紧急问题}`: 生产环境紧急修复
- `refactor/{重构内容}`: 代码重构
- `test/{测试内容}`: 测试相关

### 2.2 Commit规范

**格式**: `<type>(<scope>): <subject>`

**类型（type）**:
- `feat`: 新功能
- `fix`: Bug修复
- `docs`: 文档更新
- `style`: 代码格式（不影响功能）
- `refactor`: 重构
- `test`: 测试
- `chore`: 构建/工具配置

**示例**:
```bash
git commit -m "feat(ip-agent): 实现小数对话功能"
git commit -m "fix(api): 修复IP切换时上下文丢失问题"
git commit -m "docs(readme): 更新部署说明"
git commit -m "test(ip-agent): 添加小数Agent单元测试"
```

**禁止提交**:
```bash
# ❌ 太模糊
git commit -m "update"
git commit -m "fix bug"

# ❌ 包含敏感信息
git commit -m "add API key: sk-ant-xxxxx"
```

### 2.3 Pull Request流程

**1. 创建PR前自检**:
```bash
# 代码格式化
black backend/
npm run lint --fix

# 运行测试
pytest backend/tests/
npm run test

# 类型检查
mypy backend/
npx tsc --noEmit
```

**2. PR标题**: 遵循Commit规范
```
feat(ip-agent): 实现小数对话功能
```

**3. PR描述模板**:
```markdown
## 变更内容
简要描述本次PR的变更

## 变更类型
- [ ] 新功能
- [ ] Bug修复
- [ ] 代码重构
- [ ] 文档更新

## 测试
- [ ] 已添加单元测试
- [ ] 已添加集成测试
- [ ] 手动测试通过

## 截图（如果涉及UI变更）
粘贴截图

## 相关Issue
Closes #123

## Checklist
- [ ] 代码遵循规范
- [ ] 已更新文档
- [ ] 测试覆盖率≥60%
- [ ] 通过CI检查
```

**4. Code Review要点**:
- 功能正确性
- 代码可读性
- 性能考虑
- 安全问题
- 测试覆盖

**5. 合并要求**:
- ≥1人Approve
- CI通过（测试+Lint）
- 无冲突

---

## 三、开发环境配置

### 3.1 必装工具

**后端开发**:
```bash
# Python 3.11
python --version  # 3.11+

# Poetry（依赖管理）
curl -sSL https://install.python-poetry.org | python3 -
poetry --version

# 开发工具
pip install black mypy pylint pytest pytest-asyncio pytest-cov
```

**前端开发**:
```bash
# Node.js 20+
node --version  # 20+
npm --version

# 全局工具
npm install -g @vue/cli vite typescript
```

### 3.2 IDE配置

**VS Code推荐插件**:
```json
{
  "recommendations": [
    "ms-python.python",
    "ms-python.vscode-pylance",
    "Vue.volar",
    "dbaeumer.vscode-eslint",
    "esbenp.prettier-vscode",
    "ms-azuretools.vscode-docker"
  ]
}
```

**VS Code配置**:
```json
{
  "editor.formatOnSave": true,
  "python.linting.enabled": true,
  "python.linting.pylintEnabled": true,
  "python.formatting.provider": "black",
  "[typescript]": {
    "editor.defaultFormatter": "esbenp.prettier-vscode"
  }
}
```

### 3.3 环境变量管理

**开发环境**:
```bash
# backend/.env.dev
DATABASE_URL=postgresql://localhost:5432/mengzhi_dev
REDIS_URL=redis://localhost:6379/0
ANTHROPIC_API_KEY=sk-ant-dev-xxxxx
DEBUG=True
LOG_LEVEL=DEBUG
```

**测试环境**:
```bash
# backend/.env.test
DATABASE_URL=postgresql://localhost:5432/mengzhi_test
ANTHROPIC_API_KEY=sk-ant-test-xxxxx
DEBUG=False
LOG_LEVEL=INFO
```

**.env文件管理**:
```bash
# .gitignore
.env
.env.*
!.env.example  # 模板文件可提交

# .env.example（提供给团队参考）
DATABASE_URL=postgresql://localhost:5432/mengzhi
ANTHROPIC_API_KEY=your_api_key_here
```

---

## 四、日志规范

### 4.1 日志级别

| 级别 | 用途 | 示例 |
|-----|------|------|
| DEBUG | 详细调试信息 | 变量值、函数调用栈 |
| INFO | 正常业务流程 | 用户登录、订单创建 |
| WARNING | 警告（不影响功能） | 缓存未命中、重试 |
| ERROR | 错误（影响功能） | API调用失败、数据库连接断开 |
| CRITICAL | 严重错误（系统级） | 数据库崩溃、内存溢出 |

### 4.2 日志格式

```python
import logging
import structlog

# 结构化日志配置
structlog.configure(
    processors=[
        structlog.stdlib.add_log_level,
        structlog.stdlib.add_logger_name,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.JSONRenderer()
    ]
)

logger = structlog.get_logger()

# 使用示例
logger.info(
    "user_login",
    user_id=123,
    username="test",
    ip="192.168.1.1"
)

logger.error(
    "llm_call_failed",
    error=str(e),
    model="claude-sonnet-4",
    retry_count=3
)
```

**日志输出**:
```json
{
  "event": "user_login",
  "level": "info",
  "timestamp": "2026-06-11T10:30:00.123Z",
  "user_id": 123,
  "username": "test",
  "ip": "192.168.1.1"
}
```

### 4.3 敏感信息脱敏

```python
def mask_sensitive_data(data: dict) -> dict:
    """脱敏敏感字段"""
    sensitive_fields = ['password', 'api_key', 'secret', 'token']
    
    masked = data.copy()
    for field in sensitive_fields:
        if field in masked:
            masked[field] = "***MASKED***"
    
    return masked

# 使用
logger.info("api_call", params=mask_sensitive_data(params))
```

---

## 五、错误处理规范

### 5.1 异常处理

```python
# ❌ 错误做法
try:
    result = do_something()
except:
    pass  # 吞掉所有错误


# ✅ 正确做法
from app.exceptions import BusinessException

try:
    result = do_something()
except ValueError as e:
    logger.error("Invalid value", error=str(e))
    raise BusinessException(
        code="INVALID_VALUE",
        message="参数值无效",
        details={"error": str(e)}
    )
except Exception as e:
    logger.critical("Unexpected error", error=str(e), exc_info=True)
    raise
```

### 5.2 自定义异常

```python
# app/exceptions.py

class BusinessException(Exception):
    """业务异常基类"""
    def __init__(self, code: str, message: str, details: dict = None):
        self.code = code
        self.message = message
        self.details = details or {}
        super().__init__(message)


class ResourceNotFoundException(BusinessException):
    """资源不存在"""
    def __init__(self, resource: str, resource_id: int):
        super().__init__(
            code="RESOURCE_NOT_FOUND",
            message=f"{resource} not found",
            details={"resource": resource, "id": resource_id}
        )


class QuotaExceededException(BusinessException):
    """配额超限"""
    def __init__(self, resource_type: str, limit: int):
        super().__init__(
            code="QUOTA_EXCEEDED",
            message=f"{resource_type} quota exceeded",
            details={"resource_type": resource_type, "limit": limit}
        )
```

### 5.3 全局异常处理

```python
# app/main.py

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

app = FastAPI()

@app.exception_handler(BusinessException)
async def business_exception_handler(request: Request, exc: BusinessException):
    return JSONResponse(
        status_code=400,
        content={
            "code": exc.code,
            "message": exc.message,
            "details": exc.details
        }
    )

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    logger.error("Unhandled exception", error=str(exc), exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "code": "INTERNAL_ERROR",
            "message": "Internal server error"
        }
    )
```

---

## 六、测试规范

### 6.1 测试文件组织

```
backend/tests/
├── conftest.py              # 全局fixtures
├── unit/
│   ├── test_ip_agent.py
│   └── test_kg_service.py
├── integration/
│   ├── test_api_auth.py
│   └── test_api_ip.py
└── e2e/
    └── test_user_flow.py
```

### 6.2 测试命名规范

```python
def test_create_user_success():
    """测试创建用户成功场景"""
    pass

def test_create_user_with_duplicate_email_should_fail():
    """测试重复邮箱创建用户应该失败"""
    pass

def test_get_user_by_id_not_found():
    """测试查询不存在的用户"""
    pass
```

### 6.3 测试覆盖率要求

```bash
# 运行测试并生成覆盖率报告
pytest --cov=app --cov-report=html --cov-report=term

# 最低要求
# 总体覆盖率: ≥60%
# 核心模块覆盖率: ≥80% (ip_agent, kg_service)
```

---

## 七、文档规范

### 7.1 代码注释

**函数文档**:
```python
def generate_brand_story(
    product_name: str,
    origin: str,
    selling_points: List[str]
) -> str:
    """生成品牌故事
    
    使用Claude API生成融入草原文化元素的品牌故事。
    
    Args:
        product_name: 产品名称，如"锡林郭勒羊肉"
        origin: 产地名称，如"锡林郭勒"
        selling_points: 产品卖点列表
    
    Returns:
        300-500字的品牌故事文本
    
    Raises:
        QuotaExceededException: 当用户配额不足时
        LLMCallException: 当LLM调用失败时
    
    Example:
        >>> story = generate_brand_story(
        ...     "锡林郭勒羊肉",
        ...     "锡林郭勒",
        ...     ["草原散养", "肉质紧实"]
        ... )
        >>> len(story) >= 300
        True
    """
    pass
```

**接口文档**:
```python
from fastapi import APIRouter
from pydantic import BaseModel, Field

router = APIRouter()

class CreateUserRequest(BaseModel):
    """创建用户请求"""
    username: str = Field(..., min_length=3, max_length=50, description="用户名")
    email: str = Field(..., description="邮箱")
    password: str = Field(..., min_length=6, description="密码")

@router.post("/users", summary="创建用户", tags=["用户管理"])
async def create_user(request: CreateUserRequest):
    """
    创建新用户
    
    - **username**: 用户名，3-50个字符
    - **email**: 邮箱地址，必须唯一
    - **password**: 密码，至少6个字符
    
    返回创建的用户信息（不含密码）
    """
    pass
```

### 7.2 README文档

**项目根目录README.md**:
```markdown
# 蒙智云 - AI营销赋能平台

## 快速开始

### 环境要求
- Python 3.11+
- Node.js 20+
- PostgreSQL 15+
- Redis 7+

### 安装依赖
\`\`\`bash
# 后端
cd backend
poetry install

# 前端
cd frontend
npm install
\`\`\`

### 启动开发服务器
\`\`\`bash
# 后端
docker-compose up -d postgres redis
cd backend
uvicorn app.main:app --reload

# 前端
cd frontend
npm run dev
\`\`\`

### 运行测试
\`\`\`bash
# 后端
pytest backend/tests/

# 前端
npm run test
\`\`\`

## 文档
- [开发路线图](docs/project-planning/03-DEVELOPMENT-ROADMAP.md)
- [API文档](http://localhost:8000/docs)
- [技术架构](docs/project-planning/02-TECHNICAL-ARCHITECTURE.md)

## 贡献指南
参见 [CONTRIBUTING.md](CONTRIBUTING.md)

## 许可证
MIT
```

---

## 八、会议与沟通

### 8.1 Daily Standup（每日站会）

**时间**: 每天上午10:00，15分钟
**参会人员**: 全体开发人员

**内容**:
1. 昨天完成了什么？
2. 今天计划做什么？
3. 遇到什么阻塞？

**记录模板**:
```
Daily Standup - 2026-06-11

张三：
- 昨天：完成了IP Agent路由逻辑
- 今天：实现小数Agent Prompt
- 阻塞：无

李四：
- 昨天：设计了对话页面UI
- 今天：对接后端API
- 阻塞：需要后端提供Mock数据
```

### 8.2 Sprint Planning（冲刺规划）

**时间**: 每个Sprint开始前，2小时
**输出**: Sprint Backlog（任务看板）

### 8.3 Sprint Retrospective（回顾会议）

**时间**: 每个Sprint结束后，1小时

**议程**:
1. What went well?（做得好的）
2. What went wrong?（需要改进的）
3. Action items（下个Sprint改进措施）

---

## 九、验收标准

### 9.1 Definition of Done（完成定义）

一个任务要标记为"完成"，必须满足:
- [ ] 功能实现正确
- [ ] 代码通过Lint检查
- [ ] 单元测试覆盖率≥60%
- [ ] 集成测试通过
- [ ] Code Review通过（≥1人Approve）
- [ ] 文档已更新
- [ ] 无遗留TODO/FIXME

### 9.2 PR合并检查清单

- [ ] CI通过（测试+Lint+构建）
- [ ] 代码覆盖率未下降
- [ ] 无安全漏洞（Bandit/ESLint扫描）
- [ ] API文档已更新（如有接口变更）
- [ ] 性能无明显退化

---

**文档结束**

> 开发规范是保证代码质量的基础，所有成员必须严格遵守。
