@echo off
setlocal
cd /d "%~dp0"

where py >nul 2>nul
if not errorlevel 1 (
    py -3 --version >nul 2>nul
    if not errorlevel 1 set "PYTHON=py -3"
)

if defined PYTHON goto python_ready
where python >nul 2>nul
if errorlevel 1 (
    echo Khong tim thay Python 3. Hay cai Python va chon "Add Python to PATH".
    pause
    exit /b 1
)
set "PYTHON=python"

:python_ready
if not exist ".dependencies_installed" goto check_dependencies
findstr /x /c:"dependencies-v2" ".dependencies_installed" >nul
if not errorlevel 1 goto run_app

:check_dependencies
%PYTHON% -c "import pyautogui, pydirectinput, pyperclip, keyboard, requests; from PIL import ImageGrab; from bs4 import BeautifulSoup" >nul 2>nul
if not errorlevel 1 goto dependencies_ready

echo Chua cai du cac thu vien can thiet cho ung dung.
choice /C YN /M "Ban co muon cai dat ngay khong"
if errorlevel 2 (
    echo Chua cai dat thu vien. Ung dung se dong.
    pause
    exit /b 1
)

%PYTHON% -m pip install -r requirements.txt
if errorlevel 1 (
    echo Cai dat that bai. Hay kiem tra ket noi Internet va Python/pip.
    pause
    exit /b 1
)

%PYTHON% -c "import pyautogui, pydirectinput, pyperclip, keyboard, requests; from PIL import ImageGrab; from bs4 import BeautifulSoup" >nul 2>nul
if errorlevel 1 (
    echo Cai dat xong nhung van khong the nap du cac thu vien.
    pause
    exit /b 1
)

:dependencies_ready
echo dependencies-v2> ".dependencies_installed"

:run_app
%PYTHON% main.py
if errorlevel 1 (
    echo Ung dung ket thuc do co loi.
    pause
)
endlocal
