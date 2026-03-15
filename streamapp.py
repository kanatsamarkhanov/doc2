# ╔══════════════════════════════════════════════════════════════════════════════╗
# ║          ArticleAI — SaaS Research Writing Platform                        ║
# ║          Streamlit · python-docx · Multilingual EN/RU/KZ                  ║
# ╚══════════════════════════════════════════════════════════════════════════════╝

import streamlit as st
import re
import json
import io
from datetime import datetime
from io import BytesIO

st.set_page_config(
    page_title="ArticleAI — Research Writing Platform",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ─────────────────────────────────────────────────────────────────────────────
# OPTIONAL DEPENDENCIES
# ─────────────────────────────────────────────────────────────────────────────
try:
    from docx import Document
    from docx.shared import Pt, Inches, RGBColor
    from docx.enum.text import WD_ALIGN_PARAGRAPH
    DOCX_OK = True
except ImportError:
    DOCX_OK = False

try:
    import pandas as pd
    PANDAS_OK = True
except ImportError:
    PANDAS_OK = False

# ─────────────────────────────────────────────────────────────────────────────
# TRANSLATIONS  (EN / RU / KZ)
# ─────────────────────────────────────────────────────────────────────────────
TR = {
    "🇬🇧 English": {
        "app_title": "ArticleAI", "tagline": "Research Writing Platform",
        "login_title": "Sign In", "username": "Username", "password": "Password",
        "login_btn": "Sign In →", "login_err": "Invalid credentials. Try: admin / admin123",
        "nav_info": "📄 Article Info", "nav_sections": "✍️ Sections",
        "nav_figures": "🖼️ Figures & Tables", "nav_refs": "📑 References",
        "nav_generate": "🚀 Generate", "nav_settings": "⚙️ Settings",
        "logout": "Logout",
        "step": "Step", "of": "of",
        "art_title": "Article Title", "authors": "Authors",
        "affiliation": "Affiliation", "journal": "Target Journal",
        "keywords": "Keywords", "abstract": "Abstract",
        "art_type": "Article Type",
        "intro": "Introduction", "methods": "Methods",
        "results": "Results", "discussion": "Discussion", "conclusion": "Conclusion",
        "upload_docx": "Upload DOCX / TXT",
        "fig_mgr": "Figures & Tables Manager",
        "add_fig": "Add Figure", "fig_caption": "Figure Caption",
        "fig_num": "Figure No.", "upload_fig": "Upload Figure (PNG/JPG/TIF)",
        "add_tbl": "Add Table", "tbl_caption": "Table Caption",
        "tbl_num": "Table No.", "tbl_data": "Table data (CSV format)",
        "ref_mgr": "References Manager", "add_ref": "Add Reference",
        "ref_type": "Type", "ref_authors": "Authors", "ref_year": "Year",
        "ref_title_f": "Title", "ref_journal": "Journal / Publisher",
        "ref_vol": "Volume", "ref_pages": "Pages", "ref_doi": "DOI",
        "import_refs": "Import BibTeX / plain text",
        "generate": "Generate Article",
        "dl_docx": "📥 Download DOCX", "dl_md": "📥 Download Markdown",
        "save_json": "💾 Save Project (JSON)", "load_json": "📂 Load Project (JSON)",
        "w_words": "Words", "w_secs": "Sections", "w_figs": "Figures",
        "w_tbls": "Tables", "w_refs": "References",
        "stats": "📊 Article Stats", "settings": "Settings",
        "theme": "Theme", "lang": "Language", "cite_style": "Citation Style",
        "success_gen": "✅ Article generated!", "warn_title": "⚠️ Please add an article title first.",
        "preview": "📄 Article Preview", "sec_editor": "✍️ Section Editor",
        "word_count": "Word count", "add_btn":
