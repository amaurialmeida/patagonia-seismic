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
html,body,[class*="css"]{font-family:'DM Sans','Noto Sans','Noto Sans SC','Noto Naskh Arabic',sans-serif;background-color:var(--cream);color:var(--black);}
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

tabs=st.tabs([T['tab1'],T['tab2'],T['tab3'],T['tab4'],T['tab5'],T['tab6'],T['tab7'],T['tab8']])

# ─────────────────────────────────────────────────────────────
# TAB 1: MAPA & ANÁLISE + DASHBOARD EM TEMPO REAL
# ─────────────────────────────────────────────────────────────
with tabs[0]:
    st.markdown(f'<div class="section-label">{T["live_label"]}</div>',unsafe_allow_html=True)
    st.markdown(f'<div class="section-title">{T["live_title"]}</div>',unsafe_allow_html=True)
    st.markdown(f'<div class="info-card urgent">{T["live_hint"]}</div>',unsafe_allow_html=True)

    col_refresh,_ = st.columns([1,7])
    with col_refresh:
        refresh = st.button(T['live_fetch'], key="refresh_live")
    if refresh:
        st.cache_data.clear()
        st.rerun()

    BASELINES = {
        "Santiago": 14.5, "Buenos Aires": 0.1, "Punta Arenas": 1.5,
        "Puerto Natales": 1.0, "Puerto Williams": 3.0, "Rio Grande": 2.0,
        "Ushuaia": 2.5, "El Calafate": 0.8, "Rio Gallegos": 1.0,
    }

    cols_live = st.columns(3)
    for i, city in enumerate(CITIES):
        cname = city['nome']
        feats, count = fetch_usgs_recent(city['lat'], city['lon'], city['r'], min_mag=2.0, days=30)
        baseline = BASELINES.get(cname, 1.0)
        pct = pct_sismos(count, baseline)
        risco = city['risco']
        cor = risk_color(risco)

        if pct > 150: status_txt = T['live_above']; status_color_css = "#C0390A"
        elif pct < 50: status_txt = T['live_below']; status_color_css = "#2D7A45"
        else: status_txt = T['live_normal']; status_color_css = "#1A3A6E"

        pct_display = f"{pct:.0f}%"

        with cols_live[i % 3]:
            st.markdown(f"""
            <div class="live-card" style="border-top-color:{cor};margin-bottom:1rem">
              <div class="live-city" style="color:{cor}">{city['pais']} {cname}</div>
              <div class="live-pct" style="color:{status_color_css}">{pct_display}</div>
              <div class="live-label" style="color:{status_color_css}">{'🔺' if pct>150 else ('🔻' if pct<50 else '➡️')} {status_txt}</div>
              <div class="live-count">📊 {count} {T['live_count']}</div>
              <div class="live-count" style="font-size:.62rem">baseline: {baseline:.1f}/mês · risco: {risco}</div>
            </div>""",unsafe_allow_html=True)

    st.markdown(f'<div style="font-size:.7rem;color:#999;font-family:DM Mono;text-align:right;margin-top:-.5rem">🕐 {datetime.utcnow().strftime("%Y-%m-%d %H:%M")} UTC · USGS API</div>',unsafe_allow_html=True)

    st.markdown(f"<br><div class='section-label'>{T['map_label']}</div>",unsafe_allow_html=True)
    st.markdown(f"<div class='section-title'>{T['map_title']}</div>",unsafe_allow_html=True)
    st.markdown(f'<div class="info-card">{T["map_hint"]}</div>',unsafe_allow_html=True)

    try:
        carto_key = st.secrets.get("CARTO_API_KEY", "")
    except Exception:
        carto_key = ""

    mapa = folium.Map(location=[-54, -68], zoom_start=5, tiles=None, control_scale=True)

    if carto_key:
        folium.TileLayer(
            tiles=("https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png?key=" + carto_key),
            attr='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/attributions">CARTO</a>',
            name="CARTO Dark Matter", subdomains="abcd", max_zoom=20, overlay=False, control=True,
        ).add_to(mapa)
    else:
        folium.TileLayer(
            "OpenStreetMap", name="OpenStreetMap",
            attr='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
            control=True,
        ).add_to(mapa)

    feats_pat=fetch_usgs_patagonia(days=365)
    for f in feats_pat[:80]:
        p=f['properties']; g=f['geometry']['coordinates']
        mag=p.get('mag',0) or 0
        dep=g[2] if len(g)>2 else 0
        place=p.get('place','')
        t_ms=p.get('time',0)
        t_str=datetime.utcfromtimestamp(t_ms/1000).strftime('%Y-%m-%d') if t_ms else '?'
        r=max(4,mag*4)
        if mag>=7: clr="#FF2000"
        elif mag>=6: clr="#FF6000"
        elif mag>=5: clr="#FFA020"
        elif mag>=4.5: clr="#FFCC50"
        else: clr="#FFE890"
        popup_html=f"<div style='font-family:sans-serif;padding:8px;min-width:200px'><b style='color:#8B2515'>M{mag:.1f}</b><br><span style='font-size:11px'>{place}</span><br><span style='font-size:10px;color:#999'>Prof: {dep:.0f} km · {t_str}</span></div>"
        folium.CircleMarker(location=[g[1],g[0]],radius=r,color=clr,fill=True,
            fill_color=clr,fill_opacity=.7,weight=1,
            popup=folium.Popup(popup_html,max_width=240),
            tooltip=f"M{mag:.1f} · {t_str}").add_to(mapa)

    drake_popup=f"""<div style='font-family:sans-serif;padding:12px;min-width:260px'>
        <h4 style='color:#FF2000;margin:0 0 8px'>⭐ M{DRAKE_EVENT['mag']} — Passagem de Drake</h4>
        <p style='margin:3px 0;font-size:12px'>📅 02/05/2025 · {DRAKE_EVENT['local']}</p>
        <p style='margin:3px 0;font-size:12px'>📍 {DRAKE_EVENT['place']}</p>
        <p style='margin:3px 0;font-size:12px'>🏔️ Prof: {DRAKE_EVENT['depth']} km (raso)</p>
        <p style='margin:3px 0;font-size:12px'>📡 MMI: {DRAKE_EVENT['mmi']}</p>
        <p style='margin:3px 0;font-size:12px'>🚨 Tsunami: ✅ · Evacuados: {DRAKE_EVENT['evacuados']:,}</p>
        <p style='margin:3px 0;font-size:12px'>🔄 Réplicas: {DRAKE_EVENT['replicas']}+ · Max: M{DRAKE_EVENT['maior_replica']}</p>
        <p style='margin:0;font-size:10px;color:#999'>ID USGS: {DRAKE_EVENT['id']}</p></div>"""
    folium.Marker(location=[DRAKE_EVENT['lat'],DRAKE_EVENT['lon']],
        popup=folium.Popup(drake_popup,max_width=290),
        tooltip="⭐ M7.4 Drake Passage · 02/05/2025",
        icon=folium.Icon(color="red",icon="star",prefix="fa")).add_to(mapa)

    for city in CITIES:
        flag="🇨🇱" if "Chile" in city['pais'] else "🇦🇷"
        cor=risk_color(city['risco'])
        is_pw = city['nome']=="Puerto Williams"
        pop=f"""<div style='font-family:sans-serif;padding:10px;min-width:220px'>
            <h4 style='color:{cor};margin:0 0 6px'>{flag} {city['nome']}</h4>
            <p style='margin:2px 0;font-size:11px'>⚠️ Risco: <b>{city['risco']}</b></p>
            <p style='margin:2px 0;font-size:11px'>📊 Sismos/ano: ~{city['sismos_ano']}</p>
            {"<p style='margin:4px 0;font-size:11px;color:#FF2000'><b>⭐ MMI V-VI no M7.4 de 02/05/2025</b></p>" if is_pw else ""}
        </div>"""
        icon_color="red" if is_pw else ("orange" if city['risco']=="Muito Alto" else "blue")
        folium.Marker(location=[city['lat'],city['lon']],
            popup=folium.Popup(pop,max_width=250),
            tooltip=f"{flag} {city['nome']} · {city['risco']}",
            icon=folium.Icon(color=icon_color,icon="home" if is_pw else "circle",prefix="fa")).add_to(mapa)

    folium.PolyLine(locations=[[-54.5,-70],[-54.8,-68],[-54.9,-67.6],[-55.2,-65],[-55.0,-63]],
        color="#F5A623",weight=3,opacity=.7,dash_array="6",
        tooltip="Falha Magallanes-Fagnano").add_to(mapa)

    folium_static(mapa,width=1100,height=540)

    st.markdown(f"<br><div class='section-label' style='color:#C0390A'>{T['drake_label']}</div>",unsafe_allow_html=True)
    col_d1,col_d2,col_d3,col_d4 = st.columns(4)
    fields=[("📅 Data/Hora","02/05/2025 · 09:58 local"),("📍 Epicentro","219 km sul de Ushuaia"),
            ("🏔️ Profundidade","10 km (raso)"),("🚨 Evacuados","~1.800 pessoas")]
    for col,(label,val) in zip([col_d1,col_d2,col_d3,col_d4],fields):
        with col:
            st.markdown(f'<div class="metric-box"><div class="metric-val" style="font-size:1.2rem">{val}</div><div class="metric-label">{label}</div></div>',unsafe_allow_html=True)

    st.markdown(f"<br><div class='section-title' style='font-size:1.3rem'>{T['mag_title']}</div>",unsafe_allow_html=True)
    mags=[f['properties'].get('mag',0) or 0 for f in feats_pat] if feats_pat else []
    if not mags: mags=list(np.random.exponential(0.5,200)+4.0)
    fig_hist=go.Figure()
    fig_hist.add_trace(go.Histogram(x=mags,nbinsx=20,marker_color='#C0390A',opacity=.85,
        hovertemplate='M%{x:.1f}: %{y} eventos<extra></extra>',name="Sismos"))
    fig_hist.add_vline(x=7.4,line_dash="dash",line_color="#F5A623",line_width=3,
        annotation_text="  M7.4 Drake",annotation_font_color="#F5A623",annotation_font_size=12)
    fig_hist.update_layout(paper_bgcolor='rgba(0,0,0,0)',plot_bgcolor='rgba(107,26,10,.03)',
        font=dict(family='DM Sans'),height=300,showlegend=False,
        xaxis=dict(title="Magnitude",showgrid=False),
        yaxis=dict(title="Frequência",showgrid=True,gridcolor='#F0E0D8'),
        margin=dict(t=20,b=20))
    plot(fig_hist)

    col_pr,col_sc=st.columns(2)
    with col_pr:
        labels=list(PROF_DIST.keys()); vals=list(PROF_DIST.values())
        fig_pie=go.Figure(go.Pie(labels=labels,values=vals,
            marker_colors=["#C0390A","#F5A623","#2555A0"],hole=.45,
            hovertemplate='%{label}: %{percent}<extra></extra>'))
        fig_pie.update_layout(title=dict(text=T['prof_title'],font=dict(size=13,family='Playfair Display')),
            paper_bgcolor='rgba(0,0,0,0)',height=300,font=dict(family='DM Sans'),
            showlegend=True,legend=dict(orientation='h',yanchor='bottom',y=-0.2),margin=dict(t=50,b=10))
        plot(fig_pie)
    with col_sc:
        if feats_pat:
            sc_mags=[f['properties'].get('mag',0) or 0 for f in feats_pat[:100]]
            sc_deps=[f['geometry']['coordinates'][2] if len(f['geometry']['coordinates'])>2 else 10 for f in feats_pat[:100]]
        else:
            sc_mags=list(np.random.uniform(4,7.5,80)); sc_deps=list(np.random.uniform(0,300,80))
        fig_sc=go.Figure(go.Scatter(x=sc_mags,y=sc_deps,mode='markers',
            marker=dict(color=sc_mags,colorscale=[[0,"#FFE890"],[0.5,"#F5A623"],[1,"#C0390A"]],
                size=8,opacity=.8,line=dict(width=.5,color='white')),
            hovertemplate='M%{x:.1f} · Prof: %{y:.0f} km<extra></extra>'))
        fig_sc.add_scatter(x=[7.4],y=[10],mode='markers',
            marker=dict(color='red',size=18,symbol='star',line=dict(width=2,color='white')),
            name="M7.4 Drake",hovertemplate='M7.4 Drake Passage<br>Prof: 10 km<extra></extra>')
        fig_sc.update_layout(title=dict(text="Magnitude × Profundidade",font=dict(size=13,family='Playfair Display')),
            paper_bgcolor='rgba(0,0,0,0)',plot_bgcolor='rgba(107,26,10,.03)',
            height=300,font=dict(family='DM Sans'),
            xaxis=dict(title="Magnitude",showgrid=False),
            yaxis=dict(title="Profundidade (km)",autorange="reversed",showgrid=True,gridcolor='#F0E0D8'),
            legend=dict(orientation='h'),margin=dict(t=50,b=20))
        plot(fig_sc)

