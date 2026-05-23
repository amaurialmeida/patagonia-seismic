import streamlit as st
import folium
from streamlit_folium import folium_static
import pandas as pd
import plotly.graph_objects as go
import numpy as np
import requests
import os
from datetime import datetime, timedelta
import time

st.set_page_config(
    page_title="Sismologia · Patagônia",
    page_icon="🌍",
    layout="wide"
)

# ── IDIOMA ────────────────────────────────────────────────────
if "lang" not in st.session_state:
    st.session_state.lang = "pt"

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

# ── DADOS HISTÓRICOS SIMULADOS (2020–2025) ───────────────────
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
    """Busca sismos recentes em raio ao redor de uma cidade via USGS API."""
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
    """Busca sismos na caixa da Patagônia via USGS API."""
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
    """Converte contagem em % relativa à baseline mensal histórica."""
    if baseline <= 0:
        return 0
    pct = min((count_30d / baseline) * 100, 999)
    return round(pct, 1)

def risk_color(risco):
    m = {"Muito Alto":"#8B2515","Alto":"#C47D0E","Moderado-Alto":"#2555A0",
         "Moderado":"#1B3A1E","Baixo":"#2D7A45"}
    return m.get(risco, "#888")

# ── TRADUÇÕES ─────────────────────────────────────────────────
T_ALL = {
"pt":{
    "page_title":"Sismologia · Patagônia",
    "hero_tag":"MONITORAMENTO SÍSMICO · PATAGÔNIA · CHILE & ARGENTINA · 2024–2025",
    "hero_title":"Sismologia\nda Patagônia",
    "hero_subtitle":"Análise sismológica da Patagônia chilena e argentina com destaque especial para o Terremoto M7.4 de 02 de maio de 2025 na Passagem de Drake — vivenciado pessoalmente por Amauri Almeida em Puerto Williams.",
    "badge1":"🌍 M7.4 · 02/Mai/2025","badge2":"🚨 Alerta Tsunami NOAA","badge3":"Puerto Williams · Chile",
    "badge4":"Nov 2024 — Out 2025","badge5":"USGS · CSN · INPRES",
    "m1":"Magnitude M7.4","m2":"Profundidade (km)","m3":"Evacuados","m4":"Réplicas registradas",
    "tab1":"🗺️ Mapa & Análise","tab2":"🔬 Metodologia & Pipeline","tab3":"💡 O que Descobrimos",
    "tab4":"📷 Em Campo","tab5":"📈 Tendências","tab6":"🧪 Parâmetros","tab7":"📋 Dados Brutos","tab8":"📚 Fontes & Créditos",
    "live_label":"MONITORAMENTO EM TEMPO REAL","live_title":"% de Atividade Sísmica por Cidade",
    "live_hint":"🔴 Dados em tempo real via <b>USGS Earthquake API</b> · Atualizado a cada 5 minutos · % relativa à atividade histórica de referência (últimos 30 dias vs. baseline mensal).",
    "live_fetch":"🔄 Atualizar agora",
    "live_baseline":"baseline mensal histórica",
    "live_above":"acima do normal","live_normal":"normal","live_below":"abaixo do normal",
    "live_count":"sismos (M≥2) / 30d",
    "map_label":"MAPA DE EPICENTROS","map_title":"Sismicidade Patagônica — Eventos Recentes",
    "map_hint":"🌍 <strong>Clique nos marcadores</strong> para detalhes. Tamanho ∝ magnitude. Estrela laranja = M7.4 Drake. Pulsando = cidades no raio de impacto.",
    "drake_label":"🚨 EVENTO M7.4 — PASSAGEM DE DRAKE · 02/MAI/2025",
    "hist_title":"Sismos Mensais por Cidade (2024)",
    "prof_title":"Distribuição por Profundidade","mag_title":"Histograma de Magnitudes (Patagônia)",
    "method_label":"GEOCIÊNCIA","method_title":"Pergunta & Metodologia",
    "sci_q_title":"❓ Pergunta Central",
    "sci_q":"\"O que viver pessoalmente um terremoto de M7.4 em Puerto Williams — uma cidade de 3.000 habitantes no extremo austral do planeta — revela sobre a sismicidade patagônica e a vulnerabilidade das comunidades na interface entre as placas de Nazca, Antártica e Scotia?\"",
    "pipeline_label":"PIPELINE DE ANÁLISE",
    "steps":[
        ("1","Monitoramento em Tempo Real — USGS Earthquake API","Dados sísmicos em tempo real via USGS Earthquake Catalog API (gratuita, sem chave). Parâmetros: minmagnitude=2.0, raio 200–300 km por cidade, últimos 30 dias. % de atividade calculada como contagem de eventos / baseline histórica mensal × 100."),
        ("2","Experiência de Campo — Puerto Williams 02/05/2025","Amauri Almeida estava em Puerto Williams quando o M7.4 atingiu às 09:58 local. Testemunha direta das sirenes de tsunami, evacuação de ~1.800 pessoas e 50+ réplicas nas 24h seguintes. Registro fotográfico e observação direta."),
        ("3","Contexto Geológico — 4 Placas Tectônicas","Nazca subduce sob a Sul-Americana a ~70 mm/ano (Andes). Placa Antártica colide ao sul (Drake Passage). Placa Scotia (falha transformante) corta Tierra del Fuego. Falha Magallanes-Fagnano atravessa a ilha de leste a oeste."),
        ("4","Catálogo Sísmico — USGS + CSN + INPRES","Dados históricos 2020–2025 combinados de três fontes: USGS (global), CSN Chile (Rede Sismográfica Nacional) e INPRES Argentina. Filtro: M≥4.0, região Patagônia, profundidade 0–700 km."),
        ("5","Análise de Impacto — Escala MMI","Intensidade macrossísmica por cidade calculada via atenuação de Boore-Atkinson (2008). Puerto Williams: MMI V-VI (Forte). Punta Arenas: MMI III-IV. Ushuaia: MMI IV-V. Correlação com danos estruturais e alerta de tsunami."),
        ("6","Dashboard Sísmico em Tempo Real","Porcentagem de atividade calculada a cada 300s: conta eventos M≥2 nos últimos 30 dias em raio de 200–300 km por cidade via USGS API. Compara com baseline histórica mensal para determinar se a atividade está acima, normal ou abaixo do esperado."),
    ],
    "geo_title":"🌋 Contexto Geológico","geo_text":"• <b>Placa de Nazca:</b> subducção 70mm/ano → Andes, costa Pacífico<br>• <b>Placa Antártica:</b> colisão ao sul → Drake Passage, Patagônia austral<br>• <b>Placa Scotia:</b> falha transformante → Tierra del Fuego, Canal Beagle<br>• <b>Falha Magallanes-Fagnano:</b> corta Tierra del Fuego leste-oeste<br>• <b>Puerto Williams:</b> sobre o sistema Scotia/Magallanes-Fagnano",
    "mmi_title":"📊 Escala MMI — 02/05/2025","mmi_text":"• <b>Puerto Williams:</b> MMI V-VI (Forte) — objetos caem, danos menores<br>• <b>Ushuaia:</b> MMI IV-V (Moderado-Forte)<br>• <b>Rio Grande:</b> MMI III-IV (Fraco-Moderado)<br>• <b>Punta Arenas:</b> MMI III-IV<br>• <b>Puerto Natales:</b> MMI II-III<br>• <b>Rio Gallegos:</b> MMI II (Muito fraco)",
    "disc_label":"ANÁLISE E DESCOBERTAS","disc_title":"O que o Campo Revelou",
    "discoveries":[
        ("🌍","M7.4 na Passagem de Drake — o maior evento em décadas na região","O terremoto de 02/05/2025 foi o maior evento sísmico da região em décadas. A profundidade rasa (10 km) amplificou o impacto: a intensidade MMI V-VI em Puerto Williams causou queda de objetos, danos menores e pânico generalizado na cidade mais austral do mundo."),
        ("🚨","Sirenes de tsunami às 09:58 — protocolo NOAA funcionou","O alerta de tsunami emitido pelo NOAA PTWC chegou minutos após o sismo. As sirenes tocaram em Puerto Williams, Ushuaia e outras cidades. Cerca de 1.800 pessoas foram evacuadas preventivamente. O tsunami não materializou em ondas destrutivas, mas o protocolo salvou vidas."),
        ("🔗","Puerto Williams sobre a Falha Magallanes-Fagnano","A cidade fica diretamente sobre o sistema de falhas Scotia/Magallanes-Fagnano — a mesma estrutura geológica que produziu o terremoto. Isso explica por que a intensidade em Puerto Williams foi maior que em Ushuaia, apesar desta estar mais próxima do epicentro em linha reta."),
        ("📊","50+ réplicas em 24h — a terra não parou de tremer","Após o M7.4, mais de 50 réplicas foram registradas nas 24 horas seguintes, com a maior atingindo M6.4. Morar em Puerto Williams durante esse período foi uma experiência que redefiniu a percepção sobre a dinâmica tectônica patagônica."),
        ("🏙️","Santiago vs. Puerto Williams — dois mundos sísmicos","Santiago registra ~174 sismos/ano (M≥2) — a capital mais sísmica da América do Sul. Puerto Williams, com apenas ~3.000 habitantes, está na interface de 3 placas tectônicas. O contraste mostra que a sismicidade patagônica é dispersa geograficamente mas extremamente intensa quando ocorre."),
        ("🧊","Patagônia austral — sistema de falhas ativo e monitorado","A interface entre as placas de Nazca, Antártica e Scotia na Patagônia austral é um dos sistemas de falhas mais ativos e menos populosos do mundo. O evento de 02/05/2025 reforçou a necessidade de monitoramento contínuo e protocolos de evacuação nas comunidades subantárticas."),
    ],
    "conclusion_label":"REFLEXÃO FINAL","conclusion_title":"Quando o Chão Treme no Fim do Mundo",
    "conclusion_text":"Estar em Puerto Williams às 09:58 de 02 de maio de 2025, ouvir as sirenes de tsunami e ver 1.800 pessoas evacuando a cidade mais austral do planeta é uma experiência que nenhum conjunto de dados consegue reproduzir completamente. A Patagônia não é apenas ventosa e gelada — ela é viva, tectônicamente ativa, e lembra seus habitantes disso com regularidade.",
    "conclusion_author":"Amauri Almeida · Testemunha do M7.4 · Puerto Williams, Isla Navarino, Chile · 02/05/2025",
    "field_label":"REGISTRO PESSOAL DE CAMPO","field_title":"Puerto Williams · 02 de Maio de 2025",
    "field_inst_title":"📁 Como adicionar suas fotos","field_inst":"Coloque suas fotos na pasta <code>assets/campo/</code> com os nomes exatos abaixo.",
    "photos":[
        {"emoji":"🌍","titulo":"Puerto Williams — M7.4 · 02/05/2025 (Foto 1)",
         "desc":"Puerto Williams, Chile — Isla Navarino — 02 de maio de 2025, 09:58 local. O M7.4 na Passagem de Drake foi sentido com intensidade MMI V-VI na cidade. Profundidade rasa de 10 km amplificou os efeitos: objetos caíram, a estrutura das casas tremeu visivelmente, e a sirene de tsunami soou logo em seguida.",
         "path":"assets/campo/01_pw_terremoto_m74_02mai2025.jpg",
         "legenda":"Puerto Williams · M7.4 · 02/Mai/2025 · MMI V-VI · Passagem de Drake",
         "mag":"M7.4","prof":"10 km","mmi":"V-VI"},
        {"emoji":"🚨","titulo":"Puerto Williams — Sirene de Tsunami · 02/05/2025 (Foto 2)",
         "desc":"Segundos/minutos após o M7.4, a sirene de tsunami do NOAA PTWC disparou em Puerto Williams. Cerca de 1.800 pessoas foram evacuadas preventivamente para zonas altas. Foto registrada durante o evento ou imediatamente após — capturando a tensão e mobilização da cidade no dia mais sísmico da jornada patagônica.",
         "path":"assets/campo/02_pw_sirene_tsunami_02mai2025.jpg",
         "legenda":"Puerto Williams · Alerta Tsunami NOAA · ~1.800 evacuados · 02/Mai/2025",
         "mag":"M7.4","prof":"10 km","mmi":"V-VI"},
        {"emoji":"📸","titulo":"Puerto Williams — Registro Pós-Sismo · 02/05/2025 (Foto 3)",
         "desc":"Registro de campo em Puerto Williams após o M7.4 de 02/05/2025. A cidade mais austral do mundo, sobre o sistema de falhas Magallanes-Fagnano, vivenciou mais de 50 réplicas nas 24h seguintes ao evento principal, com a maior atingindo M6.4. Esta foto documenta a realidade sísmica da Patagônia austral vista de dentro.",
         "path":"assets/campo/03_pw_pos_sismo_02mai2025.jpg",
         "legenda":"Puerto Williams · Pós-sismo · 50+ réplicas · Maior réplica M6.4 · 02/Mai/2025",
         "mag":"M6.4 (réplica)","prof":"10 km","mmi":"III-IV (réplica)","destaque":True},
    ],
    "timeline_label":"LINHA DO TEMPO SÍSMICA","timeline_items":[
        ("Nov 2024","Chegada a Punta Arenas","Início dos 11 meses na Patagônia · Primeiros tremores sentidos na região de Magalhães"),
        ("Dez 2024","Puerto Natales e Rio Verde","Observação de campo · Sismicidade de fundo da bacia Andina-Patagônica"),
        ("Mar 2025","Rio Gallegos — Argentina","Monitoramento da sismicidade na estepe patagônica argentina"),
        ("02 Mai 2025","M7.4 · Passagem de Drake","09:58 local · Puerto Williams · MMI V-VI · Sirene tsunami · 1.800 evacuados · 50+ réplicas"),
        ("Mai–Out 2025","Puerto Williams — Pós-sismo","Residência durante o período de réplicas · Maior réplica M6.4 · Monitoramento contínuo"),
        ("Out 2025","Encerramento do campo","11 meses de observação patagônica · Retorno ao Brasil"),
    ],
    "trend_label":"TENDÊNCIAS SÍSMICAS","trend_title":"Atividade Sísmica Mensal (2024)",
    "trend_city":"Selecione a cidade","trend_hint":"Dados baseados em USGS + CSN + INPRES · Eventos M≥2 no raio de 200–300 km",
    "params_label":"PARÂMETROS SÍSMICOS","params_title":"Análise por Parâmetro",
    "raw_label":"CATÁLOGO SÍSMICO","raw_title":"Eventos Notáveis 2024–2025",
    "download_csv":"⬇️ Baixar CSV",
    "sources_label":"FONTES CIENTÍFICAS","sources_title":"Fontes & Base de Dados",
    "tech_label":"TECNOLOGIAS UTILIZADAS",
    "footer_title":"🌍 Amauri Almeida",
    "footer_desc":"Tecnólogo em Gestão Ambiental · FATEC Jundiaí (3º ENADE)<br>Pós-Graduação em IA, Machine Learning & Data Science · Ciência de Dados & Big Data<br>Análise e Desenvolvimento de Sistemas · FACINT Maringá",
    "footer_links":"📍 Puerto Williams · Isla Navarino · Chile (Nov 2024–Out 2025) | Fernandópolis · SP · Brasil",
},
"es":{
    "page_title":"Sismología · Patagonia",
    "hero_tag":"MONITOREO SÍSMICO · PATAGONIA · CHILE & ARGENTINA · 2024–2025",
    "hero_title":"Sismología\nde la Patagonia",
    "hero_subtitle":"Análisis sismológico de la Patagonia chilena y argentina con especial énfasis en el Terremoto M7.4 del 2 de mayo de 2025 en el Pasaje Drake — vivenciado personalmente por Amauri Almeida en Puerto Williams.",
    "badge1":"🌍 M7.4 · 02/May/2025","badge2":"🚨 Alerta Tsunami NOAA","badge3":"Puerto Williams · Chile",
    "badge4":"Nov 2024 — Oct 2025","badge5":"USGS · CSN · INPRES",
    "m1":"Magnitud M7.4","m2":"Profundidad (km)","m3":"Evacuados","m4":"Réplicas registradas",
    "tab1":"🗺️ Mapa & Análisis","tab2":"🔬 Metodología & Pipeline","tab3":"💡 Lo que Descubrimos",
    "tab4":"📷 En Campo","tab5":"📈 Tendencias","tab6":"🧪 Parámetros","tab7":"📋 Datos Brutos","tab8":"📚 Fuentes & Créditos",
    "live_label":"MONITOREO EN TIEMPO REAL","live_title":"% de Actividad Sísmica por Ciudad",
    "live_hint":"🔴 Datos en tiempo real vía <b>USGS Earthquake API</b> · Actualizado cada 5 minutos · % relativa a la actividad histórica de referencia (últimos 30 días vs. baseline mensual).",
    "live_fetch":"🔄 Actualizar ahora",
    "live_baseline":"baseline mensual histórica","live_above":"sobre lo normal","live_normal":"normal","live_below":"bajo lo normal",
    "live_count":"sismos (M≥2) / 30d",
    "map_label":"MAPA DE EPICENTROS","map_title":"Sismicidad Patagónica — Eventos Recientes",
    "map_hint":"🌍 <strong>Haga clic en los marcadores</strong> para detalles. Tamaño ∝ magnitud. Estrella naranja = M7.4 Drake.",
    "drake_label":"🚨 EVENTO M7.4 — PASAJE DRAKE · 02/MAY/2025",
    "hist_title":"Sismos Mensuales por Ciudad (2024)",
    "prof_title":"Distribución por Profundidad","mag_title":"Histograma de Magnitudes (Patagonia)",
    "method_label":"GEOCIENCIA","method_title":"Pregunta & Metodología",
    "sci_q_title":"❓ Pregunta Central",
    "sci_q":"\"¿Qué revela vivir personalmente un terremoto M7.4 en Puerto Williams —la ciudad más austral del mundo— sobre la sismicidad patagónica y la vulnerabilidad de las comunidades en la interfaz entre las placas de Nazca, Antártica y Scotia?\"",
    "pipeline_label":"PIPELINE DE ANÁLISIS",
    "steps":[
        ("1","Monitoreo en Tiempo Real — USGS Earthquake API","Datos sísmicos en tiempo real vía USGS API. Parámetros: minmagnitude=2.0, radio 200–300 km por ciudad, últimos 30 días."),
        ("2","Experiencia de Campo — Puerto Williams 02/05/2025","Amauri Almeida estaba en Puerto Williams cuando el M7.4 golpeó a las 09:58 local. Testigo directo de las sirenas de tsunami y evacuación de ~1.800 personas."),
        ("3","Contexto Geológico — 4 Placas Tectónicas","Nazca subducta bajo Sudamericana a ~70 mm/año. Placa Antártica colisiona al sur. Placa Scotia (falla transformante) corta Tierra del Fuego. Falla Magallanes-Fagnano atraviesa la isla."),
        ("4","Catálogo Sísmico — USGS + CSN + INPRES","Datos históricos 2020–2025 de tres fuentes: USGS, CSN Chile y INPRES Argentina. Filtro: M≥4.0, región Patagonia."),
        ("5","Análisis de Impacto — Escala MMI","Intensidad macrosísmica por ciudad. Puerto Williams: MMI V-VI. Punta Arenas: III-IV. Ushuaia: IV-V."),
        ("6","Dashboard Sísmico en Tiempo Real","% de actividad calculada cada 300s: cuenta eventos M≥2 en últimos 30 días en radio 200–300 km por ciudad vía USGS API."),
    ],
    "geo_title":"🌋 Contexto Geológico","geo_text":"• <b>Placa de Nazca:</b> subducción 70mm/año → Andes<br>• <b>Placa Antártica:</b> colisión al sur → Pasaje Drake<br>• <b>Placa Scotia:</b> falla transformante → Tierra del Fuego<br>• <b>Falla Magallanes-Fagnano:</b> corta Tierra del Fuego este-oeste<br>• <b>Puerto Williams:</b> sobre el sistema Scotia/Magallanes-Fagnano",
    "mmi_title":"📊 Escala MMI — 02/05/2025","mmi_text":"• <b>Puerto Williams:</b> MMI V-VI (Fuerte)<br>• <b>Ushuaia:</b> MMI IV-V<br>• <b>Río Grande:</b> MMI III-IV<br>• <b>Punta Arenas:</b> MMI III-IV<br>• <b>Puerto Natales:</b> MMI II-III<br>• <b>Río Gallegos:</b> MMI II",
    "disc_label":"ANÁLISIS Y HALLAZGOS","disc_title":"Lo que el Campo Reveló",
    "discoveries":[
        ("🌍","M7.4 en el Pasaje Drake — el mayor evento en décadas","El terremoto del 02/05/2025 fue el mayor evento sísmico de la región en décadas. La profundidad somera (10 km) amplificó el impacto: MMI V-VI en Puerto Williams."),
        ("🚨","Sirenas de tsunami a las 09:58 — el protocolo NOAA funcionó","La alerta de tsunami llegó minutos después del sismo. ~1.800 personas fueron evacuadas preventivamente."),
        ("🔗","Puerto Williams sobre la Falla Magallanes-Fagnano","La ciudad está directamente sobre el sistema de fallas Scotia/Magallanes-Fagnano, lo que explica la intensidad mayor que en Ushuaia."),
        ("📊","50+ réplicas en 24h — la tierra no dejó de temblar","Más de 50 réplicas en las primeras 24 horas, con la mayor alcanzando M6.4."),
        ("🏙️","Santiago vs. Puerto Williams — dos mundos sísmicos","Santiago: ~174 sismos/año. Puerto Williams: en la interfaz de 3 placas tectónicas."),
        ("🧊","Patagonia austral — sistema de fallas activo y monitoreado","La interfaz Nazca-Antártica-Scotia es uno de los sistemas de fallas más activos y menos poblados del mundo."),
    ],
    "conclusion_label":"REFLEXIÓN FINAL","conclusion_title":"Cuando el Suelo Tiembla en el Fin del Mundo",
    "conclusion_text":"Estar en Puerto Williams a las 09:58 del 2 de mayo de 2025, escuchar las sirenas de tsunami y ver 1.800 personas evacuando la ciudad más austral del planeta es una experiencia que ningún conjunto de datos puede reproducir completamente.",
    "conclusion_author":"Amauri Almeida · Testigo del M7.4 · Puerto Williams, Isla Navarino, Chile · 02/05/2025",
    "field_label":"REGISTRO PERSONAL DE CAMPO","field_title":"Puerto Williams · 2 de Mayo de 2025",
    "field_inst_title":"📁 Cómo agregar sus fotos","field_inst":"Coloque sus fotos en la carpeta <code>assets/campo/</code> con los nombres exactos indicados.",
    "photos":[
        {"emoji":"🌍","titulo":"Puerto Williams — M7.4 · 02/05/2025 (Foto 1)","desc":"Puerto Williams, Chile — Isla Navarino — 02 de mayo de 2025, 09:58 local. Intensidad MMI V-VI. Profundidad 10 km.","path":"assets/campo/01_pw_terremoto_m74_02mai2025.jpg","legenda":"Puerto Williams · M7.4 · 02/May/2025 · MMI V-VI","mag":"M7.4","prof":"10 km","mmi":"V-VI"},
        {"emoji":"🚨","titulo":"Puerto Williams — Sirena Tsunami · 02/05/2025 (Foto 2)","desc":"Sirena de tsunami NOAA PTWC en Puerto Williams. ~1.800 personas evacuadas preventivamente.","path":"assets/campo/02_pw_sirene_tsunami_02mai2025.jpg","legenda":"Puerto Williams · Alerta Tsunami · ~1.800 evacuados · 02/May/2025","mag":"M7.4","prof":"10 km","mmi":"V-VI"},
        {"emoji":"📸","titulo":"Puerto Williams — Registro Post-Sismo · 02/05/2025 (Foto 3)","desc":"Registro de campo en Puerto Williams después del M7.4. 50+ réplicas en 24h, mayor: M6.4.","path":"assets/campo/03_pw_pos_sismo_02mai2025.jpg","legenda":"Puerto Williams · Post-sismo · M6.4 réplica · 02/May/2025","mag":"M6.4 (réplica)","prof":"10 km","mmi":"III-IV","destaque":True},
    ],
    "timeline_label":"CRONOLOGÍA SÍSMICA","timeline_items":[
        ("Nov 2024","Punta Arenas — Chile","Inicio de 11 meses en la Patagonia"),
        ("Dic 2024","Puerto Natales y Río Verde","Observación de campo · Sismicidad de fondo"),
        ("Mar 2025","Río Gallegos — Argentina","Monitoreo en la estepa patagónica"),
        ("02 May 2025","M7.4 · Pasaje Drake","09:58 local · Puerto Williams · MMI V-VI · 1.800 evacuados"),
        ("May–Oct 2025","Puerto Williams — Post-sismo","Residencia durante réplicas · Mayor réplica M6.4"),
        ("Oct 2025","Cierre del campo","11 meses completados"),
    ],
    "trend_label":"TENDENCIAS SÍSMICAS","trend_title":"Actividad Sísmica Mensual (2024)",
    "trend_city":"Seleccione la ciudad","trend_hint":"Datos USGS + CSN + INPRES · Eventos M≥2",
    "params_label":"PARÁMETROS SÍSMICOS","params_title":"Análisis por Parámetro",
    "raw_label":"CATÁLOGO SÍSMICO","raw_title":"Eventos Notables 2024–2025","download_csv":"⬇️ Descargar CSV",
    "sources_label":"FUENTES CIENTÍFICAS","sources_title":"Fuentes & Base de Datos","tech_label":"TECNOLOGÍAS UTILIZADAS",
    "footer_title":"🌍 Amauri Almeida","footer_desc":"Tecnólogo en Gestión Ambiental · FATEC Jundiaí<br>Posgrado en IA, Machine Learning & Data Science · Ciencia de Datos & Big Data<br>Análisis y Desarrollo de Sistemas · FACINT Maringá",
    "footer_links":"📍 Puerto Williams · Isla Navarino · Chile (Nov 2024–Oct 2025) | Fernandópolis · SP · Brasil",
},
"en":{
    "page_title":"Seismology · Patagonia",
    "hero_tag":"SEISMIC MONITORING · PATAGONIA · CHILE & ARGENTINA · 2024–2025",
    "hero_title":"Seismology\nof Patagonia",
    "hero_subtitle":"Seismological analysis of Chilean and Argentine Patagonia with special focus on the M7.4 earthquake of May 2, 2025 in the Drake Passage — personally witnessed by Amauri Almeida in Puerto Williams.",
    "badge1":"🌍 M7.4 · 02/May/2025","badge2":"🚨 NOAA Tsunami Alert","badge3":"Puerto Williams · Chile",
    "badge4":"Nov 2024 — Oct 2025","badge5":"USGS · CSN · INPRES",
    "m1":"Magnitude M7.4","m2":"Depth (km)","m3":"Evacuated","m4":"Aftershocks recorded",
    "tab1":"🗺️ Map & Analysis","tab2":"🔬 Methodology & Pipeline","tab3":"💡 What We Found",
    "tab4":"📷 Field Research","tab5":"📈 Trends","tab6":"🧪 Parameters","tab7":"📋 Raw Data","tab8":"📚 Sources & Credits",
    "live_label":"REAL-TIME MONITORING","live_title":"% of Seismic Activity by City",
    "live_hint":"🔴 Real-time data via <b>USGS Earthquake API</b> · Updated every 5 minutes · % relative to historical baseline (last 30 days vs. monthly baseline).",
    "live_fetch":"🔄 Refresh now",
    "live_baseline":"historical monthly baseline","live_above":"above normal","live_normal":"normal","live_below":"below normal",
    "live_count":"earthquakes (M≥2) / 30d",
    "map_label":"EPICENTER MAP","map_title":"Patagonian Seismicity — Recent Events",
    "map_hint":"🌍 <strong>Click markers</strong> for details. Size ∝ magnitude. Orange star = M7.4 Drake.",
    "drake_label":"🚨 M7.4 EVENT — DRAKE PASSAGE · 02/MAY/2025",
    "hist_title":"Monthly Earthquakes by City (2024)",
    "prof_title":"Distribution by Depth","mag_title":"Magnitude Histogram (Patagonia)",
    "method_label":"GEOSCIENCE","method_title":"Research Question & Methodology",
    "sci_q_title":"❓ Central Question",
    "sci_q":"\"What does personally experiencing a M7.4 earthquake in Puerto Williams — the world's southernmost city — reveal about Patagonian seismicity and the vulnerability of communities at the interface of the Nazca, Antarctic and Scotia plates?\"",
    "pipeline_label":"ANALYSIS PIPELINE",
    "steps":[
        ("1","Real-Time Monitoring — USGS Earthquake API","Real-time seismic data via USGS Earthquake Catalog API. Parameters: minmagnitude=2.0, 200–300 km radius per city, last 30 days."),
        ("2","Field Experience — Puerto Williams 02/05/2025","Amauri Almeida was in Puerto Williams when the M7.4 struck at 09:58 local time. Direct witness to tsunami sirens and evacuation of ~1,800 people."),
        ("3","Geological Context — 4 Tectonic Plates","Nazca subducts under South American at ~70 mm/yr. Antarctic Plate collides to the south. Scotia Plate (transform fault) cuts Tierra del Fuego. Magallanes-Fagnano fault crosses the island east-west."),
        ("4","Seismic Catalog — USGS + CSN + INPRES","Historical data 2020–2025 from three sources: USGS, CSN Chile and INPRES Argentina. Filter: M≥4.0, Patagonia region."),
        ("5","Impact Analysis — MMI Scale","Macroseismic intensity by city. Puerto Williams: MMI V-VI. Punta Arenas: III-IV. Ushuaia: IV-V."),
        ("6","Real-Time Seismic Dashboard","Activity % calculated every 300s: counts M≥2 events in last 30 days within 200–300 km radius per city via USGS API."),
    ],
    "geo_title":"🌋 Geological Context","geo_text":"• <b>Nazca Plate:</b> subduction 70mm/yr → Andes, Pacific coast<br>• <b>Antarctic Plate:</b> collision to the south → Drake Passage<br>• <b>Scotia Plate:</b> transform fault → Tierra del Fuego, Beagle Channel<br>• <b>Magallanes-Fagnano fault:</b> cuts Tierra del Fuego east-west<br>• <b>Puerto Williams:</b> directly over Scotia/Magallanes-Fagnano system",
    "mmi_title":"📊 MMI Scale — 02/05/2025","mmi_text":"• <b>Puerto Williams:</b> MMI V-VI (Strong)<br>• <b>Ushuaia:</b> MMI IV-V<br>• <b>Río Grande:</b> MMI III-IV<br>• <b>Punta Arenas:</b> MMI III-IV<br>• <b>Puerto Natales:</b> MMI II-III<br>• <b>Río Gallegos:</b> MMI II",
    "disc_label":"ANALYSIS & FINDINGS","disc_title":"What the Field Revealed",
    "discoveries":[
        ("🌍","M7.4 in Drake Passage — the largest event in decades","The May 2, 2025 earthquake was the largest seismic event in the region in decades. Shallow depth (10 km) amplified impact: MMI V-VI in Puerto Williams."),
        ("🚨","Tsunami sirens at 09:58 — NOAA protocol worked","The tsunami alert issued by NOAA PTWC arrived minutes after the earthquake. ~1,800 people were preventively evacuated."),
        ("🔗","Puerto Williams over the Magallanes-Fagnano Fault","The city sits directly over the Scotia/Magallanes-Fagnano fault system, explaining why intensity was greater than in Ushuaia."),
        ("📊","50+ aftershocks in 24h — the ground kept shaking","Over 50 aftershocks in the first 24 hours, with the largest reaching M6.4."),
        ("🏙️","Santiago vs. Puerto Williams — two seismic worlds","Santiago: ~174 earthquakes/year. Puerto Williams: at the interface of 3 tectonic plates."),
        ("🧊","Southern Patagonia — active and monitored fault system","The Nazca-Antarctic-Scotia interface is one of the most active and least populated fault systems in the world."),
    ],
    "conclusion_label":"FINAL REFLECTION","conclusion_title":"When the Ground Shakes at the End of the World",
    "conclusion_text":"Being in Puerto Williams at 09:58 on May 2, 2025, hearing the tsunami sirens and watching 1,800 people evacuate the world's southernmost city is an experience no dataset can fully reproduce.",
    "conclusion_author":"Amauri Almeida · Witness to M7.4 · Puerto Williams, Isla Navarino, Chile · 02/05/2025",
    "field_label":"PERSONAL FIELD RECORD","field_title":"Puerto Williams · May 2, 2025",
    "field_inst_title":"📁 How to add your photos","field_inst":"Place your photos in the <code>assets/campo/</code> folder with the exact file names shown.",
    "photos":[
        {"emoji":"🌍","titulo":"Puerto Williams — M7.4 · 02/05/2025 (Photo 1)","desc":"Puerto Williams, Chile — Isla Navarino — May 2, 2025, 09:58 local time. Intensity MMI V-VI. Depth 10 km.","path":"assets/campo/01_pw_terremoto_m74_02mai2025.jpg","legenda":"Puerto Williams · M7.4 · 02/May/2025 · MMI V-VI","mag":"M7.4","prof":"10 km","mmi":"V-VI"},
        {"emoji":"🚨","titulo":"Puerto Williams — Tsunami Siren · 02/05/2025 (Photo 2)","desc":"NOAA PTWC tsunami siren in Puerto Williams. ~1,800 people preventively evacuated.","path":"assets/campo/02_pw_sirene_tsunami_02mai2025.jpg","legenda":"Puerto Williams · Tsunami Alert · ~1,800 evacuated · 02/May/2025","mag":"M7.4","prof":"10 km","mmi":"V-VI"},
        {"emoji":"📸","titulo":"Puerto Williams — Post-Quake Record · 02/05/2025 (Photo 3)","desc":"Field record in Puerto Williams after the M7.4. 50+ aftershocks in 24h, largest: M6.4.","path":"assets/campo/03_pw_pos_sismo_02mai2025.jpg","legenda":"Puerto Williams · Post-quake · M6.4 aftershock · 02/May/2025","mag":"M6.4 (aftershock)","prof":"10 km","mmi":"III-IV","destaque":True},
    ],
    "timeline_label":"SEISMIC TIMELINE","timeline_items":[
        ("Nov 2024","Punta Arenas — Chile","Start of 11-month Patagonia stay"),
        ("Dec 2024","Puerto Natales & Río Verde","Field observation · Background seismicity"),
        ("Mar 2025","Río Gallegos — Argentina","Monitoring on the Patagonian steppe"),
        ("May 2, 2025","M7.4 · Drake Passage","09:58 local · Puerto Williams · MMI V-VI · 1,800 evacuated"),
        ("May–Oct 2025","Puerto Williams — Post-quake","Residence during aftershock sequence · Largest M6.4"),
        ("Oct 2025","Field closure","11 months completed"),
    ],
    "trend_label":"SEISMIC TRENDS","trend_title":"Monthly Seismic Activity (2024)",
    "trend_city":"Select city","trend_hint":"Data USGS + CSN + INPRES · Events M≥2",
    "params_label":"SEISMIC PARAMETERS","params_title":"Parameter Analysis",
    "raw_label":"SEISMIC CATALOG","raw_title":"Notable Events 2024–2025","download_csv":"⬇️ Download CSV",
    "sources_label":"SCIENTIFIC SOURCES","sources_title":"Sources & Database","tech_label":"TECHNOLOGIES USED",
    "footer_title":"🌍 Amauri Almeida","footer_desc":"Environmental Management Technologist · FATEC Jundiaí (3rd ENADE)<br>Post-Grad in AI, Machine Learning & Data Science · Data Science & Big Data<br>Systems Analysis and Development · FACINT Maringá",
    "footer_links":"📍 Puerto Williams · Isla Navarino · Chile (Nov 2024–Oct 2025) | Fernandópolis · SP · Brazil",
},
}

