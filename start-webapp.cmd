@echo off
setlocal

set "SCRIPT_DIR=%~dp0"
pushd "%SCRIPT_DIR%frontend" >nul || exit /b 1

echo [INFO] Starting React app...

if not defined HOST set "HOST=0.0.0.0"
if not defined PORT set "PORT=5173"

if defined ARXIVER_DRY_RUN (
    echo [DRY RUN] cd %CD%
    echo [DRY RUN] bun run dev -- --host %HOST% --port %PORT%
    popd >nul
    exit /b 0
)

where bun >nul 2>nul
if errorlevel 1 (
    >&2 echo [ERROR] bun is required but was not found in PATH.
    popd >nul
    exit /b 1
)

bun run dev -- --host %HOST% --port %PORT%
set "EXIT_CODE=%ERRORLEVEL%"
popd >nul
exit /b %EXIT_CODE%