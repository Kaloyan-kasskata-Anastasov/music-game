import json
import os
import time
import requests

INPUT_FILE = "songs_original.json"       
OUTPUT_FILE = "songs_fixed.json"

# Grab the API key from the GitHub Action environment variable
API_KEY = os.getenv("YOUTUBE_API_KEY")

def is_video_valid(video_id):
    """Checks if a video ID is valid, public, and embeddable using the YouTube API."""
    if not video_id or video_id == "NONE":
        return False
        
    url = f"https://www.googleapis.com/youtube/v3/videos?id={video_id}&key={API_KEY}&part=status"
    
    try:
        response = requests.get(url)
        data = response.json()
        
        if not data.get("items"):
            return False
            
        status = data["items"][0].get("status", {})
        if status.get("privacyStatus") == "public" and status.get("embeddable"):
            return True
            
    except Exception:
        pass 
        
    return False

def get_replacement_id(artist, song):
    """Searches for 'Artist Song lyrics' and returns the top video ID."""
    query = f"{artist} {song} lyrics"
    url = f"https://www.googleapis.com/youtube/v3/search?q={query}&key={API_KEY}&part=snippet&type=video&maxResults=1"
    
    try:
        response = requests.get(url)
        data = response.json()
        
        if data.get("items"):
            return data["items"][0]["id"]["videoId"]
            
    except Exception as e:
        print(f"  [!] Search Error: {e}")
        
    return None

def save_formatted_json(data_list, filename):
    """Saves list of dicts with each dict on a single line."""
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
        print("Please add it to your GitHub Secrets and workflow.")
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

    fixed_list = []

    for i, song in enumerate(all_songs):
        vid_id = song.get('vidId')
        artist = song.get('artist', 'Unknown')
        title = song.get('song', 'Unknown')
        
        print(f"[{i+1}/{total_songs}] {artist} - {title}")
        print(f"  Checking ID ({vid_id})...", end=" ", flush=True)
        
        if is_video_valid(vid_id):
            print("OK")
        else:
            print("FAIL")
            print(f"  Searching replacement...", end=" ", flush=True)
            
            new_id = get_replacement_id(artist, title)
            
            if new_id:
                print(f"Found: {new_id}")
                song['vidId'] = new_id
            else:
                print("Not Found")

        fixed_list.append(song)
        
        time.sleep(0.1) 

    print("-" * 60)
    print(f"Saving formatted JSON to {OUTPUT_FILE}...")
    save_formatted_json(fixed_list, OUTPUT_FILE)
    print("Done!")

if __name__ == "__main__":
    import sys
    main()