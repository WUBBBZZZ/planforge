#Requires -Version 5.1
<#
.SYNOPSIS
    Regenerate the pinned Python dependency lock file from pyproject.toml.
#>
Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$backendRoot = Join-Path (Split-Path $PSScriptRoot -Parent) "backend"
$python = Join-Path $backendRoot ".venv\Scripts\python.exe"
if (-not (Test-Path -LiteralPath $python)) {
    $python = "py"
}

Push-Location $backendRoot
try {
    & $python -m pip install pip-tools
    & $python -m piptools compile pyproject.toml --extra dev -o requirements.lock --strip-extras
    Write-Host "Updated backend/requirements.lock"
} finally {
    Pop-Location
}
