
from __future__ import annotations
import html
import re
from typing import Dict, List, Optional, Any
from pygments import highlight
from pygments.lexers import PythonLexer
from pygments.formatters import HtmlFormatter


THEME_CONFIG: Dict[str, Dict[str, str]] = {
    "light": {
        "bg_base": "#fbfbfa",
        "bg_surface": "#ffffff",
        "bg_elevated": "#f4f4f2",
        "bg_hover": "#f0f0ed",
        
        "border_subtle": "#e5e5e2",
        "border_strong": "#d4d4cf",
        
        "text_primary": "#1a1a1c",
        "text_secondary": "#52525b",
        "text_muted": "#71717a",
        
        "accent": "#0969da",
        "accent_hover": "#0550ae",
        "accent_subtle": "#eff6ff",
        "accent_border": "#bfdbfe",
        
        "code_bg": "#f6f6f4",
        "code_header_bg": "#ebebe8",
        "code_border": "#e2e2dd",
        "code_lineno": "#9ca3af",
        "code_text": "#1f2328",
        
        "tok_keyword": "#cf222e",
        "tok_func": "#8250df",
        "tok_class": "#0550ae",
        "tok_string": "#0a3069",
        "tok_docstring": "#57606a",
        "tok_number": "#953800",
        "tok_comment": "#6e7781",
        "tok_builtin": "#116329",
        "tok_operator": "#24292f",
        "tok_ident": "#1f2328",
        
        "query_hit_bg": "#fef08a",
        "query_hit_text": "#713f12",
        
        "status_success_bg": "#ecfdf5",
        "status_success_border": "#a7f3d0",
        "status_success_text": "#065f46",
        "status_error_bg": "#fef2f2",
        "status_error_border": "#fecaca",
        "status_error_text": "#991b1b",
    },
    "dark": {
        "bg_base": "#18191c",
        "bg_surface": "#202124",
        "bg_elevated": "#282a2e",
        "bg_hover": "#2d3035",
        
        "border_subtle": "#2e3035",
        "border_strong": "#3d4047",
        
        "text_primary": "#e6e6e8",
        "text_secondary": "#a1a1aa",
        "text_muted": "#71717a",
        
        "accent": "#3b82f6",
        "accent_hover": "#60a5fa",
        "accent_subtle": "#172554",
        "accent_border": "#1e40af",
        
        "code_bg": "#121316",
        "code_header_bg": "#1a1b1f",
        "code_border": "#28292d",
        "code_lineno": "#52525b",
        "code_text": "#e4e4e7",
        
        "tok_keyword": "#ff7b72",
        "tok_func": "#d2a8ff",
        "tok_class": "#79c0ff",
        "tok_string": "#7ee787",
        "tok_docstring": "#8b949e",
        "tok_number": "#ffa657",
        "tok_comment": "#8b949e",
        "tok_builtin": "#ffa657",
        "tok_operator": "#c9d1d9",
        "tok_ident": "#e6edf3",
        
        "query_hit_bg": "#854d0e",
        "query_hit_text": "#fef08a",
        
        "status_success_bg": "#064e3b",
        "status_success_border": "#047857",
        "status_success_text": "#a7f3d0",
        "status_error_bg": "#450a0a",
        "status_error_border": "#991b1b",
        "status_error_text": "#fecaca",
    },
}

CATEGORY_STYLES: Dict[str, Dict[str, Dict[str, str]]] = {
    "light": {
        "Authentication": {"bg": "#f5f3ff", "border": "#ddd6fe", "text": "#6d28d9"},
        "Database Operations": {"bg": "#f0f9ff", "border": "#bae6fd", "text": "#0369a1"},
        "API/Communication": {"bg": "#ecfdf5", "border": "#a7f3d0", "text": "#047857"},
        "Business Logic": {"bg": "#fffbeb", "border": "#fde68a", "text": "#b45309"},
        "Configuration/Utilities": {"bg": "#f8fafc", "border": "#cbd5e1", "text": "#475569"},
        "Testing": {"bg": "#fef2f2", "border": "#fecaca", "text": "#b91c1c"},
    },
    "dark": {
        "Authentication": {"bg": "#2e1065", "border": "#5b21b6", "text": "#c4b5fd"},
        "Database Operations": {"bg": "#082f49", "border": "#0369a1", "text": "#7dd3fc"},
        "API/Communication": {"bg": "#064e3b", "border": "#047857", "text": "#6ee7b7"},
        "Business Logic": {"bg": "#451a03", "border": "#b45309", "text": "#fde68a"},
        "Configuration/Utilities": {"bg": "#0f172a", "border": "#334155", "text": "#cbd5e1"},
        "Testing": {"bg": "#450a0a", "border": "#991b1b", "text": "#fca5a5"},
    },
}



