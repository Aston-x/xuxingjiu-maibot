@echo off
REM ============================================================
REM  Xuxingjiu (MaiBot edition) - one-shot launcher - TEMPLATE
REM
REM  Replace the paths below with your own install locations.
REM  IMPORTANT: this file MUST stay pure ASCII.
REM    cmd.exe decodes .bat with the ANSI code page (936 on zh-CN).
REM    Chinese comments in a .bat get mis-decoded into garbage and
REM    the whole script falls apart with "'xxx' is not recognized".
REM    Put explanations in the README instead.
REM
REM  Order matters: ComfyUI eats a lot of RAM and VRAM, so it goes
REM  last. If RAM is tight, stop ComfyUI before starting the rest.
REM ============================================================
setlocal
chcp 65001 >nul 2>&1
set PYTHONUTF8=1
set PYTHONIOENCODING=utf-8
set PYTHONPATH=

REM A sandbox or some VPNs inject HTTP_PROXY, which breaks every model API call.
for %%v in (HTTP_PROXY HTTPS_PROXY http_proxy https_proxy ALL_PROXY all_proxy) do set "%%v="

set "MAIBOT=D:\xuxingjiu\MaiBot"
set "SNOWLUMA=D:\xuxingjiu\SnowLuma\app"
set "GSV=D:\xuxingjiu\GPT-SoVITS"
set "COMFY=D:\xuxingjiu\ComfyUI"
set "QQEXE=C:\Program Files\Tencent\QQNT\QQ.exe"

echo [1/6] MaiBot (the brain)...
tasklist /FI "IMAGENAME eq python.exe" | find /I "bot.py" >nul || (
  start "" /D "%MAIBOT%" "%MAIBOT%\.venv\Scripts\python.exe" bot.py
  timeout /t 25 /nobreak >nul
)

echo [2/6] GPT-SoVITS api_v2 (voice)...
tasklist /FI "IMAGENAME eq python.exe" | find /I "api_v2" >nul || (
  start "" /D "%GSV%" "%GSV%\runtime\python.exe" api_v2.py -a 127.0.0.1 -p 9880
)

echo [3/6] OneBot endpoint (SnowLuma OR NapCat - enable exactly one)...
REM --- SnowLuma: hook only, the desktop QQ keeps its full UI ---
tasklist /FI "IMAGENAME eq node.exe" | find /I "node.exe" >nul || (
  set SNOWLUMA_ACCEPT_EULA=1
  set SNOWLUMA_ACCEPT_PRIVACY=1
  start "" /D "%SNOWLUMA%" "%SNOWLUMA%\node.exe" index.mjs
  timeout /t 12 /nobreak >nul
)
REM --- NapCat: replaces the QQ entry point, QQ becomes a headless protocol end ---
REM --- (MUTUALLY EXCLUSIVE with SnowLuma) ---
REM start "" /D "<your NapCat dir>" "<your NapCat dir>\NapCatWinBootMain.exe"

echo [4/6] QQ desktop client (must already be logged in)...
tasklist /FI "IMAGENAME eq QQ.exe" | find /I "QQ.exe" >nul || (
  start "" "%QQEXE%"
  timeout /t 10 /nobreak >nul
)

echo [5/6] Environment check...
"%MAIBOT%\.venv\Scripts\python.exe" "%~dp0check_env.py" --maibot "%MAIBOT%"

echo [6/6] ComfyUI (image backend - last, it eats VRAM and RAM)...
netstat -ano | find ":8188" | find "LISTENING" >nul || (
  set PYTORCH_ALLOC_CONF=expandable_segments:True
  start "" /D "%COMFY%" "%COMFY%\.venv\Scripts\python.exe" -s main.py --windows-standalone-build
)

echo.
echo ============================================
echo  MaiBot WebUI   : http://127.0.0.1:8001
echo  SnowLuma WebUI : http://127.0.0.1:5099
echo  ComfyUI        : http://127.0.0.1:8188
echo ============================================
timeout /t 15 /nobreak >nul
endlocal
