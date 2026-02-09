@echo off
setlocal enabledelayedexpansion

REM =============================================================================
REM 数据库自动备份脚本 (Windows版本)
REM 功能：MySQL数据库自动备份、上传到OSS、清理旧备份
REM 作者：AI赋能云平台运维团队
REM 版本：1.0.0
REM =============================================================================

REM 获取脚本目录
set "SCRIPT_DIR=%~dp0"
set "CONFIG_FILE=%SCRIPT_DIR%backup-config.bat"

REM 默认配置
if not defined DB_HOST set "DB_HOST=localhost"
if not defined DB_PORT set "DB_PORT=3307"
if not defined DB_USER set "DB_USER=agri_user"
if not defined DB_PASSWORD set "DB_PASSWORD=agri_pass"
if not defined DB_NAME set "DB_NAME=agri_platform"

REM 备份配置
if not defined BACKUP_DIR set "BACKUP_DIR=C:\Backups\MySQL"
if not defined BACKUP_RETENTION_DAYS set "BACKUP_RETENTION_DAYS=7"
if not defined COMPRESS_BACKUP set "COMPRESS_BACKUP=true"

REM OSS配置
if not defined OSS_ENABLED set "OSS_ENABLED=false"
if not defined OSS_ENDPOINT set "OSS_ENDPOINT="
if not defined OSS_ACCESS_KEY_ID set "OSS_ACCESS_KEY_ID="
if not defined OSS_ACCESS_KEY_SECRET set "OSS_ACCESS_KEY_SECRET="
if not defined OSS_BUCKET set "OSS_BUCKET="
if not defined OSS_PATH set "OSS_PATH=mysql-backups"

REM 通知配置
if not defined NOTIFICATION_ENABLED set "NOTIFICATION_ENABLED=false"
if not defined WEBHOOK_URL set "WEBHOOK_URL="
if not defined EMAIL_ENABLED set "EMAIL_ENABLED=false"
if not defined EMAIL_TO set "EMAIL_TO="

REM 日志配置
if not defined LOG_DIR set "LOG_DIR=C:\Logs\Backup"
set "LOG_FILE=%LOG_DIR%\mysql-backup.log"

REM 工具路径
set "MYSQL_BIN=C:\Program Files\MySQL\MySQL Server 8.0\bin"
set "SEVEN_ZIP=C:\Program Files\7-Zip\7z.exe"
set "OSSUTIL=C:\Tools\ossutil\ossutil.exe"

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
call :send_notification "FAILED" "%~1"
exit /b 1

:check_dependencies
call :log "INFO" "检查依赖工具..."

REM 检查MySQL工具
if not exist "%MYSQL_BIN%\mysqldump.exe" (
    call :error_exit "mysqldump.exe 未找到，请检查MySQL安装路径"
)

if not exist "%MYSQL_BIN%\mysql.exe" (
    call :error_exit "mysql.exe 未找到，请检查MySQL安装路径"
)

REM 检查压缩工具
if "%COMPRESS_BACKUP%"=="true" (
    if not exist "%SEVEN_ZIP%" (
        call :error_exit "7-Zip 未找到，请安装7-Zip或设置正确路径"
    )
)

REM 检查OSS工具
if "%OSS_ENABLED%"=="true" (
    if not exist "%OSSUTIL%" (
        call :error_exit "ossutil 未找到，请安装ossutil或设置正确路径"
    )
)

call :log "INFO" "依赖检查完成"
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
call :log "INFO" "创建备份目录..."

if not exist "%BACKUP_DIR%" mkdir "%BACKUP_DIR%"
if not exist "%LOG_DIR%" mkdir "%LOG_DIR%"

call :log "INFO" "目录创建完成"
goto :eof

:test_db_connection
call :log "INFO" "测试数据库连接..."

"%MYSQL_BIN%\mysql.exe" -h%DB_HOST% -P%DB_PORT% -u%DB_USER% -p%DB_PASSWORD% -e "SELECT 1;" >nul 2>&1
if errorlevel 1 (
    call :error_exit "数据库连接失败"
)

call :log "INFO" "数据库连接正常"
goto :eof

REM =============================================================================
REM 备份函数
REM =============================================================================

:perform_backup
REM 生成时间戳
for /f "tokens=1-4 delims=/ " %%a in ('date /t') do (
    set "date_part=%%d%%b%%c"
)
for /f "tokens=1-2 delims=: " %%a in ('time /t') do (
    set "time_part=%%a%%b"
)
set "timestamp=%date_part%_%time_part%"
set "timestamp=%timestamp: =0%"

