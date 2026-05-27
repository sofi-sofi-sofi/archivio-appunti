import streamlit as st
import os
import base64
from azure.ai.inference import ChatCompletionsClient
from azure.ai.inference.models import SystemMessage, UserMessage
from azure.core.credentials import AzureKeyCredential
from github import Github
import fitz  # PyMuPDF

# 1. Configurazione della pagina
st.set_page_config(
    page_title="Matora AI", 
    page_icon="logo_matora.png", 
    layout="wide"
)

# 2. CSS Custom - TEMA CHIARO PREMIUM (Apple Minimal & Purple Accent)
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=Space+Grotesk:wght@500;700&display=swap');
    
    /* Sfondo Bianco / Grigio Chiarissimo e testo scuro */
    .stApp {
        background-color: #f8f9fa !important;
        color: #1a1a24 !important;
        font-family: 'Plus Jakarta Sans', sans-serif !important;
    }
    
    /* Blocco Titolo e Logo */
    .brand-container {
        display: flex;
        align-items: center;
        gap: 24px;
        padding: 20px 0;
        margin-bottom: 30px;
    }
    .logo-container {
        border-radius: 24px;
        box-shadow: 0 10px 30px rgba(138, 43, 226, 0.12);
        border: 1px solid #e2d9f3;
        background-color: #ffffff;
        padding: 4px;
    }
    
    /* Titoli Principali */
    h1 {
        font-family: 'Space Grotesk', sans-serif !important;
        color: #1a1a24 !important;
        font-weight: 700 !important;
        font-size: 2.8rem !important;
        letter-spacing: -0.04em !important;
        margin: 0 !important;
    }
    h2, h3, h4 {
        color: #4a148c !important;
        font-weight: 700 !important;
    }
    
    /* Etichette dei campi di testo e moduli (Leggibilità Massima) */
    .stWidget label p, label, [data-testid="stWidgetLabel"] p {
        font-family: 'Space Grotesk', sans-serif !important;
        color: #2e1c6a !important;
        font-weight: 600 !important;
        font-size: 1.05rem !important;
        letter-spacing: -0.01em;
        margin-bottom: 8px !important;
    }
    
    /* INTERFACCIA CAMPI DI INPUT (Fondo bianco, bordo grigio/viola) */
    div[data-baseweb="select"], .stTextInput>div>div>input, div[data-testid="stFileUploaderDropzone"] {
        background-color: #ffffff !important;
        border: 2px solid #e1dbf0 !important;
        border-radius: 16px !important;
        color: #1a1a24 !important;
        padding: 4px !important;
        transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
    }
    
    /* Testo dentro i menu a tendina e input */
    div[data-baseweb="select"] *, .stTextInput input {
        color: #1a1a24 !important;
        font-family: 'Plus Jakarta Sans', sans-serif !important;
        font-weight: 500 !important;
    }
    
    /* Effetto Focus all'inserimento */
    div[data-baseweb="select"]:focus-within, .stTextInput>div>div>input:focus {
        border-color: #8a2be2 !important;
        box-shadow: 0 0 20px rgba(138, 43, 226, 0.15) !important;
    }
    
    /* Box di upload file */
    div[data-testid="stFileUploaderDropzone"] {
        padding: 30px !important;
        border-style: dashed !important;
        background-color: #f1ecf9 !important;
        border-color: #c0b2df !important;
    }
    div[data-testid="stFileUploaderDropzone"] [data-testid="stMarkdownContainer"] p {
        color: #4c3c75 !important;
    }
    
    /* UTILITY BUTTONS (Sfumatura Viola/Fucsia del Logo) */
    div.stButton > button:first-child {
        font-family: 'Space Grotesk', sans-serif !important;
        background: linear-gradient(135deg, #9c27b0 0%, #673ab7 100%) !important;
        color: #ffffff !important;
        border: none !important;
        padding: 16px 32px !important;
        font-weight: 700 !important;
        font-size: 1.1rem !important;
        border-radius: 16px !important;
        box-shadow: 0 6px 20px rgba(103, 58, 183, 0.25) !important;
        width: 100%;
        transition: all 0.2s ease;
        letter-spacing: 0.02em;
    }
    div.stButton > button:first-child:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 10px 25px rgba(156, 39, 176, 0.4) !important;
    }
    
    /* SELETTORE DEI TAB (Stile pulito iOS) */
    .stTabs [data-baseweb="tab-list"] {
        background-color: #ebe6f5 !important;
        border: 1px solid #dcd5eb !important;
        border-radius: 16px;
        padding: 8px;
        gap: 10px;
    }
    .stTabs [data-baseweb="tab"] {
        font-family: 'Space Grotesk', sans-serif !important;
        color: #5c527a !important;
        font-weight: 600;
        border-radius: 12px;
        padding: 12px 26px;
        background-color: transparent !important;
        border: none !important;
    }
    .stTabs [aria-selected="true"] {
        background-color: #ffffff !important;
        color: #4a148c !important;
        border: 1px solid #c0b2df !important;
        font-weight: 700 !important;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
    }
    
    /* CONTENITORI RISULTATI (Expander) */
    .streamlit-expanderHeader {
        background-color: #ffffff !important;
        border: 1px solid #e1dbf0 !important;
        border-radius: 14px !important;
        color: #1a1a24 !important;
        font-family: 'Space Grotesk', sans-serif !important;
        box-shadow: 0 2px 8px rgba(0,0,0,0.02);
    }
    .streamlit-expanderContent {
        background-color: #ffffff !important;
        border: 1px solid #e1dbf0 !important;
        border-top: none !important;
        border-radius: 0 0 14px 14px !important;
    }
    
    /* Link */
    a {
        color: #7b1fa2 !important;
        font-weight: 600;
    }
    
    /* Banner Scadenza */
    .stAlert {
        background-color: #fff3cd !important;
        border: 1px solid #ffeeba !important;
        border-radius: 14px;
    }
    .stAlert p {
        color: #856404 !important;
        font-size: 0.95rem !important;
    }
    </style>
