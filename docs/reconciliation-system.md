# 对账系统文档

## 概述

对账系统是AI赋能云平台的核心财务安全模块，负责确保平台内部支付记录与第三方支付平台账单的一致性，保障资金安全和数据准确性。

## 系统架构

### 核心组件

```
┌─────────────────────────────────────────────────────────────┐
│                    对账系统架构                              │
├─────────────────────────────────────────────────────────────┤
│  API层          │  服务层          │  数据层          │  任务层  │
│                 │                  │                  │         │
│ ┌─────────────┐ │ ┌─────────────┐ │ ┌─────────────┐ │ ┌──────┐ │
│ │ 对账API     │ │ │ 对账服务    │ │ │ 对账记录    │ │ │定时  │ │
│ │ - 触发对账  │ │ │ - 自动对账  │ │ │ - 记录表    │ │ │任务  │ │
│ │ - 查询记录  │ │ │ - 差异检测  │ │ │ - 差异表    │ │ │      │ │
│ │ - 修复差异  │ │ │ - 自动补单  │ │ │             │ │ │      │ │
│ │ - 生成报告  │ │ │ - 报告生成  │ │ │             │ │ │      │ │
│ └─────────────┘ │ └─────────────┘ │ └─────────────┘ │ └──────┘ │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
                    ┌─────────────────┐
                    │   第三方支付平台  │
                    │  - 支付宝        │
                    │  - 微信支付      │
                    │  - 银行卡        │
                    └─────────────────┘
```

### 数据模型

#### 对账记录表 (reconciliation_records)

| 字段名 | 类型 | 说明 |
|--------|------|------|
| id | BIGINT | 主键ID |
| batch_no | VARCHAR(64) | 对账批次号 |
| reconciliation_date | VARCHAR(10) | 对账日期 (YYYY-MM-DD) |
| reconciliation_type | ENUM | 对账类型 (daily/manual/retry) |
| status | ENUM | 对账状态 (pending/processing/success/failed/partial) |
| start_time | TIMESTAMP | 对账开始时间 |
| end_time | TIMESTAMP | 对账结束时间 |
| total_local_count | INT | 本地交易总数 |
| total_remote_count | INT | 第三方交易总数 |
| matched_count | INT | 匹配成功数量 |
| difference_count | INT | 差异数量 |
| total_local_amount | DECIMAL(15,2) | 本地交易总金额 |
| total_remote_amount | DECIMAL(15,2) | 第三方交易总金额 |
| matched_amount | DECIMAL(15,2) | 匹配成功金额 |
| difference_amount | DECIMAL(15,2) | 差异金额 |

#### 差异记录表 (reconciliation_differences)

| 字段名 | 类型 | 说明 |
|--------|------|------|
| id | BIGINT | 主键ID |
| reconciliation_id | BIGINT | 对账记录ID |
| difference_type | ENUM | 差异类型 (missing_local/missing_remote/amount_mismatch/status_mismatch) |
| status | ENUM | 处理状态 (pending/processing/resolved/ignored/failed) |
| local_payment_id | BIGINT | 本地支付记录ID |
| local_transaction_id | VARCHAR(128) | 本地交易号 |
| remote_transaction_id | VARCHAR(128) | 第三方交易号 |
| local_amount | DECIMAL(10,2) | 本地金额 |
| remote_amount | DECIMAL(10,2) | 第三方金额 |
| amount_difference | DECIMAL(10,2) | 金额差异 |

## 功能特性

### 1. 自动对账

- **每日定时对账**: 每天凌晨2点自动执行前一天的对账
- **智能匹配**: 基于交易号、金额、时间等多维度匹配
- **差异检测**: 自动识别本地缺失、第三方缺失、金额不匹配等差异
- **状态追踪**: 完整记录对账过程和结果

### 2. 差异处理

- **自动补单**: 对于本地缺失的交易，自动创建支付记录
- **手动处理**: 支持管理员手动处理复杂差异
- **批量操作**: 支持批量忽略或处理差异
- **处理追踪**: 记录每个差异的处理过程和结果

### 3. 报告生成

- **对账报告**: 详细的对账结果报告，包含统计信息和差异明细
- **趋势分析**: 对账成功率、差异率等趋势分析
- **异常告警**: 对账失败或差异率过高时自动告警
- **导出功能**: 支持JSON、Excel、PDF等格式导出

### 4. 监控告警

- **健康检查**: 定期检查对账系统运行状态
- **异常告警**: 连续失败、差异率过高等异常情况告警
- **性能监控**: 对账执行时间、成功率等性能指标监控
- **通知推送**: 支持邮件、短信、企业微信等多种通知方式

## API接口

### 基础路径
```
/api/reconciliation
```

### 接口列表

#### 1. 启动对账
```http
POST /api/reconciliation/start
```

**请求参数:**
```json
{
  "reconciliation_date": "2026-01-22",
  "reconciliation_type": "manual",
  "force": false
}
```

