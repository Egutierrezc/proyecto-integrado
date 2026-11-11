@echo off
title Servidor Django - Tribu / Veterinaria
cd /d %~dp0

echo [1/2] Verificando entorno virtual...
if exist venv\Scripts\activate.bat (
    call venv\Scripts\activate.bat
    echo Entorno virtual 'venv' activado.
) else if exist .venv\Scripts\activate.bat (
    call .venv\Scripts\activate.bat
    echo Entorno virtual '.venv' activado.
) else (
    echo No se encontró un entorno virtual predeterminado, usando Python global...
)

echo [2/2] Iniciando servidor en http://127.0.0.1:8000/ ...
python manage.py runserver

pause