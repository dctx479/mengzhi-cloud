"""
Jimeng AI Provider (即梦AI - 火山引擎视觉智能) - 图像/视频/音频生成

来源: F:/Ai/API接入聚合指南/即梦AI API接入示例.md
官方文档: https://www.volcengine.com/product/visual
API endpoint: https://visual.volcengineapi.com

⚠️ 与 volcengine_provider.py (方舟 Ark LLM) 是火山引擎下两个不同产品:
 - 方舟 Ark LLM: ark.cn-beijing.volces.com/api/v3 (文本对话/embedding)
 - 即梦AI 视觉: visual.volcengineapi.com (图像/视频/音频生成)

支持能力:
 - 图像生成: 文生图 3.0/3.1, 图片生成 4.0/4.6, 图生图 3.0 (智能参考)
 - 视频生成: 视频生成 3.0 (720P/1080P), 3.0 Pro, 动作模仿, OmniHuman1.5 数字人
 - 音频生成: 小云雀 AI 配音 (TTS)
"""

import asyncio
import json
import time
import base64
from typing import Dict, List, Any, Optional, Set
import httpx
from loguru import logger

from app.services.ai.multimedia_provider import MultimediaProvider, MediaCapability

# ==================== 模型常量 ====================

# 图像生成模型
IMAGE_MODELS = {
    "text-to-image-3.0": {"name": "文生图3.0", "price": 0.2, "endpoint": "/api/v1/image/text-to-image-3.0"},
    "text-to-image-3.1": {"name": "文生图3.1", "price": 0.2, "endpoint": "/api/v1/image/text-to-image-3.1"},
    "image-generation-4.0": {"name": "图片生成4.0", "price": 0.5, "endpoint": "/api/v1/image/generation-4.0"},
    "image-generation-4.6": {"name": "图片生成4.6", "price": 0.5, "endpoint": "/api/v1/image/generation-4.6"},
    "image-to-image-3.0": {"name": "图生图3.0智能参考", "price": 0.2, "endpoint": "/api/v1/image/image-to-image-3.0"},
    "material-extraction": {"name": "素材提取", "price": 0.5, "endpoint": "/api/v1/image/material-extraction"},
    "inpainting": {"name": "交互编辑inpainting", "price": 0.0, "endpoint": "/api/v1/image/inpainting"},
    "outpainting": {"name": "智能扩图outpainting", "price": 0.0, "endpoint": "/api/v1/image/outpainting"},
}

# 视频生成模型
VIDEO_MODELS = {
    "video-generation-3.0-pro": {
        "name": "视频生成3.0 Pro",
        "endpoint": "/api/v1/video/generation-3.0-pro",
        "bill_by": "second",
    },
    "video-generation-3.0-720p": {
        "name": "视频生成3.0 720P",
        "endpoint": "/api/v1/video/generation-3.0",
        "bill_by": "second",
    },
    "video-generation-3.0-1080p": {
        "name": "视频生成3.0 1080P",
        "endpoint": "/api/v1/video/generation-3.0",
        "bill_by": "second",
    },
    "action-imitation": {"name": "动作模仿", "endpoint": "/api/v1/video/action-imitation", "bill_by": "task"},
    "omni-human-1.5": {"name": "OmniHuman1.5数字人", "endpoint": "/api/v1/digital-human/generate", "bill_by": "task"},
}

# 音频生成模型
AUDIO_MODELS = {
    "tts": {"name": "小云雀AI配音", "endpoint": "/api/v1/audio/tts", "bill_by": "character"},
}

# 所有支持的模型 (扁平化)
SUPPORTED_MODELS: List[str] = list(IMAGE_MODELS.keys()) + list(VIDEO_MODELS.keys()) + list(AUDIO_MODELS.keys())


# ==================== 错误类型 ====================


class JimengAPIError(Exception):
    """即梦AI API 错误"""

    def __init__(self, message: str, code: Optional[int] = None):
        self.code = code
        super().__init__(message)


# ==================== Provider 实现 (单类) ====================


