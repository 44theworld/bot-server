# ベースイメージ
FROM python:3.11-slim

# 作業ディレクトリ
WORKDIR /app

# PYTHONPATH を追加
ENV PYTHONPATH="${PYTHONPATH}:/app"

# 必要パッケージをインストール
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# アプリケーション一式をコピー（static/ も含む）
COPY ./app ./app

# Cloud Run/本番用ポート指定
ENV PORT=8080

# 起動コマンド（FastAPI via Uvicorn）
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"]
