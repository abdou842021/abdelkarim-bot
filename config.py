import os
from dotenv import load_dotenv

load_dotenv()

# ====================== BOT CREDENTIALS ======================
BOT_TOKEN = os.getenv("BOT_TOKEN")
OWNER_ID = int(os.getenv("OWNER_ID", "0"))

# ====================== BOT INFO ======================
BOT_NAME = "Abdelkarim"
BOT_USERNAME = "AbdelkarimBot"

# ====================== LIMITS ======================
MAX_WORDS = 250

# ====================== ALLOWED GROUPS ======================
ALLOWED_GROUP_IDS = set()

# ====================== TTS VOICES ======================
VOICE_BRITISH = "en-GB-SoniaNeural"
VOICE_AMERICAN = "en-US-JennyNeural"

# ====================== NAME TRIGGERS ======================
NAME_TRIGGERS = [
    "كريم",
    "عبد الكريم",
    "عبدالكريم",
    "karim",
    "abdelkarim",
    "abdlkarim",
    "abdlkrim",
    "abdulkarim",
    "abdel krim",
    "abdel-karim",
    "abd el karim",
]

# ====================== MESSAGES ======================
WELCOME_NEW_MEMBER = (
    "Welcome to the group! 👋\n"
    "Glad to have you here."
)

THANK_INVITATION = "Thank you for the invitation! 😊"

NAME_REPLIES = [
    "Thanks! 😊",
    "You're welcome!",
    "Appreciate it!",
    "Thanks a lot!",
    "Okay, noted 👍",
    "Thank you!",
]
