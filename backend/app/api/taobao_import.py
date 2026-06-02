"""
淘宝联盟商品导入 API

端点:
  GET  /api/v1/taobao/status            查询 API 配置状态（管理员）
  GET  /api/v1/taobao/config            获取当前 Session 配置（管理员，脱敏）
  PUT  /api/v1/taobao/config            手动更新 Session（管理员，备用）
  GET  /api/v1/taobao/oauth/authorize   生成淘宝 OAuth2 授权 URL（管理员）
  GET  /api/v1/taobao/oauth/callback    接收淘宝回调，用 code 换 session（公开，淘宝回调）
  POST /api/v1/taobao/oauth/refresh     刷新 Session（管理员）
  POST /api/v1/taobao/import            批量导入（管理员）
  GET  /api/v1/taobao/search            实时搜索代理（登录用户）

OAuth2 流程:
  1. 管理员点「授权」→ 前端调 /oauth/authorize 获取授权 URL
  2. 前端弹窗打开授权 URL（淘宝登录页）
  3. 用户授权后淘宝回调 /oauth/callback?code=xxx&state=xxx
  4. 后端用 code 换 session + refresh_token，存入 system_configs
  5. 前端轮询 /status 检测 has_session 变为 true

淘宝 OAuth2 端点:
  授权: https://oauth.taobao.com/authorize
  换取 token: https://oauth.taobao.com/token  (POST, grant_type=authorization_code)
  刷新 token: https://oauth.taobao.com/token  (POST, grant_type=refresh_token)
"""

import asyncio
import secrets
from datetime import datetime, timezone, timedelta
from typing import Optional
from urllib.parse import urlencode

import httpx
from fastapi import APIRouter, Depends, Query, HTTPException, status, BackgroundTasks
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from loguru import logger

from app.api.deps import get_db, require_admin, get_current_user
from app.core.responses import success_response
from app.core.database import SessionLocal
from app.models.user import User
from app.models.system_config import SystemConfig
from app.services.taobao_import_service import TaobaoImportService, _client_instance_reset
from app.services.taobao_api_client import TaobaoApiError
from app.core.config import settings

router = APIRouter(prefix="/taobao", tags=["淘宝联盟导入 - Taobao Import"])

# system_configs 键名
_TB_TOKEN_KEY = "taobao_session"       # {"session", "refresh_token", "expires_at", "taobao_user_id"}
_TB_OAUTH_STATE_KEY = "taobao_oauth_state"  # CSRF state 临时存储

# 淘宝 OAuth2 端点
_TB_AUTH_URL = "https://oauth.taobao.com/authorize"
_TB_TOKEN_URL = "https://oauth.taobao.com/token"


# ------------------------------------------------------------------
# 内部工具
# ------------------------------------------------------------------

def _get_token_row(db: Session) -> Optional[SystemConfig]:
    return db.query(SystemConfig).filter(SystemConfig.config_key == _TB_TOKEN_KEY).first()


def _get_session(db: Session) -> Optional[str]:
    """DB 优先，其次 .env"""
    row = _get_token_row(db)
    if row and isinstance(row.config_value, dict):
        return row.config_value.get("session") or None
    return getattr(settings, "TAOBAO_SESSION", None) or None


def _save_token_data(db: Session, data: dict) -> None:
    """将 token 数据写入 system_configs，并重置客户端单例。"""
    row = _get_token_row(db)
    if row:
        row.config_value = data
    else:
        row = SystemConfig(
            config_key=_TB_TOKEN_KEY,
            config_value=data,
            description="淘宝联盟 OAuth2 Session（自动管理）",
        )
        db.add(row)
    db.commit()
    _client_instance_reset()


def _get_state_row(db: Session) -> Optional[SystemConfig]:
    return db.query(SystemConfig).filter(SystemConfig.config_key == _TB_OAUTH_STATE_KEY).first()


def _save_state(db: Session, state: str) -> None:
    row = _get_state_row(db)
    if row:
        row.config_value = {"state": state}
    else:
        db.add(SystemConfig(
            config_key=_TB_OAUTH_STATE_KEY,
            config_value={"state": state},
            description="淘宝 OAuth2 CSRF state（临时）",
        ))
    db.commit()


def _get_user_int_id(current_user: dict, db: Session) -> int:
    user_uuid = current_user["user_id"]
    user = db.query(User).filter(User.user_uuid == user_uuid).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="用户不存在")
    return user.id


# ------------------------------------------------------------------
# 请求/响应 Schema
# ------------------------------------------------------------------

