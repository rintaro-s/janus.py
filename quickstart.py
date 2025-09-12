"""
Janus SDK クイックスタートガイド

このスクリプトを実行すると、Janus SDKの基本的なセットアップと
動作確認を行えます。
"""

import asyncio
import os
import sys
from typing import Optional


def print_header():
    """ヘッダーを表示"""
    print("=" * 60)
    print("🚀 Janus SDK クイックスタート")
    print("=" * 60)
    print()


def print_step(step: int, title: str, description: str = ""):
    """ステップを表示"""
    print(f"📍 ステップ {step}: {title}")
    if description:
        print(f"   {description}")
    print()


async def check_connection(host: str, token: str) -> bool:
    """接続テスト"""
    try:
        from janus import Client
        
        client = Client(host=host, token=token, debug=False)
        server = await client.get_server()
        await client.close()
        
        print(f"✅ 接続成功！")
        print(f"   サーバー名: {server.name}")
        print(f"   サーバーID: {server.id}")
        return True
        
    except ImportError:
        print("❌ Janus SDKがインストールされていません")
        print("   pip install -e . を実行してください")
        return False
    except Exception as e:
        print(f"❌ 接続失敗: {e}")
        print("   ホストURLまたはトークンを確認してください")
        return False


def get_user_input() -> tuple[str, str]:
    """ユーザー入力を取得"""
    print("Janus サーバーの情報を入力してください：")
    print()
    
    # ホストURL入力
    host = input("🌐 ホストURL (例: localhost:3000): ").strip()
    if not host:
        host = "localhost:3000"
        print(f"   デフォルト値を使用: {host}")
    
    # トークン入力
    token = input("🔑 サーバートークン (janus_で始まる文字列): ").strip()
    if not token:
        print("   ❌ トークンは必須です")
        sys.exit(1)
    
    print()
    return host, token


async def demo_basic_features(host: str, token: str):
    """基本機能のデモ"""
    print("🔧 基本機能をテスト中...")
    
    try:
        from janus import Client
        
        client = Client(host=host, token=token, debug=True)
        
        # サーバー情報取得
        print("📊 サーバー情報を取得中...")
        server = await client.get_server()
        print(f"   ✅ サーバー名: {server.name}")
        
        # チャンネル一覧取得
        print("📢 チャンネル一覧を取得中...")
        channels = await client.get_channels()
        print(f"   ✅ チャンネル数: {len(channels)}")
        
        if channels:
            for i, channel in enumerate(channels[:3]):  # 最大3件表示
                print(f"      {i+1}. {channel.name} (ID: {channel.id})")
        
        # メンバー一覧取得
        print("👥 メンバー一覧を取得中...")
        members = await client.get_members()
        print(f"   ✅ メンバー数: {len(members)}")
        
        # テストメッセージ送信（オプション）
        if channels:
            send_test = input("🧪 テストメッセージを送信しますか？ (y/N): ").strip().lower()
            if send_test == 'y':
                try:
                    message = await client.send_message(
                        channel_id=channels[0].id,
                        content="🧪 Janus SDK テストメッセージ - セットアップが正常に完了しました！"
                    )
                    print(f"   ✅ メッセージ送信成功 (ID: {message.id})")
                except Exception as e:
                    print(f"   ⚠️  メッセージ送信失敗: {e}")
        
        await client.close()
        
    except Exception as e:
        print(f"❌ デモ実行中にエラーが発生しました: {e}")


def create_sample_bot(host: str, token: str):
    """サンプルBotファイルを作成"""
    print("🤖 サンプルBotファイルを作成中...")
    
    bot_code = f'''"""
Janus SDK サンプルBot

このファイルは自動生成されました。
編集して独自のBotを作成してください。
"""

from janus.ext.commands import Bot

# Botを作成
bot = Bot(
    host="{host}",
    token="{token}",
    prefix="!",
    debug=True
)

@bot.command(name="hello", description="挨拶メッセージを送信します")
async def hello_command(ctx):
    await ctx.send(f"こんにちは、{{ctx.author.display_name}}さん！ 👋")

@bot.command(name="ping", description="Botの応答時間を測定します")
async def ping_command(ctx):
    await ctx.send("🏓 Pong!")

@bot.command(name="info", description="サーバー情報を表示します")
async def info_command(ctx):
    server = await ctx.client.get_server()
    members = await ctx.client.get_members()
    channels = await ctx.client.get_channels()
    
    info_text = f"""
📊 **サーバー情報**
🏠 名前: {{server.name}}
👥 メンバー数: {{len(members)}}
📢 チャンネル数: {{len(channels)}}
    """.strip()
    
    await ctx.send(info_text)

@bot.event
async def on_ready():
    print(f"🤖 {{bot.user.display_name}} が起動しました！")

@bot.event
async def on_message(message):
    # Bot自身のメッセージは無視
    if message.author.id == bot.user.id:
        return
    
    # 簡単な自動応答
    if "おはよう" in message.content.lower():
        await bot.send_message(
            message.channel.id,
            f"おはようございます、{{message.author.display_name}}さん！ ☀️"
        )

if __name__ == "__main__":
    print("🚀 サンプルBotを起動中...")
    print("Ctrl+C で停止できます")
    bot.run()
'''
    
    try:
        with open("sample_bot.py", "w", encoding="utf-8") as f:
            f.write(bot_code)
        
        print("   ✅ sample_bot.py を作成しました")
        print("   💡 python sample_bot.py で実行できます")
        
    except Exception as e:
        print(f"   ❌ ファイル作成失敗: {e}")


def show_next_steps():
    """次のステップを表示"""
    print()
    print("🎉 セットアップが完了しました！")
    print()
    print("📚 次のステップ:")
    print("   1. sample_bot.py を編集して独自のBotを作成")
    print("   2. examples.py でより多くのサンプルを確認")
    print("   3. README.md でAPIリファレンスを確認")
    print()
    print("🔗 便利なリンク:")
    print("   - ドキュメント: README.md")
    print("   - サンプルコード: examples.py")
    print("   - GitHub Issues: 問題があれば報告してください")
    print()
    print("💡 ヒント:")
    print("   - Bot開発には janus.ext.commands モジュールを使用")
    print("   - データ保存には janus.ext.database モジュールを使用")
    print("   - デバッグには debug=True オプションを使用")
    print()


async def main():
    """メイン関数"""
    print_header()
    
    print_step(1, "Janus SDK動作確認", "SDKが正しくインストールされているかチェックします")
    
    try:
        import janus
        print("✅ Janus SDKが見つかりました")
        print(f"   バージョン: {janus.__version__}")
    except ImportError:
        print("❌ Janus SDKがインストールされていません")
        print("   pip install -e . を実行してください")
        return
    
    print()
    print_step(2, "サーバー接続設定", "Janusサーバーへの接続情報を設定します")
    
    host, token = get_user_input()
    
    print_step(3, "接続テスト", "サーバーに接続できるかテストします")
    
    if not await check_connection(host, token):
        print("接続に失敗しました。設定を確認してください。")
        return
    
    print()
    print_step(4, "基本機能テスト", "SDKの基本機能をテストします")
    
    await demo_basic_features(host, token)
    
    print()
    print_step(5, "サンプルBot作成", "すぐに使えるサンプルBotファイルを作成します")
    
    create_sample_bot(host, token)
    
    show_next_steps()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\\n🛑 セットアップをキャンセルしました")
    except Exception as e:
        print(f"\\n❌ セットアップ中にエラーが発生しました: {e}")
        print("問題が解決しない場合は、GitHub Issuesで報告してください")
