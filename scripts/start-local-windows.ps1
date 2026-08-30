# Auto-start AI SEO Manager on YOUR Windows PC (fixes ERR_CONNECTION_REFUSED on localhost:3000)
# Right-click > Run with PowerShell

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)

Write-Host "AI SEO Manager - automatic local start" -ForegroundColor Cyan

# Disable proxy (common cause of localhost issues)
Set-ItemProperty "HKCU:\Software\Microsoft\Windows\CurrentVersion\Internet Settings" ProxyEnable 0 -ErrorAction SilentlyContinue
netsh winhttp reset proxy | Out-Null

Set-Location $Root

function Wait-ForBackend {
    for ($i = 0; $i -lt 30; $i++) {
        try {
            $r = Invoke-WebRequest -Uri "http://localhost:8000/api/health" -UseBasicParsing -TimeoutSec 2
            if ($r.StatusCode -eq 200) { return $true }
        } catch {}
        Start-Sleep -Seconds 2
    }
    return $false
}

function Initialize-DemoPortfolio {
    if (-not (Wait-ForBackend)) {
        Write-Host "Backend not ready - open http://localhost:3000 and login manually." -ForegroundColor Yellow
        return
    }

    $email = "demo@example.com"
    $password = "demo1234"
    $loginBody = @{
        username = $email
        password = $password
    }

    try {
        $token = (Invoke-RestMethod -Uri "http://localhost:8000/api/auth/login" -Method Post -ContentType "application/x-www-form-urlencoded" -Body $loginBody).access_token
    } catch {
        $register = @{ email = $email; password = $password; full_name = "Demo User"; organization = "Saba Tours" } | ConvertTo-Json
        Invoke-RestMethod -Uri "http://localhost:8000/api/auth/register" -Method Post -ContentType "application/json" -Body $register | Out-Null
        $token = (Invoke-RestMethod -Uri "http://localhost:8000/api/auth/login" -Method Post -ContentType "application/x-www-form-urlencoded" -Body $loginBody).access_token
    }

    $headers = @{ Authorization = "Bearer $token" }
    $sites = Invoke-RestMethod -Uri "http://localhost:8000/api/portfolio/bootstrap/saba-tours" -Method Post -Headers $headers
    Write-Host "Auto-setup complete: $($sites.Count) websites configured" -ForegroundColor Green
    foreach ($site in $sites) {
        Write-Host "  - $($site.name) ($($site.domain))" -ForegroundColor Gray
    }
}

if (Get-Command docker -ErrorAction SilentlyContinue) {
    Write-Host "Starting with Docker Compose..." -ForegroundColor Green
    docker compose up -d --build
    Write-Host ""
    Write-Host "Ready!" -ForegroundColor Green
    Write-Host "  Frontend: http://localhost:3000"
    Write-Host "  API:      http://localhost:8000/docs"
    Write-Host "  Login:    demo@example.com / demo1234"
    Start-Sleep -Seconds 5
    Initialize-DemoPortfolio
    Start-Process "http://localhost:3000/dashboard"
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

Initialize-DemoPortfolio
Start-Process "http://localhost:3000/dashboard"
Write-Host "  Login:    demo@example.com / demo1234"
Write-Host "  Dashboard: http://localhost:3000/dashboard"
