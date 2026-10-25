

from __future__ import annotations
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple, Any
import networkx as nx
import matplotlib.pyplot as plt

from parser import ParsedFile, ImportInfo


def normalize_rel_path(path_str: str) -> str:
    return path_str.replace("\\", "/").lstrip("./")


def build_module_lookup(parsed_files: List[ParsedFile]) -> Dict[str, str]:
    lookup: Dict[str, str] = {}
    stem_counts: Dict[str, List[str]] = {}

    for pf in parsed_files:
        norm_path = normalize_rel_path(pf.file_path)
        path_obj = Path(norm_path)

        parts = list(path_obj.parts)
        if parts:
            if parts[-1].endswith(".py"):
                parts[-1] = parts[-1][:-3]
            if parts[-1] == "__init__":
                pkg_dotted = ".".join(parts[:-1])
                if pkg_dotted:
                    lookup[pkg_dotted] = norm_path
            dotted = ".".join(parts)
            lookup[dotted] = norm_path

        stem = path_obj.stem
        if stem != "__init__":
            stem_counts.setdefault(stem, []).append(norm_path)

    for stem, paths in stem_counts.items():
        if len(paths) == 1 and stem not in lookup:
            lookup[stem] = paths[0]

    return lookup


def resolve_relative_import(
    current_file_path: str,
    module: Optional[str],
    level: int,
    module_lookup: Dict[str, str]
) -> Optional[str]:
    current_parts = list(Path(normalize_rel_path(current_file_path)).parent.parts)

    up_steps = level - 1
    if up_steps > len(current_parts):
        return None

    base_parts = current_parts[: len(current_parts) - up_steps] if up_steps > 0 else current_parts

    target_tokens = list(base_parts)
    if module:
        target_tokens.extend(module.split("."))

    candidate_dotted = ".".join(target_tokens)
    if candidate_dotted in module_lookup:
        return module_lookup[candidate_dotted]

    candidate_path = "/".join(target_tokens) + ".py"
    for path in module_lookup.values():
        if path == candidate_path:
            return path

    return None


def resolve_import(
    current_file_path: str,
    imp: ImportInfo,
    module_lookup: Dict[str, str]
) -> List[str]:
    resolved_targets: Set[str] = set()

    if imp.level > 0:
        target = resolve_relative_import(
            current_file_path, imp.module, imp.level, module_lookup
        )
        if target:
            resolved_targets.add(target)
        else:
            for name in imp.names:
                sub_target = resolve_relative_import(
                    current_file_path, name, imp.level, module_lookup
                )
                if sub_target:
                    resolved_targets.add(sub_target)
        return list(resolved_targets)

    candidates: List[str] = []
    if imp.is_from and imp.module:
        candidates.append(imp.module)
        for name in imp.names:
            candidates.append(f"{imp.module}.{name}")
    else:
        for name in imp.names:
            candidates.append(name)

    for cand in candidates:
        if cand in module_lookup:
            resolved_targets.add(module_lookup[cand])
            continue

        tokens = cand.split(".")
        found = False
        for i in range(len(tokens), 0, -1):
            sub = ".".join(tokens[:i])
            if sub in module_lookup:
                resolved_targets.add(module_lookup[sub])
                found = True
                break

        if not found:
            for i in range(1, len(tokens)):
                sub = ".".join(tokens[i:])
                if sub in module_lookup:
                    resolved_targets.add(module_lookup[sub])
                    break

    return list(resolved_targets)


def build_dependency_graph(parsed_files: List[ParsedFile]) -> nx.DiGraph:
    graph = nx.DiGraph()
    module_lookup = build_module_lookup(parsed_files)

    for pf in parsed_files:
        norm = normalize_rel_path(pf.file_path)
        graph.add_node(
            norm,
            line_count=pf.line_count,
            functions_count=len(pf.functions),
            classes_count=len(pf.classes),
            has_error=bool(pf.error),
        )

    for pf in parsed_files:
        source_path = normalize_rel_path(pf.file_path)
        for imp in pf.imports:
            targets = resolve_import(source_path, imp, module_lookup)
            for target in targets:
                if target != source_path and graph.has_node(target):
                    if graph.has_edge(source_path, target):
                        graph[source_path][target]["weight"] += 1
                    else:
                        graph.add_edge(source_path, target, weight=1)

    return graph


