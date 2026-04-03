#!/usr/bin/env python3
"""
Batch process cattle fairs to get GPS coordinates and landmark info
"""

import pandas as pd
from backend import download_video, scan_video, predict_location
import time

def process_fair(fair_name, video_url, base_lat=None, base_lon=None):
    """Process a single fair and return results"""
    try:
        if pd.notna(video_url) and video_url:
            print(f'\n🔄 Processing {fair_name}...')
            print(f'📹 Video URL: {video_url}')
            
            download_video(video_url)
            objects = scan_video()
            lat, lon, landmarks = predict_location(objects, base_lat, base_lon, fair_name=fair_name)
            
            if lat is not None and lon is not None:
                field_lat_str = f"{base_lat:.6f}" if base_lat is not None else f"{lat:.6f}"
                field_lon_str = f"{base_lon:.6f}" if base_lon is not None else f"{lon:.6f}"
                
                print(f'✅ Field Coordinates: {field_lat_str}, {field_lon_str}')
                print(f'✅ Landmark Coordinates: {lat:.6f}, {lon:.6f}')
                print(f'🔍 Objects: {objects}')
                
                object_names = ", ".join(objects) if objects else "No objects detected"
                
                # Create Google Maps satellite link
                satellite_link = f"https://www.google.com/maps/@{lat:.6f},{lon:.6f},847m/data=!3m1!1e3!4m6!1m2!2s{lat:.6f}!3d{lon:.6f}!2m1!1e0"
                
                return {
                    'name': fair_name,
                    'lat': f"Field: {field_lat_str}, {field_lon_str} | Landmark: {lat:.6f}, {lon:.6f}",
                    'month': 'Jan',  # Default to January for Karnataka cattle fairs
                    'proof': f"(Y1, {object_names} (Lat: {lat:.6f}, Lon: {lon:.6f}), 0:30 ,{satellite_link})",
                    'objects': objects
                }
            else:
                print(f'❌ No location found for {fair_name}')
                return None
                
        else:
            print(f'⚠️ No video URL for {fair_name}')
            return None
            
    except Exception as e:
        print(f'❌ Error processing {fair_name}: {e}')
        return None

def main():
    """Main processing function"""
    df = pd.read_csv('cattle_fairs.csv')
    
    # Get fairs to process (first 10 with valid video links)
    unprocessed = df[df['Video link 1'].notna()]
    
    print(f"📊 Found {len(unprocessed)} fairs to process")
    print("🎯 Processing first 10 fairs...")
    
    results = []
    
    for idx, row in unprocessed.head(10).iterrows():
        fair_name = row['Name or Place']
        video_url = row['Video link 1']
        
        base_lat = float(row['Lat']) if 'Lat' in row and pd.notna(row['Lat']) else None
        base_lon = float(row['Long']) if 'Long' in row and pd.notna(row['Long']) else None
        
        result = process_fair(fair_name, video_url, base_lat, base_lon)
        if result:
            results.append(result)
        
        time.sleep(2)  # Small delay between requests
    
    print(f"\n🎉 Successfully processed {len(results)} fairs")
    
    # Save results
    if results:
        with open('processed_fairs.txt', 'w') as f:
            for result in results:
                f.write(f"{result['name']}: {result['lat']}\n")
                f.write(f"Proof: {result['proof']}\n")
                f.write("---\n")
        
        print("💾 Results saved to processed_fairs.txt")
    
    return results

if __name__ == "__main__":
    main()
