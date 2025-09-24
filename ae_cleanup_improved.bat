@echo off
setlocal enabledelayedexpansion

:: Перевіряємо існування Report.txt
if not exist "Report.txt" (
    echo [ERROR] Report.txt not found!
    pause
    exit /b 1
)

:: Створюємо тимчасові файли
set "files_list=%temp%\files_to_delete.txt"
set "sequences_list=%temp%\sequences_to_delete.txt"
set "log_file=%temp%\cleanup_log.txt"

if exist "!files_list!" del "!files_list!"
if exist "!sequences_list!" del "!sequences_list!"
if exist "!log_file!" del "!log_file!"

echo Processing Report.txt...
echo Start time: %date% %time% > "!log_file!"
echo.

set /a file_count=0
set /a sequence_count=0
set /a missing_files=0

:: Обробляємо файл Report.txt
for /f "usebackq delims=" %%a in ("Report.txt") do (
    set "line=%%a"
    
    :: Видаляємо табуляцію (використовуємо справжній символ табуляції)
    set "line=!line:	=!"
    
    :: Перевіряємо чи це пустий рядок
    if not "!line!"=="" (
        :: Перевіряємо чи це послідовність
        echo !line! | findstr /b "Sequence" >nul
        if !errorlevel! equ 0 (
            echo Found sequence: !line!
            echo !line! >> "!sequences_list!"
            set /a sequence_count+=1
        ) else (
            :: Перевіряємо чи це файл з повним шляхом (починається з диска або UNC)
            set "first_char=!line:~0,1!"
            set "second_char=!line:~1,1!"
            set "third_char=!line:~2,1!"
            
            :: Логіка для визначення файлів: або "X:\" або "\\server"
            if "!second_char!"==":" if "!third_char!"=="\" (
                set "is_file=1"
            ) else if "!first_char!"=="\" if "!line:~1,1!"=="\" (
                set "is_file=1"
            ) else (
                set "is_file=0"
            )
            
            if "!is_file!"=="1" (
                if exist "!line!" (
                    echo Found file: !line!
                    echo !line! >> "!files_list!"
                    set /a file_count+=1
                ) else (
                    echo [MISSING] File not found: !line!
                    echo [MISSING] !line! >> "!log_file!"
                    set /a missing_files+=1
                )
            )
        )
    )
)

:: Показуємо статистику
echo.
echo ===========================================
echo CLEANUP SUMMARY:
echo ===========================================
echo Found !file_count! files for deletion
echo Found !sequence_count! sequences for manual deletion  
echo Missing !missing_files! files (already deleted or moved)
echo ===========================================
echo.

:: Показуємо файли для видалення
if !file_count! gtr 0 (
    echo FILES TO DELETE:
    echo ---------------
    type "!files_list!"
    echo ---------------
) else (
    echo No individual files found for deletion.
)
echo.

:: Показуємо послідовності
if !sequence_count! gtr 0 (
    echo SEQUENCES FOR MANUAL DELETION:
    echo ------------------------------
    type "!sequences_list!"
    echo ------------------------------
) else (
    echo No sequences found.
)
echo.

:: Підтвердження видалення файлів
if !file_count! gtr 0 (
    set /p "confirm=Delete !file_count! individual files? (y/n): "
    
    if /i "!confirm!"=="y" (
        set /a deleted_count=0
        set /a error_count=0
        
        echo.
        echo Deleting files...
        echo Deletion started: %time% >> "!log_file!"
        
        for /f "usebackq delims=" %%a in ("!files_list!") do (
            echo Deleting: %%a
            del /f "%%a" 2>nul
            
            if !errorlevel! equ 0 (
                echo [SUCCESS] %%a >> "!log_file!"
                set /a deleted_count+=1
            ) else (
                echo [ERROR] Failed to delete: %%a
                echo [ERROR] %%a >> "!log_file!"
                set /a error_count+=1
            )
        )
        
        echo.
        echo ===========================================
        echo DELETION RESULTS:
        echo Successfully deleted: !deleted_count! files
        echo Failed to delete: !error_count! files
        echo ===========================================
        
        if !error_count! gtr 0 (
            echo.
            echo Check log file for details: !log_file!
        )
    ) else (
        echo.
        echo File deletion cancelled by user.
    )
) else (
    echo No files to delete.
)

:: Нагадування про послідовності
if !sequence_count! gtr 0 (
    echo.
    echo [REMINDER] Please manually delete !sequence_count! sequence folder(s).
    echo Check the list above for folder paths.
)

:: Очищення тимчасових файлів
if exist "!files_list!" del "!files_list!"
if exist "!sequences_list!" del "!sequences_list!"

echo.
echo Cleanup process completed.
echo Log file: !log_file!
pause