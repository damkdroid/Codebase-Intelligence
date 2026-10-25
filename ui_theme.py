# ui_theme.py

from __future__ import annotations
import html
import re
from typing import Dict, List, Optional, Any
from pygments import highlight
from pygments.lexers import PythonLexer
from pygments.formatters import HtmlFormatter


THEME_CONFIG: Dict[str, Dict[str, str]] = {
    "light": {
        "bg_base": "#f8fafc",
        "bg_surface": "#ffffff",
        "bg_elevated": "#f1f5f9",
        "bg_hover": "#f8fafc",
        
        "border_subtle": "#e2e8f0",
        "border_strong": "#cbd5e1",
        
        "text_primary": "#0f172a",
        "text_secondary": "#334155",
        "text_muted": "#64748b",
        
        "accent": "#4f46e5",
        "accent_hover": "#4338ca",
        "accent_subtle": "#eef2ff",
        "accent_border": "#c7d2fe",
        
        "code_bg": "#ffffff",
        "code_header_bg": "#f8fafc",
        "code_border": "#e2e8f0",
        "code_lineno": "#94a3b8",
        "code_text": "#0f172a",
        
        "tok_keyword": "#cf222e",
        "tok_func": "#6f42c1",
        "tok_class": "#0969da",
        "tok_string": "#0a7d57",
        "tok_docstring": "#57606a",
        "tok_number": "#d97706",
        "tok_comment": "#6e7781",
        "tok_builtin": "#0d9488",
        "tok_operator": "#24292f",
        "tok_ident": "#0f172a",
        
        "query_hit_bg": "#fef08a",
        "query_hit_text": "#713f12",
        
        "status_success_bg": "#ecfdf5",
        "status_success_border": "#a7f3d0",
        "status_success_text": "#047857",
        "status_error_bg": "#fef2f2",
        "status_error_border": "#fecaca",
        "status_error_text": "#b91c1c",
    },
    "dark": {
        "bg_base": "#0a0c10",
        "bg_surface": "#12151c",
        "bg_elevated": "#181d27",
        "bg_hover": "#222a38",
        
        "border_subtle": "rgba(255, 255, 255, 0.08)",
        "border_strong": "rgba(255, 255, 255, 0.16)",
        
        "text_primary": "#f8fafc",
        "text_secondary": "#94a3b8",
        "text_muted": "#64748b",
        
        "accent": "#6366f1",
        "accent_hover": "#818cf8",
        "accent_subtle": "rgba(99, 102, 241, 0.15)",
        "accent_border": "rgba(99, 102, 241, 0.35)",
        
        "code_bg": "#0c0f15",
        "code_header_bg": "#141822",
        "code_border": "#1e2533",
        "code_lineno": "#475569",
        "code_text": "#e2e8f0",
        
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
        "Authentication": {"bg": "#ede9fe", "border": "#c4b5fd", "text": "#5b21b6", "dot": "#7c3aed"},
        "Database Operations": {"bg": "#e0f2fe", "border": "#7dd3fc", "text": "#0369a1", "dot": "#0284c7"},
        "API/Communication": {"bg": "#d1fae5", "border": "#6ee7b7", "text": "#065f46", "dot": "#059669"},
        "Business Logic": {"bg": "#fef3c7", "border": "#fcd34d", "text": "#92400e", "dot": "#d97706"},
        "Configuration/Utilities": {"bg": "#f1f5f9", "border": "#cbd5e1", "text": "#1e293b", "dot": "#475569"},
        "Testing": {"bg": "#fee2e2", "border": "#fca5a5", "text": "#991b1b", "dot": "#dc2626"},
    },
    "dark": {
        "Authentication": {"bg": "rgba(139, 92, 246, 0.15)", "border": "rgba(139, 92, 246, 0.4)", "text": "#c4b5fd", "dot": "#a78bfa"},
        "Database Operations": {"bg": "rgba(14, 165, 233, 0.15)", "border": "rgba(14, 165, 233, 0.4)", "text": "#7dd3fc", "dot": "#38bdf8"},
        "API/Communication": {"bg": "rgba(16, 185, 129, 0.15)", "border": "rgba(16, 185, 129, 0.4)", "text": "#6ee7b7", "dot": "#34d399"},
        "Business Logic": {"bg": "rgba(245, 158, 11, 0.15)", "border": "rgba(245, 158, 11, 0.4)", "text": "#fde68a", "dot": "#fbbf24"},
        "Configuration/Utilities": {"bg": "rgba(148, 163, 184, 0.15)", "border": "rgba(148, 163, 184, 0.4)", "text": "#cbd5e1", "dot": "#94a3b8"},
        "Testing": {"bg": "rgba(239, 68, 68, 0.15)", "border": "rgba(239, 68, 68, 0.4)", "text": "#fca5a5", "dot": "#f87171"},
    },
}


