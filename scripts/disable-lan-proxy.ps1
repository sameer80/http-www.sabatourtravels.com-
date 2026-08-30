# Disable Windows LAN / system proxy (run on YOUR Windows PC as your user)
# Right-click > Run with PowerShell, or: powershell -ExecutionPolicy Bypass -File disable-lan-proxy.ps1

Write-Host "Disabling Windows proxy settings..." -ForegroundColor Cyan

# Internet Options > Connections > LAN settings (manual proxy off)
Set-ItemProperty -Path "HKCU:\Software\Microsoft\Windows\CurrentVersion\Internet Settings" -Name ProxyEnable -Value 0 -ErrorAction SilentlyContinue
Set-ItemProperty -Path "HKCU:\Software\Microsoft\Windows\CurrentVersion\Internet Settings" -Name ProxyServer -Value "" -ErrorAction SilentlyContinue
Set-ItemProperty -Path "HKCU:\Software\Microsoft\Windows\CurrentVersion\Internet Settings" -Name AutoDetect -Value 0 -ErrorAction SilentlyContinue
Set-ItemProperty -Path "HKCU:\Software\Microsoft\Windows\CurrentVersion\Internet Settings" -Name AutoConfigURL -Value "" -ErrorAction SilentlyContinue

# Windows 11 Settings > Network & Internet > Proxy
$proxyPath = "HKCU:\Software\Microsoft\Windows\CurrentVersion\Internet Settings"
if (Test-Path $proxyPath) {
    New-ItemProperty -Path $proxyPath -Name ProxyEnable -Value 0 -PropertyType DWord -Force | Out-Null
}

# Reset WinHTTP proxy (used by some apps/services)
netsh winhttp reset proxy | Out-Null

# Clear user environment proxy vars for current session
$env:HTTP_PROXY = $null
$env:HTTPS_PROXY = $null
$env:ALL_PROXY = $null
[Environment]::SetEnvironmentVariable("HTTP_PROXY", $null, "User")
[Environment]::SetEnvironmentVariable("HTTPS_PROXY", $null, "User")
[Environment]::SetEnvironmentVariable("ALL_PROXY", $null, "User")

Write-Host "Done. Proxy disabled." -ForegroundColor Green
Write-Host "Restart Edge/Chrome, then open: http://localhost:3000" -ForegroundColor Yellow
Read-Host "Press Enter to close"
