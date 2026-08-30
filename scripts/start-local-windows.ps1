# Auto-start AI SEO Manager on YOUR Windows PC (fixes ERR_CONNECTION_REFUSED on localhost:3000)
# Right-click > Run with PowerShell

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)

Write-Host "AI SEO Manager - automatic local start" -ForegroundColor Cyan

# Disable proxy (common cause of localhost issues)
Set-ItemProperty "HKCU:\Software\Microsoft\Windows\CurrentVersion\Internet Settings" ProxyEnable 0 -ErrorAction SilentlyContinue
netsh winhttp reset proxy | Out-Null

Set-Location $Root

if (Get-Command docker -ErrorAction SilentlyContinue) {
    Write-Host "Starting with Docker Compose..." -ForegroundColor Green
    docker compose up -d --build
    Write-Host ""
    Write-Host "Ready!" -ForegroundColor Green
    Write-Host "  Frontend: http://localhost:3000"
    Write-Host "  API:      http://localhost:8000/docs"
    Write-Host "  Login:    demo@example.com / demo1234"
    Start-Process "http://localhost:3000"
    exit 0
}

Write-Host "Docker not found. Starting with Node + Python..." -ForegroundColor Yellow

# Backend
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$Root\backend'; pip install -r requirements.txt; uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload"

Start-Sleep -Seconds 3

# Frontend
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$Root\frontend'; npm install; npm run dev"

Start-Sleep -Seconds 8
Write-Host "Opening browser..." -ForegroundColor Green
Start-Process "http://localhost:3000"
Write-Host "  Login: demo@example.com / demo1234"
