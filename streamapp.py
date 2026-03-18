# ════════════════════════════════════════════════════════════════════════════
#  Smart Article — Research Writing Platform  v2.0
#  Fixes: light-mode CSS · login+register · separate Figures/Tables/Formulas
#         ГОСТ 7.0.5-2008 · GitHub Gist · file logging
# ════════════════════════════════════════════════════════════════════════════

import streamlit as st
import re, json, io, hashlib, smtplib, base64
from datetime import datetime
from io import BytesIO
from pathlib import Path
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

try:
    import requests
    REQ_OK = True
except ImportError:
    REQ_OK = False

st.set_page_config(
    page_title="Smart Article",
    page_icon="📝",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ── optional deps ─────────────────────────────────────────────────────────────
try:
    from docx import Document
    from docx.shared import Pt, Inches, RGBColor
    from docx.enum.text import WD_ALIGN_PARAGRAPH
    DOCX_OK = True
except ImportError:
    DOCX_OK = False

try:
    import pandas as pd
    PD_OK = True
except ImportError:
    PD_OK = False

try:
    import requests
    REQ_OK = True
except ImportError:
    REQ_OK = False

# ── storage paths ─────────────────────────────────────────────────────────────
USERS_FILE = Path("users.json")
LOGS_FILE  = Path("logs.json")

# ════════════════════════════════════════════════════════════════════════════
# AUTH  (Registration · Login · File Logging)
# ════════════════════════════════════════════════════════════════════════════
def hp(pw: str) -> str:
    return hashlib.sha256(pw.encode()).hexdigest()

def load_users() -> dict:
    if USERS_FILE.exists():
        try:   return json.loads(USERS_FILE.read_text("utf-8"))
        except: return {}
    seed = {"admin": {"password": hp("admin123"), "name": "Kanat Samarkhanov",
                      "email": "admin@smart-article.kz", "role": "Researcher",
                      "created_at": datetime.now().isoformat()}}
    USERS_FILE.write_text(json.dumps(seed, ensure_ascii=False, indent=2), "utf-8")
    return seed

def save_users(u: dict):
    USERS_FILE.write_text(json.dumps(u, ensure_ascii=False, indent=2), "utf-8")

def load_logs() -> list:
    if LOGS_FILE.exists():
        try:   return json.loads(LOGS_FILE.read_text("utf-8"))
        except: return []
    return []

def add_log(event: str, user: str, detail: str = ""):
    logs = load_logs()
    logs.append({"event": event, "username": user,
                 "detail": detail, "ts": datetime.now().isoformat()})
    LOGS_FILE.write_text(
        json.dumps(logs[-2000:], ensure_ascii=False, indent=2), "utf-8")

def do_register(uname, email, pw, name, role="Researcher"):
    if len(uname) < 3:  return False, "uname_short"
    if len(pw) < 6:     return False, "pw_short"
    users = load_users()
    if uname in users:  return False, "username_taken"
    if any(v.get("email") == email for v in users.values()):
        return False, "email_taken"
    users[uname] = {"password": hp(pw), "name": name, "email": email,
                    "role": role, "created_at": datetime.now().isoformat()}
    save_users(users)
    add_log("register", uname, f"email={email} role={role}")

    # ── Sync to GitHub + send email ───────────────────────────────
    sync_users_to_github()
    sync_logs_to_github()
    _notify_register(uname, email, role)

    return True, "ok"


def do_login(uname, pw):
    users = load_users()
    if uname not in users:
        add_log("fail", uname, "user_not_found")
        sync_logs_to_github()
        return False, {}
    if users[uname]["password"] != hp(pw):
        add_log("fail", uname, "wrong_password")
        sync_logs_to_github()
        return False, {}
    add_log("login", uname)
    sync_logs_to_github()
    _notify_login(uname)
    return True, users[uname]

# ════════════════════════════════════════════════════════════════════════════
# TRANSLATIONS  EN / RU / KZ
# ════════════════════════════════════════════════════════════════════════════
TR = {
"🇬🇧 English": dict(
    app="Smart Article", tagline="Research Writing Platform",
    sign_in="Sign In", register="Register", username="Username",
    password="Password", confirm_pw="Confirm Password", email="E-mail",
    full_name="Full Name", role="Role",
    roles=["Researcher","PhD Student","Professor","Analyst","Other"],
    login_btn="Sign In →", reg_btn="Create Account →",
    login_err="Invalid credentials", pw_mismatch="Passwords do not match",
    pw_short="Password must be ≥ 6 characters", uname_short="Username must be ≥ 3 characters",
    username_taken="Username already taken", email_taken="E-mail already registered",
    reg_ok="✅ Account created! You can sign in now.",
    have_account="Already have an account?", no_account="No account yet?",
    logout="Logout",
    nav_info="📄 Article Info", nav_sec="✍️ Sections",
    nav_fig="🖼️ Figures", nav_tbl="📊 Tables",
    nav_form="🧮 Formulas", nav_ref="📑 References",
    nav_gen="🚀 Generate", nav_set="⚙️ Settings",
    step="Step", of_="of",
    title_f="Article Title", authors_f="Authors", affil_f="Affiliation",
    journal_f="Target Journal", keywords_f="Keywords", abstract_f="Abstract",
    art_type_f="Article Type",
    art_types=["Research Article","Review Article","Short Communication","Letter","Case Study"],
    intro="Introduction", methods="Methods", results="Results",
    discussion="Discussion", conclusion="Conclusion",
    upload_docx="Upload DOCX / TXT",
    fig_mgr="Figures Manager", add_fig="Add Figure",
    fig_no="Figure No.", fig_cap="Caption", upload_fig="Upload image (PNG/JPG/TIF)",
    tbl_mgr="Tables Manager", add_tbl="Add Table",
    tbl_no="Table No.", tbl_cap="Caption", tbl_data="Data (CSV format)",
    form_mgr="Formulas Manager", add_form="Add Formula",
    form_no="Formula No.", form_latex="LaTeX code",
    form_desc="Description", form_preview="Preview",
    ref_mgr="References Manager", add_ref="Add Reference",
    ref_type="Type", ref_au="Authors", ref_yr="Year",
    ref_ti="Title", ref_jn="Journal / Publisher",
    ref_vol="Volume", ref_no="Number", ref_pp="Pages", ref_doi="DOI",
    ref_city="City", ref_pub="Publisher",
    ref_types=["Journal Article","Book","Book Chapter","Conference Paper","Website","Thesis"],
    cite_styles=["APA 7th","Vancouver","Harvard","IEEE","ГОСТ 7.0.5-2008"],
    import_refs="Import BibTeX / plain text", import_btn="Import",
    imported="Imported", ref_s="reference(s)",
    ref_list="Reference List", no_refs="No references yet.",
    no_figs="No figures yet.", no_tbls="No tables yet.", no_forms="No formulas yet.",
    gen_title="Generate & Export",
    dl_docx="📥 Download DOCX", dl_md="📥 Download Markdown",
    save_json="💾 Save Project (JSON)",
    load_json_help=("💾 Save / Load Project (JSON): saves ALL article data — title, "
                    "sections, references, formulas — into a .json file on your computer. "
                    "Use 'Load' later to continue writing from where you left off, "
                    "or share the file with co-authors."),
    w_words="Words", w_secs="Sections", w_figs="Figures",
    w_tbls="Tables", w_refs="References", w_forms="Formulas",
    stats="📊 Article Stats",
    settings_title="Settings", theme_label="Theme",
    cite_style_label="Default Citation Style",
    themes=["🌙 Dark","☀️ Light"],
    reset_btn="Reset all data", reset_ok="✅ All data cleared.",
    load_json="📂 Load Project (JSON)", loaded="✅ Project loaded!",
    gh_title="GitHub Gist — Save / Load",
    gh_token="GitHub Personal Access Token",
    gh_save="☁️ Save to Gist", gh_load="📥 Load from Gist URL",
    gh_url="Gist URL", gh_saved="✅ Saved to Gist!", gh_loaded="✅ Loaded from Gist!",
    gh_err="GitHub error", gh_need_req="Install requests: pip install requests",
    warn_title="⚠️ Please add an article title first.",
    completeness="Article Completeness",
    success_gen="✅ Article generated!", downloading="Preparing document…",
    word_count="Word count", add_btn="Add", del_btn="Delete",
    jrn_ph="e.g. Remote Sensing, Catena, Journal of Hydrology",
    kw_ph="e.g. GIS, remote sensing, hydrology",
    welcome="Welcome back",
    preview="📄 Article Preview", sec_editor="✍️ Section Editor",
),
"🇷🇺 Русский": dict(
    app="Smart Article", tagline="Платформа написания научных статей",
    sign_in="Вход", register="Регистрация", username="Логин",
    password="Пароль", confirm_pw="Подтвердите пароль", email="E-mail",
    full_name="Полное имя", role="Роль",
    roles=["Исследователь","Докторант","Профессор","Аналитик","Другое"],
    login_btn="Войти →", reg_btn="Создать аккаунт →",
    login_err="Неверный логин или пароль",
    pw_mismatch="Пароли не совпадают",
    pw_short="Пароль должен быть ≥ 6 символов",
    uname_short="Логин должен быть ≥ 3 символов",
    username_taken="Такой логин уже занят",
    email_taken="E-mail уже зарегистрирован",
    reg_ok="✅ Аккаунт создан! Теперь войдите в систему.",
    have_account="Уже есть аккаунт?",
    no_account="Нет аккаунта?",
    logout="Выйти",
    nav_info="📄 Информация", nav_sec="✍️ Разделы",
    nav_fig="🖼️ Рисунки", nav_tbl="📊 Таблицы",
    nav_form="🧮 Формулы", nav_ref="📑 Литература",
    nav_gen="🚀 Генерация", nav_set="⚙️ Настройки",
    step="Шаг", of_="из",
    title_f="Название статьи", authors_f="Авторы", affil_f="Аффилиация",
    journal_f="Целевой журнал", keywords_f="Ключевые слова", abstract_f="Аннотация",
    art_type_f="Тип статьи",
    art_types=["Научная статья","Обзорная статья","Краткое сообщение","Письмо","Кейс-стади"],
    intro="Введение", methods="Методы", results="Результаты",
    discussion="Обсуждение", conclusion="Заключение",
    upload_docx="Загрузить DOCX / TXT",
    fig_mgr="Менеджер рисунков", add_fig="Добавить рисунок",
    fig_no="№ рисунка", fig_cap="Подпись", upload_fig="Загрузить изображение (PNG/JPG)",
    tbl_mgr="Менеджер таблиц", add_tbl="Добавить таблицу",
    tbl_no="№ таблицы", tbl_cap="Заголовок", tbl_data="Данные (формат CSV)",
    form_mgr="Менеджер формул", add_form="Добавить формулу",
    form_no="№ формулы", form_latex="Код LaTeX",
    form_desc="Описание", form_preview="Предпросмотр",
    ref_mgr="Менеджер литературы", add_ref="Добавить источник",
    ref_type="Тип", ref_au="Авторы", ref_yr="Год",
    ref_ti="Название", ref_jn="Журнал / Издательство",
    ref_vol="Том", ref_no="Номер", ref_pp="Страницы", ref_doi="DOI",
    ref_city="Город", ref_pub="Издательство",
    ref_types=["Журнальная статья","Книга","Глава книги","Материалы конференции","Сайт","Диссертация"],
    cite_styles=["APA 7th","Ванкувер","Гарвард","IEEE","ГОСТ 7.0.5-2008"],
    import_refs="Импорт BibTeX / текст", import_btn="Импорт",
    imported="Импортировано", ref_s="источник(ов)",
    ref_list="Список литературы", no_refs="Источники не добавлены.",
    no_figs="Рисунки не добавлены.", no_tbls="Таблицы не добавлены.", no_forms="Формулы не добавлены.",
    gen_title="Генерация и экспорт",
    dl_docx="📥 Скачать DOCX", dl_md="📥 Скачать Markdown",
    save_json="💾 Сохранить проект (JSON)",
    load_json_help=("💾 Сохранить / Загрузить проект (JSON): сохраняет ВСЕ данные статьи — "
                    "заголовок, разделы, литературу, формулы — в файл .json на вашем компьютере. "
                    "Нажмите «Загрузить» позже, чтобы продолжить работу с того же места "
                    "или поделиться файлом с соавторами."),
    w_words="Слов", w_secs="Разделов", w_figs="Рисунков",
    w_tbls="Таблиц", w_refs="Источников", w_forms="Формул",
    stats="📊 Статистика статьи",
    settings_title="Настройки", theme_label="Тема",
    cite_style_label="Стиль цитирования",
    themes=["🌙 Тёмная","☀️ Светлая"],
    reset_btn="Очистить все данные", reset_ok="✅ Данные очищены.",
    load_json="📂 Загрузить проект (JSON)", loaded="✅ Проект загружен!",
    gh_title="GitHub Gist — Сохранить / Загрузить",
    gh_token="GitHub Personal Access Token",
    gh_save="☁️ Сохранить в Gist", gh_load="📥 Загрузить из Gist",
    gh_url="URL Gist", gh_saved="✅ Сохранено в Gist!",
    gh_loaded="✅ Загружено из Gist!", gh_err="Ошибка GitHub",
    gh_need_req="Установите: pip install requests",
    warn_title="⚠️ Пожалуйста, добавьте название статьи.",
    completeness="Заполненность статьи",
    success_gen="✅ Статья сгенерирована!", downloading="Подготовка документа…",
    word_count="Количество слов", add_btn="Добавить", del_btn="Удалить",
    jrn_ph="напр., Remote Sensing, Catena, Гидрология",
    kw_ph="напр., ГИС, дистанционное зондирование",
    welcome="Добро пожаловать",
    preview="📄 Предпросмотр", sec_editor="✍️ Редактор разделов",
),
"🇰🇿 Қазақша": dict(
    app="Smart Article", tagline="Ғылыми мақала жазу платформасы",
    sign_in="Кіру", register="Тіркелу", username="Пайдаланушы аты",
    password="Құпия сөз", confirm_pw="Құпия сөзді растаңыз", email="E-mail",
    full_name="Толық аты", role="Рөл",
    roles=["Зерттеуші","Докторант","Профессор","Аналитик","Басқа"],
    login_btn="Кіру →", reg_btn="Аккаунт жасау →",
    login_err="Қате логин немесе құпия сөз",
    pw_mismatch="Құпия сөздер сәйкес келмейді",
    pw_short="Құпия сөз ≥ 6 таңба болуы керек",
    uname_short="Логин ≥ 3 таңба болуы керек",
    username_taken="Мұндай логин бар",
    email_taken="E-mail тіркелген",
    reg_ok="✅ Аккаунт жасалды! Жүйеге кіріңіз.",
    have_account="Аккаунтыңыз бар ма?",
    no_account="Аккаунтыңыз жоқ па?",
    logout="Шығу",
    nav_info="📄 Мақала туралы", nav_sec="✍️ Бөлімдер",
    nav_fig="🖼️ Суреттер", nav_tbl="📊 Кестелер",
    nav_form="🧮 Формулалар", nav_ref="📑 Әдебиеттер",
    nav_gen="🚀 Генерация", nav_set="⚙️ Параметрлер",
    step="Қадам", of_="/",
    title_f="Мақала атауы", authors_f="Авторлар", affil_f="Аффилиация",
    journal_f="Мақсатты журнал", keywords_f="Кілт сөздер", abstract_f="Аннотация",
    art_type_f="Мақала түрі",
    art_types=["Ғылыми мақала","Шолу мақаласы","Қысқа хабарлама","Хат","Кейс-стади"],
    intro="Кіріспе", methods="Әдістер", results="Нәтижелер",
    discussion="Талқылау", conclusion="Қорытынды",
    upload_docx="DOCX / TXT жүктеу",
    fig_mgr="Суреттер менеджері", add_fig="Сурет қосу",
    fig_no="Сурет №", fig_cap="Аңыз", upload_fig="Сурет жүктеу (PNG/JPG)",
    tbl_mgr="Кестелер менеджері", add_tbl="Кесте қосу",
    tbl_no="Кесте №", tbl_cap="Тақырып", tbl_data="Деректер (CSV форматы)",
    form_mgr="Формулалар менеджері", add_form="Формула қосу",
    form_no="Формула №", form_latex="LaTeX коды",
    form_desc="Сипаттама", form_preview="Алдын ала қарау",
    ref_mgr="Әдебиеттер менеджері", add_ref="Дереккөз қосу",
    ref_type="Түрі", ref_au="Авторлар", ref_yr="Жыл",
    ref_ti="Атауы", ref_jn="Журнал / Баспа",
    ref_vol="Том", ref_no="Нөмір", ref_pp="Беттер", ref_doi="DOI",
    ref_city="Қала", ref_pub="Баспа",
    ref_types=["Журнал мақаласы","Кітап","Кітап тарауы","Конференция баяндамасы","Сайт","Диссертация"],
    cite_styles=["APA 7th","Ванкувер","Гарвард","IEEE","ГОСТ 7.0.5-2008"],
    import_refs="BibTeX / мәтін импорты", import_btn="Импорт",
    imported="Импортталды", ref_s="дереккөз(дер)",
    ref_list="Әдебиеттер тізімі", no_refs="Дереккөздер қосылмаған.",
    no_figs="Суреттер қосылмаған.", no_tbls="Кестелер қосылмаған.", no_forms="Формулалар қосылмаған.",
    gen_title="Генерация және экспорт",
    dl_docx="📥 DOCX жүктеу", dl_md="📥 Markdown жүктеу",
    save_json="💾 Жобаны сақтау (JSON)",
    load_json_help=("💾 Жобаны сақтау / жүктеу (JSON): мақаланың барлық деректерін — "
                    "тақырып, бөлімдер, әдебиеттер, формулалар — компьютерге .json файлы ретінде сақтайды. "
                    "Жұмысты жалғастыру үшін кейін «Жүктеу» батырмасын басыңыз."),
    w_words="Сөздер", w_secs="Бөлімдер", w_figs="Суреттер",
    w_tbls="Кестелер", w_refs="Дереккөздер", w_forms="Формулалар",
    stats="📊 Мақала статистикасы",
    settings_title="Параметрлер", theme_label="Тақырып",
    cite_style_label="Цитата стилі",
    themes=["🌙 Күңгірт","☀️ Жарық"],
    reset_btn="Барлық деректерді тазалау", reset_ok="✅ Деректер тазаланды.",
    load_json="📂 Жобаны жүктеу (JSON)", loaded="✅ Жоба жүктелді!",
    gh_title="GitHub Gist — Сақтау / Жүктеу",
    gh_token="GitHub Personal Access Token",
    gh_save="☁️ Gist-ке сақтау", gh_load="📥 Gist-тен жүктеу",
    gh_url="Gist URL", gh_saved="✅ Gist-ке сақталды!",
    gh_loaded="✅ Gist-тен жүктелді!", gh_err="GitHub қатесі",
    gh_need_req="Орнату: pip install requests",
    warn_title="⚠️ Мақала атауын енгізіңіз.",
    completeness="Мақала толықтығы",
    success_gen="✅ Мақала сәтті жасалды!", downloading="Құжат дайындалуда…",
    word_count="Сөз саны", add_btn="Қосу", del_btn="Жою",
    jrn_ph="мыс., Remote Sensing, Catena",
    kw_ph="мыс., ГАЖ, қашықтықтан зондтау",
    welcome="Қош келдіңіз",
    preview="📄 Алдын ала қарау", sec_editor="✍️ Бөлім редакторы",
),
}

t("register")])

        # ── LOGIN ──
        with tab_login:
            with st.form("lf"):
                uname = st.text_input(f"👤 {t('username')}", placeholder="admin")
                pw    = st.text_input(f"🔑 {t('password')}", type="password")
                ok    = st.form_submit_button(t("login_btn"), use_container_width=True)
            if ok:
                success, udata = do_login(uname, pw)
                if success:
                    st.session_state.logged_in = True
                    st.session_state.username  = uname
                    st.session_state.user_data = udata
                    st.rerun()
                else:
                    st.error(f"❌ {t('login_err')}")
            st.markdown(
                f'<p style="text-align:center;color:#64748b;font-size:0.78rem;">'
                f'Demo: <b style="color:#94a3b8;">admin</b> / <b style="color:#94a3b8;">admin123</b></p>',
                unsafe_allow_html=True)

        # ── REGISTER ──
        with tab_reg:
            with st.form("rf"):
                r_uname = st.text_input(f"👤 {t('username')}", placeholder="john_doe", key="ru")
                r_name  = st.text_input(f"🙍 {t('full_name')}", placeholder="John Doe", key="rn")
                r_email = st.text_input(f"📧 {t('email')}", placeholder="john@uni.kz", key="re")
                r_role  = st.selectbox(f"🎓 {t('role')}", t("roles"), key="rr")
                r_pw    = st.text_input(f"🔑 {t('password')}", type="password", key="rp")
                r_pw2   = st.text_input(f"🔑 {t('confirm_pw')}", type="password", key="rp2")
                r_ok    = st.form_submit_button(t("reg_btn"), use_container_width=True)
            if r_ok:
                if r_pw != r_pw2:
                    st.error(f"❌ {t('pw_mismatch')}")
                else:
                    ok2, code = do_register(r_uname, r_email, r_pw, r_name, r_role)
                    if ok2:
                        st.success(t("reg_ok"))
                    else:
                        msg = t(code) if code in ("username_taken","email_taken",
                                                   "pw_short","uname_short") else code
                        st.error(f"❌ {msg}")

