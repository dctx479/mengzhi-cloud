# 性能测试计划

**项目**: 内蒙古农畜产品品牌营销AI赋能云平台
**版本**: v1.0.0
**编写日期**: [项目完成日期]

---

## 目录

- [1. 性能测试目标](#1-性能测试目标)
- [2. 性能指标](#2-性能指标)
- [3. 接口性能测试](#3-接口性能测试)
- [4. 并发压力测试](#4-并发压力测试)
- [5. 数据库性能测试](#5-数据库性能测试)
- [6. 前端性能测试](#6-前端性能测试)
- [7. 测试工具和环境](#7-测试工具和环境)

---

## 1. 性能测试目标

### 1.1 测试目标

- 验证系统在正常负载下的响应时间
- 确定系统的最大并发承载能力
- 识别性能瓶颈和优化点
- 验证系统稳定性和可靠性

### 1.2 测试范围

#### 包含
- 关键API接口响应时间
- 数据库查询性能
- 并发用户压力测试
- 前端页面加载性能
- AI对话流式响应性能

#### 不包含
- 第三方服务性能（DeepSeek API）
- 网络带宽测试
- 硬件性能测试

---

## 2. 性能指标

### 2.1 响应时间指标

| 接口类型 | 目标响应时间 | 可接受范围 | 优秀标准 |
|---------|-------------|-----------|---------|
| 登录/注册 | <200ms | <500ms | <100ms |
| 产品列表 | <500ms | <1s | <300ms |
| 产品详情 | <300ms | <800ms | <200ms |
| AI对话（非流式） | <3s | <5s | <2s |
| AI对话（流式首字节） | <1s | <2s | <500ms |
| 对话列表 | <400ms | <1s | <300ms |
| 用户信息 | <200ms | <500ms | <150ms |

### 2.2 吞吐量指标

| 指标 | 目标值 | 说明 |
|------|--------|------|
| QPS（每秒请求数）| ≥100 | 产品列表接口 |
| 并发用户数 | ≥100 | 同时在线用户 |
| AI对话并发 | ≥50 | 同时进行对话 |
| 数据库连接数 | ≥50 | 连接池大小 |

### 2.3 资源使用指标

| 资源 | 正常范围 | 告警阈值 |
|------|---------|---------|
| CPU使用率 | <50% | >80% |
| 内存使用率 | <70% | >85% |
| 数据库连接 | <40个 | >45个 |
| Redis内存 | <500MB | >1GB |

---

## 3. 接口性能测试

### 3.1 认证API性能测试

#### TC-PERF-AUTH-001: 用户登录性能

**目标**: 响应时间<200ms
**并发**: 50用户
**持续时间**: 5分钟

**测试场景**:
```python
# Locust测试脚本
from locust import HttpUser, task, between

class LoginUser(HttpUser):
    wait_time = between(1, 3)

    @task
    def login(self):
        self.client.post("/api/v1/auth/login", json={
            "username": "test_user",
            "password": "Test123!"
        })
```

**性能指标**:
- 平均响应时间: <200ms
- 95百分位: <300ms
- 99百分位: <500ms
- 失败率: <1%

**验证点**:
- 数据库连接池未耗尽
- Redis响应正常
- 无慢查询
- CPU使用率<60%

---

#### TC-PERF-AUTH-002: 用户注册性能

**目标**: 响应时间<200ms
**并发**: 20用户
**持续时间**: 3分钟

**测试场景**:
- 模拟20个用户同时注册
- 每个用户唯一用户名和邮箱
- 验证码模拟通过

**性能指标**:
- 平均响应时间: <200ms
- 数据库写入延迟: <50ms

---

#### TC-PERF-AUTH-003: Token刷新性能

**目标**: 响应时间<150ms
**并发**: 30用户
**持续时间**: 3分钟

**测试场景**:
- 30个用户同时刷新Token
- 验证旧Token失效
- 验证新Token有效

**性能指标**:
- 平均响应时间: <150ms
- Redis读写延迟: <10ms

---

### 3.2 产品API性能测试

#### TC-PERF-PRODUCT-001: 产品列表性能

**目标**: 响应时间<500ms
**并发**: 100用户
**持续时间**: 10分钟

**测试场景**:
```python
class ProductUser(HttpUser):
    wait_time = between(1, 5)

    @task(3)
    def list_products(self):
        self.client.get("/api/v1/products?page=1&size=10")

    @task(2)
    def search_products(self):
        self.client.get("/api/v1/products?search=牛肉&category=肉类")

    @task(1)
    def filtered_products(self):
        self.client.get("/api/v1/products?category=肉类&sort_by=price&sort_order=asc")
```

**性能指标**:
- 平均响应时间: <500ms
- 95百分位: <800ms
- 数据库查询时间: <100ms
- QPS: ≥100

**数据库优化验证**:
- 索引使用情况（category, region, status）
- 查询执行计划
- 慢查询日志

---

#### TC-PERF-PRODUCT-002: 产品详情性能

**目标**: 响应时间<300ms
**并发**: 80用户
**持续时间**: 5分钟

**测试场景**:
- 80个用户随机访问产品详情
- 包括文化信息接口

**性能指标**:
- 产品详情: <300ms
- 文化信息: <200ms
- 数据库JOIN查询: <80ms

---

#### TC-PERF-PRODUCT-003: 产品创建性能（管理员）

**目标**: 响应时间<400ms
**并发**: 10管理员
**持续时间**: 3分钟

**测试场景**:
- 10个管理员同时创建产品
- 包含完整字段和文化信息

**性能指标**:
- 平均响应时间: <400ms
- 数据库事务提交: <100ms

---

### 3.3 AI对话API性能测试

#### TC-PERF-CHAT-001: AI对话非流式性能

**目标**: 响应时间<3s
**并发**: 30用户
**持续时间**: 5分钟

**测试场景**:
```python
class ChatUser(HttpUser):
    wait_time = between(2, 5)

    def on_start(self):
        # 登录获取token
        response = self.client.post("/api/v1/auth/login", json={
            "username": "test_user",
            "password": "Test123!"
        })
        self.token = response.json()["data"]["tokens"]["access_token"]

    @task
    def send_message(self):
        self.client.post("/api/v1/chat/message",
            headers={"Authorization": f"Bearer {self.token}"},
            json={
                "content": "请介绍内蒙古特色农产品",
                "conversation_id": None
            }
        )
```

**性能指标**:
- 平均响应时间: <3s
- 95百分位: <5s
- DeepSeek API调用: <2.5s
- 数据库写入: <50ms

**注意事项**:
- DeepSeek API响应时间不可控
- 重点测试本地处理性能
- 验证超时和重试机制

---

#### TC-PERF-CHAT-002: AI对话流式性能

**目标**: 首字节<1s，流式稳定
**并发**: 50用户
**持续时间**: 5分钟

**测试场景**:
- 50个用户同时发起流式对话
- 测量TTFB（Time To First Byte）
- 测量完整流式传输时间

**性能指标**:
- TTFB: <1s
- 流式传输稳定性: >95%
- SSE连接数: ≤50

**验证点**:
- SSE连接不中断
- 内存使用稳定
- CPU使用合理

---

#### TC-PERF-CHAT-003: 对话列表性能

**目标**: 响应时间<400ms
**并发**: 60用户
**持续时间**: 5分钟

**测试场景**:
- 每个用户有20个历史对话
- 分页查询（page=1, size=20）

**性能指标**:
- 平均响应时间: <400ms
- 数据库查询: <150ms
- JOIN查询优化

---

## 4. 并发压力测试

### 4.1 登录并发压力测试

#### TC-PERF-STRESS-001: 100并发登录

**测试场景**:
- 100个用户同时登录
- 递增并发: 10 → 50 → 100
- 持续时间: 10分钟

**测试步骤**:
1. 准备100个测试账号
2. 使用Locust模拟并发登录
3. 监控系统资源
4. 记录性能指标

**配置参数**:
```python
# locustfile.py
class LoginStressTest(HttpUser):
    wait_time = between(1, 2)

    @task
    def concurrent_login(self):
        self.client.post("/api/v1/auth/login", json={
            "username": f"user_{random.randint(1, 100)}",
            "password": "Test123!"
        })
```

**性能指标**:
- 50并发响应时间: <300ms
- 100并发响应时间: <500ms
- 失败率: <2%
- CPU使用率: <75%
- 内存使用率: <80%

**压力阈值**:
- 最大并发: ≥100
- 系统崩溃点: >150（记录临界值）

---

### 4.2 产品浏览并发压力测试

#### TC-PERF-STRESS-002: 200并发浏览产品

**测试场景**:
- 200个用户同时浏览产品
- 混合操作:
  - 70% 列表查询
  - 20% 详情查询
  - 10% 搜索筛选

**Locust配置**:
```python
class ProductStressTest(HttpUser):
    wait_time = between(1, 3)

    @task(7)
    def list_products(self):
        page = random.randint(1, 10)
        self.client.get(f"/api/v1/products?page={page}&size=10")

    @task(2)
    def product_detail(self):
        product_id = random.randint(1, 100)
        self.client.get(f"/api/v1/products/{product_id}")

    @task(1)
    def search_products(self):
        self.client.get("/api/v1/products?search=牛肉")
```

**性能指标**:
- 100并发QPS: ≥100
- 200并发QPS: ≥150
- 平均响应时间: <800ms
- 数据库CPU: <70%

---

### 4.3 AI对话并发压力测试

#### TC-PERF-STRESS-003: 50并发AI对话

**测试场景**:
- 50个用户同时AI对话
- 递增并发: 10 → 30 → 50
- 持续时间: 10分钟

**性能指标**:
- 30并发响应时间: <4s
- 50并发响应时间: <6s
- DeepSeek API限流处理
- 队列等待时间: <2s

**资源监控**:
- CPU使用率
- 内存使用率
- 网络带宽
- DeepSeek API配额

---

## 5. 数据库性能测试

### 5.1 慢查询分析

#### TC-PERF-DB-001: 识别慢查询

**测试目标**: 无查询超过1s

**测试步骤**:
1. 开启MySQL慢查询日志
   ```sql
   SET GLOBAL slow_query_log = 'ON';
   SET GLOBAL long_query_time = 1;
   ```
2. 执行压力测试
3. 分析慢查询日志
4. 优化查询

**常见慢查询**:
- 产品列表未使用索引
- JOIN查询过多
- 全表扫描

**优化方案**:
- 添加索引
- 查询优化
- 分页优化

---

### 5.2 索引性能测试

#### TC-PERF-DB-002: 索引效果验证

**测试查询**:
```sql
-- 测试1: 类别筛选（有索引）
EXPLAIN SELECT * FROM products WHERE category = '肉类';

-- 测试2: 产地筛选（有索引）
EXPLAIN SELECT * FROM products WHERE region = '内蒙古呼伦贝尔';

-- 测试3: 组合筛选（复合索引）
EXPLAIN SELECT * FROM products
WHERE category = '肉类' AND status = 'active'
ORDER BY created_at DESC;
```

**性能指标**:
- type: ref或range（不能是ALL）
- rows: <1000
- Extra: Using index（覆盖索引最佳）

**索引策略**:
```sql
-- 单列索引
CREATE INDEX idx_category ON products(category);
CREATE INDEX idx_region ON products(region);
CREATE INDEX idx_status ON products(status);

-- 复合索引
CREATE INDEX idx_category_status_created ON products(category, status, created_at);

-- 全文索引（可选）
CREATE FULLTEXT INDEX idx_name_desc ON products(name, description);
```

---

### 5.3 连接池性能测试

#### TC-PERF-DB-003: 连接池压力测试

**测试场景**:
- 模拟高并发场景
- 连接池配置:
  - min_size: 5
  - max_size: 50
  - timeout: 30s

**监控指标**:
- 活跃连接数
- 等待连接数
- 连接超时次数
- 连接泄漏检测

**优化建议**:
- 合理设置连接池大小
- 及时释放连接
- 使用连接池监控

---

## 6. 前端性能测试

### 6.1 页面加载性能

#### TC-PERF-FE-001: 首页加载性能

**测试工具**: Lighthouse

**性能指标**:
| 指标 | 目标值 | 说明 |
|------|--------|------|
| FCP（首次内容绘制） | <1.5s | 用户看到第一个内容的时间 |
| LCP（最大内容绘制） | <2.5s | 最大内容元素加载时间 |
| TTI（可交互时间） | <3.5s | 页面完全可交互时间 |
| CLS（累积布局偏移） | <0.1 | 视觉稳定性 |
| FID（首次输入延迟） | <100ms | 交互响应速度 |

**优化建议**:
- 代码分割和懒加载
- 图片优化和CDN
- 资源压缩（Gzip）
- 浏览器缓存策略

---

#### TC-PERF-FE-002: 产品列表页性能

**测试场景**:
- 加载100个产品
- 包含图片和卡片渲染

**性能指标**:
- 初始渲染: <1s
- 滚动性能: 60 FPS
- 内存占用: <100MB

**优化技术**:
- 虚拟滚动（react-window）
- 图片懒加载
- 防抖和节流

---

#### TC-PERF-FE-003: AI对话页性能

**测试场景**:
- 加载包含100条消息的对话
- 实时接收流式响应

**性能指标**:
- 消息渲染: <50ms/条
- 滚动流畅度: 60 FPS
- 内存占用稳定

---

### 6.2 打包体积优化

#### TC-PERF-FE-004: Bundle体积分析

**目标**: 初始加载<500KB（Gzip后）

**分析工具**: webpack-bundle-analyzer

**优化策略**:
- Tree Shaking
- Code Splitting
- 按需加载
- 移除未使用依赖

**体积目标**:
| 资源类型 | 目标体积 |
|---------|---------|
| vendor.js | <200KB |
| main.js | <150KB |
| CSS | <50KB |
| 图片资源 | 按需加载 |

---

## 7. 测试工具和环境

### 7.1 性能测试工具

#### Locust（后端压力测试）
```bash
# 安装
pip install locust

# 运行
locust -f locustfile.py --host=http://localhost:8000

# Web UI
http://localhost:8089
```

#### Apache JMeter
- 下载：https://jmeter.apache.org/
- 用途：复杂性能测试场景
- 配置文件：`tests/performance/jmeter_plan.jmx`

#### Lighthouse（前端性能）
```bash
# 安装
npm install -g lighthouse

# 运行
lighthouse http://localhost:5173 --view
```

#### Chrome DevTools
- Performance面板
- Network面板
- Memory面板

---

### 7.2 监控工具

#### 系统监控
- CPU: `htop` / `top`
- 内存: `free -h`
- 磁盘IO: `iostat`
- 网络: `iftop`

#### 数据库监控
```sql
-- 查看慢查询
SHOW VARIABLES LIKE 'slow_query%';

-- 查看连接数
SHOW STATUS LIKE 'Threads_connected';

-- 查看查询执行计划
EXPLAIN SELECT ...;
```

#### Redis监控
```bash
# 连接Redis
redis-cli

# 查看状态
INFO stats

# 查看内存使用
INFO memory

# 实时监控
MONITOR
```

---

### 7.3 测试环境配置

#### 硬件配置
```
CPU: 4核
内存: 8GB
硬盘: SSD 100GB
网络: 100Mbps
```

#### 软件配置
```
OS: Linux Ubuntu 22.04
Python: 3.11
Node.js: 18 LTS
MySQL: 8.0
Redis: 7.0
Nginx: 1.24
```

#### 数据准备
- 用户数据: 1000条
- 产品数据: 500条
- 对话数据: 200条
- 消息数据: 1000条

---

## 测试执行计划

### 第1天: 接口性能测试
- 上午: 认证API性能测试
- 下午: 产品API性能测试

### 第2天: 并发压力测试
- 上午: 登录和产品浏览并发测试
- 下午: AI对话并发测试

### 第3天: 数据库和前端测试
- 上午: 数据库性能优化
- 下午: 前端性能测试

### 第4天: 报告和优化
- 整理测试报告
- 性能优化建议
- 验证优化效果

---

## 性能测试报告模板

```markdown
# 性能测试报告

## 测试概述
- 测试日期: [项目月份]-XX
- 测试环境: QA环境
- 测试工具: Locust + Lighthouse

## 测试结果

### 1. 接口性能
| 接口 | 并发数 | 平均响应时间 | 95百分位 | QPS | 是否达标 |
|------|--------|-------------|---------|-----|---------|
| 登录 | 50 | 180ms | 250ms | 120 | ✅ |
| 产品列表 | 100 | 450ms | 700ms | 110 | ✅ |
| AI对话 | 30 | 2.8s | 4.5s | 25 | ✅ |

### 2. 压力测试
- 最大并发: 150用户
- 系统崩溃点: >200用户
- CPU使用率峰值: 78%
- 内存使用率峰值: 72%

### 3. 瓶颈分析
1. 产品列表查询慢（缺少复合索引）
2. AI对话并发受DeepSeek API限制
3. 数据库连接池偶尔耗尽

### 4. 优化建议
1. 添加复合索引优化查询
2. 增加连接池大小到60
3. 实现AI对话排队机制
4. 启用Redis查询缓存

### 5. 优化后效果
| 指标 | 优化前 | 优化后 | 提升 |
|------|--------|--------|------|
| 产品列表响应时间 | 650ms | 420ms | 35% |
| 最大并发 | 150 | 180 | 20% |
```

---

**文档版本**: v1.0
**最后更新**: [项目完成日期]
**维护团队**: QA团队 + 运维团队
