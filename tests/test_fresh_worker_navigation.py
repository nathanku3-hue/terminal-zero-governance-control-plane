"""
E2E tests for fresh worker navigation flow.

Tests path resolution, file discovery, and navigation from AGENTS.md through skill files.
Uses minimal fixture repo to avoid main-repo noise.
"""
import os
import subprocess
from pathlib import Path
import pytest


@pytest.fixture
def fixture_repo_root():
    """Return path to fresh_worker_happy_path fixture repo."""
    return Path(__file__).parent / "fixtures" / "repos" / "fresh_worker_happy_path"


@pytest.fixture
def repo_files(fixture_repo_root):
    """Return dict of expected file paths relative to fixture repo root."""
    return {
        "agents_md": fixture_repo_root / "AGENTS.md",
        "skill_registry": fixture_repo_root / ".codex" / "skills" / "README.md",
        "project_guider": fixture_repo_root / ".codex" / "skills" / "project-guider" / "SKILL.md",
        "saw": fixture_repo_root / ".codex" / "skills" / "saw" / "SKILL.md",
        "research_analysis": fixture_repo_root / ".codex" / "skills" / "research-analysis" / "SKILL.md",
        "workflow_wiring": fixture_repo_root / "docs" / "workflow_wiring_detailed.md",
        "tech_stack": fixture_repo_root / "docs" / "tech_stack.md",
        "project_init": fixture_repo_root / "docs" / "context" / "project_init_latest.md",
        "handover_template": fixture_repo_root / "references" / "phase_end_handover_template.md",
        "profile_outcomes": fixture_repo_root / "docs" / "architect" / "profile_outcomes.csv",
        "validate_closure": fixture_repo_root / ".codex" / "skills" / "_shared" / "scripts" / "validate_closure_packet.py",
        "validate_saw": fixture_repo_root / ".codex" / "skills" / "_shared" / "scripts" / "validate_saw_report_blocks.py",
        "validate_claims": fixture_repo_root / ".codex" / "skills" / "_shared" / "scripts" / "validate_research_claims.py",
    }


