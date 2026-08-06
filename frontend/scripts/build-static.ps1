$ErrorActionPreference = "Stop"

$frontendRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
$outDir = Join-Path $frontendRoot "out"
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
  throw "Next.js is not installed. Run dependency installation for the frontend before building."
}

if (Test-Path $outDir) {
  $resolvedOut = Resolve-Path $outDir
  if (-not $resolvedOut.Path.StartsWith($frontendRoot.Path, [System.StringComparison]::OrdinalIgnoreCase)) {
    throw "Refusing to remove output directory outside the frontend workspace: $resolvedOut"
  }
  Remove-Item -LiteralPath $resolvedOut.Path -Recurse -Force
}

$nodeExe = Resolve-Node
Push-Location $frontendRoot
try {
  & $nodeExe $nextBin build
  if ($LASTEXITCODE -ne 0) {
    exit $LASTEXITCODE
  }
}
finally {
  Pop-Location
}

