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
        "word_count": "Word count", "add_btn": "Add", "del_btn": "Delete",
        "ref_list": "Reference List", "no_refs": "No references yet.",
        "no_figs": "No figures yet.", "no_tbls": "No tables yet.",
        "welcome": "Welcome back", "downloading": "Preparing document…",
        "completeness": "Article Completeness",
        "art_types": ["Research Article", "Review Article", "Short Communication",
                      "Letter", "Case Study"],
        "ref_types_list": ["Journal Article", "Book", "Book Chapter",
                           "Conference Paper", "Website", "Thesis"],
        "cite_styles": ["APA 7th", "Vancouver", "Harvard", "IEEE", "Chicago"],
        "themes": ["🌙 Dark", "☀️ Light"],
        "jrn_ph": "e.g. Remote Sensing, Catena, Journal of Hydrology",
        "kw_ph":  "e.g. GIS, remote sensing, hydrology",
        "reset": "Reset all data", "reset_ok": "✅ All data cleared.",
        "import_btn": "Import", "imported": "Imported",
        "ref_s": "reference(s)", "loaded": "✅ Project loaded!",
    },
    "🇷🇺 Русский": {
        "app_title": "ArticleAI", "tagline": "Платформа написания статей",
        "login_title": "Вход", "username": "Логин", "password": "Пароль",
        "login_btn": "Войти →", "login_err": "Ошибка. Попробуйте: admin / admin123",
        "nav_info": "📄 Информация", "nav_sections": "✍️ Разделы",
        "nav_figures": "🖼️ Рисунки и таблицы", "nav_refs": "📑 Литература",
        "nav_generate": "🚀 Генерация", "nav_settings": "⚙️ Настройки",
        "logout": "Выйти",
        "step": "Шаг", "of": "из",
        "art_title": "Название статьи", "authors": "Авторы",
        "affiliation": "Аффилиация", "journal": "Целевой журнал",
        "keywords": "Ключевые слова", "abstract": "Аннотация",
        "art_type": "Тип статьи",
        "intro": "Введение", "methods": "Методы",
        "results": "Результаты", "discussion": "Обсуждение", "conclusion": "Заключение",
        "upload_docx": "Загрузить DOCX / TXT",
        "fig_mgr": "Менеджер рисунков и таблиц",
        "add_fig": "Добавить рисунок", "fig_caption": "Подпись к рисунку",
        "fig_num": "№ рисунка", "upload_fig": "Загрузить рисунок (PNG/JPG)",
        "add_tbl": "Добавить таблицу", "tbl_caption": "Заголовок таблицы",
        "tbl_num": "№ таблицы", "tbl_data": "Данные таблицы (CSV)",
        "ref_mgr": "Менеджер литературы", "add_ref": "Добавить источник",
        "ref_type": "Тип", "ref_authors": "Авторы", "ref_year": "Год",
        "ref_title_f": "Название", "ref_journal": "Журнал / Издательство",
        "ref_vol": "Том", "ref_pages": "Страницы", "ref_doi": "DOI",
        "import_refs": "Импорт BibTeX / текст",
        "generate": "Генерировать статью",
        "dl_docx": "📥 Скачать DOCX", "dl_md": "📥 Скачать Markdown",
        "save_json": "💾 Сохранить проект (JSON)", "load_json": "📂 Загрузить проект (JSON)",
        "w_words": "Слов", "w_secs": "Разделов", "w_figs": "Рисунков",
        "w_tbls": "Таблиц", "w_refs": "Источников",
        "stats": "📊 Статистика статьи", "settings": "Настройки",
        "theme": "Тема", "lang": "Язык", "cite_style": "Стиль цитирования",
        "success_gen": "✅ Статья сгенерирована!", "warn_title": "⚠️ Введите название статьи.",
        "preview": "📄 Предпросмотр", "sec_editor": "✍️ Редактор разделов",
        "word_count": "Количество слов", "add_btn": "Добавить", "del_btn": "Удалить",
        "ref_list": "Список литературы", "no_refs": "Источники не добавлены.",
        "no_figs": "Рисунки не добавлены.", "no_tbls": "Таблицы не добавлены.",
        "welcome": "Добро пожаловать", "downloading": "Подготовка документа…",
        "completeness": "Заполненность статьи",
        "art_types": ["Научная статья", "Обзорная статья", "Краткое сообщение",
                      "Письмо", "Кейс-стади"],
        "ref_types_list": ["Журнальная статья", "Книга", "Глава книги",
                           "Материалы конференции", "Сайт", "Диссертация"],
        "cite_styles": ["APA 7th", "Ванкувер", "Гарвард", "IEEE", "Чикаго"],
        "themes": ["🌙 Тёмная", "☀️ Светлая"],
        "jrn_ph": "напр., Remote Sensing, Catena, Гидрология",
        "kw_ph":  "напр., ГИС, дистанционное зондирование, гидрология",
        "reset": "Очистить все данные", "reset_ok": "✅ Данные очищены.",
        "import_btn": "Импорт", "imported": "Импортировано",
        "ref_s": "источник(ов)", "loaded": "✅ Проект загружен!",
    },
    "🇰🇿 Қазақша": {
        "app_title": "ArticleAI", "tagline": "Ғылыми мақала жазу платформасы",
        "login_title": "Жүйеге кіру", "username": "Пайдаланушы аты", "password": "Құпия сөз",
        "login_btn": "Кіру →", "login_err": "Қате. admin / admin123 қолданыңыз",
        "nav_info": "📄 Мақала туралы", "nav_sections": "✍️ Бөлімдер",
        "nav_figures": "🖼️ Суреттер мен кестелер", "nav_refs": "📑 Әдебиеттер",
        "nav_generate": "🚀 Генерация", "nav_settings": "⚙️ Параметрлер",
        "logout": "Шығу",
        "step": "Қадам", "of": "/",
        "art_title": "Мақала атауы", "authors": "Авторлар",
        "affiliation": "Аффилиация", "journal": "Мақсатты журнал",
        "keywords": "Кілт сөздер", "abstract": "Аннотация",
        "art_type": "Мақала түрі",
        "intro": "Кіріспе", "methods": "Әдістер",
        "results": "Нәтижелер", "discussion": "Талқылау", "conclusion": "Қорытынды",
        "upload_docx": "DOCX / TXT жүктеу",
        "fig_mgr": "Суреттер мен кестелер менеджері",
        "add_fig": "Сурет қосу", "fig_caption": "Сурет аңызы",
        "fig_num": "Сурет №", "upload_fig": "Сурет жүктеу (PNG/JPG)",
        "add_tbl": "Кесте қосу", "tbl_caption": "Кесте тақырыбы",
        "tbl_num": "Кесте №", "tbl_data": "Кесте деректері (CSV)",
        "ref_mgr": "Әдебиеттер менеджері", "add_ref": "Дереккөз қосу",
        "ref_type": "Түрі", "ref_authors": "Авторлар", "ref_year": "Жыл",
        "ref_title_f": "Атауы", "ref_journal": "Журнал / Баспа",
        "ref_vol": "Том", "ref_pages": "Беттер", "ref_doi": "DOI",
        "import_refs": "BibTeX / мәтін импорты",
        "generate": "Мақала генерациялау",
        "dl_docx": "📥 DOCX жүктеу", "dl_md": "📥 Markdown жүктеу",
        "save_json": "💾 Жобаны сақтау (JSON)", "load_json": "📂 Жобаны жүктеу (JSON)",
        "w_words": "Сөздер", "w_secs": "Бөлімдер", "w_figs": "Суреттер",
        "w_tbls": "Кестелер", "w_refs": "Дереккөздер",
        "stats": "📊 Мақала статистикасы", "settings": "Параметрлер",
        "theme": "Тақырып", "lang": "Тіл", "cite_style": "Цитата стилі",
        "success_gen": "✅ Мақала сәтті жасалды!", "warn_title": "⚠️ Мақала атауын енгізіңіз.",
        "preview": "📄 Алдын ала қарау", "sec_editor": "✍️ Бөлім редакторы",
        "word_count": "Сөз саны", "add_btn": "Қосу", "del_btn": "Жою",
        "ref_list": "Әдебиеттер тізімі", "no_refs": "Дереккөздер қосылмаған.",
        "no_figs": "Суреттер қосылмаған.", "no_tbls": "Кестелер қосылмаған.",
        "welcome": "Қош келдіңіз", "downloading": "Құжат дайындалуда…",
        "completeness": "Мақала толықтығы",
        "art_types": ["Ғылыми мақала", "Шолу мақаласы", "Қысқа хабарлама",
                      "Хат", "Кейс-стади"],
        "ref_types_list": ["Журнал мақаласы", "Кітап", "Кітап тарауы",
                           "Конференция баяндамасы", "Веб-сайт", "Диссертация"],
        "cite_styles": ["APA 7th", "Ванкувер", "Гарвард", "IEEE", "Чикаго"],
        "themes": ["🌙 Күңгірт", "☀️ Жарық"],
        "jrn_ph": "мыс., Remote Sensing, Catena",
        "kw_ph":  "мыс., ГАЖ, қашықтықтан зондтау",
        "reset": "Барлық деректерді тазалау", "reset_ok": "✅ Деректер тазаланды.",
        "import_btn": "Импорт", "imported": "Импортталды",
        "ref_s": "дереккөз(дер)", "loaded": "✅ Жоба жүктелді!",
    },
}

