"""
内容生成测试脚本

功能：
- 测试内容生成功能
- 测试RAG知识库集成
- 测试批量生成
- 测试内容评分和导出

使用方法：
    python test_content_generation.py
"""

import asyncio
import httpx
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional

BASE_URL = "http://localhost:8000"
TIMEOUT = 60.0  # 内容生成需要更长的超时时间

test_results = {
    "total": 0,
    "passed": 0,
    "failed": 0,
    "errors": []
}


class ContentGenerationTester:
    """内容生成测试器"""

    def __init__(self, base_url: str = BASE_URL):
        self.base_url = base_url
        self.client = None
        self.access_token = None
        self.test_product_id = None
        self.test_template_id = None
        self.generated_content_id = None

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

    async def setup(self):
        """测试前准备：登录并获取测试数据"""
        print("\n=== 测试环境准备 ===")

        # 登录获取Token
        try:
            response = await self.client.post(
                "/api/v1/auth/login",
                json={
                    "email": "test@example.com",
                    "password": "Test123!@#"
                }
            )

            if response.status_code == 200:
                data = response.json()
                self.access_token = data.get("data", {}).get("access_token")
                if self.access_token:
                    print(f"✓ 登录成功，Token: {self.access_token[:20]}...")
                else:
                    print("✗ 登录失败：未返回Token")
                    return False
            else:
                print(f"✗ 登录失败：状态码 {response.status_code}")
                return False

        except Exception as e:
            print(f"✗ 登录异常：{str(e)}")
            return False

        # 获取测试产品ID
        try:
            response = await self.client.get("/api/v1/products?page=1&size=1")
            if response.status_code == 200:
                data = response.json()
                items = data.get("data", {}).get("items", [])
                if items:
                    self.test_product_id = items[0].get("id")
                    print(f"✓ 获取测试产品ID: {self.test_product_id}")
                else:
                    print("✗ 没有可用的测试产品")
                    return False
            else:
                print(f"✗ 获取产品失败：状态码 {response.status_code}")
                return False

        except Exception as e:
            print(f"✗ 获取产品异常：{str(e)}")
            return False

        # 获取测试模板ID（假设存在）
        self.test_template_id = 1
        print(f"✓ 使用测试模板ID: {self.test_template_id}")

        return True

    async def test_01_generate_content(self):
        """测试1: 生成内容"""
        print("\n=== 测试1: 生成内容 ===")

        if not self.access_token or not self.test_product_id:
            self.log_test("生成内容", False, "测试环境未准备好")
            return False

        try:
            start_time = datetime.now()

            response = await self.client.post(
                "/api/v1/content/generate",
                headers={"Authorization": f"Bearer {self.access_token}"},
                json={
                    "product_id": self.test_product_id,
                    "template_id": self.test_template_id,
                    "config": {
                        "length": 500,
                        "style": "professional",
                        "target_audience": "enterprise"
                    }
                }
            )

            elapsed = (datetime.now() - start_time).total_seconds()

            if response.status_code == 200:
                data = response.json()
                if "data" in data:
                    content = data["data"].get("content", "")
                    self.generated_content_id = data["data"].get("id")

                    if content:
                        self.log_test(
                            "生成内容",
                            True,
                            f"生成成功，耗时 {elapsed:.2f}s，内容长度 {len(content)} 字符"
                        )
                        return True
                    else:
                        self.log_test("生成内容", False, "返回内容为空")
                        return False
                else:
                    self.log_test("生成内容", False, "响应格式错误")
                    return False
            else:
                self.log_test(
                    "生成内容",
                    False,
                    f"状态码 {response.status_code}, 响应: {response.text[:200]}"
                )
                return False

        except Exception as e:
            self.log_test("生成内容", False, str(e))
            return False

    async def test_02_generate_with_rag(self):
        """测试2: 使用RAG生成内容"""
        print("\n=== 测试2: 使用RAG生成内容 ===")

        if not self.access_token or not self.test_product_id:
            self.log_test("RAG生成", False, "测试环境未准备好")
            return False

        try:
            response = await self.client.post(
                "/api/v1/content/generate",
                headers={"Authorization": f"Bearer {self.access_token}"},
                json={
                    "product_id": self.test_product_id,
                    "template_id": self.test_template_id,
                    "config": {
                        "use_rag": True,
                        "length": 500,
                        "style": "professional"
                    }
                }
            )

            if response.status_code == 200:
                data = response.json()
                content = data.get("data", {}).get("content", "")

                if content:
                    self.log_test(
                        "RAG生成",
                        True,
                        f"RAG生成成功，内容长度 {len(content)} 字符"
                    )
                    return True
                else:
                    self.log_test("RAG生成", False, "返回内容为空")
                    return False
            else:
                self.log_test(
                    "RAG生成",
                    False,
                    f"状态码 {response.status_code}"
                )
                return False

        except Exception as e:
            self.log_test("RAG生成", False, str(e))
            return False

    async def test_03_batch_generate(self):
        """测试3: 批量生成"""
        print("\n=== 测试3: 批量生成 ===")

        if not self.access_token or not self.test_product_id:
            self.log_test("批量生成", False, "测试环境未准备好")
            return False

        try:
            start_time = datetime.now()

            # 批量生成3个内容
            response = await self.client.post(
                "/api/v1/content/batch-generate",
                headers={"Authorization": f"Bearer {self.access_token}"},
                json={
                    "product_ids": [self.test_product_id] * 3,
                    "template_id": self.test_template_id,
                    "config": {
                        "length": 300,
                        "style": "professional"
                    }
                }
            )

            elapsed = (datetime.now() - start_time).total_seconds()

            if response.status_code in [200, 201, 202]:
                data = response.json()
                task_id = data.get("data", {}).get("task_id")

                if task_id:
                    self.log_test(
                        "批量生成",
                        True,
                        f"批量任务创建成功，任务ID: {task_id}，耗时 {elapsed:.2f}s"
                    )
                    return True
                else:
                    self.log_test("批量生成", False, "未返回任务ID")
                    return False
            else:
                self.log_test(
                    "批量生成",
                    False,
                    f"状态码 {response.status_code}"
                )
                return False

        except Exception as e:
            self.log_test("批量生成", False, str(e))
            return False

    async def test_04_score_content(self):
        """测试4: 内容评分"""
        print("\n=== 测试4: 内容评分 ===")

        if not self.access_token or not self.generated_content_id:
            self.log_test("内容评分", False, "没有可评分的内容")
            return False

        try:
            response = await self.client.post(
                "/api/v1/content/score",
                headers={"Authorization": f"Bearer {self.access_token}"},
                json={
                    "content_id": self.generated_content_id
                }
            )

            if response.status_code == 200:
                data = response.json()
                score = data.get("data", {}).get("score")

                if score is not None:
                    self.log_test(
                        "内容评分",
                        True,
                        f"评分成功，得分: {score}/100"
                    )
                    return True
                else:
                    self.log_test("内容评分", False, "未返回评分")
                    return False
            else:
                self.log_test(
                    "内容评分",
                    False,
                    f"状态码 {response.status_code}"
                )
                return False

        except Exception as e:
            self.log_test("内容评分", False, str(e))
            return False

    async def test_05_export_markdown(self):
        """测试5: 导出Markdown"""
        print("\n=== 测试5: 导出Markdown ===")

        if not self.access_token or not self.generated_content_id:
            self.log_test("导出Markdown", False, "没有可导出的内容")
            return False

        try:
            response = await self.client.post(
                "/api/v1/content/export",
                headers={"Authorization": f"Bearer {self.access_token}"},
                json={
                    "content_id": self.generated_content_id,
                    "format": "markdown"
                }
            )

            if response.status_code == 200:
                # 检查是否返回文件
                content_type = response.headers.get("content-type", "")

                if "application/octet-stream" in content_type or "text/markdown" in content_type:
                    file_size = len(response.content)
                    self.log_test(
                        "导出Markdown",
                        True,
                        f"导出成功，文件大小: {file_size} 字节"
                    )
                    return True
                else:
                    self.log_test(
                        "导出Markdown",
                        False,
                        f"返回类型错误: {content_type}"
                    )
                    return False
            else:
                self.log_test(
                    "导出Markdown",
                    False,
                    f"状态码 {response.status_code}"
                )
                return False

        except Exception as e:
            self.log_test("导出Markdown", False, str(e))
            return False

    async def test_06_export_word(self):
        """测试6: 导出Word"""
        print("\n=== 测试6: 导出Word ===")

        if not self.access_token or not self.generated_content_id:
            self.log_test("导出Word", False, "没有可导出的内容")
            return False

        try:
            response = await self.client.post(
                "/api/v1/content/export",
                headers={"Authorization": f"Bearer {self.access_token}"},
                json={
                    "content_id": self.generated_content_id,
                    "format": "docx"
                }
            )

            if response.status_code == 200:
                content_type = response.headers.get("content-type", "")

                if "application/vnd.openxmlformats" in content_type or "application/octet-stream" in content_type:
                    file_size = len(response.content)
                    self.log_test(
                        "导出Word",
                        True,
                        f"导出成功，文件大小: {file_size} 字节"
                    )
                    return True
                else:
                    self.log_test(
                        "导出Word",
                        False,
                        f"返回类型错误: {content_type}"
                    )
                    return False
            else:
                self.log_test(
                    "导出Word",
                    False,
                    f"状态码 {response.status_code}"
                )
                return False

        except Exception as e:
            self.log_test("导出Word", False, str(e))
            return False

    async def test_07_get_templates(self):
        """测试7: 获取模板列表"""
        print("\n=== 测试7: 获取模板列表 ===")

        if not self.access_token:
            self.log_test("获取模板列表", False, "未登录")
            return False

        try:
            response = await self.client.get(
                "/api/v1/content/templates",
                headers={"Authorization": f"Bearer {self.access_token}"}
            )

            if response.status_code == 200:
                data = response.json()
                templates = data.get("data", {}).get("templates", [])

                self.log_test(
                    "获取模板列表",
                    True,
                    f"获取成功，共 {len(templates)} 个模板"
                )
                return True
            else:
                self.log_test(
                    "获取模板列表",
                    False,
                    f"状态码 {response.status_code}"
                )
                return False

        except Exception as e:
            self.log_test("获取模板列表", False, str(e))
            return False

    async def test_08_get_tasks(self):
        """测试8: 获取任务列表"""
        print("\n=== 测试8: 获取任务列表 ===")

        if not self.access_token:
            self.log_test("获取任务列表", False, "未登录")
            return False

        try:
            response = await self.client.get(
                "/api/v1/content/tasks",
                headers={"Authorization": f"Bearer {self.access_token}"}
            )

            if response.status_code == 200:
                data = response.json()
                tasks = data.get("data", {}).get("tasks", [])

                self.log_test(
                    "获取任务列表",
                    True,
                    f"获取成功，共 {len(tasks)} 个任务"
                )
                return True
            else:
                self.log_test(
                    "获取任务列表",
                    False,
                    f"状态码 {response.status_code}"
                )
                return False

        except Exception as e:
            self.log_test("获取任务列表", False, str(e))
            return False

    async def test_09_invalid_product_id(self):
        """测试9: 无效产品ID"""
        print("\n=== 测试9: 无效产品ID ===")

        if not self.access_token:
            self.log_test("无效产品ID", False, "未登录")
            return False

        try:
            response = await self.client.post(
                "/api/v1/content/generate",
                headers={"Authorization": f"Bearer {self.access_token}"},
                json={
                    "product_id": 999999,
                    "template_id": self.test_template_id,
                    "config": {"length": 500}
                }
            )

            if response.status_code == 404:
                self.log_test("无效产品ID", True, "正确返回404错误")
                return True
            else:
                self.log_test(
                    "无效产品ID",
                    False,
                    f"应返回404，实际 {response.status_code}"
                )
                return False

        except Exception as e:
            self.log_test("无效产品ID", False, str(e))
            return False

    async def test_10_missing_config(self):
        """测试10: 缺少配置参数"""
        print("\n=== 测试10: 缺少配置参数 ===")

        if not self.access_token or not self.test_product_id:
            self.log_test("缺少配置参数", False, "测试环境未准备好")
            return False

        try:
            response = await self.client.post(
                "/api/v1/content/generate",
                headers={"Authorization": f"Bearer {self.access_token}"},
                json={
                    "product_id": self.test_product_id,
                    "template_id": self.test_template_id
                    # 缺少config参数
                }
            )

            if response.status_code in [400, 422]:
                self.log_test("缺少配置参数", True, "正确返回错误")
                return True
            else:
                self.log_test(
                    "缺少配置参数",
                    False,
                    f"应返回400/422，实际 {response.status_code}"
                )
                return False

        except Exception as e:
            self.log_test("缺少配置参数", False, str(e))
            return False


