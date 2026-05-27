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
    st.session_state.tema_scuro = True

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
    bg_app          = "#0d0d1a"
    text_main       = "#ffffff"
    text_sec        = "#9090b8"
    card_bg         = "#12122a"
    card_border     = "#9d00ff"
    neon_glow       = "rgba(157,0,255,0.3)"
    neon_glow2      = "rgba(255,0,127,0.35)"
    input_bg        = "#1a1a35"
    input_border    = "#2a2a55"
    row_border      = "#2a2a55"
    btn_elim_bg     = "#25003d"
    btn_elim_border = "#9d00ff"
    btn_elim_color  = "#cc66ff"
    pill_bg         = "#0d001f"
    pill_border     = "#ff007f"
    pill_color      = "#ff007f"
    fc_bg           = "#181830"
    fc_border       = "#2a2a55"
    fc_hover        = "#9d00ff"
    header_sub      = "#8888aa"
    grid_line       = "rgba(157,0,255,0.08)"
else:
    bg_app          = "#f0f0fa"
    text_main       = "#0a0a20"
    text_sec        = "#5a5a80"
    card_bg         = "#ffffff"
    card_border     = "#ff007f"
    neon_glow       = "rgba(255,0,127,0.15)"
    neon_glow2      = "rgba(157,0,255,0.18)"
    input_bg        = "#f5f5ff"
    input_border    = "#dcdcf5"
    row_border      = "#ebebf8"
    btn_elim_bg     = "#1a0033"
    btn_elim_border = "#9d00ff"
    btn_elim_color  = "#dd88ff"
    pill_bg         = "#0b001a"
    pill_border     = "#ff007f"
    pill_color      = "#ff007f"
    fc_bg           = "#ffffff"
    fc_border       = "#e0e0f5"
    fc_hover        = "#ff007f"
    header_sub      = "#6060a0"
    grid_line       = "rgba(255,0,127,0.07)"

# ==========================================
# 3. CSS GLOBALE
# ==========================================
st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Outfit:wght@400;500;600;700;800;900&display=swap');

/* ── BASE ── */
html, body, .stApp, [data-testid="stAppViewContainer"], .main {{
    background-color: {bg_app} !important;
    font-family: 'Outfit', sans-serif !important;
    color: {text_main} !important;
}}
.main .block-container {{
    padding: 1.4rem 2rem 2rem 2rem !important;
    max-width: 1420px !important;
}}

/* Circuit-board grid */
[data-testid="stAppViewContainer"]::before {{
    content: '';
    position: fixed; inset: 0;
    background-image:
        linear-gradient({grid_line} 1px, transparent 1px),
        linear-gradient(90deg, {grid_line} 1px, transparent 1px);
    background-size: 44px 44px;
    pointer-events: none;
    z-index: 0;
}}

/* ── TESTO ── */
h1,h2,h3,h4,h5,h6,p,span,label,li {{
    color: {text_main} !important;
    font-family: 'Outfit', sans-serif !important;
}}

/* ── HIDE STREAMLIT CHROME ── */
#MainMenu, footer, header {{ visibility: hidden !important; }}

