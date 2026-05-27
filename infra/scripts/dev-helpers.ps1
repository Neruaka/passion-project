# PASSION dev helpers (Windows PowerShell).
#
# Why: PowerShell on Windows still uses Windows-1252 for console I/O by default,
# which mojibakes any UTF-8 JSON the FastAPI returns (e.g. "Entraînement" →
# "EntraÃ®nement"). Dot-source this file in your profile to get correct UTF-8:
#
#     . C:\path\to\passion-project\infra\scripts\dev-helpers.ps1
#
# Or run it ad-hoc in the session before hitting the API:
#
#     . .\infra\scripts\dev-helpers.ps1
#
# Then use the helpers below: `passion-login`, `passion-workouts`, `passion-prs`,
# `passion-sync`, etc. — they all set the right encoding and pretty-print JSON.

# --- UTF-8 everywhere -----------------------------------------------------------

[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
[Console]::InputEncoding = [System.Text.Encoding]::UTF8
$OutputEncoding = [System.Text.Encoding]::UTF8
$env:PYTHONIOENCODING = "utf-8"

# --- Config ---------------------------------------------------------------------

$Global:PASSION_BASE = "http://localhost:8000"
$Global:PASSION_PWD  = "changeme"   # rotate via `docker compose exec backend python -m src.scripts.hash_password`

# --- Helpers --------------------------------------------------------------------

function passion-login {
    $body = @{ password = $Global:PASSION_PWD } | ConvertTo-Json -Compress
    $resp = Invoke-RestMethod -Uri "$Global:PASSION_BASE/api/v1/auth/login" `
        -Method POST -ContentType 'application/json; charset=utf-8' -Body $body
    $Global:PASSION_TOKEN = $resp.access_token
    Write-Host "✓ Logged in. Token cached in `$Global:PASSION_TOKEN ($($resp.expires_at))" -ForegroundColor Green
}

function _passion-headers {
    if (-not $Global:PASSION_TOKEN) { passion-login | Out-Null }
    return @{ Authorization = "Bearer $($Global:PASSION_TOKEN)" }
}

function passion-get {
    param([Parameter(Mandatory = $true)] [string] $Path, [int] $Depth = 6)
    $resp = Invoke-RestMethod -Uri "$Global:PASSION_BASE$Path" -Headers (_passion-headers)
    $resp | ConvertTo-Json -Depth $Depth
}

function passion-sync {
    Invoke-RestMethod -Uri "$Global:PASSION_BASE/api/v1/workouts/sync" `
        -Method POST -Headers (_passion-headers)
}

function passion-workouts { passion-get "/api/v1/workouts?page_size=5" }
function passion-workout  { param([Parameter(Mandatory)] [string] $Id) passion-get "/api/v1/workouts/$Id" }
function passion-prs      { passion-get "/api/v1/analysis/prs?page_size=10" }
function passion-plateaus { passion-get "/api/v1/analysis/plateaus" }
function passion-targets  { passion-get "/api/v1/analysis/targets" }
function passion-muscles  { passion-get "/api/v1/analysis/muscle-status" }
function passion-stats    { param([string] $Period = "week") passion-get "/api/v1/analysis/stats?period=$Period" }

Write-Host "PASSION helpers loaded. UTF-8 active. Try: passion-login; passion-workouts" -ForegroundColor Cyan
