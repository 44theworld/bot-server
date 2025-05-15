# app/main.py
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
import app.core.firebase
from app.core.router import setup_router
import os

app = FastAPI()
STATIC_DIR = os.path.join(os.path.dirname(__file__), "static")
app.mount("/liff", StaticFiles(directory=os.path.join(STATIC_DIR, "liff")), name="liff")

setup_router(app)