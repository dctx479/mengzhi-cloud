"""
API集成测试脚本

功能：
- 测试所有API端点
- 验证请求响应
- 检查错误处理
- 生成测试报告

使用方法：
    python test_api_integration.py
    python test_api_integration.py --module auth
    python test_api_integration.py --verbose
"""

import asyncio
import httpx
import json
import sys
import argparse
from typing import Dict, List, Optional, Any
from datetime import datetime
from pathlib import Path

# 配置
BASE_URL = "http://localhost:8000"
TIMEOUT = 30.0

# 测试结果
test_results = {
    "total": 0,
    "passed": 0,
    "failed": 0,
    "skipped": 0,
    "errors": []
}


class APITester:
    """API测试器"""

    def __init__(self, base_url: str = BASE_URL):
        self.base_url = base_url
        self.client = None
        self.tokens = {}
        self.test_data = {}

    async def __aenter__(self):
        self.client = httpx.AsyncClient(base_url=self.base_url, timeout=TIMEOUT)
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.client:
            await self.client.aclose()

    async def request(
        self,
        method: str,
        endpoint: str,
        headers: Optional[Dict] = None,
        json_data: Optional[Dict] = None,
        params: Optional[Dict] = None,
        files: Optional[Dict] = None
    ) -> httpx.Response:
        """发送HTTP请求"""
        try:
            response = await self.client.request(
                method=method,
                url=endpoint,
                headers=headers,
                json=json_data,
                params=params,
                files=files
            )
            return response
        except Exception as e:
            print(f"❌ 请求失败: {method} {endpoint} - {str(e)}")
            raise

    def assert_status(self, response: httpx.Response, expected: int, test_name: str):
        """断言状态码"""
        test_results["total"] += 1
        if response.status_code == expected:
            test_results["passed"] += 1
            print(f"✅ {test_name}: 状态码 {response.status_code}")
            return True
        else:
            test_results["failed"] += 1
            error = f"{test_name}: 期望 {expected}, 实际 {response.status_code}"
            test_results["errors"].append(error)
            print(f"❌ {error}")
            print(f"   响应: {response.text[:200]}")
            return False

    def assert_json_field(self, data: Dict, field: str, test_name: str):
        """断言JSON字段存在"""
        test_results["total"] += 1
        if field in data:
            test_results["passed"] += 1
            print(f"✅ {test_name}: 字段 '{field}' 存在")
            return True
        else:
            test_results["failed"] += 1
            error = f"{test_name}: 字段 '{field}' 不存在"
            test_results["errors"].append(error)
            print(f"❌ {error}")
            return False


class AuthTests:
    """认证模块测试"""

    def __init__(self, tester: APITester):
        self.tester = tester

    async def test_register(self):
        """测试用户注册"""
        print("\n=== 测试用户注册 ===")

        # 正常注册
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        test_user = {
            "email": f"test_{timestamp}@example.com",
            "password": "Test123!@#",
            "username": f"TestUser{timestamp}"
        }

        response = await self.tester.request(
            "POST",
            "/api/v1/auth/register",
            json_data=test_user
        )

        if self.tester.assert_status(response, 201, "AUTH-001-01: 正常注册"):
            data = response.json()
            self.tester.assert_json_field(data, "data", "AUTH-001-01: 返回数据")
            self.tester.test_data["test_user"] = test_user

        # 邮箱已存在
        response = await self.tester.request(
            "POST",
            "/api/v1/auth/register",
            json_data=test_user
        )
        self.tester.assert_status(response, 400, "AUTH-001-02: 邮箱已存在")

        # 密码格式错误
        weak_user = test_user.copy()
        weak_user["email"] = f"weak_{timestamp}@example.com"
        weak_user["password"] = "123"

        response = await self.tester.request(
            "POST",
            "/api/v1/auth/register",
            json_data=weak_user
        )
        self.tester.assert_status(response, 400, "AUTH-001-03: 密码格式错误")

    async def test_login(self):
        """测试用户登录"""
        print("\n=== 测试用户登录 ===")

        # 正常登录
        if "test_user" in self.tester.test_data:
            test_user = self.tester.test_data["test_user"]

            response = await self.tester.request(
                "POST",
                "/api/v1/auth/login",
                json_data={
                    "email": test_user["email"],
                    "password": test_user["password"]
                }
            )

            if self.tester.assert_status(response, 200, "AUTH-002-01: 正常登录"):
                data = response.json()
                if self.tester.assert_json_field(data, "data", "AUTH-002-01: 返回Token"):
                    token = data["data"].get("access_token")
                    if token:
                        self.tester.tokens["user"] = token
                        print(f"   Token已保存")

        # 密码错误
        response = await self.tester.request(
            "POST",
            "/api/v1/auth/login",
            json_data={
                "email": "test@example.com",
                "password": "WrongPassword123!"
            }
        )
        self.tester.assert_status(response, 401, "AUTH-002-02: 密码错误")

        # 用户不存在
        response = await self.tester.request(
            "POST",
            "/api/v1/auth/login",
            json_data={
                "email": "nonexistent@example.com",
                "password": "Test123!@#"
            }
        )
        self.tester.assert_status(response, 401, "AUTH-002-03: 用户不存在")

    async def test_verify_token(self):
        """测试Token验证"""
        print("\n=== 测试Token验证 ===")

        # 有效Token
        if "user" in self.tester.tokens:
            response = await self.tester.request(
                "GET",
                "/api/v1/auth/verify",
                headers={"Authorization": f"Bearer {self.tester.tokens['user']}"}
            )
            self.tester.assert_status(response, 200, "AUTH-007-01: 有效Token")

        # 无效Token
        response = await self.tester.request(
            "GET",
            "/api/v1/auth/verify",
            headers={"Authorization": "Bearer invalid_token_12345"}
        )
        self.tester.assert_status(response, 401, "AUTH-007-02: 无效Token")


