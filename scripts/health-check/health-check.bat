@echo off
setlocal enabledelayedexpansion

REM =============================================================================
REM 系统健康检查脚本 (Windows版本)
REM 功能：检查服务状态、数据库连接、Redis连接、磁盘空间等
REM 作者：AI赋能云平台运维团队
REM 版本：1.0.0
REM =============================================================================

REM 获取脚本目录
set "SCRIPT_DIR=%~dp0"
set "CONFIG_FILE=%SCRIPT_DIR%health-check-config.bat"

REM 默认配置
if not defined CHECK_INTERVAL set "CHECK_INTERVAL=60"
if not defined MAX_RETRIES set "MAX_RETRIES=3"
if not defined TIMEOUT set "TIMEOUT=10"

REM 服务配置
if not defined SERVICES_TO_CHECK set "SERVICES_TO_CHECK=MySQL80 Redis Docker Desktop Service"
if not defined DOCKER_CONTAINERS set "DOCKER_CONTAINERS=agri-backend agri-frontend agri-mysql agri-redis"

REM 数据库配置
if not defined DB_HOST set "DB_HOST=localhost"
if not defined DB_PORT set "DB_PORT=3307"
if not defined DB_USER set "DB_USER=agri_user"
if not defined DB_PASSWORD set "DB_PASSWORD=agri_pass"
if not defined DB_NAME set "DB_NAME=agri_platform"

REM Redis配置
if not defined REDIS_HOST set "REDIS_HOST=localhost"
if not defined REDIS_PORT set "REDIS_PORT=6380"
if not defined REDIS_PASSWORD set "REDIS_PASSWORD="

REM 磁盘空间检查
if not defined DISK_USAGE_THRESHOLD set "DISK_USAGE_THRESHOLD=80"
if not defined DISK_DRIVES_TO_CHECK set "DISK_DRIVES_TO_CHECK=C: D:"

REM 内存使用检查
if not defined MEMORY_USAGE_THRESHOLD set "MEMORY_USAGE_THRESHOLD=85"

REM CPU使用检查
if not defined CPU_USAGE_THRESHOLD set "CPU_USAGE_THRESHOLD=90"

REM 网络检查
if not defined NETWORK_HOSTS_TO_CHECK set "NETWORK_HOSTS_TO_CHECK=8.8.8.8 114.114.114.114"
if not defined API_ENDPOINTS_TO_CHECK set "API_ENDPOINTS_TO_CHECK=http://localhost:5000/health"

REM 日志配置
if not defined LOG_DIR set "LOG_DIR=C:\Logs\HealthCheck"
set "LOG_FILE=%LOG_DIR%\health-check.log"
set "ALERT_LOG=%LOG_DIR%\alerts.log"

REM 通知配置
if not defined NOTIFICATION_ENABLED set "NOTIFICATION_ENABLED=false"
if not defined WEBHOOK_URL set "WEBHOOK_URL="
if not defined EMAIL_ENABLED set "EMAIL_ENABLED=false"
if not defined EMAIL_TO set "EMAIL_TO="

REM 工具路径
set "MYSQL_BIN=C:\Program Files\MySQL\MySQL Server 8.0\bin"
set "REDIS_CLI=C:\Program Files\Redis\redis-cli.exe"
set "CURL=C:\Windows\System32\curl.exe"

REM 全局变量
set "HEALTH_STATUS=HEALTHY"
set "FAILED_COUNT=0"
set "WARNING_COUNT=0"

REM =============================================================================
REM 工具函数
REM =============================================================================

:log
set "level=%1"
set "message=%~2"
set "timestamp=%date% %time%"

if "%level%"=="INFO" (
    echo [INFO] %timestamp% - %message%
    echo [INFO] %timestamp% - %message% >> "%LOG_FILE%"
) else if "%level%"=="WARN" (
    echo [WARN] %timestamp% - %message%
    echo [WARN] %timestamp% - %message% >> "%LOG_FILE%"
    echo %timestamp% - WARN - %message% >> "%ALERT_LOG%"
) else if "%level%"=="ERROR" (
    echo [ERROR] %timestamp% - %message%
    echo [ERROR] %timestamp% - %message% >> "%LOG_FILE%"
    echo %timestamp% - ERROR - %message% >> "%ALERT_LOG%"
) else if "%level%"=="DEBUG" (
    echo [DEBUG] %timestamp% - %message%
    echo [DEBUG] %timestamp% - %message% >> "%LOG_FILE%"
)
goto :eof