class TaobaoImportRequest(BaseModel):
    keyword: str = Field(..., min_length=1, max_length=100)
    max_pages: int = Field(default=3, ge=1, le=10)
    page_size: int = Field(default=40, ge=1, le=100)
    adzone_id: Optional[str] = Field(default=None, max_length=64, description="推广位 ID（可选，用于佣金追踪）")


class TaobaoSessionUpdateRequest(BaseModel):
    session: str = Field(..., min_length=1, max_length=512, description="淘宝联盟 OAuth2 Session（access_token）")


# ------------------------------------------------------------------
# 状态 / 配置
# ------------------------------------------------------------------

@router.get("/status")
async def get_taobao_status(
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_admin),
):
    """查询淘宝联盟 API 配置状态（管理员）"""
    app_key = getattr(settings, "TAOBAO_APP_KEY", None)
    app_secret = getattr(settings, "TAOBAO_APP_SECRET", None)
    configured = bool(app_key and app_secret)

    row = _get_token_row(db)
    db_data = row.config_value if (row and isinstance(row.config_value, dict)) else {}
    db_session = db_data.get("session") if db_data else None
    env_session = getattr(settings, "TAOBAO_SESSION", None)
    session = db_session or env_session
    has_session = bool(session)
    session_source = "db" if db_session else ("env" if env_session else None)

    # 过期时间
    expires_at = db_data.get("expires_at") if db_data else None
    session_expired = False
    if expires_at:
        try:
            exp_dt = datetime.fromisoformat(expires_at)
            session_expired = datetime.now(timezone.utc) >= exp_dt
        except Exception:
            pass

    redirect_uri = getattr(settings, "TAOBAO_OAUTH_REDIRECT_URI", None)

    if not configured:
        note = None
    elif not has_session:
        note = "⚠️ 未获取 Session，请点击「淘宝授权」按钮完成 OAuth2 授权。"
    elif session_expired:
        note = "⚠️ Session 已过期，请点击「刷新 Session」或重新授权。"
    else:
        note = (
            f"API 已就绪（来源: {'数据库' if session_source == 'db' else '.env 文件'}）。"
            "商品搜索使用升级版物料搜索接口（taobao.tbk.dg.material.optional.upgrade）。"
        )

    return success_response(data={
        "configured": configured,
        "has_session": has_session and not session_expired,
        "session_expired": session_expired,
        "session_source": session_source,
        "has_redirect_uri": bool(redirect_uri),
        "app_key_prefix": (app_key[:4] + "****") if app_key else None,
        "note": note,
    })


@router.get("/config")
async def get_taobao_config(
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_admin),
):
    """获取当前 Session 配置（脱敏）"""
    row = _get_token_row(db)
    db_data = row.config_value if (row and isinstance(row.config_value, dict)) else {}
    session = (db_data.get("session") if db_data else None) or getattr(settings, "TAOBAO_SESSION", None)
    masked = (session[:6] + "****" + session[-4:]) if session and len(session) > 10 else ("****" if session else None)
    return success_response(data={
        "has_session": bool(session),
        "session_masked": masked,
        "session_source": "db" if (db_data.get("session") if db_data else None) else ("env" if session else None),
        "expires_at": db_data.get("expires_at") if db_data else None,
        "taobao_user_id": db_data.get("taobao_user_id") if db_data else None,
    })


@router.put("/config")
async def update_taobao_config(
    body: TaobaoSessionUpdateRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_admin),
):
    """手动更新 Session（备用，推荐使用 OAuth2 授权流程）"""
    _save_token_data(db, {"session": body.session, "source": "manual"})
    logger.info("淘宝联盟 Session 已通过管理后台手动更新")
    return success_response(data={"updated": True}, message="Session 已更新")


# ------------------------------------------------------------------
# OAuth2 授权流程
# ------------------------------------------------------------------

@router.get("/oauth/authorize")
async def taobao_oauth_authorize(
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_admin),
):
    """
    生成淘宝 OAuth2 授权 URL（管理员）。
    前端收到 URL 后用 window.open() 弹窗打开。
    """
    app_key = getattr(settings, "TAOBAO_APP_KEY", None)
    redirect_uri = getattr(settings, "TAOBAO_OAUTH_REDIRECT_URI", None)
    if not app_key:
        raise HTTPException(status_code=400, detail="TAOBAO_APP_KEY 未配置")
    if not redirect_uri:
        raise HTTPException(
            status_code=400,
            detail="TAOBAO_OAUTH_REDIRECT_URI 未配置，请在 .env 中设置回调地址（例如: https://shushang.online/api/v1/taobao/oauth/callback）",
        )

    state = secrets.token_urlsafe(16)
    _save_state(db, state)

    params = {
        "response_type": "code",
        "client_id": app_key,
        "redirect_uri": redirect_uri,
        "scope": "item",
        "state": state,
        "view": "web",
    }
    auth_url = f"{_TB_AUTH_URL}?{urlencode(params)}"
    return success_response(data={"auth_url": auth_url, "state": state})


