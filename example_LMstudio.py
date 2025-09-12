import janus
import requests
import time
import sys

# --- ユーザー設定 (ここを自分の環境に合わせて変更してください) ---

# 1. Janusサーバーの情報を設定
JANUS_HOST = "http://localhost:8000"  # あなたのJanusサーバーのアドレス
JANUS_TOKEN = "token_here"# 提供されたトークンを設定

# 2. LM StudioのAPIエンドポイントを設定
LMSTUDIO_API_URL = "http://localhost:1234/v1/chat/completions"

# 3. ★★★【最重要】あなたのJanus上の正確なユーザー名を設定してください ★★★
# この名前のユーザーからのメッセージにのみ、ボットは応答します。
HUMAN_USER_NAME = "あなたのユーザー名を設定"  # 例: "rinta", "Rinta Yamada" などJanusアプリに表示される名前

# 4. ボットが応答するチャンネル名を設定
TARGET_CHANNEL_NAME = "llm妹"

# 5. ポーリング間隔（秒）を設定
POLLING_INTERVAL = 3

# --- ボットのプログラム本体 ---

def get_ai_response(user_message):
    """LM Studio APIに問い合わせて、AIからの返信を取得する"""
    try:
        response = requests.post(
            LMSTUDIO_API_URL,
            json={
                "model": "local-model",
                "messages": [
                    {"role": "system", "content": "あなたはフレンドリーな妹として、ユーザー（お兄ちゃんまたはお姉ちゃん）に応答します。"},
                    {"role": "user", "content": user_message}
                ],
                "temperature": 0.7,
            },
            timeout=120
        )
        if response.status_code == 200:
            return response.json()["choices"][0]["message"]["content"]
        else:
            error_msg = f"⚠️ AIサービスでエラーが発生 (コード: {response.status_code})"
            print(error_msg, file=sys.stderr)
            return error_msg
    except requests.exceptions.RequestException as e:
        error_msg = f"❌ LM Studioへの接続に失敗しました。サーバーが起動しているか確認してください。"
        print(f"{error_msg}\n詳細: {e}", file=sys.stderr)
        return error_msg

def main():
    """メインの処理"""
    print("🤖 AIチャットボットを起動します...")
    if HUMAN_USER_NAME == "あなたのユーザー名を設定":
        print("🚨致命的なエラー: ボットが応答すべき人間のユーザー名が設定されていません。")
        print("   コード内の 'HUMAN_USER_NAME' 変数をあなたのJanus上の名前に書き換えてください。")
        sys.exit(1)

    try:
        client = janus.Client(host=JANUS_HOST, token=JANUS_TOKEN, use_server_token=True)
        print(f"✅ サーバー '{client.server.name}' への接続に成功しました。")
    except Exception as e:
        print(f"❌ Janusサーバーへの接続に失敗しました: {e}", file=sys.stderr)
        sys.exit(1)

    # 応答対象のチャンネルIDを取得
    try:
        print(f"🎯 チャンネル '{TARGET_CHANNEL_NAME}' を探しています...")
        channels = client.get_channels()
        target_channel = next((ch for ch in channels if ch.name == TARGET_CHANNEL_NAME), None)
        if not target_channel:
            print(f"❌ チャンネル '{TARGET_CHANNEL_NAME}' が見つかりませんでした。")
            sys.exit(1)
        print(f"👍 チャンネルを発見しました (ID: {target_channel.id})。")
        channel_id = target_channel.id
    except Exception as e:
        print(f"❌ チャンネルの取得中にエラーが発生しました: {e}", file=sys.stderr)
        sys.exit(1)

    # 最後に処理したメッセージのIDを初期化
    try:
        latest_messages = client.get_messages(channel_id, limit=1)
        last_id = latest_messages[0].id if latest_messages else 0
        print(f"💬 メッセージ監視を開始します。最後に確認したID: {last_id}")
        print(f"👤 '{HUMAN_USER_NAME}' さんからのメッセージにのみ応答します。")
    except Exception as e:
        print(f"❌ 初期メッセージの取得に失敗しました: {e}", file=sys.stderr)
        last_id = 0

    while True:
        try:
            messages = client.get_messages(channel_id, limit=10)
            
            new_human_messages = []
            for msg in reversed(messages):
                # ▼▼▼【最終修正】新しい and 'HUMAN_USER_NAME' からのメッセージか？ ▼▼▼
                if msg.id > last_id and msg.author.name == HUMAN_USER_NAME:
                    new_human_messages.append(msg)
            
            for message in new_human_messages:
                print(f"\n[{message.timestamp}] 🗣️ {message.author.name}さんからの新着: {message.content[:100]}...")
                
                client.send_message(channel_id, "（考え中...）")
                
                print("🧠 LM Studioに応答を問い合わせ中...")
                ai_reply = get_ai_response(message.content)
                
                print(f"🤖 AIからの応答を送信します。")
                client.send_message(channel_id, ai_reply)
                
                # 1件処理するごとに、そのメッセージのIDを記録する
                last_id = message.id
            
            # もし処理対象外の新しいメッセージがあった場合でも、last_idは更新しておく
            if messages and messages[0].id > last_id:
                last_id = messages[0].id

            time.sleep(POLLING_INTERVAL)

        except KeyboardInterrupt:
            print("\n👋 ボットを停止します。")
            break
        except Exception as e:
            print(f"❌ ループ中にエラーが発生しました: {e}", file=sys.stderr)
            print(f"{POLLING_INTERVAL}秒待機してリトライします...")
            time.sleep(POLLING_INTERVAL)

if __name__ == "__main__":
    main()