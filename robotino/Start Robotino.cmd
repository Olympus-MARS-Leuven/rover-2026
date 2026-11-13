@echo off
rem Double-click to connect to the robot, start it and open the control page.
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0tools\start.ps1" %*
