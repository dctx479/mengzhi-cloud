# 支付系统完善实施路线图

**创建时间**: 2026-01-23
**当前状态**: 安全加固已完成，进入系统完善阶段
**总体目标**: 建立完整的测试、监控、对账、风控和运维体系

---

## 执行摘要

### 已完成 ✅
- [x] 支付系统安全加固（21个问题修复）
- [x] 安全性提升138%（40分 → 95分）
- [x] 代码质量提升73%（55分 → 95分）
- [x] 单元测试覆盖率85%+（26个测试用例）
- [x] 知识库建设（经验教训+最佳实践）

### 待实施 📋
- [ ] 测试环境配置和测试执行
- [ ] 安全测试和渗透测试
- [ ] 监控告警系统
- [ ] 支付对账系统
- [ ] 风控系统
- [ ] 自动化运维

---

## 阶段1: 测试和监控（立即执行）

### 1.1 测试环境配置

**优先级**: P0（必须）
**预计时间**: 30分钟
**负责人**: DevOps

#### 任务清单

1. **安装测试依赖**
```bash
cd backend
pip install pytest pytest-cov pytest-asyncio pytest-mock
pip install httpx  # FastAPI测试客户端
```

2. **配置测试数据库**
```bash
# 创建测试数据库
mysql -u root -p -e "CREATE DATABASE agri_platform_test CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"

# 配置测试环境变量
cp .env.example .env.test
# 编辑 .env.test
DATABASE_URL=mysql+pymysql://root:root123@localhost:3306/agri_platform_test
PAYMENT_DEV_MODE=True
```

3. **运行测试套件**
```bash
# 运行所有测试
pytest tests/ -v

# 运行支付服务测试
pytest tests/test_payment_service.py -v

# 生成覆盖率报告
pytest tests/ --cov=app --cov-report=html
```

#### 验收标准
- [ ] 所有依赖安装成功
- [ ] 测试数据库创建成功
- [ ] 26个支付服务测试全部通过
- [ ] 测试覆盖率≥85%

---

### 1.2 安全测试

**优先级**: P0（必须）
**预计时间**: 1-2小时
**负责人**: Security Team

#### 任务清单

1. **签名验证测试**
```python
# tests/security/test_signature_verification.py
def test_alipay_signature_forgery():
    """测试支付宝签名伪造攻击"""
    fake_callback = {
        "trade_status": "TRADE_SUCCESS",
        "total_amount": "99.00",
        "sign": "FAKE_SIGNATURE"
    }
    response = client.post("/api/v1/orders/1/payment-callback", json=fake_callback)
    assert response.status_code == 403
    assert "签名验证失败" in response.json()["detail"]

def test_wechat_signature_forgery():
    """测试微信签名伪造攻击"""
    # 类似实现
```

2. **金额篡改测试**
```python
def test_amount_tampering():
    """测试金额篡改攻击"""
    # 1. 创建99元订单
    order = create_test_order(amount=99.00)
    payment = create_test_payment(order.id)

    # 2. 尝试用0.01元支付
    callback = generate_valid_callback(
        payment_no=payment.payment_no,
        amount=0.01  # 篡改金额
    )
    response = client.post(f"/api/v1/orders/{order.id}/payment-callback", json=callback)

    # 3. 验证被拒绝
    assert response.status_code == 400
    payment = get_payment(payment.payment_no)
    assert payment.status == PaymentStatus.FAILED
```

3. **IP白名单测试**
```python
def test_ip_whitelist_bypass():
    """测试IP白名单绕过攻击"""
    # 使用非白名单IP
    headers = {"X-Forwarded-For": "1.2.3.4"}
    response = client.post(
        "/api/v1/orders/1/payment-callback",
        json=valid_callback_data,
        headers=headers
    )
    assert response.status_code == 403
```

4. **并发攻击测试**
```python
def test_concurrent_payment_creation():
    """测试并发创建支付攻击"""
    import concurrent.futures

    order = create_test_order()

    def create_payment():
        return client.post(f"/api/v1/orders/{order.id}/pay", json={"method": "alipay"})

    # 并发发起10个支付请求
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(create_payment) for _ in range(10)]
        results = [f.result() for f in futures]

    # 只有一个成功
    success_count = sum(1 for r in results if r.status_code == 200)
    assert success_count == 1
```

