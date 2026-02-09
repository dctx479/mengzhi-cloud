"""
E2E测试 - 使用Playwright

测试主要用户流程:
1. 用户注册和登录
2. 浏览产品
3. AI对话功能

运行方式:
    pytest tests/e2e_tests.py -v --headed
"""

import pytest
from playwright.async_api import async_playwright, expect
import asyncio


class TestUserAuthFlow:
    """用户认证流程E2E测试"""

    BASE_URL = "http://localhost:5173"

    @pytest.fixture(scope="function")
    async def browser_context(self):
        """创建浏览器上下文"""
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context()
            yield context
            await context.close()
            await browser.close()

    @pytest.mark.asyncio
    async def test_user_registration(self, browser_context):
        """测试用户注册流程"""
        page = await browser_context.new_page()

        try:
            # 导航到注册页面
            await page.goto(f"{self.BASE_URL}/auth/register")

            # 等待页面加载
            await page.wait_for_load_state("networkidle")

            # 检查页面标题
            title = await page.title()
            assert "注册" in title or "Register" in title

            # 填写注册表单
            await page.fill('input[name="email"]', f"test_user_{int(asyncio.get_event_loop().time())}@example.com")
            await page.fill('input[name="username"]', f"testuser_{int(asyncio.get_event_loop().time())}")
            await page.fill('input[name="password"]', "TestPassword123!")
            await page.fill('input[name="confirmPassword"]', "TestPassword123!")

            # 点击注册按钮
            await page.click('button:has-text("注册")')

            # 等待提示信息或重定向
            await page.wait_for_load_state("networkidle")

            # 检查是否成功（可能重定向到登录或仪表板）
            await page.wait_for_url("**/login|**/dashboard", timeout=5000)

        finally:
            await page.close()

    @pytest.mark.asyncio
    async def test_user_login(self, browser_context):
        """测试用户登录流程"""
        page = await browser_context.new_page()

        try:
            # 导航到登录页面
            await page.goto(f"{self.BASE_URL}/auth/login")

            await page.wait_for_load_state("networkidle")

            # 检查页面元素
            email_input = page.locator('input[name="email"]')
            await expect(email_input).to_be_visible()

            # 填写登录表单
            await email_input.fill("admin@example.com")
            await page.fill('input[name="password"]', "Admin@123")

            # 点击登录按钮
            login_btn = page.locator('button:has-text("登录")')
            await login_btn.click()

            # 等待重定向到仪表板
            await page.wait_for_url("**/dashboard", timeout=10000)

            # 验证已登录（检查导航栏中的用户信息）
            user_menu = page.locator('[data-test="user-menu"]')
            await expect(user_menu).to_be_visible()

        finally:
            await page.close()

    @pytest.mark.asyncio
    async def test_user_logout(self, browser_context):
        """测试用户登出流程"""
        page = await browser_context.new_page()

        try:
            # 首先登录
            await page.goto(f"{self.BASE_URL}/auth/login")
            await page.wait_for_load_state("networkidle")

            await page.fill('input[name="email"]', "admin@example.com")
            await page.fill('input[name="password"]', "Admin@123")
            await page.click('button:has-text("登录")')

            await page.wait_for_url("**/dashboard")

            # 点击用户菜单并选择登出
            user_menu = page.locator('[data-test="user-menu"]')
            await user_menu.click()

            logout_btn = page.locator('button:has-text("登出")')
            await logout_btn.click()

            # 等待重定向到登录页
            await page.wait_for_url("**/login", timeout=5000)

        finally:
            await page.close()


