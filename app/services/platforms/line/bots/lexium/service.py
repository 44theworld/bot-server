# app/services/platforms/line/bots/lexium/service.py
from app.core.firebase import get_db
from google.cloud import firestore
from linebot import LineBotApi
from linebot.models import TextSendMessage
from app.services.platforms.line.bots.lexium import handlers
from app.core.config import settings
import os

line_bot_api = LineBotApi(os.getenv("CHANNEL_ACCESS_TOKEN"))

async def handle_lexium_message(event):
    message_text = event["message"]["text"].strip().lower()
    reply_token = event["replyToken"]
    line_user_id = event["source"]["userId"]  # LINEのユーザーID

    db = get_db()

    # Firestoreでline_user_idに紐づくuser_idを取得
    users_ref = db.collection("users")
    query = users_ref.where("line_user_id", "==", line_user_id).limit(1)
    docs = list(query.stream())

    if not docs:
        line_bot_api.reply_message(
            reply_token,
            TextSendMessage(text=f"まだ初回のレベルチェックが完了していません。以下のリンクからレベルチェックを行ってください。\n\nhttps://miniapp.line.me/{settings.level_check_liff_id}")
        )
        return

    user_doc = docs[0]
    user_id = user_doc.id  # ドキュメントIDとして使うuser_id

    # コマンドルーティング
    if message_text in ["quiz", "start"]:
        await handlers.handle_quiz_command(reply_token, line_bot_api, user_id)
    elif message_text in ["movie", "learn"]:
        await handlers.handle_movie_command(user_id, reply_token, line_bot_api)
    elif message_text in ["past", "history", "watched"]:
        await handlers.handle_past_movies_command(user_id, reply_token, line_bot_api)
    elif message_text in ["progress", "status"]:
        await handlers.handle_progress_command(user_id, reply_token, line_bot_api)
    elif message_text in ["help", "?"]:
        await handlers.handle_help_command(reply_token, line_bot_api)
    elif message_text.startswith(("ok|", "ng|")) and "|" in message_text:
        await handlers.handle_quiz_action(message_text, reply_token, line_bot_api, user_id)
    else:
        line_bot_api.reply_message(
            reply_token,
            TextSendMessage(text="コマンドが見つかりませんでした。`help` と送って使い方を確認してください。")
        )