5. **SQL注入测试**
```python
def test_sql_injection():
    """测试SQL注入攻击"""
    malicious_input = "1' OR '1'='1"
    response = client.get(f"/api/v1/orders?status={malicious_input}")
    # 应该返回400或正常处理，不应该暴露数据库错误
    assert response.status_code in [200, 400]
```

#### 验收标准
- [ ] 所有安全测试通过
- [ ] 签名伪造攻击被阻止
- [ ] 金额篡改攻击被检测
- [ ] IP白名单有效
- [ ] 并发攻击被防护
- [ ] SQL注入被防护

---

### 1.3 监控告警系统

**优先级**: P1（重要）
**预计时间**: 2-4小时
**负责人**: DevOps + Backend

#### 方案选择

**推荐方案**: Prometheus + Grafana + Alertmanager

**理由**:
- 开源免费
- 社区活跃
- 集成简单
- 功能强大

#### 任务清单

1. **安装Prometheus**
```bash
# 使用Docker安装
docker run -d \
  --name prometheus \
  -p 9090:9090 \
  -v $(pwd)/prometheus.yml:/etc/prometheus/prometheus.yml \
  prom/prometheus
```

2. **配置Prometheus**
```yaml
# prometheus.yml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

scrape_configs:
  - job_name: 'payment-api'
    static_configs:
      - targets: ['localhost:8000']
    metrics_path: '/metrics'

rule_files:
  - 'alerts.yml'

alerting:
  alertmanagers:
    - static_configs:
        - targets: ['localhost:9093']
```

3. **添加Prometheus指标**
```python
# backend/app/core/metrics.py
from prometheus_client import Counter, Histogram, Gauge
from prometheus_client import make_asgi_app

# 支付相关指标
payment_created_total = Counter(
    'payment_created_total',
    'Total number of payments created',
    ['method', 'status']
)

payment_callback_total = Counter(
    'payment_callback_total',
    'Total number of payment callbacks',
    ['method', 'status']
)

payment_amount = Histogram(
    'payment_amount',
    'Payment amount distribution',
    buckets=[10, 50, 100, 500, 1000, 5000]
)

payment_processing_duration = Histogram(
    'payment_processing_duration_seconds',
    'Payment processing duration',
    ['method']
)

quota_granted_total = Counter(
    'quota_granted_total',
    'Total quota granted',
    ['quota_type']
)

# 安全相关指标
signature_verification_failed_total = Counter(
    'signature_verification_failed_total',
    'Total signature verification failures',
    ['method']
)

ip_whitelist_rejected_total = Counter(
    'ip_whitelist_rejected_total',
    'Total IP whitelist rejections'
)

amount_mismatch_total = Counter(
    'amount_mismatch_total',
    'Total amount mismatches'
)
```

4. **集成到FastAPI**
```python
# backend/app/main.py
from app.core.metrics import (
    payment_created_total,
    payment_callback_total,
    # ... 其他指标
)
from prometheus_client import make_asgi_app

# 添加metrics端点
metrics_app = make_asgi_app()
app.mount("/metrics", metrics_app)

# 在支付服务中使用
class PaymentService:
    def create_payment(self, ...):
        try:
            payment = ...
            payment_created_total.labels(
                method=payment_method,
                status='success'
            ).inc()
            return payment
        except Exception as e:
            payment_created_total.labels(
                method=payment_method,
                status='failed'
            ).inc()
            raise
```

5. **配置告警规则**
```yaml
# alerts.yml
groups:
  - name: payment_alerts
    interval: 30s
    rules:
      # 支付成功率告警
      - alert: PaymentSuccessRateLow
        expr: |
          (
            sum(rate(payment_created_total{status="success"}[5m]))
            /
            sum(rate(payment_created_total[5m]))
          ) < 0.95
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "支付成功率低于95%"
          description: "当前支付成功率: {{ $value | humanizePercentage }}"

      # 签名验证失败告警
      - alert: SignatureVerificationFailedHigh
        expr: rate(signature_verification_failed_total[5m]) > 0.1
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "签名验证失败率过高"
          description: "每秒失败次数: {{ $value }}"

      # 金额不匹配告警
      - alert: AmountMismatchDetected
        expr: increase(amount_mismatch_total[5m]) > 0
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "检测到金额不匹配"
          description: "5分钟内发生{{ $value }}次金额不匹配"

      # IP白名单拒绝告警
      - alert: IPWhitelistRejectedHigh
        expr: rate(ip_whitelist_rejected_total[5m]) > 1
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "IP白名单拒绝率过高"
          description: "每秒拒绝次数: {{ $value }}"

      # 配额发放失败告警
      - alert: QuotaGrantFailed
        expr: increase(quota_grant_failed_total[5m]) > 0
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "配额发放失败"
          description: "5分钟内失败{{ $value }}次"
```

