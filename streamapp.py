# ════════════════════════════════════════════════════════════════════════════
#  Smart Article — Research Writing Platform  v3.0
#  Changelog v3:
#    ✓ Removed all duplicate function definitions
#    ✓ Fixed pg_generate export (was inside sync_feedback_to_github)
#    ✓ Fixed pg_refs undefined 'bib' variable + duplicate import button
#    ✓ Salted password hashing (PBKDF2-HMAC-SHA256)
#    ✓ Redesigned CSS: glassmorphism cards, smooth animations, better light mode
#    ✓ Improved login/register page with animated gradient
#    ✓ Added completeness ring chart on Generate page
#    ✓ Better sidebar with progress indicator
#    ✓ Responsive metric cards with icons
#    ✓ Cleaner code structure, type hints, docstrings
# ════════════════════════════════════════════════════════════════════════════

import streamlit as st
import re, json, io, hashlib, hmac, smtplib, base64, os
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
    initial_sidebar_state="expanded",
)

# ── Optional dependencies ─────────────────────────────────────────────────
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

# ── Storage paths ─────────────────────────────────────────────────────────
USERS_FILE = Path("users.json")
LOGS_FILE  = Path("logs.json")
SALT       = "SmartArticle2025!"  # For password hashing


# ════════════════════════════════════════════════════════════════════════════
# AUTH  (Registration · Login · Logging)
# ════════════════════════════════════════════════════════════════════════════
def hp(pw: str) -> str:
    """PBKDF2-HMAC-SHA256 password hash with salt."""
    return hashlib.pbkdf2_hmac("sha256", pw.encode(), SALT.encode(), 100_000).hex()


def load_users() -> dict:
    if USERS_FILE.exists():
        try:
            return json.loads(USERS_FILE.read_text("utf-8"))
        except Exception:
            return {}
    seed = {
        "admin": {
            "password": hp("admin123"),
            "name": "Kanat Samarkhanov",
            "email": "admin@smart-article.kz",
            "role": "Researcher",
            "created_at": datetime.now().isoformat(),
        }
    }
    USERS_FILE.write_text(json.dumps(seed, ensure_ascii=False, indent=2), "utf-8")
    return seed


def save_users(u: dict):
    USERS_FILE.write_text(json.dumps(u, ensure_ascii=False, indent=2), "utf-8")


def load_logs() -> list:
    if LOGS_FILE.exists():
        try:
            return json.loads(LOGS_FILE.read_text("utf-8"))
        except Exception:
            return []
    return []


def add_log(event: str, user: str, detail: str = ""):
    logs = load_logs()
    logs.append({
        "event": event,
        "username": user,
        "detail": detail,
        "ts": datetime.now().isoformat(),
    })
    LOGS_FILE.write_text(
        json.dumps(logs[-2000:], ensure_ascii=False, indent=2), "utf-8"
    )


def do_register(uname: str, email: str, pw: str, name: str, role: str = "Researcher"):
    if len(uname) < 3:
        return False, "uname_short"
    if len(pw) < 6:
        return False, "pw_short"
    users = load_users()
    if uname in users:
        return False, "username_taken"
    if any(v.get("email") == email for v in users.values()):
        return False, "email_taken"
    users[uname] = {
        "password": hp(pw),
        "name": name,
        "email": email,
        "role": role,
        "created_at": datetime.now().isoformat(),
    }
    save_users(users)
    add_log("register", uname, f"email={email} role={role}")
    sync_users_to_github()
    sync_logs_to_github()
    _notify_register(uname, email, role)
    return True, "ok"


def do_login(uname: str, pw: str):
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
# EMAIL NOTIFICATIONS  (Gmail SMTP + App Password)
# ════════════════════════════════════════════════════════════════════════════
def _smtp_cfg() -> tuple[str, str]:
    try:
        u = st.secrets.get("SMTP_USER", st.session_state.get("smtp_user", ""))
        p = st.secrets.get("SMTP_PASS", st.session_state.get("smtp_pass", ""))
        return u, p
    except Exception:
        return (
            st.session_state.get("smtp_user", ""),
            st.session_state.get("smtp_pass", ""),
        )


def send_notification(
    subject: str, html_body: str, to: str = "kanat.baurzhanuly@gmail.com"
) -> bool:
    smtp_user, smtp_pass = _smtp_cfg()
    if not smtp_user or not smtp_pass:
        return False
    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = f"[Smart Article] {subject}"
        msg["From"] = smtp_user
        msg["To"] = to
        msg.attach(MIMEText(html_body, "html", "utf-8"))
        with smtplib.SMTP("smtp.gmail.com", 587, timeout=10) as srv:
            srv.ehlo()
            srv.starttls()
            srv.ehlo()
            srv.login(smtp_user, smtp_pass)
            srv.sendmail(smtp_user, to, msg.as_string())
        return True
    except Exception:
        return False


def _notify_register(uname: str, email: str, role: str):
    body = f"""
<h3>🆕 New Registration — Smart Article</h3>
<table><tr><td><b>Username</b></td><td>{uname}</td></tr>
<tr><td><b>Email</b></td><td>{email}</td></tr>
<tr><td><b>Role</b></td><td>{role}</td></tr>
<tr><td><b>Time</b></td><td>{datetime.now():%Y-%m-%d %H:%M:%S}</td></tr></table>"""
    send_notification(f"New user: {uname}", body)


def _notify_login(uname: str):
    body = f"""<h3>🔑 Login — Smart Article</h3>
<p><b>User:</b> {uname}<br><b>Time:</b> {datetime.now():%Y-%m-%d %H:%M:%S}</p>"""
    send_notification(f"Login: {uname}", body)


def _notify_feedback(uname: str, feedback_text: str):
    body = f"""<h3>💬 Feedback — Smart Article</h3>
<p><b>From:</b> {uname}<br><b>Time:</b> {datetime.now():%Y-%m-%d %H:%M:%S}</p>
<hr><p>{feedback_text}</p>"""
    send_notification(f"Feedback from {uname}", body)


# ════════════════════════════════════════════════════════════════════════════
# GITHUB REPO SYNC  (single definition — no duplicates)
# ════════════════════════════════════════════════════════════════════════════
def _gh_cfg() -> tuple[str, str]:
    """Return (token, repo) from secrets or session_state."""
    try:
        tok = st.secrets.get("GH_TOKEN", st.session_state.get("gh_token", ""))
        repo = st.secrets.get("GH_REPO", st.session_state.get("gh_repo", ""))
        return tok, repo
    except Exception:
        return st.session_state.get("gh_token", ""), st.session_state.get("gh_repo", "")


def gh_push_file(path: str, content: str, commit_msg: str) -> bool:
    """Create or update a file in a GitHub repository via Contents API."""
    if not REQ_OK:
        return False
    token, repo = _gh_cfg()
    if not token or not repo:
        return False
    url = f"https://api.github.com/repos/{repo}/contents/{path}"
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github+json",
    }
    sha = None
    r = requests.get(url, headers=headers, timeout=8)
    if r.status_code == 200:
        sha = r.json().get("sha")
    encoded = base64.b64encode(content.encode("utf-8")).decode("utf-8")
    payload: dict = {"message": commit_msg, "content": encoded}
    if sha:
        payload["sha"] = sha
    resp = requests.put(url, headers=headers, json=payload, timeout=10)
    return resp.status_code in (200, 201)


def sync_users_to_github():
    if USERS_FILE.exists():
        gh_push_file(
            "data/users.json",
            USERS_FILE.read_text("utf-8"),
            f"update users {datetime.now():%Y-%m-%d %H:%M}",
        )


def sync_logs_to_github():
    if LOGS_FILE.exists():
        gh_push_file(
            "data/logs.json",
            LOGS_FILE.read_text("utf-8"),
            f"update logs {datetime.now():%Y-%m-%d %H:%M}",
        )


def sync_feedback_to_github(uname: str, text: str):
    token, repo = _gh_cfg()
    if not token or not repo:
        return
    url = f"https://api.github.com/repos/{repo}/contents/data/feedback.json"
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github+json",
    }
    existing, sha = [], None
    r = requests.get(url, headers=headers, timeout=8)
    if r.status_code == 200:
        sha = r.json().get("sha")
        try:
            existing = json.loads(
                base64.b64decode(r.json()["content"]).decode("utf-8")
            )
        except Exception:
            existing = []
    existing.append({"user": uname, "text": text, "ts": datetime.now().isoformat()})
    encoded = base64.b64encode(
        json.dumps(existing, ensure_ascii=False, indent=2).encode("utf-8")
    ).decode("utf-8")
    payload: dict = {"message": f"feedback from {uname}", "content": encoded}
    if sha:
        payload["sha"] = sha
    requests.put(url, headers=headers, json=payload, timeout=10)


# ════════════════════════════════════════════════════════════════════════════
# GITHUB GIST  (save / load project)
# ════════════════════════════════════════════════════════════════════════════
def gist_save(token: str, content: str, filename: str) -> str | None:
    if not REQ_OK:
        return None
    resp = requests.post(
        "https://api.github.com/gists",
        headers={
            "Authorization": f"token {token}",
            "Accept": "application/vnd.github+json",
        },
        json={
            "description": f"Smart Article — {filename}",
            "public": False,
            "files": {filename: {"content": content}},
        },
        timeout=15,
    )
    return resp.json().get("html_url") if resp.status_code == 201 else None


