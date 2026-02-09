@echo off
setlocal enabledelayedexpansion

REM =============================================================================
REM 自动化部署脚本 (Windows版本)
REM 功能：拉取代码、安装依赖、数据库迁移、重启服务
REM 作者：AI赋能云平台运维团队
REM 版本：1.0.0
REM =============================================================================

REM 获取脚本目录
set "SCRIPT_DIR=%~dp0"
set "CONFIG_FILE=%SCRIPT_DIR%deploy-config.bat"

REM 默认配置
if not defined PROJECT_DIR set "PROJECT_DIR=C:\Projects\agri-platform"
if not defined GIT_REPO set "GIT_REPO=https://github.com/your-org/agri-platform.git"
if not defined GIT_BRANCH set "GIT_BRANCH=main"
if not defined BACKUP_DIR set "BACKUP_DIR=C:\Backups\Deployments"

REM 服务配置
if not defined DOCKER_COMPOSE_FILE set "DOCKER_COMPOSE_FILE=docker-compose.yml"
if not defined SERVICES_TO_RESTART set "SERVICES_TO_RESTART=backend frontend"

REM 数据库配置
if not defined DB_HOST set "DB_HOST=localhost"
if not defined DB_PORT set "DB_PORT=3307"
if not defined DB_USER set "DB_USER=agri_user"
if not defined DB_PASSWORD set "DB_PASSWORD=agri_pass"
if not defined DB_NAME set "DB_NAME=agri_platform"

REM 部署配置
if not defined ENABLE_BACKUP set "ENABLE_BACKUP=true"
if not defined ENABLE_MIGRATION set "ENABLE_MIGRATION=true"
if not defined ENABLE_TESTS set "ENABLE_TESTS=false"
if not defined ROLLBACK_ON_FAILURE set "ROLLBACK_ON_FAILURE=true"
if not defined HEALTH_CHECK_TIMEOUT set "HEALTH_CHECK_TIMEOUT=300"

REM 通知配置
if not defined NOTIFICATION_ENABLED set "NOTIFICATION_ENABLED=false"
if not defined WEBHOOK_URL set "WEBHOOK_URL="
if not defined EMAIL_ENABLED set "EMAIL_ENABLED=false"
if not defined EMAIL_TO set "EMAIL_TO="

REM 日志配置
if not defined LOG_DIR set "LOG_DIR=C:\Logs\Deploy"
set "LOG_FILE=%LOG_DIR%\deploy.log"

REM 工具路径
set "GIT_BIN=C:\Program Files\Git\bin\git.exe"
set "DOCKER_BIN=C:\Program Files\Docker\Docker\resources\bin\docker.exe"
set "DOCKER_COMPOSE_BIN=C:\Program Files\Docker\Docker\resources\bin\docker-compose.exe"
set "MYSQL_BIN=C:\Program Files\MySQL\MySQL Server 8.0\bin"
set "CURL_BIN=C:\Windows\System32\curl.exe"

REM 全局变量
set "DEPLOYMENT_ID="
set "BACKUP_PATH="
set "PREVIOUS_COMMIT="
set "CURRENT_COMMIT="
set "DEPLOYMENT_STATUS=UNKNOWN"

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
) else if "%level%"=="ERROR" (
    echo [ERROR] %timestamp% - %message%
    echo [ERROR] %timestamp% - %message% >> "%LOG_FILE%"
) else if "%level%"=="DEBUG" (
    echo [DEBUG] %timestamp% - %message%
    echo [DEBUG] %timestamp% - %message% >> "%LOG_FILE%"
)
goto :eof

:error_exit
call :log "ERROR" "%~1"
set "DEPLOYMENT_STATUS=FAILED"
call :send_notification "FAILED" "%~1"

if "%ROLLBACK_ON_FAILURE%"=="true" if not "%BACKUP_PATH%"=="" (
    call :log "WARN" "开始自动回滚..."
    call :rollback_deployment
)

exit /b 1

