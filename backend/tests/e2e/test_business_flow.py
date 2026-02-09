"""完整业务流程自动化测试"""
import pytest
import httpx
import time

BASE_URL = "http://localhost:8000"

class TestBusinessFlow:
    @pytest.mark.asyncio
    async def test_flow(self):
        print("\n业务流程测试")
        async with httpx.AsyncClient(base_url=BASE_URL, timeout=30) as client:
            ts = int(time.time())
            user = {"username": f"test_{ts}", "email": f"test_{ts}@test.com", "password": "Test123456", "user_type": "personal"}
            r = await client.post("/api/v1/auth/register", json=user)
            print(f"注册: {r.status_code}")
            r = await client.post("/api/v1/auth/login", json={"username": user["username"], "password": user["password"]})
            print(f"登录: {r.status_code}")
            if r.status_code == 200:
                token = r.json()["data"]["tokens"]["access_token"]
                r = await client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
                print(f"获取信息: {r.status_code}")
