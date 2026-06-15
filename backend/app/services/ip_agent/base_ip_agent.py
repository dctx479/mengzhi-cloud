"""
IP智能体基类

定义所有IP Agent的通用接口和行为
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, AsyncGenerator, Any
from sqlalchemy.orm import Session
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class BaseIPAgent(ABC):
    """IP智能体基类"""

    def __init__(self, db: Session, llm_client: Any):
        """
        初始化IP Agent

        Args:
            db: 数据库会话
            llm_client: LLM客户端 (DeepSeekProvider)
        """
        self.db = db
        self.llm_client = llm_client
        self.ip_name: str = ""  # 子类设置，如"小数"
        self.ip_type: str = ""  # 子类设置，如"xiaoshu"

    async def generate_response(
        self,
        user_message: str,
        conversation_id: Optional[int] = None,
        user_profile: Optional[Dict] = None,
        temperature: float = 0.7,
    ) -> Dict[str, Any]:
        """
        生成非流式响应

        Args:
            user_message: 用户消息
            conversation_id: 对话ID
            user_profile: 用户画像 (可选)
            temperature: 温度参数

        Returns:
            {
                "content": str,  # 响应内容
                "metadata": Dict,  # 元数据 (文化元素、情绪等)
                "tokens": {
                    "input": int,
                    "output": int,
                    "total": int
                },
                "cost": float
            }
        """
        try:
            # 1. 构建对话历史
            conversation_history = []
            if conversation_id:
                conversation_history = self._build_conversation_history(conversation_id)

            # 2. 构建完整Prompt
            messages = self._build_messages(user_message, conversation_history, user_profile)

            # 2.5 注入领域知识上下文（子类可覆盖，如小数注入文化元素）
            messages = self._inject_knowledge_context(user_message, messages)

            # 3. 调用LLM
            logger.info(
                f"[{self.ip_type}] Generating response for message: {user_message[:50]}... "
                f"(conversation_id={conversation_id})"
            )

            response = await self.llm_client.chat_completion(
                messages=messages, system_prompt=self._get_system_prompt(), temperature=temperature
            )

            # 4. 解析响应
            choice = response["choices"][0]
            content = choice["message"]["content"]
            usage = response["usage"]

            # 5. 提取元数据
            metadata = self._extract_metadata(user_message, content)

            result = {
                "content": content,
                "metadata": metadata,
                "tokens": {
                    "input": usage["prompt_tokens"],
                    "output": usage["completion_tokens"],
                    "total": usage["total_tokens"],
                },
                "cost": self.llm_client.calculate_cost(usage["prompt_tokens"], usage["completion_tokens"]),
            }

            logger.info(
                f"[{self.ip_type}] Response generated successfully. "
                f"Tokens: {result['tokens']['total']}, Cost: ${result['cost']:.4f}"
            )

            return result

        except Exception as e:
            logger.error(f"[{self.ip_type}] Failed to generate response: {str(e)}")
            raise

    async def generate_response_stream(
        self,
        user_message: str,
        conversation_id: Optional[int] = None,
        user_profile: Optional[Dict] = None,
        temperature: float = 0.7,
    ) -> AsyncGenerator[str, None]:
        """
        生成流式响应

        Args:
            user_message: 用户消息
            conversation_id: 对话ID
            user_profile: 用户画像
            temperature: 温度参数

        Yields:
            str: 响应文本片段
        """
        try:
            # 1. 构建对话历史
            conversation_history = []
            if conversation_id:
                conversation_history = self._build_conversation_history(conversation_id)

            # 2. 构建完整Prompt
            messages = self._build_messages(user_message, conversation_history, user_profile)

            # 2.5 注入领域知识上下文（子类可覆盖，如小数注入文化元素）
            messages = self._inject_knowledge_context(user_message, messages)

            # 3. 调用LLM流式接口
            logger.info(f"[{self.ip_type}] Starting stream for message: {user_message[:50]}...")

            async for chunk in self.llm_client.chat_completion_stream(
                messages=messages, system_prompt=self._get_system_prompt(), temperature=temperature
            ):
                if "choices" in chunk and len(chunk["choices"]) > 0:
                    delta = chunk["choices"][0].get("delta", {})
                    content_chunk = delta.get("content", "")
                    if content_chunk:
                        yield content_chunk

        except Exception as e:
            logger.error(f"[{self.ip_type}] Stream failed: {str(e)}")
            raise

    def _inject_knowledge_context(self, user_message: str, messages: List[Dict[str, str]]) -> List[Dict[str, str]]:
        """
        注入领域知识上下文（默认不修改；子类可覆盖以实现 RAG 式知识增强）

        Args:
            user_message: 当前用户消息
            messages: 已构建的消息列表

        Returns:
            List[Dict]: 注入知识后的消息列表
        """
        return messages

    @abstractmethod
    def _get_system_prompt(self) -> str:
        """
        获取系统提示词 (子类实现)

        Returns:
            str: 系统提示词
        """
        pass

    @abstractmethod
    def _get_few_shot_examples(self) -> List[Dict[str, str]]:
        """
        获取Few-shot示例 (子类实现)

        Returns:
            List[Dict]: [{"user": "...", "assistant": "..."}, ...]
        """
        pass

    def _build_messages(
        self, user_message: str, conversation_history: List[Dict], user_profile: Optional[Dict] = None
    ) -> List[Dict[str, str]]:
        """
        构建消息列表

        Args:
            user_message: 用户消息
            conversation_history: 对话历史
            user_profile: 用户画像

        Returns:
            List[Dict]: [{"role": "user", "content": "..."}, ...]
        """
        messages = []

        # 1. Few-shot示例 (仅前2个，控制token)
        examples = self._get_few_shot_examples()[:2]
        for example in examples:
            messages.append({"role": "user", "content": example["user"]})
            messages.append({"role": "assistant", "content": example["assistant"]})

        # 2. 对话历史 (最近3轮)
        recent_history = conversation_history[-3:] if len(conversation_history) > 3 else conversation_history
        messages.extend(recent_history)

        # 3. 当前用户消息
        messages.append({"role": "user", "content": user_message})

        return messages

    def _build_conversation_history(self, conversation_id: int) -> List[Dict[str, str]]:
        """
        构建对话历史

        Args:
            conversation_id: 对话ID

        Returns:
            List[Dict]: [{"role": "user", "content": "..."}, ...]
        """
        from ...models.conversation import Message

        messages = (
            self.db.query(Message).filter(Message.conversation_id == conversation_id).order_by(Message.created_at).all()
        )

        return [{"role": msg.role.value, "content": msg.content} for msg in messages]

    def _extract_metadata(self, user_message: str, assistant_response: str) -> Dict[str, Any]:
        """
        提取元数据 (子类可覆盖以添加专属元数据)

        Args:
            user_message: 用户消息
            assistant_response: 助手响应

        Returns:
            Dict: 元数据字典
        """
        return {
            "ip_type": self.ip_type,
            "ip_name": self.ip_name,
            "timestamp": datetime.utcnow().isoformat(),
        }