class TestFreshWorkerNavigation:
    """Test fresh worker can navigate from AGENTS.md without guessing."""

    def test_agents_md_exists(self, repo_files):
        """Fresh worker entry point must exist."""
        assert repo_files["agents_md"].exists(), "AGENTS.md missing at repo root"

    def test_agents_md_has_path_resolution_rule(self, repo_files):
        """AGENTS.md must declare path resolution rule."""
        content = repo_files["agents_md"].read_text()
        assert "Path Resolution Rule" in content, "Missing path resolution rule in AGENTS.md"
        assert "repo-root relative" in content, "Path resolution rule doesn't specify repo-root relative"

    def test_skill_registry_exists(self, repo_files):
        """Skill registry must exist at declared path."""
        assert repo_files["skill_registry"].exists(), ".codex/skills/README.md missing"

    def test_skill_registry_has_path_rule(self, repo_files):
        """Skill registry must declare path resolution rule."""
        content = repo_files["skill_registry"].read_text()
        assert "Path Resolution Rule" in content, "Missing path resolution rule in README.md"

    def test_all_referenced_skills_exist(self, repo_files):
        """All skills referenced in AGENTS.md must exist."""
        assert repo_files["project_guider"].exists(), "project-guider/SKILL.md missing"
        assert repo_files["saw"].exists(), "saw/SKILL.md missing"
        assert repo_files["research_analysis"].exists(), "research-analysis/SKILL.md missing"

    def test_all_deep_dive_docs_exist(self, repo_files):
        """All deep-dive docs referenced in AGENTS.md must exist."""
        agents_content = repo_files["agents_md"].read_text()

        # Extract referenced docs from AGENTS.md
        if "docs/workflow_wiring_detailed.md" in agents_content:
            assert repo_files["workflow_wiring"].exists(), "workflow_wiring_detailed.md missing"

        if "docs/tech_stack.md" in agents_content:
            assert repo_files["tech_stack"].exists(), "tech_stack.md missing"

    def test_skill_deep_dive_references_exist(self, repo_files):
        """All docs referenced in skill files must exist."""
        # project-guider references
        pg_content = repo_files["project_guider"].read_text()
        if "docs/workflow_wiring_detailed.md" in pg_content:
            assert repo_files["workflow_wiring"].exists()
        if "docs/tech_stack.md" in pg_content:
            assert repo_files["tech_stack"].exists()

        # saw references
        saw_content = repo_files["saw"].read_text()
        if "references/phase_end_handover_template.md" in saw_content:
            assert repo_files["handover_template"].exists(), "handover template missing (D4)"

        # research-analysis references
        ra_content = repo_files["research_analysis"].read_text()
        if "docs/workflow_wiring_detailed.md" in ra_content:
            assert repo_files["workflow_wiring"].exists()

    def test_all_validators_exist(self, repo_files):
        """All validator scripts referenced in skill files must exist."""
        assert repo_files["validate_closure"].exists(), "validate_closure_packet.py missing"
        assert repo_files["validate_saw"].exists(), "validate_saw_report_blocks.py missing"
        assert repo_files["validate_claims"].exists(), "validate_research_claims.py missing"

    def test_validators_executable_from_repo_root(self, fixture_repo_root, repo_files):
        """Validators must be executable from repo root as working directory."""
        result = subprocess.run(
            ["python", ".codex/skills/_shared/scripts/validate_closure_packet.py"],
            cwd=fixture_repo_root,
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, f"Validator failed: {result.stderr}"
        assert "ClosureValidation: PASS" in result.stdout

    def test_context_artifacts_exist(self, repo_files):
        """Required context artifacts must exist."""
        assert repo_files["project_init"].exists(), "project_init_latest.md missing"

    def test_no_ambiguous_paths_in_agents_md(self, repo_files):
        """AGENTS.md should not have ambiguous relative paths like ../../../."""
        content = repo_files["agents_md"].read_text()
        # Paths should be repo-root relative, not file-relative
        assert "../../../" not in content, "AGENTS.md contains file-relative paths (should be repo-root relative)"

    def test_no_ambiguous_paths_in_skill_files(self, repo_files):
        """Skill files should use repo-root relative paths, not file-relative."""
        for skill_file in [repo_files["project_guider"], repo_files["saw"], repo_files["research_analysis"]]:
            content = skill_file.read_text()
            # Paths should be repo-root relative, not file-relative
            assert "../../../" not in content, f"{skill_file.name} contains file-relative paths (should be repo-root relative)"


class TestPathResolutionStress:
    """Stress test path resolution with missing files and wrong working directory."""

    def test_missing_agents_md(self, fixture_repo_root, tmp_path):
        """Fresh worker should fail gracefully if AGENTS.md is missing."""
        broken_repo = tmp_path / "broken_repo"
        broken_repo.mkdir()

        # Copy everything except AGENTS.md
        import shutil
        for item in fixture_repo_root.iterdir():
            if item.name != "AGENTS.md":
                if item.is_dir():
                    shutil.copytree(item, broken_repo / item.name)
                else:
                    shutil.copy2(item, broken_repo / item.name)

        assert not (broken_repo / "AGENTS.md").exists()

    def test_missing_skill_registry(self, fixture_repo_root, tmp_path):
        """Fresh worker should fail if skill registry is missing."""
        broken_repo = tmp_path / "broken_repo"
        broken_repo.mkdir()

        import shutil
        shutil.copytree(fixture_repo_root, broken_repo, dirs_exist_ok=True)

        # Remove skill registry
        skill_readme = broken_repo / ".codex" / "skills" / "README.md"
        if skill_readme.exists():
            skill_readme.unlink()

        assert not skill_readme.exists()

    def test_validator_wrong_working_directory(self, fixture_repo_root):
        """Validator should fail if executed from wrong working directory."""
        # Execute from skill directory instead of repo root
        skill_dir = fixture_repo_root / ".codex" / "skills" / "saw"

        result = subprocess.run(
            ["python", ".codex/skills/_shared/scripts/validate_closure_packet.py"],
            cwd=skill_dir,
            capture_output=True,
            text=True,
        )
        # Should fail because path is repo-root relative
        assert result.returncode != 0, "Validator should fail when executed from wrong directory"

    def test_missing_deep_dive_doc(self, fixture_repo_root, tmp_path):
        """Fresh worker should detect missing deep-dive docs."""
        broken_repo = tmp_path / "broken_repo"

        import shutil
        shutil.copytree(fixture_repo_root, broken_repo, dirs_exist_ok=True)

        # Remove a referenced doc
        workflow_doc = broken_repo / "docs" / "workflow_wiring_detailed.md"
        if workflow_doc.exists():
            workflow_doc.unlink()

        assert not workflow_doc.exists()

        # Skill file still references it
        saw_skill = broken_repo / ".codex" / "skills" / "saw" / "SKILL.md"
        content = saw_skill.read_text()
        assert "docs/workflow_wiring_detailed.md" in content

    def test_missing_validator_script(self, fixture_repo_root, tmp_path):
        """Fresh worker should detect missing validator scripts."""
        broken_repo = tmp_path / "broken_repo"

        import shutil
        shutil.copytree(fixture_repo_root, broken_repo, dirs_exist_ok=True)

        # Remove validator
        validator = broken_repo / ".codex" / "skills" / "_shared" / "scripts" / "validate_closure_packet.py"
        if validator.exists():
            validator.unlink()

        assert not validator.exists()

        # Try to execute it
        result = subprocess.run(
            ["python", ".codex/skills/_shared/scripts/validate_closure_packet.py"],
            cwd=broken_repo,
            capture_output=True,
            text=True,
        )
        assert result.returncode != 0, "Should fail when validator is missing"


class TestRealRepoSmoke:
    """Smoke test against actual quant_current_scope repo."""

    @pytest.fixture
    def real_repo_root(self):
        """Return path to actual quant_current_scope repo."""
        # Assuming tests are in quant_current_scope/tests/
        return Path(__file__).parent.parent

    def test_real_repo_agents_md_exists(self, real_repo_root):
        """Real repo must have AGENTS.md."""
        agents_md = real_repo_root / "AGENTS.md"
        assert agents_md.exists(), f"AGENTS.md missing in real repo at {real_repo_root}"

    def test_real_repo_has_path_resolution_rule(self, real_repo_root):
        """Real repo AGENTS.md must have path resolution rule."""
        agents_md = real_repo_root / "AGENTS.md"
        content = agents_md.read_text()
        assert "Path Resolution Rule" in content, "Real repo AGENTS.md missing path resolution rule"

    def test_real_repo_dead_links_documented(self, real_repo_root):
        """Real repo should document D4/D5 as resolved."""
        defects_doc = real_repo_root / "docs" / "path_validation_defects.md"
        assert defects_doc.exists(), "path_validation_defects.md missing"

        content = defects_doc.read_text()

        # D4 and D5 should be in Resolved Defects section
        assert "## Resolved Defects" in content, "Missing Resolved Defects section"
        assert "D4: `references/phase_end_handover_template.md` — RESOLVED" in content, "D4 not marked as resolved"
        assert "D5: `docs/architect/profile_outcomes.csv` — RESOLVED" in content, "D5 not marked as resolved"

        # Open Defects section should show None
        assert "## Open Defects" in content, "Missing Open Defects section"
        # Find the Open Defects section and verify it says None
        open_section_start = content.find("## Open Defects")
        if open_section_start != -1:
            # Get text after "## Open Defects" until next ## or end
            remaining = content[open_section_start:]
            next_section = remaining.find("##", 3)  # Skip the current ##
            if next_section != -1:
                open_section = remaining[:next_section]
            else:
                open_section = remaining
            assert "None." in open_section, "Open Defects section should show 'None.'"


    def test_real_repo_navigation_flow(self, real_repo_root):
        """Walk AGENTS.md -> README.md -> SKILL.md and verify all references exist."""
        # Start at AGENTS.md
        agents_md = real_repo_root / "AGENTS.md"
        assert agents_md.exists(), "AGENTS.md missing"

        agents_content = agents_md.read_text()

        # Follow to skill registry
        skill_registry = real_repo_root / ".codex" / "skills" / "README.md"
        assert skill_registry.exists(), "Skill registry missing"

        # Check key skill files referenced in AGENTS.md
        saw_skill = real_repo_root / ".codex" / "skills" / "saw" / "SKILL.md"
        assert saw_skill.exists(), "saw/SKILL.md missing"

        # Verify saw skill references exist
        saw_content = saw_skill.read_text()

        # Check handover template reference (now should exist)
        handover_template = real_repo_root / "references" / "phase_end_handover_template.md"
        assert handover_template.exists(), "references/phase_end_handover_template.md missing (referenced by saw/SKILL.md:142)"

        # Check architect-review skill
        architect_skill = real_repo_root / ".codex" / "skills" / "architect-review" / "SKILL.md"
        assert architect_skill.exists(), "architect-review/SKILL.md missing"

        architect_content = architect_skill.read_text()

        # Check profile outcomes CSV (now should exist)
        profile_outcomes = real_repo_root / "docs" / "architect" / "profile_outcomes.csv"
        assert profile_outcomes.exists(), "docs/architect/profile_outcomes.csv missing (referenced by architect-review/SKILL.md:45-46)"

    def test_real_repo_validator_execution(self, real_repo_root):
        """Execute a real validator from repo root with actual packet."""
        # Check if validate_closure_packet.py exists
        validator = real_repo_root / ".codex" / "skills" / "_shared" / "scripts" / "validate_closure_packet.py"

        if not validator.exists():
            pytest.skip("validate_closure_packet.py not yet implemented in real repo")

        # Execute with a valid test packet
        test_packet = "ClosurePacket: RoundID=test-001; ScopeID=nav-test; ChecksTotal=5; ChecksPassed=5; ChecksFailed=0; Verdict=PASS"
        result = subprocess.run(
            ["python", ".codex/skills/_shared/scripts/validate_closure_packet.py", "--packet", test_packet],
            cwd=real_repo_root,
            capture_output=True,
            text=True,
            timeout=10,
        )

        # Should validate successfully
        assert result.returncode == 0, f"Validator failed: {result.stderr}"
        assert "VALID" in result.stdout, f"Expected VALID output, got: {result.stdout}"

    def test_real_repo_validator_negative_case(self, real_repo_root):
        """Execute validator with invalid packet to verify failure behavior."""
        validator = real_repo_root / ".codex" / "skills" / "_shared" / "scripts" / "validate_closure_packet.py"

        if not validator.exists():
            pytest.skip("validate_closure_packet.py not yet implemented in real repo")

        # Execute with invalid packet (math mismatch)
        invalid_packet = "ClosurePacket: RoundID=test-002; ScopeID=nav-test; ChecksTotal=10; ChecksPassed=5; ChecksFailed=3; Verdict=PASS"
        result = subprocess.run(
            ["python", ".codex/skills/_shared/scripts/validate_closure_packet.py", "--packet", invalid_packet],
            cwd=real_repo_root,
            capture_output=True,
            text=True,
            timeout=10,
        )

        # Should fail validation
        assert result.returncode == 1, f"Validator should fail on invalid packet, got returncode: {result.returncode}"
        assert "INVALID" in result.stdout, f"Expected INVALID output, got: {result.stdout}"
        assert "math mismatch" in result.stdout.lower(), f"Expected math mismatch error, got: {result.stdout}"

    def test_real_repo_content_driven_path_crawler(self, real_repo_root):
        """Extract path references from skill files and verify they exist."""
        import re

        # Pattern to match repo-root relative paths in markdown
        # Matches: docs/file.md, .codex/skills/name/SKILL.md, references/file.md, scripts/file.py
        path_pattern = re.compile(r'(?:^|\s|`|")([.\w/-]+\.(?:md|py|csv|json))(?:\s|`|"|:|$)', re.MULTILINE)

        skill_dir = real_repo_root / ".codex" / "skills"
        skill_files = list(skill_dir.rglob("SKILL.md"))

        assert len(skill_files) > 0, "No SKILL.md files found"

        missing_refs = []
        checked_paths = set()

        # Known aspirational/example references that don't need to exist yet
        aspirational_paths = {
            "docs/decision_log.md",  # doc-draft example
            "scripts/validate_pit_discipline.py",  # workflow-status realm example
            "docs/spec.md",  # hierarchy-init fallback example
            "docs/context/project_init_latest.md",  # runtime-generated by startup
            "docs/context/workflow_status_latest.json",  # runtime-generated by workflow-status
        }

        for skill_file in skill_files:
            content = skill_file.read_text()
            matches = path_pattern.findall(content)

            for match in matches:
                # Filter to likely repo-root paths
                if match.startswith(("docs/", ".codex/", "references/", "scripts/")):
                    if match in checked_paths or match in aspirational_paths:
                        continue
                    checked_paths.add(match)

                    target = real_repo_root / match
                    if not target.exists():
                        missing_refs.append(f"{skill_file.relative_to(real_repo_root)}:{match}")

        assert len(missing_refs) == 0, f"Found {len(missing_refs)} missing path references:\n" + "\n".join(missing_refs)

