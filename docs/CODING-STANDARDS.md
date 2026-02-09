# 代码规范指南

**项目**: AI赋能云平台
**版本**: 1.0
**生效日期**: [项目完成日期]

## 目录

- [变量命名规范](#变量命名规范)
- [函数和方法命名](#函数和方法命名)
- [类和接口命名](#类和接口命名)
- [常量命名](#常量命名)
- [代码注释规范](#代码注释规范)
- [Python代码规范](#python代码规范)
- [TypeScript/JavaScript代码规范](#typescriptjavascript代码规范)
- [提交前检查清单](#提交前检查清单)

---

## 变量命名规范

### Python 变量命名 (snake_case)

使用全小写，单词间用下划线分隔。

#### 规则

| 用途 | 规则 | 示例 |
|------|------|------|
| 普通变量 | snake_case | user_id, product_name, is_active |
| 布尔变量 | is_/has_/can_前缀 | is_verified, has_avatar, can_delete |
| 常量 | UPPER_SNAKE_CASE | MAX_UPLOAD_SIZE, DEFAULT_TIMEOUT |
| 私有变量 | _开头 + snake_case | _internal_state, _cache_data |
| 魔法变量 | 避免使用 | 使用具名常量替代 |

#### 示例

```python
# 正确
user_id = 123
is_admin = True
product_name = "有机大米"
email_verified = False
MAX_RETRIES = 3
_internal_cache = {}

# 错误
userId = 123  # 应该用snake_case
IsAdmin = True  # 大写首字母
productName = "有机大米"  # camelCase
status = 1  # 使用魔法数字，应该用常量或布尔值
```

### JavaScript/TypeScript 变量命名 (camelCase)

使用小驼峰法，首字母小写。

#### 规则

| 用途 | 规则 | 示例 |
|------|------|------|
| 普通变量 | camelCase | userId, productName, isActive |
| 布尔变量 | is/has/can前缀 | isVerified, hasAvatar, canDelete |
| 常量 | UPPER_CASE | MAX_UPLOAD_SIZE, DEFAULT_TIMEOUT |
| 私有属性 | #或_开头 | #internalState, _cacheData |
| 响应式引用 | Ref后缀或普通命名 | userRef或userData |

#### 示例

```typescript
// 正确
const userId = 123
const isAdmin = ref(true)
const productName = "有机大米"
const MAX_RETRIES = 3
const formatUserName = (name: string) => name.trim()

// 错误
const user_id = 123  // 应该用camelCase
const IsAdmin = true  // 大写首字母
const productName = 1  // 使用魔法数字
```

---

## 函数和方法命名

### Python 函数命名

使用 snake_case，动词开头。

```python
# 正确
def get_user_by_id(user_id: int) -> User:
    """获取用户"""
    pass

def validate_email(email: str) -> bool:
    """验证邮箱"""
    pass

def calculate_total_price(items: List[Item]) -> float:
    """计算总价"""
    pass

async def fetch_product_details(product_id: int) -> dict:
    """异步获取产品详情"""
    pass

# 错误
def GetUserByID(user_id):  # 应该用snake_case和小写
def validate(email):  # 太模糊
def calc(items):  # 缩写
```

### TypeScript/JavaScript 函数命名

使用 camelCase，动词开头。

```typescript
// 正确
function getUserById(userId: number): Promise<User> {
  return fetch(`/api/users/${userId}`).then(r => r.json())
}

const validateEmail = (email: string): boolean => {
  return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)
}

const handleFormSubmit = async (formData: FormData) => {
  // 处理表单提交
}

// 错误
function GetUserByID(userId) {  // 大写首字母
const validate_email = (email) => {}  // 应该用camelCase
async function fetch_data() {}  // snake_case
```

### Getter/Setter 方法

```typescript
// TypeScript类中
class User {
  #privateData: string

  // Getter
  get data(): string {
    return this.#privateData
  }

  // Setter
  set data(value: string) {
    this.#privateData = value
  }

  // 方法
  getData(): string {
    return this.#privateData
  }
}
```

---

## 类和接口命名

### Python 类命名

使用 PascalCase（大驼峰）。

```python
# 正确
class UserService:
    """用户服务"""
    pass

class ProductDTO:
    """产品数据传输对象"""
    pass

class InvalidEmailError(Exception):
    """邮箱格式无效错误"""
    pass

# 错误
class user_service:  # 应该是PascalCase
class Product_DTO:  # 应该是PascalCase
```

### TypeScript/JavaScript 类和接口命名

使用 PascalCase。

```typescript
// 接口
interface User {
  id: number
  name: string
  email: string
}

interface IUserService {
  getUser(id: number): Promise<User>
}

// 类
class UserService implements IUserService {
  async getUser(id: number): Promise<User> {
    // 实现
  }
}

// 类型别名
type UserStatus = 'active' | 'inactive' | 'banned'

// 枚举
enum UserRole {
  ADMIN = 'admin',
  USER = 'user',
  GUEST = 'guest'
}

// 错误
interface user {}  // 应该是PascalCase
class User_Service {}  // 应该是PascalCase
type user_status = 'active'  // 应该是PascalCase或camelCase
```

---

## 常量命名

### Python 常量

使用 UPPER_SNAKE_CASE，通常在模块顶部定义。

```python
# 正确
MAX_USERNAME_LENGTH = 100
DEFAULT_PAGE_SIZE = 20
API_TIMEOUT_SECONDS = 30
DATABASE_CONNECTION_POOL_SIZE = 10
ALLOWED_IMAGE_FORMATS = {'jpg', 'png', 'gif'}

# 在类中
class Config:
    DEBUG = True
    SECRET_KEY = "your-secret-key"
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB

# 错误
max_username_length = 100  # 应该是大写
MaxUsernameLength = 100  # 应该是大写
API_TIMEOUT = 30  # 单位应该在名称中
```

### TypeScript/JavaScript 常量

使用 UPPER_CASE 或 camelCase（取决于是否为对象）。

```typescript
// 简单常量 - UPPER_CASE
const MAX_USERNAME_LENGTH = 100
const DEFAULT_PAGE_SIZE = 20
const API_TIMEOUT_MS = 30000

// 对象常量 - camelCase（值为UPPER_CASE）
const config = {
  maxUploadSize: 10 * 1024 * 1024,  // 10MB
  defaultLanguage: 'zh-CN',
  supportedFormats: ['jpg', 'png', 'gif']
}

// 枚举 - UPPER_CASE
enum HttpStatus {
  OK = 200,
  CREATED = 201,
  BAD_REQUEST = 400,
  UNAUTHORIZED = 401,
  FORBIDDEN = 403,
  NOT_FOUND = 404,
  INTERNAL_ERROR = 500
}
```

---

## 代码注释规范

### 文件头注释

#### Python

```python
"""
模块名称: 用户服务模块

功能描述:
- 用户账户管理
- 用户认证和授权
- 用户资料维护

版本: 1.0
创建日期: [项目完成日期]
最后修改: [项目完成日期]
作者: 团队名
"""
```

#### TypeScript/JavaScript

```typescript
/**
 * 用户服务模块
 *
 * 功能:
 * - 用户账户管理
 * - 用户认证和授权
 * - 用户资料维护
 *
 * @version 1.0
 * @author 团队名
 * @since [项目完成日期]
 */
```

### 函数/方法注释

#### Python

```python
def create_user(email: str, password: str, name: str) -> User:
    """
    创建新用户账户。

    参数:
        email (str): 用户邮箱，必须唯一
        password (str): 用户密码，至少8个字符，需包含大小写字母、数字和特殊字符
        name (str): 用户名称

    返回:
        User: 创建的用户对象

    抛出:
        ValueError: 邮箱已存在或密码强度不足
        DatabaseError: 数据库操作失败

    示例:
        >>> user = create_user('test@example.com', 'Pass123!', 'Test User')
        >>> print(user.email)
        test@example.com
    """
    pass
```

#### TypeScript/JavaScript

```typescript
/**
 * 创建新用户账户
 *
 * @param email - 用户邮箱，必须唯一
 * @param password - 用户密码，至少8个字符，需包含大小写字母、数字和特殊字符
 * @param name - 用户名称
 *
 * @returns 创建的用户对象
 *
 * @throws {ValueError} 邮箱已存在或密码强度不足
 * @throws {DatabaseError} 数据库操作失败
 *
 * @example
 * const user = await createUser('test@example.com', 'Pass123!', 'Test User')
 * console.log(user.email)  // 'test@example.com'
 */
async function createUser(
  email: string,
  password: string,
  name: string
): Promise<User> {
  // 实现
}
```

### 内联注释

```python
# Python
# 验证邮箱格式和唯一性
if not is_valid_email(email) or user_exists(email):
    raise ValueError("邮箱格式无效或已存在")

# 密码加密存储（bcrypt）
hashed_password = hash_password(password)
```

```typescript
// TypeScript
// 验证邮箱格式和唯一性
if (!isValidEmail(email) || userExists(email)) {
  throw new Error('邮箱格式无效或已存在')
}

// 密码加密存储 (bcrypt)
const hashedPassword = hashPassword(password)
```

### 注释写作要点

- 使用中文或英文，保持一致
- 解释 **为什么**，不是 **是什么**（代码已经说明了）
- 避免过度注释
- 保持注释的时效性
- 复杂算法或业务逻辑添加注释

---

## Python代码规范

### 导入规范

```python
# 顺序: 标准库 -> 第三方库 -> 本地库
import json
import logging
from datetime import datetime
from typing import List, Optional, Dict

import sqlalchemy
from fastapi import FastAPI
from pydantic import BaseModel

from app.models import User
from app.schemas import UserCreate
from app.services import user_service
```

### 类型注解

```python
from typing import List, Optional, Dict, Tuple, Union

# 简单类型
def get_user(user_id: int) -> User:
    pass

# 可选类型
def find_user(email: Optional[str] = None) -> Optional[User]:
    pass

# 集合类型
def get_users(ids: List[int]) -> List[User]:
    pass

# 字典类型
def parse_data(data: Dict[str, any]) -> Dict[str, str]:
    pass

# 联合类型
def process(value: Union[int, str]) -> int:
    pass
```

### 异常处理

```python
# 不要这样做
try:
    result = do_something()
except:  # 捕获所有异常
    pass

# 要这样做
try:
    result = do_something()
except ValueError as e:
    logger.error(f"参数错误: {e}")
    raise
except DatabaseError as e:
    logger.error(f"数据库错误: {e}")
    raise HTTPException(status_code=500, detail="操作失败")
except Exception as e:
    logger.error(f"未预期的错误: {e}")
    raise
```

---

## TypeScript/JavaScript代码规范

### 导入规范

```typescript
// 顺序: 第三方库 -> 本地库
import { ref, computed, defineComponent } from 'vue'
import { useRouter } from 'vue-router'

import { userApi } from '@/api'
import { useUserStore } from '@/stores'
import type { User, UserCreate } from '@/types'
```

### 类型定义

```typescript
// 接口优先于类型别名（对象类型）
interface User {
  id: number
  email: string
  name: string
  isActive: boolean
}

// 类型别名用于原始类型、联合类型
type UserId = number
type UserStatus = 'active' | 'inactive' | 'banned'
type UserOrAdmin = User | Admin

// 泛型
interface ApiResponse<T> {
  code: number
  message: string
  data: T
}

// 函数签名
type CreateUserFn = (data: UserCreate) => Promise<User>
```

### 异步处理

```typescript
// 使用 async/await
async function fetchUser(id: number): Promise<User> {
  try {
    const response = await fetch(`/api/users/${id}`)
    if (!response.ok) throw new Error('网络请求失败')
    return response.json()
  } catch (error) {
    logger.error('获取用户失败:', error)
    throw error
  }
}

// Vue 组件中
const loading = ref(false)
const error = ref<string | null>(null)

const handleSubmit = async () => {
  loading.value = true
  error.value = null
  try {
    await submitForm()
  } catch (err) {
    error.value = err instanceof Error ? err.message : '操作失败'
  } finally {
    loading.value = false
  }
}
```

---

## 提交前检查清单

在提交代码前，请检查以下项目：

### 代码质量

- [ ] 遵循本规范的命名规范
- [ ] 添加了必要的类型注解（TS/Python）
- [ ] 错误处理完整（try-catch 或异常处理）
- [ ] 没有使用 console.log 或 print（调试代码）
- [ ] 没有注释掉的大块代码
- [ ] 没有 TODO/FIXME 注释（除非记录在 Issue 中）

### 测试

- [ ] 单元测试通过
- [ ] 测试覆盖率 > 70%
- [ ] 没有跳过的测试 (skip/xit)

### 文档

- [ ] 代码注释清晰
- [ ] 公开接口有文档说明
- [ ] 复杂算法有说明
- [ ] 修改了公开API时更新了文档

### 性能

- [ ] 没有明显的性能问题
- [ ] 没有死循环或内存泄漏
- [ ] 大列表使用了虚拟滚动

### 安全

- [ ] 没有硬编码的密钥或密码
- [ ] SQL 语句使用参数化查询
- [ ] 用户输入进行了验证和转义

---

**维护者**: 开发团队
**最后更新**: [项目完成日期]
**下一个更新**: 发现规范问题或添加新规范时
