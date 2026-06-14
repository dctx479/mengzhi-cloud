"""
IP智能体对话API

提供小数和小商双IP智能体对话服务
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Optional
from pydantic import BaseModel, Field
import logging
import json

from app.core.database import get_db
from app.core.responses import success_response
from app.api.deps import get_user_id
from app.services.ip_agent import IPRouter, IPAgentFactory, IPType
from app.core.exceptions import BusinessException

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ip-chat", tags=["IP对话"])


# ============ Request Models ============


class IPChatRequest(BaseModel):
    """IP对话请求"""

    content: str = Field(..., description="用户消息内容", min_length=1, max_length=2000)
    conversation_id: Optional[int] = Field(None, description="对话ID (可选，不传则创建新对话)")
    ip_type: Optional[str] = Field(None, description="指定IP类型 (xiaoshu/xiaoshang)，不传则自动路由")
    temperature: float = Field(0.7, ge=0, le=1, description="温度参数")


class IPInfoResponse(BaseModel):
    """IP信息响应"""

    ip_type: str
    name: str
    description: str
    focus: str


# ============ API Endpoints ============


@router.post("/message")
async def send_ip_message(
    request: IPChatRequest, user_id: int = Depends(get_user_id), db: Session = Depends(get_db)
):
    """
    IP智能体对话 (非流式)

    根据用户消息自动路由到合适的IP Agent，或手动指定IP类型

    请求示例:
    ```json
    {
        "content": "推荐一款羊肉",
        "conversation_id": 123,
        "ip_type": "xiaoshu",
        "temperature": 0.7
    }
    ```

    响应示例:
    ```json
    {
        "code": 200,
        "data": {
            "content": "咱们草原上的羊肉...",
            "ip_type": "xiaoshu",
            "ip_name": "小数",
            "conversation_id": 123,
            "tokens": {"input": 100, "output": 200, "total": 300},
            "cost": 0.0015,
            "metadata": {
                "cultural_elements": ["草原", "蒙古"]
            }
        }
    }
    ```
    """
    try:
        # 1. 决定使用哪个IP (自动路由 或 手动指定)
        if request.ip_type:
            # 手动指定IP
            try:
                ip_type = IPType(request.ip_type)
                logger.info(f"[IPChat] User specified IP: {ip_type.value}")
            except ValueError:
                raise HTTPException(status_code=400, detail=f"Invalid IP type: {request.ip_type}")
        else:
            # 自动路由
            router_instance = IPRouter()
            ip_type = router_instance.route(request.content)
            logger.info(f"[IPChat] Auto-routed to IP: {ip_type.value}")

        # 2. 创建Agent
        agent = IPAgentFactory.create_agent(ip_type, db)

        # 3. 生成响应
        response = await agent.generate_response(
            user_message=request.content, conversation_id=request.conversation_id, temperature=request.temperature
        )

        # 4. 构建返回数据
        result = {
            "content": response["content"],
            "ip_type": agent.ip_type,
            "ip_name": agent.ip_name,
            "conversation_id": request.conversation_id,  # TODO: 实际应从Agent返回
            "tokens": response["tokens"],
            "cost": response["cost"],
            "metadata": response["metadata"],
        }

        return success_response(data=result)

    except BusinessException as e:
        logger.error(f"[IPChat] Business error: {e.message}")
        raise HTTPException(status_code=e.get_http_status(), detail=e.message)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[IPChat] Unexpected error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/stream")
async def send_ip_message_stream(
    request: IPChatRequest, user_id: int = Depends(get_user_id), db: Session = Depends(get_db)
):
    """
    IP智能体对话 (流式SSE)

    功能与 /message 相同，但返回流式响应

    响应格式 (SSE):
    ```
    data: {"type": "chunk", "content": "咱们"}
    data: {"type": "chunk", "content": "草原上"}
    data: {"type": "done", "metadata": {...}}
    ```
    """
    from fastapi.responses import StreamingResponse

    # 1. 决定使用哪个IP
    if request.ip_type:
        try:
            ip_type = IPType(request.ip_type)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid IP type: {request.ip_type}")
    else:
        router_instance = IPRouter()
        ip_type = router_instance.route(request.content)

    # 2. 创建Agent
    agent = IPAgentFactory.create_agent(ip_type, db)

    # 3. 流式生成器
    async def event_generator():
        try:
            async for chunk in agent.generate_response_stream(
                user_message=request.content, conversation_id=request.conversation_id, temperature=request.temperature
            ):
                payload = {"type": "chunk", "content": chunk}
                yield f"data: {json.dumps(payload, ensure_ascii=False)}\n\n"

            # 发送完成信号
            done_payload = {"type": "done", "ip_type": agent.ip_type, "ip_name": agent.ip_name}
            yield f"data: {json.dumps(done_payload, ensure_ascii=False)}\n\n"

        except Exception as e:
            logger.error(f"[IPChat Stream] Error: {str(e)}")
            error_payload = {"type": "error", "message": str(e)}
            yield f"data: {json.dumps(error_payload, ensure_ascii=False)}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "Connection": "keep-alive", "X-Accel-Buffering": "no"},
    )


@router.get("/ips")
async def get_available_ips():
    """
    获取所有可用的IP列表

    响应示例:
    ```json
    {
        "code": 200,
        "data": {
            "xiaoshu": {
                "name": "小数",
                "description": "草原文化传承者",
                "focus": "产品咨询、文化故事、选购建议"
            },
            "xiaoshang": {
                "name": "小商",
                "description": "品牌营销顾问",
                "focus": "营销策略、内容创作、平台运营"
            }
        }
    }
    ```
    """
    ips = IPAgentFactory.get_available_ips()
    return success_response(data=ips)


@router.post("/route")
async def test_route(content: str):
    """
    测试路由算法 (调试用)

    返回给定消息会被路由到哪个IP

    响应示例:
    ```json
    {
        "code": 200,
        "data": {
            "content": "推荐一款羊肉",
            "routed_to": "xiaoshu",
            "explanation": "匹配关键词: 推荐, 羊肉"
        }
    }
    ```
    """
    router_instance = IPRouter()
    ip_type = router_instance.route(content)
    explanation = router_instance.get_route_explanation(content, ip_type)

    return success_response(data={"content": content, "routed_to": ip_type.value, "explanation": explanation})
