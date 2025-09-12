"""
Janus SDK サンプルコード集

このファイルには、Janus SDKの基本的な使用方法から
高度な機能までの様々なサンプルコードが含まれています。
"""

# ========================================
# 基本的な使用例
# ========================================

from janus import Client

# 基本的なクライアント使用例
async def basic_example():
    """基本的なJanus SDKの使用例"""
    # クライアントを作成
    client = Client(
        host="localhost:3000",
        token="janus_your_server_token_here",
        debug=True  # デバッグ情報を表示
    )
    
    try:
        # サーバー情報を取得
        server = await client.get_server()
        print(f"サーバー名: {server.name}")
        
        # チャンネル一覧を取得
        channels = await client.get_channels()
        print(f"チャンネル数: {len(channels)}")
        
        # 最初のチャンネルにメッセージを送信
        if channels:
            message = await client.send_message(
                channel_id=channels[0].id,
                content="Hello from Janus SDK! 🎉"
            )
            print(f"メッセージを送信しました: {message.id}")
        
        # メンバー一覧を取得
        members = await client.get_members()
        print(f"メンバー数: {len(members)}")
        
    except Exception as e:
        print(f"エラーが発生しました: {e}")
    finally:
        await client.close()


# ========================================
# Botフレームワーク使用例
# ========================================

from janus.ext.commands import Bot

# Botの基本設定
bot = Bot(
    host="localhost:3000",
    token="janus_your_server_token_here",
    prefix=["!", "?", "janus "],  # 複数のプレフィックスに対応
    case_insensitive=True,
    debug=True
)

# 基本的なコマンド
@bot.command(name="hello", description="挨拶メッセージを送信します")
async def hello_command(ctx):
    """シンプルな挨拶コマンド"""
    await ctx.send(f"こんにちは、{ctx.author.display_name}さん！ 👋")

@bot.command(name="info", description="サーバー情報を表示します")
async def server_info_command(ctx):
    """サーバー情報表示コマンド"""
    server = await ctx.client.get_server()
    members = await ctx.client.get_members()
    channels = await ctx.client.get_channels()
    
    info_message = f"""
📊 **サーバー情報**
🏠 サーバー名: {server.name}
👥 メンバー数: {len(members)}
📢 チャンネル数: {len(channels)}
🔧 作成日: {server.created_at}
    """.strip()
    
    await ctx.send(info_message)

@bot.command(name="ping", description="Botの応答時間を測定します")
async def ping_command(ctx):
    """レイテンシー測定コマンド"""
    import time
    start_time = time.time()
    message = await ctx.send("🏓 Pong!")
    end_time = time.time()
    
    latency = round((end_time - start_time) * 1000, 2)
    await ctx.send(f"🏓 Pong! レイテンシー: {latency}ms")

# コマンド引数を使用する例
@bot.command(name="echo", description="指定されたメッセージを繰り返します")
async def echo_command(ctx):
    """メッセージエコーコマンド"""
    if not ctx.args:
        await ctx.send("❌ メッセージを指定してください")
        return
    
    message = " ".join(ctx.args)
    await ctx.send(f"🔄 {message}")

@bot.command(name="channel", description="新しいチャンネルを作成します")
async def create_channel_command(ctx):
    """チャンネル作成コマンド"""
    if not ctx.args:
        await ctx.send("❌ チャンネル名を指定してください")
        return
    
    channel_name = " ".join(ctx.args)
    try:
        channel = await ctx.client.create_channel(
            name=channel_name,
            description=f"{ctx.author.display_name}が作成したチャンネル"
        )
        await ctx.send(f"✅ チャンネル「{channel.name}」を作成しました！")
    except Exception as e:
        await ctx.send(f"❌ チャンネル作成に失敗しました: {e}")

# イベントリスナーの例
@bot.event
async def on_message(message):
    """メッセージ受信イベント"""
    # Bot自身のメッセージは無視
    if message.author.id == bot.user.id:
        return
    
    # 特定のキーワードに反応
    if "おはよう" in message.content.lower():
        await bot.send_message(
            message.channel.id,
            f"おはようございます、{message.author.display_name}さん！ ☀️"
        )
    
    # デバッグ情報を出力
    print(f"[{message.channel.name}] {message.author.display_name}: {message.content}")

@bot.event
async def on_ready():
    """Bot起動完了イベント"""
    print(f"🤖 {bot.user.display_name} が起動しました！")
    print(f"📊 サーバー: {bot.server.name}")
    print(f"👥 メンバー数: {len(await bot.get_members())}")

# Botを実行
if __name__ == "__main__":
    bot.run()


# ========================================
# データベース統合例
# ========================================

from janus.ext.commands import Bot
from janus.ext.database import create_sqlite_database

# データベース統合Bot
class DatabaseBot(Bot):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.db = create_sqlite_database("./bot_data/bot.db")
    
    async def close(self):
        """Botを終了する際にデータベースも閉じる"""
        self.db.close()
        await super().close()

# データベース付きBot
db_bot = DatabaseBot(
    host="localhost:3000",
    token="janus_your_server_token_here",
    prefix="db!"
)

