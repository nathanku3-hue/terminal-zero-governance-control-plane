param(
    [Parameter(Mandatory = $true)]
    [string]$TaskName,
    [Parameter(Mandatory = $true)]
    [string]$RepoRoot,
    [Parameter(Mandatory = $true)]
    [string]$DropDir,
    [string]$EvidenceRelativePath = "docs/context/e2e_evidence",
    [string]$WatcherScriptPath = "",
    [string]$PythonExe = "",
    [int]$IntervalSeconds = 10,
    [int]$WarnMinutes = 15,
    [int]$BlockMinutes = 30,
    [int]$MinImageBytes = 1024,
    [switch]$AcceptAnyFilename,
    [switch]$SingleOccupancy,
    [string]$OwnerId = "",
    [string]$RepoKey = "",
    [string]$StateFile = "",
    [string]$RegistryFile = "",
    [switch]$MoveFromDrop,
    [switch]$FailOnBlock,
    [switch]$DryRun
)

$ErrorActionPreference = "Stop"

function Resolve-AbsolutePath([string]$PathValue) {
    if ([System.IO.Path]::IsPathRooted($PathValue)) {
        return [System.IO.Path]::GetFullPath($PathValue)
    }
    return [System.IO.Path]::GetFullPath((Join-Path (Get-Location).Path $PathValue))
}

function Quote-Arg([string]$Value) {
    return '"' + $Value.Replace('"', '\"') + '"'
}

$resolvedRepoRoot = Resolve-AbsolutePath $RepoRoot
if (-not (Test-Path -LiteralPath $resolvedRepoRoot)) {
    throw "RepoRoot does not exist: $resolvedRepoRoot"
}

if ([string]::IsNullOrWhiteSpace($WatcherScriptPath)) {
    $WatcherScriptPath = Join-Path $PSScriptRoot "manual_capture_watcher.py"
}
$resolvedWatcherScript = Resolve-AbsolutePath $WatcherScriptPath
if (-not (Test-Path -LiteralPath $resolvedWatcherScript)) {
    throw "Watcher script not found: $resolvedWatcherScript"
}

if ([string]::IsNullOrWhiteSpace($PythonExe)) {
    $candidatePython = Join-Path $resolvedRepoRoot ".venv\Scripts\python.exe"
    if (Test-Path -LiteralPath $candidatePython) {
        $PythonExe = $candidatePython
    } else {
        $pythonCommand = Get-Command python -ErrorAction SilentlyContinue
        if ($null -eq $pythonCommand) {
            throw "Python executable not found. Provide -PythonExe."
        }
        $PythonExe = $pythonCommand.Source
    }
}
$resolvedPython = Resolve-AbsolutePath $PythonExe

$resolvedDropDir = Resolve-AbsolutePath $DropDir
$evidenceDir = Join-Path $resolvedRepoRoot $EvidenceRelativePath
$indexPath = Join-Path $evidenceDir "index.md"
$queuePath = Join-Path $evidenceDir "manual_capture_queue.json"
$alertsPath = Join-Path $evidenceDir "manual_capture_alerts.json"

if (-not (Test-Path -LiteralPath $indexPath)) {
    throw "Missing index.md at $indexPath. Run init_manual_capture_repo.ps1 first."
}

New-Item -ItemType Directory -Path $resolvedDropDir -Force | Out-Null
New-Item -ItemType Directory -Path $evidenceDir -Force | Out-Null

if ([string]::IsNullOrWhiteSpace($OwnerId)) {
    $OwnerId = $TaskName
}
if ([string]::IsNullOrWhiteSpace($RepoKey)) {
    $RepoKey = Split-Path -Path $resolvedRepoRoot -Leaf
}

$argList = @(
    (Quote-Arg $resolvedWatcherScript),
    "--watch",
    "--index", (Quote-Arg $indexPath),
    "--queue", (Quote-Arg $queuePath),
    "--alerts", (Quote-Arg $alertsPath),
    "--drop-dir", (Quote-Arg $resolvedDropDir),
    "--evidence-dir", (Quote-Arg $evidenceDir),
    "--interval-seconds", $IntervalSeconds,
    "--warn-minutes", $WarnMinutes,
    "--block-minutes", $BlockMinutes,
    "--min-image-bytes", $MinImageBytes,
    "--repo-root", (Quote-Arg $resolvedRepoRoot),
    "--owner-id", (Quote-Arg $OwnerId),
    "--repo-key", (Quote-Arg $RepoKey)
)
if ($MoveFromDrop) { $argList += "--move-from-drop" }
if ($FailOnBlock) { $argList += "--fail-on-block" }
if ($AcceptAnyFilename) { $argList += "--accept-any-filename" }
if ($SingleOccupancy) { $argList += "--single-occupancy" }
if (-not [string]::IsNullOrWhiteSpace($StateFile)) {
    $argList += "--state-file"
    $argList += (Quote-Arg (Resolve-AbsolutePath $StateFile))
}
if (-not [string]::IsNullOrWhiteSpace($RegistryFile)) {
    $argList += "--registry-file"
    $argList += (Quote-Arg (Resolve-AbsolutePath $RegistryFile))
}
$arguments = $argList -join " "

$action = New-ScheduledTaskAction -Execute $resolvedPython -Argument $arguments -WorkingDirectory $resolvedRepoRoot
$trigger = New-ScheduledTaskTrigger -AtLogOn -User $env:USERNAME
$settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable -MultipleInstances IgnoreNew
$principal = New-ScheduledTaskPrincipal -UserId "$env:USERDOMAIN\$env:USERNAME" -LogonType Interactive -RunLevel Limited

if ($DryRun) {
    Write-Host "[DRY-RUN] TaskName: $TaskName"
    Write-Host "[DRY-RUN] RepoRoot: $resolvedRepoRoot"
    Write-Host "[DRY-RUN] DropDir: $resolvedDropDir"
    Write-Host "[DRY-RUN] EvidenceDir: $evidenceDir"
    Write-Host "[DRY-RUN] Execute: $resolvedPython"
    Write-Host "[DRY-RUN] Arguments: $arguments"
    return
}

Register-ScheduledTask -TaskName $TaskName -Action $action -Trigger $trigger -Settings $settings -Principal $principal -Force | Out-Null

Write-Host "Registered scheduled task: $TaskName"
Write-Host "  RepoRoot: $resolvedRepoRoot"
Write-Host "  DropDir: $resolvedDropDir"
Write-Host "  EvidenceDir: $evidenceDir"
Write-Host "  Python: $resolvedPython"
