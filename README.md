# Istanbul Healthcare Accessibility Analysis 🏥

Geospatial analysis of healthcare facility accessibility across Istanbul neighborhoods.

## 🎯 Objective

Analyze which neighborhoods in Istanbul have good/poor access to healthcare facilities using spatial analysis.

## 📊 Data Sources

- Healthcare facilities: Istanbul Municipality Open Data
- Neighborhood boundaries: Istanbul Municipality
- District boundaries: Istanbul Municipality

## 🛠️ Technologies

- Python 3.9+
- GeoPandas
- Matplotlib
- Folium (for interactive maps)

## 🚀 Setup & Installation
```bash
git clone https://github.com/ArifeMutlu/istanbul-healthcare-accessibility.git
cd istanbul-healthcare-accessibility
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
jupyter notebook notebooks/
```

## 📈 Analysis Methods
1. **Buffer Analysis**: 2km, 5km, 10km zones around hospitals
2. **Nearest Facility**: Closest hospital to each neighborhood centroid
3. **Two-Step Floating Catchment Area (2SFCA)**: Population-weighted accessibility scoring
4. **Network Analysis**: Real road-network travel time using OSMnx
5. **Isochrone Mapping**: 15/30 minute travel time zones
6. **Visualization**: Interactive Folium maps + static Matplotlib charts

## 📊 Status
- [x] Project setup & data collection
- [x] Data exploration & cleaning
- [ ] Spatial accessibility analysis
- [ ] Network-based analysis (OSMnx)
- [ ] Interactive dashboard
- [ ] Final report & findings

## 📝 License

MIT License

## 👤 Author

Arife Mutlu - [LinkedIn](https://linkedin.com/in/arife-mutlu-75020942)
