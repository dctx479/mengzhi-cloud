# 测试覆盖率改进指南

## 当前状态

- **总测试数**: 383个
- **当前覆盖率**: 26.23%
- **目标覆盖率**: 70%
- **需要提升**: 43.77%

## 优先级模块（覆盖率最低）

### 🔴 高优先级（0-10%覆盖率）

1. **app/utils.py** (0%)
   - 工具函数集合
   - 建议：为每个工具函数添加单元测试

2. **app/tasks/** (0%)
   - 后台任务和调度器
   - 建议：使用Mock测试异步任务

3. **app/services/usage_stats.py** (0%)
   - 使用统计服务
   - 建议：测试统计数据收集和聚合

4. **app/services/risk_control_service.py** (8%)
   - 风险控制服务
   - 建议：测试风险检测和控制逻辑

5. **app/services/sla_report.py** (8%)
   - SLA报告服务
   - 建议：测试报告生成和数据计算

### 🟡 中优先级（10-20%覆盖率）

6. **app/services/tenant_db_manager.py** (10%)
   - 租户数据库管理
   - 建议：测试数据库创建、备份、恢复

7. **app/services/sla_monitor.py** (11%)
   - SLA监控服务
   - 建议：测试监控指标和告警

8. **app/services/strict_billing.py** (13%)
   - 严格计费服务
   - 建议：测试计费逻辑和幂等性

9. **app/services/billing_engine.py** (13%)
   - 计费引擎
   - 建议：测试计费规则和计算

10. **app/services/upload_service.py** (14%)
    - 文件上传服务
    - 建议：测试文件验证和存储

## 测试策略

### 1. 单元测试

为每个服务类编写单元测试：

```python
# tests/unit/services/test_usage_stats.py
import pytest
from app.services.usage_stats import UsageStatsService

class TestUsageStatsService:
    def test_collect_stats(self, db):
        service = UsageStatsService(db)
        stats = service.collect_stats(user_id=1)
        assert stats is not None
        assert "total_requests" in stats
```

### 2. 集成测试

测试服务间的交互：

```python
# tests/integration/test_billing_flow.py
import pytest
from app.services.billing_engine import BillingEngine
from app.services.quota_service import QuotaService

class TestBillingFlow:
    def test_complete_billing_flow(self, db):
        # 测试从配额检查到计费的完整流程
        pass
```

### 3. Mock外部依赖

使用pytest-mock模拟外部服务：

```python
def test_ai_service_with_mock(mocker):
    mock_response = mocker.Mock()
    mock_response.json.return_value = {"result": "success"}
    mocker.patch("requests.post", return_value=mock_response)

    # 测试AI服务调用
```

### 4. 数据库测试

使用fixtures提供测试数据：

```python
@pytest.fixture
def sample_user(db):
    user = User(username="test", email="test@example.com")
    db.add(user)
    db.commit()
    return user

def test_user_service(db, sample_user):
    # 使用sample_user进行测试
    pass
```

## 测试工具配置

### pytest.ini

```ini
[pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts =
    -v
    --cov=app
    --cov-report=html
    --cov-report=term
    --cov-fail-under=70
```

### conftest.py

```python
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.database import Base

@pytest.fixture(scope="session")
def engine():
    return create_engine("sqlite:///:memory:")

@pytest.fixture(scope="function")
def db(engine):
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()
    Base.metadata.drop_all(engine)
```

## 执行计划

### 阶段1：基础覆盖（目标：40%）
- [ ] 为所有0%覆盖率的模块添加基础测试
- [ ] 测试核心业务逻辑（认证、计费、配额）
- [ ] 预计增加：14%

### 阶段2：服务测试（目标：55%）
- [ ] 完善服务层测试
- [ ] 添加集成测试
- [ ] 测试错误处理和边界情况
- [ ] 预计增加：15%

### 阶段3：全面覆盖（目标：70%）
- [ ] 测试工具函数和辅助类
- [ ] 测试后台任务和调度器
- [ ] 测试API端点
- [ ] 预计增加：15%

## 测试命令

```bash
# 运行所有测试
pytest tests/

# 运行特定模块测试
pytest tests/unit/services/test_usage_stats.py

# 生成覆盖率报告
pytest --cov=app --cov-report=html

# 只运行失败的测试
pytest --lf

# 并行运行测试
pytest -n auto
```

## 持续改进

1. **每次提交都运行测试**
   - 使用pre-commit hooks
   - CI/CD自动运行测试

2. **定期审查覆盖率**
   - 每周检查覆盖率报告
   - 识别未覆盖的关键代码

3. **测试驱动开发（TDD）**
   - 新功能先写测试
   - 确保测试通过后再提交

4. **代码审查**
   - 要求PR包含测试
   - 审查测试质量和覆盖率

## 参考资源

- [pytest文档](https://docs.pytest.org/)
- [pytest-cov文档](https://pytest-cov.readthedocs.io/)
- [FastAPI测试指南](https://fastapi.tiangolo.com/tutorial/testing/)
- [SQLAlchemy测试最佳实践](https://docs.sqlalchemy.org/en/14/orm/session_transaction.html#joining-a-session-into-an-external-transaction-such-as-for-test-suites)
