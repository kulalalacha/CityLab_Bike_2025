import streamlit as st
from streamlit_folium import st_folium
import folium
from folium.plugins import Draw
import pandas as pd
import json
from datetime import datetime
import zipfile
import io
import shutil
import os
from pydrive2.auth import GoogleAuth
from pydrive2.drive import GoogleDrive


st.set_page_config(layout="centered")
st.title("🚲 Bicycle OD Route Survey")

# ---------- Google Drive Setup ----------
# Step 1: Copy token.json from symlink to real file
secrets_token_path = "/etc/secrets/token.json"
token_copy_path = "token.json"
if os.path.islink(secrets_token_path) or True:  # Always copy for safety
    shutil.copy(secrets_token_path, token_copy_path)

# Step 2: Same for client_secrets.json
secrets_client_path = "/etc/secrets/client_secrets.json"
client_copy_path = "client_secrets.json"
if os.path.islink(secrets_client_path) or True:
    shutil.copy(secrets_client_path, client_copy_path)

# Step 3: Auth
gauth = GoogleAuth()
gauth.LoadClientConfigFile(client_copy_path)
gauth.LoadCredentialsFile(token_copy_path)
drive = GoogleDrive(gauth)



# ---------- FORM ----------
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

# ---------- MAP ----------
st.subheader("🗌️ Draw your route below:")

lat, lon = 13.730275905118468, 100.56987498465178
offset_deg = 0.01
sw = [lat - offset_deg, lon - offset_deg]
ne = [lat + offset_deg, lon + offset_deg]

m = folium.Map(tiles="CartoDB positron", control_scale=True)
m.fit_bounds([sw, ne])

Draw(export=True, draw_options={
    "polyline": {"shapeOptions": {"color": "red", "weight": 4, "opacity": 0.9}},
    "polygon": False,
    "rectangle": False,
    "circle": False,
    "marker": False,
    "circlemarker": False
}).add_to(m)

st_map = st_folium(m, width=700, height=500, returned_objects=["last_active_drawing"])

# ---------- SUBMIT HANDLER ----------
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

        # 📦 Download
        st.success("✅ Your files are ready:")
        st.download_button(
            label="📦 Download All (CSV + GeoJSON)",
            data=zip_buffer,
            file_name=f"{survey_id}_files.zip",
            mime="application/zip"
        )

        # 🚀 Upload to Google Drive folder
        folder_name = "2025_citilab_bike/Survey"

        # Create ZIP file on disk (Render has ephemeral storage)
        with open(f"/tmp/{survey_id}.zip", "wb") as f:
            f.write(zip_buffer.getvalue())

        gfile = drive.CreateFile({
            'title': f"{survey_id}.zip",
            'parents': [{"kind": "drive#fileLink", "path": folder_name}]
        })
        gfile.SetContentFile(f"/tmp/{survey_id}.zip")
        gfile.Upload()
        st.success(f"✉ Uploaded to Google Drive: {folder_name}/{survey_id}.zip")

    else:
        st.error("⚠️ Please draw your route before submitting.")
