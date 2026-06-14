# 测试策略与质量保障
## Testing Strategy v1.0

**文档版本**: 1.0  
**创建日期**: 2026-06-11  
**质量目标**: 代码覆盖率≥60%，缺陷密度<3个/KLOC

---

## 一、测试策略总览

### 1.1 测试金字塔

```
       ┌─────────────┐
       │  E2E测试    │  ← 10%（关键用户流程）
       │   5-10个    │
       └─────────────┘
      ┌───────────────┐
      │  集成测试     │  ← 30%（API/模块集成）
      │   30-50个     │
      └───────────────┘
    ┌─────────────────┐
    │   单元测试      │  ← 60%（函数/方法级别）
    │   100-200个     │
    └─────────────────┘
```

### 1.2 测试类型与覆盖范围

| 测试类型 | 覆盖范围 | 工具 | 目标覆盖率 |
|---------|---------|------|-----------|
| **单元测试** | 独立函数/方法 | pytest, Jest | 60% |
| **集成测试** | API接口 | pytest + httpx | 80% |
| **E2E测试** | 用户流程 | Playwright | 核心流程100% |
| **性能测试** | 并发/负载 | Locust | P95<2s |
| **安全测试** | OWASP Top 10 | Bandit, ESLint | 0严重漏洞 |

---

## 二、单元测试

### 2.1 后端单元测试

**测试框架**: pytest + pytest-asyncio + pytest-cov

**目录结构**
```
backend/tests/
├── conftest.py              # 全局fixtures
├── test_ip_agent/
│   ├── test_xiaoshu_agent.py
│   ├── test_xiaoshang_agent.py
│   ├── test_ip_router.py
│   └── test_llm_client.py
├── test_knowledge_graph/
│   └── test_kg_service.py
└── test_utils/
    └── test_helpers.py
```

**示例测试用例**

```python
# backend/tests/test_ip_agent/test_xiaoshu_agent.py

import pytest
from app.services.ip_agent import XiaoshuAgent

@pytest.fixture
def agent():
    """测试用Agent实例"""
    return XiaoshuAgent()

def test_welcome_message(agent):
    """测试欢迎语"""
    welcome = agent.get_welcome_message()
    assert "小数" in welcome
    assert len(welcome) > 10

def test_generate_response_with_culture_elements(agent):
    """测试回复包含草原文化元素"""
    response = agent.generate_response(
        user_message="推荐一款羊肉",
        user_profile=None,
        product_context=None
    )
    
    # 验证包含草原文化元素
    assert any(kw in response.content for kw in ["草原", "老额吉", "咱们"])
    
    # 验证有建议追问
    assert len(response.suggestions) > 0
    
    # 验证文化元素提取
    assert len(response.cultural_elements) > 0

def test_generate_brand_story(agent):
    """测试品牌故事生成"""
    story = agent.generate_brand_story(
        product_name="锡林郭勒羊肉",
        category="牛羊肉",
        origin="锡林郭勒",
        selling_points=["草原散养", "肉质紧实"],
        target_audience="都市家庭"
    )
    
    # 验证长度
    assert len(story) >= 300
    
    # 验证包含产品名
    assert "锡林郭勒" in story
    
    # 验证包含文化元素
    assert any(kw in story for kw in ["草原", "蒙古", "那达慕"])

@pytest.mark.asyncio
async def test_llm_cache_hit():
    """测试LLM缓存命中"""
    from app.services.ip_agent.llm_client import LLMClient
    
    client = LLMClient()
    prompt = "推荐一款羊肉"
    
    # 第一次调用（未命中缓存）
    result1 = await client.call_with_cache(prompt)
    
    # 第二次调用（应命中缓存）
    result2 = await client.call_with_cache(prompt)
    
    assert result1 == result2  # 结果一致
```

