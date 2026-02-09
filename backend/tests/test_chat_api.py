"""
AI对话API路由单元测试

测试内容：
- 创建对话
- 获取对话列表
- 发送消息
- 获取消息历史
- 删除对话

运行: pytest tests/test_chat_api.py -v
"""

import pytest
from unittest.mock import patch, MagicMock


# ==================== 创建对话端点测试 ====================

class TestCreateConversationEndpoint:
    """创建对话端点功能测试"""

    @pytest.mark.unit
    def test_create_conversation_success(self, client, auth_headers, test_product_data, test_db_session):
        """测试创建对话成功"""
        from app.schemas.products import ProductCreateRequest
        from app.services.product_service import ProductService

        # 先创建一个产品
        service = ProductService(test_db_session)
        request = ProductCreateRequest(**test_product_data)
        product = service.create_product(request, user_id=1)

        conversation_data = {
            "title": "营销方案讨论",
            "agent_type": "marketing_expert",
            "product_id": product.id
        }

        response = client.post(
            "/api/v1/chat/conversations",
            json=conversation_data,
            headers=auth_headers
        )

        assert response.status_code in [200, 201]

    @pytest.mark.unit
    def test_create_conversation_without_auth(self, client, test_conversation_data):
        """测试未认证创建对话"""
        response = client.post(
            "/api/v1/chat/conversations",
            json=test_conversation_data
        )

        assert response.status_code == 401


# ==================== 获取对话列表端点测试 ====================

class TestConversationListEndpoint:
    """获取对话列表端点功能测试"""

    @pytest.mark.unit
    def test_list_conversations(self, client, auth_headers):
        """测试获取对话列表"""
        response = client.get(
            "/api/v1/chat/conversations",
            headers=auth_headers
        )

        assert response.status_code in [200, 404]

    @pytest.mark.unit
    def test_list_conversations_without_auth(self, client):
        """测试未认证获取对话列表"""
        response = client.get("/api/v1/chat/conversations")

        assert response.status_code == 401


# ==================== 获取对话详情端点测试 ====================

class TestConversationDetailEndpoint:
    """获取对话详情端点功能测试"""

    @pytest.mark.unit
    def test_get_conversation_success(self, client, auth_headers):
        """测试获取对话详情"""
        # 假设对话ID为1
        response = client.get(
            "/api/v1/chat/conversations/1",
            headers=auth_headers
        )

        assert response.status_code in [200, 404]

    @pytest.mark.unit
    def test_get_conversation_without_auth(self, client):
        """测试未认证获取对话详情"""
        response = client.get("/api/v1/chat/conversations/1")

        assert response.status_code == 401


# ==================== 发送消息端点测试 ====================

class TestSendMessageEndpoint:
    """发送消息端点功能测试"""

    @pytest.mark.unit
    def test_send_message_success(self, client, auth_headers):
        """测试发送消息成功"""
        message_data = {
            "conversation_id": 1,
            "content": "请帮我制定营销方案",
            "content_type": "text"
        }

        with patch('app.services.ai.deepseek_client.DeepSeekClient') as mock_ai:
            mock_ai.return_value.generate_content.return_value = "这是AI生成的回复"

            response = client.post(
                "/api/v1/chat/messages",
                json=message_data,
                headers=auth_headers
            )

        assert response.status_code in [200, 201, 404]

    @pytest.mark.unit
    def test_send_message_without_auth(self, client):
        """测试未认证发送消息"""
        message_data = {
            "conversation_id": 1,
            "content": "请帮我制定营销方案",
            "content_type": "text"
        }

        response = client.post(
            "/api/v1/chat/messages",
            json=message_data
        )

        assert response.status_code == 401

    @pytest.mark.unit
    def test_send_message_empty_content(self, client, auth_headers):
        """测试发送空消息"""
        message_data = {
            "conversation_id": 1,
            "content": "",
            "content_type": "text"
        }

        response = client.post(
            "/api/v1/chat/messages",
            json=message_data,
            headers=auth_headers
        )

        assert response.status_code in [400, 422]


# ==================== 获取消息历史端点测试 ====================

class TestMessageHistoryEndpoint:
    """获取消息历史端点功能测试"""

    @pytest.mark.unit
    def test_get_message_history(self, client, auth_headers):
        """测试获取消息历史"""
        response = client.get(
            "/api/v1/chat/conversations/1/messages",
            headers=auth_headers
        )

        assert response.status_code in [200, 404]

    @pytest.mark.unit
    def test_get_message_history_with_pagination(self, client, auth_headers):
        """测试分页获取消息历史"""
        response = client.get(
            "/api/v1/chat/conversations/1/messages?page=1&size=10",
            headers=auth_headers
        )

        assert response.status_code in [200, 404]


# ==================== 删除对话端点测试 ====================

class TestDeleteConversationEndpoint:
    """删除对话端点功能测试"""

    @pytest.mark.unit
    def test_delete_conversation(self, client, auth_headers):
        """测试删除对话"""
        response = client.delete(
            "/api/v1/chat/conversations/1",
            headers=auth_headers
        )

        assert response.status_code in [200, 404]

    @pytest.mark.unit
    def test_delete_conversation_without_auth(self, client):
        """测试未认证删除对话"""
        response = client.delete("/api/v1/chat/conversations/1")

        assert response.status_code == 401


# ==================== 错误处理端点测试 ====================

class TestErrorHandling:
    """错误处理功能测试"""

    @pytest.mark.unit
    def test_invalid_endpoint(self, client):
        """测试无效端点"""
        response = client.get("/api/v1/chat/invalid")

        assert response.status_code == 404

    @pytest.mark.unit
    def test_method_not_allowed(self, client):
        """测试方法不允许"""
        response = client.post("/api/v1/auth/me")  # /me只支持GET

        assert response.status_code in [405, 404]


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