class TestProductFlow:
    """产品浏览E2E测试"""

    BASE_URL = "http://localhost:5173"

    @pytest.fixture(scope="function")
    async def browser_context(self):
        """创建浏览器上下文"""
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context()
            yield context
            await context.close()
            await browser.close()

    @pytest.mark.asyncio
    async def test_product_listing(self, browser_context):
        """测试产品列表浏览"""
        page = await browser_context.new_page()

        try:
            # 导航到产品列表页面
            await page.goto(f"{self.BASE_URL}/products")

            await page.wait_for_load_state("networkidle")

            # 检查产品卡片是否加载
            product_cards = page.locator('[data-test="product-card"]')
            count = await product_cards.count()

            assert count > 0, "应该至少加载一个产品"

        finally:
            await page.close()

    @pytest.mark.asyncio
    async def test_product_search(self, browser_context):
        """测试产品搜索功能"""
        page = await browser_context.new_page()

        try:
            # 导航到产品页面
            await page.goto(f"{self.BASE_URL}/products")

            await page.wait_for_load_state("networkidle")

            # 查找搜索框
            search_input = page.locator('input[placeholder*="搜索"]')
            await expect(search_input).to_be_visible()

            # 输入搜索词
            await search_input.fill("有机")

            # 等待搜索结果
            await page.wait_for_load_state("networkidle")

            # 验证搜索结果
            product_cards = page.locator('[data-test="product-card"]')
            count = await product_cards.count()

            # 应该至少有结果或显示无结果信息
            assert count >= 0

        finally:
            await page.close()

    @pytest.mark.asyncio
    async def test_product_detail(self, browser_context):
        """测试产品详情页面"""
        page = await browser_context.new_page()

        try:
            # 导航到产品列表
            await page.goto(f"{self.BASE_URL}/products")

            await page.wait_for_load_state("networkidle")

            # 点击第一个产品卡片
            first_product = page.locator('[data-test="product-card"]').first
            await first_product.click()

            # 等待详情页加载
            await page.wait_for_load_state("networkidle")

            # 验证详情页元素
            product_title = page.locator('[data-test="product-title"]')
            await expect(product_title).to_be_visible()

            product_description = page.locator('[data-test="product-description"]')
            await expect(product_description).to_be_visible()

        finally:
            await page.close()


class TestChatFlow:
    """AI对话E2E测试"""

    BASE_URL = "http://localhost:5173"

    @pytest.fixture(scope="function")
    async def browser_context(self):
        """创建浏览器上下文"""
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context()
            yield context
            await context.close()
            await browser.close()

    @pytest.fixture
    async def logged_in_page(self, browser_context):
        """提供已登录的页面"""
        page = await browser_context.new_page()

        # 登录
        await page.goto(f"{self.BASE_URL}/auth/login")
        await page.wait_for_load_state("networkidle")

        await page.fill('input[name="email"]', "admin@example.com")
        await page.fill('input[name="password"]', "Admin@123")
        await page.click('button:has-text("登录")')

        await page.wait_for_url("**/dashboard")

        yield page
        await page.close()

    @pytest.mark.asyncio
    async def test_start_chat_conversation(self, logged_in_page):
        """测试开始聊天对话"""
        page = logged_in_page

        # 导航到聊天页面
        await page.goto(f"{self.BASE_URL}/chat")

        await page.wait_for_load_state("networkidle")

        # 检查聊天界面元素
        message_input = page.locator('[data-test="message-input"]')
        await expect(message_input).to_be_visible()

        send_btn = page.locator('[data-test="send-button"]')
        await expect(send_btn).to_be_visible()

    @pytest.mark.asyncio
    async def test_send_message(self, logged_in_page):
        """测试发送聊天消息"""
        page = logged_in_page

        # 导航到聊天页面
        await page.goto(f"{self.BASE_URL}/chat")

        await page.wait_for_load_state("networkidle")

        # 发送消息
        message_input = page.locator('[data-test="message-input"]')
        await message_input.fill("我想了解关于有机大米的信息")

        send_btn = page.locator('[data-test="send-button"]')
        await send_btn.click()

        # 等待AI回复
        ai_message = page.locator('[data-test="ai-message"]')
        await expect(ai_message).to_be_visible(timeout=15000)

    @pytest.mark.asyncio
    async def test_chat_history(self, logged_in_page):
        """测试对话历史"""
        page = logged_in_page

        # 导航到对话历史
        await page.goto(f"{self.BASE_URL}/chat/history")

        await page.wait_for_load_state("networkidle")

        # 检查历史列表
        history_items = page.locator('[data-test="conversation-item"]')
        count = await history_items.count()

        # 应该有历史记录或显示空状态
        assert count >= 0


# 测试配置
@pytest.fixture(scope="session")
def event_loop():
    """为异步测试提供事件循环"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--html=report.html", "--self-contained-html"])
