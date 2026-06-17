# SPEC-BILLING-AUTOBIND — 计费方案自动关联 + 配额预警通知规范

**版本**: v1.0  
**创建**: 2026-06-17  
**状态**: 📐 Spec 阶段（RIPER: R）  
**优先级**: 🟡 P1  
**作者**: AI Engineer (Claude Code)

---

## 1. 背景与目标 (Background & Goals)

### 1.1 现状问题

通过 codegraph + Read 验证，发现：

| 现状 | 文件 | 行号 | 备注 |
|---|---|---|---|
| ❌ `get_user_plan` 是占位 | `backend/app/services/billing_engine.py` | 51 | 直接返回全局默认方案，忽略用户身份 |
| ❌ `_send_quota_alert` 通知占位 | `backend/app/services/quota_service.py` | 1280, 1284 | 只 `logger.info`，未真实发送 |
| ✅ `BillingPlan.applicable_to` | `backend/app/models/billing_plan.py` | — | 已有 `personal`/`enterprise`/`all` 字段 |
| ✅ `BillingPlan.is_default` | `backend/app/models/billing_plan.py` | — | 已支持全局默认方案 |
| ❌ `BillingPlan` 无 `trial_days` | — | — | 需在 application 层计算 |
| ❌ 无 UserPlanBinding 表 | — | — | 通过函数级策略实现关联 |

### 1.2 目标

| ID | 目标 | 验收标准 |
|---|---|---|
| G1 | 个人用户自动绑定"个人版"方案 | `User.is_enterprise=False` 时返回 `applicable_to='personal'` 或 `is_default=True` 的方案 |
| G2 | 企业用户自动绑定"企业版"方案 | `User.enterprise_id` 非空时返回 `applicable_to='enterprise'` 方案 |
| G3 | 试用期到期自动处理 | 用户的 `created_at + trial_days` 已过 → 降级到免费方案 |
| G4 | 配额预警真实通知 | `_send_quota_alert` 通过 `core/alerts.py` 真实发送邮件/钉钉 |
| G5 | 不破坏现有调用 | `record_usage()`、`get_user_plan()` 调用方零修改 |

### 1.3 非目标

- ❌ 不创建 `user_plan_bindings` 数据库表（最小侵入）
- ❌ 不实现套餐升降级的支付流程（依赖订单系统，本次只做应用层策略）
- ❌ 不实现多方案优先级排序（默认仅返回 1 个最匹配方案）
- ❌ 不修改 `BillingPlan` 表结构（已有字段够用）

---

## 2. 详细设计 (Design)

### 2.1 计费方案匹配策略

**输入**：`user_id: int`  
**输出**：`BillingPlan`

**匹配算法**（优先级从高到低）：
1. **企业用户专用**：若 `User.enterprise_id` 非空 → 返回首个 `applicable_to='enterprise'` 且 `is_active=True` 的方案
2. **个人用户专用**：若 `User.enterprise_id` 为空 → 返回首个 `applicable_to='personal'` 且 `is_active=True` 的方案
3. **全局兜底**：返回首个 `is_default=True` 且 `is_active=True` 的方案
4. **最后兜底**：返回首个 `is_active=True` 的方案（不分类别）

### 2.2 试用期逻辑（应用层）

```python
TRIAL_PERIOD_DAYS = 14  # 环境变量 TRIAL_PERIOD_DAYS，可覆盖
```

- `User.created_at` + `TRIAL_PERIOD_DAYS` < 当前时间 → 用户超出试用期
- 超出试用期后：自动降级到"免费"方案（通过 `pricing_rules` 含 `{"tier": "free"}` 标识）
- 该逻辑在 `record_usage` 时检查，**不**自动改 plan 字段（保持审计可追溯）

### 2.3 配额预警通知集成

**触发条件**（已有）：`_send_quota_alert(quota, alert_level)` 在 `quota_service` 内部被调用

**集成方式**：替换两处 `TODO` 为 `alert_manager.send_alert()`

```python
# quota_service.py:1280
if quota.enterprise_id:
    await alert_manager.send_alert(
        level="warning",  # WARNING/CRITICAL/EXHAUSTED 映射
        title=f"企业配额预警: {quota.enterprise_id}",
        message=f"{message}\n{detail}",
        extra={"enterprise_id": quota.enterprise_id, "alert_type": "quota"}
    )

# quota_service.py:1284
elif quota.user_id:
    await alert_manager.send_alert(
        level="warning",
        title=f"用户配额预警: {quota.user_id}",
        message=f"{message}\n{detail}",
        extra={"user_id": quota.user_id, "alert_type": "quota"}
    )
```

### 2.4 关键行为规则

