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
    
    proof_col = "Proof of location: Landmarks (Youtube video, Landmark, Timestamp, GPS or Google Street link)"
    original_proof = str(row[proof_col]).strip() if proof_col in df.columns and pd.notna(row.get(proof_col)) else "No documented proof"
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
            "field_lat": base_lat,
            "field_lon": base_lon,
            "original_proof": original_proof,
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
        # Calculate semantic proof of location for the UI
        objects_ui = res.get('objects', [])
        landmarks_ui = res.get('landmarks', [])
        
        livestock_map_ui = {"cow": "cattle", "sheep": "sheep", "horse": "horses", "elephant": "elephants", "bird": "poultry"}
        livestock_present_ui = list(set([livestock_map_ui[obj] for obj in objects_ui if obj in livestock_map_ui]))
        other_objects_ui = list(set([obj for obj in objects_ui if obj not in livestock_map_ui]))
        
        area_ui = "Open field"
        if landmarks_ui:
            lm_type = landmarks_ui[0].get("type", "").lower().replace("_", " ")
            if "farm" in lm_type: area_ui = "Farm area"
            elif "market" in lm_type: area_ui = "Marketplace"
            elif "build" in lm_type or "resident" in lm_type: area_ui = "Populated area"
            elif "place of worship" in lm_type: area_ui = "Temple/Worship area"
            elif "parking" in lm_type: area_ui = "Parking area"
                
        if livestock_present_ui:
            l_str = " and ".join(livestock_present_ui[:2])
            if "person" in other_objects_ui:
                desc_ui = f"{area_ui} with {l_str} and people gathering"
            else:
                desc_ui = f"{area_ui} with {l_str} gathering"
        elif other_objects_ui:
            if "person" in other_objects_ui:
                desc_ui = f"{area_ui} with people present"
            else:
                o_str = ", ".join(other_objects_ui[:2])
                desc_ui = f"{area_ui} with {o_str} present"
        else:
            desc_ui = f"{area_ui} representing the location"
            
        sat_link = f"https://www.google.com/maps/@{res['lat']:.6f},{res['lon']:.6f},893m/data=!3m1!1e3!4m6!1m2!2s{res['lat']:.6f}!3d{res['lon']:.6f}!2m1!1e0"
        semantic_proof_str = f"(Y1, {desc_ui}, 0:30 ,{sat_link})"
        
        proof_html = f"<div style='margin-top: 8px; padding: 12px; background: rgba(0,0,0,0.4); border-radius: 6px; border-left: 4px solid #4CAF50; font-family: monospace; font-size: 0.9rem; color: #aef359; word-wrap: break-word;'>{semantic_proof_str}</div>"

        field_location_html = ""
        if res.get('field_lat') is not None and res.get('field_lon') is not None:
            field_location_html = "".join(line.strip() for line in f"""
            <div style="margin-top: 1.2rem; background: rgba(0,0,0,0.2); padding: 10px; border-radius: 8px; border: 1px solid rgba(255,255,255,0.05);">
                <h4 style="color:#8b9dc3; font-size: 0.95rem; margin-bottom:0;">📌 Livestock Field Location:</h4>
                <div style="color:#e6edf3; font-size: 0.9rem; margin-top: 5px;">
                    <b>Lat:</b> {res['field_lat']:.6f} &nbsp;&nbsp;|&nbsp;&nbsp; <b>Lon:</b> {res['field_lon']:.6f}
                </div>
            </div>
            """.split("\n"))

        main_html = "".join(line.strip() for line in f"""
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
                📌 Fair: <strong style="color:#e6edf3;">{res['fair']}</strong><br/>
                📌 Original Provided Proof: <strong style="color:#e6edf3;">{res.get('original_proof', 'None')}</strong>
            </p>
            {field_location_html}
            <div style="margin-top: 1.2rem; background: rgba(0,0,0,0.2); padding: 10px; border-radius: 8px; border: 1px solid rgba(255,255,255,0.05);">
                <h4 style="color:#8b9dc3; font-size: 0.95rem; margin-bottom:0;">📌 Proof of Location:</h4>
                {proof_html}
            </div>
        </div>
        """.split("\n"))
        st.markdown(main_html, unsafe_allow_html=True)

    with col_right:
        st.markdown('<div class="glass-card"><h3>🗺️ Geolocation Map</h3></div>', unsafe_allow_html=True)

        # Dark themed folium map
        m = folium.Map(
            location=[res["lat"], res["lon"]],
            zoom_start=11,
            tiles="CartoDB dark_matter",
        )

        if res.get("field_lat") is not None and res.get("field_lon") is not None:
            folium.Marker(
                [res["field_lat"], res["field_lon"]],
                popup=folium.Popup(
                    f"<b>{res['fair']} (Field)</b><br>Lat: {res['field_lat']:.4f}<br>Lon: {res['field_lon']:.4f}",
                    max_width=250,
                ),
                icon=folium.Icon(color="red", icon="flag", prefix="fa"),
                tooltip="Livestock Field Location"
            ).add_to(m)

            # Accuracy circle
            folium.Circle(
                location=[res["field_lat"], res["field_lon"]],
                radius=25000,
                color="#00d4ff",
                fill=True,
                fill_color="#00d4ff",
                fill_opacity=0.1,
                weight=1,
            ).add_to(m)

        # Add Proof of Location (Semantic description) to the map
        objects = res.get('objects', [])
        landmarks = res.get('landmarks', [])
        
        livestock_map = {"cow": "cattle", "sheep": "sheep", "horse": "horses", "elephant": "elephants", "bird": "poultry"}
        livestock_present = list(set([livestock_map[obj] for obj in objects if obj in livestock_map]))
        other_objects = list(set([obj for obj in objects if obj not in livestock_map]))
        
        area = "Open field"
        if landmarks:
            lm_type = landmarks[0].get("type", "").lower().replace("_", " ")
            if "farm" in lm_type: area = "Farm area"
            elif "market" in lm_type: area = "Marketplace"
            elif "build" in lm_type or "resident" in lm_type: area = "Populated area"
            elif "place of worship" in lm_type: area = "Temple/Worship area"
            elif "parking" in lm_type: area = "Parking area"
                
        if livestock_present:
            l_str = " and ".join(livestock_present[:2])
            if "person" in other_objects:
                proof_desc = f"{area} with {l_str} and people gathering"
            else:
                proof_desc = f"{area} with {l_str} gathering"
        elif other_objects:
            if "person" in other_objects:
                proof_desc = f"{area} with people present"
            else:
                o_str = ", ".join(other_objects[:2])
                proof_desc = f"{area} with {o_str} present"
        else:
            proof_desc = f"{area} representing the location"
            
        folium.Marker(
            [res["lat"], res["lon"]],
            popup=folium.Popup(
                f"<b>Proof of Location</b><br>Landmark: {proof_desc}<br>Lat: {res['lat']:.4f}<br>Lon: {res['lon']:.4f}",
                max_width=250,
            ),
            icon=folium.Icon(color="green", icon="info-sign"),
            tooltip=f"Proof: {proof_desc}"
        ).add_to(m)

        st_folium(m, height=420, use_container_width=True)

        # ── Satellite/Street View Links ──
        satellite_link = f"https://www.google.com/maps/search/?api=1&query={res['lat']},{res['lon']}&basemap=satellite"
        street_view_link = f"https://www.google.com/maps/@{res['lat']:.6f},{res['lon']:.6f},18z/data=!3m1!1e3"
        
        satellite_html = "".join(line.strip() for line in f"""
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
        """.split("\n"))
        st.markdown(satellite_html, unsafe_allow_html=True)
