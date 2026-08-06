$scriptPath = Join-Path $PSScriptRoot "frontend\scripts\build-static.ps1"
if (-not (Test-Path -LiteralPath $scriptPath)) {
    throw "Frontend static build script not found at $scriptPath"
}

& $scriptPath
