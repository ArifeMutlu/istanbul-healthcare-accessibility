import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

import streamlit as st
import streamlit.components.v1 as components

from find_nearest import find_nearest
from load_data import load_osm_districts, load_osm_facilities
from spatial_analysis import calculate_accessibility_score
from visualize import create_accessibility_interactive_map

st.set_page_config(page_title="Istanbul Healthcare Accessibility", layout="wide")
st.title("Istanbul Healthcare Accessibility Dashboard")


@st.cache_data
def load():
    facilities = load_osm_facilities()
    districts = load_osm_districts()
    scored = calculate_accessibility_score(districts, facilities)
    return facilities, scored


facilities, scored_districts = load()

district_name = st.sidebar.selectbox(
    "Select District", sorted(scored_districts["name"].dropna().tolist())
)

row = scored_districts[scored_districts["name"] == district_name].iloc[0]

col1, col2, col3 = st.columns(3)
col1.metric("Accessibility Score", f"{row['accessibility_score']:.1f} / 100")
col2.metric("Facilities in District", int(row["facility_count"]))
col3.metric("Nearest Facility", f"{row['nearest_hospital_km']:.2f} km")

centroid = row.geometry.centroid
nearest = find_nearest((centroid.x, centroid.y), facilities, k=5)
nearest = nearest.copy()
nearest["distance_km"] = (nearest["distance_m"] / 1000).round(2)
nearest = nearest.drop(columns=["distance_m"])

st.subheader("5 Nearest Facilities")
st.dataframe(nearest, use_container_width=True)

m = create_accessibility_interactive_map(
    scored_districts, score_column="accessibility_score"
)
st.subheader("District Accessibility Map")
components.html(m._repr_html_(), height=500)