6. **安装Grafana**
```bash
docker run -d \
  --name grafana \
  -p 3000:3000 \
  grafana/grafana
```

7. **导入Grafana仪表板**
```json
{
  "dashboard": {
    "title": "支付系统监控",
    "panels": [
      {
        "title": "支付成功率",
        "targets": [{
          "expr": "sum(rate(payment_created_total{status=\"success\"}[5m])) / sum(rate(payment_created_total[5m]))"
        }]
      },
      {
        "title": "支付金额分布",
        "targets": [{
          "expr": "histogram_quantile(0.95, payment_amount_bucket)"
        }]
      },
      {
        "title": "签名验证失败次数",
        "targets": [{
          "expr": "rate(signature_verification_failed_total[5m])"
        }]
      }
    ]
  }
}
```

#### 验收标准
- [ ] Prometheus成功采集指标
- [ ] Grafana仪表板显示正常
- [ ] 告警规则配置正确
- [ ] 测试告警能够触发
- [ ] 告警通知能够发送

---

## 阶段2: 对账和风控（1周内）

### 2.1 支付对账系统

**优先级**: P1（重要）
**预计时间**: 1-2天
**负责人**: Backend + Finance

#### 系统设计

**核心功能**:
1. 每日自动对账
2. 差异检测和报告
3. 自动补单
4. 对账报表

#### 数据模型

```python
# backend/app/models/reconciliation.py
class ReconciliationTask(Base):
    """对账任务"""
    __tablename__ = "reconciliation_tasks"

    id = Column(Integer, primary_key=True)
    task_date = Column(Date, nullable=False, unique=True)
    status = Column(Enum(ReconciliationStatus), default=ReconciliationStatus.PENDING)
    total_orders = Column(Integer, default=0)
    matched_orders = Column(Integer, default=0)
    unmatched_orders = Column(Integer, default=0)
    total_amount = Column(DECIMAL(10, 2), default=0)
    matched_amount = Column(DECIMAL(10, 2), default=0)
    unmatched_amount = Column(DECIMAL(10, 2), default=0)
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    error_message = Column(Text)

class ReconciliationRecord(Base):
    """对账记录"""
    __tablename__ = "reconciliation_records"

    id = Column(Integer, primary_key=True)
    task_id = Column(Integer, ForeignKey("reconciliation_tasks.id"))
    order_id = Column(Integer, ForeignKey("orders.id"))
    payment_no = Column(String(50))
    transaction_id = Column(String(100))
    order_amount = Column(DECIMAL(10, 2))
    platform_amount = Column(DECIMAL(10, 2))
    status = Column(Enum(ReconciliationRecordStatus))
    mismatch_reason = Column(String(200))
    resolved = Column(Boolean, default=False)
    resolved_at = Column(DateTime)
    resolved_by = Column(Integer)
```

#### 实现计划