| 规则 | 说明 |
|---|---|
| **R1** 匹配原子性 | 单事务内完成 User 加载 + Plan 查询，避免脏读 |
| **R2** 试用期只警告 | 不强制降级，避免影响在用用户；只 `logger.info` 记录 |
| **R3** 通知失败不阻塞 | `_send_quota_alert` 失败不影响配额扣减主流程 |
| **R4** 企业 ID 类型兼容 | `User.enterprise_id` 在内存中可能是 str 或 int，统一 `str()` 比较 |

### 2.5 安全与边界

| 项 | 说明 |
|---|---|
| **S1** SQL 注入 | 全部 SQLAlchemy ORM 查询，无字符串拼接 |
| **S2** 越权访问 | `get_user_plan(user_id)` 仅由系统调用，不暴露 HTTP API |
| **S3** 审计追溯 | 不修改 Plan 字段，只在记录中标注 trial_expired，不影响历史 |
| **S4** 性能 | 单次查询，O(1) 数据库调用 |

### 2.6 测试覆盖要求

| 测试类型 | 范围 |
|---|---|
| 单元测试 | 1) 个人用户匹配 personal 方案 2) 企业用户匹配 enterprise 方案 3) 无对应方案时回退到 default 4) 试用期到期日志 5) `_send_quota_alert` 真实调用 alert_manager |
| 回归测试 | 1) `record_usage()` 既有测试通过 2) `BillingPlanManager` 既有测试通过 |
| 集成测试 | 1) 用户注册 → 自动绑定 → 第一次 record_usage 验证 plan 正确 2) 配额耗尽 → 真实收到 alert |

---

## 3. 实施步骤

### 步骤 1: 重写 `BillingEngine.get_user_plan()`
- 文件：`backend/app/services/billing_engine.py`
- 新增 `User` 模型导入
- 按 2.1 优先级算法实现
- 试用期判断（仅日志，不强制降级）

### 步骤 2: 替换 `_send_quota_alert` 中的 TODO
- 文件：`backend/app/services/quota_service.py`
- 导入 `alert_manager` from `app.core.alerts`
- 两处 `TODO` 替换为 `alert_manager.send_alert()` 调用

### 步骤 3: 环境变量与配置
- `.env.example` 添加 `TRIAL_PERIOD_DAYS=14`
- `config/settings.py` 读取该变量

### 步骤 4: 单元测试
- `backend/tests/test_billing_engine.py` 补充 4 个测试用例
- `backend/tests/test_quota_service.py` 补充告警集成测试

---

## 4. 验收标准 (Acceptance Criteria)

### AC1: 自动绑定生效
- ✅ 单元测试 `test_get_user_plan_personal` 通过
- ✅ 单元测试 `test_get_user_plan_enterprise` 通过
- ✅ `record_usage()` 既有测试零修改通过

### AC2: 配额预警真实通知
- ✅ `_send_quota_alert` 调用后 `alert_manager.send_alert()` 被调用（通过 mock 验证）
- ✅ 邮件/钉钉配置正确时真实发送；缺失时降级为 logger

### AC3: 试用期处理
- ✅ `User.created_at` 14 天前注册的用户，在 `get_user_plan` 中输出 `logger.info("[TRIAL] User ... is past trial period")`

### AC4: 向后兼容
- ✅ `BillingEngine.get_user_plan(user_id)` 签名不变
- ✅ `BillingEngine.record_usage(...)` 签名不变

---

## 5. 风险与缓解

| 风险 | 影响 | 缓解 |
|---|---|---|
| `User` 模型无 `enterprise_id` 字段 | 高 | 实现前 Read User 模型验证；不存在则降级到"全部用户走 personal" |
| `_send_quota_alert` 改成 async 后调用方未 await | 中 | 保持函数同步；用 `asyncio.create_task(alert_manager.send_alert(...))` fire-and-forget |
| 企业方案存在多个时排序不定 | 低 | 显式 `ORDER BY sort_order, created_at`，确保确定性 |
| 试用期判断性能 | 低 | 仅在 `get_user_plan` 调用时检查，业务路径无额外开销 |

---

## 6. 开放问题

1. **Q1**: 试用期过期后是否要自动修改 user 的 plan 字段？
   **决策**: 否。保持 plan 字段稳定，trial 状态通过日志/审计追踪，避免脏写
2. **Q2**: 企业版方案如何选择（可能多个 enterprise 方案）？
   **决策**: `applicable_to='enterprise'` + `is_active=True` + `sort_order` 最小者优先
3. **Q3**: 个人/企业分类是否需要新增 `is_enterprise` 字段？
   **决策**: 否。已有 `User.enterprise_id` 可推断（非空 = 企业用户）

---

## 7. 参考资料

- 现有 `BillingPlan` 模型: `backend/app/models/billing_plan.py`
- 现有调用方: `backend/app/services/billing_engine.py:42` (3 个内部调用)
- 配额预警入口: `backend/app/services/quota_service.py:1260`
- 统一告警接口: `core/alerts.py` (Spec #NOTIFICATION-UNIFICATION)