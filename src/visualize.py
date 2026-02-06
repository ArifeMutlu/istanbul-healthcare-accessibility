"""
Visualization functions for healthcare accessibility.
"""
import folium
import matplotlib.pyplot as plt

def create_interactive_map(facilities_gdf, center=[41.0082, 28.9784]):
    """
    Create interactive map of healthcare facilities.
    
    Args:
        facilities_gdf: GeoDataFrame with facility points
        center: [lat, lon] for map center
        
    Returns:
        folium.Map object
    """
    # Create base map
    m = folium.Map(location=center, zoom_start=11, tiles='OpenStreetMap')
    
    # Define colors for facility types
    color_map = {
        'hastane': 'red',
        'sağlık_merkezi': 'blue',
        'sağlık_ocağı': 'green'
    }
    
    # Add each facility
    for idx, row in facilities_gdf.iterrows():
        folium.CircleMarker(
            location=[row.geometry.y, row.geometry.x],
            radius=8,
            popup=f"<b>{row['name']}</b><br>Tip: {row['type']}",
            color=color_map.get(row['type'], 'gray'),
            fill=True,
            fillOpacity=0.7
        ).add_to(m)
    
    return m

def save_map(map_obj, filepath='outputs/facility_map.html'):
    """Save map to HTML file."""
    map_obj.save(filepath)
    print(f"Map saved to {filepath}")

def plot_facility_distribution(facilities_gdf):
    """Create bar chart of facility types."""
    type_counts = facilities_gdf['type'].value_counts()
    
    plt.figure(figsize=(10, 6))
    type_counts.plot(kind='bar', color=['red', 'blue', 'green'])
    plt.title('Healthcare Facility Distribution in Istanbul', fontsize=14)
    plt.xlabel('Facility Type', fontsize=12)
    plt.ylabel('Count', fontsize=12)
    plt.xticks(rotation=45)
    plt.tight_layout()
    
    return plt.gcf()

if __name__ == "__main__":
    from load_data import load_sample_facilities
    
    # Load data
    facilities = load_sample_facilities()
    
    # Create and save map
    m = create_interactive_map(facilities)
    save_map(m)
    
    # Create bar chart
    fig = plot_facility_distribution(facilities)
    plt.savefig('outputs/facility_distribution.png', dpi=300, bbox_inches='tight')
    print("Chart saved to outputs/facility_distribution.png")
    
    plt.show()