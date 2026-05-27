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

# 2. CSS Avanzato per sovrascrivere l'interfaccia nativa di Streamlit
st.markdown("""
    <style>
    /* Sfondo Nero Assoluto e font pulito */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');
    
    .stApp {
        background-color: #000000 !important;
        color: #ffffff !important;
        font-family: 'Inter', sans-serif !important;
    }
    
    /* Disattiva i sotto-testi nativi grigi di Streamlit che si vedono male */
    .stWidget label p, .stMarkdown p, label, .stFileUploader label, [data-testid="stWidgetLabel"] {
        color: #ffffff !important;
        font-weight: 600 !important;
        font-size: 1rem !important;
    }
    
    /* Titoli */
    h1 {
        color: #ffffff !important;
        font-weight: 800 !important;
        letter-spacing: -0.05em;
    }
    h2, h3, h4 {
        color: #b3a4ff !important;
        font-weight: 700 !important;
    }
    
    /* MENU A TENDINA (Selectbox), INPUT DI TESTO E FILE UPLOADER */
    /* Sovrascrive il contenitore nativo per farlo diventare nero con bordo viola */
    div[data-baseweb="select"], .stTextInput>div>div>input, div[data-testid="stFileUploaderDropzone"] {
        background-color: #0f0a21 !important;
        border: 2px solid #321b63 !important;
        border-radius: 12px !important;
        color: #ffffff !important;
        transition: all 0.25s ease-in-out;
    }
    
    /* Forza il testo dentro i menu a tendina e gli input a essere bianco puro */
    div[data-baseweb="select"] *, .stTextInput input {
        color: #ffffff !important;
        font-weight: 500 !important;
    }
    
    /* Effetto Focus quando si tocca un elemento dall'iPad */
    div[data-baseweb="select"]:focus-within, .stTextInput>div>div>input:focus, div[data-testid="stFileUploaderDropzone"]:hover {
        border-color: #bf40bf !important;
        box-shadow: 0 0 15px rgba(191, 64, 191, 0.25) !important;
    }
    
    /* Fix per i testi dentro l'uploader dei file */
    div[data-testid="stFileUploaderDropzone"] [data-testid="stMarkdownContainer"] p {
        color: #e3d9ff !important;
    }
    
    /* BARRA DEI TAB */
    .stTabs [data-baseweb="tab-list"] {
        background-color: #0d081c !important;
        border: 1px solid #1f123a !important;
        border-radius: 14px;
        padding: 6px;
    }
    .stTabs [data-baseweb="tab"] {
        color: #8f85b3 !important;
        font-weight: 600;
        border-radius: 10px;
        padding: 12px 24px;
        background-color: transparent !important;
        border: none !important;
    }
    .stTabs [aria-selected="true"] {
        background-color: #5211a8 !important;
        color: #ffffff !important;
        font-weight: 700 !important;
        box-shadow: 0 4px 20px rgba(82, 17, 168, 0.4);
    }
    
    /* PULSANTI (Bottoni di azione) */
    div.stButton > button:first-child {
        background: linear-gradient(135deg, #7916c2 0%, #3b0666 100%) !important;
        color: #ffffff !important;
        border: 1px solid #9933ff !important;
        padding: 14px 32px !important;
        font-weight: 700 !important;
        border-radius: 12px !important;
        box-shadow: 0 4px 15px rgba(121, 22, 194, 0.3) !important;
        width: 100%;
        transition: all 0.2s ease;
    }
    div.stButton > button:first-child:hover {
        background: linear-gradient(135deg, #9422eb 0%, #4f0b85 100%) !important;
        border-color: #bd6eff !important;
        box-shadow: 0 6px 25px rgba(148, 34, 235, 0.5) !important;
    }
    
    /* CONTENITORI ARCHIVIO (Expander) */
    .streamlit-expanderHeader {
        background-color: #0c081f !important;
        border: 2px solid #231545 !important;
        border-radius: 12px !important;
        color: #ffffff !important;
        font-size: 1.1rem !important;
    }
    .streamlit-expanderContent {
        background-color: #05030d !important;
        border: 2px solid #231545 !important;
        border-top: none !important;
        border-radius: 0 0 12px 12px !important;
        padding: 20px !important;
    }
    
    /* Link intelligenti */
    a {
        color: #b97eff !important;
        text-decoration: none;
        font-weight: 600;
    }
    a:hover {
        color: #ffffff !important;
        text-decoration: underline;
    }
    
    /* Banner Scadenza */
    .stAlert {
        background-color: #1a0813 !important;
        border: 1px solid #59163b !important;
        border-radius: 12px;
    }
    .stAlert p {
        color: #ff99d6 !important;
    }
    </style>
""", unsafe_allow_html=True)

# ==================== CONFIGURAZIONE CREDENZIALI ====================
GITHUB_TOKEN = st.secrets["GITHUB_TOKEN"]
NOME_REPOSITORY = "sofi-sofi-sofi/archivio-appunti"
# ====================================================================

g = Github(GITHUB_TOKEN)
repo = g.get_repo(NOME_REPOSITORY)

# Banner Scadenza Token
st.warning("⚠️ **Scadenza Token AI:** Il sistema scadrà il **26/05/2027**.")

# Header di Classe (Logo e Titolo affiancati)
col_logo, col_titolo = st.columns([1, 7])
with col_logo:
    if os.path.exists("logo_matora.png"):
        st.image("logo_matora.png", width=95)
    else:
        st.write("🔮") 
with col_titolo:
    st.markdown("<h1 style='margin-top: 5px; margin-bottom: 0px;'>Matora AI</h1>", unsafe_allow_html=True)
    st.markdown("<p style='color: #8f85b3; margin-top: 0px;'>L'ecosistema intelligente per i tuoi appunti universitari</p>", unsafe_allow_html=True)

st.write("")

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
    materie_rilevate = []
else:
    materie_rilevate.sort()

# Navigazione principale a Tab
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
    query_ricerca = st.text_input("Cerca per titolo o #ParolaChiave (es: #Elettronica):", "").strip().lower()
    
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
