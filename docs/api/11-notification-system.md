# 告警通知系统 API 文档

**版本**: v1.0  
**更新日期**: 2026-06-17  
**模块**: 统一告警通知（Unified Notification System）  
**基础路径**: 内部模块（不暴露 HTTP API，仅 `core.alerts.alert_manager`）

---

## 1. 模块概述

项目所有告警统一通过 `backend/app/core/alerts.py` 中的 `alert_manager` 实例发送。历史遗留的 `ai/monitor.py` 副本已重构为委托模式，所有调用方统一入口。

**支持的渠道**:
- 📧 **Email** (SMTP + TLS)
- 📱 **DingTalk** (Webhook + HMAC-SHA256 签名，可选)
- 📞 **SMS** (阿里云短信 API v3)

**核心特性**:
- 🎯 单一入口: `alert_manager.send_alert()`
- 🔁 频率限制: 同 `alert_key` 在 300s 内只发送一次
- 📊 渠道独立: 任一渠道失败不影响其他渠道
- 🛡️ 优雅降级: 凭证缺失时仅 `logger.warning`，不抛错
- 🏢 企业路由: 支持 `enterprise_id` 维度路由（钉钉 webhook 优先企业配置）

---

## 2. 公开 API

### 2.1 `alert_manager.send_alert()`

```python
from app.core.alerts import alert_manager

await alert_manager.send_alert(
    level="warning",          # info | warning | error | critical
    title="AI Provider 健康度下降",
    message="Provider deepseek 错误率 25%，超过警告阈值 10%",
    extra={
        "provider_id": 12,
        "error_rate": 25.3,
    },
    channels=["email", "dingtalk"],  # 可选；None 时按全局配置自动选择
    enterprise_id="ent_123",         # 可选；企业级路由
)
```

**参数**:

| 参数 | 类型 | 必填 | 默认 | 说明 |
|---|---|---|---|---|
| `level` | str | ✅ | - | 告警级别：info/warning/error/critical |
| `title` | str | ✅ | - | 告警标题（≤1000 字符，超长自动截断） |
| `message` | str | ✅ | - | 告警详情（≤1000 字符） |
| `extra` | dict | ❌ | None | 额外元数据（dict） |
| `channels` | list | ❌ | None | 显式指定渠道；None 时按全局开关自动选择 |
| `enterprise_id` | str | ❌ | None | 企业 ID（用于钉钉 webhook 企业级覆盖） |

**返回值**:

```python
{
    "email": True,        # 发送成功
    "dingtalk": False,    # 凭证缺失或发送失败
    "sms": True,          # ERROR/CRITICAL 才会触发 SMS
}
```

**频率限制**:
- `alert_key = f"{level}:{title}"`
- 同 key 在 `cooldown_period` (300s) 内只发送一次
- 冷却中调用仅 `logger.debug`，不实际发送

---

### 2.2 `get_alert_recipients(enterprise_id)`

```python
from app.core.alerts import get_alert_recipients

recipients = get_alert_recipients(enterprise_id="ent_123")
# {
#     "email": ["admin@example.com"],
#     "dingtalk": ["https://oapi.dingtalk.com/robot/send?access_token=..."],
#     "sms": ["13800138000"]
# }
```

**当前实现**: 全局配置（`monitoring_config`）。  
**未来扩展**: TenantConfig.alert_config 字段读取（接口已预留）。

---

## 3. 配置

所有渠道凭证通过 `backend/config/monitoring.py` 的 `MonitoringConfig` 读取，对应 `.env` 环境变量。

### 3.1 全局开关

```bash
ALERT_ENABLED=true
ALERT_EMAIL_ENABLED=true
ALERT_DINGTALK_ENABLED=true
ALERT_SMS_ENABLED=false   # 默认关闭，启用前请确保凭证完整
```

### 3.2 邮件 (Email)

```bash
ALERT_EMAIL_SMTP_HOST=smtp.example.com
ALERT_EMAIL_SMTP_PORT=587
ALERT_EMAIL_USERNAME=alert@example.com
ALERT_EMAIL_PASSWORD=your-password
ALERT_EMAIL_FROM=alert@example.com
ALERT_EMAIL_TO=["admin@example.com","ops@example.com"]
```

### 3.3 钉钉 (DingTalk)

```bash
# 必填：webhook URL（必须含 access_token）
ALERT_DINGTALK_WEBHOOK=https://oapi.dingtalk.com/robot/send?access_token=xxxxx

# 可选：加签密钥（启用后消息需带签名才能送达）
ALERT_DINGTALK_SECRET=SEC...
```

