# janus_tools - Tool README

このモジュールは「Janus APIを活用した補助ツール集」です。
Bot開発・運用・分析・自動化を効率化するための実用的な機能をまとめています。

> **注意: janus_toolsは試験的なツール群です。API仕様変更や機能追加・削除が頻繁に発生する可能性があります。安定運用前のプロトタイプとしてご利用ください。**

## 主な機能一覧

- **PseudoWebhook**
  - 指定チャンネルをポーリングし、on_messageコールバックで新着メッセージを受信
- **CommandRecognizer**
  - メッセージからコマンド（!help等）を自動判定し、コールバックで処理
- **ChannelAggregator**
  - 複数チャンネルのメッセージを一括取得・集計
- **UserHistory**
  - 指定ユーザーの発言履歴抽出・分析
- **AutoResponder**
  - 条件付き自動返信Bot（例: 特定ワード/ユーザーに反応）
- **InfoUtils**
  - サーバー/チャンネル/ユーザー情報の簡易取得

## 使い方例

```python
import janus
import janus_tools

client = janus.Client(...)

# 疑似Webhookで新着メッセージを監視
webhook = janus_tools.PseudoWebhook(client, "llm妹")
def on_msg(msg):
    print(msg.content)
webhook.on_message = on_msg
webhook.start()

# コマンド認識
cmd = janus_tools.CommandRecognizer()
def help_cmd(msg):
    print("ヘルプ表示")
cmd.add_command("help", help_cmd)
# ...メッセージ受信時にcmd.recognize(msg)を呼ぶ

# チャンネル集計
agg = janus_tools.ChannelAggregator(client)
all_msgs = agg.get_all_messages(["llm妹", "general"])

# ユーザー履歴
uh = janus_tools.UserHistory(client)
msgs = uh.get_user_messages("りんた")

# 自動返信Bot
ar = janus_tools.AutoResponder(client, "llm妹", lambda m: "妹" in m.content, lambda m: "お兄ちゃん！")
ar.start()

# 情報取得
info = janus_tools.InfoUtils.get_server_info(client)
```

## 注意事項
- janus_toolsはAPI仕様や設計が今後大きく変わる可能性があります。
- 本番運用前のテスト・プロトタイプ用途を推奨します。
- バグ報告・機能要望は随時歓迎です。

---

最終更新: 2025-09-13
