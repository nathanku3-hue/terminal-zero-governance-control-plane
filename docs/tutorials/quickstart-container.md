# Quickstart (Container)

## Context
Run one governance cycle using the published container image to validate operator onboarding flow.

## Prerequisites
- Docker Engine running
- A local repo path mounted to `/workspace`
- Image access to `ghcr.io/<org>/terminal-zero-governance:latest`

## Commands
```bash
docker pull ghcr.io/<org>/terminal-zero-governance:latest
docker run --rm ghcr.io/<org>/terminal-zero-governance:latest sop version
docker run --rm -v "$PWD:/workspace" ghcr.io/<org>/terminal-zero-governance:latest \
  sop run --repo-root /workspace --skip-phase-end
docker run --rm -v "$PWD:/workspace" ghcr.io/<org>/terminal-zero-governance:latest \
  sop validate --repo-root /workspace
```

## Output
```text
$ docker run --rm ghcr.io/<org>/terminal-zero-governance:latest sop version
terminal-zero-governance 1.0.0

$ docker run --rm -v "$PWD:/workspace" ghcr.io/<org>/terminal-zero-governance:latest sop run --repo-root /workspace --skip-phase-end
[loop] gate=preflight status=PASS
[loop] gate=execution status=PASS decision=ALLOW
[loop] artifacts: docs/context/loop_cycle_summary_latest.json
[loop] final_result=PASS

$ docker run --rm -v "$PWD:/workspace" ghcr.io/<org>/terminal-zero-governance:latest sop validate --repo-root /workspace
READY_TO_ESCALATE
```

## Expected Decision
`PASS` on run and `READY_TO_ESCALATE` on validate.

## Next Steps
- Run `sop audit --repo-root /workspace --tail 10` to inspect the decision trail.
- Proceed to Helm quickstart for Kubernetes execution parity.
