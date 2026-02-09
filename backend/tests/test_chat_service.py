"""
聊天服务单元测试

测试内容:
- 发送消息(非流式/流式)
- 对话管理(创建/获取/删除/更新)
- 消息历史构建
- 配额检查和扣减
- 反馈功能

运行: pytest tests/test_chat_service.py -v --cov=app/services/chat_service
"""

import pytest
from unittest.mock import Mock, patch, MagicMock, AsyncMock
from datetime import date
from typing import AsyncGenerator

from sqlalchemy.orm import Session

from app.services.chat_service import ChatService
from app.models.conversation import Conversation, ConversationStatus, AgentType
from app.models.message import Message, MessageRole
from app.models.user_quota import UserQuota, QuotaType
from app.core.errors import BusinessException


# ==================== Fixtures ====================

@pytest.fixture
def chat_service(test_db_session):
    """创建聊天服务实例"""
    return ChatService(test_db_session)


@pytest.fixture
def mock_quota():
    """Mock配额对象"""
    quota = MagicMock(spec=UserQuota)
    quota.can_chat.return_value = True
    quota.increment_chat_usage.return_value = None
    quota.increment_token_usage.return_value = None
    return quota


@pytest.fixture
def mock_conversation():
    """Mock对话对象"""
    conv = MagicMock(spec=Conversation)
    conv.id = 1
    conv.user_id = 123
    conv.title = "测试对话"
    conv.agent_type = AgentType.GENERAL
    conv.model = "deepseek-chat"
    conv.max_tokens = 4096
    conv.message_count = 0
    conv.total_tokens = 0
    conv.total_cost = 0.0
    conv.status = ConversationStatus.ACTIVE
    conv.to_dict.return_value = {
        "id": 1,
        "title": "测试对话",
        "agent_type": "general"
    }
    return conv


@pytest.fixture
def mock_deepseek_response():
    """Mock DeepSeek响应"""
    return {
        "choices": [
            {
                "message": {
                    "content": "这是AI的回复"
                },
                "finish_reason": "stop"
            }
        ],
        "usage": {
            "prompt_tokens": 10,
            "completion_tokens": 20,
            "total_tokens": 30
        }
    }


@pytest.fixture
def mock_deepseek_client(mock_deepseek_response):
    """Mock DeepSeek客户端"""
    client = AsyncMock()
    client.chat_completion.return_value = mock_deepseek_response
    client.calculate_cost.return_value = 0.001
    return client


# ==================== 发送消息测试(非流式) ====================