:success_exit
call :log "INFO" "%~1"
set "DEPLOYMENT_STATUS=SUCCESS"
call :send_notification "SUCCESS" "%~1"
exit /b 0

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
if not exist "%BACKUP_DIR%" mkdir "%BACKUP_DIR%"
goto :eof

:check_dependencies
call :log "INFO" "检查依赖工具..."

if not exist "%GIT_BIN%" (
    call :error_exit "Git 未找到，请检查安装路径"
)

if not exist "%DOCKER_BIN%" (
    call :error_exit "Docker 未找到，请检查安装路径"
)

if not exist "%DOCKER_COMPOSE_BIN%" (
    call :error_exit "Docker Compose 未找到，请检查安装路径"
)

call :log "INFO" "依赖检查完成"
goto :eof

:generate_deployment_id
REM 生成部署ID
for /f "tokens=1-4 delims=/ " %%a in ('date /t') do (
    set "date_part=%%d%%b%%c"
)
for /f "tokens=1-2 delims=: " %%a in ('time /t') do (
    set "time_part=%%a%%b"
)
set "DEPLOYMENT_ID=deploy_%date_part%_%time_part%_%RANDOM%"
set "DEPLOYMENT_ID=%DEPLOYMENT_ID: =0%"
call :log "INFO" "部署ID: %DEPLOYMENT_ID%"
goto :eof

REM =============================================================================
REM 备份函数
REM =============================================================================

:create_backup
if not "%ENABLE_BACKUP%"=="true" (
    call :log "INFO" "备份功能未启用，跳过"
    goto :eof
)

call :log "INFO" "创建部署备份..."

set "BACKUP_PATH=%BACKUP_DIR%\%DEPLOYMENT_ID%"
mkdir "%BACKUP_PATH%"

REM 备份代码
if exist "%PROJECT_DIR%" (
    call :log "INFO" "备份项目代码..."
    xcopy "%PROJECT_DIR%" "%BACKUP_PATH%\code\" /E /I /H /Y >nul
)

REM 备份数据库
call :log "INFO" "备份数据库..."
if exist "%MYSQL_BIN%\mysqldump.exe" (
    "%MYSQL_BIN%\mysqldump.exe" ^
        --host=%DB_HOST% ^
        --port=%DB_PORT% ^
        --user=%DB_USER% ^
        --password=%DB_PASSWORD% ^
        --single-transaction ^
        --routines ^
        --triggers ^
        %DB_NAME% > "%BACKUP_PATH%\database.sql"

    if !errorlevel! equ 0 (
        call :log "INFO" "数据库备份完成"
    ) else (
        call :log "WARN" "数据库备份失败，但继续部署"
    )
) else (
    call :log "WARN" "mysqldump 未找到，跳过数据库备份"
)

REM 备份Docker镜像信息
call :log "INFO" "备份Docker镜像信息..."
"%DOCKER_BIN%" images --format "table {{.Repository}}:{{.Tag}}\t{{.ID}}\t{{.CreatedAt}}" > "%BACKUP_PATH%\docker-images.txt"

REM 备份配置文件
if exist "%PROJECT_DIR%\.env" (
    copy "%PROJECT_DIR%\.env" "%BACKUP_PATH%\" >nul
)

if exist "%PROJECT_DIR%\%DOCKER_COMPOSE_FILE%" (
    copy "%PROJECT_DIR%\%DOCKER_COMPOSE_FILE%" "%BACKUP_PATH%\" >nul
)

call :log "INFO" "备份创建完成: %BACKUP_PATH%"
goto :eof

REM =============================================================================
REM 代码部署函数
REM =============================================================================

:pull_code
call :log "INFO" "拉取最新代码..."

cd /d "%PROJECT_DIR%" || (
    call :error_exit "无法进入项目目录: %PROJECT_DIR%"
)

REM 记录当前提交
for /f %%c in ('"%GIT_BIN%" rev-parse HEAD 2^>nul') do set "PREVIOUS_COMMIT=%%c"
if not "%PREVIOUS_COMMIT%"=="" (
    call :log "INFO" "当前提交: %PREVIOUS_COMMIT%"
)

