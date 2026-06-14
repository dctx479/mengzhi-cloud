"""即梦AI (Jimeng) 多媒体生成 API 端点."""

from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from typing import Optional
import time
import json
import base64
from loguru import logger

from app.api.deps import get_db, get_current_user
from app.models.user import User
from app.services.ai.multimedia_factory import MultimediaProviderFactory
from app.services.ai.providers.jimeng_provider import (
    JimengAI,
    JimengAPIError,
    IMAGE_MODELS,
    VIDEO_MODELS,
    AUDIO_MODELS,
    SUPPORTED_MODELS,
)

router = APIRouter(
    prefix="/jimeng",
    tags=[
        chr(34)
        + chr(21363)
        + chr(26790)
        + chr(65)
        + chr(73)
        + chr(32)
        + chr(45)
        + chr(32)
        + chr(74)
        + chr(105)
        + chr(109)
        + chr(101)
        + chr(110)
        + chr(103)
        + chr(34)
    ],
)


async def _get_jimeng_client(db: Session, user: User) -> JimengAI:
    try:
        client = MultimediaProviderFactory.resolve_for_enterprise(db, user.enterprise_id, "jimeng")
    except Exception:
        logger.error("Jimeng API key decrypt failed")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="API Key decrypt failed",
        )
    if client is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Jimeng not configured",
        )
    return client


class TextToImageRequest(BaseModel):
    prompt: str = Field(..., min_length=1, max_length=2000)
    model: str = Field(default="text-to-image-3.1")
    width: int = Field(default=1024, ge=256, le=2048)
    height: int = Field(default=1024, ge=256, le=2048)
    steps: int = Field(default=50, ge=1, le=100)
    guidance_scale: float = Field(default=7.5, ge=0.0, le=20.0)
    seed: int = Field(default=-1)
    negative_prompt: str = Field(default="")


@router.post("/text-to-image")
async def text_to_image(
    request: TextToImageRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        client = await _get_jimeng_client(db, current_user)
        result = await client.text_to_image(
            prompt=request.prompt,
            model=request.model,
            width=request.width,
            height=request.height,
            steps=request.steps,
            guidance_scale=request.guidance_scale,
            seed=request.seed,
            negative_prompt=request.negative_prompt,
        )
        return result
    except JimengAPIError as e:
        raise HTTPException(status_code=400, detail=str(e))


class ImageToImageRequest(BaseModel):
    reference_image_url: str = Field(...)
    prompt: str = Field(..., min_length=1, max_length=2000)
    strength: float = Field(default=0.7, ge=0.0, le=1.0)
    seed: int = Field(default=-1)


@router.post("/image-to-image")
async def image_to_image(
    request: ImageToImageRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        client = await _get_jimeng_client(db, current_user)
        result = await client.image_to_image(
            request.reference_image_url,
            request.prompt,
            strength=request.strength,
            seed=request.seed,
        )
        return result
    except JimengAPIError as e:
        raise HTTPException(status_code=400, detail=str(e))


class InpaintingRequest(BaseModel):
    original_image_url: str = Field(...)
    mask_url: str = Field(...)
    prompt: str = Field(..., min_length=1, max_length=2000)


@router.post("/inpainting")
async def inpainting(
    request: InpaintingRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        client = await _get_jimeng_client(db, current_user)
        result = await client.inpainting(
            original_image_url=request.original_image_url,
            mask_url=request.mask_url,
            prompt=request.prompt,
        )
        return result
    except JimengAPIError as e:
        raise HTTPException(status_code=400, detail=str(e))


class OutpaintingRequest(BaseModel):
    original_image_url: str = Field(...)
    prompt: str = Field(...)
    scale_factor: float = Field(default=1.5, ge=1.0, le=3.0)


@router.post("/outpainting")
async def outpainting(
    request: OutpaintingRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        client = await _get_jimeng_client(db, current_user)
        result = await client.outpainting(
            original_image_url=request.original_image_url,
            prompt=request.prompt,
            scale_factor=request.scale_factor,
        )
        return result
    except JimengAPIError as e:
        raise HTTPException(status_code=400, detail=str(e))


class ExtractMaterialRequest(BaseModel):
    product_image_url: str = Field(...)
    background: str = Field(default="white")


@router.post("/extract-material")
async def extract_material(
    request: ExtractMaterialRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        client = await _get_jimeng_client(db, current_user)
        result = await client.extract_material(
            product_image_url=request.product_image_url,
            background=request.background,
        )
        return result
    except JimengAPIError as e:
        raise HTTPException(status_code=400, detail=str(e))


class GenerateVideoRequest(BaseModel):
    prompt: str = Field(..., min_length=1, max_length=2000)
    model: str = Field(default="video-generation-3.0-pro")
    duration: int = Field(default=5, ge=1, le=60)
    resolution: str = Field(default="720p")
    wait: bool = Field(default=False)


@router.post("/generate-video")
async def generate_video(
    request: GenerateVideoRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        client = await _get_jimeng_client(db, current_user)
        result = await client.generate_video(
            prompt=request.prompt,
            model=request.model,
            duration=request.duration,
            resolution=request.resolution,
            wait=request.wait,
        )
        return result
    except JimengAPIError as e:
        raise HTTPException(status_code=400, detail=str(e))


class ActionImitationRequest(BaseModel):
    reference_video_url: str = Field(...)
    target_image_url: str = Field(...)


@router.post("/action-imitation")
async def action_imitation(
    request: ActionImitationRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        client = await _get_jimeng_client(db, current_user)
        result = await client.action_imitation(
            reference_video_url=request.reference_video_url,
            target_image_url=request.target_image_url,
        )
        return result
    except JimengAPIError as e:
        raise HTTPException(status_code=400, detail=str(e))


class OmniHumanRequest(BaseModel):
    audio_url: str = Field(...)
    image_url: str = Field(...)


@router.post("/omni-human")
async def omni_human(
    request: OmniHumanRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        client = await _get_jimeng_client(db, current_user)
        result = await client.omni_human(
            audio_url=request.audio_url,
            image_url=request.image_url,
        )
        return result
    except JimengAPIError as e:
        raise HTTPException(status_code=400, detail=str(e))


class TextToSpeechRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=5000)
    voice: str = Field(default="female_1")
    speed: float = Field(default=1.0, ge=0.5, le=2.0)


@router.post("/text-to-speech")
async def text_to_speech(
    request: TextToSpeechRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        client = await _get_jimeng_client(db, current_user)
        result = await client.text_to_speech(
            text=request.text,
            voice=request.voice,
            speed=request.speed,
        )
        return result
    except JimengAPIError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/upload-image")
async def upload_image(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        client = await _get_jimeng_client(db, current_user)
        content = await file.read()
        image_b64 = base64.b64encode(content).decode("utf-8")
        result = await client.upload_image(image_b64)
        return result
    except JimengAPIError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/task/{task_id}")
async def get_task_status(
    task_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        client = await _get_jimeng_client(db, current_user)
        result = await client._poll_task(task_id)
        return result
    except JimengAPIError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/models")
async def list_models(
    current_user: User = Depends(get_current_user),
):
    return {
        "image": IMAGE_MODELS,
        "video": VIDEO_MODELS,
        "audio": AUDIO_MODELS,
        "total": len(SUPPORTED_MODELS),
    }


@router.post("/test-connection")
async def test_connection(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        client = await _get_jimeng_client(db, current_user)
        result = await client.test_connection()
        return result
    except Exception as e:
        logger.error("test connection error")
    return {"success": False, "message": str(e)}
