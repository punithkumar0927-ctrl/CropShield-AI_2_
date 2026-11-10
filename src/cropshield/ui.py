"""Shared motion and color treatment for the CropShield pages."""

from __future__ import annotations

import base64
import html
from pathlib import Path

import streamlit as st

from .translations import LANGUAGES, translate

_CSS = """
<style>
@keyframes cs-rise {
    from { opacity: 0; transform: translateY(18px); }
    to { opacity: 1; transform: translateY(0); }
}
@keyframes cs-drift {
    0% { transform: translateY(0) rotate(0deg); }
    50% { transform: translateY(14px) rotate(8deg); }
    100% { transform: translateY(0) rotate(0deg); }
}
.cs-hero {
    position: relative;
    overflow: hidden;
    margin: 0 0 1.1rem 0;
    padding: 1.35rem 7.5rem 1.2rem 1.5rem;
    border-radius: 22px;
    border: 1px solid rgba(22, 101, 52, 0.18);
    background: linear-gradient(120deg, rgba(255,255,255,0.82), rgba(236,253,245,0.72) 45%, rgba(254,249,195,0.55));
    box-shadow: 0 18px 40px rgba(22, 101, 52, 0.12);
    animation: cs-rise 0.7s ease both;
}
.cs-kicker {
    margin: 0 0 0.35rem 0;
    letter-spacing: 0.16em;
    text-transform: uppercase;
    font-size: 0.78rem;
    font-weight: 700;
    color: #166534;
}
.cs-lead {
    margin: 0;
    max-width: 40rem;
    font-size: 1.35rem;
    line-height: 1.35;
    font-weight: 650;
    color: #14532d;
}
.cs-leaf {
    position: absolute;
    top: 0.4rem;
    font-size: 1.4rem;
    opacity: 0.72;
    pointer-events: none;
    animation: cs-drift 5.5s ease-in-out infinite;
}
[data-testid="stHeading"] h1,
[data-testid="stHeading"] h1 span,
[data-testid="stSidebar"] h1,
[data-testid="stSidebar"] h1 span {
    color: #14532d !important;
    letter-spacing: -0.03em;
}
[data-testid="stHeading"] h2,
[data-testid="stHeading"] h2 span,
[data-testid="stHeading"] h3,
[data-testid="stHeading"] h3 span {
    color: #166534 !important;
}
[data-testid="stHeading"] {
    animation: cs-rise 0.65s ease both;
}
div[data-testid="stMetric"] {
    background: rgba(255, 255, 255, 0.92);
    border: 1px solid rgba(22, 101, 52, 0.16);
    padding: 16px;
    border-radius: 18px;
    box-shadow: 0 8px 18px rgba(22, 101, 52, 0.06);
    animation: cs-rise 0.8s ease both;
    transition: transform 0.25s ease, box-shadow 0.25s ease;
}
div[data-testid="stMetric"]:hover {
    transform: translateY(-6px);
    box-shadow: 0 18px 32px rgba(22, 101, 52, 0.16);
}
div[data-testid="stMetric"]:nth-of-type(2) { animation-delay: 0.08s; }
div[data-testid="stMetric"]:nth-of-type(3) { animation-delay: 0.16s; }
div[data-testid="stMetric"]:nth-of-type(4) { animation-delay: 0.24s; }
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #f3faf1 0%, #e7f5e4 100%);
    border-right: 1px solid rgba(22, 101, 52, 0.12);
}
[data-testid="stSidebar"] a {
    border-radius: 10px;
    transition: background 0.2s ease, transform 0.2s ease;
}
[data-testid="stSidebar"] a:hover {
    transform: translateX(4px);
}
.stButton > button, .stDownloadButton > button, .stPageLink a {
    border-radius: 999px;
    transition: transform 0.22s ease, box-shadow 0.22s ease;
}
.stButton > button:hover, .stDownloadButton > button:hover, .stPageLink a:hover {
    transform: translateY(-3px);
    box-shadow: 0 10px 22px rgba(22, 101, 52, 0.18);
}
div[data-testid="stAlert"], div[data-testid="stCaptionContainer"], .stPageLink {
    animation: cs-rise 0.75s ease both;
}
.cs-chip {
    display: inline-block;
    margin: 6px;
    padding: 8px 14px;
    border-radius: 999px;
    background: rgba(255,255,255,0.92);
    border: 1px solid rgba(22, 101, 52, 0.2);
    color: #166534;
    font-weight: 700;
    font-size: 0.9rem;
    animation: cs-rise 0.6s ease both;
    transition: transform 0.2s ease, box-shadow 0.2s ease;
}
.cs-chip:hover {
    transform: translateY(-3px) scale(1.04);
    box-shadow: 0 10px 18px rgba(22, 101, 52, 0.14);
}
p, li, label { color: #17231B; }
[data-testid="stHeader"] { background: rgba(247, 250, 245, 0.72); }
@media (prefers-reduced-motion: reduce) {
    .cs-hero, .cs-leaf, [data-testid="stHeading"], div[data-testid="stMetric"],
    .stButton > button, div[data-testid="stAlert"], .stPageLink, .cs-chip {
        animation: none !important;
        transition: none !important;
    }
}
@media (max-width: 640px) {
    .cs-hero { padding: 1rem; border-radius: 16px; }
    .cs-lead { font-size: 1.12rem; }
    div[data-testid="stMetric"] { padding: 12px; }
}
</style>
"""


def inject_theme(*, home: bool = False) -> None:
    """Apply the field photograph and animated theme on every page."""
    del home
    background_css = ""
    background_path = Path(__file__).resolve().parents[2] / "assets" / "homepage_background.jpg"
    if background_path.is_file():
        encoded = base64.b64encode(background_path.read_bytes()).decode("ascii")
        background_css = f"""
        <style>
        .stApp {{
            background-color: #F7FAF5;
            background-image:
                linear-gradient(rgba(247,250,245,0.62), rgba(247,250,245,0.84)),
                url('data:image/jpeg;base64,{encoded}');
            background-size: cover;
            background-position: center;
            background-attachment: fixed;
        }}
        </style>
        """
    st.markdown(background_css + _CSS, unsafe_allow_html=True)


def render_home_hero() -> None:
    """Render the compact, localized home-page hero."""
    language = get_selected_language()
    st.markdown(
        f"""
        <section class="cs-hero">
            <span class="cs-leaf" style="right:8%;animation-delay:0s;">🌿</span>
            <p class="cs-kicker">{html.escape(translate("app_title", language))}</p>
            <p class="cs-lead">{html.escape(translate("subtitle", language))}</p>
            <p>{html.escape(translate("description", language))}</p>
        </section>
        """,
        unsafe_allow_html=True,
    )


def get_selected_language() -> str:
    """Return the active UI language, defaulting to English."""
    selected = st.session_state.get("cropshield_language", "en")
    return selected if selected in LANGUAGES else "en"


def render_language_selector() -> None:
    """Render the shared sidebar language selector."""
    language = get_selected_language()
    st.sidebar.selectbox(
        translate("language", language),
        options=list(LANGUAGES),
        format_func=lambda code: LANGUAGES[code],
        key="cropshield_language",
    )
