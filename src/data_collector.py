"""
Istanbul Healthcare Facility Data Collector
Collects hospital and clinic data from OpenStreetMap using Overpass API
"""

import requests
import pandas as pd
import geopandas as gpd
from shapely.geometry import Point
import json
import os
from datetime import datetime


def fetch_healthcare_from_osm():
    """Fetch healthcare facilities in Istanbul from OpenStreetMap"""
    
    overpass_url = "http://overpass-api.de/api/interpreter"
    
    # Istanbul bounding box (approximate)
    # South-West: 40.80, 28.50  North-East: 41.60, 29.95
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
    response = requests.get(overpass_url, params={"data": query})
    
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
                "operator_type": tags.get("operator:type", ""),  # public/private
                "phone": tags.get("phone", ""),
                "website": tags.get("website", ""),
                "addr_district": tags.get("addr:district", ""),
                "latitude": lat,
                "longitude": lon,
            })
    
    df = pd.DataFrame(facilities)
    
    # Facility type sınıflandırması
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
    
    df["facility_type"] = df.apply(classify_type, axis=1)
    
    # Operator type sınıflandırması
    def classify_operator(row):
        op = (row["operator"] + " " + row["operator_type"]).lower()
        if any(k in op for k in ["devlet", "public", "sağlık bakanlığı", "government"]):
            return "Public"
        elif any(k in op for k in ["özel", "private"]):
            return "Private"
        elif any(k in op for k in ["üniversite", "university"]):
            return "University"
        return "Unknown"
    
    df["sector"] = df.apply(classify_operator, axis=1)
    
    # GeoDataFrame'e dönüştür
    gdf = gpd.GeoDataFrame(
        df,
        geometry=gpd.points_from_xy(df.longitude, df.latitude),
        crs="EPSG:4326"
    )
    
    return gdf


def fetch_istanbul_districts():
    """Fetch Istanbul district boundaries from OpenStreetMap"""
    
    overpass_url = "http://overpass-api.de/api/interpreter"
    
    query = """
    [out:json][timeout:120];
    area["name"="İstanbul"]["admin_level"="4"]->.istanbul;
    rel["admin_level"="6"](area.istanbul);
    out geom;
    """
    
    print("Fetching Istanbul district boundaries...")
    response = requests.get(overpass_url, params={"data": query})
    
    if response.status_code != 200:
        raise Exception(f"Overpass API error: {response.status_code}")
    
    data = response.json()
    print(f"Found {len(data['elements'])} districts")
    
    # Not: Bu basit bir yaklaşım. Daha iyi sonuç için
    # data.ibb.gov.tr'den GeoJSON indirebilirsin.
    return data


def save_data(gdf, output_dir="../data"):
    """Save collected data in multiple formats"""
    
    os.makedirs(output_dir, exist_ok=True)
    
    # GeoJSON
    geojson_path = os.path.join(output_dir, "istanbul_healthcare_facilities.geojson")
    gdf.to_file(geojson_path, driver="GeoJSON")
    print(f"Saved GeoJSON: {geojson_path}")
    
    # CSV
    csv_path = os.path.join(output_dir, "istanbul_healthcare_facilities.csv")
    gdf.drop(columns="geometry").to_csv(csv_path, index=False, encoding="utf-8-sig")
    print(f"Saved CSV: {csv_path}")
    
    # Summary
    print(f"\n=== Data Summary ===")
    print(f"Total facilities: {len(gdf)}")
    print(f"\nBy type:")
    print(gdf["facility_type"].value_counts().to_string())
    print(f"\nBy sector:")
    print(gdf["sector"].value_counts().to_string())
    
    # Metadata
    metadata = {
        "source": "OpenStreetMap via Overpass API",
        "collection_date": datetime.now().isoformat(),
        "total_facilities": len(gdf),
        "crs": "EPSG:4326",
        "types": gdf["facility_type"].value_counts().to_dict(),
    }
    meta_path = os.path.join(output_dir, "data_metadata.json")
    with open(meta_path, "w") as f:
        json.dump(metadata, f, indent=2, ensure_ascii=False)
    print(f"Saved metadata: {meta_path}")


if __name__ == "__main__":
    gdf = fetch_healthcare_from_osm()
    save_data(gdf)
