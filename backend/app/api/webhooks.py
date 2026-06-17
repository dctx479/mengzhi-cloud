"""
Alertmanager Webhook接收器

接收来自Alertmanager的告警通知并处理。

示例Webhook URL:
- /api/v1/webhooks/alerts
- /api/v1/webhooks/critical-alerts
- /api/v1/webhooks/warning-alerts
- /api/v1/webhooks/info-alerts
"""

import os
import logging
import secrets
from datetime import datetime
from typing import Dict, Any, List

from fastapi import APIRouter, Request, HTTPException, Depends
from fastapi.security import HTTPBasic, HTTPBasicCredentials

from app.core.alerts import alert_manager

router = APIRouter(prefix="/api/v1/webhooks", tags=["Webhooks"])
security = HTTPBasic()

# 配置日志
logger = logging.getLogger(__name__)


# Severity → level 映射
_SEVERITY_LEVEL_MAP = {
    "critical": "critical",
    "high": "error",
    "warning": "warning",
    "info": "info",
    "low": "info",
}


async def _dispatch_to_alert_manager(alert: Dict[str, Any], severity: str) -> None:
    """统一的告警分发入口: 委托给 alert_manager"""
    alert_name = alert.get("labels", {}).get("alertname", "Unknown")
    summary = alert.get("annotations", {}).get("summary", "")
    description = alert.get("annotations", {}).get("description", "")
    level = _SEVERITY_LEVEL_MAP.get(severity, "warning")

    title = f"[{severity.upper()}] {alert_name}"
    message_parts = [f"Alertmanager 告警: {alert_name}"]
    if summary:
        message_parts.append(f"摘要: {summary}")
    if description:
        message_parts.append(f"描述: {description}")
    message_parts.append(f"原始状态: {alert.get('status', 'unknown')}")
    message_parts.append(f"时间: {datetime.utcnow().isoformat()}Z")

    extra = {
        "source": "alertmanager",
        "severity": severity,
        "alert_labels": alert.get("labels", {}),
    }

    try:
        results = await alert_manager.send_alert(
            level=level,
            title=title,
            message="\n".join(message_parts),
            extra=extra,
        )
        logger.info(
            f"Alertmanager webhook dispatched: {alert_name}, "
            f"channels={list(results.keys())}, success={sum(1 for v in results.values() if v)}"
        )
    except Exception as e:
        logger.error(f"⚠️ WARNING: alert_manager.send_alert failed: {e}", exc_info=True)


def verify_alertmanager_auth(credentials: HTTPBasicCredentials = Depends(security)):
    """验证Alertmanager的HTTP Basic Auth"""
    correct_username = os.getenv("ALERTMANAGER_WEBHOOK_USER", "alertmanager")
    correct_password = os.getenv("ALERTMANAGER_WEBHOOK_SECRET", "changeme")

    # 生产环境默认密码告警
    if correct_password == "changeme":
        logger.warning(
            "⚠️ WARNING: ALERTMANAGER_WEBHOOK_SECRET is using the default value 'changeme'. "
            "Set this environment variable to a strong secret in production."
        )

    # 使用 secrets.compare_digest() 防止timing attack
    username_match = secrets.compare_digest(
        credentials.username.encode(), correct_username.encode()
    )
    password_match = secrets.compare_digest(
        credentials.password.encode(), correct_password.encode()
    )

    if not (username_match and password_match):
        raise HTTPException(
            status_code=401,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Basic"},
        )
    return credentials


@router.post("/alerts")
async def receive_alerts(
    request: Request,
    credentials: HTTPBasicCredentials = Depends(verify_alertmanager_auth)
):
    """
    接收所有级别的告警

    Alertmanager会POST JSON格式的告警数据:
    {
        "receiver": "default",
        "status": "firing",
        "alerts": [
            {
                "status": "firing",
                "labels": {
                    "alertname": "HighCPUUsage",
                    "severity": "warning",
                    "instance": "localhost:9090"
                },
                "annotations": {
                    "summary": "CPU使用率过高",
                    "description": "CPU使用率已超过80%"
                },
                "startsAt": "2026-01-23T12:00:00Z",
                "endsAt": "0001-01-01T00:00:00Z",
                "generatorURL": "http://prometheus:9090/graph?..."
            }
        ],
        "groupLabels": {},
        "commonLabels": {},
        "commonAnnotations": {},
        "externalURL": "http://alertmanager:9093",
        "version": "4",
        "groupKey": "{}:{}"
    }
    """
    try:
        # 验证Content-Type必须为application/json
        content_type = request.headers.get("content-type", "")
        if "application/json" not in content_type:
            raise HTTPException(
                status_code=400,
                detail="Content-Type must be application/json"
            )

        alert_data = await request.json()

        # 解析告警数据
        receiver = alert_data.get("receiver", "unknown")
        status = alert_data.get("status", "unknown")
        alerts = alert_data.get("alerts", [])

        logger.info(
            f"Received {len(alerts)} alert(s) from Alertmanager",
            extra={
                "receiver": receiver,
                "status": status,
                "alert_count": len(alerts)
            }
        )

        # 处理每个告警
        for alert in alerts:
            await process_alert(alert)

        return {
            "status": "success",
            "message": f"Processed {len(alerts)} alert(s)",
            "received_at": datetime.utcnow().isoformat()
        }

    except HTTPException:
        raise
    except ValueError as e:
        logger.error(f"Invalid JSON in request: {str(e)}")
        raise HTTPException(status_code=400, detail="Invalid JSON format")
    except Exception as e:
        logger.error(f"Error processing alerts: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/critical-alerts")