class ProductTests:
    """产品模块测试"""

    def __init__(self, tester: APITester):
        self.tester = tester

    async def test_list_products(self):
        """测试获取产品列表"""
        print("\n=== 测试获取产品列表 ===")

        # 默认分页
        response = await self.tester.request(
            "GET",
            "/api/v1/products",
            params={"page": 1, "size": 10}
        )

        if self.tester.assert_status(response, 200, "PROD-001-01: 默认分页"):
            data = response.json()
            self.tester.assert_json_field(data, "data", "PROD-001-01: 返回数据")
            if "data" in data:
                items = data["data"].get("items", [])
                print(f"   返回 {len(items)} 个产品")

        # 搜索功能
        response = await self.tester.request(
            "GET",
            "/api/v1/products",
            params={"search": "牛肉", "page": 1, "size": 10}
        )
        self.tester.assert_status(response, 200, "PROD-001-02: 搜索功能")

        # 类别筛选
        response = await self.tester.request(
            "GET",
            "/api/v1/products",
            params={"category": "肉类", "page": 1, "size": 10}
        )
        self.tester.assert_status(response, 200, "PROD-001-03: 类别筛选")

        # 排序功能
        response = await self.tester.request(
            "GET",
            "/api/v1/products",
            params={"sort_by": "price", "sort_order": "asc", "page": 1, "size": 10}
        )
        self.tester.assert_status(response, 200, "PROD-001-07: 排序功能")

        # 无效排序字段
        response = await self.tester.request(
            "GET",
            "/api/v1/products",
            params={"sort_by": "invalid_field", "page": 1, "size": 10}
        )
        self.tester.assert_status(response, 400, "PROD-001-08: 无效排序字段")

    async def test_get_product(self):
        """测试获取产品详情"""
        print("\n=== 测试获取产品详情 ===")

        # 正常获取（假设产品ID=1存在）
        response = await self.tester.request(
            "GET",
            "/api/v1/products/1"
        )

        if self.tester.assert_status(response, 200, "PROD-002-01: 正常获取"):
            data = response.json()
            self.tester.assert_json_field(data, "data", "PROD-002-01: 返回产品详情")

        # 产品不存在
        response = await self.tester.request(
            "GET",
            "/api/v1/products/999999"
        )
        self.tester.assert_status(response, 404, "PROD-002-02: 产品不存在")

    async def test_get_categories(self):
        """测试获取类别列表"""
        print("\n=== 测试获取类别列表 ===")

        response = await self.tester.request(
            "GET",
            "/api/v1/products/categories/list"
        )

        if self.tester.assert_status(response, 200, "PROD-007-01: 正常获取"):
            data = response.json()
            if self.tester.assert_json_field(data, "data", "PROD-007-01: 返回类别"):
                categories = data["data"].get("categories", [])
                print(f"   返回 {len(categories)} 个类别")

    async def test_get_regions(self):
        """测试获取地区列表"""
        print("\n=== 测试获取地区列表 ===")

        response = await self.tester.request(
            "GET",
            "/api/v1/products/regions/list"
        )

        if self.tester.assert_status(response, 200, "PROD-008-01: 正常获取"):
            data = response.json()
            if self.tester.assert_json_field(data, "data", "PROD-008-01: 返回地区"):
                regions = data["data"].get("regions", [])
                print(f"   返回 {len(regions)} 个地区")