class TestSendMessage:
    """发送消息功能测试(非流式)"""

    @pytest.mark.asyncio
    async def test_send_message_success(
        self,
        chat_service,
        test_db_session,
        mock_quota,
        mock_conversation,
        mock_deepseek_client
    ):
        """测试成功发送消息"""
        user_id = "123"
        content = "你好"

        with patch.object(chat_service, '_get_or_create_quota', return_value=mock_quota):
            with patch.object(chat_service, '_get_or_create_conversation', return_value=mock_conversation):
                with patch.object(chat_service, '_build_message_history', return_value=[]):
                    with patch('app.services.chat_service.get_deepseek_client', return_value=mock_deepseek_client):
                        with patch.object(test_db_session, 'add'):
                            with patch.object(test_db_session, 'commit'):
                                conv_id, reply, input_tokens, output_tokens, cost = await chat_service.send_message(
                                    user_id=user_id,
                                    content=content
                                )

        assert conv_id == 1
        assert reply == "这是AI的回复"
        assert input_tokens == 10
        assert output_tokens == 20
        assert cost == 0.001

    @pytest.mark.asyncio
    async def test_send_message_quota_exhausted(
        self,
        chat_service,
        mock_quota
    ):
        """测试配额用尽"""
        mock_quota.can_chat.return_value = False

        with patch.object(chat_service, '_get_or_create_quota', return_value=mock_quota):
            with pytest.raises(BusinessException) as exc_info:
                await chat_service.send_message(
                    user_id="123",
                    content="你好"
                )
            assert "对话次数已用完" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_send_message_with_conversation_id(
        self,
        chat_service,
        test_db_session,
        mock_quota,
        mock_conversation,
        mock_deepseek_client
    ):
        """测试指定对话ID发送消息"""
        user_id = "123"
        conversation_id = 1
        content = "继续对话"

        with patch.object(chat_service, '_get_or_create_quota', return_value=mock_quota):
            with patch.object(chat_service, '_get_or_create_conversation', return_value=mock_conversation):
                with patch.object(chat_service, '_build_message_history', return_value=[
                    {"role": "user", "content": "你好"},
                    {"role": "assistant", "content": "你好！"}
                ]):
                    with patch('app.services.chat_service.get_deepseek_client', return_value=mock_deepseek_client):
                        with patch.object(test_db_session, 'add'):
                            with patch.object(test_db_session, 'commit'):
                                conv_id, reply, _, _, _ = await chat_service.send_message(
                                    user_id=user_id,
                                    content=content,
                                    conversation_id=conversation_id
                                )

        assert conv_id == conversation_id

    @pytest.mark.asyncio
    async def test_send_message_with_temperature(
        self,
        chat_service,
        test_db_session,
        mock_quota,
        mock_conversation,
        mock_deepseek_client
    ):
        """测试自定义temperature"""
        temperature = 0.9

        with patch.object(chat_service, '_get_or_create_quota', return_value=mock_quota):
            with patch.object(chat_service, '_get_or_create_conversation', return_value=mock_conversation):
                with patch.object(chat_service, '_build_message_history', return_value=[]):
                    with patch('app.services.chat_service.get_deepseek_client', return_value=mock_deepseek_client):
                        with patch.object(test_db_session, 'add'):
                            with patch.object(test_db_session, 'commit'):
                                await chat_service.send_message(
                                    user_id="123",
                                    content="你好",
                                    temperature=temperature
                                )

        # 验证temperature参数被传递
        mock_deepseek_client.chat_completion.assert_called_once()
        call_args = mock_deepseek_client.chat_completion.call_args
        assert call_args[1]['temperature'] == temperature


# ==================== 发送消息测试(流式) ====================

class TestSendMessageStream:
    """发送消息功能测试(流式)"""

    @pytest.mark.asyncio
    async def test_send_message_stream_success(
        self,
        chat_service,
        test_db_session,
        mock_quota,
        mock_conversation
    ):
        """测试流式发送消息"""
        user_id = "123"
        content = "你好"

        # Mock流式响应
        async def mock_stream():
            yield {
                "choices": [
                    {
                        "delta": {"content": "这是"}
                    }
                ]
            }
            yield {
                "choices": [
                    {
                        "delta": {"content": "AI"},
                        "finish_reason": "stop"
                    }
                ],
                "usage": {
                    "prompt_tokens": 10,
                    "completion_tokens": 20,
                    "total_tokens": 30
                }
            }

        mock_client = AsyncMock()
        mock_client.chat_completion_stream.return_value = mock_stream()
        mock_client.calculate_cost.return_value = 0.001

        with patch.object(chat_service, '_get_or_create_quota', return_value=mock_quota):
            with patch.object(chat_service, '_get_or_create_conversation', return_value=mock_conversation):
                with patch.object(chat_service, '_build_message_history', return_value=[]):
                    with patch('app.services.chat_service.get_deepseek_client', return_value=mock_client):
                        with patch.object(test_db_session, 'add'):
                            with patch.object(test_db_session, 'commit'):
                                chunks = []
                                async for chunk in chat_service.send_message_stream(
                                    user_id=user_id,
                                    content=content
                                ):
                                    chunks.append(chunk)

        assert chunks == ["这是", "AI"]

    @pytest.mark.asyncio
    async def test_send_message_stream_quota_exhausted(
        self,
        chat_service,
        mock_quota
    ):
        """测试流式消息配额用尽"""
        mock_quota.can_chat.return_value = False

        with patch.object(chat_service, '_get_or_create_quota', return_value=mock_quota):
            with pytest.raises(BusinessException) as exc_info:
                async for _ in chat_service.send_message_stream(
                    user_id="123",
                    content="你好"
                ):
                    pass
            assert "对话次数已用完" in str(exc_info.value)


# ==================== 对话列表测试 ====================

