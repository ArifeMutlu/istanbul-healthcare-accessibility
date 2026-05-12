"""
Visualization module for Istanbul Healthcare Accessibility
Creates both static (Matplotlib) and interactive (Folium) maps
"""

import geopandas as gpd
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import folium
from folium.plugins import MarkerCluster, HeatMap
import os


def plot_facility_distribution(facilities, districts=None, save_path=None):
    """Plot healthcare facility distribution map"""
    
    fig, ax = plt.subplots(1, 1, figsize=(14, 10))
    
    if districts is not None:
        districts.plot(ax=ax, color="#f0f0f0", edgecolor="#333333", linewidth=0.5)
    
    # Color by type
    colors = {
        "Hospital": "#e74c3c",
        "Clinic": "#3498db",
        "Doctor": "#2ecc71",
        "Other": "#95a5a6"
    }
    
    for ftype, color in colors.items():
        subset = facilities[facilities["facility_type"] == ftype]
        if len(subset) > 0:
            subset.plot(ax=ax, color=color, markersize=15, alpha=0.7, label=f"{ftype} ({len(subset)})")
    
    ax.legend(loc="upper left", fontsize=10)
    ax.set_title("Istanbul Healthcare Facilities Distribution", fontsize=16, fontweight="bold")
    ax.set_axis_off()
    plt.tight_layout()
    
    if save_path:
        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        plt.savefig(save_path, dpi=150, bbox_inches="tight")
        print(f"Saved: {save_path}")
    
    plt.show()


def plot_accessibility_choropleth(districts, score_column="accessibility_score", save_path=None):
    """Plot accessibility score as choropleth map"""
    
    fig, ax = plt.subplots(1, 1, figsize=(14, 10))
    
    districts.plot(
        column=score_column,
        ax=ax,
        legend=True,
        legend_kwds={"label": "Accessibility Score", "orientation": "horizontal", "shrink": 0.6},
        cmap="RdYlGn",
        edgecolor="black",
        linewidth=0.5,
        missing_kwds={"color": "lightgrey"}
    )
    
    ax.set_title("Istanbul Healthcare Accessibility by District", fontsize=16, fontweight="bold")
    ax.set_axis_off()
    plt.tight_layout()
    
    if save_path:
        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        plt.savefig(save_path, dpi=150, bbox_inches="tight")
        print(f"Saved: {save_path}")
    
    plt.show()


def create_interactive_map(facilities, districts=None, save_path=None):
    """Create an interactive Folium map with clustered markers"""
    
    # Istanbul center
    m = folium.Map(location=[41.0082, 28.9784], zoom_start=10, tiles="CartoDB positron")
    
    # Add district boundaries if available
    if districts is not None:
        folium.GeoJson(
            districts,
            style_function=lambda x: {
                "fillColor": "#f0f0f0",
                "color": "#333333",
                "weight": 1,
                "fillOpacity": 0.3,
            },
            tooltip=folium.GeoJsonTooltip(
                fields=[col for col in ["name", "district_name", "ilce"] if col in districts.columns][:1],
                aliases=["District"],
            )
        ).add_to(m)
    
    # Marker cluster
    marker_cluster = MarkerCluster(name="Healthcare Facilities").add_to(m)
    
    icon_map = {
        "Hospital": ("hospital", "red"),
        "Clinic": ("plus-sign", "blue"),
        "Doctor": ("user", "green"),
        "Other": ("info-sign", "gray"),
    }
    
    for _, row in facilities.iterrows():
        ftype = row.get("facility_type", "Other")
        icon_name, icon_color = icon_map.get(ftype, ("info-sign", "gray"))
        
        popup_html = f"""
        <b>{row.get('name', 'N/A')}</b><br>
        Type: {ftype}<br>
        Sector: {row.get('sector', 'N/A')}<br>
        District: {row.get('addr_district', 'N/A')}
        """
        
        folium.Marker(
            location=[row.geometry.y, row.geometry.x],
            popup=folium.Popup(popup_html, max_width=250),
            icon=folium.Icon(color=icon_color, icon=icon_name, prefix="glyphicon"),
        ).add_to(marker_cluster)
    
    # Heatmap layer
    heat_data = [[row.geometry.y, row.geometry.x] for _, row in facilities.iterrows()]
    HeatMap(heat_data, name="Density Heatmap", radius=15, blur=10).add_to(m)
    
    # Layer control
    folium.LayerControl().add_to(m)
    
    if save_path:
        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        m.save(save_path)
        print(f"Saved interactive map: {save_path}")
    
    return m


def create_accessibility_interactive_map(districts, score_column="accessibility_score", save_path=None):
    """Create interactive choropleth of accessibility scores"""
    
    m = folium.Map(location=[41.0082, 28.9784], zoom_start=10, tiles="CartoDB positron")
    
    # Find the name column
    name_col = None
    for col in ["name", "district_name", "ilce", "NAME"]:
        if col in districts.columns:
            name_col = col
            break
    
    folium.Choropleth(
        geo_data=districts,
        data=districts,
        columns=[name_col, score_column] if name_col else None,
        key_on=f"feature.properties.{name_col}" if name_col else None,
        fill_color="RdYlGn",
        fill_opacity=0.7,
        line_opacity=0.5,
        legend_name="Accessibility Score",
        name="Accessibility"
    ).add_to(m)
    
    folium.LayerControl().add_to(m)
    
    if save_path:
        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        m.save(save_path)
        print(f"Saved: {save_path}")
    
    return m


if __name__ == "__main__":
    facilities = gpd.read_file("data/istanbul_healthcare_facilities.geojson")
    print(f"Loaded {len(facilities)} facilities")
    
    # Static map
    plot_facility_distribution(facilities, save_path="outputs/maps/facility_distribution.png")
    
    # Interactive map
    create_interactive_map(facilities, save_path="outputs/maps/interactive_map.html")
    
    print("Visualization complete!")
