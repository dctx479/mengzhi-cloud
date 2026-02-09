# 后端单元测试文档

## 概述

本文档介绍"内蒙古农畜产品品牌营销AI赋能云平台"的后端单元测试框架。

**测试框架**: Pytest
**数据库**: SQLite（内存数据库）
**覆盖率目标**: 70%+
**测试用例总数**: 100+

---

## 项目结构

```
backend/
├── tests/
│   ├── conftest.py                 # pytest配置和全局fixtures
│   ├── test_auth_service.py        # 认证服务测试 (~60个测试)
│   ├── test_product_service.py     # 产品服务测试 (~25个测试)
│   ├── test_auth_api.py            # 认证API测试 (~15个测试)
│   ├── test_products_api.py        # 产品API测试 (~20个测试)
│   ├── test_chat_api.py            # 对话API测试 (~15个测试)
│   ├── test_models.py              # 数据模型测试 (~20个测试)
│   └── README.md                   # 测试说明文档
├── pytest.ini                      # pytest配置
├── requirements-test.txt           # 测试依赖
└── app/                            # 应用源代码
```

---

## 依赖安装

### 1. 安装pytest及插件

```bash
pip install -r requirements-test.txt
```

### 2. requirements-test.txt内容

```
pytest==7.4.0
pytest-cov==4.1.0
pytest-asyncio==0.21.1
pytest-timeout==2.1.0
pytest-mock==3.11.1
fastapi==0.104.1
sqlalchemy==2.0.21
sqlalchemy-utils==0.41.1
pydantic==2.4.2
pydantic-settings==2.0.3
python-jose==3.3.0
passlib==1.7.4
bcrypt==4.1.0
python-multipart==0.0.6
email-validator==2.1.0
httpx==0.25.0
redis==5.0.0
```

---

## 快速开始

### 1. 运行所有测试

```bash
# 进入backend目录
cd backend

# 运行所有测试
pytest

# 运行指定测试文件
pytest tests/test_auth_service.py -v

# 运行指定测试类
pytest tests/test_auth_service.py::TestPasswordHandling -v

# 运行指定测试用例
pytest tests/test_auth_service.py::TestPasswordHandling::test_hash_password_creates_hash -v
```

### 2. 查看覆盖率报告

```bash
# 生成HTML覆盖率报告
pytest --cov=app --cov-report=html

# 查看终端覆盖率报告
pytest --cov=app --cov-report=term-missing
```

### 3. 运行特定标记的测试

```bash
# 运行所有认证相关测试
pytest -m auth

# 运行所有产品相关测试
pytest -m product

# 运行所有模型测试
pytest -m models

# 运行单元测试（不包括集成测试）
pytest -m unit
```

### 4. 调试和详细输出

```bash
# 显示详细信息和本地变量
pytest -vv -l

# 显示print输出
pytest -s

# 显示最慢的10个测试
pytest --durations=10

# 在第一个失败处停止
pytest -x

# 在指定数量失败后停止
pytest --maxfail=3
```

---

## 测试套件详解

### 1. 认证服务测试 (test_auth_service.py)

**覆盖功能**:
- 密码哈希和验证
- JWT Token生成和验证
- Token刷新和黑名单
- 账号状态检查
- 登录尝试计数
- 验证码管理
- 数据脱敏

**测试用例数**: ~60个

**关键测试**:
```python
# 密码处理
test_hash_password_creates_hash
test_verify_password_correct
test_verify_password_incorrect

# Token管理
test_create_access_token
test_decode_token_success
test_decode_token_expired

# Token刷新
test_refresh_tokens_success
test_refresh_token_expired

# 验证码
test_set_verification_code
test_verify_code_success
test_verify_code_incorrect
```

### 2. 产品服务测试 (test_product_service.py)

**覆盖功能**:
- 产品CRUD操作
- 搜索和筛选
- 分页功能
- SKU唯一性验证
- 特殊查询（精选、分类、地区）
- 统计信息

**测试用例数**: ~25个

