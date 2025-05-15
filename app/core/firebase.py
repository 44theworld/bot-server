# app/core/firebase.py
import firebase_admin
from firebase_admin import credentials, firestore
from app.core.config import settings

# アプリ初期化（既存のコード）
cred = credentials.Certificate(settings.firebase_api_key)
firebase_admin.initialize_app(cred)

# 追加：Firestore クライアントを取得する関数
def get_db():
    return firestore.client()
