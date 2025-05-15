# app/services/platforms/line/bots/lexium/handlers.py
import asyncio
from datetime import datetime, timedelta, timezone
from google.cloud import firestore
from linebot.models import TextSendMessage, TemplateSendMessage, ConfirmTemplate, MessageAction
from app.services.platforms.line.bots.lexium.movie_service import fetch_next_movie
from app.core.firebase import get_db
from app.core.config import settings
import random

# ──────────────────────────────
# タイムゾーン定義
# ──────────────────────────────
JST = timezone(timedelta(hours=9))

# ──────────────────────────────
# ロック制御（ユーザー単位）
# ──────────────────────────────
user_locks: dict[str, asyncio.Lock] = {}

async def acquire_user_lock(user_id: str):
    lock = user_locks.setdefault(user_id, asyncio.Lock())
    await lock.acquire()

def release_user_lock(user_id: str):
    lock = user_locks.get(user_id)
    if lock and lock.locked():
        lock.release()

# ──────────────────────────────
# 共通ヘルパ
# ──────────────────────────────
def ensure_user_doc(db, user_id: str):
    user_ref = db.collection("users").document(user_id)
    if not user_ref.get().exists:
        user_ref.set({
            "mastered_level": 0,
            "last_sent_movie_sequence": 0,
            "created_at": firestore.SERVER_TIMESTAMP,
            "updated_at": firestore.SERVER_TIMESTAMP,
        }, merge=True)

def can_ask_today(udata: dict | None) -> bool:
    if not udata:
        return True
    ts = udata.get("last_quiz_at")
    if not ts:
        return True
    last_day = ts.astimezone(JST).date()
    return last_day < datetime.now(JST).date()


def touch_last_quiz_at(db, user_id: str, word_id: str):
    uref = db.collection("users").document(user_id).collection("words").document(word_id)
    uref.set({"last_quiz_at": firestore.SERVER_TIMESTAMP}, merge=True)

# ──────────────────────────────
# クイズ出題
# ──────────────────────────────
async def handle_quiz_command(reply_token, line_bot_api, user_id):
    await acquire_user_lock(user_id)
    try:
        db = get_db()
        ensure_user_doc(db, user_id)

        user_words_ref = db.collection("users").document(user_id).collection("words")
        user_word_map = {d.id: d.to_dict() for d in user_words_ref.stream()}
        all_word_ids = [d.id for d in db.collection("words").stream()]

        p1, p2, p3 = [], [], []
        for wid in all_word_ids:
            if not can_ask_today(user_word_map.get(wid)):
                continue
            udata = user_word_map.get(wid)
            if not udata:
                p2.append(wid); continue
            if udata.get("learned_via_movie"):
                p1.append(wid); continue
            s = udata.get("status")
            if s == "missed":
                p2.append(wid)
            elif s == "learning":
                p3.append(wid)

        for group in [p1, p2, p3]:
            if group:
                chosen_id = random.choice(group)
                break
        else:
            line_bot_api.reply_message(reply_token, TextSendMessage(text="出題できる単語が見つかりませんでした。"))
            return

        wdoc = db.collection("words").document(chosen_id).get()
        if not wdoc.exists:
            line_bot_api.reply_message(reply_token, TextSendMessage(text="単語データが見つかりませんでした。"))
            return

        wdata = wdoc.to_dict()
        meanings = wdata.get("meanings", [])
        if not meanings:
            line_bot_api.reply_message(reply_token, TextSendMessage(text="出題情報が不足しています。"))
            return

        ustatus = user_word_map.get(chosen_id, {}).get("status")
        item = meanings[1] if len(meanings) == 2 and ustatus == "learning" else meanings[0]
        phrase = item.get("collocation_phrase") or f"（例文なし）{chosen_id}"

        touch_last_quiz_at(db, user_id, chosen_id)

        quiz_msg = TemplateSendMessage(
            alt_text=f"【問題】{phrase}",
            template=ConfirmTemplate(
                text=f"【問題】{phrase}",
                actions=[
                    MessageAction(label="○", text=f"ok|{chosen_id}"),
                    MessageAction(label="✕", text=f"ng|{chosen_id}")
                ]
            )
        )
        line_bot_api.reply_message(reply_token, quiz_msg)

    finally:
        release_user_lock(user_id)

