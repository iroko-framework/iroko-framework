@echo off
title Iroko Ontology Manager
cd /d "%~dp0scripts\manage"

echo Starting Iroko Ontology Manager...
echo Open: http://localhost:5050
echo Close this window to stop the server.
echo.

start "" http://localhost:5050
python app.py
