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
    """Fetch healthcare facilities in Istanbul from OpenStreetMap via Overpass API."""

    overpass_url = "http://overpass-api.de/api/interpreter"

    query = """
    [out:json][timeout:120];
    area["name"="İstanbul"]["admin_level"="4"]->.istanbul;
    (
      node["amenity"="hospital"](area.istanbul);
      way["amenity"="hospital"](area.istanbul);
      node["amenity"="clinic"](area.istanbul);
      way["amenity"="clinic"](area.istanbul);
      node["amenity"="doctors"](area.istanbul);
      way["amenity"="doctors"](area.istanbul);
      node["healthcare"](area.istanbul);
      way["healthcare"](area.istanbul);
    );
    out center;
    """

    print("Fetching healthcare facilities from OpenStreetMap...")
    response = requests.get(overpass_url, params={"data": query}, timeout=130)

    if response.status_code != 200:
        raise Exception(f"Overpass API error: {response.status_code}")

    data = response.json()
    elements = data.get("elements", [])
    print(f"Found {len(elements)} healthcare facilities")

    facilities = []
    for el in elements:
        lat = el.get("lat") or el.get("center", {}).get("lat")
        lon = el.get("lon") or el.get("center", {}).get("lon")
        tags = el.get("tags", {})

        if lat and lon:
            facilities.append({
                "osm_id": el["id"],
                "name": tags.get("name", "Unknown"),
                "name_en": tags.get("name:en", ""),
                "amenity": tags.get("amenity", ""),
                "healthcare": tags.get("healthcare", ""),
                "operator": tags.get("operator", ""),
                "operator_type": tags.get("operator:type", ""),
                "phone": tags.get("phone", ""),
                "website": tags.get("website", ""),
                "addr_district": tags.get("addr:district", ""),
                "latitude": lat,
                "longitude": lon,
            })

    df = pd.DataFrame(facilities)

    def classify_type(row):
        if row["amenity"] == "hospital":
            return "Hospital"
        elif row["amenity"] == "clinic":
            return "Clinic"
        elif row["amenity"] == "doctors":
            return "Doctor"
        elif row["healthcare"]:
            return row["healthcare"].title()
        return "Other"

    def classify_operator(row):
        op = (row["operator"] + " " + row["operator_type"]).lower()
        if any(k in op for k in ["devlet", "public", "sağlık bakanlığı", "government"]):
            return "Public"
        elif any(k in op for k in ["özel", "private"]):
            return "Private"
        elif any(k in op for k in ["üniversite", "university"]):
            return "University"
        return "Unknown"

    df["facility_type"] = df.apply(classify_type, axis=1)
    df["sector"] = df.apply(classify_operator, axis=1)

    gdf = gpd.GeoDataFrame(
        df,
        geometry=gpd.points_from_xy(df.longitude, df.latitude),
        crs="EPSG:4326"
    )

    return gdf


def fetch_istanbul_districts():
    """
    Fetch Istanbul district (ilçe) boundaries from OSM using osmnx.
    Returns a GeoDataFrame with district polygons and a 'name' column.
    """
    import osmnx as ox

    print("Fetching Istanbul district boundaries from OSM...")
    tags = {"boundary": "administrative", "admin_level": "6"}
    gdf = ox.features_from_place("İstanbul, Turkey", tags=tags)

    # Keep only polygon/multipolygon features with a name
    gdf = gdf[gdf.geometry.geom_type.isin(["Polygon", "MultiPolygon"])].copy()
    gdf = gdf[gdf["name"].notna()].copy()

    result = gdf[["name", "geometry"]].reset_index(drop=True)
    result.crs  # ensure CRS is set (osmnx always returns EPSG:4326)
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
