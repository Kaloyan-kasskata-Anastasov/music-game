import subprocess
import sys
import importlib.util
import os
import calendar

# --- 1. AUTOMATIC INSTALLATION OF DEPENDENCIES ---
required_libraries = {
    "reportlab": "reportlab",
    "qrcode": "qrcode",
    "PIL": "pillow"
}

def install_and_import(package_import_name, pip_install_name):
    if importlib.util.find_spec(package_import_name) is None:
        print(f"Library '{package_import_name}' not found. Installing '{pip_install_name}'...")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", pip_install_name])
            print(f"Successfully installed '{pip_install_name}'.")
        except subprocess.CalledProcessError as e:
            print(f"Error installing '{pip_install_name}': {e}")
            sys.exit(1)
    else:
        print(f"Library '{package_import_name}' is already installed.")

print("--- Checking Dependencies ---")
for import_name, pip_name in required_libraries.items():
    install_and_import(import_name, pip_name)
print("-----------------------------\n")

# --- 2. MAIN SCRIPT IMPORTS ---
import json
import qrcode
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.lib.utils import ImageReader
from io import BytesIO

# --- 3. CONFIGURATION ---
JSON_FILE = "../songs.json"
OUTPUT_PDF = "song_cards.pdf"
BASE_URL = "https://kaloyan-kasskata-anastasov.github.io/music-game/index?Id="

# --- OPTIMIZATION SETTINGS ---
# 6.4 cm width allows 3 columns (19.2cm) within A4 (21cm) leaving ~0.9cm margins
CARD_SIZE = 6.4 * cm 

PAGE_WIDTH, PAGE_HEIGHT = A4

COLS = 3  # Increased from 2
ROWS = 4  # Increased from 3
# Total cards per page: 12

GRID_WIDTH = COLS * CARD_SIZE
GRID_HEIGHT = ROWS * CARD_SIZE
MARGIN_X = (PAGE_WIDTH - GRID_WIDTH) / 2
MARGIN_Y = (PAGE_HEIGHT - GRID_HEIGHT) / 2

def load_data():
    if not os.path.exists(JSON_FILE):
        print(f"Error: '{JSON_FILE}' not found. Please create it first.")
        sys.exit(1)
    with open(JSON_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)

def get_month_abbr(month_str):
    try:
        month_int = int(month_str)
        if 1 <= month_int <= 12:
            return calendar.month_abbr[month_int]
        return month_str
    except ValueError:
        return month_str

def draw_crop_marks(c, x, y, size):
    c.setStrokeColor(colors.lightgrey)
    c.setLineWidth(0.5)
    c.rect(x, y, size, size)

def draw_front(c, x, y, song_data):
    draw_crop_marks(c, x, y, CARD_SIZE)
    cx = x + CARD_SIZE / 2
    
    # --- 1. Artist (Top) ---
    c.setFillColor(colors.black)
    artist_text = song_data['artist']
    
    # Scaled down font for smaller card
    artist_size = 12 
    c.setFont("Helvetica", artist_size)
    while c.stringWidth(artist_text, "Helvetica", artist_size) > (CARD_SIZE - 0.4 * cm) and artist_size > 7:
        artist_size -= 1
        c.setFont("Helvetica", artist_size)
        
    c.drawCentredString(cx, y + CARD_SIZE - 1.2 * cm, artist_text)
    
    # --- 2. Date (Middle) ---
    date_parts = song_data['date'].split('.') 
    month_raw = date_parts[0] if len(date_parts) > 0 else "??"
    year = date_parts[1] if len(date_parts) > 1 else "????"
    month = get_month_abbr(month_raw)

    # Smaller fonts for smaller card
    font_month_name = "Helvetica"
    font_month_size = 12          
    font_year_name = "Helvetica-Bold"
    font_year_size = 28           

    w_month = c.stringWidth(month, font_month_name, font_month_size)
    w_dot   = c.stringWidth(".", font_month_name, font_month_size)
    w_year  = c.stringWidth(year, font_year_name, font_year_size)
    
    total_date_width = w_month + w_dot + w_year
    start_x = cx - (total_date_width / 2)
    base_y = y + CARD_SIZE / 2 - 0.3 * cm

    c.setFont(font_month_name, font_month_size)
    c.drawString(start_x, base_y, month)
    c.drawString(start_x + w_month, base_y, ".")
    c.setFont(font_year_name, font_year_size)
    c.drawString(start_x + w_month + w_dot, base_y, year)

    # --- 3. Title (Bottom) ---
    title_text = song_data['song']
    title_size = 12
    c.setFont("Helvetica", title_size)
    while c.stringWidth(title_text, "Helvetica", title_size) > (CARD_SIZE - 0.4 * cm) and title_size > 7:
        title_size -= 1
        c.setFont("Helvetica", title_size)
    
    c.drawCentredString(cx, y + 1.2 * cm, title_text)
    
    # --- 4. ID (Bottom Right) ---
    c.setFont("Helvetica", 5)
    c.drawRightString(x + CARD_SIZE - 0.2 * cm, y + 0.2 * cm, f"ID: {song_data['id']}")

def draw_back(c, x, y, song_data):
    draw_crop_marks(c, x, y, CARD_SIZE)
    
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=10,
        border=0
    )
    qr.add_data(f"{BASE_URL}{song_data['id']}")
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    
    img_buffer = BytesIO()
    img.save(img_buffer)
    img_buffer.seek(0)
    rl_img = ImageReader(img_buffer)
    
    qr_display_size = CARD_SIZE * 0.85
    qx = x + (CARD_SIZE - qr_display_size) / 2
    qy = y + (CARD_SIZE - qr_display_size) / 2
    
    c.drawImage(rl_img, qx, qy, width=qr_display_size, height=qr_display_size)

def generate_pdf():
    print("Loading data...")
    data = load_data()
    
    c = canvas.Canvas(OUTPUT_PDF, pagesize=A4)
    c.setTitle("Music Game Cards")
    
    cards_per_page = COLS * ROWS
    total_songs = len(data)
    
    for i in range(0, total_songs, cards_per_page):
        chunk = data[i : i + cards_per_page]
        
        # --- FRONT PAGE ---
        for idx, song in enumerate(chunk):
            row = idx // COLS  
            col = idx % COLS   
            draw_row = (ROWS - 1) - row 
            
            x = MARGIN_X + (col * CARD_SIZE)
            y = MARGIN_Y + (draw_row * CARD_SIZE)
            
            draw_front(c, x, y, song)
        
        c.showPage() 
        
        # --- BACK PAGE (MIRRORED) ---
        for idx, song in enumerate(chunk):
            row = idx // COLS
            col = idx % COLS
            
            # Mirror Logic for 3 columns:
            # Col 0 (Left) -> Col 2 (Right)
            # Col 1 (Mid)  -> Col 1 (Mid)
            # Col 2 (Right)-> Col 0 (Left)
            mirror_col = (COLS - 1) - col
            
            draw_row = (ROWS - 1) - row
            
            x = MARGIN_X + (mirror_col * CARD_SIZE)
            y = MARGIN_Y + (draw_row * CARD_SIZE)
            
            draw_back(c, x, y, song)
            
        c.showPage() 

    c.save()
    print(f"Success! Generated '{OUTPUT_PDF}' with {total_songs} cards.")
    print(f"Layout: {COLS}x{ROWS} grid (12 cards per page).")

if __name__ == "__main__":
    generate_pdf()