# app/services/platforms/discord/handler.py

from fastapi import BackgroundTasks
from app.services.platforms.discord.bots.gamedev_slidebot.service import handle_gamedev_slide_command

async def handle_discord_message(body: dict, background_tasks: BackgroundTasks):
    if body.get("type") == 1:
        return {"type": 1}

    data = body.get("data", {})
    command_name = data.get("name")
    bot_id = detect_discord_bot_id(data)

    if bot_id == "gamedev_slidebot":
        interaction_id = body.get("id")
        interaction_token = body.get("token")
        application_id = body.get("application_id")
        return handle_gamedev_slide_command(data, interaction_id, interaction_token, application_id, background_tasks)
    else:
        return {"type": 4, "data": {"content": "Unknown command."}}

def detect_discord_bot_id(data: dict) -> str:
    return "gamedev_slidebot"
