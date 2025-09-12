"""
Janus SDK データモデル
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from dataclasses import dataclass


@dataclass
class User:
    """ユーザー情報"""
    id: str  # Auth0 ID
    name: str
    display_name: Optional[str] = None
    avatar_url: Optional[str] = None
    status: str = "offline"  # "online", "offline", "away"
    roles: List[str] = None
    
    def __post_init__(self):
        if self.roles is None:
            self.roles = []
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'User':
        return cls(
            id=data.get("id", ""),
            name=data.get("name", ""),
            display_name=data.get("display_name", data.get("name", "")),
            avatar_url=data.get("avatar_url"),
            status=data.get("status", "offline"),
            roles=data.get("roles", [])
        )


@dataclass 
class Member:
    """サーバーメンバー情報"""
    id: int
    user: User
    role: str  # "owner", "admin", "member"
    joined_at: datetime
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Member':
        return cls(
            id=data.get("id", 0),
            user=User.from_dict(data.get("user", {})),
            role=data.get("role", "member"),
            joined_at=datetime.fromisoformat(data.get("joined_at", datetime.now().isoformat()))
        )


@dataclass
class Channel:
    """チャンネル情報"""
    id: int
    name: str
    description: str = ""
    type: str = "text"  # "text", "voice", "forum"
    server_id: int = 0
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Channel':
        return cls(
            id=data.get("id", 0),
            name=data.get("name", ""),
            description=data.get("description", ""),
            type=data.get("type", "text"),
            server_id=data.get("server_id", 0),
            created_at=datetime.fromisoformat(data["created_at"]) if data.get("created_at") else None,
            updated_at=datetime.fromisoformat(data["updated_at"]) if data.get("updated_at") else None
        )


@dataclass
class Attachment:
    """添付ファイル情報"""
    id: int
    filename: str
    url: str
    size: int
    content_type: str
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Attachment':
        return cls(
            id=data.get("id", 0),
            filename=data.get("filename", ""),
            url=data.get("url", ""),
            size=data.get("size", 0),
            content_type=data.get("content_type", "")
        )


@dataclass
class Message:
    """メッセージ情報"""
    id: int
    channel_id: int
    author: User
    content: str
    timestamp: datetime
    edited_at: Optional[datetime] = None
    attachments: List[Attachment] = None
    embeds: List[Dict[str, Any]] = None
    
    def __post_init__(self):
        if self.attachments is None:
            self.attachments = []
        if self.embeds is None:
            self.embeds = []
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Message':
        # Handle author field - it might be a string (user_auth0_id) or dict
        author_data = data.get("author", {})
        if isinstance(author_data, str):
            # If author is a string, create a User with minimal info
            author = User(id=author_data, name=author_data, display_name=author_data)
        elif isinstance(author_data, dict):
            author = User.from_dict(author_data)
        else:
            author = User(id="unknown", name="Unknown", display_name="Unknown")
        
        # Handle timestamp/createdAt field
        timestamp_str = data.get("timestamp") or data.get("createdAt")
        if timestamp_str:
            if isinstance(timestamp_str, str):
                timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
            else:
                timestamp = datetime.now()
        else:
            timestamp = datetime.now()
        
        return cls(
            id=data.get("id", 0),
            channel_id=data.get("channel_id") or data.get("channelId", 0),
            author=author,
            content=data.get("content", ""),
            timestamp=timestamp,
            edited_at=datetime.fromisoformat(data["edited_at"]) if data.get("edited_at") else None,
            attachments=[Attachment.from_dict(att) for att in data.get("attachments", [])],
            embeds=data.get("embeds", [])
        )


@dataclass
class Server:
    """サーバー情報"""
    id: int
    name: str
    icon_url: Optional[str] = None
    invite_code: Optional[str] = None
    api_token: Optional[str] = None
    member_count: int = 0
    created_at: Optional[datetime] = None
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Server':
        return cls(
            id=data.get("id", 0),
            name=data.get("name", ""),
            icon_url=data.get("icon_url"),
            invite_code=data.get("invite_code"),
            api_token=data.get("api_token"),
            member_count=data.get("member_count", 0),
            created_at=datetime.fromisoformat(data["created_at"]) if data.get("created_at") else None
        )
