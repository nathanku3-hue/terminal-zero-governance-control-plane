# Quickstart (Helm)

## Context
Deploy and execute Terminal Zero governance as a Kubernetes Job using the in-repo chart source.

## Prerequisites
- Kubernetes cluster access (`kubectl` context set)
- Helm 3.x
- A PVC for workspace mounting (or equivalent values override)
- Local chart source available at `./charts/terminal-zero-governance`

## Commands
```bash
helm upgrade --install t0-governance ./charts/terminal-zero-governance \
  --namespace governance --create-namespace \
  --set image.repository=ghcr.io/<org>/terminal-zero-governance \
  --set image.tag=latest \
  --set workspace.pvcName=governance-workspace

kubectl -n governance get jobs
kubectl -n governance logs job/t0-governance-terminal-zero-governance --tail=100
kubectl -n governance get pods -l app.kubernetes.io/instance=t0-governance
```

## Output
```text
$ helm upgrade --install t0-governance ./charts/terminal-zero-governance --namespace governance --create-namespace ...
Release "t0-governance" has been upgraded. Happy Helming!
NAME: t0-governance
NAMESPACE: governance
STATUS: deployed
REVISION: 3

$ kubectl -n governance logs job/t0-governance-terminal-zero-governance --tail=100
[loop] gate=preflight status=PASS
[loop] gate=execution status=PASS decision=ALLOW
[loop] artifacts: docs/context/audit_log.ndjson
[loop] final_result=PASS
```

## Expected Decision
`PASS` in job logs, with governance artifacts written to mounted workspace.

## Rollback
```bash
helm rollback t0-governance 2 -n governance
kubectl -n governance delete job -l app.kubernetes.io/instance=t0-governance
```
