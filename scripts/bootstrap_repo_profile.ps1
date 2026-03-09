param(
    [ValidateSet("", "Quant", "Film")]
    [string]$RepoProfile = "",
    [string]$RepoRoot = "",
    [switch]$WithContextSkeleton,
    [bool]$EnsureMinimalContext = $true,
    [switch]$SkipContextBuild,
    [string]$PythonExe = "",
    [switch]$Force,
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

function Get-RepoProfileRoot {
    param([string]$ProfileName)
    switch ($ProfileName) {
        "Quant" { return "E:/Code/Quant" }
        "Film" { return "E:/Code/Film" }
        default { return "." }
    }
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

function Ensure-Directory {
    param(
        [Parameter(Mandatory = $true)]
        [string]$PathValue
    )
    if ($DryRun) {
        Write-Host ("[DRY-RUN] Ensure directory: {0}" -f $PathValue)
        return
    }
    New-Item -ItemType Directory -Path $PathValue -Force | Out-Null
}

function Write-TextFile {
    param(
        [Parameter(Mandatory = $true)]
        [string]$PathValue,
        [Parameter(Mandatory = $true)]
        [string]$Content,
        [switch]$Overwrite
    )
    if ((Test-Path -LiteralPath $PathValue) -and (-not $Overwrite)) {
        Write-Host ("[SKIP] Exists: {0}" -f $PathValue)
        return
    }
    if ($DryRun) {
        $action = if (Test-Path -LiteralPath $PathValue) { "Overwrite" } else { "Create" }
        Write-Host ("[DRY-RUN] {0}: {1}" -f $action, $PathValue)
        return
    }
    $parent = Split-Path -Path $PathValue -Parent
    if (-not [string]::IsNullOrWhiteSpace($parent) -and -not (Test-Path -LiteralPath $parent)) {
        New-Item -ItemType Directory -Path $parent -Force | Out-Null
    }
    $utf8NoBom = New-Object System.Text.UTF8Encoding($false)
    [System.IO.File]::WriteAllText($PathValue, $Content, $utf8NoBom)
    $actionDone = if (Test-Path -LiteralPath $PathValue) { "Wrote" } else { "Created" }
    Write-Host ("[{0}] {1}" -f $actionDone.ToUpper(), $PathValue)
}

function Write-JsonFile {
    param(
        [Parameter(Mandatory = $true)]
        [string]$PathValue,
        [Parameter(Mandatory = $true)]
        [hashtable]$Payload,
        [switch]$Overwrite
    )
    $json = $Payload | ConvertTo-Json -Depth 12
    Write-TextFile -PathValue $PathValue -Content $json -Overwrite:$Overwrite
}

function Test-ContextSourceBaseline {
    param(
        [Parameter(Mandatory = $true)]
        [string]$RepoRootAbs
    )
    $phaseBriefMatches = @(Get-ChildItem -Path (Join-Path $RepoRootAbs "docs/phase_brief") -Filter "phase*-brief.md" -File -ErrorAction SilentlyContinue)
    $phaseHandoverMatches = @(Get-ChildItem -Path (Join-Path $RepoRootAbs "docs/handover") -Filter "phase*_handover.md" -File -ErrorAction SilentlyContinue)

    $hasBrief = $phaseBriefMatches.Count -gt 0
    $hasHandover = $phaseHandoverMatches.Count -gt 0
    $hasDecisionLog = Test-Path -LiteralPath (Join-Path $RepoRootAbs "docs/decision log.md")
    $hasLessons = Test-Path -LiteralPath (Join-Path $RepoRootAbs "docs/lessonss.md")
    $hasTopLevelPm = Test-Path -LiteralPath (Join-Path $RepoRootAbs "top_level_PM.md")
    return ($hasBrief -and $hasHandover -and $hasDecisionLog -and $hasLessons -and $hasTopLevelPm)
}

$effectiveRepoRoot = if (-not [string]::IsNullOrWhiteSpace($RepoRoot)) {
    $RepoRoot
}
else {
    Get-RepoProfileRoot -ProfileName $RepoProfile
}

$repoRootAbs = Resolve-AbsolutePath -BasePath (Get-Location).Path -PathValue $effectiveRepoRoot
if (-not (Test-Path -LiteralPath $repoRootAbs)) {
    throw "Repo root does not exist: $repoRootAbs"
}

$profileLabel = if ([string]::IsNullOrWhiteSpace($RepoProfile)) { "default" } else { $RepoProfile }
$nowUtc = Get-UtcIso
$deadlineUtc = [DateTime]::UtcNow.AddHours(24).ToString("yyyy-MM-ddTHH:mm:ssZ")
$hasContextBaseline = Test-ContextSourceBaseline -RepoRootAbs $repoRootAbs
$emitContextSkeleton = [bool]$WithContextSkeleton -or ([bool]$EnsureMinimalContext -and (-not $hasContextBaseline))

$docsDir = Resolve-AbsolutePath -BasePath $repoRootAbs -PathValue "docs"
$contextDir = Resolve-AbsolutePath -BasePath $repoRootAbs -PathValue "docs/context"
$evidenceHashesDir = Resolve-AbsolutePath -BasePath $repoRootAbs -PathValue "docs/context/evidence_hashes"
$phaseBriefDir = Resolve-AbsolutePath -BasePath $repoRootAbs -PathValue "docs/phase_brief"
$handoverDir = Resolve-AbsolutePath -BasePath $repoRootAbs -PathValue "docs/handover"

$traceabilityPath = Resolve-AbsolutePath -BasePath $repoRootAbs -PathValue "docs/pm_to_code_traceability.yaml"
$workerReplyPath = Resolve-AbsolutePath -BasePath $repoRootAbs -PathValue "docs/context/worker_reply_packet.json"
$dispatchManifestPath = Resolve-AbsolutePath -BasePath $repoRootAbs -PathValue "docs/context/dispatch_manifest.json"
$phaseBriefPath = Resolve-AbsolutePath -BasePath $repoRootAbs -PathValue "docs/phase_brief/phase0-brief.md"
$phaseHandoverPath = Resolve-AbsolutePath -BasePath $repoRootAbs -PathValue "docs/handover/phase0_handover.md"
$decisionLogPath = Resolve-AbsolutePath -BasePath $repoRootAbs -PathValue "docs/decision log.md"
$lessonsPath = Resolve-AbsolutePath -BasePath $repoRootAbs -PathValue "docs/lessonss.md"
$topLevelPmPath = Resolve-AbsolutePath -BasePath $repoRootAbs -PathValue "top_level_PM.md"

Write-Host "Bootstrap target:"
Write-Host ("  profile: {0}" -f $profileLabel)
Write-Host ("  repo_root: {0}" -f $repoRootAbs)
Write-Host ("  with_context_skeleton: {0}" -f [bool]$WithContextSkeleton)
Write-Host ("  ensure_minimal_context: {0}" -f [bool]$EnsureMinimalContext)
Write-Host ("  has_context_baseline: {0}" -f [bool]$hasContextBaseline)
Write-Host ("  emit_context_skeleton: {0}" -f [bool]$emitContextSkeleton)
Write-Host ("  skip_context_build: {0}" -f [bool]$SkipContextBuild)
Write-Host ("  force: {0}" -f [bool]$Force)
Write-Host ("  dry_run: {0}" -f [bool]$DryRun)

Ensure-Directory -PathValue $docsDir
Ensure-Directory -PathValue $contextDir
Ensure-Directory -PathValue $evidenceHashesDir
if ($emitContextSkeleton) {
    Ensure-Directory -PathValue $phaseBriefDir
    Ensure-Directory -PathValue $handoverDir
}

$traceabilityContent = @(
    'schema_version: "1.0.0"',
    'phase: "phase_bootstrap"',
    ('last_updated_utc: "{0}"' -f $nowUtc),
    "",
    "directives: []",
    ""
) -join [Environment]::NewLine
Write-TextFile -PathValue $traceabilityPath -Content $traceabilityContent -Overwrite:$Force

$workerReplyPayload = [ordered]@{
    schema_version   = "2.0.0"
    worker_id        = "@bootstrap"
    phase            = "phase_bootstrap"
    generated_at_utc = $nowUtc
    items            = @(
        [ordered]@{
            task_id      = "T-BOOTSTRAP"
            decision     = "Bootstrap scaffold created. Replace this packet with real worker output before phase-end."
            dod_result   = "PARTIAL"
            evidence_ids = @("BOOTSTRAP")
            open_risks   = @("bootstrap placeholder must be replaced with real task evidence")
            citations    = @(
                [ordered]@{
                    type    = "doc"
                    path    = "docs/context/worker_reply_packet.json"
                    locator = "items[0]"
                    claim   = "bootstrap placeholder exists and should be replaced before handover"
                }
            )
            machine_optimized = [ordered]@{
                confidence_level = [ordered]@{
                    score     = 0.30
                    band      = "LOW"
                    rationale = "placeholder scaffold, not execution evidence"
                }
                problem_solving_alignment_score = 0.0
                expertise_coverage = @(
                    [ordered]@{
                        domain    = "principal"
                        verdict   = "SKIPPED"
                        rationale = "bootstrap placeholder - replace before phase-end"
                    },
                    [ordered]@{
                        domain    = "riskops"
                        verdict   = "SKIPPED"
                        rationale = "bootstrap placeholder - replace before phase-end"
                    },
                    [ordered]@{
                        domain    = "qa"
                        verdict   = "SKIPPED"
                        rationale = "bootstrap placeholder - replace before phase-end"
                    }
                )
            }
            pm_first_principles = [ordered]@{
                problem     = "bootstrap placeholder - replace before phase-end"
                constraints = "bootstrap placeholder - replace before phase-end"
                logic       = "bootstrap placeholder - replace before phase-end"
                solution    = "bootstrap placeholder - replace before phase-end"
            }
        }
    )
}
Write-JsonFile -PathValue $workerReplyPath -Payload $workerReplyPayload -Overwrite:$Force

$dispatchPayload = [ordered]@{
    schema_version            = "1.0.0"
    dispatch_id               = ("DISP-BOOTSTRAP-{0}" -f ([DateTime]::UtcNow.ToString("yyyyMMdd")))
    command_plan_hash_sha256  = "sha256:bootstrap"
    ack_deadline_utc          = $deadlineUtc
    tasks                     = @()
}
Write-JsonFile -PathValue $dispatchManifestPath -Payload $dispatchPayload -Overwrite:$Force

if ($emitContextSkeleton) {
    $phaseBriefContent = @(
        "# Phase 0 Brief",
        "",
        "## Status",
        "- Bootstrap initialized",
        "",
        "## Objective",
        "- Establish first executable context packet and handover contract.",
        ""
    ) -join [Environment]::NewLine
    Write-TextFile -PathValue $phaseBriefPath -Content $phaseBriefContent -Overwrite:$Force

    $phaseHandoverContent = @(
        "# Phase 0 Handover",
        "",
        "## New Context Packet",
        "## What Was Done",
        "- Repository bootstrap scaffolding was created for closed-loop gates.",
        "## What Is Locked",
        "- Bootstrap files are placeholders and must be replaced by real phase outputs before release.",
        "## What Is Next",
        "- Replace bootstrap directives with real PM directives and evidence links.",
        "- Publish the first production phase brief and handover.",
        "## First Command",
        "Draft docs/phase_brief/phase1-brief.md and update docs/handover/phase1_handover.md.",
        ""
    ) -join [Environment]::NewLine
    Write-TextFile -PathValue $phaseHandoverPath -Content $phaseHandoverContent -Overwrite:$Force

    $decisionLogContent = @(
        "Decision Log: Bootstrap",
        "",
        "| ID | Component | Decision | Rationale |",
        "|----|-----------|----------|-----------|",
        "| B-001 | bootstrap | Initialize minimal governance scaffolds | Enable fail-closed phase-end gating on new repos. |",
        ""
    ) -join [Environment]::NewLine
    Write-TextFile -PathValue $decisionLogPath -Content $decisionLogContent -Overwrite:$Force

    $lessonsContent = @(
        "# Lessons",
        "",
        "## 2026-03-01",
        "- Mistake: New repo lacked context files required by context packet builder.",
        "- Root cause: Bootstrap only covered gate preflight assets, not context sources.",
        "- Fix: Added optional context skeleton generation in bootstrap script.",
        "- Guardrail: Use -WithContextSkeleton when initializing new repos.",
        ""
    ) -join [Environment]::NewLine
    Write-TextFile -PathValue $lessonsPath -Content $lessonsContent -Overwrite:$Force

    $topLevelPmContent = @(
        "# Top Level PM and Thinker Compass",
        "",
        "Date: 2026-03-01",
        "Owner: PM / Architecture Office",
        "Status: ACTIVE",
        "",
        "## Core Base",
        "- McKinsey-style decomposition",
        "- MECE",
        "- 5W1H",
        "- Pyramid Principle",
        "",
        "## Expansion",
        "- Systems Dynamics and Cybernetics",
        "- Axiomatic Design and Design by Contract",
        "- Antifragility",
        "- TPS Jidoka",
        "- OODA Loop",
        "- Theory of Constraints",
        "- Cynefin Framework",
        "- Ergodicity and Survival Logic",
        ""
    ) -join [Environment]::NewLine
    Write-TextFile -PathValue $topLevelPmPath -Content $topLevelPmContent -Overwrite:$Force
}

$contextScriptPath = Resolve-AbsolutePath -BasePath $PSScriptRoot -PathValue "build_context_packet.py"
$contextBuildState = "SKIPPED"
$contextBuildMessage = ""
if ($SkipContextBuild) {
    $contextBuildState = "SKIPPED"
    $contextBuildMessage = "Skipped by -SkipContextBuild."
}
elseif (-not (Test-Path -LiteralPath $contextScriptPath)) {
    throw "Context build script not found: $contextScriptPath"
}
else {
    $pythonPath = Resolve-PythonExecutable -Requested $PythonExe
    if ($DryRun) {
        Write-Host ("[DRY-RUN] Context build: {0} {1} --repo-root {2}" -f $pythonPath, $contextScriptPath, $repoRootAbs)
        Write-Host ("[DRY-RUN] Context validate: {0} {1} --repo-root {2} --validate" -f $pythonPath, $contextScriptPath, $repoRootAbs)
        $contextBuildState = "PREVIEW"
        $contextBuildMessage = "Dry-run only."
    }
    else {
        $previousNativePref = $null
        if (Get-Variable -Name PSNativeCommandUseErrorActionPreference -ErrorAction SilentlyContinue) {
            $previousNativePref = $PSNativeCommandUseErrorActionPreference
            $PSNativeCommandUseErrorActionPreference = $false
        }
        $previousErrorAction = $ErrorActionPreference
        $ErrorActionPreference = "Continue"
        try {
            & $pythonPath $contextScriptPath --repo-root $repoRootAbs
            $buildExit = $LASTEXITCODE
            if ($buildExit -ne 0) {
                throw "Context build failed (exit=$buildExit)."
            }
            & $pythonPath $contextScriptPath --repo-root $repoRootAbs --validate
            $validateExit = $LASTEXITCODE
            if ($validateExit -ne 0) {
                throw "Context validate failed (exit=$validateExit)."
            }
        }
        finally {
            $ErrorActionPreference = $previousErrorAction
            if ($null -ne $previousNativePref) {
                $PSNativeCommandUseErrorActionPreference = $previousNativePref
            }
        }
        $contextBuildState = "PASS"
        $contextBuildMessage = "current_context.json/current_context.md and phase handover artifact generated."
    }
}

Write-Host ""
Write-Host "Bootstrap completed."
Write-Host ("  traceability: {0}" -f $traceabilityPath)
Write-Host ("  worker_reply: {0}" -f $workerReplyPath)
Write-Host ("  dispatch_manifest: {0}" -f $dispatchManifestPath)
Write-Host ("  evidence_hashes_dir: {0}" -f $evidenceHashesDir)
if ($emitContextSkeleton) {
    Write-Host ("  phase_brief: {0}" -f $phaseBriefPath)
    Write-Host ("  phase_handover: {0}" -f $phaseHandoverPath)
    Write-Host ("  decision_log: {0}" -f $decisionLogPath)
    Write-Host ("  lessons: {0}" -f $lessonsPath)
    Write-Host ("  top_level_pm: {0}" -f $topLevelPmPath)
}
Write-Host ("  context_build_state: {0}" -f $contextBuildState)
if (-not [string]::IsNullOrWhiteSpace($contextBuildMessage)) {
    Write-Host ("  context_build_message: {0}" -f $contextBuildMessage)
}
Write-Host ""
Write-Host "Next:"
Write-Host ("  powershell -ExecutionPolicy Bypass -File scripts/phase_end_handover.ps1 -RepoRoot '{0}' -ScanRoot '{0}\docs' -SkipOrphanGate -SkipDispatchGate -DryRun" -f $repoRootAbs)
