param(
    [string]$RepoRoot = ".",
    [ValidateSet("", "Quant", "Film")]
    [string]$RepoProfile = "",
    [string]$TraceabilityPath = "",
    [string]$DispatchManifestPath = "",
    [string]$WorkerReplyPath = "",
    [string[]]$OrphanInclude = @(),
    [string]$PythonExe = "",
    [string]$LogsRelativeDir = "docs/context/phase_end_logs",
    [string]$ScanRoot = "",
    [string]$SinceCommit = "",
    [int]$DigestTtlMinutes = 60,
    [int]$DispatchTimeoutMinutes = 10,
    [switch]$SkipOrphanGate,
    [switch]$SkipDispatchGate,
    [switch]$DryRun
)

$ErrorActionPreference = "Stop"

function Resolve-AbsolutePath {
    param(
        [Parameter(Mandatory = $true)]
        [string]$BasePath,
        [Parameter(Mandatory = $true)]
        [string]$PathValue
    )
    if ([System.IO.Path]::IsPathRooted($PathValue)) {
        return [System.IO.Path]::GetFullPath($PathValue)
    }
    return [System.IO.Path]::GetFullPath((Join-Path $BasePath $PathValue))
}

function Get-RepoProfileDefaults {
    param([string]$ProfileName)

    switch ($ProfileName) {
        "Quant" {
            return [ordered]@{
                repo_root               = "E:/Code/Quant"
                scan_root               = "E:/Code/Quant"
                traceability_candidates = @(
                    "docs/pm_to_code_traceability.yaml",
                    "docs/context/pm_to_code_traceability.yaml"
                )
                dispatch_manifest       = "docs/context/dispatch_manifest.json"
                worker_reply_packet     = "docs/context/worker_reply_packet.json"
                orphan_include          = @("*.py", "*.ps1", "*.ts", "*.tsx", "*.js", "*.jsx", "*.yaml", "*.yml")
            }
        }
        "Film" {
            return [ordered]@{
                repo_root               = "E:/Code/Film"
                scan_root               = "E:/Code/Film"
                traceability_candidates = @(
                    "docs/pm_to_code_traceability.yaml",
                    "docs/context/pm_to_code_traceability.yaml"
                )
                dispatch_manifest       = "docs/context/dispatch_manifest.json"
                worker_reply_packet     = "docs/context/worker_reply_packet.json"
                orphan_include          = @("*.py", "*.ps1", "*.ts", "*.tsx", "*.js", "*.jsx", "*.yaml", "*.yml")
            }
        }
        default {
            return [ordered]@{
                repo_root               = "."
                scan_root               = ""
                traceability_candidates = @(
                    "docs/pm_to_code_traceability.yaml",
                    "docs/context/pm_to_code_traceability.yaml"
                )
                dispatch_manifest       = "docs/context/dispatch_manifest.json"
                worker_reply_packet     = "docs/context/worker_reply_packet.json"
                orphan_include          = @("*.py", "*.ps1", "*.ts", "*.tsx", "*.js", "*.jsx", "*.yaml", "*.yml")
            }
        }
    }
}

function Resolve-ConfiguredPath {
    param(
        [string]$RepoRootAbs,
        [string]$ExplicitValue,
        [string]$DefaultValue
    )
    if (-not [string]::IsNullOrWhiteSpace($ExplicitValue)) {
        return Resolve-AbsolutePath -BasePath $RepoRootAbs -PathValue $ExplicitValue
    }
    return Resolve-AbsolutePath -BasePath $RepoRootAbs -PathValue $DefaultValue
}

function Get-UtcIso {
    return [DateTime]::UtcNow.ToString("yyyy-MM-ddTHH:mm:ssZ")
}

function Resolve-PythonExecutable {
    param([string]$Requested)
    if (-not [string]::IsNullOrWhiteSpace($Requested)) {
        if (Test-Path -LiteralPath $Requested) {
            return [System.IO.Path]::GetFullPath($Requested)
        }
        $cmd = Get-Command $Requested -ErrorAction SilentlyContinue
        if ($null -ne $cmd) {
            return $cmd.Source
        }
        throw "Python executable not found: $Requested"
    }

    $globalPython = Get-Command python -ErrorAction SilentlyContinue
    if ($null -eq $globalPython) {
        throw "Python executable not found. Provide -PythonExe."
    }
    return $globalPython.Source
}

