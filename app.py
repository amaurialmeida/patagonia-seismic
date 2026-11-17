import streamlit as st
import folium
from streamlit_folium import folium_static
import pandas as pd
import plotly.graph_objects as go
import numpy as np
import requests
import os
import io
from datetime import datetime, timedelta

from translations import TRANSLATIONS

st.set_page_config(
    page_title="Patagonia Seismic",
    page_icon="🌍",
    layout="wide"
)

# ============================================================
# SISTEMA DE IDIOMAS (10 idiomas)
# ============================================================
LANGS = [
    ("pt", "🇧🇷", "PT"), ("en", "🇺🇸", "EN"), ("es", "🇪🇸", "ES"),
    ("it", "🇮🇹", "IT"), ("fr", "🇫🇷", "FR"), ("de", "🇩🇪", "DE"),
    ("zh", "🇨🇳", "ZH"), ("ar", "🇸🇦", "AR"), ("el", "🇬🇷", "EL"),
    ("af", "🇿🇦", "AF"),
]
CODES = [c for c, _, _ in LANGS]
FLAGS = {c: f"{flag} {label}" for c, flag, label in LANGS}

DECIMAL = {"pt": ",", "en": ".", "es": ",", "it": ",", "fr": ",", "de": ",", "zh": ".", "ar": ".", "el": ",", "af": ","}
PLOTLY_SEP = {"pt": ",.", "en": ".,", "es": ",.", "it": ",.", "fr": ", ", "de": ",.", "zh": ".,", "ar": ".,", "el": ",.", "af": ", "}

def _initial_lang():
    q = st.query_params.get("lang")
    if isinstance(q, list):
        q = q[0] if q else None
    return q if q in CODES else "pt"

if "lang" not in st.session_state:
    st.session_state.lang = _initial_lang()

def render_lang_selector():
    try:
        escolha = st.pills(
            "Language", CODES, selection_mode="single",
            default=st.session_state.lang, format_func=lambda c: FLAGS[c],
            key="lang_pick", label_visibility="collapsed",
        )
    except AttributeError:
        escolha = st.radio(
            "Language", CODES, index=CODES.index(st.session_state.lang),
            format_func=lambda c: FLAGS[c], horizontal=True,
            key="lang_pick", label_visibility="collapsed",
        )
    if escolha and escolha != st.session_state.lang:
        st.session_state.lang = escolha
        st.query_params["lang"] = escolha
        st.rerun()

render_lang_selector()
LANG = st.session_state.lang
T = TRANSLATIONS[LANG]
RTL = LANG == "ar"

def fmt(x, nd=1):
    return f"{x:.{nd}f}".replace(".", DECIMAL[LANG])

def plot(fig):
    fig.update_layout(separators=PLOTLY_SEP[LANG])
    try:
        st.plotly_chart(fig, use_container_width=True)
    except TypeError:
        st.plotly_chart(fig, use_container_width=True)

# ── CIDADES MONITORADAS ───────────────────────────────────────
CITIES = [
    {"nome": "Santiago",       "pais": "🇨🇱 Chile",     "lat": -33.450, "lon": -70.670, "r": 300, "risco": "Alto",      "sismos_ano": 174},
    {"nome": "Buenos Aires",   "pais": "🇦🇷 Argentina", "lat": -34.615, "lon": -58.373, "r": 300, "risco": "Baixo",     "sismos_ano": 1.1},
    {"nome": "Punta Arenas",   "pais": "🇨🇱 Chile",     "lat": -53.163, "lon": -70.917, "r": 200, "risco": "Alto",      "sismos_ano": 18},
    {"nome": "Puerto Natales", "pais": "🇨🇱 Chile",     "lat": -51.729, "lon": -72.494, "r": 200, "risco": "Moderado-Alto","sismos_ano": 12},
    {"nome": "Puerto Williams","pais": "🇨🇱 Chile",     "lat": -54.935, "lon": -67.616, "r": 200, "risco": "Muito Alto", "sismos_ano": 35},
    {"nome": "Rio Grande",     "pais": "🇦🇷 Argentina", "lat": -53.788, "lon": -67.707, "r": 200, "risco": "Alto",      "sismos_ano": 22},
    {"nome": "Ushuaia",        "pais": "🇦🇷 Argentina", "lat": -54.801, "lon": -68.303, "r": 200, "risco": "Muito Alto", "sismos_ano": 30},
    {"nome": "El Calafate",    "pais": "🇦🇷 Argentina", "lat": -50.338, "lon": -72.270, "r": 200, "risco": "Moderado",  "sismos_ano": 8},
    {"nome": "Rio Gallegos",   "pais": "🇦🇷 Argentina", "lat": -51.622, "lon": -69.218, "r": 200, "risco": "Moderado",  "sismos_ano": 10},
]

