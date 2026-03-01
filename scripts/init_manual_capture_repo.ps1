param(
    [Parameter(Mandatory = $true)]
    [string]$RepoRoot,
    [string]$EvidenceRelativePath = "docs/context/e2e_evidence",
    [string]$TaskId = "T12",
    [string]$DateCompact = "",
    [switch]$Force,
    [switch]$DryRun
)

$ErrorActionPreference = "Stop"

function Resolve-AbsolutePath([string]$PathValue) {
    if ([System.IO.Path]::IsPathRooted($PathValue)) {
        return [System.IO.Path]::GetFullPath($PathValue)
    }
    return [System.IO.Path]::GetFullPath((Join-Path (Get-Location).Path $PathValue))
}

$resolvedRepoRoot = Resolve-AbsolutePath $RepoRoot
$evidenceDir = Join-Path $resolvedRepoRoot $EvidenceRelativePath
$indexPath = Join-Path $evidenceDir "index.md"
$queuePath = Join-Path $evidenceDir "manual_capture_queue.json"
$alertsPath = Join-Path $evidenceDir "manual_capture_alerts.json"

if (-not (Test-Path -LiteralPath $resolvedRepoRoot)) {
    throw "RepoRoot does not exist: $resolvedRepoRoot"
}

if ([string]::IsNullOrWhiteSpace($DateCompact)) {
    $DateCompact = (Get-Date).ToString("yyyyMMdd")
}
if ($DateCompact -notmatch '^\d{8}$') {
    throw "DateCompact must be YYYYMMDD. Got: $DateCompact"
}
$dateDash = "{0}-{1}-{2}" -f $DateCompact.Substring(0,4), $DateCompact.Substring(4,2), $DateCompact.Substring(6,2)

$templatePath = Join-Path $PSScriptRoot "..\docs\context\templates\e2e_evidence_index.md.template"
$templatePath = [System.IO.Path]::GetFullPath($templatePath)
if (-not (Test-Path -LiteralPath $templatePath)) {
    throw "Missing template file: $templatePath"
}

if ((Test-Path -LiteralPath $indexPath) -and (-not $Force)) {
    throw "index.md already exists at $indexPath. Use -Force to overwrite."
}

$templateText = Get-Content -LiteralPath $templatePath -Raw -Encoding UTF8
$outputText = $templateText.Replace("{{TASK_ID}}", $TaskId).Replace("{{DATE_COMPACT}}", $DateCompact).Replace("{{DATE_DASH}}", $dateDash)

$queueSeed = @{
    schema_version = "1.0.0"
    generated_at_utc = (Get-Date).ToUniversalTime().ToString("yyyy-MM-ddTHH:mm:ssZ")
    task_id = $TaskId
    drop_dir = ""
    evidence_dir = $evidenceDir
    items = @()
}

$alertsSeed = @{
    schema_version = "1.0.0"
    generated_at_utc = (Get-Date).ToUniversalTime().ToString("yyyy-MM-ddTHH:mm:ssZ")
    events = @()
}

if ($DryRun) {
    Write-Host "[DRY-RUN] RepoRoot: $resolvedRepoRoot"
    Write-Host "[DRY-RUN] EvidenceDir: $evidenceDir"
    Write-Host "[DRY-RUN] IndexPath: $indexPath"
    Write-Host "[DRY-RUN] QueuePath: $queuePath"
    Write-Host "[DRY-RUN] AlertsPath: $alertsPath"
    return
}

New-Item -ItemType Directory -Path $evidenceDir -Force | Out-Null
Set-Content -LiteralPath $indexPath -Value $outputText -Encoding UTF8

if (-not (Test-Path -LiteralPath $queuePath) -or $Force) {
    $queueSeed | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath $queuePath -Encoding UTF8
}
if (-not (Test-Path -LiteralPath $alertsPath) -or $Force) {
    $alertsSeed | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath $alertsPath -Encoding UTF8
}

Write-Host "Initialized manual capture evidence structure:"
Write-Host "  RepoRoot: $resolvedRepoRoot"
Write-Host "  EvidenceDir: $evidenceDir"
Write-Host "  Index: $indexPath"
Write-Host "  Queue: $queuePath"
Write-Host "  Alerts: $alertsPath"
