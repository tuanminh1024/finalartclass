import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ASSETS_DIR = os.path.join(BASE_DIR, "assets")

REGULAR_FONT_PATH = os.path.join(ASSETS_DIR, "NotoSans-Regular.ttf")
BOLD_FONT_PATH = os.path.join(ASSETS_DIR, "NotoSans-Bold.ttf")
WATERMARK_RUNTIME_PATH = os.path.join(BASE_DIR, "selected_watermark.png")
