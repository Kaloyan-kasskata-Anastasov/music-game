import subprocess
import sys
import importlib.util
import os
import calendar
import json
import qrcode
from io import BytesIO

# --- 1. DEPENDENCIES ---
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

for import_name, pip_name in required_libraries.items():
    install_and_import(import_name, pip_name)

# --- 2. IMPORTS ---
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.lib.utils import ImageReader

# --- 3. CONFIGURATION ---
JSON_FILE = "songs_original.json"
OUTPUT_PDF = "./generation/song_cards.pdf"
BASE_URL = "https://kaloyan-kasskata-anastasov.github.io/music-game/index?Id="

# --- LAYOUT SETTINGS ---
CARD_WIDTH = 6.4 * cm
CARD_HEIGHT = 6.4 * cm
PADDING = 0.5 * cm      # 5mm internal padding for text

PAGE_WIDTH, PAGE_HEIGHT = A4

COLS = 3
ROWS = 4
GRID_WIDTH = COLS * CARD_WIDTH
GRID_HEIGHT = ROWS * CARD_HEIGHT

# --- ZERO MARGIN POSITIONING ---
# Start exactly at the edge of the paper
FRONT_MARGIN_X = 0.0
TOP_MARGIN_Y = 0.0

# CALCULATE MIRROR MARGIN FOR BACK PAGE
# Since Front starts at 0 (Left Edge), Back must start at (Page Width - Grid Width) (Right Edge)
# to align perfectly when printed double-sided.
BACK_MARGIN_X = PAGE_WIDTH - GRID_WIDTH

def load_data():
    if not os.path.exists(JSON_FILE):
        print(f"Error: '{JSON_FILE}' not found.")
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

def draw_card_border(c, x, y):
    """Draws the shared border around the card."""
    c.setStrokeColor(colors.black)
    c.setLineWidth(1)
    c.rect(x, y, CARD_WIDTH, CARD_HEIGHT)

def draw_front(c, x, y, song_data):
    draw_card_border(c, x, y)
    
    cx = x + CARD_WIDTH / 2
    max_text_width = CARD_WIDTH - (2 * PADDING)
    
    # --- Artist (Top) ---
    c.setFillColor(colors.black)
    artist_text = song_data['artist']
    artist_size = 18
    c.setFont("Helvetica-Bold", artist_size)
    
    while c.stringWidth(artist_text, "Helvetica-Bold", artist_size) > max_text_width and artist_size > 8:
        artist_size -= 1
        c.setFont("Helvetica-Bold", artist_size)
        
    c.drawCentredString(cx, y + CARD_HEIGHT - PADDING - 0.6 * cm, artist_text)
    
    # --- Date (Middle) ---
    date_parts = song_data['date'].split('.') 
    month_raw = date_parts[0] if len(date_parts) > 0 else "??"
    year = date_parts[1] if len(date_parts) > 1 else "????"
    month = get_month_abbr(month_raw)

    font_month_size = 14          
    font_year_size = 36           

    w_month = c.stringWidth(month, "Helvetica", font_month_size)
    w_dot   = c.stringWidth(".", "Helvetica", font_month_size)
    w_year  = c.stringWidth(year, "Helvetica-Bold", font_year_size)
    
    total_date_width = w_month + w_dot + w_year
    start_x = cx - (total_date_width / 2)
    base_y = y + (CARD_HEIGHT / 2) - 0.3 * cm

    c.setFont("Helvetica", font_month_size)
    c.drawString(start_x, base_y, month)
    c.drawString(start_x + w_month, base_y, ".")
    c.setFont("Helvetica-Bold", font_year_size)
    c.drawString(start_x + w_month + w_dot, base_y, year)

    # --- Title (Bottom) ---
    title_text = song_data['song']
    title_size = 14
    c.setFont("Helvetica", title_size)
    while c.stringWidth(title_text, "Helvetica", title_size) > max_text_width and title_size > 8:
        title_size -= 1
        c.setFont("Helvetica", title_size)
    
    c.drawCentredString(cx, y + PADDING + 0.5 * cm, title_text)
    
    # --- ID (Bottom Right) ---
    c.setFont("Helvetica", 6)
    c.drawRightString(x + CARD_WIDTH - PADDING, y + PADDING / 2, f"ID: {song_data['id']}")

def draw_back(c, x, y, song_data):
    draw_card_border(c, x, y)
    
    # Generate QR
    qr = qrcode.QRCode(border=0)
    qr.add_data(f"{BASE_URL}{song_data['id']}")
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    
    img_buffer = BytesIO()
    img.save(img_buffer)
    img_buffer.seek(0)
    rl_img = ImageReader(img_buffer)
    
    # QR Size fits inside padding
    qr_size = CARD_WIDTH - (2 * PADDING)
    qx = x + PADDING
    qy = y + PADDING
    
    c.drawImage(rl_img, qx, qy, width=qr_size, height=qr_size)

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
            
            # Position: Absolute Top-Left
            x = FRONT_MARGIN_X + (col * CARD_WIDTH)
            # Y starts from TOP of page (PAGE_HEIGHT) and goes down
            y = PAGE_HEIGHT - TOP_MARGIN_Y - ((row + 1) * CARD_HEIGHT)
            
            draw_front(c, x, y, song)
        
        c.showPage()
        
        # --- BACK PAGE (MIRRORED) ---
        for idx, song in enumerate(chunk):
            row = idx // COLS
            col = idx % COLS
            
            # MIRROR: Left column becomes Right column
            mirror_col = (COLS - 1) - col
            
            # BACK_MARGIN_X aligns the grid to the RIGHT edge of the page
            x = BACK_MARGIN_X + (mirror_col * CARD_WIDTH)
            y = PAGE_HEIGHT - TOP_MARGIN_Y - ((row + 1) * CARD_HEIGHT)
            
            draw_back(c, x, y, song)
            
        c.showPage()

    c.save()
    print(f"Success! Generated '{OUTPUT_PDF}'.")
    print(f"Margins: 0cm. Start cutting from the Top-Left edge.")

if __name__ == "__main__":
    generate_pdf()