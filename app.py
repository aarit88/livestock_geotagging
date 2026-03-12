"""
Main Streamlit app — UI layout only.
Imports backend logic from backend.py and styles from styles.py.
"""

import streamlit as st  # pyre-ignore[21]
import pandas as pd  # pyre-ignore[21]
import folium  # pyre-ignore[21]
from streamlit_folium import st_folium  # pyre-ignore[21]

from backend import download_video, scan_video, predict_location  # pyre-ignore[21]
from styles import get_css  # pyre-ignore[21]

# ----------------------------------
# Page config
# ----------------------------------

st.set_page_config(
    page_title="AI Livestock Geolocation",
    page_icon="🐄",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ----------------------------------
# Inject custom CSS
# ----------------------------------

st.markdown(get_css(), unsafe_allow_html=True)

# ==================================
# SIDEBAR
# ==================================

with st.sidebar:
    st.markdown("## 🐄 Livestock GeoAI")
    st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)

    st.markdown("""
    **How it works:**
    1. Select a livestock fair from the list
    2. Preview the video feed
    3. Click **Scan** to run AI detection
    4. View geotagged location on the map
    """)

    st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)

    st.markdown("""
    **Powered by:**
    - 🧠 YOLOv8 Object Detection
    - 🗺️ OpenStreetMap Overpass API
    - 📍 Folium Dark Maps
    """)

    st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)
    st.caption("Built with Streamlit • AI Livestock Geolocation System")

# ==================================
# MAIN CONTENT
# ==================================

# ── Hero Header ──
st.markdown("""
<div class="hero-header">
    <h1>🛰️ AI Livestock Fair Geolocation</h1>
    <p>Detect objects in livestock fair videos and predict geographic location using AI</p>
</div>
""", unsafe_allow_html=True)

st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)

# ── Load data ──
df = pd.read_csv("cattle_fairs.csv", quotechar='"', skipinitialspace=True)

# ── Fair selector ──
st.markdown('<div class="glass-card"><h3>📋 Select a Livestock Fair</h3>', unsafe_allow_html=True)
fair = st.selectbox("Choose a fair to analyze", df["Name or Place"], label_visibility="collapsed")
st.markdown('</div>', unsafe_allow_html=True)

row = df[df["Name or Place"] == fair].iloc[0]
video = row["Video link 1"]

# ── Video preview ──
if pd.notna(video) and video:
    st.markdown('<div class="glass-card"><h3>🎬 Video Preview</h3>', unsafe_allow_html=True)
    st.video(video)
    st.markdown('</div>', unsafe_allow_html=True)

st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)

# ── Scan button ──
if st.button("🔍  Scan Video & Locate Fair"):
    if pd.notna(video) and video:
        with st.spinner("🧠 Analyzing video with YOLOv8..."):
            download_video(video)
            objects = scan_video()
            lat, lon = predict_location(objects)

        month = row["Month"] if pd.notna(row["Month"]) else "N/A"
        
        # Handle case where no location is found
        if lat is None or lon is None:
            st.error("📍 Unable to determine location from detected objects. The video may not contain enough location-specific features.")
            st.stop()
            
        st.session_state["results"] = {
            "objects": objects,
            "lat": lat,
            "lon": lon,
            "fair": fair,
            "month": month,
        }
    else:
        st.warning("⚠️ No video link available for this fair.")

# ==================================
# RESULTS
# ==================================

if "results" in st.session_state:
    res = st.session_state["results"]

    st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)

    # ── Detected objects ──
    st.markdown('<div class="glass-card"><h3>🔎 Detected Objects</h3>', unsafe_allow_html=True)
    pills_html = '<div class="pill-container">'
    for obj in res["objects"]:
        pills_html += f'<span class="pill">{obj}</span>'
    pills_html += '</div>'
    st.markdown(pills_html, unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

    # ── Coordinates + Map ──
    col_left, col_right = st.columns([1, 2])

    with col_left:
        st.markdown(f"""
        <div class="glass-card">
            <h3>📍 Predicted Location</h3>
            <div class="metric-row" style="flex-direction: column;">
                <div class="metric-card">
                    <div class="label">Latitude</div>
                    <div class="value">{res['lat']:.6f}</div>
                </div>
                <div class="metric-card">
                    <div class="label">Longitude</div>
                    <div class="value">{res['lon']:.6f}</div>
                </div>
                <div class="metric-card">
                    <div class="label">📅 Fair Month</div>
                    <div class="value" style="font-size:1.3rem;">{res['month']}</div>
                </div>
            </div>
            <p style="color:#8b9dc3; font-size:0.85rem; margin-top:0.8rem;">
                📌 Fair: <strong style="color:#e6edf3;">{res['fair']}</strong>
            </p>
        </div>
        """, unsafe_allow_html=True)

    with col_right:
        st.markdown('<div class="glass-card"><h3>🗺️ Geolocation Map</h3>', unsafe_allow_html=True)

        # Dark themed folium map
        m = folium.Map(
            location=[res["lat"], res["lon"]],
            zoom_start=8,
            tiles="CartoDB dark_matter",
        )

        folium.Marker(
            [res["lat"], res["lon"]],
            popup=folium.Popup(
                f"<b>{res['fair']}</b><br>Lat: {res['lat']:.4f}<br>Lon: {res['lon']:.4f}",
                max_width=250,
            ),
            icon=folium.Icon(color="blue", icon="map-marker", prefix="fa"),
        ).add_to(m)

        # Accuracy circle
        folium.Circle(
            location=[res["lat"], res["lon"]],
            radius=20000,
            color="#00d4ff",
            fill=True,
            fill_color="#00d4ff",
            fill_opacity=0.1,
            weight=1,
        ).add_to(m)

        st.markdown('<div class="map-container">', unsafe_allow_html=True)
        st_folium(m, height=420, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

        st.markdown('</div>', unsafe_allow_html=True)

        # ── Satellite/Street View Links ──
        st.markdown('<div class="glass-card"><h3>🛰️ Satellite & Street View</h3>', unsafe_allow_html=True)
        
        # Create satellite and street view links
        satellite_link = f"https://www.google.com/maps/@{res['lat']:.6f},{res['lon']:.6f},847m/data=!3m1!1e3!4m6!1m2!2s{res['lat']:.6f}!3d{res['lon']:.6f}!2m1!1e0"
        street_view_link = f"https://www.google.com/maps/@{res['lat']:.6f},{res['lon']:.6f},18z/data=!3m1!1e3"
        
        col1, col2 = st.columns(2)
        with col1:
            st.markdown(f"""
            <div style="text-align: center; padding: 10px;">
                <a href="{satellite_link}" target="_blank" style="
                    display: inline-block;
                    padding: 12px 24px;
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    color: white;
                    text-decoration: none;
                    border-radius: 8px;
                    font-weight: bold;
                    transition: all 0.3s ease;
                ">
                    🛰️ Open Satellite View
                </a>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.markdown(f"""
            <div style="text-align: center; padding: 10px;">
                <a href="{street_view_link}" target="_blank" style="
                    display: inline-block;
                    padding: 12px 24px;
                    background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
                    color: white;
                    text-decoration: none;
                    border-radius: 8px;
                    font-weight: bold;
                    transition: all 0.3s ease;
                ">
                    🚶 Open Street View
                </a>
            </div>
            """, unsafe_allow_html=True)

        st.markdown('</div>', unsafe_allow_html=True)