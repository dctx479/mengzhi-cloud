"""
京东联盟商品导入 API

端点:
  GET  /api/v1/jd/status               查询 API 配置状态（管理员）
  GET  /api/v1/jd/config               获取当前 AccessToken 配置（管理员，脱敏）
  PUT  /api/v1/jd/config               手动更新 AccessToken（管理员，备用）
  GET  /api/v1/jd/oauth/authorize      生成京东 OAuth2 授权 URL（管理员）
  GET  /api/v1/jd/oauth/callback       接收京东回调，用 code 换 token（公开，京东回调）
  POST /api/v1/jd/oauth/refresh        刷新 AccessToken（管理员）
  POST /api/v1/jd/import               批量导入（管理员）
  GET  /api/v1/jd/search               实时搜索代理（登录用户）

OAuth2 流程:
  1. 管理员点「授权」→ 前端调 /oauth/authorize 获取授权 URL
  2. 前端弹窗打开授权 URL（京东登录页）
  3. 用户授权后京东回调 /oauth/callback?code=xxx&state=xxx
  4. 后端用 code 换 access_token + refresh_token，存入 system_configs
  5. 前端轮询 /status 检测 has_access_token 变为 true
"""

import asyncio
import secrets
from datetime import datetime, timezone, timedelta
from typing import Optional

import httpx
from fastapi import APIRouter, Depends, Query, HTTPException, status, BackgroundTasks
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from loguru import logger

from app.api.deps import get_db, require_admin, get_current_user
from app.core.responses import success_response
from app.core.database import SessionLocal
from app.models.user import User
from app.models.system_config import SystemConfig
from app.services.jd_import_service import JdImportService, _client_instance_reset
from app.services.jd_api_client import JdApiError
from app.core.config import settings

router = APIRouter(prefix="/jd", tags=["京东联盟导入 - JD Import"])

# system_configs 键名
_JD_TOKEN_KEY = "jd_access_token"       # {"access_token", "refresh_token", "expires_at", "uid"}
_JD_OAUTH_STATE_KEY = "jd_oauth_state"  # CSRF state 临时存储

# 京东 OAuth2 端点
_JD_AUTH_URL = "https://open.jd.com/oauth2/to_login"
_JD_TOKEN_URL = "https://open-oauth.jd.com/oauth2/access_token"
_JD_REFRESH_URL = "https://open-oauth.jd.com/oauth2/refresh_token"


# ------------------------------------------------------------------
# 内部工具
# ------------------------------------------------------------------

def _get_token_row(db: Session) -> Optional[SystemConfig]:
    return db.query(SystemConfig).filter(SystemConfig.config_key == _JD_TOKEN_KEY).first()


def _get_access_token(db: Session) -> Optional[str]:
    """DB 优先，其次 .env"""
    row = _get_token_row(db)
    if row and isinstance(row.config_value, dict):
        return row.config_value.get("access_token") or None
    env_token = getattr(settings, "JD_ACCESS_TOKEN", None)
    return env_token or None


def _save_token_data(db: Session, data: dict) -> None:
    """将 token 数据写入 system_configs，并重置客户端单例。"""
    row = _get_token_row(db)
    if row:
        row.config_value = data
    else:
        row = SystemConfig(
            config_key=_JD_TOKEN_KEY,
            config_value=data,
            description="京东联盟 OAuth2 AccessToken（自动管理）",
        )
        db.add(row)
    db.commit()
    _client_instance_reset()


def _get_state_row(db: Session) -> Optional[SystemConfig]:
    return db.query(SystemConfig).filter(SystemConfig.config_key == _JD_OAUTH_STATE_KEY).first()


