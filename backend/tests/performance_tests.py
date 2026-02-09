"""
性能测试 - 使用Locust

测试系统在高并发下的性能表现:
1. API端点响应时间
2. 并发处理能力
3. 错误率

运行方式:
    locust -f tests/performance_tests.py --host=http://localhost:8000
    # 或无头模式:
    locust -f tests/performance_tests.py --host=http://localhost:8000 -u 100 -r 10 --run-time 5m --headless
"""

from locust import HttpUser, task, between, events
import random
import json
from typing import Optional


class AuthToken:
    """认证令牌管理"""

    _token: Optional[str] = None
    _user_id: Optional[int] = None

    @classmethod
    def get_token(cls, client, email="admin@example.com", password="Admin@123"):
        """获取或刷新认证令牌"""
        if cls._token is None:
            response = client.post(
                "/api/v1/auth/login",
                json={"email": email, "password": password},
                name="登录"
            )
            if response.status_code == 200:
                data = response.json()
                cls._token = data.get("data", {}).get("access_token")
                cls._user_id = data.get("data", {}).get("user_id")
        return cls._token

    @classmethod
    def get_headers(cls, client):
        """获取认证头"""
        token = cls.get_token(client)
        return {"Authorization": f"Bearer {token}"} if token else {}


class ProductAPIUser(HttpUser):
    """产品API用户行为模型"""

    wait_time = between(1, 3)

    def on_start(self):
        """用户启动时执行"""
        self.token = None
        self.products = []

    @task(10)
    def get_products(self):
        """获取产品列表（权重：10）"""
        params = {
            "page": random.randint(1, 5),
            "page_size": 20,
            "category": random.choice(["农产品", "畜产品", "水产品", None]),
            "status": "published"
        }
        # 移除None值
        params = {k: v for k, v in params.items() if v is not None}

        response = self.client.get(
            "/api/v1/products",
            params=params,
            name="获取产品列表"
        )

        if response.status_code == 200:
            data = response.json()
            self.products = data.get("data", {}).get("items", [])

    @task(5)
    def get_product_detail(self):
        """获取产品详情（权重：5）"""
        if not self.products:
            return

        product = random.choice(self.products)
        product_id = product.get("id")

        self.client.get(
            f"/api/v1/products/{product_id}",
            name="获取产品详情"
        )

    @task(3)
    def search_products(self):
        """搜索产品（权重：3）"""
        keywords = ["有机", "绿色", "地理标志", "认证", "农产品"]
        keyword = random.choice(keywords)

        self.client.get(
            "/api/v1/products/search",
            params={"q": keyword, "limit": 20},
            name="搜索产品"
        )

    @task(2)
    def filter_products(self):
        """筛选产品（权重：2）"""
        self.client.get(
            "/api/v1/products/filter",
            params={
                "category": random.choice(["农产品", "畜产品"]),
                "province": random.choice(["内蒙古", "吉林", "辽宁"]),
                "price_range": random.choice(["0-100", "100-500", "500+"])
            },
            name="筛选产品"
        )


class AuthAPIUser(HttpUser):
    """认证API用户行为模型"""

    wait_time = between(2, 5)

    def on_start(self):
        """用户启动时执行"""
        self.login()

    def login(self):
        """用户登录"""
        response = self.client.post(
            "/api/v1/auth/login",
            json={
                "email": f"user{random.randint(1, 100)}@example.com",
                "password": "Password123!"
            },
            name="登录"
        )

        if response.status_code == 200:
            self.token = response.json().get("data", {}).get("access_token")
        else:
            self.token = None

    @task(5)
    def get_user_profile(self):
        """获取用户资料（权重：5）"""
        if not self.token:
            self.login()
            return

        headers = {"Authorization": f"Bearer {self.token}"}
        self.client.get(
            "/api/v1/auth/me",
            headers=headers,
            name="获取用户资料"
        )

    @task(3)
    def update_profile(self):
        """更新用户资料（权重：3）"""
        if not self.token:
            self.login()
            return

        headers = {"Authorization": f"Bearer {self.token}"}
        self.client.patch(
            "/api/v1/auth/profile",
            headers=headers,
            json={
                "real_name": f"User{random.randint(1, 1000)}",
                "bio": "This is a test bio"
            },
            name="更新用户资料"
        )

    @task(2)
    def change_password(self):
        """修改密码（权重：2）"""
        if not self.token:
            self.login()
            return

        headers = {"Authorization": f"Bearer {self.token}"}
        self.client.post(
            "/api/v1/auth/change-password",
            headers=headers,
            json={
                "old_password": "OldPassword123!",
                "new_password": "NewPassword123!"
            },
            name="修改密码"
        )

    @task(1)
    def logout(self):
        """登出（权重：1）"""
        if not self.token:
            return

        headers = {"Authorization": f"Bearer {self.token}"}
        self.client.post(
            "/api/v1/auth/logout",
            headers=headers,
            name="登出"
        )
        self.token = None


