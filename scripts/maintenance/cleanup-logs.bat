@echo off
setlocal enabledelayedexpansion

REM =============================================================================
REM 日志清理脚本 (Windows版本)
REM 功能：清理过期日志、压缩归档
REM 作者：AI赋能云平台运维团队
REM 版本：1.0.0
REM =============================================================================

REM 获取脚本目录
set "SCRIPT_DIR=%~dp0"
set "CONFIG_FILE=%SCRIPT_DIR%cleanup-config.bat"

REM 默认配置
if not defined LOG_RETENTION_DAYS set "LOG_RETENTION_DAYS=30"
if not defined ARCHIVE_RETENTION_DAYS set "ARCHIVE_RETENTION_DAYS=90"
if not defined COMPRESS_LOGS set "COMPRESS_LOGS=true"
if not defined DELETE_EMPTY_DIRS set "DELETE_EMPTY_DIRS=true"

REM 日志路径配置
if not defined LOG_PATHS set "LOG_PATHS=C:\Logs C:\Projects\agri-platform\backend\logs C:\Projects\agri-platform\logs"
if not defined SYSTEM_LOG_PATHS set "SYSTEM_LOG_PATHS=C:\Windows\Logs C:\Windows\System32\LogFiles"
if not defined APPLICATION_LOG_PATHS set "APPLICATION_LOG_PATHS=C:\Projects\agri-platform\backend\logs C:\Projects\agri-platform\logs"

REM 排除配置
if not defined EXCLUDE_PATTERNS set "EXCLUDE_PATTERNS=*.pid *.lock current active"
if not defined EXCLUDE_EXTENSIONS set "EXCLUDE_EXTENSIONS=pid lock tmp"

REM 压缩配置
if not defined COMPRESSION_TYPE set "COMPRESSION_TYPE=zip"

REM 通知配置
if not defined NOTIFICATION_ENABLED set "NOTIFICATION_ENABLED=false"
if not defined WEBHOOK_URL set "WEBHOOK_URL="
if not defined EMAIL_ENABLED set "EMAIL_ENABLED=false"
if not defined EMAIL_TO set "EMAIL_TO="

REM 日志配置
if not defined CLEANUP_LOG_DIR set "CLEANUP_LOG_DIR=C:\Logs\Cleanup"
set "CLEANUP_LOG_FILE=%CLEANUP_LOG_DIR%\cleanup.log"

REM 工具路径
set "SEVEN_ZIP=C:\Program Files\7-Zip\7z.exe"
set "POWERSHELL=C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe"

REM 统计变量
set "TOTAL_FILES_PROCESSED=0"
set "TOTAL_FILES_DELETED=0"
set "TOTAL_FILES_COMPRESSED=0"
set "TOTAL_SIZE_FREED=0"
set "TOTAL_SIZE_COMPRESSED=0"

REM =============================================================================
REM 工具函数
REM =============================================================================

:log
set "level=%1"
set "message=%~2"
set "timestamp=%date% %time%"

if "%level%"=="INFO" (
    echo [INFO] %timestamp% - %message%
    echo [INFO] %timestamp% - %message% >> "%CLEANUP_LOG_FILE%"
) else if "%level%"=="WARN" (
    echo [WARN] %timestamp% - %message%
    echo [WARN] %timestamp% - %message% >> "%CLEANUP_LOG_FILE%"
) else if "%level%"=="ERROR" (
    echo [ERROR] %timestamp% - %message%
    echo [ERROR] %timestamp% - %message% >> "%CLEANUP_LOG_FILE%"
) else if "%level%"=="DEBUG" (
    echo [DEBUG] %timestamp% - %message%
    echo [DEBUG] %timestamp% - %message% >> "%CLEANUP_LOG_FILE%"
)
goto :eof

:error_exit
call :log "ERROR" "%~1"
call :send_notification "FAILED" "%~1"
exit /b 1

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
if not exist "%CLEANUP_LOG_DIR%" mkdir "%CLEANUP_LOG_DIR%"
goto :eof

:check_permissions
call :log "INFO" "检查权限..."

for %%p in (%LOG_PATHS%) do (
    if exist "%%p" (
        dir "%%p" >nul 2>&1
        if errorlevel 1 (
            call :log "WARN" "无访问权限: %%p"
        )
    )
)

call :log "INFO" "权限检查完成"
goto :eof

:human_readable_size
set "size=%1"
set "unit=B"

if %size% gtr 1073741824 (
    set /a "size=%size%/1073741824"
    set "unit=GB"
) else if %size% gtr 1048576 (
    set /a "size=%size%/1048576"
    set "unit=MB"
) else if %size% gtr 1024 (
    set /a "size=%size%/1024"
    set "unit=KB"
)

set "HUMAN_SIZE=%size%%unit%"
goto :eof

