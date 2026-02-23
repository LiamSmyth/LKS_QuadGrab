@echo off
REM ============================================================================
REM Launch Blender HEADLESS with factory settings, load ONLY this addon,
REM and run the test suite.
REM ============================================================================
setlocal

call "%~dp0local_paths.bat"
set SCRIPT=%~dp0tests\blender_test_runner.py

if not exist "%BLENDER_EXE%" (
    echo ERROR: Blender not found at %BLENDER_EXE%
    echo Edit local_paths.bat to set BLENDER_EXE
    pause
    exit /b 1
)

echo ============================================
echo  LKS QuadGrab - Headless Test Suite
echo  Blender: %BLENDER_EXE%
echo ============================================

set BLENDER_USER_SCRIPTS=%BLENDER_USER_SCRIPTS%
"%BLENDER_EXE%" --background --factory-startup --addons lks_quadgrab --python "%SCRIPT%"
set EXIT_CODE=%ERRORLEVEL%

echo.
if %EXIT_CODE% EQU 0 (
    echo ALL TESTS PASSED
) else (
    echo TESTS FAILED (exit code %EXIT_CODE%)
)
echo.
pause
exit /b %EXIT_CODE%
