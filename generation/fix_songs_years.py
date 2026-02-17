import json
import requests
import time
from datetime import datetime

INPUT_FILE = "songs_original.json"
API_URL = "https://itunes.apple.com/search"
ROW_FMT = "{:<4} | {:<20} | {:<30} | {:<9} | {:<9} | {}"
SLEEP_ON_SONGS = 1
SLEEP_ON_ERROR = 20

def update_songs():
    try:
        with open(INPUT_FILE, 'r', encoding='utf-8') as f:
            songs = json.load(f)
    except FileNotFoundError:
        print(f"Error: Could not find '{INPUT_FILE}'")
        return

    updates_count = 0
    errors_summary = []

    print(ROW_FMT.format('ID', 'ARTIST', 'SONG', 'OLD', 'NEW', 'STATUS'))
    print("-" * 110)

    for song in songs:
        original_date_str = song.get('date', '')
        artist_disp = (song['artist'][:17] + '..') if len(song['artist']) > 17 else song['artist']
        song_disp = (song['song'][:27] + '..') if len(song['song']) > 27 else song['song']
        
        search_term = f"{song['artist']} {song['song']}"
        params = {'term': search_term, 'entity': 'song', 'limit': 10}

        retries = 0
        success = False

        while retries < 2 and not success:
            try:
                response = requests.get(API_URL, params=params, timeout=10)
                
                if response.status_code == 200:
                    data = response.json()
                    if data['resultCount'] > 0:
                        valid_dates = [datetime.strptime(r['releaseDate'], "%Y-%m-%dT%H:%M:%SZ") 
                                       for r in data['results'] if 'releaseDate' in r]
                        
                        if valid_dates:
                            valid_dates.sort()
                            new_date_str = valid_dates[0].strftime("%m.%Y")
                            
                            if new_date_str != original_date_str:
                                song['date'] = new_date_str
                                print(ROW_FMT.format(song['id'], artist_disp, song_disp, original_date_str, new_date_str, "UPDATED"))
                                updates_count += 1
                            else:
                                print(ROW_FMT.format(song['id'], artist_disp, song_disp, original_date_str, new_date_str, "MATCH"))
                            success = True
                        else:
                            print(ROW_FMT.format(song['id'], artist_disp, song_disp, original_date_str, "---", "NO DATE"))
                            success = True
                    else:
                        print(ROW_FMT.format(song['id'], artist_disp, song_disp, original_date_str, "---", "NOT FOUND"))
                        success = True

                elif response.status_code == 403:
                    print(f"403 Forbidden for ID {song['id']}. Sleeping 20s before retry...")
                    time.sleep(SLEEP_ON_ERROR)
                    retries += 1
                else:
                    status_msg = f"API Error {response.status_code}"
                    print(ROW_FMT.format(song['id'], artist_disp, song_disp, original_date_str, "---", status_msg))
                    errors_summary.append(f"ID {song['id']} - {artist_disp}: {status_msg}")
                    success = True 

            except Exception as e:
                errors_summary.append(f"ID {song['id']} - {artist_disp}: {str(e)}")
                success = True

        if not success and retries >= 2:
            errors_summary.append(f"ID {song['id']} - {artist_disp}: Persistent 403 Error")

        time.sleep(SLEEP_ON_SONGS)

    print("-" * 110)
    print(f"Process complete. Total songs updated: {updates_count}")

    if errors_summary:
        print("\n" + "="*30 + "\n ERROR SUMMARY \n" + "="*30)
        for err in errors_summary: print(f"• {err}")

    # Custom write logic for "One Entity Per Line"
    with open(INPUT_FILE, 'w', encoding='utf-8') as f:
        f.write("[\n")
        for i, song in enumerate(songs):
            # separators=(',', ':') removes spaces inside the JSON string
            line = json.dumps(song, ensure_ascii=False, separators=(',', ':'))
            f.write(f"  {line}")
            if i < len(songs) - 1:
                f.write(",")
            f.write("\n")
        f.write("]")
    
    print(f"Saved updated list to '{INPUT_FILE}'")

if __name__ == "__main__":
    update_songs()