class JimengAI(MultimediaProvider):
    """即梦AI Provider (图像/视频/音频生成) - 异步版本"""

    def __init__(
        self,
        api_key: str,
        base_url: Optional[str] = None,
        endpoint: Optional[str] = None,
        timeout: float = 120.0,
        **kwargs,
    ):
        # base_url (工厂统一入参) 与 endpoint (历史入参) 二选一, 均映射到 self.endpoint
        resolved = base_url or endpoint
        super().__init__(api_key=api_key, base_url=resolved, **kwargs)
        self.endpoint = resolved or "https://visual.volcengineapi.com"
        self.timeout = timeout
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }

    @property
    def name(self) -> str:
        return "jimeng"

    @property
    def supported_models(self) -> List[str]:
        return SUPPORTED_MODELS

    @property
    def capabilities(self) -> Set[MediaCapability]:
        return {MediaCapability.IMAGE, MediaCapability.VIDEO, MediaCapability.AUDIO}

    # ---- MultimediaProvider 统一接口 (委托给具体业务方法) ----

    async def generate_image(self, prompt: str, **opts) -> Dict[str, Any]:
        return await self.text_to_image(prompt, **opts)

    async def generate_audio(self, text: str, **opts) -> Dict[str, Any]:
        return await self.text_to_speech(text, **opts)

    def _build_url(self, path: str) -> str:
        return f"{self.endpoint}{path}"

    async def _request(self, method: str, path: str, **kwargs) -> Dict[str, Any]:
        """统一请求方法"""
        url = self._build_url(path)
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.request(method, url, headers=self.headers, **kwargs)
            response.raise_for_status()
            result = response.json()
            if result.get("code") != 0:
                raise JimengAPIError(f"API error: {result.get('message')}", code=result.get("code"))
            return result.get("data", {})

    async def _poll_task(
        self,
        task_id: str,
        max_attempts: int = 60,
        interval: float = 5.0,
    ) -> Dict[str, Any]:
        """轮询异步任务结果"""
        for attempt in range(max_attempts):
            data = await self._request("GET", "/api/v1/task/query", params={"task_id": task_id})
            status = data.get("status")
            if status == "completed":
                return data
            elif status == "failed":
                raise JimengAPIError(f"Task failed: {data.get('error', 'unknown')}")
            else:
                progress = data.get("progress", 0)
                logger.info(f"Jimeng task {task_id}: {progress}% ({attempt+1}/{max_attempts})")
                await asyncio.sleep(interval)
        raise TimeoutError(f"Jimeng task {task_id} timed out after {max_attempts} attempts")

    async def test_connection(self) -> Dict[str, Any]:
        """测试连接 - 用最便宜的文生图3.0验证API Key"""
        start = time.time()
        try:
            await self.text_to_image("test", model="text-to-image-3.0", width=256, height=256, steps=10)
            return {
                "success": True,
                "message": "Connection successful",
                "latency_ms": int((time.time() - start) * 1000),
            }
        except JimengAPIError as e:
            return {"success": False, "message": f"API error: {e}", "error": str(e)}
        except Exception as e:
            return {"success": False, "message": f"Connection failed: {e}", "error": str(e)}

    # ==================== 图像生成 ====================

    async def text_to_image(
        self,
        prompt: str,
        model: str = "text-to-image-3.1",
        width: int = 1024,
        height: int = 1024,
        steps: int = 50,
        guidance_scale: float = 7.5,
        seed: int = -1,
        negative_prompt: str = "低质量, 模糊, 扭曲",
    ) -> Dict[str, Any]:
        """文生图 (支持 3.0/3.1/4.0/4.6)"""
        if model not in IMAGE_MODELS:
            raise ValueError(f"Unknown image model: {model}. Available: {list(IMAGE_MODELS.keys())}")
        model_info = IMAGE_MODELS[model]

        if model.startswith("image-generation-4"):
            # 4.0/4.6 系列的 payload 格式
            payload = {
                "prompt": prompt,
                "style": "realistic",  # realistic/anime/oil_painting/watercolor
                "quality": "high",  # standard/high/ultra
                "aspect_ratio": f"{width}:{height}",
                "num_images": 1,
            }
        else:
            # 3.0/3.1 系列
            payload = {
                "prompt": prompt,
                "negative_prompt": negative_prompt,
                "width": width,
                "height": height,
                "steps": steps,
                "guidance_scale": guidance_scale,
                "seed": seed,
            }

        data = await self._request("POST", model_info["endpoint"], json=payload)
        return {
            "model": model,
            "image_url": data.get("image_url"),
            "task_id": data.get("task_id"),
            "cost_cny": model_info["price"],
        }

    async def image_to_image(
        self,
        reference_image_url: str,
        prompt: str,
        strength: float = 0.7,
        seed: int = -1,
    ) -> Dict[str, Any]:
        """图生图 3.0 智能参考 (风格迁移)"""
        payload = {
            "reference_image": reference_image_url,
            "prompt": prompt,
            "strength": strength,
            "seed": seed,
        }
        data = await self._request("POST", IMAGE_MODELS["image-to-image-3.0"]["endpoint"], json=payload)
        return {
            "model": "image-to-image-3.0",
            "image_url": data.get("image_url"),
            "task_id": data.get("task_id"),
            "cost_cny": IMAGE_MODELS["image-to-image-3.0"]["price"],
        }

    async def extract_material(self, image_url: str, material_type: str = "POD") -> Dict[str, Any]:
        """素材提取 (POD按需定制/商品提取)"""
        payload = {"image_url": image_url, "material_type": material_type}
        data = await self._request("POST", IMAGE_MODELS["material-extraction"]["endpoint"], json=payload)
        return {
            "model": "material-extraction",
            "materials": data.get("materials", []),
            "task_id": data.get("task_id"),
            "cost_cny": IMAGE_MODELS["material-extraction"]["price"],
        }

    async def inpainting(
        self,
        image_url: str,
        mask_url: str,
        prompt: str,
    ) -> Dict[str, Any]:
        """交互编辑 inpainting (局部修复)"""
        payload = {"image_url": image_url, "mask_url": mask_url, "prompt": prompt}
        data = await self._request("POST", IMAGE_MODELS["inpainting"]["endpoint"], json=payload)
        return {
            "model": "inpainting",
            "image_url": data.get("image_url"),
            "task_id": data.get("task_id"),
        }

    async def outpainting(self, image_url: str, direction: str = "all", ratio: float = 1.5) -> Dict[str, Any]:
        """智能扩图 outpainting (图片外延)"""
        payload = {"image_url": image_url, "direction": direction, "ratio": ratio}
        data = await self._request("POST", IMAGE_MODELS["outpainting"]["endpoint"], json=payload)
        return {
            "model": "outpainting",
            "image_url": data.get("image_url"),
            "task_id": data.get("task_id"),
        }

    async def upload_image(self, image_path: str) -> str:
        """上传本地图片, 返回URL (供 image_to_image/inpainting 使用)"""
        with open(image_path, "rb") as f:
            image_b64 = base64.b64encode(f.read()).decode("utf-8")
        ext = image_path.rsplit(".", 1)[-1].lower()
        payload = {"image_data": image_b64, "format": ext}
        data = await self._request("POST", "/api/v1/upload", json=payload)
        return data["image_url"]

    # ==================== 视频生成 ====================

    async def generate_video(
        self,
        prompt: str,
        duration: int = 5,
        resolution: str = "1080p",
        fps: int = 30,
        style: str = "realistic",
        model: str = "video-generation-3.0-pro",
        wait: bool = True,
        max_poll_attempts: int = 60,
    ) -> Dict[str, Any]:
        """视频生成 (3.0/3.0 Pro)"""
        if model not in VIDEO_MODELS:
            raise ValueError(f"Unknown video model: {model}")
        model_info = VIDEO_MODELS[model]
        payload = {
            "prompt": prompt,
            "duration": duration,
            "resolution": resolution,
            "fps": fps,
            "style": style,
        }
        data = await self._request("POST", model_info["endpoint"], json=payload)
        task_id = data.get("task_id")
        if not task_id:
            raise JimengAPIError("No task_id in response")
        if not wait:
            return {"model": model, "task_id": task_id, "status": "submitted"}
        result = await self._poll_task(task_id, max_attempts=max_poll_attempts)
        return {
            "model": model,
            "task_id": task_id,
            "video_url": result.get("video_url") or result.get("result_url"),
            "status": "completed",
            "duration": duration,
        }

    async def action_imitation(
        self,
        source_video_url: str,
        target_image_url: str,
        preserve_face: bool = True,
    ) -> Dict[str, Any]:
        """动作模仿 (将 source_video 的动作应用到 target_image)"""
        payload = {
            "source_video": source_video_url,
            "target_image": target_image_url,
            "preserve_face": preserve_face,
        }
        data = await self._request("POST", VIDEO_MODELS["action-imitation"]["endpoint"], json=payload)
        task_id = data.get("task_id")
        if not task_id:
            raise JimengAPIError("No task_id in response")
        result = await self._poll_task(task_id)
        return {
            "model": "action-imitation",
            "task_id": task_id,
            "video_url": result.get("video_url"),
        }

    async def omni_human(
        self,
        image_url: str,
        audio_url: Optional[str] = None,
        script: Optional[str] = None,
    ) -> Dict[str, Any]:
        """OmniHuman1.5 数字人生成 (三步流程)"""
        # 1. 主体识别
        identify = await self._request("POST", "/api/v1/digital-human/identify", json={"image_url": image_url})
        subject_id = identify.get("subject_id")
        # 2. 主体检测
        await self._request("POST", "/api/v1/digital-human/detect", json={"subject_id": subject_id})
        # 3. 数字人合成
        synth = await self._request(
            "POST",
            VIDEO_MODELS["omni-human-1.5"]["endpoint"],
            json={
                "subject_id": subject_id,
                "audio_url": audio_url,
                "script": script,
            },
        )
        task_id = synth.get("task_id")
        result = await self._poll_task(task_id)
        return {
            "model": "omni-human-1.5",
            "task_id": task_id,
            "video_url": result.get("video_url"),
        }

    # ==================== 音频生成 ====================

    async def text_to_speech(
        self,
        text: str,
        voice: str = "female_1",
        speed: float = 1.0,
        pitch: float = 1.0,
        volume: float = 1.0,
        format: str = "mp3",
    ) -> Dict[str, Any]:
        """小云雀 AI 配音 (TTS)"""
        payload = {
            "text": text,
            "voice": voice,
            "speed": max(0.5, min(2.0, speed)),
            "pitch": max(0.5, min(2.0, pitch)),
            "volume": max(0.5, min(2.0, volume)),
            "format": format if format in ("mp3", "wav") else "mp3",
        }
        data = await self._request("POST", AUDIO_MODELS["tts"]["endpoint"], json=payload)
        return {
            "model": "tts",
            "audio_url": data.get("audio_url"),
            "voice": voice,
            "format": format,
            "duration_sec": data.get("duration_sec", 0),
        }


# ==================== 兼容性别名 ====================

# 兼容旧代码从 jimeng_provider 导入 JimengClient
JimengClient = JimengAI
