param(
    [Parameter(Mandatory = $true)]
    [string]$RepoARoot,
    [Parameter(Mandatory = $true)]
    [string]$RepoADropDir,
    [Parameter(Mandatory = $true)]
    [string]$RepoBRoot,
    [Parameter(Mandatory = $true)]
    [string]$RepoBDropDir,
    [string]$RepoAName = "RepoA",
    [string]$RepoBName = "RepoB",
    [string]$TaskPrefix = "ManualCapture",
    [string]$RepoAEvidenceRelativePath = "docs/context/e2e_evidence",
    [string]$RepoBEvidenceRelativePath = "docs/context/e2e_evidence",
    [string]$WatcherScriptPath = "",
    [string]$PythonExeA = "",
    [string]$PythonExeB = "",
    [int]$IntervalSeconds = 10,
    [int]$WarnMinutes = 15,
    [int]$BlockMinutes = 30,
    [int]$MinImageBytes = 1024,
    [switch]$AcceptAnyFilename,
    [switch]$SingleOccupancy,
    [string]$StateFile = "",
    [string]$RegistryFile = "",
    [switch]$MoveFromDrop,
    [switch]$FailOnBlock,
    [switch]$DryRun
)

$ErrorActionPreference = "Stop"

$registerScript = Join-Path $PSScriptRoot "register_manual_capture_watcher_task.ps1"
if (-not (Test-Path -LiteralPath $registerScript)) {
    throw "Missing register script: $registerScript"
}

$common = @{
    IntervalSeconds = $IntervalSeconds
    WarnMinutes = $WarnMinutes
    BlockMinutes = $BlockMinutes
    MinImageBytes = $MinImageBytes
    AcceptAnyFilename = $AcceptAnyFilename
    SingleOccupancy = $SingleOccupancy
    MoveFromDrop = $MoveFromDrop
    FailOnBlock = $FailOnBlock
    DryRun = $DryRun
}
if (-not [string]::IsNullOrWhiteSpace($WatcherScriptPath)) {
    $common["WatcherScriptPath"] = $WatcherScriptPath
}
if (-not [string]::IsNullOrWhiteSpace($StateFile)) {
    $common["StateFile"] = $StateFile
}
if (-not [string]::IsNullOrWhiteSpace($RegistryFile)) {
    $common["RegistryFile"] = $RegistryFile
}

$taskA = "$TaskPrefix-$RepoAName"
$paramsA = @{
    TaskName = $taskA
    RepoRoot = $RepoARoot
    DropDir = $RepoADropDir
    OwnerId = $taskA
    RepoKey = $RepoAName
    EvidenceRelativePath = $RepoAEvidenceRelativePath
}
if (-not [string]::IsNullOrWhiteSpace($PythonExeA)) {
    $paramsA["PythonExe"] = $PythonExeA
}
$paramsA += $common
& $registerScript @paramsA

$taskB = "$TaskPrefix-$RepoBName"
$paramsB = @{
    TaskName = $taskB
    RepoRoot = $RepoBRoot
    DropDir = $RepoBDropDir
    OwnerId = $taskB
    RepoKey = $RepoBName
    EvidenceRelativePath = $RepoBEvidenceRelativePath
}
if (-not [string]::IsNullOrWhiteSpace($PythonExeB)) {
    $paramsB["PythonExe"] = $PythonExeB
}
$paramsB += $common
& $registerScript @paramsB

Write-Host "Dual repo watcher tasks processed:"
Write-Host "  $taskA"
Write-Host "  $taskB"