REM 拉取最新代码
"%GIT_BIN%" fetch origin %GIT_BRANCH%
if errorlevel 1 (
    call :error_exit "拉取代码失败"
)

REM 检查是否有更新
for /f %%c in ('"%GIT_BIN%" rev-parse origin/%GIT_BRANCH%') do set "REMOTE_COMMIT=%%c"
if "%PREVIOUS_COMMIT%"=="%REMOTE_COMMIT%" (
    call :log "INFO" "代码无更新，跳过部署"
    exit /b 0
)

REM 切换到最新代码
"%GIT_BIN%" reset --hard origin/%GIT_BRANCH%
if errorlevel 1 (
    call :error_exit "切换代码失败"
)

for /f %%c in ('"%GIT_BIN%" rev-parse HEAD') do set "CURRENT_COMMIT=%%c"
call :log "INFO" "更新到提交: %CURRENT_COMMIT%"

REM 显示变更信息
if not "%PREVIOUS_COMMIT%"=="" (
    call :log "INFO" "代码变更:"
    "%GIT_BIN%" log --oneline %PREVIOUS_COMMIT%..%CURRENT_COMMIT% | head -10
)
goto :eof

:build_application
call :log "INFO" "构建应用..."

cd /d "%PROJECT_DIR%" || (
    call :error_exit "无法进入项目目录"
)

REM 构建Docker镜像
"%DOCKER_COMPOSE_BIN%" -f "%DOCKER_COMPOSE_FILE%" build --no-cache
if errorlevel 1 (
    call :error_exit "Docker镜像构建失败"
)

call :log "INFO" "应用构建完成"
goto :eof

:install_dependencies
call :log "INFO" "安装依赖..."

cd /d "%PROJECT_DIR%" || (
    call :error_exit "无法进入项目目录"
)

REM 后端依赖
if exist "backend\requirements.txt" (
    call :log "INFO" "安装后端依赖..."
    "%DOCKER_COMPOSE_BIN%" -f "%DOCKER_COMPOSE_FILE%" run --rm backend pip install -r requirements.txt
)

REM 前端依赖
if exist "frontend\package.json" (
    call :log "INFO" "安装前端依赖..."
    "%DOCKER_COMPOSE_BIN%" -f "%DOCKER_COMPOSE_FILE%" run --rm frontend npm ci
)

call :log "INFO" "依赖安装完成"
goto :eof

REM =============================================================================
REM 数据库迁移函数
REM =============================================================================

:run_database_migration
if not "%ENABLE_MIGRATION%"=="true" (
    call :log "INFO" "数据库迁移未启用，跳过"
    goto :eof
)

call :log "INFO" "执行数据库迁移..."

cd /d "%PROJECT_DIR%" || (
    call :error_exit "无法进入项目目录"
)

REM 检查数据库连接
"%MYSQL_BIN%\mysql.exe" -h%DB_HOST% -P%DB_PORT% -u%DB_USER% -p%DB_PASSWORD% -e "SELECT 1;" >nul 2>&1
if errorlevel 1 (
    call :error_exit "数据库连接失败，无法执行迁移"
)

REM 执行Alembic迁移
if exist "backend\migrations" (
    call :log "INFO" "执行Alembic迁移..."
    "%DOCKER_COMPOSE_BIN%" -f "%DOCKER_COMPOSE_FILE%" run --rm backend alembic upgrade head
    if errorlevel 1 (
        call :error_exit "数据库迁移失败"
    )
)

REM 执行自定义SQL脚本
if exist "database\migrations" (
    call :log "INFO" "执行自定义SQL迁移..."
    for %%f in (database\migrations\*.sql) do (
        call :log "INFO" "执行: %%f"
        "%MYSQL_BIN%\mysql.exe" -h%DB_HOST% -P%DB_PORT% -u%DB_USER% -p%DB_PASSWORD% %DB_NAME% < "%%f"
        if errorlevel 1 (
            call :error_exit "SQL脚本执行失败: %%f"
        )
    )
)

call :log "INFO" "数据库迁移完成"
goto :eof

