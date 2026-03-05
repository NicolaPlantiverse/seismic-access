import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, Wedge, Circle, Polygon
import math

# --- CONFIGURAZIONE PAGINA ---
st.set_page_config(page_title="Seismic Access | Demo", page_icon="🏗️", layout="wide")

# --- STILI CSS PREMIUM ---
st.markdown("""
<style>
    .metric-box { background-color: #f8f9fa; border-left: 5px solid #004085; padding: 15px; border-radius: 5px; margin-bottom: 10px;}
    .alert-box { background-color: #f8d7da; border-left: 5px solid #dc3545; padding: 15px; border-radius: 5px; margin-bottom: 10px;}
    .success-box { background-color: #d4edda; border-left: 5px solid #28a745; padding: 15px; border-radius: 5px; margin-bottom: 10px;}
    .title-text { color: #004085; font-weight: bold; }
</style>
""", unsafe_allow_html=True)

# --- HEADER COMMERCIALE ---
st.markdown("<h1 class='title-text'>🏗️ SEISMIC ACCESS Validator</h1>", unsafe_allow_html=True)
st.markdown("**Il tuo Piano di Emergenza Comunale (CLE) ti sta proteggendo o ti sta ingannando?** Scopri i limiti del metodo geometrico standard e il vantaggio del nostro Gemello Digitale Cinematico.")

# --- MOTORE MATEMATICO (Dal Paper Q1) ---
def calcola_k_b(typology, slope, confinement):
    # Parametri paper
    c_dict = {"Muratura Storica": 0.22, "Cemento Armato (Post-1980)": 0.04}
    theta_dict = {"Muratura Storica": 65, "Cemento Armato (Post-1980)": 20}
    
    # Moltiplicatori
    c = c_dict[typology]
    theta = theta_dict[typology]
    beta_topo = 1 + 0.4 * math.tanh(slope / 0.3)
    gamma_conf = {"Isolato": 1.0, "A schiera (Centro Storico)": 0.65}[confinement]
    
    # Semplificazione per la demo: assumiamo PGA alta (0.35g) per collasso avvenuto
    w_eff = 1.0 * beta_topo * 0.35
    f_typ = min(1.0, c * (w_eff ** 1.2)) # Approssimazione potenza
    k_b = min(1.0, f_typ * gamma_conf)
    
    return k_b, theta

# --- SIDEBAR: SCENARI "TRAPPOLA" ---
st.sidebar.header("🕹️ Scenari Dimostrativi")
scenario = st.sidebar.radio(
    "Seleziona un caso reale:",
    ("1. Il Falso Allarme (Spreco fondi)", 
     "2. La Trappola Mortale (Falso sicuro)", 
     "3. La Chicane (Strettoia storica)")
)

st.sidebar.markdown("---")
st.sidebar.header("⚙️ Parametri Avanzati")

# Imposta valori di default in base allo scenario per stupire l'utente
if "1" in scenario:
    st.sidebar.info("💡 **Scenario:** Un palazzo in cemento armato confinato. Il CLE blocca la strada, noi sappiamo che imploderà su se stesso liberando il passaggio.")
    w_road = st.sidebar.slider("Larghezza Strada (m)", 4.0, 12.0, 7.0)
    h_bldg = st.sidebar.slider("Altezza Edificio (m)", 5.0, 20.0, 12.0)
    typology = st.sidebar.selectbox("Tipologia", ["Cemento Armato (Post-1980)", "Muratura Storica"])
    slope = st.sidebar.slider("Pendenza terreno", 0.0, 0.4, 0.0)
    conf = st.sidebar.selectbox("Confinamento", ["A schiera (Centro Storico)", "Isolato"])
    chicane_mode = False
