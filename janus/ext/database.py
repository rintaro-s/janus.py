"""
Janus SDK Database Extension

データベース統合機能を提供します。
SQLite、PostgreSQL、MySQLなどの各種データベースとの連携をサポート。
"""

import sqlite3
import json
import os
from typing import Any, Dict, List, Optional, Union
from datetime import datetime
from contextlib import contextmanager


class DatabaseAdapter:
    """データベースアダプター基底クラス"""
    
    def __init__(self, connection_string: str):
        self.connection_string = connection_string
        self.connection = None
    
    def connect(self):
        """データベースに接続"""
        raise NotImplementedError
    
    def disconnect(self):
        """データベース接続を切断"""
        raise NotImplementedError
    
    def execute(self, query: str, params: tuple = None) -> Any:
        """クエリを実行"""
        raise NotImplementedError
    
    def fetch_one(self, query: str, params: tuple = None) -> Optional[Dict]:
        """1件のレコードを取得"""
        raise NotImplementedError
    
    def fetch_all(self, query: str, params: tuple = None) -> List[Dict]:
        """すべてのレコードを取得"""
        raise NotImplementedError


class SQLiteAdapter(DatabaseAdapter):
    """SQLite データベースアダプター"""
    
    def __init__(self, database_path: str):
        super().__init__(database_path)
        self.database_path = database_path
        
        # データベースディレクトリを作成
        os.makedirs(os.path.dirname(database_path), exist_ok=True)
    
    def connect(self):
        """SQLiteデータベースに接続"""
        self.connection = sqlite3.connect(self.database_path)
        self.connection.row_factory = sqlite3.Row  # 辞書形式で結果を取得
        return self.connection
    
    def disconnect(self):
        """データベース接続を切断"""
        if self.connection:
            self.connection.close()
            self.connection = None
    
    @contextmanager
    def get_cursor(self):
        """カーソルのコンテキストマネージャー"""
        if not self.connection:
            self.connect()
        
        cursor = self.connection.cursor()
        try:
            yield cursor
            self.connection.commit()
        except Exception as e:
            self.connection.rollback()
            raise e
        finally:
            cursor.close()
    
    def execute(self, query: str, params: tuple = None) -> sqlite3.Cursor:
        """クエリを実行"""
        with self.get_cursor() as cursor:
            if params:
                return cursor.execute(query, params)
            else:
                return cursor.execute(query)
    
    def fetch_one(self, query: str, params: tuple = None) -> Optional[Dict]:
        """1件のレコードを取得"""
        with self.get_cursor() as cursor:
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            
            row = cursor.fetchone()
            return dict(row) if row else None
    
    def fetch_all(self, query: str, params: tuple = None) -> List[Dict]:
        """すべてのレコードを取得"""
        with self.get_cursor() as cursor:
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            
            rows = cursor.fetchall()
            return [dict(row) for row in rows]


