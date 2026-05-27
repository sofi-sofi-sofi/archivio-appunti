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
    st.session_state.tema_scuro = False

# ==================== CREDENZIALI ====================
GITHUB_TOKEN = st.secrets["GITHUB_TOKEN"]
NOME_REPOSITORY = "sofi-sofi-sofi/archivio-appunti"
g = Github(GITHUB_TOKEN)
repo = g.get_repo(NOME_REPOSITORY)

# ==========================================
# 2. MOTORE CSS DINAMICO (LIGHT / DARK MODE)
# ==========================================
if st.session_state.tema_scuro:
    bg_app = "#0a0a0a"
    text_main = "#ffffff"
    text_sec = "#a3a3a3"
    card_bg = "#111111"
    card_border = "#9d00ff"
    neon_glow = "rgba(157, 0, 255, 0.4)"
    input_bg = "#1a1a1a"
    input_border = "#333333"
    btn_elimina = "#1f0033"
else:
    bg_app = "#f5f5fc"
    text_main = "#000000"
    text_sec = "#4a4a4a"
    card_bg = "#ffffff"
    card_border = "#ff007f"
    neon_glow = "rgba(255, 0, 127, 0.2)"
    input_bg = "#ffffff"
    input_border = "#e0e0e0"
    btn_elimina = "#1a0033"