# ──────────────────────────────
# クイズ回答
# ──────────────────────────────
async def handle_quiz_action(message_text, reply_token, line_bot_api, user_id):
    db = get_db()
    ensure_user_doc(db, user_id)

    action, word_id = message_text.split("|", 1)

    # ── 単語マスタ取得 ───────────────────────
    wdoc = db.collection("words").document(word_id).get()
    if not wdoc.exists:
        line_bot_api.reply_message(reply_token, TextSendMessage(text="単語情報取得エラー"))
        return
    wdata = wdoc.to_dict()
    meanings = wdata.get("meanings", [])

    # ── ユーザー単語ステータス取得 ────────────
    uref = (
        db.collection("users")
        .document(user_id)
        .collection("words")
        .document(word_id)
    )
    udoc = uref.get()
    udata = udoc.to_dict() if udoc.exists else {}
    current_status = udata.get("status")

    # 🔒 すでに learning で「当日回答済み」なら無視
    if current_status == "learning" and not can_ask_today(udata):
        line_bot_api.reply_message(
            reply_token,
            TextSendMessage(text="この問題はすでに回答済みです。次の問題をお待ちください。"),
        )
        return

    # 🔒 すでに mastered 済みの単語にも無視
    if current_status == "mastered":
        line_bot_api.reply_message(
            reply_token,
            TextSendMessage(text="この単語はすでにマスター済みです。"),
        )
        return

    # ── 翻訳選択 ─────────────────────────────
    idx = 1 if len(meanings) == 2 and current_status == "learning" else 0
    trans = (
        meanings[idx].get("collocation_translation", "（訳なし）")
        if meanings
        else "（訳情報なし）"
    )

    # ステータス遷移
    if action == "ng":
        new_status = "missed"
        extra = {"learned_via_movie": False}  # ← ここを追加
    elif action == "ok":
        new_status = "learning" if current_status in [None, "missed"] else "mastered"
        extra = {}
    else:
        new_status = current_status
        extra = {}

    # Firestore 更新
    uref.set(
        {
            "status": new_status,
            "last_quiz_at": firestore.SERVER_TIMESTAMP,
            "updated_at": firestore.SERVER_TIMESTAMP,
            **extra  # ← ここで含める
        },
        merge=True,
    )

    # ── 返信メッセージ構築 ───────────────────
    msgs = []
    if action == "ng":
        msgs.append(TextSendMessage(text=f"【和訳】{trans}"))

    next_q = await build_next_quiz_message(db, user_id, exclude_ids={word_id})
    msgs.append(
        next_q
        if next_q
        else TextSendMessage(text="出題できる単語が見つかりませんでした。")
    )
    line_bot_api.reply_message(reply_token, msgs)


# ──────────────────────────────
# 次問生成
# ──────────────────────────────
async def build_next_quiz_message(db, user_id, exclude_ids: set[str] | None = None):
    exclude_ids = exclude_ids or set()

    user_words_ref = db.collection("users").document(user_id).collection("words")
    u_map = {d.id: d.to_dict() for d in user_words_ref.stream()}
    all_ids = [d.id for d in db.collection("words").stream()]

    p1, p2, p3 = [], [], []
    for wid in all_ids:
        if wid in exclude_ids or not can_ask_today(u_map.get(wid)):
            continue
        u = u_map.get(wid)
        if not u:
            p2.append(wid); continue
        if u.get("learned_via_movie"):
            p1.append(wid); continue
        s = u.get("status")
        if s == "missed":
            p2.append(wid)
        elif s == "learning":
            p3.append(wid)

    for grp in (p1, p2, p3):
        if grp:
            cid = random.choice(grp)
            break
    else:
        return None

    wdoc = db.collection("words").document(cid).get()
    if not wdoc.exists:
        return None
    wdata = wdoc.to_dict()
    meanings = wdata.get("meanings", [])
    if not meanings:
        return None

    ustat = u_map.get(cid, {}).get("status")
    item = meanings[1] if len(meanings) == 2 and ustat == "learning" else meanings[0]
    phrase = item.get("collocation_phrase") or f"（例文なし）{cid}"
    touch_last_quiz_at(db, user_id, cid)

    return TemplateSendMessage(
        alt_text=f"【問題】{phrase}",
        template=ConfirmTemplate(
            text=f"【問題】{phrase}",
            actions=[
                MessageAction(label="○", text=f"ok|{cid}"),
                MessageAction(label="✕", text=f"ng|{cid}")
            ]
        )
    )


# --------------------------------------------------
# 動画コマンド
# --------------------------------------------------

async def handle_movie_command(user_id, reply_token, line_bot_api):
    db = get_db()
    ensure_user_doc(db, user_id)

    result = fetch_next_movie(user_id, db)
    if result:
        movie_id, _ = result
        url = f"{settings.fastapi_url}/api/v1/redirect/movie?user_id={user_id}&movie_id={movie_id}"
        line_bot_api.reply_message(reply_token, TextSendMessage(text=url))
    else:
        line_bot_api.reply_message(reply_token, TextSendMessage(text="すべての動画を学習済みです。次の動画追加をお待ちください。"))

# --------------------------------------------------
# 過去動画リンク送信 (past)
# --------------------------------------------------

