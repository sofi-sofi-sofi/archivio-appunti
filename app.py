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

# 2. Nuova interfaccia Dark Mode coordinata al logo (Sfondo scuro, Fucsia/Viola Elettrico, Scritte Chiare)
st.markdown("""
    <style>
    /* Sfondo dell'applicazione */
    .stApp {
        background-color: #0b071a !important;
        color: #f1edff !important;
    }
    
    /* Titoli principali */
    h1 {
        color: #e25eff !important;
        font-family: 'Inter', sans-serif;
        font-weight: 800;
        text-shadow: 0 0 15px rgba(226, 94, 255, 0.3);
    }
    h2, h3, h4 {
        color: #d1c9ff !important;
    }
    
    /* Contenitore dei Tab */
    .stTabs [data-baseweb="tab-list"] {
        background-color: #160f33 !important;
        border-radius: 12px;
        padding: 6px;
        border-bottom: none;
    }
    
    /* Singolo Tab (Non selezionato) */
    .stTabs [data-baseweb="tab"] {
        color: #a499e0 !important;
        font-weight: 600;
        border-radius: 8px;
        padding: 10px 20px;
        background-color: transparent !important;
        transition: all 0.2s ease;
    }
    
    /* Tab Selezionato attivo */
    .stTabs [aria-selected="true"] {
        background-color: #e25eff !important;
        color: #0b071a !important;
        font-weight: 700 !important;
        box-shadow: 0 0 15px rgba(226, 94, 255, 0.5);
    }
    
    /* Pulsanti (Carica, Elimina, ecc.) */
    div.stButton > button:first-child {
        background: linear-gradient(135deg, #e25eff 0%, #891aff 100%) !important;
        color: #ffffff !important;
        border: none !important;
        padding: 12px 28px !important;
        font-weight: 700 !important;
        font-size: 1rem !important;
        border-radius: 10px !important;
        box-shadow: 0 4px 15px rgba(137, 26, 255, 0.4) !important;
        transition: all 0.3s ease !important;
        width: auto;
    }
    div.stButton > button:first-child:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 6px 22px rgba(226, 94, 255, 0.6) !important;
    }
    
    /* Campi di testo, Selettori e File Uploader */
    .stTextInput>div>div>input, .stSelectbox>div>div, .stFileUploader>div>div {
        background-color: #1b1340 !important;
        border: 2px solid #362973 !important;
        color: #ffffff !important;
        border-radius: 10px !important;
        font-size: 1rem !important;
    }
    
    /* Testi all'interno dei menu a tendina e input per massima leggibilità */
    .stTextInput input, .stSelectbox div[data-baseweb="select"] {
        color: #ffffff !important;
    }
    
    /* Quando selezioni un campo (Focus) */
    .stTextInput>div>div>input:focus, .stSelectbox>div>div:focus-within {
        border-color: #e25eff !important;
        box-shadow: 0 0 12px rgba(226, 94, 255, 0.4) !important;
    }
    
    /* Scatole dei Risultati (Expander) */
    .streamlit-expanderHeader {
        background-color: #160f33 !important;
        border: 1px solid #2d2066 !important;
        border-radius: 10px !important;
        color: #f1edff !important;
    }
    .streamlit-expanderContent {
        background-color: #0e0924 !important;
        border-left: 1px solid #2d2066 !important;
        border-right: 1px solid #2d2066 !important;
        border-bottom: 1px solid #2d2066 !important;
        border-radius: 0 0 10px 10px !important;
    }

    /* Link per aprire i file */
    a {
        color: #e25eff !important;
        font-weight: 600;
        text-decoration: none;
    }
    a:hover {
        text-decoration: underline !important;
    }
    
    /* Banner di avviso in alto */
    .stAlert {
        background-color: #260f1c !important;
        border: 1px solid #e25eff !important;
        color: #ffd6fa !important;
        border-radius: 10px;
    }
    </style>
""", unsafe_allow_html=True)

# ==================== CONFIGURAZIONE CREDENZIALI ====================
GITHUB_TOKEN = st.secrets["GITHUB_TOKEN"]
NOME_REPOSITORY = "sofi-sofi-sofi/archivio-appunti"
# ====================================================================

# Connessione globale a GitHub
g = Github(GITHUB_TOKEN)
repo = g.get_repo(NOME_REPOSITORY)

# Banner Scadenza Token coordinato cromaticamente
st.warning("⚠️ **Attenzione: Scadenza Token AI** Il sistema scadrà il **26/05/2027**.")

# Header principale affiancando il tuo Logo e il Titolo Grande
col_logo, col_titolo = st.columns([1, 6])
with col_logo:
    if os.path.exists("logo_matora.png"):
        st.image("logo_matora.png", width=110)
    else:
        st.write("🔮") 
with col_titolo:
    st.markdown("<h1 style='margin-top: 10px;'>Matora AI</h1>", unsafe_allow_html=True)
    st.markdown("<p style='color: #a499e0;'>L'ecosistema intelligente per i tuoi appunti universitari dall'iPad</p>", unsafe_allow_html=True)

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

