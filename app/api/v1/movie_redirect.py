# app/api/v1/movie_redirect.py
from fastapi import APIRouter, Query, HTTPException
from fastapi.responses import RedirectResponse
from app.core.firebase import get_db
from app.services.platforms.line.bots.lexium.models import MovieDoc
from google.cloud import firestore

router = APIRouter()

@router.get("/redirect/movie")
async def redirect_to_movie(user_id: str = Query(...), movie_id: str = Query(...)):
    db = get_db()

    user_ref = db.collection("users").document(user_id)
    user_doc = user_ref.get()
    if not user_doc.exists:
        raise HTTPException(status_code=404, detail="User not found")

    # 動画取得
    movie_ref = db.collection("movies").document(movie_id)
    movie_snap = movie_ref.get()
    if not movie_snap.exists:
        raise HTTPException(status_code=404, detail="Movie not found")

    movie: MovieDoc = movie_snap.to_dict()
    word_ids = movie.get("word_ids", [])
    youtube_url = movie.get("youtube_url")
    if not youtube_url:
        raise HTTPException(status_code=500, detail="YouTube URL missing")

    # 単語ステータス更新
    batch = db.batch()
    for word in word_ids:
        word_ref = user_ref.collection("words").document(word)
        batch.set(word_ref, {
            "learned_via_movie": True,
            "updated_at": firestore.SERVER_TIMESTAMP,
        }, merge=True)
    batch.commit()

    return RedirectResponse(url=youtube_url)
