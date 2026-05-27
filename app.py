import streamlit as st
import streamlit.components.v1 as components
import os
import base64
from azure.ai.inference import ChatCompletionsClient
from azure.ai.inference.models import SystemMessage, UserMessage
from azure.core.credentials import AzureKeyCredential
from github import Github
import fitz  # PyMuPDF

# ==========================================
# 1. SETUP INIZIALE & STATO DEL TEMA
# ==========================================
st.set_page_config(page_title="Matora AI", page_icon="logo_matora.png", layout="wide", initial_sidebar_state="collapsed")

if "tema_scuro" not in st.session_state:
    st.session_state.tema_scuro = False  # Default LIGHT come nella foto

# ==================== CREDENZIALI ====================
GITHUB_TOKEN = st.secrets["GITHUB_TOKEN"]
NOME_REPOSITORY = "sofi-sofi-sofi/archivio-appunti"
g = Github(GITHUB_TOKEN)
repo = g.get_repo(NOME_REPOSITORY)

# ==========================================
# 2. VARIABILI TEMA
# ==========================================
is_dark = st.session_state.tema_scuro

if is_dark:
    # DARK MODE
    bg_app          = "#0d0d1a"
    text_main       = "#ffffff"
    text_sec        = "#9090b8"
    card_bg         = "#12122a"
    card_border     = "#ff007f"
    panel_shadow    = "rgba(255,0,127,0.2)"
    input_bg        = "#1a1a35"
    input_border    = "#2a2a55"
    input_placeholder = "#6060a0"
    row_border      = "#2a2a55"
    btn_elim_bg     = "#2d1b5e"
    btn_elim_color  = "#ffffff"
    pill_bg         = "#0d001f"
    pill_border     = "#ff007f"
    pill_color      = "#ff007f"
    pill_shadow     = "rgba(255,0,127,0.4)"
    fc_bg           = "#1a1a35"
    fc_border       = "#2a2a55"
    fc_hover        = "#ff007f"
    fc_text         = "#ffffff"
    grid_color      = "rgba(255,0,127,0.06)"
    upload_border   = "#ff007f"
    upload_bg       = "#0d001f"
    upload_text     = "#ff007f"
    logo_border     = "#9d00ff"
    logo_glow       = "rgba(157,0,255,0.5)"
    header_sub      = "#8888aa"
    man_icon_color  = "#ff4466"
else:
    # LIGHT MODE — identico alla foto
    bg_app          = "#e8e8f5"
    text_main       = "#111111"
    text_sec        = "#444444"
    card_bg         = "#ffffff"
    card_border     = "#ff007f"
    panel_shadow    = "rgba(0,0,0,0.08)"
    input_bg        = "#ffffff"
    input_border    = "#ddddee"
    input_placeholder = "#aaaacc"
    row_border      = "#eeeeee"
    btn_elim_bg     = "#2d1b5e"
    btn_elim_color  = "#ffffff"
    pill_bg         = "#0d001a"
    pill_border     = "#ff007f"
    pill_color      = "#ff007f"
    pill_shadow     = "rgba(255,0,127,0.35)"
    fc_bg           = "#ffffff"
    fc_border       = "#e8e8ee"
    fc_hover        = "#ff007f"
    fc_text         = "#111111"
    grid_color      = "rgba(200,0,150,0.07)"
    upload_border   = "#ff007f"
    upload_bg       = "#fff0f8"
    upload_text     = "#cc0066"
    logo_border     = "#9d00ff"
    logo_glow       = "rgba(157,0,255,0.4)"
    header_sub      = "#555555"
    man_icon_color  = "#ff0055"

# ==========================================
# 3. CSS GLOBALE — fedele alla foto
# ==========================================
st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&display=swap');

/* ── BASE ── */
html, body, .stApp, [data-testid="stAppViewContainer"], .main {{
    background-color: {bg_app} !important;
    font-family: 'Inter', sans-serif !important;
    color: {text_main} !important;
}}
.main .block-container {{
    padding: 1.2rem 2rem 2rem 2rem !important;
    max-width: 1400px !important;
}}

/* Circuit board — sottile, come nella foto */
[data-testid="stAppViewContainer"]::before {{
    content: '';
    position: fixed; inset: 0;
    background-image:
        linear-gradient({grid_color} 1px, transparent 1px),
        linear-gradient(90deg, {grid_color} 1px, transparent 1px);
    background-size: 38px 38px;
    pointer-events: none;
    z-index: 0;
}}