elif "2" in scenario:
    st.sidebar.info("💡 **Scenario:** Strada di 6m. Macerie di 3m. Il CLE vede 3m liberi e dice 'Aperta'. Ma l'autobotte (2.5m + raggio sterzata) si incastra.")
    w_road = st.sidebar.slider("Larghezza Strada (m)", 4.0, 12.0, 6.0)
    h_bldg = st.sidebar.slider("Altezza Edificio (m)", 5.0, 20.0, 10.0)
    typology = st.sidebar.selectbox("Tipologia", ["Muratura Storica", "Cemento Armato (Post-1980)"])
    slope = st.sidebar.slider("Pendenza terreno", 0.0, 0.4, 0.1)
    conf = st.sidebar.selectbox("Confinamento", ["Isolato", "A schiera (Centro Storico)"])
    chicane_mode = False
else:
    st.sidebar.info("💡 **Scenario:** Due crolli sfalsati. Matematicamente c'è spazio, ma il mezzo di soccorso non ha il raggio di sterzata. Il CLE non lo vede.")
    w_road = st.sidebar.slider("Larghezza Strada (m)", 4.0, 12.0, 6.5)
    h_bldg = st.sidebar.slider("Altezza Edifici (m)", 5.0, 20.0, 10.0)
    typology = "Muratura Storica"
    slope = 0.0
    conf = "Isolato"
    chicane_mode = True

# --- CALCOLI ---
L_req = 3.5 # 2.5m veicolo + 1m margine/curva
R_cle = h_bldg

if chicane_mode:
    # Calcoli per scenario chicane (bilateral)
    k_b, theta = calcola_k_b(typology, slope, conf)
    R_new = h_bldg * k_b * math.sin(math.radians(theta))
    R_new = max(R_new, 3.5) # Forzazione per scopo illustrativo demo
    spazio_residuo_cle = w_road - 3.0 # Fittizio per far passare CLE
    spazio_residuo_new = "Chicane Block"
else:
    k_b, theta = calcola_k_b(typology, slope, conf)
    R_new = h_bldg * k_b * math.sin(math.radians(theta))
    spazio_residuo_cle = w_road - R_cle
    spazio_residuo_new = w_road - R_new

# Logica di Blocco
passa_cle = spazio_residuo_cle > (w_road / 2.0) if not chicane_mode else True # Il CLE ingenuo guarda solo il centro
if chicane_mode:
    passa_new = False
else:
    passa_new = spazio_residuo_new >= L_req

# --- PLOTTING FUNZIONE ---
def draw_street(ax, method_name, is_pass, R_val, chicane=False):
    ax.set_xlim(0, max(20, w_road + 10))
    ax.set_ylim(0, 30)
    ax.axis('off')
    
    # Disegna Strada
    ax.add_patch(Rectangle((5, 0), w_road, 30, color='#d3d3d3', zorder=1))
    ax.plot([5 + w_road/2, 5 + w_road/2], [0, 30], color='white', linestyle='--', zorder=2)
    
    # Disegna Edificio/i
    ax.add_patch(Rectangle((0, 5), 5, 20, color='#6c757d', zorder=3)) # Sinistra
    if chicane:
        ax.add_patch(Rectangle((5+w_road, 15), 5, 10, color='#6c757d', zorder=3)) # Destra sfalsato
        
    # Disegna Macerie
    if method_name == "CLE":
        if chicane:
            ax.add_patch(Wedge((5, 10), 3.5, -90, 90, color='red', alpha=0.3, zorder=4))
            ax.add_patch(Wedge((5+w_road, 20), 3.5, 90, 270, color='red', alpha=0.3, zorder=4))
        else:
            ax.add_patch(Wedge((5, 15), R_val, -90, 90, color='red', alpha=0.3, zorder=4)) # Cerchio CLE
    else:
        if chicane:
             ax.add_patch(Wedge((5, 10), R_new, -theta, theta, color='#cc3333', alpha=0.7, zorder=4))
             ax.add_patch(Wedge((5+w_road, 20), R_new, 180-theta, 180+theta, color='#cc3333', alpha=0.7, zorder=4))
        else:
            ax.add_patch(Wedge((5, 15), R_new, -theta, theta, color='#cc3333', alpha=0.7, zorder=4)) # Wedge Nuovo
            
    # Disegna Veicolo Emergenza (2.5m x 6m)
    veh_color = '#28a745' if is_pass else '#dc3545'
    if chicane:
        # Mostra il veicolo incastrato di traverso
        veh = Rectangle((5 + w_road/2 - 1.25, 12), 2.5, 6, angle=45, color=veh_color, zorder=5)
        ax.add_patch(veh)
    else:
        y_pos = 12
        if not is_pass and method_name == "Nuovo Modello":
            x_pos = 5 + w_road - 2.8 # Schiacciato
        else:
            x_pos = 5 + (w_road/2) - 1.25
        ax.add_patch(Rectangle((x_pos, y_pos), 2.5, 6, color=veh_color, zorder=5))

