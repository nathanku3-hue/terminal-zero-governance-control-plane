param(
    [string]$RepoRoot = ".",
    [ValidateSet("", "Quant", "Film")]
    [string]$RepoProfile = "",
    [string]$TraceabilityPath = "",
    [string]$DispatchManifestPath = "",
    [string]$WorkerReplyPath = "",
    [string[]]$OrphanInclude = @(),
    [string[]]$OrphanExclude = @(),
    [string]$PythonExe = "",
    [string]$LogsRelativeDir = "docs/context/phase_end_logs",
    [string]$ScanRoot = "",
    [string]$SinceCommit = "",
    [int]$DigestTtlMinutes = 60,
    [int]$DispatchTimeoutMinutes = 10,
    [switch]$SkipOrphanGate,
    [switch]$SkipDispatchGate,
    [string]$CrossRepoRoots = "",
    [switch]$EnforceScoreThresholds,
    [ValidateSet("none", "shadow", "enforce")]
    [string]$AuditMode = "enforce",
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
                scan_root               = "E:/Code/Quant/docs"
                traceability_candidates = @(
                    "docs/pm_to_code_traceability.yaml",
                    "docs/context/pm_to_code_traceability.yaml"
                )
                dispatch_manifest       = "docs/context/dispatch_manifest.json"
                worker_reply_packet     = "docs/context/worker_reply_packet.json"
                orphan_include          = @("*.py", "*.ps1", "*.ts", "*.tsx", "*.js", "*.jsx", "*.yaml", "*.yml")
                orphan_exclude          = @("docs/archive/**")
            }
        }
        "Film" {
            return [ordered]@{
                repo_root               = "E:/Code/Film"
                scan_root               = "E:/Code/Film/docs"
                traceability_candidates = @(
                    "docs/pm_to_code_traceability.yaml",
                    "docs/context/pm_to_code_traceability.yaml"
                )
                dispatch_manifest       = "docs/context/dispatch_manifest.json"
                worker_reply_packet     = "docs/context/worker_reply_packet.json"
                orphan_include          = @("*.py", "*.ps1", "*.ts", "*.tsx", "*.js", "*.jsx", "*.yaml", "*.yml")
                orphan_exclude          = @("docs/archive/**")
            }
        }
        default {
            return [ordered]@{
                repo_root               = "."
                scan_root               = "docs"
                traceability_candidates = @(
                    "docs/pm_to_code_traceability.yaml",
                    "docs/context/pm_to_code_traceability.yaml"
                )
                dispatch_manifest       = "docs/context/dispatch_manifest.json"
                worker_reply_packet     = "docs/context/worker_reply_packet.json"
                orphan_include          = @("*.py", "*.ps1", "*.ts", "*.tsx", "*.js", "*.jsx", "*.yaml", "*.yml")
                orphan_exclude          = @("docs/archive/**")
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
$orphanExcludePatterns = if ($OrphanExclude -and $OrphanExclude.Count -gt 0) {
    $OrphanExclude
}
else {
    @($profileDefaults.orphan_exclude)
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
    orphan_exclude         = $orphanExcludePatterns
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

# 5b) Cross-repo readiness gate (triad + threshold pre-flight)
if (-not $stopExecution) {
    if ($EnforceScoreThresholds -and [string]::IsNullOrWhiteSpace($CrossRepoRoots)) {
        # Mandatory when -EnforceScoreThresholds is true: cannot bypass by omitting -CrossRepoRoots
        $gateResults += (New-GateResult -Gate "G05b_cross_repo_readiness" -Status "BLOCK" -ExitCode 1 -Command "-" -LogPath "-" -StartedUtc (Get-UtcIso) -EndedUtc (Get-UtcIso) -Message "Cross-repo readiness is mandatory when -EnforceScoreThresholds is enabled. Provide -CrossRepoRoots.")
        $overall = "BLOCK"
        $failedGate = "G05b_cross_repo_readiness"
        $failedExit = 1
        $stopExecution = $true
    }
    elseif (-not [string]::IsNullOrWhiteSpace($CrossRepoRoots)) {
        $repoList = $CrossRepoRoots -split ","
        $allCrossRepoPassed = $true
        $crossRepoMessages = @()
        foreach ($crossRepo in $repoList) {
            $crossRepoTrimmed = $crossRepo.Trim()
            if ([string]::IsNullOrWhiteSpace($crossRepoTrimmed)) { continue }
            $crossRepoAbs = Resolve-AbsolutePath -BasePath (Get-Location).Path -PathValue $crossRepoTrimmed
            $crossRepoPacket = Join-Path $crossRepoAbs "docs/context/worker_reply_packet.json"
            if (-not (Test-Path -LiteralPath $crossRepoPacket)) {
                $crossRepoMessages += "Worker reply packet not found: $crossRepoPacket"
                $allCrossRepoPassed = $false
                continue
            }
            $crossRepoArgs = @("--input", $crossRepoPacket, "--schema-version-override", "2.0.0")
            if ($EnforceScoreThresholds) {
                $crossRepoArgs += "--enforce-score-thresholds"
            }
            $crossRepoResult = Invoke-PythonGate -GateName "G05b_cross_repo_readiness_$crossRepoTrimmed" -ScriptPath (Join-Path $scriptRoot "validate_worker_reply_packet.py") -PythonPath $pythonPath -RepoRootAbs $crossRepoAbs -LogPath $logsDirAbs -Arguments $crossRepoArgs -PreviewOnly:$DryRun
            if ($crossRepoResult.Status -ne "PASS") {
                $crossRepoMessages += "Cross-repo readiness failed for $crossRepoTrimmed. Update worker packets before enabling enforcement."
                $allCrossRepoPassed = $false
            }
        }
        if ($allCrossRepoPassed) {
            $gateResults += (New-GateResult -Gate "G05b_cross_repo_readiness" -Status "PASS" -ExitCode 0 -Command "validate_worker_reply_packet.py (cross-repo)" -LogPath "-" -StartedUtc (Get-UtcIso) -EndedUtc (Get-UtcIso) -Message "All cross-repo packets passed readiness check.")
        }
        else {
            $combinedMsg = $crossRepoMessages -join "; "
            $gateResults += (New-GateResult -Gate "G05b_cross_repo_readiness" -Status "BLOCK" -ExitCode 1 -Command "validate_worker_reply_packet.py (cross-repo)" -LogPath "-" -StartedUtc (Get-UtcIso) -EndedUtc (Get-UtcIso) -Message $combinedMsg)
            $overall = "BLOCK"
            $failedGate = "G05b_cross_repo_readiness"
            $failedExit = 1
            $stopExecution = $true
        }
    }
    else {
        $gateResults += (New-GateResult -Gate "G05b_cross_repo_readiness" -Status "SKIPPED" -ExitCode 0 -Command "-" -LogPath "-" -StartedUtc (Get-UtcIso) -EndedUtc (Get-UtcIso) -Message "No -CrossRepoRoots provided and -EnforceScoreThresholds not set.")
    }
}

# 6) Worker reply gate (confidence + citations + triad/threshold when enforced)
# CUTOVER: Enable -EnforceScoreThresholds after all repos pass G05b readiness gate.
# Phase 25+ will remove v1 path entirely from validate_worker_reply_packet.py.
if (-not $stopExecution) {
    $g06Args = @("--input", $workerReplyPath, "--repo-root", $repoRootAbs, "--require-existing-paths")
    if ($EnforceScoreThresholds) {
        $g06Args += "--enforce-score-thresholds"
    }
    $ok = Add-And-Check (Invoke-PythonGate -GateName "G06_worker_reply_gate" -ScriptPath (Join-Path $scriptRoot "validate_worker_reply_packet.py") -PythonPath $pythonPath -RepoRootAbs $repoRootAbs -LogPath $logsDirAbs -Arguments $g06Args -PreviewOnly:$DryRun)
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
            foreach ($pattern in $orphanExcludePatterns) {
                if (-not [string]::IsNullOrWhiteSpace($pattern)) {
                    $orphanArgs += @("--exclude", $pattern)
                }
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

# Capture primary failure before finalize path
$primaryFailedGate = $failedGate
$primaryFailedExit = $failedExit
$primaryOverall = $overall
$finalizeFailures = @()

# 11) Auditor review gate
$auditorOutputPath = ""
if ($AuditMode -ne "none") {
    # Run-scoped auditor output to prevent stale file ingestion
    $auditorOutputPath = Join-Path $logsDirAbs ("auditor_findings_{0}.json" -f $script:RunId)
    $canonicalAuditorPath = Resolve-AbsolutePath -BasePath $repoRootAbs -PathValue "docs/context/auditor_findings.json"

    $g11Started = Get-UtcIso
    $g11Result = Invoke-PythonGate -GateName "G11_auditor_review" -ScriptPath (Join-Path $scriptRoot "run_auditor_review.py") -PythonPath $pythonPath -RepoRootAbs $repoRootAbs -LogPath $logsDirAbs -Arguments @("--input", $workerReplyPath, "--repo-root", $repoRootAbs, "--output", $auditorOutputPath, "--mode", $AuditMode) -PreviewOnly:$DryRun

    if ($g11Result.exit_code -eq 2) {
        # Infra error: always block regardless of mode
        $g11Result.status = "BLOCK"
        $g11Result.message = "Auditor infra error (exit=2); check script logs"
        $gateResults += $g11Result
        if ([string]::IsNullOrWhiteSpace($primaryFailedGate)) {
            $overall = "BLOCK"
            $failedGate = "G11_auditor_review"
            $failedExit = 2
            $primaryFailedGate = $failedGate
            $primaryFailedExit = $failedExit
            $primaryOverall = $overall
        }
    }
    elseif ($AuditMode -eq "shadow") {
        # Shadow: policy findings non-blocking
        $g11Result.status = "PASS"
        $g11Result.message = "Shadow mode: findings logged (see $auditorOutputPath)"
        $gateResults += $g11Result
    }
    elseif ($AuditMode -eq "enforce") {
        $gateResults += $g11Result
        if ($g11Result.status -eq "BLOCK") {
            if ([string]::IsNullOrWhiteSpace($primaryFailedGate)) {
                $overall = "BLOCK"
                $failedGate = "G11_auditor_review"
                $failedExit = $g11Result.exit_code
                $primaryFailedGate = $failedGate
                $primaryFailedExit = $failedExit
                $primaryOverall = $overall
            }
        }
    }

    # Copy to canonical path on successful auditor completion (exit 0 or 1 = valid policy output)
    if (-not $DryRun -and (Test-Path -LiteralPath $auditorOutputPath) -and $g11Result.exit_code -ne 2) {
        Copy-Item -LiteralPath $auditorOutputPath -Destination $canonicalAuditorPath -Force
    }
}
else {
    $gateResults += (New-GateResult -Gate "G11_auditor_review" -Status "SKIPPED" -ExitCode 0 -Command "-" -LogPath "-" -StartedUtc (Get-UtcIso) -EndedUtc (Get-UtcIso) -Message "Skipped by -AuditMode none")
}

# --- Finalize path: G09b + G10b (always run when AuditMode != none) ---
# These run regardless of G11 verdict so the final digest includes auditor findings.
if ($AuditMode -ne "none") {
    # Build digest sources — include run-scoped auditor output if it exists
    $g09bSources = "{0},{1},{2},{3}" -f $workerAggregatePath, $traceabilityPath, $escalationPath, $workerReplyPath
    if ((Test-Path -LiteralPath $auditorOutputPath)) {
        $g09bSources += ",$auditorOutputPath"
    }

    $g09bResult = Invoke-PythonGate -GateName "G09b_rebuild_ceo_digest" -ScriptPath (Join-Path $scriptRoot "build_ceo_bridge_digest.py") -PythonPath $pythonPath -RepoRootAbs $repoRootAbs -LogPath $logsDirAbs -Arguments @("--sources", $g09bSources, "--output", $digestPath) -PreviewOnly:$DryRun
    $gateResults += $g09bResult
    if ($g09bResult.status -eq "BLOCK") {
        $finalizeFailures += $g09bResult
    }

    $g10bResult = Invoke-PythonGate -GateName "G10b_digest_freshness_revalidation" -ScriptPath (Join-Path $scriptRoot "validate_digest_freshness.py") -PythonPath $pythonPath -RepoRootAbs $repoRootAbs -LogPath $logsDirAbs -Arguments @("--input", $digestPath, "--ttl-minutes", $DigestTtlMinutes) -PreviewOnly:$DryRun
    $gateResults += $g10bResult
    if ($g10bResult.status -eq "BLOCK") {
        $finalizeFailures += $g10bResult
    }
}

# --- Block-precedence resolution ---
# Primary failure (G00–G11) takes precedence. Finalize failures are secondary.
if (-not [string]::IsNullOrWhiteSpace($primaryFailedGate)) {
    $overall = "BLOCK"
    $failedGate = $primaryFailedGate
    $failedExit = $primaryFailedExit
}
elseif ($finalizeFailures.Count -gt 0) {
    $overall = "BLOCK"
    $failedGate = $finalizeFailures[0].gate
    $failedExit = $finalizeFailures[0].exit_code
}

$endedUtc = Get-UtcIso
$statusPath = Join-Path $logsDirAbs ("phase_end_handover_status_{0}.json" -f $script:RunId)
$summaryPath = Join-Path $logsDirAbs ("phase_end_handover_summary_{0}.md" -f $script:RunId)

$runState = [ordered]@{
    schema_version       = "1.0.0"
    run_id               = $script:RunId
    started_utc          = $startedUtc
    ended_utc            = $endedUtc
    repo_root            = $repoRootAbs
    repo_profile         = $(if ([string]::IsNullOrWhiteSpace($RepoProfile)) { "default" } else { $RepoProfile })
    result               = $overall
    failed_gate          = $failedGate
    failed_exit_code     = $failedExit
    finalize_failures    = @($finalizeFailures | ForEach-Object { $_.gate })
    logs_dir             = $logsDirAbs
    resolved_config      = $resolvedConfig
    gates                = $gateResults
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

# Non-blocking CEO GO signal refresh (fail-open).
$ceoGoScriptPath = Join-Path $scriptRoot "generate_ceo_go_signal.py"
$ceoGoCalibrationPath = Resolve-AbsolutePath -BasePath $repoRootAbs -PathValue "docs/context/auditor_calibration_report.json"
$ceoGoDossierPath = Resolve-AbsolutePath -BasePath $repoRootAbs -PathValue "docs/context/auditor_promotion_dossier.json"
$ceoGoOutputPath = Resolve-AbsolutePath -BasePath $repoRootAbs -PathValue "docs/context/ceo_go_signal.md"
if (Test-Path -LiteralPath $ceoGoScriptPath) {
    $goSignalExitCode = 0
    $previousNativePref = $null
    if (Get-Variable -Name PSNativeCommandUseErrorActionPreference -ErrorAction SilentlyContinue) {
        $previousNativePref = $PSNativeCommandUseErrorActionPreference
        $PSNativeCommandUseErrorActionPreference = $false
    }
    $previousErrorAction = $ErrorActionPreference
    $ErrorActionPreference = "Continue"
    Push-Location $repoRootAbs
    try {
        & $pythonPath $ceoGoScriptPath --calibration-json $ceoGoCalibrationPath --dossier-json $ceoGoDossierPath --output $ceoGoOutputPath
        $goSignalExitCode = $LASTEXITCODE
    }
    finally {
        $ErrorActionPreference = $previousErrorAction
        if ($null -ne $previousNativePref) {
            $PSNativeCommandUseErrorActionPreference = $previousNativePref
        }
        Pop-Location
    }

    if ($goSignalExitCode -eq 0) {
        Write-Host ("CEO GO signal refreshed: {0}" -f $ceoGoOutputPath)
    }
    else {
        Write-Warning ("CEO GO signal refresh failed (exit={0}). Phase-end verdict unchanged." -f $goSignalExitCode)
    }
}
else {
    Write-Warning ("CEO GO signal script not found: {0}" -f $ceoGoScriptPath)
}

if ($overall -eq "BLOCK") {
    Write-Host ("BLOCKED at gate: {0} (exit={1})" -f $failedGate, $failedExit)
    exit 1
}

exit 0
