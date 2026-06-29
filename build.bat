@echo off
cls
echo ====================================================
echo             STICKYDESK - SCRIPT DE BUILD            
echo ====================================================
echo.

echo [1/3] Ativando ambiente virtual...
:: Usando o caminho absoluto do script para evitar erros de sintaxe no CMD
cd /d "%~dp0"
call ".\.venv\Scripts\activate.bat"

echo [2/3] Garantindo dependencias de desenvolvimento...
python -m pip install -r requirements-dev.txt

echo [3/3] Compilando executavel unico com PyInstaller...
pyinstaller -F -w -i "assets\icon.ico" --add-data "assets;assets" --name="StickyDesk" main.py

if %errorlevel% equ 0 (
    echo.
    echo ====================================================
    echo SUCESSO! O executavel foi gerado em: dist\StickyDesk.exe
    echo Agora voce pode compilar o instalador no Inno Setup.
    echo ====================================================
) else (
    echo.
    echo ERRO: Falha na compilacao com o PyInstaller.
)

pause
