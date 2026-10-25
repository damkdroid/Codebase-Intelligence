# app.py

from __future__ import annotations
import os
from pathlib import Path
from typing import List, Dict, Any, Optional

import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import matplotlib.pyplot as plt

from scanner import scan_python_files, DEFAULT_EXCLUDED_DIRS
from parser import parse_repository, ParsedFile, FunctionEntity, ClassInfo
from search import CodeSearchEngine
from classifier import CodeClassifier, CATEGORIES
from clustering import CodeClusterer
import importlib
import dependencies
importlib.reload(dependencies)
from dependencies import (
    build_dependency_graph,
    get_graph_metrics,
    render_graph_figure,
    render_interactive_graph_html,
)

import ui_theme
importlib.reload(ui_theme)
from ui_theme import (
    get_theme_css,
    render_code_block,
    render_category_tag,
    render_probability_bars,
    get_svg_icon,
)

st.set_page_config(
    page_title="Codebase Intelligence",
    page_icon="◈",
    layout="wide",
    initial_sidebar_state="expanded",
)


def display_html(html_str: str):
    st.markdown(html_str, unsafe_allow_html=True)


@st.cache_resource(show_spinner=False)
def get_classifier() -> CodeClassifier:
    return CodeClassifier()


def init_session_state():
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
    path_obj = Path(target_dir).resolve()
    if not path_obj.exists():
        st.sidebar.error(f"Path not found: {path_obj}")
        return
    if not path_obj.is_dir():
        st.sidebar.error(f"Path is not a directory: {path_obj}")
        return

    with st.spinner("Analyzing repository AST & generating feature index..."):
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

        search_engine = CodeSearchEngine()
        search_engine.index(all_functions)

        dep_graph = build_dependency_graph(parsed_files)
        graph_metrics = get_graph_metrics(dep_graph)

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

    active_theme = st.session_state.theme
    is_dark = (active_theme == "dark")
    st.markdown(get_theme_css(active_theme), unsafe_allow_html=True)

    # Sidebar Header
    st.sidebar.markdown(f"""
        <div style="padding-bottom: 12px; margin-bottom: 14px; border-bottom: 1px solid var(--ui-border-subtle);">
            <div style="display: flex; align-items: center; gap: 9px;">
                <span class="app-logo-badge">
                    {get_svg_icon("logo", size=16, color="#ffffff")}
                </span>
                <span style="font-size: 16px; font-weight: 800; letter-spacing: -0.02em; color: var(--ui-text-primary);">
                    Codebase Intelligence
                </span>
            </div>
            <div style="font-size: 11.5px; color: var(--ui-text-muted); margin-top: 5px;">
                Static AST Analysis & Semantic Intelligence
            </div>
        </div>
    """, unsafe_allow_html=True)

    # Sleek Segmented Theme Switcher
    st.sidebar.caption("INTERFACE THEME")
    theme_options = ["Dark Mode", "Light Mode"]
    current_theme_idx = 0 if is_dark else 1
    selected_theme_label = st.sidebar.radio(
        "Theme",
        options=theme_options,
        index=current_theme_idx,
        horizontal=True,
        label_visibility="collapsed",
        key="theme_radio",
    )
    desired_theme = "dark" if "Dark" in selected_theme_label else "light"
    if desired_theme != active_theme:
        st.session_state.theme = desired_theme
        st.query_params["theme"] = desired_theme
        st.rerun()

    st.sidebar.markdown("<div style='margin-top: 14px;'></div>", unsafe_allow_html=True)

    default_sample = str((Path(__file__).parent / "sample_project").resolve())

    st.sidebar.caption("TARGET CODEBASE")
    repo_input = st.sidebar.text_input(
        "Repository Directory",
        value=st.session_state.repo_path or default_sample,
        help="Local directory path containing the Python codebase to analyze.",
        label_visibility="collapsed",
    )

    btn_col1, btn_col2 = st.sidebar.columns([1, 1])
    with btn_col1:
        if st.button("Scan Repo", type="primary", use_container_width=True):
            run_scan(repo_input)
    with btn_col2:
        if st.button("Load Sample", use_container_width=True):
            run_scan(default_sample)

    if st.session_state.scanned:
        repo_name = Path(st.session_state.repo_path).name or "Repository"
        st.sidebar.markdown(f"""
            <div style="margin-top: 14px; padding: 12px 14px; border-radius: 8px; background-color: var(--ui-bg-elevated); border: 1px solid var(--ui-border-strong);">
                <div style="font-size: 11px; font-weight: 700; text-transform: uppercase; color: var(--ui-text-muted); letter-spacing: 0.05em;">ACTIVE CODEBASE</div>
                <div style="font-family: 'JetBrains Mono', Consolas, monospace; font-size: 13.5px; font-weight: 700; color: var(--ui-text-primary); margin-top: 2px;">
                    {repo_name}
                </div>
                <div style="font-size: 11.5px; color: var(--ui-text-secondary); margin-top: 4px;">
                    {len(st.session_state.parsed_files)} Python files · {len(st.session_state.functions)} functions
                </div>
            </div>
        """, unsafe_allow_html=True)

    with st.sidebar.expander("Excluded Directories", expanded=False):
        st.caption("Bypassed during scanner traversal:")
        st.code("\n".join(sorted(DEFAULT_EXCLUDED_DIRS)), language="text")

    st.sidebar.markdown("<div style='margin-top: 18px;'></div>", unsafe_allow_html=True)
    st.sidebar.caption("Zero-Execution Guarantee: Analyzed code is never imported or executed.")

    # Top Header Bar
    repo_tag = Path(st.session_state.repo_path).name if st.session_state.scanned else "No repository loaded"
    status_dot = '<span class="live-pulse-dot"></span>' if st.session_state.scanned else ''
    status_text = "AST Index Live" if st.session_state.scanned else "Awaiting repository scan"

    display_html(f"""
        <div class="app-header-bar">
            <div class="app-header-left">
                <span class="app-brand-title">
                    <span class="app-logo-badge">
                        {get_svg_icon("logo", size=16, color="#ffffff")}
                    </span>
                    Codebase Intelligence
                </span>
                <span class="app-repo-badge">
                    {status_dot} <span style="margin-left: 4px; font-weight: 600;">{repo_tag}</span>
                    <span style="color: var(--ui-text-muted); margin-left: 6px;">({status_text})</span>
                </span>
            </div>
            <div class="app-header-right">
                <span class="ui-tag">
                    <span style="display:inline-block; width:6px; height:6px; border-radius:50%; background:#4f46e5;"></span>
                    AST Grammar
                </span>
                <span class="ui-tag">
                    <span style="display:inline-block; width:6px; height:6px; border-radius:50%; background:#0284c7;"></span>
                    TF-IDF Vectorizer
                </span>
                <span class="ui-tag">
                    <span style="display:inline-block; width:6px; height:6px; border-radius:50%; background:#7c3aed;"></span>
                    Logistic Regression
                </span>
                <span class="ui-tag">
                    <span style="display:inline-block; width:6px; height:6px; border-radius:50%; background:#059669;"></span>
                    NetworkX Directed Graph
                </span>
            </div>
        </div>
    """)

    # Landing / Empty State
    if not st.session_state.scanned:
        st.markdown(f"""
            <div class="ui-panel" style="padding: 32px 28px; text-align: left;">
                <div style="display: inline-block; padding: 4px 10px; border-radius: 6px; background-color: var(--ui-accent-subtle); border: 1px solid var(--ui-accent-border); color: var(--ui-accent); font-size: 11.5px; font-weight: 700; margin-bottom: 12px; letter-spacing: 0.05em; text-transform: uppercase;">
                    Static Intelligence Engine
                </div>
                <h1 style="font-size: 28px; margin: 0 0 10px 0; font-weight: 800; letter-spacing: -0.03em;">
                    Zero-Cloud Codebase Intelligence & Architectural Mapping
                </h1>
                <p style="font-size: 15px; color: var(--ui-text-secondary); max-width: 850px; line-height: 1.6; margin-bottom: 24px;">
                    Perform deep static AST grammar discovery, natural-language code search, 6-class supervised architectural classification, unsupervised subsystem clustering, and internal import hierarchy analysis — completely locally with zero code execution.
                </p>
                <div class="metric-grid">
                    <div class="ui-metric-tile">
                        <div class="ui-metric-label">
                            Zero Execution Guarantee
                            <span class="metric-icon-well">{get_svg_icon("shield", size=14, color="var(--ui-accent)")}</span>
                        </div>
                        <div style="font-size: 13px; color: var(--ui-text-secondary); margin-top: 6px; line-height: 1.5;">
                            Analyzed code is safely inspected with Python's standard <code>ast.NodeVisitor</code> without ever importing or executing it.
                        </div>
                    </div>
                    <div class="ui-metric-tile">
                        <div class="ui-metric-label">
                            Natural-Language Search
                            <span class="metric-icon-well">{get_svg_icon("search", size=14, color="var(--ui-accent)")}</span>
                        </div>
                        <div style="font-size: 13px; color: var(--ui-text-secondary); margin-top: 6px; line-height: 1.5;">
                            High-speed cosine similarity search powered by sublinear TF-IDF vector n-grams across signatures, docstrings, and code.
                        </div>
                    </div>
                    <div class="ui-metric-tile">
                        <div class="ui-metric-label">
                            Architectural Role Classifier
                            <span class="metric-icon-well">{get_svg_icon("classifier", size=14, color="var(--ui-accent)")}</span>
                        </div>
                        <div style="font-size: 13px; color: var(--ui-text-secondary); margin-top: 6px; line-height: 1.5;">
                            Supervised multiclass Logistic Regression predicting roles (Auth, DB, API, Logic, Config, Tests) with calibrated probabilities.
                        </div>
                    </div>
                    <div class="ui-metric-tile">
                        <div class="ui-metric-label">
                            Interactive Dependency Graph
                            <span class="metric-icon-well">{get_svg_icon("dependencies", size=14, color="var(--ui-accent)")}</span>
                        </div>
                        <div style="font-size: 13px; color: var(--ui-text-secondary); margin-top: 6px; line-height: 1.5;">
                            Force-directed physics visualization mapping internal module import coupling, in-degree utilities, and circular import cycles.
                        </div>
                    </div>
                </div>
            </div>
        """, unsafe_allow_html=True)

        st.markdown("<div style='margin-top: 10px;'></div>", unsafe_allow_html=True)
        col_start1, col_start2, _ = st.columns([1.5, 1.5, 3])
        with col_start1:
            if st.button("Load Sample Project & Explore", type="primary", use_container_width=True):
                run_scan(default_sample)
                st.rerun()
        with col_start2:
            if st.button("Scan Configured Path", use_container_width=True):
                run_scan(repo_input)
                st.rerun()
        return

    # Tabs Navigation
    tab_overview, tab_search, tab_classify, tab_cluster, tab_deps = st.tabs([
        "Codebase Overview",
        "Natural-Language Search",
        "Architectural Classifier",
        "Subsystem Clustering",
        "Dependency Hierarchy",
    ])

    # 1. OVERVIEW TAB
    with tab_overview:
        parsed_files: List[ParsedFile] = st.session_state.parsed_files
        functions: List[FunctionEntity] = st.session_state.functions
        classes: List[ClassInfo] = st.session_state.classes
        total_lines = sum(pf.line_count for pf in parsed_files)
        error_files = [pf for pf in parsed_files if pf.error]
        health_pct = 100 if not error_files else int(((len(parsed_files) - len(error_files)) / len(parsed_files)) * 100)
        health_color = "#10b981" if health_pct == 100 else "#ef4444"

        st.markdown(f"""
            <div class="metric-grid">
                <div class="ui-metric-tile">
                    <div class="ui-metric-label">Python Files <span class="metric-icon-well">{get_svg_icon("file", size=14, color="var(--ui-accent)")}</span></div>
                    <div class="ui-metric-value">{len(parsed_files)}</div>
                    <div class="ui-metric-subtext">Discovered in repository</div>
                </div>
                <div class="ui-metric-tile">
                    <div class="ui-metric-label">Total Lines of Code <span class="metric-icon-well">{get_svg_icon("code", size=14, color="var(--ui-accent)")}</span></div>
                    <div class="ui-metric-value">{total_lines:,}</div>
                    <div class="ui-metric-subtext">Clean source lines scanned</div>
                </div>
                <div class="ui-metric-tile">
                    <div class="ui-metric-label">Functions & Methods <span class="metric-icon-well">{get_svg_icon("function", size=14, color="var(--ui-accent)")}</span></div>
                    <div class="ui-metric-value">{len(functions)}</div>
                    <div class="ui-metric-subtext">Indexed AST entities</div>
                </div>
                <div class="ui-metric-tile">
                    <div class="ui-metric-label">Classes Defined <span class="metric-icon-well">{get_svg_icon("box", size=14, color="var(--ui-accent)")}</span></div>
                    <div class="ui-metric-value">{len(classes)}</div>
                    <div class="ui-metric-subtext">Object models & types</div>
                </div>
                <div class="ui-metric-tile" style="border-left: 3px solid {health_color};">
                    <div class="ui-metric-label">AST Health Score <span class="metric-icon-well" style="background: var(--ui-accent-subtle);">{get_svg_icon("shield", size=14, color=health_color)}</span></div>
                    <div class="ui-metric-value" style="color: {health_color};">{health_pct}%</div>
                    <div class="ui-metric-subtext">{'All files parsed cleanly' if not error_files else f'{len(error_files)} syntax exception(s)'}</div>
                </div>
            </div>
        """, unsafe_allow_html=True)

        if error_files:
            st.markdown("""
                <div style="padding: 12px 16px; background-color: var(--ui-bg-elevated); border-left: 3px solid #ef4444; border-radius: 8px; margin-bottom: 18px;">
                    <span style="font-weight: 700; font-size: 13.5px; color: #ef4444;">Syntax / Parsing Exceptions Encountered:</span>
                </div>
            """, unsafe_allow_html=True)
            for ef in error_files:
                st.code(f"{ef.file_path}: {ef.error}")

        st.markdown("### Discovered Source Files")
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

    # 2. CODE SEARCH TAB
    with tab_search:
        st.markdown("### Natural-Language Code Search")
        st.caption(
            "Vector retrieval across function signatures, parameters, docstrings, and source code using sublinear TF-IDF and Cosine Similarity."
        )

        st.markdown("<small style='color: var(--ui-text-muted); font-weight: 700; letter-spacing: 0.04em;'>QUICK QUERY PRESETS:</small>", unsafe_allow_html=True)
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
                    <div class="ui-panel" style="padding: 24px; text-align: center; color: var(--ui-text-muted);">
                        No code matches found meeting the minimum relevance threshold.
                    </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown(f"<div style='font-size: 13.5px; color: var(--ui-text-muted); margin-bottom: 14px;'>Showing <b>{len(results)}</b> ranked match(es):</div>", unsafe_allow_html=True)

                for r in results:
                    score_pct = int(r.score * 100)
                    meter_color = "#10b981" if score_pct >= 60 else ("#f59e0b" if score_pct >= 35 else "#6366f1")

                    header_title = f"#{r.rank} · {r.full_name}() — {score_pct}% Match"
                    with st.expander(header_title, expanded=(r.rank == 1)):
                        # Relevance Score Bar
                        st.markdown(f"""
                            <div style="display: flex; align-items: center; gap: 12px; margin-bottom: 12px; padding: 8px 12px; background: var(--ui-bg-elevated); border-radius: 6px; border: 1px solid var(--ui-border-subtle);">
                                <span style="font-size: 11.5px; font-weight: 700; color: var(--ui-text-muted); text-transform: uppercase;">Match Score:</span>
                                <div style="flex-grow: 1; height: 8px; background: var(--ui-bg-base); border-radius: 4px; overflow: hidden;">
                                    <div style="width: {score_pct}%; height: 100%; background: {meter_color}; border-radius: 4px;"></div>
                                </div>
                                <span style="font-family: 'JetBrains Mono', monospace; font-weight: 700; font-size: 12px; color: {meter_color};">{score_pct}%</span>
                            </div>
                        """, unsafe_allow_html=True)

                        meta_col1, meta_col2 = st.columns(2)
                        with meta_col1:
                            st.markdown(f"<span style='font-size: 12px; color: var(--ui-text-muted);'>File:</span> <code style='font-size: 12px;'>{r.file_path}</code>", unsafe_allow_html=True)
                        with meta_col2:
                            st.markdown(f"<span style='font-size: 12px; color: var(--ui-text-muted);'>Lines:</span> <code style='font-size: 12px;'>{r.line_start}–{r.line_end}</code>", unsafe_allow_html=True)

                        if r.docstring:
                            st.markdown(f"""
                                <div style="margin: 10px 0; padding: 8px 12px; background-color: var(--ui-bg-elevated); border-left: 3px solid var(--ui-accent); border-radius: 4px; font-size: 13px; font-style: italic; color: var(--ui-text-secondary);">
                                    {r.docstring}
                                </div>
                            """, unsafe_allow_html=True)

                        code_html = render_code_block(
                            source_code=r.source_code,
                            file_path=r.file_path,
                            line_start=r.line_start,
                            line_end=r.line_end,
                            query=query,
                            is_dark=is_dark,
                        )
                        display_html(code_html)

    # 3. ARCHITECTURAL CLASSIFICATION TAB
    with tab_classify:
        st.markdown("### Architectural Code Classification")
        st.caption(
            "Supervised multiclass Logistic Regression model with calibrated probability distributions across 6 core architectural layers."
        )

        classifier = get_classifier()
        info = classifier.get_dataset_info()

        df: pd.DataFrame = st.session_state.classified_df
        if df is not None and not df.empty:
            cat_counts = df["Category"].value_counts()

            c_chart, c_filter = st.columns([1.2, 1])
            with c_chart:
                st.markdown("#### Architectural Role Breakdown")
                st.bar_chart(cat_counts, color="#6366f1" if is_dark else "#4f46e5")

            with c_filter:
                st.markdown("#### Filter Functions")
                f_cat = st.selectbox("Filter by Category", ["All Categories"] + CATEGORIES)
                conf_min = st.slider("Minimum Confidence Threshold", 0.0, 1.0, 0.0, step=0.05)

                filtered_df = df[df["Confidence"] >= conf_min]
                if f_cat != "All Categories":
                    filtered_df = filtered_df[filtered_df["Category"] == f_cat]

                st.markdown(f"<div style='font-size: 13px; color: var(--ui-text-muted);'>Displaying <b>{len(filtered_df)}</b> of {len(df)} functions</div>", unsafe_allow_html=True)

            st.markdown("<div style='margin-top: 18px;'></div>", unsafe_allow_html=True)

            for _, row in filtered_df.iterrows():
                entity: FunctionEntity = row["Entity"]
                conf_pct = int(row["Confidence"] * 100)
                category = row["Category"]

                with st.expander(f"{row['Function']}() · {category} ({conf_pct}% confidence)"):
                    badge_html = render_category_tag(category, row["Confidence"], is_dark=is_dark)
                    st.markdown(f"""
                        <div style="display: flex; align-items: center; justify-content: space-between; gap: 8px; margin-bottom: 12px;">
                            <div style="display: flex; align-items: center; gap: 8px;">
                                {badge_html}
                                <span style="font-size: 12.5px; color: var(--ui-text-muted);">
                                    Defined in <code>{row['File']}</code> (lines {row['Lines']})
                                </span>
                            </div>
                        </div>
                    """, unsafe_allow_html=True)

                    # Modern Horizontal Multi-Class Probability Bars
                    st.markdown("<div style='font-size: 11px; font-weight: 700; text-transform: uppercase; color: var(--ui-text-muted); margin-bottom: 6px;'>Calibrated Class Probabilities:</div>", unsafe_allow_html=True)
                    prob_bars_html = render_probability_bars(row["Probabilities"], is_dark=is_dark)
                    display_html(f"<div style='padding: 8px 12px; background: var(--ui-bg-elevated); border-radius: 6px; border: 1px solid var(--ui-border-subtle); margin-bottom: 12px;'>{prob_bars_html}</div>")

                    code_html = render_code_block(
                        source_code=entity.source_code,
                        file_path=row["File"],
                        line_start=entity.line_start,
                        line_end=entity.line_end,
                        is_dark=is_dark,
                    )
                    display_html(code_html)

            st.markdown("<div style='margin-top: 16px;'></div>", unsafe_allow_html=True)
            st.caption(f"Note: {info['disclaimer']}")
        else:
            st.info("No functions available to classify.")

    # 4. SUBSYSTEM CLUSTERING TAB
    with tab_cluster:
        st.markdown("### Subsystem Topic Discovery & Code Clustering")
        st.caption(
            "Unsupervised K-Means clustering in the TF-IDF feature space identifying functional subsystems without manual tags."
        )

        functions: List[FunctionEntity] = st.session_state.functions
        if functions:
            max_k_possible = min(15, max(2, len(functions)))
            k_val = st.slider(
                "Number of Subsystem Clusters (k)",
                min_value=1,
                max_value=max_k_possible,
                value=min(4, max_k_possible),
            )

            clusterer = CodeClusterer()
            outcome = clusterer.cluster(functions, n_clusters=k_val)

            if outcome.note:
                st.caption(outcome.note)

            st.markdown(f"<div style='font-size: 13.5px; color: var(--ui-text-muted); margin-bottom: 14px;'>Discovered <b>{outcome.effective_k}</b> subsystem cluster(s) across {len(functions)} functions:</div>", unsafe_allow_html=True)

            for group in outcome.groups:
                terms_str = ", ".join(group.representative_terms[:4]) if group.representative_terms else "general"
                with st.expander(f"Cluster {group.cluster_id}: {group.size} function(s) — [{terms_str}]", expanded=True):
                    st.markdown("<div style='font-size: 11px; font-weight: 700; text-transform: uppercase; color: var(--ui-text-muted); margin-bottom: 6px;'>Representative Vocabulary Keywords:</div>", unsafe_allow_html=True)
                    terms_badges = " ".join(
                        f"<span class='ui-tag' style='background: var(--ui-bg-elevated); border: 1px solid var(--ui-border-subtle); color: var(--ui-text-primary); margin-right: 6px;'>#{term}</span>"
                        for term in group.representative_terms
                    )
                    st.markdown(terms_badges or "None", unsafe_allow_html=True)

                    st.markdown("<div style='font-size: 11px; font-weight: 700; text-transform: uppercase; color: var(--ui-text-muted); margin-top: 14px; margin-bottom: 8px;'>Assigned Functions:</div>", unsafe_allow_html=True)
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

    # 5. DEPENDENCY GRAPH TAB
    with tab_deps:
        st.markdown("### Internal Module Dependency Hierarchy")
        st.caption(
            "Directed graph of internal file-level imports constructed using NetworkX. Analyzes architectural couplings and detects circular dependencies."
        )

        dep_graph = st.session_state.dep_graph
        metrics = st.session_state.graph_metrics

        if dep_graph is not None and metrics is not None:
            has_cycle = metrics["cycle_count"] > 0
            cycle_color = "#ef4444" if has_cycle else "#10b981"

            st.markdown(f"""
                <div class="metric-grid">
                    <div class="ui-metric-tile">
                        <div class="ui-metric-label">Internal Files (Nodes) <span class="metric-icon-well">{get_svg_icon("file", size=14, color="var(--ui-accent)")}</span></div>
                        <div class="ui-metric-value">{metrics['num_nodes']}</div>
                        <div class="ui-metric-subtext">Active repository modules</div>
                    </div>
                    <div class="ui-metric-tile">
                        <div class="ui-metric-label">Import Edges <span class="metric-icon-well">{get_svg_icon("link", size=14, color="var(--ui-accent)")}</span></div>
                        <div class="ui-metric-value">{metrics['num_edges']}</div>
                        <div class="ui-metric-subtext">Directed dependency links</div>
                    </div>
                    <div class="ui-metric-tile" style="border-left: 3px solid {cycle_color};">
                        <div class="ui-metric-label">Circular Import Cycles <span class="metric-icon-well" style="background: {'rgba(16, 185, 129, 0.1)' if not has_cycle else 'rgba(239, 68, 68, 0.1)'};">{get_svg_icon("cycle", size=14, color=cycle_color)}</span></div>
                        <div class="ui-metric-value" style="color: {cycle_color};">{metrics['cycle_count']}</div>
                        <div class="ui-metric-subtext">{'Zero cycles detected (Clean)' if not has_cycle else 'Dangerous circular couplings'}</div>
                    </div>
                    <div class="ui-metric-tile">
                        <div class="ui-metric-label">Isolated Modules <span class="metric-icon-well">{get_svg_icon("isolated", size=14, color="var(--ui-accent)")}</span></div>
                        <div class="ui-metric-value">{len(metrics['isolated_files'])}</div>
                        <div class="ui-metric-subtext">Zero internal imports</div>
                    </div>
                </div>
            """, unsafe_allow_html=True)

            if metrics["cycles"]:
                st.error(f"Circular import cycle detected: {metrics['cycles']}")

            # Visualization Mode Toggle
            v_col1, v_col2 = st.columns([2, 1])
            with v_col1:
                graph_mode = st.radio(
                    "Graph Mode",
                    options=["Interactive Physics Graph (Drag & Zoom)", "Hi-Res Publication Diagram"],
                    horizontal=True,
                    label_visibility="collapsed",
                )

            if "Interactive" in graph_mode:
                interactive_html = render_interactive_graph_html(dep_graph, is_dark=is_dark, height_px=550)
                components.html(interactive_html, height=560)
            else:
                fig = render_graph_figure(dep_graph, is_dark=is_dark)
                st.pyplot(fig)
                plt.close(fig)

            st.markdown("### Architectural Coupling Breakdown")
            c_dep1, c_dep2 = st.columns(2)
            with c_dep1:
                st.markdown("#### In-Degree (Core Utility Modules)")
                st.caption("Foundational utilities that multiple other modules depend on.")
                in_data = [
                    {"File": f, "Imported By (Count)": count}
                    for f, count in metrics["most_depended_on"]
                ]
                st.dataframe(pd.DataFrame(in_data), use_container_width=True, hide_index=True)

            with c_dep2:
                st.markdown("#### Out-Degree (High Consumer Modules)")
                st.caption("Orchestrators or services that import multiple internal modules.")
                out_data = [
                    {"File": f, "Imports (Count)": count}
                    for f, count in metrics["most_dependencies"]
                ]
                st.dataframe(pd.DataFrame(out_data), use_container_width=True, hide_index=True)

            with st.expander("Detailed Internal Edge Dependency Matrix"):
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
