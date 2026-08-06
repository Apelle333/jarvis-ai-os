$ErrorActionPreference = "Stop"

$frontendRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
$nextBin = Join-Path $frontendRoot "node_modules\next\dist\bin\next"

function Resolve-Node {
  $node = Get-Command node -ErrorAction SilentlyContinue
  if ($node) {
    return $node.Source
  }

  $bundledNode = Join-Path $env:USERPROFILE ".cache\codex-runtimes\codex-primary-runtime\dependencies\node\bin\node.exe"
  if (Test-Path $bundledNode) {
    return $bundledNode
  }

  throw "Node.js was not found. Install Node.js or run this from the Codex desktop environment with bundled Node available."
}

if (-not (Test-Path $nextBin)) {
  throw "Next.js is not installed. Run dependency installation for the frontend before starting dev mode."
}

$nodeExe = Resolve-Node
Push-Location $frontendRoot
try {
  & $nodeExe $nextBin dev
  if ($LASTEXITCODE -ne 0) {
    exit $LASTEXITCODE
  }
}
finally {
  Pop-Location
}

