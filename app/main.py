from fastapi import FastAPI
from app.core.router import setup_router


app = FastAPI()

setup_router(app)

@app.get("/")
def read_root():
    return {"Hello": "World"}