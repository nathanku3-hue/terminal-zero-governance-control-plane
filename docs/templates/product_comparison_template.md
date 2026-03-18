# Product Comparison Template

Status: Template  
Authority: advisory-only; instantiate into `docs/context/product_comparison_latest.md`.  
Purpose: compare researched products and make explicit `COPY`, `MODIFY_ON_TOP`, and `REJECT` decisions from both technical and product/operator perspectives before implementation.

## Header
- `COMPARISON_ID`: `<YYYYMMDD-short-id>`
- `OWNER`: `<name>`
- `DATE_UTC`: `<ISO8601>`
- `SCOPE`: `<decision or system scope>`
- `PRIMARY_OBJECTIVE`: `<one sentence>`
- `NON_GOALS`: `<one sentence>`
- `REVIEW_TRIGGER`: `<architecture_choice|tooling_choice|adoption_review|other>`

## Comparison Lens
- `TRANSFER_BOUNDARY`: `<what may transfer vs what must stay repo-specific>`
- `AUTHORITY_NOTE`: `Advisory only; final implementation and policy decisions still follow the normal PM/CEO approval path.`
- `SOURCE_ACCESS_NOTES`: `<unreadable, gated, or client-rendered sources>`

## Product Entries

### PRODUCT_1: `<name>`
- `WHY_RESEARCHED`: `<why this product is in scope>`
- `TECHNICAL_PERSPECTIVE`
  - `COPY`:
    - `<technical pattern to reuse as-is>`
  - `MODIFY_ON_TOP`:
    - `<technical pattern> -> <required repo-specific modification>`
  - `REJECT`:
    - `<technical pattern + reason>`
- `PRODUCT_PERSPECTIVE`
  - `COPY`:
    - `<product/operator pattern to reuse as-is>`
  - `MODIFY_ON_TOP`:
    - `<product/operator pattern> -> <required repo-specific modification>`
  - `REJECT`:
    - `<product/operator pattern + reason>`
- `EVIDENCE_PATHS`:
  - `<path or link>`
- `OPEN_RISKS`: `<one line or NONE>`

### PRODUCT_2: `<name>`
- `WHY_RESEARCHED`: `<why this product is in scope>`
- `TECHNICAL_PERSPECTIVE`
  - `COPY`:
    - `<technical pattern to reuse as-is>`
  - `MODIFY_ON_TOP`:
    - `<technical pattern> -> <required repo-specific modification>`
  - `REJECT`:
    - `<technical pattern + reason>`
- `PRODUCT_PERSPECTIVE`
  - `COPY`:
    - `<product/operator pattern to reuse as-is>`
  - `MODIFY_ON_TOP`:
    - `<product/operator pattern> -> <required repo-specific modification>`
  - `REJECT`:
    - `<product/operator pattern + reason>`
- `EVIDENCE_PATHS`:
  - `<path or link>`
- `OPEN_RISKS`: `<one line or NONE>`

### PRODUCT_3 (Optional): `<name>`
- `WHY_RESEARCHED`: `<why this product is in scope>`
- `TECHNICAL_PERSPECTIVE`
  - `COPY`:
    - `<technical pattern to reuse as-is>`
  - `MODIFY_ON_TOP`:
    - `<technical pattern> -> <required repo-specific modification>`
  - `REJECT`:
    - `<technical pattern + reason>`
- `PRODUCT_PERSPECTIVE`
  - `COPY`:
    - `<product/operator pattern to reuse as-is>`
  - `MODIFY_ON_TOP`:
    - `<product/operator pattern> -> <required repo-specific modification>`
  - `REJECT`:
    - `<product/operator pattern + reason>`
- `EVIDENCE_PATHS`:
  - `<path or link>`
- `OPEN_RISKS`: `<one line or NONE>`

## Cross-Product Synthesis
- `TECHNICAL_KEEP_THESE_PATTERNS`: `<shared technical patterns worth reusing>`
- `PRODUCT_KEEP_THESE_PATTERNS`: `<shared product/operator patterns worth reusing>`
- `DO_NOT_IMPORT`: `<shared anti-patterns to keep out>`
- `BIGGEST_DECISION_RISK`: `<main failure mode if the comparison is wrong>`
- `NEXT_ACTION`: `<single next action>`

## Endgame
- `PRODUCT_ENDGAME`: `<the intended operator/user experience if this goes right>`
- `TECHNICAL_ENDGAME`: `<the intended system shape if this goes right>`
- `WHAT_WE_ARE_NOT_BUILDING`: `<explicit anti-goals>`

## Notes
- `docs/context/product_comparison_latest.md` is the authoritative working copy.
- This artifact does not create a new gate or authority path.
