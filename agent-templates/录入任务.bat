@echo off
chcp 65001 >nul
setlocal
cd /d "%~dp0"

rem 手动往 3D 看板补一条任务（双击即可）
rem 也可带参数直接跑：录入任务.bat "标题" cfo in_progress high

echo ============================================================
echo  录一条任务到 3D 看板
echo ============================================================
echo.

set "TITLE=%~1"
set "DEPT=%~2"
set "STATUS=%~3"
set "PRIO=%~4"

if not "%TITLE%"=="" goto run
set /p TITLE=标题（必填）：
if "%TITLE%"=="" (
  echo 标题为空，已取消。
  pause
  exit /b 1
)
echo 部门：cfo 财务 / cmo 营销 / cto 技术 / coo 运营 / cpo 产品 / cro 风控 / ceo 战略 / meeting 会议
set /p DEPT=部门（可留空，留空则按标题自动判）：
set /p STATUS=状态（回车=待办 todo；也可填 in_progress / done / blocked）：
set /p PRIO=优先级（回车=中；也可填 high / low）：

:run
if "%STATUS%"=="" set "STATUS=todo"
if "%PRIO%"=="" set "PRIO=medium"

where python >nul 2>nul
if errorlevel 1 (
  echo [×] 找不到 python 命令，无法录入。
  echo     替代办法：打开看板 http://127.0.0.1:8787/ ，或对 WorkBuddy 说「记到看板」。
  echo.
  pause
  exit /b 1
)

echo.
python "%~dp0python-stdlib.py" add "%TITLE%" --dept "%DEPT%" --status "%STATUS%" --priority "%PRIO%" --source manual

echo.
echo ------------------------------------------------------------
echo  看板地址：http://127.0.0.1:8787/
echo ------------------------------------------------------------
pause
