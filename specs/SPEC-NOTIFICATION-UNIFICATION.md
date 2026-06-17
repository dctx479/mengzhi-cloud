# SPEC-NOTIFICATION-UNIFICATION — 告警通知系统统一规范

**版本**: v1.0  
**创建**: 2026-06-17  
**状态**: 📐 Spec 阶段（RIPER: R）  
**优先级**: 🔴 P0  
**作者**: AI Engineer (Claude Code)

---

## 1. 背景与目标 (Background & Goals)

### 1.1 现状问题

通过 codegraph 勘察，发现项目告警系统存在**实现分散与重复**问题：

| 现状 | 文件 | 备注 |
|---|---|---|
| ✅ 主告警管理器 | `backend/app/core/alerts.py` | `AlertManager` 类，已实现 SMTP + 钉钉 + 冷却期；`_send_sms_alert` 是占位 |
| ❌ 旧告警副本 | `backend/app/services/ai/monitor.py` | `Monitor.send_alert()`，3 处 TODO（EMAIL/WEBHOOK/SMS） |
| ✅ 监控配置 | `backend/config/monitoring.py` | `MonitoringConfig` 已有完整 8 个 ALERT_* 环境变量 |
| ✅ 已被调用 | `monitoring.py`、`middleware/monitoring.py` | `core/alerts.py` 的 `send_alert` 已被 2 处使用 |

**核心问题**：
1. **重复实现**：`ai/monitor.py` 是独立维护的旧版告警，3 处 TODO 永远不会被填上，因为它绕过了 `core/alerts.py`
2. **SMS 占位**：`core/alerts.py:153` 的 `_send_sms_alert` 只是 `logger.info`，未真正调用阿里云 SDK
3. **Webhook URL 未配置**：`ai/monitor.py:179` 的 TODO 提示"从企业配置中获取"，但 `core/alerts.py` 的钉钉 URL 来自全局 env，无企业级路由

### 1.2 目标

| ID | 目标 | 验收标准 |
|---|---|---|
| G1 | 统一告警入口 | 所有调用方使用 `core.alerts.alert_manager.send_alert()`，`ai/monitor.py` 的副本被委托 |
| G2 | 补 SMS 真实实现 | 阿里云 SDK 完整集成；环境变量缺失时优雅降级为 logger |
| G3 | 企业级 Webhook | 钉钉/企微 URL 支持企业级覆盖（从 `TenantConfig` 读取），全局兜底 |
| G4 | 向后兼容 | 现有 `core/alerts.py` 调用方（2 处）零修改 |

### 1.3 非目标 (Out of Scope)

- ❌ 不实现真实短信网关对接（按用户决策走环境变量驱动，缺凭证时降级）
- ❌ 不实现真实邮件发送（已实现 SMTP）
- ❌ 不重构 `monitoring.py`、`middleware/monitoring.py` 调用方
- ❌ 不引入额外依赖（阿里云 SDK 通过标准库 `urllib` 实现，避免新增 `aliyun-python-sdk-core`）

---

## 2. 详细设计 (Design)

### 2.1 架构图

```
┌─────────────────────────────────────────────────────────────┐
│                  业务调用方 (Callers)                         │
│  - ai/monitor.py::Monitor.send_alert   [将被委托]            │
│  - sla_monitor.py::send_alert          [待集成]             │
│  - quota_service.py::_send_quota_alert [待集成]             │
│  - api/monitoring.py                   [已集成] ✅           │
│  - middleware/monitoring.py            [已集成] ✅           │
└─────────────────────┬───────────────────────────────────────┘
                      │ await alert_manager.send_alert(...)
                      ▼
┌─────────────────────────────────────────────────────────────┐
│              core/alerts.py (统一入口)                        │
│                                                              │
│  AlertManager.send_alert(level, title, message, extra)        │
│       ├── 频率限制 (alert_cooldown Dict)                      │
│       ├── 并发分派到多渠道                                     │
│       └── asyncio.gather(*tasks, return_exceptions=True)      │
└──────┬───────────┬─────────────┬─────────────────────────────┘
       ▼           ▼             ▼
┌────────────┐ ┌─────────────┐ ┌────────────────────────┐
│ _send_email│ │_send_dingtalk│ │   _send_sms (新增真实)   │
│   (SMTP)   │ │ (HMAC-SHA256)│ │                        │
│ ✅ 已实现   │ │ ✅ 已实现     │ │ ❌ 待实现 (aliyun SDK)   │
└────────────┘ └─────────────┘ └────────────────────────┘
```

### 2.2 接口签名（契约）