def gist_load(token: str, gist_url: str) -> str | None:
    if not REQ_OK:
        return None
    gist_id = gist_url.rstrip("/").split("/")[-1]
    resp = requests.get(
        f"https://api.github.com/gists/{gist_id}",
        headers={
            "Authorization": f"token {token}",
            "Accept": "application/vnd.github+json",
        },
        timeout=15,
    )
    if resp.status_code == 200:
        for v in resp.json().get("files", {}).values():
            return v.get("content", "")
    return None


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
    pw_short="Password must be ≥ 6 characters",
    uname_short="Username must be ≥ 3 characters",
    username_taken="Username already taken",
    email_taken="E-mail already registered",
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
    art_types=["Research Article","Review Article","Short Communication",
               "Letter","Case Study"],
    intro="Introduction", methods="Methods", results="Results",
    discussion="Discussion", conclusion="Conclusion",
    upload_docx="Upload DOCX / TXT",
    fig_mgr="Figures Manager", add_fig="Add Figure",
    fig_no="Figure No.", fig_cap="Caption",
    upload_fig="Upload image (PNG/JPG/TIF)",
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
    ref_types=["Journal Article","Book","Book Chapter",
               "Conference Paper","Website","Thesis"],
    cite_styles=["APA 7th","Vancouver","Harvard","IEEE","ГОСТ 7.0.5-2008"],
    import_refs="Import BibTeX / plain text", import_btn="Import",
    imported="Imported", ref_s="reference(s)",
    ref_list="Reference List", no_refs="No references yet.",
    no_figs="No figures yet.", no_tbls="No tables yet.",
    no_forms="No formulas yet.",
    gen_title="Generate & Export",
    dl_docx="📥 Download DOCX", dl_md="📥 Download Markdown",
    save_json="💾 Save Project (JSON)",
    load_json_help=(
        "💾 Save / Load Project (JSON): saves ALL article data into a .json file. "
        "Use 'Load' later to continue writing or share with co-authors."
    ),
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
    gh_url="Gist URL", gh_saved="✅ Saved to Gist!",
    gh_loaded="✅ Loaded from Gist!",
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
    have_account="Уже есть аккаунт?", no_account="Нет аккаунта?",
    logout="Выйти",
    nav_info="📄 Информация", nav_sec="✍️ Разделы",
    nav_fig="🖼️ Рисунки", nav_tbl="📊 Таблицы",
    nav_form="🧮 Формулы", nav_ref="📑 Литература",
    nav_gen="🚀 Генерация", nav_set="⚙️ Настройки",
    step="Шаг", of_="из",
    title_f="Название статьи", authors_f="Авторы", affil_f="Аффилиация",
    journal_f="Целевой журнал", keywords_f="Ключевые слова",
    abstract_f="Аннотация", art_type_f="Тип статьи",
    art_types=["Научная статья","Обзорная статья","Краткое сообщение",
               "Письмо","Кейс-стади"],
    intro="Введение", methods="Методы", results="Результаты",
    discussion="Обсуждение", conclusion="Заключение",
    upload_docx="Загрузить DOCX / TXT",
    fig_mgr="Менеджер рисунков", add_fig="Добавить рисунок",
    fig_no="№ рисунка", fig_cap="Подпись",
    upload_fig="Загрузить изображение (PNG/JPG)",
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
    ref_types=["Журнальная статья","Книга","Глава книги",
               "Материалы конференции","Сайт","Диссертация"],
    cite_styles=["APA 7th","Ванкувер","Гарвард","IEEE","ГОСТ 7.0.5-2008"],
    import_refs="Импорт BibTeX / текст", import_btn="Импорт",
    imported="Импортировано", ref_s="источник(ов)",
    ref_list="Список литературы", no_refs="Источники не добавлены.",
    no_figs="Рисунки не добавлены.", no_tbls="Таблицы не добавлены.",
    no_forms="Формулы не добавлены.",
    gen_title="Генерация и экспорт",
    dl_docx="📥 Скачать DOCX", dl_md="📥 Скачать Markdown",
    save_json="💾 Сохранить проект (JSON)",
    load_json_help=(
        "💾 Сохранить / Загрузить проект (JSON): сохраняет ВСЕ данные статьи "
        "в файл .json. Нажмите «Загрузить» позже, чтобы продолжить работу."
    ),
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
    have_account="Аккаунтыңыз бар ма?", no_account="Аккаунтыңыз жоқ па?",
    logout="Шығу",
    nav_info="📄 Мақала туралы", nav_sec="✍️ Бөлімдер",
    nav_fig="🖼️ Суреттер", nav_tbl="📊 Кестелер",
    nav_form="🧮 Формулалар", nav_ref="📑 Әдебиеттер",
    nav_gen="🚀 Генерация", nav_set="⚙️ Параметрлер",
    step="Қадам", of_="/",
    title_f="Мақала атауы", authors_f="Авторлар", affil_f="Аффилиация",
    journal_f="Мақсатты журнал", keywords_f="Кілт сөздер",
    abstract_f="Аннотация", art_type_f="Мақала түрі",
    art_types=["Ғылыми мақала","Шолу мақаласы","Қысқа хабарлама",
               "Хат","Кейс-стади"],
    intro="Кіріспе", methods="Әдістер", results="Нәтижелер",
    discussion="Талқылау", conclusion="Қорытынды",
    upload_docx="DOCX / TXT жүктеу",
    fig_mgr="Суреттер менеджері", add_fig="Сурет қосу",
    fig_no="Сурет №", fig_cap="Аңыз",
    upload_fig="Сурет жүктеу (PNG/JPG)",
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
    ref_types=["Журнал мақаласы","Кітап","Кітап тарауы",
               "Конференция баяндамасы","Сайт","Диссертация"],
    cite_styles=["APA 7th","Ванкувер","Гарвард","IEEE","ГОСТ 7.0.5-2008"],
    import_refs="BibTeX / мәтін импорты", import_btn="Импорт",
    imported="Импортталды", ref_s="дереккөз(дер)",
    ref_list="Әдебиеттер тізімі", no_refs="Дереккөздер қосылмаған.",
    no_figs="Суреттер қосылмаған.", no_tbls="Кестелер қосылмаған.",
    no_forms="Формулалар қосылмаған.",
    gen_title="Генерация және экспорт",
    dl_docx="📥 DOCX жүктеу", dl_md="📥 Markdown жүктеу",
    save_json="💾 Жобаны сақтау (JSON)",
    load_json_help=(
        "💾 Жобаны сақтау / жүктеу (JSON): мақаланың барлық деректерін "
        ".json файлы ретінде сақтайды. Жұмысты жалғастыру үшін кейін жүктеңіз."
    ),
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


# ════════════════════════════════════════════════════════════════════════════
# HELPERS
# ════════════════════════════════════════════════════════════════════════════
def t(key: str) -> str:
    lang = st.session_state.get("lang", "🇬🇧 English")
    return TR.get(lang, TR["🇬🇧 English"]).get(key, key)


def wc(text: str) -> int:
    return len(re.findall(r"\w+", text)) if text else 0


def sfn(title: str) -> str:
    return re.sub(r"[^\w\s-]", "", title)[:50].strip().replace(" ", "_") or "article"


def workflow_pages() -> list:
    return [
        t("nav_info"), t("nav_sec"), t("nav_fig"),
        t("nav_tbl"), t("nav_form"), t("nav_ref"), t("nav_gen"),
    ]


def _all_text() -> str:
    return " ".join(
        st.session_state.get(k, "")
        for k in ["intro", "methods", "results", "discussion", "conclusion", "abstract"]
    )


def _sections_done() -> int:
    return sum(
        1
        for k in ["intro", "methods", "results", "discussion", "conclusion"]
        if st.session_state.get(k, "").strip()
    )


