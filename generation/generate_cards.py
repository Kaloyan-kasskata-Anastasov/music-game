import subprocess
import sys
import importlib.util
import os
import json
import urllib.request
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
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

# --- 3. CONFIGURATION ---
JSON_FILE = "songs_original.json"
OUTPUT_PDF = "./generation/song_cards.pdf"
BASE_URL = "https://kaloyan-kasskata-anastasov.github.io/music-game/index?Id="

# --- LAYOUT SETTINGS ---
CARD_WIDTH = 6.4 * cm
CARD_HEIGHT = 6.4 * cm
PADDING = 0.5 * cm      

PAGE_WIDTH, PAGE_HEIGHT = A4

COLS = 3
ROWS = 4
GRID_WIDTH = COLS * CARD_WIDTH
GRID_HEIGHT = ROWS * CARD_HEIGHT

FRONT_MARGIN_X = 0.0
TOP_MARGIN_Y = 0.0
BACK_MARGIN_X = PAGE_WIDTH - GRID_WIDTH

def setup_fonts():
    """Downloads and registers fonts with Cyrillic support."""
    # Using reliable raw GitHub links from the matplotlib repository
    reg_url = "https://raw.githubusercontent.com/matplotlib/matplotlib/main/lib/matplotlib/mpl-data/fonts/ttf/DejaVuSans.ttf"
    bold_url = "https://raw.githubusercontent.com/matplotlib/matplotlib/main/lib/matplotlib/mpl-data/fonts/ttf/DejaVuSans-Bold.ttf"
    
    if not os.path.exists("DejaVuSans.ttf"):
        print("Downloading font (Regular)...")
        try:
            urllib.request.urlretrieve(reg_url, "DejaVuSans.ttf")
        except Exception as e:
            print(f"Failed to download Regular font. Error: {e}")
            sys.exit(1)
            
    if not os.path.exists("DejaVuSans-Bold.ttf"):
        print("Downloading font (Bold)...")
        try:
            urllib.request.urlretrieve(bold_url, "DejaVuSans-Bold.ttf")
        except Exception as e:
            print(f"Failed to download Bold font. Error: {e}")
            sys.exit(1)
        
    pdfmetrics.registerFont(TTFont('Cyrillic-Regular', 'DejaVuSans.ttf'))
    pdfmetrics.registerFont(TTFont('Cyrillic-Bold', 'DejaVuSans-Bold.ttf'))

def load_data():
    if not os.path.exists(JSON_FILE):
        print(f"Error: '{JSON_FILE}' not found.")
        sys.exit(1)
    with open(JSON_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)

def draw_card_border(c, x, y):
    c.setStrokeColor(colors.black)
    c.setLineWidth(1)
    c.rect(x, y, CARD_WIDTH, CARD_HEIGHT)

def draw_front(c, x, y, song_data):
    draw_card_border(c, x, y)
    
    cx = x + CARD_WIDTH / 2
    max_text_width = CARD_WIDTH - (2 * PADDING)
    
    # --- 1. Artist (Top) ---
    c.setFillColor(colors.black)
    artist_text = song_data['artist']
    artist_size = 22
    c.setFont("Cyrillic-Bold", artist_size)
    
    while c.stringWidth(artist_text, "Cyrillic-Bold", artist_size) > max_text_width and artist_size > 8:
        artist_size -= 1
        c.setFont("Cyrillic-Bold", artist_size)
        
    c.drawCentredString(cx, y + CARD_HEIGHT - PADDING - 0.7 * cm, artist_text)
    
    # --- 2. Year (Middle) ---
    date_parts = song_data['date'].split('.') 
    year = date_parts[1] if len(date_parts) > 1 else song_data['date']

    font_year_size = 44
    c.setFont("Cyrillic-Bold", font_year_size)
    
    base_y = y + (CARD_HEIGHT / 2) - 0.4 * cm
    c.drawCentredString(cx, base_y, year)

    # --- 3. Title (Bottom) ---
    title_text = song_data['song']
    title_size = 18
    c.setFont("Cyrillic-Regular", title_size)
    
    while c.stringWidth(title_text, "Cyrillic-Regular", title_size) > max_text_width and title_size > 8:
        title_size -= 1
        c.setFont("Cyrillic-Regular", title_size)
    
    c.drawCentredString(cx, y + PADDING + 0.6 * cm, title_text)
    
    # --- 4. ID (Bottom Right) ---
    c.setFont("Cyrillic-Regular", 7)
    c.drawRightString(x + CARD_WIDTH - PADDING, y + PADDING / 2, f"ID: {song_data['id']}")

def draw_back(c, x, y, song_data):
    draw_card_border(c, x, y)
    
    qr = qrcode.QRCode(border=0)
    qr.add_data(f"{BASE_URL}{song_data['id']}")
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    
    img_buffer = BytesIO()
    img.save(img_buffer)
    img_buffer.seek(0)
    rl_img = ImageReader(img_buffer)
    
    qr_size = CARD_WIDTH - (2 * PADDING)
    qx = x + PADDING
    qy = y + PADDING
    
    c.drawImage(rl_img, qx, qy, width=qr_size, height=qr_size)

def generate_pdf():
    print("Setting up fonts...")
    setup_fonts()
    
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
            
            x = FRONT_MARGIN_X + (col * CARD_WIDTH)
            y = PAGE_HEIGHT - TOP_MARGIN_Y - ((row + 1) * CARD_HEIGHT)
            
            draw_front(c, x, y, song)
        
        c.showPage()
        
        # --- BACK PAGE (MIRRORED) ---
        for idx, song in enumerate(chunk):
            row = idx // COLS
            col = idx % COLS
            
            mirror_col = (COLS - 1) - col
            
            x = BACK_MARGIN_X + (mirror_col * CARD_WIDTH)
            y = PAGE_HEIGHT - TOP_MARGIN_Y - ((row + 1) * CARD_HEIGHT)
            
            draw_back(c, x, y, song)
            
        c.showPage()

    c.save()
    print(f"Success! Generated '{OUTPUT_PDF}'.")

if __name__ == "__main__":
    generate_pdf()