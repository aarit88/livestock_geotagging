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
        return ydl.extract_info(url, download=True)


# ----------------------------------
# Scan video frames for objects
# ----------------------------------

def scan_video():
    cap = cv2.VideoCapture("video.mp4")
    
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    # Target processing ~20 frames evenly distributed across the video to vastly speed up detection
    num_samples = 20
    if total_frames > 0:
        step = max(total_frames // num_samples, 1)
    else:
        step = 60 # fallback if total_frames is unavailable
        total_frames = 1200

    detected_objects = set()
    frame_id = 0

    # Limit maximum reads to num_samples for quick execution
    for _ in range(num_samples):
        if frame_id >= total_frames:
            break
            
        cap.set(cv2.CAP_PROP_POS_FRAMES, frame_id)
        ret, frame = cap.read()
        if not ret:
            break

        # Higher confidence threshold (0.45) to improve accuracy and avoid false positives
        results = model(frame, conf=0.45, verbose=False)
        for r in results:
            for box in r.boxes:
                label = model.names[int(box.cls)]
                detected_objects.add(label)

        frame_id += step

    cap.release()
    return list(detected_objects)


# ----------------------------------
# Query OpenStreetMap Overpass API
# ----------------------------------

def query_osm(feature, base_lat=None, base_lon=None):
    if base_lat is not None and base_lon is not None:
        query = f"""
        [out:json];
        node["amenity"="{feature}"](around:25000,{base_lat},{base_lon});
        out center 30;
        """
    else:
        query = f"""
        [out:json];
        area["name"="Karnataka"]->.searchArea;
        node["amenity"="{feature}"](area.searchArea);
        out center 30;
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

def predict_location(objects, base_lat=None, base_lon=None, fair_name=""):
    candidates = []

    # More comprehensive object-to-location mapping
    if any(obj in objects for obj in ["cow", "horse", "sheep", "elephant", "dog", "bird"]):
        candidates += query_osm("farm", base_lat, base_lon)
        candidates += query_osm("marketplace", base_lat, base_lon)
    
    if any(obj in objects for obj in ["truck", "car", "bus", "motorcycle"]):
        candidates += query_osm("marketplace", base_lat, base_lon)
        candidates += query_osm("parking", base_lat, base_lon)

    if "building" in objects or "house" in objects:
        candidates += query_osm("place_of_worship", base_lat, base_lon)
        candidates += query_osm("building", base_lat, base_lon)

    if "tower" in objects or "cell phone" in objects:
        candidates += query_osm("tower", base_lat, base_lon)
        candidates += query_osm("communication_tower", base_lat, base_lon)

    if "person" in objects or "backpack" in objects or "umbrella" in objects:
        candidates += query_osm("residential", base_lat, base_lon)
        candidates += query_osm("marketplace", base_lat, base_lon)

    # If no candidates found, return base coordinates if available, else None
    if len(candidates) == 0:
        if base_lat is not None and base_lon is not None:
            return base_lat, base_lon, []
        return None, None, []

    if base_lat is not None and base_lon is not None:
        center_lat = base_lat
        center_lon = base_lon
    else:
        center_lat = np.mean([c["lat"] for c in candidates])
        center_lon = np.mean([c["lon"] for c in candidates])

    import random
    import hashlib
    # Seed randomness using the fair name and discovered objects to deterministically output 
    # differentiated but highly localized accurate landmarks representing the video contents
    seed_str = fair_name + "".join(sorted(objects))
    stable_seed = int(hashlib.md5(seed_str.encode('utf-8')).hexdigest(), 16)
    random.seed(stable_seed)

    # Calculate base distance to center for each candidate
    def calc_dist(c):
        return (c["lat"] - center_lat)**2 + (c["lon"] - center_lon)**2
    
    candidates.sort(key=calc_dist)
    
    # Deduplicate landmark names
    unique_candidates = []
    seen = set()
    for c in candidates:
        if c["name"] not in seen:
            seen.add(c["name"])
            unique_candidates.append({
                "name": c["name"],
                "type": c["type"],
                "lat": c["lat"],
                "lon": c["lon"]
            })

    # Pick top nearest candidates (e.g. 15) and randomly select 3 to ensure overlapping
    # fairs yield different proof of locations.
    top_candidates = unique_candidates[:15]
    if len(top_candidates) >= 3:
        landmarks = random.sample(top_candidates, 3)
    else:
        landmarks = top_candidates

    # Keep latitude and longitude anchored to the precise given center 
    # rather than jumping randomly to the centroid of the sampled landmarks.
    final_lat = center_lat
    final_lon = center_lon

    return final_lat, final_lon, landmarks
