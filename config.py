import os, logging
from logging.handlers import RotatingFileHandler
from dotenv import load_dotenv

load_dotenv()

# ─── BOT SETTINGS ───────────────────────────────
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN", "YOUR_TOKEN")
ADMIN_IDS       = list(map(int, os.getenv("ADMIN_IDS", "123456789").split(",")))

# ─── BROWSER SETTINGS ───────────────────────────
HEADLESS        = True
MIN_DELAY       = 1
MAX_DELAY       = 3
TIMEOUT         = 30000

# ─── PATHS ──────────────────────────────────────
DOCS_DIR        = "generated_cards"
SCREENSHOTS_DIR = "screenshots"
os.makedirs(DOCS_DIR,        exist_ok=True)
os.makedirs(SCREENSHOTS_DIR, exist_ok=True)

# ─── LOGGER ─────────────────────────────────────
def setup_logger():
    logger = logging.getLogger("GHS")
    logger.setLevel(logging.INFO)

    fmt = logging.Formatter("[%(asctime)s] %(levelname)s — %(message)s", "%H:%M:%S")

    # Console
    ch = logging.StreamHandler()
    ch.setFormatter(fmt)

    # File rotation
    fh = RotatingFileHandler("bot.log", maxBytes=5*1024*1024, backupCount=3)
    fh.setFormatter(fmt)

    logger.addHandler(ch)
    logger.addHandler(fh)
    return logger

log = setup_logger()