function Resolve-FirstExistingPath {
    param(
        [Parameter(Mandatory = $true)]
        [string]$RepoRootAbs,
        [Parameter(Mandatory = $true)]
        [string[]]$Candidates
    )
    foreach ($candidate in $Candidates) {
        $abs = Resolve-AbsolutePath -BasePath $RepoRootAbs -PathValue $candidate
        if (Test-Path -LiteralPath $abs) {
            return $abs
        }
    }
    return (Resolve-AbsolutePath -BasePath $RepoRootAbs -PathValue $Candidates[0])
}

function New-GateResult {
    param(
        [string]$Gate,
        [string]$Status,
        [int]$ExitCode,
        [string]$Command,
        [string]$LogPath,
        [string]$StartedUtc,
        [string]$EndedUtc,
        [string]$Message = ""
    )
    return [ordered]@{
        gate        = $Gate
        status      = $Status
        exit_code   = $ExitCode
        command     = $Command
        log_path    = $LogPath
        started_utc = $StartedUtc
        ended_utc   = $EndedUtc
        message     = $Message
    }
}

function Invoke-PythonGate {
    param(
        [Parameter(Mandatory = $true)]
        [string]$GateName,
        [Parameter(Mandatory = $true)]
        [string]$ScriptPath,
        [Parameter(Mandatory = $true)]
        [string]$PythonPath,
        [Parameter(Mandatory = $true)]
        [string]$RepoRootAbs,
        [Parameter(Mandatory = $true)]
        [string]$LogPath,
        [string[]]$Arguments = @(),
        [switch]$PreviewOnly
    )

    $started = Get-UtcIso
    $commandDisplay = @($PythonPath, $ScriptPath) + $Arguments
    $commandText = ($commandDisplay | ForEach-Object {
        if ($_ -match "\s") { '"' + $_ + '"' } else { $_ }
    }) -join " "

    if ($PreviewOnly) {
        Write-Host "[DRY-RUN] $GateName"
        Write-Host "  $commandText"
        return (New-GateResult -Gate $GateName -Status "PREVIEW" -ExitCode 0 -Command $commandText -LogPath "-" -StartedUtc $started -EndedUtc (Get-UtcIso))
    }

    $safeName = ($GateName -replace "[^A-Za-z0-9_-]", "_")
    $logFile = Join-Path $LogPath ("{0}_{1}.log" -f $script:RunId, $safeName)
    $header = @(
        "timestamp_utc=$started",
        "gate=$GateName",
        "command=$commandText",
        "----- stdout_stderr -----"
    ) -join [Environment]::NewLine
    Set-Content -Path $logFile -Value $header -Encoding UTF8

    Push-Location $RepoRootAbs
    $previousNativePref = $null
    if (Get-Variable -Name PSNativeCommandUseErrorActionPreference -ErrorAction SilentlyContinue) {
        $previousNativePref = $PSNativeCommandUseErrorActionPreference
        $PSNativeCommandUseErrorActionPreference = $false
    }
    $previousErrorAction = $ErrorActionPreference
    $ErrorActionPreference = "Continue"
    try {
        & $PythonPath $ScriptPath @Arguments *>> $logFile
        $exitCode = $LASTEXITCODE
    }
    finally {
        $ErrorActionPreference = $previousErrorAction
        if ($null -ne $previousNativePref) {
            $PSNativeCommandUseErrorActionPreference = $previousNativePref
        }
        Pop-Location
    }

    $ended = Get-UtcIso
    Add-Content -Path $logFile -Value ("----- exit -----{0}exit_code={1}{0}ended_utc={2}" -f [Environment]::NewLine, $exitCode, $ended) -Encoding UTF8
    $status = if ($exitCode -eq 0) { "PASS" } else { "BLOCK" }
    Write-Host ("[{0}] {1} (exit={2})" -f $status, $GateName, $exitCode)
    if ($exitCode -ne 0) {
        Write-Host ("  log: {0}" -f $logFile)
    }

    return (New-GateResult -Gate $GateName -Status $status -ExitCode $exitCode -Command $commandText -LogPath $logFile -StartedUtc $started -EndedUtc $ended)
}

