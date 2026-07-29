#Requires -Version 5.1
<#
.SYNOPSIS
    Create a verified SQLite backup of the Planforge database.

.DESCRIPTION
    Safe manual backup workflow:
    1. Prompt to stop application writes (backend must not be running).
    2. Create a consistent backup using SQLite's online backup API.
    3. Run PRAGMA integrity_check on the copy.
    4. Open the copy in an isolated temporary verification database.
    5. Never overwrite the live database during verification.

    This script does not import arbitrary files. It only copies the configured
    Planforge SQLite database to a timestamped backup file.

.NOTES
    Phone access and external networking are out of scope. Run locally only.
#>
[CmdletBinding()]
param(
    [string]$DatabasePath = "",
    [string]$BackupDirectory = "",
    [switch]$SkipStopPrompt
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Resolve-PlanforgeDatabasePath {
    param([string]$OverridePath)

    if ($OverridePath) {
        return (Resolve-Path -LiteralPath $OverridePath).Path
    }

    $envPath = $env:PLANFORGE_DATABASE_URL
    if ($envPath -and $envPath -like "sqlite:///*") {
        $relative = $envPath.Substring("sqlite:///".Length) -replace "/", "\"
        return (Resolve-Path -LiteralPath (Join-Path (Get-Location) $relative)).Path
    }

    $defaultPath = Join-Path (Split-Path $PSScriptRoot -Parent) "data\planforge.db"
    if (-not (Test-Path -LiteralPath $defaultPath)) {
        throw "Database not found at $defaultPath. Pass -DatabasePath or set PLANFORGE_DATABASE_URL."
    }
    return (Resolve-Path -LiteralPath $defaultPath).Path
}

function Confirm-ApplicationStopped {
    if ($SkipStopPrompt) {
        Write-Warning "Skipping stop prompt because -SkipStopPrompt was supplied."
        return
    }

    Write-Host ""
    Write-Host "Before backing up, stop all Planforge writers:" -ForegroundColor Yellow
    Write-Host "  - Stop uvicorn / the backend API"
    Write-Host "  - Close any SQLite browser connected to the live database"
    Write-Host ""
    $answer = Read-Host "Have you stopped application writes? [y/N]"
    if ($answer -notin @("y", "Y", "yes", "Yes")) {
        throw "Backup cancelled. Stop the backend and run this script again."
    }
}

$liveDatabasePath = Resolve-PlanforgeDatabasePath -OverridePath $DatabasePath
$backupRoot = if ($BackupDirectory) {
    $BackupDirectory
} else {
    Join-Path (Split-Path $liveDatabasePath -Parent) "backups"
}

if (-not (Test-Path -LiteralPath $backupRoot)) {
    New-Item -ItemType Directory -Path $backupRoot | Out-Null
}

Confirm-ApplicationStopped

$timestamp = Get-Date -Format "yyyyMMdd-HHmmss"
$backupPath = Join-Path $backupRoot "planforge-$timestamp.db"

Write-Host "Live database : $liveDatabasePath"
Write-Host "Backup target : $backupPath"
Write-Host ""

$backendRoot = Join-Path (Split-Path $PSScriptRoot -Parent) "backend"
$python = Join-Path $backendRoot ".venv\Scripts\python.exe"
if (-not (Test-Path -LiteralPath $python)) {
    $python = "py"
}

$verifyScript = Join-Path $backendRoot "scripts\verify_sqlite_backup.py"
if (-not (Test-Path -LiteralPath $verifyScript)) {
    throw "Verification script not found: $verifyScript"
}

& $python $verifyScript --source $liveDatabasePath --backup $backupPath
if ($LASTEXITCODE -ne 0) {
    throw "Backup verification failed. The live database was not modified."
}

Write-Host ""
Write-Host "Backup completed successfully." -ForegroundColor Green
Write-Host "Verified copy: $backupPath"
Write-Host "Restore only by copying this file to a new path and pointing PLANFORGE_DATABASE_URL at it."
Write-Host "Never overwrite the live database while verifying a backup."
