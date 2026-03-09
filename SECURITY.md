# Security Policy

This repository is a script-driven AI engineering governance control plane.  
This file is the public vulnerability disclosure policy for external reporters.

## Scope

- Covers security vulnerabilities in repository code, scripts, CI workflow definitions, and governance artifacts that can impact confidentiality, integrity, or availability.
- Covers vulnerabilities that can incorrectly move operational state to escalation-ready outcomes.
- Does not replace internal operational controls documented in `docs/security.md`.

## Supported Versions

- This project does not currently publish versioned security support windows.
- Security fixes are applied on the active default branch.
- If you are running an older snapshot, rebase to current `HEAD` and re-test before filing.

## Reporting a Vulnerability

Please do not post sensitive exploit details in a public issue.

Preferred reporting paths:
1. Use GitHub private vulnerability reporting / repository security advisories, if enabled for this repository.
2. If private reporting is unavailable, open a minimal public issue titled `Security Contact Request` with no exploit details, and request a private contact channel.

Include the following details when possible:
- affected file paths and command surface,
- reproducible steps,
- security impact and expected vs actual behavior,
- required environment or permissions,
- sanitized logs or artifacts (no secrets, keys, or tokens).

## What to Expect

- Reports are triaged on a best-effort basis.
- This repository does not offer a bug bounty program.
- This repository does not publish SLA response guarantees.
- Maintainers may coordinate remediation and request non-public handling until a fix is ready.

## Non-Security Issues

- Correctness, feature, or usability issues without a security impact should use normal issue channels.
- Internal operator runbook and fail-closed response procedures are defined in `docs/security.md`.

