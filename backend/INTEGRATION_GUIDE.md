"""
认证API集成指南

版本: 1.0
更新日期: [项目完成日期]

本文档提供认证模块的完整集成说明和使用示例
"""

# ==================== 1. 项目结构 ====================

"""
backend/app/
├── core/
│   ├── __init__.py
│   ├── config.py           # 应用配置
│   ├── errors.py          # 错误码和异常定义 ✓ 已生成
│   └── responses.py       # 统一响应格式 ✓ 已生成
├── api/
│   ├── __init__.py        # API模块初始化 ✓ 已生成
│   ├── auth.py            # 认证路由（8个端点） ✓ 已生成
│   └── deps.py            # 依赖注入和中间件 ✓ 已生成
├── schemas/
│   ├── __init__.py        # Schema模块初始化 ✓ 已生成
│   └── auth.py            # 认证Schema定义 ✓ 已生成
├── services/
│   ├── __init__.py        # Service模块初始化 ✓ 已生成
│   └── auth_service.py    # 认证业务逻辑 ✓ 已生成
├── __init__.py
└── main.py                # 应用入口 ✓ 已更新
"""

# ==================== 2. API端点概览 ====================

"""
已实现的8个认证端点:

1. POST /api/v1/auth/register
   - 用户注册
   - 支持个人用户和企业用户
   - 需要验证码验证
   - 返回: 201 Created

2. POST /api/v1/auth/login
   - 用户登录
   - 支持用户名/邮箱/手机号登录
   - 返回Access Token和Refresh Token
   - 返回: 200 OK

3. POST /api/v1/auth/refresh
   - 刷新Token
   - 使用Refresh Token获取新的Access Token
   - 旧Refresh Token加入黑名单
   - 返回: 200 OK

4. POST /api/v1/auth/logout
   - 用户登出
   - 将Token加入黑名单
   - 返回: 200 OK

5. GET /api/v1/auth/me
   - 获取当前用户信息
   - 需要Valid Access Token
   - 返回脱敏的用户信息
   - 返回: 200 OK

6. PUT /api/v1/auth/me
   - 更新用户信息
   - 支持更新昵称、头像、性别
   - 需要Valid Access Token
   - 返回: 200 OK

7. POST /api/v1/auth/change-password
   - 修改密码
   - 需要验证旧密码
   - 需要Valid Access Token
   - 返回: 200 OK

8. POST /api/v1/auth/reset-password
   - 重置密码（忘记密码）
   - 需要验证码验证
   - 不需要登录
   - 返回: 200 OK
"""

# ==================== 3. 依赖包列表 ====================

"""
# requirements.txt

# FastAPI框架
fastapi==0.104.1
uvicorn[standard]==0.24.0

# 数据库
sqlalchemy==2.0.23
pymysql==1.1.0

# 认证
pyjwt==2.8.1
bcrypt==4.1.1

# 缓存
redis==5.0.1

# 数据验证
pydantic==2.5.0
pydantic-settings==2.1.0
email-validator==2.1.0

# 日志
loguru==0.7.2

# 工具
python-dotenv==1.0.0
"""

# ==================== 4. 环境配置 ====================

"""
# .env 文件示例

# 应用配置
DEBUG=True
APP_NAME="内蒙古农畜产品AI平台"

# 数据库
DATABASE_URL=mysql+pymysql://root:root123@localhost:3306/agri_platform?charset=utf8mb4

# Redis
REDIS_URL=redis://localhost:6379/0

# JWT
SECRET_KEY=your-256-bit-secret-key-change-in-production-at-least-32-chars-long-string
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# CORS
CORS_ORIGINS=["http://localhost:5173", "http://127.0.0.1:5173"]

# DeepSeek API
DEEPSEEK_API_KEY=sk-xxxxx
DEEPSEEK_API_BASE=https://api.deepseek.com
"""

# ==================== 5. 使用示例 ====================

