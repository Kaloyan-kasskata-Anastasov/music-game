import json
import os
import time
import yt_dlp

INPUT_FILE = "../songs.json"       
OUTPUT_FILE = "../songs_fixed.json"

VALIDATE_OPTS = {
    'quiet': True,
    'no_warnings': True,
    'skip_download': True,
    'check_formats': False, 
    'ignoreerrors': False, 
}

SEARCH_OPTS = {
    'quiet': True,
    'no_warnings': True,
    'default_search': 'ytsearch1',
    'noplaylist': True,
    'skip_download': True,
}

def is_video_valid(video_id):
    """Checks if a video ID is valid and accessible."""
    if not video_id or video_id == "NONE":
        return False
        
    url = f"https://www.youtube.com/watch?v={video_id}"
    try:
        with yt_dlp.YoutubeDL(VALIDATE_OPTS) as ydl:
            info = ydl.extract_info(url, download=False)
            if 'title' in info and info.get('duration', 0) > 0:
                return True
    except Exception:
        pass 
    return False

def get_replacement_id(artist, song):
    """Searches for 'Artist Song Lyrics'."""
    query = f"{artist} {song} lyrics"
    try:
        with yt_dlp.YoutubeDL(SEARCH_OPTS) as ydl:
            info = ydl.extract_info(f"ytsearch1:{query}", download=False)
            if 'entries' in info and len(info['entries']) > 0:
                return info['entries'][0]['id']
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
        
        time.sleep(1)

    print("-" * 60)
    print(f"Saving formatted JSON to {OUTPUT_FILE}...")
    save_formatted_json(fixed_list, OUTPUT_FILE)
    print("Done!")

if __name__ == "__main__":
    main()