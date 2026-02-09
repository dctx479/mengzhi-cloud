# 后端单元测试 - 快速参考指南

## 🚀 快速开始 (5分钟)

```bash
# 1. 进入backend目录
cd backend

# 2. 安装测试依赖（首次）
pip install -r requirements-test.txt

# 3. 运行所有测试
pytest

# 4. 查看覆盖率报告
pytest --cov=app --cov-report=html
open coverage_html/index.html
```

---

## 📋 常用命令

### 基本命令

```bash
# 运行所有测试
pytest

# 运行所有测试（详细输出）
pytest -v

# 运行指定文件
pytest tests/test_auth_service.py

# 运行指定测试类
pytest tests/test_auth_service.py::TestPasswordHandling

# 运行指定测试方法
pytest tests/test_auth_service.py::TestPasswordHandling::test_hash_password_creates_hash
```

### 覆盖率命令

```bash
# 生成终端覆盖率报告
pytest --cov=app --cov-report=term-missing

# 生成XML覆盖率报告
pytest --cov=app --cov-report=xml

# 生成HTML覆盖率报告
pytest --cov=app --cov-report=html

# 查看HTML报告
open coverage_html/index.html
```

### 调试命令

```bash
# 显示所有print输出
pytest -s

# 显示详细信息
pytest -vv

# 在失败处进入调试器
pytest --pdb

# 显示最慢的10个测试
pytest --durations=10

# 在第一个失败处停止
pytest -x

# 在3个失败后停止
pytest --maxfail=3
```

### 筛选命令

```bash
# 运行特定标记的测试
pytest -m auth          # 认证测试
pytest -m product       # 产品测试
pytest -m chat          # 对话测试
pytest -m models        # 模型测试
pytest -m unit          # 单元测试

# 跳过慢速测试
pytest -m "not slow"

# 按关键字筛选
pytest -k "password"    # 运行名称包含password的测试
pytest -k "not slow"    # 跳过名称包含slow的测试
```

### Makefile命令

```bash
make help               # 显示帮助信息
make install            # 安装依赖
make test               # 运行所有测试
make test-verbose       # 详细输出运行测试
make test-auth          # 运行认证相关测试
make test-product       # 运行产品相关测试
make test-chat          # 运行对话相关测试
make test-models        # 运行模型相关测试
make coverage           # 生成覆盖率报告
make coverage-html      # 生成HTML覆盖率报告
make clean              # 清理测试生成的文件
```

---

## 📂 测试文件概览

| 文件 | 测试数 | 说明 |
|------|--------|------|
| `test_auth_service.py` | ~60 | 密码、Token、验证码、数据脱敏等 |
| `test_product_service.py` | ~25 | CRUD、搜索、分页、统计等 |
| `test_auth_api.py` | ~15 | 注册、登录、Token、用户信息等 |
| `test_products_api.py` | ~20 | 产品列表、创建、更新、删除等 |
| `test_chat_api.py` | ~15 | 对话、消息、历史等 |
| `test_models.py` | ~20 | 模型字段、关系、验证等 |

---

## 🔧 Fixtures 快速查看

```python
# 数据库
test_db_session        # 测试数据库会话
db_override           # 覆盖FastAPI依赖

# 客户端
client                # FastAPI TestClient

# 用户
test_user_data            # 个人用户数据
test_enterprise_user_data # 企业用户数据
test_user_token          # 用户Token (access, refresh, uuid)
auth_headers             # 认证headers

# 产品
test_product_data        # 单个产品数据
test_product_data_multiple # 多个产品数据

# 对话
test_conversation_data   # 对话数据
test_message_data       # 消息数据

# 模拟
mock_redis              # Redis模拟
mock_deepseek_client    # AI客户端模拟
mock_email_service      # 邮件服务模拟
patch_redis, patch_deepseek, patch_email  # 补丁
```

---

## 💡 编写测试的模板