set "backup_filename=%DB_NAME%_%timestamp%.sql"
set "backup_path=%BACKUP_DIR%\%backup_filename%"

call :log "INFO" "开始备份数据库: %DB_NAME%"
call :log "INFO" "备份文件: %backup_path%"

REM 执行备份
"%MYSQL_BIN%\mysqldump.exe" ^
    --host=%DB_HOST% ^
    --port=%DB_PORT% ^
    --user=%DB_USER% ^
    --password=%DB_PASSWORD% ^
    --single-transaction ^
    --routines ^
    --triggers ^
    --events ^
    --hex-blob ^
    --opt ^
    --comments ^
    --dump-date ^
    %DB_NAME% > "%backup_path%"

if errorlevel 1 (
    call :error_exit "数据库备份失败"
)

REM 验证备份文件
if not exist "%backup_path%" (
    call :error_exit "备份文件创建失败"
)

REM 检查文件大小
for %%F in ("%backup_path%") do set "file_size=%%~zF"
if %file_size% equ 0 (
    call :error_exit "备份文件为空"
)

call :log "INFO" "备份完成，文件大小: %file_size% 字节"

REM 压缩备份
if "%COMPRESS_BACKUP%"=="true" (
    call :log "INFO" "压缩备份文件..."

    "%SEVEN_ZIP%" a -t7z "%backup_path%.7z" "%backup_path%" >nul
    if errorlevel 1 (
        call :error_exit "备份文件压缩失败"
    )

    del "%backup_path%"
    set "backup_path=%backup_path%.7z"
    set "backup_filename=%backup_filename%.7z"

    for %%F in ("%backup_path%") do set "compressed_size=%%~zF"
    call :log "INFO" "压缩完成，压缩后大小: !compressed_size! 字节"
)

set "BACKUP_RESULT=%backup_path%"
goto :eof

:upload_to_oss
set "backup_path=%~1"
set "backup_filename=%~nx1"

if not "%OSS_ENABLED%"=="true" (
    call :log "INFO" "OSS上传未启用，跳过"
    goto :eof
)

call :log "INFO" "上传备份到OSS..."

REM 配置OSS
"%OSSUTIL%" config -e %OSS_ENDPOINT% -i %OSS_ACCESS_KEY_ID% -k %OSS_ACCESS_KEY_SECRET% >nul

REM 上传文件
set "oss_path=oss://%OSS_BUCKET%/%OSS_PATH%/%backup_filename%"

"%OSSUTIL%" cp "%backup_path%" "%oss_path%" >nul
if errorlevel 1 (
    call :log "ERROR" "OSS上传失败"
    goto :eof
)

call :log "INFO" "OSS上传完成: %oss_path%"
goto :eof

:cleanup_old_backups
call :log "INFO" "清理 %BACKUP_RETENTION_DAYS% 天前的备份文件..."

set "deleted_count=0"

REM 计算截止日期
for /f %%a in ('powershell -command "(Get-Date).AddDays(-%BACKUP_RETENTION_DAYS%).ToString('yyyyMMdd')"') do set "cutoff_date=%%a"

REM 清理本地备份
for %%F in ("%BACKUP_DIR%\%DB_NAME%_*.sql*") do (
    set "filename=%%~nF"
    set "file_date=!filename:~-8!"

    if "!file_date!" lss "%cutoff_date%" (
        del "%%F"
        set /a "deleted_count+=1"
        call :log "INFO" "删除本地备份: %%~nxF"
    )
)

REM 清理OSS备份
if "%OSS_ENABLED%"=="true" (
    call :log "INFO" "清理OSS旧备份..."

    REM 这里需要根据实际的ossutil命令来实现OSS文件清理
    REM 由于Windows批处理的限制，这部分可能需要PowerShell脚本辅助
)

call :log "INFO" "清理完成，共删除 %deleted_count% 个备份文件"
goto :eof

REM =============================================================================
REM 通知函数
REM =============================================================================

:send_notification
set "status=%~1"
set "message=%~2"

if not "%NOTIFICATION_ENABLED%"=="true" goto :eof

set "timestamp=%date% %time%"
for /f %%a in ('hostname') do set "hostname=%%a"

