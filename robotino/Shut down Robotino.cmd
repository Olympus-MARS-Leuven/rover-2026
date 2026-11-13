@echo off
rem Double-click to switch the robot's Raspberry Pi off safely before the power switch.
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0tools\start.ps1" -Shutdown
