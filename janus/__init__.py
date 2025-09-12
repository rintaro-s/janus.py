"""
Janus SDK - Discord風チャットプラットフォームのPython SDK

使用例:
    import janus
    
    client = janus.Client(
        host="https://your-janus-server.com",
        token="janus_your_server_token_here"
    )
    
    # チャンネル一覧取得
    channels = client.get_channels()
    
    # メッセージ送信
    message = client.send_message(channels[0].id, "Hello!")
"""

from .client import Client
from .models import Channel, Message, User, Member
from .exceptions import (
    JanusAPIError,
    PermissionError,
    RateLimitError,
    ServerNotFoundError,
    InvalidTokenError
)

__version__ = "1.0.0"
__author__ = "Janus Team"
__license__ = "MIT"

__all__ = [
    "Client",
    "Channel",
    "Message", 
    "User",
    "Member",
    "JanusAPIError",
    "PermissionError",
    "RateLimitError",
    "ServerNotFoundError",
    "InvalidTokenError"
]
