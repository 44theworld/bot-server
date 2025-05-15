# app/services/platforms/line/bots/lexium/models.py
from pydantic import BaseModel, Field
from typing import Any, List, Literal, Optional


class UserDoc(BaseModel):
    mastered_level: int = 0
    last_sent_movie_sequence: int = 0
    line_user_id: Optional[str] = None
    created_at: Optional[object] = Field(default=None, exclude=True)
    updated_at: Optional[object] = Field(default=None, exclude=True)

    def firestore_dict(self) -> dict:
        return self.model_dump(exclude_none=True)


class UserWordDoc(BaseModel):
    status: Optional[Literal["missed", "learning", "mastered"]] = None
    correct_count: int = 0
    learned_via_movie: Optional[bool] = False
    last_quiz_at: Optional[Any] = None
    updated_at: Optional[Any] = Field(default=None, exclude=True)

class MovieDoc(BaseModel):
    youtube_url: str
    level: int
    sequence: int
    word_ids: List[str]
    type: Literal["public", "customized"] = "public"
    user_id: Optional[str] = None

    def firestore_dict(self) -> dict:
        return self.model_dump(exclude_none=True)
