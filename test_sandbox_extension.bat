@echo off
REM ============================================================================
REM Sandbox Extension Test
REM
REM Builds the extension zip (or pulls from gh-pages with --remote),
REM extracts it to a temp sandbox, and runs Blender headless against it
REM to verify the packaged extension loads and registers correctly.
REM
REM Usage:
REM   test_sandbox_extension.bat            Build locally + test
REM   test_sandbox_extension.bat --remote   Pull from gh-pages + test
REM ============================================================================
setlocal

call "%~dp0local_paths.bat"

echo ============================================
echo  LKS QuadGrab - Sandbox Extension Test
echo ============================================

python "%~dp0test_sandbox_extension.py" %*
set EXIT_CODE=%ERRORLEVEL%

echo.
if %EXIT_CODE% EQU 0 (
    echo SANDBOX TEST PASSED
) else (
    echo SANDBOX TEST FAILED (exit code %EXIT_CODE%)
)
echo.
pause
exit /b %EXIT_CODE%
