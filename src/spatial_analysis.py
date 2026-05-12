"""
Spatial Accessibility Analysis for Istanbul Healthcare
Implements buffer analysis, nearest facility, and basic accessibility scoring
"""

import geopandas as gpd
import pandas as pd
import numpy as np
from shapely.geometry import Point
from shapely.ops import nearest_points
import warnings
warnings.filterwarnings('ignore')


def load_data(facilities_path, districts_path=None):
    """Load healthcare facilities and optionally district boundaries"""
    facilities = gpd.read_file(facilities_path)
    districts = gpd.read_file(districts_path) if districts_path else None
    return facilities, districts


def buffer_analysis(facilities, buffer_distances_km=[2, 5, 10]):
    """
    Create buffer zones around healthcare facilities
    Returns: GeoDataFrame with buffer polygons
    """
    # Project to UTM Zone 35N (Istanbul)
    facilities_proj = facilities.to_crs("EPSG:32635")
    
    buffers = {}
    for dist_km in buffer_distances_km:
        dist_m = dist_km * 1000
        buffer_gdf = facilities_proj.copy()
        buffer_gdf["geometry"] = facilities_proj.geometry.buffer(dist_m)
        buffer_gdf["buffer_km"] = dist_km
        
        # Dissolve to get union of all buffers
        dissolved = buffer_gdf.dissolve()
        dissolved = dissolved.to_crs("EPSG:4326")
        
        buffers[dist_km] = dissolved
        
        area_km2 = dissolved.to_crs("EPSG:32635").geometry.area.sum() / 1e6
        print(f"Buffer {dist_km}km: covers {area_km2:.1f} km²")
    
    return buffers


def nearest_facility_analysis(points_gdf, facilities):
    """
    Calculate distance from each point to nearest healthcare facility
    
    Args:
        points_gdf: GeoDataFrame with points (district centroids or grid)
        facilities: GeoDataFrame with healthcare facility locations
    
    Returns:
        GeoDataFrame with nearest facility distance added
    """
    # Project to UTM for accurate distance calculation
    points_proj = points_gdf.to_crs("EPSG:32635")
    facilities_proj = facilities.to_crs("EPSG:32635")
    
    from shapely.ops import nearest_points
    
    results = []
    facility_union = facilities_proj.geometry.unary_union
    
    for idx, row in points_proj.iterrows():
        point = row.geometry
        nearest_geom = nearest_points(point, facility_union)[1]
        distance_m = point.distance(nearest_geom)
        
        results.append({
            "geometry": row.geometry,
            "nearest_distance_m": distance_m,
            "nearest_distance_km": distance_m / 1000,
        })
    
    result_gdf = gpd.GeoDataFrame(results, crs="EPSG:32635")
    
    # Merge with original data
    points_gdf = points_gdf.copy()
    points_gdf["nearest_hospital_km"] = [r["nearest_distance_km"] for r in results]
    
    return points_gdf


def calculate_accessibility_score(districts, facilities):
    """
    Calculate a simple accessibility score per district:
    Score = (facility_count / population) * distance_factor
    
    Higher score = better accessibility
    """
    districts_proj = districts.to_crs("EPSG:32635")
    facilities_proj = facilities.to_crs("EPSG:32635")
    
    # Count facilities per district
    joined = gpd.sjoin(facilities_proj, districts_proj, how="left", predicate="within")
    
    # District name column (adjust based on your data)
    district_col = None
    for col in ["name", "district_name", "ilce", "NAME", "ilce_adi"]:
        if col in districts.columns:
            district_col = col
            break
    
    if district_col is None:
        print("Warning: Could not identify district name column")
        district_col = districts.columns[0]
    
    counts = joined.groupby(f"{district_col}_right").size().reset_index(name="facility_count")
    
    # Merge back to districts
    districts = districts.copy()
    districts = districts.merge(counts, left_on=district_col, right_on=f"{district_col}_right", how="left")
    districts["facility_count"] = districts["facility_count"].fillna(0).astype(int)
    
    # Calculate centroid distance to nearest facility
    districts = nearest_facility_analysis(
        districts.copy().set_geometry(districts.geometry.centroid),
        facilities
    )
    
    # Simple accessibility score (0-100)
    max_count = districts["facility_count"].max()
    max_dist = districts["nearest_hospital_km"].max()
    
    districts["count_score"] = (districts["facility_count"] / max_count) * 50
    districts["distance_score"] = (1 - districts["nearest_hospital_km"] / max_dist) * 50
    districts["accessibility_score"] = districts["count_score"] + districts["distance_score"]
    
    return districts


def create_analysis_grid(bounds, cell_size_m=1000):
    """
    Create a regular grid over Istanbul for fine-grained analysis
    
    Args:
        bounds: tuple (minx, miny, maxx, maxy) in EPSG:4326
        cell_size_m: grid cell size in meters
    """
    from shapely.geometry import box
    
    # Convert bounds to UTM
    minx, miny, maxx, maxy = bounds
    
    # Create grid in UTM
    grid_gdf = gpd.GeoDataFrame(
        geometry=[Point(minx + i * 0.01, miny + j * 0.01) 
                  for i in range(int((maxx - minx) / 0.01))
                  for j in range(int((maxy - miny) / 0.01))],
        crs="EPSG:4326"
    )
    
    return grid_gdf


def generate_summary_statistics(districts):
    """Generate summary statistics for the analysis"""
    
    stats = {
        "total_districts": len(districts),
        "total_facilities": int(districts["facility_count"].sum()),
        "avg_facilities_per_district": round(districts["facility_count"].mean(), 1),
        "median_distance_km": round(districts["nearest_hospital_km"].median(), 2),
        "max_distance_km": round(districts["nearest_hospital_km"].max(), 2),
        "min_distance_km": round(districts["nearest_hospital_km"].min(), 2),
        "avg_accessibility_score": round(districts["accessibility_score"].mean(), 1),
        "best_district": districts.loc[districts["accessibility_score"].idxmax()].get("name", "N/A"),
        "worst_district": districts.loc[districts["accessibility_score"].idxmin()].get("name", "N/A"),
    }
    
    print("\n=== Accessibility Analysis Summary ===")
    for key, val in stats.items():
        print(f"  {key}: {val}")
    
    return stats


if __name__ == "__main__":
    # Quick test
    facilities, _ = load_data("data/istanbul_healthcare_facilities.geojson")
    print(f"Loaded {len(facilities)} facilities")
    
    buffers = buffer_analysis(facilities)
    print("\nBuffer analysis complete!")
