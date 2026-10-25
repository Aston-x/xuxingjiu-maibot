@echo off
REM ============================================================
REM  许杏玖（MaiBot 版）一键启动 —— 模板
REM  把 G:\AI\ 换成你的实际安装路径后再用。
REM  顺序有讲究：先停/跳过吃内存的 ComfyUI，最后再起它。
REM ============================================================
setlocal
chcp 65001 >nul 2>&1
set PYTHONUTF8=1
set PYTHONIOENCODING=utf-8
set PYTHONPATH=

REM ⚠ 沙箱/某些 VPN 会注入 HTTP_PROXY，会让模型 API 全部 Connection error
for %%v in (HTTP_PROXY HTTPS_PROXY http_proxy https_proxy ALL_PROXY all_proxy) do set "%%v="

set "MAIBOT=G:\AI\许杏玖-MaiBot\MaiBot"
set "SNOWLUMA=G:\AI\许杏玖-MaiBot\SnowLuma\app"
set "GSV=G:\AI\Models\GPT-SoVITS-v2pro"

echo [1/6] MaiBot（对话大脑）...
tasklist /FI "IMAGENAME eq python.exe" | find /I "bot.py" >nul || (
  start "" /D "%MAIBOT%" "%MAIBOT%\.venv\Scripts\python.exe" bot.py
  timeout /t 25 /nobreak >nul
)

echo [2/6] GPT-SoVITS api_v2（语音）...
tasklist /FI "IMAGENAME eq python.exe" | find /I "api_v2" >nul || (
  start "" /D "%GSV%" "%GSV%\runtime\python.exe" api_v2.py -a 127.0.0.1 -p 9880
)

echo [3/6] OneBot 端（SnowLuma / NapCat，二选一，按你装的是哪个开）...
REM --- SnowLuma：只 hook，QQ 完整 UI 照常跑 ---
tasklist /FI "IMAGENAME eq node.exe" | find /I "node.exe" >nul || (
  set SNOWLUMA_ACCEPT_EULA=1
  set SNOWLUMA_ACCEPT_PRIVACY=1
  start "" /D "%SNOWLUMA%" "%SNOWLUMA%\node.exe" index.mjs
  timeout /t 12 /nobreak >nul
)
REM --- NapCat：替换 QQ 入口，QQ 变纯协议端（与 SnowLuma 互斥！）---
REM start "" /D "<你的 NapCat 目录>" "<你的 NapCat 目录>\NapCatWinBootMain.exe"

echo [4/6] QQ 桌面端（需已登录）...
tasklist /FI "IMAGENAME eq QQ.exe" | find /I "QQ.exe" >nul || (
  start "" "B:\QQ\QQ.exe"
  timeout /t 10 /nobreak >nul
)

echo [5/6] 环境体检...
"%MAIBOT%\.venv\Scripts\python.exe" "%~dp0check_env.py" --maibot "%MAIBOT%"

echo [6/6] ComfyUI（画图后端，放最后：它吃显存也吃内存）...
netstat -ano | find ":8188" | find "LISTENING" >nul || (
  set PYTORCH_ALLOC_CONF=expandable_segments:True
  start "" /D "G:\AI\ComfyUI" "G:\AI\ComfyUI\.venv\Scripts\python.exe" -s main.py --windows-standalone-build
)

echo.
echo ============================================
echo  MaiBot WebUI : http://127.0.0.1:8001
echo  SnowLuma WebUI: http://127.0.0.1:5099
echo  ComfyUI      : http://127.0.0.1:8188
echo ============================================
timeout /t 15 /nobreak >nul
endlocal
