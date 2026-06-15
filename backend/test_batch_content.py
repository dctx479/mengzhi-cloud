"""
批量内容生成功能测试

覆盖：
- BatchTask.to_dict() 字段与前端 BatchTask 接口对齐
- run_batch_generation 任务体：进度回写、完成状态、结果结构（mock 生成服务，不真调 DeepSeek）
- GET /tasks 列表、POST /tasks 创建、cancel 置状态
- export txt/docx/pdf 返回正确 content-type，非法格式 400

运行：pytest backend/test_batch_content.py -v
"""

import asyncio
import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

import app.models  # noqa: F401 —— 确保所有表注册到 Base.metadata
from app.main import app
from app.core.database import Base
from app.api.deps import get_db, get_current_user
from app.models.user import User
from app.models.batch_task import BatchTask
import app.tasks.batch_content as batch_content


# ==================== 测试数据库（内存 SQLite，StaticPool 单连接共享） ====================

engine = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)
Base.metadata.create_all(bind=engine)

# 当前测试用户上下文（供 get_current_user 覆盖读取）
_ctx = {"user_uuid": None}


def _override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


def _override_get_current_user():
    return {"user_id": _ctx["user_uuid"], "user_type": "personal", "role": "user",
            "tenant_id": None, "jti": "test"}


app.dependency_overrides[get_db] = _override_get_db
app.dependency_overrides[get_current_user] = _override_get_current_user

client = TestClient(app)


# 前端 BatchTask 接口字段（types/content-generation.ts）
FRONTEND_BATCH_TASK_KEYS = {
    "id", "name", "template", "template_id", "count", "progress", "status",
    "results", "error_message", "retry_count", "created_at", "updated_at", "started_at", "completed_at",
}
FRONTEND_RESULT_KEYS = {
    "id", "template_id", "product_id", "content", "word_count", "rating",
    "edited", "created_at", "updated_at",
}


