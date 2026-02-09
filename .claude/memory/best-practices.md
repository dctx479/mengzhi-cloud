# 最佳实践

记录项目开发过程中总结的最佳实践，供团队参考。

---

## 支付系统安全开发最佳实践

### 1. 安全设计评审

**在实现前必须完成**:
- [ ] 威胁建模（STRIDE方法）
- [ ] 安全架构设计
- [ ] 参考OWASP和PCI DSS标准
- [ ] 评审支付流程和数据流
- [ ] 识别潜在安全风险

**评审清单**:
```markdown
- [ ] 是否验证支付回调签名？
- [ ] 是否有IP白名单保护？
- [ ] 是否验证订单金额？
- [ ] 是否使用安全随机数？
- [ ] 是否有并发控制？
- [ ] 是否有事务保护？
- [ ] 是否有详细日志？
- [ ] 是否有监控告警？
```

### 2. 多层防护机制

**支付回调保护**:
```python
# 第一层：IP白名单
@router.post("/payment-callback")
async def payment_callback(
    request: Request,
    client_ip: str = Depends(verify_callback_ip)  # IP验证
):
    # 第二层：签名验证
    if not verify_signature(request.data):
        raise HTTPException(403, "签名验证失败")

    # 第三层：金额验证
    if not verify_amount(payment, callback_data):
        raise HTTPException(400, "金额不匹配")

    # 第四层：幂等性检查
    if payment.is_success():
        return {"success": True}  # 已处理，直接返回

    # 处理支付
    process_payment(payment, callback_data)
```

**防护层级**:
1. **网络层**: IP白名单、HTTPS强制
2. **应用层**: 签名验证、金额验证
3. **业务层**: 幂等性检查、状态机验证
4. **数据层**: 事务保护、并发控制

### 3. 安全随机数生成

**使用secrets模块**:
```python
import secrets
import uuid

# ✅ 推荐：使用secrets模块
payment_no = f"PAY{date_str}{secrets.token_hex(4)}".upper()

# ✅ 推荐：使用UUID
payment_no = f"PAY{date_str}{uuid.uuid4().hex[:8]}".upper()

# ❌ 禁止：使用random模块
payment_no = f"PAY{date_str}{random.randint(100000, 999999)}"  # 不安全
```

**唯一性保证**:
```python
def generate_unique_payment_no(max_retries=10):
    """生成唯一支付单号"""
    for _ in range(max_retries):
        payment_no = generate_payment_no()
        if not exists_in_db(payment_no):
            return payment_no

    # 后备方案：使用UUID
    return f"PAY{date_str}{uuid.uuid4().hex[:12]}".upper()
```

### 4. 金额验证

**使用Decimal类型**:
```python
from decimal import Decimal

# ✅ 推荐：使用Decimal
callback_amount = Decimal(str(callback_data.get("total_amount")))
expected_amount = Decimal(str(order.amount))

# 允许小误差（处理浮点数精度问题）
tolerance = Decimal('0.01')
if abs(callback_amount - expected_amount) > tolerance:
    raise AmountMismatchError()

# ❌ 禁止：使用float
callback_amount = float(callback_data.get("total_amount"))  # 精度问题
```

**金额来源验证**:
```python
# ✅ 从数据库读取订单金额（可信来源）
order = db.query(Order).filter(Order.id == order_id).first()
expected_amount = order.amount

# ❌ 从请求参数读取金额（不可信来源）
expected_amount = request.data.get("amount")  # 可被篡改
```

### 5. 事务保护

**使用嵌套事务**:
```python
def process_payment_with_quota(payment, order):
    """处理支付并发放配额（带事务保护）"""
    savepoint = db.begin_nested()  # 创建保存点

    try:
        # 关键操作1：更新支付状态
        payment.mark_as_success()

        # 关键操作2：更新订单状态
        order.mark_as_paid()

        # 关键操作3：发放配额（可能失败）
        try:
            grant_quota(order)
        except Exception as e:
            # 回滚到保存点
            savepoint.rollback()
            # 标记失败
            payment.mark_as_failed(str(e))
            order.mark_as_failed(str(e))
            db.commit()
            raise

        # 全部成功，提交
        order.mark_as_completed()
        db.commit()

    except Exception as e:
        db.rollback()
        raise
```

### 6. 并发控制

**使用悲观锁**:
```python
# ✅ 推荐：使用悲观锁
order = db.query(Order).filter(
    Order.id == order_id
).with_for_update().first()  # 锁定记录

# 检查并创建支付
existing_payment = db.query(Payment).filter(
    Payment.order_id == order_id,
    Payment.status == PaymentStatus.PENDING
).first()

if existing_payment:
    return existing_payment

# 创建新支付
payment = Payment(...)
db.add(payment)
db.commit()
```

