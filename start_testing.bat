@echo off
REM Start API Server for End-to-End Testing

echo ================================================================================
echo   Starting API Server with Full Logging
echo ================================================================================
echo.

REM Check if ANTHROPIC_API_KEY is set
if "%ANTHROPIC_API_KEY%"=="" (
    echo ERROR: ANTHROPIC_API_KEY environment variable not set!
    echo.
    echo Please set it first:
    echo   set ANTHROPIC_API_KEY=your-key-here
    echo.
    echo Or add to your system environment variables.
    echo.
    pause
    exit /b 1
)

echo API Key: %ANTHROPIC_API_KEY:~0,10%...
echo.

echo ================================================================================
echo   Configuration
echo ================================================================================
echo   Port: 8000
echo   Settings: .claude/settings.json
echo   S3 Skills: Enabled
echo   S3 Bucket: cerebricks-studio-agent-skills
echo   S3 Prefix: skills_phase3/
echo ================================================================================
echo.

echo Starting server...
echo Open Postman and import: postman_collection.json
echo Test endpoint: http://localhost:8000/status
echo.
echo Terminal logs will appear below:
echo ================================================================================
echo.

python api_server.py

pause
