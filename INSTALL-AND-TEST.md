# 安装和测试指南

本指南帮助你快速部署和测试P1修复后的系统。

---

## 快速开始

### 1. 环境准备

**系统要求**:
- Python 3.10+
- Node.js 18+
- MySQL 8.0+
- Redis 6.0+

**检查环境**:
```bash
python --version    # 应显示 3.10+
node --version      # 应显示 v18+
mysql --version     # 应显示 8.0+
redis-cli --version # 应显示 6.0+
```

---

### 2. 后端部署

**步骤1: 进入后端目录**:
```bash
cd backend
```

**步骤2: 创建虚拟环境**:
```bash
python -m venv venv

# Windows
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate
```

**步骤3: 安装依赖**:
```bash
pip install -r requirements.txt
```

**步骤4: 配置环境变量**:
```bash
# 复制示例文件
copy .env.example .env  # Windows
# 或
cp .env.example .env    # Linux/Mac

# 编辑 .env 文件
# 必须修改的配置:
# - SECRET_KEY (生成32位随机字符串)
# - DEEPSEEK_API_KEY (如果使用AI功能)
# - DATABASE_URL (数据库连接)
# - REDIS_HOST (Redis地址)
```

**生成SECRET_KEY**:
```python
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

**步骤5: 初始化数据库**:
```bash
# 创建数据库
mysql -u root -p
CREATE DATABASE agri_platform CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
exit

# 运行迁移
alembic upgrade head

# 验证表结构
mysql -u root -p agri_platform
SHOW TABLES;
DESCRIBE users;
DESCRIBE products;
exit
```

**步骤6: 启动服务**:
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**验证**: 访问 http://localhost:8000/docs 查看API文档

---

### 3. 前端部署

**步骤1: 进入前端目录**:
```bash
cd frontend
```

**步骤2: 安装依赖**:
```bash
npm install
```

**步骤3: 配置环境变量**:
```bash
# 复制示例文件
copy .env.example .env.development  # Windows
# 或
cp .env.example .env.development    # Linux/Mac

# 默认配置应该可以直接使用
```

**步骤4: 启动开发服务器**:
```bash
npm run dev
```

**验证**: 访问 http://localhost:5173

---

## P1修复验证测试

### 1. 自动化测试

**运行P1修复验证脚本**:
```bash
cd backend
python test_p1_fixes.py
```

**预期输出**:
```
============================================================
P1 修复验证测试套件
============================================================

测试 1: 模块导入验证
✓ Redis客户端模块导入成功
✓ 验证码服务模块导入成功
✓ 通用Schema模块导入成功
✓ 管理员权限依赖导入成功

测试 2: 密码验证规则
✓ 合法密码通过: Password123!
✓ 合法密码通过: Test@2026Abc
✓ 不合法密码正确拒绝: password (缺少大写字母和数字)
...

通过: 4/4

🎉 所有测试通过！P1修复验证成功！
```

---

### 2. 手动功能测试

#### 测试1: 用户注册（新密码规则）

**请求**:
```bash
curl -X POST http://localhost:8000/api/v1/auth/send-code \
  -H "Content-Type: application/json" \
  -d '{"identifier": "test@example.com", "code_type": "register"}'

curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "email": "test@example.com",
    "password": "Test123!@#",
    "user_type": "personal",
    "verification_code": "查看控制台日志获取"
  }'
```

**预期**: 注册成功，返回用户信息

**测试密码规则**:
- ❌ `password` - 缺少大写字母、数字、特殊字符
- ❌ `Pass123` - 缺少特殊字符
- ✅ `Pass123!` - 符合规则

---

#### 测试2: 验证码功能

**图片验证码**:
```bash
# 浏览器访问
http://localhost:8000/api/v1/auth/captcha?session_id=test123
```

**预期**: 返回PNG图片

**邮箱验证码**:
```bash
curl -X POST "http://localhost:8000/api/v1/auth/send-code?identifier=test@example.com&code_type=register"
```

**预期**: 返回成功，查看后端日志可看到验证码

---

#### 测试3: 管理员权限

**准备**: 先创建管理员用户
```sql
-- 在数据库中更新用户为管理员
UPDATE users SET role = 'ADMIN' WHERE username = 'testuser';
```

**测试非管理员创建产品**:
```bash
# 普通用户登录
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "normaluser", "password": "Pass123!"}'

# 尝试创建产品（应失败 403）
curl -X POST http://localhost:8000/api/v1/products \
  -H "Authorization: Bearer {普通用户token}" \
  -H "Content-Type: application/json" \
  -d '{"name": "测试产品", ...}'
