# Troubleshooting

## Context
Resolve common operator onboarding failures when running container and Helm tutorials.

## Failure Modes
### Image pull denied
Symptom: Container start fails with `pull access denied`.
Likely cause: Missing registry auth or incorrect org path.
Check: `docker pull ghcr.io/<org>/terminal-zero-governance:latest`
Fix: Authenticate to GHCR and verify org/repo permissions, then retry pull.

### Docker daemon unavailable
Symptom: Commands return `Cannot connect to the Docker daemon`.
Likely cause: Docker service is stopped.
Check: `docker info`
Fix: Start Docker Desktop/service and rerun quickstart commands.

### Workspace mount path invalid
Symptom: `sop run` fails with repo path not found in container.
Likely cause: Host path not mounted to `/workspace`.
Check: `docker run --rm -v "$PWD:/workspace" ghcr.io/<org>/terminal-zero-governance:latest ls /workspace`
Fix: Use the correct host path and ensure read/write permissions.

### Helm chart path not found
Symptom: Helm reports `path "./charts/terminal-zero-governance" not found`.
Likely cause: Command executed outside repo root.
Check: `pwd && ls ./charts/terminal-zero-governance`
Fix: Run from repo root or use absolute chart path.

### Namespace create forbidden
Symptom: Helm install fails with RBAC `forbidden` on namespace create.
Likely cause: Operator account lacks cluster-scoped create permissions.
Check: `kubectl auth can-i create namespaces`
Fix: Pre-create namespace with privileged account or use an existing namespace.

### PVC not found
Symptom: Pod remains Pending with volume claim errors.
Likely cause: `workspace.pvcName` points to missing claim.
Check: `kubectl -n governance get pvc`
Fix: Create the PVC or set `workspace.pvcName` to an existing claim.

### Job pod CrashLoopBackOff
Symptom: Pod restarts repeatedly and job does not complete.
Likely cause: Invalid command args or missing runtime dependency.
Check: `kubectl -n governance describe pod <pod-name>`
Fix: Correct Helm values/command and redeploy release.

### Missing governance artifacts
Symptom: Run completes but `docs/context` artifacts are absent.
Likely cause: Workspace mount is read-only or wrong path.
Check: `kubectl -n governance logs job/t0-governance-terminal-zero-governance --tail=200`
Fix: Mount writable workspace and confirm `--repo-root` points to mounted directory.

### Validation returns NOT_READY
Symptom: `sop validate` output is `NOT_READY`.
Likely cause: Required closure artifacts incomplete for this round.
Check: `sop audit --repo-root /workspace --tail 20`
Fix: Rerun `sop run --skip-phase-end` and verify expected artifact generation.

### Rollback does not restore healthy state
Symptom: Post-rollback job still fails with same error.
Likely cause: Persistent bad values or unchanged PVC data state.
Check: `helm history t0-governance -n governance`
Fix: Roll back to known good revision, then clear/reseed workspace state as needed.

## Diagnostics
```bash
kubectl -n governance get all
kubectl -n governance describe job t0-governance-terminal-zero-governance
kubectl -n governance logs job/t0-governance-terminal-zero-governance --tail=200
sop audit --repo-root /workspace --tail 20
```

## Remediation
```bash
helm upgrade --install t0-governance ./charts/terminal-zero-governance -n governance --create-namespace
kubectl -n governance delete job -l app.kubernetes.io/instance=t0-governance
docker pull ghcr.io/<org>/terminal-zero-governance:latest
```

## Output
```text
$ kubectl -n governance logs job/t0-governance-terminal-zero-governance --tail=200
[loop] gate=preflight status=PASS
[loop] gate=execution status=HOLD decision=BLOCK
[loop] reason=workspace pvc missing: governance-workspace
[loop] final_result=HOLD

$ sop validate --repo-root /workspace
NOT_READY
```

## Escalation
Escalate to platform/on-call when RBAC restrictions, registry access, or cluster storage policies prevent operator remediation.
