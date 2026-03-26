"""Tests for Phase 5C.1 — repo_map.py"""
from __future__ import annotations

import json
import sys
import textwrap
from pathlib import Path

try:
    from sop.scripts.repo_map import build_repo_map, format_repo_map_text, main
except ModuleNotFoundError:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
    from sop.scripts.repo_map import build_repo_map, format_repo_map_text, main


def _py(directory: Path, name: str, source: str) -> Path:
    p = directory / name
    p.write_text(textwrap.dedent(source), encoding="utf-8")
    return p


# --- output contract ---

def test_repo_map_keys_present(tmp_path):
    _py(tmp_path, "a.py", "x = 1")
    r = build_repo_map(tmp_path)
    for k in ("repo_root", "generated_at_utc", "file_count", "files", "errors"):
        assert k in r

def test_entry_keys_present(tmp_path):
    _py(tmp_path, "a.py", "def foo(): pass")
    entry = build_repo_map(tmp_path)["files"][0]
    for k in ("path", "symbols", "imports", "error"):
        assert k in entry

def test_file_count_matches_files_length(tmp_path):
    _py(tmp_path, "a.py", "x=1")
    _py(tmp_path, "b.py", "y=2")
    r = build_repo_map(tmp_path)
    assert r["file_count"] == len(r["files"])

def test_repo_root_is_absolute(tmp_path):
    _py(tmp_path, "a.py", "x=1")
    assert Path(build_repo_map(tmp_path)["repo_root"]).is_absolute()

def test_generated_at_utc_ends_with_z(tmp_path):
    _py(tmp_path, "a.py", "x=1")
    assert build_repo_map(tmp_path)["generated_at_utc"].endswith("Z")

def test_path_uses_posix_separators(tmp_path):
    sub = tmp_path / "pkg"
    sub.mkdir()
    _py(sub, "mod.py", "x=1")
    assert build_repo_map(tmp_path)["files"][0]["path"] == "pkg/mod.py"


# --- symbol extraction ---

def test_extracts_function(tmp_path):
    _py(tmp_path, "a.py", "def my_func(): pass")
    assert "my_func" in build_repo_map(tmp_path)["files"][0]["symbols"]

def test_extracts_class(tmp_path):
    _py(tmp_path, "a.py", "class MyClass: pass")
    assert "MyClass" in build_repo_map(tmp_path)["files"][0]["symbols"]

def test_extracts_async_function(tmp_path):
    _py(tmp_path, "a.py", "async def my_async(): pass")
    assert "my_async" in build_repo_map(tmp_path)["files"][0]["symbols"]

def test_does_not_extract_nested_functions(tmp_path):
    _py(tmp_path, "a.py", "def outer():\n    def inner(): pass")
    syms = build_repo_map(tmp_path)["files"][0]["symbols"]
    assert "outer" in syms
    assert "inner" not in syms

def test_empty_file_has_empty_symbols(tmp_path):
    _py(tmp_path, "a.py", "")
    assert build_repo_map(tmp_path)["files"][0]["symbols"] == []


# --- import extraction ---

def test_extracts_simple_import(tmp_path):
    _py(tmp_path, "a.py", "import os")
    assert "os" in build_repo_map(tmp_path)["files"][0]["imports"]

def test_extracts_from_import_first_segment(tmp_path):
    _py(tmp_path, "a.py", "from pathlib import Path")
    assert "pathlib" in build_repo_map(tmp_path)["files"][0]["imports"]

def test_deduplicates_imports(tmp_path):
    _py(tmp_path, "a.py", "import os\nimport os.path\nfrom os import getcwd")
    assert build_repo_map(tmp_path)["files"][0]["imports"].count("os") == 1

def test_dotted_import_first_segment_only(tmp_path):
    _py(tmp_path, "a.py", "import sop.scripts.repo_map")
    assert "sop" in build_repo_map(tmp_path)["files"][0]["imports"]


# --- exclusions ---

