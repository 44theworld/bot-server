from app.services.platforms.line.bots.lexium.service import handle_lexium_message

async def handle_line_message(body: dict):
    events = body.get("events", [])
    for event in events:
        bot_id = detect_line_bot_id(event)
        if bot_id == "lexium":
            await handle_lexium_message(event)
        else:
            pass

def detect_line_bot_id(event: dict) -> str:
    return "lexium"
