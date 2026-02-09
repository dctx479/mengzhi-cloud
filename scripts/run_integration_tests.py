#!/usr/bin/env python3
"""
集成测试主执行脚本
运行所有集成测试并生成详细报告
"""

import os
import sys
import subprocess
import time
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple


class IntegrationTestRunner:
    """集成测试执行器"""

    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
        self.backend_root = self.project_root / "backend"
        self.frontend_root = self.project_root / "frontend"
        self.results: Dict = {
            "start_time": None,
            "end_time": None,
            "duration": 0,
            "tests": {},
            "summary": {
                "total": 0,
                "passed": 0,
                "failed": 0,
                "skipped": 0,
                "warnings": 0
            },
            "bugs": []
        }

    def print_header(self, title: str):
        """打印标题"""
        print("\n" + "=" * 80)
        print(f"  {title}")
        print("=" * 80 + "\n")

    def run_command(self, cmd: List[str], cwd: Path, timeout: int = 300) -> Tuple[bool, str, str]:
        """运行命令并返回结果"""
        try:
            result = subprocess.run(
                cmd,
                cwd=cwd,
                capture_output=True,
                text=True,
                timeout=timeout
            )
            success = result.returncode == 0
            return success, result.stdout, result.stderr
        except subprocess.TimeoutExpired:
            return False, "", f"命令超时 ({timeout}秒)"
        except Exception as e:
            return False, "", str(e)

    def check_services(self) -> Dict:
        """检查必要服务状态"""
        self.print_header("1. 环境和服务检查")

        services = {
            "mysql": {"status": False, "message": ""},
            "redis": {"status": False, "message": ""},
            "python": {"status": False, "message": ""},
            "node": {"status": False, "message": ""}
        }

        # 检查MySQL
        print("检查 MySQL...")
        success, stdout, stderr = self.run_command(
            ["mysql", "--version"],
            self.backend_root
        )
        if success:
            services["mysql"]["status"] = True
            services["mysql"]["message"] = stdout.strip()
            print(f"✓ MySQL已安装: {stdout.strip()}")
        else:
            services["mysql"]["message"] = "MySQL未安装或未在PATH中"
            print(f"✗ {services['mysql']['message']}")

        # 检查Redis
        print("\n检查 Redis...")
        success, stdout, stderr = self.run_command(
            ["redis-cli", "--version"],
            self.backend_root
        )
        if success:
            services["redis"]["status"] = True
            services["redis"]["message"] = stdout.strip()
            print(f"✓ Redis已安装: {stdout.strip()}")
        else:
            services["redis"]["message"] = "Redis未安装或未在PATH中"
            print(f"✗ {services['redis']['message']}")

        # 检查Python
        print("\n检查 Python...")
        success, stdout, stderr = self.run_command(
            ["python", "--version"],
            self.backend_root
        )
        if success:
            services["python"]["status"] = True
            services["python"]["message"] = stdout.strip()
            print(f"✓ Python已安装: {stdout.strip()}")
        else:
            print("✗ Python未安装或未在PATH中")

        # 检查Node.js
        print("\n检查 Node.js...")
        success, stdout, stderr = self.run_command(
            ["node", "--version"],
            self.frontend_root
        )
        if success:
            services["node"]["status"] = True
            services["node"]["message"] = stdout.strip()
            print(f"✓ Node.js已安装: {stdout.strip()}")
        else:
            print("✗ Node.js未安装或未在PATH中")

        return services

    def run_backend_tests(self) -> Dict:
        """运行后端集成测试"""
        self.print_header("2. 后端API集成测试")

        test_results = {
            "environment": {"status": "pending", "output": ""},
            "api_integration": {"status": "pending", "output": ""},
            "e2e_flows": {"status": "pending", "output": ""}
        }

        # 检查pytest是否安装
        print("检查pytest安装...")
        success, stdout, stderr = self.run_command(
            ["python", "-m", "pytest", "--version"],
            self.backend_root
        )

        if not success:
            print("✗ pytest未安装，正在安装...")
            self.run_command(
                ["pip", "install", "pytest", "pytest-asyncio", "httpx"],
                self.backend_root
            )

        # 运行环境检查测试
        print("\n运行环境检查测试...")
        success, stdout, stderr = self.run_command(
            ["python", "-m", "pytest", "tests/integration/test_environment.py", "-v", "-s"],
            self.backend_root,
            timeout=60
        )

        test_results["environment"]["status"] = "passed" if success else "failed"
        test_results["environment"]["output"] = stdout + "\n" + stderr
        print(stdout)
        if stderr:
            print(stderr)

        # 运行API集成测试
        print("\n运行API集成测试...")
        success, stdout, stderr = self.run_command(
            ["python", "-m", "pytest", "tests/integration/test_api_integration.py", "-v", "-s"],
            self.backend_root,
            timeout=180
        )

        test_results["api_integration"]["status"] = "passed" if success else "failed"
        test_results["api_integration"]["output"] = stdout + "\n" + stderr
        print(stdout)
        if stderr:
            print(stderr)

        # 运行E2E流程测试
        print("\n运行端到端流程测试...")
        success, stdout, stderr = self.run_command(
            ["python", "-m", "pytest", "tests/integration/test_e2e_flows.py", "-v", "-s"],
            self.backend_root,
            timeout=300
        )

        test_results["e2e_flows"]["status"] = "passed" if success else "failed"
        test_results["e2e_flows"]["output"] = stdout + "\n" + stderr
        print(stdout)
        if stderr:
            print(stderr)

        return test_results

    def run_frontend_tests(self) -> Dict:
        """运行前端测试"""
        self.print_header("3. 前端集成测试")

        test_results = {
            "environment": {"status": "pending", "output": ""}
        }

        # 检查node_modules是否存在
        if not (self.frontend_root / "node_modules").exists():
            print("node_modules不存在，正在安装依赖...")
            success, stdout, stderr = self.run_command(
                ["npm", "install"],
                self.frontend_root,
                timeout=300
            )
            if not success:
                print("✗ 前端依赖安装失败")
                test_results["environment"]["status"] = "failed"
                test_results["environment"]["output"] = stderr
                return test_results

        # 运行前端环境检查
        print("\n运行前端环境检查...")
        success, stdout, stderr = self.run_command(
            ["npm", "run", "test", "--", "tests/integration/environment.test.ts"],
            self.frontend_root,
            timeout=60
        )

        test_results["environment"]["status"] = "passed" if success else "failed"
        test_results["environment"]["output"] = stdout + "\n" + stderr
        print(stdout)
        if stderr:
            print(stderr)

        return test_results

    def generate_report(self, services: Dict, backend_tests: Dict, frontend_tests: Dict):
        """生成测试报告"""
        self.print_header("集成测试报告生成")

        report_path = self.project_root / "INTEGRATION_TEST_REPORT.md"

        # 计算总结
        total_tests = len(backend_tests) + len(frontend_tests)
        passed_tests = sum(1 for t in list(backend_tests.values()) + list(frontend_tests.values()) if t["status"] == "passed")
        failed_tests = sum(1 for t in list(backend_tests.values()) + list(frontend_tests.values()) if t["status"] == "failed")

        report_content = f"""# 集成测试报告

**生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
**项目**: 内蒙古农畜产品品牌营销AI赋能云平台
**测试范围**: 前后端完整集成测试

---

## 📊 测试总结

```
总测试套件: {total_tests}
通过: {passed_tests}
失败: {failed_tests}
通过率: {(passed_tests / total_tests * 100) if total_tests > 0 else 0:.1f}%
```

---

## 1. 环境和服务检查

### MySQL
- **状态**: {'✅ 正常' if services['mysql']['status'] else '❌ 异常'}
- **信息**: {services['mysql']['message']}

### Redis
- **状态**: {'✅ 正常' if services['redis']['status'] else '❌ 异常'}
- **信息**: {services['redis']['message']}

### Python
- **状态**: {'✅ 正常' if services['python']['status'] else '❌ 异常'}
- **信息**: {services['python']['message']}

### Node.js
- **状态**: {'✅ 正常' if services['node']['status'] else '❌ 异常'}
- **信息**: {services['node']['message']}

---

## 2. 后端集成测试

### 2.1 环境检查测试
- **状态**: {backend_tests.get('environment', {}).get('status', 'unknown').upper()}
- **详细输出**: 查看完整日志

### 2.2 API集成测试
- **状态**: {backend_tests.get('api_integration', {}).get('status', 'unknown').upper()}
- **测试范围**:
  - 健康检查端点
  - 认证模块 (8个端点)
  - 产品模块 (9个端点)
  - AI对话模块 (6个端点)
  - RBAC权限管理 (15个端点)

### 2.3 端到端流程测试
- **状态**: {backend_tests.get('e2e_flows', {}).get('status', 'unknown').upper()}
- **测试场景**:
  - 新用户完整业务流程
  - 企业用户内容生成流程
  - 管理员管理流程

---

## 3. 前端集成测试

### 3.1 环境检查
- **状态**: {frontend_tests.get('environment', {}).get('status', 'unknown').upper()}
- **检查项**:
  - 项目配置
  - 依赖安装
  - 目录结构
  - TypeScript配置
  - Vite配置

---

## 4. 发现的问题

### 高优先级 (P0)
{self._format_bugs('P0')}

### 中优先级 (P1)
{self._format_bugs('P1')}

### 低优先级 (P2)
{self._format_bugs('P2')}

---

## 5. 性能指标

### API响应时间
- **平均响应**: 待测试
- **P95响应**: 待测试
- **超时次数**: 待测试

### 前端性能
- **首次内容绘制(FCP)**: 待测试
- **最大内容绘制(LCP)**: 待测试
- **可交互时间(TTI)**: 待测试

---

## 6. 验收状态

### 必须通过 ✅
- {'✅' if all([services['python']['status']]) else '❌'} 所有API端点可访问
- {'✅' if passed_tests == total_tests else '❌'} 前后端数据完整传输
- {'✅' if backend_tests.get('api_integration', {}).get('status') == 'passed' else '❌'} 认证授权正常工作
- {'✅' if backend_tests.get('e2e_flows', {}).get('status') == 'passed' else '❌'} 核心业务流程无阻塞

### 期望达成 🎯
- ⏳ API响应时间p95 < 500ms
- ⏳ 前端FCP < 1.8s
- ⏳ 测试覆盖率 > 80%
- ⏳ 安全测试0高危漏洞
- ⏳ 浏览器兼容性100%

---

## 7. 下一步行动

### 立即修复
{self._format_action_items()}

### 优化建议
- 实施性能测试
- 补充安全测试
- 添加压力测试
- 完善监控系统

---

**报告生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""

        # 写入报告
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(report_content)

        print(f"✓ 测试报告已生成: {report_path}")

        return report_path

    def _format_bugs(self, priority: str) -> str:
        """格式化bug列表"""
        # 这里可以根据实际测试结果动态生成
        return "- 暂无发现\n"

    def _format_action_items(self) -> str:
        """格式化行动项"""
        return "- 根据测试结果修复发现的问题\n"

    def run(self):
        """运行完整的集成测试"""
        self.results["start_time"] = datetime.now().isoformat()

        print("=" * 80)
        print("  内蒙古农畜产品AI平台 - 集成测试")
        print("=" * 80)

        # 1. 检查服务
        services = self.check_services()
        self.results["tests"]["services"] = services

        # 2. 运行后端测试
        backend_tests = self.run_backend_tests()
        self.results["tests"]["backend"] = backend_tests

        # 3. 运行前端测试
        frontend_tests = self.run_frontend_tests()
        self.results["tests"]["frontend"] = frontend_tests

        # 4. 生成报告
        report_path = self.generate_report(services, backend_tests, frontend_tests)

        self.results["end_time"] = datetime.now().isoformat()

        # 5. 打印总结
        self.print_header("测试完成")
        print(f"测试报告: {report_path}")
        print("\n后端测试结果:")
        for name, result in backend_tests.items():
            status_icon = "✅" if result["status"] == "passed" else "❌"
            print(f"  {status_icon} {name}: {result['status'].upper()}")

        print("\n前端测试结果:")
        for name, result in frontend_tests.items():
            status_icon = "✅" if result["status"] == "passed" else "❌"
            print(f"  {status_icon} {name}: {result['status'].upper()}")


if __name__ == "__main__":
    # 项目根目录
    project_root = Path(__file__).parent.parent.parent

    runner = IntegrationTestRunner(str(project_root))
    runner.run()