# ════════════════════════════════════════════════════════════════════════════
# SIDEBAR
# ════════════════════════════════════════════════════════════════════════════
def sidebar():
    with st.sidebar:
        lang = st.session_state.lang
        st.markdown(
            f'<div style="font-size:1.4rem;font-weight:900;color:#3b82f6;">📝 Smart Article</div>'
            f'<div style="font-size:0.7rem;color:#64748b;margin-bottom:14px;">{t("tagline")}</div>',
            unsafe_allow_html=True)
        st.divider()

        # Language
        langs = list(TR.keys())
        sel = st.selectbox("🌍", langs, index=langs.index(lang),
                           label_visibility="collapsed", key="lang_sb")
        if sel != lang:
            st.session_state.lang = sel
            st.session_state.page = t("nav_info")
            st.rerun()

        st.divider()

        # Navigation
        wf   = workflow_pages()
        all_ = wf + [t("nav_set")]
        cur  = st.session_state.page if st.session_state.page in all_ else all_[0]
        pg   = st.radio("nav", all_, index=all_.index(cur),
                        label_visibility="collapsed", key="nav_rb")
        if pg != st.session_state.page:
            st.session_state.page = pg; st.rerun()

        st.divider()

        # Quick stats
        at = " ".join(st.session_state.get(k,"") for k in
                      ["intro","methods","results","discussion","conclusion","abstract"])
        w  = wc(at); f = len(st.session_state.figures)
        tb = len(st.session_state.tables); r = len(st.session_state.refs)
        fm = len(st.session_state.formulas)
        st.markdown(
            f'<div style="font-size:0.71rem;color:#64748b;margin-bottom:6px;">📊 Quick Stats</div>'
            f'<span class="qs" style="background:#1e3a5f;color:#60a5fa;">{w} words</span>'
            f'<span class="qs" style="background:#1c3a2e;color:#34d399;">{f} figs</span>'
            f'<span class="qs" style="background:#3a1c1c;color:#f87171;">{r} refs</span>'
            f'<span class="qs" style="background:#2d1b4e;color:#c084fc;">{fm} forms</span>',
            unsafe_allow_html=True)

        st.divider()

        ud = st.session_state.user_data
        st.markdown(
            f'<div style="font-size:0.78rem;color:#94a3b8;">👤 '
            f'<b style="color:#f1f5f9;">{ud.get("name", st.session_state.username)}</b><br>'
            f'<span style="color:#64748b;">{ud.get("role","")}</span></div>',
            unsafe_allow_html=True)
        if st.button(f"🚪 {t('logout')}", use_container_width=True):
            add_log("logout", st.session_state.username)
            st.session_state.logged_in = False; st.rerun()

