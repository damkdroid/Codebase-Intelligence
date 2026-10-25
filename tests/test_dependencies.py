"""Unit tests for NetworkX internal dependency graph."""

from pathlib import Path
from parser import ParsedFile, ImportInfo
from dependencies import build_dependency_graph, get_graph_metrics, build_module_lookup, resolve_import


def test_internal_dependency_graph_building():
    f1 = ParsedFile(
        file_path="sample_project/auth.py",
        absolute_path="/repo/sample_project/auth.py",
        line_count=50,
        imports=[
            ImportInfo(module="sample_project.config", names=["load_settings"], level=0, is_from=True, line_number=5),
            ImportInfo(module="sample_project.database", names=["DatabaseClient"], level=0, is_from=True, line_number=6),
            ImportInfo(module="hashlib", names=["sha256"], level=0, is_from=True, line_number=1),  # External!
        ],
    )
    f2 = ParsedFile(
        file_path="sample_project/config.py",
        absolute_path="/repo/sample_project/config.py",
        line_count=30,
        imports=[
            ImportInfo(module="os", names=[], level=0, is_from=False, line_number=1),
        ],
    )
    f3 = ParsedFile(
        file_path="sample_project/database.py",
        absolute_path="/repo/sample_project/database.py",
        line_count=40,
        imports=[
            ImportInfo(module="sample_project.config", names=["load_settings"], level=0, is_from=True, line_number=3),
        ],
    )

    graph = build_dependency_graph([f1, f2, f3])

    assert graph.number_of_nodes() == 3
    # auth -> config, auth -> database, database -> config => total 3 internal edges
    assert graph.number_of_edges() == 3
    assert graph.has_edge("sample_project/auth.py", "sample_project/config.py")
    assert graph.has_edge("sample_project/auth.py", "sample_project/database.py")
    assert graph.has_edge("sample_project/database.py", "sample_project/config.py")

    metrics = get_graph_metrics(graph)
    assert metrics["num_nodes"] == 3
    assert metrics["num_edges"] == 3
    assert metrics["cycle_count"] == 0
    # config is most depended on (in-degree 2)
    assert metrics["most_depended_on"][0][0] == "sample_project/config.py"
    assert metrics["most_depended_on"][0][1] == 2


def test_relative_import_resolution():
    f1 = ParsedFile(
        file_path="pkg/sub/child.py",
        absolute_path="/repo/pkg/sub/child.py",
        line_count=20,
        imports=[
            # from .sibling import foo -> pkg/sub/sibling.py
            ImportInfo(module="sibling", names=["foo"], level=1, is_from=True, line_number=2),
            # from ..parent_mod import bar -> pkg/parent_mod.py
            ImportInfo(module="parent_mod", names=["bar"], level=2, is_from=True, line_number=3),
        ],
    )
    f2 = ParsedFile(
        file_path="pkg/sub/sibling.py",
        absolute_path="/repo/pkg/sub/sibling.py",
        line_count=10,
        imports=[],
    )
    f3 = ParsedFile(
        file_path="pkg/parent_mod.py",
        absolute_path="/repo/pkg/parent_mod.py",
        line_count=10,
        imports=[],
    )

    graph = build_dependency_graph([f1, f2, f3])
    assert graph.has_edge("pkg/sub/child.py", "pkg/sub/sibling.py")
    assert graph.has_edge("pkg/sub/child.py", "pkg/parent_mod.py")
