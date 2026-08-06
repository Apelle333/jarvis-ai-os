$scriptPath = Join-Path $PSScriptRoot "frontend\scripts\dev-next.ps1"
if (-not (Test-Path -LiteralPath $scriptPath)) {
    throw "Frontend dev script not found at $scriptPath"
}

& $scriptPath
