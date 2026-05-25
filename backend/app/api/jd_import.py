"""
京东联盟商品导入 API

端点:
  POST /api/v1/jd/import          批量导入（管理员）
  GET  /api/v1/jd/search          实时搜索代理（登录用户）
  GET  /api/v1/jd/status          查询 API 配置状态（管理员）
"""

import asyncio

from fastapi import APIRouter, Depends, Query, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from loguru import logger

from app.api.deps import get_db, require_admin, get_current_user
from app.core.responses import success_response
from app.core.database import SessionLocal
from app.models.user import User
from app.services.jd_import_service import JdImportService
from app.services.jd_api_client import JdApiError
from app.core.config import settings

router = APIRouter(prefix="/jd", tags=["京东联盟导入 - JD Import"])


# ------------------------------------------------------------------
# 请求/响应 Schema
# ------------------------------------------------------------------

class ImportRequest(BaseModel):
    keyword: str = Field(..., min_length=1, max_length=100, description="搜索关键词")
    max_pages: int = Field(default=3, ge=1, le=10, description="最多拉取页数（每页30条）")
    page_size: int = Field(default=30, ge=1, le=30, description="每页数量")


def _get_user_int_id(current_user: dict, db: Session) -> int:
    """从 JWT payload (user_id=UUID) 查询用户的整数 DB id。"""
    user_uuid = current_user["user_id"]
    user = db.query(User).filter(User.user_uuid == user_uuid).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="用户不存在")
    return user.id


# ------------------------------------------------------------------
# 路由
# ------------------------------------------------------------------

@router.get("/status")
async def get_jd_status(current_user: dict = Depends(require_admin)):
    """查询京东联盟 API 配置状态（管理员）"""
    app_key = getattr(settings, "JD_APP_KEY", None)
    configured = bool(app_key and getattr(settings, "JD_SECRET_KEY", None))
    return success_response(data={
        "configured": configured,
        "app_key_prefix": (app_key[:4] + "****") if app_key else None,
        "note": "当前 AppKey 具备基础权限。商品搜索/导入功能需在京东联盟后台申请「商品查询」高级接口权限。",
    })


@router.post("/import")
async def import_from_jd(
    body: ImportRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_admin),
):
    """
    按关键词批量导入京东商品（管理员）。
    任务在后台执行，立即返回 202 Accepted。
    """
    user_int_id = _get_user_int_id(current_user, db)
    keyword = body.keyword
    max_pages = body.max_pages
    page_size = body.page_size

    def _run():
        bg_db = SessionLocal()
        try:
            service = JdImportService(bg_db)
            result = asyncio.run(service.import_by_keyword(
                keyword=keyword,
                max_pages=max_pages,
                page_size=page_size,
                created_by_id=user_int_id,
            ))
            logger.info(f"JD 后台导入完成: {result}")
        except Exception as e:
            logger.error(f"JD 后台导入失败: {e}")
        finally:
            bg_db.close()

    background_tasks.add_task(_run)

    return success_response(
        data={"status": "accepted", "keyword": body.keyword},
        message=f"导入任务已提交，正在后台拉取「{body.keyword}」相关商品",
    )


@router.get("/search")
async def search_jd_goods(
    keyword: str = Query(..., min_length=1, max_length=100),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=30),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    实时搜索京东商品（登录用户）。
    结果不写库，直接返回格式化数据供前端展示。
    """
    service = JdImportService(db)
    try:
        result = await service.search_realtime(
            keyword=keyword,
            page=page,
            page_size=page_size,
        )
    except RuntimeError as e:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(e))
    except JdApiError as e:
        if e.code == "403":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=e.message,
            )
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=f"京东API错误: {e.message}")

    return success_response(data=result)
