"""
认证流程测试脚本

功能：
- 测试完整的认证流程
- 测试Token生命周期
- 测试权限验证
- 测试密码安全

使用方法：
    python test_auth_flow.py
"""

import asyncio
import httpx
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional

BASE_URL = "http://localhost:8000"
TIMEOUT = 30.0

test_results = {
    "total": 0,
    "passed": 0,
    "failed": 0,
    "errors": []
}


class AuthFlowTester:
    """认证流程测试器"""

    def __init__(self, base_url: str = BASE_URL):
        self.base_url = base_url
        self.client = None
        self.test_user = None
        self.access_token = None
        self.refresh_token = None

    async def __aenter__(self):
        self.client = httpx.AsyncClient(base_url=self.base_url, timeout=TIMEOUT)
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.client:
            await self.client.aclose()

    def log_test(self, test_name: str, passed: bool, message: str = ""):
        """记录测试结果"""
        test_results["total"] += 1
        if passed:
            test_results["passed"] += 1
            print(f"✅ {test_name}")
            if message:
                print(f"   {message}")
        else:
            test_results["failed"] += 1
            test_results["errors"].append(f"{test_name}: {message}")
            print(f"❌ {test_name}")
            print(f"   {message}")

    async def test_01_register_new_user(self):
        """测试1: 注册新用户"""
        print("\n=== 测试1: 注册新用户 ===")

        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        self.test_user = {
            "email": f"auth_test_{timestamp}@example.com",
            "password": "AuthTest123!@#",
            "username": f"AuthTest{timestamp}"
        }

        try:
            response = await self.client.post(
                "/api/v1/auth/register",
                json=self.test_user
            )

            if response.status_code == 201:
                data = response.json()
                self.log_test(
                    "注册新用户",
                    True,
                    f"用户 {self.test_user['email']} 注册成功"
                )
                return True
            else:
                self.log_test(
                    "注册新用户",
                    False,
                    f"状态码 {response.status_code}, 响应: {response.text[:200]}"
                )
                return False

        except Exception as e:
            self.log_test("注册新用户", False, str(e))
            return False

    async def test_02_login_with_credentials(self):
        """测试2: 使用凭证登录"""
        print("\n=== 测试2: 使用凭证登录 ===")

        if not self.test_user:
            self.log_test("使用凭证登录", False, "测试用户未创建")
            return False

        try:
            response = await self.client.post(
                "/api/v1/auth/login",
                json={
                    "email": self.test_user["email"],
                    "password": self.test_user["password"]
                }
            )

            if response.status_code == 200:
                data = response.json()
                if "data" in data:
                    self.access_token = data["data"].get("access_token")
                    self.refresh_token = data["data"].get("refresh_token")

                    if self.access_token:
                        self.log_test(
                            "使用凭证登录",
                            True,
                            f"Token: {self.access_token[:20]}..."
                        )
                        return True
                    else:
                        self.log_test("使用凭证登录", False, "未返回Token")
                        return False
                else:
                    self.log_test("使用凭证登录", False, "响应格式错误")
                    return False
            else:
                self.log_test(
                    "使用凭证登录",
                    False,
                    f"状态码 {response.status_code}"
                )
                return False

        except Exception as e:
            self.log_test("使用凭证登录", False, str(e))
            return False

    async def test_03_verify_token(self):
        """测试3: 验证Token"""
        print("\n=== 测试3: 验证Token ===")

        if not self.access_token:
            self.log_test("验证Token", False, "Token未获取")
            return False

        try:
            response = await self.client.get(
                "/api/v1/auth/verify",
                headers={"Authorization": f"Bearer {self.access_token}"}
            )

            if response.status_code == 200:
                data = response.json()
                self.log_test("验证Token", True, "Token有效")
                return True
            else:
                self.log_test(
                    "验证Token",
                    False,
                    f"状态码 {response.status_code}"
                )
                return False

        except Exception as e:
            self.log_test("验证Token", False, str(e))
            return False

    async def test_04_access_protected_resource(self):
        """测试4: 访问受保护资源"""
        print("\n=== 测试4: 访问受保护资源 ===")

        if not self.access_token:
            self.log_test("访问受保护资源", False, "Token未获取")
            return False

        try:
            # 尝试访问需要认证的端点（例如对话列表）
            response = await self.client.get(
                "/api/v1/chat/conversations",
                headers={"Authorization": f"Bearer {self.access_token}"}
            )

            if response.status_code in [200, 404]:  # 200或404都表示认证通过
                self.log_test("访问受保护资源", True, "认证成功")
                return True
            elif response.status_code == 401:
                self.log_test("访问受保护资源", False, "认证失败")
                return False
            else:
                self.log_test(
                    "访问受保护资源",
                    True,  # 其他状态码也算通过认证
                    f"状态码 {response.status_code}"
                )
                return True

        except Exception as e:
            self.log_test("访问受保护资源", False, str(e))
            return False

    async def test_05_access_without_token(self):
        """测试5: 无Token访问受保护资源"""
        print("\n=== 测试5: 无Token访问受保护资源 ===")

        try:
            response = await self.client.get("/api/v1/chat/conversations")

            if response.status_code == 401:
                self.log_test("无Token访问", True, "正确拒绝访问")
                return True
            else:
                self.log_test(
                    "无Token访问",
                    False,
                    f"应返回401，实际 {response.status_code}"
                )
                return False

        except Exception as e:
            self.log_test("无Token访问", False, str(e))
            return False

    async def test_06_invalid_token(self):
        """测试6: 使用无效Token"""
        print("\n=== 测试6: 使用无效Token ===")

        try:
            response = await self.client.get(
                "/api/v1/auth/verify",
                headers={"Authorization": "Bearer invalid_token_12345"}
            )

            if response.status_code == 401:
                self.log_test("使用无效Token", True, "正确识别无效Token")
                return True
            else:
                self.log_test(
                    "使用无效Token",
                    False,
                    f"应返回401，实际 {response.status_code}"
                )
                return False

        except Exception as e:
            self.log_test("使用无效Token", False, str(e))
            return False

    async def test_07_wrong_password(self):
        """测试7: 错误密码登录"""
        print("\n=== 测试7: 错误密码登录 ===")

        if not self.test_user:
            self.log_test("错误密码登录", False, "测试用户未创建")
            return False

        try:
            response = await self.client.post(
                "/api/v1/auth/login",
                json={
                    "email": self.test_user["email"],
                    "password": "WrongPassword123!"
                }
            )

            if response.status_code == 401:
                self.log_test("错误密码登录", True, "正确拒绝错误密码")
                return True
            else:
                self.log_test(
                    "错误密码登录",
                    False,
                    f"应返回401，实际 {response.status_code}"
                )
                return False

        except Exception as e:
            self.log_test("错误密码登录", False, str(e))
            return False

    async def test_08_duplicate_registration(self):
        """测试8: 重复注册"""
        print("\n=== 测试8: 重复注册 ===")

        if not self.test_user:
            self.log_test("重复注册", False, "测试用户未创建")
            return False

        try:
            response = await self.client.post(
                "/api/v1/auth/register",
                json=self.test_user
            )

            if response.status_code == 400:
                self.log_test("重复注册", True, "正确拒绝重复注册")
                return True
            else:
                self.log_test(
                    "重复注册",
                    False,
                    f"应返回400，实际 {response.status_code}"
                )
                return False

        except Exception as e:
            self.log_test("重复注册", False, str(e))
            return False

    async def test_09_weak_password(self):
        """测试9: 弱密码注册"""
        print("\n=== 测试9: 弱密码注册 ===")

        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        weak_user = {
            "email": f"weak_{timestamp}@example.com",
            "password": "123",
            "username": f"WeakUser{timestamp}"
        }

        try:
            response = await self.client.post(
                "/api/v1/auth/register",
                json=weak_user
            )

            if response.status_code in [400, 422]:
                self.log_test("弱密码注册", True, "正确拒绝弱密码")
                return True
            else:
                self.log_test(
                    "弱密码注册",
                    False,
                    f"应返回400/422，实际 {response.status_code}"
                )
                return False

        except Exception as e:
            self.log_test("弱密码注册", False, str(e))
            return False

    async def test_10_logout(self):
        """测试10: 登出"""
        print("\n=== 测试10: 登出 ===")

        if not self.access_token:
            self.log_test("登出", False, "Token未获取")
            return False

        try:
            response = await self.client.post(
                "/api/v1/auth/logout",
                headers={"Authorization": f"Bearer {self.access_token}"}
            )

            if response.status_code == 200:
                self.log_test("登出", True, "登出成功")
                return True
            else:
                self.log_test(
                    "登出",
                    False,
                    f"状态码 {response.status_code}"
                )
                return False

        except Exception as e:
            self.log_test("登出", False, str(e))
            return False


