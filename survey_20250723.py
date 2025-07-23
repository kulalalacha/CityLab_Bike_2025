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

# ----- Create Map -----
m = folium.Map(location=[13.7563, 100.5018], zoom_start=12)
Draw(export=True, filename='drawn_route.geojson').add_to(m)
st.subheader("🗺️ Draw your recent trip on the map below:")
st_map = st_folium(m, width=700, height=500, returned_objects=["last_active_drawing"])

# ----- Survey Form -----
with st.form("survey_form"):
    st.subheader("🧑 Demographic Info")
    gender = st.radio("Gender", ["M", "F", "LGBTQ+"])
    age = st.number_input("Age", min_value=10, max_value=100)
    income = st.selectbox("Income Range", ["A: <10,000", "B: 10,001–30,000", "C: 30,001–50,000", "D: >50,000"])
    home_location = st.text_input("Home Location")

    st.subheader("🛣️ Recent Bicycle Trip")
    trip_type = st.selectbox("Trip Type", ["Work", "Recreation", "School", "Errand"])
    trip_month = st.selectbox("Trip Month", ["Jan", "Feb", "Mar", "Apr", "May", "Jun", 
                                             "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"])
    trip_frequency = st.text_input("Trip Frequency (e.g., 3x/week)")

    submit = st.form_submit_button("Submit")

# ----- Generate Unique Survey ID -----
def generate_survey_id(survey_no):
    now = datetime.now()
    return f"{now.strftime('%y%m%d_%H%M')}_SurveyNo_{survey_no:02d}"

# ----- Save to CSV & JSON -----
if submit:
    if st_map and st_map["last_active_drawing"]:
        route_geojson = st_map["last_active_drawing"]["geometry"]
        timestamp = datetime.now()
        survey_no = 1  # you can make this auto-increment if needed
        survey_id = generate_survey_id(survey_no)

        data = {
            "survey_id": survey_id,
            "timestamp": timestamp.isoformat(),
            "gender": gender,
            "age": age,
            "income": income,
            "home_location": home_location,
            "trip_type": trip_type,
            "trip_month": trip_month,
            "trip_frequency": trip_frequency,
            "route_geojson": route_geojson
        }

        # Save CSV
        csv_path = f"{survey_id}.csv"
        df = pd.DataFrame([data])
        df.to_csv(csv_path, index=False)

        # Save JSON
        json_path = f"{survey_id}.json"
        with open(json_path, "w") as jf:
            json.dump(data, jf, indent=2)

        st.success(f"✅ Saved as {survey_id}.csv and .json")

        # Download buttons
        st.download_button("📥 Download CSV", df.to_csv(index=False), file_name=csv_path, mime="text/csv")
        st.download_button("📥 Download JSON", json.dumps(data, indent=2), file_name=json_path, mime="application/json")
    else:
        st.error("⚠️ Please draw a route on the map before submitting.")