REM =============================================================================
REM 日志清理函数
REM =============================================================================

:should_exclude_file
set "file_path=%~1"
set "filename=%~nx1"
set "extension=%~x1"
set "extension=%extension:~1%"

REM 检查排除模式
for %%p in (%EXCLUDE_PATTERNS%) do (
    if /i "%filename%"=="%%p" (
        exit /b 0
    )
)

REM 检查排除扩展名
for %%e in (%EXCLUDE_EXTENSIONS%) do (
    if /i "%extension%"=="%%e" (
        exit /b 0
    )
)

exit /b 1

:cleanup_expired_logs
set "log_path=%~1"
set "retention_days=%~2"
set "action=%~3"

call :log "INFO" "清理 %log_path% 中 %retention_days% 天前的日志文件 (动作: %action%)..."

if not exist "%log_path%" (
    call :log "WARN" "日志路径不存在: %log_path%"
    goto :eof
)

set "files_found=0"
set "files_processed=0"

REM 计算截止日期
for /f %%d in ('powershell -command "(Get-Date).AddDays(-%retention_days%).ToString('yyyy-MM-dd')"') do set "cutoff_date=%%d"

REM 查找过期文件
for /r "%log_path%" %%f in (*.*) do (
    set /a "files_found+=1"
    set /a "TOTAL_FILES_PROCESSED+=1"

    REM 检查是否应该排除
    call :should_exclude_file "%%f"
    if !errorlevel! equ 0 (
        call :log "DEBUG" "跳过排除文件: %%f"
        goto :continue_loop
    )

    REM 获取文件修改时间
    for /f %%t in ('powershell -command "(Get-Item '%%f').LastWriteTime.ToString('yyyy-MM-dd')"') do set "file_date=%%t"

    REM 比较日期
    if "!file_date!" lss "%cutoff_date%" (
        for %%s in ("%%f") do set "file_size=%%~zs"

        if "%action%"=="delete" (
            call :log "DEBUG" "删除文件: %%f"
            del "%%f" >nul 2>&1
            if !errorlevel! equ 0 (
                set /a "files_processed+=1"
                set /a "TOTAL_FILES_DELETED+=1"
                set /a "TOTAL_SIZE_FREED+=!file_size!"
            ) else (
                call :log "WARN" "删除失败: %%f"
            )
        ) else if "%action%"=="compress" (
            echo "%%f" | find ".zip" >nul
            if errorlevel 1 (
                echo "%%f" | find ".7z" >nul
                if errorlevel 1 (
                    call :log "DEBUG" "压缩文件: %%f"
                    call :compress_file "%%f"
                    if !errorlevel! equ 0 (
                        set /a "files_processed+=1"
                        set /a "TOTAL_FILES_COMPRESSED+=1"
                    ) else (
                        call :log "WARN" "压缩失败: %%f"
                    )
                ) else (
                    call :log "DEBUG" "文件已压缩，跳过: %%f"
                )
            ) else (
                call :log "DEBUG" "文件已压缩，跳过: %%f"
            )
        )
    )

    :continue_loop
)

call :log "INFO" "路径 %log_path%: 找到 %files_found% 个文件，处理 %files_processed% 个"
goto :eof

:compress_file
set "file_path=%~1"
set "compressed_file=%file_path%.zip"

if "%COMPRESSION_TYPE%"=="zip" (
    if exist "%SEVEN_ZIP%" (
        "%SEVEN_ZIP%" a -tzip "%compressed_file%" "%file_path%" >nul 2>&1
        if !errorlevel! equ 0 (
            del "%file_path%" >nul 2>&1
            exit /b 0
        )
    ) else (
        REM 使用PowerShell压缩
        powershell -command "Compress-Archive -Path '%file_path%' -DestinationPath '%compressed_file%'" >nul 2>&1
        if !errorlevel! equ 0 (
            del "%file_path%" >nul 2>&1
            exit /b 0
        )
    )
) else if "%COMPRESSION_TYPE%"=="7z" (
    if exist "%SEVEN_ZIP%" (
        "%SEVEN_ZIP%" a -t7z "%file_path%.7z" "%file_path%" >nul 2>&1
        if !errorlevel! equ 0 (
            del "%file_path%" >nul 2>&1
            exit /b 0
        )
    )
)

exit /b 1

:cleanup_application_logs
call :log "INFO" "清理应用日志..."

for %%p in (%APPLICATION_LOG_PATHS%) do (
    if exist "%%p" (
        REM 压缩7天前的日志
        if "%COMPRESS_LOGS%"=="true" (
            call :cleanup_expired_logs "%%p" 7 "compress"
        )

        REM 删除超过保留期的日志
        call :cleanup_expired_logs "%%p" %LOG_RETENTION_DAYS% "delete"
    )
)
goto :eof

