import streamlit as st
import pandas as pd
import folium
from folium import PolyLine
import json
from geopy.distance import geodesic
from folium.plugins import LocateControl
from streamlit_folium import st_folium
from streamlit_js_eval import streamlit_js_eval

st.set_page_config(page_title="Nursery Finder", layout="wide")
st.title("🌱 Nursery Locator – Find Nearest Nursery with Route")

# Load nursery data
df = pd.read_excel("NURSARY.xlsx")
required_cols = ['Name', 'Latitude', 'Longitude', 'Capacity', 'PlantsAvailable', 'Contact']
if not all(col in df.columns for col in required_cols):
    st.error("❌ Excel must include: " + ", ".join(required_cols))
    st.stop()

# Load boundary if available
try:
    with open("khariar_boundary.geojson", "r") as f:
        khariar_boundary = json.load(f)
except:
    khariar_boundary = None

# Create map
center = [df['Latitude'].mean(), df['Longitude'].mean()]
m = folium.Map(location=center, zoom_start=10)
LocateControl(auto_start=True).add_to(m)

# Draw boundary
if khariar_boundary:
    folium.GeoJson(
        khariar_boundary,
        name="Khariar Division",
        style_function=lambda x: {
            "fillColor": "orange",
            "color": "black",
            "weight": 2,
            "fillOpacity": 0.1,
        },
    ).add_to(m)

# Add nursery markers
for _, row in df.iterrows():
    folium.Marker(
        location=[row['Latitude'], row['Longitude']],
        tooltip=row['Name'],
        popup=f"""
        <b>{row['Name']}</b><br>
        Capacity: {row['Capacity']}<br>
        Plants Available: {row['PlantsAvailable']}<br>
        Contact: {row['Contact']}
        """,
        icon=folium.Icon(color="green", icon="leaf")
    ).add_to(m)

# 🖱️ Button: Trigger geolocation
st.subheader("📍 Click to show your location and nearest nursery")
if st.button("Show Me Where I Am"):
    loc = streamlit_js_eval(
        js_expressions="navigator.geolocation.getCurrentPosition((pos) => pos.coords)",
        key="get_user_location_click"
    )

    if loc and "latitude" in loc and "longitude" in loc:
        user_location = (loc["latitude"], loc["longitude"])
        st.success(f"✅ Location found: {user_location}")

        # Add user marker
        folium.Marker(
            location=user_location,
            tooltip="Your Location",
            icon=folium.Icon(color="blue", icon="user")
        ).add_to(m)

        # Calculate distance
        df['Distance_km'] = df.apply(
            lambda row: geodesic(user_location, (row['Latitude'], row['Longitude'])).km,
            axis=1
        )

        # Find nearest nursery
        nearest = df.loc[df['Distance_km'].idxmin()]

        # Add nearest nursery marker (highlighted)
        folium.Marker(
            location=[nearest['Latitude'], nearest['Longitude']],
            popup=f"""
            <b>Nearest Nursery:</b><br>
            {nearest['Name']}<br>
            Distance: {nearest['Distance_km']:.2f} km<br>
            Capacity: {nearest['Capacity']}<br>
            Plants: {nearest['PlantsAvailable']}<br>
            Contact: {nearest['Contact']}
            """,
            icon=folium.Icon(color="red", icon="star")
        ).add_to(m)

        # Draw route (line)
        PolyLine(
            locations=[user_location, (nearest['Latitude'], nearest['Longitude'])],
            color='purple',
            weight=3,
            dash_array='5'
        ).add_to(m)

        # Zoom to route
        m.location = [(user_location[0] + nearest['Latitude']) / 2,
                      (user_location[1] + nearest['Longitude']) / 2]
        m.zoom_start = 13

        # Show details
        st.subheader("🌿 Nearest Nursery Details")
        st.markdown(f"""
        **Name:** {nearest['Name']}  
        **Distance:** {nearest['Distance_km']:.2f} km  
        **Capacity:** {nearest['Capacity']}  
        **Plants Available:** {nearest['PlantsAvailable']}  
        **Contact:** {nearest['Contact']}
        """)
    else:
        st.error("❌ Location permission denied or failed.")

# Show map
st.subheader("🗺️ Interactive Map")
st_folium(m, width=1000, height=600)
