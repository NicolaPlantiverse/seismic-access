import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, Wedge
import math

# --- CONFIGURAZIONE PAGINA ---
st.set_page_config(page_title="Seismic Access | Demo", page_icon="🏗️", layout="wide")

st.markdown("""
<style>
    .metric-box { background-color: #f8f9fa; border-left: 5px solid #004085; padding: 15px; border-radius: 5px; margin-bottom: 10px;}
    .alert-box { background-color: #f8d7da; border-left: 5px solid #dc3545; padding: 15px; border-radius: 5px; margin-bottom: 10px;}
    .success-box { background-color: #d4edda; border-left: 5px solid #28a745; padding: 15px; border-radius: 5px; margin-bottom: 10px;}
    .warning-box { background-color: #fff3cd; border-left: 5px solid #ffc107; padding: 15px; border-radius: 5px; margin-bottom: 10px;}
</style>
""", unsafe_allow_html=True)

st.markdown("<h1>🏗️ SEISMIC ACCESS Validator</h1>", unsafe_allow_html=True)
st.markdown("**Simulatore Cinematico in Real-Time (Basato su equazioni Tier I del Framework)**")

# --- SIDEBAR: INPUT UTENTE (DINAMICI E REALI) ---
st.sidebar.header("⚙️ Inserisci i Dati della Strada")

w_road = st.sidebar.slider("Larghezza Carreggiata (m)", 3.0, 15.0, 6.0, step=0.5)
h_bldg = st.sidebar.slider("Altezza Edificio (m)", 3.0, 25.0, 10.0, step=0.5)

typology = st.sidebar.radio("Tipologia Strutturale", ["Muratura Storica", "Cemento Armato (Post-1980)"])
conf = st.sidebar.radio("Confinamento Urbano", ["Isolato", "A schiera (Centro Storico)"])
slope = st.sidebar.slider("Pendenza topografica (s_b)", 0.0, 0.5, 0.0, step=0.05)

st.sidebar.markdown("---")
st.sidebar.markdown("*PGA di simulazione fissata a **0.30g***")

# --- MOTORE MATEMATICO (Esatto dal Paper) ---
w_pga = 0.30
alpha_soil = 1.0 # Suolo tipo B

# Eq 7: Topografia
beta_topo = 1.0 + 0.4 * math.tanh(slope / 0.3)

# Eq 4: Intensità Efficace
w_eff = alpha_soil * beta_topo * w_pga

# Dizionari parametri da Table 1 e Eq 9
if typology == "Muratura Storica":
    c, d = 0.22, 1.50
    theta_deg = 65
else:
    c, d = 0.04, 1.00
    theta_deg = 20

# Eq 5: Typology function
f_typ = min(1.0, c * (w_eff ** d))

# Eq 8: Confinement
gamma_conf = 1.0 if conf == "Isolato" else 0.65

# Eq 3: Vulnerability coeff
k_b = min(1.0, f_typ * gamma_conf)

# Eq 10: Horizontal Projection Radius (NEW MODEL)
r_star = h_bldg * k_b * math.sin(math.radians(theta_deg))

# Baseline CLE (Cerchio = altezza intera)
r_cle = h_bldg

# Eq 14: Required Free Width (Ingombro veicolo emergenza)
w_veh = 2.5
c_lat = 0.5
L_req = w_veh + (2 * c_lat) # 3.5m (Assumendo strada dritta per semplicità)

# Calcolo Spazi Residui
spazio_residuo_cle = w_road - r_cle
spazio_residuo_new = w_road - r_star

# Condizioni di Blocco
# CLE: Spesso considera transitabile se c'è uno spazio positivo qualsiasi, ignorando l'ambulanza
passa_cle = spazio_residuo_cle > 0.5 
# NUOVO MODELLO (Eq 17): Spazio deve essere >= L_req
passa_new = spazio_residuo_new >= L_req

# --- PLOTTING FUNZIONE (Matplotlib) ---
def draw_street(ax, method_name, is_pass, debris_radius, theta):
    ax.set_xlim(-5, w_road + 5)
    ax.set_ylim(0, 30)
    ax.axis('off')
    
    # Asfalto
    ax.add_patch(Rectangle((0, 0), w_road, 30, color='#d3d3d3', zorder=1))
    ax.plot([w_road/2, w_road/2], [0, 30], color='white', linestyle='--', zorder=2)
    
    # Marciapiedi/Bordi
    ax.plot([0, 0], [0, 30], color='#4a4a4a', linewidth=3, zorder=2)
    ax.plot([w_road, w_road], [0, 30], color='#4a4a4a', linewidth=3, zorder=2)
    
    # Edificio (a Sinistra, x = 0)
    ax.add_patch(Rectangle((-5, 5), 5, 20, color='#6c757d', zorder=3))
    
    # Disegna Macerie
    if method_name == "CLE":
        # CLE: Semicerchio isotropo 180 gradi (raggio h_bldg)
        ax.add_patch(Wedge((0, 15), debris_radius, -90, 90, color='red', alpha=0.3, zorder=4))
    else:
        # NEW MODEL: Cuneo direzionale (raggio r_star, angolo theta)
        ax.add_patch(Wedge((0, 15), debris_radius, -theta, theta, color='#cc3333', alpha=0.7, zorder=4))
        
    # Posizione del Veicolo di Emergenza (Tenta di passare a destra)
    veh_color = '#28a745' if is_pass else '#dc3545'
    
    # Se il veicolo passa, sta al centro dello spazio residuo. Se sbatte, si incastra sulle macerie
    if is_pass:
        x_pos = w_road - 1.25 - 0.5 # Sta a mezzo metro dal bordo destro
    else:
        # Lo disegniamo che sbatte contro le macerie o incastrato
        x_pos = max(debris_radius + 0.1, w_road/2) 
        if x_pos + 2.5 > w_road + 1: 
            x_pos = w_road - 2.0 # Incastrato fuori strada
            
    ax.add_patch(Rectangle((x_pos - 1.25, 12), 2.5, 6, color=veh_color, zorder=5))
    
    # Testo L_req (per mostrare il vincolo sul nuovo modello)
    if method_name == "SEISMIC ACCESS":
        ax.plot([w_road - L_req, w_road], [5, 5], color='blue', linewidth=2, marker='|')
        ax.text(w_road - (L_req/2), 3, f"L_req = {L_req}m", ha='center', color='blue', fontsize=8)