# ════════════════════════════════════════════════════════════════════════════
# STEPPER + STATS ROW
# ════════════════════════════════════════════════════════════════════════════
def stepper():
    wf = workflow_pages()
    if st.session_state.page not in wf: return
    ci = wf.index(st.session_state.page)
    html = ""
    for i, s in enumerate(wf):
        lbl = s.split(" ",1)[1] if " " in s else s
        cls = "si sd" if i < ci else ("si sa" if i == ci else "si")
        pfx = "✓ " if i < ci else ""
        html += f'<div class="{cls}">{pfx}{lbl}</div>'
        if i < len(wf)-1: html += '<div style="color:#475569;font-size:0.68rem;">›</div>'
    st.markdown(f'<div class="stp">{html}</div>', unsafe_allow_html=True)
    st.progress((ci+1)/len(wf))
    st.caption(f"{t('step')} {ci+1} {t('of_')} {len(wf)}")

def stats_row():
    at = " ".join(st.session_state.get(k,"") for k in
                  ["intro","methods","results","discussion","conclusion","abstract"])
    w   = wc(at)
    sc  = sum(1 for k in ["intro","methods","results","discussion","conclusion"]
              if st.session_state.get(k,"").strip())
    cols = st.columns(6)
    for col, val, lbl in zip(cols,
        [w, sc, len(st.session_state.figures), len(st.session_state.tables),
         len(st.session_state.formulas), len(st.session_state.refs)],
        [t("w_words"),t("w_secs"),t("w_figs"),t("w_tbls"),t("w_forms"),t("w_refs")]):
        col.markdown(
            f'<div class="mc"><div class="mv">{val}</div><div class="ml">{lbl}</div></div>',
            unsafe_allow_html=True)

