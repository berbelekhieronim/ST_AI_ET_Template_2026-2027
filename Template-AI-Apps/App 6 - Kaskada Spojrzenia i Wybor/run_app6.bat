@echo off
cd /d "%~dp0"
if exist "..\PsychoPy\python.exe" (
  "..\PsychoPy\python.exe" app6_kaskada_spojrzenia.py
) else (
  where py >nul 2>nul
  if %errorlevel%==0 (
    py -3 app6_kaskada_spojrzenia.py
  ) else (
    python app6_kaskada_spojrzenia.py
  )
)
pause