#### 2.2.1 `core/alerts.py` 公开 API（不变）

```python
class AlertManager:
    async def send_alert(
        self,
        level: str,         # "info" | "warning" | "error" | "critical"
        title: str,
        message: str,
        extra: Optional[Dict[str, Any]] = None,
        channels: Optional[List[str]] = None,  # 新增：显式指定渠道
        enterprise_id: Optional[str] = None,  # 新增：企业级路由
    ) -> Dict[str, bool]:  # 新增：每渠道发送结果
        """统一告警入口。返回 {channel: success_bool}"""
```

**向后兼容**：
- 现有 `send_alert(level, title, message, extra)` 4 参调用**不变**（通过 `Optional` 默认值兼容）
- 新增 3 个 keyword-only 参数，对老调用方透明

#### 2.2.2 新增辅助函数 `get_alert_recipients(enterprise_id)`

```python
def get_alert_recipients(enterprise_id: Optional[str]) -> Dict[str, List[str]]:
    """获取企业的告警接收人配置

    Returns:
        {
            "email": ["admin@x.com"],
            "dingtalk": ["https://oapi.dingtalk.com/robot/send?access_token=..."],
            "sms": ["13800138000"],
            "use_global_fallback": True/False
        }

    实现要点：
    - 优先查 TenantConfig 表（如果存在 alert_config 字段）
    - 缺失时降级到 monitoring_config 全局配置
    - 全部缺失时返回空 dict，由各 channel 自行 skip
    """
```

### 2.3 数据结构

#### 2.3.1 告警级别映射（已存在，沿用）

```python
class AlertLevel:
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"
```

#### 2.3.2 钉钉消息格式（已存在，沿用）

```python
# 已在 alerts.py:124-141 实现 Markdown 格式
# 新增：支持 @特定人（如果 extra.get("at_mobiles") 提供）
```

#### 2.3.3 阿里云短信参数（新增）

```python
SMS_API_URL = "https://dysmsapi.aliyuncs.com/"
SMS_REQUIRED_PARAMS = {
    "AccessKeyId": str,        # from ALERT_SMS_ACCESS_KEY
    "AccessKeySecret": str,    # from ALERT_SMS_SECRET_KEY
    "SignName": str,           # from ALERT_SMS_SIGN_NAME
    "TemplateCode": str,       # from ALERT_SMS_TEMPLATE_CODE
    "PhoneNumbers": str,       # 逗号分隔
    "TemplateParam": str,      # JSON: {"level":"...", "title":"...", "message":"..."}
}
```

### 2.4 关键行为规则

| 规则 | 说明 |
|---|---|
| **R1** 频率限制 | 同一 `alert_key` (level:title) 在 `cooldown_period` (300s) 内只发送一次 |
| **R2** 优雅降级 | 任一渠道发送失败不影响其他渠道；全部失败也不抛出异常（外层捕获） |
| **R3** 凭证缺失处理 | 任何渠道凭证不全（关键字段为空）→ 跳过该渠道，`logger.warning`，不抛错 |
| **R4** 同步 SMTP | 邮件发送走 `asyncio.to_thread()` 避免阻塞事件循环（已实现） |
| **R5** SMS 仅高优先级 | `INFO`/`WARNING` 不发短信（节省成本），仅 `ERROR`/`CRITICAL` 触发 |
| **R6** 企业级覆盖 | 当 `enterprise_id` 提供时，钉钉 URL 优先用企业配置；email/sms 收件人优先用企业配置 |

### 2.5 安全与边界

| 项 | 说明 |
|---|---|
| **S1 凭证管理** | 所有密钥从环境变量读取，**绝不**硬编码或日志输出 |
| **S2 错误日志脱敏** | 错误日志只记录异常类型和摘要，不记录完整 traceback 含凭证 |
| **S3 速率限制** | `alert_cooldown` 全局内存 Dict；进程重启后清空（可接受） |
| **S4 输入校验** | `title`/`message` 长度限制 1-1000 字符；超长截断并加省略号 |
| **S5 SQL 注入** | 不涉及 SQL（纯 HTTP/SMTP/SDK 调用） |

### 2.6 测试覆盖要求

| 测试类型 | 范围 |
|---|---|
| 单元测试 | 1) 频率限制（连续 2 次发送，第 2 次被 cooldown）2) 优雅降级（凭证缺失）3) 渠道分派（按 channels 过滤）4) 输入校验（超长截断） |
| 集成测试 | 1) SMTP 邮件（mock SMTP server）2) 钉钉 HTTP（mock httpx）3) 阿里云短信（mock HTTP） |
| 兼容性测试 | 1) `ai/monitor.py` 调用方透明升级 2) `sla_monitor.py` 集成后真实路径 3) `quota_service.py` 集成后真实路径 |

