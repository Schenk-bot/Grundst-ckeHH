# 🏠 Grundstücksanalyse Hamburg

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Flask-2.0+-green.svg)](https://flask.palletsprojects.com/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

**Eine professionelle Analyseplattform für Grundstücksangebote in Hamburg mit intelligentem Qualitäts-Scoring-System**

![Dashboard Preview](https://via.placeholder.com/800x400/4A90E2/FFFFFF?text=Hamburg+Grundst%C3%BCcksanalyse+Dashboard)

---

## 📊 Übersicht

Diese Plattform analysiert **162 Grundstücksangebote** in Hamburg und bewertet sie nach einem intelligenten **4-Kriterien-Scoring-System**. Basierend auf echten Daten von ImmobilienScout24.

### 🎯 Hauptfeatures

- ✅ **Qualitäts-Scoring** mit 4 gewichteten Kriterien
- ✅ **Interaktives Dashboard** mit Plotly-Charts
- ✅ **Interaktive Karte** mit Farbcodierung nach Qualität
- ✅ **Preis-Qualitäts-Verhältnis-Analyse**
- ✅ **Excel-Reports** mit umfassenden Statistiken
- ✅ **REST API** für programmatischen Zugriff
- ✅ **47 Stadtteile** analysiert

---

## 🚀 Quick Start

### 1. Repository klonen
```bash
git clone https://github.com/IHR-USERNAME/grundstueck-analyse-hamburg.git
cd grundstueck-analyse-hamburg
```

### 2. Abhängigkeiten installieren
```bash
pip install -r requirements.txt
```

### 3. Web-Plattform starten
```bash
python web_app_enhanced.py
```

### 4. Browser öffnen
Öffnen Sie: **http://localhost:5001**

---

## 📈 Marktüberblick Hamburg

| Metrik | Wert |
|--------|------|
| **Anzahl Angebote** | 162 |
| **Stadtteile** | 47 |
| **Ø Preis** | €1.130.955 |
| **Ø Preis/m²** | €727 |
| **Ø Fläche** | 2.000 m² |
| **Preisspanne** | €399.000 - €7.350.000 |

### 💎 Top 3 teuerste Stadtteile
1. **Blankenese**: €2.119.000 (Ø)
2. **Wellingsbüttel**: €1.942.143 (Ø)
3. **Rissen**: €1.854.750 (Ø)

---

## ⭐ Qualitäts-Scoring-System

### Bewertungskriterien (gewichtet)

```
┌─────────────────────────────────────────────────────────┐
│ 1. Baugenehmigungsstatus (40%) - HAUPTKRITERIUM        │
│    ✅ Mit Baugenehmigung: 100 Punkte                   │
│    📋 Mit Bauvorbescheid: 60 Punkte                    │
│    ❌ Ohne Genehmigung: 30 Punkte                      │
├─────────────────────────────────────────────────────────┤
│ 2. Erschließung (25%)                                   │
│    ✅ Voll erschlossen: 100 Punkte                     │
│    🔨 Teilerschlossen: 50 Punkte                       │
│    ❌ Nicht erschlossen: 0 Punkte                      │
├─────────────────────────────────────────────────────────┤
│ 3. Kurzfristige Bebaubarkeit (20%)                     │
│    ✅ Ja: 100 Punkte                                    │
│    ❌ Nein: 0 Punkte                                    │
├─────────────────────────────────────────────────────────┤
│ 4. Abriss-Notwendigkeit (15%)                          │
│    ✅ Kein Abriss: 100 Punkte                          │
│    🏚️ Abriss erforderlich: 0 Punkte                   │
└─────────────────────────────────────────────────────────┘
```

### 📊 Qualitätsverteilung

- **Sehr Gut (80-100)**: 0 Grundstücke (0%)
- **Gut (60-79)**: 55 Grundstücke (34%)
- **Mittel (40-59)**: 102 Grundstücke (63%)
- **Niedrig (0-39)**: 5 Grundstücke (3%)

### 💰 KEY INSIGHT
**67% der Angebote sind unterbewertet!** 🎯
- Sehr günstig: 98 Angebote (60%)
- Günstig: 11 Angebote (7%)

---

## 🗺️ Interaktive Karte

Die Karte zeigt alle Grundstücke mit **Farbcodierung nach Qualität**:

- 🟢 **Grün**: Sehr Gut (80-100)
- 🔵 **Blau**: Gut (60-79)
- 🟠 **Orange**: Mittel (40-59)
- 🔴 **Rot**: Niedrig (0-39)

---

## 📁 Projektstruktur

```
grundstueck-analyse-hamburg/
├── web_app_enhanced.py          # Hauptserver mit Qualitäts-Features
├── quality_scoring.py           # Scoring-Engine
├── data_parser.py               # XML → CSV/JSON Parser
├── advanced_analytics.py        # Erweiterte Analysen
│
├── templates/                   # HTML-Templates
│   ├── index_enhanced.html      # Dashboard
│   └── map_enhanced.html        # Interaktive Karte
│
├── charts/                      # Visualisierungen (PNG, 300 DPI)
│   ├── quality_distribution.png
│   ├── quality_vs_price.png
│   ├── value_rating_distribution.png
│   └── quality_factors_heatmap.png
│
├── grundstuecke_hamburg_mit_qualitaet.csv  # Hauptdaten mit Scores
├── grundstuecke_mit_qualitaet.xlsx         # Excel-Report
│
└── docs/                        # Dokumentation
    ├── README.md
    ├── SCHNELLSTART.md
    ├── QUALITAETS_SCORING_ANLEITUNG.md
    └── ZUSAMMENFASSUNG.txt
```

---

## 🛠️ Technologie-Stack

- **Backend**: Python 3.8+, Flask
- **Datenverarbeitung**: Pandas, NumPy
- **Visualisierung**: Plotly, Matplotlib, Seaborn
- **Karten**: Folium
- **Frontend**: HTML5, Bootstrap 5, JavaScript
- **Datenformat**: CSV, JSON, Excel (XLSX)

---

## 📊 Verfügbare Analysen

### 1. **Web-Dashboard** (`web_app_enhanced.py`)
- Qualitätsverteilung
- Score vs. Preis/m²
- Preis-Bewertungen
- Stadtteile nach Qualität
- Interaktive Karte

### 2. **Qualitäts-Scoring** (`quality_scoring.py`)
```bash
python quality_scoring.py
```
Erstellt:
- CSV mit allen Scores
- Excel-Report (6 Sheets)
- 4 hochauflösende Charts

### 3. **Erweiterte Analysen** (`advanced_analytics.py`)
```bash
python advanced_analytics.py
```
Erstellt:
- Stadtteil-Rankings
- Preissegment-Analysen
- Best-Value-Finder

---

## 🔌 REST API

### Endpoints

```bash
# Alle Grundstücke
GET http://localhost:5001/api/grundstuecke

# Einzelnes Grundstück
GET http://localhost:5001/api/grundstueck/<id>

# Stadtteile-Statistiken
GET http://localhost:5001/api/stadtteile

# Qualitäts-Statistiken
GET http://localhost:5001/api/quality-stats
```

---

## 📖 Dokumentation

- **[README.md](README.md)** - Technische Dokumentation
- **[SCHNELLSTART.md](SCHNELLSTART.md)** - Quick Start Guide
- **[QUALITAETS_SCORING_ANLEITUNG.md](QUALITAETS_SCORING_ANLEITUNG.md)** - Scoring-System detailliert
- **[ZUSAMMENFASSUNG.txt](ZUSAMMENFASSUNG.txt)** - Projektübersicht

---

## 🤝 Beiträge

Contributions sind willkommen! Bitte:
1. Fork das Repository
2. Erstelle einen Feature Branch (`git checkout -b feature/AmazingFeature`)
3. Commit deine Änderungen (`git commit -m 'Add AmazingFeature'`)
4. Push zum Branch (`git push origin feature/AmazingFeature`)
5. Öffne einen Pull Request

---

## 📄 Lizenz

Dieses Projekt steht unter der MIT-Lizenz. Siehe [LICENSE](LICENSE) für Details.

---

## 👨‍💻 Autor

Erstellt mit ❤️ für die Grundstücksanalyse in Hamburg

---

## 📞 Support

Bei Fragen oder Problemen:
- 📧 Issue auf GitHub öffnen
- 📖 Dokumentation lesen
- 🔧 Pull Request erstellen

---

## 🌟 Features in Entwicklung

- [ ] Historische Preisentwicklung
- [ ] Predictive Analytics (ML-Modelle)
- [ ] Vergleich mit anderen Städten
- [ ] Mobile App
- [ ] Export nach PDF

---

**⭐ Wenn Ihnen dieses Projekt gefällt, geben Sie ihm einen Stern auf GitHub!**