**关键测试**:
```python
# CRUD
test_create_product_success
test_get_product_by_id_success
test_update_product_success
test_delete_product_success

# 筛选和搜索
test_list_products_search
test_list_products_filter_category
test_list_products_filter_featured

# 分页
test_list_products_pagination

# 特殊查询
test_get_featured_products
test_get_products_by_category
test_get_products_by_region
```

### 3. 数据模型测试 (test_models.py)

**覆盖功能**:
- 模型字段验证
- 关系映射
- to_dict()方法
- Enum验证
- 唯一性约束
- 默认值

**测试用例数**: ~20个

**关键测试**:
```python
# User模型
test_user_creation
test_user_unique_constraints

# Product模型
test_product_creation
test_product_sku_uniqueness
test_product_with_all_fields

# 基类方法
test_base_model_to_dict
test_base_model_to_dict_exclude
test_base_model_from_dict
```

### 4. 认证API测试 (test_auth_api.py)

**覆盖功能**:
- 用户注册端点
- 用户登录端点
- Token刷新端点
- 用户登出端点
- 获取用户信息端点
- 修改密码端点

**测试用例数**: ~15个

**关键测试**:
```python
# 注册
test_register_personal_user_success
test_register_duplicate_username

# 登录
test_login_success
test_login_with_email
test_login_wrong_password

# Token
test_refresh_token_success

# 用户信息
test_get_me_success
test_get_me_without_token

# 密码
test_change_password_success
```

### 5. 产品API测试 (test_products_api.py)

**覆盖功能**:
- 产品列表查询
- 产品详情查询
- 创建产品
- 更新产品
- 删除产品
- 特殊查询

**测试用例数**: ~20个

### 6. 对话API测试 (test_chat_api.py)

**覆盖功能**:
- 创建对话
- 获取对话列表
- 发送消息
- 获取消息历史
- 删除对话

**测试用例数**: ~15个

---

## Fixtures说明

### 数据库Fixtures

```python
# 测试数据库引擎（会话级别）
test_db_engine: Engine

# 测试数据库会话（函数级别）
test_db_session: Session

# 覆盖FastAPI依赖
db_override: Session
```

### 客户端Fixtures

```python
# TestClient实例
client: TestClient

# 认证headers
auth_headers: Dict[str, str]
```

### 用户数据Fixtures

```python
# 个人用户数据
test_user_data: Dict

# 企业用户数据
test_enterprise_user_data: Dict

# 用户Token
test_user_token: Tuple[access_token, refresh_token, user_uuid]
```

### 产品数据Fixtures

```python
# 单个产品数据
test_product_data: Dict

# 多个产品数据
test_product_data_multiple: List[Dict]
```

### 对话数据Fixtures

```python
# 对话数据
test_conversation_data: Dict

# 消息数据
test_message_data: Dict
```

### 模拟Fixtures

```python
# Redis模拟
mock_redis: MagicMock

# DeepSeek AI模拟
mock_deepseek_client: MagicMock

# 邮件服务模拟
mock_email_service: MagicMock

# 应用补丁
patch_redis, patch_deepseek, patch_email
```

---

## 最佳实践

### 1. 编写测试

**单元测试原则**:
- 一个测试函数测试一个功能
- 使用清晰的测试名称
- 遵循AAA模式 (Arrange, Act, Assert)

```python
@pytest.mark.unit
def test_hash_password_creates_hash(self):
    """测试密码哈希生成"""
    # Arrange - 准备测试数据
    password = "TestPassword123!"

    # Act - 执行被测试函数
    hashed = AuthService.hash_password(password)

    # Assert - 验证结果
    assert hashed != password
    assert len(hashed) > 20
```

### 2. 使用Fixtures

```python
@pytest.mark.unit
def test_create_product(self, test_db_session, test_product_data):
    """使用fixtures创建产品"""
    service = ProductService(test_db_session)
    product = service.create_product(test_product_data, user_id=1)

    assert product is not None
    assert product.name == test_product_data["name"]
```

### 3. 模拟外部依赖

