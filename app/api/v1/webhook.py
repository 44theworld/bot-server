# app/api/v1/webhook.py
from fastapi import APIRouter, Request, Header, HTTPException, BackgroundTasks
from nacl.signing import VerifyKey
from nacl.exceptions import BadSignatureError
import os
import json

DISCORD_PUBLIC_KEY = os.getenv("DISCORD_PUBLIC_KEY")

router = APIRouter()

@router.post("/{platform}")
async def handle_webhook(
    platform: str,
    request: Request,
    background_tasks: BackgroundTasks,
    x_signature_ed25519: str = Header(None),
    x_signature_timestamp: str = Header(None),
):
    raw_body = await request.body()

    # Discordのみ署名検証を行う
    if platform == "discord":
        if not x_signature_ed25519 or not x_signature_timestamp:
            raise HTTPException(status_code=400, detail="Missing signature headers")

        message = x_signature_timestamp.encode() + raw_body

        try:
            verify_key = VerifyKey(bytes.fromhex(DISCORD_PUBLIC_KEY))
            verify_key.verify(message, bytes.fromhex(x_signature_ed25519))
        except BadSignatureError:
            raise HTTPException(status_code=401, detail="Invalid request signature")

        # DiscordのPING応答（interactionエンドポイント登録時の確認）
        body = json.loads(raw_body)
        if body.get("type") == 1:
            return {"type": 1}

    else:
        # Discord以外（LINEなど）は署名検証せずボディをパース
        body = json.loads(raw_body)

    # それ以外は通常処理へ
    from app.services.dispatcher import dispatch_message
    return await dispatch_message(platform, body, background_tasks)
