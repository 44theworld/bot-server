# app/services/platforms/discord/bots/gamedev_slidebot/service.py

import httpx
from fastapi import BackgroundTasks
from app.services.platforms.discord.bots.gamedev_slidebot.slide_generator import SlideGenerator


def handle_gamedev_slide_command(
    data: dict,
    interaction_id: str,
    interaction_token: str,
    application_id: str,
    background_tasks: BackgroundTasks
):
    # 即時に Discord に defer 応答（ACK）
    deferred_response = {
        "type": 5  # DEFERRED_CHANNEL_MESSAGE_WITH_SOURCE
    }

    options = data.get("options", [])
    memo_text = next((opt["value"] for opt in options if opt["name"] == "memo"), "")

    # バックグラウンドで実行
    background_tasks.add_task(process_later, memo_text, interaction_id, interaction_token, application_id)

    return deferred_response

async def process_later(memo_text: str, interaction_id: str, interaction_token: str, application_id: str):

    generator = SlideGenerator()
    slide_url = await generator.create_slide_from_memo(memo_text)

    followup_url = f"https://discord.com/api/v10/webhooks/{application_id}/{interaction_token}"
    async with httpx.AsyncClient() as client:
        res = await client.post(followup_url, json={
            "content": f"✅ スライド作成完了！\n{slide_url}"
        })