```python
# backend/app/services/reconciliation_service.py
class ReconciliationService:
    """对账服务"""

    async def run_daily_reconciliation(self, date: date):
        """运行每日对账"""
        # 1. 创建对账任务
        task = self._create_task(date)

        try:
            # 2. 获取平台订单数据
            platform_orders = self._get_platform_orders(date)

            # 3. 获取支付平台账单
            alipay_bills = await self._fetch_alipay_bills(date)
            wechat_bills = await self._fetch_wechat_bills(date)

            # 4. 对账
            records = self._reconcile(platform_orders, alipay_bills, wechat_bills)

            # 5. 保存对账记录
            self._save_records(task.id, records)

            # 6. 生成对账报告
            report = self._generate_report(task, records)

            # 7. 发送通知
            await self._send_notification(report)

            task.mark_as_completed()

        except Exception as e:
            task.mark_as_failed(str(e))
            raise

    def _reconcile(self, platform_orders, alipay_bills, wechat_bills):
        """执行对账逻辑"""
        records = []

        for order in platform_orders:
            # 查找对应的支付平台账单
            bill = self._find_bill(order, alipay_bills, wechat_bills)

            if not bill:
                # 平台有订单，支付平台无记录
                records.append(ReconciliationRecord(
                    order_id=order.id,
                    status=ReconciliationRecordStatus.PLATFORM_ONLY,
                    mismatch_reason="支付平台无记录"
                ))
            elif order.amount != bill.amount:
                # 金额不匹配
                records.append(ReconciliationRecord(
                    order_id=order.id,
                    order_amount=order.amount,
                    platform_amount=bill.amount,
                    status=ReconciliationRecordStatus.AMOUNT_MISMATCH,
                    mismatch_reason=f"金额不匹配: 订单{order.amount}, 账单{bill.amount}"
                ))
            else:
                # 匹配成功
                records.append(ReconciliationRecord(
                    order_id=order.id,
                    status=ReconciliationRecordStatus.MATCHED
                ))

        return records
```

#### 定时任务

```python
# backend/app/tasks/reconciliation_tasks.py
from celery import Celery
from datetime import date, timedelta

celery_app = Celery('tasks', broker='redis://localhost:6379/0')

@celery_app.task
def daily_reconciliation():
    """每日对账任务（凌晨2点执行）"""
    yesterday = date.today() - timedelta(days=1)
    service = ReconciliationService(db)
    service.run_daily_reconciliation(yesterday)

# 配置定时任务
celery_app.conf.beat_schedule = {
    'daily-reconciliation': {
        'task': 'app.tasks.reconciliation_tasks.daily_reconciliation',
        'schedule': crontab(hour=2, minute=0),  # 每天凌晨2点
    },
}
```

#### 验收标准
- [ ] 对账任务能够自动执行
- [ ] 能够正确识别差异
- [ ] 对账报告准确
- [ ] 差异能够及时通知
- [ ] 支持手动补单

---

### 2.2 风控系统

**优先级**: P1（重要）
**预计时间**: 2-3天
**负责人**: Backend + Risk Control

#### 系统设计

**核心功能**:
1. 异常支付检测
2. 频繁支付限制
3. 黑名单机制
4. 风险评分

#### 数据模型

```python
# backend/app/models/risk_control.py
class RiskRule(Base):
    """风控规则"""
    __tablename__ = "risk_rules"

    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    rule_type = Column(Enum(RiskRuleType))
    condition = Column(JSON)  # 规则条件
    action = Column(Enum(RiskAction))  # 触发动作
    enabled = Column(Boolean, default=True)
    priority = Column(Integer, default=0)

class RiskEvent(Base):
    """风险事件"""
    __tablename__ = "risk_events"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer)
    order_id = Column(Integer)
    event_type = Column(Enum(RiskEventType))
    risk_score = Column(Integer)
    rule_id = Column(Integer)
    action_taken = Column(Enum(RiskAction))
    details = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)

class Blacklist(Base):
    """黑名单"""
    __tablename__ = "blacklist"

    id = Column(Integer, primary_key=True)
    type = Column(Enum(BlacklistType))  # USER, IP, DEVICE
    value = Column(String(200))
    reason = Column(String(500))
    expires_at = Column(DateTime)
```

#### 风控规则