:set_health_status
set "status=%1"
set "check_name=%2"
set "message=%~3"

if "%status%"=="FAILED" (
    set "HEALTH_STATUS=UNHEALTHY"
    set /a "FAILED_COUNT+=1"
    call :log "ERROR" "%check_name% 检查失败: %message%"
) else if "%status%"=="WARNING" (
    if not "%HEALTH_STATUS%"=="UNHEALTHY" set "HEALTH_STATUS=WARNING"
    set /a "WARNING_COUNT+=1"
    call :log "WARN" "%check_name% 检查警告: %message%"
) else if "%status%"=="PASSED" (
    call :log "INFO" "%check_name% 检查通过: %message%"
)
goto :eof

:load_config
if exist "%CONFIG_FILE%" (
    call :log "INFO" "加载配置文件: %CONFIG_FILE%"
    call "%CONFIG_FILE%"
) else (
    call :log "WARN" "配置文件不存在，使用默认配置"
)
goto :eof

:create_directories
call :log "INFO" "创建必要目录..."
if not exist "%LOG_DIR%" mkdir "%LOG_DIR%"
goto :eof

REM =============================================================================
REM 健康检查函数
REM =============================================================================

:check_services
call :log "INFO" "检查Windows服务状态..."

for %%s in (%SERVICES_TO_CHECK%) do (
    sc query "%%s" | find "RUNNING" >nul
    if !errorlevel! equ 0 (
        call :set_health_status "PASSED" "Service-%%s" "服务运行正常"
    ) else (
        call :set_health_status "FAILED" "Service-%%s" "服务未运行"
    )
)
goto :eof

:check_docker_containers
call :log "INFO" "检查Docker容器状态..."

REM 检查Docker是否可用
docker version >nul 2>&1
if errorlevel 1 (
    call :set_health_status "WARNING" "Docker" "Docker不可用"
    goto :eof
)

for %%c in (%DOCKER_CONTAINERS%) do (
    docker ps --format "table {{.Names}}" | find "%%c" >nul
    if !errorlevel! equ 0 (
        REM 检查容器健康状态
        for /f %%h in ('docker inspect --format="{{.State.Health.Status}}" "%%c" 2^>nul') do set "health_status=%%h"

        if "!health_status!"=="healthy" (
            call :set_health_status "PASSED" "Container-%%c" "容器健康"
        ) else if "!health_status!"=="unhealthy" (
            call :set_health_status "FAILED" "Container-%%c" "容器不健康"
        ) else if "!health_status!"=="starting" (
            call :set_health_status "WARNING" "Container-%%c" "容器启动中"
        ) else (
            call :set_health_status "PASSED" "Container-%%c" "容器运行中"
        )
    ) else (
        call :set_health_status "FAILED" "Container-%%c" "容器未运行"
    )
)
goto :eof

:check_database
call :log "INFO" "检查数据库连接..."

set "retry_count=0"
:db_retry_loop
if !retry_count! geq %MAX_RETRIES% (
    call :set_health_status "FAILED" "Database" "连接失败，重试 %MAX_RETRIES% 次后仍无法连接"
    goto :eof
)

"%MYSQL_BIN%\mysql.exe" -h%DB_HOST% -P%DB_PORT% -u%DB_USER% -p%DB_PASSWORD% -e "SELECT 1;" >nul 2>&1
if errorlevel 1 (
    set /a "retry_count+=1"
    timeout /t 2 /nobreak >nul
    goto :db_retry_loop
)

REM 检查数据库性能
for /f %%c in ('"%MYSQL_BIN%\mysql.exe" -h%DB_HOST% -P%DB_PORT% -u%DB_USER% -p%DB_PASSWORD% -e "SHOW STATUS LIKE 'Threads_connected';" 2^>nul ^| findstr /v "Variable_name" ^| for /f "tokens=2" %%a in ('more') do @echo %%a') do set "connections=%%c"

for /f %%m in ('"%MYSQL_BIN%\mysql.exe" -h%DB_HOST% -P%DB_PORT% -u%DB_USER% -p%DB_PASSWORD% -e "SHOW VARIABLES LIKE 'max_connections';" 2^>nul ^| findstr /v "Variable_name" ^| for /f "tokens=2" %%a in ('more') do @echo %%a') do set "max_connections=%%m"

