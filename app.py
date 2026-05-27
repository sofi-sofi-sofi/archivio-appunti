import streamlit as st
import streamlit.components.v1 as components
import os
import base64
from azure.ai.inference import ChatCompletionsClient
from azure.ai.inference.models import SystemMessage, UserMessage
from azure.core.credentials import AzureKeyCredential
from github import Github
import fitz  # PyMuPDF

# ── SETUP ──────────────────────────────────────────────────
st.set_page_config(page_title="Matora AI", page_icon="logo_matora.png", layout="wide", initial_sidebar_state="collapsed")

if "tema_scuro" not in st.session_state:
    st.session_state.tema_scuro = False

GITHUB_TOKEN = st.secrets["GITHUB_TOKEN"]
NOME_REPOSITORY = "sofi-sofi-sofi/archivio-appunti"
g = Github(GITHUB_TOKEN)
repo = g.get_repo(NOME_REPOSITORY)

is_dark = st.session_state.tema_scuro

# ── COLORI TEMA ────────────────────────────────────────────
if is_dark:
    BG          = "#0d0d1a"
    TEXT        = "#ffffff"
    TEXT2       = "#9090b8"
    CARD        = "#12122a"
    BORDER      = "#ff007f"
    SHADOW      = "rgba(255,0,127,0.2)"
    INP_BG      = "#1a1a35"
    INP_BD      = "#2a2a55"
    INP_PH      = "#6060a0"
    ROW_BD      = "#2a2a55"
    ELIM_BG     = "#2d1b5e"
    ELIM_FG     = "#ffffff"
    PILL_BG     = "#0d001f"
    PILL_BD     = "#ff007f"
    PILL_FG     = "#ff007f"
    PILL_SH     = "rgba(255,0,127,0.4)"
    FC_BG       = "#1a1a35"
    FC_BD       = "#2a2a55"
    FC_HV       = "#ff007f"
    FC_TX       = "#ffffff"
    UPL_BG      = "#0d001f"
    UPL_BD      = "#ff007f"
    UPL_TX      = "#ff007f"
    HDR_SUB     = "#8888aa"
    CIRCUIT_C   = "rgba(255,0,127,0.18)"
    CIRCUIT_N   = "rgba(255,0,127,0.35)"
else:
    BG          = "#e8e8f5"
    TEXT        = "#111111"
    TEXT2       = "#555555"
    CARD        = "#ffffff"
    BORDER      = "#ff007f"
    SHADOW      = "rgba(0,0,0,0.07)"
    INP_BG      = "#ffffff"
    INP_BD      = "#e0e0ee"
    INP_PH      = "#aaaacc"
    ROW_BD      = "#eeeeee"
    ELIM_BG     = "#2d1b5e"
    ELIM_FG     = "#ffffff"
    PILL_BG     = "#0d001a"
    PILL_BD     = "#ff007f"
    PILL_FG     = "#ff007f"
    PILL_SH     = "rgba(255,0,127,0.35)"
    FC_BG       = "#ffffff"
    FC_BD       = "#e8e8ee"
    FC_HV       = "#ff007f"
    FC_TX       = "#111111"
    UPL_BG      = "#fff5fa"
    UPL_BD      = "#ff007f"
    UPL_TX      = "#cc0066"
    HDR_SUB     = "#666666"
    CIRCUIT_C   = "rgba(200,0,150,0.12)"
    CIRCUIT_N   = "rgba(200,0,150,0.3)"

