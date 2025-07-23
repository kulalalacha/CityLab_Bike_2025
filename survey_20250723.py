import streamlit as st
from streamlit_folium import st_folium
import folium
from folium.plugins import Draw
import pandas as pd
import json
from datetime import datetime
import os

st.set_page_config(layout="wide")
st.title("🚲 Bicycle OD Route Survey")

# --- Map Drawing ---
m = folium.Map(location=[13.7563, 100.5018], zoom_start=12)
Draw(export=True).add_to(m)
st.subheader("🗺️ Draw your route below:")
st_map = st_folium(m, width=700, height=500, returned_objects=["last_active_drawing"])

# --- Form Input ---
with st.form("od_form"):
    st.subheader("🧑 Demographics")
    gender = st.radio("Gender", ["M", "F", "LGBTQ+"])
    age = st.number_input("Age", min_value=10, max_value=100)
    income = st.selectbox("Income Range", ["A: <10,000", "B: 10,001–30,000", "C: 30,001–50,000", "D: >50,000"])
    home_location = st.text_input("Home Location")

    st.subheader("🚲 Recent Trip")
    trip_type = st.selectbox("Trip Type", ["Work", "Recreation", "School", "Errand"])
    trip_month = st.selectbox("Month", ["Jan", "Feb", "Mar", "Apr", "May", "Jun", 
                                        "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"])
    trip_frequency = st.text_input("Trip Frequency (e.g., 3x/week)")

    submit = st.form_submit_button("✅ Generate and Download")

# --- Download Button (CSV + GeoJSON) ---
if submit:
    if st_map and st_map["last_active_drawing"]:
        # Generate Survey ID
        timestamp = datetime.now()
        survey_id = timestamp.strftime("%y%m%d_%H%M_SurveyNo_01")

        # Prepare CSV
        csv_data = {
            "survey_id": survey_id,
            "timestamp": timestamp.isoformat(),
            "gender": gender,
            "age": age,
            "income": income,
            "home_location": home_location,
            "trip_type": trip_type,
            "trip_month": trip_month,
            "trip_frequency": trip_frequency
        }
        csv_df = pd.DataFrame([csv_data])
        csv_bytes = csv_df.to_csv(index=False).encode("utf-8")

        # Prepare GeoJSON
        route_geometry = st_map["last_active_drawing"]["geometry"]
        geojson_obj = {
            "type": "FeatureCollection",
            "features": [{
                "type": "Feature",
                "geometry": route_geometry,
                "properties": {
                    "survey_id": survey_id,
                    "timestamp": timestamp.isoformat()
                }
            }]
        }
        geojson_bytes = json.dumps(geojson_obj, indent=2).encode("utf-8")

        # --- Combined Download Button ---
        st.success("✅ Files ready for download")

        col1, col2 = st.columns(2)
        with col1:
            st.download_button("📥 Download CSV", csv_bytes, file_name=f"{survey_id}.csv", mime="text/csv")
        with col2:
            st.download_button("🌍 Download GeoJSON", geojson_bytes, file_name=f"{survey_id}.geojson", mime="application/geo+json")

    else:
        st.error("⚠️ Please draw a route on the map before submitting.")
