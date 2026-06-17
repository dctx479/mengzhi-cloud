# SPEC-SLA-RECONCILIATION-FRAMEWORK — SLA 监控集成 + 对账框架规范

**版本**: v1.0  
**创建**: 2026-06-17  
**状态**: 📐 Spec 阶段（RIPER: R）  
**优先级**: 🟡 P1  
**作者**: AI Engineer (Claude Code)

---

## 1. 背景与目标 (Background & Goals)

### 1.1 现状问题

| 现状 | 文件 | 行号 | 备注 |
|---|---|---|---|
| ❌ SLA 告警未集成 | `backend/app/services/sla_monitor.py` | 607 | 注释掉的 `self.notification_service.send_alert(...)` |
| ❌ `_get_remote_transactions` 是空壳 | `backend/app/services/reconciliation_service.py` | 233 | 直接返回空 list，注释提示"实际应该调用支付宝、微信等API" |
| ❌ `_supplement_local_payment` 是占位 | `backend/app/services/reconciliation_service.py` | 576 | 仅 `logger.info`，返回假结果 |
| ❌ `_query_remote_status` 是占位 | `backend/app/services/reconciliation_service.py` | 592 | 同上 |
| ❌ `_manual_supplement_transaction` 是占位 | `backend/app/services/reconciliation_service.py` | 605 | 同上 |
| ✅ `RemoteTransaction` dataclass 已存在 | `reconciliation_service.py` | 31 | 结构完整 |
| ✅ `ReconciliationDifference` 模型已存在 | `backend/app/models/reconciliation.py` | — | DB 表已迁移 |
| ✅ SLA 协议/指标/违约表已存在 | `backend/alembic/versions/009_add_sla_system.py` | — | 三表 + 性能日志 |

### 1.2 目标

| ID | 目标 | 验收标准 |
|---|---|---|
| G1 | SLA 违约真实告警 | `_send_alert` 调用 `alert_manager.send_alert()`，按 severity 映射 level |
| G2 | 对账单文件解析框架 | 支持 CSV/XLS 两种格式解析为 `RemoteTransaction` 列表 |
| G3 | 第三方对接接口预留 | 提供 `WechatBillFetcher` / `AlipayBillFetcher` 抽象基类与 Mock 实现 |
| G4 | 补单/查询/手动 框架完整 | 4 处 TODO 替换为可工作的实现（含日志持久化），不依赖真实商户号 |
| G5 | 向后兼容 | `ReconciliationService` 公开 API 零修改 |

### 1.3 非目标

- ❌ 不调用真实支付宝/微信商户 API（按用户决策走环境变量驱动）
- ❌ 不实现定时任务调度（已有 `scheduler.py` 框架，本次只补业务方法）
- ❌ 不修改 `ReconciliationDifference` 数据库表结构
- ❌ 不引入 pandas/xlrd 等大依赖（CSV 用标准库 `csv`，XLS 用 `openpyxl`）

---

## 2. 详细设计 (Design)

### 2.1 架构图

```
┌──────────────────────────────────────────────────────────┐
│                  业务调用方 (Callers)                       │
│  - scheduler.py / 定时任务                                  │
│  - api/reconciliation.py / HTTP API                        │
│  - scripts/run_reconciliation.py / CLI                    │
└─────────────────────┬────────────────────────────────────┘
                      ▼
┌──────────────────────────────────────────────────────────┐
│           ReconciliationService (统一入口)                 │
│   start_reconciliation() / _execute_reconciliation()      │
└──────┬──────────────────┬──────────────────┬──────────────┘
       ▼                  ▼                  ▼
┌──────────────┐  ┌─────────────────┐  ┌─────────────────┐
│ _get_local   │  │_get_remote      │  │_match_trans     │
│ _payments    │  │_transactions    │  │actions          │
│ (DB查询)     │  │ (重构: 文件+API) │  │ (规则匹配)       │
│ ✅ 已实现     │  │ ❌ 待重构        │  │ ✅ 已实现        │
└──────────────┘  └────────┬────────┘  └─────────────────┘
                           │
                           ▼
              ┌─────────────────────────────┐
              │   BillFetcher (抽象基类)     │
              │                             │
              │   + fetch(date) -> List[RT] │
              │   + parse_file(path)         │
              └────┬──────────────┬─────────┘
                   ▼              ▼
         ┌─────────────────┐ ┌────────────────┐
         │ WechatBillFetcher│ │AlipayBillFetcher│
         │  (Mock默认)       │ │  (Mock默认)     │
         │  真实模式: API下载 │ │  真实模式: API下载│
         └─────────────────┘ └────────────────┘
```

