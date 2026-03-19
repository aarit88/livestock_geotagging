"""
Backend module — Model loading, video processing, OSM queries, and geolocation prediction.
"""

import cv2  # pyre-ignore[21]
import yt_dlp  # pyre-ignore[21]
import numpy as np  # pyre-ignore[21]
import requests  # pyre-ignore[21]
from ultralytics import YOLO  # pyre-ignore[21]


# ----------------------------------
# Load YOLO model
# ----------------------------------

# Using YOLOv8s (Small) instead of Nano for better detection accuracy
model = YOLO("yolov8s.pt")


# ----------------------------------
# Download video from URL
# ----------------------------------

def download_video(url):
    ydl_opts = {
        "format": "best",
        "quiet": True,
        "outtmpl": "video.mp4"
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])


# ----------------------------------
# Scan video frames for objects
# ----------------------------------

def scan_video():
    cap = cv2.VideoCapture("video.mp4")
    detected_objects = []
    frame_id = 0

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        # Process frames more frequently (e.g. every 60 frames approx 2 seconds instead of 150)
        if frame_id % 60 == 0:
            # Add a confidence threshold of 0.3 to prevent false positive hallucinations
            results = model(frame, conf=0.3, verbose=False)
            for r in results:
                for box in r.boxes:
                    label = model.names[int(box.cls)]
                    detected_objects.append(label)

        frame_id += 1

    cap.release()
    return list(set(detected_objects))


# ----------------------------------
# Query OpenStreetMap Overpass API
# ----------------------------------

def query_osm(feature):
    query = f"""
    [out:json];
    area["name"="Karnataka"]->.searchArea;
    node["amenity"="{feature}"](area.searchArea);
    out center 10;
    """
    url = "https://overpass-api.de/api/interpreter"

    try:
        r = requests.post(url, data=query, timeout=30)
        if r.status_code != 200:
            return []
        data = r.json()
        coords = []
        for el in data.get("elements", []):
            name = el.get("tags", {}).get("name", "Unnamed " + feature.replace("_", " ").title())
            coords.append({
                "lat": el["lat"],
                "lon": el["lon"],
                "name": name,
                "type": feature.replace("_", " ").title()
            })
        return coords
    except:
        return []


# ----------------------------------
# Predict location from detected objects
# ----------------------------------

def predict_location(objects):
    candidates = []

    # More comprehensive object-to-location mapping
    if any(obj in objects for obj in ["cow", "horse", "sheep", "elephant", "dog", "bird"]):
        candidates += query_osm("farm")
        candidates += query_osm("marketplace")
    
    if any(obj in objects for obj in ["truck", "car", "bus", "motorcycle"]):
        candidates += query_osm("marketplace")
        candidates += query_osm("parking")

    if "building" in objects or "house" in objects:
        candidates += query_osm("place_of_worship")
        candidates += query_osm("building")

    if "tower" in objects or "cell phone" in objects:
        candidates += query_osm("tower")
        candidates += query_osm("communication_tower")

    if "person" in objects or "backpack" in objects or "umbrella" in objects:
        candidates += query_osm("residential")
        candidates += query_osm("marketplace")

    # If no candidates found, return None instead of hardcoded coordinates
    if len(candidates) == 0:
        return None, None, []

    lat = np.mean([c["lat"] for c in candidates])
    lon = np.mean([c["lon"] for c in candidates])

    # Calculate distance to center for each candidate
    def calc_dist(c):
        return (c["lat"] - lat)**2 + (c["lon"] - lon)**2
    
    candidates.sort(key=calc_dist)
    
    # Deduplicate landmark names
    landmarks = []
    seen = set()
    for c in candidates:
        if c["name"] not in seen:
            seen.add(c["name"])
            landmarks.append({
                "name": c["name"],
                "type": c["type"],
                "lat": c["lat"],
                "lon": c["lon"]
            })
        if len(landmarks) >= 3:
            break

    return lat, lon, landmarks