def get_theme_css(theme: str) -> str:
    t = THEME_CONFIG.get(theme, THEME_CONFIG["light"])
    is_dark = (theme == "dark")

    return f"""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600;700&display=swap');

    /* CSS Custom Properties */
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

    /* Global Typography & Smoothing */
    html, body, [data-testid="stApp"], [data-testid="stAppViewContainer"] {{
        background-color: var(--ui-bg-base) !important;
        color: var(--ui-text-primary) !important;
        font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif !important;
        -webkit-font-smoothing: antialiased;
        -moz-osx-font-smoothing: grayscale;
        font-size: 14px;
        line-height: 1.6;
    }}

    /* Main Container max width and spacing */
    .block-container {{
        padding-top: 3.8rem !important;
        padding-bottom: 3.5rem !important;
        max-width: 1320px;
    }}

    /* Streamlit Fixed Header & Sidebar */
    [data-testid="stHeader"] {{
        background-color: {"rgba(10, 12, 16, 0.85)" if is_dark else "rgba(255, 255, 255, 0.85)"} !important;
        backdrop-filter: blur(12px) !important;
        -webkit-backdrop-filter: blur(12px) !important;
        border-bottom: 1px solid var(--ui-border-subtle) !important;
        height: 3.2rem !important;
        z-index: 99 !important;
    }}

    [data-testid="stSidebar"] {{
        background-color: var(--ui-bg-surface) !important;
        border-right: 1px solid var(--ui-border-subtle) !important;
        box-shadow: {"none" if is_dark else "2px 0 12px rgba(15, 23, 42, 0.03)"} !important;
    }}

    [data-testid="stSidebar"] * {{
        color: var(--ui-text-primary);
    }}

    /* Modern Headings Hierarchy */
    h1, h2, h3, h4, h5, h6 {{
        color: var(--ui-text-primary) !important;
        font-family: 'Plus Jakarta Sans', sans-serif !important;
        font-weight: 700 !important;
        letter-spacing: -0.025em !important;
    }}

    h1 {{ font-size: 24px !important; margin-bottom: 6px !important; }}
    h2 {{ font-size: 18px !important; margin-top: 20px !important; margin-bottom: 10px !important; }}
    h3 {{ font-size: 16px !important; margin-top: 20px !important; margin-bottom: 10px !important; font-weight: 700 !important; }}
    h4 {{ font-size: 12.5px !important; text-transform: uppercase; letter-spacing: 0.05em; color: var(--ui-text-muted) !important; }}

    p, span, label {{
        color: var(--ui-text-secondary);
    }}

    /* Streamlit Global Primary Color Overrides */
    :root {{
        --primary-color: {t["accent"]} !important;
    }}

    /* Custom Modern Streamlit Tabs (Segmented Control Pill Style) */
    .stTabs [role="tablist"],
    div[data-testid="stTabs"] [role="tablist"],
    .stTabs [data-baseweb="tab-list"] {{
        background-color: {"rgba(255, 255, 255, 0.04)" if is_dark else "#f1f5f9"} !important;
        border: 1px solid {"rgba(255, 255, 255, 0.08)" if is_dark else "#e2e8f0"} !important;
        border-radius: 10px !important;
        padding: 4px !important;
        gap: 3px !important;
        display: inline-flex !important;
        margin-bottom: 22px !important;
        position: relative !important;
    }}

    /* Remove Streamlit default red tab-highlight underline completely */
    .stTabs [role="tablist"] > div:not([role="tab"]),
    div[data-testid="stTabs"] [role="tablist"] > div:not([role="tab"]),
    .stTabs [data-baseweb="tab-highlight"],
    [data-baseweb="tab-highlight"],
    .stTabs [role="tablist"] > span:last-child {{
        display: none !important;
        visibility: hidden !important;
        opacity: 0 !important;
        height: 0 !important;
        width: 0 !important;
        background-color: transparent !important;
        border: none !important;
    }}

    .stTabs [role="tab"],
    div[data-testid="stTabs"] [role="tab"],
    .stTabs [data-baseweb="tab"] {{
        display: inline-flex !important;
        align-items: center !important;
        gap: 8px !important;
        background-color: transparent !important;
        color: {"#94a3b8" if is_dark else "#64748b"} !important;
        font-size: 13px !important;
        font-weight: 500 !important;
        padding: 7px 15px !important;
        border-radius: 7px !important;
        border: 1px solid transparent !important;
        border-bottom: 1px solid transparent !important;
        transition: all 0.15s cubic-bezier(0.16, 1, 0.3, 1) !important;
        cursor: pointer !important;
    }}

    .stTabs [role="tab"]::before,
    div[data-testid="stTabs"] [role="tab"]::before,
    .stTabs [data-baseweb="tab"]::before {{
        content: "";
        display: inline-block;
        width: 14px;
        height: 14px;
        background-color: currentColor;
        flex-shrink: 0;
        -webkit-mask-size: contain;
        mask-size: contain;
        -webkit-mask-repeat: no-repeat;
        mask-repeat: no-repeat;
        -webkit-mask-position: center;
        mask-position: center;
        opacity: 0.85;
    }}

    .stTabs [role="tab"]:hover,
    div[data-testid="stTabs"] [role="tab"]:hover,
    .stTabs [data-baseweb="tab"]:hover {{
        background-color: {"rgba(255, 255, 255, 0.06)" if is_dark else "rgba(255, 255, 255, 0.7)"} !important;
        color: {"#f8fafc" if is_dark else "#0f172a"} !important;
    }}

    .stTabs [role="tab"]:hover::before,
    div[data-testid="stTabs"] [role="tab"]:hover::before,
    .stTabs [data-baseweb="tab"]:hover::before {{
        opacity: 1;
    }}

    .stTabs [role="tab"][aria-selected="true"],
    div[data-testid="stTabs"] [role="tab"][aria-selected="true"],
    .stTabs [aria-selected="true"] {{
        background-color: {"rgba(99, 102, 241, 0.18)" if is_dark else "#ffffff"} !important;
        border: 1px solid {"rgba(99, 102, 241, 0.4)" if is_dark else "rgba(15, 23, 42, 0.08)"} !important;
        color: {"#818cf8" if is_dark else "#4f46e5"} !important;
        font-weight: 600 !important;
        box-shadow: {"0 2px 8px rgba(99, 102, 241, 0.25)" if is_dark else "0 1px 3px rgba(15, 23, 42, 0.08), 0 1px 2px rgba(15, 23, 42, 0.04)"} !important;
    }}

    .stTabs [role="tab"][aria-selected="true"]::before,
    div[data-testid="stTabs"] [role="tab"][aria-selected="true"]::before,
    .stTabs [aria-selected="true"]::before {{
        opacity: 1;
    }}

    .stTabs [role="tab"]:nth-of-type(1)::before,
    .stTabs [data-baseweb="tab"]:nth-child(1)::before {{
        -webkit-mask-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='black' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3E%3Crect width='7' height='9' x='3' y='3' rx='1'/%3E%3Crect width='7' height='5' x='14' y='3' rx='1'/%3E%3Crect width='7' height='9' x='14' y='12' rx='1'/%3E%3Crect width='7' height='5' x='3' y='16' rx='1'/%3E%3C/svg%3E");
        mask-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='black' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3E%3Crect width='7' height='9' x='3' y='3' rx='1'/%3E%3Crect width='7' height='5' x='14' y='3' rx='1'/%3E%3Crect width='7' height='9' x='14' y='12' rx='1'/%3E%3Crect width='7' height='5' x='3' y='16' rx='1'/%3E%3C/svg%3E");
    }}

    .stTabs [role="tab"]:nth-of-type(2)::before,
    .stTabs [data-baseweb="tab"]:nth-child(2)::before {{
        -webkit-mask-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='black' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3E%3Ccircle cx='11' cy='11' r='8'/%3E%3Cpath d='m21 21-4.3-4.3'/%3E%3C/svg%3E");
        mask-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='black' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3E%3Ccircle cx='11' cy='11' r='8'/%3E%3Cpath d='m21 21-4.3-4.3'/%3E%3C/svg%3E");
    }}

    .stTabs [role="tab"]:nth-of-type(3)::before,
    .stTabs [data-baseweb="tab"]:nth-child(3)::before {{
        -webkit-mask-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='black' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpath d='M12.586 2.586A2 2 0 0 0 11.172 2H4a2 2 0 0 0-2 2v7.172a2 2 0 0 0 .586 1.414l8 8a2 2 0 0 0 2.828 0l7.172-7.172a2 2 0 0 0 0-2.828l-8-8z'/%3E%3C/svg%3E");
        mask-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='black' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpath d='M12.586 2.586A2 2 0 0 0 11.172 2H4a2 2 0 0 0-2 2v7.172a2 2 0 0 0 .586 1.414l8 8a2 2 0 0 0 2.828 0l7.172-7.172a2 2 0 0 0 0-2.828l-8-8z'/%3E%3C/svg%3E");
    }}

    .stTabs [role="tab"]:nth-of-type(4)::before,
    .stTabs [data-baseweb="tab"]:nth-child(4)::before {{
        -webkit-mask-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='black' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3E%3Ccircle cx='18' cy='5' r='3'/%3E%3Ccircle cx='6' cy='12' r='3'/%3E%3Ccircle cx='18' cy='19' r='3'/%3E%3Cline x1='8.59' y1='13.51' x2='15.42' y2='17.49'/%3E%3Cline x1='15.41' y1='6.51' x2='8.59' y2='10.49'/%3E%3C/svg%3E");
        mask-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='black' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3E%3Ccircle cx='18' cy='5' r='3'/%3E%3Ccircle cx='6' cy='12' r='3'/%3E%3Ccircle cx='18' cy='19' r='3'/%3E%3Cline x1='8.59' y1='13.51' x2='15.42' y2='17.49'/%3E%3Cline x1='15.41' y1='6.51' x2='8.59' y2='10.49'/%3E%3C/svg%3E");
    }}

    .stTabs [role="tab"]:nth-of-type(5)::before,
    .stTabs [data-baseweb="tab"]:nth-child(5)::before {{
        -webkit-mask-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='black' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3E%3Ccircle cx='18' cy='6' r='3'/%3E%3Ccircle cx='6' cy='18' r='3'/%3E%3Cpath d='M18 9a9 9 0 0 1-9 9'/%3E%3Cline x1='6' y1='6' x2='6' y2='15'/%3E%3C/svg%3E");
        mask-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='black' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3E%3Ccircle cx='18' cy='6' r='3'/%3E%3Ccircle cx='6' cy='18' r='3'/%3E%3Cpath d='M18 9a9 9 0 0 1-9 9'/%3E%3Cline x1='6' y1='6' x2='6' y2='15'/%3E%3C/svg%3E");
    }}

    /* Radio button custom styling - pure indigo dot, zero red */
    div[data-testid="stRadio"] [role="radiogroup"] label {{
        cursor: pointer !important;
        font-size: 13px !important;
        font-weight: 500 !important;
        color: var(--ui-text-secondary) !important;
    }}
    div[data-testid="stRadio"] [role="radiogroup"] label:hover {{
        color: var(--ui-text-primary) !important;
    }}
    div[data-testid="stRadio"] div[role="radiogroup"] > label > div:first-child,
    div[data-testid="stRadio"] input[type="radio"] + div {{
        border-color: var(--ui-border-strong) !important;
        background-color: var(--ui-bg-surface) !important;
        box-shadow: 0 1px 2px rgba(15, 23, 42, 0.04) !important;
    }}
    div[data-testid="stRadio"] div[role="radiogroup"] > label[data-checked="true"] > div:first-child,
    div[data-testid="stRadio"] input[type="radio"]:checked + div {{
        border-color: var(--ui-accent) !important;
        background-color: var(--ui-accent) !important;
    }}
    div[data-testid="stRadio"] div[role="radiogroup"] > label[data-checked="true"] > div:first-child > div,
    div[data-testid="stRadio"] input[type="radio"]:checked + div > div {{
        background-color: #ffffff !important;
    }}

    /* Streamlit Sliders - Indigo Accent */
    div[data-testid="stSlider"] [role="slider"] {{
        background-color: var(--ui-accent) !important;
        border-color: var(--ui-accent) !important;
        box-shadow: 0 0 0 3px var(--ui-accent-subtle) !important;
    }}
    div[data-testid="stSlider"] [data-testid="stThumbValue"] {{
        color: var(--ui-accent) !important;
        font-family: 'JetBrains Mono', Consolas, monospace !important;
        font-weight: 700 !important;
    }}
    div[data-testid="stSlider"] div[data-baseweb="slider"] div:first-child {{
        background-color: var(--ui-accent) !important;
    }}

    /* Inputs, Textareas & Selectboxes */
    input, textarea, [data-baseweb="input"] input, [data-baseweb="select"] {{
        background-color: var(--ui-bg-surface) !important;
        color: var(--ui-text-primary) !important;
        border: 1px solid var(--ui-border-strong) !important;
        border-radius: 8px !important;
        font-size: 13px !important;
        font-family: inherit !important;
        box-shadow: {"none" if is_dark else "0 1px 2px rgba(15, 23, 42, 0.04)"} !important;
        transition: border-color 0.2s ease, box-shadow 0.2s ease !important;
    }}

    input:focus, textarea:focus {{
        border-color: var(--ui-accent) !important;
        box-shadow: 0 0 0 3px var(--ui-accent-subtle) !important;
    }}

    /* Streamlit Buttons */
    .stButton button {{
        background-color: var(--ui-bg-surface) !important;
        color: var(--ui-text-primary) !important;
        border: 1px solid var(--ui-border-strong) !important;
        border-radius: 8px !important;
        font-size: 13px !important;
        font-weight: 600 !important;
        font-family: inherit !important;
        padding: 8px 16px !important;
        box-shadow: {"none" if is_dark else "0 1px 2px rgba(15, 23, 42, 0.05)"} !important;
        transition: all 0.2s cubic-bezier(0.16, 1, 0.3, 1) !important;
    }}

    .stButton button:hover {{
        background-color: var(--ui-bg-hover) !important;
        border-color: var(--ui-accent) !important;
        color: var(--ui-accent) !important;
        transform: translateY(-1px) !important;
        box-shadow: {"0 4px 12px rgba(0, 0, 0, 0.3)" if is_dark else "0 4px 12px rgba(15, 23, 42, 0.08)"} !important;
    }}

    .stButton button[kind="primary"] {{
        background: {"linear-gradient(135deg, #4f46e5 0%, #6366f1 100%)" if is_dark else "linear-gradient(135deg, #4f46e5 0%, #4338ca 100%)"} !important;
        color: #ffffff !important;
        border: 1px solid {"var(--ui-accent)" if is_dark else "#4338ca"} !important;
        font-weight: 600 !important;
        box-shadow: {"0 2px 10px rgba(99, 102, 241, 0.35)" if is_dark else "0 2px 6px rgba(79, 70, 229, 0.25)"} !important;
    }}

    .stButton button[kind="primary"]:hover {{
        background: {"linear-gradient(135deg, #4338ca 0%, #4f46e5 100%)" if is_dark else "linear-gradient(135deg, #4338ca 0%, #3730a3 100%)"} !important;
        transform: translateY(-1px) !important;
        box-shadow: {"0 6px 16px rgba(99, 102, 241, 0.5)" if is_dark else "0 6px 16px rgba(79, 70, 229, 0.35)"} !important;
    }}

    /* Modern App Top Header Bar */
    .app-header-bar {{
        display: flex;
        justify-content: space-between;
        align-items: center;
        flex-wrap: wrap;
        gap: 14px;
        padding: 8px 0 18px 0;
        margin-bottom: 20px;
        border-bottom: 1px solid var(--ui-border-subtle);
    }}

    .app-header-left {{
        display: flex;
        align-items: center;
        gap: 12px;
        flex-wrap: wrap;
    }}

    .app-header-right {{
        font-size: 12px;
        color: var(--ui-text-muted);
        display: flex;
        align-items: center;
        gap: 8px;
    }}

    .app-brand-title {{
        font-size: 18px;
        font-weight: 800;
        color: var(--ui-text-primary);
        letter-spacing: -0.03em;
        margin: 0;
        display: flex;
        align-items: center;
        gap: 8px;
    }}

    .app-logo-badge {{
        display: inline-flex;
        align-items: center;
        justify-content: center;
        width: 30px;
        height: 30px;
        border-radius: 8px;
        background: {"rgba(255, 255, 255, 0.08)" if is_dark else "#0f172a"};
        border: 1px solid {"rgba(255, 255, 255, 0.14)" if is_dark else "#1e293b"};
        box-shadow: {"0 2px 6px rgba(0, 0, 0, 0.3)" if is_dark else "0 2px 6px rgba(15, 23, 42, 0.18)"};
        color: #ffffff !important;
        flex-shrink: 0;
    }}

    .app-repo-badge {{
        display: inline-flex;
        align-items: center;
        font-family: "JetBrains Mono", Consolas, monospace;
        font-size: 11.5px;
        padding: 4px 11px;
        border-radius: 7px;
        background-color: var(--ui-bg-surface);
        color: var(--ui-text-primary);
        border: 1px solid var(--ui-border-strong);
        box-shadow: {"none" if is_dark else "0 1px 2px rgba(15, 23, 42, 0.04)"};
    }}

    .live-pulse-dot {{
        width: 8px;
        height: 8px;
        border-radius: 50%;
        background-color: #10b981;
        box-shadow: 0 0 0 2px rgba(16, 185, 129, 0.2);
        animation: pulse 2s infinite;
        display: inline-block;
    }}

    @keyframes pulse {{
        0% {{ box-shadow: 0 0 0 0 rgba(16, 185, 129, 0.4); }}
        70% {{ box-shadow: 0 0 0 6px rgba(16, 185, 129, 0); }}
        100% {{ box-shadow: 0 0 0 0 rgba(16, 185, 129, 0); }}
    }}

    /* Card Panels & Containers */
    .ui-panel {{
        background-color: var(--ui-bg-surface);
        border: 1px solid var(--ui-border-subtle);
        border-radius: 12px;
        padding: 24px;
        margin-bottom: 18px;
        box-shadow: {"0 2px 10px rgba(0, 0, 0, 0.2)" if is_dark else "0 1px 3px rgba(15, 23, 42, 0.05), 0 4px 12px -2px rgba(15, 23, 42, 0.04)"};
    }}

    /* Modern KPI Metric Grid */
    .metric-grid {{
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(210px, 1fr));
        gap: 14px;
        margin-bottom: 24px;
    }}

    .ui-metric-tile {{
        position: relative;
        background-color: var(--ui-bg-surface);
        border: 1px solid var(--ui-border-subtle);
        border-radius: 12px;
        padding: 18px 20px;
        transition: all 0.2s cubic-bezier(0.16, 1, 0.3, 1);
        overflow: hidden;
        box-shadow: {"0 2px 8px rgba(0, 0, 0, 0.25)" if is_dark else "0 1px 3px rgba(15, 23, 42, 0.04), 0 3px 8px -1px rgba(15, 23, 42, 0.03)"};
    }}

    .ui-metric-tile:hover {{
        transform: translateY(-2px);
        border-color: var(--ui-accent-border);
        box-shadow: {"0 8px 24px -4px rgba(0, 0, 0, 0.4)" if is_dark else "0 8px 20px -4px rgba(15, 23, 42, 0.09), 0 2px 6px -1px rgba(15, 23, 42, 0.04)"};
    }}

    .metric-icon-well {{
        display: inline-flex;
        align-items: center;
        justify-content: center;
        width: 28px;
        height: 28px;
        border-radius: 7px;
        background-color: {"rgba(255, 255, 255, 0.05)" if is_dark else "#f1f5f9"};
        border: 1px solid var(--ui-border-subtle);
        flex-shrink: 0;
    }}

    .ui-metric-label {{
        font-size: 11.5px;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        color: var(--ui-text-muted);
        margin-bottom: 8px;
        display: flex;
        align-items: center;
        justify-content: space-between;
    }}

    .ui-metric-value {{
        font-size: 28px;
        font-weight: 800;
        font-family: 'Plus Jakarta Sans', sans-serif;
        color: var(--ui-text-primary);
        letter-spacing: -0.03em;
        line-height: 1.15;
    }}

    .ui-metric-subtext {{
        font-size: 12px;
        color: var(--ui-text-secondary);
        margin-top: 5px;
    }}

    /* Streamlit DataFrame Container */
    [data-testid="stDataFrame"] {{
        border: 1px solid var(--ui-border-subtle) !important;
        border-radius: 10px !important;
        overflow: hidden !important;
        box-shadow: {"0 2px 8px rgba(0, 0, 0, 0.2)" if is_dark else "0 1px 3px rgba(15, 23, 42, 0.04)"} !important;
        background-color: var(--ui-bg-surface) !important;
    }}

    /* Badges & Tags */
    .ui-tag {{
        display: inline-flex;
        align-items: center;
        gap: 5px;
        padding: 4px 10px;
        border-radius: 6px;
        font-size: 11.5px;
        font-weight: 600;
        font-family: "JetBrains Mono", Consolas, monospace;
        letter-spacing: 0.01em;
        white-space: nowrap;
    }}

    .app-header-right .ui-tag {{
        background-color: var(--ui-bg-surface) !important;
        border: 1px solid var(--ui-border-strong) !important;
        color: var(--ui-text-secondary) !important;
        box-shadow: {"0 1px 2px rgba(0, 0, 0, 0.2)" if is_dark else "0 1px 2px rgba(15, 23, 42, 0.04)"} !important;
    }}

    /* Horizontal Probability Bar Component */
    .prob-bar-container {{
        display: flex;
        align-items: center;
        gap: 10px;
        margin: 4px 0;
    }}

    .prob-bar-label {{
        width: 140px;
        font-size: 12px;
        font-weight: 500;
        color: var(--ui-text-secondary);
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
    }}

    .prob-bar-track {{
        flex-grow: 1;
        height: 7px;
        background-color: var(--ui-bg-elevated);
        border-radius: 4px;
        overflow: hidden;
    }}

    .prob-bar-fill {{
        height: 100%;
        border-radius: 4px;
        transition: width 0.4s ease;
    }}

    .prob-bar-value {{
        width: 45px;
        text-align: right;
        font-size: 11.5px;
        font-family: "JetBrains Mono", monospace;
        font-weight: 600;
        color: var(--ui-text-primary);
    }}

    /* Code Container & Obsidian Highlights */
    .obsidian-code-wrapper {{
        margin: 14px 0 18px 0;
        border: 1px solid var(--ui-code-border);
        border-radius: 8px;
        background-color: var(--ui-code-bg);
        overflow: hidden;
        box-shadow: 0 4px 16px -2px {"rgba(0, 0, 0, 0.3)" if is_dark else "rgba(0, 0, 0, 0.04)"};
    }}

    .obsidian-code-header {{
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 7px 14px;
        background-color: var(--ui-code-header-bg);
        border-bottom: 1px solid var(--ui-code-border);
        font-family: "JetBrains Mono", Consolas, monospace;
        font-size: 11.5px;
        color: var(--ui-text-muted);
    }}

    .obsidian-code-lang {{
        font-weight: 700;
        letter-spacing: 0.06em;
        color: var(--ui-accent);
    }}

    .obsidian-code-lines {{
        padding: 10px 0;
        overflow-x: auto;
        background-color: var(--ui-code-bg);
    }}

    .code-line {{
        display: flex !important;
        flex-direction: row !important;
        align-items: baseline !important;
        min-height: 1.5rem !important;
        line-height: 1.6 !important;
        padding: 0 14px !important;
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
        font-family: "JetBrains Mono", "Fira Code", Consolas, monospace !important;
        font-size: 12.5px !important;
        color: var(--ui-code-text) !important;
    }}

    /* Query Match Highlight */
    mark.query-match {{
        background-color: {t["query_hit_bg"]};
        color: {t["query_hit_text"]};
        padding: 2px 4px;
        border-radius: 4px;
        font-weight: 700;
    }}

    /* Pygments Token Color Styles */
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

    /* Streamlit Expander Styling */
    [data-testid="stExpander"] {{
        background-color: var(--ui-bg-surface) !important;
        border: 1px solid var(--ui-border-subtle) !important;
        border-radius: 8px !important;
        margin-bottom: 10px !important;
        transition: border-color 0.2s ease !important;
    }}

    [data-testid="stExpander"]:hover {{
        border-color: var(--ui-border-strong) !important;
    }}

    [data-testid="stExpander"] summary {{
        font-size: 13.5px !important;
        font-weight: 600 !important;
        color: var(--ui-text-primary) !important;
        padding: 10px 16px !important;
    }}

    /* Modern Scrollbars */
    ::-webkit-scrollbar {{
        width: 8px;
        height: 8px;
    }}
    ::-webkit-scrollbar-track {{
        background: var(--ui-bg-base);
    }}
    ::-webkit-scrollbar-thumb {{
        background: var(--ui-border-strong);
        border-radius: 4px;
    }}
    ::-webkit-scrollbar-thumb:hover {{
        background: var(--ui-text-muted);
    }}
</style>
"""


