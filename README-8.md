# 🌍 Patagonia Seismic Monitoring — The Drake Passage M7.4 Earthquake

[![Streamlit App](https://img.shields.io/badge/Streamlit-Live_App-FF4B4B?logo=streamlit&logoColor=white)](https://patagonia-seismic.streamlit.app/)
[![Python](https://img.shields.io/badge/Python-3.11-blue?logo=python&logoColor=white)](https://www.python.org/)
[![License: Academic](https://img.shields.io/badge/License-Academic-blue.svg)]()
[![Status](https://img.shields.io/badge/Status-Active-brightgreen)]()

🌐 **Languages:** English | [Português](README.pt-BR.md) | [Español](README.es.md)

**Independent Field Research — Live Seismological Monitoring & Firsthand Field Account**
Chilean & Argentine Patagonia · Nov 2024–Oct 2025
**Author:** Amauri Almeida de Souza Junior

---

## ❓ Research Question

> "What does personally living through a magnitude 7.4 earthquake in Puerto Williams — a town of 3,000 people at the planet's southern edge — reveal about Patagonian seismicity and community vulnerability at the interface of the Nazca, Antarctic, and Scotia plates?"

**Answer:** The May 2, 2025 M7.4 Drake Passage earthquake was the region's largest seismic event in decades, and its intensity in Puerto Williams (MMI V–VI) — stronger than in the closer-by-distance Ushuaia — is explained by the town sitting directly atop the Magallanes-Fagnano fault system that produced the quake. The event, including a functioning NOAA tsunami-alert protocol, ~1,800 preventive evacuations, and 50+ aftershocks in 24 hours, was experienced firsthand by the author, turning a live USGS data feed into a lived account of Patagonian tectonic risk.

---

## 📊 The Drake Passage Earthquake — May 2, 2025

| Parameter | Value |
|---|---|
| Magnitude | M7.4 |
| Depth | 10 km (shallow — amplified surface impact) |
| Epicenter | Drake Passage, ~219 km south of Ushuaia |
| Local time | 09:58 (GMT-3) |
| USGS event ID | us7000pwkn |
| Intensity in Puerto Williams | MMI V–VI (Strong) |
| Tsunami alert | Yes — NOAA PTWC |
| Preventive evacuations | ~1,800 people |
| Aftershocks (24h) | 50+ |
| Largest aftershock | M6.4 |

---

## 🔵 Key Findings

- **M7.4 in the Drake Passage — the region's largest event in decades** — the shallow 10 km depth amplified surface impact; MMI V–VI intensity in Puerto Williams caused falling objects, minor damage, and widespread alarm in the world's southernmost town.
- **Tsunami sirens at 09:58 — the NOAA protocol worked** — the NOAA Pacific Tsunami Warning Center alert arrived minutes after the quake; sirens sounded in Puerto Williams, Ushuaia, and other towns, and ~1,800 people were evacuated preventively. No destructive wave materialized, but the protocol demonstrably protected lives.
- **Puerto Williams sits directly on the Magallanes-Fagnano fault** — the same Scotia/Magallanes-Fagnano fault system that produced the earthquake runs beneath the town, explaining why intensity there exceeded Ushuaia's despite Ushuaia being geographically closer to the epicenter in straight-line distance.
- **50+ aftershocks in 24 hours** — the largest reaching M6.4, an experience that reshaped the author's understanding of Patagonian tectonic dynamics in real time.
- **Four tectonic plates converge in this region** — the Nazca plate subducts beneath South America at ~70 mm/year (forming the Andes); the Antarctic plate collides to the south at the Drake Passage; the Scotia plate's transform fault cuts through Tierra del Fuego; and the Magallanes-Fagnano fault crosses the island east to west.

---

## 🗺️ Monitored Cities & Risk Levels

| City | Country | Risk Level | Est. Annual Seismicity |
|---|---|---|---|
| Santiago | 🇨🇱 Chile | High | ~174 events/year |
| Punta Arenas | 🇨🇱 Chile | High | ~18 events/year |
| Puerto Natales | 🇨🇱 Chile | Moderate–High | ~12 events/year |
| Puerto Williams | 🇨🇱 Chile | Very High | ~35 events/year |
| Río Grande | 🇦🇷 Argentina | High | ~22 events/year |
| Ushuaia | 🇦🇷 Argentina | Very High | ~30 events/year |
| El Calafate | 🇦🇷 Argentina | Moderate | ~8 events/year |
| Río Gallegos | 🇦🇷 Argentina | Moderate | ~10 events/year |
| Buenos Aires | 🇦🇷 Argentina | Low | ~1.1 events/year |

---

## 🔬 Methodology

```
Real-time monitoring  →  Live seismic data via the USGS Earthquake Catalog
                         API (free, no key required); parameters:
                         minmagnitude=2.0, 200–300 km radius per city, last
                         30 days. Activity % = (30-day event count /
                         historical monthly baseline) × 100, refreshed every
                         5 minutes

Field experience       →  The author was in Puerto Williams when the M7.4
                         struck at 09:58 local time — a direct witness to
                         the tsunami sirens, the evacuation of ~1,800
                         people, and 50+ aftershocks in the following 24
                         hours, with photographic documentation

Geological context      →  Four-plate tectonic framework: Nazca subduction
                         (~70 mm/yr, Andes); Antarctic plate collision
                         (Drake Passage); Scotia transform fault (Tierra
                         del Fuego); Magallanes-Fagnano fault (crosses the
                         island east–west)

Seismic catalog          →  Historical 2020–2025 data combined from USGS
                         (global), CSN Chile (National Seismological
                         Network), and INPRES Argentina — filtered for
                         M≥4.0, Patagonia region, 0–700 km depth

Impact/intensity analysis →  Macroseismic intensity per city via the
                         Boore-Atkinson (2008) attenuation model — Puerto
                         Williams: MMI V–VI; Punta Arenas: MMI III–IV;
                         Ushuaia: MMI IV–V — correlated with structural
                         damage and tsunami alert scope

Live dashboard            →  Seismic activity percentage recalculated
                         every 300 seconds: counts M≥2 events in the last
                         30 days within each city's radius via the USGS
                         API, compared against historical monthly baseline
```

---

## 🖥️ Dashboard Overview

The Streamlit app is organized into eight tabs:

1. **🗺️ Map & Analysis** — live epicenter map (marker size ∝ magnitude), with the Drake Passage M7.4 marked by an orange star and pulsing markers on cities within its impact radius.
2. **🔬 Methodology & Pipeline** — the six-step research pipeline, geological plate context, and the May 2025 MMI intensity breakdown by city.
3. **💡 What We Found** — the key findings above, plus the project's conclusion.
4. **📷 Field Research** — first-hand photos and account from Puerto Williams during and after the earthquake.
5. **📈 Trends** — monthly seismic activity by city (2024) and depth distribution.
6. **🧪 Parameters** — magnitude histogram and regional seismic parameters.
7. **📋 Raw Data** — full event data table.
8. **📚 Sources & Credits** — USGS, CSN, and INPRES citations, and author credentials.

A **live monitoring panel** shows real-time seismic activity percentage per city (USGS API, refreshed every 5 minutes, compared against historical baselines) — one of the few genuinely real-time, API-driven components across the author's portfolio.

The full interface — labels, chart titles, and narrative text — is natively trilingual (PT/EN/ES), switchable from the sidebar.

---

## 🛠️ Tech Stack

| Technology | Use |
|---|---|
| Python 3.11 | Core language |
| Streamlit | Dashboard framework, with 5-minute data caching (`st.cache_data`) |
| Folium + streamlit-folium | Live epicenter mapping |
| Plotly (Graph Objects) | Seismic trend, depth distribution, and magnitude histogram charts |
| Pandas / NumPy | Data processing |
| Requests | Live USGS Earthquake API integration |

---

## 📁 Repository Structure

```
patagonia-seismic/
├── app.py                    # Main dashboard (8 tabs, live USGS API, PT/EN/ES)
├── requirements.txt          # Python dependencies
├── README.md                   # This file (English)
├── README.pt-BR.md             # Portuguese version
└── README.es.md                # Spanish version
```

---

## 🚀 Run Locally

```bash
# Clone the repository
git clone https://github.com/amaurialmeida/patagonia-seismic.git
cd patagonia-seismic

# Install dependencies
pip install -r requirements.txt

# Run
streamlit run app.py
```

---

## 🌐 Live App

🔗 **[patagonia-seismic.streamlit.app](https://patagonia-seismic.streamlit.app/)**

Available in 🇧🇷 Portuguese, 🇺🇸 English, and 🇪🇸 Spanish.

---

## 📚 References

- USGS Earthquake Catalog API — real-time and historical global seismic event data.
- CSN Chile (Centro Sismológico Nacional) — Chilean national seismological network.
- INPRES Argentina (Instituto Nacional de Prevención Sísmica) — Argentine seismic prevention data.
- Boore, D.M.; Atkinson, G.M. (2008) — Ground-motion prediction equations for the average horizontal component of PGA, PGV, and 5%-damped PSA.

---

## 🔗 Academic / Professional Links

| Platform | Link |
|---|---|
| Lattes | http://lattes.cnpq.br/9545242042800090 |
| Escavador | https://www.escavador.com/sobre/8577779/amauri-almeida-de-souza-junior |

---

## 🌿 Environmental Portfolio

This project is part of the author's environmental research and data science portfolio.
🔗 [amaurialmeida.github.io/environmental-portfolio](https://amaurialmeida.github.io/environmental-portfolio)

---

© 2024–2026 · Amauri Almeida de Souza Junior · Independent Field Research · Portfolio Project
