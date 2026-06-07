"""Domain-модели приложения users."""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class UserEntity:
    """Чистая доменная модель пользователя (без привязки к Django ORM)."""
    id: Optional[int] = None
    username: str = ""
    email: str = ""
    password_hash: str = ""
    is_active: bool = True
    is_staff: bool = False
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