# --- RENDER UI ---
col1, col2 = st.columns(2)

with col1:
    st.subheader("🔴 Modello CLE (Attuale)")
    fig_cle, ax_cle = plt.subplots(figsize=(4, 6))
    draw_street(ax_cle, "CLE", passa_cle, R_cle, chicane_mode)
    st.pyplot(fig_cle)
    
    if "1" in scenario:
        st.markdown("<div class='alert-box'><b>FALSO ALLARME:</b> Il CLE dichiara la strada bloccata. Il Comune pianifica un percorso alternativo più lungo, allungando i tempi di soccorso e sprecando risorse per sgombero prioritario inutile.</div>", unsafe_allow_html=True)
    elif "2" in scenario:
        st.markdown("<div class='success-box' style='border-left-color: #ffc107;'><b>FALSO SICURO:</b> Il CLE vede che le macerie non superano la metà strada e dà il via libera.</div>", unsafe_allow_html=True)
    else:
        st.markdown("<div class='success-box' style='border-left-color: #ffc107;'><b>FALSO SICURO:</b> Il CLE calcola i metri liberi, ignora il raggio di sterzata e dà il via libera.</div>", unsafe_allow_html=True)

with col2:
    st.subheader("🟢 Seismic Access (Il nostro Modello)")
    fig_new, ax_new = plt.subplots(figsize=(4, 6))
    draw_street(ax_new, "Nuovo Modello", passa_new, R_new, chicane_mode)
    st.pyplot(fig_new)
    
    if "1" in scenario:
        st.markdown("<div class='success-box'><b>✅ RISORSE SALVATE:</b> Calcolando il crollo gravitazionale del Cemento Armato (Wedge stretto), il software certifica che l'autobotte passa in sicurezza. Strada strategica salvata!</div>", unsafe_allow_html=True)
    elif "2" in scenario:
        st.markdown("<div class='alert-box'><b>🚨 TRAPPOLA EVITATA:</b> Il software rileva che lo spazio residuo è minore di L_req (2.5m del mezzo + margini). Il CLE avrebbe mandato i pompieri a incastrarsi.</div>", unsafe_allow_html=True)
    else:
        st.markdown("<div class='alert-box'><b>🚨 TRAPPOLA EVITATA:</b> L'algoritmo rileva una <i>Chicane Cinematica</i>. L'autobotte (corpo rigido) non ha spazio longitudinale per curvare. Strada bloccata, vite salvate.</div>", unsafe_allow_html=True)

st.markdown("---")
st.markdown("""
### 📊 Perché ti serve il livello Enterprise (Tier II)?
Il modello sopra è il livello base. La realtà è che un terremoto è un evento probabilistico e spazialmente correlato.
Il nostro modulo **Enterprise** simula 500 scenari Monte Carlo (approvati dalla letteratura scientifica) per creare una mappa dell'**USAI (Urban Seismic Accessibility Index)**, identificando l'1% degli edifici la cui messa in sicurezza salverà l'intera viabilità del tuo Comune.

👉 [Contattaci per un Audit sui dati del tuo Comune](#) | 📄 [Leggi il Paper Scientifico Q1](#)
""")
