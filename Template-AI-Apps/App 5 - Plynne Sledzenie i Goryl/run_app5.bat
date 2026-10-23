@echo off
cd /d "%~dp0"
if exist "..\PsychoPy\python.exe" (
  "..\PsychoPy\python.exe" app5_plynne_sledzenie_i_goryl.py
) else (
  where py >nul 2>nul
  if %errorlevel%==0 (
    py -3 app5_plynne_sledzenie_i_goryl.py
  ) else (
    python app5_plynne_sledzenie_i_goryl.py
  )
)
pause
