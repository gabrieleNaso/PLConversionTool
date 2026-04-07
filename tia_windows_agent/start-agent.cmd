@echo off
powershell -NoExit -ExecutionPolicy Bypass -File "%~dp0run-agent.ps1" -PauseOnExit
