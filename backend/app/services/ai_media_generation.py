"""
AI媒体生成业务服务
"""

import base64
import hashlib
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from cryptography.fernet import Fernet
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.ai_media_generation import (
    MediaGenerationCost,
    MediaGenerationResult,
    MediaGenerationTask,
    MediaProvider,
    MediaProviderType,
    MediaTaskStatus,
)
from app.models.user import User
from app.services.ai_media_providers import (
    MediaGenerationQueryResult,
    MediaGenerationRequest,
    MediaGenerationSubmitResult,
    MediaProviderError,
    build_media_provider_client,
)

_raw_key = hashlib.sha256(settings.SECRET_KEY.encode()).digest()
cipher = Fernet(base64.urlsafe_b64encode(_raw_key))


def encrypt_media_api_key(api_key: str) -> str:
    return cipher.encrypt(api_key.encode()).decode()


def decrypt_media_api_key(api_key_encrypted: str) -> str:
    return cipher.decrypt(api_key_encrypted.encode()).decode()


class AIMediaGenerationService:
    """AI媒体生成任务服务"""

    def __init__(self, db: Session):
        self.db = db

    def get_user_by_uuid(self, user_uuid: str) -> Optional[User]:
        return self.db.query(User).filter(User.user_uuid == user_uuid).first()

    def list_providers(self, provider_type: Optional[MediaProviderType] = None, include_inactive: bool = True):
        query = self.db.query(MediaProvider)
        if provider_type:
            query = query.filter(MediaProvider.provider_type == provider_type)
        if not include_inactive:
            query = query.filter(MediaProvider.is_active.is_(True))
        query = query.filter(MediaProvider.deleted_at.is_(None))
        return query.order_by(
            MediaProvider.provider_type, MediaProvider.priority.desc(), MediaProvider.created_at.desc()
        ).all()

    def get_provider(self, provider_id: int) -> Optional[MediaProvider]:
        return (
            self.db.query(MediaProvider)
            .filter(MediaProvider.id == provider_id, MediaProvider.deleted_at.is_(None))
            .first()
        )

    def create_provider(self, data: Dict[str, Any]) -> MediaProvider:
        provider = MediaProvider(**data)
        if provider.is_primary:
            self._clear_primary_provider(provider.provider_type)
        self.db.add(provider)
        self.db.commit()
        self.db.refresh(provider)
        return provider

    def update_provider(self, provider: MediaProvider, data: Dict[str, Any]) -> MediaProvider:
        next_provider_type = data.get("provider_type", provider.provider_type)
        next_is_primary = data.get("is_primary", provider.is_primary)
        if next_is_primary:
            self._clear_primary_provider(next_provider_type, exclude_id=provider.id)
        for key, value in data.items():
            setattr(provider, key, value)
        self.db.commit()
        self.db.refresh(provider)
        return provider

    def delete_provider(self, provider: MediaProvider) -> None:
        provider.is_active = False
        provider.deleted_at = datetime.now(timezone.utc)
        self.db.commit()

    def select_provider(
        self, media_type: MediaProviderType, provider_id: Optional[int] = None
    ) -> Optional[MediaProvider]:
        query = self.db.query(MediaProvider).filter(
            MediaProvider.provider_type == media_type,
            MediaProvider.is_active.is_(True),
            MediaProvider.health_status != "unhealthy",
            MediaProvider.deleted_at.is_(None),
        )
        if provider_id:
            return query.filter(MediaProvider.id == provider_id).first()
        return query.order_by(
            MediaProvider.is_primary.desc(), MediaProvider.priority.desc(), MediaProvider.created_at.desc()
        ).first()

    def create_generation_task(
        self,
        user: User,
        media_type: MediaProviderType,
        prompt: str,
        provider: Optional[MediaProvider],
        **kwargs: Any,
    ) -> MediaGenerationTask:
        task = MediaGenerationTask(
            user_id=user.id,
            enterprise_id=user.enterprise_id,
            provider_id=provider.id if provider else None,
            media_type=media_type,
            status=MediaTaskStatus.PENDING,
            prompt=prompt,
            model=kwargs.get("model") or (provider.default_model if provider else None),
            negative_prompt=kwargs.get("negative_prompt"),
            width=kwargs.get("width"),
            height=kwargs.get("height"),
            duration=kwargs.get("duration"),
            result_count=kwargs.get("result_count", 1),
            request_params=kwargs.get("request_params"),
            cost_amount=self.calculate_task_cost(provider, kwargs.get("result_count", 1), kwargs.get("duration")),
        )
        self.db.add(task)
        self.db.commit()
        self.db.refresh(task)
        return task

    def mark_task_processing(
        self, task: MediaGenerationTask, provider_task_id: Optional[str] = None
    ) -> MediaGenerationTask:
        task.status = MediaTaskStatus.PROCESSING
        task.started_at = datetime.now(timezone.utc)
        if provider_task_id:
            task.provider_task_id = provider_task_id
        self.db.commit()
        self.db.refresh(task)
        return task

    def cancel_task(self, task: MediaGenerationTask) -> MediaGenerationTask:
        task.status = MediaTaskStatus.CANCELED
        task.completed_at = datetime.now(timezone.utc)
        self.db.commit()
        self.db.refresh(task)
        return task

    def get_task(self, task_uuid: str) -> Optional[MediaGenerationTask]:
        return (
            self.db.query(MediaGenerationTask)
            .filter(
                MediaGenerationTask.task_uuid == task_uuid,
                MediaGenerationTask.deleted_at.is_(None),
            )
            .first()
        )

    def list_tasks(
        self,
        user: Optional[User],
        is_admin: bool,
        status: Optional[MediaTaskStatus],
        media_type: Optional[MediaProviderType],
        page: int,
        page_size: int,
    ):
        query = self.db.query(MediaGenerationTask).filter(MediaGenerationTask.deleted_at.is_(None))
        if not is_admin and user:
            query = query.filter(MediaGenerationTask.user_id == user.id)
        if status:
            query = query.filter(MediaGenerationTask.status == status)
        if media_type:
            query = query.filter(MediaGenerationTask.media_type == media_type)
        total = query.count()
        items = (
            query.order_by(MediaGenerationTask.created_at.desc()).offset((page - 1) * page_size).limit(page_size).all()
        )
        return total, items

    def calculate_task_cost(
        self, provider: Optional[MediaProvider], result_count: int, duration: Optional[int]
    ) -> float:
        if not provider:
            return 0.0
        unit_count = max(result_count, 1)
        if provider.provider_type == MediaProviderType.VIDEO and duration:
            unit_count = max(duration, 1)
        return round(provider.cost_per_unit * unit_count, 4)

    def record_cost(self, task: MediaGenerationTask) -> Optional[MediaGenerationCost]:
        if not task.provider:
            return None
        existing = self.db.query(MediaGenerationCost).filter(MediaGenerationCost.task_id == task.id).first()
        if existing:
            return existing
        unit_count = task.result_count
        if task.media_type == MediaProviderType.VIDEO and task.duration:
            unit_count = task.duration
        cost = MediaGenerationCost(
            task_id=task.id,
            provider_id=task.provider_id,
            user_id=task.user_id,
            enterprise_id=task.enterprise_id,
            media_type=task.media_type,
            unit_count=unit_count,
            unit_price=task.provider.cost_per_unit,
            total_amount=task.cost_amount,
        )
        self.db.add(cost)
        self.db.commit()
        self.db.refresh(cost)
        return cost

    def get_cost_summary(self, media_type: Optional[MediaProviderType] = None) -> Dict[str, Any]:
        query = self.db.query(MediaGenerationCost)
        if media_type:
            query = query.filter(MediaGenerationCost.media_type == media_type)
        total_cost = query.with_entities(func.coalesce(func.sum(MediaGenerationCost.total_amount), 0)).scalar() or 0
        total_tasks = query.count()
        by_provider = (
            query.join(MediaProvider, MediaGenerationCost.provider_id == MediaProvider.id)
            .with_entities(
                MediaProvider.provider_name,
                func.coalesce(func.sum(MediaGenerationCost.total_amount), 0).label("amount"),
                func.count(MediaGenerationCost.id).label("count"),
            )
            .group_by(MediaProvider.provider_name)
            .all()
        )
        return {
            "total_cost": float(total_cost),
            "total_tasks": total_tasks,
            "by_provider": [
                {"provider_name": name, "total_cost": float(amount), "task_count": count}
                for name, amount, count in by_provider
            ],
        }

    def build_generation_request(self, task: MediaGenerationTask) -> MediaGenerationRequest:
        return MediaGenerationRequest(
            media_type=task.media_type,
            prompt=task.prompt,
            negative_prompt=task.negative_prompt,
            model=task.model,
            width=task.width,
            height=task.height,
            duration=task.duration,
            result_count=task.result_count,
            params=task.request_params or {},
        )

    def get_provider_client(self, provider: MediaProvider):
        api_key = decrypt_media_api_key(provider.api_key_encrypted)
        return build_media_provider_client(provider, api_key)

    async def validate_provider(self, provider: MediaProvider) -> Dict[str, Any]:
        client = self.get_provider_client(provider)
        try:
            success, error_message, payload = await client.validate_config()
            if success:
                provider.record_success()
                self.db.commit()
                self.db.refresh(provider)
                return {"success": True, "message": "配置测试成功", "details": payload or {}}
            provider.record_failure(error_message or "配置测试失败")
            self.db.commit()
            self.db.refresh(provider)
            return {"success": False, "message": error_message or "配置测试失败", "details": payload or {}}
        except MediaProviderError as exc:
            provider.record_failure(str(exc))
            self.db.commit()
            self.db.refresh(provider)
            return {"success": False, "message": str(exc), "details": {}}

    async def submit_task_to_provider(self, task: MediaGenerationTask) -> MediaGenerationTask:
        if not task.provider:
            raise MediaProviderError("任务未绑定服务商")
        client = self.get_provider_client(task.provider)
        request = self.build_generation_request(task)
        result = await client.submit_task(request)
        self.apply_submit_result(task, result)
        return task

    async def sync_task_status(self, task: MediaGenerationTask) -> MediaGenerationTask:
        if not task.provider:
            raise MediaProviderError("任务未绑定服务商")
        if not task.provider_task_id:
            return task
        client = self.get_provider_client(task.provider)
        result = await client.query_task(task.provider_task_id)
        self.apply_query_result(task, result)
        return task

    def apply_submit_result(
        self, task: MediaGenerationTask, result: MediaGenerationSubmitResult
    ) -> MediaGenerationTask:
        task.provider_task_id = result.provider_task_id or task.provider_task_id
        task.started_at = task.started_at or datetime.now(timezone.utc)
        self._apply_task_result(task, result.status, result.results, result.error_message)
        return task

    def apply_query_result(self, task: MediaGenerationTask, result: MediaGenerationQueryResult) -> MediaGenerationTask:
        task.provider_task_id = result.provider_task_id or task.provider_task_id
        self._apply_task_result(task, result.status, result.results, result.error_message)
        return task

    def _apply_task_result(
        self,
        task: MediaGenerationTask,
        status: MediaTaskStatus,
        results: list,
        error_message: Optional[str],
    ) -> None:
        task.status = status
        if error_message:
            task.error_message = error_message[:1000]
        if status == MediaTaskStatus.PROCESSING:
            if task.provider:
                task.provider.record_success()
            self.db.commit()
            self.db.refresh(task)
            return
        if status == MediaTaskStatus.SUCCEEDED:
            task.completed_at = datetime.now(timezone.utc)
            if task.provider:
                task.provider.record_success()
            self._replace_task_results(task, results)
            self.db.commit()
            self.db.refresh(task)
            self.record_cost(task)
            return
        if status == MediaTaskStatus.FAILED:
            task.completed_at = datetime.now(timezone.utc)
            if task.provider:
                task.provider.record_failure(error_message or "任务执行失败")
            self.db.commit()
            self.db.refresh(task)
            return
        self.db.commit()
        self.db.refresh(task)

    def _replace_task_results(self, task: MediaGenerationTask, results: list) -> None:
        self.db.query(MediaGenerationResult).filter(MediaGenerationResult.task_id == task.id).delete(
            synchronize_session=False
        )
        for item in results:
            self.db.add(
                MediaGenerationResult(
                    task_id=task.id,
                    file_url=item.file_url,
                    thumbnail_url=item.thumbnail_url,
                    file_size=item.file_size,
                    width=item.width,
                    height=item.height,
                    duration=item.duration,
                    metadata_json=item.metadata,
                )
            )

    def _clear_primary_provider(self, provider_type: MediaProviderType, exclude_id: Optional[int] = None) -> None:
        query = self.db.query(MediaProvider).filter(
            MediaProvider.provider_type == provider_type,
            MediaProvider.is_primary.is_(True),
            MediaProvider.deleted_at.is_(None),
        )
        if exclude_id:
            query = query.filter(MediaProvider.id != exclude_id)
        query.with_for_update().update({MediaProvider.is_primary: False}, synchronize_session=False)