function Resolve-SinceCommitValue {
    param(
        [string]$RepoRootAbs,
        [string]$ExplicitSinceCommit
    )
    if (-not [string]::IsNullOrWhiteSpace($ExplicitSinceCommit)) {
        return $ExplicitSinceCommit.Trim()
    }

    $candidates = @(
        @("merge-base", "HEAD", "origin/main"),
        @("merge-base", "HEAD", "origin/master"),
        @("rev-parse", "HEAD~1")
    )

    $previousNativePref = $null
    $resolved = ""
    if (Get-Variable -Name PSNativeCommandUseErrorActionPreference -ErrorAction SilentlyContinue) {
        $previousNativePref = $PSNativeCommandUseErrorActionPreference
        $PSNativeCommandUseErrorActionPreference = $false
    }
    $previousErrorAction = $ErrorActionPreference
    $ErrorActionPreference = "Continue"
    try {
        foreach ($candidate in $candidates) {
            try {
                $out = & git -C $RepoRootAbs @candidate 2>$null
                if ($LASTEXITCODE -eq 0 -and $out) {
                    $first = ($out | Select-Object -First 1).ToString().Trim()
                    if (-not [string]::IsNullOrWhiteSpace($first)) {
                        $resolved = $first
                        break
                    }
                }
            }
            catch {
                continue
            }
        }
    }
    finally {
        $ErrorActionPreference = $previousErrorAction
        if ($null -ne $previousNativePref) {
            $PSNativeCommandUseErrorActionPreference = $previousNativePref
        }
    }
    return $resolved
}

function Write-RunArtifacts {
    param(
        [string]$StatusPath,
        [string]$SummaryPath,
        [hashtable]$RunState
    )

    $json = $RunState | ConvertTo-Json -Depth 12
    Set-Content -Path $StatusPath -Value $json -Encoding UTF8

    $lines = @()
    $lines += "# Phase-End Handover Gate Summary"
    $lines += ""
    $lines += ("- RunID: {0}" -f $RunState.run_id)
    $lines += ("- Result: {0}" -f $RunState.result)
    $lines += ("- FailedGate: {0}" -f $RunState.failed_gate)
    $lines += ("- RepoRoot: {0}" -f $RunState.repo_root)
    $lines += ("- RepoProfile: {0}" -f $RunState.repo_profile)
    $lines += ("- StartedUTC: {0}" -f $RunState.started_utc)
    $lines += ("- EndedUTC: {0}" -f $RunState.ended_utc)
    $lines += ""
    $lines += "## Resolved Config"
    $lines += ""
    foreach ($key in $RunState.resolved_config.Keys) {
        $value = $RunState.resolved_config[$key]
        if ($value -is [System.Array]) {
            $rendered = ($value -join ", ")
        }
        else {
            $rendered = [string]$value
        }
        $lines += ("- {0}: {1}" -f $key, $rendered)
    }
    $lines += ""
    $lines += "| Gate | Status | Exit | Log |"
    $lines += "|------|--------|------|-----|"
    foreach ($gate in $RunState.gates) {
        $lines += ("| {0} | {1} | {2} | {3} |" -f $gate.gate, $gate.status, $gate.exit_code, $gate.log_path)
    }
    $lines += ""
    Set-Content -Path $SummaryPath -Value ($lines -join [Environment]::NewLine) -Encoding UTF8
}

$profileDefaults = Get-RepoProfileDefaults -ProfileName $RepoProfile
$hasExplicitRepoRoot = $PSBoundParameters.ContainsKey("RepoRoot")
$effectiveRepoRoot = if ($hasExplicitRepoRoot) { $RepoRoot } else { [string]$profileDefaults.repo_root }
$repoRootAbs = Resolve-AbsolutePath -BasePath (Get-Location).Path -PathValue $effectiveRepoRoot
if (-not (Test-Path -LiteralPath $repoRootAbs)) {
    throw "RepoRoot does not exist: $repoRootAbs"
}

$effectiveScanRoot = if (-not [string]::IsNullOrWhiteSpace($ScanRoot)) {
    $ScanRoot
}
elseif (-not [string]::IsNullOrWhiteSpace([string]$profileDefaults.scan_root)) {
    [string]$profileDefaults.scan_root
}
else {
    $repoRootAbs
}
$scanRootAbs = Resolve-AbsolutePath -BasePath $repoRootAbs -PathValue $effectiveScanRoot

$pythonPath = Resolve-PythonExecutable -Requested $PythonExe
$scriptRoot = [System.IO.Path]::GetFullPath($PSScriptRoot)
$logsDirAbs = Resolve-AbsolutePath -BasePath $repoRootAbs -PathValue $LogsRelativeDir

$script:RunId = Get-Date -Format "yyyyMMdd_HHmmss"
$startedUtc = Get-UtcIso

if (-not $DryRun) {
    New-Item -ItemType Directory -Path $logsDirAbs -Force | Out-Null
}

