@echo off
REM Deploy FitTrack chatbot host to Google Cloud Run
REM Reads DEEPSEEK_API_KEY from .env in this folder (not committed to git)

set REGION=us-central1
set SERVICE=fittrack-chatbot
set FITTRACK_URL=https://fittrack-mcp-907980440492.us-central1.run.app

if not exist .env (
  echo Error: create chatbot/.env with DEEPSEEK_API_KEY first
  exit /b 1
)

for /f "usebackq tokens=1,* delims==" %%A in (".env") do (
  if "%%A"=="DEEPSEEK_API_KEY" set DEEPSEEK_API_KEY=%%B
)

if "%DEEPSEEK_API_KEY%"=="" (
  echo Error: DEEPSEEK_API_KEY not found in .env
  exit /b 1
)

echo Deploying %SERVICE% to Cloud Run...
gcloud run deploy %SERVICE% ^
  --source . ^
  --region %REGION% ^
  --allow-unauthenticated ^
  --platform managed ^
  --memory 1Gi ^
  --cpu 1 ^
  --timeout 300 ^
  --set-env-vars "DEEPSEEK_API_KEY=%DEEPSEEK_API_KEY%,FITTRACK_MODE=remote,FITTRACK_REMOTE_URL=%FITTRACK_URL%"

echo.
echo Chatbot URL will be shown above. Open it in any browser.