**使用唯一索引**:
```sql
-- 防止重复支付
ALTER TABLE payments
ADD UNIQUE INDEX idx_order_pending (order_id, status)
WHERE status = 'PENDING';
```

### 7. 日志和监控

**详细的安全日志**:
```python
# ✅ 记录关键操作
logger.info(f"创建支付: order_id={order_id}, amount={amount}, user_id={user_id}")
logger.info(f"支付成功: payment_no={payment_no}, transaction_id={transaction_id}")

# ✅ 记录安全事件
logger.warning(f"签名验证失败: payment_no={payment_no}, ip={client_ip}")
logger.error(f"金额不匹配: expected={expected}, got={actual}")

# ❌ 不要记录敏感信息
logger.info(f"支付密钥: {api_key}")  # 禁止
logger.info(f"用户密码: {password}")  # 禁止
```

**监控指标**:
```yaml
关键指标:
  - 支付成功率 (目标 >99%)
  - 支付回调延迟 (目标 <3秒)
  - 配额发放成功率 (目标 100%)
  - 签名验证失败次数 (告警阈值 >10次/小时)
  - 金额不匹配次数 (告警阈值 >0次)
  - IP验证失败次数 (告警阈值 >50次/小时)
```

### 8. 测试策略

**单元测试**:
```python
# 测试支付创建
def test_create_payment_success():
    payment = service.create_payment(order_id=1, method="alipay")
    assert payment.status == PaymentStatus.PENDING

# 测试签名验证
def test_verify_signature_success():
    assert service._verify_alipay_callback(valid_callback_data) == True

def test_verify_signature_failed():
    assert service._verify_alipay_callback(invalid_callback_data) == False

# 测试金额验证
def test_verify_amount_mismatch():
    with pytest.raises(AmountMismatchError):
        service._verify_payment_amount(payment, wrong_amount_data)

# 测试并发控制
def test_concurrent_payment_creation():
    # 并发创建支付，应该只有一个成功
    results = run_concurrent([
        lambda: service.create_payment(order_id=1, method="alipay"),
        lambda: service.create_payment(order_id=1, method="alipay")
    ])
    assert len([r for r in results if r.success]) == 1
```

**集成测试**:
```python
def test_complete_payment_flow():
    # 1. 创建订单
    order = create_order(user_id=1, package_id=1)

    # 2. 创建支付
    payment = create_payment(order.id, "alipay")

    # 3. 模拟支付回调
    callback_payment(payment.payment_no, success=True)

    # 4. 验证结果
    order = get_order(order.id)
    assert order.status == OrderStatus.COMPLETED

    user = get_user(order.user_id)
    assert user.chat_quota == expected_quota
```

**安全测试**:
```python
def test_security_signature_forgery():
    """测试签名伪造攻击"""
    fake_callback = {
        "trade_status": "TRADE_SUCCESS",
        "total_amount": "99.00",
        "sign": "FAKE_SIGNATURE"
    }
    response = client.post("/payment-callback", json=fake_callback)
    assert response.status_code == 403

def test_security_amount_tampering():
    """测试金额篡改攻击"""
    # 创建99元订单
    order = create_order(amount=99.00)
    payment = create_payment(order.id)

    # 尝试用0.01元支付
    callback = generate_callback(payment.payment_no, amount=0.01)
    response = client.post("/payment-callback", json=callback)

    # 应该被拒绝
    payment = get_payment(payment.payment_no)
    assert payment.status == PaymentStatus.FAILED
```

### 9. 配置管理

**强制环境变量**:
```python
class Settings(BaseSettings):
    # 支付配置（必填）
    ALIPAY_APP_ID: str = Field(..., min_length=1)
    ALIPAY_PRIVATE_KEY: str = Field(..., min_length=100)
    ALIPAY_PUBLIC_KEY: str = Field(..., min_length=100)

    @field_validator("ALIPAY_PRIVATE_KEY")
    def validate_private_key(cls, v):
        if "BEGIN PRIVATE KEY" not in v:
            raise ValueError("无效的私钥格式")
        return v
```

**开发/生产分离**:
```python
# 开发模式：跳过验证，方便测试
if settings.PAYMENT_DEV_MODE:
    logger.warning("支付开发模式已启用，跳过签名验证")
    return True

# 生产模式：严格验证
return verify_signature(callback_data)
```

### 10. 应急响应

**支付异常处理**:
```python
# 1. 记录详细日志
logger.error(f"支付异常: {error}", exc_info=True)

# 2. 通知相关人员
send_alert("支付系统异常", error_details)

# 3. 标记订单状态
order.mark_as_failed(error_message)

# 4. 提供补救方案
create_manual_review_task(order_id)
```

**监控告警**:
```yaml
告警规则:
  - 支付成功率 <95%: 立即告警
  - 签名验证失败 >10次/小时: 立即告警
  - 金额不匹配 >0次: 立即告警
  - 配额发放失败 >0次: 立即告警
  - 支付回调延迟 >10秒: 警告
```

