# app/core/config.py
import os
from dotenv import load_dotenv
import json

load_dotenv()

class Settings:
    # OpenRouter (ChatGPT API)
    openrouter_api_key: str = os.getenv("OPENROUTER_API_KEY")

    # Google Slides
    google_service_account_info: dict = json.loads(os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON"))
    google_template_presentation_id: str = os.getenv("GOOGLE_TEMPLATE_PRESENTATION_ID")

settings = Settings()
