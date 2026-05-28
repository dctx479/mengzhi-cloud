"""
淘宝联盟 Session 自动刷新任务

淘宝 access_token 有效期仅 1 天，refresh_token 有效期约 30 天。
本任务每 20 小时检查一次，若 session 将在 4 小时内过期则自动刷新。
"""

from datetime import datetime, timezone, timedelta
from loguru import logger

import httpx

_TB_TOKEN_URL = "https://oauth.taobao.com/token"
_REFRESH_THRESHOLD_HOURS = 4  # 距过期不足 4 小时时触发刷新


async def refresh_taobao_session_if_needed() -> None:
    """
    检查淘宝联盟 session 是否即将过期，若是则自动刷新。
    从 system_configs 读取 token 数据，刷新后写回。
    """
    from app.core.database import SessionLocal
    from app.models.system_config import SystemConfig
    from app.services.taobao_import_service import _client_instance_reset
    from app.core.config import settings

    db = SessionLocal()
    try:
        row = db.query(SystemConfig).filter(SystemConfig.config_key == "taobao_session").first()
        if not row or not isinstance(row.config_value, dict):
            logger.debug("淘宝 session 未存储在 DB，跳过自动刷新")
            return

        data = row.config_value
        session = data.get("session")
        refresh_token = data.get("refresh_token")
        expires_at_str = data.get("expires_at")

        if not session or not refresh_token:
            logger.debug("淘宝 session 或 refresh_token 缺失，跳过自动刷新")
            return

        # 检查是否需要刷新
        if expires_at_str:
            try:
                expires_at = datetime.fromisoformat(expires_at_str)
                time_left = expires_at - datetime.now(timezone.utc)
                if time_left > timedelta(hours=_REFRESH_THRESHOLD_HOURS):
                    logger.debug(f"淘宝 session 仍有 {time_left} 有效，无需刷新")
                    return
                logger.info(f"淘宝 session 将在 {time_left} 后过期，开始自动刷新")
            except Exception:
                logger.warning("淘宝 session expires_at 格式异常，强制刷新")

        app_key = getattr(settings, "TAOBAO_APP_KEY", None)
        app_secret = getattr(settings, "TAOBAO_APP_SECRET", None)
        if not app_key or not app_secret:
            logger.warning("TAOBAO_APP_KEY/APP_SECRET 未配置，无法自动刷新")
            return

        # 检查 refresh_token 是否过期
        rt_timeout_str = data.get("refresh_token_timeout")
        if rt_timeout_str:
            try:
                rt_timeout = datetime.fromisoformat(rt_timeout_str)
                if datetime.now(timezone.utc) >= rt_timeout:
                    logger.error("淘宝 refresh_token 已过期，需要重新 OAuth2 授权")
                    return
            except Exception:
                pass

        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.post(_TB_TOKEN_URL, data={
                "grant_type": "refresh_token",
                "refresh_token": refresh_token,
                "client_id": app_key,
                "client_secret": app_secret,
                "view": "web",
            })
            resp.raise_for_status()
            result = resp.json()

        if "error" in result:
            err = result.get("error_description") or result.get("error")
            logger.error(f"淘宝 session 自动刷新失败: {err}")
            return

        new_session = result.get("access_token") or result.get("session_key")
        if not new_session:
            logger.error("淘宝 session 自动刷新响应无 access_token")
            return

        expires_in = int(result.get("expires_in") or 86400)
        new_expires_at = (datetime.now(timezone.utc) + timedelta(seconds=expires_in)).isoformat()

        row.config_value = {
            **data,
            "session": new_session,
            "refresh_token": result.get("refresh_token") or refresh_token,
            "expires_in": expires_in,
            "expires_at": new_expires_at,
            "refresh_token_timeout": result.get("refresh_token_timeout") or data.get("refresh_token_timeout"),
            "source": "auto_refresh",
        }
        db.commit()
        _client_instance_reset()
        logger.info(f"淘宝 session 自动刷新成功，新过期时间: {new_expires_at}")

    except Exception as e:
        logger.error(f"淘宝 session 自动刷新异常: {e}")
    finally:
        db.close()