# ── TAB 2: METODOLOGIA ───────────────────────────────────────
with tabs[1]:
    st.markdown(f'<div class="section-label">{T["method_label"]}</div>',unsafe_allow_html=True)
    st.markdown(f'<div class="section-title">{T["method_title"]}</div>',unsafe_allow_html=True)
    st.markdown(f'<div class="discovery-box"><div class="discovery-title">{T["sci_q_title"]}</div><p style="font-size:1.05rem;color:#8B2515;line-height:1.7"><em>{T["sci_q"]}</em></p></div>',unsafe_allow_html=True)
    st.markdown(f'<div class="section-label" style="margin-top:1.5rem">{T["pipeline_label"]}</div>',unsafe_allow_html=True)
    for num,title,desc in T['steps']:
        st.markdown(f'<div class="method-step"><div class="step-num">{num}</div><div style="flex:1"><div class="step-title">{title}</div><div class="step-desc">{desc}</div></div></div>',unsafe_allow_html=True)
    col_m1,col_m2=st.columns(2)
    with col_m1:
        st.markdown(f'<div class="info-card"><strong>{T["geo_title"]}</strong><br><br><div style="font-size:.88rem;line-height:2.1">{T["geo_text"]}</div></div>',unsafe_allow_html=True)
    with col_m2:
        st.markdown(f'<div class="info-card urgent"><strong>{T["mmi_title"]}</strong><br><br><div style="font-size:.88rem;line-height:2.1">{T["mmi_text"]}</div></div>',unsafe_allow_html=True)
    st.markdown("""<div class="info-card tect" style="margin-top:.5rem;background:linear-gradient(135deg,#EEF4FF,#D8EAF8)">
      <strong style="color:#1A3A6E">📐 API USGS — Endpoint de Tempo Real</strong><br><br>
      <div style="font-family:'DM Mono',monospace;font-size:.82rem;line-height:2.2;color:#1A3A6E;direction:ltr">
        <b>URL:</b> earthquake.usgs.gov/fdsnws/event/1/query<br>
        <b>Parâmetros:</b> format=geojson · minmagnitude=2.0 · maxradiuskm=300<br>
        <b>% atividade</b> = (count 30d / baseline mensal) × 100<br>
        <b>>150%</b> = acima do normal · <b>50–150%</b> = normal · <b><50%</b> = abaixo do normal<br>
        <b>Cache:</b> 5 minutos (TTL=300s) · Gratuito · Sem chave de API
      </div></div>""",unsafe_allow_html=True)

