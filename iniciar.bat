@echo off
rem Atalho de dois cliques: roda o iniciar.ps1 sem esbarrar na politica de execucao do Windows.
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0iniciar.ps1" %*