# ════════════════════════════════════════════════════════════════════════════
# PAGE: ARTICLE INFO
# ════════════════════════════════════════════════════════════════════════════
def pg_info():
    st.markdown(f'<div class="tb"><span class="tt">📄 {t("nav_info")}</span></div>',
                unsafe_allow_html=True)
    stepper(); stats_row(); st.write("")
    L, R = st.columns(2)

    with L:
        st.session_state.art_title   = st.text_input(t("title_f"),   value=st.session_state.art_title,
            placeholder="e.g. Flood Mapping in Kazakhstan Using Sentinel-1 SAR Data")
        st.session_state.authors     = st.text_input(t("authors_f"), value=st.session_state.authors,
            placeholder="Samarkhanov K., Smith J., Doe A.")
        st.session_state.affiliation = st.text_area(t("affil_f"),    value=st.session_state.affiliation,
            height=70, placeholder="Institute of Geography, Almaty, Kazakhstan")
        st.session_state.journal     = st.text_input(t("journal_f"), value=st.session_state.journal,
            placeholder=t("jrn_ph"))
        atypes = t("art_types")
        idx    = min(st.session_state.art_type_idx, len(atypes)-1)
        sel    = st.selectbox(t("art_type_f"), atypes, index=idx)
        st.session_state.art_type_idx = atypes.index(sel)

    with R:
        st.session_state.keywords = st.text_input(t("keywords_f"), value=st.session_state.keywords,
            placeholder=t("kw_ph"))
        st.session_state.abstract = st.text_area(t("abstract_f"),  value=st.session_state.abstract,
            height=200, placeholder="Write your abstract here (150–300 words)…")
        w = wc(st.session_state.abstract)
        color = "#10b981" if 150 <= w <= 300 else ("#f59e0b" if w > 0 else "#64748b")
        st.markdown(f'<span style="color:{color};font-size:0.78rem;">📝 {t("word_count")}: {w}</span>',
                    unsafe_allow_html=True)
        st.markdown("---")
        ab = st.session_state.abstract
        ab_html = (f'<div class="pab"><b>Abstract:</b> {ab[:280]}{"…" if len(ab)>280 else ""}</div>'
                   if ab else "")
        kw_html = (f'<div style="font-size:0.77rem;color:#64748b;margin-top:6px;">'
                   f'<b>Keywords:</b> {st.session_state.keywords}</div>'
                   if st.session_state.keywords else "")
        st.markdown(
            f'<div class="pv" style="min-height:auto;padding:18px;">'
            f'<div class="pt">{st.session_state.art_title or "—"}</div>'
            f'<div class="pa">{st.session_state.authors or "—"}</div>'
            f'<div class="pa" style="font-size:0.8rem;">{st.session_state.affiliation or ""}</div>'
            f'{ab_html}{kw_html}</div>', unsafe_allow_html=True)

