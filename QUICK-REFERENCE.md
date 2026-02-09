# 安全修复快速参考

## 快速开始

### 1. 生成密钥 (必须)

```bash
# 生成SECRET_KEY
python backend/scripts/generate_secret_key.py

# 输出示例:
# SECRET_KEY=BAuaXe2pOcUo9iLaNauvoxTPruLQ231gPObg04wK0KJVqnwO_m-Wuk44sQNcYPdE
```

### 2. 配置.env文件 (必须)

```env
# 复制生成的密钥到.env
SECRET_KEY=<从上面复制>

# 设置数据库密码
DATABASE_URL=mysql+pymysql://root:YOUR_PASSWORD@localhost:3306/agri_platform
```

### 3. 运行测试 (验证)

```bash
cd backend
python -m pytest tests/test_security_fixes.py -v
```

---

## 使用新功能

### 输入验证

```python
from app.core.input_validation import input_validator

# 验证用户名
valid, error = input_validator.validate_username("testuser")
if not valid:
    raise HTTPException(status_code=400, detail=error)

# 清理HTML（防XSS）
safe_text = input_validator.sanitize_html(user_input)
```

### 频率限制

```python
from app.api.deps_security import check_login_rate_limit

# 在路由中使用
@router.post("/login", dependencies=[Depends(check_login_rate_limit)])
async def login(request: LoginRequest):
    # 自动检查频率限制（5次/5分钟）
    pass
```

### 完整示例

```python
from fastapi import APIRouter, Depends
from app.api.deps_security import (
    check_login_rate_limit,
    validate_register_input
)

@router.post("/register")
async def register(request: RegisterRequest, db: Session):
    # 1. 验证输入
    validate_register_input(
        username=request.username,
        email=request.email,
        phone=request.phone,
        password=request.password
    )
    
    # 2. 业务逻辑
    # ...

@router.post("/login", dependencies=[Depends(check_login_rate_limit)])
async def login(request: LoginRequest, db: Session):
    # 自动频率限制
    # ...
```

---

## 常量使用

```python
from app.core.constants import (
    MAX_LOGIN_ATTEMPTS,
    LOGIN_LOCK_MINUTES,
    RATE_LIMIT_LOGIN_MAX_REQUESTS,
    RATE_LIMIT_LOGIN_WINDOW_SECONDS
)

# 使用常量代替魔法数字
if login_attempts >= MAX_LOGIN_ATTEMPTS:
    lock_until = datetime.utcnow() + timedelta(minutes=LOGIN_LOCK_MINUTES)
```

---

## 测试命令

```bash
# 运行安全测试
python -m pytest tests/test_security_fixes.py -v

# 运行所有测试
python -m pytest tests/ -v

# 查看覆盖率
python -m pytest tests/ --cov=app --cov-report=html
```

---

## 故障排除

### 问题: SECRET_KEY验证失败

```bash
# 错误: SECRET_KEY不能使用默认值
# 解决: 运行密钥生成脚本
python backend/scripts/generate_secret_key.py
```

### 问题: 频率限制不工作

```bash
# 检查Redis是否运行
redis-cli ping

# 如果Redis不可用，会自动降级到内存存储
```

### 问题: 输入验证太严格

```python
# 可以调整验证规则
# 编辑: backend/app/core/input_validation.py
```

---

## 文件位置

| 功能 | 文件路径 |
|------|---------|
| 密钥生成 | `backend/scripts/generate_secret_key.py` |
| 输入验证 | `backend/app/core/input_validation.py` |
| 频率限制 | `backend/app/core/rate_limiter.py` |
| 安全依赖 | `backend/app/api/deps_security.py` |
| 常量定义 | `backend/app/core/constants.py` |
| 安全测试 | `backend/tests/test_security_fixes.py` |

---

## 更多信息

- 完整修复报告: `FIX-SUMMARY.md`
- 安全设计文档: `docs/security-design.md`
- API文档: `docs/api/`