DRAKE_EVENT = {
    "id": "us7000pwkn", "mag": 7.4, "depth": 10.0,
    "lat": -57.5, "lon": -64.8,
    "time": "2025-05-02T12:58:00Z",
    "local": "09:58 (GMT-3)",
    "place": "Passagem de Drake · 219 km sul de Ushuaia",
    "mmi": "V-VI em Puerto Williams",
    "tsunami": True, "evacuados": 1800, "replicas": 50,
    "maior_replica": 6.4,
}

np.random.seed(42)
ANOS = [2020, 2021, 2022, 2023, 2024, 2025]
MESES = ["Jan","Fev","Mar","Abr","Mai","Jun","Jul","Ago","Set","Out","Nov","Dez"]

HIST_SISMOS = {
    "Santiago":       [18,14,16,20,15,17,19,22,16,18,14,21],
    "Punta Arenas":   [1,2,1,1,3,1,2,1,1,2,1,2],
    "Puerto Williams":[2,3,4,2,8,3,2,4,2,3,2,2],
    "Ushuaia":        [2,3,2,3,7,2,3,2,2,3,2,3],
    "Rio Gallegos":   [1,1,0,1,2,1,1,0,1,1,1,1],
}

PROF_DIST = {"Raso (0–70km)":45,"Intermediário (70–300km)":35,"Profundo (>300km)":20}

# ── FUNÇÕES USGS ─────────────────────────────────────────────
@st.cache_data(ttl=300)
def fetch_usgs_recent(city_lat, city_lon, radius_km=300, min_mag=2.0, days=30):
    end = datetime.utcnow()
    start = end - timedelta(days=days)
    url = (
        f"https://earthquake.usgs.gov/fdsnws/event/1/query?"
        f"format=geojson&starttime={start.strftime('%Y-%m-%d')}"
        f"&endtime={end.strftime('%Y-%m-%d')}"
        f"&latitude={city_lat}&longitude={city_lon}"
        f"&maxradiuskm={radius_km}&minmagnitude={min_mag}"
        f"&orderby=time&limit=50"
    )
    try:
        r = requests.get(url, timeout=8)
        if r.status_code == 200:
            data = r.json()
            feats = data.get("features", [])
            return feats, data.get("metadata", {}).get("count", 0)
    except Exception:
        pass
    return [], 0

@st.cache_data(ttl=600)
def fetch_usgs_patagonia(days=365):
    end = datetime.utcnow()
    start = end - timedelta(days=days)
    url = (
        f"https://earthquake.usgs.gov/fdsnws/event/1/query?"
        f"format=geojson&starttime={start.strftime('%Y-%m-%d')}"
        f"&endtime={end.strftime('%Y-%m-%d')}"
        f"&minlatitude=-62&maxlatitude=-45"
        f"&minlongitude=-82&maxlongitude=-60"
        f"&minmagnitude=4.0&orderby=time&limit=200"
    )
    try:
        r = requests.get(url, timeout=10)
        if r.status_code == 200:
            return r.json().get("features", [])
    except Exception:
        pass
    return []