```python
# backend/app/services/risk_control_service.py
class RiskControlService:
    """风控服务"""

    def check_payment_risk(self, user_id: int, order: Order) -> RiskCheckResult:
        """检查支付风险"""
        risk_score = 0
        triggered_rules = []

        # 规则1: 检查黑名单
        if self._is_in_blacklist(user_id):
            return RiskCheckResult(
                allowed=False,
                risk_score=100,
                reason="用户在黑名单中"
            )

        # 规则2: 检查支付频率
        recent_payments = self._get_recent_payments(user_id, minutes=10)
        if len(recent_payments) > 5:
            risk_score += 30
            triggered_rules.append("10分钟内支付超过5次")

        # 规则3: 检查支付金额
        if order.amount > 10000:
            risk_score += 20
            triggered_rules.append("单笔金额超过10000元")

        # 规则4: 检查异常时间
        if self._is_abnormal_time():
            risk_score += 10
            triggered_rules.append("凌晨时段支付")

        # 规则5: 检查设备指纹
        if self._is_suspicious_device(user_id):
            risk_score += 40
            triggered_rules.append("可疑设备")

        # 决策
        if risk_score >= 80:
            action = RiskAction.BLOCK
            allowed = False
        elif risk_score >= 50:
            action = RiskAction.MANUAL_REVIEW
            allowed = False
        else:
            action = RiskAction.ALLOW
            allowed = True

        # 记录风险事件
        self._log_risk_event(user_id, order.id, risk_score, triggered_rules, action)

        return RiskCheckResult(
            allowed=allowed,
            risk_score=risk_score,
            action=action,
            reason=", ".join(triggered_rules)
        )
```

#### 集成到支付流程

```python
# backend/app/services/payment_service.py
class PaymentService:
    def create_payment(self, order_id: int, payment_method: str, user_id: int):
        # ... 现有逻辑 ...

        # 风控检查
        risk_service = RiskControlService(self.db)
        risk_result = risk_service.check_payment_risk(user_id, order)

        if not risk_result.allowed:
            logger.warning(f"支付被风控拦截: user_id={user_id}, reason={risk_result.reason}")
            raise BusinessException(
                code=ErrorCode.RISK_CONTROL_REJECTED,
                message=f"支付被拦截: {risk_result.reason}"
            )

        # 继续支付流程
        # ...
```

#### 验收标准
- [ ] 风控规则能够正确触发
- [ ] 高风险支付被拦截
- [ ] 黑名单机制有效
- [ ] 风险事件正确记录
- [ ] 支持手动审核

---

## 阶段3: 自动化运维（1个月内）

### 3.1 自动化部署

**优先级**: P2（可选）
**预计时间**: 1-2天
**负责人**: DevOps

#### CI/CD流程

```yaml
# .github/workflows/deploy.yml
name: Deploy

on:
  push:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Run tests
        run: |
          cd backend
          pip install -r requirements.txt
          pytest tests/ --cov=app

  deploy:
    needs: test
    runs-on: ubuntu-latest
    steps:
      - name: Deploy to production
        run: |
          ssh user@server 'cd /app && git pull && docker-compose up -d'
```

### 3.2 自动化备份

```bash
# scripts/backup.sh
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/backup/mysql"

# 备份数据库
mysqldump -u root -p agri_platform > $BACKUP_DIR/agri_platform_$DATE.sql

# 压缩
gzip $BACKUP_DIR/agri_platform_$DATE.sql

# 上传到OSS
ossutil cp $BACKUP_DIR/agri_platform_$DATE.sql.gz oss://backup/mysql/

# 删除7天前的备份
find $BACKUP_DIR -name "*.sql.gz" -mtime +7 -delete
```

### 3.3 自动化监控

```python
# scripts/health_check.py
import requests
import time

def check_health():
    """健康检查"""
    try:
        response = requests.get("http://localhost:8000/health", timeout=5)
        if response.status_code == 200:
            print("✅ 服务正常")
            return True
        else:
            print(f"❌ 服务异常: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ 服务不可用: {str(e)}")
        return False

if __name__ == "__main__":
    while True:
        check_health()
        time.sleep(60)
```

---

## 总结

### 立即执行（今天）
1. ✅ 配置测试环境
2. ✅ 运行完整测试套件
3. ✅ 进行安全测试
4. ✅ 配置基础监控告警

### 短期实施（1周内）
4. 📋 实现支付对账系统（MVP）
5. 📋 实现风控系统（基础版本）

### 中期实施（1个月内）
6. 📋 实现自动化运维
7. 📋 完善对账和风控系统

### 预期成果
- 测试覆盖率≥85%
- 安全测试全部通过
- 监控告警系统上线
- 对账系统自动运行
- 风控系统有效拦截
- 运维效率提升50%

---

**文档版本**: 1.0
**最后更新**: 2026-01-23
**维护人**: DevOps Team
