# app/services/clients/chatgpt_client.py
from app.core.config import settings
from openai import AsyncOpenAI
import logging

class ChatGPTClient:
    def __init__(self):
        self.client = AsyncOpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=settings.openrouter_api_key,
        )

    async def generate_slide_markdown(self, memo: str) -> str:
        prompt = f"""
あなたはゲーム企画書を作成するプロのライターです。

以下のメモから、Googleスライドにそのまま貼り付けることを前提としたMarkdown形式の原稿を作成してください。

- 出力形式はMarkdownとし、1行目には「# ◯◯」という形式で、企画書のタイトルを記載してください（例: # 新作ゲーム企画「ソウルリンク」）。
- その後、「## スライドタイトル」から始まる各セクションで1スライドを表してください。
- 各スライドのタイトルは、**「スライドタイトル：概要」や「タイトル：目的」のようにラベルを含めず、タイトルそのものだけ**を簡潔に記載してください（例: ## ゲームの目的、## プレイ体験、## 市場性 など）。
- 各スライドには、タイトル（##）と簡潔な本文（2〜5行）を含めてください。
- 全体で6〜8スライドに収めてください（タイトルスライドを含む）。
- 本文中にMarkdownのリスト（- 箇条書き）を使ってもかまいませんが、無理に使う必要はありません。
- 文法ミスがないようにしてください。
- 出力には不要な前置きや説明を含めないでください。

【メモ】
{memo}
"""




        completion = await self.client.chat.completions.create(
            model="openai/gpt-4.1-nano",
            messages=[
                {"role": "user", "content": prompt}
            ]
        )
        logging.info(f"ChatGPT response: {completion.choices[0].message.content}")
        return completion.choices[0].message.content
