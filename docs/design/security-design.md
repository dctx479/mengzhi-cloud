# 数据安全方案

> **文档版本**: v1.0  
> **更新日期**: [项目完成日期]  
> **适用项目**: 内蒙古农畜产品品牌营销AI赋能云平台

---

## 目录

1. [安全架构概述](#1-安全架构概述)
2. [敏感数据分类](#2-敏感数据分类)
3. [加密策略](#3-加密策略)
4. [访问控制](#4-访问控制)
5. [安全检查清单](#5-安全检查清单)
6. [合规要求](#6-合规要求)

---

## 1. 安全架构概述

### 1.1 纵深防御架构

### 1.2 零信任原则

- **始终验证**: 每次请求都进行身份验证和授权检查
- **最小权限**: 用户和服务只获得完成任务所需的最小权限
- **假设被入侵**: 设计时假设网络已被渗透，实施多层防护

---

## 2. 敏感数据分类

### 2.1 数据分级标准

| 等级 | 分类 | 数据示例 | 存储要求 | 传输要求 |
|------|------|----------|----------|----------|
| L1 | 极敏感 | 密码、API密钥、支付信息 | AES-256加密 | TLS 1.3 |
| L2 | 敏感 | 手机号、邮箱、身份证号 | 加密或脱敏 | TLS 1.2+ |
| L3 | 内部 | 昵称、头像、浏览记录 | 明文存储 | HTTPS |
| L4 | 公开 | 产品信息、文化介绍 | 明文存储 | HTTP可选 |

### 2.2 各表敏感字段标识

#### 2.2.1 users表

| 字段 | 敏感等级 | 处理方式 |
|------|----------|----------|
| password_hash | L1 | bcrypt加密存储 |
| phone | L2 | 展示时脱敏(138****8000) |
| email | L2 | 展示时脱敏(zh***@example.com) |
| wechat_openid | L2 | 原文存储，不对外暴露 |
| douyin_openid | L2 | 原文存储，不对外暴露 |
| last_login_ip | L3 | 原文存储 |
| user_uuid | L3 | 对外使用，代替内部ID |
| nickname | L3 | 原文存储 |
| avatar_url | L4 | 原文存储 |

#### 2.2.2 enterprises表

| 字段 | 敏感等级 | 处理方式 |
|------|----------|----------|
| license_no | L2 | 展示时部分脱敏 |
| contact_phone | L2 | 展示时脱敏 |
| contact_email | L2 | 展示时脱敏 |
| license_image_url | L2 | 访问需鉴权 |
| name | L3 | 原文存储 |
| address | L3 | 原文存储 |

#### 2.2.3 AI相关表

| 表名 | 字段 | 敏感等级 | 处理方式 |
|------|------|----------|----------|
| ai_conversations | context_data | L3 | JSON加密可选 |
| ai_messages | content | L3 | 原文存储 |
| content_records | input_params | L3 | 原文存储 |
| content_records | generated_content | L3 | 原文存储 |

---

## 3. 加密策略

### 3.1 传输层加密

| 配置项 | 值 | 说明 |
|--------|-----|------|
| 最低版本 | TLS 1.2 | 禁用TLS 1.0/1.1 |
| 推荐版本 | TLS 1.3 | 优先使用 |
| 证书类型 | RSA 2048 | Lets Encrypt证书 |
| HSTS | max-age=31536000 | 强制HTTPS |

### 3.2 存储层加密

#### 3.2.1 密码加密

- 算法: bcrypt
- Cost Factor: 12
- 用途: 用户密码存储

#### 3.2.2 敏感数据加密

- 算法: AES-256-GCM  
- Nonce: 96-bit随机
- 用途: L1级敏感数据

#### 3.2.3 API签名

- 算法: HMAC-SHA256
- 用途: API请求防篡改

### 3.3 密钥管理

| 密钥类型 | 存储位置 | 轮换周期 |
|----------|----------|----------|
| JWT签名密钥 | 环境变量 | 90天 |
| 数据加密密钥 | KMS | 180天 |
| 数据库密码 | 配置中心 | 30天 |

---

## 4. 访问控制

### 4.1 RBAC权限模型

#### 4.1.1 角色定义

| 角色 | 代码 | 说明 | 权限范围 |
|------|------|------|----------|
| 系统管理员 | admin | 平台管理员 | 全部权限 |
| 企业管理员 | enterprise_admin | 企业管理者 | 企业内全部权限 |
| 企业成员 | enterprise_user | 企业普通成员 | 企业内操作权限 |
| 个人用户 | personal_user | 个人注册用户 | 个人数据权限 |
| 访客 | guest | 未登录用户 | 公开数据只读 |

#### 4.1.2 权限矩阵

| 资源 | admin | enterprise_admin | enterprise_user | personal_user |
|------|-------|------------------|-----------------|---------------|
| 用户管理 | CRUD | R(企业内) | - | R(自己) |
| 企业管理 | CRUD | RU(自己企业) | R | - |
| 产品管理 | CRUD | CRUD(企业内) | CRU | CRUD(自己) |
| 内容生成 | CRUD | CRUD(企业内) | CRUD | CRUD(自己) |
| AI对话 | CRUD | CRUD(企业内) | CRUD | CRUD(自己) |
| 数据分析 | R(全部) | R(企业内) | R(自己) | R(自己) |
| 系统配置 | CRUD | - | - | - |

**权限说明**: C=创建, R=读取, U=更新, D=删除

### 4.2 多租户隔离

- 所有业务数据通过 enterprise_id 字段进行租户隔离
- 查询时自动注入租户过滤条件
- 跨租户访问需要特殊授权

### 4.3 API访问控制

| 接口 | 方法 | 需要认证 | 需要权限 |
|------|------|----------|----------|
| /api/v1/auth/login | POST | 否 | - |
| /api/v1/auth/register | POST | 否 | - |
| /api/v1/users/profile | GET | 是 | user:read:self |
| /api/v1/products | GET | 否 | product:read |
| /api/v1/products | POST | 是 | product:create |
| /api/v1/content/generate | POST | 是 | content:create |
| /api/v1/chat/send | POST | 是 | chat:create |
| /api/v1/admin/* | * | 是 | admin:* |

---

## 5. 安全检查清单

### 5.1 输入验证

#### 5.1.1 SQL注入防护

- 使用参数化查询（SQLAlchemy ORM）
- 禁止拼接SQL字符串
- 对动态表名/列名使用白名单

```python
# 正确方式 - 参数化查询
from sqlalchemy import text

result = db.execute(
    text("SELECT * FROM users WHERE username = :username"),
    {"username": user_input}
)

# 错误方式 - 字符串拼接（禁止）
# result = db.execute(f"SELECT * FROM users WHERE username = '{user_input}'")
```

#### 5.1.2 XSS防护

- 输出时进行HTML转义
- 使用Content-Security-Policy头
- 对富文本使用白名单过滤

```python
import html
from markupsafe import escape

def safe_output(user_content: str) -> str:
    return html.escape(user_content)

# CSP响应头配置
CSP_HEADER = "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'"
```

#### 5.1.3 CSRF防护

- API使用JWT认证（无状态，天然防CSRF）
- 表单提交使用CSRF Token
- 验证Referer/Origin头

#### 5.1.4 文件上传安全

| 检查项 | 实现方式 |
|--------|----------|
| 文件类型验证 | 白名单检查MIME类型和扩展名 |
| 文件大小限制 | 最大10MB |
| 文件名处理 | 重命名为UUID，去除路径字符 |
| 存储隔离 | 上传目录与代码目录分离 |
| 病毒扫描 | ClamAV扫描（可选） |

```python
import uuid
import magic
from pathlib import Path

ALLOWED_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.gif', '.pdf'}
ALLOWED_MIMES = {'image/jpeg', 'image/png', 'image/gif', 'application/pdf'}
MAX_SIZE = 10 * 1024 * 1024  # 10MB

def validate_upload(file) -> tuple:
    # 检查大小
    if file.size > MAX_SIZE:
        return False, "File too large"
    
    # 检查扩展名
    ext = Path(file.filename).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        return False, "Invalid file type"
    
    # 检查MIME类型
    mime = magic.from_buffer(file.read(1024), mime=True)
    file.seek(0)
    if mime not in ALLOWED_MIMES:
        return False, "Invalid file content"
    
    return True, None

def save_upload(file) -> str:
    ext = Path(file.filename).suffix.lower()
    new_filename = f"{uuid.uuid4()}{ext}"
    # 保存到隔离的上传目录
    return new_filename
```

### 5.2 敏感词过滤

```python
import re
from typing import List

class SensitiveFilter:
    def __init__(self, word_file: str):
        with open(word_file, 'r', encoding='utf-8') as f:
            self.words = set(line.strip() for line in f)
        self.pattern = re.compile('|'.join(map(re.escape, self.words)))
    
    def contains_sensitive(self, text: str) -> bool:
        return bool(self.pattern.search(text))
    
    def filter_text(self, text: str, replacement: str = '***') -> str:
        return self.pattern.sub(replacement, text)
    
    def get_sensitive_words(self, text: str) -> List[str]:
        return self.pattern.findall(text)

# 使用示例
filter = SensitiveFilter('/path/to/sensitive_words.txt')
if filter.contains_sensitive(user_input):
    raise ValueError("Content contains sensitive words")
```

### 5.3 限流配置

| 接口类型 | 限流策略 | 说明 |
|----------|----------|------|
| 登录接口 | 5次/分钟/IP | 防暴力破解 |
| 注册接口 | 3次/分钟/IP | 防批量注册 |
| 验证码接口 | 1次/分钟/手机号 | 防滥用 |
| AI对话接口 | 60次/分钟/用户 | 按配额控制 |
| 内容生成接口 | 20次/分钟/用户 | 按配额控制 |
| 通用API | 100次/分钟/用户 | 防滥用 |

```python
from fastapi import Request, HTTPException
import redis

redis_client = redis.Redis()

async def rate_limit(request: Request, key_prefix: str, limit: int, window: int = 60):
    # 构建限流key
    if request.user:
        key = f"rate:{key_prefix}:user:{request.user.id}"
    else:
        key = f"rate:{key_prefix}:ip:{request.client.host}"
    
    # 增加计数
    current = redis_client.incr(key)
    if current == 1:
        redis_client.expire(key, window)
    
    if current > limit:
        raise HTTPException(status_code=429, detail="Too many requests")
```

### 5.4 审计日志

#### 5.4.1 需要记录的操作

| 操作类型 | 记录内容 |
|----------|----------|
| 用户登录 | 用户ID、IP、设备、时间、结果 |
| 用户登出 | 用户ID、时间 |
| 密码修改 | 用户ID、时间、IP |
| 权限变更 | 操作者、目标用户、变更内容 |
| 数据导出 | 用户ID、导出内容、时间 |
| 敏感数据访问 | 用户ID、访问内容、时间 |
| 管理员操作 | 所有管理员操作 |

#### 5.4.2 日志格式

```python
import json
from datetime import datetime
from loguru import logger

def audit_log(
    action: str,
    user_id: str,
    resource: str,
    details: dict,
    ip: str,
    result: str = "success"
):
    log_entry = {
        "timestamp": datetime.utcnow().isoformat(),
        "action": action,
        "user_id": user_id,
        "resource": resource,
        "details": details,
        "ip": ip,
        "result": result
    }
    logger.bind(audit=True).info(json.dumps(log_entry, ensure_ascii=False))

# 使用示例
audit_log(
    action="user_login",
    user_id="user_123",
    resource="auth",
    details={"device": "Chrome/Windows", "method": "password"},
    ip="192.168.1.100",
    result="success"
)
```

### 5.5 数据脱敏

```python
import re

def mask_phone(phone: str) -> str:
    if not phone or len(phone) < 7:
        return phone
    return phone[:3] + '****' + phone[-4:]

def mask_email(email: str) -> str:
    if not email or '@' not in email:
        return email
    local, domain = email.rsplit('@', 1)
    if len(local) <= 2:
        masked_local = local[0] + '***'
    else:
        masked_local = local[:2] + '***'
    return f"{masked_local}@{domain}"

def mask_id_card(id_card: str) -> str:
    if not id_card or len(id_card) < 10:
        return id_card
    return id_card[:6] + '********' + id_card[-4:]

def mask_bank_card(card: str) -> str:
    if not card or len(card) < 8:
        return card
    return card[:4] + ' **** **** ' + card[-4:]

# 使用示例
print(mask_phone("13812345678"))  # 138****5678
print(mask_email("zhangsan@example.com"))  # zh***@example.com
print(mask_id_card("110101199001011234"))  # 110101********1234
```

---

## 6. 合规要求

### 6.1 个人信息保护法合规

#### 6.1.1 合规要点

| 要求 | 实现措施 |
|------|----------|
| 知情同意 | 注册时展示隐私政策，获取用户同意 |
| 最小必要 | 只收集业务必需的个人信息 |
| 目的明确 | 明确告知数据使用目的 |
| 存储期限 | 用户注销后30天内删除个人数据 |
| 数据安全 | 采用加密、脱敏等技术保护 |
| 用户权利 | 提供查询、更正、删除、导出功能 |
| 跨境传输 | 数据存储在境内服务器 |

#### 6.1.2 用户权利实现

```python
from fastapi import APIRouter, Depends
from datetime import datetime, timedelta

router = APIRouter()

@router.get("/api/v1/users/data-export")
async def export_user_data(current_user = Depends(get_current_user)):
    # 导出用户所有数据
    user_data = {
        "basic_info": get_user_basic_info(current_user.id),
        "products": get_user_products(current_user.id),
        "conversations": get_user_conversations(current_user.id),
        "content_records": get_user_content_records(current_user.id),
        "export_time": datetime.utcnow().isoformat()
    }
    return user_data

@router.delete("/api/v1/users/account")
async def delete_account(current_user = Depends(get_current_user)):
    # 软删除用户账号
    user = get_user(current_user.id)
    user.status = "deleted"
    user.deleted_at = datetime.utcnow()
    user.deletion_scheduled_at = datetime.utcnow() + timedelta(days=30)
    db.commit()
    
    # 30天后永久删除（定时任务）
    return {"message": "Account scheduled for deletion in 30 days"}
```

### 6.2 网络安全等级保护

#### 6.2.1 等保二级要求

本系统按照网络安全等级保护二级要求设计：

| 安全域 | 要求 | 实现措施 |
|--------|------|----------|
| 物理安全 | 机房安全 | 使用阿里云等保合规机房 |
| 网络安全 | 边界防护 | WAF、安全组、VPC隔离 |
| 主机安全 | 入侵防范 | 安骑士/云安全中心 |
| 应用安全 | 身份鉴别 | 双因素认证、强密码策略 |
| 数据安全 | 数据完整性 | 数据校验、备份恢复 |
| 安全管理 | 安全审计 | 操作日志、审计分析 |

#### 6.2.2 安全审计要求

- 审计日志保留180天以上
- 记录用户登录、操作、退出等关键行为
- 审计记录包含时间、用户、IP、操作内容、结果
- 审计记录防篡改（只追加、定期归档）

### 6.3 GDPR合规（如涉及海外用户）

| 要求 | 实现措施 |
|------|----------|
| 合法性基础 | 用户明确同意 |
| 数据最小化 | 只处理必要数据 |
| 存储限制 | 明确数据保留期限 |
| 数据主体权利 | 访问、更正、删除、可携带 |
| 数据保护官 | 指定DPO联系人 |
| 数据泄露通知 | 72小时内通知监管机构 |

### 6.4 AI内容安全

#### 6.4.1 内容审核流程

```
用户输入 -> 敏感词过滤 -> AI生成 -> 输出审核 -> 返回用户
              |                         |
              v                         v
          拒绝/提示                 过滤/警告
```

#### 6.4.2 AI安全措施

| 措施 | 说明 |
|------|------|
| Prompt注入防护 | 过滤恶意Prompt，限制系统指令修改 |
| 输出过滤 | 过滤敏感词、违规内容 |
| 内容标记 | AI生成内容添加标识 |
| 人工审核 | 高风险内容人工复核 |
| 用户举报 | 提供举报通道 |

```python
def safe_ai_generate(user_prompt: str, context: dict) -> str:
    # 1. 输入过滤
    if sensitive_filter.contains_sensitive(user_prompt):
        raise ValueError("Input contains prohibited content")
    
    # 2. Prompt注入检测
    if detect_prompt_injection(user_prompt):
        raise ValueError("Invalid input detected")
    
    # 3. AI生成
    response = call_ai_api(user_prompt, context)
    
    # 4. 输出过滤
    filtered_response = sensitive_filter.filter_text(response)
    
    # 5. 添加AI生成标记
    return f"{filtered_response}

[本内容由AI生成，仅供参考]"
```

---

## 7. 附录

### 7.1 安全配置检查表

| 检查项 | 状态 | 备注 |
|--------|------|------|
| TLS 1.2+已启用 | [ ] | 禁用低版本TLS |
| HSTS已配置 | [ ] | max-age>=31536000 |
| CSP已配置 | [ ] | 限制资源加载来源 |
| X-Frame-Options | [ ] | 防止点击劫持 |
| X-Content-Type-Options | [ ] | 禁止MIME嗅探 |
| 密码策略已实施 | [ ] | 8位+字母+数字 |
| bcrypt cost>=12 | [ ] | 密码加密强度 |
| JWT过期时间合理 | [ ] | Access 30min, Refresh 7day |
| 限流已配置 | [ ] | 各接口限流规则 |
| 审计日志已开启 | [ ] | 关键操作记录 |
| 数据备份已配置 | [ ] | 每日备份 |
| 敏感词库已更新 | [ ] | 定期更新 |
| 安全扫描已执行 | [ ] | 定期漏洞扫描 |

### 7.2 安全响应头配置

```nginx
# Nginx安全响应头配置
add_header X-Frame-Options "SAMEORIGIN" always;
add_header X-Content-Type-Options "nosniff" always;
add_header X-XSS-Protection "1; mode=block" always;
add_header Referrer-Policy "strict-origin-when-cross-origin" always;
add_header Content-Security-Policy "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data: https:; font-src 'self'; connect-src 'self' https://api.deepseek.com" always;
add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
```

### 7.3 安全事件响应流程

```
1. 检测 -> 2. 评估 -> 3. 响应 -> 4. 恢复 -> 5. 复盘
   |          |          |          |          |
   监控告警   影响范围   隔离止损   恢复服务   总结改进
   日志分析   严重程度   证据保全   验证正常   更新策略
   用户报告   通知决策   修复漏洞   用户通知   文档记录
```

### 7.4 联系方式

- **安全问题报告**: security@example.com
- **数据保护官(DPO)**: dpo@example.com
- **紧急安全事件**: 7x24值班电话

---

**文档版本**: v1.0  
**最后更新**: [项目完成日期]  
**维护者**: AI赋能云平台技术团队