def _save_state(db: Session, state: str) -> None:
    row = _get_state_row(db)
    if row:
        row.config_value = {"state": state}
    else:
        db.add(SystemConfig(
            config_key=_JD_OAUTH_STATE_KEY,
            config_value={"state": state},
            description="京东 OAuth2 CSRF state（临时）",
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

class ImportRequest(BaseModel):
    keyword: str = Field(..., min_length=1, max_length=100)
    max_pages: int = Field(default=3, ge=1, le=10)
    page_size: int = Field(default=30, ge=1, le=30)


class JdConfigUpdateRequest(BaseModel):
    access_token: str = Field(..., min_length=1, max_length=512)


# ------------------------------------------------------------------
# 路由
# ------------------------------------------------------------------

@router.get("/status")
async def get_jd_status(
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_admin),
):
    """查询京东联盟 API 配置状态（管理员）"""
    app_key = getattr(settings, "JD_APP_KEY", None)
    secret_key = getattr(settings, "JD_SECRET_KEY", None)
    configured = bool(app_key and secret_key)

    row = _get_token_row(db)
    db_data = row.config_value if (row and isinstance(row.config_value, dict)) else {}
    db_token = db_data.get("access_token") if db_data else None
    env_token = getattr(settings, "JD_ACCESS_TOKEN", None)
    access_token = db_token or env_token
    has_token = bool(access_token)
    token_source = "db" if db_token else ("env" if env_token else None)

    # 过期时间
    expires_at = db_data.get("expires_at") if db_data else None
    token_expired = False
    if expires_at:
        try:
            exp_dt = datetime.fromisoformat(expires_at)
            token_expired = datetime.now(timezone.utc) >= exp_dt
        except Exception:
            pass

    redirect_uri = getattr(settings, "JD_OAUTH_REDIRECT_URI", None)

    if not configured:
        note = None
    elif not has_token:
        note = "⚠️ 未获取 AccessToken，请点击「京东授权」按钮完成 OAuth2 授权。"
    elif token_expired:
        note = "⚠️ AccessToken 已过期，请点击「刷新 Token」或重新授权。"
    else:
        note = f"API 已就绪（来源: {'数据库' if token_source == 'db' else '.env 文件'}）。商品搜索需在京东联盟后台申请「商品查询」高级接口权限。"

    return success_response(data={
        "configured": configured,
        "has_access_token": has_token and not token_expired,
        "token_expired": token_expired,
        "token_source": token_source,
        "has_redirect_uri": bool(redirect_uri),
        "app_key_prefix": (app_key[:4] + "****") if app_key else None,
        "note": note,
    })


@router.get("/config")
async def get_jd_config(
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_admin),
):
    """获取当前 AccessToken 配置（脱敏）"""
    row = _get_token_row(db)
    db_data = row.config_value if (row and isinstance(row.config_value, dict)) else {}
    token = db_data.get("access_token") if db_data else None
    if not token:
        token = getattr(settings, "JD_ACCESS_TOKEN", None)
    masked = (token[:6] + "****" + token[-4:]) if token and len(token) > 10 else ("****" if token else None)
    return success_response(data={
        "has_token": bool(token),
        "token_masked": masked,
        "token_source": "db" if (db_data.get("access_token") if db_data else None) else ("env" if token else None),
        "expires_at": db_data.get("expires_at") if db_data else None,
        "uid": db_data.get("uid") if db_data else None,
    })


@router.put("/config")
async def update_jd_config(
    body: JdConfigUpdateRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_admin),
):
    """手动更新 AccessToken（备用，推荐使用 OAuth2 授权流程）"""
    _save_token_data(db, {"access_token": body.access_token, "source": "manual"})
    logger.info("JD AccessToken 已通过管理后台手动更新")
    return success_response(data={"updated": True}, message="AccessToken 已更新")


# ------------------------------------------------------------------
# OAuth2 授权流程
# ------------------------------------------------------------------

@router.get("/oauth/authorize")
async def jd_oauth_authorize(
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_admin),
):
    """
    生成京东 OAuth2 授权 URL（管理员）。
    前端收到 URL 后用 window.open() 弹窗打开。
    """
    app_key = getattr(settings, "JD_APP_KEY", None)
    redirect_uri = getattr(settings, "JD_OAUTH_REDIRECT_URI", None)
    if not app_key:
        raise HTTPException(status_code=400, detail="JD_APP_KEY 未配置")
    if not redirect_uri:
        raise HTTPException(status_code=400, detail="JD_OAUTH_REDIRECT_URI 未配置，请在 .env 中设置回调地址")

    state = secrets.token_urlsafe(16)
    _save_state(db, state)

    from urllib.parse import urlencode
    params = {
        "app_key": app_key,
        "redirect_uri": redirect_uri,
        "response_type": "code",
        "scope": "snsapi_base",
        "state": state,
    }
    auth_url = f"{_JD_AUTH_URL}?{urlencode(params)}"
    return success_response(data={"auth_url": auth_url, "state": state})


