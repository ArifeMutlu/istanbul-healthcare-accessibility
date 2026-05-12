"""
Create simple map of facilities.
"""

import folium
from load_data import load_facilities, make_geodataframe

_TYPE_COLORS = {
    'hastane': 'red',
    'sağlık_merkezi': 'blue',
    'sağlık_ocağı': 'green',
}


def create_map(gdf, save_path='outputs/map.html'):
    """Create interactive map of facilities."""
    m = folium.Map(location=[41.0082, 28.9784], zoom_start=11)

    for idx, row in gdf.iterrows():
        color = _TYPE_COLORS.get(row['type'], 'gray')
        folium.Marker(
            location=[row.geometry.y, row.geometry.x],
            popup=row['name'],
            icon=folium.Icon(color=color)
        ).add_to(m)

    m.save(save_path)
    print(f"Map saved to {save_path}")
    return m


if __name__ == "__main__":
    import os
    os.makedirs('outputs', exist_ok=True)

    df = load_facilities()
    gdf = make_geodataframe(df)

    create_map(gdf)
    print("Open outputs/map.html in browser to see map!")
