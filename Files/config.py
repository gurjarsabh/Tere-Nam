import os
from dotenv import load_dotenv

load_dotenv()

# ================= BOT CONFIG =================
BOT_TOKEN = os.getenv("BOT_TOKEN", "8821787887:AAE_bcVwD4oF3L1vFSGeUvIKWwxCG064O0Y")
PORT = int(os.getenv("PORT", 8080))

# ================= ADMIN =================
ADMIN_ID = int(os.getenv("ADMIN_ID", "7301992915"))

# ================= MONGODB =================
MONGO_URI = os.getenv("MONGO_URI", "")
DB_NAME = "romeo_bot"

# ================= FORCE JOIN =================
CHANNEL_1 = "Freaky_WorldX"
CHANNEL_2 = "FileDownloadXx"
CHANNEL_1_LINK = "https://t.me/Freaky_WorldX"
CHANNEL_2_LINK = "https://t.me/FileDownloadXx"

# ================= LIMITS =================
MAX_FILE_SIZE_MB = 50
FREE_CREDITS = 5

# ================= CREDITS =================
DEVELOPER = "t.me/KingXRomeo"
CHANNEL = "@RomeoXOfficial"
OWNER = "@KingXRomeo"

# ================= PATHS =================
QR_CODE_PATH = "qr_code.png"