**签名机制**（可选）:
- HMAC-SHA256(`{timestamp}\n{secret}`) → base64
- URL: `{webhook}&timestamp={ts}&sign={sign}`
- 不配置 `ALERT_DINGTALK_SECRET` 时不签名（兼容旧版钉钉机器人）

### 3.4 短信 (SMS - 阿里云)

```bash
ALERT_SMS_PROVIDER=aliyun
ALERT_SMS_ACCESS_KEY=your-access-key-id
ALERT_SMS_SECRET_KEY=your-access-key-secret
ALERT_SMS_SIGN_NAME=your-sign-name   # 阿里云短信签名
ALERT_SMS_TEMPLATE_CODE=SMS_xxxxxx   # 阿里云短信模板 ID
ALERT_SMS_PHONES=["13800138000","13900139000"]
```

**API**: 阿里云短信 v3 (`https://dysmsapi.aliyuncs.com/`)，HMAC-SHA1 签名。

**模板变量**（必填模板需包含）:
```json
{"level": "error", "title": "...", "message": "..."}
```

**触发规则**: 仅 `level=error|critical` 才会发送 SMS（节省成本）。

---

## 4. 集成示例

### 4.1 AI Provider 健康度监控

```python
from app.services.ai.monitor import Monitor
from app.services.ai.monitor import Alert, AlertLevel

monitor = Monitor(db)
alert = Alert(
    level=AlertLevel.WARNING,
    title="Provider deepseek 错误率过高",
    message=f"错误率 {error_rate}% 超过阈值 10%",
    provider_id=12,
    enterprise_id=1,
    metadata={"error_rate": error_rate},
)
await monitor.send_alert(alert)
# 内部委托到 alert_manager.send_alert()
```

### 4.2 SLA 违约告警

```python
# backend/app/services/sla_monitor.py 内部
# severity 映射 level：LOW→info, MEDIUM→warning, HIGH→error, CRITICAL→critical
# 通过 alert_manager.send_alert() 发送（fire-and-forget）
```

### 4.3 配额预警

```python
# backend/app/services/quota_service.py::_send_quota_alert()
# 通过 NotificationService.notify_quota_alert() 发送（邮件 + 短信）
```

---

## 5. 故障排查

### 5.1 邮件发送失败
- 检查 `ALERT_EMAIL_SMTP_HOST` / `ALERT_EMAIL_USERNAME` / `ALERT_EMAIL_PASSWORD` 是否正确
- 测试 SMTP 连接: `python -c "import smtplib; smtplib.SMTP('host', 587).starttls()"`
- 查看日志: `Failed to send email alert: <error>`

### 5.2 钉钉发送失败
- 检查 `ALERT_DINGTALK_WEBHOOK` 是否以 `https://oapi.dingtalk.com/robot/send?access_token=` 开头
- 若启用签名: 检查 `ALERT_DINGTALK_SECRET` 与钉钉机器人"加签"设置一致
- 测试 webhook: 用 `curl` 模拟 POST 请求

### 5.3 短信发送失败
- 检查 `ALERT_SMS_*` 凭证是否完整
- 检查模板变量格式（JSON）
- 阿里云控制台 → 短信服务 → 发送记录查看详细错误
- 本地仅 ERROR/CRITICAL 触发 SMS，WARNING/INFO 不会发送（预期行为）

---

## 6. 安全注意

- ⚠️ **凭证绝不硬编码**：所有密钥通过 `.env` 注入
- ⚠️ **错误日志脱敏**：异常仅记录摘要，不含完整 traceback
- ⚠️ **输入校验**：`title` / `message` 自动截断至 1000 字符
- ⚠️ **频率限制**：全局内存 Dict 防止告警风暴

---

## 7. 测试

参见: `backend/tests/test_alerts.py`（单元测试）

测试场景:
- 频率限制（连续 2 次发送，第 2 次被 cooldown）
- 优雅降级（凭证缺失）
- 渠道分派（按 channels 过滤）
- 输入校验（超长截断）
- 阿里云签名算法正确性

---

## 8. 相关文档

- 监控配置: `backend/config/monitoring.py`
- 阿里云短信 API v3 签名: https://help.aliyun.com/document_detail/101414.html
- 钉钉自定义机器人: https://open.dingtalk.com/document/orgapp/custom-robot-access
- Phase 2 完成报告: `docs/reports/PHASE2-COMPLETION-REPORT.md`