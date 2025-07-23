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

# ========== FORM ==========
with st.form("survey_form"):
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

    submit = st.form_submit_button("✅ Generate and Download All")

# ========== MAP ==========
st.subheader("🗺️ Draw your route below:")

# Setup base map
start_coords = [13.730275905118468, 100.56987498465178]
m = folium.Map(
    location=start_coords,
    zoom_start=16,
    tiles="CartoDB positron",  # black-and-white basemap
    control_scale=True
)

# Add circle for radius
folium.Circle(
    radius=300,
    location=start_coords,
    color="#666",
    fill=False
).add_to(m)

# Add red draw tool
draw_options = {
    "polyline": {
        "shapeOptions": {
            "color": "red",
            "weight": 4,
            "opacity": 0.9
        }
    },
    "polygon": False,
    "rectangle": False,
    "circle": False,
    "marker": False,
    "circlemarker": False
}
Draw(export=True, draw_options=draw_options).add_to(m)
st_map = st_folium(m, width=700, height=500, returned_objects=["last_active_drawing"])

# ========== HANDLE SUBMIT ==========
if submit:
    if st_map and st_map["last_active_drawing"]:
        timestamp = datetime.now()
        survey_id = timestamp.strftime("%y%m%d_%H%M_SurveyNo_01")

        # CSV
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

        # GeoJSON
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

        # ZIP
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, "a", zipfile.ZIP_DEFLATED) as zf:
            zf.writestr(f"{survey_id}.csv", csv_bytes)
            zf.writestr(f"{survey_id}.geojson", geojson_bytes)
        zip_buffer.seek(0)

        # DOWNLOAD
        col1, col2 = st.columns([1, 6])
        with col2:
            st.success("✅ Your files are ready:")
            st.download_button(
                label="📦 Download All (CSV + GeoJSON)",
                data=zip_buffer,
                file_name=f"{survey_id}_files.zip",
                mime="application/zip"
            )
    else:
        st.error("⚠️ Please draw your route before submitting.")