# --- RENDER INTERFACCIA E RISULTATI ---

# Mostriamo in alto i risultati numerici calcolati
st.markdown("### 📊 Risultati Matematici Real-Time")
c1, c2, c3, c4 = st.columns(4)
c1.metric("Larghezza Strada (L)", f"{w_road:.1f} m")
c2.metric("Altezza Efficace (h*)", f"{(h_bldg * k_b):.2f} m")
c3.metric("Raggio CLE (R)", f"{r_cle:.1f} m")
c4.metric("Raggio Nostro (r*)", f"{r_star:.2f} m")

st.markdown("---")

col1, col2 = st.columns(2)

with col1:
    st.subheader("🔴 Metodo CLE (Attuale)")
    fig_cle, ax_cle = plt.subplots(figsize=(5, 6))
    draw_street(ax_cle, "CLE", passa_cle, r_cle, 90)
    st.pyplot(fig_cle)
    
    if not passa_cle and passa_new:
        st.markdown("<div class='alert-box'><b>FALSO ALLARME:</b> Il CLE dichiara la strada inagibile per colpa del buffer circolare irrealistico. Hai appena 'perso' una strada sicura.</div>", unsafe_allow_html=True)
    elif passa_cle and not passa_new:
        st.markdown("<div class='warning-box'><b>PERICOLO (FALSO NEGATIVO):</b> Il CLE vede spazio libero geometrico e dà il via libera, ignorando che i 2.5m del camion dei pompieri non ci passano.</div>", unsafe_allow_html=True)
    elif not passa_cle and not passa_new:
        st.markdown("<div class='metric-box'>Strada bloccata anche per il CLE.</div>", unsafe_allow_html=True)
    else:
        st.markdown("<div class='metric-box'>Strada aperta per il CLE.</div>", unsafe_allow_html=True)

with col2:
    st.subheader("🟢 SEISMIC ACCESS (Tier I)")
    fig_new, ax_new = plt.subplots(figsize=(5, 6))
    draw_street(ax_new, "SEISMIC ACCESS", passa_new, r_star, theta_deg)
    st.pyplot(fig_new)
    
    if passa_new and not passa_cle:
        st.markdown(f"<div class='success-box'><b>✅ RISORSE SALVATE:</b> Calcolando la cinematica ({theta_deg}° wedge) e il confinamento (k_b={k_b:.2f}), restano {spazio_residuo_new:.1f}m liberi (≥ {L_req}m L_req). L'autobotte passa!</div>", unsafe_allow_html=True)
    elif not passa_new and passa_cle:
        st.markdown(f"<div class='alert-box'><b>🚨 TRAPPOLA EVITATA:</b> Restano solo {spazio_residuo_new:.1f}m. Minori dei {L_req}m richiesti (L_req). Il software impedisce che l'autobotte si incastri.</div>", unsafe_allow_html=True)
    elif passa_new:
        st.markdown(f"<div class='success-box'><b>✅ PERCORRIBILE:</b> La strada è sicura. (Spazio residuo: {spazio_residuo_new:.1f}m)</div>", unsafe_allow_html=True)
    else:
        st.markdown(f"<div class='alert-box'><b>🚨 BLOCCATA:</b> L'ingombro reale ostruisce il transito dei mezzi (Spazio residuo: {spazio_residuo_new:.1f}m < {L_req}m L_req).</div>", unsafe_allow_html=True)

st.markdown("---")
st.markdown("""
**Come testare le falle del CLE con questa Demo:**
1. **Prova il Falso Allarme:** Imposta Strada a `6.0m`, Edificio a `15m`, `Cemento Armato`, `A schiera`. Il CLE blocca tutto (raggio 15m), il nostro algoritmo capisce che l'edificio implode e la strada è libera.
2. **Prova il Falso Negativo (Trappola):** Imposta Strada a `6.0m`, Edificio a `10m`, `Muratura Storica`, `Isolato`. Il CLE vede che restano metri vuoti e la considera percorribile. Noi blocchiamo: il camion (2.5m) tocca le macerie!
""")