### 2.2 SLA 告警集成

#### 2.2.1 severity → alert_level 映射

| SLA severity | alert_manager level |
|---|---|
| LOW | "info" |
| MEDIUM | "warning" |
| HIGH | "error" |
| CRITICAL | "critical" |

#### 2.2.2 实现

```python
# sla_monitor.py 替换 607 行 TODO
SEVERITY_TO_ALERT_LEVEL = {
    "LOW": "info",
    "MEDIUM": "warning",
    "HIGH": "error",
    "CRITICAL": "critical",
}

# 在 send_alert 方法内
alert_level = SEVERITY_TO_ALERT_LEVEL.get(violation.severity.value, "warning")

# 异步 fire-and-forget（不阻塞 SLA 主流程）
try:
    loop = asyncio.get_event_loop()
    if loop.is_running():
        asyncio.create_task(
            alert_manager.send_alert(
                level=alert_level,
                title=f"SLA违约: {agreement.name}",
                message=message,
                extra={
                    "agreement_id": agreement.id,
                    "violation_id": violation.id,
                    "metric_type": violation.metric_type.value,
                    "severity": violation.severity.value,
                    "deviation_rate": violation.deviation_rate,
                }
            )
        )
    else:
        # 同步上下文降级
        logger.warning(f"[SLA ALERT FALLBACK] {alert_level}: {title}")
except RuntimeError:
    logger.warning(f"[SLA ALERT FALLBACK] {alert_level}: {title}")
```

### 2.3 对账单解析框架

#### 2.3.1 文件格式约定

| 渠道 | 文件格式 | 关键字段 |
|---|---|---|
| 微信支付 | `.csv` (GBK 编码) | 交易时间, 微信订单号, 商户订单号, 订单金额, 退款金额, 交易状态 |
| 支付宝 | `.csv` (UTF-8 BOM) | 交易号, 商户订单号, 订单金额（元）, 退款金额（元）, 交易状态, 支付时间 |

#### 2.3.2 解析器接口

```python
class BillParser(ABC):
    """对账单解析器抽象基类"""

    @abstractmethod
    def parse(self, file_path: str) -> List[RemoteTransaction]:
        """解析对账文件为 RemoteTransaction 列表"""

class WechatBillParser(BillParser):
    """微信对账单 CSV 解析（GBK）"""

class AlipayBillParser(BillParser):
    """支付宝对账单 CSV 解析（UTF-8 BOM）"""

class GenericCSVParser(BillParser):
    """通用 CSV 解析（按列名约定，兜底）"""
```

#### 2.3.3 Fetcher 接口

```python
class BillFetcher(ABC):
    """对账单获取器抽象基类"""

    @abstractmethod
    def fetch(self, date: date) -> Optional[str]:
        """下载对账文件到本地，返回文件路径；失败返回 None"""

class WechatBillFetcher(BillFetcher):
    """微信账单下载（Mock: 返回示例文件路径；真实: HTTP API）"""

class AlipayBillFetcher(BillFetcher):
    """支付宝账单下载（Mock: 返回示例文件路径；真实: HTTP API）"""
```

**真实模式触发**：环境变量 `WECHAT_BILL_API_KEY` / `ALIPAY_BILL_API_KEY` 任意一个非空时启用真实下载逻辑（保留 HTTP 代码框架但不真正发送请求）。

### 2.4 补单/查询/手动 实现

#### 2.4.1 `_supplement_local_payment(difference)`