USERS = {
    "admin": {"password": "admin123", "name": "Kanat Samarkhanov", "role": "Researcher"},
    "demo":  {"password": "demo2024", "name": "Demo User",          "role": "Student"},
}

# ─────────────────────────────────────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────────────────────────────────────
def t(key: str) -> str:
    lang = st.session_state.get("lang", "🇬🇧 English")
    return TR.get(lang, TR["🇬🇧 English"]).get(key, key)

def wc(text: str) -> int:
    return len(re.findall(r"\w+", text)) if text else 0

def nav_steps():
    return [t("nav_info"), t("nav_sections"), t("nav_figures"),
            t("nav_refs"), t("nav_generate")]

def safe_filename(title: str) -> str:
    return re.sub(r"[^\w\s-]", "", title)[:50].strip().replace(" ", "_") or "article"

# ─────────────────────────────────────────────────────────────────────────────
# SESSION STATE
# ─────────────────────────────────────────────────────────────────────────────
def init_state():
    d = {
        "logged_in": False, "username": "",
        "lang": "🇬🇧 English", "dark": True,
        "page": "📄 Article Info", "cite_style": "APA 7th",
        # article fields
        "art_title": "", "authors": "", "affiliation": "",
        "journal": "", "keywords": "", "abstract": "", "art_type_idx": 0,
        # sections
        "intro": "", "methods": "", "results": "", "discussion": "", "conclusion": "",
        # collections
        "figures": [], "tables": [], "refs": [],
    }
    for k, v in d.items():
        if k not in st.session_state:
            st.session_state[k] = v

