#!/usr/bin/env python3
"""
Process ALL cattle fairs with video links to get GPS coordinates and landmark info
"""

import pandas as pd
from backend import download_video, scan_video, predict_location
import time
import re

def parse_csv_safely():
    """Parse CSV with quoted columns that may contain commas"""
    fairs = []
    
    with open('cattle_fairs.csv', 'r', encoding='utf-8') as f:
        lines = f.readlines()
        
    # Skip header
    for line in lines[1:]:
        # Split by comma but handle quoted fields
        parts = []
        current = ""
        in_quotes = False
        
        for char in line.strip():
            if char == '"' and (not current.endswith('\\') or current.count('\\') % 2 == 0):
                in_quotes = not in_quotes
            elif char == ',' and not in_quotes:
                parts.append(current.strip('"'))
                current = ""
            else:
                current += char
        
        if current:
            parts.append(current.strip('"'))
        
        # Ensure we have exactly 7 parts
        while len(parts) < 7:
            parts.append('')
        
        fairs.append({
            'name': parts[0],
            'video1': parts[1],
            'video2': parts[2],
            'lat': parts[3],
            'long': parts[4],
            'month': parts[5],
            'proof': parts[6]
        })
    
    return fairs

def process_fair(fair_info):
    """Process a single fair and return results"""
    try:
        fair_name = fair_info['name']
        video_url = fair_info['video1']
        
        if not video_url or not video_url.strip():
            print(f'⚠️  Skipping {fair_name} - no video URL')
            return None
            
        print(f'\n🔄 Processing {fair_name}...')
        print(f'📹 Video: {video_url[:50]}...')
        
        try:
            base_lat = float(fair_info['lat']) if fair_info['lat'].strip() else None
            base_lon = float(fair_info['long']) if fair_info['long'].strip() else None
        except ValueError:
            base_lat, base_lon = None, None

        # Process video
        download_video(video_url)
        objects = scan_video()
        lat, lon, landmarks = predict_location(objects, base_lat, base_lon, fair_name=fair_name)
        
        if lat is not None and lon is not None:
            field_lat_str = fair_info['lat'].strip() if base_lat is not None else f"{lat:.6f}"
            field_lon_str = fair_info['long'].strip() if base_lon is not None else f"{lon:.6f}"
            
            print(f'✅ Field Coordinates: {field_lat_str}, {field_lon_str}')
            print(f'✅ Landmark Coordinates: {lat:.6f}, {lon:.6f}')
            print(f'🔍 Objects detected: {len(objects)} types')
            
            landmark_name = landmarks[0]['name'] if landmarks else "Unknown Landmark"
            
            # Create Google Maps satellite link for the landmark (proof of location)
            satellite_link = f"https://www.google.com/maps/@{lat:.6f},{lon:.6f},847m/data=!3m1!1e3!4m6!1m2!2s{lat:.6f}!3d{lon:.6f}!2m1!1e0"
            
            return {
                'name': fair_name,
                'lat': field_lat_str,
                'long': field_lon_str,
                'month': fair_info['month'] if fair_info['month'].strip() else 'Jan',
                'proof': f"(Y1, {landmark_name} (Lat: {lat:.6f}, Lon: {lon:.6f}), 0:30 ,{satellite_link})",
                'video1': video_url,
                'video2': fair_info['video2'],
                'objects': objects
            }
        else:
            print(f'❌ No location found for {fair_name}')
            return None
            
    except Exception as e:
        print(f'❌ Error processing {fair_name}: {str(e)[:100]}...')
        return None

def update_csv(results):
    """Update the CSV with processed results"""
    if not results:
        print("No results to update")
        return
        
    # Read original CSV
    fairs = parse_csv_safely()
    
    # Update with new results
    updated_count = 0
    for result in results:
        for fair in fairs:
            if fair['name'] == result['name']:
                fair['lat'] = result['lat']
                fair['long'] = result['long']
                fair['month'] = result['month']
                fair['proof'] = result['proof']
                updated_count += 1
                break
    
    # Write updated CSV
    with open('cattle_fairs_updated.csv', 'w', encoding='utf-8') as f:
        f.write('Name or Place,Video link 1,Video link 2,Lat,Long,Month,"Proof of location: Landmarks (Youtube video, Landmark, Timestamp, GPS or Google Street link)"\n')
        
        for fair in fairs:
            # Quote the proof column properly
            proof = fair['proof'].replace('"', '""') if fair['proof'] else ''
            line = f'{fair["name"]},{fair["video1"]},{fair["video2"]},{fair["lat"]},{fair["long"]},{fair["month"]},"{proof}"\n'
            f.write(line)
    
    print(f"📝 Updated {updated_count} fairs in cattle_fairs_updated.csv")

def main():
    """Process all fairs with video links"""
    print("🚀 Starting batch processing of ALL cattle fairs...")
    print("=" * 60)
    
    # Parse CSV
    fairs = parse_csv_safely()
    
    # Filter fairs to process all valid video links to update proof formats
    to_process = [f for f in fairs if f['video1']]
    
    print(f"📊 Found {len(to_process)} fairs to process")
    print(f"🎯 Total fairs in dataset: {len(fairs)}")
    
    results = []
    start_time = time.time()
    
    for i, fair in enumerate(to_process, 1):
        print(f"\n📍 [{i}/{len(to_process)}] Processing {fair['name']}")
        
        result = process_fair(fair)
        if result:
            results.append(result)
        
        # Progress update
        if i % 5 == 0:
            elapsed = time.time() - start_time
            avg_time = elapsed / i
            remaining = (len(to_process) - i) * avg_time
            print(f"\n📈 Progress: {i}/{len(to_process)} completed")
            print(f"⏱️  Average time per fair: {avg_time:.1f}s")
            print(f"🕐 Estimated remaining time: {remaining/60:.1f} minutes")
        
        # Small delay to avoid overwhelming servers
        time.sleep(1)
    
    # Update CSV
    update_csv(results)
    
    # Summary
    total_time = time.time() - start_time
    print(f"\n🎉 PROCESSING COMPLETE!")
    print(f"✅ Successfully processed: {len(results)}/{len(to_process)} fairs")
    print(f"⏱️  Total time: {total_time/60:.1f} minutes")
    print(f"📊 Success rate: {len(results)/len(to_process)*100:.1f}%")
    
    # Save detailed results
    with open('processing_results.txt', 'w', encoding='utf-8') as f:
        f.write("CATTLE FAIRS PROCESSING RESULTS\n")
        f.write("=" * 50 + "\n\n")
        
        for result in results:
            f.write(f"FAIR: {result['name']}\n")
            f.write(f"FIELD COORDINATES: {result['lat']}, {result['long']}\n")
            f.write(f"MONTH: {result['month']}\n")
            f.write(f"PROOF: {result['proof']}\n")
            f.write(f"OBJECTS DETECTED: {result['objects']}\n")
            f.write("-" * 50 + "\n\n")
    
    print("💾 Detailed results saved to processing_results.txt")
    print("📝 Updated CSV saved as cattle_fairs_updated.csv")

if __name__ == "__main__":
    main()