**运行单元测试**
```bash
# 运行所有测试
pytest backend/tests/

# 运行指定模块
pytest backend/tests/test_ip_agent/

# 生成覆盖率报告
pytest --cov=app --cov-report=html backend/tests/
```

### 2.2 前端单元测试

**测试框架**: Vitest + @vue/test-utils

**目录结构**
```
frontend/tests/
├── unit/
│   ├── components/
│   │   └── MessageItem.spec.ts
│   ├── stores/
│   │   └── ip.spec.ts
│   └── utils/
│       └── helpers.spec.ts
└── setup.ts
```

**示例测试用例**

```typescript
// frontend/tests/unit/stores/ip.spec.ts

import { setActivePinia, createPinia } from 'pinia'
import { useIPStore } from '@/stores/ip'
import { describe, it, expect, beforeEach, vi } from 'vitest'

describe('IP Store', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
  })

  it('初始状态正确', () => {
    const store = useIPStore()
    expect(store.currentIP).toBe('xiaoshu')
    expect(store.messages).toEqual([])
  })

  it('发送消息后更新messages', async () => {
    const store = useIPStore()
    
    // Mock API
    vi.mock('@/api/ip', () => ({
      ipAPI: {
        chat: vi.fn().mockResolvedValue({
          data: {
            content: '咱们草原上的羊肉...',
            suggestions: []
          }
        })
      }
    }))
    
    await store.sendMessage('推荐羊肉')
    
    expect(store.messages.length).toBe(2)  // 用户消息 + AI回复
    expect(store.messages[1].role).toBe('ai')
  })

  it('切换IP后更新currentIP', () => {
    const store = useIPStore()
    store.switchIP('xiaoshang')
    expect(store.currentIP).toBe('xiaoshang')
  })
})
```

---

## 三、集成测试

### 3.1 API集成测试

**测试框架**: pytest + httpx

**示例测试用例**

```python
# backend/tests/integration/test_ip_api.py

import pytest
from httpx import AsyncClient
from app.main import app

@pytest.mark.asyncio
async def test_ip_chat_api():
    """测试IP对话API"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post("/api/v1/ip/chat", json={
            "ip_type": "xiaoshu",
            "message": "推荐一款羊肉"
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 200
        assert "response" in data["data"]
        assert "草原" in data["data"]["response"] or "老额吉" in data["data"]["response"]

@pytest.mark.asyncio
async def test_ip_chat_with_invalid_type():
    """测试无效IP类型"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post("/api/v1/ip/chat", json={
            "ip_type": "invalid",
            "message": "测试"
        })
        
        assert response.status_code == 400

@pytest.mark.asyncio
async def test_knowledge_graph_trace():
    """测试知识图谱溯源API"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        # 先创建测试产品
        product_response = await client.post("/api/v1/products", json={
            "name": "测试羊肉",
            "category": "牛羊肉",
            "origin_id": 1
        })
        product_id = product_response.json()["data"]["id"]
        
        # 查询溯源
        trace_response = await client.get(f"/api/v1/knowledge/trace/{product_id}")
        
        assert trace_response.status_code == 200
        data = trace_response.json()["data"]
        assert "product" in data
        assert "origin" in data
        assert "cultures" in data
```

**运行集成测试**
```bash
pytest backend/tests/integration/ -v
```

---

## 四、端到端测试

### 4.1 E2E测试框架

**测试框架**: Playwright

**测试场景**

| 场景ID | 场景名称 | 测试步骤 | 预期结果 |
|--------|---------|---------|---------|
| E2E-01 | IP对话流程 | 1. 登录<br>2. 进入IP对话<br>3. 发送消息<br>4. 切换IP | 对话正常，切换成功 |
| E2E-02 | 品牌故事生成 | 1. 选择产品<br>2. 生成故事<br>3. 保存 | 故事生成成功，保存成功 |
| E2E-03 | 文化溯源查询 | 1. 选择产品<br>2. 查看溯源 | 显示完整溯源链路 |

**示例测试用例**

