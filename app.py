import streamlit as st
import os
import base64
from azure.ai.inference import ChatCompletionsClient
from azure.ai.inference.models import SystemMessage, UserMessage
from azure.core.credentials import AzureKeyCredential
from github import Github
import fitz  # PyMuPDF

# Configurazione del titolo della pagina web
st.set_page_config(page_title="Matora 1.0 - Caricamento Appunti", page_icon="📄")

# Banner Arancione di avviso scadenza token visibile anche nell'app di caricamento
st.warning("""
⚠️ **Attenzione: Scadenza Token AI** Il token di autenticazione GitHub Models scadrà il **26/05/2027**. Dopo questa data l'applicazione smetterà di funzionare finché non verrà aggiornato il codice con un nuovo Token Classic (ghp_).
""")

st.title("🧠 Matora AI - Hub di Elaborazione Appunti")
st.write("Carica il tuo PDF dall'iPad, seleziona la materia e genera i riassunti in automatico.")

# ==================== CONFIGURAZIONE CREDENZIALI ====================
# Invece di scrivere il token in chiaro, lo leggiamo dai Secrets sicuri di Streamlit
GITHUB_TOKEN = st.secrets["GITHUB_TOKEN"]

NOME_REPOSITORY = "sofi-sofi-sofi/archivio-appunti"
# ====================================================================

# --- GESTIONE MATERIE DINAMICA ---
materie_predefinite = ["Matematica", "Fisica", "Chimica", "Informatica", "Biologia"]

# Creiamo il menu a tendina con l'opzione per aggiungere una nuova materia
opzioni = ["-- Seleziona una materia --", "➕ Aggiungi Nuova Materia..."] + materie_predefinite
scelta = st.selectbox("📚 Su quale materia stai lavorando?", opzioni)

if scelta == "➕ Aggiungi Nuova Materia...":
    materia_selezionata = st.text_input("✍️ Scrivi il nome della nuova materia (es. Storia, Economia):").strip()
elif scelta == "-- Seleziona una materia --":
    materia_selezionata = ""
else:
    materia_selezionata = scelta
# ----------------------------------

# Campo per caricare il file PDF (funziona perfettamente da iPad/File)
file_caricato = st.file_uploader("📂 Scegli il file PDF dei tuoi appunti", type=["pdf"])

# Nome personalizzato del file (facoltativo, prende il nome originale altrimenti)
nome_personalizzato = st.text_input("✍️ Dai un nome al file (es: lezione_1)", "")

# Controllo validità: l'utente deve aver caricato un file e scelto/scritto una materia valida
if file_caricato is not None and materia_selezionata != "":
    
    # Pulizia del nome del file
    if nome_personalizzato.strip() == "":
        nome_base = os.path.splitext(file_caricato.name)[0]
    else:
        nome_base = nome_personalizzato.strip().replace(" ", "_")
        
    if st.button("🚀 Avvia Elaborazione AI e Salva", type="primary"):
        with st.spinner("⏳ Elaborazione in corso... Lettura PDF e analisi AI..."):
            try:
                # Leggiamo i byte del PDF caricato dal browser
                pdf_bytes = file_caricato.read()
                doc = fitz.open(stream=pdf_bytes, filetype="pdf")
                immagini_pagine = []

                # Conversione pagine in immagini per la Vision dell'AI
                for numero_pagina in range(len(doc)):
                    pagina = doc.load_page(numero_pagina)
                    pix = pagina.get_pixmap(matrix=fitz.Matrix(2, 2))
                    img_bytes = pix.tobytes("png")
                    base64_image = base64.b64encode(img_bytes).decode('utf-8')
                    immagini_pagine.append(base64_image)

                # Inizializzazione AI
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
                4. **PAROLE CHIAVE**: Estrai una lista di parole chiave (es: #Termodinamica, #Analisi, #Derivate) separate da virgola, utili per indicizzare questo appunto nel mio motore di ricerca.
                """

                contenuto_utente = [{"type": "text", "text": prompt}]
                for img_b64 in immagini_pagine:
                    contenuto_utente.append({
                        "type": "image_url",
                        "image_url": {"url": f"data:image/png;base64,{img_b64}"}
                    })

                # Chiamata a GPT-4o-mini
                response = client.complete(
                    messages=[
                        SystemMessage(content="Sei un assistente universitario che organizza e indicizza appunti."),
                        UserMessage(content=contenuto_utente)
                    ],
                    model="gpt-4o-mini",
                    max_tokens=2500
                )
                risultato_ai = response.choices[0].message.content

                # Connessione a GitHub
                g = Github(GITHUB_TOKEN)
                repo = g.get_repo(NOME_REPOSITORY)

                # Definizione dei percorsi precisi basati sulla materia scelta o scritta dall'utente
                path_appunto_pdf = f"appunti/{materia_selezionata}/{nome_base}.pdf"
                path_risultato_md = f"risultati/{materia_selezionata}/{nome_base}.md"

                # 1. Carica il PDF originale nella cartella appunti/Materia/
                try:
                    repo.create_file(path_appunto_pdf, f"Caricato PDF originale: {nome_base}", pdf_bytes, branch="main")
                except Exception:
                    st.info(f"Il PDF '{nome_base}.pdf' esiste già su GitHub, non è stato sovrascritto.")

                # 2. Carica il file Markdown nella cartella risultati/Materia/
                try:
                    contents = repo.get_contents(path_risultato_md, ref="main")
                    repo.update_file(contents.path, f"Aggiornato risultato AI: {nome_base}", risultato_ai, contents.sha, branch="main")
                    st.success(f"✅ Aggiornato con successo in: {path_risultato_md}")
                except Exception:
                    repo.create_file(path_risultato_md, f"Creato risultato AI: {nome_base}", risultato_ai, branch="main")
                    st.success(f"✅ Salvato con successo in: {path_risultato_md}")

                st.balloons()

            except Exception as e:
                st.error(f"❌ Si è verificato un errore: {e}")
else:
    if scelta == "-- Seleziona una materia --" or materia_selezionata == "":
        st.info("💡 Per procedere, seleziona una materia esistente o inseriscine una nuova dal menu in alto.")
