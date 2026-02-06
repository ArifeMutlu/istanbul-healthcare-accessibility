"""
Load and process healthcare facility data.
"""
import pandas as pd
import geopandas as gpd
from shapely.geometry import Point

def load_sample_facilities():
    """Load sample healthcare facilities for Istanbul."""
    data = {
        'name': [
            'Taksim Hastanesi',
            'Kadıköy Sağlık Merkezi',
            'Bakırköy Devlet Hastanesi',
            'Şişli Etfal Hastanesi',
            'Beşiktaş Sağlık Ocağı',
            'Üsküdar Devlet Hastanesi',
            'Beyoğlu Göz Hastanesi',
            'Fatih Devlet Hastanesi'
        ],
        'type': [
            'hastane', 'sağlık_merkezi', 'hastane', 'hastane',
            'sağlık_ocağı', 'hastane', 'hastane', 'hastane'
        ],
        'latitude': [
            41.0369, 40.9903, 40.9799, 41.0606,
            41.0428, 41.0221, 41.0341, 41.0186
        ],
        'longitude': [
            28.9850, 29.0260, 28.8719, 28.9875,
            29.0072, 29.0188, 28.9740, 28.9497
        ]
    }
    
    df = pd.DataFrame(data)
    
    # Convert to GeoDataFrame
    geometry = [Point(xy) for xy in zip(df.longitude, df.latitude)]
    gdf = gpd.GeoDataFrame(df, geometry=geometry, crs="EPSG:4326")
    
    return gdf

def load_istanbul_districts():
    """
    Load Istanbul district boundaries.
    For now, return sample bounding box.
    TODO: Load real district data from OSM.
    """
    # Istanbul bounding box (simplified)
    from shapely.geometry import box
    
    # Rough Istanbul bounds
    minx, miny = 28.5, 40.8
    maxx, maxy = 29.5, 41.3
    
    bbox = box(minx, miny, maxx, maxy)
    
    gdf = gpd.GeoDataFrame(
        {'name': ['Istanbul'], 'geometry': [bbox]},
        crs="EPSG:4326"
    )
    
    return gdf

if __name__ == "__main__":
    # Test
    print("Loading facilities...")
    facilities = load_sample_facilities()
    print(f"Loaded {len(facilities)} facilities")
    print(facilities.head())
    
    print("\nLoading districts...")
    districts = load_istanbul_districts()
    print(districts)