REM =============================================================================
REM 服务管理函数
REM =============================================================================

:restart_services
call :log "INFO" "重启服务..."

cd /d "%PROJECT_DIR%" || (
    call :error_exit "无法进入项目目录"
)

REM 停止服务
call :log "INFO" "停止现有服务..."
"%DOCKER_COMPOSE_BIN%" -f "%DOCKER_COMPOSE_FILE%" down

REM 启动服务
call :log "INFO" "启动服务..."
"%DOCKER_COMPOSE_BIN%" -f "%DOCKER_COMPOSE_FILE%" up -d
if errorlevel 1 (
    call :error_exit "服务启动失败"
)

call :log "INFO" "服务重启完成"
goto :eof

:health_check
call :log "INFO" "执行健康检查..."

set "timeout=%HEALTH_CHECK_TIMEOUT%"
set "interval=10"
set "elapsed=0"

:health_check_loop
if !elapsed! geq %timeout% (
    call :error_exit "健康检查失败，服务在 %timeout% 秒内未能正常启动"
)

REM 检查容器状态
"%DOCKER_COMPOSE_BIN%" -f "%DOCKER_COMPOSE_FILE%" ps | find "Up" >nul
if errorlevel 1 (
    call :log "INFO" "等待服务启动... (!elapsed!/%timeout% 秒)"
    timeout /t %interval% /nobreak >nul
    set /a "elapsed+=interval"
    goto :health_check_loop
)

REM 检查API端点
"%CURL_BIN%" -f -s "http://localhost:5000/health" >nul 2>&1
if errorlevel 1 (
    call :log "INFO" "等待API响应... (!elapsed!/%timeout% 秒)"
    timeout /t %interval% /nobreak >nul
    set /a "elapsed+=interval"
    goto :health_check_loop
)

call :log "INFO" "健康检查通过"
goto :eof

REM =============================================================================
REM 测试函数
REM =============================================================================

:run_tests
if not "%ENABLE_TESTS%"=="true" (
    call :log "INFO" "测试未启用，跳过"
    goto :eof
)

call :log "INFO" "运行测试..."

cd /d "%PROJECT_DIR%" || (
    call :error_exit "无法进入项目目录"
)

REM 后端测试
if exist "backend\pytest.ini" (
    call :log "INFO" "运行后端测试..."
    "%DOCKER_COMPOSE_BIN%" -f "%DOCKER_COMPOSE_FILE%" run --rm backend pytest tests/ -v
    if errorlevel 1 (
        call :error_exit "后端测试失败"
    )
) else if exist "backend\tests" (
    call :log "INFO" "运行后端测试..."
    "%DOCKER_COMPOSE_BIN%" -f "%DOCKER_COMPOSE_FILE%" run --rm backend pytest tests/ -v
    if errorlevel 1 (
        call :error_exit "后端测试失败"
    )
)

REM 前端测试
if exist "frontend\package.json" (
    call :log "INFO" "运行前端测试..."
    "%DOCKER_COMPOSE_BIN%" -f "%DOCKER_COMPOSE_FILE%" run --rm frontend npm test
    if errorlevel 1 (
        call :error_exit "前端测试失败"
    )
)

call :log "INFO" "测试完成"
goto :eof

REM =============================================================================
REM 回滚函数
REM =============================================================================

:rollback_deployment
if "%BACKUP_PATH%"=="" (
    call :log "ERROR" "备份路径不存在，无法回滚"
    goto :eof
)

if not exist "%BACKUP_PATH%" (
    call :log "ERROR" "备份目录不存在，无法回滚"
    goto :eof
)

call :log "WARN" "开始回滚部署..."

cd /d "%PROJECT_DIR%" || (
    call :log "ERROR" "无法进入项目目录"
    goto :eof
)

REM 停止当前服务
"%DOCKER_COMPOSE_BIN%" -f "%DOCKER_COMPOSE_FILE%" down

REM 恢复代码
if exist "%BACKUP_PATH%\code" (
    call :log "INFO" "恢复代码..."
    rmdir /s /q "%PROJECT_DIR%" 2>nul
    xcopy "%BACKUP_PATH%\code" "%PROJECT_DIR%\" /E /I /H /Y >nul
)

