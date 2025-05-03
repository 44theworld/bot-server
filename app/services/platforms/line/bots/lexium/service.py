import random
from linebot import LineBotApi
from linebot.models import (
    TextSendMessage,
    TemplateSendMessage,
    ConfirmTemplate,
    MessageAction
)
import os

line_bot_api = LineBotApi(os.getenv("CHANNEL_ACCESS_TOKEN"))

SAMPLE_WORDS = [
    {"id": 1, "word": "achieve", "collocation": "achieve a goal", "translation": "目標を達成する"},
    {"id": 2, "word": "maintain", "collocation": "maintain balance", "translation": "バランスを維持する"},
    {"id": 3, "word": "create", "collocation": "create opportunities", "translation": "機会を作り出す"},
]

def get_question_by_id(word_id):
    for word in SAMPLE_WORDS:
        if word["id"] == word_id:
            return word
    return None

async def handle_lexium_message(event):
    message_text = event["message"]["text"]
    reply_token = event["replyToken"]
    user_id = event["source"]["userId"]

    # 最初の出題（イベントがpostbackじゃなく、普通のメッセージだったら）
    if not ("ok|" in message_text or "ng|" in message_text):
        await send_question(reply_token)
        return

    # ユーザーが〇✕ボタンを押したとき
    action, word_id_str = message_text.split("|")
    word_id = int(word_id_str)
    word = get_question_by_id(word_id)

    messages = []

    if action == "ng":
        # 間違えたときだけ、和訳を先にリプライ
        messages.append(TextSendMessage(text=f"【和訳】{word['translation']}"))

    # 次の問題を送る
    question = random.choice(SAMPLE_WORDS)
    messages.append(
        TemplateSendMessage(
            alt_text="次の問題に答えてください",
            template=ConfirmTemplate(
                text=f"{question['collocation']}",
                actions=[
                    MessageAction(label="〇", text=f"ok|{question['id']}"),
                    MessageAction(label="✕", text=f"ng|{question['id']}")
                ]
            )
        )
    )

    line_bot_api.reply_message(reply_token, messages)

async def send_question(reply_token):
    question = random.choice(SAMPLE_WORDS)
    line_bot_api.reply_message(
        reply_token,
        TemplateSendMessage(
            alt_text="問題に答えてください",
            template=ConfirmTemplate(
                text=f"【問題】{question['collocation']}",
                actions=[
                    MessageAction(label="〇", text=f"ok|{question['id']}"),
                    MessageAction(label="✕", text=f"ng|{question['id']}")
                ]
            )
        )
    )