# ── SVG CIRCUIT BOARD (stile PCB reale, angolo top-right + bottom-left) ──
CIRCUIT_SVG = f"""
<svg xmlns="http://www.w3.org/2000/svg" style="position:fixed;top:0;right:0;width:420px;height:420px;pointer-events:none;z-index:0;opacity:1;" viewBox="0 0 420 420">
  <!-- Linee orizzontali e verticali stile PCB -->
  <g stroke="{CIRCUIT_C}" stroke-width="1.5" fill="none">
    <!-- top-right traces -->
    <polyline points="420,60 340,60 340,20 280,20"/>
    <polyline points="420,100 360,100 360,40 300,40 300,20"/>
    <polyline points="420,140 380,140 380,80 320,80 320,60 280,60"/>
    <polyline points="420,180 350,180 350,120 290,120 290,80"/>
    <polyline points="420,220 370,220 370,160 310,160 310,100 260,100"/>
    <polyline points="420,60 420,0"/>
    <polyline points="380,0 380,40"/>
    <polyline points="340,0 340,20"/>
    <polyline points="300,0 300,40"/>
    <polyline points="260,0 260,100"/>
  </g>
  <!-- Nodi (pad) -->
  <g fill="{CIRCUIT_N}">
    <circle cx="340" cy="60" r="3.5"/>
    <circle cx="280" cy="20" r="3.5"/>
    <circle cx="360" cy="100" r="3.5"/>
    <circle cx="300" cy="40" r="3.5"/>
    <circle cx="380" cy="140" r="3.5"/>
    <circle cx="320" cy="80" r="3.5"/>
    <circle cx="350" cy="180" r="3.5"/>
    <circle cx="290" cy="120" r="3.5"/>
    <circle cx="370" cy="220" r="3.5"/>
    <circle cx="310" cy="160" r="3.5"/>
    <circle cx="260" cy="100" r="3.5"/>
    <circle cx="380" cy="40" r="3.5"/>
    <circle cx="300" cy="20" r="3.5"/>
  </g>
</svg>
<svg xmlns="http://www.w3.org/2000/svg" style="position:fixed;bottom:0;left:0;width:300px;height:300px;pointer-events:none;z-index:0;opacity:1;" viewBox="0 0 300 300">
  <g stroke="{CIRCUIT_C}" stroke-width="1.5" fill="none">
    <polyline points="0,240 60,240 60,280 120,280"/>
    <polyline points="0,200 40,200 40,260 100,260 100,300"/>
    <polyline points="0,160 80,160 80,220 140,220 140,280 180,280"/>
    <polyline points="0,120 50,120 50,180 110,180 110,240 160,240"/>
  </g>
  <g fill="{CIRCUIT_N}">
    <circle cx="60" cy="240" r="3"/>
    <circle cx="120" cy="280" r="3"/>
    <circle cx="40" cy="200" r="3"/>
    <circle cx="100" cy="260" r="3"/>
    <circle cx="80" cy="160" r="3"/>
    <circle cx="140" cy="220" r="3"/>
    <circle cx="50" cy="120" r="3"/>
    <circle cx="110" cy="180" r="3"/>
  </g>
</svg>
"""

# ── CSS ────────────────────────────────────────────────────
st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&display=swap');

html, body, .stApp, [data-testid="stAppViewContainer"], .main {{
    background-color: {BG} !important;
    font-family: 'Inter', sans-serif !important;
    color: {TEXT} !important;
}}
.main .block-container {{
    padding: 1.2rem 2rem 2rem 2rem !important;
    max-width: 1400px !important;
}}
h1,h2,h3,h4,h5,h6,p,span,label,li,div {{
    font-family: 'Inter', sans-serif !important;
    color: {TEXT} !important;
}}
#MainMenu, footer, header {{ visibility: hidden !important; }}
[data-testid="stToolbar"] {{ display:none !important; }}

