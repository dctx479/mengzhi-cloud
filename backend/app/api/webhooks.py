"""
Alertmanager Webhook接收器

接收来自Alertmanager的告警通知并处理。

示例Webhook URL:
- /api/v1/webhooks/alerts
- /api/v1/webhooks/critical-alerts
- /api/v1/webhooks/warning-alerts
- /api/v1/webhooks/info-alerts
"""

from fastapi import APIRouter, Request, HTTPException, Depends
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from typing import Dict, Any, List
from datetime import datetime
import logging
import secrets

router = APIRouter(prefix="/api/v1/webhooks", tags=["Webhooks"])
security = HTTPBasic()

# 配置日志
logger = logging.getLogger(__name__)


def verify_alertmanager_auth(credentials: HTTPBasicCredentials = Depends(security)):
    """验证Alertmanager的HTTP Basic Auth"""
    import os
    correct_username = os.getenv("ALERTMANAGER_WEBHOOK_USER", "alertmanager")
    correct_password = os.getenv("ALERTMANAGER_WEBHOOK_SECRET", "changeme")

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
        # 验证Content-Type
        if request.headers.get("content-type") and "application/json" not in request.headers.get("content-type", ""):
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
            process_alert(alert)

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
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/critical-alerts")
async def receive_critical_alerts(
    request: Request,
    credentials: HTTPBasicCredentials = Depends(verify_alertmanager_auth)
):
    """接收严重告警"""
    try:
        # 验证Content-Type
        if request.headers.get("content-type") and "application/json" not in request.headers.get("content-type", ""):
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
            process_critical_alert(alert)

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
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/warning-alerts")
async def receive_warning_alerts(
    request: Request,
    credentials: HTTPBasicCredentials = Depends(verify_alertmanager_auth)
):
    """接收警告告警"""
    try:
        # 验证Content-Type
        if request.headers.get("content-type") and "application/json" not in request.headers.get("content-type", ""):
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
            process_warning_alert(alert)

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
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/info-alerts")
async def receive_info_alerts(
    request: Request,
    credentials: HTTPBasicCredentials = Depends(verify_alertmanager_auth)
):
    """接收信息告警"""
    try:
        # 验证Content-Type
        if request.headers.get("content-type") and "application/json" not in request.headers.get("content-type", ""):
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
            process_info_alert(alert)

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
        raise HTTPException(status_code=500, detail=str(e))


# ==================== 告警处理函数 ====================

def process_alert(alert: Dict[str, Any]):
    """
    处理通用告警

    参数:
        alert: 告警数据字典
    """
    alert_name = alert.get("labels", {}).get("alertname", "Unknown")
    severity = alert.get("labels", {}).get("severity", "unknown")
    status = alert.get("status", "unknown")
    summary = alert.get("annotations", {}).get("summary", "")
    description = alert.get("annotations", {}).get("description", "")

    logger.info(
        f"Processing alert: {alert_name}",
        extra={
            "alertname": alert_name,
            "severity": severity,
            "status": status,
            "summary": summary,
            "description": description
        }
    )

    # TODO: 实现具体的告警处理逻辑
    # - 保存到数据库
    # - 发送通知（邮件、短信、微信等）
    # - 触发自动化响应
    # - 更新监控仪表盘


def process_critical_alert(alert: Dict[str, Any]):
    """
    处理严重告警

    严重告警需要：
    - 立即通知管理员
    - 触发应急响应流程
    - 记录到事故管理系统
    """
    alert_name = alert.get("labels", {}).get("alertname", "Unknown")
    description = alert.get("annotations", {}).get("description", "")

    logger.critical(
        f"CRITICAL ALERT: {alert_name} - {description}",
        extra={"alert": alert}
    )

    # TODO: 实现严重告警处理逻辑
    # - 发送紧急通知（电话、短信）
    # - 创建事故工单
    # - 触发自动恢复脚本（如果有）
    # - 通知值班人员


def process_warning_alert(alert: Dict[str, Any]):
    """
    处理警告告警

    警告告警需要：
    - 记录到日志
    - 发送通知
    - 监控趋势
    """
    alert_name = alert.get("labels", {}).get("alertname", "Unknown")
    description = alert.get("annotations", {}).get("description", "")

    logger.warning(
        f"WARNING ALERT: {alert_name} - {description}",
        extra={"alert": alert}
    )

    # TODO: 实现警告告警处理逻辑
    # - 发送通知到告警频道
    # - 更新监控仪表盘
    # - 记录到告警历史


def process_info_alert(alert: Dict[str, Any]):
    """
    处理信息告警

    信息告警需要：
    - 记录到日志
    - 更新统计信息
    """
    alert_name = alert.get("labels", {}).get("alertname", "Unknown")
    description = alert.get("annotations", {}).get("description", "")

    logger.info(
        f"INFO ALERT: {alert_name} - {description}",
        extra={"alert": alert}
    )

    # TODO: 实现信息告警处理逻辑
    # - 更新监控仪表盘
    # - 记录到日志系统


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