if defined connections if defined max_connections (
    set /a "usage_percent=connections*100/max_connections"
    if !usage_percent! gtr 80 (
        call :set_health_status "WARNING" "Database" "连接数使用率过高: !usage_percent!%%"
    ) else (
        call :set_health_status "PASSED" "Database" "连接正常，使用率: !usage_percent!%%"
    )
) else (
    call :set_health_status "PASSED" "Database" "连接正常"
)
goto :eof

:check_redis
call :log "INFO" "检查Redis连接..."

set "retry_count=0"
:redis_retry_loop
if !retry_count! geq %MAX_RETRIES% (
    call :set_health_status "FAILED" "Redis" "连接失败，重试 %MAX_RETRIES% 次后仍无法连接"
    goto :eof
)

if "%REDIS_PASSWORD%"=="" (
    "%REDIS_CLI%" -h %REDIS_HOST% -p %REDIS_PORT% ping >nul 2>&1
) else (
    "%REDIS_CLI%" -h %REDIS_HOST% -p %REDIS_PORT% -a %REDIS_PASSWORD% ping >nul 2>&1
)

if errorlevel 1 (
    set /a "retry_count+=1"
    timeout /t 2 /nobreak >nul
    goto :redis_retry_loop
)

call :set_health_status "PASSED" "Redis" "连接正常"
goto :eof

:check_disk_space
call :log "INFO" "检查磁盘空间..."

for %%d in (%DISK_DRIVES_TO_CHECK%) do (
    for /f "tokens=3" %%u in ('dir %%d ^| find "bytes free"') do (
        set "free_bytes=%%u"
        set "free_bytes=!free_bytes:,=!"
    )

    for /f "tokens=1" %%t in ('dir %%d ^| find "bytes free"') do (
        set "total_bytes=%%t"
        set "total_bytes=!total_bytes:,=!"
    )

    REM 使用PowerShell计算使用率
    for /f %%p in ('powershell -command "([math]::Round((1 - !free_bytes! / !total_bytes!) * 100))"') do set "usage_percent=%%p"

    if !usage_percent! gtr %DISK_USAGE_THRESHOLD% (
        call :set_health_status "FAILED" "Disk-%%d" "磁盘使用率过高: !usage_percent!%%"
    ) else (
        set /a "warning_threshold=%DISK_USAGE_THRESHOLD%-10"
        if !usage_percent! gtr !warning_threshold! (
            call :set_health_status "WARNING" "Disk-%%d" "磁盘使用率较高: !usage_percent!%%"
        ) else (
            call :set_health_status "PASSED" "Disk-%%d" "磁盘使用率正常: !usage_percent!%%"
        )
    )
)
goto :eof

:check_memory_usage
call :log "INFO" "检查内存使用..."

REM 使用PowerShell获取内存使用率
for /f %%m in ('powershell -command "Get-WmiObject -Class Win32_OperatingSystem | ForEach-Object {[math]::Round((($_.TotalVisibleMemorySize - $_.FreePhysicalMemory) / $_.TotalVisibleMemorySize) * 100)}"') do set "memory_usage=%%m"

if !memory_usage! gtr %MEMORY_USAGE_THRESHOLD% (
    call :set_health_status "FAILED" "Memory" "内存使用率过高: !memory_usage!%%"
) else (
    set /a "warning_threshold=%MEMORY_USAGE_THRESHOLD%-10"
    if !memory_usage! gtr !warning_threshold! (
        call :set_health_status "WARNING" "Memory" "内存使用率较高: !memory_usage!%%"
    ) else (
        call :set_health_status "PASSED" "Memory" "内存使用率正常: !memory_usage!%%"
    )
)
goto :eof

:check_cpu_usage
call :log "INFO" "检查CPU使用..."

REM 使用PowerShell获取CPU使用率
for /f %%c in ('powershell -command "Get-WmiObject -Class Win32_Processor | Measure-Object -Property LoadPercentage -Average | Select-Object -ExpandProperty Average"') do set "cpu_usage=%%c"

