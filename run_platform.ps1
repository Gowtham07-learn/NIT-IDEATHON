# DPI Platform Launcher (PowerShell Edition)
$ErrorActionPreference = "Continue"

Write-Host "===================================================" -ForegroundColor Cyan
Write-Host "  DPI PLATFORM - LOCAL AI EDITION (PowerShell)" -ForegroundColor Cyan
Write-Host "===================================================" -ForegroundColor Cyan

# 1. Check for Ollama
Write-Host "[1/6] Checking AI Dependencies (Ollama)..."
$ollamaPath = Get-Command ollama -ErrorAction SilentlyContinue | Select-Object -ExpandProperty Source
if (-not $ollamaPath) {
    # Try common C: drive path
    $defaultPath = "$env:LOCALAPPDATA\Programs\Ollama\ollama.exe"
    if (Test-Path $defaultPath) {
        $ollamaPath = $defaultPath
        Write-Host "[OK] Ollama detected at $ollamaPath" -ForegroundColor Green
    }
    else {
        Write-Host "[!] WARNING: 'ollama' command not found." -ForegroundColor Yellow
        Write-Host "[!] Please install Ollama from: https://ollama.com/download" -ForegroundColor Yellow
        Write-Host "[!] Until then, AI Advisor will run in 'Manual Mode'." -ForegroundColor Yellow
    }
}
else {
    Write-Host "[OK] Ollama found in PATH." -ForegroundColor Green
}

if ($ollamaPath) {
    Write-Host "[OK] Starting Ollama background service on Port 11435..." -ForegroundColor Green
    $env:OLLAMA_HOST = "127.0.0.1:11435"
    $env:OLLAMA_PORT = "11435" # So python knows which port to call
    Start-Process -FilePath $ollamaPath -ArgumentList "serve" -WindowStyle Minimized
    $AI_READY = $true
    Start-Sleep -Seconds 3
    
    Write-Host "[2/6] Verifying Mistral Model..."
    Start-Process -FilePath $ollamaPath -ArgumentList "pull mistral" -WindowStyle Minimized
}
else {
    Write-Host "[2/6] Skipping model pull (Ollama missing)." -ForegroundColor Gray
    $AI_READY = $false
}

# 2. Python dependencies
Write-Host "[3/6] Installing Python Dependencies..."
pip install -r requirements.txt --quiet

# 3. Start Microservices in PowerShell windows
Write-Host "[4/6] Starting Microservices..."
Start-Process powershell -ArgumentList "-NoExit", "-Command", "`$Host.UI.RawUI.WindowTitle = 'Services: Gateway'; uvicorn services.gateway:app --port 8000" -WindowStyle Normal
Start-Process powershell -ArgumentList "-NoExit", "-Command", "`$Host.UI.RawUI.WindowTitle = 'Services: UPI PSP'; uvicorn services.upi_psp:app --port 8001" -WindowStyle Normal
Start-Process powershell -ArgumentList "-NoExit", "-Command", "`$Host.UI.RawUI.WindowTitle = 'Services: Issuer Bank'; uvicorn services.issuer_bank:app --port 8002" -WindowStyle Normal

# 4. Start Telemetry
Write-Host "[5/6] Starting Telemetry Collector & Incident Backend..."
Start-Process powershell -ArgumentList "-NoExit", "-Command", "`$Host.UI.RawUI.WindowTitle = 'Telemetry Collector'; python telemetry/collector.py" -WindowStyle Normal
Start-Process powershell -ArgumentList "-NoExit", "-Command", "`$Host.UI.RawUI.WindowTitle = 'Incident Backend'; python backend/routes.py" -WindowStyle Normal

# 5. Start Dashboard
Write-Host "[6/6] Launching Multi-Page Forensic Dashboard..."
Start-Process powershell -ArgumentList "-Command", "streamlit run frontend/streamlit_app.py" -WindowStyle Normal

Write-Host ""
Write-Host "===================================================" -ForegroundColor Green
Write-Host "DPI Platform is LIVE!" -ForegroundColor Green
Write-Host "===================================================" -ForegroundColor Green
Write-Host ""
Write-Host "Dashboard: http://localhost:8501"
Write-Host "Gateway:   http://localhost:8000"
Write-Host ""
Write-Host "Keep this window open or press any key to close."
Read-Host "Press Enter to exit..."
