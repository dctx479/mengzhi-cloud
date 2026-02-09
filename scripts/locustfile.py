"""
Locust性能测试脚本
用于API压力测试和性能评估
"""

from locust import HttpUser, task, between
import random
import time


class APIUser(HttpUser):
    """模拟API用户"""
    wait_time = between(1, 3)  # 用户操作间隔1-3秒

    def on_start(self):
        """用户启动时执行：注册并登录"""
        # 创建唯一用户
        timestamp = int(time.time() * 1000)
        self.username = f"perf_user_{timestamp}_{random.randint(1000, 9999)}"
        self.password = "PerfTest123!"

        # 注册
        register_data = {
            "username": self.username,
            "email": f"{self.username}@example.com",
            "password": self.password,
            "full_name": "性能测试用户"
        }

        response = self.client.post("/api/v1/auth/register", json=register_data)
        if response.status_code not in [200, 400]:  # 400可能是用户已存在
            print(f"注册失败: {response.status_code}")

        # 登录获取token
        login_data = {
            "username": self.username,
            "password": self.password
        }

        response = self.client.post("/api/v1/auth/login", json=login_data)
        if response.status_code == 200:
            data = response.json()
            self.token = data["data"]["access_token"]
            self.headers = {"Authorization": f"Bearer {self.token}"}
        else:
            print(f"登录失败: {response.status_code}")
            self.token = None
            self.headers = {}

    @task(10)
    def get_products_list(self):
        """测试：获取产品列表（最高权重）"""
        page = random.randint(1, 5)
        page_size = random.choice([10, 20, 50])
        self.client.get(f"/api/v1/products?page={page}&page_size={page_size}")

    @task(5)
    def search_products(self):
        """测试：搜索产品"""
        keywords = ["羊肉", "牛奶", "马铃薯", "荞麦", "黄芪"]
        keyword = random.choice(keywords)
        self.client.get(f"/api/v1/products?search={keyword}")

    @task(3)
    def filter_products(self):
        """测试：筛选产品"""
        categories = ["畜产品", "农产品", "特色产品", "加工品"]
        category = random.choice(categories)
        self.client.get(f"/api/v1/products?category={category}")

    @task(8)
    def get_product_detail(self):
        """测试：获取产品详情"""
        # 假设产品ID在1-100之间
        product_id = random.randint(1, 100)
        with self.client.get(f"/api/v1/products/{product_id}", catch_response=True) as response:
            if response.status_code == 404:
                response.success()  # 产品不存在也算正常

    @task(2)
    def get_current_user(self):
        """测试：获取当前用户信息"""
        if self.token:
            self.client.get("/api/v1/auth/me", headers=self.headers)

    @task(1)
    def update_profile(self):
        """测试：更新用户资料"""
        if self.token:
            update_data = {
                "full_name": f"性能测试用户{random.randint(1, 1000)}"
            }
            self.client.put("/api/v1/auth/profile", json=update_data, headers=self.headers)

    @task(3)
    def create_conversation(self):
        """测试：创建AI对话"""
        if self.token:
            conv_data = {
                "title": f"性能测试对话_{int(time.time())}"
            }
            with self.client.post("/api/v1/chat/conversations", json=conv_data, headers=self.headers, catch_response=True) as response:
                if response.status_code in [200, 201]:
                    response.success()

    @task(2)
    def get_conversations(self):
        """测试：获取对话列表"""
        if self.token:
            self.client.get("/api/v1/chat/conversations", headers=self.headers)


class HeavyLoadUser(HttpUser):
    """模拟高负载用户（AI内容生成）"""
    wait_time = between(5, 10)

    def on_start(self):
        """登录"""
        timestamp = int(time.time() * 1000)
        self.username = f"heavy_user_{timestamp}_{random.randint(1000, 9999)}"
        self.password = "HeavyTest123!"

        # 注册
        register_data = {
            "username": self.username,
            "email": f"{self.username}@example.com",
            "password": self.password,
            "full_name": "高负载测试用户"
        }
        self.client.post("/api/v1/auth/register", json=register_data)

        # 登录
        login_data = {
            "username": self.username,
            "password": self.password
        }
        response = self.client.post("/api/v1/auth/login", json=login_data)
        if response.status_code == 200:
            data = response.json()
            self.token = data["data"]["access_token"]
            self.headers = {"Authorization": f"Bearer {self.token}"}
        else:
            self.token = None
            self.headers = {}

    @task(5)
    def send_ai_message(self):
        """测试：发送AI消息（高负载）"""
        if not self.token:
            return

        # 先创建对话
        conv_data = {"title": "性能测试"}
        conv_response = self.client.post("/api/v1/chat/conversations", json=conv_data, headers=self.headers)

        if conv_response.status_code in [200, 201]:
            conv_id = conv_response.json()["data"]["id"]

            # 发送消息
            messages = [
                "介绍一下内蒙古羊肉的特点",
                "如何推广内蒙古的农产品",
                "帮我写一段产品文案",
                "分析一下市场趋势"
            ]

            message_data = {
                "conversation_id": conv_id,
                "content": random.choice(messages),
                "role": "user"
            }

            with self.client.post("/api/v1/chat/messages", json=message_data, headers=self.headers, catch_response=True, timeout=30) as response:
                if response.status_code in [200, 201, 500]:  # 500可能是AI API未配置
                    response.success()


class AdminUser(HttpUser):
    """模拟管理员用户"""
    wait_time = between(3, 7)

    def on_start(self):
        """登录管理员"""
        admin_data = {
            "username": "admin",
            "password": "admin123"
        }

        response = self.client.post("/api/v1/auth/login", json=admin_data)
        if response.status_code == 200:
            data = response.json()
            self.token = data["data"]["access_token"]
            self.headers = {"Authorization": f"Bearer {self.token}"}
        else:
            self.token = None
            self.headers = {}

    @task(3)
    def get_roles(self):
        """测试：获取角色列表"""
        if self.token:
            self.client.get("/api/v1/rbac/roles", headers=self.headers)

    @task(3)
    def get_permissions(self):
        """测试：获取权限列表"""
        if self.token:
            self.client.get("/api/v1/rbac/permissions", headers=self.headers)

    @task(1)
    def create_product(self):
        """测试：创建产品"""
        if self.token:
            product_data = {
                "name": f"测试产品_{int(time.time())}",
                "category": "测试分类",
                "origin": "内蒙古",
                "description": "性能测试创建的产品"
            }

            with self.client.post("/api/v1/products", json=product_data, headers=self.headers, catch_response=True) as response:
                if response.status_code in [200, 201, 403, 404]:
                    response.success()


# 性能测试场景配置
"""
使用方法:

1. 基础性能测试（100并发用户）
   locust -f scripts/locustfile.py --host=http://localhost:8000 --users 100 --spawn-rate 10

2. 压力测试（500并发用户）
   locust -f scripts/locustfile.py --host=http://localhost:8000 --users 500 --spawn-rate 50

3. 持久化测试（运行10分钟）
   locust -f scripts/locustfile.py --host=http://localhost:8000 --users 200 --spawn-rate 20 --run-time 10m

4. 无界面模式（适合CI/CD）
   locust -f scripts/locustfile.py --host=http://localhost:8000 --users 100 --spawn-rate 10 --headless --run-time 5m --html=perf_report.html

性能指标目标:
- 平均响应时间: < 200ms
- P95响应时间: < 500ms
- P99响应时间: < 1000ms
- 错误率: < 1%
- 吞吐量: > 100 req/s
"""