st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap');
    
    /* Reset Generale */
    .stApp {{
        background-color: {bg_app} !important;
        color: {text_main} !important;
        font-family: 'Plus Jakarta Sans', sans-serif !important;
    }}
    
    h1, h2, h3, h4, p, span, label {{
        color: {text_main} !important;
    }}

    /* HEADER & PILLOLE SUPERIORI */
    .header-logo-text {{
        font-weight: 800;
        font-size: 2rem;
        letter-spacing: -1px;
        margin-bottom: 0;
        background: linear-gradient(90deg, #ff007f, #9d00ff);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }}
    .pills-container {{
        display: flex;
        justify-content: center;
        gap: 20px;
        margin: 10px 0 30px 0;
    }}
    .nav-pill {{
        background-color: #0b001a;
        border: 2px solid #ff007f;
        border-radius: 50px;
        padding: 12px 30px;
        font-weight: 700;
        font-size: 0.9rem;
        color: #ff007f !important;
        box-shadow: 0 0 15px rgba(255, 0, 127, 0.4);
        text-transform: uppercase;
        letter-spacing: 1px;
    }}

    /* STILE DEI 3 PANNELLI PRINCIPALI */
    [data-testid="stVerticalBlockBorderWrapper"] {{
        background-color: {card_bg} !important;
        border: 2px solid {card_border} !important;
        border-radius: 12px !important;
        padding: 20px !important;
        box-shadow: 0 0 20px {neon_glow} !important;
    }}

    /* INPUT E DROPZONE */
    div[data-baseweb="select"] > div, .stTextInput input {{
        background-color: {input_bg} !important;
        border: 1px solid {input_border} !important;
        color: {text_main} !important;
        border-radius: 8px !important;
    }}
    div[data-testid="stFileUploaderDropzone"] {{
        background-color: {input_bg} !important;
        border: 2px dashed {card_border} !important;
        border-radius: 12px !important;
        padding: 25px !important;
    }}

    /* PULSANTI */
    div.stButton > button[kind="primary"] {{
        background: linear-gradient(90deg, #ff007f, #9d00ff) !important;
        color: white !important;
        font-weight: 800 !important;
        border-radius: 8px !important;
        border: none !important;
        width: 100%;
        padding: 12px !important;
        box-shadow: 0 4px 15px {neon_glow} !important;
    }}
    
    /* GRIGLIA FILE ARCHIVIO (Fedele all'immagine) */
    .file-grid {{
        display: grid;
        grid-template-columns: repeat(3, 1fr);
        gap: 15px;
        margin-top: 10px;
    }}
    .file-card {{
        background-color: {card_bg};
        border: 1px solid {input_border};
        border-radius: 10px;
        padding: 15px 10px;
        text-align: center;
        text-decoration: none;
        display: flex;
        flex-direction: column;
        align-items: center;
        gap: 10px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.05);
        transition: transform 0.2s, border-color 0.2s;
    }}
    .file-card:hover {{
        transform: translateY(-3px);
        border-color: {card_border};
        box-shadow: 0 5px 15px {neon_glow};
    }}
    .file-icon {{
        font-size: 2rem;
        color: #ff007f;
    }}
    .file-title {{
        font-size: 0.85rem;
        font-weight: 700;
        color: {text_main};
        line-height: 1.2;
    }}

    /* ELENCO MANUTENZIONE */
    .manutenzione-row {{
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 10px 0;
        border-bottom: 1px solid {input_border};
    }}
    </style>
""", unsafe_allow_html=True)

# ==========================================
# 3. HEADER
# ==========================================
col_logo, col_titolo, col_toggle = st.columns([1, 8, 2], vertical_alignment="center")
with col_logo:
    st.image("https://raw.githubusercontent.com/sofi-sofi-sofi/archivio-appunti/main/logo_matora.png", width=60)
with col_titolo:
    st.markdown('<p class="header-logo-text">MATORA AI</p><p style="margin:0; font-size:1rem; font-weight:500;">L\'ecosistema intelligente per i tuoi appunti universitari</p>', unsafe_allow_html=True)
with col_toggle:
    st.toggle("Tema Scuro", key="tema_scuro")

# Pillole decorative in alto
st.markdown("""
<div class="pills-container">
    <div class="nav-pill">📥 INVIA APPUNTI</div>
    <div class="nav-pill">🔍 CERCA NELL'ARCHIVIO</div>
    <div class="nav-pill">🗑️ MANUTENZIONE</div>
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
                    # Precarica file per la griglia
                    if folder == "risultati":
                        for f in repo.get_contents(f"risultati/{obj.name}", ref="main"):
                            if f.name.endswith(".md"):
                                tutti_i_file.append({"nome": f.name.replace(".md", ""), "url": f.html_url})
        except: pass
except: pass
materie_ordinate = sorted(list(materie_rilevate))

# ==========================================
# 4. DASHBOARD A 3 COLONNE IDENTICA ALL'IMMAGINE
# ==========================================
col_invia, col_cerca, col_gestisci = st.columns([1.3, 2, 1.3], gap="large")

# ----------------- PANNELLO 1: INVIA -----------------
with col_invia:
    with st.container(border=True):
        st.markdown("### Invia Appunti")
        st.markdown("<p style='font-size:0.9rem; margin-bottom:5px;'>Su quale materia stai lavorando?</p>", unsafe_allow_html=True)
        
        opzioni = ["-- Seleziona --", "➕ Aggiungi Nuova Materia..."] + materie_ordinate
        scelta = st.selectbox("Materia", opzioni, label_visibility="collapsed")
        
        materia_selezionata = ""
        if scelta == "➕ Aggiungi Nuova Materia...":
            materia_selezionata = st.text_input("Nome nuova materia:")
        elif scelta != "-- Seleziona --":
            materia_selezionata = scelta

        st.markdown("<h4 style='margin-top:20px;'>PDF Upload</h4>", unsafe_allow_html=True)
        file_caricato = st.file_uploader("Trascina o seleziona il PDF dei tuoi appunti", type=["pdf"])
        nome_pers = st.text_input("Dai un nome al file (opzionale):")

        if file_caricato and materia_selezionata:
            if st.button("🚀 AVVIA ELABORAZIONE INTELIGENTE", type="primary"):
                with st.spinner("Elaborazione AI in corso..."):
                    nome_base = nome_pers.strip().replace(" ", "_") if nome_pers else os.path.splitext(file_caricato.name)[0]
                    try:
                        pdf_bytes = file_caricato.read()
                        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
                        immagini = [base64.b64encode(doc.load_page(i).get_pixmap(matrix=fitz.Matrix(2,2)).tobytes("png")).decode('utf-8') for i in range(len(doc))]
                        
                        client = ChatCompletionsClient(endpoint="https://models.inference.ai.azure.com", credential=AzureKeyCredential(GITHUB_TOKEN))
                        prompt = "Analizza questo appunto. Crea: 1. Riassunto. 2. Schema. 3. Quiz 3 domande. 4. Parole chiave."
                        
                        contenuto = [{"type": "text", "text": prompt}] + [{"type": "image_url", "image_url": {"url": f"data:image/png;base64,{img}"}} for img in immagini]
                        response = client.complete(
                            messages=[SystemMessage(content="Sei un assistente universitario."), UserMessage(content=contenuto)],
                            model="gpt-4o-mini", max_tokens=2500
                        )
                        risultato = response.choices[0].message.content

                        try: repo.create_file(f"appunti/{materia_selezionata}/{nome_base}.pdf", "Nuovo PDF", pdf_bytes, branch="main")
                        except: pass
                        
                        path_md = f"risultati/{materia_selezionata}/{nome_base}.md"
                        try:
                            contents = repo.get_contents(path_md, ref="main")
                            repo.update_file(contents.path, "Aggiornato", risultato, contents.sha, branch="main")
                        except:
                            repo.create_file(path_md, "Creato", risultato, branch="main")
                        
                        st.success("Fatto!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Errore: {e}")

# ----------------- PANNELLO 2: CERCA (Griglia Visiva) -----------------
with col_cerca:
    with st.container(border=True):
        st.markdown("### Cerca nell'Archivio")
        query = st.text_input("Cerca", placeholder="🔍 Cerca nell'Archivio... (#Tag o Materia)", label_visibility="collapsed").strip().lower()
        
        file_filtrati = [f for f in tutti_i_file if query in f["nome"].lower()] if query else tutti_i_file
        
        if file_filtrati:
            grid_html = '<div class="file-grid">'
            for f in file_filtrati:
                # Ripristina spazi nel titolo per una lettura pulita
                titolo_bello = f["nome"].replace("_", " ").title()
                grid_html += f'''
                <a href="{f["url"]}" target="_blank" class="file-card">
                    <div class="file-icon">📄</div>
                    <div class="file-title">{titolo_bello}</div>
                </a>
                '''
            grid_html += '</div>'
            st.markdown(grid_html, unsafe_allow_html=True)
        else:
            st.info("Nessun appunto disponibile. Carica il tuo primo PDF!")

# ----------------- PANNELLO 3: MANUTENZIONE -----------------
with col_gestisci:
    with st.container(border=True):
        st.markdown("### Manutenzione")
        st.markdown("<p style='font-size:0.9rem; font-weight:600;'>Gestisci Archivio</p>", unsafe_allow_html=True)
        
        materia_del = st.selectbox("Seleziona", materie_ordinate if materie_ordinate else ["Nessuna materia"], label_visibility="collapsed")
        
        if materia_del and materia_del != "Nessuna materia":
            tutti_files_del = []
            try: tutti_files_del.extend(repo.get_contents(f"appunti/{materia_del}", ref="main"))
            except: pass
            try: tutti_files_del.extend(repo.get_contents(f"risultati/{materia_del}", ref="main"))
            except: pass
            
            if not tutti_files_del:
                st.write("Cartella vuota.")
            else:
                for file_gh in tutti_files_del:
                    c1, c2 = st.columns([7, 3], vertical_alignment="center")
                    with c1:
                        icon = "📄" if file_gh.name.endswith(".pdf") else "📝"
                        st.markdown(f"<span style='font-size:0.85rem; font-weight:600;'>{icon} {file_gh.name}</span>", unsafe_allow_html=True)
                    with c2:
                        # Pulsante elimina in stile scuro
                        st.markdown(f"""
                            <style>
                            div[data-testid="stButton"] button:contains("Elimina") {{
                                background-color: {btn_elimina} !important;
                                color: white !important;
                                padding: 2px 10px !important;
                                border-radius: 8px !important;
                                border: 1px solid rgba(255,255,255,0.1) !important;
                            }}
                            </style>
                        """, unsafe_allow_html=True)
                        if st.button("Elimina", key=f"del_{file_gh.path}"):
                            try:
                                repo.delete_file(file_gh.path, "Rimosso", file_gh.sha, branch="main")
                                st.rerun()
                            except:
                                st.error("Errore")
