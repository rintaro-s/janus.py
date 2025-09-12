import janus
import requests
import time
import sys

# --- ユーザー設定 (ここを自分の環境に合わせて変更してください) ---

# 1. Janusサーバーの情報を設定
JANUS_HOST = "http://localhost:8000"  # あなたのJanusサーバーのアドレス
JANUS_TOKEN = "janus_c0a11e568f803f40b0a98c04f18f83b41a550c2911cb3d19a38367615d1c7983"# 提供されたトークンを設定

# 2. LM StudioのAPIエンドポイントを設定
LMSTUDIO_API_URL = "http://localhost:1234/v1/chat/completions"

# 3. ★★★【最重要】あなたのJanus上の正確なユーザー名を設定してください ★★★
# この名前のユーザーからのメッセージにのみ、ボットは応答します。
HUMAN_USER_NAME = "りんた"  # 例: 表示名
# 4. ボットが応答するチャンネル名を設定
TARGET_CHANNEL_NAME = "llm妹"

# 5. ポーリング間隔（秒）を設定
POLLING_INTERVAL = 3

# --- ボットのプログラム本体 ---

import janus, requests, time, sys

JANUS_HOST = "http://localhost:8000"
JANUS_TOKEN = "janus_c4ce1635dd72153eab29f6c0c87ac7fab67d878a67560f045c0e7ca133559580"
LMSTUDIO_API_URL = "http://localhost:1234/v1/chat/completions"
HUMAN_USER_NAME = "りんりん"
TARGET_CHANNEL_NAME = "llm妹"
POLLING_INTERVAL = 3

def get_ai_response(user_message):
    try:
        r = requests.post(LMSTUDIO_API_URL,
            json={"model": "local-model",
                  "messages": [
                      {"role": "system", "content": "あなたはフレンドリーな妹として、ユーザー（お兄ちゃんまたはお姉ちゃん）に応答します。"},
                      {"role": "user", "content": user_message}],
                  "temperature": 0.7}, timeout=120)
        return r.json()["choices"][0]["message"]["content"] if r.status_code == 200 else f"⚠️ AIサービスエラー({r.status_code})"
    except Exception as e:
        print(f"❌ LM Studio接続失敗: {e}", file=sys.stderr)
        return "❌ LM Studio接続失敗"

def main():
    print("🤖 AIチャットボット起動")
    if not HUMAN_USER_NAME:
        print("🚨致命的: HUMAN_USER_NAME未設定"); sys.exit(1)
    try:
        client = janus.Client(host=JANUS_HOST, token=JANUS_TOKEN, use_server_token=True)
        channels = client.get_channels()
        ch = next((c for c in channels if c.name == TARGET_CHANNEL_NAME), None)
        if not ch:
            print(f"❌ チャンネル '{TARGET_CHANNEL_NAME}' 未発見"); sys.exit(1)
        channel_id = ch.id
    except Exception as e:
        print(f"❌ 初期化失敗: {e}", file=sys.stderr); sys.exit(1)

    # 起動時に過去メッセージIDをインデックス
    try:
        indexed_ids = {msg.id for msg in client.get_messages(channel_id, limit=200) if msg.author.display_name == HUMAN_USER_NAME}
        print(f"✅ {len(indexed_ids)}件インデックス済み")
    except Exception as e:
        print(f"❌ インデックス取得失敗: {e}", file=sys.stderr); indexed_ids = set()

    while True:
        try:
            for msg in reversed(client.get_messages(channel_id, limit=10)):
                if msg.author.display_name == HUMAN_USER_NAME and msg.id not in indexed_ids:
                    print(f"\n[{msg.timestamp}] 🗣️ {msg.author.display_name} ({msg.author.id}): {msg.content[:100]}...")
                    print(f"アイコンURL: {msg.author.avatar_url}")
                    client.send_message(channel_id, "（考え中...）")
                    ai_reply = get_ai_response(msg.content)
                    client.send_message(channel_id, ai_reply)
                    indexed_ids.add(msg.id)
            time.sleep(POLLING_INTERVAL)
        except KeyboardInterrupt:
            print("\n👋 ボット停止"); break
        except Exception as e:
            print(f"❌ ループエラー: {e}", file=sys.stderr); time.sleep(POLLING_INTERVAL)

if __name__ == "__main__":
    main()