@db_bot.command(name="set", description="ユーザー設定を保存します")
async def set_setting_command(ctx):
    """ユーザー設定保存コマンド"""
    if len(ctx.args) < 2:
        await ctx.send("❌ 使用方法: `db!set <キー> <値>`")
        return
    
    key = ctx.args[0]
    value = " ".join(ctx.args[1:])
    
    # データベースに設定を保存
    ctx.client.db.set_user_setting(
        user_id=ctx.author.id,
        server_id=ctx.client.server.id,
        key=key,
        value=value
    )
    
    await ctx.send(f"✅ 設定「{key}」を保存しました")

@db_bot.command(name="get", description="ユーザー設定を取得します")
async def get_setting_command(ctx):
    """ユーザー設定取得コマンド"""
    if not ctx.args:
        # すべての設定を表示
        settings = ctx.client.db.get_all_user_settings(
            user_id=ctx.author.id,
            server_id=ctx.client.server.id
        )
        
        if not settings:
            await ctx.send("❌ 設定が見つかりません")
            return
        
        settings_text = "\n".join([f"**{k}**: {v}" for k, v in settings.items()])
        await ctx.send(f"📋 **あなたの設定**\n{settings_text}")
    else:
        # 特定の設定を表示
        key = ctx.args[0]
        value = ctx.client.db.get_user_setting(
            user_id=ctx.author.id,
            server_id=ctx.client.server.id,
            key=key
        )
        
        if value is None:
            await ctx.send(f"❌ 設定「{key}」が見つかりません")
        else:
            await ctx.send(f"📋 **{key}**: {value}")

@db_bot.event
async def on_message(message):
    """メッセージをデータベースにログ"""
    if message.author.id != db_bot.user.id:
        db_bot.db.log_message(
            message_id=message.id,
            user_id=message.author.id,
            channel_id=message.channel.id,
            server_id=db_bot.server.id,
            content=message.content
        )


# ========================================
# 高度な使用例
# ========================================

import asyncio
from janus import Client
from janus.models import Channel

async def advanced_example():
    """高度な機能の使用例"""
    client = Client(
        host="localhost:3000",
        token="janus_your_server_token_here",
        enable_websocket=True,  # リアルタイムイベントを有効化
        debug=True
    )
    
    # リアルタイムイベントリスナーを設定
    @client.event
    async def on_message(message):
        print(f"新しいメッセージ: {message.content}")
        
        # 自動返信の例
        if message.content.startswith("!weather"):
            await client.send_message(
                message.channel.id,
                "☀️ 今日は晴れです！（天気APIと連携させることも可能）"
            )
    
    @client.event
    async def on_channel_create(channel):
        print(f"新しいチャンネルが作成されました: {channel.name}")
    
    @client.event
    async def on_member_join(member):
        print(f"新しいメンバーが参加しました: {member.display_name}")
        
        # ウェルカムメッセージを送信
        channels = await client.get_channels()
        general_channel = next((ch for ch in channels if "general" in ch.name.lower()), None)
        if general_channel:
            await client.send_message(
                general_channel.id,
                f"🎉 {member.display_name}さん、ようこそ！"
            )
    
    try:
        # ファイルアップロードの例
        with open("example.txt", "w") as f:
            f.write("これはサンプルファイルです")
        
        channels = await client.get_channels()
        if channels:
            message = await client.send_message(
                channel_id=channels[0].id,
                content="ファイルをアップロードします",
                files=["example.txt"]
            )
            print(f"ファイル付きメッセージを送信: {message.id}")
        
        # 複数チャンネルの管理
        bot_channels = []
        for i in range(3):
            channel = await client.create_channel(
                name=f"bot-channel-{i+1}",
                description=f"Bot用チャンネル {i+1}"
            )
            bot_channels.append(channel)
            print(f"チャンネル作成: {channel.name}")
        
        # 各チャンネルにウェルカムメッセージ
        for channel in bot_channels:
            await client.send_message(
                channel.id,
                f"🤖 {channel.name} へようこそ！\nこのチャンネルはBotによって管理されています。"
            )
        
        # WebSocketで継続的にイベントを監視
        print("WebSocketでイベントを監視中... (Ctrl+Cで終了)")
        await client.start_websocket()
        
    except KeyboardInterrupt:
        print("プログラムを終了します...")
    except Exception as e:
        print(f"エラー: {e}")
    finally:
        await client.close()


# ========================================
# 実行例
# ========================================

if __name__ == "__main__":
    print("Janus SDK サンプルコード")
    print("=" * 50)
    print("1. 基本的な使用例")
    print("2. Botフレームワーク例")
    print("3. データベース統合例") 
    print("4. 高度な使用例")
    print("=" * 50)
    
    choice = input("実行する例を選択してください (1-4): ").strip()
    
    if choice == "1":
        asyncio.run(basic_example())
    elif choice == "2":
        print("Botフレームワークを起動中...")
        bot.run()
    elif choice == "3":
        print("データベース統合Botを起動中...")
        db_bot.run()
    elif choice == "4":
        asyncio.run(advanced_example())
    else:
        print("無効な選択です")