$traceabilityCandidates = if (-not [string]::IsNullOrWhiteSpace($TraceabilityPath)) {
    @($TraceabilityPath)
}
else {
    @($profileDefaults.traceability_candidates)
}
$traceabilityPath = Resolve-FirstExistingPath -RepoRootAbs $repoRootAbs -Candidates $traceabilityCandidates
$workerAggregatePath = Resolve-AbsolutePath -BasePath $repoRootAbs -PathValue "docs/context/worker_status_aggregate.json"
$escalationPath = Resolve-AbsolutePath -BasePath $repoRootAbs -PathValue "docs/context/escalation_events.json"
$evidenceHashesDir = Resolve-AbsolutePath -BasePath $repoRootAbs -PathValue "docs/context/evidence_hashes"
$workerReplyPath = Resolve-ConfiguredPath -RepoRootAbs $repoRootAbs -ExplicitValue $WorkerReplyPath -DefaultValue ([string]$profileDefaults.worker_reply_packet)
$dispatchManifestPath = Resolve-ConfiguredPath -RepoRootAbs $repoRootAbs -ExplicitValue $DispatchManifestPath -DefaultValue ([string]$profileDefaults.dispatch_manifest)
$digestPath = Resolve-AbsolutePath -BasePath $repoRootAbs -PathValue "docs/context/ceo_bridge_digest.md"
$orphanIncludePatterns = if ($OrphanInclude -and $OrphanInclude.Count -gt 0) {
    $OrphanInclude
}
else {
    @($profileDefaults.orphan_include)
}

$gateResults = @()
$overall = "PASS"
$failedGate = ""
$failedExit = 0
$stopExecution = $false
$resolvedConfig = [ordered]@{
    repo_profile           = $(if ([string]::IsNullOrWhiteSpace($RepoProfile)) { "default" } else { $RepoProfile })
    repo_root              = $repoRootAbs
    scan_root              = $scanRootAbs
    traceability_path      = $traceabilityPath
    dispatch_manifest_path = $dispatchManifestPath
    worker_reply_path      = $workerReplyPath
    worker_aggregate_path  = $workerAggregatePath
    escalation_path        = $escalationPath
    digest_path            = $digestPath
    orphan_include         = $orphanIncludePatterns
    skip_orphan_gate       = [bool]$SkipOrphanGate
    skip_dispatch_gate     = [bool]$SkipDispatchGate
}

Write-Host "Resolved Config:"
foreach ($item in $resolvedConfig.GetEnumerator()) {
    if ($item.Value -is [System.Array]) {
        Write-Host ("  {0}: {1}" -f $item.Key, ($item.Value -join ", "))
    }
    else {
        Write-Host ("  {0}: {1}" -f $item.Key, $item.Value)
    }
}

function Add-And-Check {
    param([hashtable]$GateResult)
    $script:gateResults += $GateResult
    if ($GateResult.status -eq "BLOCK") {
        $script:overall = "BLOCK"
        $script:failedGate = $GateResult.gate
        $script:failedExit = $GateResult.exit_code
        return $false
    }
    return $true
}

# G00) Preflight path checks
$missingPaths = @()
if (-not (Test-Path -LiteralPath $scanRootAbs)) {
    $missingPaths += "scan_root missing: $scanRootAbs"
}
if (-not (Test-Path -LiteralPath $traceabilityPath)) {
    $missingPaths += "traceability missing: $traceabilityPath"
}
if (-not (Test-Path -LiteralPath $evidenceHashesDir)) {
    $missingPaths += "evidence hash dir missing: $evidenceHashesDir"
}
if (-not (Test-Path -LiteralPath $workerReplyPath)) {
    $missingPaths += "worker reply packet missing: $workerReplyPath"
}
if (-not $SkipDispatchGate -and -not (Test-Path -LiteralPath $dispatchManifestPath)) {
    $missingPaths += "dispatch manifest missing: $dispatchManifestPath"
}

if ($missingPaths.Count -gt 0) {
    $stopExecution = $true
    $overall = "BLOCK"
    $failedGate = "G00_preflight"
    $failedExit = 1
    $gateResults += (New-GateResult -Gate "G00_preflight" -Status "BLOCK" -ExitCode 1 -Command "path preflight" -LogPath "-" -StartedUtc (Get-UtcIso) -EndedUtc (Get-UtcIso) -Message ($missingPaths -join "; "))
    Write-Host "[BLOCK] G00_preflight (exit=1)"
    foreach ($missing in $missingPaths) {
        Write-Host ("  - {0}" -f $missing)
    }
}

