#!/usr/bin/env python3
"""
Janus SDK 動作確認テスト

サーバートークンでHTTP APIが正常に動作することを確認します。
"""

import os
import sys
import asyncio
sys.path.insert(0, '/home/rinta/ドキュメント/devcamp/devcamp-workspace8/janus-sdk')

import janus

async def test_sdk():
    """SDK基本機能テスト"""
    
    # 設定
    JANUS_HOST = "http://localhost:8000"
    JANUS_TOKEN = "token_here"
    print("🚀 Janus SDK 動作確認テスト開始")
    print("=" * 50)
    
    try:
        # クライアント作成（WebSocket無効）
        client = janus.Client(
            host=JANUS_HOST, 
            token=JANUS_TOKEN, 
            use_server_token=True,
            debug=False  # デバッグ出力を無効化
        )
        
        print("✅ クライアント初期化成功")
        print(f"   サーバー: {client.server.name}")
        print(f"   サーバーID: {client.server.id}")
        
        # チャンネル一覧取得
        print("\n📢 チャンネル一覧取得中...")
        channels = client.get_channels()
        print(f"✅ チャンネル数: {len(channels)}")
        
        for i, channel in enumerate(channels[:3]):  # 最大3件表示
            print(f"   {i+1}. {channel.name} (ID: {channel.id}, Type: {channel.type})")
        
        # メンバー一覧取得
        print("\n👥 メンバー一覧取得中...")
        members = client.get_members()
        print(f"✅ メンバー数: {len(members)}")
        
        # テストチャンネル作成
        print("\n🛠️ テストチャンネル作成中...")
        test_channel = client.create_channel(
            name="sdk-test-channel",
            description="SDK動作確認用チャンネル",
            type="text"
        )
        print(f"✅ チャンネル作成成功: {test_channel.name} (ID: {test_channel.id})")
        
        # テストメッセージ送信
        print("\n💬 テストメッセージ送信中...")
        message = client.send_message(
            test_channel.id,
            "🧪 Janus SDK テストメッセージ - サーバートークン認証が正常に動作しています！"
        )
        print(f"✅ メッセージ送信成功 (ID: {message.id})")
        
        # メッセージ履歴取得
        print("\n📜 メッセージ履歴取得中...")
        messages = client.get_messages(test_channel.id, limit=5)
        print(f"✅ メッセージ数: {len(messages)}")
        
        for i, msg in enumerate(messages):
            content_preview = msg.content[:50] + "..." if len(msg.content) > 50 else msg.content
            print(f"   {i+1}. {content_preview}")
        
        print("\n🎉 すべてのテストが成功しました！")
        print("=" * 50)
        print("✅ サーバートークン認証: 動作OK")
        print("✅ サーバー情報取得: 動作OK") 
        print("✅ チャンネル操作: 動作OK")
        print("✅ メッセージ操作: 動作OK")
        print("✅ メンバー情報取得: 動作OK")
        
        return True
        
    except Exception as e:
        print(f"\n❌ テストが失敗しました: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(test_sdk())
    sys.exit(0 if success else 1)
