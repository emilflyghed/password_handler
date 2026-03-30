@echo off
echo Building Password Vault...
echo.

pyinstaller --noconfirm --onefile --windowed ^
    --name "PasswordVault" ^
    --add-data "C:\Users\Admin\AppData\Local\Programs\Python\Python313\Lib\site-packages\customtkinter;customtkinter" ^
    --hidden-import customtkinter ^
    --icon NUL ^
    main.py

echo.
if exist "dist\PasswordVault.exe" (
    echo Build successful! Your .exe is at: dist\PasswordVault.exe
) else (
    echo Build failed. Check the output above for errors.
)
pause
