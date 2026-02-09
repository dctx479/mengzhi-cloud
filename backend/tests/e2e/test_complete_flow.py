"""完整业务流程自动化测试"""
import pytest
import httpx
import time
from datetime import datetime

BASE_URL = "http://localhost:8000"
TIMEOUT = 30.0

test_results = {"tests": [], "summary": {"total": 0, "passed": 0, "failed": 0}}

def log_result(name, status, msg=""):
    test_results["tests"].append({"name": name, "status": status, "message": msg, "time": datetime.now().isoformat()})
    test_results["summary"]["total"] += 1
    if status == "PASSED":
        test_results["summary"]["passed"] += 1
    else:
        test_results["summary"]["failed"] += 1

class TestBusinessFlow:
    @pytest.mark.asyncio
    async def test_01_registration_login(self):
        print("\n" + "="*80)
        print("测试1: 用户注册和登录")
        print("="*80)
        
        async with httpx.AsyncClient(base_url=BASE_URL, timeout=TIMEOUT) as client:
            ts = int(time.time())
            user = {"username": f"test_{ts}", "email": f"test_{ts}@test.com", "phone": f"138{ts%100000000:08d}", "password": "Test123456", "user_type": "personal"}
            
            try:
                r = await client.post("/api/v1/auth/register", json=user)
                if r.status_code in [200, 201]:
                    print(f"✓ 注册成功: {user['username']}")
                    log_result("用户注册", "PASSED", f"用户: {user['username']}")
                else:
                    print(f"✗ 注册失败: {r.status_code}")
                    log_result("用户注册", "FAILED", f"状态码: {r.status_code}")
            except Exception as e:
                print(f"✗ 注册异常: {e}")
                log_result("用户注册", "FAILED", str(e))
            
            try:
                r = await client.post("/api/v1/auth/login", json={"username": user["username"], "password": user["password"]})
                if r.status_code == 200:
                    token = r.json()["data"]["tokens"]["access_token"]
                    print("✓ 登录成功")
                    log_result("用户登录", "PASSED")
                    
                    r = await client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
                    if r.status_code == 200:
                        print("✓ 获取用户信息成功")
                        log_result("获取用户信息", "PASSED")
                else:
                    print(f"✗ 登录失败: {r.status_code}")
                    log_result("用户登录", "FAILED", f"状态码: {r.status_code}")
            except Exception as e:
                print(f"✗ 登录异常: {e}")
                log_result("用户登录", "FAILED", str(e))

    @pytest.mark.asyncio
    async def test_02_enterprise_registration(self):
        print("\n" + "="*80)
        print("测试2: 企业用户注册")
        print("="*80)
        
        async with httpx.AsyncClient(base_url=BASE_URL, timeout=TIMEOUT) as client:
            ts = int(time.time())
            ent = {"username": f"ent_{ts}", "email": f"ent_{ts}@test.com", "password": "Test123456", "user_type": "enterprise", "enterprise_name": f"企业{ts}", "enterprise_license": f"91150100MA{ts%1000000:06d}"}
            
            try:
                r = await client.post("/api/v1/auth/register", json=ent)
                if r.status_code in [200, 201]:
                    print(f"✓ 企业注册成功: {ent['username']}")
                    log_result("企业注册", "PASSED", f"企业: {ent['enterprise_name']}")
                else:
                    print(f"✗ 企业注册失败: {r.status_code}")
                    log_result("企业注册", "FAILED", f"状态码: {r.status_code}")
            except Exception as e:
                print(f"✗ 企业注册异常: {e}")
                log_result("企业注册", "FAILED", str(e))

    @pytest.mark.asyncio
    async def test_03_chat_conversation(self):
        print("\n" + "="*80)
        print("测试3: AI对话功能")
        print("="*80)
        
        async with httpx.AsyncClient(base_url=BASE_URL, timeout=TIMEOUT) as client:
            ts = int(time.time())
            user = {"username": f"chat_{ts}", "email": f"chat_{ts}@test.com", "password": "Test123456", "user_type": "personal"}
            
            try:
                await client.post("/api/v1/auth/register", json=user)
                r = await client.post("/api/v1/auth/login", json={"username": user["username"], "password": user["password"]})
                if r.status_code == 200:
                    token = r.json()["data"]["tokens"]["access_token"]
                    headers = {"Authorization": f"Bearer {token}"}
                    
                    r = await client.post("/api/v1/chat/conversations", json={"title": "测试对话"}, headers=headers)
                    if r.status_code in [200, 201]:
                        print("✓ 创建对话成功")
                        log_result("创建对话", "PASSED")
                    else:
                        print(f"✗ 创建对话失败: {r.status_code}")
                        log_result("创建对话", "FAILED", f"状态码: {r.status_code}")
            except Exception as e:
                print(f"✗ 对话测试异常: {e}")
                log_result("创建对话", "FAILED", str(e))

    @pytest.mark.asyncio
    async def test_04_quota_query(self):
        print("\n" + "="*80)
        print("测试4: 配额查询")
        print("="*80)
        
        async with httpx.AsyncClient(base_url=BASE_URL, timeout=TIMEOUT) as client:
            ts = int(time.time())
            user = {"username": f"quota_{ts}", "email": f"quota_{ts}@test.com", "password": "Test123456", "user_type": "personal"}
            
            try:
                await client.post("/api/v1/auth/register", json=user)
                r = await client.post("/api/v1/auth/login", json={"username": user["username"], "password": user["password"]})
                if r.status_code == 200:
                    token = r.json()["data"]["tokens"]["access_token"]
                    headers = {"Authorization": f"Bearer {token}"}
                    
                    r = await client.get("/api/quotas/", headers=headers)
                    if r.status_code == 200:
                        quotas = r.json()["data"]["items"]
                        print(f"✓ 配额查询成功，共 {len(quotas)} 个")
                        log_result("配额查询", "PASSED", f"配额数: {len(quotas)}")
                    else:
                        print(f"✗ 配额查询失败: {r.status_code}")
                        log_result("配额查询", "FAILED", f"状态码: {r.status_code}")
            except Exception as e:
                print(f"✗ 配额测试异常: {e}")
                log_result("配额查询", "FAILED", str(e))

def generate_report():
    report = f"""# 业务流程自动化测试报告

## 测试概要

- 总测试数: {test_results['summary']['total']}
- 通过: {test_results['summary']['passed']} ✓
- 失败: {test_results['summary']['failed']} ✗
- 通过率: {(test_results['summary']['passed']/test_results['summary']['total']*100) if test_results['summary']['total']>0 else 0:.1f}%

## 测试详情

"""
    for t in test_results['tests']:
        icon = "✓" if t['status'] == "PASSED" else "✗"
        report += f"### {icon} {t['name']}\n- 状态: {t['status']}\n- 时间: {t['time']}\n"
        if t['message']:
            report += f"- 信息: {t['message']}\n"
        report += "\n"
    
    report += f"\n## 结论\n\n{'✅ 所有测试通过' if test_results['summary']['failed']==0 else f'⚠ 存在 {test_results['summary']['failed']} 个失败测试'}\n"
    return report

if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s", "--asyncio-mode=auto"])
    with open("../../TEST_REPORT.md", "w", encoding="utf-8") as f:
        f.write(generate_report())
    print("\n测试报告已生成: TEST_REPORT.md")
