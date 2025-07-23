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

# --- Create map ---
m = folium.Map(location=[13.7563, 100.5018], zoom_start=12)  # Centered on Bangkok
Draw(export=True, filename='drawn_route.geojson').add_to(m)

# --- Show map and capture drawing ---
st.subheader("🗺️ Draw your cycling route on the map below:")
st_map = st_folium(m, width=700, height=500, returned_objects=["last_active_drawing"])

# --- Survey Form ---
with st.form("survey_form"):
    st.subheader("📋 Trip Information")
    trip_purpose = st.selectbox("What is the purpose of your trip?", ["Commute", "School", "Leisure", "Errand"])
    frequency = st.selectbox("How often do you cycle this route?", ["Daily", "Weekly", "Occasionally"])
    age = st.number_input("Your Age", min_value=10, max_value=100)
    gender = st.selectbox("Gender", ["Male", "Female", "Other", "Prefer not to say"])
    submit = st.form_submit_button("Submit")

# --- Save to CSV ---
if submit:
    if st_map and st_map["last_active_drawing"]:
        timestamp = datetime.now().isoformat()
        geojson_data = st_map["last_active_drawing"]["geometry"]
        route_json = json.dumps(geojson_data)

        row = {
            "timestamp": timestamp,
            "trip_purpose": trip_purpose,
            "frequency": frequency,
            "age": age,
            "gender": gender,
            "route_geojson": route_json
        }

        df = pd.DataFrame([row])
        csv_file = "od_survey_data.csv"
        file_exists = os.path.isfile(csv_file)

        df.to_csv(csv_file, mode='a', header=not file_exists, index=False)
        st.success("✅ Submission saved successfully!")
        st.download_button("📥 Download CSV", df.to_csv(index=False), file_name="your_response.csv", mime="text/csv")
    else:
        st.error("⚠️ Please draw a route on the map before submitting.")
