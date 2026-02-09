@echo off
REM 监控系统快速启动脚本 (Windows)

echo ==========================================
echo   支付系统监控告警系统 - 快速启动
echo ==========================================
echo.

REM 检查 Docker
docker --version >nul 2>&1
if errorlevel 1 (
    echo ❌ 错误: 未安装 Docker
    echo 请先安装 Docker Desktop: https://www.docker.com/products/docker-desktop
    pause
    exit /b 1
)

REM 检查 Docker Compose
docker-compose --version >nul 2>&1
if errorlevel 1 (
    echo ❌ 错误: 未安装 Docker Compose
    echo Docker Desktop 应该已包含 Docker Compose
    pause
    exit /b 1
)

echo ✅ Docker 环境检查通过
echo.

REM 创建必要的目录
echo 📁 创建数据目录...
if not exist "data\prometheus" mkdir data\prometheus
if not exist "data\grafana" mkdir data\grafana
if not exist "data\alertmanager" mkdir data\alertmanager

echo.
echo 🚀 启动监控服务...
docker-compose up -d

echo.
echo ⏳ 等待服务启动...
timeout /t 10 /nobreak >nul

REM 检查服务状态
echo.
echo 📊 检查服务状态...
docker-compose ps

echo.
echo ==========================================
echo   监控系统启动完成！
echo ==========================================
echo.
echo 访问地址:
echo   - Prometheus:    http://localhost:9090
echo   - Grafana:       http://localhost:3000
echo   - Alertmanager:  http://localhost:9093
echo.
echo Grafana 默认登录:
echo   用户名: admin
echo   密码:   admin123
echo.
echo 查看日志:
echo   docker-compose logs -f
echo.
echo 停止服务:
echo   docker-compose down
echo.
echo ==========================================
echo.
pause
