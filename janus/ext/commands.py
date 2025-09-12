"""
Janus SDK Commands Extension

Discord.pyライクなBotコマンドフレームワーク
"""

import asyncio
import inspect
import re
from typing import Callable, Dict, List, Optional, Any, Union
from ..client import Client
from ..models import Message, Channel


class Context:
    """コマンドコンテキスト - Discord.pyのContextクラスと同様"""
    
    def __init__(self, client: Client, message: Message, prefix: str, command: str, args: List[str]):
        self.client = client
        self.message = message
        self.prefix = prefix
        self.command = command
        self.args = args
        self.channel = message.channel
        self.author = message.author
        
    async def send(self, content: str = None, **kwargs) -> Message:
        """メッセージを送信"""
        return await self.client.send_message(self.channel.id, content, **kwargs)
    
    async def reply(self, content: str = None, **kwargs) -> Message:
        """返信メッセージを送信"""
        return await self.send(f"<@{self.author.id}> {content}", **kwargs)


class Command:
    """コマンドクラス"""
    
    def __init__(
        self, 
        func: Callable,
        name: str = None,
        description: str = None,
        usage: str = None,
        aliases: List[str] = None,
        permission_required: str = None
    ):
        self.func = func
        self.name = name or func.__name__
        self.description = description or func.__doc__ or "説明なし"
        self.usage = usage
        self.aliases = aliases or []
        self.permission_required = permission_required
        
    async def invoke(self, ctx: Context):
        """コマンドを実行"""
        try:
            if inspect.iscoroutinefunction(self.func):
                await self.func(ctx)
            else:
                self.func(ctx)
        except Exception as e:
            await ctx.send(f"❌ コマンド実行中にエラーが発生しました: {e}")


class Bot(Client):
    """
    Botクライアント - Discord.pyのBotクラスと同様の機能
    
    Example:
        ```python
        from janus.ext.commands import Bot
        
        bot = Bot(host="localhost:3000", token="your_token", prefix="!")
        
        @bot.command(name="hello")
        async def hello_command(ctx):
            await ctx.send("こんにちは！")
        
        @bot.event
        async def on_message(message):
            print(f"メッセージ受信: {message.content}")
        
        bot.run()
        ```
    """
    
    def __init__(
        self, 
        host: str, 
        token: str, 
        prefix: Union[str, List[str]] = "!",
        case_insensitive: bool = True,
        **kwargs
    ):
        super().__init__(host, token, **kwargs)
        self.prefix = prefix if isinstance(prefix, list) else [prefix]
        self.case_insensitive = case_insensitive
        self.commands: Dict[str, Command] = {}
        self._command_aliases: Dict[str, str] = {}
        
        # メッセージイベントにコマンド処理を追加
        self.add_event_listener("message", self._process_commands)
        
    def command(
        self,
        name: str = None,
        description: str = None,
        usage: str = None,
        aliases: List[str] = None,
        permission_required: str = None
    ):
        """
        コマンドデコレータ
        
        Args:
            name: コマンド名
            description: コマンドの説明
            usage: 使用方法
            aliases: エイリアス
            permission_required: 必要な権限
        """
        def decorator(func):
            cmd = Command(
                func=func,
                name=name,
                description=description,
                usage=usage,
                aliases=aliases,
                permission_required=permission_required
            )
            self.add_command(cmd)
            return func
        return decorator
    
    def add_command(self, command: Command):
        """コマンドを追加"""
        cmd_name = command.name.lower() if self.case_insensitive else command.name
        self.commands[cmd_name] = command
        
        # エイリアスを登録
        for alias in command.aliases:
            alias_key = alias.lower() if self.case_insensitive else alias
            self._command_aliases[alias_key] = cmd_name
    
    def remove_command(self, name: str):
        """コマンドを削除"""
        cmd_name = name.lower() if self.case_insensitive else name
        if cmd_name in self.commands:
            command = self.commands[cmd_name]
            del self.commands[cmd_name]
            
            # エイリアスも削除
            for alias in command.aliases:
                alias_key = alias.lower() if self.case_insensitive else alias
                if alias_key in self._command_aliases:
                    del self._command_aliases[alias_key]
    
    def get_command(self, name: str) -> Optional[Command]:
        """コマンドを取得"""
        cmd_name = name.lower() if self.case_insensitive else name
        
        # 直接のコマンド名で検索
        if cmd_name in self.commands:
            return self.commands[cmd_name]
        
        # エイリアスで検索
        if cmd_name in self._command_aliases:
            return self.commands[self._command_aliases[cmd_name]]
        
        return None
    
    async def _process_commands(self, message: Message):
        """メッセージからコマンドを処理"""
        if not message.content or message.author.id == self.user.id:
            return
        
        # プレフィックスをチェック
        used_prefix = None
        for prefix in self.prefix:
            if message.content.startswith(prefix):
                used_prefix = prefix
                break
        
        if not used_prefix:
            return
        
        # コマンドとコマンド引数を解析
        content = message.content[len(used_prefix):].strip()
        if not content:
            return
        
        parts = content.split()
        command_name = parts[0]
        args = parts[1:] if len(parts) > 1 else []
        
        # コマンドを取得
        command = self.get_command(command_name)
        if not command:
            return
        
        # 権限チェック
        if command.permission_required:
            # ここで権限チェックロジックを実装
            # 例: if not self.check_permission(message.author, command.permission_required):
            #         await self.send_message(message.channel.id, "❌ 権限が不足しています")
            #         return
            pass
        
        # コンテキストを作成してコマンドを実行
        ctx = Context(self, message, used_prefix, command_name, args)
        await command.invoke(ctx)
    
    def run(self):
        """Botを開始 - Discord.pyのrunメソッドと同様"""
        print(f"🤖 Janus Bot を開始中...")
        print(f"📡 サーバー: {self.host}")
        print(f"🔧 プレフィックス: {', '.join(self.prefix)}")
        
        try:
            if self.enable_websocket:
                # WebSocket接続でリアルタイムイベントを受信
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                loop.run_until_complete(self._run_websocket())
            else:
                print("⚠️  WebSocketが無効です。リアルタイムイベントは受信できません")
                print("💡 enable_websocket=True でBotを作成してください")
        except KeyboardInterrupt:
            print("\n🛑 Bot を停止中...")
        except Exception as e:
            print(f"❌ Bot実行中にエラーが発生しました: {e}")
        finally:
            print("👋 Bot が停止しました")


# 便利なデコレータ関数
def command(name: str = None, **kwargs):
    """
    グローバルコマンドデコレータ（非推奨 - Botインスタンスのcommandデコレータを使用してください）
    """
    def decorator(func):
        func._janus_command = True
        func._janus_command_name = name or func.__name__
        func._janus_command_kwargs = kwargs
        return func
    return decorator


# ヘルパー関数
def has_permission(permission: str):
    """権限チェックデコレータ"""
    def decorator(func):
        func._janus_permission = permission
        return func
    return decorator


def cooldown(rate: int, per: float):
    """クールダウンデコレータ"""
    def decorator(func):
        func._janus_cooldown = (rate, per)
        return func
    return decorator