class BotDatabase:
    """
    Bot用データベースクラス
    
    よく使用されるBot機能のためのテーブルとメソッドを提供
    """
    
    def __init__(self, adapter: DatabaseAdapter):
        self.adapter = adapter
        self.adapter.connect()
        self._create_tables()
    
    def _create_tables(self):
        """必要なテーブルを作成"""
        # ユーザー設定テーブル
        self.adapter.execute("""
            CREATE TABLE IF NOT EXISTS user_settings (
                user_id TEXT PRIMARY KEY,
                server_id TEXT NOT NULL,
                settings TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # サーバー設定テーブル
        self.adapter.execute("""
            CREATE TABLE IF NOT EXISTS server_settings (
                server_id TEXT PRIMARY KEY,
                settings TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # メッセージログテーブル
        self.adapter.execute("""
            CREATE TABLE IF NOT EXISTS message_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                message_id TEXT NOT NULL,
                user_id TEXT NOT NULL,
                channel_id TEXT NOT NULL,
                server_id TEXT NOT NULL,
                content TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # コマンド使用統計テーブル
        self.adapter.execute("""
            CREATE TABLE IF NOT EXISTS command_stats (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                command_name TEXT NOT NULL,
                user_id TEXT NOT NULL,
                server_id TEXT NOT NULL,
                success BOOLEAN NOT NULL,
                executed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
    
    # ユーザー設定関連メソッド
    def get_user_setting(self, user_id: str, server_id: str, key: str, default: Any = None) -> Any:
        """ユーザー設定を取得"""
        row = self.adapter.fetch_one(
            "SELECT settings FROM user_settings WHERE user_id = ? AND server_id = ?",
            (user_id, server_id)
        )
        
        if not row:
            return default
        
        settings = json.loads(row['settings'])
        return settings.get(key, default)
    
    def set_user_setting(self, user_id: str, server_id: str, key: str, value: Any):
        """ユーザー設定を保存"""
        # 既存の設定を取得
        row = self.adapter.fetch_one(
            "SELECT settings FROM user_settings WHERE user_id = ? AND server_id = ?",
            (user_id, server_id)
        )
        
        if row:
            settings = json.loads(row['settings'])
            settings[key] = value
            self.adapter.execute(
                "UPDATE user_settings SET settings = ?, updated_at = CURRENT_TIMESTAMP WHERE user_id = ? AND server_id = ?",
                (json.dumps(settings), user_id, server_id)
            )
        else:
            settings = {key: value}
            self.adapter.execute(
                "INSERT INTO user_settings (user_id, server_id, settings) VALUES (?, ?, ?)",
                (user_id, server_id, json.dumps(settings))
            )
    
    def get_all_user_settings(self, user_id: str, server_id: str) -> Dict[str, Any]:
        """ユーザーのすべての設定を取得"""
        row = self.adapter.fetch_one(
            "SELECT settings FROM user_settings WHERE user_id = ? AND server_id = ?",
            (user_id, server_id)
        )
        
        if not row:
            return {}
        
        return json.loads(row['settings'])
    
    # サーバー設定関連メソッド
    def get_server_setting(self, server_id: str, key: str, default: Any = None) -> Any:
        """サーバー設定を取得"""
        row = self.adapter.fetch_one(
            "SELECT settings FROM server_settings WHERE server_id = ?",
            (server_id,)
        )
        
        if not row:
            return default
        
        settings = json.loads(row['settings'])
        return settings.get(key, default)
    
    def set_server_setting(self, server_id: str, key: str, value: Any):
        """サーバー設定を保存"""
        row = self.adapter.fetch_one(
            "SELECT settings FROM server_settings WHERE server_id = ?",
            (server_id,)
        )
        
        if row:
            settings = json.loads(row['settings'])
            settings[key] = value
            self.adapter.execute(
                "UPDATE server_settings SET settings = ?, updated_at = CURRENT_TIMESTAMP WHERE server_id = ?",
                (json.dumps(settings), server_id)
            )
        else:
            settings = {key: value}
            self.adapter.execute(
                "INSERT INTO server_settings (server_id, settings) VALUES (?, ?)",
                (server_id, json.dumps(settings))
            )
    
    # メッセージログ関連メソッド
    def log_message(self, message_id: str, user_id: str, channel_id: str, server_id: str, content: str):
        """メッセージをログに記録"""
        self.adapter.execute(
            "INSERT INTO message_logs (message_id, user_id, channel_id, server_id, content) VALUES (?, ?, ?, ?, ?)",
            (message_id, user_id, channel_id, server_id, content)
        )
    
    def get_message_history(self, channel_id: str, limit: int = 100) -> List[Dict]:
        """チャンネルのメッセージ履歴を取得"""
        return self.adapter.fetch_all(
            "SELECT * FROM message_logs WHERE channel_id = ? ORDER BY created_at DESC LIMIT ?",
            (channel_id, limit)
        )
    
    def search_messages(self, query: str, server_id: str = None, limit: int = 50) -> List[Dict]:
        """メッセージを検索"""
        if server_id:
            return self.adapter.fetch_all(
                "SELECT * FROM message_logs WHERE content LIKE ? AND server_id = ? ORDER BY created_at DESC LIMIT ?",
                (f"%{query}%", server_id, limit)
            )
        else:
            return self.adapter.fetch_all(
                "SELECT * FROM message_logs WHERE content LIKE ? ORDER BY created_at DESC LIMIT ?",
                (f"%{query}%", limit)
            )
    
    # コマンド統計関連メソッド
    def log_command(self, command_name: str, user_id: str, server_id: str, success: bool = True):
        """コマンド使用を記録"""
        self.adapter.execute(
            "INSERT INTO command_stats (command_name, user_id, server_id, success) VALUES (?, ?, ?, ?)",
            (command_name, user_id, server_id, success)
        )
    
    def get_command_stats(self, server_id: str = None, limit: int = 10) -> List[Dict]:
        """コマンド使用統計を取得"""
        if server_id:
            return self.adapter.fetch_all("""
                SELECT command_name, COUNT(*) as usage_count, 
                       SUM(CASE WHEN success THEN 1 ELSE 0 END) as success_count
                FROM command_stats 
                WHERE server_id = ?
                GROUP BY command_name 
                ORDER BY usage_count DESC 
                LIMIT ?
            """, (server_id, limit))
        else:
            return self.adapter.fetch_all("""
                SELECT command_name, COUNT(*) as usage_count,
                       SUM(CASE WHEN success THEN 1 ELSE 0 END) as success_count
                FROM command_stats 
                GROUP BY command_name 
                ORDER BY usage_count DESC 
                LIMIT ?
            """, (limit,))
    
    def close(self):
        """データベース接続を閉じる"""
        self.adapter.disconnect()


# 便利な関数
def create_sqlite_database(path: str = "./bot_data/bot.db") -> BotDatabase:
    """SQLiteデータベースを作成"""
    adapter = SQLiteAdapter(path)
    return BotDatabase(adapter)


# PostgreSQL / MySQL サポート（オプション）
try:
    import psycopg2
    import psycopg2.extras
    
    class PostgreSQLAdapter(DatabaseAdapter):
        """PostgreSQL データベースアダプター"""
        
        def connect(self):
            self.connection = psycopg2.connect(self.connection_string)
            return self.connection
        
        def disconnect(self):
            if self.connection:
                self.connection.close()
                self.connection = None
        
        @contextmanager
        def get_cursor(self):
            if not self.connection:
                self.connect()
            
            cursor = self.connection.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
            try:
                yield cursor
                self.connection.commit()
            except Exception as e:
                self.connection.rollback()
                raise e
            finally:
                cursor.close()
        
        def execute(self, query: str, params: tuple = None):
            with self.get_cursor() as cursor:
                if params:
                    return cursor.execute(query, params)
                else:
                    return cursor.execute(query)
        
        def fetch_one(self, query: str, params: tuple = None) -> Optional[Dict]:
            with self.get_cursor() as cursor:
                if params:
                    cursor.execute(query, params)
                else:
                    cursor.execute(query)
                
                row = cursor.fetchone()
                return dict(row) if row else None
        
        def fetch_all(self, query: str, params: tuple = None) -> List[Dict]:
            with self.get_cursor() as cursor:
                if params:
                    cursor.execute(query, params)
                else:
                    cursor.execute(query)
                
                rows = cursor.fetchall()
                return [dict(row) for row in rows]

except ImportError:
    # psycopg2がインストールされていない場合
    class PostgreSQLAdapter:
        def __init__(self, *args, **kwargs):
            raise ImportError("PostgreSQL サポートには psycopg2 が必要です: pip install psycopg2-binary")


try:
    import mysql.connector
    
    class MySQLAdapter(DatabaseAdapter):
        """MySQL データベースアダプター"""
        
        def connect(self):
            # connection_string をパース（簡易版）
            self.connection = mysql.connector.connect(
                host="localhost",  # connection_string から解析
                user="user",
                password="password",
                database="database"
            )
            return self.connection
        
        # 他のメソッドも実装...

except ImportError:
    # mysql-connectorがインストールされていない場合
    class MySQLAdapter:
        def __init__(self, *args, **kwargs):
            raise ImportError("MySQL サポートには mysql-connector-python が必要です: pip install mysql-connector-python")
