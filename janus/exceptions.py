"""
Janus SDK 例外クラス
"""

class JanusAPIError(Exception):
    """Janus API関連の基底例外クラス"""
    
    def __init__(self, message: str, status_code: int = None, response_data: dict = None):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.response_data = response_data


class PermissionError(JanusAPIError):
    """権限不足エラー"""
    pass


class RateLimitError(JanusAPIError):
    """レート制限エラー"""
    
    def __init__(self, message: str, retry_after: int = None):
        super().__init__(message)
        self.retry_after = retry_after


class ServerNotFoundError(JanusAPIError):
    """サーバーが見つからないエラー"""
    pass


class InvalidTokenError(JanusAPIError):
    """無効なトークンエラー"""
    pass


class ChannelNotFoundError(JanusAPIError):
    """チャンネルが見つからないエラー"""
    pass


class MessageNotFoundError(JanusAPIError):
    """メッセージが見つからないエラー"""
    pass


class UserNotFoundError(JanusAPIError):
    """ユーザーが見つからないエラー"""
    pass


class UserNotFoundError(JanusAPIError):
    """Raised when a user is not found."""
    pass


class ConnectionError(JanusAPIError):
    """Raised when there's a connection error."""
    pass
