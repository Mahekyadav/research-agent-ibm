# ── Full-Stack Build Script ───────────────────────────────────────────────────
# build.ps1 — Build frontend & run full-stack on Windows (PowerShell)
Write-Host ""
Write-Host "╔══════════════════════════════════════════════════════════════╗"
Write-Host "║       ResearchMind — Full-Stack Build                        ║"
Write-Host "╚══════════════════════════════════════════════════════════════╝"
Write-Host ""

# 1. Frontend build
Write-Host "→ Installing frontend dependencies..."
Set-Location frontend
npm install
Write-Host "→ Building React frontend..."
npm run build
Set-Location ..

Write-Host ""
Write-Host "✓ Frontend built to /static"
Write-Host ""
Write-Host "→ Starting FastAPI (serves frontend + API)..."
Write-Host "  App:      http://localhost:8000"
Write-Host "  API Docs: http://localhost:8000/docs"
Write-Host ""
python main.py
