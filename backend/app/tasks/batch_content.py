"""
批量内容生成任务执行体

由 POST /content-generation/tasks 通过 FastAPI BackgroundTasks 触发。
状态全程写入 batch_tasks 表（DB 驱动状态机），不依赖外部任务队列。

设计要点（仿 tasks/cultural.py）：
- 任务体内自建 SessionLocal()，因为 HTTP 响应返回后请求 session 已关闭。
- 进度以 DB 表为准：每完成一个产品就回写 completed_count/progress/results。
- 协作式取消：cancel 端点把 status 置 cancelled，任务体每轮循环 re-query，发现已取消即 break。
- 已知局限：进程重启会中断正在 running 的任务，其状态停留在 running（MVP 可接受）。

版本: 1.0
创建日期: 2026-06-14
"""

import asyncio
from datetime import datetime
from typing import Any, Dict, List, Optional

from loguru import logger

from app.core.database import SessionLocal
from app.models.batch_task import BatchTask
from app.models.base import generate_uuid
from app.models.content_record import (
    ContentRecord, ContentType, Style, Platform, RecordStatus, LengthType,
)
from app.services.optimized_content_generation import ContentGenerationServiceFactory

# 单次生成超时（秒）
_SINGLE_TIMEOUT = 60
_VARIANT_TIMEOUT = 180


def _get_task(db, task_uuid: str) -> Optional[BatchTask]:
    return db.query(BatchTask).filter(BatchTask.task_uuid == task_uuid).first()


def _update_task(db, task_uuid: str, **fields) -> None:
    """更新批量任务字段并提交"""
    task = _get_task(db, task_uuid)
    if not task:
        return
    for key, value in fields.items():
        setattr(task, key, value)
    task.updated_at = datetime.utcnow()
    db.commit()


def _resolve_enum(enum_cls, value: str, default):
    """字符串 → 枚举，无效时回退默认值"""
    try:
        return enum_cls[value.upper()]
    except (KeyError, AttributeError):
        return default


def _length_type(word_count: int) -> LengthType:
    if word_count < 500:
        return LengthType.SHORT
    if word_count <= 1500:
        return LengthType.MEDIUM
    return LengthType.LONG


def _word_count(content: str) -> int:
    return len("".join((content or "").split()))


async def _generate_product(
    pid_str: str, semaphore: asyncio.Semaphore, task_uuid: str, service: Any,
    count: int, content_type_enum, style_enum, platform_enum, word_count: int,
    keywords, avoid_words, target_audience, temperature, template_id,
    user_id: int, length_type
) -> List[Dict[str, Any]]:
    """单产品并行生成（带 Semaphore 限流和取消检查）"""
    async with semaphore:
        # 协作式取消检查
        db = SessionLocal()
        try:
            current = _get_task(db, task_uuid)
            if current and current.status == "cancelled":
                logger.info(f"批量任务已取消，跳过产品 {pid_str} (task_uuid={task_uuid})")
                return []
        finally:
            db.close()

        try:
            product_id = int(pid_str)
        except (ValueError, TypeError):
            logger.warning(f"⚠️ 无效的 product_id={pid_str!r}，跳过 (task_uuid={task_uuid})")
            return []

        try:
            if count > 1:
                contents = await asyncio.wait_for(
                    service.generate_multiple_variants(
                        product_id=product_id, count=count,
                        content_type=content_type_enum, style=style_enum,
                        platform=platform_enum, word_count=word_count,
                        keywords=keywords, avoid_words=avoid_words,
                        target_audience=target_audience, temperature=temperature,
                        template_id=template_id,
                    ),
                    timeout=min(_SINGLE_TIMEOUT * count, _VARIANT_TIMEOUT),
                )
            else:
                single = await asyncio.wait_for(
                    service.generate_product_copy(
                        product_id=product_id,
                        content_type=content_type_enum, style=style_enum,
                        platform=platform_enum, word_count=word_count,
                        keywords=keywords, avoid_words=avoid_words,
                        target_audience=target_audience, temperature=temperature,
                        template_id=template_id,
                    ),
                    timeout=_SINGLE_TIMEOUT,
                )
                contents = [single]
        except Exception as e:
            logger.error(f"⚠️ 批量生成单产品失败 product_id={product_id} task_uuid={task_uuid}: {e}")
            return []

        now_iso = datetime.utcnow().isoformat()
        results = []
        for content in contents:
            content = content or ""
            results.append({
                "id": generate_uuid(),
                "template_id": template_id or "",
                "product_id": str(product_id),
                "content": content,
                "word_count": _word_count(content),
                "rating": 0,
                "edited": False,
                "created_at": now_iso,
                "updated_at": now_iso,
            })

        # 落 ContentRecord（独立子 session）
        try:
            rec_db = SessionLocal()
            rec_db.add(ContentRecord(
                user_id=user_id, product_id=product_id,
                content_type=content_type_enum, platform=platform_enum,
                style=style_enum, length_type=length_type,
                input_params={"word_count": word_count, "template_id": template_id,
                "count": count, "batch_task": task_uuid},
                keywords=keywords, generated_content=contents[0] if contents else "",
                model_name="deepseek-chat", status=RecordStatus.COMPLETED,
            ))
            rec_db.commit()
        except Exception as rec_err:
            logger.warning(f"⚠️ 批量任务保存 ContentRecord 失败: {rec_err}")
        finally:
            rec_db.close()

        return results


