# 配额和计费系统优化文档

<thinking>
现在我需要生成一个完整的文档，说明优化后的配额和计费系统的设计、使用方法和注意事项。
</thinking>

**版本**: 2.0
**日期**: 2026-01-22
**状态**: ✅ 已完成

---

## 📋 优化概述

针对即梦视频/图片生成服务，设计了严谨的配额和计费系统，确保计费准确、防止漏洞。

### 核心改进

1. **细粒度配额管理**
   - 图片配额（按张数和分辨率）
   - 视频配额（按秒数和分辨率）
   - 并发限制

2. **严谨的计费机制**
   - 预扣费（生成前扣费）
   - 幂等性保障（防重复计费）
   - 自动退款（失败全额退款）
   - 计费审计（完整日志）

3. **成本控制**
   - 单次生成限额
   - 每日消费限额
   - 异常消费告警

---

## 🎯 配额层级

### 免费版（¥0/月）
- **图片**: 10张/月，2张/日（仅512x512）
- **视频**: 不支持
- **并发**: 1个
- **频率**: 10请求/分钟

### 基础版（¥99/月）
- **图片**: 100张/月，20张/日（支持1024x1024）
- **视频**: 60秒/月，10秒/日（720p）
- **并发**: 3个
- **频率**: 30请求/分钟

### 专业版（¥999/月）
- **图片**: 1000张/月，200张/日（支持2048x2048）
- **视频**: 600秒/月，100秒/日（1080p）
- **并发**: 10个
- **频率**: 100请求/分钟

### 企业版（¥9999/月）
- **图片**: 无限制
- **视频**: 无限制
- **并发**: 50个
- **频率**: 500请求/分钟

---

## 💰 计费规则

### 图片生成计费

| 分辨率 | 价格 | 配额消耗 |
|--------|------|----------|
| 512x512 | ¥0.1/张 | 1张 |
| 1024x1024 | ¥0.3/张 | 3张 |
| 2048x2048 | ¥0.8/张 | 8张 |

**说明**: 配额消耗表示生成一张该分辨率图片消耗的配额数量。

### 视频生成计费

| 分辨率 | 价格 | 配额消耗 |
|--------|------|----------|
| 720p | ¥0.5/秒 | 1秒/秒 |
| 1080p | ¥1.0/秒 | 2秒/秒 |
| 4K | ¥3.0/秒 | 5秒/秒 |

**说明**: 配额消耗表示生成1秒该分辨率视频消耗的配额秒数。

### 失败处理

- **生成失败**: 100%退款
- **部分生成**: 不退款（已消耗资源）

### 超额计费

超出配额后，价格上浮50%：
- 图片: ¥0.15/¥0.45/¥1.2
- 视频: ¥0.75/¥1.5/¥4.5

---

## 🔒 计费严谨性保障

### 1. 预扣费机制

```
用户请求 → 检查配额 → 检查余额 → 预扣费 → 调用API
                                    ↓
                            生成成功 → 确认交易
                            生成失败 → 全额退款
```

**优势**:
- 防止余额不足导致的坏账
- 确保资源使用前已付费
- 5分钟超时自动退款

### 2. 幂等性保障

<thinking>
幂等性是防止重复计费的关键机制。通过生成唯一的幂等性key，确保相同的请求不会被重复计费。
</thinking>

```python
# 生成幂等性key
idempotency_key = hash(enterprise_id + request_params)

# 检查是否重复请求
existing = check_idempotency(idempotency_key)
if existing:
    return existing  # 返回已有交易，不重复计费
```

**优势**:
- 防止网络重试导致重复计费
- 防止用户恶意重复提交
- 1小时内有效

### 3. 计费审计

每笔交易记录：
- 交易ID、企业ID、金额
- 请求参数、实际使用情况
- 状态变更历史
- 操作人和操作时间

**保留期**: 1年

### 4. 双重验证

```python
# 生成前验证
validate_quota()  # 检查配额
validate_balance()  # 检查余额

# 扣费后验证
double_check_after_deduction()  # 确认扣费成功
```

---

## 🚀 使用示例

### 图片生成

```python
from app.services.strict_billing import StrictBillingService

billing = StrictBillingService(db)

# 1. 预扣费
transaction = billing.pre_deduct(
    enterprise_id=123,
    service_type="jimeng_image",
    params={"resolution": "1024x1024", "prompt": "美丽的风景"},
    idempotency_key="unique-key-123"
)

# 2. 调用即梦API
try:
    result = jimeng_api.generate_image(...)

    # 3. 成功：确认交易
    billing.confirm_transaction(
        transaction.id,
        actual_usage={"result_url": result.url}
    )
except Exception as e:
    # 4. 失败：全额退款
    billing.refund_transaction(
        transaction.id,
        reason=str(e),
        refund_percentage=100
    )
```

### 视频生成

