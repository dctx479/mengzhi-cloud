# 代码质量改进方案

## 执行日期: 2026-01-21

## 一、类型注解规范

### 1.1 所有公共函数必须有完整类型注解

```python
# ❌ 错误
def create_user(username, email):
    pass

# ✅ 正确
def create_user(username: str, email: str) -> User:
    pass
```

### 1.2 复杂类型使用typing模块

```python
from typing import Optional, List, Dict, Any, Tuple

def get_products(
    page: int = 1,
    filters: Optional[Dict[str, Any]] = None
) -> Tuple[List[Product], int]:
    pass
```

## 二、异常处理规范

### 2.1 禁止使用裸except

```python
# ❌ 错误
try:
    operation()
except:
    pass

# ✅ 正确
try:
    operation()
except ValueError as e:
    logger.error(f"参数错误: {e}")
    raise ValidationError("参数无效")
except Exception as e:
    logger.error(f"未知错误: {e}")
    raise BusinessException("操作失败")
```

### 2.2 统一异常处理模式

**API层**: 捕获并转换为HTTP响应
```python
try:
    result = service.operation()
    return success_response(data=result)
except BusinessException as e:
    return error_response(code=e.code, message=e.message)
except Exception as e:
    logger.error(f"系统错误: {e}", exc_info=True)
    return error_response(code=ErrorCode.SYSTEM_ERROR)
```

**Service层**: 抛出业务异常
```python
try:
    data = db.query(Model).first()
    if not data:
        raise RecordNotFoundError("记录")
    return data
except SQLAlchemyError as e:
    logger.error(f"数据库错误: {e}")
    raise BusinessException("数据库操作失败")
```

### 2.3 异常必须包含明确信息

```python
# ❌ 错误
raise BusinessException("操作失败")

# ✅ 正确
raise BusinessException(
    code=ErrorCode.VALIDATION_ERROR,
    message=f"用户名 '{username}' 已存在"
)
```

## 三、日志规范

### 3.1 日志级别使用标准

- **DEBUG**: 详细调试信息
- **INFO**: 关键业务操作
- **WARNING**: 业务异常（可恢复）
- **ERROR**: 系统错误（需人工介入）

```python
# 正常操作
logger.info(f"用户登录成功: user_id={user_id}")

# 业务异常
logger.warning(f"用户名已存在: {username}")

# 系统错误
logger.error(f"数据库连接失败: {e}", exc_info=True)
```

### 3.2 关键操作必须记录

```python
def create_product(request: ProductCreateRequest) -> Product:
    logger.info(f"开始创建产品: name={request.name}")
    
    product = Product(**request.dict())
    db.add(product)
    db.commit()
    
    logger.info(f"产品创建成功: id={product.id}")
    return product
```

## 四、代码复杂度控制

### 4.1 单个函数不超过50行

```python
# ❌ 错误: 115行的register函数
async def register(request, db):
    # 验证验证码
    # 检查用户名
    # 检查邮箱
    # 检查手机号
    # 创建用户
    # 返回响应
    pass

# ✅ 正确: 拆分为多个函数
async def register(request, db):
    await validate_registration(request, db)
    user = await create_user(request, db)
    return build_register_response(user)

async def validate_registration(request, db):
    validate_verification_code(request)
    check_username_exists(request.username, db)
    check_email_exists(request.email, db)
```

### 4.2 提取重复代码

```python
# ❌ 错误: 每个端点重复异常处理
@router.get("/endpoint1")
async def endpoint1():
    try:
        ...
    except BusinessException as e:
        return JSONResponse(...)
    except Exception as e:
        return JSONResponse(...)

# ✅ 正确: 使用装饰器
def handle_exceptions(func):
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except BusinessException as e:
            return error_response(e.code, e.message)
        except Exception as e:
            logger.error(f"未处理异常: {e}")
            return error_response(ErrorCode.SYSTEM_ERROR)
    return wrapper

@router.get("/endpoint1")
@handle_exceptions
async def endpoint1():
    ...
```

## 五、常量和配置

### 5.1 魔法数字提取为常量

```python
# ❌ 错误
if similarity > 0.85:
    return True

# ✅ 正确
SIMILARITY_THRESHOLD = 0.85

if similarity > SIMILARITY_THRESHOLD:
    return True
```

### 5.2 配置集中管理

```python
# config/constants.py
class ContentConfig:
    SIMILARITY_THRESHOLD = 0.85
    MAX_RETRY_ATTEMPTS = 3
    CACHE_TTL_SECONDS = 300
```

## 六、优先修复清单

### 立即修复 (P0)
1. ✅ 修复 `backend/app/api/auth.py:584,687` - raise APIResponse错误
2. ✅ 修复 `backend/app/services/captcha_service.py` - 裸except
3. ✅ 修复 `backend/app/api/exports.py` - 裸except

### 本周修复 (P1)
4. 为所有service层函数添加类型注解
5. 统一API层异常处理模式
6. 拆分超过50行的函数

### 持续改进 (P2)
7. 添加关键操作日志
8. 提取魔法数字为常量
9. 减少代码重复

## 七、检查工具

### 7.1 使用mypy检查类型
```bash
mypy backend/app --ignore-missing-imports
```

### 7.2 使用pylint检查代码质量
```bash
pylint backend/app --disable=C0111
```

### 7.3 使用black格式化代码
```bash
black backend/app
```

---

**更新人**: AI Code Reviewer
**更新时间**: 2026-01-21