### 基本模板

```python
import pytest

class TestFeature:
    """功能测试"""

    @pytest.mark.unit
    def test_something(self):
        """测试某个功能"""
        # Arrange - 准备
        value = 10

        # Act - 执行
        result = some_function(value)

        # Assert - 验证
        assert result == 20
```

### 使用Fixtures

```python
@pytest.mark.unit
def test_with_fixtures(self, test_db_session, test_product_data):
    """使用Fixtures进行测试"""
    service = ProductService(test_db_session)
    product = service.create_product(test_product_data, user_id=1)

    assert product is not None
    assert product.name == test_product_data["name"]
```

### 测试异常

```python
@pytest.mark.unit
def test_raises_exception(self):
    """测试异常抛出"""
    with pytest.raises(ValueError) as exc_info:
        bad_function()

    assert "错误信息" in str(exc_info.value)
```

### 模拟外部依赖

```python
@pytest.mark.unit
def test_with_mock(self, test_db_session):
    """使用Mock"""
    auth_service = AuthService(test_db_session)

    with patch.object(auth_service, 'redis_client') as mock_redis:
        auth_service.add_token_to_blacklist("jti", 3600)
        mock_redis.setex.assert_called_once()
```

---

## 📊 覆盖率目标

| 层级 | 目标 | 状态 |
|------|------|------|
| 服务层 | 80%+ | ✅ |
| API层 | 70%+ | ✅ |
| 模型层 | 60%+ | ✅ |
| **总体** | **70%+** | **✅** |

---

## 🐛 故障排除

### 问题：导入错误

```bash
# 解决：设置PYTHONPATH
export PYTHONPATH="${PYTHONPATH}:$(pwd)/backend"
pytest
```

### 问题：数据库错误

```bash
# 解决：检查数据库配置
export DATABASE_URL="sqlite:///:memory:"
pytest
```

### 问题：Redis连接失败

```bash
# 解决：自动使用Mock Redis
# conftest.py已配置，无需手动处理
```

### 问题：测试超时

```bash
# 解决：增加超时时间
pytest --timeout=600
```

---

## 🎯 最佳实践

### ✅ Do（应该做）

- 使用清晰的测试名称: `test_create_product_success`
- 使用Fixtures避免重复代码
- 编写异常情况的测试
- 使用Mock隔离外部依赖
- 遵循AAA模式 (Arrange, Act, Assert)
- 保持测试简洁和专注
- 添加文档字符串说明测试目的

### ❌ Don't（不应该做）

- 在测试中依赖其他测试的结果
- 编写过大或复杂的测试
- 忽视异常情况和边界值
- 直接调用真实的外部服务
- 使用不清晰或过长的测试名称
- 在测试中修改全局状态
- 忽视测试的隔离性

---

## 📚 相关资源

- [Pytest官方文档](https://docs.pytest.org/)
- [FastAPI测试](https://fastapi.tiangolo.com/tutorial/testing/)
- [unittest.mock文档](https://docs.python.org/3/library/unittest.mock.html)
- [SQLAlchemy测试](https://docs.sqlalchemy.org/en/14/)

---

## 📞 获取帮助

查看完整文档：
```bash
cat tests/README.md
```

查看测试配置：
```bash
cat pytest.ini
```

查看依赖：
```bash
cat requirements-test.txt
```

---

## 版本信息

- **框架版本**: 1.0.0
- **Pytest版本**: 7.4.0+
- **Python版本**: 3.9+
- **更新日期**: [项目完成日期]

---

## 快速链接

| 项目 | 位置 |
|------|------|
| 所有测试文件 | `backend/tests/` |
| 配置文件 | `backend/pytest.ini` |
| Fixtures定义 | `backend/tests/conftest.py` |
| 完整文档 | `backend/tests/README.md` |
| 完成报告 | `TESTING_SUMMARY.md` |

---

**祝测试顺利！** 🎉