@router.get("/oauth/callback")
async def jd_oauth_callback(
    code: str = Query(...),
    state: str = Query(...),
    db: Session = Depends(get_db),
):
    """
    京东 OAuth2 回调端点（公开，由京东服务器回调）。
    用 code 换取 access_token + refresh_token，存入 DB。
    返回一个自动关闭的 HTML 页面通知前端弹窗。
    """
    # 验证 state 防 CSRF
    state_row = _get_state_row(db)
    saved_state = (state_row.config_value or {}).get("state") if state_row else None
    if not saved_state or saved_state != state:
        return HTMLResponse(_oauth_result_html(False, "state 验证失败，请重新授权"), status_code=400)

    app_key = getattr(settings, "JD_APP_KEY", None)
    secret_key = getattr(settings, "JD_SECRET_KEY", None)
    redirect_uri = getattr(settings, "JD_OAUTH_REDIRECT_URI", None)
    if not app_key or not secret_key:
        return HTMLResponse(_oauth_result_html(False, "服务端 AppKey 未配置"), status_code=500)

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.get(_JD_TOKEN_URL, params={
                "app_key": app_key,
                "app_secret": secret_key,
                "grant_type": "authorization_code",
                "code": code,
                "redirect_uri": redirect_uri or "",
            })
            resp.raise_for_status()
            data = resp.json()
    except Exception as e:
        logger.error(f"JD OAuth2 换取 token 失败: {e}")
        return HTMLResponse(_oauth_result_html(False, f"换取 token 失败: {e}"), status_code=502)

    access_token = data.get("access_token")
    if not access_token:
        err = data.get("error_description") or data.get("error") or str(data)
        logger.error(f"JD OAuth2 响应无 access_token: {data}")
        return HTMLResponse(_oauth_result_html(False, f"授权失败: {err}"), status_code=400)

    expires_in = int(data.get("expires_in") or 2592000)  # 默认30天
    expires_at = (datetime.now(timezone.utc) + timedelta(seconds=expires_in)).isoformat()

    _save_token_data(db, {
        "access_token": access_token,
        "refresh_token": data.get("refresh_token"),
        "expires_in": expires_in,
        "expires_at": expires_at,
        "uid": data.get("uid") or data.get("open_id"),
        "source": "oauth2",
    })

    # 清理 state
    if state_row:
        db.delete(state_row)
        db.commit()

    logger.info(f"JD OAuth2 授权成功，token 已存储，expires_at={expires_at}")
    return HTMLResponse(_oauth_result_html(True, "授权成功！此窗口将自动关闭。"))


@router.post("/oauth/refresh")
async def jd_oauth_refresh(
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_admin),
):
    """使用 refresh_token 刷新 AccessToken（管理员）"""
    row = _get_token_row(db)
    db_data = row.config_value if (row and isinstance(row.config_value, dict)) else {}
    refresh_token = db_data.get("refresh_token") if db_data else None
    if not refresh_token:
        raise HTTPException(status_code=400, detail="无可用的 refresh_token，请重新进行 OAuth2 授权")

    app_key = getattr(settings, "JD_APP_KEY", None)
    secret_key = getattr(settings, "JD_SECRET_KEY", None)
    if not app_key or not secret_key:
        raise HTTPException(status_code=400, detail="JD_APP_KEY 未配置")

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.get(_JD_REFRESH_URL, params={
                "app_key": app_key,
                "app_secret": secret_key,
                "grant_type": "refresh_token",
                "refresh_token": refresh_token,
            })
            resp.raise_for_status()
            data = resp.json()
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"刷新 token 失败: {e}")

    new_token = data.get("access_token")
    if not new_token:
        err = data.get("error_description") or data.get("error") or str(data)
        raise HTTPException(status_code=400, detail=f"刷新失败: {err}")

    expires_in = int(data.get("expires_in") or 2592000)
    expires_at = (datetime.now(timezone.utc) + timedelta(seconds=expires_in)).isoformat()

    _save_token_data(db, {
        **db_data,
        "access_token": new_token,
        "refresh_token": data.get("refresh_token") or refresh_token,
        "expires_in": expires_in,
        "expires_at": expires_at,
        "source": "oauth2_refresh",
    })

    logger.info(f"JD AccessToken 刷新成功，expires_at={expires_at}")
    return success_response(data={"refreshed": True, "expires_at": expires_at}, message="Token 刷新成功")


# ------------------------------------------------------------------
# 商品导入 / 搜索
# ------------------------------------------------------------------

@router.post("/import")
async def import_from_jd(
    body: ImportRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_admin),
):
    """按关键词批量导入京东商品（管理员）。任务在后台执行，立即返回。"""
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
    """实时搜索京东商品（登录用户）。结果不写库，直接返回格式化数据。"""
    service = JdImportService(db)
    try:
        result = await service.search_realtime(keyword=keyword, page=page, page_size=page_size)
    except RuntimeError as e:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(e))
    except JdApiError as e:
        no_permission = (
            e.code in ("403", "50030", "50200")
            or "无访问权限" in str(e.message)
            or "permission" in str(e.message).lower()
        )
        if no_permission:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="当前AppKey无商品搜索权限，请在京东联盟后台申请「商品查询」高级接口权限",
            )
        detail = e.message if e.message and e.message not in ("unknown", "API error") else f"京东API调用失败（错误码: {e.code}），请检查AppKey配置"
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=detail)

    return success_response(data=result)


# ------------------------------------------------------------------
# 工具函数
# ------------------------------------------------------------------

def _oauth_result_html(success: bool, message: str) -> str:
    """生成 OAuth2 回调结果页面，自动关闭弹窗并通知父窗口。"""
    icon = "✅" if success else "❌"
    color = "#67c23a" if success else "#f56c6c"
    event = "jd_oauth_success" if success else "jd_oauth_error"
    return f"""<!DOCTYPE html>
<html lang="zh">
<head>
  <meta charset="UTF-8">
  <title>京东授权{'成功' if success else '失败'}</title>
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
