"""
Janus SDK メインクライアント
"""

import requests
import time
import asyncio
try:
    import websockets
    _WEBSOCKETS_AVAILABLE = True
except Exception:
    websockets = None
    _WEBSOCKETS_AVAILABLE = False
import json
from typing import List, Optional, Dict, Any, Callable, Union
from urllib.parse import urljoin, urlparse

from .models import Channel, Message, User, Member, Server, Attachment
from .exceptions import (
    JanusAPIError,
    PermissionError,
    RateLimitError,
    ServerNotFoundError,
    InvalidTokenError,
    ChannelNotFoundError,
    MessageNotFoundError,
    UserNotFoundError,
    ConnectionError
)


class Client:
    def get_user_profile(self, user_id: str) -> User:
        """
        UserProfile（表示名・アイコン）を取得
        Args:
            user_id: Auth0 ID
        Returns:
            User（display_name, avatar_url含む）
        """
        response = self._make_request("GET", f"/users/profile", params={"auth0_id": user_id})
        return User.from_dict(response)
    """
    Janus SDKのメインクライアントクラス
    
    使用例:
        client = Client(
            host="https://your-janus-server.com",
            token="janus_your_server_token_here"
        )
        
        channels = client.get_channels()
        message = client.send_message(channels[0].id, "Hello!")
    """
    
    def __init__(
        self,
        host: str,
        token: str,
    use_server_token: bool = False,
    skip_initialization: bool = False,
        timeout: int = 30,
        retry_attempts: int = 3,
        rate_limit_per_minute: int = 60,
        auto_reconnect: bool = True,
        debug: bool = False,
        user_agent: str = "Janus-SDK/1.0"
    ):
        """
        クライアント初期化
        
        Args:
            host: JanusサーバーのURL (例: "https://your-janus-server.com")
            token: サーバーAPIトークン (例: "janus_abc123...")
            timeout: リクエストタイムアウト（秒）
            retry_attempts: 再試行回数
            rate_limit_per_minute: 分あたりリクエスト制限
            auto_reconnect: WebSocket自動再接続
            debug: デバッグモード
            user_agent: ユーザーエージェント
        """
        self.host = host.rstrip('/')
        self.token = token
        self.timeout = timeout
        self.retry_attempts = retry_attempts
        self.rate_limit_per_minute = rate_limit_per_minute
        self.auto_reconnect = auto_reconnect
        self.debug = debug
        
        # APIエンドポイント
        self.api_base = f"{self.host}/api/v1"

        # HTTPセッション
        self.session = requests.Session()
        # 認証方式: デフォルトは Auth0 の Bearer JWT を想定
        if use_server_token:
            # サーバー向けのシンプルなトークンヘッダーを追加（バックエンド側で受け付けるよう実装されている場合）
            # 互換性のため、X-Server-Token と Authorization: Token <token> を両方セット
            self.session.headers.update({
                "X-Server-Token": token,
                "Authorization": f"Token {token}",
                "User-Agent": user_agent,
                "Content-Type": "application/json"
            })
        else:
            self.session.headers.update({
                "Authorization": f"Bearer {token}",
                "User-Agent": user_agent,
                "Content-Type": "application/json"
            })
        
        if self.debug:
            print(f"[Janus SDK] api_base={self.api_base}")
            print(f"[Janus SDK] headers={dict(self.session.headers)}")
        
        # レート制限管理
        self._request_times = []
        
        # WebSocket接続
        self._ws = None
        self._event_handlers = {}
        self._running = False
        
        # キャッシュ
        self._channels_cache = {}
        self._users_cache = {}
        self._server_info = None
        # 初期化時にサーバー情報取得（必要に応じてスキップ可能）
        if not skip_initialization:
            self._initialize()
    
    def _initialize(self):
        """初期化処理"""
        try:
            # トークンの検証とサーバー情報取得
            response = self._make_request("GET", "/servers")
            if response and len(response) > 0:
                self._server_info = Server.from_dict(response[0])
                if self.debug:
                    print(f"[Janus SDK] 接続成功: {self._server_info.name}")
            else:
                raise InvalidTokenError("無効なトークンまたはサーバーアクセス権限がありません")
        except Exception as e:
            if self.debug:
                print(f"[Janus SDK] 初期化エラー: {e}")
            raise
    
    def _make_request(
        self, 
        method: str, 
        endpoint: str, 
        data: Dict[str, Any] = None,
        params: Dict[str, Any] = None,
        files: Dict[str, Any] = None
    ) -> Any:
        """
        API リクエスト実行
        
        Args:
            method: HTTPメソッド
            endpoint: APIエンドポイント
            data: リクエストボディ
            params: クエリパラメータ
            files: ファイルアップロード
            
        Returns:
            APIレスポンス
            
        Raises:
            JanusAPIError: API エラー
        """
        # レート制限チェック
        self._check_rate_limit()
        
        # URLを正しく構築
        if endpoint.startswith('/'):
            endpoint = endpoint[1:]  # 先頭の/を削除
        url = f"{self.api_base}/{endpoint}"
        
        for attempt in range(self.retry_attempts):
            try:
                if self.debug:
                    print(f"[Janus SDK] {method} {url}")
                    print(f"[Janus SDK] headers={dict(self.session.headers)}")
                
                kwargs = {
                    "timeout": self.timeout,
                    "params": params
                }
                
                if files:
                    kwargs["files"] = files
                    if data:
                        kwargs["data"] = data
                else:
                    if data:
                        kwargs["json"] = data
                
                response = self.session.request(method, url, **kwargs)
                
                if self.debug:
                    print(f"[Janus SDK] response status: {response.status_code}")
                    try:
                        print(f"[Janus SDK] response body: {response.text[:500]}")
                    except:
                        print(f"[Janus SDK] response body: <unable to decode>")
                
                # レート制限記録
                self._request_times.append(time.time())
                
                if response.status_code == 401:
                    raise InvalidTokenError("認証に失敗しました。トークンを確認してください")
                elif response.status_code == 403:
                    raise PermissionError("この操作を実行する権限がありません")
                elif response.status_code == 404:
                    raise ServerNotFoundError("指定されたリソースが見つかりません")
                elif response.status_code == 429:
                    retry_after = int(response.headers.get("Retry-After", 60))
                    raise RateLimitError("レート制限に達しました", retry_after)
                elif response.status_code >= 400:
                    error_data = response.json() if response.headers.get("content-type", "").startswith("application/json") else {}
                    raise JanusAPIError(
                        f"API エラー: {response.status_code}",
                        response.status_code,
                        error_data
                    )
                
                # 成功レスポンス
                if response.headers.get("content-type", "").startswith("application/json"):
                    return response.json()
                else:
                    return response.content
                    
            except requests.exceptions.ConnectionError:
                if attempt == self.retry_attempts - 1:
                    raise ConnectionError(f"サーバーに接続できません: {self.host}")
                time.sleep(2 ** attempt)  # 指数バックオフ
            except requests.exceptions.Timeout:
                if attempt == self.retry_attempts - 1:
                    raise ConnectionError("リクエストがタイムアウトしました")
                time.sleep(2 ** attempt)
    
    def _check_rate_limit(self):
        """レート制限チェック"""
        now = time.time()
        # 1分以内のリクエストを数える
        self._request_times = [t for t in self._request_times if now - t < 60]
        
        if len(self._request_times) >= self.rate_limit_per_minute:
            sleep_time = 60 - (now - self._request_times[0])
            if self.debug:
                print(f"[Janus SDK] レート制限により {sleep_time:.1f}秒待機")
            time.sleep(sleep_time)
    
    # チャンネル操作
    def get_channels(self, force_refresh: bool = False) -> List[Channel]:
        """
        チャンネル一覧取得
        
        Args:
            force_refresh: キャッシュを無視して最新データを取得
            
        Returns:
            チャンネルリスト
        """
        if not force_refresh and self._channels_cache:
            return list(self._channels_cache.values())
        
        if not self._server_info:
            raise ServerNotFoundError("サーバー情報が取得できません")
        
        response = self._make_request("GET", f"/servers/{self._server_info.id}/channels")
        channels = [Channel.from_dict(ch) for ch in response]
        
        # キャッシュ更新
        self._channels_cache = {ch.id: ch for ch in channels}
        
        return channels
    
    def get_channel(self, channel_id: int) -> Channel:
        """
        チャンネル情報取得
        
        Args:
            channel_id: チャンネルID
            
        Returns:
            チャンネル情報
        """
        # キャッシュから検索
        if channel_id in self._channels_cache:
            return self._channels_cache[channel_id]
        
        # キャッシュになければ一覧を更新
        channels = self.get_channels(force_refresh=True)
        channel = next((ch for ch in channels if ch.id == channel_id), None)
        
        if not channel:
            raise ChannelNotFoundError(f"チャンネル ID {channel_id} が見つかりません")
        
        return channel
    
    def create_channel(
        self, 
        name: str, 
        description: str = "", 
        type: str = "text"
    ) -> Channel:
        """
        チャンネル作成
        
        Args:
            name: チャンネル名
            description: チャンネル説明
            type: チャンネルタイプ ("text", "voice", "forum")
            
        Returns:
            作成されたチャンネル
        """
        if not self._server_info:
            raise ServerNotFoundError("サーバー情報が取得できません")
        
        data = {
            "name": name,
            "description": description,
            "type": type
        }
        
        response = self._make_request(
            "POST", 
            f"/servers/{self._server_info.id}/channels", 
            data=data
        )
        
        channel = Channel.from_dict(response)
        # キャッシュ更新
        self._channels_cache[channel.id] = channel
        
        return channel
    
    def delete_channel(self, channel_id: int) -> bool:
        """
        チャンネル削除
        
        Args:
            channel_id: チャンネルID
            
        Returns:
            削除成功フラグ
        """
        if not self._server_info:
            raise ServerNotFoundError("サーバー情報が取得できません")
        
        self._make_request("DELETE", f"/servers/{self._server_info.id}/channels/{channel_id}")
        
        # キャッシュから削除
        self._channels_cache.pop(channel_id, None)
        
        return True
    
    # メッセージ操作
    def send_message(
        self, 
        channel_id: int, 
        content: str,
        embeds: List[Dict[str, Any]] = None
    ) -> Message:
        """
        メッセージ送信
        
        Args:
            channel_id: チャンネルID
            content: メッセージ内容
            embeds: 埋め込みコンテンツ
            
        Returns:
            送信されたメッセージ
        """
        if not self._server_info:
            raise ServerNotFoundError("サーバー情報が取得できません")
        
        data = {
            "content": content
        }
        if embeds:
            data["embeds"] = embeds
        
        response = self._make_request(
            "POST",
            f"/servers/{self._server_info.id}/channels/{channel_id}/messages",
            data=data
        )
        
        return Message.from_dict(response)
    
    def get_messages(
        self,
        channel_id: int,
        limit: int = 50,
        before: Optional[int] = None,
        after: Optional[int] = None
    ) -> List[Message]:
        """
        メッセージ履歴取得
        
        Args:
            channel_id: チャンネルID
            limit: 取得件数
            before: 指定メッセージより前
            after: 指定メッセージより後
            
        Returns:
            メッセージリスト
        """
        if not self._server_info:
            raise ServerNotFoundError("サーバー情報が取得できません")
        
        params = {"limit": limit}
        if before:
            params["before"] = before
        if after:
            params["after"] = after
        
        response = self._make_request(
            "GET",
            f"/servers/{self._server_info.id}/channels/{channel_id}/messages",
            params=params
        )
        
        return [Message.from_dict(msg) for msg in response]
    
    def edit_message(self, message_id: int, content: str) -> Message:
        """
        メッセージ編集
        
        Args:
            message_id: メッセージID
            content: 新しい内容
            
        Returns:
            編集されたメッセージ
        """
        # TODO: 実装（バックエンド側でエンドポイント追加が必要）
        raise NotImplementedError("メッセージ編集機能は今後実装予定です")
    
    def delete_message(self, message_id: int) -> bool:
        """
        メッセージ削除
        
        Args:
            message_id: メッセージID
            
        Returns:
            削除成功フラグ
        """
        # TODO: 実装（バックエンド側でエンドポイント追加が必要）
        raise NotImplementedError("メッセージ削除機能は今後実装予定です")
    
    # ファイル操作
    def send_file(
        self,
        channel_id: int,
        file_path: str,
        message: str = ""
    ) -> Message:
        """
        ファイル送信
        
        Args:
            channel_id: チャンネルID
            file_path: ファイルパス
            message: 追加メッセージ
            
        Returns:
            送信されたメッセージ
        """
        import os
        
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"ファイルが見つかりません: {file_path}")
        
        if not self._server_info:
            raise ServerNotFoundError("サーバー情報が取得できません")
        
        with open(file_path, 'rb') as f:
            files = {
                'file': (os.path.basename(file_path), f, 'application/octet-stream')
            }
            data = {}
            if message:
                data['message'] = message
            
            response = self._make_request(
                "POST",
                f"/servers/{self._server_info.id}/channels/{channel_id}/files",
                data=data,
                files=files
            )
        
        return Message.from_dict(response)
    
    def send_image(
        self,
        channel_id: int,
        image_path: str,
        message: str = ""
    ) -> Message:
        """
        画像送信
        
        Args:
            channel_id: チャンネルID
            image_path: 画像ファイルパス
            message: 追加メッセージ
            
        Returns:
            送信されたメッセージ
        """
        return self.send_file(channel_id, image_path, message)
    
    # ユーザー・メンバー操作
    def get_members(self) -> List[Member]:
        """
        サーバーメンバー一覧取得
        
        Returns:
            メンバーリスト
        """
        if not self._server_info:
            raise ServerNotFoundError("サーバー情報が取得できません")
        
        response = self._make_request("GET", f"/servers/{self._server_info.id}/members")
        return [Member.from_dict(member) for member in response]
    
    def get_user(self, user_id: str) -> User:
        """
        ユーザー情報取得
        
        Args:
            user_id: ユーザーID
            
        Returns:
            ユーザー情報
        """
        # キャッシュから検索
        if user_id in self._users_cache:
            return self._users_cache[user_id]
        
        # メンバー一覧から検索
        members = self.get_members()
        user = next((member.user for member in members if member.user.id == user_id), None)
        
        if not user:
            raise UserNotFoundError(f"ユーザー ID {user_id} が見つかりません")
        
        # キャッシュ更新
        self._users_cache[user_id] = user
        
        return user
    
    def get_online_members(self) -> List[Member]:
        """
        オンラインメンバー取得
        
        Returns:
            オンラインメンバーリスト
        """
        members = self.get_members()
        return [member for member in members if member.user.status == "online"]
    
    # 権限管理
    def has_permission(self, user_id: str, permission: str, channel_id: int = None) -> bool:
        """
        権限チェック
        
        Args:
            user_id: ユーザーID
            permission: 権限名
            channel_id: チャンネルID (チャンネル固有権限の場合)
            
        Returns:
            権限有無
        """
        try:
            members = self.get_members()
            member = next((m for m in members if m.user.id == user_id), None)
            
            if not member:
                return False
            
            # オーナーは全権限あり
            if member.role == "owner":
                return True
            
            # 基本的な権限マッピング
            permission_map = {
                "SEND_MESSAGES": ["owner", "admin", "member"],
                "DELETE_MESSAGES": ["owner", "admin"],
                "MANAGE_CHANNELS": ["owner", "admin"],
                "MANAGE_SERVER": ["owner"],
                "INVITE_USERS": ["owner", "admin", "member"]
            }
            
            allowed_roles = permission_map.get(permission, [])
            return member.role in allowed_roles
            
        except Exception:
            return False
    
    def is_admin(self, user_id: str) -> bool:
        """
        管理者権限チェック
        
        Args:
            user_id: ユーザーID
            
        Returns:
            管理者権限有無
        """
        try:
            members = self.get_members()
            member = next((m for m in members if m.user.id == user_id), None)
            return member and member.role in ["owner", "admin"]
        except Exception:
            return False
    
    # イベント処理
    def event(self, func: Callable):
        """
        イベントハンドラーデコレータ
        
        使用例:
            @client.event
            async def on_message(message):
                print(f"新しいメッセージ: {message.content}")
        """
        event_name = func.__name__
        self._event_handlers[event_name] = func
        return func
    
    def set_webhook_url(self, webhook_url: str, secret: str = None):
        """
        Webhook URL設定
        
        Args:
            webhook_url: WebhookのURL
            secret: Webhook検証用シークレット
        """
        # TODO: 実装（バックエンド側でWebhook設定エンドポイント追加が必要）
        self._webhook_url = webhook_url
        self._webhook_secret = secret
        if self.debug:
            print(f"[Janus SDK] Webhook URL設定: {webhook_url}")
    
    async def _handle_websocket_message(self, message: str):
        """WebSocketメッセージハンドラー"""
        try:
            data = json.loads(message)
            event_type = data.get("type")
            
            if event_type == "message" and "on_message" in self._event_handlers:
                message_obj = Message.from_dict(data.get("data", {}))
                await self._event_handlers["on_message"](message_obj)
            elif event_type == "member_join" and "on_member_join" in self._event_handlers:
                member_obj = Member.from_dict(data.get("data", {}))
                await self._event_handlers["on_member_join"](member_obj)
            elif event_type == "channel_create" and "on_channel_create" in self._event_handlers:
                channel_obj = Channel.from_dict(data.get("data", {}))
                await self._event_handlers["on_channel_create"](channel_obj)
                
        except Exception as e:
            if self.debug:
                print(f"[Janus SDK] WebSocketメッセージ処理エラー: {e}")
    
    async def _websocket_connection(self):
        """WebSocket接続処理"""
        if not self._server_info:
            return
        if not _WEBSOCKETS_AVAILABLE:
            if self.debug:
                print("[Janus SDK] websockets ライブラリが見つかりません。WebSocketは無効化されます。")
            return

        # WebSocket URL構築
        ws_url = self.host.replace("http://", "ws://").replace("https://", "wss://")
        ws_url += f"/ws/servers/{self._server_info.id}?token={self.token}"

        while self._running:
            try:
                if self.debug:
                    print(f"[Janus SDK] WebSocket接続中: {ws_url}")
                
                async with websockets.connect(ws_url) as websocket:
                    self._ws = websocket
                    
                    # 準備完了イベント
                    if "on_ready" in self._event_handlers:
                        await self._event_handlers["on_ready"]()
                    
                    # メッセージ受信ループ
                    async for message in websocket:
                        await self._handle_websocket_message(message)
                        
            except Exception as e:
                if self.debug:
                    print(f"[Janus SDK] WebSocket エラー: {e}")
                
                if self.auto_reconnect and self._running:
                    await asyncio.sleep(5)  # 5秒後に再接続
                else:
                    break
    
    def run(self):
        """
        イベントループ開始
        
        WebSocket接続を開始してリアルタイムイベントを受信します。
        """
        if not self._event_handlers:
            if self.debug:
                print("[Janus SDK] イベントハンドラーが設定されていません")
            return
        
        self._running = True
        
        try:
            if self.debug:
                print("[Janus SDK] イベントループ開始")
            
            asyncio.run(self._websocket_connection())
            
        except KeyboardInterrupt:
            if self.debug:
                print("[Janus SDK] 中断されました")
        finally:
            self._running = False
    
    def stop(self):
        """イベントループ停止"""
        self._running = False
        if self._ws:
            asyncio.create_task(self._ws.close())
    
    # プロパティ
    @property
    def user(self) -> Optional[User]:
        """現在のユーザー情報"""
        # TODO: 実装（認証されたユーザー情報の取得）
        return None
    
    @property
    def server(self) -> Optional[Server]:
        """接続中のサーバー情報"""
        return self._server_info
    
    def __repr__(self):
        return f"<Client host='{self.host}' server='{self._server_info.name if self._server_info else 'Unknown'}'>"
