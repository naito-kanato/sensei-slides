@echo off
rem sensei-slides setup (Windows). The steps and messages are in setup.ps1 next to this file.
rem Keep this file ASCII only: after chcp 65001, cmd misreads lines with Japanese text.
cd /d "%~dp0.."
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0setup.ps1"
exit /b %errorlevel%
