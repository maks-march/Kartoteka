"""Domain-модели приложения categories."""

from dataclasses import dataclass
from typing import Optional


@dataclass
class CategoryEntity:
    """Чистая доменная модель категории."""
    id: Optional[int] = None
    name: str = ""
    level: int = 1  # 1, 2 или 3