if !cpu_usage! gtr %CPU_USAGE_THRESHOLD% (
    call :set_health_status "FAILED" "CPU" "CPU使用率过高: !cpu_usage!%%"
) else (
    set /a "warning_threshold=%CPU_USAGE_THRESHOLD%-10"
    if !cpu_usage! gtr !warning_threshold! (
        call :set_health_status "WARNING" "CPU" "CPU使用率较高: !cpu_usage!%%"
    ) else (
        call :set_health_status "PASSED" "CPU" "CPU使用率正常: !cpu_usage!%%"
    )
)
goto :eof

:check_network
call :log "INFO" "检查网络连接..."

for %%h in (%NETWORK_HOSTS_TO_CHECK%) do (
    ping -n 1 -w %TIMEOUT%000 %%h >nul 2>&1
    if !errorlevel! equ 0 (
        call :set_health_status "PASSED" "Network-%%h" "网络连接正常"
    ) else (
        call :set_health_status "FAILED" "Network-%%h" "网络连接失败"
    )
)
goto :eof

:check_api_endpoints
call :log "INFO" "检查API端点..."

for %%e in (%API_ENDPOINTS_TO_CHECK%) do (
    for /f %%r in ('"%CURL%" -s -o nul -w "%%{http_code}" --max-time %TIMEOUT% "%%e" 2^>nul') do set "response_code=%%r"

    if "!response_code!"=="200" (
        call :set_health_status "PASSED" "API-%%e" "API响应正常"
    ) else if "!response_code:~0,1!"=="4" (
        call :set_health_status "FAILED" "API-%%e" "API返回客户端错误: !response_code!"
    ) else if "!response_code:~0,1!"=="5" (
        call :set_health_status "FAILED" "API-%%e" "API返回服务器错误: !response_code!"
    ) else (
        call :set_health_status "FAILED" "API-%%e" "API无响应或超时"
    )
)
goto :eof

:check_log_errors
call :log "INFO" "检查应用日志错误..."

set "error_count=0"
set "log_paths=C:\Logs\Application\app.log .\backend\logs\app.log .\logs\error.log"

for %%l in (%log_paths%) do (
    if exist "%%l" (
        REM 检查最近的错误日志（简化版本，实际可能需要更复杂的时间过滤）
        for /f %%c in ('findstr /i "error exception fatal" "%%l" 2^>nul ^| find /c /v ""') do (
            set /a "error_count+=%%c"
        )
    )
)

if !error_count! gtr 50 (
    call :set_health_status "FAILED" "Logs" "发现大量错误日志: !error_count! 条"
) else if !error_count! gtr 10 (
    call :set_health_status "WARNING" "Logs" "发现较多错误日志: !error_count! 条"
) else (
    call :set_health_status "PASSED" "Logs" "错误日志数量正常: !error_count! 条"
)
goto :eof

REM =============================================================================
REM 通知函数
REM =============================================================================

:send_notification
set "status=%1"
set "summary=%~2"

if not "%NOTIFICATION_ENABLED%"=="true" goto :eof

set "timestamp=%date% %time%"
for /f %%h in ('hostname') do set "hostname=%%h"

REM Webhook通知
if not "%WEBHOOK_URL%"=="" (
    set "payload={\"msgtype\":\"text\",\"text\":{\"content\":\"系统健康检查报告\\n状态: %status%\\n时间: %timestamp%\\n主机: %hostname%\\n摘要: %summary%\"}}"

    powershell -command "Invoke-RestMethod -Uri '%WEBHOOK_URL%' -Method Post -ContentType 'application/json' -Body '%payload%'" >nul 2>&1
)

REM 邮件通知
if "%EMAIL_ENABLED%"=="true" if not "%EMAIL_TO%"=="" (
    set "subject=系统健康检查报告 - %status%"
    set "body=时间: %timestamp%\n主机: %hostname%\n状态: %status%\n摘要: %summary%"

    powershell -command "Send-MailMessage -To '%EMAIL_TO%' -Subject '%subject%' -Body '%body%' -SmtpServer 'your-smtp-server'" >nul 2>&1
)
goto :eof

REM =============================================================================
REM 主函数
REM =============================================================================

