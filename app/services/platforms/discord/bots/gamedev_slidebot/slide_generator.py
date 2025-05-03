# app/services/platforms/discord/bots/gamedev_slidebot/slide_generator.py
from app.core.config import settings
from google.oauth2 import service_account
from googleapiclient.discovery import build

from app.services.clients.chatgpt_client import ChatGPTClient
import logging
import re

class SlideGenerator:
    def __init__(self):
        self.credentials = service_account.Credentials.from_service_account_info(
            settings.google_service_account_info,
            scopes=[
                "https://www.googleapis.com/auth/presentations",
                "https://www.googleapis.com/auth/drive"
            ]
        )
        self.service = build('slides', 'v1', credentials=self.credentials)
        self.drive_service = build('drive', 'v3', credentials=self.credentials)
        self.chatgpt_client = ChatGPTClient()

    async def create_slide_from_memo(self, memo: str) -> str:
        # ① ChatGPTでMarkdownを作成
        markdown = await self.chatgpt_client.generate_slide_markdown(memo)

        # ② Markdownをパース（タイトルスライドを分離）
        slides_content = []
        current_slide = {}
        lines = markdown.splitlines()

        title_slide_title = "GameDev Idea"
        if lines and lines[0].startswith("# "):
            title_slide_title = lines[0][2:].strip()
            lines = lines[1:]

        for line in lines:
            line = line.strip()
            if line.startswith("## "):
                if current_slide:
                    slides_content.append(current_slide)
                current_slide = {"title": line[3:], "body": ""}
            else:
                if current_slide:
                    current_slide["body"] += line + "\n"
        if current_slide:
            slides_content.append(current_slide)

        # ファイル名に使えるようにスライドタイトルをサニタイズ
        safe_title = re.sub(r'[\\/*?:"<>|]', "", title_slide_title)

        # ③ 新しいGoogleスライドを作成（タイトルを使用）
        presentation = self.service.presentations().create(body={
            'title': safe_title
        }).execute()
        presentation_id = presentation['presentationId']

        # ④ 公開設定
        self.drive_service.permissions().create(
            fileId=presentation_id,
            body={
                'role': 'writer',
                'type': 'anyone',
                'allowFileDiscovery': False
            }
        ).execute()

        # ⑤ 本文スライドを追加（1ページ目は作成済みのタイトルスライドを利用）
        requests = []
        object_ids = []
        for i, slide in enumerate(slides_content):
            slide_id = f"slide_{i+1}"  # +1して1ページ目と重複しないように
            object_ids.append(slide_id)
            requests.append({
                'createSlide': {
                    'objectId': slide_id,
                    'slideLayoutReference': {
                        'predefinedLayout': 'TITLE_AND_BODY'
                    }
                }
            })

        # スライド作成
        if requests:
            self.service.presentations().batchUpdate(
                presentationId=presentation_id,
                body={'requests': requests}
            ).execute()

        # ⑥ 各スライドにタイトルと本文を設定
        presentation = self.service.presentations().get(
            presentationId=presentation_id
        ).execute()
        all_slides = presentation.get("slides", [])

        requests = []

        # ⑥-1 タイトルスライド（1枚目）にタイトルを挿入
        if all_slides:
            title_slide_shapes = [el for el in all_slides[0].get("pageElements", []) if "shape" in el]
            if len(title_slide_shapes) >= 1:
                title_id = title_slide_shapes[0]["objectId"]
                requests.append({
                    'insertText': {
                        'objectId': title_id,
                        'text': title_slide_title,
                        'insertionIndex': 0
                    }
                })

        # ⑥-2 本文スライドに内容を挿入
        target_slides = all_slides[1:1+len(slides_content)]  # 2ページ目以降が対象
        for i, slide in enumerate(target_slides):
            shapes = [el for el in slide.get("pageElements", []) if "shape" in el]
            if len(shapes) >= 1:
                title_id = shapes[0]["objectId"]
                requests.append({
                    'insertText': {
                        'objectId': title_id,
                        'text': slides_content[i]["title"],
                        'insertionIndex': 0
                    }
                })
            if len(shapes) >= 2:
                body_id = shapes[1]["objectId"]
                requests.append({
                    'insertText': {
                        'objectId': body_id,
                        'text': slides_content[i]["body"],
                        'insertionIndex': 0
                    }
                })

        if requests:
            self.service.presentations().batchUpdate(
                presentationId=presentation_id,
                body={'requests': requests}
            ).execute()

        return f"https://docs.google.com/presentation/d/{presentation_id}/edit"
