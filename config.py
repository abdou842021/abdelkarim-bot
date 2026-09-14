import os

BOT_TOKEN = os.getenv("BOT_TOKEN", "YOUR_BOT_TOKEN_HERE")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "YOUR_GEMINI_API_KEY_HERE")
OWNER_ID = int(os.getenv("OWNER_ID", "123456789"))

# مجموعات مفعلة مبدئياً
ALLOWED_GROUP_IDS = set()

# إعدادات عامة
MAX_WORDS = 50
VOICE_AMERICAN = "en-US-AriaNeural"
VOICE_BRITISH = "en-GB-SoniaNeural"
WELCOME_NEW_MEMBER = "Welcome to the group! 🎉 Enjoy learning English with us."