def get_theme_css(theme: str) -> str:
    """Generate complete CSS stylesheet matching active theme."""
    t = THEME_CONFIG.get(theme, THEME_CONFIG["light"])
    is_dark = (theme == "dark")

    return f"""
<style>
    /* CSS Variables */
    :root {{
        --ui-bg-base: {t["bg_base"]};
        --ui-bg-surface: {t["bg_surface"]};
        --ui-bg-elevated: {t["bg_elevated"]};
        --ui-bg-hover: {t["bg_hover"]};
        --ui-border-subtle: {t["border_subtle"]};
        --ui-border-strong: {t["border_strong"]};
        --ui-text-primary: {t["text_primary"]};
        --ui-text-secondary: {t["text_secondary"]};
        --ui-text-muted: {t["text_muted"]};
        --ui-accent: {t["accent"]};
        --ui-accent-hover: {t["accent_hover"]};
        --ui-accent-subtle: {t["accent_subtle"]};
        --ui-accent-border: {t["accent_border"]};
        --ui-code-bg: {t["code_bg"]};
        --ui-code-header-bg: {t["code_header_bg"]};
        --ui-code-border: {t["code_border"]};
        --ui-code-lineno: {t["code_lineno"]};
        --ui-code-text: {t["code_text"]};
    }}

    /* Global Typography & Font Stacks */
    html, body, [data-testid="stApp"], [data-testid="stAppViewContainer"] {{
        background-color: var(--ui-bg-base) !important;
        color: var(--ui-text-primary) !important;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "Inter", Roboto, Helvetica, Arial, sans-serif !important;
        -webkit-font-smoothing: antialiased;
        -moz-osx-font-smoothing: grayscale;
        font-size: 14px;
        line-height: 1.55;
    }}

    /* Top padding clearance for Streamlit fixed header */
    .block-container {{
        padding-top: 4.5rem !important;
        padding-bottom: 3rem !important;
        max-width: 1280px;
    }}

    /* Streamlit Header & Sidebar Overrides */
    [data-testid="stHeader"] {{
        background-color: var(--ui-bg-base) !important;
        border-bottom: 1px solid var(--ui-border-subtle) !important;
        height: 3.2rem !important;
        z-index: 99 !important;
    }}

    [data-testid="stSidebar"] {{
        background-color: var(--ui-bg-surface) !important;
        border-right: 1px solid var(--ui-border-subtle) !important;
    }}

    [data-testid="stSidebar"] * {{
        color: var(--ui-text-primary);
    }}

    /* Headings hierarchy */
    h1, h2, h3, h4, h5, h6 {{
        color: var(--ui-text-primary) !important;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "Inter", Roboto, sans-serif !important;
        font-weight: 600 !important;
        letter-spacing: -0.015em !important;
    }}

    h1 {{ font-size: 22px !important; margin-bottom: 4px !important; }}
    h2 {{ font-size: 17px !important; margin-top: 18px !important; margin-bottom: 8px !important; }}
    h3 {{ font-size: 15px !important; margin-top: 14px !important; margin-bottom: 6px !important; }}
    h4 {{ font-size: 13px !important; text-transform: uppercase; letter-spacing: 0.04em; color: var(--ui-text-muted) !important; }}

    p, span, label {{
        color: var(--ui-text-secondary);
    }}

    /* Streamlit Tabs Navigation */
    .stTabs [data-baseweb="tab-list"] {{
        background-color: transparent !important;
        border-bottom: 1px solid var(--ui-border-subtle) !important;
        gap: 20px !important;
        padding-bottom: 2px !important;
    }}

    .stTabs [data-baseweb="tab"] {{
        background-color: transparent !important;
        color: var(--ui-text-muted) !important;
        font-size: 13px !important;
        font-weight: 500 !important;
        padding: 8px 4px !important;
        border: none !important;
        border-bottom: 2px solid transparent !important;
        transition: color 0.15s ease, border-color 0.15s ease;
    }}

    .stTabs [data-baseweb="tab"]:hover {{
        color: var(--ui-text-primary) !important;
    }}

    .stTabs [aria-selected="true"] {{
        color: var(--ui-accent) !important;
        font-weight: 600 !important;
        border-bottom: 2px solid var(--ui-accent) !important;
    }}

    /* Form Controls & Inputs */
    input, textarea, [data-baseweb="input"] input, [data-baseweb="select"] {{
        background-color: var(--ui-bg-surface) !important;
        color: var(--ui-text-primary) !important;
        border: 1px solid var(--ui-border-subtle) !important;
        border-radius: 6px !important;
        font-size: 13px !important;
    }}

    input:focus, textarea:focus {{
        border-color: var(--ui-accent) !important;
        box-shadow: 0 0 0 1px var(--ui-accent) !important;
    }}

    /* Buttons */
    .stButton button {{
        background-color: var(--ui-bg-surface) !important;
        color: var(--ui-text-primary) !important;
        border: 1px solid var(--ui-border-subtle) !important;
        border-radius: 6px !important;
        font-size: 13px !important;
        font-weight: 500 !important;
        padding: 6px 14px !important;
        transition: background-color 0.15s ease, border-color 0.15s ease;
    }}

    .stButton button:hover {{
        background-color: var(--ui-bg-hover) !important;
        border-color: var(--ui-border-strong) !important;
    }}

    .stButton button[kind="primary"] {{
        background-color: var(--ui-accent) !important;
        color: #ffffff !important;
        border: 1px solid var(--ui-accent) !important;
        font-weight: 600 !important;
    }}

    .stButton button[kind="primary"]:hover {{
        background-color: var(--ui-accent-hover) !important;
        border-color: var(--ui-accent-hover) !important;
    }}

    /* Custom UI Components */
    .app-header-bar {{
        display: flex;
        justify-content: space-between;
        align-items: center;
        flex-wrap: wrap;
        gap: 12px;
        padding: 4px 0 16px 0;
        margin-top: 0;
        margin-bottom: 18px;
        border-bottom: 1px solid var(--ui-border-subtle);
    }}

    .app-header-left {{
        display: flex;
        align-items: center;
        gap: 10px;
        flex-wrap: wrap;
    }}

    .app-header-right {{
        font-size: 12px;
        color: var(--ui-text-muted);
    }}

    .app-brand-title {{
        font-size: 17px;
        font-weight: 700;
        color: var(--ui-text-primary);
        letter-spacing: -0.02em;
        margin: 0;
    }}

    .app-repo-badge {{
        display: inline-flex;
        align-items: center;
        font-family: "JetBrains Mono", Consolas, monospace;
        font-size: 11px;
        padding: 2px 8px;
        border-radius: 4px;
        background-color: var(--ui-bg-elevated);
        color: var(--ui-text-secondary);
        border: 1px solid var(--ui-border-subtle);
    }}

    /* Card Panels */
    .ui-panel {{
        background-color: var(--ui-bg-surface);
        border: 1px solid var(--ui-border-subtle);
        border-radius: 6px;
        padding: 16px 18px;
        margin-bottom: 14px;
    }}

    /* Metric Tiles Grid */
    .metric-grid {{
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
        gap: 12px;
        margin-bottom: 18px;
    }}

    .ui-metric-tile {{
        background-color: var(--ui-bg-surface);
        border: 1px solid var(--ui-border-subtle);
        border-radius: 6px;
        padding: 12px 14px;
    }}

    .ui-metric-label {{
        font-size: 11px;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        color: var(--ui-text-muted);
        margin-bottom: 4px;
    }}

    .ui-metric-value {{
        font-size: 22px;
        font-weight: 700;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
        color: var(--ui-text-primary);
        letter-spacing: -0.02em;
    }}

    /* Badges & Tags */
    .ui-tag {{
        display: inline-block;
        padding: 2px 8px;
        border-radius: 4px;
        font-size: 11px;
        font-weight: 600;
        font-family: "JetBrains Mono", Consolas, monospace;
        letter-spacing: 0.01em;
        white-space: nowrap;
    }}

    /* Pygments Obsidian Code Container */
    .obsidian-code-wrapper {{
        margin: 12px 0 16px 0;
        border: 1px solid var(--ui-code-border);
        border-radius: 6px;
        background-color: var(--ui-code-bg);
        overflow: hidden;
    }}

    .obsidian-code-header {{
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 6px 12px;
        background-color: var(--ui-code-header-bg);
        border-bottom: 1px solid var(--ui-code-border);
        font-family: "JetBrains Mono", Consolas, monospace;
        font-size: 11px;
        color: var(--ui-text-muted);
    }}

    .obsidian-code-lang {{
        font-weight: 600;
        letter-spacing: 0.05em;
        color: var(--ui-text-secondary);
    }}

    .obsidian-code-lines {{
        padding: 8px 0;
        overflow-x: auto;
        background-color: var(--ui-code-bg);
    }}

    .code-line {{
        display: flex !important;
        flex-direction: row !important;
        align-items: baseline !important;
        min-height: 1.45rem !important;
        line-height: 1.55 !important;
        padding: 0 12px !important;
        margin: 0 !important;
        box-sizing: border-box !important;
        width: 100% !important;
    }}

    .code-lineno {{
        flex-shrink: 0 !important;
        width: 3.2rem !important;
        padding-right: 0.8rem !important;
        margin-right: 0.8rem !important;
        text-align: right !important;
        color: var(--ui-code-lineno) !important;
        user-select: none !important;
        border-right: 1px solid var(--ui-code-border) !important;
        font-family: "JetBrains Mono", Consolas, monospace !important;
        font-size: 11.5px !important;
    }}

    .code-content {{
        flex-grow: 1 !important;
        white-space: pre !important;
        overflow-x: visible !important;
        font-family: "JetBrains Mono", "Fira Code", Consolas, "Courier New", monospace !important;
        font-size: 12.5px !important;
        color: var(--ui-code-text) !important;
    }}

    /* Query term highlight inside code */
    mark.query-match {{
        background-color: {t["query_hit_bg"]};
        color: {t["query_hit_text"]};
        padding: 1px 3px;
        border-radius: 3px;
        font-weight: 600;
    }}

    /* Pygments Token Styles */
    .code-content .k, 
    .code-content .kd, 
    .code-content .kn, 
    .code-content .kp, 
    .code-content .kr {{ color: {t["tok_keyword"]}; font-weight: 600; }}
    
    .code-content .nf {{ color: {t["tok_func"]}; font-weight: 600; }}
    .code-content .nc {{ color: {t["tok_class"]}; font-weight: 600; }}
    .code-content .s, 
    .code-content .s1, 
    .code-content .s2, 
    .code-content .sa, 
    .code-content .sb, 
    .code-content .sc {{ color: {t["tok_string"]}; }}
    
    .code-content .sd {{ color: {t["tok_docstring"]}; font-style: italic; }}
    .code-content .m, 
    .code-content .mi, 
    .code-content .mf {{ color: {t["tok_number"]}; }}
    
    .code-content .c, 
    .code-content .c1, 
    .code-content .ch, 
    .code-content .cm {{ color: {t["tok_comment"]}; font-style: italic; }}
    
    .code-content .nb {{ color: {t["tok_builtin"]}; }}
    .code-content .o, 
    .code-content .ow, 
    .code-content .p {{ color: {t["tok_operator"]}; }}
    .code-content .n, 
    .code-content .na, 
    .code-content .nv, 
    .code-content .nn {{ color: {t["tok_ident"]}; }}

    /* Streamlit Expander styling */
    [data-testid="stExpander"] {{
        background-color: var(--ui-bg-surface) !important;
        border: 1px solid var(--ui-border-subtle) !important;
        border-radius: 6px !important;
        margin-bottom: 8px !important;
    }}

    [data-testid="stExpander"] summary {{
        font-size: 13px !important;
        font-weight: 500 !important;
        color: var(--ui-text-primary) !important;
        padding: 10px 14px !important;
    }}

    /* Table styling */
    [data-testid="stDataFrame"] {{
        border: 1px solid var(--ui-border-subtle) !important;
        border-radius: 6px !important;
        overflow: hidden;
    }}
</style>
"""