# 1) Context refresh
if (-not $stopExecution) {
    $ok = Add-And-Check (Invoke-PythonGate -GateName "G01_context_build" -ScriptPath (Join-Path $scriptRoot "build_context_packet.py") -PythonPath $pythonPath -RepoRootAbs $repoRootAbs -LogPath $logsDirAbs -Arguments @("--repo-root", $repoRootAbs) -PreviewOnly:$DryRun)
    if (-not $ok) { $stopExecution = $true }
}

# 2) Context validate
if (-not $stopExecution) {
    $ok = Add-And-Check (Invoke-PythonGate -GateName "G02_context_validate" -ScriptPath (Join-Path $scriptRoot "build_context_packet.py") -PythonPath $pythonPath -RepoRootAbs $repoRootAbs -LogPath $logsDirAbs -Arguments @("--repo-root", $repoRootAbs, "--validate") -PreviewOnly:$DryRun)
    if (-not $ok) { $stopExecution = $true }
}

# 3) Worker status aggregation
if (-not $stopExecution) {
    $ok = Add-And-Check (Invoke-PythonGate -GateName "G03_worker_status_aggregate" -ScriptPath (Join-Path $scriptRoot "aggregate_worker_status.py") -PythonPath $pythonPath -RepoRootAbs $repoRootAbs -LogPath $logsDirAbs -Arguments @("--scan-root", $scanRootAbs, "--output", $workerAggregatePath, "--escalation-output", $escalationPath) -PreviewOnly:$DryRun)
    if (-not $ok) { $stopExecution = $true }
}

# 4) Traceability gate
if (-not $stopExecution) {
    $ok = Add-And-Check (Invoke-PythonGate -GateName "G04_traceability_gate" -ScriptPath (Join-Path $scriptRoot "validate_traceability.py") -PythonPath $pythonPath -RepoRootAbs $repoRootAbs -LogPath $logsDirAbs -Arguments @("--input", $traceabilityPath, "--strict", "--require-test") -PreviewOnly:$DryRun)
    if (-not $ok) { $stopExecution = $true }
}

# 5) Evidence hash gate
if (-not $stopExecution) {
    $ok = Add-And-Check (Invoke-PythonGate -GateName "G05_evidence_hash_gate" -ScriptPath (Join-Path $scriptRoot "validate_evidence_hashes.py") -PythonPath $pythonPath -RepoRootAbs $repoRootAbs -LogPath $logsDirAbs -Arguments @("--input", $traceabilityPath, "--evidence-dir", $evidenceHashesDir) -PreviewOnly:$DryRun)
    if (-not $ok) { $stopExecution = $true }
}

# 6) Worker reply gate (confidence + citations)
if (-not $stopExecution) {
    $ok = Add-And-Check (Invoke-PythonGate -GateName "G06_worker_reply_gate" -ScriptPath (Join-Path $scriptRoot "validate_worker_reply_packet.py") -PythonPath $pythonPath -RepoRootAbs $repoRootAbs -LogPath $logsDirAbs -Arguments @("--input", $workerReplyPath, "--repo-root", $repoRootAbs, "--require-existing-paths") -PreviewOnly:$DryRun)
    if (-not $ok) { $stopExecution = $true }
}

# 7) Orphan change gate
if (-not $stopExecution) {
    if ($SkipOrphanGate) {
        $gateResults += (New-GateResult -Gate "G07_orphan_change_gate" -Status "SKIPPED" -ExitCode 0 -Command "-" -LogPath "-" -StartedUtc (Get-UtcIso) -EndedUtc (Get-UtcIso) -Message "Skipped by -SkipOrphanGate")
    }
    else {
        $resolvedSinceCommit = Resolve-SinceCommitValue -RepoRootAbs $repoRootAbs -ExplicitSinceCommit $SinceCommit
        if ([string]::IsNullOrWhiteSpace($resolvedSinceCommit)) {
            $gateResults += (New-GateResult -Gate "G07_orphan_change_gate" -Status "BLOCK" -ExitCode 1 -Command "git merge-base/rev-parse" -LogPath "-" -StartedUtc (Get-UtcIso) -EndedUtc (Get-UtcIso) -Message "Failed to resolve since-commit. Provide -SinceCommit explicitly.")
            $overall = "BLOCK"
            $failedGate = "G07_orphan_change_gate"
            $failedExit = 1
            $stopExecution = $true
        }
        else {
            $orphanArgs = @("--traceability", $traceabilityPath, "--since-commit", $resolvedSinceCommit)
            foreach ($pattern in $orphanIncludePatterns) {
                $orphanArgs += @("--include", $pattern)
            }
            $ok = Add-And-Check (Invoke-PythonGate -GateName "G07_orphan_change_gate" -ScriptPath (Join-Path $scriptRoot "validate_orphan_changes.py") -PythonPath $pythonPath -RepoRootAbs $repoRootAbs -LogPath $logsDirAbs -Arguments $orphanArgs -PreviewOnly:$DryRun)
            if (-not $ok) { $stopExecution = $true }
        }
    }
}