REM Webhook通知
if not "%WEBHOOK_URL%"=="" (
    set "payload={\"msgtype\":\"text\",\"text\":{\"content\":\"数据库备份通知\\n状态: %status%\\n时间: %timestamp%\\n主机: %hostname%\\n数据库: %DB_NAME%\\n消息: %message%\"}}"

    powershell -command "Invoke-RestMethod -Uri '%WEBHOOK_URL%' -Method Post -ContentType 'application/json' -Body '%payload%'" >nul 2>&1
)

REM 邮件通知
if "%EMAIL_ENABLED%"=="true" if not "%EMAIL_TO%"=="" (
    set "subject=数据库备份通知 - %status%"
    set "body=时间: %timestamp%\n主机: %hostname%\n数据库: %DB_NAME%\n状态: %status%\n消息: %message%"

    REM 这里需要配置SMTP设置或使用PowerShell发送邮件
    powershell -command "Send-MailMessage -To '%EMAIL_TO%' -Subject '%subject%' -Body '%body%' -SmtpServer 'your-smtp-server'" >nul 2>&1
)

goto :eof

REM =============================================================================
REM 主函数
REM =============================================================================

:show_help
echo 数据库自动备份脚本
echo.
echo 用法: %~nx0 [选项]
echo.
echo 选项:
echo     /h, /help           显示帮助信息
echo     /c CONFIG_FILE      指定配置文件路径
echo     /d DATABASE         指定数据库名称
echo     /o OUTPUT_DIR       指定备份输出目录
echo     /r RETENTION_DAYS   指定备份保留天数
echo     /no-compress        不压缩备份文件
echo     /no-oss            不上传到OSS
echo     /dry-run           模拟运行，不执行实际操作
echo.
echo 示例:
echo     %~nx0                                   # 使用默认配置
echo     %~nx0 /c backup.bat                    # 使用指定配置文件
echo     %~nx0 /d mydb /o C:\Backup             # 指定数据库和输出目录
echo     %~nx0 /dry-run                         # 模拟运行
echo.
echo 配置文件示例:
echo     set "DB_HOST=localhost"
echo     set "DB_PORT=3307"
echo     set "DB_USER=backup_user"
echo     set "DB_PASSWORD=backup_pass"
echo     set "DB_NAME=agri_platform"
echo     set "BACKUP_DIR=C:\Backups\MySQL"
echo     set "BACKUP_RETENTION_DAYS=7"
echo     set "OSS_ENABLED=true"
echo     set "OSS_BUCKET=my-backup-bucket"
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
if /i "%~1"=="/d" (
    set "DB_NAME=%~2"
    shift
    shift
    goto :parse_loop
)
if /i "%~1"=="/o" (
    set "BACKUP_DIR=%~2"
    shift
    shift
    goto :parse_loop
)
if /i "%~1"=="/r" (
    set "BACKUP_RETENTION_DAYS=%~2"
    shift
    shift
    goto :parse_loop
)
if /i "%~1"=="/no-compress" (
    set "COMPRESS_BACKUP=false"
    shift
    goto :parse_loop
)
if /i "%~1"=="/no-oss" (
    set "OSS_ENABLED=false"
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
call :log "INFO" "数据库备份开始"
call :log "INFO" "=========================================="

REM 解析参数
call :parse_args %*

REM 加载配置
call :load_config

REM 检查依赖
call :check_dependencies

REM 创建目录
call :create_directories

REM 测试数据库连接
call :test_db_connection

if "%DRY_RUN%"=="true" (
    call :log "INFO" "模拟运行模式，不执行实际操作"
    call :log "INFO" "配置信息:"
    call :log "INFO" "  数据库: %DB_HOST%:%DB_PORT%/%DB_NAME%"
    call :log "INFO" "  备份目录: %BACKUP_DIR%"
    call :log "INFO" "  保留天数: %BACKUP_RETENTION_DAYS%"
    call :log "INFO" "  压缩: %COMPRESS_BACKUP%"
    call :log "INFO" "  OSS上传: %OSS_ENABLED%"
    goto :eof
)

REM 执行备份
call :perform_backup

REM 上传到OSS
call :upload_to_oss "%BACKUP_RESULT%"

REM 清理旧备份
call :cleanup_old_backups

set "end_time=%time%"

call :log "INFO" "=========================================="
call :log "INFO" "数据库备份完成"
call :log "INFO" "=========================================="

call :send_notification "SUCCESS" "数据库备份成功完成"
goto :eof

REM 执行主函数
call :main %*