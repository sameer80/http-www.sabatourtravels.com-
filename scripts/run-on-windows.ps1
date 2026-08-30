# Paste this entire block into PowerShell on your Windows PC
Set-Location $PSScriptRoot\..

Write-Host "Pulling latest code..." -ForegroundColor Cyan
git pull origin cursor/ai-seo-manager-mvp-4db6
if ($LASTEXITCODE -ne 0) { Write-Host "Git pull failed. Check you are in the repo folder." -ForegroundColor Red; pause; exit 1 }

Write-Host "Starting AI SEO Manager..." -ForegroundColor Cyan
& "$PSScriptRoot\start-local-windows.ps1"