# ── TAB 3: DESCOBERTAS ───────────────────────────────────────
with tabs[2]:
    st.markdown(f'<div class="section-label">{T["disc_label"]}</div>',unsafe_allow_html=True)
    st.markdown(f'<div class="section-title">{T["disc_title"]}</div>',unsafe_allow_html=True)
    for emoji,titulo,texto in T['discoveries']:
        st.markdown(f'<div class="discovery-box" style="margin-bottom:.8rem"><div style="display:flex;align-items:flex-start;gap:1rem"><span style="font-size:1.5rem">{emoji}</span><div><div class="discovery-title">{titulo}</div><p style="color:#6B1A0A;line-height:1.65;font-size:.93rem;margin:0">{texto}</p></div></div></div>',unsafe_allow_html=True)
    st.markdown(f'<div class="section-label" style="margin-top:1.5rem">{T["conclusion_label"]}</div>',unsafe_allow_html=True)
    st.markdown(f'<div class="info-card urgent"><strong style="color:#8B2515;font-size:1rem">{T["conclusion_title"]}</strong><br><br><p style="color:#6B1A0A;line-height:1.7;font-size:.93rem">{T["conclusion_text"]}</p><p style="color:#C0390A;font-size:.82rem;margin-bottom:0"><em>{T["conclusion_author"]}</em></p></div>',unsafe_allow_html=True)

    fig_cities=go.Figure()
    names=[c['nome'] for c in CITIES]
    riscos=[c['sismos_ano'] for c in CITIES]
    cores=[risk_color(c['risco']) for c in CITIES]
    fig_cities.add_trace(go.Bar(x=names,y=riscos,marker_color=cores,opacity=.88,
        text=[f"{r:.1f}" for r in riscos],textposition='outside',
        textfont=dict(size=10,family="DM Mono"),
        hovertemplate='<b>%{x}</b><br>~%{y:.1f} sismos/ano (M≥2)<extra></extra>',showlegend=False))
    fig_cities.add_annotation(x="Puerto Williams",y=35,text="⭐ M7.4 02/05/25",
        showarrow=True,arrowcolor="#C0390A",font=dict(color="#C0390A",size=10,family="DM Mono"))
    fig_cities.update_layout(paper_bgcolor='rgba(0,0,0,0)',plot_bgcolor='rgba(107,26,10,.02)',
        font=dict(family='DM Sans'),height=360,
        xaxis=dict(showgrid=False,tickangle=-30),
        yaxis=dict(showgrid=True,gridcolor='#F0E0D8',title="Sismos/ano (M≥2, est.)"),
        title=dict(text="Atividade Sísmica Anual por Cidade (estimativa)",font=dict(size=13,family='Playfair Display')),
        margin=dict(t=50,b=20))
    plot(fig_cities)

