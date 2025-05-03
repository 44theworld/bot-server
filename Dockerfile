# ベースイメージ
FROM python:3.11-slim

# 作業ディレクトリ作成
WORKDIR /app

# 必要なファイルをコピー
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# アプリケーションコピー
COPY ./app ./app

# 環境変数（Cloud Run用にポートは8080）
ENV PORT=8080

# uvicorn起動
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"]