/* TITOLO MATORA */
.matora-title {{
    font-size:2rem; font-weight:900; letter-spacing:-0.5px; line-height:1;
    background:linear-gradient(90deg,#ff007f,#9d00ff);
    -webkit-background-clip:text; -webkit-text-fill-color:transparent; background-clip:text;
    margin:0 0 2px 0;
}}
.matora-sub {{
    font-size:0.88rem; font-weight:400;
    color:{HDR_SUB} !important; -webkit-text-fill-color:{HDR_SUB} !important; margin:0;
}}

/* PILLOLE */
.pills-wrap {{ display:flex; justify-content:center; gap:12px; margin:14px 0 24px 0; }}
.pill {{
    background:{PILL_BG}; border:2px solid {PILL_BD}; border-radius:50px;
    padding:10px 26px; font-weight:700; font-size:0.8rem;
    color:{PILL_FG} !important; -webkit-text-fill-color:{PILL_FG} !important;
    text-transform:uppercase; letter-spacing:1px;
    box-shadow:0 0 12px {PILL_SH};
    display:inline-flex; align-items:center; gap:7px; cursor:default;
}}

/* PANNELLI */
[data-testid="stVerticalBlockBorderWrapper"] {{
    background:{CARD} !important;
    border:1.5px solid {BORDER} !important;
    border-radius:12px !important;
    padding:20px !important;
    box-shadow:0 2px 16px {SHADOW} !important;
}}
[data-testid="stVerticalBlockBorderWrapper"] h3 {{
    font-size:1.25rem !important; font-weight:800 !important;
    color:{TEXT} !important; -webkit-text-fill-color:{TEXT} !important;
    margin-bottom:12px !important;
}}

/* SELECTBOX */
div[data-baseweb="select"] > div {{
    background-color:{INP_BG} !important; border:1px solid {INP_BD} !important;
    border-radius:8px !important; color:{TEXT} !important;
}}
div[data-baseweb="select"] span {{ color:{TEXT} !important; -webkit-text-fill-color:{TEXT} !important; }}
div[data-baseweb="select"] svg {{ fill:{TEXT} !important; }}
div[data-baseweb="popover"] li {{ background-color:{INP_BG} !important; color:{TEXT} !important; }}
div[data-baseweb="popover"] li:hover {{ background-color:{BORDER}22 !important; }}

/* TEXT INPUT */
.stTextInput input {{
    background-color:{INP_BG} !important; border:1px solid {INP_BD} !important;
    border-radius:8px !important; color:{TEXT} !important;
    font-family:'Inter',sans-serif !important; font-size:0.9rem !important;
    padding:9px 12px !important;
}}
.stTextInput input::placeholder {{ color:{INP_PH} !important; }}
.stTextInput label {{ color:{TEXT2} !important; -webkit-text-fill-color:{TEXT2} !important; font-size:0.85rem !important; }}

/* FILE UPLOADER — nascondi TUTTO il default, mostra solo dropzone */
[data-testid="stFileUploaderDropzone"] {{
    background-color:{UPL_BG} !important;
    border:2px dashed {UPL_BD} !important;
    border-radius:10px !important;
    padding:0 !important;
    min-height:70px !important;
    display:flex !important; align-items:center !important; justify-content:center !important;
}}
/* Nascondi istruzioni testo (drag & drop, size limit) */
[data-testid="stFileUploaderDropzoneInstructions"] {{ display:none !important; }}
/* Nascondi la scritta "Browse files" del pulsante nativo */
[data-testid="stFileUploaderDropzone"] button span {{ display:none !important; }}
/* Riscrivi il pulsante come testo personalizzato */
[data-testid="stFileUploaderDropzone"] button {{
    background:transparent !important; border:none !important;
    color:{UPL_TX} !important; -webkit-text-fill-color:{UPL_TX} !important;
    font-weight:600 !important; font-size:0.9rem !important;
    font-family:'Inter',sans-serif !important;
    padding:20px 16px !important; width:100% !important; cursor:pointer !important;
}}
[data-testid="stFileUploaderDropzone"] button::before {{
    content:"📁  [ Seleziona il file ]";
    color:{UPL_TX}; font-size:0.9rem; font-weight:600;
}}
/* Nasconde label sopra il file uploader */
[data-testid="stFileUploader"] label {{ display:none !important; }}
/* Nasconde eventuale nome file caricato che fa overflow */
[data-testid="stFileUploaderFile"] small {{ color:{TEXT2} !important; }}

/* PULSANTE PRIMARY */
div.stButton > button[kind="primary"] {{
    background:linear-gradient(90deg,#ff007f,#cc00aa) !important;
    color:#fff !important; font-weight:700 !important;
    font-family:'Inter',sans-serif !important; font-size:0.85rem !important;
    letter-spacing:0.5px; border-radius:8px !important; border:none !important;
    width:100% !important; padding:13px 20px !important; text-transform:uppercase;
    box-shadow:0 3px 16px rgba(255,0,127,0.4) !important;
}}
div.stButton > button[kind="primary"]:hover {{ opacity:0.9 !important; }}

/* PULSANTE ELIMINA */
div.stButton > button[kind="secondary"] {{
    background-color:{ELIM_BG} !important;
    color:{ELIM_FG} !important; -webkit-text-fill-color:{ELIM_FG} !important;
    border:none !important; border-radius:6px !important;
    font-weight:600 !important; font-family:'Inter',sans-serif !important;
    font-size:0.78rem !important; padding:5px 14px !important;
    white-space:nowrap; min-width:70px;
}}
div.stButton > button[kind="secondary"]:hover {{ background-color:#3d1b7e !important; }}

/* TOGGLE */
[data-testid="stToggle"] label {{
    color:{TEXT2} !important; -webkit-text-fill-color:{TEXT2} !important;
    font-size:0.85rem !important; font-weight:600 !important;
}}

/* ALERTS */
[data-testid="stAlert"] {{ border-radius:8px !important; font-family:'Inter',sans-serif !important; }}
</style>
""", unsafe_allow_html=True)

# Inietta SVG circuit board
st.markdown(CIRCUIT_SVG, unsafe_allow_html=True)

# ── HEADER ────────────────────────────────────────────────
col_logo, col_titolo, col_toggle = st.columns([1, 8, 2], vertical_alignment="center")
with col_logo:
    st.image("https://raw.githubusercontent.com/sofi-sofi-sofi/archivio-appunti/main/logo_matora.png", width=58)
with col_titolo:
    st.markdown(
        '<p class="matora-title">MATORA AI</p>'
        f'<p class="matora-sub">L\'ecosistema intelligente per i tuoi appunti universitari</p>',
        unsafe_allow_html=True
    )
with col_toggle:
    st.toggle("☀️ Chiaro" if is_dark else "🌙 Scuro", key="tema_scuro")

st.markdown("""
<div class="pills-wrap">
  <div class="pill">📥 &nbsp;INVIA APPUNTI</div>
  <div class="pill">🔍 &nbsp;CERCA NELL'ARCHIVIO</div>
  <div class="pill">🗑️ &nbsp;MANUTENZIONE</div>
</div>
""", unsafe_allow_html=True)

# ── DATI GITHUB (cache 10s) ────────────────────────────────
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
                                    files.append({"nome": f.name.replace(".md",""), "url": f.html_url})
            except:
                pass
    except:
        pass
    return sorted(list(materie)), files

materie_ordinate, tutti_i_file = get_github_data(GITHUB_TOKEN, NOME_REPOSITORY)

# ── DASHBOARD ─────────────────────────────────────────────
col_invia, col_cerca, col_gestisci = st.columns([1.3, 2, 1.3], gap="large")

# ─── PANNELLO 1: INVIA ────────────────────────────────────
with col_invia:
    with st.container(border=True):
        st.markdown("### Invia Appunti")
        st.markdown(f"<p style='font-size:0.88rem;font-weight:500;color:{TEXT2};margin-bottom:8px;'>Su quale materia stai lavorando?</p>", unsafe_allow_html=True)

        opzioni = ["➕ Aggiungi Nuova Materia..."] + materie_ordinate
        scelta = st.selectbox("Materia", opzioni, label_visibility="collapsed")

        materia_selezionata = ""
        if scelta == "➕ Aggiungi Nuova Materia...":
            materia_selezionata = st.text_input("Nome nuova materia:")
        else:
            materia_selezionata = scelta

        st.markdown(f"<h4 style='margin:18px 0 2px 0;font-size:1.05rem;font-weight:800;color:{TEXT};'>PDF Upload</h4>", unsafe_allow_html=True)
        st.markdown(f"<p style='font-size:0.82rem;color:{TEXT2};margin-bottom:8px;'>Trascina o seleziona il PDF dei tuoi appunti</p>", unsafe_allow_html=True)

        # label_visibility="collapsed" nasconde la label nativa;
        # il testo visibile viene iniettato via CSS ::before sul pulsante
        file_caricato = st.file_uploader("upload", type=["pdf"], label_visibility="collapsed")

        nome_pers = st.text_input("Dai un nome al file (opzionale):", placeholder="es. Lezione_1")

        if file_caricato and materia_selezionata:
            if st.button("🚀 AVVIA ELABORAZIONE INTELLIGENTE", type="primary"):
                with st.spinner("Elaborazione AI in corso..."):
                    nome_base = nome_pers.strip().replace(" ","_") if nome_pers else os.path.splitext(file_caricato.name)[0]
                    try:
                        pdf_bytes = file_caricato.read()
                        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
                        immagini = [
                            base64.b64encode(doc.load_page(i).get_pixmap(matrix=fitz.Matrix(2,2)).tobytes("png")).decode('utf-8')
                            for i in range(len(doc))
                        ]
                        client = ChatCompletionsClient(
                            endpoint="https://models.inference.ai.azure.com",
                            credential=AzureKeyCredential(GITHUB_TOKEN)
                        )
                        prompt = "Analizza questo appunto. Crea: 1. Riassunto. 2. Schema. 3. Quiz 3 domande. 4. Parole chiave."
                        contenuto = [{"type":"text","text":prompt}] + [
                            {"type":"image_url","image_url":{"url":f"data:image/png;base64,{img}"}}
                            for img in immagini
                        ]
                        response = client.complete(
                            messages=[SystemMessage(content="Sei un assistente universitario."), UserMessage(content=contenuto)],
                            model="gpt-4o-mini", max_tokens=2500
                        )
                        risultato = response.choices[0].message.content
                        try:
                            repo.create_file(f"appunti/{materia_selezionata}/{nome_base}.pdf","Nuovo PDF",pdf_bytes,branch="main")
                        except: pass
                        path_md = f"risultati/{materia_selezionata}/{nome_base}.md"
                        try:
                            c = repo.get_contents(path_md, ref="main")
                            repo.update_file(c.path,"Aggiornato",risultato,c.sha,branch="main")
                        except:
                            repo.create_file(path_md,"Creato",risultato,branch="main")
                        st.success("✅ Elaborazione completata!")
                        get_github_data.clear()
                        st.rerun()
                    except Exception as e:
                        st.error(f"Errore: {e}")

# ─── PANNELLO 2: CERCA ────────────────────────────────────
with col_cerca:
    with st.container(border=True):
        st.markdown("### Cerca nell'Archivio")
        query = st.text_input("Cerca", placeholder="🔍  Cerca nell'Archivio... (#Tag o Materia)", label_visibility="collapsed").strip().lower()
        file_filtrati = [f for f in tutti_i_file if query in f["nome"].lower()] if query else tutti_i_file

        if file_filtrati:
            cards = ""
            for f in file_filtrati:
                titolo = f["nome"].replace("_"," ").title()
                if len(titolo) > 18: titolo = titolo[:16]+"…"
                cards += f"""<a href="{f['url']}" target="_blank"
                  style="background:{FC_BG};border:1px solid {FC_BD};border-radius:10px;
                         padding:12px 8px;text-align:center;text-decoration:none;
                         display:flex;flex-direction:column;align-items:center;
                         justify-content:flex-start;gap:6px;min-height:88px;
                         font-family:Inter,sans-serif;cursor:pointer;transition:all 0.15s;"
                  onmouseover="this.style.borderColor='{FC_HV}';this.style.transform='translateY(-2px)';this.style.boxShadow='0 4px 14px rgba(255,0,127,0.2)'"
                  onmouseout="this.style.borderColor='{FC_BD}';this.style.transform='none';this.style.boxShadow='none'">
                  <svg width="32" height="38" viewBox="0 0 32 38" fill="none" xmlns="http://www.w3.org/2000/svg">
                    <path d="M4 0H22L32 10V34C32 36.2 30.2 38 28 38H4C1.8 38 0 36.2 0 34V4C0 1.8 1.8 0 4 0Z" fill="#ff2255"/>
                    <path d="M22 0L32 10H24C22.9 10 22 9.1 22 8V0Z" fill="#cc0033"/>
                    <text x="5" y="28" font-family="Inter,sans-serif" font-size="9" font-weight="800" fill="white">PDF</text>
                  </svg>
                  <div style="font-size:0.75rem;font-weight:700;color:{FC_TX};line-height:1.25;word-break:break-word;">{titolo}</div>
                </a>"""

            html = f"""<!DOCTYPE html><html><head>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@700&display=swap" rel="stylesheet">
<style>body{{margin:0;padding:0;background:transparent;}}
.g{{display:grid;grid-template-columns:repeat(3,1fr);gap:10px;padding:4px 2px;}}</style>
</head><body><div class="g">{cards}</div></body></html>"""
            n_rows = (len(file_filtrati)+2)//3
            components.html(html, height=n_rows*108+20, scrolling=False)
        else:
            st.info("Nessun appunto disponibile. Carica il tuo primo PDF!")

# ─── PANNELLO 3: MANUTENZIONE ─────────────────────────────
with col_gestisci:
    with st.container(border=True):
        st.markdown("### Manutenzione")
        st.markdown(f"<p style='font-size:0.88rem;font-weight:600;color:{TEXT2};margin-bottom:10px;'>Gestisci Archivio</p>", unsafe_allow_html=True)

        materia_del = st.selectbox(
            "Materia",
            materie_ordinate if materie_ordinate else ["Nessuna materia"],
            label_visibility="collapsed"
        )

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
                    c1, c2 = st.columns([7,3], vertical_alignment="center")
                    with c1:
                        icon = "📄" if file_gh.name.endswith(".pdf") else "📝"
                        st.markdown(f"<span style='font-size:0.82rem;font-weight:600;'>{icon} {file_gh.name}</span>", unsafe_allow_html=True)
                    with c2:
                        if st.button("Elimina", key=f"del_{file_gh.path}"):
                            try:
                                repo.delete_file(file_gh.path,"Rimosso",file_gh.sha,branch="main")
                                get_github_data.clear()
                                st.rerun()
                            except:
                                st.error("Errore eliminazione")