/* ── TITOLO MATORA ── */
.matora-title {{
    font-size: 2.1rem; font-weight: 900; letter-spacing: -1px; line-height: 1;
    background: linear-gradient(90deg, #ff007f, #9d00ff);
    -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text;
    margin: 0;
}}
.matora-sub {{
    font-size: 0.9rem; font-weight: 500; color: {header_sub} !important;
    -webkit-text-fill-color: {header_sub} !important; margin: 3px 0 0 0;
}}

/* ── PILLOLE ── */
.pills-wrap {{
    display: flex; justify-content: center; gap: 14px;
    margin: 16px 0 26px 0; flex-wrap: wrap;
}}
.pill {{
    background: {pill_bg};
    border: 2px solid {pill_border};
    border-radius: 50px;
    padding: 11px 30px;
    font-weight: 700; font-size: 0.82rem;
    color: {pill_color} !important; -webkit-text-fill-color: {pill_color} !important;
    text-transform: uppercase; letter-spacing: 1.5px;
    box-shadow: 0 0 14px {neon_glow2};
    display: inline-flex; align-items: center; gap: 8px;
}}

/* ── PANNELLI ── */
[data-testid="stVerticalBlockBorderWrapper"] {{
    background: {card_bg} !important;
    border: 1.5px solid {card_border} !important;
    border-radius: 16px !important;
    padding: 22px !important;
    box-shadow: 0 0 28px {neon_glow}, 0 4px 20px rgba(0,0,0,0.1) !important;
    position: relative; overflow: hidden;
}}
[data-testid="stVerticalBlockBorderWrapper"]::before {{
    content: ''; position: absolute; top: 0; left: 0; right: 0; height: 3px;
    background: linear-gradient(90deg, #ff007f, #9d00ff);
    border-radius: 16px 16px 0 0;
}}
[data-testid="stVerticalBlockBorderWrapper"] h3 {{
    font-size: 1.3rem !important; font-weight: 800 !important;
    color: {text_main} !important; -webkit-text-fill-color: {text_main} !important;
    margin-bottom: 16px !important;
}}

/* ── SELECTBOX ── */
div[data-baseweb="select"] > div {{
    background-color: {input_bg} !important;
    border: 1.5px solid {input_border} !important;
    border-radius: 10px !important; color: {text_main} !important;
}}
div[data-baseweb="select"] span {{ color: {text_main} !important; -webkit-text-fill-color: {text_main} !important; }}
div[data-baseweb="select"] svg {{ fill: {text_main} !important; }}
div[data-baseweb="popover"] li {{
    background-color: {input_bg} !important; color: {text_main} !important;
}}
div[data-baseweb="popover"] li:hover {{ background-color: {card_border}44 !important; }}

/* ── TEXT INPUT ── */
.stTextInput input {{
    background-color: {input_bg} !important;
    border: 1.5px solid {input_border} !important;
    border-radius: 10px !important; color: {text_main} !important;
    font-family: 'Outfit', sans-serif !important;
}}
.stTextInput input::placeholder {{ color: {text_sec} !important; }}
.stTextInput input:focus {{
    border-color: {card_border} !important;
    box-shadow: 0 0 0 3px {neon_glow} !important;
}}
.stTextInput label {{ color: {text_sec} !important; -webkit-text-fill-color: {text_sec} !important; font-size:0.85rem !important; }}

/* ── FILE UPLOADER ── */
div[data-testid="stFileUploaderDropzone"] {{
    background-color: {input_bg} !important;
    border: 2px dashed {card_border} !important;
    border-radius: 12px !important;
}}
div[data-testid="stFileUploaderDropzone"] button {{
    background: transparent !important;
    border: 1.5px solid {card_border} !important;
    color: {card_border} !important;
    border-radius: 8px !important; font-weight: 700 !important;
    font-family: 'Outfit', sans-serif !important;
}}
div[data-testid="stFileUploaderDropzone"] * {{ color: {text_sec} !important; }}

/* ── PULSANTE PRIMARY (Avvia) ── */
div.stButton > button[kind="primary"] {{
    background: linear-gradient(90deg, #ff007f, #9d00ff) !important;
    color: #fff !important; font-weight: 800 !important;
    font-family: 'Outfit', sans-serif !important;
    font-size: 0.88rem !important; letter-spacing: 0.8px;
    border-radius: 10px !important; border: none !important;
    width: 100% !important; padding: 14px 20px !important;
    text-transform: uppercase;
    box-shadow: 0 4px 20px {neon_glow2} !important;
    transition: transform 0.15s, box-shadow 0.15s !important;
}}
div.stButton > button[kind="primary"]:hover {{
    transform: translateY(-2px) !important;
    box-shadow: 0 8px 30px {neon_glow2} !important;
}}

/* ── PULSANTE ELIMINA (secondary) ── */
div.stButton > button[kind="secondary"] {{
    background-color: {btn_elim_bg} !important;
    color: {btn_elim_color} !important; -webkit-text-fill-color: {btn_elim_color} !important;
    border: 1.5px solid {btn_elim_border} !important;
    border-radius: 8px !important; font-weight: 700 !important;
    font-family: 'Outfit', sans-serif !important;
    font-size: 0.8rem !important; padding: 5px 14px !important;
    white-space: nowrap;
    transition: background 0.15s, box-shadow 0.15s !important;
}}
div.stButton > button[kind="secondary"]:hover {{
    background-color: #3d0060 !important;
    box-shadow: 0 0 12px rgba(157,0,255,0.45) !important;
}}

/* ── TOGGLE ── */
[data-testid="stToggle"] label {{
    color: {text_sec} !important; -webkit-text-fill-color: {text_sec} !important;
    font-size: 0.85rem !important; font-weight: 600 !important;
}}

/* ── MANUTENZIONE righe ── */
.man-row {{
    display: flex; align-items: center; justify-content: space-between;
    padding: 8px 0; border-bottom: 1px solid {row_border};
}}
.man-row:last-child {{ border-bottom: none; }}
.man-name {{
    font-size: 0.83rem; font-weight: 600;
    color: {text_main} !important; -webkit-text-fill-color: {text_main} !important;
    display: flex; align-items: center; gap: 6px;
}}
</style>
""", unsafe_allow_html=True)

# ==========================================
# 4. HEADER
# ==========================================
col_logo, col_titolo, col_toggle = st.columns([1, 8, 2], vertical_alignment="center")
with col_logo:
    st.image("https://raw.githubusercontent.com/sofi-sofi-sofi/archivio-appunti/main/logo_matora.png", width=56)
with col_titolo:
    st.markdown('<p class="matora-title">MATORA AI</p><p class="matora-sub">L\'ecosistema intelligente per i tuoi appunti universitari</p>', unsafe_allow_html=True)
with col_toggle:
    label_toggle = "☀️ Tema Chiaro" if is_dark else "🌙 Tema Scuro"
    st.toggle(label_toggle, key="tema_scuro")

st.markdown("""
<div class="pills-wrap">
    <div class="pill">📥&nbsp; INVIA APPUNTI</div>
    <div class="pill">🔍&nbsp; CERCA NELL'ARCHIVIO</div>
    <div class="pill">🗑️&nbsp; MANUTENZIONE</div>
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
# 5. DASHBOARD 3 COLONNE
# ==========================================
col_invia, col_cerca, col_gestisci = st.columns([1.3, 2, 1.3], gap="large")

# ─── PANNELLO 1: INVIA ──────────────────
with col_invia:
    with st.container(border=True):
        st.markdown("### Invia Appunti")
        st.markdown(f"<p style='font-size:0.88rem;font-weight:500;color:{text_sec};-webkit-text-fill-color:{text_sec};margin-bottom:6px;'>Su quale materia stai lavorando?</p>", unsafe_allow_html=True)

        opzioni = ["➕ Aggiungi Nuova Materia..."] + materie_ordinate
        scelta = st.selectbox("Materia", opzioni, label_visibility="collapsed")

        materia_selezionata = ""
        if scelta == "➕ Aggiungi Nuova Materia...":
            materia_selezionata = st.text_input("Nome nuova materia:")
        else:
            materia_selezionata = scelta

        st.markdown(f"<h4 style='margin-top:18px;margin-bottom:4px;font-size:1rem;font-weight:700;color:{text_main};-webkit-text-fill-color:{text_main};'>📄 PDF Upload</h4>", unsafe_allow_html=True)
        st.markdown(f"<p style='font-size:0.82rem;color:{text_sec};-webkit-text-fill-color:{text_sec};margin-bottom:8px;'>Trascina o seleziona il PDF dei tuoi appunti</p>", unsafe_allow_html=True)
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

# ─── PANNELLO 2: CERCA ──────────────────
with col_cerca:
    with st.container(border=True):
        st.markdown("### Cerca nell'Archivio")
        query = st.text_input("Cerca", placeholder="🔍  Cerca nell'Archivio... (#Tag o Materia)", label_visibility="collapsed").strip().lower()

        file_filtrati = [f for f in tutti_i_file if query in f["nome"].lower()] if query else tutti_i_file

        if file_filtrati:
            # Costruiamo l'HTML della griglia con i colori corretti già embedded
            card_items = ""
            for f in file_filtrati:
                titolo = f["nome"].replace("_", " ").title()
                card_items += f"""
                <a href="{f['url']}" target="_blank" style="
                    background:{fc_bg};
                    border:1.5px solid {fc_border};
                    border-radius:12px;
                    padding:14px 10px;
                    text-align:center;
                    text-decoration:none;
                    display:flex;
                    flex-direction:column;
                    align-items:center;
                    justify-content:center;
                    gap:8px;
                    min-height:88px;
                    transition:transform 0.18s,border-color 0.18s,box-shadow 0.18s;
                    cursor:pointer;
                " onmouseover="this.style.borderColor='{fc_hover}';this.style.transform='translateY(-3px)';this.style.boxShadow='0 6px 18px rgba(157,0,255,0.25)'"
                   onmouseout="this.style.borderColor='{fc_border}';this.style.transform='none';this.style.boxShadow='none'">
                    <div style="font-size:1.7rem;line-height:1;">📄</div>
                    <div style="font-size:0.78rem;font-weight:700;color:{text_main};line-height:1.25;word-break:break-word;">{titolo}</div>
                </a>"""

            grid_html = f"""
            <style>
              @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@700&display=swap');
              .fgrid {{ display:grid; grid-template-columns:repeat(3,1fr); gap:12px; margin-top:10px; font-family:'Outfit',sans-serif; }}
            </style>
            <div class="fgrid">{card_items}</div>
            """
            # Usa components.html per evitare il bug di escape di Streamlit
            components.html(grid_html, height=max(120, (len(file_filtrati) // 3 + 1) * 110), scrolling=False)
        else:
            st.info("Nessun appunto disponibile. Carica il tuo primo PDF!")

# ─── PANNELLO 3: MANUTENZIONE ───────────
with col_gestisci:
    with st.container(border=True):
        st.markdown("### Manutenzione")
        st.markdown(f"<p style='font-size:0.88rem;font-weight:600;color:{text_main};-webkit-text-fill-color:{text_main};margin-bottom:10px;'>Gestisci Archivio</p>", unsafe_allow_html=True)

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
                            f"<span class='man-name'>{icon} {file_gh.name}</span>",
                            unsafe_allow_html=True
                        )
                    with c2:
                        if st.button("Elimina", key=f"del_{file_gh.path}"):
                            try:
                                repo.delete_file(file_gh.path, "Rimosso", file_gh.sha, branch="main")
                                st.rerun()
                            except:
                                st.error("Errore eliminazione")
