import json
import os
import time
import requests
import sys

INPUT_FILE = "songs_original.json"       
OUTPUT_FILE = "songs_original.json"

API_KEY = os.getenv("YOUTUBE_API_KEY")

# 90 searches * 100 quota units = 9,000 units.
# Leaves 1,000 units safely available for the batch checking.
MAX_SEARCHES_PER_RUN = 90  

def check_videos_batch(video_ids):
    """Checks multiple video IDs at once (up to 50 per request)."""
    valid_vids = set()
    chunk_size = 50
    
    for i in range(0, len(video_ids), chunk_size):
        chunk = video_ids[i:i + chunk_size]
        ids_str = ",".join(chunk)
        url = f"https://www.googleapis.com/youtube/v3/videos?id={ids_str}&key={API_KEY}&part=status"
        
        try:
            response = requests.get(url)
            data = response.json()
            
            if "error" in data:
                print(f"\n[API Error during batch check: {data['error']['message']}]")
                return valid_vids
                
            for item in data.get("items", []):
                vid_id = item["id"]
                status = item.get("status", {})
                
                if status.get("privacyStatus") == "public":
                    valid_vids.add(vid_id)
                    
        except Exception as e:
            print(f"\n[!] Batch Check Exception: {e}")
            
    return valid_vids

def get_replacement_id(artist, song):
    """Searches for a replacement (Costs 100 quota units per run!)."""
    query = f"{artist} {song} lyrics"
    url = f"https://www.googleapis.com/youtube/v3/search?q={query}&key={API_KEY}&part=snippet&type=video&maxResults=1"
    
    try:
        response = requests.get(url)
        data = response.json()
        
        if "error" in data:
            print(f" [API Search Error: {data['error']['message']}]", end="")
            return None
        
        if data.get("items"):
            return data["items"][0]["id"]["videoId"]
            
    except Exception as e:
        print(f"  [!] Exception: {e}")
        
    return None

def save_formatted_json(data_list, filename):
    with open(filename, 'w', encoding='utf-8') as f:
        f.write("[\n")
        total = len(data_list)
        for i, item in enumerate(data_list):
            json_str = json.dumps(item, separators=(',', ':'), ensure_ascii=False)
            comma = "," if i < total - 1 else ""
            f.write(f"  {json_str}{comma}\n")
        f.write("]\n")

def main():
    if not API_KEY:
        print("Error: YOUTUBE_API_KEY environment variable not found!")
        sys.exit(1)

    if not os.path.exists(INPUT_FILE):
        print(f"Error: {INPUT_FILE} not found.")
        return

    print(f"Loading {INPUT_FILE}...")
    with open(INPUT_FILE, 'r', encoding='utf-8') as f:
        all_songs = json.load(f)

    total_songs = len(all_songs)
    print(f"Processing {total_songs} songs...")
    print("-" * 60)

    # 1. BATCH CHECK ALL SONGS
    print("Checking all video statuses in batches...")
    all_vid_ids = [song.get('vidId') for song in all_songs if song.get('vidId') and song.get('vidId') != "NONE"]
    valid_vids = check_videos_batch(all_vid_ids)
    print(f"Finished batch check. {len(valid_vids)} videos are valid.")
    print("-" * 60)

    fixed_list = []
    searches_performed = 0

    for i, song in enumerate(all_songs):
        vid_id = song.get('vidId')
        artist = song.get('artist', 'Unknown')
        title = song.get('song', 'Unknown')
        
        print(f"[{i+1}/{total_songs}] {artist} - {title}")
        print(f"  Status...", end=" ", flush=True)
        
        if vid_id in valid_vids:
            print("OK")
        else:
            print("FAIL")
            
            # Quota Protection Logic
            if searches_performed < MAX_SEARCHES_PER_RUN:
                print(f"  Searching replacement...", end=" ", flush=True)
                new_id = get_replacement_id(artist, title)
                searches_performed += 1
                
                if new_id:
                    print(f"Found: {new_id}")
                    song['vidId'] = new_id
                else:
                    print("Not Found")
            else:
                print("  [!] Search skipped to protect API quota. Will fix in future runs.")

        fixed_list.append(song)
        time.sleep(0.1)

    print("-" * 60)
    print(f"Total searches performed this run: {searches_performed}/{MAX_SEARCHES_PER_RUN}")
    print(f"Saving formatted JSON to {OUTPUT_FILE}...")
    save_formatted_json(fixed_list, OUTPUT_FILE)
    print("Done!")

if __name__ == "__main__":
    main()