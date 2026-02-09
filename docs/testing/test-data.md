# 测试数据准备

**项目**: 内蒙古农畜产品品牌营销AI赋能云平台
**版本**: v1.0.0
**编写日期**: [项目完成日期]

---

## 目录

- [1. 种子数据概览](#1-种子数据概览)
- [2. 用户测试数据](#2-用户测试数据)
- [3. 产品测试数据](#3-产品测试数据)
- [4. AI对话测试数据](#4-ai对话测试数据)
- [5. 数据加载脚本](#5-数据加载脚本)
- [6. 数据清理脚本](#6-数据清理脚本)

---

## 1. 种子数据概览

### 1.1 数据量统计

| 数据类型 | 数量 | 用途 |
|---------|------|------|
| 用户 | 10 | 包含管理员、普通用户、企业用户、锁定用户 |
| 产品 | 30 | 覆盖各类别、状态、价格区间 |
| 对话 | 20 | 不同用户的历史对话 |
| 消息 | 100 | 对话历史消息 |

### 1.2 数据关系图

```
users (10条)
  ↓
  ├── conversations (20条) → messages (100条)
  └── created products (30条)
```

---

## 2. 用户测试数据

### 2.1 管理员账号

#### 账号1: 主管理员
```json
{
  "username": "admin",
  "email": "admin@test.com",
  "phone": "13900000001",
  "password": "Admin123!",
  "password_hash": "$2b$12$...",
  "user_type": "enterprise",
  "role": "admin",
  "status": "active",
  "enterprise_name": "平台管理团队",
  "enterprise_license": "91150100MA0N0000X0"
}
```

**用途**:
- 管理员功能测试
- 产品CRUD测试
- 权限验证测试

---

### 2.2 普通用户账号

#### 账号2: 个人用户1
```json
{
  "username": "user1",
  "email": "user1@test.com",
  "phone": "13800138001",
  "password": "User123!",
  "user_type": "personal",
  "role": "user",
  "status": "active",
  "nickname": "测试用户1",
  "avatar_url": null,
  "gender": 1
}
```

**用途**:
- 普通用户流程测试
- 产品浏览测试
- AI对话测试

---

#### 账号3: 个人用户2
```json
{
  "username": "user2",
  "email": "user2@test.com",
  "phone": "13800138002",
  "password": "User123!",
  "user_type": "personal",
  "role": "user",
  "status": "active",
  "nickname": "测试用户2",
  "gender": 2
}
```

**用途**:
- 多用户场景测试
- 数据隔离测试
- 并发测试

---

### 2.3 企业用户账号

#### 账号4: 企业用户1
```json
{
  "username": "enterprise1",
  "email": "ent1@test.com",
  "phone": "13800138003",
  "password": "Ent123!",
  "user_type": "enterprise",
  "role": "user",
  "status": "active",
  "enterprise_name": "内蒙古草原牧业有限公司",
  "enterprise_license": "91150100MA0N1234X5"
}
```

**用途**:
- 企业用户功能测试
- 企业注册流程测试

---

### 2.4 特殊状态账号

#### 账号5: 禁用用户
```json
{
  "username": "disabled_user",
  "email": "disabled@test.com",
  "phone": "13800138004",
  "password": "Disabled123!",
  "user_type": "personal",
  "role": "user",
  "status": "disabled"
}
```

**用途**: 测试账号禁用功能

---

#### 账号6: 锁定用户
```json
{
  "username": "locked_user",
  "email": "locked@test.com",
  "phone": "13800138005",
  "password": "Locked123!",
  "user_type": "personal",
  "role": "user",
  "status": "locked",
  "login_attempts": 5,
  "locked_until": "<30分钟后>"
}
```

**用途**: 测试密码错误锁定功能

---

### 2.5 性能测试用户

#### 账号7-10: 并发测试用户
```json
{
  "username": "perf_user_1",
  "email": "perf1@test.com",
  "password": "Perf123!",
  "user_type": "personal",
  "role": "user",
  "status": "active"
}
// ... perf_user_2 到 perf_user_10
```

**用途**: 并发和压力测试

---

### 2.6 用户SQL插入脚本

```sql
-- 清空现有测试数据
DELETE FROM users WHERE email LIKE '%@test.com';

-- 插入管理员
INSERT INTO users (username, email, phone, password, user_type, role, status, enterprise_name, enterprise_license, created_at, updated_at)
VALUES
('admin', 'admin@test.com', '13900000001', '$2b$12$...', 'enterprise', 'admin', 'active', '平台管理团队', '91150100MA0N0000X0', NOW(), NOW());

-- 插入普通用户
INSERT INTO users (username, email, phone, password, user_type, role, status, nickname, gender, created_at, updated_at)
VALUES
('user1', 'user1@test.com', '13800138001', '$2b$12$...', 'personal', 'user', 'active', '测试用户1', 1, NOW(), NOW()),
('user2', 'user2@test.com', '13800138002', '$2b$12$...', 'personal', 'user', 'active', '测试用户2', 2, NOW(), NOW());

-- 更多插入语句...
```

---

## 3. 产品测试数据

### 3.1 产品分类分布

| 类别 | 数量 | 状态分布 |
|------|------|---------|
| 肉类 | 8 | active: 6, inactive: 1, draft: 1 |
| 奶制品 | 6 | active: 5, inactive: 1 |
| 粮食 | 5 | active: 4, draft: 1 |
| 蔬菜 | 4 | active: 4 |
| 水果 | 4 | active: 3, inactive: 1 |
| 特色食品 | 3 | active: 3 |

### 3.2 产品详细数据

#### 产品1: 草原牛肉（精选）
```json
{
  "sku": "PROD-001",
  "name": "草原牛肉",
  "description": "来自内蒙古呼伦贝尔大草原的优质牛肉，自然放牧，肉质鲜嫩。牛群自由放牧在广袤的草原上，以天然牧草为食，遵循自然生长规律，确保肉质纯正、营养丰富。",
  "category": "肉类",
  "price": 199.99,
  "cost": 100.00,
  "stock": 100,
  "region": "内蒙古呼伦贝尔",
  "region_code": "NMG-HLB",
  "cultural_tags": ["草原", "有机", "绿色", "自然放牧"],
  "cultural_description": "传统草原养殖文化，牛群自由放牧于广袤草原，遵循自然生长规律。",
  "origin_story": "呼伦贝尔大草原是世界四大草原之一，这里水草丰美，气候宜人。草原牛在这片土地上自由生长，以天然牧草为食，肉质鲜美、营养丰富。",
  "efficacy": "营养丰富，富含蛋白质、铁元素和多种维生素，易消化吸收，适合各年龄段人群食用。",
  "usage": "适合烧烤、炖汤、炒菜等多种烹饪方式。建议烧烤时不要过熟，保持肉质嫩度。",
  "status": "active",
  "is_featured": true,
  "created_by": 1,
  "updated_by": 1
}
```

**用途**:
- 产品详情页测试
- 文化信息展示测试
- AI对话上下文测试

---

#### 产品2: 草原羊肉
```json
{
  "sku": "PROD-002",
  "name": "草原羊肉",
  "description": "内蒙古锡林郭勒草原羊肉，肉质鲜美，无膻味。",
  "category": "肉类",
  "price": 149.99,
  "cost": 75.00,
  "stock": 80,
  "region": "内蒙古锡林郭勒",
  "region_code": "NMG-XLG",
  "cultural_tags": ["草原", "绿色", "无膻"],
  "cultural_description": "锡林郭勒大草原的羊肉以肉质鲜嫩、无膻味著称。",
  "origin_story": "锡林郭勒盟是内蒙古重要的畜牧业基地...",
  "efficacy": "温补身体，富含蛋白质，冬季滋补佳品。",
  "usage": "适合涮火锅、烧烤、炖汤。",
  "status": "active",
  "is_featured": true,
  "created_by": 1,
  "updated_by": 1
}
```

---

#### 产品3-30: 其他产品数据

**奶制品**:
- PROD-003: 内蒙古奶制品（89.99元，活跃）
- PROD-004: 蒙古酸奶（39.99元，活跃）
- PROD-005: 奶酪（69.99元，活跃）
- PROD-006: 奶皮子（49.99元，活跃）
- PROD-007: 奶豆腐（35.99元，活跃）
- PROD-008: 过期奶制品（59.99元，下架）

**粮食**:
- PROD-009: 有机杂粮（59.99元，活跃）
- PROD-010: 荞麦（45.99元，活跃）
- PROD-011: 莜面（38.99元，活跃）
- PROD-012: 燕麦（42.99元，活跃）
- PROD-013: 测试草稿粮食（29.99元，草稿）

**蔬菜**:
- PROD-014: 草原蔬菜（39.99元，活跃）
- PROD-015: 有机土豆（25.99元，活跃）
- PROD-016: 胡萝卜（18.99元，活跃）
- PROD-017: 圆葱（15.99元，活跃）

**水果**:
- PROD-018: 沙漠水果（79.99元，活跃）
- PROD-019: 沙棘（69.99元，活跃）
- PROD-020: 枸杞（89.99元，活跃）
- PROD-021: 过期水果（59.99元，下架）

**特色食品**:
- PROD-022: 草原蜂蜜（129.99元，活跃）
- PROD-023: 风干牛肉（179.99元，活跃）
- PROD-024: 奶茶粉（49.99元，活跃）

**测试特殊产品**:
- PROD-025: 缺货产品（99.99元，库存0）
- PROD-026: 高价产品（999.99元，测试价格排序）
- PROD-027: 低价产品（9.99元，测试价格排序）
- PROD-028: 长名称产品（测试UI显示）
- PROD-029: 特殊字符产品（测试转义）
- PROD-030: 无文化信息产品（测试可选字段）

---

### 3.3 产品SQL插入脚本

```sql
-- 清空测试产品
DELETE FROM products WHERE sku LIKE 'PROD-%';

-- 插入产品
INSERT INTO products (sku, name, description, category, price, cost, stock, region, region_code, cultural_tags, cultural_description, origin_story, efficacy, usage, status, is_featured, created_by, updated_by, created_at, updated_at)
VALUES
('PROD-001', '草原牛肉', '来自内蒙古呼伦贝尔大草原...', '肉类', 199.99, 100.00, 100, '内蒙古呼伦贝尔', 'NMG-HLB', JSON_ARRAY('草原', '有机', '绿色', '自然放牧'), '传统草原养殖文化...', '呼伦贝尔大草原是...', '营养丰富...', '适合烧烤、炖汤...', 'active', 1, 1, 1, NOW(), NOW()),
('PROD-002', '草原羊肉', '内蒙古锡林郭勒...', '肉类', 149.99, 75.00, 80, '内蒙古锡林郭勒', 'NMG-XLG', JSON_ARRAY('草原', '绿色', '无膻'), '锡林郭勒大草原...', '锡林郭勒盟是...', '温补身体...', '适合涮火锅...', 'active', 1, 1, 1, NOW(), NOW());
-- ... 更多产品
```

---

## 4. AI对话测试数据

### 4.1 对话场景分布

| 场景 | 对话数 | 消息数 | 用途 |
|------|--------|--------|------|
| 产品咨询 | 8 | 40 | 测试产品相关对话 |
| 文化介绍 | 5 | 25 | 测试文化知识对话 |
| 通用聊天 | 4 | 20 | 测试通用AI对话 |
| 测试对话 | 3 | 15 | 测试特殊场景 |

### 4.2 对话数据示例

#### 对话1: 产品咨询对话
```json
{
  "id": 1,
  "conversation_uuid": "conv-uuid-001",
  "user_id": 2,
  "title": "关于草原牛肉的咨询",
  "agent_type": "assistant",
  "context_product_id": 1,
  "message_count": 5,
  "total_tokens": 650,
  "status": "active",
  "last_message_at": "[项目完成日期]T14:30:00",
  "created_at": "[项目完成日期]T14:00:00",
  "updated_at": "[项目完成日期]T14:30:00",
  "messages": [
    {
      "id": 1,
      "message_uuid": "msg-uuid-001",
      "conversation_id": 1,
      "role": "user",
      "content": "请介绍一下草原牛肉的特点",
      "input_tokens": 0,
      "output_tokens": 0,
      "total_tokens": 0,
      "created_at": "[项目完成日期]T14:00:00"
    },
    {
      "id": 2,
      "message_uuid": "msg-uuid-002",
      "conversation_id": 1,
      "role": "assistant",
      "content": "草原牛肉来自内蒙古呼伦贝尔大草原，具有以下特点：\n1. 自然放牧：牛群自由放牧在广袤草原\n2. 肉质鲜嫩：以天然牧草为食\n3. 营养丰富：富含蛋白质和铁元素\n4. 绿色有机：无添加剂，纯天然",
      "input_tokens": 25,
      "output_tokens": 105,
      "total_tokens": 130,
      "cost": 0.000266,
      "model": "deepseek-chat",
      "finish_reason": "stop",
      "created_at": "[项目完成日期]T14:00:15"
    },
    {
      "id": 3,
      "message_uuid": "msg-uuid-003",
      "conversation_id": 1,
      "role": "user",
      "content": "价格怎么样？",
      "created_at": "[项目完成日期]T14:15:00"
    },
    {
      "id": 4,
      "message_uuid": "msg-uuid-004",
      "conversation_id": 1,
      "role": "assistant",
      "content": "草原牛肉的价格是199.99元。这个价格考虑了以下因素：\n- 优质的放牧环境\n- 纯天然的饲养方式\n- 严格的品质把控\n相比市场同类产品，性价比很高。",
      "input_tokens": 135,
      "output_tokens": 85,
      "total_tokens": 220,
      "cost": 0.000413,
      "model": "deepseek-chat",
      "created_at": "[项目完成日期]T14:15:10"
    },
    {
      "id": 5,
      "message_uuid": "msg-uuid-005",
      "conversation_id": 1,
      "role": "user",
      "content": "如何烹饪最好吃？",
      "created_at": "[项目完成日期]T14:30:00"
    }
    // 第5条AI回复省略
  ]
}
```

**用途**:
- 上下文对话测试
- 消息历史测试
- Token消耗计算测试

---

### 4.3 对话SQL插入脚本

```sql
-- 清空测试对话
DELETE FROM conversations WHERE user_id IN (SELECT id FROM users WHERE email LIKE '%@test.com');
DELETE FROM messages WHERE conversation_id IN (SELECT id FROM conversations WHERE user_id IN (SELECT id FROM users WHERE email LIKE '%@test.com'));

-- 插入对话
INSERT INTO conversations (conversation_uuid, user_id, title, agent_type, context_product_id, message_count, total_tokens, status, last_message_at, created_at, updated_at)
VALUES
('conv-uuid-001', 2, '关于草原牛肉的咨询', 'assistant', 1, 5, 650, 'active', '[项目完成日期] 14:30:00', '[项目完成日期] 14:00:00', '[项目完成日期] 14:30:00');

-- 插入消息
INSERT INTO messages (message_uuid, conversation_id, role, content, input_tokens, output_tokens, total_tokens, cost, model, finish_reason, created_at, updated_at)
VALUES
('msg-uuid-001', 1, 'user', '请介绍一下草原牛肉的特点', 0, 0, 0, 0, NULL, NULL, '[项目完成日期] 14:00:00', '[项目完成日期] 14:00:00'),
('msg-uuid-002', 1, 'assistant', '草原牛肉来自内蒙古...', 25, 105, 130, 0.000266, 'deepseek-chat', 'stop', '[项目完成日期] 14:00:15', '[项目完成日期] 14:00:15');
-- 更多消息...
```

---

## 5. 数据加载脚本

### 5.1 Python脚本 (seed_data.py)

```python
"""
种子数据加载脚本

用法:
    python backend/scripts/seed_data.py
"""

import sys
import os
from pathlib import Path

# 添加项目根目录到路径
sys.path.append(str(Path(__file__).parent.parent))

from app.database import SessionLocal, engine
from app.models import User, Product, Conversation, Message
from passlib.context import CryptContext
from datetime import datetime
import json

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def load_users(db):
    """加载用户数据"""
    users_data = [
        {
            "username": "admin",
            "email": "admin@test.com",
            "phone": "13900000001",
            "password": hash_password("Admin123!"),
            "user_type": "enterprise",
            "role": "admin",
            "status": "active",
            "enterprise_name": "平台管理团队",
            "enterprise_license": "91150100MA0N0000X0"
        },
        {
            "username": "user1",
            "email": "user1@test.com",
            "phone": "13800138001",
            "password": hash_password("User123!"),
            "user_type": "personal",
            "role": "user",
            "status": "active",
            "nickname": "测试用户1",
            "gender": 1
        },
        {
            "username": "user2",
            "email": "user2@test.com",
            "phone": "13800138002",
            "password": hash_password("User123!"),
            "user_type": "personal",
            "role": "user",
            "status": "active",
            "nickname": "测试用户2",
            "gender": 2
        },
        # ... 更多用户
    ]

    for user_data in users_data:
        user = User(**user_data)
        db.add(user)

    db.commit()
    print(f"✅ 已加载 {len(users_data)} 个用户")

def load_products(db):
    """加载产品数据"""
    admin_user = db.query(User).filter(User.username == "admin").first()

    products_data = [
        {
            "sku": "PROD-001",
            "name": "草原牛肉",
            "description": "来自内蒙古呼伦贝尔大草原...",
            "category": "肉类",
            "price": 199.99,
            "cost": 100.00,
            "stock": 100,
            "region": "内蒙古呼伦贝尔",
            "region_code": "NMG-HLB",
            "cultural_tags": json.dumps(["草原", "有机", "绿色"]),
            "cultural_description": "传统草原养殖文化...",
            "status": "active",
            "is_featured": True,
            "created_by": admin_user.id,
            "updated_by": admin_user.id
        },
        # ... 更多产品
    ]

    for product_data in products_data:
        product = Product(**product_data)
        db.add(product)

    db.commit()
    print(f"✅ 已加载 {len(products_data)} 个产品")

def load_conversations(db):
    """加载对话数据"""
    # 实现对话和消息加载
    pass

def main():
    """主函数"""
    print("开始加载种子数据...")

    db = SessionLocal()

    try:
        # 清空现有测试数据
        print("清理现有测试数据...")
        db.query(Message).delete()
        db.query(Conversation).delete()
        db.query(Product).filter(Product.sku.like('PROD-%')).delete()
        db.query(User).filter(User.email.like('%@test.com')).delete()
        db.commit()

        # 加载新数据
        load_users(db)
        load_products(db)
        load_conversations(db)

        print("✅ 种子数据加载完成！")

    except Exception as e:
        print(f"❌ 加载失败: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    main()
```

**使用方法**:
```bash
cd backend
python scripts/seed_data.py
```

---

### 5.2 SQL脚本 (seed_data.sql)

```sql
-- 种子数据SQL脚本
-- 用法: mysql -u root -p ai_platform_test < backend/scripts/seed_data.sql

USE ai_platform_test;

-- 清空现有数据
DELETE FROM messages;
DELETE FROM conversations;
DELETE FROM products WHERE sku LIKE 'PROD-%';
DELETE FROM users WHERE email LIKE '%@test.com';

-- 重置自增ID
ALTER TABLE users AUTO_INCREMENT = 1;
ALTER TABLE products AUTO_INCREMENT = 1;
ALTER TABLE conversations AUTO_INCREMENT = 1;
ALTER TABLE messages AUTO_INCREMENT = 1;

-- 插入用户（省略...见上文）
-- 插入产品（省略...见上文）
-- 插入对话（省略...见上文）

SELECT '✅ 种子数据加载完成！' AS status;
```

---

## 6. 数据清理脚本

### 6.1 Python清理脚本 (clear_test_data.py)

```python
"""
测试数据清理脚本

用法:
    python backend/scripts/clear_test_data.py
"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from app.database import SessionLocal
from app.models import User, Product, Conversation, Message

def clear_test_data():
    """清理所有测试数据"""
    db = SessionLocal()

    try:
        print("开始清理测试数据...")

        # 按依赖关系顺序删除
        message_count = db.query(Message).delete()
        conv_count = db.query(Conversation).delete()
        product_count = db.query(Product).filter(Product.sku.like('PROD-%')).delete()
        user_count = db.query(User).filter(User.email.like('%@test.com')).delete()

        db.commit()

        print(f"✅ 已删除:")
        print(f"   - 用户: {user_count} 条")
        print(f"   - 产品: {product_count} 条")
        print(f"   - 对话: {conv_count} 条")
        print(f"   - 消息: {message_count} 条")

    except Exception as e:
        print(f"❌ 清理失败: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    clear_test_data()
```

---

### 6.2 SQL清理脚本 (clear_test_data.sql)

```sql
-- 测试数据清理SQL脚本

USE ai_platform_test;

DELETE FROM messages;
DELETE FROM conversations;
DELETE FROM products WHERE sku LIKE 'PROD-%';
DELETE FROM users WHERE email LIKE '%@test.com';

SELECT '✅ 测试数据已清理' AS status;
```

---

## 7. 数据验证

### 7.1 数据完整性检查

```sql
-- 检查用户数量
SELECT COUNT(*) AS user_count FROM users WHERE email LIKE '%@test.com';
-- 预期: 10

-- 检查产品数量
SELECT COUNT(*) AS product_count FROM products WHERE sku LIKE 'PROD-%';
-- 预期: 30

-- 检查对话数量
SELECT COUNT(*) AS conversation_count FROM conversations;
-- 预期: 20

-- 检查消息数量
SELECT COUNT(*) AS message_count FROM messages;
-- 预期: 100

-- 检查数据关联
SELECT
    u.username,
    COUNT(DISTINCT c.id) AS conversation_count,
    COUNT(m.id) AS message_count
FROM users u
LEFT JOIN conversations c ON u.id = c.user_id
LEFT JOIN messages m ON c.id = m.conversation_id
WHERE u.email LIKE '%@test.com'
GROUP BY u.id
ORDER BY u.id;
```

---

### 7.2 数据质量检查

```sql
-- 检查必填字段不为空
SELECT COUNT(*) FROM products WHERE name IS NULL OR name = '';
-- 预期: 0

-- 检查价格合理性
SELECT COUNT(*) FROM products WHERE price <= 0 OR cost < 0;
-- 预期: 0

-- 检查密码已加密
SELECT COUNT(*) FROM users WHERE password NOT LIKE '$2b$%';
-- 预期: 0

-- 检查Token消耗合理性
SELECT
    AVG(total_tokens) AS avg_tokens,
    MIN(total_tokens) AS min_tokens,
    MAX(total_tokens) AS max_tokens
FROM messages
WHERE role = 'assistant';
-- 预期: avg在100-200之间
```

---

## 8. 快速开始

### 一键加载测试数据

```bash
#!/bin/bash
# 文件: backend/scripts/setup_test_data.sh

echo "=== 开始设置测试数据 ==="

# 1. 清理旧数据
echo "1. 清理现有测试数据..."
python backend/scripts/clear_test_data.py

# 2. 加载新数据
echo "2. 加载种子数据..."
python backend/scripts/seed_data.py

# 3. 验证数据
echo "3. 验证数据完整性..."
mysql -u root -p ai_platform_test < backend/scripts/verify_data.sql

echo "=== 测试数据设置完成 ==="
```

**使用方法**:
```bash
chmod +x backend/scripts/setup_test_data.sh
./backend/scripts/setup_test_data.sh
```

---

**文档版本**: v1.0
**最后更新**: [项目完成日期]
**维护团队**: QA团队
