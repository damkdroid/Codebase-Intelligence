

from __future__ import annotations
import os
from pathlib import Path
from typing import List, Dict, Any, Optional

import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

from scanner import scan_python_files, DEFAULT_EXCLUDED_DIRS
from parser import parse_repository, ParsedFile, FunctionEntity, ClassInfo
from search import CodeSearchEngine
from classifier import CodeClassifier, CATEGORIES
from clustering import CodeClusterer
from dependencies import build_dependency_graph, get_graph_metrics, render_graph_figure
from ui_theme import get_theme_css, render_code_block, render_category_tag

# Page configuration
st.set_page_config(
    page_title="Codebase Intelligence",
    layout="wide",
    initial_sidebar_state="expanded",
)


def display_html(html_str: str):
    """Safely render HTML, preferring native st.html for clean DOM output."""
    if hasattr(st, "html"):
        st.html(html_str)
    else:
        st.markdown(html_str, unsafe_allow_html=True)


@st.cache_resource(show_spinner=False)
def get_classifier() -> CodeClassifier:
    """Cache the trained classifier across application reruns."""
    return CodeClassifier()


def init_session_state():
    """Initialize session state and query parameter theme persistence."""
    # Theme persistence via query parameters or default to dark
    url_theme = st.query_params.get("theme", None)
    if "theme" not in st.session_state:
        st.session_state.theme = url_theme if url_theme in ("light", "dark") else "dark"
    elif url_theme in ("light", "dark") and url_theme != st.session_state.theme:
        st.session_state.theme = url_theme

    if "scanned" not in st.session_state:
        st.session_state.scanned = False
    if "repo_path" not in st.session_state:
        st.session_state.repo_path = ""
    if "parsed_files" not in st.session_state:
        st.session_state.parsed_files = []
    if "functions" not in st.session_state:
        st.session_state.functions = []
    if "classes" not in st.session_state:
        st.session_state.classes = []
    if "search_engine" not in st.session_state:
        st.session_state.search_engine = CodeSearchEngine()
    if "classified_df" not in st.session_state:
        st.session_state.classified_df = None
    if "dep_graph" not in st.session_state:
        st.session_state.dep_graph = None
    if "graph_metrics" not in st.session_state:
        st.session_state.graph_metrics = None
    if "search_query_preset" not in st.session_state:
        st.session_state.search_query_preset = ""


def run_scan(target_dir: str):
    """Scan and parse the repository, populating session state."""
    path_obj = Path(target_dir).resolve()
    if not path_obj.exists():
        st.sidebar.error(f"Path not found: {path_obj}")
        return
    if not path_obj.is_dir():
        st.sidebar.error(f"Path is not a directory: {path_obj}")
        return

    with st.spinner("Analyzing codebase and extracting AST index..."):
        try:
            discovered_files = scan_python_files(path_obj)
        except Exception as exc:
            st.sidebar.error(f"Scanner error: {exc}")
            return

        if not discovered_files:
            st.sidebar.warning("No Python files discovered in the selected directory.")
            return

        parsed_files = parse_repository(path_obj, discovered_files)

        all_functions: List[FunctionEntity] = []
        all_classes: List[ClassInfo] = []
        for pf in parsed_files:
            all_functions.extend(pf.functions)
            all_classes.extend(pf.classes)

        # Index search engine
        search_engine = CodeSearchEngine()
        search_engine.index(all_functions)

        # Build dependency graph
        dep_graph = build_dependency_graph(parsed_files)
        graph_metrics = get_graph_metrics(dep_graph)

        # Precompute classifications
        classifier = get_classifier()
        classification_rows = []
        for fn in all_functions:
            res = classifier.predict(fn.searchable_text)
            classification_rows.append({
                "Function": fn.full_name,
                "File": fn.file_path,
                "Lines": f"{fn.line_start}–{fn.line_end}",
                "Category": res.category,
                "Confidence": res.confidence,
                "Entity": fn,
                "Probabilities": res.probabilities,
            })
        classified_df = pd.DataFrame(classification_rows) if classification_rows else pd.DataFrame()

        # Update session state
        st.session_state.scanned = True
        st.session_state.repo_path = str(path_obj)
        st.session_state.parsed_files = parsed_files
        st.session_state.functions = all_functions
        st.session_state.classes = all_classes
        st.session_state.search_engine = search_engine
        st.session_state.classified_df = classified_df
        st.session_state.dep_graph = dep_graph
        st.session_state.graph_metrics = graph_metrics

    st.sidebar.success(f"Indexed {len(discovered_files)} files ({len(all_functions)} functions)")


