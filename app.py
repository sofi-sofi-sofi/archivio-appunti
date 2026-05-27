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
st.set_page_config(page_title="Matora AI", page_icon="logo_matora.png", layout="wide")

if "tema_scuro" not in st.session_state:
    st.session_state.tema_scuro = False

# Credenziali (assicurati di averle nei secrets)
GITHUB_TOKEN = st.secrets["GITHUB_TOKEN"]
NOME_REPOSITORY = "sofi-sofi-sofi/archivio-appunti"
g = Github(GITHUB_TOKEN)
repo = g.get_repo(NOME_REPOSITORY)

# ==========================================
# 2. MOTORE CSS DINAMICO (LIGHT / DARK MODE)
# ==========================================
if st.session_state.tema_scuro:
    # --- VARIABILI TEMA SCURO (Ispirato al Logo) ---
    css_vars = """
    :root {
        --bg-app: #08050e;
        --text-main: #ffffff;
        --text-sec: #a39eb8;
        --card-bg: #120c21;
        --card-border: #a333ff;
        --neon-glow: rgba(163, 51, 255, 0.35);
        --input-bg: #1b1330;
        --input-border: #3d2b63;
        --btn-grad: linear-gradient(90deg, #9b2de0, #5c16c5);
        --item-bg: #1c142e;
    }
    """
else:
    # --- VARIABILI TEMA CHIARO (Ispirato al Mockup) ---
    css_vars = """
    :root {
        --bg-app: #f4f6f9;
        --text-main: #1a1a24;
        --text-sec: #5c527a;
        --card-bg: #ffffff;
        --card-border: #ff33cc;
        --neon-glow: rgba(255, 51, 204, 0.25);
        --input-bg: #f9f9fc;
        --input-border: #e2d9f3;
        --btn-grad: linear-gradient(90deg, #ff007f, #8a2be2);
        --item-bg: #ffffff;
    }
    """

