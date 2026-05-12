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

## 📈 Analysis Methods

1. **Buffer Analysis**: 2km, 5km, 10km zones around hospitals
2. **Nearest Facility**: Closest hospital to each neighborhood
3. **Service Area Coverage**: Percentage of population within X km
4. **Visualization**: Interactive maps showing accessibility

## 🚀 Status

✅ Core implementation complete:
- Data loading from CSV + GeoDataFrame conversion
- 30 sample facilities across Istanbul districts
- Interactive Folium maps (facility map, buffer map)
- Nearest facility finder (geodesic distance via UTM projection)
- Buffer analysis: 2km / 5km / 10km coverage zones
- Jupyter EDA notebook (`notebooks/01_data_exploration.ipynb`)

🔄 Next: real district boundaries from OSM, actual facility data from Istanbul Municipality

## 📝 License

MIT License

## 👤 Author

Arife Mutlu - [LinkedIn](https://linkedin.com/in/arife-mutlu-75020942)