def main():
    init_session_state()

    # Apply centralized theme CSS
    active_theme = st.session_state.theme
    is_dark = (active_theme == "dark")
    st.markdown(get_theme_css(active_theme), unsafe_allow_html=True)

    # -------------------------------------------------------------------------
    # SIDEBAR: CONTROLS & THEME TOGGLE
    # -------------------------------------------------------------------------
    st.sidebar.markdown("""
        <div style="padding-bottom: 10px; margin-bottom: 12px; border-bottom: 1px solid var(--ui-border-subtle);">
            <div style="font-size: 15px; font-weight: 700; letter-spacing: -0.01em; color: var(--ui-text-primary);">
                Codebase Intelligence
            </div>
            <div style="font-size: 11px; color: var(--ui-text-muted); margin-top: 2px;">
                Static AST & Semantic Code Search
            </div>
        </div>
    """, unsafe_allow_html=True)

    # Theme Toggle
    theme_col1, theme_col2 = st.sidebar.columns([1, 1])
    with theme_col1:
        st.caption("INTERFACE THEME")
    with theme_col2:
        new_theme = st.selectbox(
            "Theme",
            options=["dark", "light"],
            index=0 if is_dark else 1,
            label_visibility="collapsed",
            key="theme_selector",
        )
        if new_theme != active_theme:
            st.session_state.theme = new_theme
            st.query_params["theme"] = new_theme
            st.rerun()

    st.sidebar.markdown("<div style='margin-top: 10px;'></div>", unsafe_allow_html=True)

    default_sample = str((Path(__file__).parent / "sample_project").resolve())

    repo_input = st.sidebar.text_input(
        "Repository Directory",
        value=st.session_state.repo_path or default_sample,
        help="Local directory path containing the Python codebase to analyze.",
    )

    btn_col1, btn_col2 = st.sidebar.columns([1, 1])
    with btn_col1:
        if st.button("Scan Repository", type="primary", use_container_width=True):
            run_scan(repo_input)
    with btn_col2:
        if st.button("Load Sample", use_container_width=True):
            run_scan(default_sample)

    if st.session_state.scanned:
        repo_name = Path(st.session_state.repo_path).name or "Repository"
        st.sidebar.markdown(f"""
            <div style="margin-top: 12px; padding: 6px 10px; border-radius: 4px; background-color: var(--ui-bg-elevated); border: 1px solid var(--ui-border-subtle);">
                <span style="font-size: 11px; font-weight: 600; text-transform: uppercase; color: var(--ui-text-muted);">Loaded:</span>
                <span style="font-family: 'JetBrains Mono', Consolas, monospace; font-size: 11.5px; font-weight: 600; color: var(--ui-text-primary); margin-left: 4px;">{repo_name}</span>
            </div>
        """, unsafe_allow_html=True)

    with st.sidebar.expander("Excluded Directories", expanded=False):
        st.caption("Directories bypassed during scanning:")
        st.code("\n".join(sorted(DEFAULT_EXCLUDED_DIRS)), language="text")

    st.sidebar.markdown("<div style='margin-top: 20px;'></div>", unsafe_allow_html=True)
    st.sidebar.caption("Static analysis only. Analyzed repository code is never executed.")

    # -------------------------------------------------------------------------
    # MAIN HEADER
    # -------------------------------------------------------------------------
    repo_tag = Path(st.session_state.repo_path).name if st.session_state.scanned else "No repository loaded"
    display_html(f"""
        <div class="app-header-bar">
            <div class="app-header-left">
                <span class="app-brand-title">Codebase Intelligence</span>
                <span class="app-repo-badge">{repo_tag}</span>
            </div>
            <div class="app-header-right">
                AST Parsing · TF-IDF Search · ML Classification · Dependency Graph
            </div>
        </div>
    """)

    # Empty State when no repository is scanned yet
    if not st.session_state.scanned:
        st.markdown("""
            <div class="ui-panel" style="padding: 24px;">
                <h3 style="margin-top: 0;">Getting Started</h3>
                <p style="margin-bottom: 16px;">
                    Select or enter a Python repository path in the sidebar and click <b>Scan Repository</b> to build the structural AST index.
                </p>
                <div class="metric-grid">
                    <div class="ui-metric-tile">
                        <div class="ui-metric-label">Structural Parser</div>
                        <div style="font-size: 13px; color: var(--ui-text-secondary); margin-top: 4px;">
                            Extracts functions, classes, docstrings, and imports safely using Python <code>ast</code> without code execution.
                        </div>
                    </div>
                    <div class="ui-metric-tile">
                        <div class="ui-metric-label">Semantic Code Search</div>
                        <div style="font-size: 13px; color: var(--ui-text-secondary); margin-top: 4px;">
                            Ranked cosine similarity search across docstrings, signatures, and syntax using TF-IDF n-grams.
                        </div>
                    </div>
                    <div class="ui-metric-tile">
                        <div class="ui-metric-label">Architectural Classifier</div>
                        <div style="font-size: 13px; color: var(--ui-text-secondary); margin-top: 4px;">
                            Identifies Authentication, Database, API, Logic, Utilities, and Testing roles with probability scores.
                        </div>
                    </div>
                    <div class="ui-metric-tile">
                        <div class="ui-metric-label">Dependency Hierarchy</div>
                        <div style="font-size: 13px; color: var(--ui-text-secondary); margin-top: 4px;">
                            Directed graph resolution of internal relative and absolute imports with cycle detection.
                        </div>
                    </div>
                </div>
            </div>
        """, unsafe_allow_html=True)
        return

    # -------------------------------------------------------------------------
    # MAIN NAVIGATION TABS (No emojis)
    # -------------------------------------------------------------------------
    tab_overview, tab_search, tab_classify, tab_cluster, tab_deps = st.tabs([
        "Overview",
        "Code Search",
        "Classification",
        "Clustering",
        "Dependency Graph",
    ])

    # =========================================================================
    # TAB 1: OVERVIEW
    # =========================================================================
    with tab_overview:
        parsed_files: List[ParsedFile] = st.session_state.parsed_files
        functions: List[FunctionEntity] = st.session_state.functions
        classes: List[ClassInfo] = st.session_state.classes
        total_lines = sum(pf.line_count for pf in parsed_files)
        error_files = [pf for pf in parsed_files if pf.error]

        # Top Metric Tiles
        st.markdown(f"""
            <div class="metric-grid">
                <div class="ui-metric-tile">
                    <div class="ui-metric-label">Python Files</div>
                    <div class="ui-metric-value">{len(parsed_files)}</div>
                </div>
                <div class="ui-metric-tile">
                    <div class="ui-metric-label">Total Lines of Code</div>
                    <div class="ui-metric-value">{total_lines:,}</div>
                </div>
                <div class="ui-metric-tile">
                    <div class="ui-metric-label">Functions & Methods</div>
                    <div class="ui-metric-value">{len(functions)}</div>
                </div>
                <div class="ui-metric-tile">
                    <div class="ui-metric-label">Classes Defined</div>
                    <div class="ui-metric-value">{len(classes)}</div>
                </div>
                <div class="ui-metric-tile" style="border-left: 3px solid {'#ef4444' if error_files else 'var(--ui-border-subtle)'};">
                    <div class="ui-metric-label">Syntax Errors</div>
                    <div class="ui-metric-value" style="color: {'#ef4444' if error_files else 'var(--ui-text-primary)'};">{len(error_files)}</div>
                </div>
            </div>
        """, unsafe_allow_html=True)

        if error_files:
            st.markdown("""
                <div style="padding: 10px 14px; background-color: var(--ui-bg-elevated); border-left: 3px solid #ef4444; border-radius: 4px; margin-bottom: 16px;">
                    <span style="font-weight: 600; font-size: 13px;">Syntax / Parsing Exceptions Encountered:</span>
                </div>
            """, unsafe_allow_html=True)
            for ef in error_files:
                st.code(f"{ef.file_path}: {ef.error}")

        st.subheader("Discovered Python Files")
        file_summary = []
        for pf in parsed_files:
            file_summary.append({
                "File Path": pf.file_path,
                "Lines": pf.line_count,
                "Functions": len(pf.functions),
                "Classes": len(pf.classes),
                "Imports": len(pf.imports),
                "Status": "Error" if pf.error else "Parsed",
            })
        st.dataframe(pd.DataFrame(file_summary), use_container_width=True, hide_index=True)

    # =========================================================================
    # TAB 2: CODE SEARCH
    # =========================================================================
    with tab_search:
        st.subheader("Natural-Language Code Search")
        st.caption(
            "Vector search over function names, parameter signatures, docstrings, and source code using TF-IDF and Cosine Similarity."
        )

        # Quick query presets (Clean buttons without emojis)
        st.markdown("<small style='color: var(--ui-text-muted); font-weight: 600;'>QUICK SEARCH PRESETS:</small>", unsafe_allow_html=True)
        q1, q2, q3, q4 = st.columns(4)
        preset_query = None
        with q1:
            if st.button("Password verification", use_container_width=True):
                preset_query = "verify user password and salt"
        with q2:
            if st.button("Database query execution", use_container_width=True):
                preset_query = "execute sql query and fetch records"
        with q3:
            if st.button("Cart discount calculation", use_container_width=True):
                preset_query = "calculate cart discount code total"
        with q4:
            if st.button("Authentication token", use_container_width=True):
                preset_query = "generate jwt token signature"

        active_query = preset_query if preset_query else st.session_state.search_query_preset

        s_col1, s_col2, s_col3 = st.columns([3, 1, 1])
        with s_col1:
            query = st.text_input(
                "Search Query",
                value=active_query,
                placeholder="e.g., verify password hash, calculate sales tax, execute query...",
                label_visibility="collapsed",
            )
        with s_col2:
            top_k = st.slider("Max Results", min_value=1, max_value=20, value=5)
        with s_col3:
            min_score = st.slider("Min Relevance", min_value=0.0, max_value=1.0, value=0.05, step=0.05)

        if query:
            engine: CodeSearchEngine = st.session_state.search_engine
            results = engine.search(query, top_k=top_k, min_score=min_score)

            if not results:
                st.markdown("""
                    <div class="ui-panel" style="padding: 18px; text-align: center; color: var(--ui-text-muted);">
                        No code matches found meeting the minimum relevance threshold.
                    </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown(f"<div style='font-size: 13px; color: var(--ui-text-muted); margin-bottom: 12px;'>Showing <b>{len(results)}</b> ranked match(es):</div>", unsafe_allow_html=True)

                for r in results:
                    score_pct = int(r.score * 100)

                    # Result Card
                    header_title = f"#{r.rank} · {r.full_name}() — {score_pct}% relevance"
                    with st.expander(header_title, expanded=(r.rank == 1)):
                        meta_col1, meta_col2 = st.columns(2)
                        with meta_col1:
                            st.markdown(f"<span style='font-size: 12px; color: var(--ui-text-muted);'>File:</span> <code style='font-size: 12px;'>{r.file_path}</code>", unsafe_allow_html=True)
                        with meta_col2:
                            st.markdown(f"<span style='font-size: 12px; color: var(--ui-text-muted);'>Lines:</span> <code style='font-size: 12px;'>{r.line_start}–{r.line_end}</code>", unsafe_allow_html=True)

                        if r.docstring:
                            st.markdown(f"""
                                <div style="margin: 8px 0; padding: 6px 10px; background-color: var(--ui-bg-elevated); border-left: 2px solid var(--ui-border-strong); font-size: 12.5px; font-style: italic; color: var(--ui-text-secondary);">
                                    {r.docstring}
                                </div>
                            """, unsafe_allow_html=True)

                        # Obsidian-inspired code snippet with Pygments syntax highlighting
                        code_html = render_code_block(
                            source_code=r.source_code,
                            file_path=r.file_path,
                            line_start=r.line_start,
                            line_end=r.line_end,
                            query=query,
                            is_dark=is_dark,
                        )
                        display_html(code_html)

    # =========================================================================
    # TAB 3: CLASSIFICATION
    # =========================================================================
    with tab_classify:
        st.subheader("Architectural Code Classification")
        st.caption(
            "Multiclass Logistic Regression model with TF-IDF features predicting the architectural role of discovered functions."
        )

        classifier = get_classifier()
        info = classifier.get_dataset_info()

        df: pd.DataFrame = st.session_state.classified_df
        if df is not None and not df.empty:
            cat_counts = df["Category"].value_counts()

            c_chart, c_filter = st.columns([1, 1])
            with c_chart:
                st.markdown("#### Category Distribution")
                st.bar_chart(cat_counts, color="#0969da" if not is_dark else "#3b82f6")

            with c_filter:
                st.markdown("#### Filter Entities")
                f_cat = st.selectbox("Role Filter", ["All Categories"] + CATEGORIES)
                conf_min = st.slider("Minimum Confidence", 0.0, 1.0, 0.0, step=0.05)

                filtered_df = df[df["Confidence"] >= conf_min]
                if f_cat != "All Categories":
                    filtered_df = filtered_df[filtered_df["Category"] == f_cat]

                st.markdown(f"<div style='font-size: 13px; color: var(--ui-text-muted);'>Showing <b>{len(filtered_df)}</b> of {len(df)} functions:</div>", unsafe_allow_html=True)

            st.markdown("<div style='margin-top: 14px;'></div>", unsafe_allow_html=True)

            # Function cards with restrained category tags
            for _, row in filtered_df.iterrows():
                entity: FunctionEntity = row["Entity"]
                conf_pct = int(row["Confidence"] * 100)
                category = row["Category"]

                with st.expander(f"{row['Function']}() · {category} ({conf_pct}% confidence)"):
                    badge_html = render_category_tag(category, row["Confidence"], is_dark=is_dark)
                    st.markdown(f"""
                        <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 8px;">
                            {badge_html}
                            <span style="font-size: 12px; color: var(--ui-text-muted);">
                                Defined in <code>{row['File']}</code> (lines {row['Lines']})
                            </span>
                        </div>
                    """, unsafe_allow_html=True)

                    st.markdown("<div style='font-size: 11px; font-weight: 600; text-transform: uppercase; color: var(--ui-text-muted); margin-bottom: 4px;'>Class Probabilities:</div>", unsafe_allow_html=True)
                    prob_cols = st.columns(len(CATEGORIES))
                    for col, (c_name, c_prob) in zip(prob_cols, row["Probabilities"].items()):
                        c_short = c_name.split()[0]
                        col.metric(c_short, f"{int(c_prob * 100)}%")

                    # Pygments syntax highlighted source snippet
                    code_html = render_code_block(
                        source_code=entity.source_code,
                        file_path=row["File"],
                        line_start=entity.line_start,
                        line_end=entity.line_end,
                        is_dark=is_dark,
                    )
                    display_html(code_html)

            st.markdown("<div style='margin-top: 12px;'></div>", unsafe_allow_html=True)
            st.caption(f"Note: {info['disclaimer']}")
        else:
            st.info("No functions available to classify.")

    # =========================================================================
    # TAB 4: CLUSTERING
    # =========================================================================
    with tab_cluster:
        st.subheader("Topic Discovery & Code Clustering")
        st.caption(
            "Unsupervised K-Means clustering in the TF-IDF feature space identifying functional subsystems without manual tags."
        )

        functions: List[FunctionEntity] = st.session_state.functions
        if functions:
            max_k_possible = min(15, max(2, len(functions)))
            k_val = st.slider(
                "Number of Clusters (k)",
                min_value=1,
                max_value=max_k_possible,
                value=min(4, max_k_possible),
            )

            clusterer = CodeClusterer()
            outcome = clusterer.cluster(functions, n_clusters=k_val)

            if outcome.note:
                st.caption(outcome.note)

            st.markdown(f"<div style='font-size: 13px; color: var(--ui-text-muted); margin-bottom: 12px;'>Discovered <b>{outcome.effective_k}</b> cluster(s) across {len(functions)} functions:</div>", unsafe_allow_html=True)

            for group in outcome.groups:
                terms_str = ", ".join(group.representative_terms[:4]) if group.representative_terms else "general"
                with st.expander(f"Cluster {group.cluster_id}: {group.size} function(s) — [{terms_str}]", expanded=True):
                    st.markdown("<div style='font-size: 11px; font-weight: 600; text-transform: uppercase; color: var(--ui-text-muted); margin-bottom: 4px;'>Representative Terms:</div>", unsafe_allow_html=True)
                    terms_badges = " ".join(
                        f"<span class='ui-tag' style='background: var(--ui-bg-elevated); border: 1px solid var(--ui-border-subtle); color: var(--ui-text-primary); margin-right: 4px;'>{term}</span>"
                        for term in group.representative_terms
                    )
                    st.markdown(terms_badges or "None", unsafe_allow_html=True)

                    st.markdown("<div style='font-size: 11px; font-weight: 600; text-transform: uppercase; color: var(--ui-text-muted); margin-top: 10px; margin-bottom: 4px;'>Assigned Functions:</div>", unsafe_allow_html=True)
                    for fn in group.entities:
                        with st.expander(f"{fn.full_name}() · {fn.file_path}:{fn.line_start}"):
                            code_html = render_code_block(
                                source_code=fn.source_code,
                                file_path=fn.file_path,
                                line_start=fn.line_start,
                                line_end=fn.line_end,
                                is_dark=is_dark,
                            )
                            display_html(code_html)
        else:
            st.info("No functions available to cluster.")

    # =========================================================================
    # TAB 5: DEPENDENCY GRAPH
    # =========================================================================
    with tab_deps:
        st.subheader("Internal Module Dependency Graph")
        st.caption(
            "Directed graph of internal file-level imports constructed using NetworkX. Analyzes architectural couplings and detects circular dependencies."
        )

        dep_graph = st.session_state.dep_graph
        metrics = st.session_state.graph_metrics

        if dep_graph is not None and metrics is not None:
            # Metric Tiles
            has_cycle = metrics["cycle_count"] > 0
            st.markdown(f"""
                <div class="metric-grid">
                    <div class="ui-metric-tile">
                        <div class="ui-metric-label">Internal Files (Nodes)</div>
                        <div class="ui-metric-value">{metrics['num_nodes']}</div>
                    </div>
                    <div class="ui-metric-tile">
                        <div class="ui-metric-label">Import Edges</div>
                        <div class="ui-metric-value">{metrics['num_edges']}</div>
                    </div>
                    <div class="ui-metric-tile" style="border-left: 3px solid {'#ef4444' if has_cycle else 'var(--ui-border-subtle)'};">
                        <div class="ui-metric-label">Circular Cycles</div>
                        <div class="ui-metric-value" style="color: {'#ef4444' if has_cycle else 'var(--ui-text-primary)'};">{metrics['cycle_count']}</div>
                    </div>
                    <div class="ui-metric-tile">
                        <div class="ui-metric-label">Isolated Files</div>
                        <div class="ui-metric-value">{len(metrics['isolated_files'])}</div>
                    </div>
                </div>
            """, unsafe_allow_html=True)

            if metrics["cycles"]:
                st.error(f"Circular import cycle detected: {metrics['cycles']}")

            # Theme-aware Matplotlib network rendering
            fig = render_graph_figure(dep_graph, is_dark=is_dark)
            st.pyplot(fig)
            plt.close(fig)

            st.markdown("### Coupling Metrics Breakdown")
            c_dep1, c_dep2 = st.columns(2)
            with c_dep1:
                st.markdown("#### In-Degree (Most Depended-Upon Files)")
                st.caption("Core foundational utilities that other modules import.")
                in_data = [
                    {"File": f, "Imported By (Count)": count}
                    for f, count in metrics["most_depended_on"]
                ]
                st.dataframe(pd.DataFrame(in_data), use_container_width=True, hide_index=True)

            with c_dep2:
                st.markdown("#### Out-Degree (High Consumer Files)")
                st.caption("Orchestrator modules that import multiple submodules.")
                out_data = [
                    {"File": f, "Imports (Count)": count}
                    for f, count in metrics["most_dependencies"]
                ]
                st.dataframe(pd.DataFrame(out_data), use_container_width=True, hide_index=True)

            with st.expander("Internal Edge Dependency List"):
                edge_rows = []
                for u, v, data in dep_graph.edges(data=True):
                    edge_rows.append({
                        "Source (Importer)": u,
                        "Target (Imported)": v,
                        "Weight": data.get("weight", 1),
                    })
                st.dataframe(pd.DataFrame(edge_rows), use_container_width=True, hide_index=True)


if __name__ == "__main__":
    main()