REM 恢复配置文件
if exist "%BACKUP_PATH%\.env" (
    copy "%BACKUP_PATH%\.env" "%PROJECT_DIR%\" >nul
)

if exist "%BACKUP_PATH%\%DOCKER_COMPOSE_FILE%" (
    copy "%BACKUP_PATH%\%DOCKER_COMPOSE_FILE%" "%PROJECT_DIR%\" >nul
)

REM 恢复数据库
if exist "%BACKUP_PATH%\database.sql" (
    call :log "INFO" "恢复数据库..."
    "%MYSQL_BIN%\mysql.exe" -h%DB_HOST% -P%DB_PORT% -u%DB_USER% -p%DB_PASSWORD% %DB_NAME% < "%BACKUP_PATH%\database.sql"
    if errorlevel 1 (
        call :log "WARN" "数据库恢复失败"
    )
)

REM 重启服务
call :log "INFO" "重启服务..."
"%DOCKER_COMPOSE_BIN%" -f "%DOCKER_COMPOSE_FILE%" up -d

REM 等待服务启动
timeout /t 30 /nobreak >nul

REM 简单健康检查
"%CURL_BIN%" -f -s "http://localhost:5000/health" >nul 2>&1
if errorlevel 1 (
    call :log "ERROR" "回滚后服务仍然异常"
    set "DEPLOYMENT_STATUS=ROLLBACK_FAILED"
    call :send_notification "ROLLBACK_FAILED" "部署回滚失败"
) else (
    call :log "INFO" "回滚完成，服务正常"
    set "DEPLOYMENT_STATUS=ROLLBACK_SUCCESS"
    call :send_notification "ROLLBACK_SUCCESS" "部署回滚成功"
)
goto :eof

REM =============================================================================
REM 通知函数
REM =============================================================================

:send_notification
set "status=%1"
set "message=%~2"

if not "%NOTIFICATION_ENABLED%"=="true" goto :eof

set "timestamp=%date% %time%"
for /f %%h in ('hostname') do set "hostname=%%h"

REM 构建详细信息
set "details="
if not "%PREVIOUS_COMMIT%"=="" if not "%CURRENT_COMMIT%"=="" (
    set "details=从 %PREVIOUS_COMMIT:~0,8% 更新到 %CURRENT_COMMIT:~0,8%"
)

REM Webhook通知
if not "%WEBHOOK_URL%"=="" (
    set "payload={\"msgtype\":\"text\",\"text\":{\"content\":\"部署通知\\n状态: %status%\\n时间: %timestamp%\\n主机: %hostname%\\n部署ID: %DEPLOYMENT_ID%\\n详情: %details%\\n消息: %message%\"}}"

    powershell -command "Invoke-RestMethod -Uri '%WEBHOOK_URL%' -Method Post -ContentType 'application/json' -Body '%payload%'" >nul 2>&1
)

REM 邮件通知
if "%EMAIL_ENABLED%"=="true" if not "%EMAIL_TO%"=="" (
    set "subject=部署通知 - %status%"
    set "body=时间: %timestamp%\n主机: %hostname%\n部署ID: %DEPLOYMENT_ID%\n状态: %status%\n详情: %details%\n消息: %message%"

    powershell -command "Send-MailMessage -To '%EMAIL_TO%' -Subject '%subject%' -Body '%body%' -SmtpServer 'your-smtp-server'" >nul 2>&1
)
goto :eof

REM =============================================================================
REM 清理函数
REM =============================================================================

:cleanup_old_backups
call :log "INFO" "清理旧备份..."

set "retention_days=7"

REM 清理旧的部署备份
forfiles /p "%BACKUP_DIR%" /m "deploy_*" /d -%retention_days% /c "cmd /c rmdir /s /q @path" 2>nul

REM 清理旧的Docker镜像
"%DOCKER_BIN%" image prune -f >nul 2>&1

call :log "INFO" "清理完成"
goto :eof