# Iniezione dello stile
st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=Space+Grotesk:wght@500;700&display=swap');
    
    {css_vars}

    /* Reset Sfondo App */
    .stApp {{ background-color: var(--bg-app) !important; color: var(--text-main) !important; font-family: 'Plus Jakarta Sans', sans-serif !important; transition: background 0.4s ease; }}
    
    /* Top Bar & Titoli */
    h1, h2, h3, p {{ color: var(--text-main) !important; }}
    .title-glow {{ font-family: 'Space Grotesk', sans-serif; font-weight: 800; font-size: 2.2rem; background: var(--btn-grad); -webkit-background-clip: text; -webkit-text-fill-color: transparent; margin-bottom: 0; }}
    
    /* Navbar Decorativa (Pillole Mockup) */
    .nav-pill-container {{ display: flex; justify-content: center; gap: 15px; margin-bottom: 30px; }}
    .nav-pill {{ background-color: var(--card-bg); border: 2px solid var(--card-border); border-radius: 30px; padding: 10px 24px; font-weight: 700; font-size: 0.9rem; color: var(--text-main); box-shadow: 0 0 15px var(--neon-glow); letter-spacing: 1px; }}

    /* STILE DEI 3 PANNELLI PRINCIPALI (Bordi Neon) */
    [data-testid="stVerticalBlockBorderWrapper"] {{
        background-color: var(--card-bg) !important;
        border: 2px solid var(--card-border) !important;
        border-radius: 20px !important;
        padding: 15px !important;
        box-shadow: 0 0 25px var(--neon-glow) !important;
        transition: all 0.3s ease;
    }}
    
    /* Input, Select, Uploader */
    .stTextInput input, div[data-baseweb="select"] {{ background-color: var(--input-bg) !important; border: 1px solid var(--input-border) !important; color: var(--text-main) !important; border-radius: 12px !important; }}
    div[data-testid="stFileUploaderDropzone"] {{ background-color: var(--input-bg) !important; border: 2px dashed var(--card-border) !important; border-radius: 16px !important; padding: 20px !important; }}
    
    /* Pulsante Primario */
    div.stButton > button[kind="primary"] {{
        background: var(--btn-grad) !important; color: white !important; font-weight: 800 !important; border-radius: 12px !important; border: none !important; width: 100%; padding: 12px !important; box-shadow: 0 4px 15px var(--neon-glow) !important;
    }}

    /* Pulsante Elimina (Piccolo e scuro) */
    div.stButton > button[kind="secondary"] {{ background-color: #2b1a4a !important; color: white !important; border: none !important; border-radius: 8px !important; font-size: 0.8rem !important; padding: 4px 12px !important; }}
    
    /* Griglia Elementi (File Cards) */
    .file-grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(110px, 1fr)); gap: 15px; margin-top: 15px; }}
    .file-card {{
        background-color: var(--item-bg); border: 1px solid var(--input-border); border-radius: 12px; padding: 15px 10px; text-align: center; text-decoration: none; color: var(--text-main); display: flex; flex-direction: column; align-items: center; gap: 8px; box-shadow: 0 4px 10px rgba(0,0,0,0.05); transition: transform 0.2s;
    }}
    .file-card:hover {{ transform: translateY(-3px); border-color: var(--card-border); box-shadow: 0 6px 15px var(--neon-glow); }}
    .file-icon {{ font-size: 1.8rem; color: #ff007f; }}
    .file-title {{ font-size: 0.85rem; font-weight: 600; line-height: 1.2; word-break: break-word; }}
    
    /* Nascondi il bordo nativo dei blocchi interni se esistono */
    [data-testid="stVerticalBlockBorderWrapper"] [data-testid="stVerticalBlockBorderWrapper"] {{ border: none !important; box-shadow: none !important; padding: 0 !important; }}
    </style>
""", unsafe_allow_html=True)

# ==========================================
# 3. HEADER & TOP BAR
# ==========================================
col_logo, col_titolo, col_toggle = st.columns([1, 6, 2])
with col_logo:
    st.image("https://raw.githubusercontent.com/sofi-sofi-sofi/archivio-appunti/main/logo_matora.png", width=70)
with col_titolo:
    st.markdown('<p class="title-glow">MATORA AI</p><p style="margin:0; font-size:0.9rem; font-weight:500;">L\'ecosistema intelligente per i tuoi appunti universitari</p>', unsafe_allow_html=True)
with col_toggle:
    st.write("")
    # Il Toggle ricarica la pagina e applica il tema scuro o chiaro
    if st.toggle("🌙 Tema Scuro", value=st.session_state.tema_scuro):
        st.session_state.tema_scuro = True
    else:
        st.session_state.tema_scuro = False

# Navbar Decorativa centrale (come da Mockup)
st.markdown("""
<div class="nav-pill-container">
    <div class="nav-pill">📥 INVIA APPUNTI</div>
    <div class="nav-pill">🔍 CERCA NELL'ARCHIVIO</div>
    <div class="nav-pill">🗑️ MANUTENZIONE</div>
</div>
""", unsafe_allow_html=True)

st.warning("⚠️ Scadenza Token AI: 26/05/2027", icon="⏳")

# ==========================================
# RECUPERO DATI GITHUB
# ==========================================
materie_rilevate = []
try:
    for folder in ["risultati", "appunti"]:
        try:
            for obj in repo.get_contents(folder, ref="main"):
                if obj.type == "dir" and obj.name not in materie_rilevate:
                    materie_rilevate.append(obj.name)
        except: pass
except: pass
materie_rilevate.sort()


# ==========================================
# 4. DASHBOARD A 3 COLONNE (Il cuore del Mockup)
# ==========================================
# Proporzioni per replicare l'immagine: Input(più stretto), Centro(Largo), Destra(Medio)
col_invia, col_cerca, col_gestisci = st.columns([1.2, 1.8, 1.2], gap="large")

# ----------------- PANNELLO 1: INVIA -----------------
with col_invia:
    with st.container(border=True):
        st.markdown("### Invia Appunti")
        
        opzioni = ["-- Seleziona --", "➕ Nuova Materia..."] + materie_rilevate
        scelta = st.selectbox("Su quale materia stai lavorando?", opzioni)
        
        materia_selezionata = ""
        if scelta == "➕ Nuova Materia...":
            materia_selezionata = st.text_input("Nome nuova materia:")
        elif scelta != "-- Seleziona --":
            materia_selezionata = scelta

        st.markdown("#### PDF Upload")
        file_caricato = st.file_uploader("Trascina o seleziona il PDF", type=["pdf"])
        nome_pers = st.text_input("Nome file (opzionale):")

        if file_caricato and materia_selezionata:
            if st.button("🚀 AVVIA ELABORAZIONE INTELIGENTE", type="primary"):
                with st.spinner("Elaborazione in corso..."):
                    nome_base = nome_pers.strip().replace(" ", "_") if nome_pers else os.path.splitext(file_caricato.name)[0]
                    try:
                        # Estrazione Immagini PDF
                        pdf_bytes = file_caricato.read()
                        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
                        immagini = [base64.b64encode(doc.load_page(i).get_pixmap(matrix=fitz.Matrix(2,2)).tobytes("png")).decode('utf-8') for i in range(len(doc))]
                        
                        # Chiamata AI Azure
                        client = ChatCompletionsClient(endpoint="https://models.inference.ai.azure.com", credential=AzureKeyCredential(GITHUB_TOKEN))
                        prompt = "Analizza questo appunto iPad. Crea: 1. Riassunto discorsivo. 2. Schema puntato. 3. 3 Domande a scelta multipla. 4. Parole chiave."
                        
                        contenuto = [{"type": "text", "text": prompt}] + [{"type": "image_url", "image_url": {"url": f"data:image/png;base64,{img}"}} for img in immagini]
                        response = client.complete(
                            messages=[SystemMessage(content="Sei un assistente universitario esperto."), UserMessage(content=contenuto)],
                            model="gpt-4o-mini", max_tokens=2500
                        )
                        risultato = response.choices[0].message.content

                        # Salvataggio Github
                        try: repo.create_file(f"appunti/{materia_selezionata}/{nome_base}.pdf", "Nuovo PDF", pdf_bytes, branch="main")
                        except: pass
                        
                        path_md = f"risultati/{materia_selezionata}/{nome_base}.md"
                        try:
                            contents = repo.get_contents(path_md, ref="main")
                            repo.update_file(contents.path, "Aggiornato MD", risultato, contents.sha, branch="main")
                        except:
                            repo.create_file(path_md, "Creato MD", risultato, branch="main")
                        
                        st.success("Completato!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Errore: {e}")

# ----------------- PANNELLO 2: CERCA (Griglia) -----------------
with col_cerca:
    with st.container(border=True):
        st.markdown("### Cerca nell'Archivio")
        query = st.text_input("🔍 Cerca nell'Archivio... (#Tag o Materia)", label_visibility="collapsed").strip().lower()
        
        # Recupero file per la griglia
        tutti_i_file = []
        try:
            for mat in materie_rilevate:
                for f in repo.get_contents(f"risultati/{mat}", ref="main"):
                    if f.name.endswith(".md"):
                        tutti_i_file.append({"nome": f.name.replace(".md", ""), "url": f.html_url})
        except: pass
        
        # Filtro
        file_filtrati = [f for f in tutti_i_file if query in f["nome"].lower()] if query else tutti_i_file
        
        # Costruzione Griglia HTML
        if file_filtrati:
            grid_html = '<div class="file-grid">'
            for f in file_filtrati:
                # Titolo pulito (es: rimuove underscore)
                titolo_pulito = f["nome"].replace("_", " ").title()
                grid_html += f'''
                <a href="{f["url"]}" target="_blank" class="file-card">
                    <div class="file-icon">📄</div>
                    <div class="file-title">{titolo_pulito}</div>
                </a>
                '''
            grid_html += '</div>'
            st.markdown(grid_html, unsafe_allow_html=True)
        else:
            st.info("Nessun appunto trovato.")

# ----------------- PANNELLO 3: MANUTENZIONE -----------------
with col_gestisci:
    with st.container(border=True):
        st.markdown("### Manutenzione")
        st.markdown("Gestisci Archivio")
        
        materia_del = st.selectbox("Seleziona Materia:", materie_rilevate if materie_rilevate else ["Nessuna"])
        if materia_del != "Nessuna":
            try:
                files_pdf = repo.get_contents(f"appunti/{materia_del}", ref="main")
            except: files_pdf = []
            try:
                files_md = repo.get_contents(f"risultati/{materia_del}", ref="main")
            except: files_md = []
            
            tutti_files_del = files_pdf + files_md
            
            if not tutti_files_del:
                st.write("Cartella vuota.")
            else:
                for file_gh in tutti_files_del:
                    # Riga singola per ogni file: Nome | Pulsante
                    c1, c2 = st.columns([7, 3])
                    with c1:
                        icona = "📄" if file_gh.name.endswith(".pdf") else "📝"
                        st.markdown(f"<div style='font-size:0.85rem; font-weight:600; padding-top:5px;'>{icona} {file_gh.name}</div>", unsafe_allow_html=True)
                    with c2:
                        if st.button("Elimina", key=f"del_{file_gh.path}"):
                            try:
                                repo.delete_file(file_gh.path, "Eliminato da App", file_gh.sha, branch="main")
                                st.rerun()
                            except Exception as e:
                                st.error("Errore")