init_state()

# ─────────────────────────────────────────────────────────────────────────────
# CSS THEME
# ─────────────────────────────────────────────────────────────────────────────
def css(dark=True):
    if dark:
        bg="#0f172a"; sbg="#1e293b"; cbg="#1e293b"; brd="#334155"
        fg="#f1f5f9"; sub="#94a3b8"; acc="#3b82f6"; acc2="#2563eb"
        ibg="#0f172a"; mbg="#162032"
    else:
        bg="#f8fafc"; sbg="#ffffff"; cbg="#ffffff"; brd="#e2e8f0"
        fg="#0f172a"; sub="#64748b"; acc="#2563eb"; acc2="#1d4ed8"
        ibg="#f1f5f9"; mbg="#eef2ff"

    st.markdown(f"""<style>
html,body,[data-testid="stAppViewContainer"]{{background:{bg}!important;color:{fg}!important;font-family:'Inter','Segoe UI',sans-serif;}}
[data-testid="stSidebar"]{{background:{sbg}!important;border-right:1px solid {brd};}}
[data-testid="stSidebar"] *{{color:{fg}!important;}}
textarea,input,.stTextInput>div>input{{background:{ibg}!important;color:{fg}!important;border:1px solid {brd}!important;border-radius:8px!important;}}
/* metric card */
.mc{{background:{mbg};border:1px solid {brd};border-radius:12px;padding:14px 18px;text-align:center;}}
.mv{{font-size:1.8rem;font-weight:800;color:{acc};}}
.ml{{font-size:0.75rem;color:{sub};margin-top:2px;}}
/* preview */
.pv{{background:{cbg};border:1px solid {brd};border-radius:12px;padding:24px 28px;min-height:500px;font-family:'Times New Roman',serif;line-height:1.8;}}
.pt{{font-size:1.25rem;font-weight:700;text-align:center;color:{fg};}}
.pa{{text-align:center;color:{sub};font-size:0.88rem;margin-bottom:16px;}}
.ph{{font-weight:700;color:{acc};border-bottom:1px solid {brd};padding-bottom:3px;margin-top:14px;font-size:1rem;}}
.pab{{background:{mbg};border-left:4px solid {acc};padding:10px 14px;border-radius:0 8px 8px 0;margin:10px 0;font-size:0.88rem;color:{sub};}}
/* section card */
.sc{{background:{cbg};border:1px solid {brd};border-radius:12px;padding:18px;margin-bottom:14px;}}
/* ref item */
.ri{{background:{cbg};border:1px solid {brd};border-radius:8px;padding:10px 14px;margin-bottom:7px;font-size:0.84rem;}}
.rn{{color:{acc};font-weight:700;}}
/* fab */
.fab{{position:fixed;bottom:28px;right:28px;z-index:9999;background:linear-gradient(135deg,{acc2},{acc});color:white!important;padding:14px 26px;border-radius:50px;font-weight:700;font-size:0.95rem;box-shadow:0 8px 30px rgba(37,99,235,.5);cursor:pointer;border:none;}}
/* stepper */
.stp{{display:flex;gap:6px;align-items:center;flex-wrap:wrap;margin-bottom:16px;}}
.si{{padding:5px 12px;border-radius:20px;font-size:0.75rem;font-weight:600;border:1px solid {brd};color:{sub};white-space:nowrap;}}
.sa{{background:{acc};color:white!important;border-color:{acc};}}
.sd{{background:#10b981;color:white!important;border-color:#10b981;}}
/* topbar */
.tb{{display:flex;justify-content:space-between;align-items:center;padding-bottom:10px;border-bottom:1px solid {brd};margin-bottom:20px;}}
.tt{{font-size:1.3rem;font-weight:800;color:{fg};}}
/* login */
.lc{{max-width:420px;margin:80px auto;background:{cbg};border:1px solid {brd};border-radius:20px;padding:44px 36px;box-shadow:0 20px 60px rgba(0,0,0,.35);}}
/* sidebar quick stats */
.qs{{font-size:0.73rem;padding:3px 8px;border-radius:6px;font-weight:700;display:inline-block;margin:2px;}}
footer{{visibility:hidden;}} #MainMenu{{visibility:hidden;}} .stDeployButton{{display:none;}}
</style>""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# LOGIN
# ─────────────────────────────────────────────────────────────────────────────
def page_login():
    css(dark=True)
    _, mid, _ = st.columns([1, 1.1, 1])
    with mid:
        st.markdown("""<div class="lc">
  <div style="text-align:center;margin-bottom:24px;">
    <div style="font-size:3rem;">🧠</div>
    <h2 style="margin:6px 0 2px;font-weight:900;color:#3b82f6;">ArticleAI</h2>
    <p style="color:#94a3b8;margin:0;font-size:0.88rem;">Research Writing Platform</p>
  </div></div>""", unsafe_allow_html=True)

        with st.form("lf"):
            u = st.text_input("👤 Username", placeholder="admin")
            p = st.text_input("🔑 Password", type="password", placeholder="••••••••")
            if st.form_submit_button("Sign In →", use_container_width=True):
                if u in USERS and USERS[u]["password"] == p:
                    st.session_state.logged_in = True
                    st.session_state.username  = u
                    st.rerun()
                else:
                    st.error("❌ Invalid credentials. Try: admin / admin123")

        st.markdown("""<div style="text-align:center;margin-top:14px;color:#64748b;font-size:0.78rem;">
Demo: <b style="color:#94a3b8;">admin</b> / <b style="color:#94a3b8;">admin123</b></div>""",
        unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# SIDEBAR
# ─────────────────────────────────────────────────────────────────────────────
def sidebar():
    with st.sidebar:
        st.markdown(f"""<div style="font-size:1.45rem;font-weight:900;color:#3b82f6;">🧠 {t('app_title')}</div>
<div style="font-size:0.72rem;color:#64748b;margin-bottom:16px;">{t('tagline')}</div>""",
        unsafe_allow_html=True)
        st.divider()

        # Language selector
        langs = list(TR.keys())
        sel = st.selectbox("🌍", langs,
                           index=langs.index(st.session_state.lang),
                           label_visibility="collapsed")
        if sel != st.session_state.lang:
            st.session_state.lang = sel
            st.session_state.page = t("nav_info")
            st.rerun()

        st.divider()

        # Navigation
        all_pages = nav_steps() + [t("nav_settings")]
        cur = st.session_state.page if st.session_state.page in all_pages else all_pages[0]
        pg = st.radio("nav", all_pages, index=all_pages.index(cur),
                      label_visibility="collapsed")
        if pg != st.session_state.page:
            st.session_state.page = pg
            st.rerun()

        st.divider()

        # Quick stats
        all_text = " ".join([st.session_state.get(k,"") for k in
                              ["intro","methods","results","discussion","conclusion","abstract"]])
        w = wc(all_text)
        f = len(st.session_state.figures)
        r = len(st.session_state.refs)
        st.markdown(f"""<div style="font-size:0.72rem;color:#64748b;margin-bottom:6px;">📊 Quick Stats</div>
<span class="qs" style="background:#1e3a5f;color:#60a5fa;">{w} words</span>
<span class="qs" style="background:#1c3a2e;color:#34d399;">{f} figs</span>
<span class="qs" style="background:#3a1c1c;color:#f87171;">{r} refs</span>""",
        unsafe_allow_html=True)

        st.divider()

        # User + logout
        u = USERS.get(st.session_state.username, {})
        st.markdown(f"""<div style="font-size:0.8rem;color:#94a3b8;">
👤 <b style="color:#f1f5f9;">{u.get('name','User')}</b><br>
<span style="color:#64748b;">{u.get('role','')}</span></div>""", unsafe_allow_html=True)

        if st.button(f"🚪 {t('logout')}", use_container_width=True):
            st.session_state.logged_in = False
            st.rerun()

# ─────────────────────────────────────────────────────────────────────────────
# STEPPER + STATS ROW
# ─────────────────────────────────────────────────────────────────────────────
def stepper():
    steps = nav_steps()
    if st.session_state.page not in steps:
        return
    ci = steps.index(st.session_state.page)
    html = ""
    for i, s in enumerate(steps):
        lbl = s.split(" ",1)[1] if " " in s else s
        cls = "si sd" if i < ci else ("si sa" if i == ci else "si")
        pfx = "✓ " if i < ci else ""
        html += f'<div class="{cls}">{pfx}{lbl}</div>'
        if i < len(steps)-1:
            html += '<div style="color:#475569;font-size:0.7rem;">›</div>'
    st.markdown(f'<div class="stp">{html}</div>', unsafe_allow_html=True)
    st.progress((ci+1)/len(steps))
    st.caption(f"{t('step')} {ci+1} {t('of')} {len(steps)}")

def stats_row():
    all_text = " ".join([st.session_state.get(k,"") for k in
                         ["intro","methods","results","discussion","conclusion","abstract"]])
    w  = wc(all_text)
    sc = sum(1 for k in ["intro","methods","results","discussion","conclusion"]
             if st.session_state.get(k,"").strip())
    f  = len(st.session_state.figures)
    tb = len(st.session_state.tables)
    r  = len(st.session_state.refs)

    cols = st.columns(5)
    for col, val, lbl in zip(cols,
                              [w, sc, f, tb, r],
                              [t("w_words"), t("w_secs"), t("w_figs"), t("w_tbls"), t("w_refs")]):
        col.markdown(f'<div class="mc"><div class="mv">{val}</div><div class="ml">{lbl}</div></div>',
                     unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# PAGE: ARTICLE INFO
# ─────────────────────────────────────────────────────────────────────────────
def pg_info():
    st.markdown(f'<div class="tb"><span class="tt">📄 {t("art_title")}</span></div>',
                unsafe_allow_html=True)
    stepper(); stats_row(); st.write("")

    L, R = st.columns(2)
    with L:
        st.session_state.art_title  = st.text_input(t("art_title"),  value=st.session_state.art_title,
            placeholder="e.g. Flood Mapping in Kazakhstan Using Sentinel-1 SAR Data")
        st.session_state.authors    = st.text_input(t("authors"),    value=st.session_state.authors,
            placeholder="Samarkhanov K., Smith J.")
        st.session_state.affiliation= st.text_area(t("affiliation"), value=st.session_state.affiliation,
            height=70, placeholder="Institute of Geography, Almaty, Kazakhstan")
        st.session_state.journal    = st.text_input(t("journal"),    value=st.session_state.journal,
            placeholder=t("jrn_ph"))
        art_types = TR[st.session_state.lang]["art_types"]
        idx = min(st.session_state.art_type_idx, len(art_types)-1)
        sel = st.selectbox(t("art_type"), art_types, index=idx)
        st.session_state.art_type_idx = art_types.index(sel)

    with R:
        st.session_state.keywords = st.text_input(t("keywords"), value=st.session_state.keywords,
            placeholder=t("kw_ph"))
        st.session_state.abstract = st.text_area(t("abstract"), value=st.session_state.abstract,
            height=190, placeholder="Write your abstract here (150–300 words)…")
        w = wc(st.session_state.abstract)
        color = "#10b981" if 150 <= w <= 300 else ("#f59e0b" if w > 0 else "#64748b")
        st.markdown(f'<span style="color:{color};font-size:0.78rem;">📝 {t("word_count")}: {w}</span>',
                    unsafe_allow_html=True)
        st.markdown("---")
        # mini preview card
        ab_snip = st.session_state.abstract[:280] + ("…" if len(st.session_state.abstract)>280 else "")
        ab_html = f'<div class="pab"><b>Abstract:</b> {ab_snip}</div>' if st.session_state.abstract else ""
        kw_html = (f'<div style="font-size:0.78rem;color:#64748b;margin-top:6px;">'
                   f'<b>Keywords:</b> {st.session_state.keywords}</div>'
                   if st.session_state.keywords else "")
        st.markdown(f"""<div class="pv" style="min-height:auto;padding:18px;">
  <div class="pt">{st.session_state.art_title or "—"}</div>
  <div class="pa">{st.session_state.authors or "—"}</div>
  <div class="pa" style="font-size:0.8rem;">{st.session_state.affiliation or ""}</div>
  {ab_html}{kw_html}
</div>""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# PAGE: SECTIONS
# ─────────────────────────────────────────────────────────────────────────────
def pg_sections():
    st.markdown(f'<div class="tb"><span class="tt">✍️ {t("nav_sections")}</span></div>',
                unsafe_allow_html=True)
    stepper(); stats_row(); st.write("")

    L, R = st.columns(2, gap="large")
    sec_keys   = ["intro","methods","results","discussion","conclusion"]
    sec_labels = [t("intro"),t("methods"),t("results"),t("discussion"),t("conclusion")]

    with L:
        st.subheader(t("sec_editor"))
        tabs = st.tabs(sec_labels)
        for tab, key, label in zip(tabs, sec_keys, sec_labels):
            with tab:
                up = st.file_uploader(t("upload_docx"), type=["docx","txt"],
                                      key=f"up_{key}", label_visibility="collapsed")
                if up:
                    if up.name.endswith(".txt"):
                        st.session_state[key] = up.read().decode("utf-8", errors="ignore")
                    elif up.name.endswith(".docx") and DOCX_OK:
                        try:
                            doc = Document(BytesIO(up.read()))
                            st.session_state[key] = "\n".join(p.text for p in doc.paragraphs)
                        except Exception:
                            st.warning("Could not parse DOCX.")

                st.session_state[key] = st.text_area(
                    label, value=st.session_state[key],
                    height=290, key=f"ed_{key}",
                    label_visibility="collapsed",
                    placeholder=f"Write the {label} section here…")
                st.caption(f"📝 {t('word_count')}: {wc(st.session_state[key])}")

    with R:
        st.subheader(t("preview"))
        parts = [f'<div class="pt">{st.session_state.art_title or "—"}</div>',
                 f'<div class="pa">{st.session_state.authors or "—"}</div>']
        if st.session_state.abstract:
            ab = st.session_state.abstract[:400] + ("…" if len(st.session_state.abstract)>400 else "")
            parts.append(f'<div class="pab"><b>Abstract:</b> {ab}</div>')
        for key, lbl in zip(sec_keys, sec_labels):
            c = st.session_state.get(key,"")
            if c:
                snip = c[:500] + ("…" if len(c)>500 else "")
                parts.append(f'<div class="ph">{lbl}</div><p style="font-size:0.86rem;">{snip}</p>')
        st.markdown(f'<div class="pv">{"".join(parts)}</div>', unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# PAGE: FIGURES & TABLES
# ─────────────────────────────────────────────────────────────────────────────
def pg_figures():
    st.markdown(f'<div class="tb"><span class="tt">🖼️ {t("fig_mgr")}</span></div>',
                unsafe_allow_html=True)
    stepper(); stats_row(); st.write("")

    L, R = st.columns(2, gap="large")

    with L:
        st.subheader(f"🖼️ {t('add_fig')}")
        with st.form("ff", clear_on_submit=True):
            fn  = st.text_input(t("fig_num"), placeholder="1")
            fc  = st.text_input(t("fig_caption"), placeholder="Map of study area, Kazakhstan")
            fup = st.file_uploader(t("upload_fig"), type=["png","jpg","jpeg","tif","svg"])
            if st.form_submit_button(f"➕ {t('add_btn')}", use_container_width=True) and fc:
                st.session_state.figures.append({
                    "number": fn or str(len(st.session_state.figures)+1),
                    "caption": fc,
                    "image": fup.read() if fup else None,
                    "name":  fup.name  if fup else None,
                })
                st.success("✅ Figure added")
        st.divider()
        if not st.session_state.figures:
            st.info(t("no_figs"))
        else:
            for i, fig in enumerate(st.session_state.figures):
                with st.expander(f"Fig. {fig['number']} — {fig['caption']}"):
                    if fig.get("image"):
                        st.image(fig["image"], use_container_width=True)
                    if st.button(f"🗑️ {t('del_btn')}", key=f"df{i}"):
                        st.session_state.figures.pop(i); st.rerun()

    with R:
        st.subheader(f"📊 {t('add_tbl')}")
        with st.form("tf", clear_on_submit=True):
            tn = st.text_input(t("tbl_num"), placeholder="1")
            tc = st.text_input(t("tbl_caption"), placeholder="Summary statistics of study area")
            td = st.text_area(t("tbl_data"), height=110,
                              placeholder="Col1,Col2,Col3\nVal1,Val2,Val3")
            if st.form_submit_button(f"➕ {t('add_btn')}", use_container_width=True) and tc:
                st.session_state.tables.append({
                    "number": tn or str(len(st.session_state.tables)+1),
                    "caption": tc, "data": td,
                })
                st.success("✅ Table added")
        st.divider()
        if not st.session_state.tables:
            st.info(t("no_tbls"))
        else:
            for i, tbl in enumerate(st.session_state.tables):
                with st.expander(f"Table {tbl['number']} — {tbl['caption']}"):
                    if tbl.get("data") and PANDAS_OK:
                        try:
                            df = pd.read_csv(io.StringIO(tbl["data"]))
                            st.dataframe(df, use_container_width=True)
                        except Exception:
                            st.text(tbl["data"])
                    if st.button(f"🗑️ {t('del_btn')}", key=f"dt{i}"):
                        st.session_state.tables.pop(i); st.rerun()

# ─────────────────────────────────────────────────────────────────────────────
# REFERENCE FORMATTER
# ─────────────────────────────────────────────────────────────────────────────
def fmt_ref(ref: dict, style: str, n: int) -> str:
    au = ref.get("authors",""); yr = ref.get("year",""); ti = ref.get("title","")
    jn = ref.get("journal",""); vo = ref.get("volume",""); pg = ref.get("pages","")
    doi = f" https://doi.org/{ref['doi']}" if ref.get("doi") else ""
    if "Vancouver" in style or "Ванкувер" in style:
        return f"{n}. {au}. {ti}. *{jn}*. {yr};{vo}:{pg}.{doi}"
    elif "APA" in style:
        return f"{au} ({yr}). {ti}. *{jn}*, *{vo}*, {pg}.{doi}"
    elif "IEEE" in style:
        return f"[{n}] {au}, \"{ti},\" *{jn}*, vol. {vo}, pp. {pg}, {yr}.{doi}"
    else:  # Harvard / Гарвард / Чикаго
        return f"{au} {yr}, '{ti}', *{jn}*, vol. {vo}, pp. {pg}.{doi}"

# ─────────────────────────────────────────────────────────────────────────────
# PAGE: REFERENCES
# ─────────────────────────────────────────────────────────────────────────────
def pg_refs():
    st.markdown(f'<div class="tb"><span class="tt">📑 {t("ref_mgr")}</span></div>',
                unsafe_allow_html=True)
    stepper(); stats_row(); st.write("")

    rt_list = TR[st.session_state.lang]["ref_types_list"]
    cs_list = TR[st.session_state.lang]["cite_styles"]

    L, R = st.columns(2, gap="large")

    with L:
        st.subheader(f"➕ {t('add_ref')}")
        with st.form("rf", clear_on_submit=True):
            rtype = st.selectbox(t("ref_type"), rt_list)
            rau   = st.text_input(t("ref_authors"), placeholder="Samarkhanov K., Doe J.")
            ryr   = st.text_input(t("ref_year"), placeholder="2024")
            rti   = st.text_input(t("ref_title_f"), placeholder="Flood Mapping Using SAR Data")
            rjn   = st.text_input(t("ref_journal"), placeholder="Remote Sensing")
            c1,c2 = st.columns(2)
            rvo   = c1.text_input(t("ref_vol"), placeholder="15")
            rpg   = c2.text_input(t("ref_pages"), placeholder="1234–1250")
            rdoi  = st.text_input(t("ref_doi"), placeholder="10.3390/rs15051234")
            if st.form_submit_button(f"➕ {t('add_btn')}", use_container_width=True) and rti:
                st.session_state.refs.append({
                    "type": rtype, "authors": rau, "year": ryr, "title": rti,
                    "journal": rjn, "volume": rvo, "pages": rpg, "doi": rdoi,
                })
                st.success("✅ Reference added")

        st.divider()
        st.subheader(f"📥 {t('import_refs')}")
        bib = st.text_area("BibTeX / plain text", height=110,
                           placeholder="Paste BibTeX or one reference per line…")
        if st.button(t("import_btn")):
            lines = [l.strip() for l in bib.split("\n") if l.strip()]
            for ln in lines:
                st.session_state.refs.append({
                    "type":"Journal Article","authors":"","year":"",
                    "title": ln,"journal":"","volume":"","pages":"","doi":""})
            st.success(f"{t('imported')} {len(lines)} {t('ref_s')}")

    with R:
        st.subheader(f"📋 {t('ref_list')}")
        style = st.selectbox(t("cite_style"), cs_list, key="rs")
        st.session_state.cite_style = style
        if not st.session_state.refs:
            st.info(t("no_refs"))
        else:
            for i, ref in enumerate(st.session_state.refs):
                c1, c2 = st.columns([11,1])
                c1.markdown(
                    f'<div class="ri"><span class="rn">[{i+1}]</span> {fmt_ref(ref, style, i+1)}</div>',
                    unsafe_allow_html=True)
                if c2.button("🗑️", key=f"dr{i}"):
                    st.session_state.refs.pop(i); st.rerun()

# ─────────────────────────────────────────────────────────────────────────────
# DOCX GENERATOR
# ─────────────────────────────────────────────────────────────────────────────
def build_docx() -> BytesIO:
    doc = Document()
    sec = doc.sections[0]
    sec.top_margin    = Inches(1);   sec.bottom_margin = Inches(1)
    sec.left_margin   = Inches(1.25);sec.right_margin  = Inches(1.25)

    BLUE = RGBColor(0x1a,0x56,0xdb)

    # Title
    tp = doc.add_paragraph()
    tp.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = tp.add_run(st.session_state.art_title or "Untitled")
    r.bold = True; r.font.size = Pt(16); r.font.color.rgb = BLUE

    if st.session_state.authors:
        ap = doc.add_paragraph(); ap.alignment = WD_ALIGN_PARAGRAPH.CENTER
        ap.add_run(st.session_state.authors).bold = True

    if st.session_state.affiliation:
        af = doc.add_paragraph(); af.alignment = WD_ALIGN_PARAGRAPH.CENTER
        r = af.add_run(st.session_state.affiliation)
        r.font.size = Pt(10); r.font.color.rgb = RGBColor(0x64,0x74,0x8b)

    if st.session_state.keywords:
        kp = doc.add_paragraph(); kp.alignment = WD_ALIGN_PARAGRAPH.CENTER
        r = kp.add_run(f"Keywords: {st.session_state.keywords}")
        r.italic = True; r.font.size = Pt(10)

    doc.add_paragraph()

    if st.session_state.abstract:
        h = doc.add_heading("Abstract", level=2)
        h.runs[0].font.color.rgb = BLUE
        doc.add_paragraph(st.session_state.abstract)
        doc.add_paragraph()

    sec_keys   = ["intro","methods","results","discussion","conclusion"]
    sec_labels = [t("intro"),t("methods"),t("results"),t("discussion"),t("conclusion")]
    for i, (k, lbl) in enumerate(zip(sec_keys, sec_labels), 1):
        if st.session_state.get(k,"").strip():
            h = doc.add_heading(f"{i}. {lbl}", level=1)
            h.runs[0].font.color.rgb = BLUE
            doc.add_paragraph(st.session_state[k])
            doc.add_paragraph()

    # Figures
    if st.session_state.figures:
        doc.add_heading("Figures", level=1)
        for fig in st.session_state.figures:
            if fig.get("image"):
                try: doc.add_picture(BytesIO(fig["image"]), width=Inches(4.5))
                except Exception: pass
            cp = doc.add_paragraph(f"Figure {fig['number']}. {fig['caption']}")
            cp.alignment = WD_ALIGN_PARAGRAPH.CENTER
            if cp.runs: cp.runs[0].italic = True; cp.runs[0].font.size = Pt(9)
            doc.add_paragraph()

    # Tables
    if st.session_state.tables:
        for tbl in st.session_state.tables:
            tp = doc.add_paragraph(f"Table {tbl['number']}. {tbl['caption']}")
            if tp.runs: tp.runs[0].bold = True
            if tbl.get("data") and PANDAS_OK:
                try:
                    df = pd.read_csv(io.StringIO(tbl["data"]))
                    wt = doc.add_table(rows=len(df)+1, cols=len(df.columns))
                    wt.style = "Table Grid"
                    for ci, col in enumerate(df.columns):
                        wt.cell(0,ci).text = str(col)
                    for ri in range(len(df)):
                        for ci in range(len(df.columns)):
                            wt.cell(ri+1,ci).text = str(df.iloc[ri,ci])
                except Exception: pass
            doc.add_paragraph()

    # References
    if st.session_state.refs:
        h = doc.add_heading("References", level=1)
        h.runs[0].font.color.rgb = BLUE
        for i, ref in enumerate(st.session_state.refs, 1):
            p = doc.add_paragraph(fmt_ref(ref, st.session_state.cite_style, i),
                                  style="List Number")
            if p.runs: p.runs[0].font.size = Pt(10)

    buf = BytesIO(); doc.save(buf); buf.seek(0)
    return buf

# ─────────────────────────────────────────────────────────────────────────────
# PAGE: GENERATE
# ─────────────────────────────────────────────────────────────────────────────
def pg_generate():
    st.markdown(f'<div class="tb"><span class="tt">🚀 {t("generate")}</span></div>',
                unsafe_allow_html=True)
    stepper(); stats_row(); st.write("")

    if not st.session_state.art_title:
        st.warning(t("warn_title")); return

    # Completeness meter
    done = sum(1 for k in ["intro","methods","results","discussion","conclusion"]
               if st.session_state.get(k,"").strip())
    st.markdown(f"### 📋 {t('completeness')}")
    c1,c2,c3 = st.columns([3,1,1])
    c1.progress(done/5, text=f"{done*20}% complete")
    c2.metric(t("w_secs"), f"{done}/5")
    c3.metric(t("w_refs"), len(st.session_state.refs))
    st.write("")

    # Full preview
    st.markdown(f"### {t('preview')}")
    sec_keys   = ["intro","methods","results","discussion","conclusion"]
    sec_labels = [t("intro"),t("methods"),t("results"),t("discussion"),t("conclusion")]

    parts = [f'<div class="pt">{st.session_state.art_title}</div>',
             f'<div class="pa">{st.session_state.authors}</div>']
    if st.session_state.abstract:
        ab = st.session_state.abstract[:500] + ("…" if len(st.session_state.abstract)>500 else "")
        parts.append(f'<div class="pab"><b>Abstract:</b> {ab}</div>')
    if st.session_state.keywords:
        parts.append(f'<div style="font-size:0.78rem;color:#64748b;margin:6px 0;">'
                     f'<b>Keywords:</b> {st.session_state.keywords}</div>')
    for i,(k,lbl) in enumerate(zip(sec_keys, sec_labels),1):
        c = st.session_state.get(k,"")
        if c:
            parts.append(f'<div class="ph">{i}. {lbl}</div>'
                         f'<p style="font-size:0.85rem;">{c}</p>')
    if st.session_state.refs:
        parts.append('<div class="ph">References</div>')
        for i,ref in enumerate(st.session_state.refs,1):
            parts.append(f'<p style="font-size:0.82rem;">{fmt_ref(ref,st.session_state.cite_style,i)}</p>')

    st.markdown(f'<div class="pv">{"".join(parts)}</div>', unsafe_allow_html=True)
    st.write("")

    # Export buttons
    st.markdown("### 📥 Export")
    e1, e2, e3 = st.columns(3)
    fn = safe_filename(st.session_state.art_title)

    with e1:
        if DOCX_OK:
            with st.spinner(t("downloading")):
                buf = build_docx()
            st.download_button(t("dl_docx"), buf, f"{fn}.docx",
                               "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                               use_container_width=True)
            st.success(t("success_gen"))
        else:
            st.error("Install python-docx: `pip install python-docx`")

    with e2:
        md_lines = [f"# {st.session_state.art_title}",
                    f"**{st.session_state.authors}**",
                    f"*{st.session_state.affiliation}*", "",
                    f"**Keywords:** {st.session_state.keywords}", "",
                    f"## Abstract\n\n{st.session_state.abstract}", ""]
        for i,(k,lbl) in enumerate(zip(sec_keys,sec_labels),1):
            if st.session_state.get(k,""):
                md_lines += [f"## {i}. {lbl}", st.session_state[k], ""]
        if st.session_state.refs:
            md_lines.append("## References")
            for i,ref in enumerate(st.session_state.refs,1):
                md_lines.append(fmt_ref(ref, st.session_state.cite_style, i))
        st.download_button(t("dl_md"),
                           "\n".join(md_lines).encode("utf-8"),
                           f"{fn}.md", "text/markdown",
                           use_container_width=True)

    with e3:
        proj = {k: st.session_state.get(k,"") for k in
                ["art_title","authors","affiliation","journal","keywords","abstract",
                 "intro","methods","results","discussion","conclusion","cite_style"]}
        proj["refs"]   = st.session_state.refs
        proj["tables"] = [{k2:v2 for k2,v2 in tb.items() if k2!="image"}
                          for tb in st.session_state.tables]
        proj["exported_at"] = datetime.now().isoformat()
        st.download_button(t("save_json"),
                           json.dumps(proj, ensure_ascii=False, indent=2).encode("utf-8"),
                           f"{fn}_project.json", "application/json",
                           use_container_width=True)

# ─────────────────────────────────────────────────────────────────────────────
# PAGE: SETTINGS
# ─────────────────────────────────────────────────────────────────────────────
def pg_settings():
    st.markdown(f'<div class="tb"><span class="tt">⚙️ {t("settings")}</span></div>',
                unsafe_allow_html=True)
    st.write("")

    L, R = st.columns(2)
    with L:
        st.subheader(f"🎨 {t('theme')}")
        themes = TR[st.session_state.lang]["themes"]
        choice = st.radio(t("theme"), themes,
                          index=0 if st.session_state.dark else 1,
                          label_visibility="collapsed")
        st.session_state.dark = (choice == themes[0])

        st.subheader(f"📝 {t('cite_style')}")
        cs_list = TR[st.session_state.lang]["cite_styles"]
        cs = st.selectbox(t("cite_style"), cs_list, label_visibility="collapsed")
        st.session_state.cite_style = cs

        st.subheader(f"🗑️ {t('reset')}")
        if st.button(t("reset"), type="secondary"):
            for k in ["art_title","authors","affiliation","journal","keywords","abstract",
                      "intro","methods","results","discussion","conclusion"]:
                st.session_state[k] = ""
            st.session_state.figures = []
            st.session_state.tables  = []
            st.session_state.refs    = []
            st.success(t("reset_ok"))

    with R:
        st.subheader(f"📂 {t('load_json')}")
        upf = st.file_uploader("JSON project file", type="json")
        if upf:
            try:
                data = json.load(upf)
                for f in ["art_title","authors","affiliation","journal","keywords","abstract",
                          "intro","methods","results","discussion","conclusion",
                          "refs","tables","cite_style"]:
                    if f in data:
                        st.session_state[f] = data[f]
                st.success(t("loaded"))
            except Exception as e:
                st.error(f"Error: {e}")

# ─────────────────────────────────────────────────────────────────────────────
# FLOATING ACTION BUTTON
# ─────────────────────────────────────────────────────────────────────────────
def fab():
    steps = nav_steps()
    if st.session_state.page in steps and st.session_state.page != t("nav_generate"):
        st.markdown(
            f'<div class="fab">🚀 {t("generate")}</div>',
            unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────────────────────────────────
def main():
    if not st.session_state.logged_in:
        page_login(); return

    css(dark=st.session_state.dark)
    sidebar()

    pg = st.session_state.page
    routes = {
        t("nav_info"):     pg_info,
        t("nav_sections"): pg_sections,
        t("nav_figures"):  pg_figures,
        t("nav_refs"):     pg_refs,
        t("nav_generate"): pg_generate,
        t("nav_settings"): pg_settings,
    }
    routes.get(pg, pg_info)()
    fab()

if __name__ == "__main__":
    main()
