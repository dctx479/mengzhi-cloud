@echo off
REM Docker环境重建脚本 (Windows)
REM 用途: 清理并重建完整的Docker环境（应用+监控+日志）

setlocal enabledelayedexpansion

echo ==========================================
echo Docker环境重建脚本 (Windows)
echo ==========================================
echo.

cd /d "%~dp0\.."
echo 当前目录: %CD%
echo.

REM Step 1: 停止所有容器
echo [INFO] Step 1/6: 停止所有运行中的容器...
docker-compose -f docker-compose.yml down >nul 2>&1
docker-compose -f docker-compose.monitoring.yml down >nul 2>&1
docker-compose -f docker-compose.test.yml down >nul 2>&1
echo [INFO] √ 容器已停止
echo.

REM Step 2: 清理孤儿容器和网络
echo [INFO] Step 2/6: 清理孤儿容器和未使用的网络...
docker-compose -f docker-compose.yml down --remove-orphans >nul 2>&1
docker-compose -f docker-compose.monitoring.yml down --remove-orphans >nul 2>&1
docker network prune -f >nul 2>&1
echo [INFO] √ 清理完成
echo.

REM Step 3: 询问是否清理数据卷
set /p "cleanup=是否清理数据卷？(将删除所有数据库和日志数据) [y/N]: "
if /i "%cleanup%"=="y" (
    echo [WARN] 清理数据卷中...
    docker volume rm backend_mysql_data 2>nul
    docker volume rm backend_redis_data 2>nul
    docker volume rm backend_es_data 2>nul
    docker volume rm backend_prometheus_data 2>nul
    docker volume rm backend_grafana_data 2>nul
    echo [INFO] √ 数据卷已清理
) else (
    echo [INFO] 保留现有数据卷
)
echo.

REM Step 4: 重建镜像
echo [INFO] Step 3/6: 重建Docker镜像（强制无缓存构建）...
docker-compose -f docker-compose.yml build --no-cache backend
docker-compose -f docker-compose.test.yml build --no-cache test-runner 2>nul
echo [INFO] √ 镜像构建完成
echo.

REM Step 5: 拉取最新的第三方镜像
echo [INFO] Step 4/6: 拉取最新的第三方镜像...
docker-compose -f docker-compose.yml pull mysql redis nginx 2>nul
docker-compose -f docker-compose.monitoring.yml pull 2>nul
echo [INFO] √ 镜像拉取完成
echo.

REM Step 6: 启动应用服务
echo [INFO] Step 5/6: 启动应用服务...
docker-compose -f docker-compose.yml up -d
echo [INFO] 等待服务健康检查...
timeout /t 10 /nobreak >nul

echo [INFO] 检查服务状态:
docker-compose -f docker-compose.yml ps
echo.

REM Step 7: 启动监控服务
echo [INFO] Step 6/6: 启动监控和日志服务...
docker-compose -f docker-compose.monitoring.yml up -d
echo [INFO] 等待监控服务启动...
timeout /t 15 /nobreak >nul

echo [INFO] 检查监控服务状态:
docker-compose -f docker-compose.monitoring.yml ps
echo.

REM Step 8: 健康检查
echo [INFO] 执行健康检查...
echo.

REM 检查Backend
curl -s http://localhost:8001/health | findstr /C:"healthy" >nul
if %errorlevel% equ 0 (
    echo [INFO] √ Backend: 健康 (http://localhost:8001^)
) else (
    echo [ERROR] × Backend: 不健康
)

REM 检查Prometheus
curl -s http://localhost:9090/-/healthy | findstr /C:"Prometheus" >nul
if %errorlevel% equ 0 (
    echo [INFO] √ Prometheus: 健康 (http://localhost:9090^)
) else (
    echo [ERROR] × Prometheus: 不健康
)

REM 检查Grafana
curl -s http://localhost:3000/api/health | findstr /C:"ok" >nul
if %errorlevel% equ 0 (
    echo [INFO] √ Grafana: 健康 (http://localhost:3000^)
) else (
    echo [ERROR] × Grafana: 不健康
)

REM 检查Elasticsearch
curl -s http://localhost:9200/_cluster/health | findstr /C:"cluster_name" >nul
if %errorlevel% equ 0 (
    echo [INFO] √ Elasticsearch: 运行中 (http://localhost:9200^)
) else (
    echo [ERROR] × Elasticsearch: 未运行
)

REM 检查Kibana
curl -s http://localhost:5601/api/status | findstr /C:"available" >nul
if %errorlevel% equ 0 (
    echo [INFO] √ Kibana: 可用 (http://localhost:5601^)
) else (
    echo [ERROR] × Kibana: 不可用
)

echo.
echo [INFO] ==========================================
echo [INFO] Docker环境重建完成！
echo [INFO] ==========================================
echo.
echo [INFO] 访问地址:
echo   - 应用API: http://localhost:8001
echo   - Nginx代理: http://localhost:8082
echo   - Grafana监控: http://localhost:3000 (admin/admin123^)
echo   - Prometheus: http://localhost:9090
echo   - Kibana日志: http://localhost:5601
echo   - Alertmanager: http://localhost:9093
echo.
echo [INFO] 查看日志:
echo   docker-compose -f docker-compose.yml logs -f backend
echo   docker-compose -f docker-compose.monitoring.yml logs -f
echo.
echo [INFO] 停止服务:
echo   docker-compose -f docker-compose.yml down
echo   docker-compose -f docker-compose.monitoring.yml down
echo.

pause
