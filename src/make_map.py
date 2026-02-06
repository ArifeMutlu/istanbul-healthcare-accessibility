"""
Create simple map of facilities.
"""

import folium
from load_data import load_facilities, make_geodataframe

def create_map(gdf, save_path='outputs/map.html'):
    """Create interactive map of facilities."""
    
    # Create map centered on Istanbul
    m = folium.Map(location=[41.0082, 28.9784], zoom_start=11)
    
    # Add each facility as a marker
    for idx, row in gdf.iterrows():
        folium.Marker(
            location=[row.geometry.y, row.geometry.x],
            popup=row['name'],
            icon=folium.Icon(color='red' if row['type']=='hospital' else 'blue')
        ).add_to(m)
    
    m.save(save_path)
    print(f"Map saved to {save_path}")
    return m

if __name__ == "__main__":
    # Load data
    df = load_facilities()
    gdf = make_geodataframe(df)
    
    # Create map
    create_map(gdf)
    print("Open outputs/map.html in browser to see map!")
