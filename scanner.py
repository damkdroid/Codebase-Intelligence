
from pathlib import Path
from typing import Iterable, Set, List, Optional

DEFAULT_EXCLUDED_DIRS: Set[str] = {
    ".git",
    ".svn",
    ".hg",
    ".bzr",
    "venv",
    ".venv",
    "env",
    ".env",
    "virtualenv",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    ".coverage",
    "htmlcov",
    "build",
    "dist",
    "eggs",
    ".eggs",
    "node_modules",
    ".tox",
    "site-packages",
    ".idea",
    ".vscode",
}


def is_excluded_path(path: Path, root: Path, excluded_names: Set[str]) -> bool:
    """Check if a path or any of its parent components match the exclusion set.

    Args:
        path: Absolute or relative Path to test.
        root: Root directory of the scan.
        excluded_names: Set of directory or file names to ignore (case-insensitive).

    Returns:
        True if the path should be excluded, False otherwise.
    """
    try:
        rel_path = path.relative_to(root)
    except ValueError:
        rel_path = path

    normalized_excludes = {name.lower() for name in excluded_names}
    for part in rel_path.parts:
        lowered = part.lower()
        if lowered in normalized_excludes:
            return True
        if lowered.endswith(".egg-info"):
            return True
    return False


def scan_python_files(
    repo_path: str | Path,
    custom_excludes: Optional[Iterable[str]] = None
) -> List[Path]:
    """Recursively scan a repository path for .py files, ignoring excluded dirs.

    Args:
        repo_path: Path to the root directory to scan.
        custom_excludes: Optional additional folder/file names to ignore.

    Returns:
        Sorted list of Path objects for discovered Python files.

    Raises:
        FileNotFoundError: If repo_path does not exist.
        NotADirectoryError: If repo_path is not a directory.
    """
    root = Path(repo_path).resolve()
    if not root.exists():
        raise FileNotFoundError(f"Repository path does not exist: {root}")
    if not root.is_dir():
        raise NotADirectoryError(f"Repository path is not a directory: {root}")

    excluded = set(DEFAULT_EXCLUDED_DIRS)
    if custom_excludes:
        excluded.update(custom_excludes)

    python_files: List[Path] = []

    for file_path in root.rglob("*.py"):
        if not file_path.is_file():
            continue
        if is_excluded_path(file_path, root, excluded):
            continue
        python_files.append(file_path)

    return sorted(python_files)