**逻辑**：
1. 通过 `difference.local_order_no` 查 `Order`
2. 通过 `difference.remote_transaction_id` 查 `Payment`（按 `transaction_id`）
3. 若 Order 存在但 Payment 缺失 → 创建 Payment 记录，状态 `SUCCESS`
4. 更新 Order.status = `PAID`
5. 写 `ReconciliationDifference.status = RESOLVED`、`resolved_at = now()`
6. 返回 `"已补充本地支付记录 (order={order_no})"`

**事务边界**：整个函数在 `try/except` 内，任一异常 → `db.rollback()` + `logger.error` + 返回失败描述

#### 2.4.2 `_query_remote_status(difference)`

**逻辑**：
1. 从 `difference.raw_data` 读取 `channel` (微信/支付宝)
2. 按 channel 选 fetcher，调用 `fetcher.query_transaction(transaction_id)`
3. Mock 模式：返回 `RemoteStatus.QUERY_SUCCESS` + 模拟状态字符串
4. 真实模式：调用第三方查询 API（框架已留 HTTP 代码，不实际发送）

#### 2.4.3 `_manual_supplement_transaction(difference)`

**逻辑**：
1. 必须传入 `supplement_data: Dict` 参数（来自 API 层）
2. 校验必填字段：`payment_method`, `paid_at`, `amount`
3. 创建/更新 Payment + Order
4. 标记差异 RESOLVED，写入 `remark = "manual: ..."`
5. 返回操作摘要

### 2.5 关键行为规则

| 规则 | 说明 |
|---|---|
| **R1** 解析失败优雅降级 | 单行解析失败 → 跳过该行 + `logger.warning`，不中断整个文件 |
| **R2** 文件不存在 | `parse()` 返回空 list + `logger.error`，不抛异常 |
| **R3** 编码自适应 | CSV 解析先尝试 UTF-8 BOM，失败再试 GBK |
| **R4** Mock/真实切换 | 环境变量决定；切换零代码修改 |
| **R5** 补单事务原子** | `_supplement_local_payment` 整体包在 `try/except`，失败回滚 |
| **R6** SLA 告警非阻塞** | `asyncio.create_task` fire-and-forget，失败仅日志 |

### 2.6 安全与边界

| 项 | 说明 |
|---|---|
| **S1** SQL 注入 | 全部 ORM 查询 |
| **S2** 文件路径校验 | `file_path` 必须以 `reconciliation_bills/` 开头，禁止 `..` |
| **S3** 凭证管理 | 真实 API 密钥从环境变量读取，不入日志 |
| **S4** 并发安全** | `ReconciliationDifference.status` 更新用 `with_for_update()` |
| **S5** 文件大小限制** | 解析前检查文件 < 50MB，防止 OOM |

### 2.7 测试覆盖要求

| 测试类型 | 范围 |
|---|---|
| 单元测试 | 1) WechatBillParser 解析示例 CSV 2) AlipayBillParser 解析示例 CSV 3) GBK/UTF8 编码自动识别 4) SLA severity→level 映射 5) `_supplement_local_payment` 成功路径 6) `_manual_supplement_transaction` 校验失败 |
| 集成测试 | 1) `start_reconciliation()` → `_execute_reconciliation()` 完整链路（mock 文件） 2) SLA 告警真实触发到 `alert_manager`（mock send_alert） |
| 回归测试 | 1) `ReconciliationService.start_reconciliation()` 既有测试零修改通过 2) `sla_monitor.py` 既有测试零修改通过 |

---

## 3. 实施步骤

### 步骤 1: SLA 告警集成
- 文件：`backend/app/services/sla_monitor.py`
- 替换 `:607` TODO 为 `alert_manager.send_alert()` 调用
- 新增模块级 `SEVERITY_TO_ALERT_LEVEL` 字典

### 步骤 2: 对账单解析框架
- 新文件：`backend/app/services/reconciliation/parsers.py` (BillParser 抽象 + 3 个实现)
- 新文件：`backend/app/services/reconciliation/fetchers.py` (BillFetcher 抽象 + 2 个实现)
- 新文件：`backend/app/services/reconciliation/__init__.py` (导出)