@router.get("/oauth/callback")
async def taobao_oauth_callback(
    code: str = Query(...),
    state: str = Query(...),
    db: Session = Depends(get_db),
):
    """
    淘宝 OAuth2 回调端点（公开，由淘宝服务器回调）。
    用 code 换取 session + refresh_token，存入 DB。
    返回一个自动关闭的 HTML 页面通知前端弹窗。
    """
    # 验证 state 防 CSRF
    state_row = _get_state_row(db)
    saved_state = (state_row.config_value or {}).get("state") if state_row else None
    if not saved_state or saved_state != state:
        return HTMLResponse(_oauth_result_html(False, "state 验证失败，请重新授权"), status_code=400)

    app_key = getattr(settings, "TAOBAO_APP_KEY", None)
    app_secret = getattr(settings, "TAOBAO_APP_SECRET", None)
    redirect_uri = getattr(settings, "TAOBAO_OAUTH_REDIRECT_URI", None)
    if not app_key or not app_secret:
        return HTMLResponse(_oauth_result_html(False, "服务端 AppKey 未配置"), status_code=500)

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.post(_TB_TOKEN_URL, data={
                "grant_type": "authorization_code",
                "code": code,
                "client_id": app_key,
                "client_secret": app_secret,
                "redirect_uri": redirect_uri or "",
                "view": "web",
            })
            resp.raise_for_status()
            data = resp.json()
    except Exception as e:
        logger.error(f"淘宝 OAuth2 换取 session 失败: {e}")
        return HTMLResponse(_oauth_result_html(False, f"换取 session 失败: {e}"), status_code=502)

    # 淘宝返回格式: {"token_type":"Bearer","access_token":"...","expires_in":86400,
    #               "refresh_token":"...","refresh_token_timeout":"...","taobao_user_id":"..."}
    # 错误格式: {"error":"invalid_client","error_description":"..."}
    if "error" in data:
        err = data.get("error_description") or data.get("error") or str(data)
        logger.error(f"淘宝 OAuth2 响应错误: {data}")
        return HTMLResponse(_oauth_result_html(False, f"授权失败: {err}"), status_code=400)

    session = data.get("access_token") or data.get("session_key")
    if not session:
        logger.error(f"淘宝 OAuth2 响应无 access_token: {data}")
        return HTMLResponse(_oauth_result_html(False, "授权失败：响应中无 access_token"), status_code=400)

    expires_in = int(data.get("expires_in") or 86400)
    expires_at = (datetime.now(timezone.utc) + timedelta(seconds=expires_in)).isoformat()

    # refresh_token_timeout 是 ISO 格式字符串，直接存储
    _save_token_data(db, {
        "session": session,
        "refresh_token": data.get("refresh_token"),
        "expires_in": expires_in,
        "expires_at": expires_at,
        "refresh_token_timeout": data.get("refresh_token_timeout"),
        "taobao_user_id": data.get("taobao_user_id") or data.get("taobao_open_uid"),
        "source": "oauth2",
    })

    # 清理 state
    if state_row:
        db.delete(state_row)
        db.commit()

    logger.info(f"淘宝 OAuth2 授权成功，session 已存储，expires_at={expires_at}")
    return HTMLResponse(_oauth_result_html(True, "授权成功！此窗口将自动关闭。"))


@router.post("/oauth/refresh")
async def taobao_oauth_refresh(
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_admin),
):
    """使用 refresh_token 刷新 Session（管理员）"""
    row = _get_token_row(db)
    db_data = row.config_value if (row and isinstance(row.config_value, dict)) else {}
    refresh_token = db_data.get("refresh_token") if db_data else None
    if not refresh_token:
        raise HTTPException(status_code=400, detail="无可用的 refresh_token，请重新进行 OAuth2 授权")

    app_key = getattr(settings, "TAOBAO_APP_KEY", None)
    app_secret = getattr(settings, "TAOBAO_APP_SECRET", None)
    if not app_key or not app_secret:
        raise HTTPException(status_code=400, detail="TAOBAO_APP_KEY 未配置")

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.post(_TB_TOKEN_URL, data={
                "grant_type": "refresh_token",
                "refresh_token": refresh_token,
                "client_id": app_key,
                "client_secret": app_secret,
                "view": "web",
            })
            resp.raise_for_status()
            data = resp.json()
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"刷新 session 失败: {e}")

    if "error" in data:
        err = data.get("error_description") or data.get("error") or str(data)
        raise HTTPException(status_code=400, detail=f"刷新失败: {err}")

    new_session = data.get("access_token") or data.get("session_key")
    if not new_session:
        raise HTTPException(status_code=400, detail="刷新失败：响应中无 access_token")

    expires_in = int(data.get("expires_in") or 86400)
    expires_at = (datetime.now(timezone.utc) + timedelta(seconds=expires_in)).isoformat()

    _save_token_data(db, {
        **db_data,
        "session": new_session,
        "refresh_token": data.get("refresh_token") or refresh_token,
        "expires_in": expires_in,
        "expires_at": expires_at,
        "refresh_token_timeout": data.get("refresh_token_timeout") or db_data.get("refresh_token_timeout"),
        "source": "oauth2_refresh",
    })

    logger.info(f"淘宝联盟 Session 刷新成功，expires_at={expires_at}")
    return success_response(data={"refreshed": True, "expires_at": expires_at}, message="Session 刷新成功")