# ── TAB 4: EM CAMPO ──────────────────────────────────────────
with tabs[3]:
    st.markdown(f'<div class="section-label">{T["field_label"]}</div>',unsafe_allow_html=True)
    st.markdown(f'<div class="section-title">{T["field_title"]}</div>',unsafe_allow_html=True)
    st.markdown(f"""<div class="info-card urgent" style="margin-bottom:1.5rem">
      <strong>🌍 02/05/2025 · 09:58 local · Puerto Williams · M7.4 · MMI V-VI</strong><br>
      <p style="font-size:.9rem;color:#6B1A0A;margin:.5rem 0 0"><em>"Eu estava em Puerto Williams quando o chão começou a tremer às 9h58 da manhã. Logo em seguida as sirenes de tsunami soaram pela cidade."</em> — <b>Amauri Almeida</b></p></div>""",unsafe_allow_html=True)
    st.markdown(f'<div class="info-card amber"><strong>{T["field_inst_title"]}</strong><br><div style="font-size:.88rem;color:#5C3D1E;margin-top:.4rem">{T["field_inst"]}</div></div>',unsafe_allow_html=True)

    photos=T['photos']
    foto_dest=next((f for f in photos if f.get('destaque')),None)
    fotos_norm=[f for f in photos if not f.get('destaque')]

    cols=st.columns(len(fotos_norm))
    for col,foto in zip(cols,fotos_norm):
        with col:
            ex=os.path.exists(foto['path'])
            if ex: st.image(foto['path'],use_container_width=True)
            else:
                st.markdown(f"""<div class="photo-placeholder">
                  <div class="photo-emoji">{foto['emoji']}</div>
                  <div class="photo-title">{foto['titulo']}</div>
                  <div class="photo-desc">{foto['desc']}</div>
                  <div class="photo-meta">🌍 M: {foto['mag']}<br>🏔️ Prof: {foto['prof']}<br>📡 MMI: {foto['mmi']}</div>
                  <div class="photo-path">{foto['path']}</div></div>""",unsafe_allow_html=True)
            st.markdown(f'<div class="photo-legenda">{foto["legenda"]}</div>',unsafe_allow_html=True)
    st.markdown("<br>",unsafe_allow_html=True)

    if foto_dest:
        st.markdown("---")
        st.markdown('<div class="section-label" style="color:#C0390A">⭐ DESTAQUE — REGISTRO PÓS-SISMO · M7.4 DRAKE PASSAGE</div>',unsafe_allow_html=True)
        ex=os.path.exists(foto_dest['path'])
        if ex:
            st.markdown('<div class="photo-destaque">',unsafe_allow_html=True)
            st.image(foto_dest['path'],use_container_width=True)
            st.markdown('</div>',unsafe_allow_html=True)
        else:
            st.markdown(f"""<div class="photo-placeholder" style="min-height:300px">
              <div class="photo-emoji" style="font-size:3rem">{foto_dest['emoji']}</div>
              <div class="photo-title" style="font-size:1.2rem">{foto_dest['titulo']}</div>
              <div class="photo-desc" style="max-width:660px">{foto_dest['desc']}</div>
              <div class="photo-meta">🌍 {foto_dest['mag']} · 🏔️ {foto_dest['prof']} · 📡 MMI {foto_dest['mmi']}</div>
              <div class="photo-path">{foto_dest['path']}</div></div>""",unsafe_allow_html=True)
        st.markdown(f'<div class="photo-legenda" style="font-size:.82rem;padding:.7rem 1.2rem">{foto_dest["legenda"]}</div>',unsafe_allow_html=True)

    st.markdown("<br>",unsafe_allow_html=True)
    st.markdown(f'<div class="section-label">{T["timeline_label"]}</div>',unsafe_allow_html=True)
    for data,titulo,desc in T['timeline_items']:
        is_main = "M7.4" in titulo or "M7.4" in desc
        cls = "timeline-item highlight" if is_main else "timeline-item"
        st.markdown(f'<div class="{cls}"><div class="timeline-year" style="color:{"#C0390A" if is_main else ""}">{data}</div><div style="flex:1"><div class="timeline-title">{titulo}</div><div class="timeline-desc">{desc}</div></div></div>',unsafe_allow_html=True)

