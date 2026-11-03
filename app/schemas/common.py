from typing import Generic, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")  # type générique : le type des éléments de la liste


class Page(BaseModel, Generic[T]):
    """Réponse paginée : {items, total, limit, offset}."""

    items: list[T]
    total: int   # nombre total d'éléments (toutes pages confondues)
    limit: int
    offset: int


class PaginationParams(BaseModel):
    """Paramètres de pagination communs (limit 20 par défaut, max 100)."""

    limit: int = Field(default=20, ge=1, le=100)
    offset: int = Field(default=0, ge=0)