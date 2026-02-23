@echo off
REM ============================================================================
REM Launch Blender WITH UI, factory settings, loading ONLY this addon.
REM Use this to manually test the addon in a clean environment.
REM ============================================================================
setlocal

call "%~dp0local_paths.bat"

if not exist "%BLENDER_EXE%" (
    echo ERROR: Blender not found at %BLENDER_EXE%
    echo Edit local_paths.bat to set BLENDER_EXE
    pause
    exit /b 1
)

echo ============================================
echo  LKS QuadGrab - UI Factory Launch
echo  Blender: %BLENDER_EXE%
echo ============================================

set BLENDER_USER_SCRIPTS=%BLENDER_USER_SCRIPTS%
"%BLENDER_EXE%" --factory-startup --addons lks_quadgrab
