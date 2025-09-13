# Janus SDK 仕様書

## 概要
Janus SDKは、Discord風チャットサーバー「Janus」のPython用クライアントライブラリです。
サーバートークン認証で自分のサーバーに安全にアクセスし、チャンネル・メッセージ・メンバー管理が可能です。

---

## 🚀 クイックスタート

```python
import janus

# サーバートークン認証でクライアント初期化
client = janus.Client(
    host="http://localhost:8000",  # JanusサーバーのURL
    token="janus_...",             # Janus管理画面で取得したサーバートークン
    use_server_token=True           # 必須
)

# サーバー情報取得
server = client.server
print(f"サーバー名: {server.name} (ID: {server.id})")

# チャンネル一覧取得
channels = client.get_channels()
print(f"チャンネル数: {len(channels)}")

# チャンネル作成
new_channel = client.create_channel(
    name="テストチャンネル",
    type="text",
    description="テスト用"
)
print(f"新規チャンネル: {new_channel.name} (ID: {new_channel.id})")

# メッセージ送信
message = client.send_message(new_channel.id, "こんにちは！Janus SDKテストです。")
print(f"送信メッセージID: {message.id}")

# メッセージ履歴取得
messages = client.get_messages(new_channel.id, limit=10)
for msg in messages:
    print(f"{msg.author.display_name} ({msg.author.id}): {msg.content}")
    print(f"アイコンURL: {msg.author.avatar_url}")

# ユーザープロフィール取得（UserProfile API）
profile = client.get_user_profile("auth0|xxxxxxx")
print(f"表示名: {profile.display_name}, アイコン: {profile.avatar_url}")

# メンバー一覧取得
members = client.get_members()
print(f"メンバー数: {len(members)}")
```

---

## 📚 サポートされるAPI

| メソッド                       | 説明                       | 戻り値           |
|-------------------------------|----------------------------|------------------|
| `client.server`               | サーバー情報取得           | `Server`         |
| `client.get_channels()`       | チャンネル一覧取得         | `List[Channel]`  |
| `client.create_channel(...)`  | チャンネル作成             | `Channel`        |
| `client.get_channel(id)`      | チャンネル情報取得         | `Channel`        |
| `client.send_message(...)`    | メッセージ送信             | `Message`        |
| `client.get_messages(...)`    | メッセージ履歴取得         | `List[Message]`  |
| `client.get_members()`        | メンバー一覧取得           | `List[Member]`   |
| `client.get_user_profile(id)` | ユーザープロフィール取得   | `User`           |

---

## ⚠️ 未実装・非対応機能

- イベントハンドラ（@client.event, client.run）は未実装
- WebSocket/リアルタイム通知は未実装
- ファイル送信・画像送信は未実装
- メッセージ編集・削除は未実装
- 権限チェック・管理者判定は未実装
- Webhook/拡張コマンド/DB連携は未実装

---

## 📝 仕様上の注意

- サーバートークン認証のみサポート（Auth0不要）
- APIは全て同期関数（async/await不要）
- チャンネルtypeは「text」のみサポート
- ファイル送信はテキストでリンク等を共有してください

---

## 💡 よくある使い方

### メッセージ監視（ポーリング例）

```python
import time

channel_id = ...  # 監視したいチャンネルID
last_id = 0

while True:
    messages = client.get_messages(channel_id, limit=5)
    for msg in messages:
        if msg.id > last_id:
            print(f"新着: {msg.author.name}: {msg.content}")
            last_id = msg.id
    time.sleep(5)
```

---

## モデル定義

### Channel
```python
class Channel:
    id: int
    name: str
    description: str
    type: str  # "text" (現在対応)
    created_at: datetime
    updated_at: datetime
```

### Message
```python
class Message:
    id: int
    channel_id: int
    author: User
    content: str
    timestamp: datetime
    edited_at: Optional[datetime]
    attachments: List[Attachment]
```

### User
```python
class User:
    id: str  # Auth0 ID
    name: str
    display_name: str  # 表示名（UserProfile）
    avatar_url: Optional[str]
    status: str  # "online", "offline", "away"
    roles: List[str]
- メッセージのauthorはUserProfile（display_name, avatar_url, id）を持ちます
- 表示名は`msg.author.display_name`で取得してください
- ユーザープロフィールは`client.get_user_profile(user_id)`で取得できます
```

### Server
```python
class Server:
    id: int
    name: str
    api_token: str
    member_count: int
    created_at: datetime
```

---

**Janus SDKはサーバートークン認証による安全なチャットAPIを提供します。\nREADMEのサンプルコードはすべて実際に動作します。\n未実装機能については今後のアップデートで対応予定です。**
