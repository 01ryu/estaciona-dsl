@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo EstacionaDSL - mantenha esta janela aberta durante a apresentacao.
echo Endereco: http://127.0.0.1:8766
echo Se o painel ja estiver rodando, use o navegador sem abrir outra instancia.
where py >nul 2>nul
if errorlevel 1 (
  python gui.py --port 8766
) else (
  py -3 gui.py --port 8766
)
pause
