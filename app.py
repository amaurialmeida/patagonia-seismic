import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import folium
from streamlit_folium import st_folium
from datetime import datetime, timedelta
import requests
import json
from branca.colormap import linear

# Configuração da página
st.set_page_config(
    page_title="Sismologia da Patagônia | M7.4 Drake Passage",
    page_icon="🌍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Estilo CSS personalizado
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        padding: 1rem 0;
    }
    .sub-header {
        font-size: 1.3rem;
        color: #dc2626;
        font-weight: bold;
        border-left: 4px solid #dc2626;
        padding-left: 1rem;
        margin: 1rem 0;
    }
    .info-card {
        background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
        padding: 1.5rem;
        border-radius: 10px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        margin: 1rem 0;
    }
    .highlight {
        color: #dc2626;
        font-weight: bold;
        font-size: 1.2rem;
    }
    .metric-card {
        background: white;
        padding: 1rem;
        border-radius: 8px;
        text-align: center;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    .risk-high {
        color: #dc2626;
        font-weight: bold;
    }
    .risk-moderate {
        color: #f59e0b;
        font-weight: bold;
    }
    .footer {
        text-align: center;
        padding: 2rem;
        margin-top: 2rem;
        border-top: 1px solid #e5e7eb;
        color: #6b7280;
    }
</style>
""", unsafe_allow_html=True)

# Título principal
st.markdown('<div class="main-header">🌍 Sismologia da Patagônia</div>', unsafe_allow_html=True)
st.markdown('<div style="text-align: center; color: #6b7280; margin-bottom: 2rem;">006 · CHILE & ARGENTINA · PATAGÔNIA SUL</div>', unsafe_allow_html=True)

# Sidebar
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/3276/3276938.png", width=80)
    st.markdown("## 📊 Filtros")
    
    # Filtro de magnitude
    min_magnitude = st.slider(
        "Magnitude mínima",
        min_value=4.0,
        max_value=7.5,
        value=4.5,
        step=0.1,
        help="Filtrar eventos sísmicos por magnitude"
    )
    
    # Filtro de data
    col1, col2 = st.columns(2)
    with col1:
        start_date = st.date_input(
            "Data inicial",
            value=datetime(2024, 1, 1),
            max_value=datetime(2026, 5, 31)
        )
    with col2:
        end_date = st.date_input(
            "Data final",
            value=datetime(2026, 5, 9),
            max_value=datetime(2026, 5, 31)
        )
    
    st.markdown("---")
    st.markdown("### 🔬 Contexto Geológico")
    st.info(
        "A sismicidade patagônica resulta da interação das placas de Nazca, "
        "Antártica, Scotia e da Falha Magallanes-Fagnano."
    )
    
    st.markdown("---")
    st.markdown("### 👨‍🔬 Pesquisador")
    st.markdown(
        "**Amauri Almeida de Souza Junior**\n\n"
        "📍 Puerto Williams, Chile (2025)\n\n"
        "📍 São Paulo, SP, Brasil"
    )

# Função para carregar dados da USGS
@st.cache_data(ttl=3600)
def load_usgs_data(starttime, endtime, min_lat=-60, max_lat=-45, min_lon=-80, max_lon=-60, min_mag=4.5):
    """
    Carrega dados sísmicos da API USGS
    """
    url = "https://earthquake.usgs.gov/fdsnws/event/1/query"
    
    params = {
        "format": "geojson",
        "starttime": starttime.strftime("%Y-%m-%d"),
        "endtime": endtime.strftime("%Y-%m-%d"),
        "minlatitude": min_lat,
        "maxlatitude": max_lat,
        "minlongitude": min_lon,
        "maxlongitude": max_lon,
        "minmagnitude": min_mag,
        "orderby": "time"
    }
    
    try:
        response = requests.get(url, params=params, timeout=30)
        response.raise_for_status()
        data = response.json()
        
        # Processar dados
        events = []
        for feature in data['features']:
            props = feature['properties']
            geom = feature['geometry']
            
            event = {
                'time': datetime.fromtimestamp(props['time'] / 1000),
                'magnitude': props['mag'],
                'depth': geom['coordinates'][2],
                'latitude': geom['coordinates'][1],
                'longitude': geom['coordinates'][0],
                'place': props['place'],
                'url': props['url'],
                'tsunami': props['tsunami'],
                'mmi': props.get('mmi', None)
            }
            events.append(event)
        
        df = pd.DataFrame(events)
        return df if not df.empty else pd.DataFrame()
        
    except Exception as e:
        st.error(f"Erro ao carregar dados da USGS: {str(e)}")
        return pd.DataFrame()

# Dados adicionais das cidades
cities_data = {
    'city': ['Puerto Williams', 'Punta Arenas', 'Puerto Natales', 'Rio Verde', 
             'Ushuaia', 'Rio Gallegos', 'Rio Grande', 'Santiago', 'Buenos Aires'],
    'country': ['Chile', 'Chile', 'Chile', 'Chile', 'Argentina', 'Argentina', 
                'Argentina', 'Chile', 'Argentina'],
    'latitude': [-54.9333, -53.1500, -51.7333, -52.6500, -54.8000, -51.6222, -53.8000, -33.4489, -34.6037],
    'longitude': [-67.6167, -70.9111, -72.5000, -71.4667, -68.3000, -69.2181, -67.7000, -70.6693, -58.3816],
    'mmi_2025': [5.5, 3.5, 2.5, 2.5, 4.5, 2.0, 3.5, None, None],
    'risk': ['Muito Alto', 'Alto', 'Moderado-Alto', 'Moderado', 'Muito Alto', 
             'Moderado', 'Alto', 'Alto', 'Baixo'],
    'annual_quakes': [None, None, None, None, None, None, None, 174, 1.1]
}

cities_df = pd.DataFrame(cities_data)

# Carregar dados
with st.spinner("Carregando dados sísmicos da USGS..."):
    df = load_usgs_data(start_date, end_date, min_mag=min_magnitude)

# Se não houver dados, usar dados de exemplo
if df.empty:
    st.warning("Usando dados de exemplo devido à indisponibilidade da API...")
    # Criar dados de exemplo
    np.random.seed(42)
    n_events = 50
    df = pd.DataFrame({
        'time': [datetime(2025, 1, 1) + timedelta(days=np.random.randint(0, 500)) for _ in range(n_events)],
        'magnitude': np.random.uniform(4.5, 7.5, n_events),
        'depth': np.random.uniform(5, 150, n_events),
        'latitude': np.random.uniform(-60, -45, n_events),
        'longitude': np.random.uniform(-80, -60, n_events)
    })
    df = df.sort_values('time')

# Estatísticas principais
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.markdown("""
    <div class="metric-card">
        <h3>📊 Total de Eventos</h3>
        <h2 style="color: #dc2626;">{}</h2>
        <small>Magnitude ≥ {}</small>
    </div>
    """.format(len(df), min_magnitude), unsafe_allow_html=True)

with col2:
    max_mag = df['magnitude'].max() if not df.empty else 0
    st.markdown("""
    <div class="metric-card">
        <h3>⚡ Maior Magnitude</h3>
        <h2 style="color: #dc2626;">M{:.1f}</h2>
        <small>Registrado na região</small>
    </div>
    """.format(max_mag), unsafe_allow_html=True)

with col3:
    avg_depth = df['depth'].mean() if not df.empty else 0
    st.markdown("""
    <div class="metric-card">
        <h3>📏 Profundidade Média</h3>
        <h2 style="color: #f59e0b;">{:.1f} km</h2>
        <small>Crosta terrestre</small>
    </div>
    """.format(avg_depth), unsafe_allow_html=True)

with col4:
    unique_dates = df['time'].dt.date.nunique() if not df.empty else 0
    st.markdown("""
    <div class="metric-card">
        <h3>📅 Dias com Atividade</h3>
        <h2 style="color: #10b981;">{}</h2>
        <small>Período analisado</small>
    </div>
    """.format(unique_dates), unsafe_allow_html=True)

st.markdown("---")

# Evento principal em destaque
st.markdown('<div class="sub-header">🚨 EVENTO PRINCIPAL — M7.4 · PASSAGEM DE DRAKE · 02/05/2025</div>', unsafe_allow_html=True)

col1, col2 = st.columns([2, 1])

with col1:
    st.markdown("""
    <div class="info-card">
        <p style="font-style: italic; font-size: 1.1rem;">
        "Eu estava em Puerto Williams quando o chão começou a tremer às 9h58 da manhã. 
        Logo em seguida as sirenes de tsunami soaram pela cidade."
        </p>
        <p style="text-align: right; font-weight: bold;">— <strong>Amauri Almeida</strong>, pesquisador</p>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown("""
    <div class="info-card">
        <strong>📋 Detalhes do Evento</strong><br>
        • Magnitude: <span class="highlight">M7.4</span><br>
        • Data/Hora: 02/05/2025 · 09:58 local (GMT-3)<br>
        • Epicentro: Passagem de Drake, 219 km sul de Ushuaia<br>
        • Profundidade: 10 km (raso)<br>
        • Alerta tsunami: ✅ Emitido pelo NOAA PTWC<br>
        • Evacuados: ~1.800 pessoas<br>
        • Réplicas: 50+ (maior: M6.4)
    </div>
    """, unsafe_allow_html=True)

st.markdown("---")

# Mapa interativo
st.markdown('<div class="sub-header">🗺️ MAPA DE EPICENTROS — PATAGÔNIA</div>', unsafe_allow_html=True)

# Criar mapa base
m = folium.Map(location=[-54.0, -68.0], zoom_start=5, tiles='OpenStreetMap')

# Adicionar marcadores para cidades
for _, city in cities_df.iterrows():
    if pd.notna(city['latitude']):
        # Cor baseada no risco
        if city['risk'] in ['Muito Alto', 'Alto']:
            color = 'red'
        elif city['risk'] in ['Moderado-Alto', 'Moderado']:
            color = 'orange'
        else:
            color = 'blue'
        
        folium.Marker(
            [city['latitude'], city['longitude']],
            popup=f"<b>{city['city']}</b><br>País: {city['country']}<br>Risco: {city['risk']}",
            icon=folium.Icon(color=color, icon='info-sign')
        ).add_to(m)

# Adicionar eventos sísmicos
if not df.empty:
    for _, event in df.iterrows():
        # Tamanho baseado na magnitude
        radius = event['magnitude'] * 2
        
        # Cor baseada na magnitude
        if event['magnitude'] >= 7.0:
            color = 'darkred'
            fill_color = 'red'
        elif event['magnitude'] >= 6.0:
            color = 'red'
            fill_color = 'orange'
        elif event['magnitude'] >= 5.0:
            color = 'orange'
            fill_color = 'yellow'
        else:
            color = 'green'
            fill_color = 'lightgreen'
        
        folium.CircleMarker(
            [event['latitude'], event['longitude']],
            radius=radius,
            popup=f"<b>M{event['magnitude']:.1f}</b><br>Data: {event['time'].strftime('%Y-%m-%d')}<br>Profundidade: {event['depth']:.1f} km",
            color=color,
            fill=True,
            fill_color=fill_color,
            fill_opacity=0.6
        ).add_to(m)

# Destacar evento principal (M7.4 de 02/05/2025)
main_event_lat, main_event_lon = -58.5, -68.5  # Aproximadamente Passagem de Drake
folium.CircleMarker(
    [main_event_lat, main_event_lon],
    radius=20,
    popup="<b>⭐ M7.4 · 02/05/2025 · Passagem de Drake</b><br>Evento principal vivenciado em Puerto Williams",
    color='darkred',
    fill=True,
    fill_color='red',
    fill_opacity=0.8,
    weight=4
).add_to(m)

# Adicionar legenda
legend_html = '''
<div style="position: fixed; bottom: 50px; left: 50px; z-index: 1000; background-color: white; padding: 10px; border-radius: 5px; border: 2px solid grey; font-size: 12px;">
    <b>Legenda:</b><br>
    <i class="fa fa-circle" style="color:darkred"></i> M ≥ 7.0<br>
    <i class="fa fa-circle" style="color:red"></i> M 6.0 - 6.9<br>
    <i class="fa fa-circle" style="color:orange"></i> M 5.0 - 5.9<br>
    <i class="fa fa-circle" style="color:green"></i> M 4.5 - 4.9<br>
    🔴 Cidades com alto risco<br>
    🟠 Cidades com risco moderado
</div>
'''
st.markdown(legend_html, unsafe_allow_html=True)

# Exibir mapa
st_folium(m, width=725, height=500)

st.markdown("---")

# Gráficos de análise
st.markdown('<div class="sub-header">📊 ANÁLISE ESTATÍSTICA</div>', unsafe_allow_html=True)

if not df.empty:
    # Criar subplots
    fig = make_subplots(
        rows=2, cols=2,
        subplot_titles=('Distribuição por Magnitude', 'Profundidade vs Magnitude',
                       'Frequência Mensal', 'Magnitude ao Longo do Tempo'),
        specs=[[{'type': 'histogram'}, {'type': 'scatter'}],
               [{'type': 'bar'}, {'type': 'scatter'}]]
    )
    
    # 1. Histograma de magnitudes
    fig.add_trace(
        go.Histogram(x=df['magnitude'], nbinsx=15, name='Magnitude',
                    marker_color='#3b82f6', opacity=0.7),
        row=1, col=1
    )
    
    # 2. Scatter magnitude vs profundidade
    fig.add_trace(
        go.Scatter(x=df['magnitude'], y=df['depth'], mode='markers',
                  marker=dict(size=8, color=df['magnitude'], colorscale='Viridis',
                            showscale=True, colorbar=dict(title="Magnitude")),
                  name='Eventos', text=df['time'].dt.strftime('%Y-%m-%d')),
        row=1, col=2
    )
    
    # 3. Frequência mensal
    df['month'] = df['time'].dt.to_period('M')
    monthly_counts = df.groupby('month').size().reset_index(name='count')
    monthly_counts['month_str'] = monthly_counts['month'].astype(str)
    
    fig.add_trace(
        go.Bar(x=monthly_counts['month_str'], y=monthly_counts['count'],
              name='Eventos/mês', marker_color='#10b981', opacity=0.7),
        row=2, col=1
    )
    
    # CÓDIGO CORRIGIDO - LINHA VERTICAL E ANOTAÇÃO SEPARADAS
    # Adiciona linha vertical em maio de 2025 (evento principal)
    fig.add_vline(x="2025-05", line_dash="dash", line_color="#dc2626", row=2, col=1)
    
    # Adiciona anotação separadamente para evitar o bug do Plotly
    fig.add_annotation(
        x="2025-05",
        y=0.98,
        yref="paper",
        text="02/05/2025 M7.4",
        showarrow=False,
        font=dict(color="#dc2626", size=10),
        xanchor="left",
        row=2, col=1
    )
    
    # 4. Magnitude ao longo do tempo
    fig.add_trace(
        go.Scatter(x=df['time'], y=df['magnitude'], mode='markers+lines',
                  name='Magnitude', line=dict(color='#8b5cf6', width=2),
                  marker=dict(size=8, color=df['magnitude'], colorscale='Viridis'),
                  text=df['depth'].round(1)),
        row=2, col=2
    )
    
    fig.update_layout(height=800, showlegend=False, title_text="Análise Sísmica da Patagônia")
    fig.update_xaxes(title_text="Magnitude", row=1, col=1)
    fig.update_xaxes(title_text="Magnitude", row=1, col=2)
    fig.update_xaxes(title_text="Mês/Ano", row=2, col=1, tickangle=45)
    fig.update_xaxes(title_text="Data", row=2, col=2)
    fig.update_yaxes(title_text="Frequência", row=1, col=1)
    fig.update_yaxes(title_text="Profundidade (km)", row=1, col=2)
    fig.update_yaxes(title_text="Número de Eventos", row=2, col=1)
    fig.update_yaxes(title_text="Magnitude", row=2, col=2)
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Estatísticas adicionais
    st.markdown("### 📈 Estatísticas Detalhadas")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown(f"""
        <div class="metric-card">
            <h4>📊 Distribuição de Magnitudes</h4>
            <b>M ≥ 7.0:</b> {len(df[df['magnitude'] >= 7])} eventos<br>
            <b>M 6.0-6.9:</b> {len(df[(df['magnitude'] >= 6) & (df['magnitude'] < 7)])} eventos<br>
            <b>M 5.0-5.9:</b> {len(df[(df['magnitude'] >= 5) & (df['magnitude'] < 6)])} eventos<br>
            <b>M 4.5-4.9:</b> {len(df[(df['magnitude'] >= 4.5) & (df['magnitude'] < 5)])} eventos
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div class="metric-card">
            <h4>📏 Distribuição de Profundidades</h4>
            <b>Raso (0-30 km):</b> {len(df[df['depth'] <= 30])} eventos<br>
            <b>Intermediário (30-100 km):</b> {len(df[(df['depth'] > 30) & (df['depth'] <= 100)])} eventos<br>
            <b>Profundo (>100 km):</b> {len(df[df['depth'] > 100])} eventos<br>
            <b>Profundidade máxima:</b> {df['depth'].max():.1f} km
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        # Evento mais recente
        latest_event = df.iloc[-1]
        st.markdown(f"""
        <div class="metric-card">
            <h4>🕐 Último Evento Registrado</h4>
            <b>Data:</b> {latest_event['time'].strftime('%d/%m/%Y')}<br>
            <b>Magnitude:</b> M{latest_event['magnitude']:.1f}<br>
            <b>Profundidade:</b> {latest_event['depth']:.1f} km
        </div>
        """, unsafe_allow_html=True)

st.markdown("---")

# Cidades e impactos
st.markdown('<div class="sub-header">🏙️ CIDADES & IMPACTOS — PATAGÔNIA</div>', unsafe_allow_html=True)

# Tabela de cidades
st.dataframe(
    cities_df[['city', 'country', 'mmi_2025', 'risk']],
    column_config={
        'city': 'Cidade',
        'country': 'País',
        'mmi_2025': st.column_config.NumberColumn('MMI (02/05/2025)', format="%.1f"),
        'risk': 'Risco Sísmico'
    },
    use_container_width=True,
    hide_index=True
)

# Comparativo capitais
st.markdown("### 🏛️ Comparativo com Capitais")
col1, col2 = st.columns(2)

with col1:
    st.markdown("""
    <div class="info-card">
        <h4>📊 Santiago, Chile 🇨🇱</h4>
        • Sismos/ano: <span class="highlight">~174</span><br>
        • Maior M (10 anos): M6.7 (2017)<br>
        • Risco: <span class="risk-high">Alto</span><br>
        • Contexto: Próximo à zona de subducção da Placa de Nazca
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown("""
    <div class="info-card">
        <h4>📊 Buenos Aires, Argentina 🇦🇷</h4>
        • Sismos/ano: <span class="highlight">~1.1</span><br>
        • Maior M (10 anos): M5.0 (2026)<br>
        • Risco: <span class="risk-moderate">Baixo</span><br>
        • Contexto: Distante das principais zonas sísmicas ativas
    </div>
    """, unsafe_allow_html=True)

st.markdown("---")

# Contexto geológico
st.markdown('<div class="sub-header">🔬 CONTEXTO GEOLÓGICO — PLACAS TECTÔNICAS</div>', unsafe_allow_html=True)

col1, col2 = st.columns([2, 1])

with col1:
    st.markdown("""
    A sismicidade patagônica resulta da interação de **4 placas tectônicas**:
    
    1. **Placa de Nazca** → Subducção sob a Sul-Americana a ~70 mm/ano (Andes, costa Pacífico)
    2. **Placa Antártica** → Colisão ao sul (Drake Passage, Patagônia austral)
    3. **Placa Scotia** → Falha transformante (Tierra del Fuego, Canal de Beagle)
    4. **Falha Magallanes-Fagnano** → Corta Tierra del Fuego de leste a oeste
    
    ### ⚠️ Implicações para Puerto Williams
    
    Puerto Williams está localizada diretamente sobre o **sistema de falhas Scotia / Magallanes-Fagnano** — 
    o que explica a intensidade vivenciada durante o evento M7.4 de 02/05/2025.
    
    ### 📊 Escala de Richter vs Efeitos Observados
    
    | Magnitude | Efeitos Típicos | Observado em Puerto Williams |
    |-----------|----------------|------------------------------|
    | M < 4.5 | Geralmente não sentido | - |
    | M 4.5-5.5 | Perceptível, raramente danos | Ocorrências comuns na região |
    | M 5.5-6.5 | Danos leves a moderados | Réplicas do evento principal |
    | M 6.5-7.5 | Danos significativos em áreas vulneráveis | **M7.4 - Forte, tsunami alerta** |
    | M > 7.5 | Danos catastróficos em grande área | - |
    """)
    
with col2:
    st.markdown("""
    <div class="info-card">
        <h4>🔍 Fontes de Dados</h4>
        • <b>USGS Earthquake API</b><br>
        Catálogo sísmico em tempo real<br><br>
        • <b>CSN Chile</b><br>
        Rede sismográfica nacional<br><br>
        • <b>INPRES Argentina</b><br>
        Catálogo sísmico argentino<br><br>
        • <b>The Watchers</b><br>
        Relatório detalhado M7.4<br><br>
        • <b>VolcanoDiscovery</b><br>
        Estatísticas por cidade<br><br>
        • <b>SENAPRED Chile</b><br>
        Alertas e evacuações
    </div>
    """, unsafe_allow_html=True)

st.markdown("---")

# Timeline de eventos notáveis
st.markdown('<div class="sub-header">📅 TIMELINE — EVENTOS NOTÁVEIS (2024-2026)</div>', unsafe_allow_html=True)

if not df.empty:
    # Selecionar os 10 maiores eventos
    top_events = df.nlargest(10, 'magnitude').sort_values('time')
    
    # Criar timeline visual com plotly
    fig_timeline = go.Figure()
    
    fig_timeline.add_trace(go.Scatter(
        x=top_events['time'],
        y=top_events['magnitude'],
        mode='markers+text',
        marker=dict(
            size=top_events['magnitude'] * 3,
            color=top_events['magnitude'],
            colorscale='Viridis',
            showscale=True,
            colorbar=dict(title="Magnitude")
        ),
        text=top_events['magnitude'].round(1),
        textposition="top center",
        textfont=dict(size=10),
        name='Eventos',
        hovertemplate='<b>Data:</b> %{x|%d/%m/%Y}<br>' +
                      '<b>Magnitude:</b> M%{text}<br>' +
                      '<b>Profundidade:</b> %{customdata:.1f} km<br>' +
                      '<extra></extra>',
        customdata=top_events['depth']
    ))
    
    # Destacar evento principal
    main_event = top_events[top_events['magnitude'] == top_events['magnitude'].max()]
    fig_timeline.add_trace(go.Scatter(
        x=main_event['time'],
        y=main_event['magnitude'],
        mode='markers',
        marker=dict(size=25, color='red', symbol='star'),
        name='⭐ Evento Principal M7.4',
        hovertemplate='<b>⭐ EVENTO PRINCIPAL</b><br>' +
                      'Data: 02/05/2025<br>' +
                      'Magnitude: M7.4<br>' +
                      '<extra></extra>'
    ))
    
    fig_timeline.update_layout(
        title="Top 10 Maiores Eventos Sísmicos (2024-2026)",
        xaxis_title="Data",
        yaxis_title="Magnitude",
        height=400,
        hovermode='closest'
    )
    
    st.plotly_chart(fig_timeline, use_container_width=True)
    
    # Lista textual dos eventos
    st.markdown("#### 📋 Lista dos Maiores Eventos")
    for idx, event in top_events.iterrows():
        st.markdown(f"""
        • **{event['time'].strftime('%d/%m/%Y')}** — M{event['magnitude']:.1f} 
        (Profundidade: {event['depth']:.1f} km) — {event.get('place', 'Região da Patagônia')}
        """)

st.markdown("---")

# Footer
st.markdown("""
<div class="footer">
    <p>🔬 Projeto 006 — Sismologia da Patagônia | Chile & Argentina</p>
    <p>📊 Dados: USGS Earthquake API | Última atualização: Maio 2026</p>
    <p>🌍 Desenvolvido por Amauri Almeida | Pesquisa de campo em Puerto Williams (2025)</p>
    <p style="font-size: 0.8rem;">⚠️ Este é um projeto científico-educacional. Em caso de emergência sísmica, 
    siga as orientações da defesa civil local.</p>
</div>
""", unsafe_allow_html=True)