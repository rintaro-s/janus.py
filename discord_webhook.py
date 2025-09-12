# ファイル名: RAG_webhook_bot_fixed.py
import janus
import time
import requests

# ===== 設定 =====
JANUS_HOST = "http://localhost:8000"
JANUS_TOKEN = "janus_c4ce1635dd72153eab29f6c0c87ac7fab67d878a67560f045c0e7ca133559580"
AI_CHANNEL_NAME = "webhook"

# 送信先 Discord Webhook（ハードコーディング）
DISCORD_WEBHOOK_URL = "https://discord.com/api/webhooks/1415758484128923658/SE1RzDVIDxNCcXjPXS0tMG-fxbqy4en0Em6Tc6m4pAGQxbyK9o3AO7rEW8COUaHBq-aY"

# ===== Janusクライアント初期化 =====
client = janus.Client(
    host=JANUS_HOST,
    token=JANUS_TOKEN,
    use_server_token=True
)

# ===== AIチャンネル確認/作成 =====
channels = client.get_channels()
ai_channel = next((c for c in channels if c.name == AI_CHANNEL_NAME), None)
if not ai_channel:
    ai_channel = client.create_channel(
        name=AI_CHANNEL_NAME,
        type="text",
        description="Webhook用チャンネル"
    )
print(f"AIチャンネル: {ai_channel.name} (ID: {ai_channel.id})")

# ===== 起動時の最新メッセージIDを記録 =====
messages = client.get_messages(ai_channel.id, limit=1)
last_id = messages[0].id if messages else 0

# ===== メインループ =====
while True:
    messages = client.get_messages(ai_channel.id, limit=5)
    messages = sorted(messages, key=lambda m: m.id)  # 古い順

    for msg in messages:
        if msg.id <= last_id:
            continue

        content = msg.content.strip()
        if content.startswith("!webhook "):
            # !webhook の後ろが全部メッセージ
            text = content[len("!webhook "):].strip()
            if not text:
                client.send_message(ai_channel.id, "使い方: !webhook {メッセージ}")
                continue

            try:
                res = requests.post(DISCORD_WEBHOOK_URL, json={"content": text})
                if res.status_code == 204:
                    client.send_message(ai_channel.id, "Webhook送信成功！")
                else:
                    client.send_message(ai_channel.id, f"Webhook送信失敗: {res.status_code}")
            except Exception as e:
                client.send_message(ai_channel.id, f"Webhook送信エラー: {e}")

        last_id = max(last_id, msg.id)

    time.sleep(5)
