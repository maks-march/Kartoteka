"""Domain-модели приложения objects."""

from dataclasses import dataclass
from typing import Optional


@dataclass
class ObjectEntity:
    """Чистая доменная модель объекта."""
    id: Optional[int] = None
    name: str = ""
    level: int = 1  # 1, 2 или 3
    category_id: Optional[int] = None
    category_name: Optional[str] = None
