@echo off
REM Script de Backup do Sistema de Escola
REM Execute este arquivo para fazer backup automático

setlocal enabledelayedexpansion

REM Defina a data
for /f "tokens=2-4 delims=/ " %%a in ('date /t') do (set mydate=%%c%%a%%b)
for /f "tokens=1-2 delims=/:" %%a in ('time /t') do (set mytime=%%a%%b)

REM Caminhos
set SOURCE=tmp\school_system
set BACKUP_DIR=C:\Users\brend\Desktop\school_system_backups
set BACKUP_FILE=%BACKUP_DIR%\school_system_%mydate%_%mytime%.zip

REM Crie diretório se não existir
if not exist "%BACKUP_DIR%" mkdir "%BACKUP_DIR%"

REM Faça o backup
echo.
echo ========================================
echo Fazendo backup do projeto...
echo Data: %mydate%
echo Hora: %mytime%
echo ========================================
echo.

REM Use PowerShell para compactar
powershell -command "& {Add-Type -A System.IO.Compression.FileSystem; [IO.Compression.ZipFile]::CreateFromDirectory('%SOURCE%', '%BACKUP_FILE%');}"

if %ERRORLEVEL% EQU 0 (
    echo.
    echo ========================================
    echo [OK] Backup criado com sucesso!
    echo Arquivo: %BACKUP_FILE%
    echo ========================================
    echo.
    pause
) else (
    echo.
    echo ========================================
    echo [ERRO] Falha ao criar backup!
    echo ========================================
    echo.
    pause
)

REM Copie também o banco de dados
echo.
echo Copiando banco de dados...
copy tmp\school_system\escola.db "%BACKUP_DIR%\escola_backup_%mydate%_%mytime%.db"

echo.
echo ========================================
echo Backup concluido!
echo Verifique: %BACKUP_DIR%
echo ========================================
echo.
pause