# ── TAB 5: TENDÊNCIAS ────────────────────────────────────────
with tabs[4]:
    st.markdown(f'<div class="section-label">{T["trend_label"]}</div>',unsafe_allow_html=True)
    st.markdown(f'<div class="section-title">{T["trend_title"]}</div>',unsafe_allow_html=True)
    st.markdown(f'<div class="info-card" style="font-size:.82rem;padding:.8rem 1rem">{T["trend_hint"]}</div>',unsafe_allow_html=True)

    city_sel=st.selectbox(T['trend_city'],list(HIST_SISMOS.keys()),key="trend_city_sel")
    fig_trend=go.Figure()
    vals=HIST_SISMOS[city_sel]
    cor_city=risk_color(next((c['risco'] for c in CITIES if c['nome']==city_sel),"Moderado"))
    
    # CORREÇÃO DO BUG: Usar índices numéricos (0 a 11) no eixo X para o add_vline funcionar
    x_indices = list(range(len(MESES)))
    
    fig_trend.add_trace(go.Bar(x=x_indices,y=vals,marker_color=cor_city,opacity=.85,
        text=vals,textposition='outside',textfont=dict(size=10,family="DM Mono",color=cor_city),
        hovertemplate='<b>%{text}</b><br>%{y} sismos<extra></extra>',name=city_sel))
        
    if city_sel in ("Puerto Williams","Ushuaia","Rio Grande","Punta Arenas"):
        # O add_vline agora recebe o índice numérico (4 = Maio), evitando o TypeError do Plotly
        fig_trend.add_vline(x=4, line_dash="dash", line_color="#C0390A", line_width=2,
            annotation_text="  M7.4 02/Mai/25", annotation_font_color="#C0390A", annotation_font_size=10)
            
    mean_val=np.mean(vals)
    fig_trend.add_hline(y=mean_val,line_dash="dot",line_color=cor_city,opacity=.6,
        annotation_text=f"  Média: {mean_val:.1f}",annotation_font_color=cor_city)
        
    fig_trend.update_layout(paper_bgcolor='rgba(0,0,0,0)',plot_bgcolor='rgba(107,26,10,.02)',
        font=dict(family='DM Sans'),height=360,showlegend=False,
        xaxis=dict(tickmode='array', tickvals=x_indices, ticktext=MESES, showgrid=False),
        yaxis=dict(showgrid=True,gridcolor='#F0E0D8',title="Sismos (M≥2)"),
        margin=dict(t=20,b=20))
    plot(fig_trend)

    fig_all=go.Figure()
    for cname,vals_m in HIST_SISMOS.items():
        cor_c=risk_color(next((c['risco'] for c in CITIES if c['nome']==cname),"Moderado"))
        fig_all.add_trace(go.Scatter(x=x_indices,y=vals_m,mode='lines+markers',name=cname,
            line=dict(color=cor_c,width=2),marker=dict(size=6),
            hovertemplate=f'<b>{cname}</b><br>%{{x}}: %{{y}}<extra></extra>'))
            
    fig_all.add_vline(x=4, line_dash="dash", line_color="#C0390A", line_width=2,
        annotation_text="  M7.4 02/Mai/25", annotation_font_color="#C0390A", annotation_font_size=10)
        
    fig_all.update_layout(paper_bgcolor='rgba(0,0,0,0)',plot_bgcolor='rgba(107,26,10,.02)',
        title=dict(text="Comparativo Anual — Todas as Cidades (2024)",font=dict(size=13,family='Playfair Display')),
        font=dict(family='DM Sans'),height=380,
        xaxis=dict(tickmode='array', tickvals=x_indices, ticktext=MESES, showgrid=False),
        yaxis=dict(showgrid=True,gridcolor='#F0E0D8',title="Sismos M≥2"),
        legend=dict(orientation='h',yanchor='bottom',y=1.01,font=dict(size=9)),margin=dict(t=50,b=20))
    plot(fig_all)