def highlight_terms_in_html(html_str: str, query: Optional[str]) -> str:
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
            location_parts.append(f": {line_start}–{line_end}")
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
    mode = "dark" if is_dark else "light"
    styles = CATEGORY_STYLES[mode].get(
        category,
        {"bg": "rgba(148, 163, 184, 0.15)", "border": "rgba(148, 163, 184, 0.3)", "text": "#94a3b8", "dot": "#64748b"}
    )
    
    conf_str = f" · {int(confidence * 100)}%" if confidence is not None else ""
    return (
        f'<span class="ui-tag" style="background-color: {styles["bg"]}; '
        f'border: 1px solid {styles["border"]}; color: {styles["text"]};">'
        f'<span style="width: 6px; height: 6px; border-radius: 50%; background-color: {styles["dot"]};"></span>'
        f'{html.escape(category)}{conf_str}</span>'
    )


def render_probability_bars(probabilities: Dict[str, float], is_dark: bool = False) -> str:
    mode = "dark" if is_dark else "light"
    rendered_bars = []
    sorted_probs = sorted(probabilities.items(), key=lambda x: x[1], reverse=True)

    for cat, prob in sorted_probs:
        pct = max(0, min(100, int(prob * 100)))
        styles = CATEGORY_STYLES[mode].get(cat, {"dot": "#6366f1"})
        color = styles["dot"]
        rendered_bars.append(f"""
        <div class="prob-bar-container">
            <span class="prob-bar-label" title="{html.escape(cat)}">{html.escape(cat)}</span>
            <div class="prob-bar-track">
                <div class="prob-bar-fill" style="width: {pct}%; background-color: {color};"></div>
            </div>
            <span class="prob-bar-value">{pct}%</span>
        </div>
        """)

    return "".join(rendered_bars)