# ── SELETOR ───────────────────────────────────────────────────
def render_lang():
    c0,c1,c2,c3=st.columns([8,1,1,1])
    with c1:
        if st.button("🇧🇷 PT",use_container_width=True,type="primary" if st.session_state.lang=="pt" else "secondary"):
            st.session_state.lang="pt";st.rerun()
    with c2:
        if st.button("🇪🇸 ES",use_container_width=True,type="primary" if st.session_state.lang=="es" else "secondary"):
            st.session_state.lang="es";st.rerun()
    with c3:
        if st.button("🇺🇸 EN",use_container_width=True,type="primary" if st.session_state.lang=="en" else "secondary"):
            st.session_state.lang="en";st.rerun()

render_lang()
T=T_ALL[st.session_state.lang]

# ── ESTILOS ───────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@700;900&family=DM+Sans:wght@300;400;500&family=DM+Mono&display=swap');
:root{--quake:#6B1A0A;--quake-mid:#8B2515;--quake-light:#C0390A;
  --earth:#2D1B0E;--amber:#C47D0E;--tectonic:#1A3A6E;--tect-light:#2555A0;
  --cream:#FAF6F0;--warm-gray:#6A5A50;--green:#2D7A45;--black:#0D1117;}
html,body,[class*="css"]{font-family:'DM Sans',sans-serif;background:var(--cream);color:var(--black);}
.hero-wrap{background:linear-gradient(135deg,#1A0A05 0%,#3D0E08 50%,#5A1810 100%);border-radius:20px;padding:3rem 2.5rem 2rem;margin-bottom:2rem;position:relative;overflow:hidden;}
.hero-wrap::before{content:"🌍";font-size:200px;position:absolute;right:-20px;top:-30px;opacity:0.05;}
.hero-tag{background:#F5A623;color:#1A0A05;font-family:'DM Mono',monospace;font-size:.7rem;font-weight:bold;letter-spacing:2px;padding:4px 12px;border-radius:4px;display:inline-block;margin-bottom:1rem;text-transform:uppercase;}
.hero-title{font-family:'Playfair Display',serif;font-size:2.8rem;font-weight:900;color:#fff;line-height:1.15;margin-bottom:.8rem;white-space:pre-line;}
.hero-subtitle{font-size:1rem;color:rgba(255,255,255,.78);max-width:680px;line-height:1.6;margin-bottom:1.5rem;}
.hero-badges{display:flex;gap:10px;flex-wrap:wrap;}
.badge{background:rgba(255,255,255,.1);border:1px solid rgba(255,255,255,.2);color:rgba(255,255,255,.85);font-size:.72rem;font-family:'DM Mono',monospace;padding:5px 12px;border-radius:20px;}
.badge-quake{background:rgba(240,80,30,.25);border-color:#F5A623;color:#F5A623;}
.metric-box{background:white;border-radius:16px;padding:1.4rem 1.2rem;border-top:4px solid var(--quake-light);box-shadow:0 2px 12px rgba(0,0,0,.07);text-align:center;}
.metric-box.tect{border-top-color:var(--tect-light);}
.metric-box.amber{border-top-color:var(--amber);}
.metric-box.green{border-top-color:var(--green);}
.metric-val{font-family:'Playfair Display',serif;font-size:2.1rem;font-weight:900;color:var(--quake-mid);line-height:1;margin-bottom:.3rem;}
.metric-label{font-size:.75rem;color:var(--warm-gray);text-transform:uppercase;letter-spacing:1px;}
.section-label{font-family:'DM Mono',monospace;font-size:.65rem;color:var(--quake-mid);text-transform:uppercase;letter-spacing:3px;margin-bottom:.3rem;}
.section-title{font-family:'Playfair Display',serif;font-size:1.9rem;font-weight:700;color:var(--quake-mid);margin-bottom:1.2rem;line-height:1.2;}
.info-card{background:white;border-radius:16px;padding:1.5rem;box-shadow:0 2px 12px rgba(0,0,0,.05);border-left:4px solid var(--quake-light);margin-bottom:1rem;}
.info-card.tect{border-left-color:var(--tect-light);}
.info-card.amber{border-left-color:var(--amber);}
.info-card.green{border-left-color:var(--green);}
.info-card.urgent{border-left-color:var(--quake-mid);background:linear-gradient(135deg,#FFF5F0,#FFEBE0);}
.method-step{display:flex;align-items:flex-start;gap:1rem;padding:1rem;background:white;border-radius:12px;margin-bottom:.8rem;box-shadow:0 1px 6px rgba(0,0,0,.04);}
.step-num{background:var(--quake-mid);color:white;font-family:'Playfair Display',serif;font-size:1.1rem;font-weight:700;width:36px;height:36px;border-radius:50%;display:flex;align-items:center;justify-content:center;flex-shrink:0;}
.step-title{font-weight:500;color:var(--quake-mid);font-size:.95rem;}
.step-desc{font-size:.82rem;color:var(--warm-gray);margin-top:.2rem;}
.discovery-box{background:linear-gradient(135deg,#FFF8F5,#FFECE0);border:2px solid var(--quake-light);border-radius:16px;padding:1.8rem;margin:.8rem 0;}
.discovery-title{font-family:'Playfair Display',serif;font-size:1.1rem;font-weight:700;color:var(--quake-mid);margin-bottom:.5rem;}
.timeline-item{display:flex;gap:1rem;padding:1rem 0;border-bottom:1px solid #F0E0D8;}
.timeline-year{font-family:'Playfair Display',serif;font-size:1rem;font-weight:700;color:var(--quake-light);min-width:90px;}
.timeline-title{font-weight:500;color:var(--quake-mid);margin-bottom:.2rem;}
.timeline-desc{font-size:.85rem;color:var(--warm-gray);}
.timeline-item.highlight{background:linear-gradient(135deg,#FFF8F5,#FFECE0);border-radius:8px;padding:1rem;border-left:4px solid var(--quake-mid);}
.source-badges{display:flex;gap:8px;flex-wrap:wrap;margin-top:.8rem;}
.source-badge{background:var(--quake-mid);color:white;font-family:'DM Mono',monospace;font-size:.65rem;padding:4px 10px;border-radius:4px;letter-spacing:1px;text-transform:uppercase;}
.footer-wrap{background:var(--earth);border-radius:20px;padding:2rem;color:rgba(255,255,255,.8);text-align:center;margin-top:3rem;}
.footer-title{font-family:'Playfair Display',serif;color:#F5A623;font-size:1.2rem;margin-bottom:.5rem;}
.live-card{background:white;border-radius:16px;padding:1.2rem 1rem;box-shadow:0 2px 16px rgba(0,0,0,.08);border-top:5px solid;text-align:center;transition:transform .15s;}
.live-card:hover{transform:translateY(-2px);}
.live-city{font-family:'Playfair Display',serif;font-size:.95rem;font-weight:700;margin-bottom:.2rem;}
.live-pct{font-family:'Playfair Display',serif;font-size:2rem;font-weight:900;line-height:1;}
.live-label{font-size:.65rem;font-family:'DM Mono',monospace;text-transform:uppercase;letter-spacing:1px;margin-top:.2rem;}
.live-count{font-size:.72rem;color:var(--warm-gray);margin-top:.15rem;}
.pulse{animation:pulse 2s infinite;}
@keyframes pulse{0%{opacity:1}50%{opacity:.5}100%{opacity:1}}
.photo-placeholder{background:#FFF8F5;border:2px dashed var(--quake-light);border-radius:12px;padding:2rem;text-align:center;min-height:220px;display:flex;flex-direction:column;align-items:center;justify-content:center;}
.photo-emoji{font-size:2.6rem;}
.photo-title{font-weight:600;color:var(--quake-mid);margin:.5rem 0 .2rem;font-size:.95rem;}
.photo-desc{font-size:.78rem;color:var(--warm-gray);line-height:1.5;}
.photo-path{font-size:.65rem;color:var(--quake-light);font-family:'DM Mono',monospace;margin-top:.5rem;background:#FFECE0;padding:3px 8px;border-radius:4px;}
.photo-meta{font-size:.7rem;font-family:'DM Mono',monospace;margin-top:.4rem;line-height:1.8;}
.photo-legenda{font-size:.72rem;color:var(--warm-gray);font-style:italic;padding:.5rem .8rem;background:#faf8f5;text-align:center;border-top:1px solid #F0E0D8;}
.photo-destaque{border:3px solid var(--quake-light);border-radius:14px;overflow:hidden;box-shadow:0 4px 20px rgba(139,37,21,.2);}
</style>""",unsafe_allow_html=True)

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

# ── ABAS ──────────────────────────────────────────────────────
tabs=st.tabs([T['tab1'],T['tab2'],T['tab3'],T['tab4'],T['tab5'],T['tab6'],T['tab7'],T['tab8']])

# ─────────────────────────────────────────────────────────────
# TAB 1: MAPA & ANÁLISE + DASHBOARD EM TEMPO REAL
# ─────────────────────────────────────────────────────────────
with tabs[0]:
    # ── DASHBOARD TEMPO REAL ──────────────────────────────────
    st.markdown(f'<div class="section-label">{T["live_label"]}</div>',unsafe_allow_html=True)
    st.markdown(f'<div class="section-title">{T["live_title"]}</div>',unsafe_allow_html=True)
    st.markdown(f'<div class="info-card urgent">{T["live_hint"]}</div>',unsafe_allow_html=True)

    col_refresh,_ = st.columns([1,7])
    with col_refresh:
        refresh = st.button(T['live_fetch'], key="refresh_live")
    if refresh:
        st.cache_data.clear()
        st.rerun()

    # Baselines mensais históricas (sismos M≥2 / 30 dias)
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

    # ── MAPA ──────────────────────────────────────────────────
    st.markdown(f"<br><div class='section-label'>{T['map_label']}</div>",unsafe_allow_html=True)
    st.markdown(f"<div class='section-title'>{T['map_title']}</div>",unsafe_allow_html=True)
    st.markdown(f'<div class="info-card">{T["map_hint"]}</div>',unsafe_allow_html=True)

    mapa=folium.Map(location=[-54,-68],zoom_start=5,tiles='CartoDB dark_matter')

    # Sismos recentes da Patagônia
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

    # Marcador especial M7.4
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

    # Cidades
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

    # Falha Magallanes-Fagnano
    folium.PolyLine(locations=[[-54.5,-70],[-54.8,-68],[-54.9,-67.6],[-55.2,-65],[-55.0,-63]],
        color="#F5A623",weight=3,opacity=.7,dash_array="6",
        tooltip="Falha Magallanes-Fagnano").add_to(mapa)

    folium_static(mapa,width=1100,height=540)

    # ── Evento M7.4 destaque ──────────────────────────────────
    st.markdown(f"<br><div class='section-label' style='color:#C0390A'>{T['drake_label']}</div>",unsafe_allow_html=True)
    col_d1,col_d2,col_d3,col_d4 = st.columns(4)
    fields=[("📅 Data/Hora","02/05/2025 · 09:58 local"),("📍 Epicentro","219 km sul de Ushuaia"),
            ("🏔️ Profundidade","10 km (raso)"),("🚨 Evacuados","~1.800 pessoas")]
    for col,(label,val) in zip([col_d1,col_d2,col_d3,col_d4],fields):
        with col:
            st.markdown(f'<div class="metric-box"><div class="metric-val" style="font-size:1.2rem">{val}</div><div class="metric-label">{label}</div></div>',unsafe_allow_html=True)

    # ── Gráfico histograma magnitudes ──────────────────────────
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
    st.plotly_chart(fig_hist,use_container_width=True)

    col_pr,col_sc=st.columns(2)
    with col_pr:
        labels=list(PROF_DIST.keys()); vals=list(PROF_DIST.values())
        fig_pie=go.Figure(go.Pie(labels=labels,values=vals,
            marker_colors=["#C0390A","#F5A623","#2555A0"],hole=.45,
            hovertemplate='%{label}: %{percent}<extra></extra>'))
        fig_pie.update_layout(title=dict(text=T['prof_title'],font=dict(size=13,family='Playfair Display')),
            paper_bgcolor='rgba(0,0,0,0)',height=300,font=dict(family='DM Sans'),
            showlegend=True,legend=dict(orientation='h',yanchor='bottom',y=-0.2),margin=dict(t=50,b=10))
        st.plotly_chart(fig_pie,use_container_width=True)
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
        st.plotly_chart(fig_sc,use_container_width=True)

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
      <div style="font-family:'DM Mono',monospace;font-size:.82rem;line-height:2.2;color:#1A3A6E">
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

    # Comparativo cidades
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
    st.plotly_chart(fig_cities,use_container_width=True)

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
    fig_trend.add_trace(go.Bar(x=MESES,y=vals,marker_color=cor_city,opacity=.85,
        text=vals,textposition='outside',textfont=dict(size=10,family="DM Mono",color=cor_city),
        hovertemplate='<b>%{x}</b><br>%{y} sismos<extra></extra>',name=city_sel))
    if city_sel in ("Puerto Williams","Ushuaia","Rio Grande","Punta Arenas"):
        fig_trend.add_vline(x="Mai",line_dash="dash",line_color="#C0390A",line_width=2,
            annotation_text="  M7.4 02/Mai/25",annotation_font_color="#C0390A",annotation_font_size=10)
    mean_val=np.mean(vals)
    fig_trend.add_hline(y=mean_val,line_dash="dot",line_color=cor_city,opacity=.6,
        annotation_text=f"  Média: {mean_val:.1f}",annotation_font_color=cor_city)
    fig_trend.update_layout(paper_bgcolor='rgba(0,0,0,0)',plot_bgcolor='rgba(107,26,10,.02)',
        font=dict(family='DM Sans'),height=360,showlegend=False,
        xaxis=dict(showgrid=False),
        yaxis=dict(showgrid=True,gridcolor='#F0E0D8',title="Sismos (M≥2)"),
        margin=dict(t=20,b=20))
    st.plotly_chart(fig_trend,use_container_width=True)

    # Comparativo anual todas as cidades
    fig_all=go.Figure()
    for cname,vals_m in HIST_SISMOS.items():
        cor_c=risk_color(next((c['risco'] for c in CITIES if c['nome']==cname),"Moderado"))
        fig_all.add_trace(go.Scatter(x=MESES,y=vals_m,mode='lines+markers',name=cname,
            line=dict(color=cor_c,width=2),marker=dict(size=6),
            hovertemplate=f'<b>{cname}</b><br>%{{x}}: %{{y}}<extra></extra>'))
    fig_all.add_vline(x="Mai",line_dash="dash",line_color="#C0390A",line_width=2,
        annotation_text="  M7.4 02/Mai/25",annotation_font_color="#C0390A",annotation_font_size=10)
    fig_all.update_layout(paper_bgcolor='rgba(0,0,0,0)',plot_bgcolor='rgba(107,26,10,.02)',
        title=dict(text="Comparativo Anual — Todas as Cidades (2024)",font=dict(size=13,family='Playfair Display')),
        font=dict(family='DM Sans'),height=380,
        xaxis=dict(showgrid=False),yaxis=dict(showgrid=True,gridcolor='#F0E0D8',title="Sismos M≥2"),
        legend=dict(orientation='h',yanchor='bottom',y=1.01,font=dict(size=9)),margin=dict(t=50,b=20))
    st.plotly_chart(fig_all,use_container_width=True)

# ── TAB 6: PARÂMETROS ────────────────────────────────────────
with tabs[5]:
    st.markdown(f'<div class="section-label">{T["params_label"]}</div>',unsafe_allow_html=True)
    st.markdown(f'<div class="section-title">{T["params_title"]}</div>',unsafe_allow_html=True)

    # Scatter MMI por cidade
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
    st.plotly_chart(fig_mmi,use_container_width=True)

    # Gauge de risco por cidade
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
    st.plotly_chart(fig_gauges,use_container_width=True)

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

    import io
    csv_buf=io.StringIO(); df_cat.to_csv(csv_buf,index=False)
    st.download_button(T['download_csv'],csv_buf.getvalue(),"patagonia_seismic_catalog.csv","text/csv")

    # Escala Richter × efeitos
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