# ── TAB 6: PARÂMETROS ────────────────────────────────────────
with tabs[5]:
    st.markdown(f'<div class="section-label">{T["params_label"]}</div>',unsafe_allow_html=True)
    st.markdown(f'<div class="section-title">{T["params_title"]}</div>',unsafe_allow_html=True)

    mmi_data=[
        {"cidade":"Puerto Williams","mmi":5.5,"dist":219,"pais":"CL"},
        {"cidade":"Ushuaia","mmi":4.5,"dist":219,"pais":"AR"},
        {"cidade":"Rio Grande","mmi":3.5,"dist":290,"pais":"AR"},
        {"cidade":"Punta Arenas","mmi":3.2,"dist":340,"pais":"CL"},
        {"cidade":"Puerto Natales","mmi":2.5,"dist":420,"pais":"CL"},
        {"cidade":"Rio Gallegos","mmi":2.0,"dist":480,"pais":"AR"},
    ]
    df_mmi=pd.DataFrame(mmi_data)
    fig_mmi=go.Figure()
    for _,row in df_mmi.iterrows():
        cor=risk_color(next((c['risco'] for c in CITIES if c['nome']==row['cidade']),"Moderado"))
        fig_mmi.add_trace(go.Scatter(x=[row['dist']],y=[row['mmi']],mode='markers+text',
            marker=dict(color=cor,size=18,opacity=.85,line=dict(width=2,color='white')),
            text=[row['cidade']],textposition="top center",textfont=dict(size=9),
            name=row['cidade'],showlegend=False,
            hovertemplate=f"<b>{row['cidade']}</b><br>Dist: {row['dist']} km<br>MMI: {row['mmi']:.1f}<extra></extra>"))
    fig_mmi.update_layout(paper_bgcolor='rgba(0,0,0,0)',plot_bgcolor='rgba(107,26,10,.03)',
        title=dict(text="Intensidade MMI vs. Distância ao Epicentro (M7.4 · 02/05/2025)",font=dict(size=13,family='Playfair Display')),
        font=dict(family='DM Sans'),height=380,
        xaxis=dict(title="Distância ao Epicentro (km)",showgrid=True,gridcolor='#F0E0D8'),
        yaxis=dict(title="Intensidade MMI",showgrid=True,gridcolor='#F0E0D8',range=[1,7]),
        margin=dict(t=50,b=20))
    fig_mmi.add_hline(y=5,line_dash="dot",line_color="#C0390A",opacity=.5,
        annotation_text="  MMI V = Forte",annotation_font_color="#C0390A")
    plot(fig_mmi)

    fig_gauges=go.Figure()
    risco_num={"Muito Alto":5,"Alto":4,"Moderado-Alto":3,"Moderado":2,"Baixo":1}
    risco_cor={"Muito Alto":"#C0390A","Alto":"#E67E22","Moderado-Alto":"#2555A0","Moderado":"#1B3A1E","Baixo":"#2D7A45"}
    for i,city in enumerate(CITIES):
        rv=risco_num.get(city['risco'],2); rc=risco_cor.get(city['risco'],"#888")
        fig_gauges.add_trace(go.Indicator(
            mode="gauge+number",value=rv,
            number={'font':{'size':16,'family':'Playfair Display','color':rc}},
            gauge={'axis':{'range':[0,5],'tickwidth':1,'tickvals':[1,2,3,4,5],
                'ticktext':['Baixo','Mod.','Mod+','Alto','M.Alto']},
                'bar':{'color':rc,'thickness':.3},'bgcolor':"white",'borderwidth':0,
                'steps':[{'range':[0,2],'color':'#EEF5EE'},{'range':[2,3.5],'color':'#EEF4FF'},
                          {'range':[3.5,5],'color':'#FFF5F0'}],
                'threshold':{'line':{'color':rc,'width':3},'thickness':.75,'value':rv}},
            title={'text':f"{city['nome']}",'font':{'size':9,'family':'DM Sans','color':rc}},
            domain={'row':0,'column':i}))
    fig_gauges.update_layout(grid={'rows':1,'columns':len(CITIES),'pattern':"independent"},
        paper_bgcolor='rgba(0,0,0,0)',height=240,font=dict(family='DM Sans'),
        title=dict(text="Índice de Risco Sísmico por Cidade",font=dict(size=13,family='Playfair Display'),x=.5),
        margin=dict(t=50,b=10,l=10,r=10))
    plot(fig_gauges)

