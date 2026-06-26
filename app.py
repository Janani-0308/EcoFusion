import streamlit as st
import numpy as np
import requests
from streamlit_geolocation import streamlit_geolocation
from timezonefinder import TimezoneFinder
from datetime import datetime
from pytz import timezone
from sklearn.linear_model import LinearRegression

# --- Page Configuration ---
st.set_page_config(page_title="StormShield AI+", layout="wide")
st.title("StormShield AI+ Prototype")

# --- Step 1: Location Access via Component ---
# This safely handles the browser permission request
location = streamlit_geolocation()

if location and location.get("latitude"):
    lat = location["latitude"]
    lon = location["longitude"]
    
    # --- Step 2: Fetch Weather Data ---
    # API key (Consider moving to st.secrets for production)
    api_key = "2479b1cbb4fb62c2a37c448aeb71c63d" 
    url = f"http://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={api_key}&units=metric"
    
    try:
        response = requests.get(url)
        data = response.json()
        
        if "main" in data:
            temp = data["main"]["temp"]
            wind_speed = data["wind"]["speed"]
            cloud_cover = data["clouds"]["all"]
            city = data["name"]

            # Timezone Detection
            tf = TimezoneFinder()
            tz_name = tf.timezone_at(lat=lat, lng=lon)
            local_time = datetime.now(timezone(tz_name)).strftime("%Y-%m-%d %H:%M:%S") if tz_name else "Unknown"

            # --- Step 3: Simulation Logic ---
            hours = np.arange(0, 24)
            # Basic renewable output model
            solar = np.maximum(0, (100 - cloud_cover)/100 * np.sin((hours - 6)/24 * 2 * np.pi) * 100)
            wind = np.full(24, wind_speed * 10)

            battery_capacity = 500
            demand = 120
            battery = 0
            battery_levels = []

            for s, w in zip(solar, wind):
                generation = s + w
                net = generation - demand
                battery = min(battery_capacity, max(0, battery + net))
                battery_levels.append(battery)

            # AI Trend Forecast
            X = hours.reshape(-1, 1)
            model = LinearRegression().fit(X, solar)
            
            # --- Step 4: Display UI ---
            st.info(f"📍 Location: **{city}** | 🕒 Local Time: {local_time}")
            
            col1, col2, col3 = st.columns(3)
            col1.metric("Temperature", f"{temp}°C")
            col2.metric("Wind Speed", f"{wind_speed} m/s")
            col3.metric("Cloud Cover", f"{cloud_cover}%")

            st.line_chart({"Solar": solar, "Wind": wind, "Battery Level": battery_levels})

            # --- Step 5: Redistribution Advice ---
            # Using your defined logic thresholds
            if battery_levels[-1] < 0.3 * battery_capacity:
                st.error("⚠️ Low power detected. Suggest: Prioritize critical infrastructure and enable load-sharing.")
            else:
                st.success("✅ System Status: Stable.")
        else:
            st.error("Unable to retrieve weather data. Please check your API key.")
            
    except Exception as e:
        st.error(f"An error occurred while fetching data: {e}")

else:
    st.warning("📍 Please click the 'Start Geolocation' button to allow location access.")
