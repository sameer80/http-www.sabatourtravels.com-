# Auto-start AI SEO Manager on YOUR Windows PC (fixes ERR_CONNECTION_REFUSED on localhost:3000)
# Right-click > Run with PowerShell

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
$CorsOrigins = "http://localhost:3000,http://localhost:3001,http://localhost:3002,http://127.0.0.1:3000,http://127.0.0.1:3001,http://127.0.0.1:3002"

Write-Host "AI SEO Manager - automatic local start" -ForegroundColor Cyan

# Disable proxy (common cause of localhost issues)
Set-ItemProperty "HKCU:\Software\Microsoft\Windows\CurrentVersion\Internet Settings" ProxyEnable 0 -ErrorAction SilentlyContinue
netsh winhttp reset proxy | Out-Null

Set-Location $Root

function Wait-ForBackend {
    param([int]$MaxAttempts = 45)
    for ($i = 0; $i -lt $MaxAttempts; $i++) {
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
        Write-Host "Backend not ready on http://localhost:8000" -ForegroundColor Red
        Write-Host "Check the Backend PowerShell window for Python/pip errors, then open:" -ForegroundColor Yellow
        Write-Host "  http://localhost:3000  (or the port shown in the Frontend window, e.g. 3001)" -ForegroundColor Yellow
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
    $env:CORS_ORIGINS = $CorsOrigins
    docker compose up -d --build
    Write-Host ""
    Write-Host "Waiting for backend..." -ForegroundColor Cyan
    if (-not (Wait-ForBackend)) {
        Write-Host "Docker backend did not become ready. Run: docker compose logs backend" -ForegroundColor Red
        exit 1
    }
    Write-Host "Ready!" -ForegroundColor Green
    Write-Host "  Frontend: http://localhost:3000"
    Write-Host "  API:      http://localhost:8000/docs"
    Write-Host "  Login:    demo@example.com / demo1234"
    Initialize-DemoPortfolio
    Start-Process "http://localhost:3000/dashboard"
    exit 0
}

Write-Host "Docker not found. Starting with Node + Python..." -ForegroundColor Yellow

$python = $null
foreach ($cmd in @("python", "py", "python3")) {
    if (Get-Command $cmd -ErrorAction SilentlyContinue) {
        $python = $cmd
        break
    }
}
if (-not $python) {
    Write-Host "Python not found. Install Python 3.11+ from https://www.python.org/downloads/" -ForegroundColor Red
    Write-Host "During install, check 'Add Python to PATH'." -ForegroundColor Yellow
    pause
    exit 1
}

if (-not (Get-Command node -ErrorAction SilentlyContinue)) {
    Write-Host "Node.js not found. Install LTS from https://nodejs.org/" -ForegroundColor Red
    pause
    exit 1
}

# Backend (keep window open so you can see errors)
$backendCmd = @"
`$env:CORS_ORIGINS='$CorsOrigins'
Set-Location '$Root\backend'
Write-Host 'Installing backend dependencies...' -ForegroundColor Cyan
& '$python' -m pip install -r requirements.txt
Write-Host 'Starting backend on http://localhost:8000 ...' -ForegroundColor Green
& '$python' -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
"@
Start-Process powershell -ArgumentList "-NoExit", "-Command", $backendCmd

Start-Sleep -Seconds 5

# Frontend (Next.js may use 3001 if 3000 is busy - CORS allows both)
$frontendCmd = @"
Set-Location '$Root\frontend'
Write-Host 'Installing frontend dependencies...' -ForegroundColor Cyan
npm install
Write-Host 'Starting frontend (default http://localhost:3000) ...' -ForegroundColor Green
npm run dev
"@
Start-Process powershell -ArgumentList "-NoExit", "-Command", $frontendCmd

Write-Host "Waiting for backend on http://localhost:8000 ..." -ForegroundColor Cyan
if (-not (Wait-ForBackend)) {
    Write-Host ""
    Write-Host "Backend still not ready." -ForegroundColor Red
    Write-Host "1. Look at the 'Backend' PowerShell window for errors." -ForegroundColor Yellow
    Write-Host "2. When it shows 'Application startup complete', refresh the login page." -ForegroundColor Yellow
    Write-Host "3. Open the URL shown in the Frontend window (3000 or 3001)." -ForegroundColor Yellow
    Write-Host ""
    Write-Host "  Login: demo@example.com / demo1234" -ForegroundColor Gray
    pause
    exit 1
}

Write-Host "Opening browser..." -ForegroundColor Green
Initialize-DemoPortfolio
Start-Process "http://localhost:3000/dashboard"
Write-Host "  Frontend: http://localhost:3000 (or 3001 if Next.js picked another port)" -ForegroundColor Green
Write-Host "  API:      http://localhost:8000/docs" -ForegroundColor Green
Write-Host "  Login:    demo@example.com / demo1234" -ForegroundColor Green
