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
    1. Select a livestock fair from list
    2. Choose a video if multiple are available
    3. Preview the video feed
    4. Click **Scan** to run AI detection
    5. View geotagged location on map
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
try:
    df = pd.read_csv("cattle_fairs.csv", quotechar='"', skipinitialspace=True)
    # Clean the data - ensure fair names are strings and not URLs
    df['Name or Place'] = df['Name or Place'].astype(str)
    # Remove any rows where Name or Place looks like a URL
    df = df[~df['Name or Place'].str.contains('http', na=False)]
except Exception as e:
    st.error(f"Error loading data: {e}")
    st.stop()

# ── Fair selector ──
st.markdown('<div class="glass-card"><h3>📋 Select a Livestock Fair</h3></div>', unsafe_allow_html=True)

# Get clean fair names list
fair_names = df["Name or Place"].dropna().unique().tolist()
# Sort alphabetically for better UX
fair_names = sorted(fair_names)

fair = st.selectbox("Choose a fair to analyze", fair_names, label_visibility="collapsed")

# Get selected fair data
try:
    row = df[df["Name or Place"] == fair].iloc[0]
    video1 = str(row["Video link 1"]).strip() if pd.notna(row["Video link 1"]) else ""
    video2 = str(row["Video link 2"]).strip() if pd.notna(row["Video link 2"]) else ""
except Exception as e:
    st.error(f"Error finding fair data: {e}")
    st.stop()

# ── Video selector ──
available_videos = []
if video1 and (video1.startswith('http') or video1.startswith('https')):
    available_videos.append(("Video 1", video1))
if video2 and (video2.startswith('http') or video2.startswith('https')):
    available_videos.append(("Video 2", video2))

if available_videos:
    st.markdown('<div class="glass-card"><h3>🎬 Select Video</h3></div>', unsafe_allow_html=True)
    video_label = st.selectbox("Choose video to analyze", [v[0] for v in available_videos], label_visibility="collapsed")
    video = next(v[1] for v in available_videos if v[0] == video_label)
else:
    video = None

# ── Video preview ──
if video:
    st.markdown('<div class="glass-card"><h3>🎬 Video Preview</h3></div>', unsafe_allow_html=True)
    st.video(video)

st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)

# ── Scan button ──
if st.button("🔍  Scan Video & Locate Fair"):
    if video:
        base_lat = float(row["Lat"]) if pd.notna(row["Lat"]) else None
        base_lon = float(row["Long"]) if pd.notna(row["Long"]) else None

        with st.spinner("🧠 Analyzing video with YOLOv8..."):
            video_info = download_video(video)
            objects = scan_video()
            lat, lon, landmarks = predict_location(objects, base_lat, base_lon, fair_name=fair)

        month = row["Month"] if pd.notna(row["Month"]) else "N/A"
        if isinstance(video_info, dict) and video_info.get("upload_date"):
            try:
                import datetime
                date_obj = datetime.datetime.strptime(video_info["upload_date"], "%Y%m%d")
                month = date_obj.strftime("%b")
            except Exception:
                pass
        
        # Handle case where no location is found
        if lat is None or lon is None:
            st.error("📍 Unable to determine location from detected objects. The video may not contain enough location-specific features.")
            st.stop()
            
        st.session_state["results"] = {
            "objects": objects,
            "lat": lat,
            "lon": lon,
            "landmarks": landmarks,
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
    pills_html = '<div class="glass-card"><h3>🔎 Detected Objects</h3>'
    pills_html += '<div class="pill-container">'
    for obj in res["objects"]:
        pills_html += f'<span class="pill">{obj}</span>'
    pills_html += '</div></div>'
    st.markdown(pills_html, unsafe_allow_html=True)

    # ── Coordinates + Map ──
    col_left, col_right = st.columns([1, 2])

    with col_left:
        # Format landmarks HTML
        landmarks_html = ""
        if res.get('landmarks'):
            landmarks_html = "<ul style='margin-top: 5px; color:#e6edf3; font-size:0.9rem; padding-left: 20px;'>"
            for lm in res['landmarks']:
                landmarks_html += f"<li>{lm['name']} ({lm['type']})</li>"
            landmarks_html += "</ul>"
        else:
            landmarks_html = "<span style='color:#e6edf3; font-size:0.9rem; display: block; margin-top: 5px;'>No nearby landmarks found.</span>"

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
            <div style="margin-top: 1.2rem; background: rgba(0,0,0,0.2); padding: 10px; border-radius: 8px; border: 1px solid rgba(255,255,255,0.05);">
                <h4 style="color:#8b9dc3; font-size: 0.95rem; margin-bottom:0;">📌 Proof of Location (Landmarks):</h4>
                {landmarks_html}
            </div>
        </div>
        """, unsafe_allow_html=True)

    with col_right:
        st.markdown('<div class="glass-card"><h3>🗺️ Geolocation Map</h3></div>', unsafe_allow_html=True)

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
            radius=25000,
            color="#00d4ff",
            fill=True,
            fill_color="#00d4ff",
            fill_opacity=0.1,
            weight=1,
        ).add_to(m)

        # Add landmarks to the map
        for lm in res.get('landmarks', []):
            folium.Marker(
                [lm['lat'], lm['lon']],
                popup=folium.Popup(
                    f"<b>{lm['name']}</b><br>Type: {lm['type']}",
                    max_width=250,
                ),
                icon=folium.Icon(color="green", icon="info-sign"),
                tooltip=lm['name']
            ).add_to(m)

        st_folium(m, height=420, use_container_width=True)

        # ── Satellite/Street View Links ──
        satellite_link = f"https://www.google.com/maps/search/?api=1&query={res['lat']},{res['lon']}&basemap=satellite"
        street_view_link = f"https://www.google.com/maps/@?api=1&map_action=pano&viewpoint={res['lat']},{res['lon']}"
        
        st.markdown(f"""
        <div class="glass-card">
            <h3>🛰️ Satellite & Street View</h3>
            <div style="display: flex; gap: 10px; justify-content: center; flex-wrap: wrap;">
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
            </div>
        </div>
        """, unsafe_allow_html=True)