REM =============================================================================
REM 主函数
REM =============================================================================

:show_help
echo 自动化部署脚本
echo.
echo 用法: %~nx0 [选项]
echo.
echo 选项:
echo     /h, /help               显示帮助信息
echo     /c CONFIG_FILE          指定配置文件路径
echo     /b BRANCH               指定Git分支
echo     /e ENV                  指定环境 (dev/staging/prod)
echo     /no-backup              跳过备份
echo     /no-migration           跳过数据库迁移
echo     /no-tests               跳过测试
echo     /no-rollback            失败时不自动回滚
echo     /rollback ID            回滚到指定部署
echo     /dry-run                模拟运行，不执行实际操作
echo.
echo 部署流程:
echo     1. 创建备份
echo     2. 拉取最新代码
echo     3. 构建应用
echo     4. 安装依赖
echo     5. 执行数据库迁移
echo     6. 重启服务
echo     7. 健康检查
echo     8. 运行测试
echo     9. 清理旧备份
echo.
echo 示例:
echo     %~nx0                               # 标准部署
echo     %~nx0 /b develop                    # 部署develop分支
echo     %~nx0 /no-tests                     # 跳过测试的部署
echo     %~nx0 /rollback deploy_20240123     # 回滚到指定部署
echo     %~nx0 /dry-run                      # 模拟运行
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
if /i "%~1"=="/b" (
    set "GIT_BRANCH=%~2"
    shift
    shift
    goto :parse_loop
)
if /i "%~1"=="/e" (
    set "ENVIRONMENT=%~2"
    shift
    shift
    goto :parse_loop
)
if /i "%~1"=="/no-backup" (
    set "ENABLE_BACKUP=false"
    shift
    goto :parse_loop
)
if /i "%~1"=="/no-migration" (
    set "ENABLE_MIGRATION=false"
    shift
    goto :parse_loop
)
if /i "%~1"=="/no-tests" (
    set "ENABLE_TESTS=false"
    shift
    goto :parse_loop
)
if /i "%~1"=="/no-rollback" (
    set "ROLLBACK_ON_FAILURE=false"
    shift
    goto :parse_loop
)
if /i "%~1"=="/rollback" (
    set "ROLLBACK_ID=%~2"
    shift
    shift
    goto :parse_loop
)
if /i "%~1"=="/dry-run" (
    set "DRY_RUN=true"
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

:main
set "start_time=%time%"

call :log "INFO" "=========================================="
call :log "INFO" "自动化部署开始"
call :log "INFO" "=========================================="

REM 解析参数
call :parse_args %*

REM 加载配置
call :load_config

REM 生成部署ID
call :generate_deployment_id

REM 检查依赖
call :check_dependencies

REM 创建目录
call :create_directories

REM 处理回滚请求
if not "%ROLLBACK_ID%"=="" (
    set "BACKUP_PATH=%BACKUP_DIR%\%ROLLBACK_ID%"
    call :rollback_deployment
    exit /b !errorlevel!
)

if "%DRY_RUN%"=="true" (
    call :log "INFO" "模拟运行模式，不执行实际操作"
    call :log "INFO" "配置信息:"
    call :log "INFO" "  项目目录: %PROJECT_DIR%"
    call :log "INFO" "  Git仓库: %GIT_REPO%"
    call :log "INFO" "  Git分支: %GIT_BRANCH%"
    call :log "INFO" "  备份: %ENABLE_BACKUP%"
    call :log "INFO" "  迁移: %ENABLE_MIGRATION%"
    call :log "INFO" "  测试: %ENABLE_TESTS%"
    goto :eof
)

REM 执行部署流程
call :create_backup
call :pull_code
call :build_application
call :install_dependencies
call :run_database_migration
call :restart_services
call :health_check
call :run_tests
call :cleanup_old_backups

set "end_time=%time%"

call :log "INFO" "=========================================="
call :log "INFO" "自动化部署完成"
call :log "INFO" "=========================================="

call :success_exit "部署成功完成"
goto :eof

REM 执行主函数
call :main %*