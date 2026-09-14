import os
from dotenv import load_dotenv

load_dotenv()

# =========================
# BOT SETTINGS
# =========================

BOT_TOKEN = os.getenv("BOT_TOKEN", "")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
OWNER_ID = int(os.getenv("OWNER_ID", "0"))

BOT_NAME = "Abdelkarim"
BOT_USERNAME = "AbdelkarimBot"

MAX_WORDS = 250

# =========================
# VOICES
# =========================

VOICE_AMERICAN = "en-US-JennyNeural"
VOICE_BRITISH = "en-GB-SoniaNeural"

# =========================
# GROUP SETTINGS
# =========================

ALLOWED_GROUP_IDS = set()

WELCOME_NEW_MEMBER = (
    "Welcome to the group! 👋\n"
    "Glad to have you here. 🇬🇧"
)

THANK_INVITATION = "Thank you for the invitation! 😊"

# =========================
# NAME TRIGGERS
# =========================

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

# =========================
# REPLIES WHEN NAME IS MENTIONED
# =========================

NAME_REPLIES = [
    "Abdelkarim wishes you peace, happiness, and a heart full of contentment. 🤍",
    "May you always find peace in your heart, clarity in your mind, and goodness in your life. 🌿",
    "Abdelkarim wishes you a beautiful life filled with peace, blessings, and good moments. 🤲",
    "May your heart always be at peace, your days be bright, and your path be filled with goodness. ✨",
    "May Allah bless you with peace of mind, a pure heart, and a life full of blessings. 🤍",
    "Abdelkarim wishes you comfort after every hardship and happiness after every difficult day. 🌷",
    "May Allah grant you peace in your heart, strength in your soul, and blessings in everything you do. 🤲",
    "May your heart remain pure, your soul remain peaceful, and your future be filled with beautiful things. 🌿",
    "Abdelkarim wishes you happiness that reaches your heart and peace that stays with you. 🤍",
    "May Allah fill your life with goodness, your heart with tranquility, and your days with blessings. ✨",
    "May you always have a reason to smile, a heart that feels at peace, and a life full of goodness and blessings. 🌸",
    "Abdelkarim wishes you a peaceful heart, a clear mind, and beautiful days ahead. 🌅",
    "May Allah protect you, guide you, and bless you with everything that is good for you. 🤲",
    "May every worry leave your heart, every difficulty become easier, and every new day bring you goodness. 🌿",
    "Abdelkarim wishes you inner peace, sincere happiness, and a future brighter than you imagine. ✨",
    "May Allah grant you comfort, patience, happiness, and peace of heart wherever you are. 🤍",
    "May your days be gentle, your heart be calm, and your life be surrounded by goodness and kind people. 🌷",
    "Abdelkarim wishes you a peaceful soul, a hopeful heart, and many beautiful moments in your life. 🌸",
    "May Allah turn your worries into relief, your difficulties into ease, and your hopes into beautiful realities. 🤲",
    "May peace fill your heart, blessings fill your life, and goodness follow you wherever you go. 🤍",
]

# =========================
# GEMINI
# =========================

GEMINI_MODEL = os.getenv(
    "GEMINI_MODEL",
    "gemini-2.5-flash"
)
