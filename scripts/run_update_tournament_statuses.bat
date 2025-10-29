@echo off
cd /d C:\Users\nlekk\HMB\HotelMateBackend
"C:\Users\nlekk\HMB\HotelMateBackend\venv\Scripts\python.exe" manage.py update_tournament_statuses
exit /b %ERRORLEVEL%