class TestGetConversations:
    """获取对话列表功能测试"""

    @pytest.mark.unit
    def test_get_conversations_default(self, chat_service, test_db_session):
        """测试获取对话列表(默认参数)"""
        user_id = "123"

        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.count.return_value = 2
        mock_query.order_by.return_value = mock_query
        mock_query.offset.return_value = mock_query
        mock_query.limit.return_value = mock_query

        mock_conv1 = MagicMock()
        mock_conv1.to_dict.return_value = {"id": 1, "title": "对话1"}
        mock_conv2 = MagicMock()
        mock_conv2.to_dict.return_value = {"id": 2, "title": "对话2"}

        mock_query.all.return_value = [mock_conv1, mock_conv2]

        with patch.object(test_db_session, 'query', return_value=mock_query):
            total, conversations = chat_service.get_conversations(user_id=user_id)

        assert total == 2
        assert len(conversations) == 2
        assert conversations[0]["id"] == 1

    @pytest.mark.unit
    def test_get_conversations_with_status_filter(self, chat_service, test_db_session):
        """测试按状态筛选对话列表"""
        user_id = "123"
        status = "archived"

        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.count.return_value = 1
        mock_query.order_by.return_value = mock_query
        mock_query.offset.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = []

        with patch.object(test_db_session, 'query', return_value=mock_query):
            total, _ = chat_service.get_conversations(
                user_id=user_id,
                status=status
            )

        assert total == 1

    @pytest.mark.unit
    def test_get_conversations_pagination(self, chat_service, test_db_session):
        """测试对话列表分页"""
        user_id = "123"
        page = 2
        page_size = 5

        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.count.return_value = 15
        mock_query.order_by.return_value = mock_query
        mock_query.offset.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = []

        with patch.object(test_db_session, 'query', return_value=mock_query):
            total, _ = chat_service.get_conversations(
                user_id=user_id,
                page=page,
                page_size=page_size
            )

        # 验证offset和limit
        mock_query.offset.assert_called_once_with(5)  # (page-1) * page_size
        mock_query.limit.assert_called_once_with(5)


# ==================== 对话详情测试 ====================

class TestGetConversationDetail:
    """获取对话详情功能测试"""

    @pytest.mark.unit
    def test_get_conversation_detail_success(self, chat_service, test_db_session):
        """测试成功获取对话详情"""
        conversation_id = "conv-uuid-123"
        user_id = "123"

        mock_conv = MagicMock()
        mock_conv.to_dict.return_value = {"id": 1, "title": "对话1"}
        mock_msg = MagicMock()
        mock_msg.to_dict.return_value = {"id": 1, "content": "消息1"}
        mock_conv.messages = [mock_msg]

        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = mock_conv

        with patch.object(test_db_session, 'query', return_value=mock_query):
            detail = chat_service.get_conversation_detail(
                conversation_id=conversation_id,
                user_id=user_id
            )

        assert detail["id"] == 1
        assert "messages" in detail
        assert len(detail["messages"]) == 1

    @pytest.mark.unit
    def test_get_conversation_detail_not_found(self, chat_service, test_db_session):
        """测试对话不存在"""
        conversation_id = "nonexistent"
        user_id = "123"

        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = None

        with patch.object(test_db_session, 'query', return_value=mock_query):
            with pytest.raises(BusinessException) as exc_info:
                chat_service.get_conversation_detail(
                    conversation_id=conversation_id,
                    user_id=user_id
                )
            assert "对话不存在" in str(exc_info.value)


# ==================== 删除对话测试 ====================

class TestDeleteConversation:
    """删除对话功能测试"""

    @pytest.mark.unit
    def test_delete_conversation_success(self, chat_service, test_db_session):
        """测试成功删除对话"""
        conversation_id = "conv-uuid-123"
        user_id = "123"

        mock_conv = MagicMock()
        mock_conv.soft_delete = MagicMock()

        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = mock_conv

        with patch.object(test_db_session, 'query', return_value=mock_query):
            with patch.object(test_db_session, 'commit'):
                chat_service.delete_conversation(
                    conversation_id=conversation_id,
                    user_id=user_id
                )

        mock_conv.soft_delete.assert_called_once()

    @pytest.mark.unit
    def test_delete_conversation_not_found(self, chat_service, test_db_session):
        """测试删除不存在的对话"""
        conversation_id = "nonexistent"
        user_id = "123"

        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = None

        with patch.object(test_db_session, 'query', return_value=mock_query):
            with pytest.raises(BusinessException) as exc_info:
                chat_service.delete_conversation(
                    conversation_id=conversation_id,
                    user_id=user_id
                )
            assert "对话不存在" in str(exc_info.value)


