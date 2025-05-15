# app/services/platforms/line/bots/lexium/movie_service.py
from google.cloud import firestore
from .models import MovieDoc, UserDoc

def fetch_next_movie(user_id: str, db: firestore.Client) -> tuple[str, MovieDoc] | None:
    transaction = db.transaction()
    users_ref = db.collection("users")
    movies_ref = db.collection("movies")

    @firestore.transactional
    def run_in_transaction(tx: firestore.Transaction) -> tuple[str, MovieDoc] | None:
        # ドキュメントIDでユーザー取得
        user_ref = users_ref.document(user_id)
        user_doc = user_ref.get(transaction=tx)
        if not user_doc.exists:
            return None

        user_data: UserDoc = user_doc.to_dict()  # type: ignore
        mastered = user_data.get("mastered_level", 0)
        last_seq = user_data.get("last_sent_movie_sequence", 0)

        # 次に送るべき動画を取得
        query = (
            movies_ref
            .where("level", ">", mastered)
            .order_by("level")
            .order_by("sequence")
            .limit(10)
        )

        for movie_snap in query.stream(transaction=tx):
            movie_data = movie_snap.to_dict()
            if movie_data.get("sequence", 0) > last_seq:
                tx.update(user_ref, {
                    "last_sent_movie_sequence": movie_data["sequence"],
                    "updated_at": firestore.SERVER_TIMESTAMP,
                })
                return movie_snap.id, MovieDoc(**movie_data)

        return None

    return run_in_transaction(transaction)

