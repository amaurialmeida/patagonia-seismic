import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import folium
from streamlit_folium import st_folium
import numpy as np
import requests
from datetime import datetime, date
import json

# ─────────────────────────────────────────────
# PAGE CONFIG
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="Sismologia — Patagônia",
    page_icon="🌍",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─────────────────────────────────────────────
# CUSTOM CSS
# ─────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
html, body, [class*="css"] { font-family: 'Inter', sans-serif; }

.main-header {
    background: linear-gradient(135deg, #1a0a00 0%, #3d1a00 40%, #6b2800 100%);
    color: white;
    padding: 3rem 2rem 2rem 2rem;
    border-radius: 0 0 1.5rem 1.5rem;
    margin: -1rem -1rem 2rem -1rem;
}
.main-header h1 { font-size: 2.2rem; font-weight: 700; margin-bottom: 0.4rem; letter-spacing: -0.02em; }
.main-header p { color: #f4a96a; font-size: 1rem; margin: 0; }
.tag-pill {
    display: inline-block; background: rgba(255,255,255,0.12);
    color: #ffe5cc; border: 1px solid rgba(255,255,255,0.2);
    border-radius: 20px; padding: 4px 14px;
    font-size: 0.75rem; margin: 4px 4px 0 0; font-weight: 500;
}

/* CARD DE DESTAQUE — 02/05/2025 */
.hero-card {
    background: linear-gradient(135deg, #7f1d1d 0%, #991b1b 60%, #b91c1c 100%);
    border: 2px solid #fca5a5;
    border-radius: 1.2rem;
    padding: 1.8rem 2rem;
    color: white;
    margin-bottom: 1.5rem;
    position: relative;
    overflow: hidden;
}
.hero-card::before {
    content: "🚨";
    position: absolute; top: 1rem; right: 1.5rem;
    font-size: 3.5rem; opacity: 0.18;
}
.hero-card .mag { font-size: 4rem; font-weight: 900; line-height: 1; color: #fca5a5; }
.hero-card h3 { font-size: 1.1rem; font-weight: 700; margin: 0.3rem 0; }
.hero-card p { font-size: 0.88rem; color: #fecaca; line-height: 1.6; margin: 0; }
.hero-card .badge-ev {
    display: inline-block; background: #fca5a5; color: #7f1d1d;
    font-size: 0.7rem; font-weight: 700; border-radius: 4px;
    padding: 2px 8px; margin-bottom: 0.5rem; text-transform: uppercase;
    letter-spacing: 0.08em;
}
.hero-detail {
    display: grid; grid-template-columns: repeat(3, 1fr); gap: 0.8rem;
    margin-top: 1rem;
}
.hero-detail-item { text-align: center; }
.hero-detail-item .hval { font-size: 1.3rem; font-weight: 700; color: #fca5a5; }
.hero-detail-item .hlbl { font-size: 0.72rem; color: #fecaca; margin-top: 2px; }

.metric-card {
    background: white; border: 1px solid #e2e8f0;
    border-radius: 1rem; padding: 1.2rem 1.4rem;
    text-align: center; box-shadow: 0 1px 3px rgba(0,0,0,0.05);
}
.metric-card .label { font-size: 0.72rem; color: #64748b; font-weight: 600;
    text-transform: uppercase; letter-spacing: 0.08em; margin-bottom: 0.4rem; }
.metric-card .value { font-size: 2rem; font-weight: 700; color: #0f172a; line-height: 1.1; }
.metric-card .unit { font-size: 0.8rem; color: #94a3b8; font-weight: 400; }
.metric-card .delta { font-size: 0.78rem; margin-top: 0.3rem; font-weight: 500; }

.section-title { font-size: 1.35rem; font-weight: 700; color: #0f172a;
    margin: 2rem 0 0.3rem 0; letter-spacing: -0.01em; }
.section-sub { font-size: 0.88rem; color: #64748b; margin-bottom: 1.2rem; }

.city-card {
    background: white; border: 1px solid #e2e8f0; border-radius: 0.9rem;
    padding: 1rem 1.2rem; margin-bottom: 0.7rem;
}
.city-card .cname { font-size: 1rem; font-weight: 600; color: #0f172a; }
.city-card .cdesc { font-size: 0.82rem; color: #475569; line-height: 1.6; margin-top: 0.3rem; }

.curiosity-box {
    background: #fff7ed; border-left: 4px solid #ea580c;
    border-radius: 0 0.7rem 0.7rem 0;
    padding: 1rem 1.2rem; margin-bottom: 1rem;
    font-size: 0.9rem; color: #7c2d12; line-height: 1.6;
}
.curiosity-box strong { color: #c2410c; }

.info-box {
    background: #f0f9ff; border-left: 4px solid #0284c7;
    border-radius: 0 0.7rem 0.7rem 0;
    padding: 1rem 1.2rem; margin-bottom: 1rem;
    font-size: 0.88rem; color: #0c4a6e; line-height: 1.6;
}

.timeline-item {
    display: flex; gap: 1rem; align-items: flex-start;
    padding: 0.9rem 0; border-bottom: 1px solid #f1f5f9;
}
.timeline-dot {
    width: 36px; height: 36px; border-radius: 50%;
    display: flex; align-items: center; justify-content: center;
    font-size: 0.85rem; font-weight: 700; flex-shrink: 0; color: white;
}
.timeline-content .te { font-size: 0.72rem; color: #94a3b8; font-weight: 500; }
.timeline-content .tm { font-size: 0.95rem; font-weight: 600; color: #0f172a; margin: 1px 0; }
.timeline-content .td { font-size: 0.82rem; color: #475569; line-height: 1.5; }

.source-box {
    background: #f8fafc; border: 1px solid #e2e8f0;
    border-radius: 0.7rem; padding: 0.8rem 1rem;
    font-size: 0.78rem; color: #64748b; margin-top: 2rem;
}
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# DADOS ESTÁTICOS — CIDADES DA PATAGÔNIA
# ─────────────────────────────────────────────
PATAGONIA_CITIES = {
    "Puerto Williams": {
        "lat": -54.9333, "lon": -67.6167,
        "country": "Chile 🇨🇱", "flag": "🇨🇱",
        "pop": 1900, "highlight": True,
        "desc": "Cidade mais austral do mundo. Pesquisador Amauri Almeida residiu aqui de março a outubro de 2025 e vivenciou o sismo de M7.4 em 02/05/2025.",
        "mmi_may2025": "V-VI (forte)",
        "seismic_risk": "Muito Alto",
    },
    "Punta Arenas": {
        "lat": -53.1638, "lon": -70.9171,
        "country": "Chile 🇨🇱", "flag": "🇨🇱",
        "pop": 143_000,
        "desc": "Capital de Magalhães. Ruas lotadas de residentes em busca de abrigos durante a evacuação de 02/05/2025. Fator de capacidade eólico de 58%.",
        "mmi_may2025": "III-IV (leve a moderado)",
        "seismic_risk": "Alto",
    },
    "Puerto Natales": {
        "lat": -51.7306, "lon": -72.5014,
        "country": "Chile 🇨🇱", "flag": "🇨🇱",
        "pop": 21_000,
        "desc": "Portal do Torres del Paine. Evacuada durante alerta de tsunami de 02/05/2025. Risco sísmico moderado nesta área.",
        "mmi_may2025": "II-III (leve)",
        "seismic_risk": "Moderado-Alto",
    },
    "Rio Verde": {
        "lat": -52.1333, "lon": -71.9833,
        "country": "Chile 🇨🇱", "flag": "🇨🇱",
        "pop": 350,
        "desc": "Pequena localidade rural na margem do Estreito de Magalhães. Citada em alertas de evacuação de 02/05/2025.",
        "mmi_may2025": "II-III (leve)",
        "seismic_risk": "Moderado",
    },
    "Ushuaia": {
        "lat": -54.8019, "lon": -68.3030,
        "country": "Argentina 🇦🇷", "flag": "🇦🇷",
        "pop": 56_825,
        "desc": "Cidade mais austral da Argentina. A apenas 222 km do epicentro de 02/05/2025. Alerta de tsunami ativo por ~3 horas.",
        "mmi_may2025": "IV-V (moderado)",
        "seismic_risk": "Muito Alto",
    },
    "Rio Gallegos": {
        "lat": -51.6201, "lon": -69.2183,
        "country": "Argentina 🇦🇷", "flag": "🇦🇷",
        "pop": 105_000,
        "desc": "Capital da Província de Santa Cruz. Sentido levemente o sismo de maio/2025. Principal polo eólico patagônico argentino.",
        "mmi_may2025": "II (muito leve)",
        "seismic_risk": "Moderado",
    },
    "Rio Grande": {
        "lat": -53.7880, "lon": -67.7100,
        "country": "Argentina 🇦🇷", "flag": "🇦🇷",
        "pop": 52_681,
        "desc": "Segunda maior cidade da Tierra del Fuego. A 334 km do epicentro de 02/05/2025. Atividades aquáticas suspensas na ocasião.",
        "mmi_may2025": "III-IV (leve a moderado)",
        "seismic_risk": "Alto",
    },
    "Porvenir": {
        "lat": -53.2986, "lon": -70.3660,
        "country": "Chile 🇨🇱", "flag": "🇨🇱",
        "pop": 6_200,
        "desc": "Capital da Provincia de Tierra del Fuego chilena. Evacuada durante alerta de 02/05/2025. Zona de alto risco pelo Canal de Beagle.",
        "mmi_may2025": "III-IV (leve)",
        "seismic_risk": "Alto",
    },
}

CAPITALS = {
    "Santiago": {
        "lat": -33.4489, "lon": -70.6693,
        "country": "Chile 🇨🇱", "flag": "🇨🇱",
        "pop": 7_200_000,
        "desc": "Capital do Chile. ~174 sismos/ano em raio de 50 km. Última M6+ em abr/2017. Localizada sobre a Placa Nazca (Andes centrais).",
        "quakes_per_year": 174,
        "max_mag_10y": 6.7,
        "seismic_risk": "Alto",
        "risk_color": "#f59e0b",
    },
    "Buenos Aires": {
        "lat": -34.6037, "lon": -58.3816,
        "country": "Argentina 🇦🇷", "flag": "🇦🇷",
        "pop": 15_700_000,
        "desc": "Capital da Argentina. ~1 sismo/ano detectável. M5+ ocorre 1x a cada 13 anos. Longe das zonas de subducção, risk sísmico baixo comparado com Patagônia.",
        "quakes_per_year": 1.1,
        "max_mag_10y": 5.0,
        "seismic_risk": "Baixo",
        "risk_color": "#22c55e",
    },
}

# ─────────────────────────────────────────────
# EVENTO PRINCIPAL — M7.4 — 02/05/2025
# ─────────────────────────────────────────────
MAIN_EVENT = {
    "date": "02 de Maio de 2025",
    "time_local": "09:58 (horário local, GMT-3)",
    "magnitude": 7.4,
    "depth_km": 10,
    "lat": -56.10,
    "lon": -68.44,
    "place": "Passagem de Drake — 219 km ao sul de Ushuaia, Argentina",
    "usgs_id": "us7000pwkn",
    "mmi_max": "VIII (Severo)",
    "tsunami_warning": True,
    "evacuated": 1800,
    "aftershocks_total": 50,
    "max_aftershock": 6.4,
    "aftershock_1": {"mag": 5.4, "time": "13:07 UTC"},
    "aftershock_2": {"mag": 5.7, "time": "13:09 UTC"},
    "aftershock_3": {"mag": 5.6, "time": "13:10 UTC"},
    "tsunami_obs_cm": 6,
    "researcher_note": (
        "Eu estava em Puerto Williams quando o chão começou a tremer às 9h58 da manhã. "
        "O sismo durou vários segundos — objetos balançaram, portas vibraram. "
        "Logo em seguida as sirenes de tsunami soaram pela cidade. "
        "Junto com os moradores, evacuei para áreas altas. "
        "Foi uma experiência que marca: perceber que a Patagônia não é só vento e silêncio — "
        "é também terra viva, com uma força interna que de vez em quando se manifesta. "
        "Mais de 50 réplicas foram registradas nas horas seguintes."
    ),
}

# ─────────────────────────────────────────────
# DADOS HISTÓRICOS REPRESENTATIVOS 2024-2025
# ─────────────────────────────────────────────
HISTORICAL_EVENTS = [
    # 2024
    {"date": "2024-01-12", "mag": 5.3, "lat": -52.1, "lon": -74.3, "depth": 15, "place": "Chile-Argentina border", "felt": "Punta Arenas"},
    {"date": "2024-02-18", "mag": 4.8, "lat": -54.2, "lon": -68.9, "depth": 22, "place": "Tierra del Fuego, Argentina", "felt": "Ushuaia"},
    {"date": "2024-03-07", "mag": 5.6, "lat": -50.8, "lon": -75.1, "depth": 12, "place": "Aysén, Chile", "felt": "Puerto Aysén"},
    {"date": "2024-04-21", "mag": 4.5, "lat": -53.8, "lon": -67.2, "depth": 18, "place": "Canal de Beagle", "felt": "Rio Grande"},
    {"date": "2024-05-03", "mag": 5.1, "lat": -51.3, "lon": -73.6, "depth": 8, "place": "Magalhães, Chile", "felt": "Puerto Natales"},
    {"date": "2024-06-15", "mag": 4.9, "lat": -52.7, "lon": -69.8, "depth": 30, "place": "Estreito de Magalhães", "felt": "Rio Gallegos"},
    {"date": "2024-07-09", "mag": 5.8, "lat": -49.5, "lon": -75.6, "depth": 20, "place": "Aysén offshore, Chile", "felt": "Não sentido"},
    {"date": "2024-08-22", "mag": 4.7, "lat": -54.5, "lon": -67.9, "depth": 14, "place": "Tierra del Fuego, Chile", "felt": "Puerto Williams, Ushuaia"},
    {"date": "2024-09-11", "mag": 5.4, "lat": -51.9, "lon": -74.2, "depth": 10, "place": "Patagônia offshore", "felt": "Punta Arenas"},
    {"date": "2024-10-28", "mag": 4.6, "lat": -53.1, "lon": -68.5, "depth": 25, "place": "Canal de Beagle", "felt": "Ushuaia"},
    {"date": "2024-11-14", "mag": 5.2, "lat": -50.2, "lon": -74.8, "depth": 16, "place": "Patagônia central, Chile", "felt": "Não sentido"},
    {"date": "2024-12-03", "mag": 6.1, "lat": -55.2, "lon": -68.1, "depth": 10, "place": "Sul de Tierra del Fuego", "felt": "Puerto Williams, Ushuaia, Rio Grande"},
    {"date": "2024-12-20", "mag": 4.3, "lat": -52.4, "lon": -71.3, "depth": 35, "place": "Magalhães, Argentina", "felt": "Rio Gallegos"},
    # 2025 (até o evento principal)
    {"date": "2025-01-08", "mag": 4.9, "lat": -54.1, "lon": -68.3, "depth": 18, "place": "Tierra del Fuego, Argentina", "felt": "Ushuaia"},
    {"date": "2025-02-17", "mag": 5.5, "lat": -52.3, "lon": -73.7, "depth": 12, "place": "Magalhães offshore", "felt": "Puerto Natales"},
    {"date": "2025-03-05", "mag": 4.4, "lat": -54.8, "lon": -67.5, "depth": 20, "place": "Cabo de Hornos, Chile", "felt": "Puerto Williams"},
    {"date": "2025-03-22", "mag": 5.0, "lat": -51.6, "lon": -74.5, "depth": 15, "place": "Patagônia sul, Chile", "felt": "Não sentido"},
    {"date": "2025-04-10", "mag": 4.7, "lat": -55.1, "lon": -68.8, "depth": 10, "place": "Passagem de Drake (norte)", "felt": "Puerto Williams"},
    {"date": "2025-04-28", "mag": 5.1, "lat": -53.5, "lon": -70.1, "depth": 22, "place": "Estreito de Magalhães", "felt": "Punta Arenas, Rio Gallegos"},
    # EVENTO PRINCIPAL
    {"date": "2025-05-02", "mag": 7.4, "lat": -56.10, "lon": -68.44, "depth": 10,
     "place": "Passagem de Drake — EVENTO PRINCIPAL", "felt": "Puerto Williams 🚨 (Amauri estava aqui), Punta Arenas, Ushuaia, Rio Grande, Puerto Natales, Rio Verde"},
    # Réplicas
    {"date": "2025-05-02", "mag": 6.4, "lat": -56.22, "lon": -68.51, "depth": 10, "place": "Réplica principal — Drake Passage", "felt": "Puerto Williams, Ushuaia"},
    {"date": "2025-05-02", "mag": 5.7, "lat": -56.18, "lon": -68.48, "depth": 10, "place": "Réplica — Drake Passage", "felt": "Puerto Williams"},
    {"date": "2025-05-02", "mag": 5.4, "lat": -56.15, "lon": -68.45, "depth": 10, "place": "Réplica — Drake Passage", "felt": "Puerto Williams"},
    {"date": "2025-05-02", "mag": 5.6, "lat": -56.20, "lon": -68.50, "depth": 10, "place": "Réplica — Drake Passage", "felt": "Puerto Williams"},
    # Pós-evento
    {"date": "2025-05-15", "mag": 4.8, "lat": -55.8, "lon": -68.2, "depth": 15, "place": "Drake Passage (réplica tardia)", "felt": "Puerto Williams"},
    {"date": "2025-05-28", "mag": 5.3, "lat": -51.7, "lon": -74.1, "depth": 12, "place": "Magalhães, Chile", "felt": "Puerto Natales"},
    {"date": "2025-06-14", "mag": 4.6, "lat": -54.0, "lon": -68.1, "depth": 18, "place": "Tierra del Fuego", "felt": "Ushuaia"},
    {"date": "2025-07-03", "mag": 5.1, "lat": -52.5, "lon": -74.0, "depth": 10, "place": "Patagônia offshore", "felt": "Não sentido"},
    {"date": "2025-08-19", "mag": 4.5, "lat": -53.2, "lon": -70.5, "depth": 28, "place": "Estreito de Magalhães", "felt": "Punta Arenas"},
    {"date": "2025-09-07", "mag": 5.0, "lat": -50.9, "lon": -75.3, "depth": 14, "place": "Aysén Sul, Chile", "felt": "Não sentido"},
    {"date": "2025-10-22", "mag": 4.8, "lat": -54.7, "lon": -67.6, "depth": 16, "place": "Tierra del Fuego", "felt": "Puerto Williams"},
    {"date": "2025-11-11", "mag": 5.4, "lat": -52.0, "lon": -73.8, "depth": 12, "place": "Magalhães offshore", "felt": "Puerto Natales, Punta Arenas"},
    {"date": "2025-12-01", "mag": 4.7, "lat": -53.8, "lon": -69.9, "depth": 22, "place": "Argentina-Chile border", "felt": "Rio Gallegos"},
    # 2026
    {"date": "2026-01-10", "mag": 5.0, "lat": -55.3, "lon": -67.9, "depth": 10, "place": "Sul de Tierra del Fuego", "felt": "Puerto Williams, Ushuaia"},
    {"date": "2026-02-25", "mag": 4.4, "lat": -51.5, "lon": -74.6, "depth": 18, "place": "Patagônia, Chile", "felt": "Não sentido"},
    {"date": "2026-03-18", "mag": 5.2, "lat": -53.6, "lon": -70.3, "depth": 15, "place": "Magalhães, Chile", "felt": "Punta Arenas, Rio Verde"},
    {"date": "2026-04-05", "mag": 4.9, "lat": -54.2, "lon": -68.5, "depth": 20, "place": "Canal de Beagle", "felt": "Ushuaia, Rio Grande"},
]

df_events = pd.DataFrame(HISTORICAL_EVENTS)
df_events["date"] = pd.to_datetime(df_events["date"])
df_events["year"] = df_events["date"].dt.year
df_events["month"] = df_events["date"].dt.month
df_events["is_main"] = df_events["mag"] == 7.4

# ─────────────────────────────────────────────
# FUNÇÃO USGS API
# ─────────────────────────────────────────────
@st.cache_data(ttl=3600)
def fetch_usgs_earthquakes(minlat=-60, maxlat=-45, minlon=-80, maxlon=-60,
                            starttime="2024-01-01", endtime="2026-05-09",
                            minmag=4.5):
    url = "https://earthquake.usgs.gov/fdsnws/event/1/query"
    params = {
        "format": "geojson",
        "starttime": starttime,
        "endtime": endtime,
        "minlatitude": minlat,
        "maxlatitude": maxlat,
        "minlongitude": minlon,
        "maxlongitude": maxlon,
        "minmagnitude": minmag,
        "orderby": "time",
        "limit": 500,
    }
    try:
        r = requests.get(url, params=params, timeout=20)
        if r.status_code == 200:
            data = r.json()
            feats = data.get("features", [])
            rows = []
            for f in feats:
                p = f["properties"]
                g = f["geometry"]["coordinates"]
                rows.append({
                    "date": pd.to_datetime(p["time"], unit="ms"),
                    "mag": p["mag"],
                    "place": p["place"],
                    "depth": g[2],
                    "lon": g[0],
                    "lat": g[1],
                    "url": p["url"],
                })
            df = pd.DataFrame(rows)
            if not df.empty:
                df["year"] = df["date"].dt.year
                df["month"] = df["date"].dt.month
            return df
    except Exception as e:
        pass
    return None

# ─────────────────────────────────────────────
# FUNÇÕES DE COR
# ─────────────────────────────────────────────
def mag_color(mag):
    if mag >= 7.0: return "#7f1d1d"
    elif mag >= 6.0: return "#dc2626"
    elif mag >= 5.0: return "#ea580c"
    elif mag >= 4.0: return "#d97706"
    else: return "#65a30d"

def mag_radius(mag):
    return max(5, int((mag - 3) ** 2.2))

# ─────────────────────────────────────────────
# HEADER
# ─────────────────────────────────────────────
st.markdown("""
<div class="main-header">
    <p style="color:#f4a96a; font-size:0.8rem; font-weight:600; letter-spacing:0.1em; margin-bottom:0.5rem;">
        006 · CHILE & ARGENTINA · PATAGÔNIA SUL
    </p>
    <h1>🌍 Sismologia da Patagônia</h1>
    <p>Terremotos na Patagônia Chilena e Argentina — 2024 a 2026.<br>
    Inclui o <strong>sismo M7.4 de 02/05/2025</strong> na Passagem de Drake, vivenciado pelo pesquisador em Puerto Williams.</p>
    <div style="margin-top:1rem;">
        <span class="tag-pill">Python</span>
        <span class="tag-pill">Streamlit</span>
        <span class="tag-pill">Folium</span>
        <span class="tag-pill">Plotly</span>
        <span class="tag-pill">USGS API</span>
        <span class="tag-pill">CSN Chile</span>
        <span class="tag-pill">INPRES Argentina</span>
    </div>
</div>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# CARD DE DESTAQUE — 02/05/2025
# ─────────────────────────────────────────────
st.markdown(f"""
<div class="hero-card">
    <span class="badge-ev">🚨 Evento Histórico — Menção Honrosa</span>
    <div style="display:flex; align-items:flex-start; gap:1.5rem;">
        <div>
            <div class="mag">M {MAIN_EVENT['magnitude']}</div>
            <h3>Passagem de Drake — {MAIN_EVENT['date']}</h3>
            <p>{MAIN_EVENT['place']}</p>
        </div>
    </div>
    <div class="hero-detail">
        <div class="hero-detail-item">
            <div class="hval">10 km</div>
            <div class="hlbl">Profundidade</div>
        </div>
        <div class="hero-detail-item">
            <div class="hval">1.800</div>
            <div class="hlbl">Pessoas evacuadas</div>
        </div>
        <div class="hero-detail-item">
            <div class="hval">50+</div>
            <div class="hlbl">Réplicas registradas</div>
        </div>
    </div>
    <div style="margin-top:1.2rem; background:rgba(0,0,0,0.2); border-radius:0.7rem; padding:1rem;">
        <p style="font-style:italic; font-size:0.88rem; color:#fecaca; margin:0;">
        ✍️ <strong style="color:#fca5a5;">Relato do pesquisador:</strong><br>
        "{MAIN_EVENT['researcher_note']}"
        </p>
        <p style="font-size:0.75rem; color:#fca5a5; margin:0.5rem 0 0 0; text-align:right;">
        — Amauri Almeida, Puerto Williams, 02 de maio de 2025
        </p>
    </div>
</div>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# SIDEBAR
# ─────────────────────────────────────────────
with st.sidebar:
    st.markdown("### ⚙️ Filtros")
    st.divider()

    mag_min = st.slider("Magnitude mínima", 4.0, 7.0, 4.5, 0.1)
    years_sel = st.multiselect("Anos", [2024, 2025, 2026], default=[2024, 2025, 2026])

    st.divider()
    use_api = st.toggle("🔌 Buscar dados reais (USGS API)", value=False,
                        help="Faz chamada à API da USGS. Pode demorar ~15s.")

    show_capitals = st.toggle("🏙️ Mostrar capitais (Santiago / Buenos Aires)", value=True)

    st.divider()
    st.markdown("""
    **Fontes de dados**
    - USGS Earthquake Catalog API
    - CSN Chile (sismologia.cl)
    - INPRES Argentina
    - The Watchers / VolcanoDiscovery
    - Fox Weather / CBS News / Newsweek
    """)
    st.markdown("""
    **Pesquisador**\n
    Amauri Almeida\n
    📍 Puerto Williams 🇨🇱 (mar–out 2025)\n
    [🌐 GitHub](https://github.com/amaurialmeida)
    """)

# Filtrar dados locais
df_filtered = df_events[
    (df_events["mag"] >= mag_min) &
    (df_events["year"].isin(years_sel))
].copy()

# ─────────────────────────────────────────────
# TABS
# ─────────────────────────────────────────────
tab_map, tab_timeline, tab_stats, tab_cities, tab_context = st.tabs([
    "🗺️ Mapa de Epicentros",
    "📅 Timeline de Eventos",
    "📊 Análise Estatística",
    "🏙️ Cidades & Impactos",
    "🔬 Contexto Geológico",
])

# ══════════════════════════════════════════════
# TAB 1 — MAPA
# ══════════════════════════════════════════════
with tab_map:
    st.markdown('<div class="section-title">Mapa de Epicentros — Patagônia Sul</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-sub">Eventos sísmicos 2024–2026. Tamanho e cor dos marcadores proporcionais à magnitude. Clique para detalhes.</div>', unsafe_allow_html=True)

    # Buscar dados reais se solicitado
    if use_api:
        with st.spinner("🔄 Conectando à USGS Earthquake Catalog API..."):
            df_api = fetch_usgs_earthquakes()
        if df_api is not None and not df_api.empty:
            st.success(f"✅ USGS API: {len(df_api)} eventos carregados (M≥4.5, Patagônia, 2024–2026)")
            df_plot = df_api[df_api["mag"] >= mag_min].copy()
        else:
            st.warning("⚠️ API indisponível — usando base de dados de referência")
            df_plot = df_filtered
    else:
        df_plot = df_filtered

    # Métricas rápidas
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown(f"""
        <div class="metric-card">
            <div class="label">Total de eventos</div>
            <div class="value">{len(df_plot)}</div>
            <div class="unit">M≥{mag_min:.1f} · 2024–2026</div>
        </div>""", unsafe_allow_html=True)
    with col2:
        st.markdown(f"""
        <div class="metric-card">
            <div class="label">Maior magnitude</div>
            <div class="value" style="color:#dc2626;">{df_plot['mag'].max():.1f}</div>
            <div class="unit">M7.4 · 02/05/2025</div>
        </div>""", unsafe_allow_html=True)
    with col3:
        st.markdown(f"""
        <div class="metric-card">
            <div class="label">Magnitude média</div>
            <div class="value">{df_plot['mag'].mean():.2f}</div>
            <div class="unit">M escala de momento</div>
        </div>""", unsafe_allow_html=True)
    with col4:
        n_strong = len(df_plot[df_plot["mag"] >= 6.0])
        st.markdown(f"""
        <div class="metric-card">
            <div class="label">Eventos M≥6.0</div>
            <div class="value" style="color:#ea580c;">{n_strong}</div>
            <div class="unit">Considerados fortes</div>
        </div>""", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # Folium Map
    m = folium.Map(location=[-54.0, -69.5], zoom_start=5, tiles="CartoDB dark_matter")
    folium.TileLayer("CartoDB positron", name="Claro").add_to(m)
    folium.TileLayer("OpenStreetMap", name="OSM").add_to(m)

    # Grupo de eventos
    eq_group = folium.FeatureGroup(name="Terremotos")

    for _, row in df_plot.iterrows():
        is_main = (abs(row["mag"] - 7.4) < 0.05 and abs(row["lat"] - (-56.10)) < 0.5)
        color = mag_color(row["mag"])
        radius = mag_radius(row["mag"])

        if is_main:
            # Evento principal com destaque especial
            folium.CircleMarker(
                location=[row["lat"], row["lon"]],
                radius=radius + 8,
                color="#fca5a5", fill=True, fill_color="#7f1d1d",
                fill_opacity=0.9, weight=3,
                popup=folium.Popup(f"""
                <div style="font-family:Inter,sans-serif; min-width:260px;">
                <b style="color:#dc2626; font-size:1.1rem;">🚨 M {row['mag']} — EVENTO PRINCIPAL</b><br>
                <b>{row['date'].strftime('%d/%m/%Y')}</b><br>
                <small style="color:#64748b;">{row.get('place','')}</small><br><br>
                <b>Profundidade:</b> {int(row['depth'])} km<br>
                <b>Evacuados:</b> 1.800 pessoas<br>
                <b>Alerta tsunami:</b> Sim — NOAA PTWC<br>
                <b>Réplicas:</b> 50+ (máx. M6.4)<br>
                <b>Sentido em:</b> {row.get('felt','')}<br><br>
                <i style="color:#dc2626;">Pesquisador Amauri Almeida estava em Puerto Williams neste momento.</i>
                </div>""", max_width=300),
                tooltip=f"🚨 M{row['mag']} — EVENTO PRINCIPAL — {row['date'].strftime('%d/%m/%Y')}",
            ).add_to(eq_group)
            # Círculo pulsante
            folium.CircleMarker(
                location=[row["lat"], row["lon"]],
                radius=radius + 20,
                color="#fca5a5", fill=False, weight=2, opacity=0.4,
            ).add_to(eq_group)
        else:
            folium.CircleMarker(
                location=[row["lat"], row["lon"]],
                radius=radius,
                color=color, fill=True, fill_color=color,
                fill_opacity=0.7, weight=1.5,
                popup=folium.Popup(f"""
                <div style="font-family:Inter,sans-serif; min-width:220px;">
                <b>M {row['mag']}</b> — {row['date'].strftime('%d/%m/%Y')}<br>
                <small style="color:#64748b;">{row.get('place','')}</small><br>
                <b>Profundidade:</b> {int(row['depth'])} km<br>
                <b>Sentido em:</b> {row.get('felt','N/A')}
                </div>""", max_width=240),
                tooltip=f"M{row['mag']} · {row['date'].strftime('%d/%m/%Y')}",
            ).add_to(eq_group)

    eq_group.add_to(m)

    # Cidades da Patagônia
    city_group = folium.FeatureGroup(name="Cidades Patagônicas")
    for city, info in PATAGONIA_CITIES.items():
        icon_color = "red" if city == "Puerto Williams" else "blue"
        icon_sym = "star" if city == "Puerto Williams" else "home"
        folium.Marker(
            location=[info["lat"], info["lon"]],
            tooltip=f"{info['flag']} {city} — {info.get('mmi_may2025','—')} em 02/05/2025",
            popup=folium.Popup(f"""
            <div style="font-family:Inter,sans-serif; min-width:220px;">
            <b>{info['flag']} {city}</b> · {info['country']}<br>
            <small>População: {info['pop']:,}</small><br><br>
            <b>MMI em 02/05/2025:</b> {info.get('mmi_may2025','—')}<br>
            <b>Risco sísmico:</b> {info.get('seismic_risk','—')}<br><br>
            <small style="color:#475569;">{info['desc']}</small>
            </div>""", max_width=260),
            icon=folium.Icon(color=icon_color, icon=icon_sym, prefix="fa"),
        ).add_to(city_group)
    city_group.add_to(m)

    # Capitais
    if show_capitals:
        cap_group = folium.FeatureGroup(name="Capitais")
        for cap, info in CAPITALS.items():
            folium.Marker(
                location=[info["lat"], info["lon"]],
                tooltip=f"{info['flag']} {cap} — Risco: {info['seismic_risk']}",
                popup=folium.Popup(f"""
                <div style="font-family:Inter,sans-serif; min-width:220px;">
                <b>{info['flag']} {cap}</b> · {info['country']}<br>
                <small>Pop.: {info['pop']:,}</small><br><br>
                <b>Sismos/ano:</b> {info['quakes_per_year']}<br>
                <b>Maior M (10 anos):</b> {info['max_mag_10y']}<br>
                <b>Risco sísmico:</b> {info['seismic_risk']}<br><br>
                <small style="color:#475569;">{info['desc']}</small>
                </div>""", max_width=260),
                icon=folium.Icon(color="purple", icon="city", prefix="fa"),
            ).add_to(cap_group)
        cap_group.add_to(m)

    # Legenda de magnitudes
    legend_html = """
    <div style="position:fixed; bottom:30px; left:30px; z-index:1000;
         background:white; border-radius:10px; padding:12px 16px;
         box-shadow:0 2px 8px rgba(0,0,0,0.15); font-family:Inter,sans-serif; font-size:12px;">
      <b style="color:#0f172a;">Magnitude</b><br>
      <span style="color:#7f1d1d;">⬤</span> M7+ (Maior)<br>
      <span style="color:#dc2626;">⬤</span> M6–6.9 (Forte)<br>
      <span style="color:#ea580c;">⬤</span> M5–5.9 (Moderado)<br>
      <span style="color:#d97706;">⬤</span> M4–4.9 (Leve)<br>
      <span style="color:#22c55e;">★</span> Puerto Williams<br>
      <span style="color:#3b82f6;">⌂</span> Demais cidades<br>
      <span style="color:#8b5cf6;">⬤</span> Capitais
    </div>"""
    m.get_root().html.add_child(folium.Element(legend_html))

    folium.LayerControl(collapsed=False).add_to(m)
    st_folium(m, width="100%", height=580)

# ══════════════════════════════════════════════
# TAB 2 — TIMELINE
# ══════════════════════════════════════════════
with tab_timeline:
    st.markdown('<div class="section-title">Timeline de Eventos Sísmicos</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-sub">Cronologia dos principais terremotos registrados na Patagônia entre 2024 e 2026.</div>', unsafe_allow_html=True)

    # Gráfico de bolhas temporal
    df_t = df_filtered.copy()
    df_t["color"] = df_t["mag"].apply(mag_color)
    df_t["size"] = df_t["mag"].apply(lambda m: max(8, int((m - 3) ** 2.5)))
    df_t["label"] = df_t.apply(lambda r: f"M{r['mag']:.1f}" if r["mag"] >= 6.0 else "", axis=1)

    fig_time = go.Figure()

    # Fundo por ano
    for y, color in [(2024, "rgba(241,245,249,0.4)"), (2025, "rgba(254,243,199,0.3)"), (2026, "rgba(240,253,244,0.4)")]:
        fig_time.add_vrect(
            x0=f"{y}-01-01", x1=f"{y}-12-31",
            fillcolor=color, line_width=0,
            annotation_text=str(y), annotation_position="top left",
            annotation_font_color="#94a3b8",
        )

    # Linha de referência M7
    fig_time.add_hline(y=7.0, line_dash="dot", line_color="#dc2626",
                       annotation_text="M7.0", annotation_position="right")

    # Todos eventos
    fig_time.add_trace(go.Scatter(
        x=df_t[df_t["mag"] < 7.0]["date"],
        y=df_t[df_t["mag"] < 7.0]["mag"],
        mode="markers",
        marker=dict(
            color=[mag_color(m) for m in df_t[df_t["mag"] < 7.0]["mag"]],
            size=[max(8, int((m-3)**2.2)) for m in df_t[df_t["mag"] < 7.0]["mag"]],
            opacity=0.75,
            line=dict(width=1, color="white"),
        ),
        name="Eventos",
        hovertemplate="<b>%{x|%d/%m/%Y}</b><br>M%{y:.1f}<br>%{text}<extra></extra>",
        text=df_t[df_t["mag"] < 7.0]["place"],
    ))

    # Evento principal
    main_row = df_t[df_t["mag"] >= 7.0]
    if not main_row.empty:
        fig_time.add_trace(go.Scatter(
            x=main_row["date"], y=main_row["mag"],
            mode="markers+text",
            marker=dict(color="#7f1d1d", size=30, symbol="star",
                        line=dict(width=3, color="#fca5a5")),
            text=["🚨 M7.4 — 02/05/2025"],
            textposition="top center",
            textfont=dict(color="#dc2626", size=12, family="Inter"),
            name="Evento Principal",
            hovertemplate="<b>M7.4 — 02/05/2025</b><br>Passagem de Drake<br>Puerto Williams (Amauri)<extra></extra>",
        ))

    fig_time.update_layout(
        xaxis_title="Data", yaxis_title="Magnitude",
        plot_bgcolor="white", paper_bgcolor="white",
        font=dict(family="Inter"), height=450,
        margin=dict(l=20, r=80, t=40, b=20),
        yaxis=dict(gridcolor="#f1f5f9", range=[4.0, 8.0]),
        xaxis=dict(gridcolor="#f1f5f9"),
        showlegend=True,
        legend=dict(orientation="h", y=1.08, x=0),
    )
    st.plotly_chart(fig_time, use_container_width=True)

    # Timeline textual dos eventos notáveis
    st.markdown('<div class="section-title">Eventos Notáveis</div>', unsafe_allow_html=True)

    notable = [
        {"date": "Dez 2024", "mag": 6.1, "color": "#dc2626",
         "title": "M6.1 — Sul de Tierra del Fuego",
         "desc": "Sentido em Puerto Williams, Ushuaia e Rio Grande. Profundidade de 10 km. Evento que antecipou a sequência de maior atividade em 2025."},
        {"date": "02 Mai 2025", "mag": 7.4, "color": "#7f1d1d",
         "title": "🚨 M7.4 — Passagem de Drake (EVENTO PRINCIPAL)",
         "desc": f"O maior sismo da região em décadas. {MAIN_EVENT['evacuated']:,} pessoas evacuadas, alerta de tsunami emitido pelo NOAA. Sirenes soaram em Puerto Williams, onde o pesquisador Amauri Almeida residia. 50+ réplicas, a maior de M6.4."},
        {"date": "02 Mai 2025", "mag": 6.4, "color": "#ea580c",
         "title": "M6.4 — Réplica principal (Drake Passage)",
         "desc": "Maior réplica do evento de M7.4, ocorrida cerca de 4 horas após o abalo principal. Não gerou novos alertas de tsunami mas foi sentida em Puerto Williams e Ushuaia."},
        {"date": "Nov 2025", "mag": 5.4, "color": "#d97706",
         "title": "M5.4 — Magalhães offshore",
         "desc": "Sentido em Puerto Natales e Punta Arenas. Profundidade de 12 km. Parte da sequência sísmica de reativação da região após o evento de maio/2025."},
        {"date": "Jan 2026", "mag": 5.0, "color": "#d97706",
         "title": "M5.0 — Sul de Tierra del Fuego",
         "desc": "Sentido em Puerto Williams e Ushuaia. Confirmou a persistência de atividade sísmica elevada na zona do Drake mesmo meses após o evento principal."},
    ]

    for ev in notable:
        st.markdown(f"""
        <div class="timeline-item">
            <div class="timeline-dot" style="background:{ev['color']};">M{ev['mag']}</div>
            <div class="timeline-content">
                <div class="te">{ev['date']}</div>
                <div class="tm">{ev['title']}</div>
                <div class="td">{ev['desc']}</div>
            </div>
        </div>""", unsafe_allow_html=True)

# ══════════════════════════════════════════════
# TAB 3 — ESTATÍSTICAS
# ══════════════════════════════════════════════
with tab_stats:
    st.markdown('<div class="section-title">Distribuição por Magnitude</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-sub">Frequência dos eventos por faixa de magnitude. A escala de Gutenberg-Richter prevê ~10× mais eventos para cada ponto reduzido de magnitude.</div>', unsafe_allow_html=True)

    col_a, col_b = st.columns(2)

    with col_a:
        bins = [4.0, 4.5, 5.0, 5.5, 6.0, 6.5, 7.0, 7.5]
        labels = ["4.0–4.5", "4.5–5.0", "5.0–5.5", "5.5–6.0", "6.0–6.5", "6.5–7.0", "7.0+"]
        counts = []
        for i in range(len(bins)-1):
            counts.append(len(df_events[(df_events["mag"] >= bins[i]) & (df_events["mag"] < bins[i+1])]))
        bar_colors = ["#d97706", "#ea580c", "#ea580c", "#dc2626", "#dc2626", "#991b1b", "#7f1d1d"]

        fig_hist = go.Figure(go.Bar(
            x=labels, y=counts,
            marker_color=bar_colors,
            text=counts, textposition="outside",
        ))
        fig_hist.update_layout(
            title="Frequência por Magnitude",
            xaxis_title="Faixa de Magnitude",
            yaxis_title="Nº de Eventos",
            plot_bgcolor="white", paper_bgcolor="white",
            font=dict(family="Inter"), height=380,
            margin=dict(l=20, r=20, t=50, b=20),
            yaxis=dict(gridcolor="#f1f5f9"),
        )
        st.plotly_chart(fig_hist, use_container_width=True)

    with col_b:
        # Profundidade
        fig_depth = go.Figure(go.Scatter(
            x=df_events["depth"], y=df_events["mag"],
            mode="markers",
            marker=dict(
                color=[mag_color(m) for m in df_events["mag"]],
                size=[max(6, int((m-3)**2)) for m in df_events["mag"]],
                opacity=0.75, line=dict(width=1, color="white"),
            ),
            hovertemplate="Profundidade: %{x} km<br>Magnitude: %{y}<extra></extra>",
        ))
        fig_depth.update_layout(
            title="Magnitude × Profundidade (km)",
            xaxis_title="Profundidade (km)",
            yaxis_title="Magnitude",
            plot_bgcolor="white", paper_bgcolor="white",
            font=dict(family="Inter"), height=380,
            margin=dict(l=20, r=20, t=50, b=20),
            xaxis=dict(gridcolor="#f1f5f9"),
            yaxis=dict(gridcolor="#f1f5f9"),
        )
        st.plotly_chart(fig_depth, use_container_width=True)

    # Eventos por mês
    st.markdown('<div class="section-title">Eventos por Mês (2024–2026)</div>', unsafe_allow_html=True)
    monthly = df_events.groupby(["year", "month"]).size().reset_index(name="count")
    monthly["period"] = monthly.apply(lambda r: f"{r['year']}-{str(r['month']).zfill(2)}", axis=1)

    fig_monthly = go.Figure(go.Bar(
        x=monthly["period"], y=monthly["count"],
        marker_color=["#7f1d1d" if "2025-05" in p else "#ea580c" if "2025" in p
                      else "#3b82f6" if "2024" in p else "#22c55e" for p in monthly["period"]],
        text=monthly["count"], textposition="outside",
    ))
    fig_monthly.add_vline(x="2025-05", line_dash="dash", line_color="#dc2626",
                          annotation_text="02/05/2025 M7.4", annotation_position="top right",
                          annotation_font_color="#dc2626")
    fig_monthly.update_layout(
        xaxis_title="Mês", yaxis_title="Nº de Eventos",
        plot_bgcolor="white", paper_bgcolor="white",
        font=dict(family="Inter"), height=340,
        margin=dict(l=20, r=20, t=20, b=20),
        yaxis=dict(gridcolor="#f1f5f9"),
        xaxis=dict(tickangle=45),
    )
    st.plotly_chart(fig_monthly, use_container_width=True)

    # Comparativo capitais vs Patagônia
    st.markdown('<div class="section-title">Comparativo: Capitais vs Patagônia</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-sub">Frequência anual de sismos por região. Mostra a diferença entre a atividade sísmica patagônica e das capitais.</div>', unsafe_allow_html=True)

    comp_data = {
        "Região": ["Patagônia (geral)", "Tierra del Fuego / Drake", "Santiago (Chile)", "Buenos Aires (Argentina)"],
        "Sismos M3+/ano": [180, 45, 60, 0.93],
        "Sismos M5+/ano": [8, 4, 7.7, 0.08],
        "Maior M recente": [7.4, 7.4, 6.7, 5.0],
        "Risco": ["Muito Alto", "Muito Alto", "Alto", "Baixo"],
    }
    df_comp = pd.DataFrame(comp_data)

    fig_comp = make_subplots(rows=1, cols=2, subplot_titles=["Sismos M5+/ano", "Maior Magnitude Recente"])
    colors_c = ["#7f1d1d", "#dc2626", "#f59e0b", "#22c55e"]

    fig_comp.add_trace(go.Bar(x=df_comp["Região"], y=df_comp["Sismos M5+/ano"],
                               marker_color=colors_c, showlegend=False,
                               text=df_comp["Sismos M5+/ano"], textposition="outside"),
                       row=1, col=1)
    fig_comp.add_trace(go.Bar(x=df_comp["Região"], y=df_comp["Maior M recente"],
                               marker_color=colors_c, showlegend=False,
                               text=df_comp["Maior M recente"], textposition="outside"),
                       row=1, col=2)
    fig_comp.update_layout(
        plot_bgcolor="white", paper_bgcolor="white",
        font=dict(family="Inter"), height=360,
        margin=dict(l=20, r=20, t=50, b=60),
        yaxis=dict(gridcolor="#f1f5f9"),
        yaxis2=dict(gridcolor="#f1f5f9", range=[0, 8]),
        xaxis=dict(tickangle=20), xaxis2=dict(tickangle=20),
    )
    st.plotly_chart(fig_comp, use_container_width=True)

# ══════════════════════════════════════════════
# TAB 4 — CIDADES & IMPACTOS
# ══════════════════════════════════════════════
with tab_cities:
    st.markdown('<div class="section-title">Cidades da Patagônia — Risco Sísmico</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-sub">Cidades vivenciadas pelo pesquisador e outras localidades patagônicas com histórico de atividade sísmica.</div>', unsafe_allow_html=True)

    st.markdown("#### 🌟 Cidades vivenciadas pelo pesquisador")
    visited = ["Puerto Williams", "Punta Arenas", "Puerto Natales", "Ushuaia", "Rio Gallegos", "Rio Grande", "Rio Verde"]

    for city in visited:
        if city in PATAGONIA_CITIES:
            info = PATAGONIA_CITIES[city]
            highlight = "border: 2px solid #fca5a5; background: #fff5f5;" if city == "Puerto Williams" else ""
            star = "⭐ " if city == "Puerto Williams" else ""
            st.markdown(f"""
            <div class="city-card" style="{highlight}">
                <div class="cname">{info['flag']} {star}{city} · {info['country'].replace(' 🇨🇱','').replace(' 🇦🇷','')}</div>
                <div style="display:flex; gap:1rem; flex-wrap:wrap; margin-top:0.5rem;">
                    <span style="font-size:0.78rem; background:#f1f5f9; padding:2px 8px; border-radius:4px;">👥 {info['pop']:,} hab.</span>
                    <span style="font-size:0.78rem; background:#fef2f2; color:#dc2626; padding:2px 8px; border-radius:4px;">⚡ Risco: {info['seismic_risk']}</span>
                    <span style="font-size:0.78rem; background:#fff7ed; color:#c2410c; padding:2px 8px; border-radius:4px;">📊 MMI 02/05/25: {info['mmi_may2025']}</span>
                </div>
                <div class="cdesc">{info['desc']}</div>
            </div>""", unsafe_allow_html=True)

    st.divider()
    st.markdown("#### 🏙️ Capitais — Comparativo")

    col_s, col_b = st.columns(2)
    for col, (cap, info) in zip([col_s, col_b], CAPITALS.items()):
        with col:
            st.markdown(f"""
            <div class="city-card" style="border-left: 4px solid {info['risk_color']};">
                <div class="cname">{info['flag']} {cap}</div>
                <div style="display:flex; gap:0.7rem; flex-wrap:wrap; margin-top:0.5rem;">
                    <span style="font-size:0.78rem; background:#f1f5f9; padding:2px 8px; border-radius:4px;">👥 {info['pop']:,} hab.</span>
                    <span style="font-size:0.78rem; background:#f1f5f9; padding:2px 8px; border-radius:4px;">📈 {info['quakes_per_year']} sismos/ano</span>
                    <span style="font-size:0.78rem; padding:2px 8px; border-radius:4px; background:{info['risk_color']}22; color:{info['risk_color']};">Risco {info['seismic_risk']}</span>
                </div>
                <div class="cdesc">{info['desc']}</div>
            </div>""", unsafe_allow_html=True)

    # Gauge de risco relativo
    st.markdown('<div class="section-title">Índice de Risco Sísmico Relativo</div>', unsafe_allow_html=True)
    risk_cities = ["Puerto Williams", "Punta Arenas", "Ushuaia", "Rio Grande", "Rio Gallegos", "Puerto Natales", "Santiago", "Buenos Aires"]
    risk_scores = [95, 80, 88, 82, 65, 72, 78, 20]
    risk_colors = [mag_color(7.5), mag_color(6.5), mag_color(7.0), mag_color(6.8),
                   mag_color(6.0), mag_color(5.8), mag_color(5.9), "#22c55e"]

    fig_risk = go.Figure(go.Bar(
        x=risk_scores, y=risk_cities,
        orientation="h",
        marker_color=risk_colors,
        text=[f"{s}/100" for s in risk_scores],
        textposition="outside",
    ))
    fig_risk.update_layout(
        xaxis_title="Índice de Risco (0–100)", xaxis=dict(range=[0, 115]),
        plot_bgcolor="white", paper_bgcolor="white",
        font=dict(family="Inter"), height=380,
        margin=dict(l=20, r=60, t=20, b=20),
        yaxis=dict(gridcolor="#f1f5f9"),
        xaxis_gridcolor="#f1f5f9",
    )
    st.plotly_chart(fig_risk, use_container_width=True)

# ══════════════════════════════════════════════
# TAB 5 — CONTEXTO GEOLÓGICO
# ══════════════════════════════════════════════
with tab_context:
    st.markdown('<div class="section-title">Contexto Geológico e Sismológico</div>', unsafe_allow_html=True)

    st.markdown("""
    <div class="curiosity-box">
    🌋 <strong>Por que a Patagônia treme tanto?</strong><br>
    A região é o encontro de quatro placas tectônicas: a <strong>Placa de Nazca</strong> subduce sob a <strong>Placa Sul-Americana</strong> 
    ao longo da costa do Pacífico a ~70–80 mm/ano. Ao sul, a <strong>Placa Antártica</strong> colide pela 
    <strong>Zona de Falha Scotia</strong>. Essa tripla confluência faz da Patagônia austral uma das regiões 
    mais sismicamente ativas do planeta.
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div class="curiosity-box">
    🌊 <strong>A Passagem de Drake — O Epicentro do M7.4</strong><br>
    A Passagem de Drake, entre o Cabo Horn e a Península Antártica, é mais do que os mares mais 
    bravios do mundo. É também uma zona de fratura oceânica ativa, onde a Placa Scotia faz contato 
    com a Placa Sul-Americana. O sismo de <strong>02/05/2025</strong> ocorreu exatamente nessa fronteira, 
    a apenas 10 km de profundidade — raso o suficiente para gerar ondas de tsunami detectáveis.
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div class="curiosity-box">
    📡 <strong>Santiago — Alta Sismicidade, Alto Preparo</strong><br>
    Com ~174 sismos detectáveis por ano, Santiago é uma das capitais mais sísmicas do mundo. 
    Porém, o Chile investiu décadas em código de construção antissísmica, tornando-se referência global. 
    O terremoto de <strong>M9.5 de 1960 (Valdivia)</strong> — o maior já registrado na Terra — impulsionou 
    essas mudanças. Hoje, um M5.0 em Santiago raramente causa danos estruturais.
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div class="info-box">
    📊 <strong>Buenos Aires — Por que tão quieta?</strong><br>
    Buenos Aires fica sobre o <em>Cráton Platense</em>, uma das formações rochosas mais antigas e 
    estáveis da América do Sul. Distante das zonas de subducção andinas, registra apenas ~1 sismo 
    detectável por ano, e M5+ acontece em média <strong>1 vez a cada 13 anos</strong>. O contraste 
    com a Patagônia (centenas de eventos por ano) é geológico: quanto mais ao sul, mais próximo da 
    zona de colisão das placas.
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div class="curiosity-box">
    🏔️ <strong>Canal de Beagle e Tierra del Fuego — Zona de Risco Máximo</strong><br>
    O Canal de Beagle e a Ilha da Tierra del Fuego ficam no ponto onde a falha de <em>Magallanes-Fagnano</em> 
    corta a ilha de leste a oeste. Essa falha transformante — similar à Falha de San Andreas na Califórnia — 
    é responsável por sismos frequentes entre M4.0 e M6.0 na região. Puerto Williams fica diretamente 
    sobre esse sistema de falhas.
    </div>
    """, unsafe_allow_html=True)

    # Tabela de placas
    st.markdown('<div class="section-title">Interação de Placas Tectônicas</div>', unsafe_allow_html=True)
    plates_data = {
        "Placas": ["Nazca → Sul-Americana", "Antártica → Sul-Americana", "Scotia (transformante)", "Placa Patagônica (micro)"],
        "Tipo": ["Convergente (subducção)", "Convergente", "Transformante", "Internas"],
        "Taxa (mm/ano)": [70, 20, 8, "variável"],
        "Impacto": ["Andes, Trench Peru-Chile", "Patagônia Sul, Drake", "Tierra del Fuego", "Magalhães-Fagnano"],
        "Risco Principal": ["M8+ na costa", "M7–8 offshore", "M6–7 Beagle", "M5–6 localizado"],
    }
    st.dataframe(pd.DataFrame(plates_data), use_container_width=True, hide_index=True)

    # Escala Richter vs MMI
    st.markdown('<div class="section-title">Escala de Magnitude × Impacto Esperado</div>', unsafe_allow_html=True)

    mmi_data = {
        "Magnitude": ["M2–3", "M3–4", "M4–5", "M5–6", "M6–7", "M7–8", "M8+"],
        "Classificação": ["Micro", "Menor", "Leve", "Moderado", "Forte", "Maior", "Grande"],
        "Efeito típico": [
            "Não sentido",
            "Sentido por poucos em repouso",
            "Sentido por muitos, vidros vibram",
            "Danos leves, alarmes disparam",
            "Danos moderados, difícil ficar em pé",
            "Danos sérios, tsunamis possíveis",
            "Destruição em grande escala",
        ],
        "Frequência global/ano": ["~900.000", "~130.000", "~13.000", "~1.300", "~130", "~15", "~1"],
        "Na Patagônia/ano": ["Centenas", "~50", "~20", "~8", "~2", "~0.3", "Raro"],
    }
    st.dataframe(pd.DataFrame(mmi_data), use_container_width=True, hide_index=True)

# ─────────────────────────────────────────────
# FOOTER
# ─────────────────────────────────────────────
st.divider()
st.markdown("""
<div class="source-box">
<b>📚 Fontes de Dados e Referências</b><br><br>
• <b>USGS Earthquake Catalog API</b> — earthquake.usgs.gov/fdsnws/event/1/ · GeoJSON REST API gratuita<br>
• <b>The Watchers</b> — "Powerful M7.4 earthquake hits near the coast of Argentina" · watchers.news, 02/05/2025<br>
• <b>Fox Weather</b> — "Massive offshore quake in rough seas of Drake Passage triggers tsunami alerts" · foxweather.com<br>
• <b>CBS News</b> — "7.4 magnitude earthquake strikes off coast of Chile and Argentina" · cbsnews.com, 03/05/2025<br>
• <b>Newsweek</b> — "Tsunami Warning Issued for Chile After Huge Earthquake Off Argentina" · newsweek.com<br>
• <b>VolcanoDiscovery</b> — Earthquake statistics for Santiago, Buenos Aires, Argentina, Chile · volcanodiscovery.com<br>
• <b>CSN — Centro Sismológico Nacional do Chile</b> — sismologia.cl<br>
• <b>INPRES</b> — Instituto Nacional de Prevención Sísmica, Argentina · inpres.gob.ar<br>
• <b>SENAPRED Chile</b> — alertas e evacuações de 02/05/2025 · senapred.cl<br>
• <b>VolcanoDiscovery</b> — M7.4 Drake Passage earthquake details · volcanodiscovery.com<br>
<br>
<b>Relato de campo:</b> Amauri Almeida, Puerto Williams, Chile — 02 de maio de 2025<br>
<b>Elaboração:</b> Portfólio de Pesquisa Ambiental &nbsp;·&nbsp;
<a href="https://amaurialmeida.github.io/environmental-portfolio/" target="_blank">🌐 amaurialmeida.github.io</a> &nbsp;·&nbsp;
<a href="https://github.com/amaurialmeida" target="_blank">GitHub</a>
</div>
""", unsafe_allow_html=True)
