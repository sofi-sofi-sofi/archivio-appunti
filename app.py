import streamlit as st
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
    st.session_state.tema_scuro = True  # Default dark come da foto

# ==================== CREDENZIALI ====================
GITHUB_TOKEN = st.secrets["GITHUB_TOKEN"]
NOME_REPOSITORY = "sofi-sofi-sofi/archivio-appunti"
g = Github(GITHUB_TOKEN)
repo = g.get_repo(NOME_REPOSITORY)

# ==========================================
# 2. MOTORE CSS DINAMICO (LIGHT / DARK MODE)
# ==========================================
is_dark = st.session_state.tema_scuro

if is_dark:
    bg_app         = "#0d0d1a"
    bg_circuit     = "#0d0d1a"
    text_main      = "#ffffff"
    text_sec       = "#b0b0c8"
    card_bg        = "#13132a"
    card_bg_inner  = "#0f0f22"
    card_border    = "#9d00ff"
    card_border2   = "#ff007f"
    neon_glow      = "rgba(157, 0, 255, 0.35)"
    neon_glow2     = "rgba(255, 0, 127, 0.35)"
    input_bg       = "#1a1a35"
    input_border   = "#2a2a4a"
    row_border     = "#2a2a4a"
    btn_elimina_bg = "#2d0045"
    btn_elimina_border = "#9d00ff"
    toggle_label   = "#c0c0e0"
    header_sub     = "#a0a0c0"
    pill_bg        = "#0d001f"
    pill_border    = "#ff007f"
    pill_color     = "#ff007f"
    filecard_bg    = "#1a1a35"
    filecard_border = "#2a2a50"
    filecard_hover_border = "#9d00ff"
    scrollbar_track = "#0d0d1a"
    scrollbar_thumb = "#3a0060"
else:
    bg_app         = "#f0f0fa"
    bg_circuit     = "#f0f0fa"
    text_main      = "#0a0a1a"
    text_sec       = "#4a4a6a"
    card_bg        = "#ffffff"
    card_bg_inner  = "#f8f8ff"
    card_border    = "#ff007f"
    card_border2   = "#9d00ff"
    neon_glow      = "rgba(255, 0, 127, 0.18)"
    neon_glow2     = "rgba(157, 0, 255, 0.18)"
    input_bg       = "#f5f5ff"
    input_border   = "#ddddf0"
    row_border     = "#ebebf8"
    btn_elimina_bg = "#1a0033"
    btn_elimina_border = "#9d00ff"
    toggle_label   = "#4a4a6a"
    header_sub     = "#5a5a7a"
    pill_bg        = "#0b001a"
    pill_border    = "#ff007f"
    pill_color     = "#ff007f"
    filecard_bg    = "#ffffff"
    filecard_border = "#e8e8f5"
    filecard_hover_border = "#ff007f"
    scrollbar_track = "#f0f0fa"
    scrollbar_thumb = "#d0a0e0"

