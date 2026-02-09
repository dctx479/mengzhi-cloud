# 性能测试指南

## 文档信息
- **版本**: 1.0
- **创建日期**: [项目完成日期]
- **测试工具**: Locust, Apache Bench, Browser DevTools

## 目录
1. [性能测试目标](#性能测试目标)
2. [测试指标](#测试指标)
3. [测试场景](#测试场景)
4. [测试工具](#测试工具)
5. [执行步骤](#执行步骤)
6. [结果分析](#结果分析)

---

## 性能测试目标

### 后端API性能
- **响应时间**: p50 < 200ms, p95 < 500ms, p99 < 1s
- **吞吐量**: > 100 req/s
- **并发用户**: 支持100并发用户
- **错误率**: < 1%

### 前端性能
- **FCP (First Contentful Paint)**: < 1.8s
- **LCP (Largest Contentful Paint)**: < 2.5s
- **TTI (Time to Interactive)**: < 3.8s
- **CLS (Cumulative Layout Shift)**: < 0.1
- **FID (First Input Delay)**: < 100ms

### 数据库性能
- **查询响应时间**: < 100ms
- **连接池利用率**: < 80%
- **慢查询**: 0个

---

## 测试指标

### 1. 响应时间指标

#### 定义
- **p50 (中位数)**: 50%的请求响应时间
- **p95**: 95%的请求响应时间
- **p99**: 99%的请求响应时间
- **平均响应时间**: 所有请求的平均值
- **最大响应时间**: 最慢的请求

#### 目标值
| 端点类型 | p50 | p95 | p99 |
|---------|-----|-----|-----|
| 简单查询 | < 100ms | < 200ms | < 500ms |
| 复杂查询 | < 200ms | < 500ms | < 1s |
| AI对话 | < 2s | < 5s | < 10s |
| 内容生成 | < 5s | < 10s | < 15s |

### 2. 吞吐量指标

#### 定义
- **RPS (Requests Per Second)**: 每秒请求数
- **TPS (Transactions Per Second)**: 每秒事务数

#### 目标值
- 产品列表: > 200 RPS
- 产品详情: > 150 RPS
- AI对话: > 50 RPS
- 内容生成: > 20 RPS

### 3. 并发性能指标

#### 测试场景
- 10并发用户
- 50并发用户
- 100并发用户
- 200并发用户（压力测试）

#### 验收标准
- 100并发用户时，响应时间 < p95目标值
- 错误率 < 1%
- 无服务崩溃

### 4. 资源使用指标

#### CPU使用率
- 正常负载: < 50%
- 高负载: < 80%
- 峰值: < 95%

#### 内存使用率
- 正常负载: < 60%
- 高负载: < 80%
- 无内存泄漏

#### 数据库连接
- 连接池大小: 20
- 活跃连接: < 16 (80%)
- 等待连接: 0

---

## 测试场景

### 场景1: 产品列表查询性能

#### 测试目标
验证产品列表在不同负载下的性能表现。

#### 测试步骤
```python
# 使用Locust测试
from locust import HttpUser, task, between

class ProductListUser(HttpUser):
    wait_time = between(1, 3)

    @task
    def list_products(self):
        self.client.get("/api/v1/products?page=1&size=10")

    @task(2)
    def search_products(self):
        self.client.get("/api/v1/products?search=牛肉&page=1&size=10")

    @task
    def filter_products(self):
        self.client.get("/api/v1/products?category=肉类&page=1&size=10")
```

#### 执行命令
```bash
# 10用户，持续60秒
locust -f test_product_list.py --headless -u 10 -r 2 -t 60s --host http://localhost:8000

# 50用户，持续120秒
locust -f test_product_list.py --headless -u 50 -r 5 -t 120s --host http://localhost:8000

# 100用户，持续180秒
locust -f test_product_list.py --headless -u 100 -r 10 -t 180s --host http://localhost:8000
```

#### 验收标准
- p95响应时间 < 500ms
- 吞吐量 > 100 RPS
- 错误率 < 1%

### 场景2: AI对话性能

#### 测试目标
验证AI对话在并发情况下的性能。

#### 测试步骤
```python
from locust import HttpUser, task, between

class ChatUser(HttpUser):
    wait_time = between(2, 5)
    token = None

    def on_start(self):
        # 登录获取Token
        response = self.client.post("/api/v1/auth/login", json={
            "email": "test@example.com",
            "password": "Test123!@#"
        })
        if response.status_code == 200:
            self.token = response.json()["data"]["access_token"]

    @task
    def send_message(self):
        if self.token:
            self.client.post(
                "/api/v1/chat/message",
                headers={"Authorization": f"Bearer {self.token}"},
                json={"content": "介绍一下内蒙古的牛肉产品"}
            )
```

#### 验收标准
- p95响应时间 < 5s
- 吞吐量 > 20 RPS
- DeepSeek API调用成功率 > 99%

### 场景3: 内容生成性能

#### 测试目标
验证内容生成功能的性能和稳定性。

#### 测试步骤
```python
from locust import HttpUser, task, between

class ContentGenerationUser(HttpUser):
    wait_time = between(5, 10)
    token = None

    def on_start(self):
        # 登录
        response = self.client.post("/api/v1/auth/login", json={
            "email": "test@example.com",
            "password": "Test123!@#"
        })
        if response.status_code == 200:
            self.token = response.json()["data"]["access_token"]

    @task
    def generate_content(self):
        if self.token:
            self.client.post(
                "/api/v1/content/generate",
                headers={"Authorization": f"Bearer {self.token}"},
                json={
                    "product_id": 1,
                    "template_id": 1,
                    "config": {
                        "length": 500,
                        "style": "professional"
                    }
                }
            )
```

#### 验收标准
- p95响应时间 < 10s
- 吞吐量 > 10 RPS
- 生成成功率 > 95%

### 场景4: 混合负载测试

#### 测试目标
模拟真实用户行为，混合多种操作。

#### 测试步骤
```python
from locust import HttpUser, task, between

class MixedUser(HttpUser):
    wait_time = between(1, 5)
    token = None

    def on_start(self):
        # 登录
        response = self.client.post("/api/v1/auth/login", json={
            "email": "test@example.com",
            "password": "Test123!@#"
        })
        if response.status_code == 200:
            self.token = response.json()["data"]["access_token"]

    @task(10)
    def browse_products(self):
        self.client.get("/api/v1/products?page=1&size=10")

    @task(5)
    def view_product(self):
        self.client.get("/api/v1/products/1")

    @task(3)
    def search_products(self):
        self.client.get("/api/v1/products?search=牛肉")

    @task(2)
    def chat(self):
        if self.token:
            self.client.post(
                "/api/v1/chat/message",
                headers={"Authorization": f"Bearer {self.token}"},
                json={"content": "推荐一些产品"}
            )

    @task(1)
    def generate_content(self):
        if self.token:
            self.client.post(
                "/api/v1/content/generate",
                headers={"Authorization": f"Bearer {self.token}"},
                json={"product_id": 1, "template_id": 1}
            )
```

#### 验收标准
- 整体p95响应时间 < 1s
- 错误率 < 1%
- 系统稳定运行

---

## 测试工具

### 1. Locust（推荐）

#### 安装
```bash
pip install locust
```

#### 使用
```bash
# Web界面模式
locust -f locustfile.py --host http://localhost:8000

# 无头模式
locust -f locustfile.py --headless -u 100 -r 10 -t 300s --host http://localhost:8000
```

#### 优点
- Python编写，易于扩展
- 支持分布式测试
- 实时Web界面
- 详细的统计报告

### 2. Apache Bench (ab)

#### 安装
```bash
# Ubuntu/Debian
sudo apt-get install apache2-utils

# macOS
brew install httpd
```

#### 使用
```bash
# 100个请求，10并发
ab -n 100 -c 10 http://localhost:8000/api/v1/products

# POST请求
ab -n 100 -c 10 -p data.json -T application/json http://localhost:8000/api/v1/auth/login
```

#### 优点
- 简单快速
- 命令行工具
- 适合快速测试

### 3. Browser DevTools

#### 使用
1. 打开Chrome DevTools (F12)
2. 切换到Performance标签
3. 点击录制按钮
4. 执行操作
5. 停止录制
6. 分析结果

#### 测试指标
- FCP, LCP, TTI
- JavaScript执行时间
- 网络请求时间
- 渲染时间

### 4. Lighthouse

#### 使用
```bash
# 安装
npm install -g lighthouse

# 运行
lighthouse http://localhost:5173 --output html --output-path ./report.html
```

#### 测试指标
- Performance Score
- Accessibility
- Best Practices
- SEO

---

## 执行步骤

### 步骤1: 环境准备

```bash
# 1. 启动后端服务
cd backend
uvicorn app.main:app --reload --port 8000

# 2. 启动前端服务
cd frontend
npm run dev

# 3. 确保数据库和Redis运行
docker-compose up -d mysql redis

# 4. 初始化测试数据
python scripts/seed_data.py
```

### 步骤2: 基准测试

```bash
# 单个请求测试
curl -w "@curl-format.txt" -o /dev/null -s http://localhost:8000/api/v1/products

# curl-format.txt内容:
# time_namelookup:  %{time_namelookup}\n
# time_connect:  %{time_connect}\n
# time_appconnect:  %{time_appconnect}\n
# time_pretransfer:  %{time_pretransfer}\n
# time_redirect:  %{time_redirect}\n
# time_starttransfer:  %{time_starttransfer}\n
# ----------\n
# time_total:  %{time_total}\n
```

### 步骤3: 负载测试

```bash
# 10用户
locust -f tests/performance/locustfile.py --headless -u 10 -r 2 -t 60s --host http://localhost:8000

# 50用户
locust -f tests/performance/locustfile.py --headless -u 50 -r 5 -t 120s --host http://localhost:8000

# 100用户
locust -f tests/performance/locustfile.py --headless -u 100 -r 10 -t 180s --host http://localhost:8000
```

### 步骤4: 压力测试

```bash
# 逐步增加负载，找到系统极限
locust -f tests/performance/locustfile.py --headless -u 200 -r 20 -t 300s --host http://localhost:8000
```

### 步骤5: 前端性能测试

```bash
# Lighthouse测试
lighthouse http://localhost:5173 --output html --output-path ./reports/lighthouse_report.html

# 多页面测试
lighthouse http://localhost:5173/ --output html --output-path ./reports/home.html
lighthouse http://localhost:5173/products --output html --output-path ./reports/products.html
lighthouse http://localhost:5173/chat --output html --output-path ./reports/chat.html
```

---

## 结果分析

### 1. 响应时间分析

#### 正常情况
```
Name                          # reqs  # fails  Avg    Min    Max    Median  p95    p99
GET /api/v1/products          1000    0        120    50     500    100     250    400
GET /api/v1/products/{id}     500     0        80     30     300    70      150    250
POST /api/v1/chat/message     200     0        2000   1000   5000   1800    3500   4500
```

#### 异常情况
- **响应时间突然增加**: 检查数据库连接、慢查询
- **p99远大于p95**: 存在性能瓶颈，需要优化
- **最大响应时间过大**: 可能存在超时或死锁

### 2. 吞吐量分析

#### 计算公式
```
吞吐量 (RPS) = 总请求数 / 总时间
```

#### 分析要点
- 吞吐量随并发数增加而增加（正常）
- 吞吐量达到平台期（系统瓶颈）
- 吞吐量下降（系统过载）

### 3. 错误率分析

#### 错误类型
- **4xx错误**: 客户端错误（参数错误、认证失败）
- **5xx错误**: 服务器错误（系统异常、超时）
- **连接错误**: 网络问题、服务不可用

#### 分析要点
- 错误率 < 1%: 正常
- 错误率 1-5%: 需要关注
- 错误率 > 5%: 严重问题

### 4. 资源使用分析

#### 监控命令
```bash
# CPU和内存
top

# 数据库连接
mysql -e "SHOW PROCESSLIST;"

# Redis连接
redis-cli INFO clients
```

#### 分析要点
- CPU使用率持续 > 80%: 需要优化或扩容
- 内存使用持续增长: 可能存在内存泄漏
- 数据库连接池耗尽: 需要增加连接数或优化查询

---

## 优化建议

### 后端优化

#### 1. 数据库优化
```sql
-- 添加索引
CREATE INDEX idx_products_category ON products(category);
CREATE INDEX idx_products_region ON products(region);
CREATE INDEX idx_products_status ON products(status);

-- 分析慢查询
SHOW FULL PROCESSLIST;
SELECT * FROM information_schema.PROCESSLIST WHERE TIME > 1;
```

#### 2. 缓存优化
```python
# Redis缓存产品列表
@cache(ttl=300)  # 5分钟缓存
def get_products(page, size, filters):
    return db.query(Product).filter_by(**filters).paginate(page, size)
```

#### 3. 连接池优化
```python
# 增加数据库连接池大小
SQLALCHEMY_POOL_SIZE = 20
SQLALCHEMY_MAX_OVERFLOW = 10
```

### 前端优化

#### 1. 代码分割
```javascript
// 路由懒加载
const ProductList = () => import('./views/products/ProductList.vue')
const ChatPage = () => import('./views/chat/ChatPage.vue')
```

#### 2. 图片优化
```javascript
// 使用懒加载
<img v-lazy="product.image" />

// 使用WebP格式
<picture>
  <source srcset="image.webp" type="image/webp">
  <img src="image.jpg" alt="Product">
</picture>
```

#### 3. 资源压缩
```javascript
// vite.config.js
export default {
  build: {
    minify: 'terser',
    terserOptions: {
      compress: {
        drop_console: true
      }
    }
  }
}
```

---

## 测试报告模板

### 性能测试报告

**测试日期**: [项目完成日期]
**测试人员**: [姓名]
**测试环境**: 开发环境

#### 测试摘要
- 测试场景: 产品列表查询
- 并发用户: 100
- 测试时长: 180秒
- 总请求数: 18000
- 成功请求: 17982
- 失败请求: 18
- 错误率: 0.1%

#### 响应时间
| 指标 | 值 |
|------|-----|
| 平均响应时间 | 120ms |
| p50 | 100ms |
| p95 | 250ms |
| p99 | 400ms |
| 最大响应时间 | 800ms |

#### 吞吐量
- RPS: 100 req/s
- 峰值RPS: 150 req/s

#### 资源使用
- CPU: 45%
- 内存: 2.5GB / 8GB (31%)
- 数据库连接: 12 / 20 (60%)

#### 结论
✅ 通过 - 所有指标满足要求

#### 优化建议
1. 添加产品列表缓存
2. 优化数据库查询
3. 增加CDN加速

---

**文档版本**: 1.0
**最后更新**: [项目完成日期]