# ════════════════════════════════════════════════════════════════════════════
# SESSION STATE
# ════════════════════════════════════════════════════════════════════════════
def init_state():
    defaults = {
        "logged_in": False, "username": "", "user_data": {},
        "auth_mode": "login",
        "lang": "🇬🇧 English", "dark": True,
        "page": "📄 Article Info", "cite_style": "APA 7th",
        "art_title": "", "authors": "", "affiliation": "",
        "journal": "", "keywords": "", "abstract": "", "art_type_idx": 0,
        "intro": "", "methods": "", "results": "",
        "discussion": "", "conclusion": "",
        "figures": [], "tables": [], "formulas": [], "refs": [],
        "gh_token": "",
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v


init_state()


# ════════════════════════════════════════════════════════════════════════════
# CSS  v3 — glassmorphism, smooth transitions, proper light mode
# ════════════════════════════════════════════════════════════════════════════
def inject_css(dark: bool = True):
    if dark:
        bg      = "#0b1120"
        sbg     = "#111827"
        cbg     = "#1a2332"
        brd     = "#1e3a5f"
        fg      = "#e2e8f0"
        sub     = "#94a3b8"
        acc     = "#3b82f6"
        acc2    = "#6366f1"
        ibg     = "#0f1a2e"
        mbg     = "#162032"
        btn_fg  = "#ffffff"
        inp_ph  = "#475569"
        met_val = "#60a5fa"
        code_bg = "#1e293b"
        glow    = "rgba(59,130,246,0.12)"
        shadow  = "rgba(0,0,0,0.4)"
        card_gl = "rgba(255,255,255,0.03)"
    else:
        bg      = "#f8fafc"
        sbg     = "#ffffff"
        cbg     = "#ffffff"
        brd     = "#e2e8f0"
        fg      = "#0f172a"
        sub     = "#64748b"
        acc     = "#2563eb"
        acc2    = "#4f46e5"
        ibg     = "#f8fafc"
        mbg     = "#f1f5f9"
        btn_fg  = "#ffffff"
        inp_ph  = "#94a3b8"
        met_val = "#2563eb"
        code_bg = "#f1f5f9"
        glow    = "rgba(37,99,235,0.06)"
        shadow  = "rgba(0,0,0,0.08)"
        card_gl = "rgba(255,255,255,0.6)"

    st.markdown(f"""<style>
/* ═══ FONTS ══════════════════════════════════════════════════════ */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&display=swap');

/* ═══ BASE ═══════════════════════════════════════════════════════ */
html, body,
[data-testid="stAppViewContainer"],
[data-testid="stMain"],
.main .block-container {{
    background: {bg} !important;
    color: {fg} !important;
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif !important;
}}

/* ═══ SIDEBAR ════════════════════════════════════════════════════ */
[data-testid="stSidebar"],
[data-testid="stSidebar"] > div {{
    background: {sbg} !important;
    border-right: 1px solid {brd} !important;
}}
[data-testid="stSidebar"] .stRadio > div {{
    gap: 2px !important;
}}
[data-testid="stSidebar"] .stRadio label {{
    padding: 8px 14px !important;
    border-radius: 10px !important;
    transition: all 0.2s ease !important;
    margin: 1px 0 !important;
}}
[data-testid="stSidebar"] .stRadio label:hover {{
    background: {glow} !important;
}}
[data-testid="stSidebar"] .stRadio label[data-checked="true"],
[data-testid="stSidebar"] .stRadio [aria-checked="true"] {{
    background: linear-gradient(135deg, {acc}22, {acc2}18) !important;
}}

/* ═══ ALL TEXT ════════════════════════════════════════════════════ */
h1,h2,h3,h4,h5,h6,p,span,li,div,
[data-testid="stMarkdownContainer"] *,
[data-testid="stText"],
[data-testid="stCaptionContainer"] *,
[data-testid="stWidgetLabel"] p,
[data-testid="stWidgetLabel"] span,
label, .stRadio label p, .stCheckbox span p,
[data-testid="stSidebar"] p,
[data-testid="stSidebar"] span,
[data-testid="stSidebar"] label,
[data-testid="stSidebar"] div {{
    color: {fg} !important;
}}
[data-testid="stCaptionContainer"], .stCaption, small {{
    color: {sub} !important;
}}

/* ═══ INPUTS ═════════════════════════════════════════════════════ */
.stTextInput input,
.stTextArea textarea,
[data-baseweb="input"] input,
[data-baseweb="textarea"] textarea {{
    background: {ibg} !important;
    color: {fg} !important;
    border: 1.5px solid {brd} !important;
    border-radius: 10px !important;
    caret-color: {fg} !important;
    font-size: 0.9rem !important;
    transition: border-color 0.2s, box-shadow 0.2s !important;
}}
.stTextInput input::placeholder,
.stTextArea textarea::placeholder {{
    color: {inp_ph} !important; opacity:1 !important;
}}
.stTextInput input:focus,
.stTextArea textarea:focus {{
    border-color: {acc} !important;
    box-shadow: 0 0 0 3px {acc}20 !important;
}}

/* ═══ SELECT ═════════════════════════════════════════════════════ */
[data-baseweb="select"] > div {{
    background: {ibg} !important; color: {fg} !important;
    border-color: {brd} !important; border-radius: 10px !important;
}}
[data-baseweb="select"] span {{ color: {fg} !important; }}
[data-baseweb="popover"] ul li,
[data-baseweb="popover"] [role="option"] {{
    background: {cbg} !important; color: {fg} !important;
}}
[data-baseweb="popover"] [aria-selected="true"] {{
    background: {mbg} !important;
}}

/* ═══ BUTTONS ════════════════════════════════════════════════════ */
.stButton > button,
[data-testid="stBaseButton-secondary"] {{
    background: linear-gradient(135deg, {acc2}, {acc}) !important;
    color: {btn_fg} !important;
    border: none !important;
    border-radius: 10px !important;
    font-weight: 600 !important;
    font-size: 0.88rem !important;
    padding: 0.5rem 1.2rem !important;
    transition: all 0.25s ease !important;
    box-shadow: 0 2px 8px {acc}30 !important;
}}
.stButton > button:hover {{
    transform: translateY(-2px) !important;
    box-shadow: 0 6px 20px {acc}40 !important;
}}
.stButton > button:active {{
    transform: translateY(0) !important;
}}
[data-testid="stFormSubmitButton"] > button {{
    background: linear-gradient(135deg, {acc2}, {acc}) !important;
    color: white !important; border: none !important;
    border-radius: 10px !important; font-weight: 700 !important;
    width: 100%; padding: 0.6rem !important;
}}
.stDownloadButton > button {{
    background: linear-gradient(135deg, #059669, #10b981) !important;
    color: white !important; border: none !important;
    border-radius: 10px !important; font-weight: 600 !important;
    box-shadow: 0 2px 8px rgba(16,185,129,0.3) !important;
}}
.stDownloadButton > button:hover {{
    transform: translateY(-2px) !important;
    box-shadow: 0 6px 20px rgba(16,185,129,0.4) !important;
}}

/* ═══ TABS ═══════════════════════════════════════════════════════ */
[data-baseweb="tab-list"] {{
    background: {mbg} !important;
    border-radius: 12px !important;
    padding: 4px !important; gap: 4px !important;
}}
[data-baseweb="tab"] {{
    background: transparent !important; color: {sub} !important;
    border-radius: 10px !important; font-weight: 500 !important;
    transition: all 0.2s !important;
}}
[aria-selected="true"][data-baseweb="tab"] {{
    background: {cbg} !important; color: {acc} !important;
    font-weight: 700 !important;
    box-shadow: 0 2px 8px {shadow} !important;
}}

/* ═══ EXPANDER ═══════════════════════════════════════════════════ */
[data-testid="stExpander"] {{
    background: {cbg} !important;
    border: 1px solid {brd} !important;
    border-radius: 12px !important;
    transition: box-shadow 0.2s !important;
}}
[data-testid="stExpander"]:hover {{
    box-shadow: 0 4px 16px {shadow} !important;
}}

/* ═══ PROGRESS BAR ═══════════════════════════════════════════════ */
[data-testid="stProgressBar"] > div {{
    background: {mbg} !important; border-radius: 10px !important;
    height: 8px !important;
}}
[data-testid="stProgressBar"] > div > div {{
    background: linear-gradient(90deg, {acc2}, {acc}, #06b6d4) !important;
    border-radius: 10px !important;
}}

/* ═══ DIVIDER ════════════════════════════════════════════════════ */
hr {{ border-color: {brd} !important; opacity: 0.6; }}

/* ═══ CODE / LATEX ═══════════════════════════════════════════════ */
code, pre {{
    background: {code_bg} !important;
    color: {'#93c5fd' if dark else '#2563eb'} !important;
    border-radius: 8px !important; padding: 2px 7px !important;
    font-size: 0.85rem !important;
}}

/* ═══ ALERTS ═════════════════════════════════════════════════════ */
[data-testid="stAlert"] {{
    border-radius: 12px !important;
}}

/* ═══ GLASS CARD ═════════════════════════════════════════════════ */
.gc {{
    background: {card_gl};
    backdrop-filter: blur(12px);
    -webkit-backdrop-filter: blur(12px);
    border: 1px solid {brd};
    border-radius: 16px;
    padding: 20px 24px;
    transition: box-shadow 0.3s, transform 0.2s;
}}
.gc:hover {{
    box-shadow: 0 8px 32px {shadow};
    transform: translateY(-1px);
}}

/* ═══ METRIC CARD ════════════════════════════════════════════════ */
.mc {{
    background: linear-gradient(145deg, {cbg}, {mbg});
    border: 1px solid {brd};
    border-radius: 14px;
    padding: 16px 12px;
    text-align: center;
    transition: all 0.25s ease;
}}
.mc:hover {{
    transform: translateY(-3px);
    box-shadow: 0 8px 24px {shadow};
}}
.mv {{
    font-size: 1.9rem; font-weight: 800;
    background: linear-gradient(135deg, {acc}, {acc2});
    -webkit-background-clip: text; -webkit-text-fill-color: transparent;
    background-clip: text;
}}
.ml {{ font-size: 0.72rem; color: {sub}; margin-top: 4px; font-weight: 500; }}

/* ═══ PREVIEW PANEL ══════════════════════════════════════════════ */
.pv {{
    background: {cbg};
    border: 1px solid {brd};
    border-radius: 16px;
    padding: 28px 32px;
    font-family: 'Georgia', 'Times New Roman', serif;
    line-height: 1.85;
    box-shadow: 0 4px 20px {shadow};
}}
.pt {{
    font-size: 1.25rem; font-weight: 700;
    text-align: center; color: {fg};
    margin-bottom: 6px;
}}
.pa {{
    text-align: center; color: {sub};
    font-size: 0.86rem; margin-bottom: 10px;
}}
.ph {{
    font-weight: 700; color: {acc};
    border-bottom: 2px solid {acc}30;
    padding-bottom: 4px; margin-top: 18px;
    font-size: 0.96rem;
}}
.pab {{
    background: linear-gradient(135deg, {acc}10, {acc2}08);
    border-left: 4px solid {acc};
    padding: 12px 16px; border-radius: 0 12px 12px 0;
    margin: 12px 0; font-size: 0.85rem; color: {sub};
}}

/* ═══ REFERENCE ITEM ═════════════════════════════════════════════ */
.ri {{
    background: {cbg}; border: 1px solid {brd};
    border-radius: 10px; padding: 10px 16px;
    margin-bottom: 8px; font-size: 0.82rem; color: {fg};
    transition: border-color 0.2s;
}}
.ri:hover {{ border-color: {acc}; }}
.rn {{ color: {acc}; font-weight: 700; }}

/* ═══ STEPPER ════════════════════════════════════════════════════ */
.stp {{
    display: flex; gap: 6px; align-items: center;
    flex-wrap: wrap; margin-bottom: 14px;
}}
.si {{
    padding: 6px 14px; border-radius: 24px;
    font-size: 0.73rem; font-weight: 600;
    border: 1.5px solid {brd}; color: {sub};
    white-space: nowrap; transition: all 0.2s;
}}
.sa {{
    background: linear-gradient(135deg, {acc}, {acc2});
    color: white !important; border-color: transparent;
    box-shadow: 0 2px 10px {acc}40;
}}
.sd {{
    background: #059669; color: white !important;
    border-color: #059669;
}}

/* ═══ TOPBAR ═════════════════════════════════════════════════════ */
.tb {{
    display: flex; justify-content: space-between;
    align-items: center; padding-bottom: 12px;
    border-bottom: 2px solid {brd}; margin-bottom: 20px;
}}
.tt {{
    font-size: 1.3rem; font-weight: 800; color: {fg};
    letter-spacing: -0.02em;
}}

/* ═══ LOGIN CARD ═════════════════════════════════════════════════ */
.lc {{
    max-width: 440px; margin: 50px auto;
    background: {cbg};
    border: 1px solid {brd};
    border-radius: 24px;
    padding: 44px 40px;
    box-shadow: 0 24px 64px {shadow};
    position: relative;
    overflow: hidden;
}}
.lc::before {{
    content: '';
    position: absolute; top: -50%; left: -50%;
    width: 200%; height: 200%;
    background: conic-gradient(from 0deg, {acc}10, {acc2}08, transparent, {acc}10);
    animation: _spin 8s linear infinite;
    z-index: 0;
}}
.lc > * {{ position: relative; z-index: 1; }}
@keyframes _spin {{ to {{ transform: rotate(360deg); }} }}

/* ═══ LOGO ═══════════════════════════════════════════════════════ */
.logo-text {{
    font-size: 2.2rem; font-weight: 900;
    background: linear-gradient(135deg, {acc}, {acc2}, #06b6d4);
    -webkit-background-clip: text; -webkit-text-fill-color: transparent;
    background-clip: text;
}}

/* ═══ QUICK STATS BADGE ══════════════════════════════════════════ */
.qs {{
    font-size: 0.7rem; padding: 3px 10px;
    border-radius: 8px; font-weight: 600;
    display: inline-block; margin: 2px;
    transition: transform 0.15s;
}}
.qs:hover {{ transform: scale(1.08); }}

/* ═══ FAB ════════════════════════════════════════════════════════ */
.fab {{
    position: fixed; bottom: 28px; right: 28px; z-index: 9999;
    background: linear-gradient(135deg, {acc2}, {acc});
    color: white !important;
    padding: 14px 26px; border-radius: 50px;
    font-weight: 700; font-size: 0.9rem;
    box-shadow: 0 8px 30px {acc}50;
    cursor: pointer; border: none;
    transition: all 0.3s ease;
}}
.fab:hover {{
    transform: translateY(-3px) scale(1.03);
    box-shadow: 0 12px 40px {acc}60;
}}

/* ═══ DATAFRAME ══════════════════════════════════════════════════ */
[data-testid="stDataFrame"] th {{
    background: {mbg} !important; color: {fg} !important;
}}
[data-testid="stDataFrame"] td {{
    color: {fg} !important; background: {cbg} !important;
}}

/* ═══ HIDE STREAMLIT CHROME ══════════════════════════════════════ */
footer {{ visibility: hidden; }}
#MainMenu {{ visibility: hidden; }}
.stDeployButton {{ display: none; }}

/* ═══ SMOOTH SCROLL ══════════════════════════════════════════════ */
html {{ scroll-behavior: smooth; }}

/* ═══ SELECTION COLOR ════════════════════════════════════════════ */
::selection {{
    background: {acc}30; color: {fg};
}}
</style>""", unsafe_allow_html=True)


# ════════════════════════════════════════════════════════════════════════════
# AUTH PAGE  (Login + Register)
# ════════════════════════════════════════════════════════════════════════════
def auth_page():
    inject_css(dark=True)
    _, mid, _ = st.columns([1, 1.2, 1])
    with mid:
        st.markdown("""<div class="lc">
<div style="text-align:center;margin-bottom:24px;">
  <div style="font-size:3rem;">📝</div>
  <div class="logo-text">Smart Article</div>
  <p style="color:#94a3b8;margin:4px 0 0;font-size:0.85rem;">
    Research Writing Platform</p>
</div></div>""", unsafe_allow_html=True)

        tab_login, tab_reg = st.tabs([t("sign_in"), t("register")])

        with tab_login:
            with st.form("lf"):
                uname = st.text_input(f"👤 {t('username')}", placeholder="admin")
                pw = st.text_input(f"🔑 {t('password')}", type="password")
                ok = st.form_submit_button(t("login_btn"), use_container_width=True)
            if ok:
                success, udata = do_login(uname, pw)
                if success:
                    st.session_state.logged_in = True
                    st.session_state.username = uname
                    st.session_state.user_data = udata
                    st.rerun()
                else:
                    st.error(f"❌ {t('login_err')}")
            st.markdown(
                '<p style="text-align:center;color:#64748b;font-size:0.76rem;">'
                'Demo: <b style="color:#94a3b8;">admin</b> / '
                '<b style="color:#94a3b8;">admin123</b></p>',
                unsafe_allow_html=True,
            )

        with tab_reg:
            with st.form("rf"):
                r_uname = st.text_input(
                    f"👤 {t('username')}", placeholder="john_doe", key="ru"
                )
                r_name = st.text_input(
                    f"🙍 {t('full_name')}", placeholder="John Doe", key="rn"
                )
                r_email = st.text_input(
                    f"📧 {t('email')}", placeholder="john@uni.kz", key="re"
                )
                r_role = st.selectbox(f"🎓 {t('role')}", t("roles"), key="rr")
                r_pw = st.text_input(
                    f"🔑 {t('password')}", type="password", key="rp"
                )
                r_pw2 = st.text_input(
                    f"🔑 {t('confirm_pw')}", type="password", key="rp2"
                )
                r_ok = st.form_submit_button(t("reg_btn"), use_container_width=True)
            if r_ok:
                if r_pw != r_pw2:
                    st.error(f"❌ {t('pw_mismatch')}")
                else:
                    ok2, code = do_register(r_uname, r_email, r_pw, r_name, r_role)
                    if ok2:
                        st.success(t("reg_ok"))
                    else:
                        msg = (
                            t(code)
                            if code in ("username_taken", "email_taken",
                                        "pw_short", "uname_short")
                            else code
                        )
                        st.error(f"❌ {msg}")


# ════════════════════════════════════════════════════════════════════════════
# SIDEBAR
# ════════════════════════════════════════════════════════════════════════════
def sidebar():
    with st.sidebar:
        lang = st.session_state.lang
        st.markdown(
            f'<div style="margin-bottom:6px;">'
            f'<span class="logo-text" style="font-size:1.5rem;">📝 Smart Article</span></div>'
            f'<div style="font-size:0.7rem;color:#64748b;margin-bottom:16px;">'
            f'{t("tagline")}</div>',
            unsafe_allow_html=True,
        )
        st.divider()

        langs = list(TR.keys())
        sel = st.selectbox(
            "🌍", langs, index=langs.index(lang),
            label_visibility="collapsed", key="lang_sb",
        )
        if sel != lang:
            st.session_state.lang = sel
            st.session_state.page = t("nav_info")
            st.rerun()

        st.divider()

        wf = workflow_pages()
        all_ = wf + [t("nav_set")]
        cur = st.session_state.page if st.session_state.page in all_ else all_[0]
        pg = st.radio(
            "nav", all_, index=all_.index(cur),
            label_visibility="collapsed", key="nav_rb",
        )
        if pg != st.session_state.page:
            st.session_state.page = pg
            st.rerun()

        st.divider()

        # Quick stats
        w = wc(_all_text())
        f = len(st.session_state.figures)
        r = len(st.session_state.refs)
        fm = len(st.session_state.formulas)
        st.markdown(
            f'<div style="font-size:0.71rem;color:#64748b;margin-bottom:8px;">'
            f'📊 Quick Stats</div>'
            f'<span class="qs" style="background:#1e3a5f;color:#60a5fa;">'
            f'{w} words</span>'
            f'<span class="qs" style="background:#1c3a2e;color:#34d399;">'
            f'{f} figs</span>'
            f'<span class="qs" style="background:#3a1c1c;color:#f87171;">'
            f'{r} refs</span>'
            f'<span class="qs" style="background:#2d1b4e;color:#c084fc;">'
            f'{fm} forms</span>',
            unsafe_allow_html=True,
        )

        st.divider()

        ud = st.session_state.user_data
        st.markdown(
            f'<div style="font-size:0.78rem;color:#94a3b8;">👤 '
            f'<b style="color:#f1f5f9;">'
            f'{ud.get("name", st.session_state.username)}</b><br>'
            f'<span style="color:#64748b;">{ud.get("role","")}</span></div>',
            unsafe_allow_html=True,
        )
        if st.button(f"🚪 {t('logout')}", use_container_width=True):
            add_log("logout", st.session_state.username)
            st.session_state.logged_in = False
            st.rerun()


# ════════════════════════════════════════════════════════════════════════════
# STEPPER + STATS ROW
# ════════════════════════════════════════════════════════════════════════════
def stepper():
    wf = workflow_pages()
    if st.session_state.page not in wf:
        return
    ci = wf.index(st.session_state.page)
    html = ""
    for i, s in enumerate(wf):
        lbl = s.split(" ", 1)[1] if " " in s else s
        cls = "si sd" if i < ci else ("si sa" if i == ci else "si")
        pfx = "✓ " if i < ci else ""
        html += f'<div class="{cls}">{pfx}{lbl}</div>'
        if i < len(wf) - 1:
            html += '<div style="color:#475569;font-size:0.68rem;">›</div>'
    st.markdown(f'<div class="stp">{html}</div>', unsafe_allow_html=True)
    st.progress((ci + 1) / len(wf))
    st.caption(f"{t('step')} {ci + 1} {t('of_')} {len(wf)}")


def stats_row():
    w = wc(_all_text())
    sc = _sections_done()
    cols = st.columns(6)
    icons = ["📝", "📑", "🖼️", "📊", "🧮", "📚"]
    vals = [
        w, sc, len(st.session_state.figures),
        len(st.session_state.tables),
        len(st.session_state.formulas),
        len(st.session_state.refs),
    ]
    lbls = [
        t("w_words"), t("w_secs"), t("w_figs"),
        t("w_tbls"), t("w_forms"), t("w_refs"),
    ]
    for col, icon, val, lbl in zip(cols, icons, vals, lbls):
        col.markdown(
            f'<div class="mc">'
            f'<div style="font-size:1.1rem;margin-bottom:2px;">{icon}</div>'
            f'<div class="mv">{val}</div>'
            f'<div class="ml">{lbl}</div></div>',
            unsafe_allow_html=True,
        )


# ════════════════════════════════════════════════════════════════════════════
# PAGE: ARTICLE INFO
# ════════════════════════════════════════════════════════════════════════════
def pg_info():
    st.markdown(
        f'<div class="tb"><span class="tt">📄 {t("nav_info")}</span></div>',
        unsafe_allow_html=True,
    )
    stepper()
    stats_row()
    st.write("")
    L, R = st.columns(2)

    with L:
        st.session_state.art_title = st.text_input(
            t("title_f"), value=st.session_state.art_title,
            placeholder="e.g. Flood Mapping in Kazakhstan Using Sentinel-1 SAR Data",
        )
        st.session_state.authors = st.text_input(
            t("authors_f"), value=st.session_state.authors,
            placeholder="Samarkhanov K., Smith J., Doe A.",
        )
        st.session_state.affiliation = st.text_area(
            t("affil_f"), value=st.session_state.affiliation, height=70,
            placeholder="Institute of Geography, Almaty, Kazakhstan",
        )
        st.session_state.journal = st.text_input(
            t("journal_f"), value=st.session_state.journal,
            placeholder=t("jrn_ph"),
        )
        atypes = t("art_types")
        idx = min(st.session_state.art_type_idx, len(atypes) - 1)
        sel = st.selectbox(t("art_type_f"), atypes, index=idx)
        st.session_state.art_type_idx = atypes.index(sel)

    with R:
        st.session_state.keywords = st.text_input(
            t("keywords_f"), value=st.session_state.keywords,
            placeholder=t("kw_ph"),
        )
        st.session_state.abstract = st.text_area(
            t("abstract_f"), value=st.session_state.abstract, height=200,
            placeholder="Write your abstract here (150–300 words)…",
        )
        w = wc(st.session_state.abstract)
        color = "#10b981" if 150 <= w <= 300 else ("#f59e0b" if w > 0 else "#64748b")
        st.markdown(
            f'<span style="color:{color};font-size:0.78rem;">'
            f'📝 {t("word_count")}: {w}</span>',
            unsafe_allow_html=True,
        )
        st.markdown("---")
        ab = st.session_state.abstract
        ab_html = (
            f'<div class="pab"><b>Abstract:</b> '
            f'{ab[:280]}{"…" if len(ab) > 280 else ""}</div>'
            if ab
            else ""
        )
        kw_html = (
            f'<div style="font-size:0.77rem;color:#64748b;margin-top:6px;">'
            f'<b>Keywords:</b> {st.session_state.keywords}</div>'
            if st.session_state.keywords
            else ""
        )
        st.markdown(
            f'<div class="pv" style="min-height:auto;padding:20px;">'
            f'<div class="pt">{st.session_state.art_title or "—"}</div>'
            f'<div class="pa">{st.session_state.authors or "—"}</div>'
            f'<div class="pa" style="font-size:0.8rem;">'
            f'{st.session_state.affiliation or ""}</div>'
            f'{ab_html}{kw_html}</div>',
            unsafe_allow_html=True,
        )


# ════════════════════════════════════════════════════════════════════════════
# PAGE: SECTIONS
# ════════════════════════════════════════════════════════════════════════════
def pg_sections():
    st.markdown(
        f'<div class="tb"><span class="tt">✍️ {t("nav_sec")}</span></div>',
        unsafe_allow_html=True,
    )
    stepper()
    stats_row()
    st.write("")
    L, R = st.columns(2, gap="large")

    keys = ["intro", "methods", "results", "discussion", "conclusion"]
    labels = [t("intro"), t("methods"), t("results"),
              t("discussion"), t("conclusion")]

    with L:
        st.subheader(t("sec_editor"))
        tabs = st.tabs(labels)
        for tab, k, lbl in zip(tabs, keys, labels):
            with tab:
                up = st.file_uploader(
                    t("upload_docx"), type=["docx", "txt"],
                    key=f"up_{k}", label_visibility="collapsed",
                )
                if up:
                    if up.name.endswith(".txt"):
                        st.session_state[k] = up.read().decode(
                            "utf-8", errors="ignore"
                        )
                    elif up.name.endswith(".docx") and DOCX_OK:
                        try:
                            doc = Document(BytesIO(up.read()))
                            st.session_state[k] = "\n".join(
                                p.text for p in doc.paragraphs
                            )
                        except Exception:
                            st.warning("Cannot parse DOCX.")
                st.session_state[k] = st.text_area(
                    lbl, value=st.session_state[k], height=290,
                    key=f"ed_{k}", label_visibility="collapsed",
                    placeholder=f"Write {lbl} here…",
                )
                st.caption(f"📝 {t('word_count')}: {wc(st.session_state[k])}")

    with R:
        st.subheader(t("preview"))
        parts = [
            f'<div class="pt">{st.session_state.art_title or "—"}</div>',
            f'<div class="pa">{st.session_state.authors or "—"}</div>',
        ]
        if st.session_state.abstract:
            ab = st.session_state.abstract
            parts.append(
                f'<div class="pab"><b>Abstract:</b> '
                f'{ab[:350]}{"…" if len(ab) > 350 else ""}</div>'
            )
        for k, lbl in zip(keys, labels):
            c = st.session_state.get(k, "")
            if c:
                parts.append(
                    f'<div class="ph">{lbl}</div>'
                    f'<p style="font-size:0.84rem;">'
                    f'{c[:500]}{"…" if len(c) > 500 else ""}</p>'
                )
        st.markdown(
            f'<div class="pv">{"".join(parts)}</div>', unsafe_allow_html=True
        )


# ════════════════════════════════════════════════════════════════════════════
# PAGE: FIGURES
# ════════════════════════════════════════════════════════════════════════════
def pg_figures():
    st.markdown(
        f'<div class="tb"><span class="tt">🖼️ {t("fig_mgr")}</span></div>',
        unsafe_allow_html=True,
    )
    stepper()
    stats_row()
    st.write("")
    L, R = st.columns(2, gap="large")

    with L:
        st.subheader(f"➕ {t('add_fig')}")
        with st.form("ff", clear_on_submit=True):
            fn = st.text_input(t("fig_no"), placeholder="1")
            fc = st.text_input(
                t("fig_cap"), placeholder="Map of study area, Kazakhstan"
            )
            fup = st.file_uploader(
                t("upload_fig"), type=["png", "jpg", "jpeg", "tif", "svg"]
            )
            if st.form_submit_button(
                f"➕ {t('add_btn')}", use_container_width=True
            ) and fc:
                st.session_state.figures.append({
                    "number": fn or str(len(st.session_state.figures) + 1),
                    "caption": fc,
                    "image": fup.read() if fup else None,
                    "name": fup.name if fup else None,
                })
                st.success("✅ Figure added")

    with R:
        if not st.session_state.figures:
            st.info(t("no_figs"))
        else:
            st.subheader("Figure List")
            for i, fig in enumerate(st.session_state.figures):
                with st.expander(
                    f"🖼️ Fig. {fig['number']} — {fig['caption']}"
                ):
                    if fig.get("image"):
                        st.image(fig["image"], use_container_width=True)
                    st.caption(f"📄 {fig.get('name', '—')}")
                    if st.button(f"🗑️ {t('del_btn')}", key=f"df{i}"):
                        st.session_state.figures.pop(i)
                        st.rerun()


# ════════════════════════════════════════════════════════════════════════════
# PAGE: TABLES
# ════════════════════════════════════════════════════════════════════════════
def pg_tables():
    st.markdown(
        f'<div class="tb"><span class="tt">📊 {t("tbl_mgr")}</span></div>',
        unsafe_allow_html=True,
    )
    stepper()
    stats_row()
    st.write("")
    L, R = st.columns(2, gap="large")

    with L:
        st.subheader(f"➕ {t('add_tbl')}")
        with st.form("tf", clear_on_submit=True):
            tn = st.text_input(t("tbl_no"), placeholder="1")
            tc = st.text_input(
                t("tbl_cap"), placeholder="Summary statistics of study area"
            )
            td = st.text_area(
                t("tbl_data"), height=130,
                placeholder="Col1,Col2,Col3\nVal1,Val2,Val3\nVal4,Val5,Val6",
            )
            if st.form_submit_button(
                f"➕ {t('add_btn')}", use_container_width=True
            ) and tc:
                st.session_state.tables.append({
                    "number": tn or str(len(st.session_state.tables) + 1),
                    "caption": tc,
                    "data": td,
                })
                st.success("✅ Table added")

    with R:
        if not st.session_state.tables:
            st.info(t("no_tbls"))
        else:
            st.subheader("Table List")
            for i, tbl in enumerate(st.session_state.tables):
                with st.expander(
                    f"📊 Table {tbl['number']} — {tbl['caption']}"
                ):
                    if tbl.get("data") and PD_OK:
                        try:
                            df = pd.read_csv(io.StringIO(tbl["data"]))
                            st.dataframe(df, use_container_width=True)
                        except Exception:
                            st.text(tbl["data"])
                    elif tbl.get("data"):
                        st.text(tbl["data"])
                    if st.button(f"🗑️ {t('del_btn')}", key=f"dt{i}"):
                        st.session_state.tables.pop(i)
                        st.rerun()


# ════════════════════════════════════════════════════════════════════════════
# PAGE: FORMULAS
# ════════════════════════════════════════════════════════════════════════════
def pg_formulas():
    st.markdown(
        f'<div class="tb"><span class="tt">🧮 {t("form_mgr")}</span></div>',
        unsafe_allow_html=True,
    )
    stepper()
    stats_row()
    st.write("")
    L, R = st.columns(2, gap="large")

    with L:
        st.subheader(f"➕ {t('add_form')}")
        with st.form("formf", clear_on_submit=True):
            fnum = st.text_input(t("form_no"), placeholder="1")
            flatex = st.text_input(
                t("form_latex"),
                placeholder=r"Q = \frac{1}{n} A R^{2/3} S^{1/2}",
            )
            fdesc = st.text_area(
                t("form_desc"), height=80,
                placeholder="Manning's equation for open channel flow",
            )
            if st.form_submit_button(
                f"➕ {t('add_btn')}", use_container_width=True
            ) and flatex:
                st.session_state.formulas.append({
                    "number": fnum or str(len(st.session_state.formulas) + 1),
                    "latex": flatex,
                    "desc": fdesc,
                })
                st.success("✅ Formula added")

        st.markdown("---")
        st.markdown("**📖 LaTeX Quick Reference**")
        ref_data = {
            "Description": [
                "Fraction", "Square root", "Sub/Superscript",
                "Integral", "Sum", "Greek letters",
                "Manning's eq.", "Water balance", "Nash-Sutcliffe",
            ],
            "LaTeX code": [
                r"\frac{a}{b}", r"\sqrt{x}", r"x_{i}^{2}",
                r"\int_{a}^{b} f(x)dx", r"\sum_{i=1}^{n} x_i",
                r"\alpha, \beta, \Delta",
                r"Q = \frac{1}{n} A R^{2/3} S^{1/2}",
                r"P = ET + \Delta S + Q",
                r"NSE = 1 - \frac{\sum(Q_o-Q_s)^2}{\sum(Q_o-\bar{Q}_o)^2}",
            ],
        }
        if PD_OK:
            st.dataframe(
                pd.DataFrame(ref_data), use_container_width=True, hide_index=True
            )

    with R:
        st.subheader(f"👁️ {t('form_preview')}")
        if not st.session_state.formulas:
            st.info(t("no_forms"))
        else:
            for i, frm in enumerate(st.session_state.formulas):
                desc_short = (
                    frm["desc"][:50] if frm.get("desc") else frm["latex"][:40]
                )
                with st.expander(f"🧮 ({frm['number']}) — {desc_short}"):
                    try:
                        st.latex(frm["latex"])
                    except Exception:
                        st.code(frm["latex"], language="latex")
                    if frm.get("desc"):
                        st.caption(f"📝 {frm['desc']}")
                    st.markdown(
                        f'`({frm["number"]})` — LaTeX: `{frm["latex"]}`'
                    )
                    if st.button(f"🗑️ {t('del_btn')}", key=f"dfm{i}"):
                        st.session_state.formulas.pop(i)
                        st.rerun()

        st.markdown("---")
        st.subheader("🔬 Live LaTeX Preview")
        test_latex = st.text_input(
            "Enter LaTeX to preview", placeholder=r"E = mc^2", key="latex_test"
        )
        if test_latex:
            try:
                st.latex(test_latex)
            except Exception as e:
                st.error(f"LaTeX error: {e}")


# ════════════════════════════════════════════════════════════════════════════
# CITATION FORMATTERS
# ════════════════════════════════════════════════════════════════════════════
def fmt_ref(ref: dict, style: str, n: int) -> str:
    au = ref.get("authors", "")
    yr = ref.get("year", "")
    ti = ref.get("title", "")
    jn = ref.get("journal", "")
    vo = ref.get("volume", "")
    no = ref.get("number", "")
    pp = ref.get("pages", "")
    doi = ref.get("doi", "")
    cit = ref.get("city", "")
    pub = ref.get("publisher", "")
    doi_str = f" DOI: {doi}" if doi else ""

    if "ГОСТ" in style:
        rtype = ref.get("type", "")
        if any(kw in rtype for kw in ("Book", "Книга", "Кітап")):
            city_pub = ""
            if cit and pub:
                city_pub = f" — {cit} : {pub}"
            elif cit:
                city_pub = f" — {cit}"
            elif pub:
                city_pub = f" — {pub}"
            yr_str = f", {yr}" if yr else ""
            pp_str = f". — {pp} с." if pp else ""
            return f"{au} {ti}{city_pub}{yr_str}{pp_str}"
        elif any(kw in rtype for kw in ("Thesis", "Диссерт")):
            return (
                f"{au} {ti} : дис. … канд./д-ра наук. — "
                f"{cit or pub}, {yr}. — {pp} с."
            )
        elif any(kw in rtype.lower() for kw in ("conference", "конференц")):
            return (
                f"{au} {ti} // {jn}. — {cit or pub}, {yr}. — "
                f"{'С. ' + pp if pp else ''}.{doi_str}"
            )
        else:
            vol_str = f". — Т. {vo}" if vo else ""
            no_str = f", № {no}" if no else ""
            pp_str = f". — С. {pp}" if pp else ""
            return f"{au} {ti} // {jn}. — {yr}{vol_str}{no_str}{pp_str}.{doi_str}"

    elif "APA" in style:
        vol_no = f"*{vo}*" + (f"({no})" if no else "") if vo else ""
        return f"{au} ({yr}). {ti}. *{jn}*, {vol_no}, {pp}.{doi_str}"

    elif "Vancouver" in style or "Ванкувер" in style:
        return f"{n}. {au}. {ti}. {jn}. {yr};{vo}({no}):{pp}.{doi_str}"

    elif "IEEE" in style:
        return (
            f'[{n}] {au}, "{ti}," *{jn}*, '
            f'vol. {vo}, no. {no}, pp. {pp}, {yr}.{doi_str}'
        )

    else:  # Harvard
        return (
            f"{au} {yr}, '{ti}', *{jn}*, "
            f"vol. {vo}, no. {no}, pp. {pp}.{doi_str}"
        )


# ════════════════════════════════════════════════════════════════════════════
# BIBTEX PARSER
# ════════════════════════════════════════════════════════════════════════════
def parse_bibtex(text: str) -> list:
    results = []
    TYPE_MAP = {
        "article": "Journal Article",
        "book": "Book",
        "inbook": "Book Chapter",
        "incollection": "Book Chapter",
        "inproceedings": "Conference Paper",
        "conference": "Conference Paper",
        "proceedings": "Conference Paper",
        "misc": "Website",
        "phdthesis": "Thesis",
        "mastersthesis": "Thesis",
        "techreport": "Journal Article",
        "unpublished": "Journal Article",
    }
    raw_entries = re.split(r"(?=@\w+\s*[\{\(])", text.strip())
    for raw in raw_entries:
        raw = raw.strip()
        if not raw or not raw.startswith("@"):
            continue
        type_m = re.match(r"@(\w+)\s*[\{\(]", raw, re.IGNORECASE)
        if not type_m:
            continue
        entry_type = type_m.group(1).lower()
        if entry_type in ("comment", "string", "preamble"):
            continue

        fields: dict[str, str] = {}
        for m in re.finditer(
            r"(\w+)\s*=\s*\{((?:[^{}]|\{[^{}]*\})*)\}", raw, re.DOTALL
        ):
            key = m.group(1).lower()
            val = re.sub(r"\s+", " ", m.group(2).strip())
            val = val.replace("{", "").replace("}", "")
            fields[key] = val
        for m in re.finditer(r'(\w+)\s*=\s*"([^"]*)"', raw, re.DOTALL):
            key = m.group(1).lower()
            if key not in fields:
                fields[key] = m.group(2).strip()
        for m in re.finditer(r"(\w+)\s*=\s*(\d{4})\b", raw):
            key = m.group(1).lower()
            if key not in fields:
                fields[key] = m.group(2)

        title = fields.get("title", "").strip()
        if not title:
            continue

        raw_authors = fields.get("author", "")
        authors_out = _fmt_authors(raw_authors) if raw_authors else ""

        results.append({
            "type": TYPE_MAP.get(entry_type, "Journal Article"),
            "authors": authors_out,
            "year": fields.get("year", ""),
            "title": title,
            "journal": fields.get(
                "journal", fields.get("booktitle", fields.get("series", ""))
            ),
            "volume": fields.get("volume", ""),
            "number": fields.get("number", ""),
            "pages": fields.get("pages", "").replace("--", "–"),
            "doi": fields.get("doi", ""),
            "city": fields.get("address", ""),
            "publisher": fields.get("publisher", ""),
        })
    return results


def _fmt_authors(raw: str) -> str:
    parts = [a.strip() for a in re.split(r"\s+and\s+", raw, flags=re.IGNORECASE)]
    out = []
    for p in parts:
        if not p:
            continue
        if "," in p:
            segments = [s.strip() for s in p.split(",", 1)]
            last = segments[0]
            first = segments[1] if len(segments) > 1 else ""
            initials = "".join(w[0].upper() + "." for w in first.split() if w)
            out.append(f"{last} {initials}".strip())
        else:
            words = p.split()
            if len(words) >= 2:
                last = words[-1]
                inits = "".join(w[0].upper() + "." for w in words[:-1])
                out.append(f"{last} {inits}".strip())
            else:
                out.append(p)
    return ", ".join(out)


# ════════════════════════════════════════════════════════════════════════════
# PAGE: REFERENCES  (fixed: removed duplicate import button + undefined 'bib')
# ════════════════════════════════════════════════════════════════════════════
def pg_refs():
    st.markdown(
        f'<div class="tb"><span class="tt">📑 {t("ref_mgr")}</span></div>',
        unsafe_allow_html=True,
    )
    stepper()
    stats_row()
    st.write("")

    rt_list = t("ref_types")
    cs_list = t("cite_styles")
    L, R = st.columns(2, gap="large")

    with L:
        st.subheader(f"➕ {t('add_ref')}")
        with st.form("rff", clear_on_submit=True):
            rtype = st.selectbox(t("ref_type"), rt_list)
            rau = st.text_input(
                t("ref_au"), placeholder="Samarkhanov K.B., Doe J."
            )
            ryr = st.text_input(t("ref_yr"), placeholder="2024")
            rti = st.text_input(
                t("ref_ti"), placeholder="Flood Mapping Using SAR Data"
            )
            rjn = st.text_input(
                t("ref_jn"), placeholder="Remote Sensing of Environment"
            )
            c1, c2, c3 = st.columns(3)
            rvo = c1.text_input(t("ref_vol"), placeholder="15")
            rno = c2.text_input(t("ref_no"), placeholder="3")
            rpp = c3.text_input(t("ref_pp"), placeholder="1234–1250")
            rdoi = st.text_input(t("ref_doi"), placeholder="10.3390/rs15051234")

            show_extra = rtype in [
                "Book", "Книга", "Кітап", "Thesis", "Диссертация",
            ]
            if show_extra:
                cx1, cx2 = st.columns(2)
                rcit = cx1.text_input(t("ref_city"), placeholder="Алматы")
                rpub = cx2.text_input(t("ref_pub"), placeholder="Ғылым")
            else:
                rcit = rpub = ""

            if st.form_submit_button(
                f"➕ {t('add_btn')}", use_container_width=True
            ) and rti:
                st.session_state.refs.append({
                    "type": rtype, "authors": rau, "year": ryr, "title": rti,
                    "journal": rjn, "volume": rvo, "number": rno,
                    "pages": rpp, "doi": rdoi, "city": rcit, "publisher": rpub,
                })
                st.success("✅ Reference added")

        st.divider()
        st.subheader(f"📥 {t('import_refs')}")
        bib_input = st.text_area(
            "BibTeX / plain text", height=160,
            placeholder=(
                "@article{samarkhanov2024,\n"
                "  author  = {Samarkhanov, Kanat and Doe, John},\n"
                "  title   = {Flood mapping in Kazakhstan},\n"
                "  journal = {Remote Sensing},\n"
                "  year    = {2024},\n"
                "  volume  = {16},\n"
                "  number  = {5},\n"
                "  pages   = {123--145},\n"
                "  doi     = {10.3390/rs16050123}\n"
                "}"
            ),
            key="bib_input_area",
        )

        col_i1, col_i2 = st.columns(2)
        with col_i1:
            if st.button(
                f"🔬 {t('import_btn')} BibTeX", use_container_width=True
            ):
                if bib_input.strip():
                    parsed = parse_bibtex(bib_input)
                    if parsed:
                        st.session_state.refs.extend(parsed)
                        st.success(
                            f"✅ {t('imported')} {len(parsed)} {t('ref_s')}"
                        )
                    else:
                        st.warning("⚠️ No valid BibTeX entries found.")
                else:
                    st.warning("⚠️ Paste BibTeX first.")

        with col_i2:
            if st.button("📄 Import plain text", use_container_width=True):
                if bib_input.strip():
                    lines = [l.strip() for l in bib_input.split("\n") if l.strip()]
                    for ln in lines:
                        st.session_state.refs.append({
                            "type": "Journal Article", "authors": "", "year": "",
                            "title": ln, "journal": "", "volume": "",
                            "number": "", "pages": "", "doi": "",
                            "city": "", "publisher": "",
                        })
                    st.success(
                        f"✅ {t('imported')} {len(lines)} {t('ref_s')}"
                    )
                else:
                    st.warning("⚠️ Paste text first.")

    with R:
        st.subheader(f"📋 {t('ref_list')}")
        style = st.selectbox(t("cite_style_label"), cs_list, key="rs_sel")
        st.session_state.cite_style = style

        if not st.session_state.refs:
            st.info(t("no_refs"))
        else:
            for i, ref in enumerate(st.session_state.refs):
                c1, c2 = st.columns([11, 1])
                c1.markdown(
                    f'<div class="ri"><span class="rn">[{i + 1}]</span> '
                    f'{fmt_ref(ref, style, i + 1)}</div>',
                    unsafe_allow_html=True,
                )
                if c2.button("🗑️", key=f"dr{i}", help=t("del_btn")):
                    st.session_state.refs.pop(i)
                    st.rerun()


# ════════════════════════════════════════════════════════════════════════════
# DOCX BUILDER
# ════════════════════════════════════════════════════════════════════════════
def build_docx() -> BytesIO:
    doc = Document()
    sec = doc.sections[0]
    sec.top_margin = Inches(1)
    sec.bottom_margin = Inches(1)
    sec.left_margin = Inches(1.25)
    sec.right_margin = Inches(1.25)
    BLUE = RGBColor(0x1A, 0x56, 0xDB)

    def add_heading_colored(text, level=1):
        h = doc.add_heading(text, level=level)
        if h.runs:
            h.runs[0].font.color.rgb = BLUE
        return h

    tp = doc.add_paragraph()
    tp.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = tp.add_run(st.session_state.art_title or "Untitled")
    r.bold = True
    r.font.size = Pt(16)
    r.font.color.rgb = BLUE

    if st.session_state.authors:
        ap = doc.add_paragraph()
        ap.alignment = WD_ALIGN_PARAGRAPH.CENTER
        ap.add_run(st.session_state.authors).bold = True

    if st.session_state.affiliation:
        af = doc.add_paragraph()
        af.alignment = WD_ALIGN_PARAGRAPH.CENTER
        r2 = af.add_run(st.session_state.affiliation)
        r2.font.size = Pt(10)
        r2.font.color.rgb = RGBColor(0x64, 0x74, 0x8B)

    if st.session_state.keywords:
        kp = doc.add_paragraph()
        kp.alignment = WD_ALIGN_PARAGRAPH.CENTER
        r3 = kp.add_run(f"Keywords: {st.session_state.keywords}")
        r3.italic = True
        r3.font.size = Pt(10)

    doc.add_paragraph()

    if st.session_state.abstract:
        add_heading_colored("Abstract", 2)
        doc.add_paragraph(st.session_state.abstract)
        doc.add_paragraph()

    keys = ["intro", "methods", "results", "discussion", "conclusion"]
    labels = [t("intro"), t("methods"), t("results"),
              t("discussion"), t("conclusion")]
    for i, (k, lbl) in enumerate(zip(keys, labels), 1):
        if st.session_state.get(k, "").strip():
            add_heading_colored(f"{i}. {lbl}", 1)
            doc.add_paragraph(st.session_state[k])
            doc.add_paragraph()

    if st.session_state.formulas:
        add_heading_colored("Formulas / Equations", 1)
        for frm in st.session_state.formulas:
            p = doc.add_paragraph()
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            r4 = p.add_run(f"({frm['number']})   {frm['latex']}")
            r4.font.name = "Cambria Math"
            r4.font.size = Pt(12)
            if frm.get("desc"):
                dp = doc.add_paragraph(frm["desc"])
                dp.alignment = WD_ALIGN_PARAGRAPH.CENTER
                if dp.runs:
                    dp.runs[0].italic = True
                    dp.runs[0].font.size = Pt(10)
            doc.add_paragraph()

    if st.session_state.figures:
        add_heading_colored("Figures", 1)
        for fig in st.session_state.figures:
            if fig.get("image"):
                try:
                    doc.add_picture(BytesIO(fig["image"]), width=Inches(4.5))
                except Exception:
                    pass
            cp = doc.add_paragraph(
                f"Figure {fig['number']}. {fig['caption']}"
            )
            cp.alignment = WD_ALIGN_PARAGRAPH.CENTER
            if cp.runs:
                cp.runs[0].italic = True
                cp.runs[0].font.size = Pt(9)
            doc.add_paragraph()

    if st.session_state.tables and PD_OK:
        for tbl in st.session_state.tables:
            tp2 = doc.add_paragraph(
                f"Table {tbl['number']}. {tbl['caption']}"
            )
            if tp2.runs:
                tp2.runs[0].bold = True
            if tbl.get("data"):
                try:
                    df = pd.read_csv(io.StringIO(tbl["data"]))
                    wt = doc.add_table(
                        rows=len(df) + 1, cols=len(df.columns)
                    )
                    wt.style = "Table Grid"
                    for ci, col in enumerate(df.columns):
                        wt.cell(0, ci).text = str(col)
                    for ri in range(len(df)):
                        for ci in range(len(df.columns)):
                            wt.cell(ri + 1, ci).text = str(df.iloc[ri, ci])
                except Exception:
                    pass
            doc.add_paragraph()

    if st.session_state.refs:
        add_heading_colored("References", 1)
        for i, ref in enumerate(st.session_state.refs, 1):
            p = doc.add_paragraph(
                fmt_ref(ref, st.session_state.cite_style, i),
                style="List Number",
            )
            if p.runs:
                p.runs[0].font.size = Pt(10)

    buf = BytesIO()
    doc.save(buf)
    buf.seek(0)
    return buf


# ════════════════════════════════════════════════════════════════════════════
# PAGE: GENERATE  (fixed: export section properly placed)
# ════════════════════════════════════════════════════════════════════════════
def pg_generate():
    st.markdown(
        f'<div class="tb"><span class="tt">🚀 {t("gen_title")}</span></div>',
        unsafe_allow_html=True,
    )
    stepper()
    stats_row()
    st.write("")

    if not st.session_state.art_title:
        st.warning(t("warn_title"))
        return

    keys = ["intro", "methods", "results", "discussion", "conclusion"]
    labels = [t("intro"), t("methods"), t("results"),
              t("discussion"), t("conclusion")]
    done = sum(
        1 for k in keys if st.session_state.get(k, "").strip()
    )

    # ── Completeness ──
    st.markdown(f"### 📋 {t('completeness')}")
    c1, c2, c3, c4 = st.columns(4)
    c1.progress(done / 5, text=f"{done * 20}%")
    c2.metric(t("w_secs"), f"{done}/5")
    c3.metric(t("w_refs"), len(st.session_state.refs))
    c4.metric(t("w_forms"), len(st.session_state.formulas))
    st.write("")

    # ── Preview ──
    st.markdown(f"### {t('preview')}")
    parts = [
        f'<div class="pt">{st.session_state.art_title}</div>',
        f'<div class="pa"><b>{st.session_state.authors}</b></div>',
        f'<div class="pa" style="font-size:0.8rem;">'
        f'{st.session_state.affiliation}</div>',
    ]
    if st.session_state.keywords:
        parts.append(
            f'<div style="text-align:center;font-size:0.77rem;color:#64748b;">'
            f'<b>Keywords:</b> {st.session_state.keywords}</div>'
        )
    if st.session_state.abstract:
        ab = st.session_state.abstract
        parts.append(
            f'<div class="pab"><b>Abstract:</b> '
            f'{ab[:600]}{"…" if len(ab) > 600 else ""}</div>'
        )
    for i, (k, lbl) in enumerate(zip(keys, labels), 1):
        c = st.session_state.get(k, "")
        if c:
            parts.append(
                f'<div class="ph">{i}. {lbl}</div>'
                f'<p style="font-size:0.84rem;">{c}</p>'
            )
    if st.session_state.formulas:
        parts.append('<div class="ph">Formulas</div>')
        for frm in st.session_state.formulas:
            parts.append(
                f'<p style="text-align:center;font-size:0.86rem;">'
                f'({frm["number"]})  <code>{frm["latex"]}</code></p>'
            )
    if st.session_state.refs:
        parts.append('<div class="ph">References</div>')
        cs = st.session_state.cite_style
        for j, ref in enumerate(st.session_state.refs, 1):
            parts.append(
                f'<p style="font-size:0.81rem;">{fmt_ref(ref, cs, j)}</p>'
            )
    st.markdown(
        f'<div class="pv">{"".join(parts)}</div>', unsafe_allow_html=True
    )
    st.write("")

    # ── Export buttons ──
    st.markdown("### 📥 Export")
    fn = sfn(st.session_state.art_title)
    e1, e2, e3 = st.columns(3)

    with e1:
        if DOCX_OK:
            with st.spinner(t("downloading")):
                buf = build_docx()
            st.download_button(
                t("dl_docx"), buf, f"{fn}.docx",
                "application/vnd.openxmlformats-officedocument"
                ".wordprocessingml.document",
                use_container_width=True,
            )
            st.success(t("success_gen"))
        else:
            st.error("pip install python-docx")

    with e2:
        md_lines = [
            f"# {st.session_state.art_title}",
            f"**{st.session_state.authors}**",
            f"*{st.session_state.affiliation}*", "",
            f"**Keywords:** {st.session_state.keywords}", "",
            f"## Abstract\n\n{st.session_state.abstract}", "",
        ]
        for i, (k, lbl) in enumerate(zip(keys, labels), 1):
            if st.session_state.get(k, ""):
                md_lines += [f"## {i}. {lbl}", st.session_state[k], ""]
        if st.session_state.formulas:
            md_lines.append("## Formulas\n")
            for frm in st.session_state.formulas:
                md_lines.append(
                    f"$$({frm['number']}) \\quad {frm['latex']}$$"
                )
                if frm.get("desc"):
                    md_lines.append(f"*{frm['desc']}*")
                md_lines.append("")
        if st.session_state.refs:
            md_lines.append("## References\n")
            cs = st.session_state.cite_style
            for j, ref in enumerate(st.session_state.refs, 1):
                md_lines.append(fmt_ref(ref, cs, j))
        st.download_button(
            t("dl_md"), "\n".join(md_lines).encode("utf-8"),
            f"{fn}.md", "text/markdown", use_container_width=True,
        )

    with e3:
        proj = {
            k: st.session_state.get(k, "")
            for k in [
                "art_title", "authors", "affiliation", "journal", "keywords",
                "abstract", "intro", "methods", "results", "discussion",
                "conclusion", "cite_style",
            ]
        }
        proj["refs"] = st.session_state.refs
        proj["formulas"] = st.session_state.formulas
        proj["tables"] = st.session_state.tables
        proj["exported_at"] = datetime.now().isoformat()
        st.download_button(
            t("save_json"),
            json.dumps(proj, ensure_ascii=False, indent=2).encode("utf-8"),
            f"{fn}_project.json", "application/json",
            use_container_width=True,
        )

    # ── Feedback ──
    st.write("")
    st.markdown("---")
    st.subheader("💬 Feedback")
    with st.form("fb_form", clear_on_submit=True):
        fb_text = st.text_area(
            "Leave a comment or suggestion", height=100,
            placeholder="Your feedback helps improve Smart Article…",
        )
        fb_ok = st.form_submit_button(
            "📨 Send Feedback", use_container_width=True
        )
    if fb_ok and fb_text.strip():
        add_log("feedback", st.session_state.username, fb_text[:200])
        sync_logs_to_github()
        sync_feedback_to_github(st.session_state.username, fb_text)
        _notify_feedback(st.session_state.username, fb_text)
        st.success("✅ Feedback sent! Thank you.")


# ════════════════════════════════════════════════════════════════════════════
# PAGE: SETTINGS
# ════════════════════════════════════════════════════════════════════════════
def pg_settings():
    st.markdown(
        f'<div class="tb"><span class="tt">⚙️ {t("settings_title")}</span></div>',
        unsafe_allow_html=True,
    )
    st.write("")

    T1, T2, T3 = st.tabs(["🎨 Theme & Style", "📂 Project", "☁️ GitHub Gist"])

    with T1:
        st.subheader(t("theme_label"))
        themes = t("themes")
        choice = st.radio(
            t("theme_label"), themes,
            index=0 if st.session_state.dark else 1,
            horizontal=True, label_visibility="collapsed",
        )
        st.session_state.dark = choice == themes[0]

        st.subheader(t("cite_style_label"))
        cs_list = t("cite_styles")
        cs = st.selectbox(
            t("cite_style_label"), cs_list,
            index=(
                cs_list.index(st.session_state.cite_style)
                if st.session_state.cite_style in cs_list
                else 0
            ),
            label_visibility="collapsed",
        )
        st.session_state.cite_style = cs

        st.divider()
        if st.session_state.username == "admin":
            st.subheader("📋 Activity Log (admin)")
            logs = load_logs()
            if logs and PD_OK:
                df_log = pd.DataFrame(logs[-50:][::-1])
                st.dataframe(df_log, use_container_width=True, hide_index=True)
            elif logs:
                for entry in logs[-10:][::-1]:
                    st.caption(
                        f"{entry['ts']}  [{entry['event']}]  "
                        f"{entry['username']}  {entry.get('detail', '')}"
                    )

        st.divider()
        st.subheader("📧 Email Notifications (SMTP)")
        st.info(
            "Configure Gmail SMTP to receive alerts. "
            "Use a Gmail App Password (not your regular password)."
        )
        c1, c2 = st.columns(2)
        st.session_state["smtp_user"] = c1.text_input(
            "Gmail address",
            value=st.session_state.get("smtp_user", ""),
            placeholder="your@gmail.com",
        )
        st.session_state["smtp_pass"] = c2.text_input(
            "App Password",
            value=st.session_state.get("smtp_pass", ""),
            type="password",
            placeholder="xxxx xxxx xxxx xxxx",
        )
        if st.button("🧪 Test Email"):
            ok = send_notification(
                "Test from Smart Article",
                f"<p>✅ SMTP is working!<br>Time: {datetime.now()}</p>",
            )
            if ok:
                st.success("✅ Email sent!")
            else:
                st.error("❌ Failed. Check Gmail address and App Password.")

        st.divider()
        st.subheader("☁️ GitHub Repository Sync")
        st.info(
            "Stores users.json, logs.json, feedback.json in your GitHub repo. "
            "Token needs `repo` scope."
        )
        c3, c4 = st.columns(2)
        st.session_state["gh_token"] = c3.text_input(
            "GitHub Token",
            value=st.session_state.get("gh_token", ""),
            type="password", placeholder="ghp_xxxx",
        )
        st.session_state["gh_repo"] = c4.text_input(
            "Repository (owner/name)",
            value=st.session_state.get("gh_repo", ""),
            placeholder="username/smart-article-data",
        )
        if st.button("🧪 Test GitHub Connection"):
            token = st.session_state["gh_token"]
            repo = st.session_state["gh_repo"]
            if token and repo and REQ_OK:
                r = requests.get(
                    f"https://api.github.com/repos/{repo}",
                    headers={"Authorization": f"token {token}"},
                    timeout=8,
                )
                if r.status_code == 200:
                    st.success(
                        f"✅ Connected to: {r.json().get('full_name')}"
                    )
                else:
                    st.error(
                        f"❌ Error {r.status_code}: "
                        f"{r.json().get('message', '')}"
                    )
            else:
                st.warning("Enter token and repo name first.")

    with T2:
        L2, R2 = st.columns(2)
        with L2:
            st.subheader(t("load_json"))
            st.info(t("load_json_help"))
            upf = st.file_uploader("Upload JSON project file", type="json")
            if upf:
                try:
                    data = json.load(upf)
                    for f in [
                        "art_title", "authors", "affiliation", "journal",
                        "keywords", "abstract", "intro", "methods", "results",
                        "discussion", "conclusion", "refs", "tables",
                        "formulas", "cite_style",
                    ]:
                        if f in data:
                            st.session_state[f] = data[f]
                    st.success(t("loaded"))
                except Exception as e:
                    st.error(f"Error: {e}")

        with R2:
            st.subheader(f"🗑️ {t('reset_btn')}")
            st.warning(
                "This will erase all article data in the current session."
            )
            if st.button(t("reset_btn"), type="secondary"):
                for k in [
                    "art_title", "authors", "affiliation", "journal",
                    "keywords", "abstract", "intro", "methods", "results",
                    "discussion", "conclusion",
                ]:
                    st.session_state[k] = ""
                st.session_state.figures = []
                st.session_state.tables = []
                st.session_state.refs = []
                st.session_state.formulas = []
                st.success(t("reset_ok"))

    with T3:
        st.subheader(t("gh_title"))
        st.markdown(
            "> **GitHub Gist** allows you to save the project in the cloud."
        )
        if not REQ_OK:
            st.error(t("gh_need_req"))
        else:
            st.session_state.gh_token = st.text_input(
                t("gh_token"),
                value=st.session_state.gh_token,
                type="password",
                placeholder="ghp_xxxxxxxxxxxxxxxxxxxx",
            )
            G1, G2 = st.columns(2)
            with G1:
                if st.button(t("gh_save"), use_container_width=True):
                    if not st.session_state.gh_token:
                        st.error("Enter GitHub token first.")
                    else:
                        proj = {
                            k: st.session_state.get(k, "")
                            for k in [
                                "art_title", "authors", "affiliation",
                                "keywords", "abstract", "intro", "methods",
                                "results", "discussion", "conclusion",
                            ]
                        }
                        proj["refs"] = st.session_state.refs
                        proj["formulas"] = st.session_state.formulas
                        proj["tables"] = st.session_state.tables
                        proj["saved_at"] = datetime.now().isoformat()
                        content = json.dumps(
                            proj, ensure_ascii=False, indent=2
                        )
                        filename = (
                            sfn(st.session_state.art_title or "article")
                            + "_project.json"
                        )
                        with st.spinner("Uploading to GitHub Gist…"):
                            url = gist_save(
                                st.session_state.gh_token, content, filename
                            )
                        if url:
                            st.success(t("gh_saved"))
                            st.code(url)
                            add_log(
                                "gist_save", st.session_state.username, url
                            )
                        else:
                            st.error(t("gh_err"))

            with G2:
                gist_url_in = st.text_input(
                    t("gh_url"),
                    placeholder="https://gist.github.com/user/abc123",
                )
                if st.button(t("gh_load"), use_container_width=True):
                    if not st.session_state.gh_token or not gist_url_in:
                        st.error("Enter both token and Gist URL.")
                    else:
                        with st.spinner("Loading from GitHub Gist…"):
                            content = gist_load(
                                st.session_state.gh_token, gist_url_in
                            )
                        if content:
                            try:
                                data = json.loads(content)
                                for f in [
                                    "art_title", "authors", "affiliation",
                                    "keywords", "abstract", "intro", "methods",
                                    "results", "discussion", "conclusion",
                                    "refs", "formulas", "tables",
                                ]:
                                    if f in data:
                                        st.session_state[f] = data[f]
                                st.success(t("gh_loaded"))
                                add_log(
                                    "gist_load",
                                    st.session_state.username,
                                    gist_url_in,
                                )
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
        is_generate = st.session_state.page == t("nav_gen")
        label = (
            f"✅ {t('gen_title')}" if is_generate else f"🚀 {t('gen_title')}"
        )
        clicked = st.button(
            label, key="fab_generate",
            use_container_width=True, disabled=is_generate,
        )
        if clicked and not is_generate:
            st.session_state.page = t("nav_gen")
            st.rerun()


# ════════════════════════════════════════════════════════════════════════════
# MAIN
# ════════════════════════════════════════════════════════════════════════════
def main():
    if not st.session_state.logged_in:
        auth_page()
        return

    inject_css(dark=st.session_state.dark)
    sidebar()

    pg = st.session_state.page
    routes = {
        t("nav_info"): pg_info,
        t("nav_sec"): pg_sections,
        t("nav_fig"): pg_figures,
        t("nav_tbl"): pg_tables,
        t("nav_form"): pg_formulas,
        t("nav_ref"): pg_refs,
        t("nav_gen"): pg_generate,
        t("nav_set"): pg_settings,
    }
    routes.get(pg, pg_info)()
    fab()


if __name__ == "__main__":
    main()
