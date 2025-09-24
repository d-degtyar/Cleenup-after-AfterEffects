@echo off

:: Задайте путь к папке здесь
set "TARGET_FOLDER="C:\Users\Public"

echo Scanning for empty folders in: %TARGET_FOLDER%
echo.

:: Проверяем существование папки
if not exist "%TARGET_FOLDER%" (
    echo Folder not found: %TARGET_FOLDER%
    pause
    exit
)

echo Looking for empty folders...
echo.

:: Ищем пустые папки, используя полные пути
for /d %%D in ("%TARGET_FOLDER%\*") do (
    dir "%%D" /a /b 2>nul | findstr "^" >nul || (
        echo Empty folder found: %%~nxD
    )
)

echo.
set /p "confirm=Delete empty folders? (y/n): "

if /i "%confirm%"=="y" (
    for /d %%D in ("%TARGET_FOLDER%\*") do (
        dir "%%D" /a /b 2>nul | findstr "^" >nul || (
            echo Deleting: %%~nxD
            rd "%%D"
        )
    )
    echo Deletion complete.
) else (
    echo Operation cancelled.
)

echo.
pause