def highlight_terms_in_html(html_str: str, query: Optional[str]) -> str:
    """Highlight matched query words inside HTML text nodes safely."""
    if not query:
        return html_str

    tokens = [re.escape(t.strip()) for t in re.split(r"\s+", query) if len(t.strip()) >= 3]
    if not tokens:
        return html_str

    regex_pattern = re.compile(r"\b(" + "|".join(tokens) + r")\b", re.IGNORECASE)

    def replace_text_segment(match: re.Match) -> str:
        prefix, text, suffix = match.group(1), match.group(2), match.group(3)
        highlighted = regex_pattern.sub(r'<mark class="query-match">\1</mark>', text)
        return f"{prefix}{highlighted}{suffix}"

    return re.sub(r"(>)([^<]+)(<)", replace_text_segment, html_str)


def render_code_block(
    source_code: str,
    file_path: Optional[str] = None,
    line_start: int = 1,
    line_end: Optional[int] = None,
    query: Optional[str] = None,
    is_dark: bool = False,
) -> str:
    """Render a syntax-highlighted code block with line numbering & Obsidian styling.

    Args:
        source_code: Python source code snippet.
        file_path: Optional file path to show in header.
        line_start: 1-indexed starting line number.
        line_end: Optional 1-indexed ending line number.
        query: Optional search query to highlight matching terms.
        is_dark: Boolean indicating if dark theme is active.

    Returns:
        Safe HTML string ready to render via st.html or st.markdown.
    """
    clean_code = source_code.rstrip()
    if not clean_code:
        return ""

    formatter = HtmlFormatter(nowrap=True)
    try:
        raw_highlighted = highlight(clean_code, PythonLexer(), formatter)
    except Exception:
        raw_highlighted = html.escape(clean_code)

    final_highlighted = highlight_terms_in_html(raw_highlighted, query)

    lines = final_highlighted.splitlines()
    start_num = max(1, line_start)

    rendered_line_divs = []
    for idx, line_content in enumerate(lines):
        line_num = start_num + idx
        content = line_content if line_content.strip() else "&nbsp;"
        rendered_line_divs.append(
            f'<div class="code-line">'
            f'<span class="code-lineno">{line_num}</span>'
            f'<span class="code-content">{content}</span>'
            f'</div>'
        )

    code_lines_html = "\n".join(rendered_line_divs)

    location_parts = []
    if file_path:
        location_parts.append(html.escape(file_path))
    if line_start:
        if line_end and line_end > line_start:
            location_parts.append(f": {line_start}-{line_end}")
        else:
            location_parts.append(f": {line_start}")

    location_str = "".join(location_parts)

    return f"""
<div class="obsidian-code-wrapper">
    <div class="obsidian-code-header">
        <span class="obsidian-code-lang">PYTHON</span>
        <span>{location_str}</span>
    </div>
    <div class="obsidian-code-lines">
        {code_lines_html}
    </div>
</div>
"""



def render_category_tag(category: str, confidence: Optional[float] = None, is_dark: bool = False) -> str:
    """Return an HTML tag with restrained category coloring and confidence score."""
    mode = "dark" if is_dark else "light"
    styles = CATEGORY_STYLES[mode].get(category, {"bg": "#f4f4f5", "border": "#e4e4e7", "text": "#52525b"})
    
    conf_str = f" · {int(confidence * 100)}%" if confidence is not None else ""
    return (
        f'<span class="ui-tag" style="background-color: {styles["bg"]}; '
        f'border: 1px solid {styles["border"]}; color: {styles["text"]};">'
        f'{html.escape(category)}{conf_str}</span>'
    )
