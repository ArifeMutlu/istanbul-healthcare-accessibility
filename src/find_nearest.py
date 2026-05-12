"""
Find nearest facility to a location.
"""

from load_data import load_facilities, make_geodataframe
from shapely.geometry import Point

# UTM zone 37N — accurate metric distances for Istanbul
_UTM_CRS = "EPSG:32636"  # UTM Zone 36N — correct for Istanbul


def find_nearest(location, gdf, k=1):
    """
    Find k nearest facilities to a location.

    Args:
        location: (longitude, latitude) tuple
        gdf: GeoDataFrame of facilities (EPSG:4326)
        k: number of nearest to find

    Returns:
        DataFrame with name, type, distance_m columns
    """
    import geopandas as gpd
    from shapely.geometry import Point as _Point

    point_gdf = gpd.GeoDataFrame(
        geometry=[_Point(location)], crs="EPSG:4326"
    ).to_crs(_UTM_CRS)

    projected = gdf.to_crs(_UTM_CRS).copy()
    projected['distance_m'] = projected.geometry.distance(point_gdf.geometry.iloc[0])

    nearest = projected.nsmallest(k, 'distance_m')
    return nearest[['name', 'facility_type', 'distance_m']]


if __name__ == "__main__":
    df = load_facilities()
    gdf = make_geodataframe(df)

    taksim = (28.9850, 41.0369)
    nearest = find_nearest(taksim, gdf, k=3)

    print("3 nearest facilities to Taksim:")
    print(nearest)