# 8) Dispatch lifecycle gate
if (-not $stopExecution) {
    if ($SkipDispatchGate) {
        $gateResults += (New-GateResult -Gate "G08_dispatch_lifecycle_gate" -Status "SKIPPED" -ExitCode 0 -Command "-" -LogPath "-" -StartedUtc (Get-UtcIso) -EndedUtc (Get-UtcIso) -Message "Skipped by -SkipDispatchGate")
    }
    else {
        $ok = Add-And-Check (Invoke-PythonGate -GateName "G08_dispatch_lifecycle_gate" -ScriptPath (Join-Path $scriptRoot "validate_dispatch_acks.py") -PythonPath $pythonPath -RepoRootAbs $repoRootAbs -LogPath $logsDirAbs -Arguments @("--manifest", $dispatchManifestPath, "--scan-root", $scanRootAbs, "--timeout-minutes", $DispatchTimeoutMinutes) -PreviewOnly:$DryRun)
        if (-not $ok) { $stopExecution = $true }
    }
}

# 9) Build CEO digest
if (-not $stopExecution) {
    $ok = Add-And-Check (Invoke-PythonGate -GateName "G09_build_ceo_digest" -ScriptPath (Join-Path $scriptRoot "build_ceo_bridge_digest.py") -PythonPath $pythonPath -RepoRootAbs $repoRootAbs -LogPath $logsDirAbs -Arguments @("--sources", ("{0},{1},{2},{3}" -f $workerAggregatePath, $traceabilityPath, $escalationPath, $workerReplyPath), "--output", $digestPath) -PreviewOnly:$DryRun)
    if (-not $ok) { $stopExecution = $true }
}

# 10) Digest freshness
if (-not $stopExecution) {
    $ok = Add-And-Check (Invoke-PythonGate -GateName "G10_digest_freshness_gate" -ScriptPath (Join-Path $scriptRoot "validate_digest_freshness.py") -PythonPath $pythonPath -RepoRootAbs $repoRootAbs -LogPath $logsDirAbs -Arguments @("--input", $digestPath, "--ttl-minutes", $DigestTtlMinutes) -PreviewOnly:$DryRun)
    if (-not $ok) { $stopExecution = $true }
}

$endedUtc = Get-UtcIso
$statusPath = Join-Path $logsDirAbs ("phase_end_handover_status_{0}.json" -f $script:RunId)
$summaryPath = Join-Path $logsDirAbs ("phase_end_handover_summary_{0}.md" -f $script:RunId)

$runState = [ordered]@{
    schema_version   = "1.0.0"
    run_id           = $script:RunId
    started_utc      = $startedUtc
    ended_utc        = $endedUtc
    repo_root        = $repoRootAbs
    repo_profile     = $(if ([string]::IsNullOrWhiteSpace($RepoProfile)) { "default" } else { $RepoProfile })
    result           = $overall
    failed_gate      = $failedGate
    failed_exit_code = $failedExit
    logs_dir         = $logsDirAbs
    resolved_config  = $resolvedConfig
    gates            = $gateResults
}

if ($DryRun) {
    Write-Host "[DRY-RUN] No files written."
    if ($overall -eq "BLOCK") {
        Write-Host ("[DRY-RUN] Would BLOCK at gate: {0}" -f $failedGate)
    }
    exit 0
}

Write-RunArtifacts -StatusPath $statusPath -SummaryPath $summaryPath -RunState $runState
Write-Host ("Run status: {0}" -f $overall)
Write-Host ("Status JSON: {0}" -f $statusPath)
Write-Host ("Summary MD: {0}" -f $summaryPath)

if ($overall -eq "BLOCK") {
    Write-Host ("BLOCKED at gate: {0} (exit={1})" -f $failedGate, $failedExit)
    exit 1
}

exit 0
