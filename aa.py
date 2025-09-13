import janus
import requests
import time
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))
import janus

# --- ユーザー設定 (ここを自分の環境に合わせて変更してください) ---

# 1. Janusサーバーの情報を設定
JANUS_HOST = "https://dashboard.heroku.com"  # あなたのJanusサーバーのアドレス
JANUS_TOKEN = "janus_260684703d32447e213fdc441d8a9cf567c2fb19cba9a8382179894785a6e93f"  # 提供されたトークンを設定

# 2. LM StudioのAPIエンドポイントを設定
LMSTUDIO_API_URL = "http://localhost:1234/v1/chat/completions"

# 3. あなたのJanus上の正確なユーザー名を設定
HUMAN_USER_NAME = "りんた"

# 4. ボットが応答するチャンネル名を設定
TARGET_CHANNEL_NAME = "llm妹"

# 5. ポーリング間隔（秒）を設定
POLLING_INTERVAL = 3


# --- LM Studio応答関数 ---
def get_ai_response(user_message):
    try:
        r = requests.post(
            LMSTUDIO_API_URL,
            json={
                "model": "local-model",
                "messages": [
                    {
                        "role": "system",
                        "content": "あなたはフレンドリーな妹として、ユーザー（お兄ちゃんまたはお姉ちゃん）に応答します。",
                    },
                    {"role": "user", "content": user_message},
                ],
                "temperature": 0.7,
            },
            timeout=120,
        )
        if r.status_code == 200:
            data = r.json()
            return data.get("choices", [{}])[0].get("message", {}).get("content", "⚠️ 応答なし")
        else:
            return f"⚠️ AIサービスエラー({r.status_code})"
    except Exception as e:
        print(f"❌ LM Studio接続失敗: {e}", file=sys.stderr)
        return "❌ LM Studio接続失敗"


# --- メイン処理 ---
def main():
    print("🤖 AIチャットボット起動")
    if not HUMAN_USER_NAME:
        print("🚨致命的: HUMAN_USER_NAME未設定")
        sys.exit(1)

    try:
        client = janus.Client(host=JANUS_HOST, token=JANUS_TOKEN, use_server_token=True, debug=True)
        print(f"[DEBUG] client作成成功: {client}")

        try:
            channels = client.get_channels(force_refresh=True)
            print(f"[DEBUG] get_channels() の返り値: {repr(channels)} (型: {type(channels)})")
            # APIレスポンスの生データを表示
            raw_response = client._make_request("GET", f"/servers/{client._server_info.id}/channels")
            print(f"[DEBUG] get_channels raw response: {repr(raw_response)} (型: {type(raw_response)})")
        except Exception as e:
            print(f"[DEBUG] get_channels() 失敗: {e}")
            raise


        ch = None
        # channelsをリストに変換
        if isinstance(channels, dict):
            channels_list = list(channels.values())
        elif isinstance(channels, list):
            channels_list = channels
        else:
            print(f"❌ チャンネルリストの型が不正: {type(channels)}")
            sys.exit(1)

        # --- デバッグ: 中身を全部表示 ---
        print("[DEBUG] channels_listの内容:")
        for i, c in enumerate(channels_list):
            print(f"  - 要素{i}: {repr(c)} (型: {type(c)})")

        # --- チャンネル検索 ---
        for c in channels_list:
            if isinstance(c, int) or c is None:
                print(f"⚠️ int/None型チャンネル発見: {c} → スキップ")
                continue

            if isinstance(c, dict):
                name = c.get("name")
            else:
                name = getattr(c, "name", None)

            if name == TARGET_CHANNEL_NAME:
                ch = c
                break

        if not ch:
            print(f"❌ チャンネル '{TARGET_CHANNEL_NAME}' 未発見")
            sys.exit(1)

        # --- チャンネルID取得 ---
        if isinstance(ch, dict):
            channel_id = ch.get("id")
        elif hasattr(ch, "id"):
            channel_id = ch.id
        else:
            print(f"❌ チャンネルオブジェクトが不明形式: {repr(ch)} (型: {type(ch)})")
            sys.exit(1)

        if not channel_id:
            print(f"❌ チャンネルID取得失敗: {repr(ch)}")
            sys.exit(1)

    except Exception as e:
        print(f"❌ 初期化失敗: {e}", file=sys.stderr)
        sys.exit(1)

    # 起動時に過去メッセージIDをインデックス
    try:
        indexed_ids = {
            msg.id
            for msg in client.get_messages(channel_id, limit=200)
            if getattr(msg.author, "display_name", None) == HUMAN_USER_NAME
        }
        print(f"✅ {len(indexed_ids)}件インデックス済み")
    except Exception as e:
        print(f"❌ インデックス取得失敗: {e}", file=sys.stderr)
        indexed_ids = set()

    # メインループ
    while True:
        try:
            for msg in reversed(client.get_messages(channel_id, limit=10)):
                if getattr(msg.author, "display_name", None) == HUMAN_USER_NAME and msg.id not in indexed_ids:
                    print(f"\n[{msg.timestamp}] 🗣️ {msg.author.display_name} ({msg.author.id}): {msg.content[:100]}...")
                    print(f"アイコンURL: {msg.author.avatar_url}")
                    client.send_message(channel_id, "（考え中...）")
                    ai_reply = get_ai_response(msg.content)
                    client.send_message(channel_id, ai_reply)
                    indexed_ids.add(msg.id)
            time.sleep(POLLING_INTERVAL)
        except KeyboardInterrupt:
            print("\n👋 ボット停止")
            break
        except Exception as e:
            print(f"❌ ループエラー: {e}", file=sys.stderr)
            time.sleep(POLLING_INTERVAL)


if __name__ == "__main__":
    main()