async def receive_critical_alerts(
    request: Request,
    credentials: HTTPBasicCredentials = Depends(verify_alertmanager_auth)
):
    """接收严重告警"""
    try:
        # 验证Content-Type必须为application/json
        content_type = request.headers.get("content-type", "")
        if "application/json" not in content_type:
            raise HTTPException(
                status_code=400,
                detail="Content-Type must be application/json"
            )

        alert_data = await request.json()
        alerts = alert_data.get("alerts", [])

        logger.critical(
            f"CRITICAL: Received {len(alerts)} critical alert(s)",
            extra={"alert_count": len(alerts)}
        )

        # 处理严重告警 - 可能需要立即通知管理员
        for alert in alerts:
            await process_critical_alert(alert)

        return {
            "status": "success",
            "severity": "critical",
            "message": f"Processed {len(alerts)} critical alert(s)"
        }

    except HTTPException:
        raise
    except ValueError as e:
        logger.error(f"Invalid JSON in request: {str(e)}")
        raise HTTPException(status_code=400, detail="Invalid JSON format")
    except Exception as e:
        logger.error(f"Error processing critical alerts: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/warning-alerts")
async def receive_warning_alerts(
    request: Request,
    credentials: HTTPBasicCredentials = Depends(verify_alertmanager_auth)
):
    """接收警告告警"""
    try:
        # 验证Content-Type必须为application/json
        content_type = request.headers.get("content-type", "")
        if "application/json" not in content_type:
            raise HTTPException(
                status_code=400,
                detail="Content-Type must be application/json"
            )

        alert_data = await request.json()
        alerts = alert_data.get("alerts", [])

        logger.warning(
            f"WARNING: Received {len(alerts)} warning alert(s)",
            extra={"alert_count": len(alerts)}
        )

        # 处理警告告警
        for alert in alerts:
            await process_warning_alert(alert)

        return {
            "status": "success",
            "severity": "warning",
            "message": f"Processed {len(alerts)} warning alert(s)"
        }

    except HTTPException:
        raise
    except ValueError as e:
        logger.error(f"Invalid JSON in request: {str(e)}")
        raise HTTPException(status_code=400, detail="Invalid JSON format")
    except Exception as e:
        logger.error(f"Error processing warning alerts: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/info-alerts")
async def receive_info_alerts(
    request: Request,
    credentials: HTTPBasicCredentials = Depends(verify_alertmanager_auth)
):
    """接收信息告警"""
    try:
        # 验证Content-Type必须为application/json
        content_type = request.headers.get("content-type", "")
        if "application/json" not in content_type:
            raise HTTPException(
                status_code=400,
                detail="Content-Type must be application/json"
            )

        alert_data = await request.json()
        alerts = alert_data.get("alerts", [])

        logger.info(
            f"INFO: Received {len(alerts)} info alert(s)",
            extra={"alert_count": len(alerts)}
        )

        # 处理信息告警
        for alert in alerts:
            await process_info_alert(alert)

        return {
            "status": "success",
            "severity": "info",
            "message": f"Processed {len(alerts)} info alert(s)"
        }

    except HTTPException:
        raise
    except ValueError as e:
        logger.error(f"Invalid JSON in request: {str(e)}")
        raise HTTPException(status_code=400, detail="Invalid JSON format")
    except Exception as e:
        logger.error(f"Error processing info alerts: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


# ==================== 告警处理函数 ====================

async def process_alert(alert: Dict[str, Any]):
    """
    处理通用告警 (委托给统一 alert_manager)
    """
    severity = alert.get("labels", {}).get("severity", "warning")
    await _dispatch_to_alert_manager(alert, severity)


async def process_critical_alert(alert: Dict[str, Any]):
    """
    处理严重告警 (委托给统一 alert_manager, 强制 critical)
    """
    await _dispatch_to_alert_manager(alert, "critical")


async def process_warning_alert(alert: Dict[str, Any]):
    """
    处理警告告警 (委托给统一 alert_manager)
    """
    await _dispatch_to_alert_manager(alert, "warning")


async def process_info_alert(alert: Dict[str, Any]):
    """
    处理信息告警 (委托给统一 alert_manager)
    """
    await _dispatch_to_alert_manager(alert, "info")


# ==================== 集成说明 ====================
"""
将这个router添加到main.py:

from app.api.webhooks import router as webhook_router
app.include_router(webhook_router)

测试Webhook:
curl -X POST http://localhost:8000/api/v1/webhooks/alerts \
  -u alertmanager:alertmanager_webhook_secret \
  -H "Content-Type: application/json" \
  -d '{
    "receiver": "default",
    "status": "firing",
    "alerts": [{
      "status": "firing",
      "labels": {
        "alertname": "TestAlert",
        "severity": "warning"
      },
      "annotations": {
        "summary": "Test alert",
        "description": "This is a test alert"
      }
    }]
  }'
"""