# ==================== 更新对话测试 ====================

class TestUpdateConversation:
    """更新对话功能测试"""

    @pytest.mark.unit
    def test_update_conversation_title(self, chat_service, test_db_session):
        """测试更新对话标题"""
        conversation_id = "conv-uuid-123"
        user_id = "123"
        new_title = "新标题"

        mock_conv = MagicMock()
        mock_conv.title = "旧标题"
        mock_conv.to_dict.return_value = {"id": 1, "title": new_title}

        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = mock_conv

        with patch.object(test_db_session, 'query', return_value=mock_query):
            with patch.object(test_db_session, 'commit'):
                result = chat_service.update_conversation(
                    conversation_id=conversation_id,
                    user_id=user_id,
                    title=new_title
                )

        assert mock_conv.title == new_title
        assert result["title"] == new_title

    @pytest.mark.unit
    def test_update_conversation_favorite(self, chat_service, test_db_session):
        """测试设置对话为收藏"""
        conversation_id = "conv-uuid-123"
        user_id = "123"

        mock_conv = MagicMock()
        mock_conv.metadata_info = {}
        mock_conv.to_dict.return_value = {"id": 1}

        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = mock_conv

        with patch.object(test_db_session, 'query', return_value=mock_query):
            with patch.object(test_db_session, 'commit'):
                chat_service.update_conversation(
                    conversation_id=conversation_id,
                    user_id=user_id,
                    is_favorited=True
                )

        assert mock_conv.metadata_info["is_favorited"] is True

    @pytest.mark.unit
    def test_update_conversation_not_found(self, chat_service, test_db_session):
        """测试更新不存在的对话"""
        conversation_id = "nonexistent"
        user_id = "123"

        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = None

        with patch.object(test_db_session, 'query', return_value=mock_query):
            with pytest.raises(BusinessException) as exc_info:
                chat_service.update_conversation(
                    conversation_id=conversation_id,
                    user_id=user_id,
                    title="新标题"
                )
            assert "对话不存在" in str(exc_info.value)


# ==================== 反馈功能测试 ====================

class TestAddFeedback:
    """添加反馈功能测试"""

    @pytest.mark.unit
    def test_add_feedback_helpful(self, chat_service, test_db_session):
        """测试添加正面反馈"""
        message_id = 1
        conversation_id = 1
        user_id = "123"
        rating = 5
        feedback = "很有帮助"

        mock_msg = MagicMock()
        mock_msg.to_dict.return_value = {"id": 1, "rating": 5}

        mock_query = MagicMock()
        mock_query.join.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = mock_msg

        with patch.object(test_db_session, 'query', return_value=mock_query):
            with patch.object(test_db_session, 'commit'):
                result = chat_service.add_feedback(
                    message_id=message_id,
                    conversation_id=conversation_id,
                    user_id=user_id,
                    rating=rating,
                    feedback=feedback
                )

        assert mock_msg.rating == rating
        assert mock_msg.feedback == feedback
        assert mock_msg.feedback_type == "helpful"

    @pytest.mark.unit
    def test_add_feedback_unhelpful(self, chat_service, test_db_session):
        """测试添加负面反馈"""
        message_id = 1
        conversation_id = 1
        user_id = "123"
        rating = 1

        mock_msg = MagicMock()
        mock_msg.to_dict.return_value = {"id": 1, "rating": 1}

        mock_query = MagicMock()
        mock_query.join.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = mock_msg

        with patch.object(test_db_session, 'query', return_value=mock_query):
            with patch.object(test_db_session, 'commit'):
                chat_service.add_feedback(
                    message_id=message_id,
                    conversation_id=conversation_id,
                    user_id=user_id,
                    rating=rating
                )

        assert mock_msg.feedback_type == "unhelpful"

    @pytest.mark.unit
    def test_add_feedback_message_not_found(self, chat_service, test_db_session):
        """测试消息不存在"""
        message_id = 999
        conversation_id = 1
        user_id = "123"

        mock_query = MagicMock()
        mock_query.join.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = None

        with patch.object(test_db_session, 'query', return_value=mock_query):
            with pytest.raises(BusinessException) as exc_info:
                chat_service.add_feedback(
                    message_id=message_id,
                    conversation_id=conversation_id,
                    user_id=user_id,
                    rating=5
                )
            assert "消息不存在" in str(exc_info.value)


