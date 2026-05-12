"""
Buffer analysis: coverage zones around healthcare facilities.
"""

import geopandas as gpd

# UTM zone 37N — metric CRS for Istanbul
_UTM_CRS = "EPSG:32637"


def create_buffers(facilities_gdf, distances_km=None):
    """
    Create buffer zones around facilities.

    Args:
        facilities_gdf: GeoDataFrame of facility points (EPSG:4326)
        distances_km: list of distances in km (default [2, 5, 10])

    Returns:
        dict mapping distance_km -> dissolved GeoDataFrame (EPSG:4326)
    """
    if distances_km is None:
        distances_km = [2, 5, 10]

    projected = facilities_gdf.to_crs(_UTM_CRS)
    buffers = {}

    for km in distances_km:
        buf = projected.copy()
        buf['geometry'] = projected.geometry.buffer(km * 1000)
        dissolved = buf.dissolve()[['geometry']]
        buffers[km] = dissolved.to_crs("EPSG:4326")

    return buffers


def coverage_percentage(district_gdf, buffer_gdf):
    """
    Percentage of district area covered by buffer zones.

    Args:
        district_gdf: GeoDataFrame of district polygon(s) (EPSG:4326)
        buffer_gdf: GeoDataFrame of buffer polygon(s) (EPSG:4326)

    Returns:
        float: percentage of district area covered
    """
    dist_proj = district_gdf.to_crs(_UTM_CRS)
    buf_proj = buffer_gdf.to_crs(_UTM_CRS)

    district_union = dist_proj.union_all()
    buffer_union = buf_proj.union_all()

    intersection = district_union.intersection(buffer_union)
    return (intersection.area / district_union.area) * 100


if __name__ == "__main__":
    import sys
    import os
    sys.path.insert(0, os.path.dirname(__file__))
    from load_data import load_sample_facilities, load_istanbul_districts

    facilities = load_sample_facilities()
    districts = load_istanbul_districts()

    buffers = create_buffers(facilities)
    for km, buf_gdf in buffers.items():
        pct = coverage_percentage(districts, buf_gdf)
        print(f"{km}km buffer covers {pct:.1f}% of Istanbul bounding area")
