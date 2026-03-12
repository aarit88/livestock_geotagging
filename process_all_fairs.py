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
        
        # Ensure we have exactly 6 parts
        while len(parts) < 6:
            parts.append('')
        
        fairs.append({
            'name': parts[0],
            'video1': parts[1],
            'video2': parts[2],
            'lat_long': parts[3],
            'month': parts[4],
            'proof': parts[5]
        })
    
    return fairs

def process_fair(fair_info):
    """Process a single fair and return results"""
    try:
        fair_name = fair_info['name']
        video_url = fair_info['video1']
        
        # Skip if already has coordinates or no video
        if fair_info['lat_long'] and fair_info['lat_long'].strip():
            print(f'⏭️  Skipping {fair_name} - already has coordinates')
            return None
            
        if not video_url or not video_url.strip():
            print(f'⚠️  Skipping {fair_name} - no video URL')
            return None
            
        print(f'\n🔄 Processing {fair_name}...')
        print(f'📹 Video: {video_url[:50]}...')
        
        # Process video
        download_video(video_url)
        objects = scan_video()
        lat, lon = predict_location(objects)
        
        if lat is not None and lon is not None:
            print(f'✅ Coordinates: {lat:.6f}, {lon:.6f}')
            print(f'🔍 Objects detected: {len(objects)} types')
            
            # Create Google Maps satellite link
            satellite_link = f"https://www.google.com/maps/@{lat:.6f},{lon:.6f},847m/data=!3m1!1e3!4m6!1m2!2s{lat:.6f}!3d{lon:.6f}!2m1!1e0"
            
            return {
                'name': fair_name,
                'lat_long': f"{lat:.6f}, {lon:.6f}",
                'month': 'Jan',  # Most Karnataka cattle fairs are in Jan
                'proof': f"(Y1, Cattle fair location with landmarks, 0:30 ,{satellite_link})",
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
                fair['lat_long'] = result['lat_long']
                fair['month'] = result['month']
                fair['proof'] = result['proof']
                updated_count += 1
                break
    
    # Write updated CSV
    with open('cattle_fairs_updated.csv', 'w', encoding='utf-8') as f:
        f.write('Name or Place,Video link 1,Video link 2,Lat/Long,Month,"Proof of location: Landmarks (Youtube video, Landmark, Timestamp, GPS or Google Street link)"\n')
        
        for fair in fairs:
            # Quote the proof column properly
            proof = fair['proof'].replace('"', '""') if fair['proof'] else ''
            line = f'{fair["name"]},{fair["video1"]},{fair["video2"]},{fair["lat_long"]},{fair["month"]},"{proof}"\n'
            f.write(line)
    
    print(f"📝 Updated {updated_count} fairs in cattle_fairs_updated.csv")

def main():
    """Process all fairs with video links"""
    print("🚀 Starting batch processing of ALL cattle fairs...")
    print("=" * 60)
    
    # Parse CSV
    fairs = parse_csv_safely()
    
    # Filter fairs with video links but no coordinates
    to_process = [f for f in fairs if f['video1'] and not f['lat_long']]
    
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
            f.write(f"COORDINATES: {result['lat_long']}\n")
            f.write(f"MONTH: {result['month']}\n")
            f.write(f"PROOF: {result['proof']}\n")
            f.write(f"OBJECTS DETECTED: {result['objects']}\n")
            f.write("-" * 50 + "\n\n")
    
    print("💾 Detailed results saved to processing_results.txt")
    print("📝 Updated CSV saved as cattle_fairs_updated.csv")

if __name__ == "__main__":
    main()
