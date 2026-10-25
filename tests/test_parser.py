"""Unit tests for AST code parser."""

from pathlib import Path
from parser import parse_python_file, parse_repository


def test_parse_valid_functions_and_classes(tmp_path):
    code = '''"""Module docstring."""
import os
from math import sqrt, pi

class MathHelper:
    """Class docstring."""
    def compute(self, x: int) -> float:
        """Compute square root."""
        return sqrt(x)

def top_level_func(a, b):
    return a + b
'''
    file_path = tmp_path / "calc.py"
    file_path.write_text(code, encoding="utf-8")

    result = parse_python_file(file_path, tmp_path)

    assert result.error is None
    assert result.line_count == 12
    assert len(result.classes) == 1
    assert result.classes[0].name == "MathHelper"
    assert result.classes[0].docstring == "Class docstring."
    assert "compute" in result.classes[0].methods

    assert len(result.functions) == 2
    func_names = [f.name for f in result.functions]
    assert "compute" in func_names
    assert "top_level_func" in func_names

    compute_fn = next(f for f in result.functions if f.name == "compute")
    assert compute_fn.parent_class == "MathHelper"
    assert compute_fn.full_name == "MathHelper.compute"
    assert compute_fn.docstring == "Compute square root."
    assert compute_fn.line_start == 7
    assert "def compute" in compute_fn.source_code

    assert len(result.imports) == 2
    imp_math = next(i for i in result.imports if i.module == "math")
    assert imp_math.is_from is True
    assert "sqrt" in imp_math.names


def test_parse_malformed_python_file_does_not_crash(tmp_path):
    malformed_code = """
def broken_syntax(x, y
    print('missing closing parenthesis')
"""
    file_path = tmp_path / "broken.py"
    file_path.write_text(malformed_code, encoding="utf-8")

    result = parse_python_file(file_path, tmp_path)

    assert result.error is not None
    assert "SyntaxError" in result.error
    assert len(result.functions) == 0
    assert len(result.classes) == 0


def test_parse_sample_project():
    sample_dir = Path(__file__).parent.parent / "sample_project"
    files = list(sample_dir.glob("*.py"))
    results = parse_repository(sample_dir, files)

    assert len(results) >= 5
    for r in results:
        assert r.error is None
        assert r.line_count > 0