# ── TAB 7: DADOS BRUTOS ──────────────────────────────────────
with tabs[6]:
    st.markdown(f'<div class="section-label">{T["raw_label"]}</div>',unsafe_allow_html=True)
    st.markdown(f'<div class="section-title">{T["raw_title"]}</div>',unsafe_allow_html=True)

    CATALOG=[
        {"ID":"us7000pwkn","Data":"2025-05-02","Hora":"09:58 local","Magnitude":7.4,"Profundidade_km":10,"Local":"Passagem de Drake · 219 km S de Ushuaia","Tsunami":"Sim","MMI_PW":"V-VI","Evacuados":1800},
        {"ID":"us7000pxab","Data":"2025-05-02","Hora":"10:45 local","Magnitude":6.4,"Profundidade_km":12,"Local":"Passagem de Drake (réplica)","Tsunami":"Não","MMI_PW":"III-IV","Evacuados":0},
        {"ID":"us6000nkl2","Data":"2025-03-15","Hora":"03:22 local","Magnitude":5.8,"Profundidade_km":35,"Local":"Tierra del Fuego, Argentina","Tsunami":"Não","MMI_PW":"II-III","Evacuados":0},
        {"ID":"us6000njm8","Data":"2025-01-28","Hora":"14:10 local","Magnitude":5.2,"Profundidade_km":20,"Local":"Canal Beagle, Chile","Tsunami":"Não","MMI_PW":"II","Evacuados":0},
        {"ID":"us6000mhx3","Data":"2024-11-12","Hora":"07:33 local","Magnitude":4.9,"Profundidade_km":18,"Local":"Estreito de Magalhães","Tsunami":"Não","MMI_PW":"I-II","Evacuados":0},
        {"ID":"us6000lgp4","Data":"2024-09-05","Hora":"19:45 local","Magnitude":5.5,"Profundidade_km":28,"Local":"Falha Magallanes-Fagnano","Tsunami":"Não","MMI_PW":"II-III","Evacuados":0},
        {"ID":"us6000kfn7","Data":"2024-07-20","Hora":"22:17 local","Magnitude":4.6,"Profundidade_km":45,"Local":"Patagônia Austral, Chile","Tsunami":"Não","MMI_PW":"I","Evacuados":0},
        {"ID":"us6000jel1","Data":"2024-05-03","Hora":"06:02 local","Magnitude":5.1,"Profundidade_km":15,"Local":"Isla Navarino, Chile","Tsunami":"Não","MMI_PW":"II-III","Evacuados":0},
    ]
    df_cat=pd.DataFrame(CATALOG)
    st.dataframe(df_cat,use_container_width=True,height=380,
        column_config={"Magnitude":st.column_config.NumberColumn("Magnitude",format="M%.1f")})

    csv_buf=io.StringIO(); df_cat.to_csv(csv_buf,index=False)
    st.download_button(T['download_csv'],csv_buf.getvalue(),"patagonia_seismic_catalog.csv","text/csv")

    st.markdown("""<div class="info-card tect" style="margin-top:1rem;background:linear-gradient(135deg,#EEF4FF,#D8EAF8)">
      <strong style="color:#1A3A6E">📐 Escala de Magnitude × Efeitos Observados</strong><br><br>
      <div style="font-family:'DM Mono',monospace;font-size:.82rem;line-height:2.4;color:#1A3A6E">
        <b>M7.0–7.9 (Grande):</b> Danos graves · Alerta tsunami possível · MMI VII+<br>
        <b>M6.0–6.9 (Forte):</b> Danos em construções · MMI V-VII<br>
        <b>M5.0–5.9 (Moderado):</b> Sentido amplamente · Danos menores<br>
        <b>M4.0–4.9 (Leve):</b> Sentido por muitos · Sem danos significativos<br>
        <b>M2.0–3.9 (Micro):</b> Registrado instrumentalmente · Raramente sentido<br>
        <span style="color:#C0390A"><b>M7.4 Drake (02/05/2025):</b> Alerta tsunami · 1.800 evacuados · 50+ réplicas</span>
      </div></div>""",unsafe_allow_html=True)

