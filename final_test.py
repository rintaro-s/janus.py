#!/usr/bin/env python3
"""
Janus SDK 最終動作確認テスト
サーバートークン認証を使用してすべての主要機能をテストします。
"""

import asyncio
from janus import Client

async def final_test():
    print("🎯 Janus SDK 最終動作確認")
    print("=" * 50)
    
    # サーバートークンを使用してクライアント初期化
    client = Client(
        host="http://localhost:8000",
        JANUS_TOKEN = "token_here",
        use_server_token=True,
        debug=False  # デバッグ出力を無効に
    )
    
    try:
        # 1. サーバー情報取得
        print("1️⃣ サーバー情報取得テスト")
        server_info = client.server
        print(f"   ✅ サーバー名: {server_info.name}")
        print(f"   ✅ サーバーID: {server_info.id}")
        print()
        
        # 2. チャンネル操作
        print("2️⃣ チャンネル操作テスト")
        channels = client.get_channels()
        print(f"   ✅ 既存チャンネル数: {len(channels)}")
        
        # 新しいチャンネルを作成
        new_channel = client.create_channel("final-test-channel", "text")
        print(f"   ✅ チャンネル作成: {new_channel.name} (ID: {new_channel.id})")
        print()
        
        # 3. メッセージ操作
        print("3️⃣ メッセージ操作テスト")
        message = client.send_message(
            new_channel.id, 
            "🎊 Janus SDK 最終テスト完了！サーバートークン認証が正常に動作しています。"
        )
        print(f"   ✅ メッセージ送信: ID {message.id}")
        
        # メッセージ履歴取得
        messages = client.get_messages(new_channel.id)
        print(f"   ✅ メッセージ履歴取得: {len(messages)}件")
        print()
        
        # 4. メンバー情報
        print("4️⃣ メンバー情報テスト")
        members = client.get_members()
        print(f"   ✅ サーバーメンバー数: {len(members)}")
        print()
        
        # 機能サマリー
        print("🎉 Janus SDK 最終テスト結果")
        print("=" * 50)
        print("✅ サーバートークン認証: 成功")
        print("✅ サーバー情報取得: 成功")
        print("✅ チャンネル作成: 成功")
        print("✅ メッセージ送信: 成功") 
        print("✅ メッセージ履歴取得: 成功")
        print("✅ メンバー情報取得: 成功")
        print()
        print("🎯 すべての主要機能が正常に動作しています！")
        print("Auth0を使わずにサーバートークンでバックエンドが使用可能です。")
        
    except Exception as e:
        print(f"❌ テストエラー: {e}")
        return False
        
    return True

if __name__ == "__main__":
    asyncio.run(final_test())
