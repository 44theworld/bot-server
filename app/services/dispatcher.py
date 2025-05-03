# app/services/dispatcher.py

from app.services.platforms.line.handler import handle_line_message
from app.services.platforms.discord.handler import handle_discord_message

from fastapi import BackgroundTasks

async def dispatch_message(platform: str, body: dict, background_tasks: BackgroundTasks):
    """
    受け取ったリクエストをプラットフォームごとに適切なhandlerに振り分ける
    """
    print(f"Dispatching message for platform: {platform}")
    if platform == "line":
        await handle_line_message(body)
    elif platform == "discord":
        return await handle_discord_message(body, background_tasks)
    else:
        raise ValueError(f"Unsupported platform: {platform}")