```

**预期**: 返回 403 Forbidden

**测试管理员创建产品**:
```bash
# 管理员登录
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "testuser", "password": "Pass123!"}'

# 创建产品（应成功）
curl -X POST http://localhost:8000/api/v1/products \
  -H "Authorization: Bearer {管理员token}" \
  -H "Content-Type: application/json" \
  -d '{
    "sku": "TEST001",
    "name": "内蒙古草原牛肉",
    "category": "肉类",
    "price": 199.0,
    "region": "内蒙古",
    "description": "优质草原牛肉"
  }'
```

**预期**: 创建成功，返回产品信息

---

#### 测试4: Redis故障容错

**停止Redis**:
```bash
# Windows
net stop Redis

# Linux
sudo systemctl stop redis
```

**测试登录**:
```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "testuser", "password": "Pass123!"}'
```

**预期**: 
- ✅ 登录成功（Token生成不依赖Redis）
- ⚠️ Token黑名单功能降级（查看日志有警告）

**测试验证码**:
```bash
curl -X POST "http://localhost:8000/api/v1/auth/send-code?identifier=test@example.com&code_type=register"
```

**预期**: 返回503错误，提示"验证码服务暂时不可用"

**重启Redis**:
```bash
# Windows
net start Redis

# Linux
sudo systemctl start redis
```

**验证恢复**:
```bash
# 再次测试验证码
curl -X POST "http://localhost:8000/api/v1/auth/send-code?identifier=test@example.com&code_type=register"
```

**预期**: 验证码发送成功

---

#### 测试5: 分页参数统一

**测试产品列表**:
```bash
# 测试默认分页
curl http://localhost:8000/api/v1/products

# 测试自定义分页
curl "http://localhost:8000/api/v1/products?page=2&page_size=10"

# 测试边界值（应失败）
curl "http://localhost:8000/api/v1/products?page=0&page_size=10"
curl "http://localhost:8000/api/v1/products?page=1&page_size=200"
```

**预期**:
- 默认: page=1, page_size=20
- 自定义: 返回第2页，每页10条
- page=0: 422验证错误
- page_size=200: 422验证错误（最大100）

---

### 3. 前端测试

**启动前端**:
```bash
cd frontend
npm run dev
```

**测试流程**:
1. 访问 http://localhost:5173
2. 点击"注册"
3. 填写信息，测试新密码规则
4. 查看密码提示信息
5. 提交注册
6. 测试登录
7. 访问产品列表
8. 测试AI对话

---

## 常见问题

### Q1: Redis连接失败
**错误**: `Redis connection failed`

**解决**:
1. 确认Redis服务运行: `redis-cli ping`
2. 检查`.env`中的`REDIS_HOST`和`REDIS_PORT`
3. 查看防火墙设置

### Q2: 数据库连接失败
**错误**: `Can't connect to MySQL server`

**解决**:
1. 确认MySQL服务运行
2. 验证数据库已创建: `SHOW DATABASES;`
3. 检查`.env`中的`DATABASE_URL`

### Q3: 密码验证失败
**错误**: `密码必须包含至少一个大写字母`

**解决**: 使用符合新规则的密码，例如: `Password123!`

### Q4: 验证码未收到
**说明**: 当前为模拟发送，验证码会输出到后端日志

**查看**:
```bash
# 查看后端控制台输出
[模拟发送邮件] To: test@example.com, Code: 123456, Type: register
```

---

## 性能测试

### 使用Apache Bench

**安装**:
```bash
# Windows: 下载Apache HTTP Server
# Linux: sudo apt install apache2-utils
```

**测试登录性能**:
```bash
# 创建测试数据文件 login.json
echo '{"username":"testuser","password":"Pass123!"}' > login.json

# 并发测试
ab -n 100 -c 10 -p login.json -T application/json \
   http://localhost:8000/api/v1/auth/login
```

**测试产品查询性能**:
```bash
ab -n 1000 -c 50 http://localhost:8000/api/v1/products
```

---

## 日志查看

**后端日志**:
- 控制台输出
- 或配置日志文件: `logs/app.log`

**查看关键日志**:
```bash
# Windows PowerShell
Get-Content logs/app.log -Tail 50

# Linux
tail -f logs/app.log
```

**关注的日志信息**:
- `Redis连接成功`
- `数据库表初始化成功`
- `DeepSeek API 状态: 正常`
- `[模拟发送邮件]` - 验证码信息

---

## 下一步

测试通过后:
1. ✅ 标记P1修复为完成
2. ⏳ 部署到测试环境
3. ⏳ 进行Beta测试
4. ⏳ 修复P2轻微缺陷

---

**更新日期**: [项目完成日期]