# ════════════════════════════════════════════════════════════════════════════
# PAGE: SECTIONS
# ════════════════════════════════════════════════════════════════════════════
def pg_sections():
    st.markdown(f'<div class="tb"><span class="tt">✍️ {t("nav_sec")}</span></div>',
                unsafe_allow_html=True)
    stepper(); stats_row(); st.write("")
    L, R = st.columns(2, gap="large")

    keys   = ["intro","methods","results","discussion","conclusion"]
    labels = [t("intro"),t("methods"),t("results"),t("discussion"),t("conclusion")]

    with L:
        st.subheader(t("sec_editor"))
        tabs = st.tabs(labels)
        for tab, k, lbl in zip(tabs, keys, labels):
            with tab:
                up = st.file_uploader(t("upload_docx"), type=["docx","txt"],
   doc.add_paragraph()

    if st.session_state.refs:
        add_heading_colored("References", 1)
        for i, ref in enumerate(st.session_state.refs, 1):
            p = doc.add_paragraph(fmt_ref(ref, st.session_state.cite_style, i),
                                  style="List Number")
            if p.runs: p.runs[0].font.size = Pt(10)

    buf = BytesIO(); doc.save(buf); buf.seek(0)
    return buf

# ════════════════════════════════════════════════════════════════════════════
# GITHUB GIST
# ════════════════════════════════════════════════════════════════════════════
def gist_save(token: str, content: str, filename: str) -> str | None:
    if not REQ_OK: return None
    resp = requests.post(
        "https://api.github.com/gists",
        headers={"Authorization": f"token {token}",
                 "Accept": "application/vnd.github+json"},
        json={"description": f"Smart Article — {filename}",
              "public": False,
              "files": {filename: {"content": content}}},
        timeout=15)
    if resp.status_code == 201:
        return resp.json()["html_url"]
    return None

def gist_load(token: str, gist_url: str) -> str | None:
    if not REQ_OK: return None
    gist_id = gist_url.rstrip("/").split("/")[-1]
    resp = requests.get(
        f"https://api.github.com/gists/{gist_id}",
        headers={"Authorization": f"token {token}",
                 "Accept": "application/vnd.github+json"},
        timeout=15)
    if resp.status_code == 200:
        files = resp.json().get("files", {})
        for v in files.values():
            return v.get("content","")
    return None

# ════════════════════════════════════════════════════════════════════════════
# PAGE: GENERATE
# ════════════════════════════════════════════════════════════════════════════
def pg_generate():
    st.markdown(f'<div class="tb"><span class="tt">🚀 {t("gen_title")}</span></div>',
                unsafe_allow_html=True)
    stepper(); stats_row(); st.write("")

    if not st.session_state.art_title:
        st.warning(t("warn_title")); return

    done = sum(1 for k in ["intro","methods","results","discussion","conclusion"]
               if st.session_state.get(k,"").strip())
    st.markdown(f"### 📋 {t('completeness')}")
    c1,c2,c3,c4 = st.columns(4)
    c1.progress(done/5, text=f"{done*20}%")
    c2.metric(t("w_secs"),  f"{done}/5")
    c3.metric(t("w_refs"),  len(st.session_state.refs))
    c4.metric(t("w_forms"), len(st.session_state.formulas))
    st.write("")

    st.markdown(f"### {t('preview')}")
    keys   = ["intro","methods","results","discussion","conclusion"]
    labels = [t("intro"),t("methods"),t("results"),t("discussion"),t("conclusion")]

    parts  = [
        f'<div class="pt">{st.session_state.art_title}</div>',
        f'<div class="pa"><b>{st.session_state.authors}</b></div>',
        f'<div class="pa" style="font-size:0.8rem;">{st.session_state.affiliation}</div>',
    ]
    if st.session_state.keywords:
        parts.append(f'<div style="text-align:center;font-size:0.77rem;color:#64748b;">'
                     f'<b>Keywords:</b> {st.session_state.keywords}</div>')
    if st.session_state.abstract:
        ab = st.session_state.abstract
        parts.append(f'<div class="pab"><b>Abstract:</b> '
                     f'{ab[:600]}{"…" if len(ab)>600 else ""}</div>')

    for i,(k,lbl) in enumerate(zip(keys,labels),1):
        c = st.session_state.get(k,"")
        if c:
            parts.append(f'<div class="ph">{i}. {lbl}</div>'
                         f'<p style="font-size:0.84rem;">{c}</p>')

    if st.session_state.formulas:
        parts.append(f'<div class="ph">Formulas</div>')
        for frm in st.session_state.formulas:
            parts.append(f'<p style="text-align:center;font-size:0.86rem;">'
                         f'({frm["number"]})  <code>{frm["latex"]}</code></p>')

    if st.session_state.refs:
        parts.append(f'<div class="ph">References</div>')
        cs = st.session_state.cite_style
        for j,ref in enumerate(st.session_state.refs,1):
            parts.append(f'<p style="font-size:0.81rem;">{fmt_ref(ref,cs,j)}</p>')

    st.markdown(f'<div class="pv">{"".join(parts)}</div>', unsafe_allow_html=True)
    st.write("")

    st.markdown("### 📥 Export")
    fn = sfn(st.session_state.art_title)

    e1, e2, e3 = st.columns(3)

    with e1:
        if DOCX_OK:
            with st.spinner(t("downloading")):
                buf = build_docx()
            st.download_button(
                t("dl_docx"),
                buf,
                f"{fn}.docx",
                "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                use_container_width=True
            )
            st.success(t("success_gen"))
        else:
            st.error("pip install python-docx")

    with e2:
        md_lines = [
            f"# {st.session_state.art_title}",
            f"**{st.session_state.authors}**",
            f"*{st.session_state.affiliation}*",
            "",
            f"**Keywords:** {st.session_state.keywords}",
            "",
            f"## Abstract\n\n{st.session_state.abstract}",
            "",
        ]
        for i, (k, lbl) in enumerate(zip(keys, labels), 1):
            if st.session_state.get(k, ""):
                md_lines += [f"## {i}. {lbl}", st.session_state[k], ""]
        if st.session_state.formulas:
            md_lines.append("## Formulas\n")
            for frm in st.session_state.formulas:
                md_lines.append(f"({frm['number']}) {frm['latex']}")
                if frm.get("desc"):
                    md_lines.append(f"*{frm['desc']}*")
                md_lines.append("")
        if st.session_state.refs:
            md_lines.append("## References\n")
            cs = st.session_state.cite_style
            for j, ref in enumerate(st.session_state.refs, 1):
                md_lines.append(fmt_ref(ref, cs, j))

        st.download_button(
            t("dl_md"),
            "\n".join(md_lines).encode("utf-8"),
            f"{fn}.md",
            "text/markdown",
            use_container_width=True
        )

    with e3:
        proj = {k: st.session_state.get(k, "") for k in [
            "art_title", "authors", "affiliation", "journal", "keywords", "abstract",
            "intro", "methods", "results", "discussion", "conclusion", "cite_style"
        ]}
        proj["refs"] = st.session_state.refs
        proj["formulas"] = st.session_state.formulas
        proj["tables"] = st.session_state.tables
        proj["exported_at"] = datetime.now().isoformat()

        st.download_button(
            t("save_json"),
            json.dumps(proj, ensure_ascii=False, indent=2).encode("utf-8"),
            f"{fn}_project.json",
            "application/json",
            use_container_width=True
        )

    st.write("")
    with st.expander("💬 Feedback", expanded=False):
        with st.form("fb_form", clear_on_submit=True):
            fb_text = st.text_area(
                "Leave a comment or suggestion",
                height=100,
                placeholder="Your feedback helps improve Smart Article…"
            )
            fb_ok = st.form_submit_button("📨 Send Feedback", use_container_width=True)
        if fb_ok and fb_text.strip():
            add_log("feedback", st.session_state.username, fb_text[:200])
            sync_logs_to_github()
            sync_feedback_to_github(st.session_state.username, fb_text)
            _notify_feedback(st.session_state.username, fb_text)
            st.success("✅ Feedback sent! Thank you.")

# ════════════════════════════════════════════════════════════════════════════
# BIBTEX PARSER  (no external library — pure regex)
# ════════════════════════════════════════════════════════════════════════════
def parse_bibtex(text: str) -> list:
    """
    Parse one or multiple BibTeX entries.
    Returns list of reference dicts compatible with session_state.refs format.
    """
    results  = []
    TYPE_MAP = {
        "article":        "Journal Article",
        "book":           "Book",
        "inbook":         "Book Chapter",
        "incollection":   "Book Chapter",
        "inproceedings":  "Conference Paper",
        "conference":     "Conference Paper",
        "proceedings":    "Conference Paper",
        "misc":           "Website",
        "phdthesis":      "Thesis",
        "mastersthesis":  "Thesis",
        "techreport":     "Journal Article",
        "unpublished":    "Journal Article",
    }

    # Split raw text into individual @TYPE{...} blocks
    raw_entries = re.split(r'(?=@\w+\s*[\{\(])', text.strip())

    for raw in raw_entries:
        raw = raw.strip()
        if not raw or not raw.startswith("@"):
            continue

        # ── Entry type ────────────────────────────────────────────
        type_m = re.match(r'@(\w+)\s*[\{\(]', raw, re.IGNORECASE)
        if not type_m:
            continue
        entry_type = type_m.group(1).lower()
        if entry_type in ("comment", "string", "preamble"):
            continue

        fields: dict[str, str] = {}

        # ── Parse field = {value} ─────────────────────────────────
        for m in re.finditer(r'(\w+)\s*=\s*\{((?:[^{}]|\{[^{}]*\})*)\}', raw, re.DOTALL):
            key = m.group(1).lower()
            val = m.group(2).strip()
            val = re.sub(r'\s+', ' ', val)   # collapse whitespace
            val = val.replace("{", "").replace("}", "")  # strip LaTeX braces
            fields[key] = val

        # ── Parse field = "value" ─────────────────────────────────
        for m in re.finditer(r'(\w+)\s*=\s*"([^"]*)"', raw, re.DOTALL):
            key = m.group(1).lower()
            if key not in fields:
                fields[key] = m.group(2).strip()

        # ── Parse field = number ──────────────────────────────────
        for m in re.finditer(r'(\w+)\s*=\s*(\d{4})\b', raw):
            key = m.group(1).lower()
            if key not in fields:
                fields[key] = m.goformat()
                        content  = json.dumps(proj, ensure_ascii=False, indent=2)
                        filename = sfn(st.session_state.art_title or "article") + "_project.json"
                        with st.spinner("Uploading to GitHub Gist…"):
                            url = gist_save(st.session_state.gh_token, content, filename)
                        if url:
                            st.success(t("gh_saved"))
                            st.code(url)
                            add_log("gist_save", st.session_state.username, url)
                        else:
                            st.error(t("gh_err"))

            with G2:
                gist_url_in = st.text_input(t("gh_url"),
                                            placeholder="https://gist.github.com/user/abc123")
                if st.button(t("gh_load"), use_container_width=True):
                    if not st.session_state.gh_token or not gist_url_in:
                        st.error("Enter both token and Gist URL.")
                    else:
                        with st.spinner("Loading from GitHub Gist…"):
                            content = gist_load(st.session_state.gh_token, gist_url_in)
                        if content:
                            try:
                                data = json.loads(content)
                                for f in ["art_title","authors","affiliation","keywords",
                                          "abstract","intro","methods","results","discussion",
                                          "conclusion","refs","formulas","tables"]:
                                    if f in data:
                                        st.session_state[f] = data[f]
                                st.success(t("gh_loaded"))
                                add_log("gist_load", st.session_state.username, gist_url_in)
                            except Exception as e:
                                st.error(f"Parse error: {e}")
                        else:
                            st.error(t("gh_err"))

# ════════════════════════════════════════════════════════════════════════════
# FLOATING ACTION BUTTON
# ════════════════════════════════════════════════════════════════════════════
def fab():
    wf = workflow_pages()
    if st.session_state.page in wf:
        is_gen = st.session_state.page == t("nav_gen")
        col1, col2, col3 = st.columns([6, 2, 2])
        with col3:
            clicked = st.button(
                f"✅ {t('gen_title')}" if is_gen else f"🚀 {t('gen_title')}",
                key="fab_generate_btn",
                use_container_width=True,
                disabled=is_gen
            )
        if clicked and not is_gen:
            st.session_state.page = t("nav_gen")
            st.rerun()

# ════════════════════════════════════════════════════════════════════════════
# MAIN
# ════════════════════════════════════════════════════════════════════════════
def main():
    if not st.session_state.logged_in:
        auth_page(); return

    inject_css(dark=st.session_state.dark)
    sidebar()

    pg = st.session_state.page
    routes = {
        t("nav_info"):  pg_info,
        t("nav_sec"):   pg_sections,
        t("nav_fig"):   pg_figures,
        t("nav_tbl"):   pg_tables,
        t("nav_form"):  pg_formulas,
        t("nav_ref"):   pg_refs,
        t("nav_gen"):   pg_generate,
        t("nav_set"):   pg_settings,
    }
    routes.get(pg, pg_info)()
    fab()

if __name__ == "__main__":
    main()

