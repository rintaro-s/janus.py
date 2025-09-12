#!/usr/bin/env python3
"""
Janus SDK 基本動作確認サンプル

READMEの「クイックスタート」セクションに記載されている
基本的な使用例をそのまま実行できるサンプルコードです。
"""

import janus

def main():
    print("🚀 Janus SDK 基本動作確認")
    print("=" * 40)
    
    # クライアント初期化（サーバートークンを使用）
    client = janus.Client(
        host="http://localhost:8000",  # Janusバックエンドのアドレス
        token="janus_c4ce1635dd72153eab29f6c0c87ac7fab67d878a67560f045c0e7ca133559580",
        use_server_token=True,  # サーバートークン認証を有効化
        debug=False  # デバッグモード（必要に応じて）
    )

    # サーバー情報取得
    server = client.server
    print(f"接続中のサーバー: {server.name} (ID: {server.id})")

    # チャンネル一覧取得
    channels = client.get_channels()
    print(f"利用可能なチャンネル: {len(channels)}")

    # メッセージ送信
    if channels:
        channel = channels[0]  # 最初のチャンネル
        message = client.send_message(channel.id, "Hello from Python!")
        print(f"送信完了: {message.id}")

        # メッセージ履歴取得
        messages = client.get_messages(channel.id, limit=10)
        print(f"\n📜 最新メッセージ ({len(messages)}件):")
        for msg in messages[-3:]:  # 最新3件のみ表示
            print(f"  {msg.author.name}: {msg.content}")
    
    print("\n✅ 基本動作確認完了！")

if __name__ == "__main__":
    main()