:show_help
echo 系统健康检查脚本
echo.
echo 用法: %~nx0 [选项]
echo.
echo 选项:
echo     /h, /help           显示帮助信息
echo     /c CONFIG_FILE      指定配置文件路径
echo     /i INTERVAL         指定检查间隔（秒）
echo     /once               只执行一次检查
echo     /daemon             后台运行（使用任务计划程序）
echo     /stop               停止后台运行的检查
echo.
echo 检查项目:
echo     - Windows服务状态
echo     - Docker容器状态
echo     - 数据库连接
echo     - Redis连接
echo     - 磁盘空间使用
echo     - 内存使用率
echo     - CPU使用率
echo     - 网络连接
echo     - API端点响应
echo     - 应用日志错误
echo.
echo 示例:
echo     %~nx0                       # 执行一次完整检查
echo     %~nx0 /daemon               # 设置后台持续监控
echo     %~nx0 /i 30 /once          # 30秒间隔执行一次
echo     %~nx0 /c health.bat        # 使用指定配置文件
goto :eof

:run_health_checks
call :log "INFO" "开始系统健康检查..."

REM 重置状态
set "HEALTH_STATUS=HEALTHY"
set "FAILED_COUNT=0"
set "WARNING_COUNT=0"

REM 执行各项检查
call :check_services
call :check_docker_containers
call :check_database
call :check_redis
call :check_disk_space
call :check_memory_usage
call :check_cpu_usage
call :check_network
call :check_api_endpoints
call :check_log_errors

REM 生成报告
call :generate_report
goto :eof

:generate_report
set "timestamp=%date% %time%"

call :log "INFO" "=========================================="
call :log "INFO" "健康检查报告 - %timestamp%"
call :log "INFO" "=========================================="
call :log "INFO" "总体状态: %HEALTH_STATUS%"
call :log "INFO" "失败检查: %FAILED_COUNT%"
call :log "INFO" "警告检查: %WARNING_COUNT%"
call :log "INFO" "=========================================="

REM 发送通知
set "summary=失败: %FAILED_COUNT%, 警告: %WARNING_COUNT%"
call :send_notification "%HEALTH_STATUS%" "%summary%"

REM 返回适当的退出码
if "%HEALTH_STATUS%"=="HEALTHY" exit /b 0
if "%HEALTH_STATUS%"=="WARNING" exit /b 1
if "%HEALTH_STATUS%"=="UNHEALTHY" exit /b 2
goto :eof

:parse_args
:parse_loop
if "%~1"=="" goto :parse_done
if /i "%~1"=="/h" goto :show_help_and_exit
if /i "%~1"=="/help" goto :show_help_and_exit
if /i "%~1"=="/c" (
    set "CONFIG_FILE=%~2"
    shift
    shift
    goto :parse_loop
)
if /i "%~1"=="/i" (
    set "CHECK_INTERVAL=%~2"
    shift
    shift
    goto :parse_loop
)
if /i "%~1"=="/once" (
    set "RUN_ONCE=true"
    shift
    goto :parse_loop
)
if /i "%~1"=="/daemon" (
    set "DAEMON_MODE=true"
    shift
    goto :parse_loop
)
if /i "%~1"=="/stop" (
    set "STOP_DAEMON=true"
    shift
    goto :parse_loop
)

call :log "ERROR" "未知参数: %~1"
call :show_help
exit /b 1

:show_help_and_exit
call :show_help
exit /b 0

:parse_done
goto :eof

:run_daemon
if "%STOP_DAEMON%"=="true" (
    schtasks /delete /tn "HealthCheck" /f >nul 2>&1
    if !errorlevel! equ 0 (
        call :log "INFO" "健康检查任务已停止"
    ) else (
        call :log "WARN" "健康检查任务未运行或停止失败"
    )
    exit /b 0
)

REM 创建任务计划程序任务
call :log "INFO" "创建健康检查任务，检查间隔: %CHECK_INTERVAL%秒"

schtasks /create /tn "HealthCheck" /tr "\"%~f0\" /once" /sc minute /mo 1 /f >nul 2>&1
if errorlevel 1 (
    call :log "ERROR" "创建任务计划失败"
    exit /b 1
)

call :log "INFO" "健康检查任务已创建"
goto :eof

:main
REM 解析参数
call :parse_args %*

REM 加载配置
call :load_config

REM 创建目录
call :create_directories

REM 检查运行模式
if "%DAEMON_MODE%"=="true" (
    call :run_daemon
) else if "%STOP_DAEMON%"=="true" (
    call :run_daemon
) else (
    REM 默认执行一次检查
    call :run_health_checks
)
goto :eof

REM 执行主函数
call :main %*