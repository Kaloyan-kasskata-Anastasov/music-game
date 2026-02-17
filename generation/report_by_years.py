import json
import os
from collections import Counter

INPUT_FILE = "songs_original.json"

def analyze_songs():
    if not os.path.exists(INPUT_FILE):
        print(f"Error: File '{INPUT_FILE}' not found.")
        return

    try:
        with open(INPUT_FILE, 'r', encoding='utf-8') as f:
            songs = json.load(f)
    except json.JSONDecodeError as e:
        print(f"Error reading JSON: {e}")
        return

    print(f"Loaded {len(songs)} total songs.\n")

    years = []
    for song in songs:
        date_str = song.get('date', '')
        if '.' in date_str:
            year = date_str.split('.')[1]
            years.append(int(year))
        else:
            print(f"⚠️ Warning: Invalid date format for ID {song['id']}: {date_str}")

    year_counts = Counter(years)
    sorted_years = sorted(year_counts.keys())
    
    if not sorted_years:
        print("No valid years found.")
        return

    min_year = sorted_years[0]
    max_year = sorted_years[-1]

    print(f"{'YEAR':<6} | {'COUNT':<5}")
    print("-" * 30)

    for year in range(min_year, max_year + 1):
        count = year_counts.get(year, 0)
        print(f"{year:<6} | {count:<5}")

    print("-" * 30)
    print(f"Total Range: {min_year} - {max_year}")

if __name__ == "__main__":
    analyze_songs()