# app/core/router.py
from fastapi import FastAPI
from app.api.v1 import webhook
from app.api.v1 import vocab_test
from app.api.v1 import movie_redirect


def setup_router(app: FastAPI):
    app.include_router(webhook.router, prefix="/api/v1/webhook", tags=["Webhook"])
    app.include_router(vocab_test.router, prefix="/api/v1", tags=["VocabTest"])
    app.include_router(movie_redirect.router, prefix="/api/v1")