"""
# ===================== Python/requests示例 =====================

import requests
from typing import Dict

BASE_URL = "http://localhost:8000/api/v1"

# 1. 用户注册
def register_user():
    url = f"{BASE_URL}/auth/register"
    payload = {
        "username": "zhangsan",
        "email": "zhangsan@example.com",
        "phone": "13800138000",
        "password": "Password123",
        "user_type": "enterprise",
        "verification_code": "123456",
        "enterprise_name": "内蒙古草原牧业有限公司",
        "enterprise_license": "91150100MA0N1234X5"
    }
    response = requests.post(url, json=payload)
    print(response.json())
    # 返回:
    # {
    #     "code": 200,
    #     "message": "注册成功",
    #     "data": {...}
    # }


# 2. 用户登录
def login_user():
    url = f"{BASE_URL}/auth/login"
    payload = {
        "username": "zhangsan",
        "password": "Password123"
    }
    response = requests.post(url, json=payload)
    data = response.json()

    if data["code"] == 200:
        tokens = data["data"]["tokens"]
        access_token = tokens["access_token"]
        refresh_token = tokens["refresh_token"]
        return access_token, refresh_token
    return None, None


# 3. 获取当前用户信息
def get_current_user(access_token: str):
    url = f"{BASE_URL}/auth/me"
    headers = {
        "Authorization": f"Bearer {access_token}"
    }
    response = requests.get(url, headers=headers)
    print(response.json())


# 4. 刷新Token
def refresh_token(refresh_token: str):
    url = f"{BASE_URL}/auth/refresh"
    payload = {
        "refresh_token": refresh_token
    }
    response = requests.post(url, json=payload)
    data = response.json()

    if data["code"] == 200:
        new_tokens = data["data"]
        return new_tokens["access_token"], new_tokens["refresh_token"]
    return None, None


# 5. 修改密码
def change_password(access_token: str):
    url = f"{BASE_URL}/auth/change-password"
    headers = {
        "Authorization": f"Bearer {access_token}"
    }
    payload = {
        "old_password": "Password123",
        "new_password": "NewPassword456"
    }
    response = requests.post(url, json=payload, headers=headers)
    print(response.json())


# 6. 用户登出
def logout(access_token: str):
    url = f"{BASE_URL}/auth/logout"
    headers = {
        "Authorization": f"Bearer {access_token}"
    }
    response = requests.post(url, headers=headers)
    print(response.json())


# ===================== JavaScript/fetch示例 =====================

const BASE_URL = 'http://localhost:8000/api/v1';

// 1. 用户登录
async function login(username, password) {
    const response = await fetch(`${BASE_URL}/auth/login`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            username: username,
            password: password
        })
    });

    const data = await response.json();
    if (data.code === 200) {
        const tokens = data.data.tokens;
        // 存储tokens
        localStorage.setItem('access_token', tokens.access_token);
        localStorage.setItem('refresh_token', tokens.refresh_token);
        return tokens;
    }
    throw new Error(data.message);
}

// 2. 获取当前用户信息
async function getCurrentUser() {
    const token = localStorage.getItem('access_token');
    const response = await fetch(`${BASE_URL}/auth/me`, {
        headers: {
            'Authorization': `Bearer ${token}`
        }
    });

    const data = await response.json();
    if (data.code === 200) {
        return data.data;
    }
    throw new Error(data.message);
}

// 3. 刷新Token
async function refreshToken() {
    const token = localStorage.getItem('refresh_token');
    const response = await fetch(`${BASE_URL}/auth/refresh`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            refresh_token: token
        })
    });

    const data = await response.json();
    if (data.code === 200) {
        localStorage.setItem('access_token', data.data.access_token);
        localStorage.setItem('refresh_token', data.data.refresh_token);
        return data.data;
    }
    throw new Error(data.message);
}

// 4. 登出
async function logout() {
    const token = localStorage.getItem('access_token');
    await fetch(`${BASE_URL}/auth/logout`, {
        method: 'POST',
        headers: {
            'Authorization': `Bearer ${token}`
        }
    });

    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
}

// 5. API请求拦截器（自动刷新Token）
async function apiRequest(url, options = {}) {
    let token = localStorage.getItem('access_token');

    options.headers = options.headers || {};
    options.headers['Authorization'] = `Bearer ${token}`;

    let response = await fetch(url, options);

    // 如果返回401，尝试刷新Token
    if (response.status === 401) {
        try {
            await refreshToken();
            token = localStorage.getItem('access_token');
            options.headers['Authorization'] = `Bearer ${token}`;
            response = await fetch(url, options);
        } catch (error) {
            // 刷新失败，重定向到登录页
            window.location.href = '/login';
        }
    }

    return response;
}
"""

# ==================== 6. 错误处理 ====================

"""
所有错误都会返回以下格式:

{
    "code": 错误码,
    "message": "错误消息",
    "data": null,
    "errors": [
        {
            "field": "字段名",
            "message": "字段错误消息"
        }
    ],
    "timestamp": "[项目完成日期]T10:00:00",
    "request_id": "uuid-v4"
}

常见错误码:
- 10001: 参数验证失败
- 20001: Token缺失
- 20003: Token已过期
- 20010: 用户不存在
- 20011: 密码错误
- 20012: 账号已禁用
- 20013: 账号已锁定
- 40011: 记录已存在（用户已注册）
- 50001: 内部服务器错误

客户端应该:
1. 检查code值
2. 如果是20003（Token过期），尝试刷新Token
3. 如果刷新失败或收到20001，重定向到登录页
"""

# ==================== 7. 安全建议 ====================

"""
1. Token存储:
   - Web应用: 使用HttpOnly Cookie（最安全）
   - 如必须用localStorage: 确保已实施XSS防护
   - Mobile应用: 使用系统Keychain/Keystore

2. 密码策略:
   - 最小8位，包含字母和数字
   - 建议使用多因素认证

3. HTTPS:
   - 生产环境必须使用HTTPS
   - 启用HSTS头

4. CORS配置:
   - 只允许信任的域名
   - 避免使用通配符*

5. 速率限制:
   - 登录接口: 5次/分钟/IP
   - 注册接口: 3次/分钟/IP

6. 审计日志:
   - 记录所有登录/登出事件
   - 记录敏感操作
"""

# ==================== 8. 常见问题 ====================

"""
Q1: Token过期了怎么办?
A: 使用refresh_token调用/api/v1/auth/refresh获取新的access_token

Q2: 忘记密码怎么办?
A: 调用/api/v1/auth/reset-password，需要提供验证码

Q3: 账号被锁定了怎么办?
A: 账号在5次失败登录后会被锁定30分钟，请稍后再试

Q4: 如何在多设备上保持登录?
A: 建议为每个设备生成不同的device_id，这样可以同时在多个设备上登录

Q5: 刷新Token时原来的Token会失效吗?
A: 是的，旧的refresh_token会被加入黑名单，需要使用新的tokens
"""