# ==================== 内部方法测试 ====================

class TestInternalMethods:
    """内部方法功能测试"""

    @pytest.mark.unit
    def test_get_or_create_quota_existing(self, chat_service, test_db_session):
        """测试获取已存在的配额"""
        user_id = 123
        today = date.today()

        mock_quota = MagicMock(spec=UserQuota)
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = mock_quota

        with patch.object(test_db_session, 'query', return_value=mock_query):
            quota = chat_service._get_or_create_quota(user_id)

        assert quota == mock_quota

    @pytest.mark.unit
    def test_get_or_create_quota_create_new(self, chat_service, test_db_session):
        """测试创建新配额"""
        user_id = 123
        today = date.today()

        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = None

        with patch.object(test_db_session, 'query', return_value=mock_query):
            with patch.object(test_db_session, 'add'):
                with patch.object(test_db_session, 'commit'):
                    with patch('app.services.chat_service.UserQuota.create_daily_quota') as mock_create:
                        mock_quota = MagicMock()
                        mock_create.return_value = mock_quota
                        quota = chat_service._get_or_create_quota(user_id)

        mock_create.assert_called_once_with(user_id, today)

    @pytest.mark.unit
    def test_get_or_create_conversation_existing(self, chat_service, test_db_session):
        """测试获取已存在的对话"""
        user_id = 123
        conversation_id = 1

        mock_conv = MagicMock()
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = mock_conv

        with patch.object(test_db_session, 'query', return_value=mock_query):
            conv = chat_service._get_or_create_conversation(user_id, conversation_id)

        assert conv == mock_conv

    @pytest.mark.unit
    def test_get_or_create_conversation_not_found(self, chat_service, test_db_session):
        """测试对话不存在"""
        user_id = 123
        conversation_id = 999

        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = None

        with patch.object(test_db_session, 'query', return_value=mock_query):
            with pytest.raises(BusinessException) as exc_info:
                chat_service._get_or_create_conversation(user_id, conversation_id)
            assert "对话不存在" in str(exc_info.value)

    @pytest.mark.unit
    def test_get_or_create_conversation_create_new(self, chat_service, test_db_session):
        """测试创建新对话"""
        user_id = 123

        with patch.object(test_db_session, 'add'):
            with patch.object(test_db_session, 'commit'):
                conv = chat_service._get_or_create_conversation(user_id, None)

        assert conv.user_id == user_id
        assert conv.title == "新对话"

    @pytest.mark.unit
    def test_build_message_history(self, chat_service, test_db_session):
        """测试构建消息历史"""
        conversation_id = 1

        mock_msg1 = MagicMock()
        mock_msg1.role = MessageRole.USER
        mock_msg1.content = "你好"

        mock_msg2 = MagicMock()
        mock_msg2.role = MessageRole.ASSISTANT
        mock_msg2.content = "你好！"

        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.all.return_value = [mock_msg1, mock_msg2]

        with patch.object(test_db_session, 'query', return_value=mock_query):
            history = chat_service._build_message_history(conversation_id)

        assert len(history) == 2
        assert history[0]["role"] == "user"
        assert history[0]["content"] == "你好"
        assert history[1]["role"] == "assistant"

    @pytest.mark.unit
    def test_get_system_prompt_marketing(self, chat_service):
        """测试获取营销专家提示词"""
        prompt = chat_service._get_system_prompt(AgentType.MARKETING)
        assert "营销" in prompt

    @pytest.mark.unit
    def test_get_system_prompt_cultural(self, chat_service):
        """测试获取文化专家提示词"""
        prompt = chat_service._get_system_prompt(AgentType.CULTURAL)
        assert "文化" in prompt

    @pytest.mark.unit
    def test_get_system_prompt_data(self, chat_service):
        """测试获取数据分析提示词"""
        prompt = chat_service._get_system_prompt(AgentType.DATA)
        assert "数据" in prompt

    @pytest.mark.unit
    def test_get_system_prompt_general(self, chat_service):
        """测试获取通用助手提示词"""
        prompt = chat_service._get_system_prompt(AgentType.GENERAL)
        assert "助手" in prompt


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
