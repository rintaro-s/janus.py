"""
janus_tools.py
Janus APIを活用した実用的な補助ツール集

import janus_tools で、Bot開発や運用・分析を効率化できます。

主な機能:
1. PseudoWebhook: チャンネル監視＆コールバック実行
2. CommandRecognizer: メッセージコマンド自動判定＆実行
3. ChannelAggregator: チャンネル一括メッセージ取得・集計
4. UserHistory: ユーザー発言履歴抽出・分析
5. AutoResponder: 条件付き自動返信Bot
6. InfoUtils: サーバー/チャンネル/ユーザー情報簡易取得

各機能はクラス/関数として提供されます。
"""
import time
import threading
import re
from janus import Client

class PseudoWebhook:
    """指定チャンネルをポーリングし、on_messageコールバックで新着メッセージを受信"""
    def __init__(self, client, channel_name, poll_interval=3):
        self.client = client
        self.channel_name = channel_name
        self.poll_interval = poll_interval
        self.channel_id = None
        self.last_id = 0
        self.running = False
        self._thread = None
        self.on_message = None

    def start(self):
        channels = self.client.get_channels()
        ch = next((c for c in channels if c.name == self.channel_name), None)
        if not ch:
            raise RuntimeError(f"チャンネル '{self.channel_name}' が見つかりません")
        self.channel_id = ch.id
        msgs = self.client.get_messages(self.channel_id, limit=1)
        self.last_id = msgs[0].id if msgs else 0
        self.running = True
        self._thread = threading.Thread(target=self._poll_loop, daemon=True)
        self._thread.start()

    def stop(self):
        self.running = False
        if self._thread:
            self._thread.join()

    def _poll_loop(self):
        while self.running:
            try:
                msgs = self.client.get_messages(self.channel_id, limit=10)
                for msg in sorted(msgs, key=lambda m: m.id):
                    if msg.id > self.last_id:
                        if self.on_message:
                            self.on_message(msg)
                        self.last_id = msg.id
                time.sleep(self.poll_interval)
            except Exception as e:
                print(f"[PseudoWebhook] エラー: {e}")
                time.sleep(self.poll_interval)

class CommandRecognizer:
    """メッセージからコマンド(!help等)を自動判定し、コールバックで処理"""
    def __init__(self, command_prefix="!"):
        self.command_prefix = command_prefix
        self.commands = {}

    def add_command(self, name, func):
        self.commands[name] = func

    def recognize(self, message):
        if message.content.startswith(self.command_prefix):
            cmd = message.content[len(self.command_prefix):].split()[0]
            if cmd in self.commands:
                self.commands[cmd](message)
                return True
        return False

class ChannelAggregator:
    """複数チャンネルのメッセージを一括取得・集計"""
    def __init__(self, client):
        self.client = client

    def get_all_messages(self, channel_names, limit=100):
        result = {}
        for name in channel_names:
            ch = next((c for c in self.client.get_channels() if c.name == name), None)
            if ch:
                msgs = self.client.get_messages(ch.id, limit=limit)
                result[name] = msgs
        return result

class UserHistory:
    """指定ユーザーの発言履歴抽出・分析"""
    def __init__(self, client):
        self.client = client

    def get_user_messages(self, user_display_name, channel_name=None, limit=200):
        if channel_name:
            ch = next((c for c in self.client.get_channels() if c.name == channel_name), None)
            if not ch:
                return []
            msgs = self.client.get_messages(ch.id, limit=limit)
        else:
            msgs = []
            for ch in self.client.get_channels():
                msgs += self.client.get_messages(ch.id, limit=limit)
        return [m for m in msgs if m.author.display_name == user_display_name]

class AutoResponder:
    """条件付き自動返信Bot（例: 特定ワード/ユーザーに反応）"""
    def __init__(self, client, channel_name, trigger_func, reply_func, poll_interval=3):
        self.client = client
        self.channel_name = channel_name
        self.trigger_func = trigger_func
        self.reply_func = reply_func
        self.poll_interval = poll_interval
        self.channel_id = None
        self.last_id = 0
        self.running = False
        self._thread = None

    def start(self):
        channels = self.client.get_channels()
        ch = next((c for c in channels if c.name == self.channel_name), None)
        if not ch:
            raise RuntimeError(f"チャンネル '{self.channel_name}' が見つかりません")
        self.channel_id = ch.id
        msgs = self.client.get_messages(self.channel_id, limit=1)
        self.last_id = msgs[0].id if msgs else 0
        self.running = True
        self._thread = threading.Thread(target=self._poll_loop, daemon=True)
        self._thread.start()

    def stop(self):
        self.running = False
        if self._thread:
            self._thread.join()

    def _poll_loop(self):
        while self.running:
            try:
                msgs = self.client.get_messages(self.channel_id, limit=10)
                for msg in sorted(msgs, key=lambda m: m.id):
                    if msg.id > self.last_id and self.trigger_func(msg):
                        reply = self.reply_func(msg)
                        self.client.send_message(self.channel_id, reply)
                        self.last_id = msg.id
                time.sleep(self.poll_interval)
            except Exception as e:
                print(f"[AutoResponder] エラー: {e}")
                time.sleep(self.poll_interval)

class InfoUtils:
    """サーバー/チャンネル/ユーザー情報の簡易取得"""
    @staticmethod
    def get_server_info(client):
        return client.server

    @staticmethod
    def get_channel_info(client, channel_name):
        ch = next((c for c in client.get_channels() if c.name == channel_name), None)
        return ch

    @staticmethod
    def get_user_profile(client, user_display_name):
        members = client.get_members()
        return next((m for m in members if m.display_name == user_display_name), None)

# --- ここまで ---
# 使い方例はREADMEや各クラスのdocstring参照