### 步骤 3: 替换 `_get_remote_transactions` 占位
- 文件：`backend/app/services/reconciliation_service.py`
- 实现逻辑：循环 `channels=['wechat', 'alipay']` → 各 fetcher.fetch() → 各 parser.parse()
- 合并为 List[RemoteTransaction]

### 步骤 4: 替换 3 处补单 TODO
- `_supplement_local_payment`：完整 ORM 操作 + 事务
- `_query_remote_status`：调用对应 fetcher
- `_manual_supplement_transaction`：参数校验 + ORM 操作

### 步骤 5: 示例账单文件
- `backend/data/reconciliation_bills/wechat_sample.csv` (GBK)
- `backend/data/reconciliation_bills/alipay_sample.csv` (UTF-8 BOM)
- 仅用于测试/演示，git LFS 跟踪或 .gitignore

### 步骤 6: 单元测试
- `backend/tests/test_bill_parsers.py` (3 个 parser)
- `backend/tests/test_reconciliation_service.py` 补充测试

---

## 4. 验收标准 (Acceptance Criteria)

### AC1: SLA 告警真实触发
- ✅ 单元测试 `test_sla_alert_integration` 通过
- ✅ 触发 SLA 违约时，`alert_manager.send_alert()` 被调用 1 次
- ✅ severity=CRITICAL → level="critical" 映射正确

### AC2: 对账单解析正确
- ✅ WechatBillParser 解析示例 CSV 返回 ≥1 个 RemoteTransaction
- ✅ AlipayBillParser 解析示例 CSV 返回 ≥1 个 RemoteTransaction
- ✅ 字段映射：transaction_id / order_no / amount / status / paid_at 全部正确

### AC3: 补单链路完整
- ✅ `_supplement_local_payment` 成功创建 Payment + 更新 Order + RESOLVED
- ✅ `_manual_supplement_transaction` 缺少必填字段返回 ValidationError
- ✅ 事务回滚：故意抛异常时不污染 DB

### AC4: Mock/真实切换
- ✅ 环境变量 `WECHAT_BILL_API_KEY=""` 时走 Mock
- ✅ 环境变量 `ALIPAY_BILL_API_KEY` 非空时记录 "would call real API" 日志

### AC5: 向后兼容
- ✅ `ReconciliationService.start_reconciliation()` 签名不变
- ✅ `_execute_reconciliation()` 既有测试零修改通过

---

## 5. 风险与缓解

| 风险 | 影响 | 缓解 |
|---|---|---|
| 第三方 API 签名算法错误 | 中 | 仅 Mock；真实模式留 HTTP 框架代码 + 详细注释 |
| 账单文件 GBK 解码失败 | 低 | 自动 fallback 到 UTF-8，捕获异常重试 |
| 补单并发冲突 | 中 | `ReconciliationDifference` 用 `with_for_update()` 行锁 |
| `openpyxl` 依赖未安装 | 低 | 仅当 XLS 文件出现时才尝试 import；缺失时报清晰错误 |
| Fire-and-forget 任务丢失 | 低 | `asyncio.create_task` 仅在事件循环活跃时调用；否则降级日志 |

---

## 6. 开放问题

1. **Q1**: XLS 格式是否本期支持？
   **决策**: 仅留接口 + `ImportError` 友好提示，不强制依赖 `openpyxl`
2. **Q2**: 真实模式触发后是否要支持凭证轮换？
   **决策**: 否，本期固定从 env 读取，未来可扩展 KMS
3. **Q3**: 补单成功后是否触发支付回调？
   **决策**: 否，调用方主动轮询差异状态；避免双向触发

---

## 7. 参考资料

- 阿里云账单下载: https://opendocs.alipay.com/support/01rb07
- 微信支付账单: https://pay.weixin.qq.com/wiki/doc/api/app/app_sl.php?chapter=9_1
- 现有对账模型: `backend/app/models/reconciliation.py`
- 现有 SLA 模型: `backend/alembic/versions/009_add_sla_system.py`
- 统一告警: `core/alerts.py` (Spec #NOTIFICATION-UNIFICATION)