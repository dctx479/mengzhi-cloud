"""监控API端点"""
from fastapi import APIRouter, Depends, Response
from app.core.monitoring import performance_monitor
from app.core.alerts import alert_manager
from app.api.deps import require_admin
from typing import Dict, Any

router = APIRouter(tags=["监控"])

@router.get("/metrics")
async def get_metrics(current_user: dict = Depends(require_admin)):
    """获取Prometheus指标（需要管理员权限）"""
    metrics = performance_monitor.get_metrics()
    return Response(content=metrics, media_type="text/plain")

@router.get("/health")
async def health_check() -> Dict[str, Any]:
    """健康检查（公开端点，不含敏感信息）"""
    import psutil
    import os

    # 使用平台兼容的路径：Windows 使用 'C:\' (或其他盘符)，Unix 使用 '/'
    disk_path = 'C:\\' if os.name == 'nt' else '/'

    return {
        "status": "healthy",
        "cpu_usage": psutil.cpu_percent(),
        "memory_usage": psutil.virtual_memory().percent,
        "disk_usage": psutil.disk_usage(disk_path).percent
    }

@router.get("/slow-queries")
async def get_slow_queries(
    current_user: dict = Depends(require_admin)
) -> Dict[str, Any]:
    """获取慢查询列表（需要管理员权限）"""
    return {
        "slow_queries": performance_monitor.slow_queries[-50:]  # 最近50条
    }

@router.get("/alerts")
async def get_alerts(
    current_user: dict = Depends(require_admin)
) -> Dict[str, Any]:
    """获取告警历史（需要管理员权限）"""
    return {
        "alerts": alert_manager.alert_history[-100:]  # 最近100条
    }

@router.post("/test-alert")
async def test_alert(
    current_user: dict = Depends(require_admin)
) -> Dict[str, str]:
    """测试告警（需要管理员权限）"""
    from app.core.alerts import AlertLevel

    await alert_manager.send_alert(
        level=AlertLevel.INFO,
        title="测试告警",
        message="这是一条测试告警消息",
        extra={"test": True}
    )

    return {"message": "测试告警已发送"}