# ------------------------------------------------------------------
# 商品导入 / 搜索
# ------------------------------------------------------------------

@router.post("/import")
async def import_from_taobao(
    body: TaobaoImportRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_admin),
):
    """按关键词批量导入淘宝联盟商品（管理员）。任务在后台执行，立即返回。"""
    user_int_id = _get_user_int_id(current_user, db)
    keyword = body.keyword
    max_pages = body.max_pages
    page_size = body.page_size
    adzone_id = body.adzone_id

    def _run():
        bg_db = SessionLocal()
        try:
            service = TaobaoImportService(bg_db)
            result = asyncio.run(service.import_by_keyword(
                keyword=keyword,
                max_pages=max_pages,
                page_size=page_size,
                created_by_id=user_int_id,
                adzone_id=adzone_id,
            ))
            logger.info(f"淘宝联盟后台导入完成: {result}")
        except Exception as e:
            logger.error(f"淘宝联盟后台导入失败: {e}")
        finally:
            bg_db.close()

    background_tasks.add_task(_run)
    return success_response(
        data={"status": "accepted", "keyword": body.keyword},
        message=f"导入任务已提交，正在后台拉取「{body.keyword}」相关商品",
    )


@router.get("/search")
async def search_taobao_items(
    keyword: str = Query(..., min_length=1, max_length=100),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    adzone_id: Optional[str] = Query(default=None, max_length=64),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """实时搜索淘宝联盟商品（登录用户）。结果不写库，直接返回格式化数据。"""
    service = TaobaoImportService(db)
    try:
        result = await service.search_realtime(
            keyword=keyword,
            page=page,
            page_size=page_size,
            adzone_id=adzone_id,
        )
    except RuntimeError as e:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(e))
    except TaobaoApiError as e:
        no_permission = (
            "permission" in e.sub_code.lower()
            or "27" in e.code
            or "PERMISSION" in e.code
        )
        if no_permission:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="当前 AppKey 无商品搜索权限，请在淘宝联盟开放平台申请物料搜索接口权限",
            )
        detail = e.sub_msg or e.message or f"淘宝联盟 API 调用失败（错误码: {e.code}），请检查 AppKey 配置"
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=detail)

    return success_response(data=result)


# ------------------------------------------------------------------
# 工具函数
# ------------------------------------------------------------------

def _oauth_result_html(success: bool, message: str) -> str:
    """生成 OAuth2 回调结果页面，自动关闭弹窗并通知父窗口。"""
    icon = "✅" if success else "❌"
    color = "#67c23a" if success else "#f56c6c"
    event = "taobao_oauth_success" if success else "taobao_oauth_error"
    return f"""<!DOCTYPE html>
<html lang="zh">
<head>
  <meta charset="UTF-8">
  <title>淘宝授权{'成功' if success else '失败'}</title>
  <style>
    body {{ font-family: sans-serif; display: flex; align-items: center; justify-content: center;
           height: 100vh; margin: 0; background: #f5f7fa; }}
    .box {{ text-align: center; padding: 40px; background: #fff; border-radius: 12px;
            box-shadow: 0 2px 20px rgba(0,0,0,.1); max-width: 360px; }}
    .icon {{ font-size: 48px; margin-bottom: 16px; }}
    .msg {{ color: {color}; font-size: 16px; font-weight: 500; }}
    .hint {{ color: #909399; font-size: 13px; margin-top: 12px; }}
  </style>
</head>
<body>
  <div class="box">
    <div class="icon">{icon}</div>
    <div class="msg">{message}</div>
    <div class="hint">此窗口将在 2 秒后自动关闭</div>
  </div>
  <script>
    if (window.opener) {{
      window.opener.postMessage({{ type: '{event}' }}, '*');
    }}
    setTimeout(() => window.close(), 2000);
  </script>
</body>
</html>"""