# Creazione dei tre Tab coordinati
tab_carica, tab_archivio, tab_gestisci = st.tabs([
    "📥 Carica Nuovo Appunto", 
    "🔍 Cerca & Leggi Risultati", 
    "🗑️ Elimina File"
])

# ====================================================================
# TAB 1: CARICAMENTO & ELABORAZIONE
# ====================================================================
with tab_carica:
    st.markdown("### 📂 Invia un nuovo documento")
    
    opzioni = ["-- Seleziona una materia --", "➕ Aggiungi Nuova Materia..."] + materie_rilevate
    scelta = st.selectbox("📚 Su quale materia stai lavorando?", opzioni, key="materia_carica")

    if scelta == "➕ Aggiungi Nuova Materia...":
        materia_selezionata = st.text_input("✍️ Scrivi il nome della nuova materia (es. Italiano):").strip()
    elif scelta == "-- Seleziona una materia --":
        materia_selezionata = ""
    else:
        materia_selezionata = scelta

    file_caricato = st.file_uploader("📎 Trascina o seleziona il PDF dei tuoi appunti", type=["pdf"])
    nome_personalizzato = st.text_input("✍️ Dai un nome al file (es: lezione_1)", "")

    if file_caricato is not None and materia_selezionata != "":
        if nome_personalizzato.strip() == "":
            nome_base = os.path.splitext(file_caricato.name)[0]
        else:
            nome_base = nome_personalizzato.strip().replace(" ", "_")
            
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
                    path_risultato_md = f"results/{materia_selezionata}/{nome_base}.md"

                    try:
                        repo.create_file(path_appunto_pdf, f"Caricato PDF: {nome_base}", pdf_bytes, branch="main")
                    except Exception:
                        st.info(f"Il PDF '{nome_base}.pdf' esiste già.")

                    try:
                        contents = repo.get_contents(path_risultato_md, ref="main")
                        repo.update_file(contents.path, f"Aggiornato: {nome_base}", risultato_ai, contents.sha, branch="main")
                        st.success("✅ Aggiornato con successo su GitHub!")
                    except Exception:
                        repo.create_file(path_risultato_md, f"Creato: {nome_base}", risultato_ai, branch="main")
                        st.success("✅ Creato e salvato con successo su GitHub!")

                    st.balloons()
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ Errore durante l'elaborazione: {e}")

# ====================================================================
# TAB 2: RICERCA AVANZATA & LETTURA RISULTATI
# ====================================================================
with tab_archivio:
    st.markdown("### 🔍 Motore di ricerca intelligente")
    query_ricerca = st.text_input("Filtra istantaneamente per titolo o #ParolaChiave:", "").strip().lower()
    
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
            
            st.markdown(f"🧬 *Trovati {len(risultati_filtrati)} elementi corrispondenti*")
            
            materie_visibili = set([f["materia"] for f in risultati_filtrati])
            materie_ordinate = sorted(list(materie_visibili))
            
            for m in materie_ordinate:
                with st.expander(f"📚 {m.upper()}", expanded=True):
                    for f in risultati_filtrati:
                        if f["materia"] == m:
                            col_t, col_b = st.columns([4, 1])
                            with col_t:
                                st.markdown(f"▪️ **{f['nome'].replace('.md','').replace('_',' ')}**")
                            with col_b:
                                st.markdown(f"[👁️ Apri Riassunto]({f['html_url']})")
                                
    except Exception:
        st.info("Nessun riassunto trovato nell'archivio cloud.")

# ====================================================================
# TAB 3: GESTIONE ED ELIMINAZIONE FILE
# ====================================================================
with tab_gestisci:
    st.markdown("### 🗑️ Manutenzione e pulizia database")
    st.write("Scegli un file per rimuoverlo in modo permanente dal cloud.")

    tipo_cartella = st.radio("Seleziona categoria:", ["Risultati AI (.md)", "PDF Originali (.pdf)"])
    cartella_target = "risultati" if tipo_cartella == "Risultati AI (.md)" else "appunti"

    try:
        materie_folder = repo.get_contents(cartella_target, ref="main")
        elenco_materie = [f.name for f in materie_folder if f.type == "dir"]
        
        if len(elenco_materie) == 0:
            st.info("Nessuna cartella materia trouvata.")
        else:
            materia_scelta = st.selectbox("Seleziona la materia da modificare:", elenco_materie, key="materia_del")
            files_in_folder = repo.get_contents(f"{cartella_target}/{materia_scelta}", ref="main")
            
            st.write("---")
            for file_gh in files_in_folder:
                col_nome, col_azione = st.columns([4, 1])
                with col_nome:
                    st.text(f"📄 {file_gh.name}")
                with col_azione:
                    if st.button("Elimina ❌", key=f"del_{file_gh.path}"):
                        try:
                            repo.delete_file(file_gh.path, f"Eliminato file: {file_gh.name}", file_gh.sha, branch="main")
                            st.success(f"File {file_gh.name} rimosso!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Errore di eliminazione: {e}")
    except Exception:
        st.info("L'archivio è vuoto.")