# ── TAB 8: FONTES ────────────────────────────────────────────
with tabs[7]:
    st.markdown(f'<div class="section-label">{T["sources_label"]}</div>',unsafe_allow_html=True)
    st.markdown(f'<div class="section-title">{T["sources_title"]}</div>',unsafe_allow_html=True)
    fontes=[
        ("USGS API","USGS Earthquake Hazards Program — earthquake.usgs.gov","Catálogo sísmico em tempo real via USGS FDSN Web Service API. Gratuito, sem chave. Cobertura global desde 1900. Dados do M7.4 (ID: us7000pwkn).","#C0390A"),
        ("CSN CHILE","Centro Sismológico Nacional — sismologia.cl","Rede sismográfica nacional chilena. 120+ estações. Dados de intensidade MMI para Puerto Williams, Punta Arenas e Puerto Natales.","#8B2515"),
        ("INPRES","Instituto Nacional de Prevención Sísmica — inpres.gob.ar","Catálogo sísmico argentino. Monitoramento de Rio Gallegos, Rio Grande, Ushuaia e El Calafate.","#F5A623"),
        ("NOAA PTWC","NOAA Pacific Tsunami Warning Center","Emitiu o alerta de tsunami para o M7.4 de 02/05/2025. Fonte do dado de ~1.800 evacuados.","#2555A0"),
        ("WATCHERS","The Watchers — watchers.news","Relatório detalhado do 2025 Drake Passage Earthquake (M7.4). Dados de réplicas, intensidades e impacto nas comunidades.","#1B3A1E"),
        ("SENAPRED","Servicio Nacional de Prevención y Respuesta ante Desastres — senapred.cl","Alertas oficiais, evacuações e gestão de emergências para o evento de 02/05/2025 em Puerto Williams.","#C47D0E"),
        ("CAMPO","Observação Pessoal — Amauri Almeida · Puerto Williams · 02/05/2025","Testemunha direta do M7.4. Registro fotográfico e experiência de campo durante o evento sísmico, alerta de tsunami e sequência de réplicas.","#8B2515"),
    ]
    for sigla,nome,desc,cor in fontes:
        st.markdown(f"""<div class="info-card" style="border-left-color:{cor}">
          <div style="display:flex;align-items:flex-start;gap:1rem">
            <div style="background:{cor};color:white;font-family:'DM Mono',monospace;font-size:.6rem;padding:4px 7px;border-radius:4px;white-space:nowrap;flex-shrink:0;margin-top:2px;font-weight:bold;text-align:center;min-width:70px">{sigla}</div>
            <div><div style="font-weight:500;font-size:.9rem;color:var(--quake-mid)">{nome}</div>
            <div style="font-size:.82rem;color:var(--warm-gray);margin-top:.2rem">{desc}</div></div>
          </div></div>""",unsafe_allow_html=True)

    st.markdown(f"<br><div class='section-label'>{T['tech_label']}</div>",unsafe_allow_html=True)
    techs=["Python 3.11","Streamlit","Plotly","Folium","Pandas","NumPy","USGS FDSN API","Requests"]
    st.markdown(''.join([f'<span class="source-badge">{t}</span>' for t in techs]),unsafe_allow_html=True)
    st.markdown(f"""<div class="footer-wrap" style="margin-top:2rem">
      <div class="footer-title">{T['footer_title']}</div>
      <p style="margin:.5rem 0;font-size:.9rem">{T['footer_desc']}</p>
      <p style="margin:1rem 0 .5rem;font-size:.85rem;opacity:.7">
        {T['footer_links']} &nbsp;|&nbsp;
        🌐 <a href="https://amaurialmeida.github.io/environmental-portfolio/" style="color:#F5A623">Portfólio</a> &nbsp;|&nbsp;
        🐙 <a href="https://github.com/amaurialmeida" style="color:#F5A623">GitHub</a></p>
      <p style="font-size:.75rem;opacity:.5;margin:0">© 2025–2026 · Sismologia · Patagônia · Puerto Williams, Chile</p>
    </div>""",unsafe_allow_html=True)