async def run_batch_generation(task_uuid: str) -> None:
    """执行批量内容生成（BackgroundTasks 入口，并行 + 分块）"""
    db = SessionLocal()
    try:
        task = _get_task(db, task_uuid)
        if not task:
            logger.error(f"⚠️ 批量任务不存在 task_uuid={task_uuid}")
            return

        config: Dict[str, Any] = task.config or {}
        product_ids: List[str] = config.get("product_ids") or []
        count = config.get("count") or 1
        if not isinstance(count, int) or count < 1:
            count = 1
        word_count = config.get("word_count") or 200
        keywords = config.get("keywords") or None
        avoid_words = config.get("avoid_words") or None
        target_audience = config.get("target_audience") or None
        temperature = config.get("temperature")
        template_id = config.get("template_id") or None
        user_id = task.user_id

        content_type_enum = _resolve_enum(ContentType, config.get("content_type") or "copy", ContentType.COPY)
        style_enum = _resolve_enum(Style, config.get("style") or "casual", Style.CASUAL)
        platform_enum = _resolve_enum(Platform, config.get("platform") or "general", Platform.GENERAL)
        length_type = _length_type(word_count)

        # 协作式取消：进入循环前再次确认未被取消
        if task.status == "cancelled":
            logger.info(f"批量任务已取消，跳过执行 task_uuid={task_uuid}")
            return
        total = task.total_count or (len(product_ids) * count)
        _update_task(db, task_uuid, status="running", started_at=datetime.utcnow(), last_heartbeat_at=datetime.utcnow())

        service = await ContentGenerationServiceFactory.get_service(db)

        results: List[Dict[str, Any]] = []
        completed = 0
        semaphore = asyncio.Semaphore(10)

        # 分块执行：每 100 产品一批
        chunk_size = 100
        for chunk_start in range(0, len(product_ids), chunk_size):
            # 协作式取消检查
            current = _get_task(db, task_uuid)
            if current and current.status == "cancelled":
                logger.info(f"批量任务已取消，停止生成 task_uuid={task_uuid}")
                return

            chunk = product_ids[chunk_start:chunk_start + chunk_size]
            tasks = [
                _generate_product(
                    pid, semaphore, task_uuid, service, count,
                    content_type_enum, style_enum, platform_enum, word_count,
                    keywords, avoid_words, target_audience, temperature, template_id,
                    user_id, length_type
                )
                for pid in chunk
            ]

            # 并行执行当前批次
            batch_results = await asyncio.gather(*tasks, return_exceptions=True)
            for result in batch_results:
                if isinstance(result, Exception):
                    logger.error(f"⚠️ 产品生成异常: {result}")
                    completed += count
                elif isinstance(result, list):
                    results.extend(result)
                    completed += len(result)

            # 更新进度和心跳
            progress = int(completed / total * 100) if total else 100
            _update_task(db, task_uuid, completed_count=completed,
                         progress=min(progress, 99 if completed < total else 100),
                         results=results, last_heartbeat_at=datetime.utcnow())

        # 收尾：再次确认未被取消
        current = _get_task(db, task_uuid)
        if current and current.status == "cancelled":
            return

        _update_task(db, task_uuid, status="completed", progress=100,
                     completed_count=completed, results=results,
                     completed_at=datetime.utcnow())
        logger.info(f"批量任务完成 task_uuid={task_uuid} 生成 {len(results)} 条")

    except Exception as e:
        error_msg = str(e)
        logger.error(f"⚠️ 批量内容生成任务失败 task_uuid={task_uuid}: {error_msg}")
        try:
            _update_task(db, task_uuid, status="failed",
                         error_message=error_msg[:500], completed_at=datetime.utcnow())
        except Exception as upd_err:
            logger.error(f"⚠️ 更新失败状态异常 task_uuid={task_uuid}: {upd_err}")
    finally:
        db.close()