async def handle_past_movies_command(user_id, reply_token, line_bot_api):
    db = get_db()
    ensure_user_doc(db, user_id)

    user_ref = db.collection("users").document(user_id)
    udata = (user_ref.get().to_dict() or {})
    mastered_level = udata.get("mastered_level", 0)
    last_seq = udata.get("last_sent_movie_sequence", 0)

    # ── 対象動画を取得 ─────────────────────────
    movies_ref = db.collection("movies")
    q = (
        movies_ref
        .where("level", "==", int(mastered_level + 1))
        .where("sequence", "<=", last_seq)
        .order_by("sequence")
    )

    movie_docs = list(q.stream())
    if not movie_docs:
        line_bot_api.reply_message(reply_token, TextSendMessage(text="過去動画はありません。"))
        return

    # ── 1URLずつ送信 ───────────────────────────
    first = True
    for m in movie_docs:
        url   = f"{settings.fastapi_url}/api/v1/redirect/movie?user_id={user_id}&movie_id={m.id}"

        if first:
            line_bot_api.reply_message(reply_token, TextSendMessage(text=url))
            first = False
        else:
            line_bot_api.push_message(user_id, TextSendMessage(text=url))

# --------------------------------------------------
# 進捗表示 (progress)
# --------------------------------------------------

async def handle_progress_command(user_id, reply_token, line_bot_api):
    db = get_db()
    ensure_user_doc(db, user_id)

    # ── ランク名テーブル ──────────────────────────
    TITLES = [
        "ルーキー", "アイアン", "ブロンズ", "シルバー",
        "ゴールド", "プラチナ", "ダイヤモンド", "マスター"
    ]

    # ── ユーザーデータ ────────────────────────────
    user_ref = db.collection("users").document(user_id)
    udoc = user_ref.get()
    if not udoc.exists:
        line_bot_api.reply_message(reply_token,
            TextSendMessage(text="ユーザー情報が取得できませんでした。"))
        return

    udata = udoc.to_dict() or {}
    level = udata.get("mastered_level", 0)     # 0–7
    display_level = level + 1                  # 1–8
    rank_name = TITLES[level]                  # ランク名

    start = level * 400 + 1
    end   = min((level + 1) * 400, 2_807)

    # ── レベル内単語総数 ───────────────────────────
    lvl_ids = {
        doc.id
        for doc in db.collection("words")
            .where("frequency_rank", ">=", start)
            .where("frequency_rank", "<=", end)
            .stream()
    }
    total = len(lvl_ids)
    if total == 0:
        line_bot_api.reply_message(reply_token,
            TextSendMessage(text="対象レベルの語彙データがありません。"))
        return

    # ── ユーザー単語ステータス ─────────────────────
    mastered = learning = 0
    for d in user_ref.collection("words") \
            .where("status", "in", ["learning", "mastered"]).stream():
        if d.id in lvl_ids:
            st = d.to_dict().get("status")
            if st == "mastered":  mastered += 1
            elif st == "learning": learning += 1

    score = mastered + learning * 0.5
    pct = round(score / total * 100, 1)

    msg = (
        f"📊 進捗状況 〈Lv{display_level} – {rank_name}〉\n\n"
        f"mastered : {mastered}/{total}\n"
        f"learning : {learning}/{total}\n"
        f"進捗率 : {pct}%"
    )
    line_bot_api.reply_message(reply_token, TextSendMessage(text=msg))

# --------------------------------------------------
# ヘルプ (help)
# --------------------------------------------------

async def handle_help_command(reply_token, line_bot_api):
    # ── 1通目：アプリのコンセプト ─────────────────────────
    intro = (
        "📚 Lexium へようこそ！\n\n"
        "このアプリは ①YouTube動画での単語インプット と "
        "②LINE Bot クイズでのアウトプット を繰り返して、\n"
        "NGSL（New General Service List）全 2,807 語──"
        "日常英会話の約 92% をカバー──を習得することがゴールです。\n\n"
        "▶︎ **動画で学習した単語** が優先的にクイズに出題されます。\n"
        "▶︎ **50 問ミスするごと** に、あなたが間違えた単語だけをまとめた"
        "復習動画が自動生成されるので効率的に弱点補強！\n\n"
        "今後は熟語・スラングのアップデートに加え、"
        "TOEIC 対策コースや映画対策コースも順次リリース予定です。"
    )

    # ── 2通目：コマンド一覧 ──────────────────────────────
    help_text = (
        "📘 利用できるコマンド\n\n"
        "quiz / start  : 単語問題を出題\n"
        "movie / learn : レベルに合った動画を送信\n"
        "past          : 過去に送った動画を一覧\n"
        "progress      : レベル内の学習進捗を表示\n"
        "help / ?      : このヘルプを表示"
    )

    # 2 メッセージをまとめて返信
    line_bot_api.reply_message(reply_token, [
        TextSendMessage(text=intro),
        TextSendMessage(text=help_text),
    ])
