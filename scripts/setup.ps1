# Installation Windows — dev local Cursor uniquement.
$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root

Write-Host "==> Creation du venv avec uv..." -ForegroundColor Cyan
uv venv .venv

$Py = ".\.venv\Scripts\python.exe"

Write-Host "==> Installation des dependances avec uv..." -ForegroundColor Cyan
uv pip sync . --python $Py

if (-not (Test-Path ".env")) {
    Copy-Item ".env.example" ".env"
    Write-Host "==> .env cree — adapter VLLM_BASE_URL et modeles." -ForegroundColor Yellow
}

Write-Host "==> Verification..." -ForegroundColor Cyan
& $Py scripts/verify_install.py

Write-Host ""
Write-Host "Pret pour Cursor." -ForegroundColor Green
Write-Host "1. Ouvrir rag-project-template.code-workspace"
Write-Host "2. Redemarrer Cursor (MCP rag-reference)"
Write-Host "3. Configurer .env puis deposer des PDF dans reference/"
Write-Host "4. $Py scripts/index.py"
