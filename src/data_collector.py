"""
Istanbul Healthcare Facility Data Collector
Collects hospital and clinic data from OpenStreetMap using Overpass API and osmnx.
"""

import requests
import pandas as pd
import geopandas as gpd
from shapely.geometry import Point
import json
import os
from datetime import datetime


_DEFAULT_FACILITIES_PATH = os.path.join(
    os.path.dirname(__file__), '..', 'data', 'istanbul_healthcare_facilities.geojson'
)
_DEFAULT_DISTRICTS_PATH = os.path.join(
    os.path.dirname(__file__), '..', 'data', 'istanbul_districts.geojson'
)


def fetch_healthcare_from_osm():
    """Fetch healthcare facilities in Istanbul from OpenStreetMap via osmnx."""
    import osmnx as ox

    print("Fetching healthcare facilities from OpenStreetMap (osmnx)...")

    tags = {
        "amenity": ["hospital", "clinic", "doctors"],
        "healthcare": True,
    }
    gdf = ox.features_from_place("İstanbul, Turkey", tags=tags)
    print(f"Found {len(gdf)} records")

    # Project to UTM for accurate centroid, then back to WGS84
    gdf = gdf.copy()
    centroids = gdf.geometry.to_crs("EPSG:32636").centroid.to_crs("EPSG:4326")

    def classify_type(row):
        amenity = str(row.get("amenity", "")).lower()
        if amenity == "hospital":
            return "Hospital"
        elif amenity == "clinic":
            return "Clinic"
        elif amenity == "doctors":
            return "Doctor"
        hc = str(row.get("healthcare", ""))
        if hc and hc != "nan":
            return hc.title()
        return "Other"

    def classify_operator(row):
        op = (str(row.get("operator", "")) + " " + str(row.get("operator:type", ""))).lower()
        if any(k in op for k in ["devlet", "public", "sağlık bakanlığı", "government"]):
            return "Public"
        elif any(k in op for k in ["özel", "private"]):
            return "Private"
        elif any(k in op for k in ["üniversite", "university"]):
            return "University"
        return "Unknown"

    def get_col(col):
        return gdf[col].fillna("") if col in gdf.columns else [""] * len(gdf)

    result = gpd.GeoDataFrame(
        {
            "name": get_col("name").replace("", "Unknown"),
            "name_en": get_col("name:en"),
            "amenity": get_col("amenity"),
            "healthcare": get_col("healthcare"),
            "operator": get_col("operator"),
            "addr_district": get_col("addr:district"),
            "phone": get_col("phone"),
            "website": get_col("website"),
            "latitude": centroids.y.values,
            "longitude": centroids.x.values,
            "facility_type": [classify_type(row) for _, row in gdf.iterrows()],
            "sector": [classify_operator(row) for _, row in gdf.iterrows()],
        },
        geometry=centroids.values,
        crs="EPSG:4326",
    )

    return result


def fetch_istanbul_districts():
    """
    Fetch Istanbul district (ilçe) boundaries from OSM using osmnx.
    Returns a GeoDataFrame with district polygons and a 'name' column.
    """
    import osmnx as ox

    print("Fetching Istanbul district (ilçe) boundaries from OSM...")
    # Query only admin_level=6 (ilçe in Turkey). Using a single key avoids
    # osmnx treating multiple keys as OR and returning all admin boundaries.
    gdf = ox.features_from_place("İstanbul, Turkey", tags={"admin_level": "6"})

    # Keep only polygon/multipolygon features with a name
    gdf = gdf[gdf.geometry.geom_type.isin(["Polygon", "MultiPolygon"])].copy()
    gdf = gdf[gdf["name"].notna()].copy()

    # Deduplicate: keep the largest polygon per district name
    gdf = gdf.copy()
    gdf["_area"] = gdf.geometry.to_crs("EPSG:32636").area
    gdf = gdf.sort_values("_area", ascending=False).drop_duplicates(subset="name")

    result = gdf[["name", "geometry"]].reset_index(drop=True)
    print(f"Fetched {len(result)} districts")
    return result


def load_or_fetch_facilities(cache_path=None):
    """
    Load facilities from local GeoJSON cache, or fetch from OSM if not cached.
    Saves newly fetched data to cache_path automatically.
    """
    if cache_path is None:
        cache_path = _DEFAULT_FACILITIES_PATH

    cache_path = os.path.normpath(cache_path)

    if os.path.exists(cache_path):
        print(f"Loading facilities from cache: {cache_path}")
        return gpd.read_file(cache_path)

    gdf = fetch_healthcare_from_osm()
    save_data(gdf, output_dir=os.path.dirname(cache_path))
    return gdf


def load_or_fetch_districts(cache_path=None):
    """
    Load district boundaries from local GeoJSON cache, or fetch from OSM.
    """
    if cache_path is None:
        cache_path = _DEFAULT_DISTRICTS_PATH

    cache_path = os.path.normpath(cache_path)

    if os.path.exists(cache_path):
        print(f"Loading districts from cache: {cache_path}")
        return gpd.read_file(cache_path)

    gdf = fetch_istanbul_districts()
    os.makedirs(os.path.dirname(cache_path), exist_ok=True)
    gdf.to_file(cache_path, driver="GeoJSON")
    print(f"Districts cached to: {cache_path}")
    return gdf


def save_data(gdf, output_dir=None):
    """Save collected facility data in GeoJSON, CSV, and metadata JSON."""
    if output_dir is None:
        output_dir = os.path.join(os.path.dirname(__file__), '..', 'data')

    os.makedirs(output_dir, exist_ok=True)

    geojson_path = os.path.join(output_dir, "istanbul_healthcare_facilities.geojson")
    gdf.to_file(geojson_path, driver="GeoJSON")
    print(f"Saved GeoJSON: {geojson_path}")

    csv_path = os.path.join(output_dir, "istanbul_healthcare_facilities.csv")
    gdf.drop(columns="geometry").to_csv(csv_path, index=False, encoding="utf-8-sig")
    print(f"Saved CSV: {csv_path}")

    print(f"\n=== Data Summary ===")
    print(f"Total facilities: {len(gdf)}")
    print(f"\nBy type:\n{gdf['facility_type'].value_counts().to_string()}")
    print(f"\nBy sector:\n{gdf['sector'].value_counts().to_string()}")

    metadata = {
        "source": "OpenStreetMap via Overpass API",
        "collection_date": datetime.now().isoformat(),
        "total_facilities": len(gdf),
        "crs": "EPSG:4326",
        "types": gdf["facility_type"].value_counts().to_dict(),
    }
    meta_path = os.path.join(output_dir, "data_metadata.json")
    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2, ensure_ascii=False)
    print(f"Saved metadata: {meta_path}")


if __name__ == "__main__":
    facilities = load_or_fetch_facilities()
    print(f"\nFacilities ready: {len(facilities)} records")

    districts = load_or_fetch_districts()
    print(f"Districts ready: {len(districts)} districts")
