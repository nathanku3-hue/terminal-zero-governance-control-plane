param(
    [Parameter(Mandatory = $true)]
    [string]$DropDir,
    [string]$OwnerId = "",
    [switch]$Clear,
    [switch]$DryRun
)

$ErrorActionPreference = "Stop"

function Resolve-AbsolutePath([string]$PathValue) {
    if ([System.IO.Path]::IsPathRooted($PathValue)) {
        return [System.IO.Path]::GetFullPath($PathValue)
    }
    return [System.IO.Path]::GetFullPath((Join-Path (Get-Location).Path $PathValue))
}

$resolvedDropDir = Resolve-AbsolutePath $DropDir
$statePath = Join-Path $resolvedDropDir "repo_capture_state.json"

if (-not (Test-Path -LiteralPath $resolvedDropDir)) {
    New-Item -ItemType Directory -Path $resolvedDropDir -Force | Out-Null
}

$activeOwner = $OwnerId
if ($Clear) {
    $activeOwner = ""
}
if (-not $Clear -and [string]::IsNullOrWhiteSpace($activeOwner)) {
    throw "OwnerId is required unless -Clear is specified."
}

$payload = @{
    schema_version = "1.0.0"
    generated_at_utc = (Get-Date).ToUniversalTime().ToString("yyyy-MM-ddTHH:mm:ssZ")
    active_owner_id = $activeOwner
    updated_at_utc = (Get-Date).ToUniversalTime().ToString("yyyy-MM-ddTHH:mm:ssZ")
}

if ($DryRun) {
    Write-Host "[DRY-RUN] StatePath: $statePath"
    Write-Host "[DRY-RUN] active_owner_id: $activeOwner"
    return
}

$payload | ConvertTo-Json -Depth 4 | Set-Content -LiteralPath $statePath -Encoding UTF8
if ($Clear) {
    Write-Host "Cleared active owner in: $statePath"
} else {
    Write-Host "Set active owner to '$activeOwner' in: $statePath"
}
