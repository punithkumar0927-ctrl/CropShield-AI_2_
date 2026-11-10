"""ASGI entrypoint Vercel loads. Local development still uses ``streamlit run app.py``."""

from pathlib import Path

import streamlit as st

app = st.App(Path(__file__).resolve().parent / "app.py")
