

from __future__ import annotations
import json
import html
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


def render_interactive_graph_html(
    graph: nx.DiGraph, is_dark: bool = False, height_px: int = 540
) -> str:
    if graph.number_of_nodes() == 0:
        bg = "#12151c" if is_dark else "#ffffff"
        text_color = "#94a3b8"
        return f"""
        <div style="background:{bg};height:{height_px}px;display:flex;align-items:center;justify-content:center;color:{text_color};font-family:sans-serif;border-radius:10px;border:1px dashed #334155;">
            No internal dependencies to display.
        </div>
        """

    try:
        cycle_nodes = set().union(*nx.simple_cycles(graph))
    except Exception:
        cycle_nodes = set()

    nodes_data = []
    for node in graph.nodes:
        in_deg = graph.in_degree(node)
        out_deg = graph.out_degree(node)
        parts = Path(node).parts
        short_label = "/".join(parts[-2:]) if len(parts) > 1 else parts[0]

        if node in cycle_nodes:
            bg_col = "#ef4444"
            border_col = "#b91c1c"
        elif in_deg >= 2:
            bg_col = "#6366f1" if is_dark else "#4f46e5"
            border_col = "#818cf8" if is_dark else "#3730a3"
        elif out_deg >= 2:
            bg_col = "#a855f7" if is_dark else "#7c3aed"
            border_col = "#c084fc" if is_dark else "#5b21b6"
        else:
            bg_col = "#10b981" if is_dark else "#059669"
            border_col = "#34d399" if is_dark else "#047857"

        tooltip = (
            f"<b>{html.escape(node)}</b><br>"
            f"• In-degree (imported by): {in_deg}<br>"
            f"• Out-degree (imports): {out_deg}"
        )

        nodes_data.append({
            "id": node,
            "label": short_label,
            "title": tooltip,
            "shape": "box",
            "margin": 10,
            "color": {
                "background": bg_col,
                "border": border_col,
                "highlight": {
                    "background": bg_col,
                    "border": "#ffffff" if is_dark else "#0f172a"
                }
            },
            "font": {
                "color": "#ffffff",
                "face": "JetBrains Mono, Consolas, monospace",
                "size": 12,
                "bold": True
            },
            "shadow": {"enabled": True, "color": "rgba(0,0,0,0.25)", "size": 6}
        })

    edges_data = []
    edge_color = "#64748b" if is_dark else "#94a3b8"
    edge_highlight = "#38bdf8" if is_dark else "#0284c7"
    for u, v, data in graph.edges(data=True):
        weight = data.get("weight", 1)
        edges_data.append({
            "from": u,
            "to": v,
            "arrows": "to",
            "color": {"color": edge_color, "highlight": edge_highlight},
            "width": 1.5 + min(weight * 0.5, 3),
            "smooth": {"type": "curvedCW", "roundness": 0.15}
        })

    container_bg = "#0d1117" if is_dark else "#f8fafc"
    card_border = "#21262d" if is_dark else "#e2e8f0"
    text_color = "#e6edf3" if is_dark else "#0f172a"
    sub_color = "#8b949e" if is_dark else "#64748b"
    legend_bg = "rgba(22, 27, 34, 0.88)" if is_dark else "rgba(255, 255, 255, 0.92)"

    nodes_json = json.dumps(nodes_data)
    edges_json = json.dumps(edges_data)

    cycle_legend_item = "<div class='legend-item'><span class='legend-dot' style='background:#ef4444;'></span> Circular Cycle</div>" if cycle_nodes else ""

    return f"""
    <!DOCTYPE html>
    <html>
    <head>
      <meta charset="utf-8" />
      <script type="text/javascript" src="https://unpkg.com/vis-network@9.1.9/standalone/umd/vis-network.min.js"></script>
      <style>
        * {{ box-sizing: border-box; }}
        body {{
          margin: 0;
          padding: 0;
          background: {container_bg};
          overflow: hidden;
          font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
        }}
        #mynetwork {{
          width: 100%;
          height: {height_px}px;
          border-radius: 10px;
          border: 1px solid {card_border};
          background: {container_bg};
        }}
        .graph-controls {{
          position: absolute;
          top: 12px;
          left: 14px;
          background: {legend_bg};
          backdrop-filter: blur(8px);
          -webkit-backdrop-filter: blur(8px);
          border: 1px solid {card_border};
          border-radius: 6px;
          padding: 6px 12px;
          font-size: 11.5px;
          color: {sub_color};
          pointer-events: none;
          z-index: 10;
        }}
        .graph-legend {{
          position: absolute;
          bottom: 12px;
          right: 14px;
          background: {legend_bg};
          backdrop-filter: blur(8px);
          -webkit-backdrop-filter: blur(8px);
          border: 1px solid {card_border};
          border-radius: 8px;
          padding: 10px 14px;
          font-size: 11px;
          color: {text_color};
          display: flex;
          flex-direction: column;
          gap: 6px;
          z-index: 10;
        }}
        .legend-item {{
          display: flex;
          align-items: center;
          gap: 8px;
        }}
        .legend-dot {{
          width: 10px;
          height: 10px;
          border-radius: 3px;
          flex-shrink: 0;
        }}
      </style>
    </head>
    <body>
      <div class="graph-controls">
        <b>Interactive Physics Graph:</b> Scroll to zoom • Drag to pan • Drag nodes to explore
      </div>
      <div id="mynetwork"></div>
      <div class="graph-legend">
        <div class="legend-item"><span class="legend-dot" style="background:{"#6366f1" if is_dark else "#4f46e5"};"></span> Core Utility (In-Degree ≥ 2)</div>
        <div class="legend-item"><span class="legend-dot" style="background:{"#a855f7" if is_dark else "#7c3aed"};"></span> High Consumer (Out-Degree ≥ 2)</div>
        <div class="legend-item"><span class="legend-dot" style="background:{"#10b981" if is_dark else "#059669"};"></span> Standard Module</div>
        {cycle_legend_item}
      </div>
      <script type="text/javascript">
        var container = document.getElementById('mynetwork');
        var data = {{
          nodes: new vis.DataSet({nodes_json}),
          edges: new vis.DataSet({edges_json})
        }};
        var options = {{
          physics: {{
            solver: 'forceAtlas2Based',
            forceAtlas2Based: {{
              gravitationalConstant: -60,
              centralGravity: 0.015,
              springLength: 110,
              springConstant: 0.08,
              damping: 0.4
            }},
            stabilization: {{ iterations: 120 }}
          }},
          interaction: {{
            hover: true,
            tooltipDelay: 100,
            navigationButtons: false,
            keyboard: false
          }}
        }};
        var network = new vis.Network(container, data, options);
      </script>
    </body>
    </html>
    """


