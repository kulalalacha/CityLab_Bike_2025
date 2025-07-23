import streamlit as st
from streamlit_folium import st_folium
import folium
from folium.plugins import Draw
import pandas as pd
import json
from datetime import datetime
import zipfile
import io

st.set_page_config(layout="centered")
st.title("🚲 Bicycle OD Route Survey")

# ---------- Step 1: Form ----------
st.subheader(" Demographics")
gender = st.radio("Gender", ["M", "F", "LGBTQ+"])
age = st.number_input("Age", min_value=10, max_value=100)
income = st.selectbox("Income Range", ["A: <10,000", "B: 10,001–30,000", "C: 30,001–50,000", "D: >50,000"])
home_location = st.text_input("Home Location")

st.subheader("🚲 Recent Trip")
trip_type = st.selectbox("Trip Type", ["Work", "Recreation", "School", "Errand"])
trip_month = st.selectbox("Month", ["Jan", "Feb", "Mar", "Apr", "May", "Jun", 
                                    "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"])
trip_frequency = st.text_input("Trip Frequency (e.g., 3x/week)")

# ---------- Step 2: Map ----------
st.subheader("🗺️ Draw your route below:")
m = folium.Map(location=[13.7563, 100.5018], zoom_start=12)
Draw(export=True).add_to(m)
st_map = st_folium(m, width=700, height=500, returned_objects=["last_active_drawing"])

# ---------- Final Step: Button BELOW MAP ----------
generate = st.button("✅ Generate and Download All")

if generate:
    if st_map and st_map["last_active_drawing"]:
        # Create Survey ID
        timestamp = datetime.now()
        survey_id = timestamp.strftime("%y%m%d_%H%M_SurveyNo_01")

        # Prepare CSV content
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

        # Prepare GeoJSON content
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

        # Package into ZIP
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, "a", zipfile.ZIP_DEFLATED) as zf:
            zf.writestr(f"{survey_id}.csv", csv_bytes)
            zf.writestr(f"{survey_id}.geojson", geojson_bytes)
        zip_buffer.seek(0)

        st.success("✅ ZIP file is ready.")
        st.download_button(
            label="📦 Download All (CSV + GeoJSON)",
            data=zip_buffer,
            file_name=f"{survey_id}_files.zip",
            mime="application/zip"
        )
    else:
        st.error("⚠️ Please draw your route on the map before clicking Generate.")