def test_excludes_pycache(tmp_path):
    pc = tmp_path / "__pycache__"
    pc.mkdir()
    _py(pc, "c.py", "x=1")
    assert not any("__pycache__" in e["path"] for e in build_repo_map(tmp_path)["files"])

def test_excludes_dot_git(tmp_path):
    gd = tmp_path / ".git"
    gd.mkdir()
    _py(gd, "hook.py", "x=1")
    assert not any(".git" in e["path"] for e in build_repo_map(tmp_path)["files"])

def test_excludes_venv(tmp_path):
    venv = tmp_path / ".venv" / "lib"
    venv.mkdir(parents=True)
    _py(venv, "site.py", "x=1")
    assert not any(".venv" in e["path"] for e in build_repo_map(tmp_path)["files"])

def test_include_tests_false_excludes_tests_dir(tmp_path):
    td = tmp_path / "tests"
    td.mkdir()
    _py(td, "test_foo.py", "def test_foo(): pass")
    _py(tmp_path, "main.py", "x=1")
    r = build_repo_map(tmp_path, include_tests=False)
    paths = [e["path"] for e in r["files"]]
    assert "main.py" in paths
    assert not any("tests" in p for p in paths)

def test_include_tests_true_includes_tests_dir(tmp_path):
    td = tmp_path / "tests"
    td.mkdir()
    _py(td, "test_foo.py", "def test_foo(): pass")
    assert any("tests" in e["path"] for e in build_repo_map(tmp_path, include_tests=True)["files"])

def test_extra_excludes_respected(tmp_path):
    sd = tmp_path / "generated"
    sd.mkdir()
    _py(sd, "auto.py", "x=1")
    _py(tmp_path, "real.py", "x=1")
    r = build_repo_map(tmp_path, extra_excludes=frozenset({"generated"}))
    paths = [e["path"] for e in r["files"]]
    assert "real.py" in paths
    assert not any("generated" in p for p in paths)


# --- path filter ---

def test_path_filter_restricts_to_prefix(tmp_path):
    pkg = tmp_path / "src" / "sop"
    pkg.mkdir(parents=True)
    _py(pkg, "mod.py", "def foo(): pass")
    _py(tmp_path, "other.py", "x=1")
    r = build_repo_map(tmp_path, path_filter=["src/sop/"])
    paths = [e["path"] for e in r["files"]]
    assert all(p.startswith("src/sop/") for p in paths)
    assert "other.py" not in paths

def test_path_filter_multiple_prefixes(tmp_path):
    for d in ("a", "b", "c"):
        (tmp_path / d).mkdir()
        _py(tmp_path / d, "mod.py", "x=1")
    r = build_repo_map(tmp_path, path_filter=["a/", "b/"])
    paths = [e["path"] for e in r["files"]]
    assert any(p.startswith("a/") for p in paths)
    assert any(p.startswith("b/") for p in paths)
    assert not any(p.startswith("c/") for p in paths)

def test_path_filter_empty_list_returns_nothing(tmp_path):
    _py(tmp_path, "a.py", "x=1")
    assert build_repo_map(tmp_path, path_filter=[])["file_count"] == 0


# --- fail-closed ---

def test_syntax_error_recorded_in_errors(tmp_path):
    (tmp_path / "bad.py").write_text("def broken(", encoding="utf-8")
    assert "bad.py" in build_repo_map(tmp_path)["errors"]

def test_syntax_error_entry_still_in_files(tmp_path):
    (tmp_path / "bad.py").write_text("def broken(", encoding="utf-8")
    assert any(e["path"] == "bad.py" for e in build_repo_map(tmp_path)["files"])

def test_syntax_error_entry_has_error_set(tmp_path):
    (tmp_path / "bad.py").write_text("def broken(", encoding="utf-8")
    entry = next(e for e in build_repo_map(tmp_path)["files"] if e["path"] == "bad.py")
    assert entry["error"] is not None
    assert "SyntaxError" in entry["error"]

def test_syntax_error_has_empty_symbols_and_imports(tmp_path):
    (tmp_path / "bad.py").write_text("def broken(", encoding="utf-8")
    entry = next(e for e in build_repo_map(tmp_path)["files"] if e["path"] == "bad.py")
    assert entry["symbols"] == []
    assert entry["imports"] == []