class ChatTests:
    """对话模块测试"""

    def __init__(self, tester: APITester):
        self.tester = tester

    async def test_send_message(self):
        """测试发送消息"""
        print("\n=== 测试发送消息 ===")

        if "user" not in self.tester.tokens:
            print("⏸️  跳过：需要先登录")
            test_results["skipped"] += 1
            return

        # 新对话
        response = await self.tester.request(
            "POST",
            "/api/v1/chat/message",
            headers={"Authorization": f"Bearer {self.tester.tokens['user']}"},
            json_data={
                "content": "介绍一下内蒙古的牛肉产品"
            }
        )

        if self.tester.assert_status(response, 200, "CHAT-001-01: 新对话"):
            data = response.json()
            if self.tester.assert_json_field(data, "conversation_id", "CHAT-001-01: 返回对话ID"):
                conversation_id = data.get("conversation_id")
                self.tester.test_data["conversation_id"] = conversation_id
                print(f"   对话ID: {conversation_id}")

        # 空消息
        response = await self.tester.request(
            "POST",
            "/api/v1/chat/message",
            headers={"Authorization": f"Bearer {self.tester.tokens['user']}"},
            json_data={
                "content": ""
            }
        )
        self.tester.assert_status(response, 400, "CHAT-001-03: 空消息")

    async def test_get_conversations(self):
        """测试获取对话列表"""
        print("\n=== 测试获取对话列表 ===")

        if "user" not in self.tester.tokens:
            print("⏸️  跳过：需要先登录")
            test_results["skipped"] += 1
            return

        response = await self.tester.request(
            "GET",
            "/api/v1/chat/conversations",
            headers={"Authorization": f"Bearer {self.tester.tokens['user']}"},
            params={"page": 1, "page_size": 20}
        )

        if self.tester.assert_status(response, 200, "CHAT-003-01: 默认分页"):
            data = response.json()
            self.tester.assert_json_field(data, "items", "CHAT-003-01: 返回对话列表")


class HealthTests:
    """健康检查测试"""

    def __init__(self, tester: APITester):
        self.tester = tester

    async def test_health_check(self):
        """测试健康检查"""
        print("\n=== 测试健康检查 ===")

        # 根路径
        response = await self.tester.request("GET", "/")
        if self.tester.assert_status(response, 200, "HEALTH-001: 根路径"):
            data = response.json()
            self.tester.assert_json_field(data, "status", "HEALTH-001: 返回状态")

        # 健康检查
        response = await self.tester.request("GET", "/health")
        if self.tester.assert_status(response, 200, "HEALTH-002: 健康检查"):
            data = response.json()
            self.tester.assert_json_field(data, "status", "HEALTH-002: 返回状态")


async def run_tests(module: Optional[str] = None, verbose: bool = False):
    """运行测试"""
    print("=" * 60)
    print("API集成测试")
    print("=" * 60)
    print(f"基础URL: {BASE_URL}")
    print(f"开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    async with APITester(BASE_URL) as tester:
        # 健康检查
        health_tests = HealthTests(tester)
        await health_tests.test_health_check()

        # 认证模块
        if module is None or module == "auth":
            auth_tests = AuthTests(tester)
            await auth_tests.test_register()
            await auth_tests.test_login()
            await auth_tests.test_verify_token()

        # 产品模块
        if module is None or module == "products":
            product_tests = ProductTests(tester)
            await product_tests.test_list_products()
            await product_tests.test_get_product()
            await product_tests.test_get_categories()
            await product_tests.test_get_regions()

        # 对话模块
        if module is None or module == "chat":
            chat_tests = ChatTests(tester)
            await chat_tests.test_send_message()
            await chat_tests.test_get_conversations()

    # 打印测试结果
    print("\n" + "=" * 60)
    print("测试结果汇总")
    print("=" * 60)
    print(f"总用例数: {test_results['total']}")
    print(f"✅ 通过: {test_results['passed']}")
    print(f"❌ 失败: {test_results['failed']}")
    print(f"⏸️  跳过: {test_results['skipped']}")

    if test_results['total'] > 0:
        pass_rate = (test_results['passed'] / test_results['total']) * 100
        print(f"通过率: {pass_rate:.2f}%")

    if test_results['errors']:
        print("\n失败用例:")
        for error in test_results['errors']:
            print(f"  - {error}")

    print("=" * 60)
    print(f"结束时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    # 保存测试结果
    save_results()

    # 返回退出码
    return 0 if test_results['failed'] == 0 else 1


def save_results():
    """保存测试结果"""
    results_dir = Path(__file__).parent.parent.parent / "reports"
    results_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    results_file = results_dir / f"api_test_results_{timestamp}.json"

    with open(results_file, "w", encoding="utf-8") as f:
        json.dump({
            "timestamp": datetime.now().isoformat(),
            "results": test_results
        }, f, indent=2, ensure_ascii=False)

    print(f"\n测试结果已保存到: {results_file}")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="API集成测试")
    parser.add_argument(
        "--module",
        choices=["auth", "products", "chat"],
        help="指定测试模块"
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="详细输出"
    )

    args = parser.parse_args()

    try:
        exit_code = asyncio.run(run_tests(args.module, args.verbose))
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\n测试被用户中断")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n测试执行失败: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
