@echo off
rem Avvia StruttureMenni: server locale + browser. Richiede "uv" (https://docs.astral.sh/uv/).
cd /d "%~dp0"
where uv >nul 2>nul
if errorlevel 1 (
  echo uv non trovato. Installarlo da https://docs.astral.sh/uv/ e riprovare.
  pause
  exit /b 1
)
uv run python scripts\avvia.py %*
pause
