# 🌍 Sismologia da Patagônia

**006 · CHILE & ARGENTINA · PATAGÔNIA SUL**

Análise sismológica da Patagônia Chilena e Argentina (2024–2026), com destaque especial para o **sismo M7.4 de 02 de maio de 2025 na Passagem de Drake**, vivenciado pelo pesquisador Amauri Almeida em Puerto Williams.

[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://patagonia-seismic.streamlit.app)

---

## 🚨 Evento Principal — M7.4 · Passagem de Drake · 02/05/2025

> *"Eu estava em Puerto Williams quando o chão começou a tremer às 9h58 da manhã. Logo em seguida as sirenes de tsunami soaram pela cidade."*
> — **Amauri Almeida**, pesquisador

| Campo | Dado |
|-------|------|
| Magnitude | **M7.4** |
| Data / Hora | 02/05/2025 · 09:58 local (GMT-3) |
| Epicentro | Passagem de Drake, 219 km sul de Ushuaia |
| Profundidade | 10 km (raso) |
| Alerta tsunami | ✅ Emitido pelo NOAA PTWC |
| Evacuados | ~1.800 pessoas |
| Réplicas | 50+ (maior: M6.4) |
| Sentido em | Puerto Williams 🇨🇱 · Punta Arenas · Ushuaia 🇦🇷 · Rio Grande · Puerto Natales · Rio Verde |
| ID USGS | `us7000pwkn` |

---

## 🗺️ Cidades da Patagônia Analisadas

### Vivenciadas pelo pesquisador:

| Cidade | País | Impacto 02/05/2025 | Risco Sísmico |
|--------|------|-------------------|---------------|
| ⭐ Puerto Williams | Chile 🇨🇱 | MMI V-VI (Forte) | Muito Alto |
| Punta Arenas | Chile 🇨🇱 | MMI III-IV | Alto |
| Puerto Natales | Chile 🇨🇱 | MMI II-III | Moderado-Alto |
| Rio Verde | Chile 🇨🇱 | MMI II-III | Moderado |
| Ushuaia | Argentina 🇦🇷 | MMI IV-V | Muito Alto |
| Rio Gallegos | Argentina 🇦🇷 | MMI II | Moderado |
| Rio Grande | Argentina 🇦🇷 | MMI III-IV | Alto |

### Capitais — Comparativo:

| Capital | Sismos/ano | Maior M (10a) | Risco |
|---------|-----------|--------------|-------|
| Santiago 🇨🇱 | ~174 | M6.7 (2017) | Alto |
| Buenos Aires 🇦🇷 | ~1.1 | M5.0 (2026) | Baixo |

---

## 📊 Funcionalidades

- **🗺️ Mapa de Epicentros** — Folium interativo com marcadores por magnitude (cor + tamanho), cidades patagônicas e capitais. Evento principal em destaque especial.
- **📅 Timeline de Eventos** — Bolhas temporais 2024–2026 com marcação do M7.4, lista textual dos eventos notáveis.
- **📊 Análise Estatística** — Histograma por magnitude, scatter magnitude × profundidade, frequência mensal, comparativo Patagônia vs capitais.
- **🏙️ Cidades & Impactos** — Cards com MMI por cidade, índice de risco sísmico relativo.
- **🔬 Contexto Geológico** — Interação de placas tectônicas, falha Magallanes-Fagnano, comparativo Escala de Richter vs efeitos.

---

## ⚙️ Instalação Local

```bash
git clone https://github.com/amaurialmeida/patagonia-seismic.git
cd patagonia-seismic
pip install -r requirements.txt
streamlit run seismic_app.py
```

---

## 🔌 API USGS — Como funciona

O app conecta à **USGS Earthquake Catalog API** (gratuita, sem chave de API):

```
https://earthquake.usgs.gov/fdsnws/event/1/query?
  format=geojson
  &starttime=2024-01-01
  &endtime=2026-05-09
  &minlatitude=-60
  &maxlatitude=-45
  &minlongitude=-80
  &maxlongitude=-60
  &minmagnitude=4.5
  &orderby=time
```

Retorna GeoJSON com todas as propriedades: magnitude, profundidade, localização, timestamp, MMI, alerta de tsunami.

---

## 🗂️ Fontes

| Fonte | Dados |
|-------|-------|
| [USGS Earthquake API](https://earthquake.usgs.gov/fdsnws/event/1/) | Catálogo sísmico em tempo real |
| [CSN Chile](https://sismologia.cl) | Rede sismográfica nacional |
| [INPRES Argentina](https://inpres.gob.ar) | Catálogo sísmico argentino |
| [The Watchers](https://watchers.news) | Relatório detalhado M7.4 |
| [VolcanoDiscovery](https://volcanodiscovery.com) | Estatísticas por cidade |
| [SENAPRED Chile](https://senapred.cl) | Alertas e evacuações |

---

## 🗺️ Contexto Geológico

A sismicidade patagônica resulta da interação de **4 placas tectônicas**:

1. **Placa de Nazca** → subduce sob a Sul-Americana a ~70 mm/ano (Andes, costa Pacífico)
2. **Placa Antártica** → colide ao sul (Drake Passage, Patagônia austral)
3. **Placa Scotia** → falha transformante (Tierra del Fuego, Canal de Beagle)
4. **Falha Magallanes-Fagnano** → corta Tierra del Fuego de leste a oeste

Puerto Williams fica diretamente sobre o sistema de falhas Scotia / Magallanes-Fagnano — o que explica a intensidade vivenciada em 02/05/2025.

---

## 🔭 Série de Projetos

| # | Projeto | Status |
|---|---------|--------|
| 004 | Energia Eólica — Patagônia | ✅ Online |
| **005** | **Sismologia — Patagônia** | **✅ Este projeto** |
| 006 | Castores — Ilha Cabo de Hornos | 📋 Planejado |
| 007 | Abelhas Sem Ferrão — Brasil | 📋 Planejado |
| 008 | Moringa — Tratamento de Água | 📋 Planejado |

---

## 👨‍🔬 Pesquisador

**Amauri Almeida de Souza Junior**
📍 Puerto Williams, Chile (março–outubro 2025) · São Paulo, SP, Brasil

- 🌐 [Portfólio](https://amaurialmeida.github.io/environmental-portfolio/)
- 🐙 [GitHub](https://github.com/amaurialmeida)
- 💼 [LinkedIn](https://www.linkedin.com/in/amauri-almeida26/)
