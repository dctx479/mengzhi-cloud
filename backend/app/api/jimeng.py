"""
即梦视频/图片生成服务（示例）
展示如何使用严谨的计费系统
"""
from typing import Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

from ..api.deps import get_db, get_current_user
from ..services.strict_billing import StrictBillingService, InsufficientQuotaError, InsufficientBalanceError
from ..models.user import User

router = APIRouter()


class ImageGenerationRequest(BaseModel):
    """图片生成请求"""
    prompt: str = Field(..., description="提示词")
    resolution: str = Field("1024x1024", description="分辨率", regex="^(512x512|1024x1024|2048x2048)$")
    style: Optional[str] = Field(None, description="风格")


class VideoGenerationRequest(BaseModel):
    """视频生成请求"""
    prompt: str = Field(..., description="提示词")
    duration: int = Field(5, description="时长（秒）", ge=1, le=300)
    resolution: str = Field("720p", description="分辨率", regex="^(720p|1080p|4k)$")


class GenerationResponse(BaseModel):
    """生成响应"""
    transaction_id: int
    status: str
    cost: float
    result_url: Optional[str] = None


@router.post("/jimeng/image/generate", response_model=GenerationResponse)
async def generate_image(
    request: ImageGenerationRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    生成图片（即梦）

    严谨的计费流程：
    1. 预扣费（检查配额和余额）
    2. 调用即梦API生成图片
    3. 成功：确认交易
    4. 失败：全额退款
    """
    billing_service = StrictBillingService(db)

    # 生成幂等性key
    idempotency_key = billing_service.generate_idempotency_key(
        current_user.enterprise_id,
        {"type": "image", "prompt": request.prompt, "resolution": request.resolution}
    )

    try:
        # 1. 预扣费
        transaction = billing_service.pre_deduct(
            enterprise_id=current_user.enterprise_id,
            service_type="jimeng_image",
            params={
                "resolution": request.resolution,
                "prompt": request.prompt,
                "style": request.style
            },
            idempotency_key=idempotency_key
        )

        # 2. 调用即梦API生成图片
        try:
            # TODO: 实际调用即梦API
            result_url = f"https://jimeng.example.com/images/{transaction.id}.png"

            # 模拟生成成功
            success = True

            if success:
                # 3. 确认交易
                billing_service.confirm_transaction(
                    transaction.id,
                    actual_usage={
                        "resolution": request.resolution,
                        "result_url": result_url,
                        "generated_at": str(datetime.utcnow())
                    }
                )

                return GenerationResponse(
                    transaction_id=transaction.id,
                    status="completed",
                    cost=float(transaction.amount),
                    result_url=result_url
                )
            else:
                # 4. 生成失败，全额退款
                billing_service.refund_transaction(
                    transaction.id,
                    reason="图片生成失败",
                    refund_percentage=100
                )

                raise HTTPException(status_code=500, detail="图片生成失败")

        except Exception as e:
            # 异常情况，全额退款
            billing_service.refund_transaction(
                transaction.id,
                reason=f"生成异常: {str(e)}",
                refund_percentage=100
            )
            raise

    except InsufficientQuotaError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except InsufficientBalanceError as e:
        raise HTTPException(status_code=402, detail=str(e))


@router.post("/jimeng/video/generate", response_model=GenerationResponse)
async def generate_video(
    request: VideoGenerationRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    生成视频（即梦）

    严谨的计费流程：
    1. 预扣费（检查配额和余额）
    2. 调用即梦API生成视频
    3. 成功：确认交易
    4. 失败：全额退款
    """
    billing_service = StrictBillingService(db)

    # 生成幂等性key
    idempotency_key = billing_service.generate_idempotency_key(
        current_user.enterprise_id,
        {"type": "video", "prompt": request.prompt, "duration": request.duration, "resolution": request.resolution}
    )

    try:
        # 1. 预扣费
        transaction = billing_service.pre_deduct(
            enterprise_id=current_user.enterprise_id,
            service_type="jimeng_video",
            params={
                "resolution": request.resolution,
                "duration": request.duration,
                "prompt": request.prompt
            },
            idempotency_key=idempotency_key
        )

        # 2. 调用即梦API生成视频
        try:
            # TODO: 实际调用即梦API
            result_url = f"https://jimeng.example.com/videos/{transaction.id}.mp4"

            # 模拟生成成功
            success = True
            actual_duration = request.duration  # 实际生成时长

            if success:
                # 3. 确认交易
                billing_service.confirm_transaction(
                    transaction.id,
                    actual_usage={
                        "resolution": request.resolution,
                        "duration": actual_duration,
                        "result_url": result_url,
                        "generated_at": str(datetime.utcnow())
                    }
                )

                return GenerationResponse(
                    transaction_id=transaction.id,
                    status="completed",
                    cost=float(transaction.amount),
                    result_url=result_url
                )
            else:
                # 4. 生成失败，全额退款
                billing_service.refund_transaction(
                    transaction.id,
                    reason="视频生成失败",
                    refund_percentage=100
                )

                raise HTTPException(status_code=500, detail="视频生成失败")

        except Exception as e:
            # 异常情况，全额退款
            billing_service.refund_transaction(
                transaction.id,
                reason=f"生成异常: {str(e)}",
                refund_percentage=100
            )
            raise

    except InsufficientQuotaError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except InsufficientBalanceError as e:
        raise HTTPException(status_code=402, detail=str(e))
