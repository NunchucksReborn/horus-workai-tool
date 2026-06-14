@echo off
REM ============================================
REM Athena Assistant - Build Windows EXE
REM Double-click file nay de build tu dong
REM ============================================

setlocal enabledelayedexpansion
chcp 65001 >nul

echo.
echo ============================================
echo   Athena Assistant - Build Windows EXE
echo ============================================
echo.

REM --- Kiem tra Python ---
echo [1/6] Kiem tra Python...
where python >nul 2>&1
if errorlevel 1 (
    echo.
    echo [LOI] Khong tim thay Python!
    echo.
    echo Vui long:
    echo   1. Tai Python 3.11 tu https://www.python.org/downloads/
    echo   2. Khi cai, DANH DAU "Add Python to PATH" o buoc dau tien
    echo   3. Chay lai file build-windows.bat
    echo.
    pause
    exit /b 1
)
python --version
echo.

REM --- Tao virtual environment ---
echo [2/6] Tao virtual environment...
if not exist ".venv" (
    python -m venv .venv
    if errorlevel 1 (
        echo [LOI] Tao venv that bai
        pause
        exit /b 1
    )
) else (
    echo     .venv da ton tai, su dung lai
)
echo.

REM --- Activate venv ---
call .venv\Scripts\activate.bat
if errorlevel 1 (
    echo [LOI] Khong the activate venv
    pause
    exit /b 1
)

REM --- Cap nhat pip + cai dependencies ---
echo [3/6] Cai dat Python dependencies (mat vai phut)...
python -m pip install --upgrade pip wheel --quiet
if errorlevel 1 (
    echo [LOI] pip upgrade that bai
    pause
    exit /b 1
)
pip install fastapi "uvicorn[standard]" pywebview python-multipart "pydantic>=2" requests playwright python-dotenv httpx pyinstaller --quiet
if errorlevel 1 (
    echo [LOI] Cai dat that bai
    pause
    exit /b 1
)
echo     OK
echo.

REM --- Cai Playwright Chromium ---
echo [4/6] Cai Playwright Chromium (mat vai phut)...
playwright install chromium
if errorlevel 1 (
    echo [LOI] Playwright install that bai
    pause
    exit /b 1
)
echo.

REM --- Copy ms-playwright vao project root de bundle ---
echo [5/6] Copy ms-playwright vao project root...
set "PLAYWRIGHT_DIR=%USERPROFILE%\AppData\Local\ms-playwright"
if exist "%PLAYWRIGHT_DIR%" (
    if exist "ms-playwright" (
        echo     Xoa ms-playwright cu
        rmdir /s /q "ms-playwright"
    )
    echo     Copy tu %PLAYWRIGHT_DIR%...
    xcopy "%PLAYWRIGHT_DIR%" "ms-playwright\" /E /I /Q /Y >nul
    echo     OK
) else (
    echo [LOI] Khong tim thay %PLAYWRIGHT_DIR%
    echo     Playwright co the da cai o vi tri khac, kiem tra lai.
    pause
    exit /b 1
)
echo.

REM --- Build voi PyInstaller ---
echo [6/6] Build Athena.exe voi PyInstaller (mat vai phut)...
pyinstaller main.spec --noconfirm --clean
if errorlevel 1 (
    echo [LOI] PyInstaller build that bai
    pause
    exit /b 1
)
echo.

REM --- Rename main.exe thanh Athena.exe ---
if exist "dist\main.exe" (
    if exist "dist\Athena.exe" del "dist\Athena.exe"
    ren "dist\main.exe" "Athena.exe"
    echo.
    echo ============================================
    echo   BUILD THANH CONG!
    echo ============================================
    echo.
    echo File exe cua ban: %CD%\dist\Athena.exe
    echo.
    for %%A in ("dist\Athena.exe") do echo Kich thuoc: %%~zA bytes (~%%~zA / 1048576 MB)
    echo.
    echo Ban co the:
    echo   - Copy file dist\Athena.exe cho user
    echo   - Nen thanh .zip de gui qua email/Zalo
    echo.
) else (
    echo [LOI] Khong tim thay dist\main.exe - build co the da fail
    pause
    exit /b 1
)

pause
endlocal