```python
@pytest.mark.unit
def test_refresh_tokens(self, test_db_session):
    """模拟外部服务调用"""
    auth_service = AuthService(test_db_session)

    with patch.object(auth_service, 'redis_client') as mock_redis:
        auth_service.add_token_to_blacklist("jti", 3600)
        mock_redis.setex.assert_called_once()
```

### 4. 参数化测试

```python
@pytest.mark.parametrize("email,expected", [
    ("test@example.com", "te***@example.com"),
    ("a@example.com", "a***@example.com"),
    (None, None),
])
def test_mask_email(self, email, expected):
    """参数化测试数据脱敏"""
    result = AuthService.mask_email(email)
    assert result == expected
```

---

## 覆盖率报告

运行以下命令生成覆盖率报告：

```bash
pytest --cov=app --cov-report=html --cov-report=term-missing
```

**目标**:
- 服务层覆盖率: 80%+
- API层覆盖率: 70%+
- 模型层覆盖率: 60%+
- 总体覆盖率: 70%+

**查看报告**:
```bash
# 打开HTML报告
open coverage_html/index.html  # macOS
start coverage_html/index.html # Windows
xdg-open coverage_html/index.html # Linux
```

---

## CI/CD集成

### GitHub Actions示例

```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest

    steps:
    - uses: actions/checkout@v2
    - uses: actions/setup-python@v2
      with:
        python-version: 3.11

    - name: Install dependencies
      run: |
        pip install -r requirements-test.txt

    - name: Run tests
      run: |
        pytest tests/ --cov=app --cov-report=xml

    - name: Upload coverage
      uses: codecov/codecov-action@v2
```

---

## 常见问题

### Q1: 如何运行指定的测试？

```bash
# 运行单个测试文件
pytest tests/test_auth_service.py

# 运行单个测试类
pytest tests/test_auth_service.py::TestPasswordHandling

# 运行单个测试方法
pytest tests/test_auth_service.py::TestPasswordHandling::test_hash_password_creates_hash
```

### Q2: 如何调试测试？

```bash
# 显示所有print输出
pytest -s

# 添加断点
pytest --pdb  # 在失败时进入调试器

# 显示本地变量
pytest -l
```

### Q3: 如何跳过某些测试？

```python
@pytest.mark.skip(reason="Not implemented yet")
def test_something(self):
    pass

@pytest.mark.skipif(sys.version_info < (3, 11), reason="requires python3.11+")
def test_something(self):
    pass
```

### Q4: 如何处理慢速测试？

```bash
# 显示最慢的10个测试
pytest --durations=10

# 跳过慢速测试
pytest -m "not slow"
```

---

## 故障排除

### 问题: 数据库连接失败

**解决方案**:
```bash
# 检查DATABASE_URL设置
export DATABASE_URL="sqlite:///:memory:"

# 检查数据库表
python -m app.database init_db
```

### 问题: Redis连接失败

**解决方案**:
```bash
# 使用模拟Redis
export REDIS_URL="redis://localhost:6379/0"

# 测试中自动使用mock redis
# 参见conftest.py的patch_redis fixture
```

### 问题: 导入错误

**解决方案**:
```bash
# 确保backend目录在PYTHONPATH中
export PYTHONPATH="${PYTHONPATH}:$(pwd)/backend"

# 或在conftest.py中添加
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
```

---

## 贡献指南

编写新测试时：

1. ✅ 遵循已有的测试结构
2. ✅ 使用描述性的测试名称
3. ✅ 添加测试文档字符串
4. ✅ 使用@pytest.mark.unit标记
5. ✅ 确保测试隔离（不依赖其他测试）
6. ✅ 使用fixtures避免重复代码
7. ✅ 添加异常情况的测试

---

## 相关文档

- [Pytest官方文档](https://docs.pytest.org/)
- [FastAPI测试文档](https://fastapi.tiangolo.com/tutorial/testing/)
- [SQLAlchemy测试最佳实践](https://docs.sqlalchemy.org/en/14/orm/session_basics.html)

---

## 版本历史

| 版本 | 日期 | 说明 |
|-----|------|------|
| 1.0 | [项目完成日期] | 初版，包含100+个测试用例 |

---

## 联系方式

有任何问题或建议，请联系测试团队。
