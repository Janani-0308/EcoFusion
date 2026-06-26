import streamlit as st
import numpy as np
import requests
from sklearn.linear_model import LinearRegression
from datetime import datetime
from pytz import timezone
from timezonefinder import TimezoneFinder
from streamlit_autorefresh import st_autorefresh

# Auto-refresh every 5 minutes
st_autorefresh(interval=300000, limit=None, key="refresh")

st.title("StormShield AI+ Prototype")

# Friendly banner
st.warning("📍 Please allow location access when prompted so StormShield AI+ can fetch your local weather data and local time accurately.")

# --- STEP 1: Ask browser for location ---
st.markdown("""
<script>
navigator.geolocation.getCurrentPosition(
    (pos) => {
        const coords = {lat: pos.coords.latitude, lon: pos.coords.longitude};
        const query = new URLSearchParams(coords).toString();
        window.location.search = query;
    },
    (err) => {
        alert("⚠️ Location permission denied. Please allow location access to see accurate weather and time data.");
    }
);
</script>
""", unsafe_allow_html=True)

# --- STEP 2: Read coordinates from query params ---
coords = st.query_params

if "lat" in coords and "lon" in coords:
    lat = float(coords["lat"][0])
    lon = float(coords["lon"][0])
else:
    st.error("⚠️ Location not detected. Please allow location access in your browser.")
    st.stop()

# --- STEP 3: Fetch weather using lat/lon ---
api_key = "2479b1cbb4fb62c2a37c448aeb71c63d"  # replace with your OpenWeatherMap key
url = f"http://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={api_key}&units=metric"
data = requests.get(url).json()

if "main" in data and "wind" in data and "clouds" in data:
    temp = data["main"]["temp"]
    wind_speed = data["wind"]["speed"]
    cloud_cover = data["clouds"]["all"]
    city = data["name"]
else:
    st.error("⚠️ Weather data unavailable — check API key.")
    st.stop()

# --- STEP 4: Detect timezone from coordinates ---
tf = TimezoneFinder()
detected_timezone = tf.timezone_at(lat=lat, lng=lon)

if detected_timezone:
    local_time = datetime.now(timezone(detected_timezone)).strftime("%Y-%m-%d %H:%M:%S")
else:
    local_time = "Unknown"

# --- STEP 5: Display location + weather + local time ---
st.info(f"📍 Location detected: **{city}**\n🌐 Coordinates: {lat}, {lon}")
st.write(f"🌤️ Temperature: {temp} °C")
st.write(f"💨 Wind Speed: {wind_speed} m/s")
st.write(f"☁️ Cloud Cover: {cloud_cover}%")
st.markdown(f"**Local time in {city}:** 🕒 {local_time}")

# --- STEP 6: Energy simulation ---
hours = np.arange(0, 24)
solar = np.maximum(0, (100 - cloud_cover)/100 * np.sin((hours - 6)/24 * 2 * np.pi) * 100)
wind = np.full(24, wind_speed * 10)

battery_capacity = 500
battery = 0
demand = 120
battery_levels = []

for s, w in zip(solar, wind):
    generation = s + w
    net = generation - demand
    battery = min(battery_capacity, max(0, battery + net))
    battery_levels.append(battery)

# --- STEP 7: AI forecast ---
X = hours.reshape(-1, 1)
y = solar
model = LinearRegression()
model.fit(X, y)
future_hours = np.arange(24, 30).reshape(-1, 1)
predicted_solar = model.predict(future_hours)

# --- STEP 8: Village redistribution + advice ---
village_A = 0.9 * battery_capacity
village_B = 0.25 * battery_capacity

if village_B < 0.3 * battery_capacity:
    st.error("⚠️ Village B battery is low. Suggest: reduce non‑essential load, prioritize hospitals and water pumps, and request transfer from Village A.")
elif village_A < 0.3 * battery_capacity:
    st.error("⚠️ Village A battery is low. Suggest: enable solar priority mode and request backup from Village B.")
else:
    st.success("✅ Both villages have stable battery levels. Continue normal operation.")

if village_A > 0.7 * battery_capacity and village_B < 0.4 * battery_capacity:
    transfer = 0.2 * battery_capacity
    village_A -= transfer
    village_B += transfer

# --- STEP 9: Display results ---
st.line_chart({"Solar": solar, "Wind": wind, "Battery": battery_levels})
st.write("🔮 Predicted Solar (next 6 hours):", predicted_solar)
st.write("🏠 Village A Battery:", village_A)
st.write("🏠 Village B Battery:", village_B)

# --- STEP 10: Manual refresh button ---
if st.button("🔄 Refresh Weather Data"):
    st.rerun()
