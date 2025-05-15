# app/core/config.py
import os
import json
from dotenv import load_dotenv

load_dotenv()

class Settings:
    # OpenRouter (ChatGPT API)
    openrouter_api_key: str = os.getenv("OPENROUTER_API_KEY")

    # Google Slides: Cloud Run では JSON 文字列から、ローカルではファイルから読み込み
    if os.getenv("SLIDE_CREDENTIALS"):
        google_service_account_info: dict = json.loads(os.getenv("SLIDE_CREDENTIALS"))
    else:
        with open(os.getenv("SLIDE_ACCOUNT_FILE", "secret/google-slide-key.json"), encoding="utf-8") as f:
            google_service_account_info: dict = json.load(f)

    google_template_presentation_id: str = os.getenv("GOOGLE_TEMPLATE_PRESENTATION_ID")

    # Firebase
    if os.getenv("FIREBASE_CREDENTIALS"):
        firebase_api_key: dict = json.loads(os.getenv("FIREBASE_CREDENTIALS"))
    else:
        with open(os.getenv("FIREBASE_ACCOUNT_FILE", "secret/firebase-key.json"), encoding="utf-8") as f:
            firebase_api_key: dict = json.load(f)

    # JWT
    jwt_secret: str = os.getenv("JWT_SECRET")

    # Level Check Url
    level_check_liff_id: str = os.getenv("LEVEL_CHECK_LIFF_ID")

    # FastAPI Url
    fastapi_url: str = os.getenv("FASTAPI_URL")

settings = Settings()