def pct_sismos(count_30d, baseline):
    if baseline <= 0: return 0
    pct = min((count_30d / baseline) * 100, 999)
    return round(pct, 1)

def risk_color(risco):
    m = {"Muito Alto":"#8B2515","Alto":"#C47D0E","Moderado-Alto":"#2555A0",
         "Moderado":"#1B3A1E","Baixo":"#2D7A45"}
    return m.get(risco, "#888")

# ── ESTILOS ───────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@700;900&family=DM+Sans:wght@300;400;500&family=DM+Mono&family=Noto+Serif:wght@700&family=Noto+Sans:wght@400;500&family=Noto+Sans+SC:wght@400;500;700&family=Noto+Naskh+Arabic:wght@400;700&display=swap');
:root{--quake:#6B1A0A;--quake-mid:#8B2515;--quake-light:#C0390A;
  --earth:#2D1B0E;--amber:#C47D0E;--tectonic:#1A3A6E;--tect-light:#2555A0;
  --cream:#FAF6F0;--warm-gray:#6A5A50;--green:#2D7A45;--black:#0D1117;}
html,body,[class*="css"]{font-family:'DM Sans','Noto Sans','Noto Sans SC','Noto Naskh Arabic',sans-serif;background:var(--cream);color:var(--black);}
.hero-wrap{background:linear-gradient(135deg,#1A0A05 0%,#3D0E08 50%,#5A1810 100%);border-radius:20px;padding:3rem 2.5rem 2rem;margin-bottom:2rem;position:relative;overflow:hidden;}
.hero-wrap::before{content:"🌍";font-size:200px;position:absolute;right:-20px;top:-30px;opacity:0.05;}
.hero-tag{background:#F5A623;color:#1A0A05;font-family:'DM Mono',monospace;font-size:.7rem;font-weight:bold;letter-spacing:2px;padding:4px 12px;border-radius:4px;display:inline-block;margin-bottom:1rem;text-transform:uppercase;}
.hero-title{font-family:'Playfair Display','Noto Serif','Noto Sans SC','Noto Naskh Arabic',serif;font-size:2.8rem;font-weight:900;color:#fff;line-height:1.15;margin-bottom:.8rem;white-space:pre-line;}
.hero-subtitle{font-size:1rem;color:rgba(255,255,255,.78);max-width:680px;line-height:1.6;margin-bottom:1.5rem;}
.hero-badges{display:flex;gap:10px;flex-wrap:wrap;}
.badge{background:rgba(255,255,255,.1);border:1px solid rgba(255,255,255,.2);color:rgba(255,255,255,.85);font-size:.72rem;font-family:'DM Mono','Noto Sans','Noto Sans SC','Noto Naskh Arabic',monospace;padding:5px 12px;border-radius:20px;}
.badge-quake{background:rgba(240,80,30,.25);border-color:#F5A623;color:#F5A623;}
.metric-box{background:white;border-radius:16px;padding:1.4rem 1.2rem;border-top:4px solid var(--quake-light);box-shadow:0 2px 12px rgba(0,0,0,.07);text-align:center;}
.metric-box.tect{border-top-color:var(--tect-light);}
.metric-box.amber{border-top-color:var(--amber);}
.metric-box.green{border-top-color:var(--green);}
.metric-val{font-family:'Playfair Display','Noto Serif',serif;font-size:2.1rem;font-weight:900;color:var(--quake-mid);line-height:1;margin-bottom:.3rem;}
.metric-label{font-size:.75rem;color:var(--warm-gray);text-transform:uppercase;letter-spacing:1px;}
.section-label{font-family:'DM Mono','Noto Sans','Noto Sans SC','Noto Naskh Arabic',monospace;font-size:.65rem;color:var(--quake-mid);text-transform:uppercase;letter-spacing:3px;margin-bottom:.3rem;}
.section-title{font-family:'Playfair Display','Noto Serif','Noto Sans SC','Noto Naskh Arabic',serif;font-size:1.9rem;font-weight:700;color:var(--quake-mid);margin-bottom:1.2rem;line-height:1.2;}
.info-card{background:white;border-radius:16px;padding:1.5rem;box-shadow:0 2px 12px rgba(0,0,0,.05);border-left:4px solid var(--quake-light);margin-bottom:1rem;}
.info-card.tect{border-left-color:var(--tect-light);}
.info-card.amber{border-left-color:var(--amber);}
.info-card.green{border-left-color:var(--green);}
.info-card.urgent{border-left-color:var(--quake-mid);background:linear-gradient(135deg,#FFF5F0,#FFEBE0);}
.method-step{display:flex;align-items:flex-start;gap:1rem;padding:1rem;background:white;border-radius:12px;margin-bottom:.8rem;box-shadow:0 1px 6px rgba(0,0,0,.04);}
.step-num{background:var(--quake-mid);color:white;font-family:'Playfair Display','Noto Serif',serif;font-size:1.1rem;font-weight:700;width:36px;height:36px;border-radius:50%;display:flex;align-items:center;justify-content:center;flex-shrink:0;}
.step-title{font-weight:500;color:var(--quake-mid);font-size:.95rem;}
.step-desc{font-size:.82rem;color:var(--warm-gray);margin-top:.2rem;}
.discovery-box{background:linear-gradient(135deg,#FFF8F5,#FFECE0);border:2px solid var(--quake-light);border-radius:16px;padding:1.8rem;margin:.8rem 0;}
.discovery-title{font-family:'Playfair Display','Noto Serif','Noto Sans SC','Noto Naskh Arabic',serif;font-size:1.1rem;font-weight:700;color:var(--quake-mid);margin-bottom:.5rem;}
.timeline-item{display:flex;gap:1rem;padding:1rem 0;border-bottom:1px solid #F0E0D8;}
.timeline-year{font-family:'Playfair Display','Noto Serif',serif;font-size:1rem;font-weight:700;color:var(--quake-light);min-width:90px;}
.timeline-title{font-weight:500;color:var(--quake-mid);margin-bottom:.2rem;}
.timeline-desc{font-size:.85rem;color:var(--warm-gray);}
.timeline-item.highlight{background:linear-gradient(135deg,#FFF8F5,#FFECE0);border-radius:8px;padding:1rem;border-left:4px solid var(--quake-mid);}
.source-badges{display:flex;gap:8px;flex-wrap:wrap;margin-top:.8rem;}
.source-badge{background:var(--quake-mid);color:white;font-family:'DM Mono',monospace;font-size:.65rem;padding:4px 10px;border-radius:4px;letter-spacing:1px;text-transform:uppercase;}
.footer-wrap{background:var(--earth);border-radius:20px;padding:2rem;color:rgba(255,255,255,.8);text-align:center;margin-top:3rem;}
.footer-title{font-family:'Playfair Display','Noto Serif',serif;color:#F5A623;font-size:1.2rem;margin-bottom:.5rem;}
.live-card{background:white;border-radius:16px;padding:1.2rem 1rem;box-shadow:0 2px 16px rgba(0,0,0,.08);border-top:5px solid;text-align:center;transition:transform .15s;}
.live-card:hover{transform:translateY(-2px);}
.live-city{font-family:'Playfair Display','Noto Serif',serif;font-size:.95rem;font-weight:700;margin-bottom:.2rem;}
.live-pct{font-family:'Playfair Display','Noto Serif',serif;font-size:2rem;font-weight:900;line-height:1;}
.live-label{font-size:.65rem;font-family:'DM Mono','Noto Sans','Noto Sans SC','Noto Naskh Arabic',monospace;text-transform:uppercase;letter-spacing:1px;margin-top:.2rem;}
.live-count{font-size:.72rem;color:var(--warm-gray);margin-top:.15rem;}
.pulse{animation:pulse 2s infinite;}
@keyframes pulse{0%{opacity:1}50%{opacity:.5}100%{opacity:1}}
.photo-placeholder{background:#FFF8F5;border:2px dashed var(--quake-light);border-radius:12px;padding:2rem;text-align:center;min-height:220px;display:flex;flex-direction:column;align-items:center;justify-content:center;}
.photo-emoji{font-size:2.6rem;}
.photo-title{font-weight:600;color:var(--quake-mid);margin:.5rem 0 .2rem;font-size:.95rem;}
.photo-desc{font-size:.78rem;color:var(--warm-gray);line-height:1.5;}
.photo-path{font-size:.65rem;color:var(--quake-light);font-family:'DM Mono',monospace;margin-top:.5rem;background:#FFECE0;padding:3px 8px;border-radius:4px;direction:ltr;}
.photo-meta{font-size:.7rem;font-family:'DM Mono',monospace;margin-top:.4rem;line-height:1.8;}
.photo-legenda{font-size:.72rem;color:var(--warm-gray);font-style:italic;padding:.5rem .8rem;background:#faf8f5;text-align:center;border-top:1px solid #F0E0D8;}
.photo-destaque{border:3px solid var(--quake-light);border-radius:14px;overflow:hidden;box-shadow:0 4px 20px rgba(139,37,21,.2);}
</style>""",unsafe_allow_html=True)

if RTL:
    st.markdown("""
<style>
[data-testid="stMain"], [data-testid="stAppViewContainer"] .main { direction: rtl; text-align: right; }
.hero-wrap, .info-card, .method-step, .discovery-box, .timeline-item { direction: rtl; text-align: right; }
.hero-wrap::before { right: auto; left: -20px; }
.info-card, .info-card.tect, .info-card.amber, .info-card.green, .info-card.urgent { border-left: none; border-right: 4px solid var(--quake-light); }
.info-card.urgent { border-right-color: var(--quake-mid); }
.js-plotly-plot, iframe { direction: ltr; }
body, html, [class*="css"] { font-family: 'Noto Naskh Arabic','DM Sans',sans-serif; }
</style>
""", unsafe_allow_html=True)

# ── HERO ──────────────────────────────────────────────────────
st.markdown(f"""
<div class="hero-wrap">
  <div class="hero-tag">{T['hero_tag']}</div>
  <div class="hero-title">{T['hero_title']}</div>
  <div class="hero-subtitle">{T['hero_subtitle']}</div>
  <div class="hero-badges">
    <span class="badge badge-quake">{T['badge1']}</span>
    <span class="badge badge-quake">{T['badge2']}</span>
    <span class="badge">{T['badge3']}</span>
    <span class="badge">{T['badge4']}</span>
    <span class="badge">{T['badge5']}</span>
  </div>
</div>""",unsafe_allow_html=True)

c1,c2,c3,c4=st.columns(4)
with c1: st.markdown(f'<div class="metric-box"><div class="metric-val">M7.4</div><div class="metric-label">{T["m1"]}</div></div>',unsafe_allow_html=True)
with c2: st.markdown(f'<div class="metric-box tect"><div class="metric-val">10 km</div><div class="metric-label">{T["m2"]}</div></div>',unsafe_allow_html=True)
with c3: st.markdown(f'<div class="metric-box amber"><div class="metric-val">1.800</div><div class="metric-label">{T["m3"]}</div></div>',unsafe_allow_html=True)
with c4: st.markdown(f'<div class="metric-box green"><div class="metric-val">50+</div><div class="metric-label">{T["m4"]}</div></div>',unsafe_allow_html=True)
st.markdown("<br>",unsafe_allow_html=True)

tabs=st.tabs([T['tab1'],T['tab2'],T['tab3'],T['tab4'],T['tab5'],T['tab6'],T['tab7'],T['tab8