---

## 3. 实施步骤 (Implementation Steps)

### 步骤 1: 增强 `core/alerts.py`（最小侵入）
- 添加 `send_alert()` 3 个可选参数：`channels`、`enterprise_id`
- 添加 `get_alert_recipients()` 辅助函数（依赖注入 `db` 可选）
- 新增 `_send_sms_alert()` 真实实现：阿里云 SDK HTTP 签名
- 新增 `_send_alertmanager_webhook()`（预留 AlertManager 兼容）
- 修改 `_send_dingtalk_alert()` 支持 `enterprise_id` 路由

### 步骤 2: 改造 `ai/monitor.py`（委托模式）
- `Monitor.send_alert(alert, channels)` 改为构造参数后委托到 `alert_manager.send_alert()`
- 删除 3 处 TODO（`_send_email_alert`/`_send_webhook_alert`/`_send_sms_alert`）
- 保留 `Monitor` 类（业务逻辑），移除其告警实现细节

### 步骤 3: 集成 SLA + Quota（任务 #5）
- `sla_monitor.py:607` 替换 TODO 为 `alert_manager.send_alert(severity, title, message)`
- `quota_service.py:1280, 1284` 替换 TODO 为 `alert_manager.send_alert("warning", title, message)`

### 步骤 4: 配置与文档（任务 #6）
- 更新 `.env.example` 添加所有 ALERT_* 环境变量
- 在 `docs/api/` 中补充告警系统使用文档

---

## 4. 验收标准 (Acceptance Criteria)

### AC1: 统一入口生效
- ✅ `ai/monitor.py` 调用 `send_alert()` 时，控制台只看到一次 `Sending alert` 日志（来自 `core/alerts.py`）
- ✅ `core/alerts.py` 中所有方法无 `TODO` 字样

### AC2: SMS 真实可用
- ✅ 配置完整的 `ALERT_SMS_*` 环境变量后，触发 ERROR 级别告警能调用阿里云 API
- ✅ 凭证缺失时输出 `logger.warning("SMS credentials not configured, skipping")` 而不抛错

### AC3: 频率限制生效
- ✅ 同一 alert_key 在 300s 内第二次发送时，logger 输出 `Alert in cooldown`

### AC4: 向后兼容
- ✅ `npx tsc --noEmit` 零错误（虽不涉及 TS，但 `python -m py_compile` 全部通过）
- ✅ `backend/tests/test_*.py` 既有测试用例全部通过

### AC5: 文档完整
- ✅ `docs/api/11-notification-system.md` 包含环境变量清单、调用示例、故障排查

---

## 5. 风险与缓解 (Risks & Mitigation)

| 风险 | 影响 | 缓解 |
|---|---|---|
| 阿里云签名算法错误导致 SMS 全部失败 | 高 | 1) 参考官方文档 v3 签名；2) 单元测试覆盖签名逻辑；3) 失败时降级为 logger |
| `Monitor.send_alert()` 签名变化破坏调用方 | 中 | 保持 `Monitor.send_alert(alert, channels)` 签名不变；内部委托即可 |
| 阿里云 SDK HTTP 请求阻塞事件循环 | 低 | 用 `asyncio.to_thread()` 或 `httpx.AsyncClient` |
| 环境变量误改导致生产误告警 | 中 | 所有开关默认 `False`；启用必须显式设 `True` |

---

## 6. 开放问题 (Open Questions)

1. **Q1**: 阿里云短信 SDK 选型：标准库 `urllib` 还是新增依赖？
   **决策**: 标准库 `urllib`（避免新增依赖；签名算法手动实现 ~30 行）
2. **Q2**: 钉钉"@特定人"功能优先级？
   **决策**: 本次仅实现基础告警；@人作为未来增强（`extra.get("at_mobiles")` 透传，不强制消费）
3. **Q3**: 是否引入异步告警队列（Redis/Celery）？
   **决策**: 暂不引入；现有 `asyncio.gather` 已能并发；后续如出现性能瓶颈再升级

---

## 7. 参考资料 (References)

- 阿里云短信 v3 签名: https://help.aliyun.com/document_detail/101414.html
- 钉钉自定义机器人: https://open.dingtalk.com/document/orgapp/custom-robot-access
- Python `asyncio.to_thread`: https://docs.python.org/3.9/library/asyncio-task.html
- 项目内: `backend/config/monitoring.py` (已存在配置基线)