```typescript
// frontend/tests/e2e/ip-chat.spec.ts

import { test, expect } from '@playwright/test'

test('IP对话完整流程', async ({ page }) => {
  // 1. 访问IP对话页面
  await page.goto('http://localhost:5173/ip/chat')
  
  // 2. 等待页面加载
  await expect(page.locator('.welcome-card')).toBeVisible()
  
  // 3. 点击快捷问题
  await page.click('text=推荐一款送礼的羊肉')
  
  // 4. 等待AI回复
  await expect(page.locator('.message.ai')).toBeVisible({ timeout: 5000 })
  
  // 5. 验证回复内容
  const aiMessage = await page.locator('.message.ai .message-text').textContent()
  expect(aiMessage).toContain('草原')
  
  // 6. 切换到小商
  await page.click('input[value="xiaoshang"]')
  
  // 7. 发送消息
  await page.fill('textarea', '帮我写个直播脚本')
  await page.click('button:has-text("发送")')
  
  // 8. 验证小商回复
  await expect(page.locator('.message.ai:last-child')).toBeVisible()
  const xiaoshangMessage = await page.locator('.message.ai:last-child .message-text').textContent()
  expect(xiaoshangMessage).toMatch(/建议|策略|营销/)
})

test('品牌故事生成流程', async ({ page }) => {
  await page.goto('http://localhost:5173/marketing/brand-story')
  
  // 选择产品
  await page.click('.n-select')
  await page.click('text=锡林郭勒羊肉')
  
  // 生成故事
  await page.click('button:has-text("生成品牌故事")')
  
  // 等待生成完成
  await expect(page.locator('.story-result')).toBeVisible({ timeout: 10000 })
  
  // 验证故事长度
  const storyContent = await page.locator('.story-content').textContent()
  expect(storyContent.length).toBeGreaterThan(300)
  
  // 验证包含文化元素
  expect(storyContent).toMatch(/草原|蒙古|那达慕/)
})
```

**运行E2E测试**
```bash
# 启动开发服务器
npm run dev

# 运行E2E测试
npx playwright test

# 生成HTML报告
npx playwright show-report
```

---

## 五、性能测试

### 5.1 性能测试工具

**工具**: Locust

**测试场景**

```python
# backend/tests/performance/locustfile.py

from locust import HttpUser, task, between

class IPChatUser(HttpUser):
    wait_time = between(1, 3)
    
    def on_start(self):
        """登录"""
        self.client.post("/api/v1/auth/login", json={
            "username": "testuser",
            "password": "testpass"
        })
    
    @task(3)
    def chat_with_xiaoshu(self):
        """小数对话（权重3）"""
        self.client.post("/api/v1/ip/chat", json={
            "ip_type": "xiaoshu",
            "message": "推荐一款羊肉"
        })
    
    @task(2)
    def generate_brand_story(self):
        """品牌故事生成（权重2）"""
        self.client.post("/api/v1/ip/brand-story", json={
            "product_name": "锡林郭勒羊肉",
            "category": "牛羊肉",
            "origin": "锡林郭勒",
            "selling_points": ["草原散养"],
            "target_audience": "都市家庭"
        })
    
    @task(1)
    def query_cultural_trace(self):
        """文化溯源查询（权重1）"""
        self.client.get("/api/v1/knowledge/trace/1")
```

**运行性能测试**
```bash
# 模拟10个用户
locust -f backend/tests/performance/locustfile.py --users 10 --spawn-rate 2

# 访问Web UI: http://localhost:8089
```

### 5.2 性能指标

| 指标 | 目标值 | 测试方法 |
|-----|--------|---------|
| API响应时间 | P95<2s | Locust压测 |
| 并发能力 | 100 QPS | Locust压测 |
| 数据库查询 | <500ms | SQL慢查询日志 |
| 前端首屏加载 | <3s | Lighthouse |
| LLM调用缓存命中率 | ≥50% | Redis监控 |