:cleanup_system_logs
call :log "INFO" "清理系统日志..."

REM 清理Windows事件日志
call :log "INFO" "清理Windows事件日志..."
for %%l in (Application System Security) do (
    wevtutil cl %%l >nul 2>&1
    if !errorlevel! equ 0 (
        call :log "INFO" "清理事件日志: %%l"
    ) else (
        call :log "WARN" "清理事件日志失败: %%l"
    )
)

REM 清理IIS日志
if exist "C:\inetpub\logs\LogFiles" (
    call :log "INFO" "清理IIS日志..."
    call :cleanup_expired_logs "C:\inetpub\logs\LogFiles" %LOG_RETENTION_DAYS% "delete"
)

REM 清理Windows更新日志
if exist "C:\Windows\Logs\WindowsUpdate" (
    call :log "INFO" "清理Windows更新日志..."
    call :cleanup_expired_logs "C:\Windows\Logs\WindowsUpdate" %LOG_RETENTION_DAYS% "delete"
)
goto :eof

:cleanup_docker_logs
call :log "INFO" "清理Docker日志..."

REM 检查Docker是否可用
docker version >nul 2>&1
if errorlevel 1 (
    call :log "WARN" "Docker不可用，跳过Docker日志清理"
    goto :eof
)

REM 清理Docker容器日志
call :log "INFO" "清理Docker容器日志..."
for /f %%c in ('docker ps -aq 2^>nul') do (
    REM 截断容器日志
    docker logs --tail 1000 %%c >nul 2>&1
)

REM 清理Docker系统
call :log "INFO" "清理Docker系统..."
docker system prune -f --volumes >nul 2>&1
if errorlevel 1 (
    call :log "WARN" "Docker系统清理失败"
)
goto :eof

:cleanup_iis_logs
call :log "INFO" "清理IIS日志..."

set "iis_log_paths=C:\inetpub\logs\LogFiles"

if exist "%iis_log_paths%" (
    REM 压缩7天前的IIS日志
    if "%COMPRESS_LOGS%"=="true" (
        call :cleanup_expired_logs "%iis_log_paths%" 7 "compress"
    )

    REM 删除30天前的IIS日志
    call :cleanup_expired_logs "%iis_log_paths%" 30 "delete"
)
goto :eof

:cleanup_sql_server_logs
call :log "INFO" "清理SQL Server日志..."

REM 清理SQL Server错误日志
set "sql_log_paths=C:\Program Files\Microsoft SQL Server"

if exist "%sql_log_paths%" (
    for /d %%d in ("%sql_log_paths%\*") do (
        if exist "%%d\MSSQL\Log" (
            call :cleanup_expired_logs "%%d\MSSQL\Log" %LOG_RETENTION_DAYS% "delete"
        )
    )
)

REM 使用SQLCMD清理SQL Server日志
sqlcmd -Q "EXEC sp_cycle_errorlog" >nul 2>&1
if !errorlevel! equ 0 (
    call :log "INFO" "SQL Server错误日志已循环"
) else (
    call :log "WARN" "SQL Server错误日志循环失败"
)
goto :eof

:cleanup_empty_directories
if not "%DELETE_EMPTY_DIRS%"=="true" goto :eof

call :log "INFO" "清理空目录..."

