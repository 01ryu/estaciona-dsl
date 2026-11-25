@echo off
setlocal
cd /d "%~dp0"
set PYTHONIOENCODING=utf-8
chcp 65001 >nul
py -3 --version >nul 2>&1
if errorlevel 1 (
  set "RUN=python"
) else (
  set "RUN=py -3"
)
%RUN% --version
if errorlevel 1 (
  echo Instale Python 3.10 ou superior e abra novamente.
  pause
  exit /b 2
)
echo.
echo [1/4] Ciclo completo
%RUN% main.py examples/01_ciclo_completo.dsl --trace --verify
pause
echo.
echo [2/4] Tres vagas ocupadas
%RUN% main.py examples/02_ocupacao.dsl --trace --verify
pause
echo.
echo [3/4] Conflito esperado: E005 na linha 6, coluna 1
%RUN% main.py examples/04_erro_ocupada.dsl --trace --verify
pause
echo.
echo [4/4] Testes automatizados
%RUN% run_tests.py
pause
endlocal
