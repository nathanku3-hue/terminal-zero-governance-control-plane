#!/usr/bin/env python3
"""Fix Track 3: reorder check_loop_readiness and observability_pack steps."""
import pathlib
import re

files = [
    pathlib.Path('e:/Code/SOP/quant_current_scope/scripts/run_loop_cycle.py'),
    pathlib.Path('e:/Code/SOP/quant_current_scope/src/sop/scripts/run_loop_cycle.py'),
]

for fpath in files:
    if not fpath.exists():
        print(f'SKIP (not found): {fpath}')
        continue
    text = fpath.read_text(encoding='utf-8')

    # Find the Phase 3 Stream C block start
    marker_start = '    # Phase 3 Stream C -- emit loop_readiness_latest.json as post-run step'
    marker_obs = '    # K.2: observability pack drift marker check'
    marker_return = '\n    return final_exit_code, payload, markdown'

    idx_start = text.find(marker_start)
    idx_obs = text.find(marker_obs)
    idx_return = text.find(marker_return)

    print(f'File: {fpath.name}')
    print(f'  idx_start={idx_start}, idx_obs={idx_obs}, idx_return={idx_return}')

    if idx_start == -1 or idx_obs == -1 or idx_return == -1:
        print('  SKIP: markers not found')
        continue

    # The block to replace is from marker_start to end of return statement
    end_of_return = idx_return + len(marker_return)
    old_block = text[idx_start:end_of_return]

    # Extract the two sub-blocks
    phase3_block = text[idx_start:idx_obs]
    obs_block = text[idx_obs:idx_return]

    # Build new block: obs first, then phase3 (as best-effort subprocess, not runtime.steps)
    # Replace runtime.steps.append and _run_command in phase3_block with subprocess.run
    phase3_new = (
        '    # Phase 3 Stream C -- emit loop_readiness_latest.json as best-effort side effect\n'
        '    # Not appended to runtime.steps so step ordering remains stable.\n'
        '    _loop_readiness_script = ctx.repo_root / "scripts" / "check_loop_readiness.py"\n'
        '    if not _loop_readiness_script.exists():\n'
        '        _loop_readiness_script = ctx.repo_root / "src" / "sop" / "scripts" / "check_loop_readiness.py"\n'
        '    if _loop_readiness_script.exists():\n'
        '        try:\n'
        '            subprocess.run(\n'
        '                [\n'
        '                    ctx.python_exe,\n'
        '                    str(_loop_readiness_script),\n'
        '                    "--repo-root",\n'
        '                    str(ctx.repo_root),\n'
        '                    "--output",\n'
        '                    str(ctx.context_dir / "loop_readiness_latest.json"),\n'
        '                ],\n'
        '                cwd=str(ctx.repo_root),\n'
        '                capture_output=True,\n'
        '                text=True,\n'
        '                check=False,\n'
        '            )\n'
        '        except Exception:\n'
        '            pass  # best-effort; must never abort the loop\n'
        '\n'
    )

    # obs_block needs a comment update
    obs_new = obs_block.replace(
        '    # K.2: observability pack drift marker check',
        '    # K.2: observability pack drift marker check (must be last named step)'
    )

    new_block = obs_new + '\n' + phase3_new + '    return final_exit_code, payload, markdown'

    new_text = text[:idx_start] + new_block + text[end_of_return:]
    fpath.write_text(new_text, encoding='utf-8')
    print(f'  FIXED: wrote {len(new_text)} bytes')

print('Done.')
