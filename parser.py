

from __future__ import annotations
import ast
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional


@dataclass
class ImportInfo:
    module: Optional[str]
    names: List[str]
    level: int
    is_from: bool
    line_number: int


@dataclass
class FunctionEntity:
    name: str
    parent_class: Optional[str]
    file_path: str
    line_start: int
    line_end: int
    docstring: str
    source_code: str
    args: List[str] = field(default_factory=list)
    is_async: bool = False

    @property
    def full_name(self) -> str:
        if self.parent_class:
            return f"{self.parent_class}.{self.name}"
        return self.name

    @property
    def searchable_text(self) -> str:
        parts = [
            self.full_name,
            " ".join(self.args),
            self.docstring or "",
            self.source_code or "",
        ]
        return " \n".join(part for part in parts if part).strip()


@dataclass
class ClassInfo:
    name: str
    file_path: str
    line_start: int
    line_end: int
    docstring: str
    methods: List[str] = field(default_factory=list)
    bases: List[str] = field(default_factory=list)


@dataclass
class ParsedFile:
    file_path: str
    absolute_path: str
    line_count: int
    functions: List[FunctionEntity] = field(default_factory=list)
    classes: List[ClassInfo] = field(default_factory=list)
    imports: List[ImportInfo] = field(default_factory=list)
    error: Optional[str] = None


class CodeVisitor(ast.NodeVisitor):

    def __init__(self, rel_path: str, source_lines: List[str]):
        self.rel_path = rel_path
        self.source_lines = source_lines
        self.functions: List[FunctionEntity] = []
        self.classes: List[ClassInfo] = []
        self.imports: List[ImportInfo] = []
        self._current_class: Optional[str] = None

    def _extract_source_snippet(self, start_line: int, end_line: int) -> str:
        start_idx = max(0, start_line - 1)
        end_idx = min(len(self.source_lines), end_line)
        return "".join(self.source_lines[start_idx:end_idx]).strip()

    def _get_arg_names(self, node: ast.FunctionDef | ast.AsyncFunctionDef) -> List[str]:
        return [arg.arg for arg in node.args.args if arg.arg not in ("self", "cls")]

    def visit_Import(self, node: ast.Import) -> None:
        names = [alias.name for alias in node.names]
        self.imports.append(
            ImportInfo(
                module=None,
                names=names,
                level=0,
                is_from=False,
                line_number=node.lineno,
            )
        )
        self.generic_visit(node)

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        names = [alias.name for alias in node.names]
        self.imports.append(
            ImportInfo(
                module=node.module,
                names=names,
                level=node.level or 0,
                is_from=True,
                line_number=node.lineno,
            )
        )
        self.generic_visit(node)

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        start_line = node.lineno
        end_line = getattr(node, "end_lineno", node.lineno)
        docstring = ast.get_docstring(node) or ""
        bases = [ast.unparse(b) for b in node.bases] if hasattr(ast, "unparse") else []

        method_names: List[str] = []
        for item in node.body:
            if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                method_names.append(item.name)

        self.classes.append(
            ClassInfo(
                name=node.name,
                file_path=self.rel_path,
                line_start=start_line,
                line_end=end_line,
                docstring=docstring,
                methods=method_names,
                bases=bases,
            )
        )

        previous_class = self._current_class
        self._current_class = node.name
        self.generic_visit(node)
        self._current_class = previous_class

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        self._record_function(node, is_async=False)
        self.generic_visit(node)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        self._record_function(node, is_async=True)
        self.generic_visit(node)

    def _record_function(
        self, node: ast.FunctionDef | ast.AsyncFunctionDef, is_async: bool
    ) -> None:
        start_line = node.lineno
        end_line = getattr(node, "end_lineno", node.lineno)
        docstring = ast.get_docstring(node) or ""
        source_code = self._extract_source_snippet(start_line, end_line)
        arg_names = self._get_arg_names(node)

        self.functions.append(
            FunctionEntity(
                name=node.name,
                parent_class=self._current_class,
                file_path=self.rel_path,
                line_start=start_line,
                line_end=end_line,
                docstring=docstring,
                source_code=source_code,
                args=arg_names,
                is_async=is_async,
            )
        )


def parse_python_file(file_path: Path, repo_root: Path) -> ParsedFile:
    try:
        rel_path = str(file_path.resolve().relative_to(repo_root.resolve())).replace("\\", "/")
    except ValueError:
        rel_path = file_path.name

    abs_path = str(file_path.resolve())

    try:
        content = file_path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        try:
            content = file_path.read_text(encoding="latin-1")
        except Exception as exc:
            return ParsedFile(
                file_path=rel_path,
                absolute_path=abs_path,
                line_count=0,
                error=f"Encoding error: {exc}",
            )
    except Exception as exc:
        return ParsedFile(
            file_path=rel_path,
            absolute_path=abs_path,
            line_count=0,
            error=f"Read error: {exc}",
        )

    lines = content.splitlines(keepends=True)
    line_count = len(lines)

    try:
        tree = ast.parse(content, filename=str(file_path))
    except SyntaxError as syn_err:
        return ParsedFile(
            file_path=rel_path,
            absolute_path=abs_path,
            line_count=line_count,
            error=f"SyntaxError at line {syn_err.lineno}: {syn_err.msg}",
        )
    except Exception as exc:
        return ParsedFile(
            file_path=rel_path,
            absolute_path=abs_path,
            line_count=line_count,
            error=f"AST parse error: {exc}",
        )

    visitor = CodeVisitor(rel_path=rel_path, source_lines=lines)
    visitor.visit(tree)

    return ParsedFile(
        file_path=rel_path,
        absolute_path=abs_path,
        line_count=line_count,
        functions=visitor.functions,
        classes=visitor.classes,
        imports=visitor.imports,
        error=None,
    )


def parse_repository(repo_path: str | Path, python_files: List[Path]) -> List[ParsedFile]:
    root = Path(repo_path).resolve()
    parsed_results: List[ParsedFile] = []
    for f in python_files:
        parsed_results.append(parse_python_file(f, root))
    return parsed_results