/* Nodi circuit board agli angoli */
[data-testid="stAppViewContainer"]::after {{
    content: '';
    position: fixed; inset: 0;
    background-image: radial-gradient({grid_color} 2px, transparent 2px);
    background-size: 38px 38px;
    background-position: 19px 19px;
    pointer-events: none;
    z-index: 0;
}}

/* ── TESTO GLOBALE ── */
h1,h2,h3,h4,h5,h6,p,span,label,li,div {{
    font-family: 'Inter', sans-serif !important;
    color: {text_main} !important;
}}

/* ── HIDE CHROME STREAMLIT ── */
#MainMenu, footer, header {{ visibility: hidden !important; }}
[data-testid="stToolbar"] {{ display: none !important; }}

/* ── LOGO ESAGONO ── */
.logo-hex {{
    width: 64px; height: 64px;
    border-radius: 16px;
    background: linear-gradient(135deg, #1a0033, #0d0022);
    border: 2px solid {logo_border};
    box-shadow: 0 0 20px {logo_glow};
    display: flex; align-items: center; justify-content: center;
    overflow: hidden;
}}

/* ── TITOLO ── */
.matora-title {{
    font-size: 2rem; font-weight: 900; letter-spacing: -0.5px; line-height: 1;
    background: linear-gradient(90deg, #ff007f, #9d00ff);
    -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text;
    margin: 0 0 2px 0;
}}
.matora-sub {{
    font-size: 0.88rem; font-weight: 400;
    color: {header_sub} !important; -webkit-text-fill-color: {header_sub} !important;
    margin: 0;
}}

/* ── PILLOLE NAV — identiche alla foto ── */
.pills-wrap {{
    display: flex; justify-content: center; gap: 12px;
    margin: 14px 0 24px 0;
}}
.pill {{
    background: {pill_bg};
    border: 2px solid {pill_border};
    border-radius: 50px;
    padding: 10px 26px;
    font-weight: 700; font-size: 0.8rem;
    color: {pill_color} !important; -webkit-text-fill-color: {pill_color} !important;
    text-transform: uppercase; letter-spacing: 1px;
    box-shadow: 0 0 12px {pill_shadow};
    display: inline-flex; align-items: center; gap: 7px;
    cursor: default;
}}

/* ── PANNELLI — bordo rosa, sfondo bianco/scuro, angoli 12px ── */
[data-testid="stVerticalBlockBorderWrapper"] {{
    background: {card_bg} !important;
    border: 1.5px solid {card_border} !important;
    border-radius: 12px !important;
    padding: 20px !important;
    box-shadow: 0 2px 16px {panel_shadow} !important;
}}

/* ── TITOLI PANNELLO — font bold, niente accent bar ── */
[data-testid="stVerticalBlockBorderWrapper"] h3 {{
    font-size: 1.25rem !important; font-weight: 800 !important;
    color: {text_main} !important; -webkit-text-fill-color: {text_main} !important;
    margin-bottom: 12px !important; letter-spacing: -0.3px;
}}

/* ── SELECTBOX ── */
div[data-baseweb="select"] > div {{
    background-color: {input_bg} !important;
    border: 1px solid {input_border} !important;
    border-radius: 8px !important; color: {text_main} !important;
    font-family: 'Inter', sans-serif !important;
}}
div[data-baseweb="select"] span {{
    color: {text_main} !important; -webkit-text-fill-color: {text_main} !important;
    font-family: 'Inter', sans-serif !important;
}}
div[data-baseweb="select"] svg {{ fill: {text_main} !important; }}
div[data-baseweb="popover"] li {{
    background-color: {input_bg} !important;
    color: {text_main} !important; font-family: 'Inter', sans-serif !important;
}}
div[data-baseweb="popover"] li:hover {{
    background-color: {card_border}22 !important;
}}

/* ── TEXT INPUT ── */
.stTextInput input {{
    background-color: {input_bg} !important;
    border: 1px solid {input_border} !important;
    border-radius: 8px !important; color: {text_main} !important;
    font-family: 'Inter', sans-serif !important; font-size: 0.9rem !important;
    padding: 9px 12px !important;
}}
.stTextInput input::placeholder {{ color: {input_placeholder} !important; }}
.stTextInput label {{
    color: {text_sec} !important; -webkit-text-fill-color: {text_sec} !important;
    font-size: 0.85rem !important; font-weight: 500 !important;
}}

/* ── FILE UPLOADER — box tratteggiato magenta come nella foto ── */
[data-testid="stFileUploaderDropzone"] {{
    background-color: {upload_bg} !important;
    border: 2px dashed {upload_border} !important;
    border-radius: 10px !important;
    padding: 18px !important;
}}
/* Nascondi il testo default di Streamlit e mostra solo il pulsante */
[data-testid="stFileUploaderDropzoneInstructions"] {{
    display: none !important;
}}
[data-testid="stFileUploaderDropzone"] button {{
    background: transparent !important;
    border: none !important;
    color: {upload_text} !important; -webkit-text-fill-color: {upload_text} !important;
    font-weight: 600 !important; font-size: 0.9rem !important;
    font-family: 'Inter', sans-serif !important;
    padding: 8px 16px !important;
    width: 100% !important;
    text-align: center !important;
}}
[data-testid="stFileUploaderDropzone"] small {{
    color: {text_sec} !important; font-size: 0.75rem !important;
}}

/* ── PULSANTE PRIMARY (Avvia) ── */
div.stButton > button[kind="primary"] {{
    background: linear-gradient(90deg, #ff007f, #cc00aa) !important;
    color: #ffffff !important;
    font-weight: 700 !important; font-family: 'Inter', sans-serif !important;
    font-size: 0.85rem !important; letter-spacing: 0.5px;
    border-radius: 8px !important; border: none !important;
    width: 100% !important; padding: 13px 20px !important;
    text-transform: uppercase;
    box-shadow: 0 3px 16px rgba(255,0,127,0.4) !important;
    transition: opacity 0.15s !important;
}}
div.stButton > button[kind="primary"]:hover {{
    opacity: 0.9 !important;
}}

/* ── PULSANTE ELIMINA (secondary) — viola scuro come foto ── */
div.stButton > button[kind="secondary"] {{
    background-color: {btn_elim_bg} !important;
    color: {btn_elim_color} !important; -webkit-text-fill-color: {btn_elim_color} !important;
    border: none !important;
    border-radius: 6px !important; font-weight: 600 !important;
    font-family: 'Inter', sans-serif !important;
    font-size: 0.78rem !important; padding: 5px 14px !important;
    white-space: nowrap; min-width: 70px;
}}
div.stButton > button[kind="secondary"]:hover {{
    background-color: #3d1b7e !important;
}}

/* ── TOGGLE ── */
[data-testid="stToggle"] label {{
    color: {text_sec} !important; -webkit-text-fill-color: {text_sec} !important;
    font-size: 0.85rem !important; font-weight: 600 !important;
    font-family: 'Inter', sans-serif !important;
}}

/* ── INFO / SUCCESS / ERROR ── */
[data-testid="stAlert"] {{
    border-radius: 8px !important;
    font-family: 'Inter', sans-serif !important;
}}

/* ── SIDEBAR ── */
[data-testid="stSidebar"] {{
    background-color: {card_bg} !important;
}}
</style>
""", unsafe_allow_html=True)

# ==========================================
# 4. HEADER — identico alla foto
# ==========================================
col_logo, col_titolo, col_toggle = st.columns([1, 8, 2], vertical_alignment="center")

with col_logo:
    st.image(
        "https://raw.githubusercontent.com/sofi-sofi-sofi/archivio-appunti/main/logo_matora.png",
        width=58
    )

with col_titolo:
    st.markdown(
        '<p class="matora-title">MATORA AI</p>'
        f'<p class="matora-sub">L\'ecosistema intelligente per i tuoi appunti universitari</p>',
        unsafe_allow_html=True
    )

with col_toggle:
    label_toggle = "☀️ Tema Chiaro" if is_dark else "🌙 Tema Scuro"
    st.toggle(label_toggle, key="tema_scuro")

# Pillole nav
st.markdown("""
<div class="pills-wrap">
    <div class="pill">📥 &nbsp;INVIA APPUNTI</div>
    <div class="pill">🔍 &nbsp;CERCA NELL'ARCHIVIO</div>
    <div class="pill">🗑️ &nbsp;MANUTENZIONE</div>
</div>
""", unsafe_allow_html=True)

# ==========================================
# RECUPERO DATI GITHUB — con cache breve per evitare ghost files
# ==========================================
@st.cache_data(ttl=10)
def get_github_data(token, repo_name):
    g2 = Github(token)
    r = g2.get_repo(repo_name)
    materie = set()
    files = []
    try:
        for folder in ["risultati", "appunti"]:
            try:
                for obj in r.get_contents(folder, ref="main"):
                    if obj.type == "dir":
                        materie.add(obj.name)
                        if folder == "risultati":
                            for f in r.get_contents(f"risultati/{obj.name}", ref="main"):
                                if f.name.endswith(".md"):
                                    files.append({"nome": f.name.replace(".md", ""), "url": f.html_url})
            except:
                pass
    except:
        pass
    return sorted(list(materie)), files

materie_ordinate, tutti_i_file = get_github_data(GITHUB_TOKEN, NOME_REPOSITORY)

# ==========================================
# 5. DASHBOARD 3 COLONNE
# ==========================================
col_invia, col_cerca, col_gestisci = st.columns([1.3, 2, 1.3], gap="large")

# ─── PANNELLO 1: INVIA ──────────────────────────────────────
with col_invia:
    with st.container(border=True):
        st.markdown("### Invia Appunti")
        st.markdown(f"<p style='font-size:0.88rem;font-weight:500;color:{text_sec};margin-bottom:8px;'>Su quale materia stai lavorando?</p>", unsafe_allow_html=True)

        opzioni = ["➕ Aggiungi Nuova Materia..."] + materie_ordinate
        scelta = st.selectbox("Materia", opzioni, label_visibility="collapsed")

        materia_selezionata = ""
        if scelta == "➕ Aggiungi Nuova Materia...":
            materia_selezionata = st.text_input("Nome nuova materia:")
        else:
            materia_selezionata = scelta

        st.markdown(f"<h4 style='margin:18px 0 2px 0;font-size:1.05rem;font-weight:800;'>PDF Upload</h4>", unsafe_allow_html=True)
        st.markdown(f"<p style='font-size:0.82rem;color:{text_sec};margin-bottom:8px;'>Trascina o seleziona il PDF dei tuoi appunti</p>", unsafe_allow_html=True)

        # Un solo file uploader, senza testo duplicato
        file_caricato = st.file_uploader(
            "[ Seleziona il file dal tuo iPad ]",
            type=["pdf"],
            label_visibility="visible"
        )
        nome_pers = st.text_input("Dai un nome al file (opzionale):", placeholder="es. Lezione_1")

        if file_caricato and materia_selezionata:
            if st.button("🚀 AVVIA ELABORAZIONE INTELLIGENTE", type="primary"):
                with st.spinner("Elaborazione AI in corso..."):
                    nome_base = nome_pers.strip().replace(" ", "_") if nome_pers else os.path.splitext(file_caricato.name)[0]
                    try:
                        pdf_bytes = file_caricato.read()
                        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
                        immagini = [
                            base64.b64encode(
                                doc.load_page(i).get_pixmap(matrix=fitz.Matrix(2, 2)).tobytes("png")
                            ).decode('utf-8')
                            for i in range(len(doc))
                        ]
                        client = ChatCompletionsClient(
                            endpoint="https://models.inference.ai.azure.com",
                            credential=AzureKeyCredential(GITHUB_TOKEN)
                        )
                        prompt = "Analizza questo appunto. Crea: 1. Riassunto. 2. Schema. 3. Quiz 3 domande. 4. Parole chiave."
                        contenuto = [{"type": "text", "text": prompt}] + [
                            {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{img}"}}
                            for img in immagini
                        ]
                        response = client.complete(
                            messages=[
                                SystemMessage(content="Sei un assistente universitario."),
                                UserMessage(content=contenuto)
                            ],
                            model="gpt-4o-mini", max_tokens=2500
                        )
                        risultato = response.choices[0].message.content
                        try:
                            repo.create_file(f"appunti/{materia_selezionata}/{nome_base}.pdf", "Nuovo PDF", pdf_bytes, branch="main")
                        except:
                            pass
                        path_md = f"risultati/{materia_selezionata}/{nome_base}.md"
                        try:
                            contents = repo.get_contents(path_md, ref="main")
                            repo.update_file(contents.path, "Aggiornato", risultato, contents.sha, branch="main")
                        except:
                            repo.create_file(path_md, "Creato", risultato, branch="main")
                        st.success("✅ Elaborazione completata!")
                        get_github_data.clear()
                        st.rerun()
                    except Exception as e:
                        st.error(f"Errore: {e}")

# ─── PANNELLO 2: CERCA — griglia identica alla foto ─────────
with col_cerca:
    with st.container(border=True):
        st.markdown("### Cerca nell'Archivio")
        query = st.text_input(
            "Cerca",
            placeholder="🔍  Cerca nell'Archivio... (#Tag o Materia)",
            label_visibility="collapsed"
        ).strip().lower()

        file_filtrati = [f for f in tutti_i_file if query in f["nome"].lower()] if query else tutti_i_file

        if file_filtrati:
            # Costruiamo le card con stile inline per evitare il bug di Streamlit
            cards_html = ""
            for f in file_filtrati:
                titolo = f["nome"].replace("_", " ").title()
                # Tronca titolo lungo
                titolo_display = titolo if len(titolo) <= 18 else titolo[:16] + "…"
                cards_html += f"""
                <a href="{f['url']}" target="_blank"
                   style="background:{fc_bg};border:1px solid {fc_border};border-radius:10px;
                          padding:12px 8px;text-align:center;text-decoration:none;
                          display:flex;flex-direction:column;align-items:center;
                          justify-content:flex-start;gap:6px;min-height:90px;
                          font-family:Inter,sans-serif;cursor:pointer;"
                   onmouseover="this.style.borderColor='{fc_hover}';this.style.transform='translateY(-2px)';this.style.boxShadow='0 4px 14px rgba(255,0,127,0.18)'"
                   onmouseout="this.style.borderColor='{fc_border}';this.style.transform='none';this.style.boxShadow='none'">
                  <div style="font-size:1.8rem;line-height:1;margin-bottom:2px;">📄</div>
                  <div style="font-size:0.75rem;font-weight:700;color:{fc_text};line-height:1.25;word-break:break-word;">{titolo_display}</div>
                </a>"""

            grid_html = f"""<!DOCTYPE html>
<html><head>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@700&display=swap" rel="stylesheet">
<style>
  body {{ margin:0; padding:0; background:transparent; font-family:Inter,sans-serif; }}
  .grid {{ display:grid; grid-template-columns:repeat(3,1fr); gap:10px; padding:4px 2px; }}
  a {{ transition: transform 0.15s, box-shadow 0.15s, border-color 0.15s; }}
</style>
</head><body>
<div class="grid">{cards_html}</div>
</body></html>"""

            n_rows = (len(file_filtrati) + 2) // 3
            components.html(grid_html, height=n_rows * 108 + 20, scrolling=False)
        else:
            st.info("Nessun appunto disponibile. Carica il tuo primo PDF!")

# ─── PANNELLO 3: MANUTENZIONE ────────────────────────────────
with col_gestisci:
    with st.container(border=True):
        st.markdown("### Manutenzione")
        st.markdown(
            f"<p style='font-size:0.88rem;font-weight:600;color:{text_sec};margin-bottom:10px;'>Gestisci Archivio</p>",
            unsafe_allow_html=True
        )

        materia_del = st.selectbox(
            "Materia da gestire",
            materie_ordinate if materie_ordinate else ["Nessuna materia"],
            label_visibility="collapsed"
        )

        if materia_del and materia_del != "Nessuna materia":
            tutti_files_del = []
            try:
                tutti_files_del.extend(repo.get_contents(f"appunti/{materia_del}", ref="main"))
            except:
                pass
            try:
                tutti_files_del.extend(repo.get_contents(f"risultati/{materia_del}", ref="main"))
            except:
                pass

            if not tutti_files_del:
                st.write("Cartella vuota.")
            else:
                for file_gh in tutti_files_del:
                    c1, c2 = st.columns([7, 3], vertical_alignment="center")
                    with c1:
                        icon = "📄" if file_gh.name.endswith(".pdf") else "📝"
                        st.markdown(
                            f"<span style='font-size:0.82rem;font-weight:600;display:flex;align-items:center;gap:5px;'>"
                            f"{icon} {file_gh.name}</span>",
                            unsafe_allow_html=True
                        )
                    with c2:
                        if st.button("Elimina", key=f"del_{file_gh.path}"):
                            try:
                                repo.delete_file(file_gh.path, "Rimosso", file_gh.sha, branch="main")
                                get_github_data.clear()
                                st.rerun()
                            except:
                                st.error("Errore eliminazione")