**响应示例:**
```json
{
  "code": 200,
  "message": "对账已启动",
  "data": {
    "id": 1,
    "batch_no": "REC_20260122_001",
    "reconciliation_date": "2026-01-22",
    "status": "processing"
  }
}
```

#### 2. 查询对账记录
```http
GET /api/reconciliation/records?page=1&page_size=20&status=success
```

**响应示例:**
```json
{
  "code": 200,
  "data": {
    "records": [
      {
        "id": 1,
        "batch_no": "REC_20260122_001",
        "reconciliation_date": "2026-01-22",
        "status": "success",
        "statistics": {
          "total_local_count": 100,
          "matched_count": 98,
          "difference_count": 2
        }
      }
    ],
    "total": 1,
    "page": 1,
    "page_size": 20
  }
}
```

#### 3. 查询差异记录
```http
GET /api/reconciliation/differences?reconciliation_id=1&status=pending
```

#### 4. 修复差异
```http
POST /api/reconciliation/differences/{difference_id}/fix
```

**请求参数:**
```json
{
  "action": "auto_supplement",
  "remark": "自动补单处理"
}
```

#### 5. 生成对账报告
```http
GET /api/reconciliation/records/{record_id}/report?format_type=json
```

## 使用指南

### 管理员操作

#### 1. 查看对账状态
1. 登录管理后台
2. 进入"财务管理" -> "对账管理"
3. 查看最近的对账记录和状态

#### 2. 手动触发对账
1. 点击"手动对账"按钮
2. 选择对账日期
3. 确认执行对账

#### 3. 处理差异记录
1. 进入"差异管理"页面
2. 查看待处理的差异记录
3. 选择处理方式：
   - **自动补单**: 系统自动创建缺失的支付记录
   - **手动补单**: 管理员手动处理
   - **忽略**: 标记为已忽略（需要填写原因）

#### 4. 查看对账报告
1. 选择对账记录
2. 点击"生成报告"
3. 选择报告格式（JSON/Excel/PDF）
4. 下载或在线查看报告

### 开发者集成

#### 1. 调用对账API
```python
import requests

# 启动对账
response = requests.post('/api/reconciliation/start', json={
    'reconciliation_date': '2026-01-22',
    'reconciliation_type': 'manual'
})

# 查询结果
record_id = response.json()['data']['id']
report = requests.get(f'/api/reconciliation/records/{record_id}/report')
```

#### 2. 监听对账事件
```python
from app.tasks import reconciliation_tasks

# 手动执行对账
await reconciliation_tasks.manual_reconciliation('2026-01-22')

# 检查差异
await reconciliation_tasks.run_check_pending_differences()
```

## 对账流程

### 1. 数据准备阶段
```
1. 获取指定日期的本地支付记录
   - 状态为SUCCESS的支付记录
   - 有效的第三方交易号
   - 在指定时间范围内

2. 获取第三方平台的交易数据
   - 调用支付宝对账接口
   - 调用微信支付对账接口
   - 调用银行卡对账接口
```

### 2. 数据匹配阶段
```
1. 基于交易号进行精确匹配
2. 检查金额是否一致（允许0.01元误差）
3. 检查支付状态是否一致
4. 检查支付时间是否合理
```

### 3. 差异识别阶段
```
差异类型：
- missing_local: 第三方有记录，本地无记录
- missing_remote: 本地有记录，第三方无记录
- amount_mismatch: 金额不匹配
- status_mismatch: 状态不匹配
- time_mismatch: 时间差异过大
```

### 4. 结果处理阶段
```
1. 更新对账记录统计信息
2. 保存差异记录详情
3. 生成对账报告
4. 发送通知（成功/失败/有差异）
```

## 定时任务

### 任务调度

系统使用APScheduler进行任务调度，支持以下定时任务：

#### 1. 每日自动对账
- **执行时间**: 每天凌晨2:00
- **任务内容**: 对前一天的交易进行对账
- **失败处理**: 自动重试，发送告警通知

#### 2. 差异检查
- **执行时间**: 每4小时一次
- **任务内容**: 检查是否有长时间未处理的差异
- **告警条件**: 超过24小时未处理的差异

#### 3. 健康检查
- **执行时间**: 每天上午9:00
- **任务内容**: 检查对账系统运行状态
- **检查项目**: 连续失败次数、差异率、缺失对账等

### 任务管理

#### 启动调度器
```python
from app.tasks import start_reconciliation_scheduler
start_reconciliation_scheduler()
```

#### 查看任务状态
```python
from app.tasks import get_scheduler_status
status = get_scheduler_status()
print(f"调度器运行状态: {status['scheduler_running']}")
print(f"任务数量: {status['total_jobs']}")
```

#### 手动执行任务
```python
from app.tasks import run_reconciliation_job_now
run_reconciliation_job_now('daily_reconciliation')
```

