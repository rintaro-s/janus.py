"""
Janus SDK 擬似Webhookサーバー

JanusのBot/AI連携をローカルでテストするための簡易Webhookエミュレータ。
Janusサーバーからのイベント（新着メッセージ等）を疑似的に受信し、任意のPython関数で処理できます。

使い方:
1. このファイルを janus-sdk/pseudo_webhook.py として保存
2. main()のサンプルを参考に、on_message などのコールバックを定義
3. JanusサーバーのAPIを定期ポーリングして新着イベントを検知

"""
import time
import threading
from janus import Client

class PseudoWebhook:
    def __init__(self, host, token, channel_name, poll_interval=3, use_server_token=True):
        self.client = Client(host=host, token=token, use_server_token=use_server_token)
        self.channel_name = channel_name
        self.poll_interval = poll_interval
        self.channel_id = None
        self.last_id = 0
        self.running = False
        self._thread = None
        self.on_message = None  # コールバック: def on_message(msg): ...

    def start(self):
        channels = self.client.get_channels()
        ch = next((c for c in channels if c.name == self.channel_name), None)
        if not ch:
            raise RuntimeError(f"チャンネル '{self.channel_name}' が見つかりません")
        self.channel_id = ch.id
        msgs = self.client.get_messages(self.channel_id, limit=1)
        self.last_id = msgs[0].id if msgs else 0
        self.running = True
        self._thread = threading.Thread(target=self._poll_loop, daemon=True)
        self._thread.start()
        print(f"PseudoWebhook: チャンネル '{self.channel_name}' 監視開始 (ID: {self.channel_id})")

    def stop(self):
        self.running = False
        if self._thread:
            self._thread.join()

    def _poll_loop(self):
        while self.running:
            try:
                msgs = self.client.get_messages(self.channel_id, limit=10)
                for msg in sorted(msgs, key=lambda m: m.id):
                    if msg.id > self.last_id:
                        if self.on_message:
                            self.on_message(msg)
                        self.last_id = msg.id
                time.sleep(self.poll_interval)
            except Exception as e:
                print(f"[PseudoWebhook] エラー: {e}")
                time.sleep(self.poll_interval)

# --- サンプル実装 ---
if __name__ == "__main__":
    HOST = "http://localhost:8000"
    TOKEN = "janus_xxx"  # ←自分のトークンに変更
    CHANNEL = "llm妹"

    def handle_message(msg):
        print(f"[Webhook] {msg.timestamp} {msg.author.display_name}: {msg.content}")
        # ここでAI応答や処理を記述可能

    webhook = PseudoWebhook(HOST, TOKEN, CHANNEL)
    webhook.on_message = handle_message
    webhook.start()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("PseudoWebhook停止")
        webhook.stop()
