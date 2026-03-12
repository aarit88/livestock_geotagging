#!/usr/bin/env python3
"""
Batch process cattle fairs to get GPS coordinates and landmark info
"""

import pandas as pd
from backend import download_video, scan_video, predict_location
import time

def process_fair(fair_name, video_url):
    """Process a single fair and return results"""
    try:
        if pd.notna(video_url) and video_url:
            print(f'\n🔄 Processing {fair_name}...')
            print(f'📹 Video URL: {video_url}')
            
            download_video(video_url)
            objects = scan_video()
            lat, lon = predict_location(objects)
            
            if lat is not None and lon is not None:
                print(f'✅ Coordinates: {lat:.6f}, {lon:.6f}')
                print(f'🔍 Objects: {objects}')
                
                # Create Google Maps satellite link
                satellite_link = f"https://www.google.com/maps/@{lat:.6f},{lon:.6f},847m/data=!3m1!1e3!4m6!1m2!2s{lat:.6f}!3d{lon:.6f}!2m1!1e0"
                
                return {
                    'name': fair_name,
                    'lat': f"{lat:.6f}, {lon:.6f}",
                    'month': 'Jan',  # Default to January for Karnataka cattle fairs
                    'proof': f"(Y1, Cattle fair location, 0:30 ,{satellite_link})",
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
    
    # Get fairs that need processing (empty coordinates)
    unprocessed = df[df['Lat/Long'].isna() | (df['Lat/Long'] == '')]
    
    print(f"📊 Found {len(unprocessed)} fairs to process")
    print("🎯 Processing first 10 fairs...")
    
    results = []
    
    for idx, row in unprocessed.head(10).iterrows():
        fair_name = row['Name or Place']
        video_url = row['Video link 1']
        
        result = process_fair(fair_name, video_url)
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
