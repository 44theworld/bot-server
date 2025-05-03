from fastapi import FastAPI
from app.api.v1 import webhook

def setup_router(app: FastAPI):
    app.include_router(webhook.router, prefix="/api/v1/webhook", tags=["Webhook"])
