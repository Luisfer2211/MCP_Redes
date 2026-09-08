@echo off
REM Deploy FitTrack MCP remote server to Google Cloud Run
REM Prerequisites: gcloud CLI, billing enabled, project set

set PROJECT_ID=%1
set REGION=us-central1
set SERVICE=fittrack-mcp

if "%PROJECT_ID%"=="" (
  echo Usage: deploy.bat YOUR_GCP_PROJECT_ID
  exit /b 1
)

echo Copying shared server modules...
if exist server rmdir /s /q server
mkdir server
copy ..\fittrack-mcp\server\tools.py server\
copy ..\fittrack-mcp\server\protocol.py server\

echo Deploying to Cloud Run...
gcloud config set project %PROJECT_ID%
gcloud run deploy %SERVICE% ^
  --source . ^
  --region %REGION% ^
  --allow-unauthenticated ^
  --platform managed

echo.
echo After deploy, set FITTRACK_REMOTE_URL in chatbot/.env to the service URL.
echo Example: FITTRACK_REMOTE_URL=https://fittrack-mcp-xxxxx-uc.a.run.app
