@echo off
REM Grafana社区仪表盘导入脚本 (Windows版)
REM 使用Grafana API自动导入社区仪表盘

setlocal enabledelayedexpansion

REM 配置
if "%GRAFANA_URL%"=="" set GRAFANA_URL=http://localhost:3000
if "%GRAFANA_USER%"=="" set GRAFANA_USER=admin
if "%GRAFANA_PASSWORD%"=="" set GRAFANA_PASSWORD=admin123

echo ==========================================
echo Grafana社区仪表盘导入工具
echo ==========================================
echo Grafana URL: %GRAFANA_URL%
echo.

REM 检查curl是否可用
where curl >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] curl未安装或不在PATH中
    echo 请安装curl或使用Git Bash运行 import-community-dashboards.sh
    exit /b 1
)

REM 检查Grafana是否就绪
echo [INFO] 检查Grafana服务状态...
set retry_count=0
set max_retries=30

:check_loop
curl -s -f "%GRAFANA_URL%/api/health" >nul 2>&1
if %errorlevel% equ 0 (
    echo [INFO] Grafana服务已就绪
    goto grafana_ready
)

set /a retry_count+=1
if %retry_count% geq %max_retries% (
    echo [ERROR] Grafana服务未就绪,超时退出
    exit /b 1
)

echo [WARN] Grafana未就绪, 重试 %retry_count%/%max_retries%...
timeout /t 2 /nobreak >nul
goto check_loop

:grafana_ready

echo.
echo [INFO] 开始导入社区仪表盘...
echo.

set success_count=0
set fail_count=0

REM ========================================
REM 导入仪表盘 1: Node Exporter Full (1860)
REM ========================================
echo [INFO] 导入仪表盘: Node Exporter Full (ID: 1860)

REM 下载仪表盘JSON
echo [INFO] 从Grafana.com下载仪表盘...
curl -s "https://grafana.com/api/dashboards/1860/revisions/latest/download" -o "%TEMP%\dashboard_1860.json"

if %errorlevel% neq 0 (
    echo [ERROR] 下载仪表盘失败: Node Exporter Full
    set /a fail_count+=1
    goto dashboard_2
)

REM 创建导入payload
echo {"dashboard": > "%TEMP%\import_1860.json"
type "%TEMP%\dashboard_1860.json" >> "%TEMP%\import_1860.json"
echo , "overwrite": true, "inputs": [{"name": "DS_PROMETHEUS", "type": "datasource", "pluginId": "prometheus", "value": "Prometheus"}]} >> "%TEMP%\import_1860.json"

REM 导入到Grafana
echo [INFO] 导入仪表盘到Grafana...
curl -s -X POST ^
    -H "Content-Type: application/json" ^
    -u "%GRAFANA_USER%:%GRAFANA_PASSWORD%" ^
    -d "@%TEMP%\import_1860.json" ^
    "%GRAFANA_URL%/api/dashboards/import" ^
    -o "%TEMP%\response_1860.json"

REM 检查响应
findstr /C:"\"uid\"" "%TEMP%\response_1860.json" >nul
if %errorlevel% equ 0 (
    echo [INFO] Successfully imported: Node Exporter Full
    set /a success_count+=1
) else (
    echo [ERROR] Failed to import: Node Exporter Full
    type "%TEMP%\response_1860.json"
    set /a fail_count+=1
)

del "%TEMP%\dashboard_1860.json" "%TEMP%\import_1860.json" "%TEMP%\response_1860.json" 2>nul

echo.

:dashboard_2
REM ========================================
REM 导入仪表盘 2: Docker Container & Host Metrics (179)
REM ========================================
echo [INFO] 导入仪表盘: Docker Container ^& Host Metrics (ID: 179)

REM 下载仪表盘JSON
echo [INFO] 从Grafana.com下载仪表盘...
curl -s "https://grafana.com/api/dashboards/179/revisions/latest/download" -o "%TEMP%\dashboard_179.json"

if %errorlevel% neq 0 (
    echo [ERROR] 下载仪表盘失败: Docker Container ^& Host Metrics
    set /a fail_count+=1
    goto summary
)

REM 创建导入payload
echo {"dashboard": > "%TEMP%\import_179.json"
type "%TEMP%\dashboard_179.json" >> "%TEMP%\import_179.json"
echo , "overwrite": true, "inputs": [{"name": "DS_PROMETHEUS", "type": "datasource", "pluginId": "prometheus", "value": "Prometheus"}]} >> "%TEMP%\import_179.json"

REM 导入到Grafana
echo [INFO] 导入仪表盘到Grafana...
curl -s -X POST ^
    -H "Content-Type: application/json" ^
    -u "%GRAFANA_USER%:%GRAFANA_PASSWORD%" ^
    -d "@%TEMP%\import_179.json" ^
    "%GRAFANA_URL%/api/dashboards/import" ^
    -o "%TEMP%\response_179.json"

REM 检查响应
findstr /C:"\"uid\"" "%TEMP%\response_179.json" >nul
if %errorlevel% equ 0 (
    echo [INFO] Successfully imported: Docker Container ^& Host Metrics
    set /a success_count+=1
) else (
    echo [ERROR] Failed to import: Docker Container ^& Host Metrics
    type "%TEMP%\response_179.json"
    set /a fail_count+=1
)

del "%TEMP%\dashboard_179.json" "%TEMP%\import_179.json" "%TEMP%\response_179.json" 2>nul

:summary
REM 汇总结果
echo.
echo ==========================================
echo 导入完成
echo ==========================================
echo 成功: %success_count%
echo 失败: %fail_count%
echo.

if %fail_count% equ 0 (
    echo [INFO] 所有仪表盘导入成功!
    echo [INFO] 访问Grafana查看: %GRAFANA_URL%
    exit /b 0
) else (
    echo [WARN] 部分仪表盘导入失败,请检查日志
    exit /b 1
)
