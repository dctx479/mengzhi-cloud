
"""
完整业务流程自动化测试
"""
import pytest
import httpx
import time
from datetime import datetime

BASE_URL = "http://localhost:8000"
TIMEOUT = 30.0

class TestCompleteBusinessFlow:
    @pytest.mark.asyncio
    async def test_complete_flow(self):
        print("\n" + "="*80)
        print("完整业务流程测试")
        print("="*80)

        async with httpx.AsyncClient(base_url=BASE_URL, timeout=TIMEOUT) as client:
            timestamp = int(time.time())

            # 测试1: 用户注册
            print("\n[测试1] 用户注册和登录")
            user = {
                "username": f"test_{timestamp}",
                "email": f"test_{timestamp}@test.com",
                "password": "Test123456",
                "user_type": "personal"
            }
            
            response = await client.post("/api/v1/auth/register", json=user)
            print(f"注册状态: {response.status_code}")
            
            if response.status_code in [200, 201]:
                print("✓ 用户注册成功")
            else:
                print(f"✗ 用户注册失败: {response.text}")
            
            # 测试2: 用户登录
            response = await client.post("/api/v1/auth/login", json={
                "username": user["username"],
                "password": user["password"]
            })
            
            if response.status_code == 200:
                token = response.json()["data"]["tokens"]["access_token"]
                print("✓ 用户登录成功")
                headers = {"Authorization": f"Bearer {token}"}
                
                # 测试3: 获取用户信息
                response = await client.get("/api/v1/auth/me", headers=headers)
                if response.status_code == 200:
                    print("✓ 获取用户信息成功")

                print("\n✅ 所有测试完成")
            else:
                print(f"✗ 用户登录失败: {response.text}")

if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