---

## Schema-Model一致性最佳实践

### 1. 开发流程

**创建Schema前必须先读取Model**:
```python
# 1. 读取Model定义
class QuotaUsage(Base):
    __tablename__ = "quota_usage"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, nullable=False)
    quota_type = Column(String(50), nullable=False)
    amount = Column(Integer, nullable=False)
    usage_metadata = Column(TEXT)  # ✅ 注意字段名

# 2. 创建对应的Schema
class QuotaUsageResponse(BaseModel):
    id: int
    user_id: int
    quota_type: str
    amount: int
    metadata: Optional[dict] = None  # ✅ 对外使用metadata

    @field_validator('metadata', mode='before')
    @classmethod
    def extract_metadata(cls, v, info):
        # 从Model的usage_metadata字段提取
        if hasattr(v, 'usage_metadata'):
            return v.usage_metadata
        return v

    class Config:
        from_attributes = True  # ✅ 启用ORM模式
```

### 2. 字段映射规则

**命名一致性**:
```python
# ✅ 推荐：Schema字段名与Model字段名一致
class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    created_at: datetime

# ❌ 避免：字段名不一致
class UserResponse(BaseModel):
    id: int
    user_name: str  # Model中是username
    mail: str  # Model中是email
```

**类型映射**:
```python
# Model → Schema类型映射
Integer → int
String → str
Boolean → bool
DateTime → datetime
Text → str
JSON → dict
Enum → Enum (使用field_validator转换)
```

### 3. 枚举处理

**添加field_validator**:
```python
class OrderResponse(BaseModel):
    id: int
    status: str  # 对外使用字符串

    @field_validator('status', mode='before')
    @classmethod
    def convert_enum(cls, v):
        """将枚举转换为字符串"""
        if hasattr(v, 'value'):
            return v.value
        return v

    class Config:
        from_attributes = True
```

### 4. 验证测试

**测试Schema.from_orm()**:
```python
def test_schema_from_orm():
    """测试Schema可以从ORM对象创建"""
    # 创建Model实例
    user = User(
        id=1,
        username="test",
        email="test@example.com"
    )

    # 转换为Schema
    user_response = UserResponse.from_orm(user)

    # 验证字段
    assert user_response.id == 1
    assert user_response.username == "test"
    assert user_response.email == "test@example.com"
```

---

## 编排策略最佳实践

### 1. 策略选择矩阵

| 任务特征 | 推荐策略 | 理由 |
|----------|----------|------|
| 安全修复 | SEQUENTIAL | 按优先级顺序修复，避免冲突 |
| 独立功能开发 | PARALLEL | 最大化并行，提高效率 |
| 复杂功能开发 | HIERARCHICAL | 专家指导，保证质量 |
| 跨领域问题 | COLLABORATIVE | 多专家协作，全面考虑 |
| 探索创新 | COMPETITIVE | 多方案竞争，择优选择 |

### 2. Agent选择

**安全相关**:
- security-analyst: 安全审计、漏洞分析
- debugger: 安全问题修复

**开发相关**:
- general-purpose: 通用开发任务
- code-reviewer: 代码质量审查
- qa-reviewer: 质量验证

**研究相关**:
- Explore: 代码库探索
- architect: 架构设计

### 3. 质量保证

**多轮验证**:
1. 实现 → 单元测试
2. 单元测试 → 代码审查
3. 代码审查 → 集成测试
4. 集成测试 → 安全审查
5. 安全审查 → 部署

**检查清单**:
- [ ] 功能完整性
- [ ] 代码质量
- [ ] 测试覆盖
- [ ] 安全性
- [ ] 性能
- [ ] 文档

---

## 总结

### 核心原则

1. **安全优先**: 支付系统必须进行安全设计评审
2. **多层防护**: 不依赖单一安全措施
3. **测试驱动**: 单元测试与功能开发同步
4. **详细日志**: 记录所有关键操作和安全事件
5. **持续监控**: 实时监控关键指标，及时告警

### 关键实践

- ✅ 使用secrets模块生成随机数
- ✅ 使用Decimal处理金额
- ✅ 使用嵌套事务保护关键操作
- ✅ 使用悲观锁防止并发冲突
- ✅ 验证所有外部输入
- ✅ 记录详细的安全日志
- ✅ 编写充分的单元测试
- ✅ 进行安全测试和渗透测试

### 避免的错误

- ❌ 跳过安全设计评审
- ❌ 使用不安全的随机数
- ❌ 信任客户端传来的数据
- ❌ 忽略金额验证
- ❌ 缺少事务保护
- ❌ 缺少并发控制
- ❌ 缺少单元测试
- ❌ 记录敏感信息到日志
