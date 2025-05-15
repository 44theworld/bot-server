from fastapi import APIRouter, HTTPException, Query
from firebase_admin import firestore
from app.core.firebase import get_db
import secrets

router = APIRouter()
db = get_db()

def generate_short_id(length: int = 8) -> str:
    while True:
        doc_id = secrets.token_urlsafe(length)[:length]
        if not db.collection("users").document(doc_id).get().exists:
            return doc_id

@router.post("/vocab-test/submit")
def submit(data: dict):
    mastered_level = data.get("mastered_level")
    line_user_id   = data.get("line_user_id")

    if mastered_level is None or line_user_id is None:
        raise HTTPException(status_code=400, detail="mastered_level and line_user_id are required")

    # ❶ line_user_id 検索（最大 1 件）
    existing = next(
        db.collection("users")
          .where("line_user_id", "==", line_user_id)
          .limit(1)
          .stream(),
        None
    )

    now = firestore.SERVER_TIMESTAMP
    payload = {
        "mastered_level": mastered_level,
        "last_sent_movie_sequence": 0,
        "line_user_id": line_user_id,
        "updated_at": now,
    }

    if existing:
        # ❷ 更新
        user_id = existing.id
        db.collection("users").document(user_id).update(payload)
    else:
        # ❸ 新規
        user_id = generate_short_id()
        payload["created_at"] = now
        db.collection("users").document(user_id).set(payload)

    return {"status": "ok", "user_id": user_id}

@router.get("/vocab-test/user-status")
def get_user_status(line_user_id: str = Query(...)):
    doc = next(
        db.collection("users")
          .where("line_user_id", "==", line_user_id)
          .limit(1)
          .stream(),
        None
    )
    if not doc:
        return {"mastered_level": None}

    return {"mastered_level": doc.to_dict().get("mastered_level")}