```python
# 1. 预扣费
transaction = billing.pre_deduct(
    enterprise_id=123,
    service_type="jimeng_video",
    params={"resolution": "720p", "duration": 10, "prompt": "奔跑的马"},
    idempotency_key="unique-key-456"
)

# 2. 调用即梦API
try:
    result = jimeng_api.generate_video(...)

    # 3. 成功：确认交易
    billing.confirm_transaction(
        transaction.id,
        actual_usage={
            "result_url": result.url,
            "actual_duration": result.duration
        }
    )
except Exception as e:
    # 4. 失败：全额退款
    billing.refund_transaction(
        transaction.id,
        reason=str(e),
        refund_percentage=100
    )
```

---

## 📊 数据库设计

### billing_transactions（计费事务表）

| 字段 | 类型 | 说明 |
|------|------|------|
| id | BIGINT | 交易ID |
| enterprise_id | BIGINT | 企业ID |
| quota_id | BIGINT | 配额ID |
| service_type | VARCHAR(50) | 服务类型 |
| amount | DECIMAL(10,4) | 金额 |
| status | ENUM | 状态（pending/completed/refunded） |
| idempotency_key | VARCHAR(64) | 幂等性key |
| request_params | TEXT | 请求参数（JSON） |
| actual_usage | TEXT | 实际使用（JSON） |
| refund_amount | DECIMAL(10,4) | 退款金额 |
| refund_reason | VARCHAR(200) | 退款原因 |
| created_at | TIMESTAMP | 创建时间 |
| completed_at | TIMESTAMP | 完成时间 |
| refunded_at | TIMESTAMP | 退款时间 |

### tenant_quotas（配额表 - 新增字段）

| 字段 | 类型 | 说明 |
|------|------|------|
| monthly_images | INT | 每月图片配额 |
| daily_images | INT | 每日图片配额 |
| monthly_video_seconds | INT | 每月视频秒数配额 |
| daily_video_seconds | INT | 每日视频秒数配额 |
| max_concurrent_requests | INT | 最大并发请求数 |
| balance | DECIMAL(10,2) | 账户余额 |
| pending_amount | DECIMAL(10,2) | 待确认金额 |

---

## 🛡️ 安全措施

### 1. 防止恶意消费

- 单次生成最大成本限制（图片¥10，视频¥100）
- 每日消费上限（按层级）
- 异常消费告警（单小时>¥5）

### 2. 防止计费漏洞

- 预扣费机制（先扣费后生成）
- 幂等性保障（防重复计费）
- 双重验证（生成前后验证）
- 完整审计日志（可追溯）

### 3. 防止配额滥用

- 并发限制（防刷量）
- 频率限制（防爆破）
- 分辨率限制（按层级）

---

## 📈 监控指标

### 计费相关

- 每日交易总数
- 每日交易总额
- 退款率
- 平均交易金额

### 配额相关

- 配额使用率（图片/视频）
- 配额预警次数
- 超额消费金额

### 异常监控

- 重复请求次数（幂等性拦截）
- 余额不足次数
- 配额不足次数
- 异常消费告警次数

---

## 🔧 部署步骤

### 1. 执行数据库迁移

```bash
mysql -uroot -proot123 < backend/migrations/005_optimize_quota_billing.sql
```

### 2. 更新配置文件

```bash
# 使用新的配额规则
cp backend/config/quota_rules_v2.yaml backend/config/quota_rules.yaml
```

### 3. 重启服务

```bash
cd backend
uvicorn app.main:app --reload
```

### 4. 验证功能

```bash
# 测试图片生成
curl -X POST http://localhost:8000/api/jimeng/image/generate \
  -H "Authorization: Bearer <token>" \
  -d '{"prompt": "测试", "resolution": "1024x1024"}'

# 查看交易记录
curl http://localhost:8000/api/billing/transactions \
  -H "Authorization: Bearer <token>"
```

---

## ⚠️ 注意事项

### 开发注意

1. **必须使用幂等性key**: 防止重复计费
2. **必须处理异常**: 确保失败时退款
3. **必须记录审计日志**: 便于问题追溯
4. **必须验证配额**: 生成前检查

### 运维注意

1. **定期检查退款率**: 异常高需排查
2. **监控异常消费**: 及时发现问题
3. **定期备份交易数据**: 防止数据丢失
4. **定期清理过期幂等性key**: 节省存储

### 业务注意

1. **合理设置配额**: 平衡成本和体验
2. **及时充值余额**: 避免服务中断
3. **关注配额预警**: 提前升级套餐
4. **定期查看账单**: 了解消费情况

---

## 📚 相关文档

- 配置文件: `backend/config/quota_rules_v2.yaml`
- 计费服务: `backend/app/services/strict_billing.py`
- 事务模型: `backend/app/models/billing_transaction.py`
- API示例: `backend/app/api/jimeng.py`
- 数据库迁移: `backend/migrations/005_optimize_quota_billing.sql`

---

## 🎉 总结

**优化成果**:
- ✅ 细粒度配额管理（图片/视频分开）
- ✅ 严谨的计费机制（预扣费+幂等性+审计）
- ✅ 完善的成本控制（限额+告警）
- ✅ 防止计费漏洞（双重验证+完整日志）

**系统更加可靠和安全！**

---

**完成时间**: 2026-01-22
**版本**: 2.0
**状态**: ✅ 生产就绪