class ChatAPIUser(HttpUser):
    """AI对话API用户行为模型"""

    wait_time = between(3, 8)

    def on_start(self):
        """用户启动时执行"""
        self.conversation_id = None
        self.token = self.login()

    def login(self) -> Optional[str]:
        """用户登录"""
        response = self.client.post(
            "/api/v1/auth/login",
            json={
                "email": "admin@example.com",
                "password": "Admin@123"
            },
            name="登录(聊天用户)"
        )

        if response.status_code == 200:
            return response.json().get("data", {}).get("access_token")
        return None

    @task(10)
    def send_message(self):
        """发送聊天消息（权重：10）"""
        if not self.token:
            self.token = self.login()
            return

        headers = {"Authorization": f"Bearer {self.token}"}

        # 若没有对话，先创建
        if not self.conversation_id:
            create_response = self.client.post(
                "/api/v1/chat/conversations",
                headers=headers,
                json={
                    "title": f"Conversation {random.randint(1, 1000)}",
                    "agent_type": random.choice(["marketing", "cultural", "data", "general"])
                },
                name="创建对话"
            )
            if create_response.status_code == 201:
                self.conversation_id = create_response.json().get("data", {}).get("id")

        if self.conversation_id:
            questions = [
                "这个产品有什么特点?",
                "如何选购这个产品?",
                "产品的营养价值如何?",
                "适合什么人群?",
                "有什么推荐的食用方式?"
            ]

            self.client.post(
                f"/api/v1/chat/conversations/{self.conversation_id}/messages",
                headers=headers,
                json={"content": random.choice(questions)},
                name="发送消息"
            )

    @task(5)
    def get_conversation_history(self):
        """获取对话历史（权重：5）"""
        if not self.token or not self.conversation_id:
            return

        headers = {"Authorization": f"Bearer {self.token}"}
        self.client.get(
            f"/api/v1/chat/conversations/{self.conversation_id}/messages",
            headers=headers,
            params={"limit": 50},
            name="获取对话历史"
        )

    @task(2)
    def list_conversations(self):
        """列出所有对话（权重：2）"""
        if not self.token:
            return

        headers = {"Authorization": f"Bearer {self.token}"}
        self.client.get(
            "/api/v1/chat/conversations",
            headers=headers,
            params={"limit": 20},
            name="列出对话"
        )


# 事件监听器用于性能分析
@events.test_start.add_listener
def on_test_start(environment, **kwargs):
    """测试开始时执行"""
    print("\n" + "="*60)
    print("性能测试启动")
    print(f"目标服务器: {environment.host}")
    print("="*60)


@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    """测试停止时执行"""
    print("\n" + "="*60)
    print("性能测试完成")
    print("="*60)

    # 打印统计信息
    for task_data in environment.stats.entries.values():
        print(f"\n任务: {task_data.name}")
        print(f"  请求数: {task_data.num_requests}")
        print(f"  失败数: {task_data.num_failures}")
        print(f"  平均响应时间: {task_data.avg_response_time:.2f}ms")
        print(f"  最小响应时间: {task_data.min_response_time:.2f}ms")
        print(f"  最大响应时间: {task_data.max_response_time:.2f}ms")
        print(f"  中位数响应时间: {task_data.median_response_time:.2f}ms")
        print(f"  P95响应时间: {task_data.get_response_time_percentile(0.95):.2f}ms")
        print(f"  P99响应时间: {task_data.get_response_time_percentile(0.99):.2f}ms")


# 性能基准
class PerformanceBenchmark:
    """性能基准检查"""

    # 定义性能基准（毫秒）
    BENCHMARKS = {
        "获取产品列表": {
            "p95": 500,      # P95响应时间不超过500ms
            "p99": 1000,     # P99响应时间不超过1000ms
            "avg": 200       # 平均响应时间不超过200ms
        },
        "获取产品详情": {
            "p95": 300,
            "p99": 500,
            "avg": 100
        },
        "搜索产品": {
            "p95": 1000,
            "p99": 2000,
            "avg": 500
        },
        "登录": {
            "p95": 500,
            "p99": 1000,
            "avg": 200
        },
        "发送消息": {
            "p95": 2000,
            "p99": 3000,
            "avg": 1000
        }
    }

    @classmethod
    def check_performance(cls, stats):
        """检查性能是否满足基准"""
        failures = []

        for entry_name, benchmark in cls.BENCHMARKS.items():
            # 查找对应的统计条目
            for stats_entry in stats.entries.values():
                if entry_name in stats_entry.name:
                    # 检查指标
                    if stats_entry.avg_response_time > benchmark["avg"]:
                        failures.append(
                            f"{entry_name}: 平均响应时间 {stats_entry.avg_response_time:.2f}ms "
                            f"超过基准 {benchmark['avg']}ms"
                        )

                    p95 = stats_entry.get_response_time_percentile(0.95)
                    if p95 > benchmark["p95"]:
                        failures.append(
                            f"{entry_name}: P95响应时间 {p95:.2f}ms "
                            f"超过基准 {benchmark['p95']}ms"
                        )

                    p99 = stats_entry.get_response_time_percentile(0.99)
                    if p99 > benchmark["p99"]:
                        failures.append(
                            f"{entry_name}: P99响应时间 {p99:.2f}ms "
                            f"超过基准 {benchmark['p99']}ms"
                        )

        if failures:
            print("\n性能基准检查失败:")
            for failure in failures:
                print(f"  ✗ {failure}")
        else:
            print("\n✓ 所有性能基准检查通过")

        return len(failures) == 0


if __name__ == "__main__":
    import os
    os.system("locust -f tests/performance_tests.py --host=http://localhost:8000")