def get_graph_metrics(graph: nx.DiGraph) -> Dict[str, Any]:
    num_nodes = graph.number_of_nodes()
    num_edges = graph.number_of_edges()

    in_degrees = dict(graph.in_degree())
    out_degrees = dict(graph.out_degree())

    most_depended_on = sorted(in_degrees.items(), key=lambda x: x[1], reverse=True)
    most_dependencies = sorted(out_degrees.items(), key=lambda x: x[1], reverse=True)

    try:
        cycles = list(nx.simple_cycles(graph))
    except Exception:
        cycles = []

    isolated = [node for node in graph.nodes if in_degrees.get(node, 0) == 0 and out_degrees.get(node, 0) == 0]

    return {
        "num_nodes": num_nodes,
        "num_edges": num_edges,
        "most_depended_on": most_depended_on[:5],
        "most_dependencies": most_dependencies[:5],
        "cycles": cycles,
        "cycle_count": len(cycles),
        "isolated_files": isolated,
    }


def render_graph_figure(
    graph: nx.DiGraph, figsize: Tuple[int, int] = (11, 7), is_dark: bool = False
) -> plt.Figure:
    bg_color = "#18191c" if is_dark else "#fbfbfa"
    text_color = "#e6e6e8" if is_dark else "#1a1a1c"
    edge_color = "#64748b" if is_dark else "#94a3b8"
    legend_bg = "#202124" if is_dark else "#ffffff"
    legend_border = "#2e3035" if is_dark else "#e5e5e2"
    border_color = "#202124" if is_dark else "#ffffff"

    fig, ax = plt.subplots(figsize=figsize, dpi=130)
    fig.patch.set_facecolor(bg_color)
    ax.set_facecolor(bg_color)

    if graph.number_of_nodes() == 0:
        ax.text(
            0.5, 0.5, "No internal files discovered to graph",
            ha="center", va="center", fontsize=12, color="#71717a"
        )
        ax.axis("off")
        return fig

    if graph.number_of_nodes() <= 2:
        pos = nx.spring_layout(graph, seed=42)
    else:
        try:
            pos = nx.kamada_kawai_layout(graph)
        except Exception:
            pos = nx.spring_layout(graph, k=1.3, seed=42)

    try:
        cycle_nodes = set().union(*nx.simple_cycles(graph))
    except Exception:
        cycle_nodes = set()

    node_colors = []
    for node in graph.nodes:
        if node in cycle_nodes:
            node_colors.append("#ef4444")
        elif graph.in_degree(node) >= 2:
            node_colors.append("#3b82f6" if is_dark else "#0969da")
        elif graph.out_degree(node) >= 2:
            node_colors.append("#a855f7" if is_dark else "#7c3aed")
        else:
            node_colors.append("#10b981" if is_dark else "#059669")

    nx.draw_networkx_nodes(
        graph,
        pos,
        ax=ax,
        node_color=node_colors,
        node_size=1500,
        alpha=0.95,
        edgecolors=border_color,
        linewidths=2.0,
    )

    nx.draw_networkx_edges(
        graph,
        pos,
        ax=ax,
        arrowstyle="-|>",
        arrowsize=16,
        edge_color=edge_color,
        width=1.6,
        connectionstyle="arc3,rad=0.15",
        alpha=0.8,
    )

    labels = {}
    for node in graph.nodes:
        parts = Path(node).parts
        if len(parts) > 1:
            labels[node] = "/".join(parts[-2:])
        else:
            labels[node] = parts[0]

    nx.draw_networkx_labels(
        graph,
        pos,
        labels=labels,
        ax=ax,
        font_size=8.5,
        font_family="sans-serif",
        font_weight="bold",
        font_color="#ffffff",
    )

    import matplotlib.patches as mpatches
    core_color = "#3b82f6" if is_dark else "#0969da"
    cons_color = "#a855f7" if is_dark else "#7c3aed"
    std_color = "#10b981" if is_dark else "#059669"

    legend_handles = [
        mpatches.Patch(color=core_color, label="Core Utility (In-Degree ≥ 2)"),
        mpatches.Patch(color=cons_color, label="High Consumer (Out-Degree ≥ 2)"),
        mpatches.Patch(color=std_color, label="Standard Module"),
    ]
    if cycle_nodes:
        legend_handles.append(mpatches.Patch(color="#ef4444", label="Circular Import Cycle"))

    legend = ax.legend(
        handles=legend_handles,
        loc="upper right",
        frameon=True,
        facecolor=legend_bg,
        edgecolor=legend_border,
        fontsize=8,
    )
    for text in legend.get_texts():
        text.set_color(text_color)

    ax.set_title(
        f"Internal Import Hierarchy ({graph.number_of_nodes()} files, {graph.number_of_edges()} dependencies)",
        fontsize=12,
        pad=16,
        fontweight="bold",
        color=text_color,
    )
    ax.axis("off")
    fig.tight_layout()
    return fig

