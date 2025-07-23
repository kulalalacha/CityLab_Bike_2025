import streamlit as st
import pandas as pd
import json
from datetime import datetime

st.title("Bicycle Route OD Survey")

# Form
with st.form("survey_form"):
    st.subheader("Trip Info")
    trip_purpose = st.selectbox("Trip purpose", ["Commute", "School", "Leisure", "Errand"])
    frequency = st.selectbox("Frequency", ["Daily", "Weekly", "Occasionally"])
    age = st.number_input("Your Age", min_value=10, max_value=100)
    gender = st.selectbox("Gender", ["Male", "Female", "Other"])
    route_geojson = st.text_area("Paste your drawn route GeoJSON here")  # Replace with actual drawing later

    submitted = st.form_submit_button("Submit")

if submitted:
    timestamp = datetime.now().isoformat()
    new_data = {
        "timestamp": timestamp,
        "trip_purpose": trip_purpose,
        "frequency": frequency,
        "age": age,
        "gender": gender,
        "route_geojson": route_geojson
    }

    # Save to CSV
    df = pd.DataFrame([new_data])
    csv_file = "od_survey_data.csv"
    
    # Append to file
    try:
        df.to_csv(csv_file, mode='a', header=not pd.io.common.file_exists(csv_file), index=False)
        st.success("Submission saved!")
    except Exception as e:
        st.error(f"Error saving to file: {e}")
