@echo off
chcp 65001 >nul
setlocal
cd /d "%~dp0"

rem 一键生成 agent 任务上报配置（双击即可，无需懂命令行）
rem 也可带参数直接跑：一键生成配置.bat claude-code 127.0.0.1 我的项目

echo ============================================================
echo  生成 agent 任务上报配置
echo ============================================================
echo.

set "SRC=%~1"
set "IP=%~2"
set "PJ=%~3"

if not "%SRC%"=="" goto run
set /p SRC=1) 你的来源名（如 claude-code / hermes）：
if "%SRC%"=="" set "SRC=my-agent"
set /p IP=2) 看板所在机器 IP（本机直接回车）：
if "%IP%"=="" set "IP=127.0.0.1"
set /p PJ=3) 项目名（可留空）：

:run
echo.
echo 正在生成：来源=%SRC%  地址=http://%IP%:8787  项目=%PJ%
echo.

where python >nul 2>nul
if errorlevel 1 (
  echo [×] 找不到 python 命令。
  echo     请先安装 Python 3.12+ 并把 python 加入 PATH，
  echo     或把本目录下的 make-config.py 拖给 WorkBuddy 让它代跑。
  echo.
  pause
  exit /b 1
)

python "%~dp0make-config.py" --source "%SRC%" --ip "%IP%" --project "%PJ%"

echo.
echo ------------------------------------------------------------
echo  生成完毕。文件在：agent-templates\生成配置\
echo    AGENTS.md / CLAUDE.md / .cursorrules  ^<- 复制到项目根目录
echo    粘贴.txt                              ^<- 临时用，复制其中一段
echo ------------------------------------------------------------
pause