def test_good_file_parsed_alongside_bad(tmp_path):
    (tmp_path / "bad.py").write_text("def broken(", encoding="utf-8")
    _py(tmp_path, "good.py", "def ok(): pass")
    r = build_repo_map(tmp_path)
    good = next(e for e in r["files"] if e["path"] == "good.py")
    assert good["error"] is None
    assert "ok" in good["symbols"]


# --- empty repo ---

def test_empty_repo_file_count_zero(tmp_path):
    r = build_repo_map(tmp_path)
    assert r["file_count"] == 0
    assert r["files"] == []
    assert r["errors"] == []

def test_main_returns_1_for_empty_repo(tmp_path):
    assert main(["--repo-root", str(tmp_path)]) == 1


# --- format_repo_map_text ---

def test_format_produces_nonempty_string(tmp_path):
    _py(tmp_path, "a.py", "def foo(): pass")
    assert len(format_repo_map_text(build_repo_map(tmp_path))) > 0

def test_format_includes_file_path(tmp_path):
    _py(tmp_path, "a.py", "def foo(): pass")
    assert "a.py" in format_repo_map_text(build_repo_map(tmp_path))

def test_format_includes_symbol_name(tmp_path):
    _py(tmp_path, "a.py", "def my_func(): pass")
    assert "my_func" in format_repo_map_text(build_repo_map(tmp_path))

def test_format_annotates_error_entries(tmp_path):
    (tmp_path / "bad.py").write_text("def broken(", encoding="utf-8")
    assert "ERROR" in format_repo_map_text(build_repo_map(tmp_path))

def test_format_max_symbols_cap(tmp_path):
    funcs = "\n".join(f"def f{i}(): pass" for i in range(30))
    _py(tmp_path, "a.py", funcs)
    text = format_repo_map_text(build_repo_map(tmp_path), max_symbols=5)
    sym_line = next(l for l in text.splitlines() if l.strip().startswith("symbols:"))
    assert len(sym_line.split(":", 1)[1].strip().split(",")) <= 5


# --- CLI ---

def test_cli_returns_zero_for_non_empty_repo(tmp_path):
    _py(tmp_path, "a.py", "x=1")
    assert main(["--repo-root", str(tmp_path)]) == 0

def test_cli_text_flag(tmp_path, capsys):
    _py(tmp_path, "a.py", "def foo(): pass")
    main(["--repo-root", str(tmp_path), "--text"])
    out = capsys.readouterr().out
    assert "Repo map" in out
    assert "a.py" in out

def test_cli_output_writes_json_file(tmp_path):
    _py(tmp_path, "a.py", "x=1")
    out_file = tmp_path / "out" / "map.json"
    main(["--repo-root", str(tmp_path), "--output", str(out_file)])
    assert out_file.exists()
    assert json.loads(out_file.read_text(encoding="utf-8"))["file_count"] >= 1

def test_cli_no_tests_excludes_tests_dir(tmp_path):
    td = tmp_path / "tests"
    td.mkdir()
    _py(td, "test_x.py", "def test_x(): pass")
    _py(tmp_path, "main.py", "x=1")
    out_file = tmp_path / "map.json"
    main(["--repo-root", str(tmp_path), "--no-tests", "--output", str(out_file)])
    data = json.loads(out_file.read_text(encoding="utf-8"))
    assert not any("tests" in e["path"] for e in data["files"])

def test_cli_path_filter_restricts_output(tmp_path):
    src = tmp_path / "src"
    src.mkdir()
    _py(src, "mod.py", "x=1")
    _py(tmp_path, "other.py", "y=2")
    out_file = tmp_path / "map.json"
    main(["--repo-root", str(tmp_path), "--path-filter", "src/", "--output", str(out_file)])
    data = json.loads(out_file.read_text(encoding="utf-8"))
    assert all(e["path"].startswith("src/") for e in data["files"])
