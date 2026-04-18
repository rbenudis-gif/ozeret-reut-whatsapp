"""
Configuration - loads all settings from environment variables.
"""

import os
from dotenv import load_dotenv

# Load .env with override to ensure values are always set
load_dotenv(override=True)

# Fallback: manually parse .env if dotenv missed any keys
_env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
if os.path.exists(_env_path):
    with open(_env_path) as _f:
        for _line in _f:
            _line = _line.strip()
            if _line and not _line.startswith("#") and "=" in _line:
                _k, _v = _line.split("=", 1)
                if not os.environ.get(_k.strip()):
                    os.environ[_k.strip()] = _v.strip()


class Settings:
    # Green API
    GREEN_API_URL: str = os.getenv("GREEN_API_URL", "https://api.green-api.com")
    GREEN_API_INSTANCE: str = os.getenv("GREEN_API_INSTANCE", "")
    GREEN_API_TOKEN: str = os.getenv("GREEN_API_TOKEN", "")

    # LLM
    LLM_MODEL: str = os.getenv("LLM_MODEL", "claude-haiku-4-5-20251001")

    # Agent
    SYSTEM_PROMPT: str = os.getenv("SYSTEM_PROMPT", """את העוזרת האישית של רעות בנודיס. את מכירה אותה טוב ומדברת איתה בלשון נקבה תמיד.

פרטים אישיים: שמה רעות, גרה ביבנה (פעמונית 23), נשואה לאלון (נולד 22.09.1971, נישאו 10.02.2005), שלוש בנות: נועם (25.08.2007), גל (31.07.2011), שקד (03.01.2013).

קריירה: 24 שנה בניהול רכש ובינוי בחברת אלבר (2001-2025). כרגע מחפשת עבודה בניהול רכש ושרשרת אספקה.

תחומי עניין: AI, עיצוב גרפי, Canva, כושר, אנגלית, אסטרולוגיה.

יומן ומייל: כשרעות מבקשת לתזמן פגישה, לבדוק את היומן, לשלוח מייל או לקרוא הודעות - תעזרי לה לנסח ולארגן, ותזכירי לה לבדוק ביומן Google ובג'ימייל שלה. בעתיד תחובר ישירות ליומן ולמייל.

סגנון: קליל וחברותי, כמו חברה טובה שמכירה אותה היטב. תמיד מדברת עברית. עוזרת לחשוב על רעיונות, נותנת תזכורות, ועונה על כל שאלה בכנות ובאהבה.""")

    MAX_HISTORY: int = int(os.getenv("MAX_HISTORY", "20"))

    # Owner phone number - only respond to messages from this number
    # Format: international without + (e.g. 972501234567)
    OWNER_PHONE: str = os.getenv("OWNER_PHONE", "")

    # Database
    DATABASE_PATH: str = os.getenv("DATABASE_PATH", "./conversations.db")


settings = Settings()