## 配置说明

### 环境变量

```bash
# 对账相关配置
RECONCILIATION_ENABLED=true
RECONCILIATION_AUTO_START=true
RECONCILIATION_NOTIFICATION_ENABLED=true

# 第三方支付配置
ALIPAY_RECONCILIATION_URL=https://openapi.alipay.com/gateway.do
WECHAT_RECONCILIATION_URL=https://api.mch.weixin.qq.com/pay/downloadbill
```

### 系统配置

```python
# settings.py
class Settings:
    # 对账配置
    RECONCILIATION_ENABLED: bool = True
    RECONCILIATION_AUTO_START: bool = True
    RECONCILIATION_BATCH_SIZE: int = 1000
    RECONCILIATION_TIMEOUT: int = 300  # 5分钟

    # 差异处理配置
    AUTO_SUPPLEMENT_ENABLED: bool = True
    MAX_AMOUNT_DIFFERENCE: float = 0.01  # 最大金额差异

    # 通知配置
    NOTIFICATION_ENABLED: bool = True
    ADMIN_EMAIL: str = "admin@example.com"
```

## 监控指标

### 关键指标

1. **对账成功率**: 成功完成对账的比例
2. **匹配率**: 交易匹配成功的比例
3. **差异率**: 发现差异的交易比例
4. **处理时效**: 差异记录的平均处理时间
5. **系统可用性**: 对账系统的可用时间比例

### 告警规则

1. **对账失败**: 连续2次对账失败
2. **差异率过高**: 差异率超过5%
3. **处理超时**: 差异记录超过24小时未处理
4. **系统异常**: 对账系统连续1小时无响应

## 故障排查

### 常见问题

#### 1. 对账失败
**现象**: 对账状态显示为failed
**排查步骤**:
1. 查看错误日志: `tail -f logs/reconciliation.log`
2. 检查第三方接口连通性
3. 验证数据库连接状态
4. 检查系统资源使用情况

#### 2. 差异过多
**现象**: 差异数量异常增加
**排查步骤**:
1. 检查支付系统是否正常
2. 验证第三方平台数据
3. 分析差异类型分布
4. 检查时间同步问题

#### 3. 性能问题
**现象**: 对账执行时间过长
**排查步骤**:
1. 检查数据库查询性能
2. 优化索引配置
3. 调整批处理大小
4. 增加系统资源

### 日志分析

#### 日志级别
- **INFO**: 正常对账流程日志
- **WARNING**: 发现差异或异常情况
- **ERROR**: 对账失败或系统错误
- **DEBUG**: 详细的调试信息

#### 关键日志
```
[INFO] 开始对账: date=2026-01-22, type=daily
[INFO] 获取本地交易数据: 100 条
[INFO] 获取第三方交易数据: 98 条
[WARNING] 发现 2 条差异记录
[INFO] 对账完成: REC_20260122_001, 差异数量: 2
```

## 安全考虑

### 数据安全
1. **敏感数据加密**: 交易数据采用AES加密存储
2. **访问控制**: 严格的RBAC权限控制
3. **审计日志**: 完整记录所有操作日志
4. **数据备份**: 定期备份对账数据

### 接口安全
1. **身份认证**: JWT Token认证
2. **权限验证**: 管理员权限验证
3. **请求限流**: API请求频率限制
4. **参数校验**: 严格的输入参数校验

### 系统安全
1. **网络隔离**: 对账服务独立部署
2. **防火墙**: 限制网络访问
3. **监控告警**: 异常行为监控
4. **定期更新**: 及时更新安全补丁

## 性能优化

### 数据库优化
1. **索引优化**: 为查询字段添加合适索引
2. **分区表**: 按日期分区存储历史数据
3. **连接池**: 优化数据库连接池配置
4. **查询优化**: 优化复杂查询语句

### 系统优化
1. **异步处理**: 使用异步任务处理对账
2. **批量操作**: 批量处理数据减少IO
3. **缓存机制**: 缓存频繁查询的数据
4. **资源监控**: 监控CPU、内存使用情况

### 扩展性设计
1. **微服务架构**: 对账服务独立部署
2. **水平扩展**: 支持多实例部署
3. **负载均衡**: 分布式任务调度
4. **容器化**: Docker容器化部署

## 版本历史

### v1.0 (2026-01-23)
- ✅ 基础对账功能实现
- ✅ 自动对账和差异检测
- ✅ 管理API和定时任务
- ✅ 基础监控和告警
- ✅ 完整的测试用例

### 后续规划
- 📋 支持更多支付渠道
- 📋 实时对账功能
- 📋 智能差异分析
- 📋 可视化报表
- 📋 移动端管理界面

## 联系支持

如有问题或建议，请联系：
- 📧 邮箱: support@example.com
- 📱 电话: 400-xxx-xxxx
- 💬 企业微信: AI赋能云平台技术支持群