---

## 六、安全测试

### 6.1 OWASP Top 10 检查

| 漏洞类型 | 检测方法 | 修复优先级 |
|---------|---------|-----------|
| SQL注入 | Bandit扫描 + 手工测试 | P0 |
| XSS | ESLint规则 + 手工测试 | P0 |
| 认证失效 | JWT安全审计 | P1 |
| 敏感数据暴露 | 日志审查 | P1 |
| 访问控制失效 | 权限测试用例 | P1 |

### 6.2 安全测试用例

```python
# backend/tests/security/test_sql_injection.py

def test_sql_injection_in_search():
    """测试搜索接口SQL注入防护"""
    malicious_inputs = [
        "' OR '1'='1",
        "'; DROP TABLE users; --",
        "1' UNION SELECT password FROM users--"
    ]
    
    for input_str in malicious_inputs:
        response = client.get(f"/api/v1/products?search={input_str}")
        # 应该返回正常结果或400，不应该执行SQL注入
        assert response.status_code in [200, 400]
        # 不应该返回敏感数据
        assert "password" not in response.text.lower()
```

---

## 七、测试数据管理

### 7.1 测试数据准备

```python
# backend/tests/conftest.py

import pytest
from app.database import get_db
from app.models import Product, CulturalElement

@pytest.fixture
def test_db():
    """测试数据库fixture"""
    # 创建测试数据库
    db = get_test_db()
    
    # 插入测试数据
    test_products = [
        Product(name="测试羊肉1", category="牛羊肉", origin_id=1),
        Product(name="测试羊肉2", category="牛羊肉", origin_id=2),
    ]
    db.add_all(test_products)
    
    test_cultures = [
        CulturalElement(name="那达慕", type="festival"),
        CulturalElement(name="手把肉", type="food"),
    ]
    db.add_all(test_cultures)
    
    db.commit()
    
    yield db
    
    # 清理测试数据
    db.query(Product).delete()
    db.query(CulturalElement).delete()
    db.commit()
```

---

## 八、持续集成（CI）

### 8.1 GitHub Actions配置

```yaml
# .github/workflows/test.yml

name: Test Suite

on: [push, pull_request]

jobs:
  backend-tests:
    runs-on: ubuntu-latest
    
    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_PASSWORD: postgres
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
    
    steps:
      - uses: actions/checkout@v3
      
      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: |
          pip install -r backend/requirements.txt
          pip install pytest pytest-cov pytest-asyncio
      
      - name: Run tests
        run: |
          cd backend
          pytest tests/ --cov=app --cov-report=xml
      
      - name: Upload coverage
        uses: codecov/codecov-action@v3
        with:
          file: ./backend/coverage.xml
  
  frontend-tests:
    runs-on: ubuntu-latest
    
    steps:
      - uses: actions/checkout@v3
      
      - name: Setup Node
        uses: actions/setup-node@v3
        with:
          node-version: '20'
      
      - name: Install dependencies
        run: |
          cd frontend
          npm ci
      
      - name: Run tests
        run: |
          cd frontend
          npm run test:unit
          npm run test:e2e
```

---

## 九、测试报告

### 9.1 每日测试报告模板

**日期**: 2026-06-11  
**Sprint**: 1

| 测试类型 | 通过 | 失败 | 跳过 | 覆盖率 |
|---------|------|------|------|--------|
| 单元测试 | 85 | 2 | 3 | 62% |
| 集成测试 | 28 | 1 | 0 | 78% |
| E2E测试 | 5 | 0 | 0 | 100% |

**失败用例**：
- `test_llm_timeout`: LLM调用超时（已知问题，网络波动）
- `test_concurrent_chat`: 并发测试偶现失败（待修复）

**新增用例**：
- IP切换功能测试（3个用例）

**下一步行动**：
- 修复并发测试失败问题
- 增加直播脚本生成的集成测试

---

**文档结束**