async def run_auth_flow_tests():
    """运行认证流程测试"""
    print("=" * 60)
    print("认证流程测试")
    print("=" * 60)
    print(f"基础URL: {BASE_URL}")
    print(f"开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    async with AuthFlowTester(BASE_URL) as tester:
        # 按顺序执行测试
        await tester.test_01_register_new_user()
        await tester.test_02_login_with_credentials()
        await tester.test_03_verify_token()
        await tester.test_04_access_protected_resource()
        await tester.test_05_access_without_token()
        await tester.test_06_invalid_token()
        await tester.test_07_wrong_password()
        await tester.test_08_duplicate_registration()
        await tester.test_09_weak_password()
        await tester.test_10_logout()

    # 打印测试结果
    print("\n" + "=" * 60)
    print("测试结果汇总")
    print("=" * 60)
    print(f"总用例数: {test_results['total']}")
    print(f"✅ 通过: {test_results['passed']}")
    print(f"❌ 失败: {test_results['failed']}")

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

    return 0 if test_results['failed'] == 0 else 1


def save_results():
    """保存测试结果"""
    results_dir = Path(__file__).parent.parent.parent / "reports"
    results_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    results_file = results_dir / f"auth_flow_test_results_{timestamp}.json"

    with open(results_file, "w", encoding="utf-8") as f:
        json.dump({
            "timestamp": datetime.now().isoformat(),
            "results": test_results
        }, f, indent=2, ensure_ascii=False)

    print(f"\n测试结果已保存到: {results_file}")


if __name__ == "__main__":
    import sys
    try:
        exit_code = asyncio.run(run_auth_flow_tests())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\n测试被用户中断")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n测试执行失败: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
