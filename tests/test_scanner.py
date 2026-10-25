"""Unit tests for repository scanner and exclusions."""

import pytest
from pathlib import Path
from scanner import scan_python_files, is_excluded_path, DEFAULT_EXCLUDED_DIRS


def test_scanner_finds_sample_project_files():
    sample_dir = Path(__file__).parent.parent / "sample_project"
    files = scan_python_files(sample_dir)
    assert len(files) >= 6
    filenames = [f.name for f in files]
    assert "auth.py" in filenames
    assert "database.py" in filenames
    assert "billing.py" in filenames
    assert "config.py" in filenames
    assert "api.py" in filenames


def test_scanner_excludes_virtualenvs_and_git(tmp_path):
    # Setup temporary directory structure with git and venv
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "main.py").write_text("print('hello')")

    (tmp_path / ".git").mkdir()
    (tmp_path / ".git" / "hook.py").write_text("print('git')")

    (tmp_path / "venv").mkdir()
    (tmp_path / "venv" / "lib.py").write_text("print('venv')")

    (tmp_path / "__pycache__").mkdir()
    (tmp_path / "__pycache__" / "cached.py").write_text("print('cache')")

    discovered = scan_python_files(tmp_path)
    rel_paths = [str(p.relative_to(tmp_path)).replace("\\", "/") for p in discovered]

    assert "src/main.py" in rel_paths
    assert not any(".git" in p for p in rel_paths)
    assert not any("venv" in p for p in rel_paths)
    assert not any("__pycache__" in p for p in rel_paths)


def test_scanner_nonexistent_path():
    with pytest.raises(FileNotFoundError):
        scan_python_files("nonexistent_directory_xyz_12345")


def test_is_excluded_path_checks():
    root = Path("/dummy/repo")
    assert is_excluded_path(root / ".git" / "foo.py", root, DEFAULT_EXCLUDED_DIRS) is True
    assert is_excluded_path(root / "node_modules" / "bar.py", root, DEFAULT_EXCLUDED_DIRS) is True
    assert is_excluded_path(root / "pkg" / "my_module.py", root, DEFAULT_EXCLUDED_DIRS) is False