def get_svg_icon(name: str, size: int = 16, color: str = "currentColor", stroke_width: float = 1.8) -> str:
    """Returns clean, minimalist inline SVG icons for UI elements and branding."""
    icons = {
        "logo": (
            f'<svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" '
            f'stroke="{color}" stroke-width="{stroke_width}" stroke-linecap="round" stroke-linejoin="round" '
            f'style="display: inline-block; vertical-align: middle;">'
            '<polygon points="12 2 2 7 12 12 22 7 12 2"></polygon>'
            '<polyline points="2 17 12 22 22 17"></polyline>'
            '<polyline points="2 12 12 17 22 12"></polyline>'
            '</svg>'
        ),
        "brand": (
            f'<svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" '
            f'stroke="{color}" stroke-width="{stroke_width}" stroke-linecap="round" stroke-linejoin="round" '
            f'style="display: inline-block; vertical-align: middle;">'
            '<polygon points="12 2 2 7 12 12 22 7 12 2"></polygon>'
            '<polyline points="2 17 12 22 22 17"></polyline>'
            '<polyline points="2 12 12 17 22 12"></polyline>'
            '</svg>'
        ),
        "overview": (
            f'<svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" '
            f'stroke="{color}" stroke-width="{stroke_width}" stroke-linecap="round" stroke-linejoin="round" '
            f'style="display: inline-block; vertical-align: middle;">'
            '<rect width="7" height="9" x="3" y="3" rx="1.5"/>'
            '<rect width="7" height="5" x="14" y="3" rx="1.5"/>'
            '<rect width="7" height="9" x="14" y="12" rx="1.5"/>'
            '<rect width="7" height="5" x="3" y="16" rx="1.5"/>'
            '</svg>'
        ),
        "search": (
            f'<svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" '
            f'stroke="{color}" stroke-width="{stroke_width}" stroke-linecap="round" stroke-linejoin="round" '
            f'style="display: inline-block; vertical-align: middle;">'
            '<circle cx="11" cy="11" r="7.5"/>'
            '<path d="m21 21-4.35-4.35"/>'
            '</svg>'
        ),
        "classifier": (
            f'<svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" '
            f'stroke="{color}" stroke-width="{stroke_width}" stroke-linecap="round" stroke-linejoin="round" '
            f'style="display: inline-block; vertical-align: middle;">'
            '<path d="M12.586 2.586A2 2 0 0 0 11.172 2H4a2 2 0 0 0-2 2v7.172a2 2 0 0 0 .586 1.414l8 8a2 2 0 0 0 2.828 0l7.172-7.172a2 2 0 0 0 0-2.828l-8-8z"/>'
            '</svg>'
        ),
        "clustering": (
            f'<svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" '
            f'stroke="{color}" stroke-width="{stroke_width}" stroke-linecap="round" stroke-linejoin="round" '
            f'style="display: inline-block; vertical-align: middle;">'
            '<circle cx="18" cy="5" r="3"/>'
            '<circle cx="6" cy="12" r="3"/>'
            '<circle cx="18" cy="19" r="3"/>'
            '<line x1="8.6" y1="13.5" x2="15.4" y2="17.5"/>'
            '<line x1="15.4" y1="6.5" x2="8.6" y2="10.5"/>'
            '</svg>'
        ),
        "dependencies": (
            f'<svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" '
            f'stroke="{color}" stroke-width="{stroke_width}" stroke-linecap="round" stroke-linejoin="round" '
            f'style="display: inline-block; vertical-align: middle;">'
            '<circle cx="18" cy="6" r="3"/>'
            '<circle cx="6" cy="18" r="3"/>'
            '<path d="M18 9a9 9 0 0 1-9 9"/>'
            '<line x1="6" y1="6" x2="6" y2="15"/>'
            '</svg>'
        ),
        "file": (
            f'<svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" '
            f'stroke="{color}" stroke-width="{stroke_width}" stroke-linecap="round" stroke-linejoin="round" '
            f'style="display: inline-block; vertical-align: middle;">'
            '<path d="M15 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7Z"/>'
            '<path d="M14 2v4a2 2 0 0 0 2 2h4"/>'
            '</svg>'
        ),
        "code": (
            f'<svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" '
            f'stroke="{color}" stroke-width="{stroke_width}" stroke-linecap="round" stroke-linejoin="round" '
            f'style="display: inline-block; vertical-align: middle;">'
            '<polyline points="16 18 22 12 16 6"/>'
            '<polyline points="8 6 2 12 8 18"/>'
            '</svg>'
        ),
        "function": (
            f'<svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" '
            f'stroke="{color}" stroke-width="{stroke_width}" stroke-linecap="round" stroke-linejoin="round" '
            f'style="display: inline-block; vertical-align: middle;">'
            '<path d="m9 9 3 3-3 3"/>'
            '<line x1="14" y1="15" x2="16" y2="15"/>'
            '</svg>'
        ),
        "box": (
            f'<svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" '
            f'stroke="{color}" stroke-width="{stroke_width}" stroke-linecap="round" stroke-linejoin="round" '
            f'style="display: inline-block; vertical-align: middle;">'
            '<path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z"/>'
            '<polyline points="3.29 7 12 12 20.71 7"/>'
            '<line x1="12" y1="22" x2="12" y2="12"/>'
            '</svg>'
        ),
        "shield": (
            f'<svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" '
            f'stroke="{color}" stroke-width="{stroke_width}" stroke-linecap="round" stroke-linejoin="round" '
            f'style="display: inline-block; vertical-align: middle;">'
            '<path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>'
            '<path d="m9 12 2 2 4-4"/>'
            '</svg>'
        ),
        "link": (
            f'<svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" '
            f'stroke="{color}" stroke-width="{stroke_width}" stroke-linecap="round" stroke-linejoin="round" '
            f'style="display: inline-block; vertical-align: middle;">'
            '<path d="M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.71"/>'
            '<path d="M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.71-1.71"/>'
            '</svg>'
        ),
        "cycle": (
            f'<svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" '
            f'stroke="{color}" stroke-width="{stroke_width}" stroke-linecap="round" stroke-linejoin="round" '
            f'style="display: inline-block; vertical-align: middle;">'
            '<path d="M21 12a9 9 0 0 0-9-9 9.75 9.75 0 0 0-6.74 2.74L3 8"/>'
            '<path d="M3 3v5h5"/>'
            '<path d="M3 12a9 9 0 0 0 9 9 9.75 9.75 0 0 0 6.74-2.74L21 16"/>'
            '<path d="M16 16h5v5"/>'
            '</svg>'
        ),
        "isolated": (
            f'<svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" '
            f'stroke="{color}" stroke-width="{stroke_width}" stroke-linecap="round" stroke-linejoin="round" '
            f'style="display: inline-block; vertical-align: middle;">'
            '<circle cx="12" cy="12" r="3"/>'
            '<circle cx="12" cy="12" r="8" stroke-dasharray="2 2"/>'
            '</svg>'
        ),
    }
    return icons.get(name, "")
