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

model = YOLO("yolov8n.pt")


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

        if frame_id % 150 == 0:
            results = model(frame)
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
            coords.append((el["lat"], el["lon"]))
        return coords
    except:
        return []


# ----------------------------------
# Predict location from detected objects
# ----------------------------------

def predict_location(objects):
    candidates = []

    if "truck" in objects or "cow" in objects:
        candidates += query_osm("marketplace")

    if "building" in objects:
        candidates += query_osm("place_of_worship")

    if "tower" in objects:
        candidates += query_osm("tower")

    if len(candidates) == 0:
        return 15.3173, 75.7139

    lat = np.mean([c[0] for c in candidates])
    lon = np.mean([c[1] for c in candidates])

    return lat, lon