""", unsafe_allow_html=True)

# ==================== CONFIGURAZIONE CREDENZIALI ====================
GITHUB_TOKEN = st.secrets["GITHUB_TOKEN"]
NOME_REPOSITORY = "sofi-sofi-sofi/archivio-appunti"
# ====================================================================

g = Github(GITHUB_TOKEN)
repo = g.get_repo(NOME_REPOSITORY)

# Banner Scadenza
st.warning("⚠️ **Scadenza Token AI:** Il sistema scadrà il **26/05/2027**.")

# Layout Header Integrato Light Mode
st.markdown("""
<div class="brand-container">
    <div class="logo-container">
        <img src="https://raw.githubusercontent.com/sofi-sofi-sofi/archivio-appunti/main/logo_matora.png" width="130" style="display:block; border-radius:24px;">
    </div>
    <div>
        <h1>Matora AI</h1>
        <p style="color: #5c527a; margin: 4px 0 0 0; font-size: 1.1rem; font-weight: 500;">L'ecosistema intelligente per i tuoi appunti universitari</p>
    </div>
</div>
""", unsafe_allow_html=True)

# --- RECUPERO MATERIE DA GITHUB ---
materie_rilevate = []
try:
    for cartella_radice in ["risultati", "appunti"]:
        try:
            oggetti = repo.get_contents(cartella_radice, ref="main")
            for obj in oggetti:
                if obj.type == "dir" and obj.name not in materie_rilevate:
                    materie_rilevate.append(obj.name)
        except Exception:
            pass
except Exception:
    pass

if len(materie_rilevate) == 0:
    materie_rilevate = ["Matematica", "Fisica", "Chimica", "Informatica", "Biologia"]
else:
    materie_rilevate.sort()

# Navigazione Tab
tab_carica, tab_archivio, tab_gestisci = st.tabs([
    "📥 Carica Nuovo Appunto", 
    "🔍 Cerca & Leggi Risultati", 
    "🗑️ Elimina File"
])

# ====================================================================
# TAB 1: CARICAMENTO & ELABORAZIONE
# ====================================================================
with tab_carica:
    st.write("")
    
    opzioni = ["-- Seleziona una materia --", "➕ Aggiungi Nuova Materia..."] + materie_rilevate
    scelta = st.selectbox("Su quale materia stai lavorando?", opzioni, key="materia_carica")

    if scelta == "➕ Aggiungi Nuova Materia...":
        materia_selezionata = st.text_input("Scrivi il nome della nuova materia:").strip()
    elif scelta == "-- Seleziona una materia --":
        materia_selezionata = ""
    else:
        materia_selezionata = scelta

    file_caricato = st.file_uploader("Trascina o seleziona il PDF dei tuoi appunti", type=["pdf"])
    nome_personalizzato = st.text_input("Dai un nome al file (es: lezione_1)", "")

    if file_caricato is not None and materia_selezionata != "":
        if nome_personalizzato.strip() == "":
            nome_base = os.path.splitext(file_caricato.name)[0]
        else:
            nome_base = nome_personalizzato.strip().replace(" ", "_")
            
        st.write("")
        if st.button("🚀 Avvia Elaborazione AI e Salva", type="primary"):
            with st.spinner("⏳ Matora AI sta analizzando la tua grafia..."):
                try:
                    pdf_bytes = file_caricato.read()
                    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
                    immagini_pagine = []

                    for numero_pagina in range(len(doc)):
                        pagina = doc.load_page(numero_pagina)
                        pix = pagina.get_pixmap(matrix=fitz.Matrix(2, 2))
                        img_bytes = pix.tobytes("png")
                        base64_image = base64.b64encode(img_bytes).decode('utf-8')
                        immagini_pagine.append(base64_image)

                    client = ChatCompletionsClient(
                        endpoint="https://models.inference.ai.azure.com",
                        credential=AzureKeyCredential(GITHUB_TOKEN)
                    )

                    prompt = """
                    Analizza questo documento che contiene i miei appunti presi a mano su iPad.
                    Esegui i seguenti compiti in lingua italiana e formatta la risposta rigorosamente in formato Markdown:
                    1. **RIASSUNTO**: Fai un riassunto dettagliato ma discorsivo dei concetti principali spiegati nel testo.
                    2. **SCHEMA**: Crea uno schema puntato, gerarchico e super chiaro della lezione.
                    3. **QUIZ**: Genera 3 domande a scelta multipla basate su questo appunto (con le soluzioni indicate alla fine).
                    4. **PAROLE CHIAVE**: Estrai una lista di parole chiave separate da virgola (es: #Meccanica, #Equazioni).
                    """

                    contenuto_utente = [{"type": "text", "text": prompt}]
                    for img_b64 in immagini_pagine:
                        contenuto_utente.append({
                            "type": "image_url",
                            "image_url": {"url": f"data:image/png;base64,{img_b64}"}
                        })

                    response = client.complete(
                        messages=[
                            SystemMessage(content="Sei un assistente universitario che organizza e indicizza appunti."),
                            UserMessage(content=contenuto_utente)
                        ],
                        model="gpt-4o-mini",
                        max_tokens=2500
                    )
                    risultato_ai = response.choices[0].message.content

                    path_appunto_pdf = f"appunti/{materia_selezionata}/{nome_base}.pdf"
                    path_risultato_md = f"risultati/{materia_selezionata}/{nome_base}.md"

                    try:
                        repo.create_file(path_appunto_pdf, f"Caricato PDF: {nome_base}", pdf_bytes, branch="main")
                    except Exception:
                        pass

                    try:
                        contents = repo.get_contents(path_risultato_md, ref="main")
                        repo.update_file(contents.path, f"Aggiornato: {nome_base}", risultato_ai, contents.sha, branch="main")
                        st.success("✅ Aggiornato con successo su GitHub!")
                    except Exception:
                        repo.create_file(path_risultato_md, f"Creato: {nome_base}", risultato_ai, branch="main")
                        st.success("✅ Salvato con successo su GitHub!")

                    st.balloons()
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ Errore durante l'elaborazione: {e}")

# ====================================================================
# TAB 2: RICERCA AVANZATA & LETTURA RISULTATI
# ====================================================================
with tab_archivio:
    st.write("")
    query_ricerca = st.text_input("Cerca per titolo o #ParolaChiave (es: #Diritto):", "").strip().lower()
    
    try:
        materie_folder = repo.get_contents("risultati", ref="main")
        elenco_materie = [f.name for f in materie_folder if f.type == "dir"]
        
        tutti_i_file = []
        for mat in elenco_materie:
            files_in_mat = repo.get_contents(f"risultati/{mat}", ref="main")
            for f in files_in_mat:
                if f.name.endswith(".md"):
                    tutti_i_file.append({"nome": f.name, "materia": mat, "download_url": f.download_url, "html_url": f.html_url})
        
        if len(tutti_i_file) == 0:
            st.info("L'archivio è vuoto. Effettua il tuo primo caricamento!")
        else:
            risultati_filtrati = []
            
            with st.spinner("Scansione archivio cloud..."):
                for f_info in tutti_i_file:
                    nome_pulito = f_info["nome"].replace(".md", "").replace("_", " ").lower()
                    
                    if query_ricerca == "" or query_ricerca in nome_pulito:
                        risultati_filtrati.append(f_info)
                    else:
                        res_cont = base64.b64decode(repo.get_contents(f"risultati/{f_info['materia']}/{f_info['nome']}", ref="main").content).decode("utf-8").lower()
                        if query_ricerca in res_cont:
                            risultati_filtrati.append(f_info)
            
            st.markdown(f"✨ *Trovati {len(risultati_filtrati)} elementi corrispettivi*")
            st.write("")
            
            materie_visibili = set([f["materia"] for f in risultati_filtrati])
            materie_ordinate = sorted(list(materie_visibili))
            
            for m in materie_ordinate:
                with st.expander(f"📚 {m.upper()}", expanded=True):
                    for f in risultati_filtrati:
                        if f["materia"] == m:
                            col_t, col_b = st.columns([5, 1])
                            with col_t:
                                st.markdown(f"▪️ **{f['nome'].replace('.md','').replace('_',' ')}**")
                            with col_b:
                                st.markdown(f"[👁️ Leggi Riassunto]({f['html_url']})")
                                
    except Exception:
        st.info("Nessun riassunto trovato nell'archivio cloud.")

# ====================================================================
# TAB 3: GESTIONE ED ELIMINAZIONE FILE
# ====================================================================
with tab_gestisci:
    st.write("")
    tipo_cartella = st.radio("Seleziona categoria da ripulire:", ["Risultati AI (.md)", "PDF Originali (.pdf)"])
    cartella_target = "risultati" if tipo_cartella == "Risultati AI (.md)" else "appunti"

    try:
        materie_folder = repo.get_contents(cartella_target, ref="main")
        elenco_materie = [f.name for f in materie_folder if f.type == "dir"]
        
        if len(elenco_materie) == 0:
            st.info("Nessuna cartella materia trovata.")
        else:
            materia_scelta = st.selectbox("Seleziona la materia da modificare:", elenco_materie, key="materia_del")
            files_in_folder = repo.get_contents(f"{cartella_target}/{materia_scelta}", ref="main")
            
            st.write("---")
            for file_gh in files_in_folder:
                col_nome, col_azione = st.columns([5, 1])
                with col_nome:
                    st.markdown(f"📄 {file_gh.name}")
                with col_azione:
                    if st.button("Elimina ❌", key=f"del_{file_gh.path}"):
                        try:
                            repo.delete_file(file_gh.path, f"Eliminato file: {file_gh.name}", file_gh.sha, branch="main")
                            st.success("File rimosso!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Errore: {e}")
    except Exception:
        st.info("L'archivio è vuoto.")