st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@400;500;600;700;800;900&display=swap');

    /* ─── RESET & BASE ─────────────────────────────── */
    * {{ box-sizing: border-box; }}

    html, body, .stApp, .main, [data-testid="stAppViewContainer"] {{
        background-color: {bg_app} !important;
        font-family: 'Outfit', sans-serif !important;
        color: {text_main} !important;
    }}

    /* Rimuovi padding Streamlit */
    .main .block-container {{
        padding-top: 1.5rem !important;
        padding-bottom: 2rem !important;
        padding-left: 2rem !important;
        padding-right: 2rem !important;
        max-width: 1400px !important;
    }}

    /* Scrollbar personalizzata */
    ::-webkit-scrollbar {{ width: 6px; }}
    ::-webkit-scrollbar-track {{ background: {scrollbar_track}; }}
    ::-webkit-scrollbar-thumb {{ background: {scrollbar_thumb}; border-radius: 3px; }}

    /* ─── CIRCUIT BOARD BACKGROUND ─────────────────── */
    [data-testid="stAppViewContainer"]::before {{
        content: '';
        position: fixed;
        inset: 0;
        background-image:
            linear-gradient({card_border}15 1px, transparent 1px),
            linear-gradient(90deg, {card_border}15 1px, transparent 1px);
        background-size: 40px 40px;
        pointer-events: none;
        z-index: 0;
    }}

    /* ─── TESTO GLOBALE ────────────────────────────── */
    h1, h2, h3, h4, h5, h6, p, span, label, div {{
        color: {text_main} !important;
    }}

    /* ─── HEADER ───────────────────────────────────── */
    .matora-header {{
        display: flex;
        align-items: center;
        gap: 16px;
        margin-bottom: 4px;
    }}
    .matora-logo-wrap {{
        width: 56px;
        height: 56px;
        border-radius: 14px;
        background: linear-gradient(135deg, #ff007f22, #9d00ff33);
        border: 2px solid #9d00ff;
        display: flex;
        align-items: center;
        justify-content: center;
        box-shadow: 0 0 18px rgba(157,0,255,0.4);
        overflow: hidden;
    }}
    .matora-title-block {{ display: flex; flex-direction: column; gap: 2px; }}
    .matora-title {{
        font-size: 2rem;
        font-weight: 900;
        letter-spacing: -1px;
        line-height: 1;
        background: linear-gradient(90deg, #ff007f, #9d00ff);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
    }}
    .matora-subtitle {{
        font-size: 0.88rem;
        font-weight: 500;
        color: {header_sub} !important;
        -webkit-text-fill-color: {header_sub} !important;
    }}

    /* ─── PILLOLE NAV ──────────────────────────────── */
    .pills-container {{
        display: flex;
        justify-content: center;
        gap: 16px;
        margin: 18px 0 28px 0;
        flex-wrap: wrap;
    }}
    .nav-pill {{
        background: {pill_bg};
        border: 2px solid {pill_border};
        border-radius: 50px;
        padding: 11px 28px;
        font-weight: 700;
        font-size: 0.82rem;
        color: {pill_color} !important;
        -webkit-text-fill-color: {pill_color} !important;
        box-shadow: 0 0 14px {neon_glow2}, inset 0 0 10px rgba(255,0,127,0.05);
        text-transform: uppercase;
        letter-spacing: 1.5px;
        display: inline-flex;
        align-items: center;
        gap: 8px;
        cursor: default;
        transition: box-shadow 0.2s;
    }}
    .nav-pill:hover {{
        box-shadow: 0 0 22px {neon_glow2};
    }}

    /* ─── PANNELLI (container con bordo) ───────────── */
    [data-testid="stVerticalBlockBorderWrapper"] {{
        background: {card_bg} !important;
        border: 1.5px solid {card_border} !important;
        border-radius: 16px !important;
        padding: 22px !important;
        box-shadow: 0 0 24px {neon_glow}, 0 4px 20px rgba(0,0,0,0.12) !important;
        position: relative;
        overflow: hidden;
    }}
    /* Accent bar in cima al pannello */
    [data-testid="stVerticalBlockBorderWrapper"]::before {{
        content: '';
        position: absolute;
        top: 0; left: 0; right: 0;
        height: 3px;
        background: linear-gradient(90deg, #ff007f, #9d00ff);
        border-radius: 16px 16px 0 0;
    }}

    /* ─── TITOLI PANNELLO ──────────────────────────── */
    [data-testid="stVerticalBlockBorderWrapper"] h3 {{
        font-size: 1.2rem !important;
        font-weight: 800 !important;
        color: {text_main} !important;
        -webkit-text-fill-color: {text_main} !important;
        margin-bottom: 14px !important;
        letter-spacing: -0.3px;
    }}

    /* ─── SELECT / INPUT / DROPZONE ────────────────── */
    div[data-baseweb="select"] > div {{
        background-color: {input_bg} !important;
        border: 1.5px solid {input_border} !important;
        border-radius: 10px !important;
        color: {text_main} !important;
        transition: border-color 0.2s;
    }}
    div[data-baseweb="select"] > div:focus-within {{
        border-color: {card_border} !important;
        box-shadow: 0 0 0 3px {neon_glow} !important;
    }}
    div[data-baseweb="select"] span,
    div[data-baseweb="select"] svg {{
        color: {text_main} !important;
        fill: {text_main} !important;
    }}
    /* Dropdown options */
    div[data-baseweb="popover"] ul li {{
        background-color: {input_bg} !important;
        color: {text_main} !important;
    }}
    div[data-baseweb="popover"] ul li:hover {{
        background-color: {card_border}33 !important;
    }}

    .stTextInput input {{
        background-color: {input_bg} !important;
        border: 1.5px solid {input_border} !important;
        border-radius: 10px !important;
        color: {text_main} !important;
        padding: 10px 14px !important;
        font-family: 'Outfit', sans-serif !important;
        transition: border-color 0.2s;
    }}
    .stTextInput input:focus {{
        border-color: {card_border} !important;
        box-shadow: 0 0 0 3px {neon_glow} !important;
    }}
    .stTextInput input::placeholder {{ color: {text_sec} !important; }}

    /* Search box con icona */
    .stTextInput input[placeholder*="Cerca"] {{
        background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='16' height='16' fill='%239d00ff' viewBox='0 0 16 16'%3E%3Cpath d='M11.742 10.344a6.5 6.5 0 1 0-1.397 1.398l3.85 3.85a1 1 0 0 0 1.415-1.415l-3.868-3.833zM12 6.5a5.5 5.5 0 1 1-11 0 5.5 5.5 0 0 1 11 0z'/%3E%3C/svg%3E");
        background-repeat: no-repeat;
        background-position: 12px center;
        padding-left: 38px !important;
    }}

    /* File uploader dropzone */
    div[data-testid="stFileUploaderDropzone"] {{
        background-color: {input_bg} !important;
        border: 2px dashed {card_border} !important;
        border-radius: 12px !important;
        padding: 20px !important;
        transition: border-color 0.2s, box-shadow 0.2s;
    }}
    div[data-testid="stFileUploaderDropzone"]:hover {{
        border-color: #ff007f !important;
        box-shadow: 0 0 16px {neon_glow2} !important;
    }}
    div[data-testid="stFileUploaderDropzone"] > div {{
        color: {text_sec} !important;
    }}
    div[data-testid="stFileUploaderDropzone"] button {{
        background: transparent !important;
        border: 1.5px solid {card_border} !important;
        color: {card_border} !important;
        border-radius: 8px !important;
        font-weight: 600 !important;
        font-family: 'Outfit', sans-serif !important;
    }}

    /* ─── LABEL STREAMLIT ──────────────────────────── */
    .stTextInput label, .stFileUploader label, .stSelectbox label {{
        color: {text_sec} !important;
        font-size: 0.85rem !important;
        font-weight: 500 !important;
        -webkit-text-fill-color: {text_sec} !important;
    }}

    /* ─── PULSANTE PRIMARY ─────────────────────────── */
    div.stButton > button[kind="primary"] {{
        background: linear-gradient(90deg, #ff007f, #9d00ff) !important;
        color: #ffffff !important;
        font-weight: 800 !important;
        font-family: 'Outfit', sans-serif !important;
        font-size: 0.9rem !important;
        letter-spacing: 0.5px;
        border-radius: 10px !important;
        border: none !important;
        width: 100% !important;
        padding: 14px 20px !important;
        box-shadow: 0 4px 18px {neon_glow2} !important;
        transition: transform 0.15s, box-shadow 0.15s !important;
        text-transform: uppercase;
    }}
    div.stButton > button[kind="primary"]:hover {{
        transform: translateY(-2px) !important;
        box-shadow: 0 8px 28px {neon_glow2} !important;
    }}
    div.stButton > button[kind="primary"]:active {{
        transform: translateY(0) !important;
    }}

    /* ─── PULSANTE ELIMINA ─────────────────────────── */
    div.stButton > button[kind="secondary"] {{
        background-color: {btn_elimina_bg} !important;
        color: #e070ff !important;
        border: 1.5px solid {btn_elimina_border} !important;
        border-radius: 8px !important;
        font-weight: 700 !important;
        font-family: 'Outfit', sans-serif !important;
        font-size: 0.8rem !important;
        padding: 5px 14px !important;
        transition: background 0.15s, box-shadow 0.15s !important;
        white-space: nowrap;
    }}
    div.stButton > button[kind="secondary"]:hover {{
        background-color: #3d0060 !important;
        box-shadow: 0 0 10px rgba(157,0,255,0.4) !important;
    }}

    /* ─── TOGGLE TEMA ──────────────────────────────── */
    [data-testid="stToggle"] label {{
        color: {toggle_label} !important;
        -webkit-text-fill-color: {toggle_label} !important;
        font-size: 0.85rem !important;
        font-weight: 600 !important;
    }}
    [data-testid="stToggle"] [data-testid="stToggleCheckbox"] {{
        accent-color: #9d00ff !important;
    }}

    /* ─── GRIGLIA FILE ARCHIVIO ────────────────────── */
    .file-grid {{
        display: grid;
        grid-template-columns: repeat(3, 1fr);
        gap: 12px;
        margin-top: 12px;
    }}
    .file-card {{
        background: {filecard_bg};
        border: 1.5px solid {filecard_border};
        border-radius: 12px;
        padding: 14px 10px;
        text-align: center;
        text-decoration: none !important;
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        gap: 8px;
        transition: transform 0.18s, border-color 0.18s, box-shadow 0.18s;
        min-height: 90px;
    }}
    .file-card:hover {{
        transform: translateY(-4px);
        border-color: {filecard_hover_border};
        box-shadow: 0 6px 20px {neon_glow};
        text-decoration: none !important;
    }}
    .file-icon {{
        font-size: 1.7rem;
        line-height: 1;
    }}
    .file-title {{
        font-size: 0.78rem;
        font-weight: 700;
        color: {text_main} !important;
        -webkit-text-fill-color: {text_main} !important;
        line-height: 1.25;
        word-break: break-word;
    }}

    /* ─── RIGHE MANUTENZIONE ───────────────────────── */
    .manutenzione-row {{
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 9px 0;
        border-bottom: 1px solid {row_border};
    }}
    .manutenzione-row:last-child {{ border-bottom: none; }}

    /* ─── SPINNER ──────────────────────────────────── */
    [data-testid="stSpinner"] > div {{
        border-top-color: #ff007f !important;
    }}

    /* ─── SUCCESS / INFO / ERROR ───────────────────── */
    [data-testid="stAlert"] {{
        border-radius: 10px !important;
        font-family: 'Outfit', sans-serif !important;
    }}

    /* ─── SIDEBAR ──────────────────────────────────── */
    [data-testid="stSidebar"] {{
        background-color: {card_bg} !important;
        border-right: 1px solid {input_border} !important;
    }}

    /* ─── Nascondi watermark Streamlit ─────────────── */
    #MainMenu, footer, header {{ visibility: hidden; }}
    </style>
""", unsafe_allow_html=True)

# ==========================================
# 3. HEADER
# ==========================================
col_logo, col_titolo, col_toggle = st.columns([1, 8, 2], vertical_alignment="center")

with col_logo:
    st.image("https://raw.githubusercontent.com/sofi-sofi-sofi/archivio-appunti/main/logo_matora.png", width=56)

with col_titolo:
    st.markdown(
        f'<div class="matora-header">'
        f'<div class="matora-title-block">'
        f'<span class="matora-title">MATORA AI</span>'
        f'<span class="matora-subtitle">L\'ecosistema intelligente per i tuoi appunti universitari</span>'
        f'</div></div>',
        unsafe_allow_html=True
    )

with col_toggle:
    st.toggle("🌙 Tema Scuro" if not is_dark else "☀️ Tema Chiaro", key="tema_scuro")

# ─── PILLOLE NAV ────────────────────────────────────────
st.markdown("""
<div class="pills-container">
    <div class="nav-pill">📥&nbsp;&nbsp;INVIA APPUNTI</div>
    <div class="nav-pill">🔍&nbsp;&nbsp;CERCA NELL'ARCHIVIO</div>
    <div class="nav-pill">🗑️&nbsp;&nbsp;MANUTENZIONE</div>
</div>
""", unsafe_allow_html=True)

# ==========================================
# RECUPERO DATI GITHUB
# ==========================================
materie_rilevate = set()
tutti_i_file = []
try:
    for folder in ["risultati", "appunti"]:
        try:
            for obj in repo.get_contents(folder, ref="main"):
                if obj.type == "dir":
                    materie_rilevate.add(obj.name)
                    if folder == "risultati":
                        for f in repo.get_contents(f"risultati/{obj.name}", ref="main"):
                            if f.name.endswith(".md"):
                                tutti_i_file.append({"nome": f.name.replace(".md", ""), "url": f.html_url})
        except:
            pass
except:
    pass
materie_ordinate = sorted(list(materie_rilevate))

# ==========================================
# 4. DASHBOARD A 3 COLONNE
# ==========================================
col_invia, col_cerca, col_gestisci = st.columns([1.3, 2, 1.3], gap="large")

# ─── PANNELLO 1: INVIA ──────────────────────────────────
with col_invia:
    with st.container(border=True):
        st.markdown("### Invia Appunti")
        st.markdown(f"<p style='font-size:0.88rem; font-weight:500; color:{text_sec}; margin-bottom:6px;'>Su quale materia stai lavorando?</p>", unsafe_allow_html=True)

        opzioni = ["➕ Aggiungi Nuova Materia..."] + materie_ordinate
        scelta = st.selectbox("Materia", opzioni, label_visibility="collapsed")

        materia_selezionata = ""
        if scelta == "➕ Aggiungi Nuova Materia...":
            materia_selezionata = st.text_input("Nome nuova materia:")
        else:
            materia_selezionata = scelta

        st.markdown(f"<h4 style='margin-top:18px; margin-bottom:6px; font-size:1rem; font-weight:700;'>📄 PDF Upload</h4>", unsafe_allow_html=True)
        st.markdown(f"<p style='font-size:0.82rem; color:{text_sec}; margin-bottom:8px;'>Trascina o seleziona il PDF dei tuoi appunti</p>", unsafe_allow_html=True)
        file_caricato = st.file_uploader("PDF", type=["pdf"], label_visibility="collapsed")
        nome_pers = st.text_input("Dai un nome al file (opzionale):", placeholder="es. Lezione_1")

        if file_caricato and materia_selezionata:
            if st.button("🚀 AVVIA ELABORAZIONE INTELLIGENTE", type="primary"):
                with st.spinner("Elaborazione AI in corso..."):
                    nome_base = nome_pers.strip().replace(" ", "_") if nome_pers else os.path.splitext(file_caricato.name)[0]
                    try:
                        pdf_bytes = file_caricato.read()
                        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
                        immagini = [base64.b64encode(doc.load_page(i).get_pixmap(matrix=fitz.Matrix(2, 2)).tobytes("png")).decode('utf-8') for i in range(len(doc))]

                        client = ChatCompletionsClient(endpoint="https://models.inference.ai.azure.com", credential=AzureKeyCredential(GITHUB_TOKEN))
                        prompt = "Analizza questo appunto. Crea: 1. Riassunto. 2. Schema. 3. Quiz 3 domande. 4. Parole chiave."

                        contenuto = [{"type": "text", "text": prompt}] + [{"type": "image_url", "image_url": {"url": f"data:image/png;base64,{img}"}} for img in immagini]
                        response = client.complete(
                            messages=[SystemMessage(content="Sei un assistente universitario."), UserMessage(content=contenuto)],
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
                        st.rerun()
                    except Exception as e:
                        st.error(f"Errore: {e}")

# ─── PANNELLO 2: CERCA ──────────────────────────────────
with col_cerca:
    with st.container(border=True):
        st.markdown("### Cerca nell'Archivio")
        query = st.text_input("Cerca", placeholder="🔍  Cerca nell'Archivio... (#Tag o Materia)", label_visibility="collapsed").strip().lower()

        file_filtrati = [f for f in tutti_i_file if query in f["nome"].lower()] if query else tutti_i_file

        if file_filtrati:
            grid_html = '<div class="file-grid">'
            for f in file_filtrati:
                titolo_bello = f["nome"].replace("_", " ").title()
                # Icona colore in base all'estensione
                icon = "📄"
                grid_html += f'''
                <a href="{f["url"]}" target="_blank" class="file-card">
                    <div class="file-icon">{icon}</div>
                    <div class="file-title">{titolo_bello}</div>
                </a>
                '''
            grid_html += '</div>'
            st.markdown(grid_html, unsafe_allow_html=True)
        else:
            st.info("Nessun appunto disponibile. Carica il tuo primo PDF!")

# ─── PANNELLO 3: MANUTENZIONE ───────────────────────────
with col_gestisci:
    with st.container(border=True):
        st.markdown("### Manutenzione")
        st.markdown(f"<p style='font-size:0.88rem; font-weight:600; margin-bottom:10px;'>Gestisci Archivio</p>", unsafe_allow_html=True)

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
                            f"<span style='font-size:0.83rem; font-weight:600;'>{icon} {file_gh.name}</span>",
                            unsafe_allow_html=True
                        )
                    with c2:
                        if st.button("Elimina", key=f"del_{file_gh.path}"):
                            try:
                                repo.delete_file(file_gh.path, "Rimosso", file_gh.sha, branch="main")
                                st.rerun()
                            except:
                                st.error("Errore eliminazione")