for %%p in (%LOG_PATHS%) do (
    if exist "%%p" (
        REM 使用PowerShell删除空目录
        powershell -command "Get-ChildItem '%%p' -Recurse -Directory | Where-Object {(Get-ChildItem $_.FullName -Recurse -File).Count -eq 0} | Remove-Item -Recurse -Force" >nul 2>&1
    )
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

REM 构建统计信息
call :human_readable_size %TOTAL_SIZE_FREED%
set "freed_size=%HUMAN_SIZE%"
call :human_readable_size %TOTAL_SIZE_COMPRESSED%
set "compressed_size=%HUMAN_SIZE%"

set "stats=处理文件: %TOTAL_FILES_PROCESSED%, 删除: %TOTAL_FILES_DELETED%, 压缩: %TOTAL_FILES_COMPRESSED%"
set "stats=%stats%, 释放空间: %freed_size%, 压缩节省: %compressed_size%"

REM Webhook通知
if not "%WEBHOOK_URL%"=="" (
    set "payload={\"msgtype\":\"text\",\"text\":{\"content\":\"日志清理通知\\n状态: %status%\\n时间: %timestamp%\\n主机: %hostname%\\n统计: %stats%\\n消息: %message%\"}}"

    powershell -command "Invoke-RestMethod -Uri '%WEBHOOK_URL%' -Method Post -ContentType 'application/json' -Body '%payload%'" >nul 2>&1
)

REM 邮件通知
if "%EMAIL_ENABLED%"=="true" if not "%EMAIL_TO%"=="" (
    set "subject=日志清理通知 - %status%"
    set "body=时间: %timestamp%\n主机: %hostname%\n状态: %status%\n统计: %stats%\n消息: %message%"

    powershell -command "Send-MailMessage -To '%EMAIL_TO%' -Subject '%subject%' -Body '%body%' -SmtpServer 'your-smtp-server'" >nul 2>&1
)
goto :eof

REM =============================================================================
REM 主函数
REM =============================================================================

:show_help
echo 日志清理脚本
echo.
echo 用法: %~nx0 [选项]
echo.
echo 选项:
echo     /h, /help               显示帮助信息
echo     /c CONFIG_FILE          指定配置文件路径
echo     /r RETENTION_DAYS       指定日志保留天数
echo     /p PATH                 指定要清理的路径
echo     /no-compress            不压缩日志文件
echo     /no-system              不清理系统日志
echo     /no-docker              不清理Docker日志
echo     /no-iis                 不清理IIS日志
echo     /no-sql                 不清理SQL Server日志
echo     /dry-run                模拟运行，不执行实际操作
echo.
echo 清理范围:
echo     - 应用日志文件
echo     - 系统日志文件
echo     - Docker容器日志
echo     - IIS访问日志
echo     - SQL Server日志文件
echo     - 空目录清理
echo.
echo 示例:
echo     %~nx0                               # 标准清理
echo     %~nx0 /r 15                         # 保留15天的日志
echo     %~nx0 /p C:\MyApp\Logs             # 清理指定路径
echo     %~nx0 /no-compress                 # 不压缩，直接删除
echo     %~nx0 /dry-run                     # 模拟运行
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
if /i "%~1"=="/r" (
    set "LOG_RETENTION_DAYS=%~2"
    shift
    shift
    goto :parse_loop
)
if /i "%~1"=="/p" (
    set "LOG_PATHS=%LOG_PATHS% %~2"
    shift
    shift
    goto :parse_loop
)
if /i "%~1"=="/no-compress" (
    set "COMPRESS_LOGS=false"
    shift
    goto :parse_loop
)
if /i "%~1"=="/no-system" (
    set "SKIP_SYSTEM=true"
    shift
    goto :parse_loop
)
if /i "%~1"=="/no-docker" (
    set "SKIP_DOCKER=true"
    shift
    goto :parse_loop
)
if /i "%~1"=="/no-iis" (
    set "SKIP_IIS=true"
    shift
    goto :parse_loop
)
if /i "%~1"=="/no-sql" (
    set "SKIP_SQL=true"
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
call :log "INFO" "日志清理开始"
call :log "INFO" "=========================================="

REM 解析参数
call :parse_args %*

REM 加载配置
call :load_config

REM 创建目录
call :create_directories

REM 检查权限
call :check_permissions

if "%DRY_RUN%"=="true" (
    call :log "INFO" "模拟运行模式，不执行实际操作"
    call :log "INFO" "配置信息:"
    call :log "INFO" "  日志保留天数: %LOG_RETENTION_DAYS%"
    call :log "INFO" "  压缩日志: %COMPRESS_LOGS%"
    call :log "INFO" "  清理路径: %LOG_PATHS%"
    call :log "INFO" "  排除模式: %EXCLUDE_PATTERNS%"
    goto :eof
)

REM 执行清理任务
call :cleanup_application_logs

if not "%SKIP_SYSTEM%"=="true" (
    call :cleanup_system_logs
)

if not "%SKIP_DOCKER%"=="true" (
    call :cleanup_docker_logs
)

if not "%SKIP_IIS%"=="true" (
    call :cleanup_iis_logs
)

if not "%SKIP_SQL%"=="true" (
    call :cleanup_sql_server_logs
)

call :cleanup_empty_directories

set "end_time=%time%"

call :human_readable_size %TOTAL_SIZE_FREED%
set "freed_size=%HUMAN_SIZE%"
call :human_readable_size %TOTAL_SIZE_COMPRESSED%
set "compressed_size=%HUMAN_SIZE%"

call :log "INFO" "=========================================="
call :log "INFO" "日志清理完成"
call :log "INFO" "统计信息:"
call :log "INFO" "  处理文件数: %TOTAL_FILES_PROCESSED%"
call :log "INFO" "  删除文件数: %TOTAL_FILES_DELETED%"
call :log "INFO" "  压缩文件数: %TOTAL_FILES_COMPRESSED%"
call :log "INFO" "  释放空间: %freed_size%"
call :log "INFO" "  压缩节省: %compressed_size%"
call :log "INFO" "=========================================="

call :send_notification "SUCCESS" "日志清理成功完成"
goto :eof

REM 执行主函数
call :main %*