async def run_content_generation_tests():
    """运行内容生成测试"""
    print("=" * 60)
    print("内容生成测试")
    print("=" * 60)
    print(f"基础URL: {BASE_URL}")
    print(f"开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    async with ContentGenerationTester(BASE_URL) as tester:
        # 准备测试环境
        if not await tester.setup():
            print("\n测试环境准备失败，终止测试")
            return 1

        # 按顺序执行测试
        await tester.test_01_generate_content()
        await tester.test_02_generate_with_rag()
        await tester.test_03_batch_generate()
        await tester.test_04_score_content()
        await tester.test_05_export_markdown()
        await tester.test_06_export_word()
        await tester.test_07_get_templates()
        await tester.test_08_get_tasks()
        await tester.test_09_invalid_product_id()
        await tester.test_10_missing_config()

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
    results_file = results_dir / f"content_generation_test_results_{timestamp}.json"

    with open(results_file, "w", encoding="utf-8") as f:
        json.dump({
            "timestamp": datetime.now().isoformat(),
            "results": test_results
        }, f, indent=2, ensure_ascii=False)

    print(f"\n测试结果已保存到: {results_file}")


if __name__ == "__main__":
    import sys
    try:
        exit_code = asyncio.run(run_content_generation_tests())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\n测试被用户中断")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n测试执行失败: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
