"""
Find nearest facility to a location.
"""

from load_data import load_facilities, make_geodataframe
from shapely.geometry import Point

def find_nearest(location, gdf, k=1):
    """
    Find k nearest facilities to a location.
    
    Args:
        location: (longitude, latitude) tuple
        gdf: GeoDataFrame of facilities
        k: number of nearest to find
    """
    point = Point(location)
    
    # Calculate distances (simple, not geodesic)
    gdf['distance'] = gdf.geometry.distance(point)
    
    # Get k nearest
    nearest = gdf.nsmallest(k, 'distance')
    
    return nearest[['name', 'type', 'distance']]

if __name__ == "__main__":
    # Load facilities
    df = load_facilities()
    gdf = make_geodataframe(df)
    
    # Find nearest to Taksim Square
    taksim = (28.9850, 41.0369)
    nearest = find_nearest(taksim, gdf, k=3)
    
    print("3 nearest facilities to Taksim:")
    print(nearest)