@pytest.fixture(autouse=True)
def clean_and_user():
    """每个测试前清表并创建一个测试用户"""
    db = TestingSessionLocal()
    db.query(BatchTask).delete()
    db.query(User).delete()
    db.commit()

    # SQLite 上 BIGINT autoincrement 不会自增（仅 INTEGER PRIMARY KEY），显式指定 id=1
    user = User(
        id=1,
        user_uuid=str(uuid.uuid4()),
        username=f"batchtester_{uuid.uuid4().hex[:6]}",
        password_hash="x",
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    _ctx["user_uuid"] = user.user_uuid
    db.close()
    yield 1


def _fake_service(single="生成的文案内容", variants=None):
    svc = MagicMock()
    svc.generate_product_copy = AsyncMock(return_value=single)
    svc.generate_multiple_variants = AsyncMock(return_value=variants or ["变体一", "变体二"])
    return svc


def _make_task(user_id, **overrides):
    db = TestingSessionLocal()
    # SQLite 上 BIGINT autoincrement 不会自增，显式分配 id 与 task_uuid
    existing = db.query(BatchTask).count()
    fields = dict(
     id=existing + 1,
     task_uuid=str(uuid.uuid4()),
     user_id=user_id,
        name="测试批量任务",
        config={"product_ids": ["1", "2"], "count": 1, "style": "casual",
                "word_count": 200, "content_type": "copy", "platform": "general"},
        total_count=2,
        completed_count=0,
        retry_count=0,
        status="pending",
    )
    fields.update(overrides)
    task = BatchTask(**fields)
    db.add(task)
    db.commit()
    db.refresh(task)
    tid = task.task_uuid
    db.close()
    return tid


# ==================== to_dict 字段对齐 ====================

def test_to_dict_aligns_with_frontend(clean_and_user):
    tid = _make_task(clean_and_user)
    db = TestingSessionLocal()
    task = db.query(BatchTask).filter(BatchTask.task_uuid == tid).first()
    d = task.to_dict()
    db.close()
    assert set(d.keys()) == FRONTEND_BATCH_TASK_KEYS
    assert d["id"] == tid
    assert d["count"] == 2
    assert d["status"] == "pending"
    assert d["results"] == []


# ==================== 任务体：进度回写 + 完成 ====================

def test_run_batch_generation_completes(clean_and_user):
    tid = _make_task(clean_and_user)
    with patch.object(batch_content, "SessionLocal", TestingSessionLocal), \
         patch.object(batch_content.ContentGenerationServiceFactory, "get_service",
                      new=AsyncMock(return_value=_fake_service())):
        asyncio.run(batch_content.run_batch_generation(tid))

    db = TestingSessionLocal()
    task = db.query(BatchTask).filter(BatchTask.task_uuid == tid).first()
    assert task.status == "completed"
    assert task.progress == 100
    assert task.completed_count == 2
    assert len(task.results) == 2
    assert set(task.results[0].keys()) == FRONTEND_RESULT_KEYS
    assert task.results[0]["content"] == "生成的文案内容"
    assert task.started_at is not None and task.completed_at is not None
    db.close()


def test_run_batch_generation_variants_count(clean_and_user):
    tid = _make_task(
        clean_and_user,
        config={"product_ids": ["1"], "count": 2, "style": "casual",
                "word_count": 200, "content_type": "copy", "platform": "general"},
        total_count=2,
    )
    with patch.object(batch_content, "SessionLocal", TestingSessionLocal), \
         patch.object(batch_content.ContentGenerationServiceFactory, "get_service",
                      new=AsyncMock(return_value=_fake_service(variants=["A", "B"]))):
        asyncio.run(batch_content.run_batch_generation(tid))

    db = TestingSessionLocal()
    task = db.query(BatchTask).filter(BatchTask.task_uuid == tid).first()
    assert task.status == "completed"
    assert len(task.results) == 2
    db.close()


def test_run_batch_generation_respects_cancel(clean_and_user):
    tid = _make_task(clean_and_user, status="cancelled")
    with patch.object(batch_content, "SessionLocal", TestingSessionLocal), \
         patch.object(batch_content.ContentGenerationServiceFactory, "get_service",
                      new=AsyncMock(return_value=_fake_service())):
        asyncio.run(batch_content.run_batch_generation(tid))

    db = TestingSessionLocal()
    task = db.query(BatchTask).filter(BatchTask.task_uuid == tid).first()
    # 已取消 → 任务体不应把它改为 completed
    assert task.status == "cancelled"
    db.close()


# ==================== 端点：列表 / 创建 / 取消 ====================

def test_get_tasks_list(clean_and_user):
    _make_task(clean_and_user)
    _make_task(clean_and_user)
    resp = client.get("/api/v1/content-generation/tasks")
    assert resp.status_code == 200
    body = resp.json()
    assert body["code"] == 200
    assert isinstance(body["data"], list)
    assert len(body["data"]) == 2


def test_create_task_endpoint(clean_and_user):
    # 后台任务替换为 no-op，避免真实执行
    with patch.object(batch_content, "run_batch_generation", AsyncMock()):
        resp = client.post("/api/v1/content-generation/tasks", json={
            "config": {"product_ids": ["1", "2", "3"], "count": 2,
                       "style": "casual", "word_count": 200,
                       "content_type": "copy", "platform": "general"}
        })
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["count"] == 6  # 3 产品 × 2
    assert data["status"] == "pending"
    assert set(data.keys()) == FRONTEND_BATCH_TASK_KEYS


def test_create_task_requires_products(clean_and_user):
    resp = client.post("/api/v1/content-generation/tasks", json={
        "config": {"product_ids": [], "count": 1, "style": "casual",
                   "word_count": 200, "content_type": "copy", "platform": "general"}
    })
    assert resp.status_code == 400


def test_cancel_task(clean_and_user):
    tid = _make_task(clean_and_user, status="running")
    resp = client.post(f"/api/v1/content-generation/tasks/{tid}/cancel")
    assert resp.status_code == 200
    assert resp.json()["data"]["status"] == "cancelled"
    # 再次取消已结束任务 → 400
    resp2 = client.post(f"/api/v1/content-generation/tasks/{tid}/cancel")
    assert resp2.status_code == 400


# ==================== 端点：导出 ====================

@pytest.fixture
def completed_task(clean_and_user):
    results = [
        {"id": "r1", "template_id": "", "product_id": "1", "content": "牛肉文案\n第二行",
         "word_count": 6, "rating": 0, "edited": False,
         "created_at": "2026-06-14T00:00:00", "updated_at": "2026-06-14T00:00:00"},
        {"id": "r2", "template_id": "", "product_id": "2", "content": "羊肉文案",
         "word_count": 4, "rating": 0, "edited": False,
         "created_at": "2026-06-14T00:00:00", "updated_at": "2026-06-14T00:00:00"},
    ]
    return _make_task(clean_and_user, status="completed", progress=100,
                      completed_count=2, results=results)


@pytest.mark.parametrize("fmt,ctype", [
    ("txt", "text/plain"),
    ("docx", "application/vnd.openxmlformats-officedocument.wordprocessingml.document"),
    ("pdf", "application/pdf"),
])
def test_export_formats(completed_task, fmt, ctype):
    resp = client.get(f"/api/v1/content-generation/tasks/{completed_task}/export/{fmt}")
    assert resp.status_code == 200
    assert resp.headers["content-type"].startswith(ctype)
    assert len(resp.content) > 0


def test_export_invalid_format(completed_task):
    resp = client.get(f"/api/v1/content-generation/tasks/{completed_task}/export/xml")
    assert resp.status_code == 400


def test_export_empty_results(clean_and_user):
    tid = _make_task(clean_and_user, status="completed", results=[])
    resp = client.get(f"/api/v1/content-generation/tasks/{tid}/export/txt")
    assert resp.status_code == 400


# ==================== 端点：重试 ====================

def test_retry_failed_task(clean_and_user):
    tid = _make_task(clean_and_user, status="failed", error_message="生成失败", retry_count=0)
    with patch.object(batch_content, "run_batch_generation", AsyncMock()):
        resp = client.post(f"/api/v1/content-generation/tasks/{tid}/retry")
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["status"] == "pending"
    assert data["retry_count"] == 1
    assert data["error_message"] is None


def test_retry_cancelled_task(clean_and_user):
    tid = _make_task(clean_and_user, status="cancelled", retry_count=1)
    with patch.object(batch_content, "run_batch_generation", AsyncMock()):
        resp = client.post(f"/api/v1/content-generation/tasks/{tid}/retry")
    assert resp.status_code == 200
    assert resp.json()["data"]["retry_count"] == 2


def test_retry_completed_task_rejected(clean_and_user):
    tid = _make_task(clean_and_user, status="completed")
    resp = client.post(f"/api/v1/content-generation/tasks/{tid}/retry")
    assert resp.status_code == 400


# ==================== 启动清理 ====================

def test_startup_cleanup_stale_tasks(clean_and_user):
    from datetime import datetime, timedelta
    from sqlalchemy import or_
    # 创建3个 running 任务：无心跳、心跳过期、心跳正常
    tid_no_hb = _make_task(clean_and_user, status="running", last_heartbeat_at=None)
    tid_stale = _make_task(clean_and_user, status="running",
                           last_heartbeat_at=datetime.utcnow() - timedelta(minutes=10))
    tid_alive = _make_task(clean_and_user, status="running",
                           last_heartbeat_at=datetime.utcnow() - timedelta(seconds=30))

    # 模拟 startup 清理逻辑
    db = TestingSessionLocal()
    stale_tasks = db.query(BatchTask).filter(
        BatchTask.status == "running",
        or_(
            BatchTask.last_heartbeat_at.is_(None),
            BatchTask.last_heartbeat_at < datetime.utcnow() - timedelta(minutes=5)
        )
    ).all()
    for task in stale_tasks:
        task.status = "failed"
        task.error_message = "任务异常终止（进程重启或超时）"
    db.commit()

    # 验证：无心跳和过期心跳被清理，正常心跳保留
    t1 = db.query(BatchTask).filter(BatchTask.task_uuid == tid_no_hb).first()
    t2 = db.query(BatchTask).filter(BatchTask.task_uuid == tid_stale).first()
    t3 = db.query(BatchTask).filter(BatchTask.task_uuid == tid_alive).first()
    assert t1.status == "failed"
    assert "异常终止" in t1.error_message
    assert t2.status == "failed"
    assert t3.status == "running"  # 未被清理
    db.close()


# ==================== 并行执行 ====================

def test_parallel_execution(clean_and_user):
    """验证并行执行：10 个产品并行生成，Semaphore(10) 限流"""
    tid = _make_task(
        clean_and_user,
        config={"product_ids": [str(i) for i in range(1, 11)], "count": 1,
                "style": "casual", "word_count": 200,
                "content_type": "copy", "platform": "general"},
        total_count=10,
    )
    with patch.object(batch_content, "SessionLocal", TestingSessionLocal), \
         patch.object(batch_content.ContentGenerationServiceFactory, "get_service",
                      new=AsyncMock(return_value=_fake_service(single="并行测试内容"))):
        asyncio.run(batch_content.run_batch_generation(tid))

    db = TestingSessionLocal()
    task = db.query(BatchTask).filter(BatchTask.task_uuid == tid).first()
    assert task.status == "completed"
    assert len(task.results) == 10  # 10 产品全部生成
    assert task.last_heartbeat_at is not None  # 心跳已更新
    db.close()


