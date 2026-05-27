import streamlit as st
import os
import base64
from azure.ai.inference import ChatCompletionsClient
from azure.ai.inference.models import SystemMessage, UserMessage
from azure.core.credentials import AzureKeyCredential
from github import Github
import fitz  # PyMuPDF

# Configurazione della pagina
st.set_page_config(page_title="Matora AI - Plancia di Comando", page_icon="🧠", layout="wide")

# Banner Arancione di avviso scadenza token
st.warning("""
⚠️ **Attenzione: Scadenza Token AI** Il token scadrà il **26/05/2027**. Dopo questa data l'applicazione smetterà di funzionare finché non verrà aggiornato il codice.
""")

st.title("🧠 Matora AI - Plancia di Comando")

# ==================== CONFIGURAZIONE CREDENZIALI ====================
GITHUB_TOKEN = st.secrets["GITHUB_TOKEN"]
NOME_REPOSITORY = "sofi-sofi-sofi/archivio-appunti"
# ====================================================================

# Connessione globale a GitHub
g = Github(GITHUB_TOKEN)
repo = g.get_repo(NOME_REPOSITORY)

# --- RECUPERO MATERIE ESISTENTI DA GITHUB IN TEMPO REALE ---
materie_rilevate = []
try:
    # Controlliamo sia la cartella risultati che appunti per trovare tutte le materie create
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

# Se l'archivio è ancora vuoto su GitHub, usiamo quelle predefinite come base
if len(materie_rilevate) == 0:
    materie_rilevate = []
else:
    # Ordiniamo le materie alfabeticamente
    materie_rilevate.sort()
# -----------------------------------------------------------

# Creazione dei tre Tab per l'iPad
tab_carica, tab_archivio, tab_gestisci = st.tabs([
    "📥 Carica Nuovo Appunto", 
    "🔍 Cerca & Leggi Risultati", 
    "🗑️ Elimina File"
])

# ====================================================================
# TAB 1: CARICAMENTO & ELABORAZIONE
# ====================================================================
with tab_carica:
    st.header("Carica un nuovo PDF")
    
    # Il menu a tendina ora mostra dinamicamente anche "Italiano" o le altre materie vecchie
    opzioni = ["-- Seleziona una materia --", "➕ Aggiungi Nuova Materia..."] + materie_rilevate
    scelta = st.selectbox("📚 Su quale materia stai lavorando?", opzioni, key="materia_carica")

    if scelta == "➕ Aggiungi Nuova Materia...":
        materia_selezionata = st.text_input("✍️ Scrivi il nome della nuova materia (es. Storia, Economia):").strip()
    elif scelta == "-- Seleziona una materia --":
        materia_selezionata = ""
    else:
        materia_selezionata = scelta

    file_caricato = st.file_uploader("📂 Scegli il file PDF dei tuoi appunti", type=["pdf"])
    nome_personalizzato = st.text_input("✍️ Dai un nome al file (es: lezione_1)", "")

    if file_caricato is not None and materia_selezionata != "":
        if nome_personalizzato.strip() == "":
            nome_base = os.path.splitext(file_caricato.name)[0]
        else:
            nome_base = nome_personalizzato.strip().replace(" ", "_")
            
        if st.button("🚀 Avvia Elaborazione AI e Salva", type="primary"):
            with st.spinner("⏳ Elaborazione in corso... Lettura PDF e analisi AI..."):
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
                        st.info(f"Il PDF '{nome_base}.pdf' esiste già.")

                    try:
                        contents = repo.get_contents(path_risultato_md, ref="main")
                        repo.update_file(contents.path, f"Aggiornato: {nome_base}", risultato_ai, contents.sha, branch="main")
                        st.success("✅ Aggiornato con successo su GitHub!")
                    except Exception:
                        repo.create_file(path_risultato_md, f"Creato: {nome_base}", risultato_ai, branch="main")
                        st.success("✅ Creato e salvato con successo su GitHub!")

                    st.balloons()
                    st.rerun() # Riavvia per aggiornare immediatamente la lista materie
                except Exception as e:
                    st.error(f"❌ Errore durante l'elaborazione: {e}")

# ====================================================================
# TAB 2: RICERCA AVANZATA & LETTURA RISULTATI
# ====================================================================
with tab_archivio:
    st.header("🔍 Cerca tra i tuoi risultati AI")
    query_ricerca = st.text_input("Filtra per titolo o #ParolaChiave (es: #Fisica):", "").strip().lower()
    
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
            st.info("L'archivio è ancora vuoto. Carica il tuo primo appunto!")
        else:
            risultati_filtrati = []
            
            with st.spinner("Ricerca in corso..."):
                for f_info in tutti_i_file:
                    nome_pulito = f_info["nome"].replace(".md", "").replace("_", " ").lower()
                    
                    if query_ricerca == "" or query_ricerca in nome_pulito:
                        risultati_filtrati.append(f_info)
                    else:
                        res_cont = base64.b64decode(repo.get_contents(f"risultati/{f_info['materia']}/{f_info['nome']}", ref="main").content).decode("utf-8").lower()
                        if query_ricerca in res_cont:
                            risultati_filtrati.append(f_info)
            
            st.write(f"✍️ Trovati {len(risultati_filtrati)} appunti")
            
            materie_visibili = set([f["materia"] for f in risultati_filtrati])
            materie_ordinate = sorted(list(materie_visibili))
            
            for m in materie_ordinate:
                with st.expander(f"📚 {m}", expanded=True):
                    for f in risultati_filtrati:
                        if f["materia"] == m:
                            col_t, col_b = st.columns([4, 1])
                            with col_t:
                                st.write(f"📄 **{f['nome'].replace('.md','').replace('_',' ')}**")
                            with col_b:
                                st.markdown(f"[👁️ Leggi su GitHub]({f['html_url']})")
                                
    except Exception:
        st.info("Nessun riassunto trovato nell'archivio cloud.")

# ====================================================================
# TAB 3: GESTIONE ED ELIMINAZIONE FILE
# ====================================================================
with tab_gestisci:
    st.header("🗑️ Elimina file dall'archivio")
    st.write("Rimuovi definitivamente i file sia dai PDF originali che dai risultati generati dall'AI.")

    tipo_cartella = st.radio("Scegli cosa vuoi controllare:", ["Risultati AI (.md)", "PDF Originali (.pdf)"])
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
                col_nome, col_azione = st.columns([4, 1])
                with col_nome:
                    st.text(f"📄 {file_gh.name}")
                with col_azione:
                    if st.button("Elimina ❌", key=f"del_{file_gh.path}"):
                        try:
                            repo.delete_file(file_gh
