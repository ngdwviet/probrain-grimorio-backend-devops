"""
Repository (persistência).

"Fake DB" em memória e operações CRUD.
Essa camada é a que trocaria por MySQL/DynamoDB no futuro.
"""

from __future__ import annotations

from typing import Dict, List, Optional, Set
from .models import Magia


class MagiaRepository:
    def __init__(self):
        self._by_id: Dict[str, Magia] = {}
        self._index_by_school: Dict[str, Set[str]] = {}
        self._index_by_level: Dict[int, Set[str]] = {}

    def clear(self) -> None:
        self._by_id.clear()
        self._index_by_school.clear()
        self._index_by_level.clear()

    def _index_add(self, magia: Magia) -> None:
        self._index_by_school.setdefault(magia.escola, set()).add(magia.id)
        self._index_by_level.setdefault(magia.nivel, set()).add(magia.id)

    def _index_remove(self, magia: Magia) -> None:
        if magia.escola in self._index_by_school:
            self._index_by_school[magia.escola].discard(magia.id)
        if magia.nivel in self._index_by_level:
            self._index_by_level[magia.nivel].discard(magia.id)

    def insert(self, magia: Magia) -> None:
        self._by_id[magia.id] = magia
        self._index_add(magia)

    def get(self, id_magia: str) -> Optional[Magia]:
        return self._by_id.get(id_magia)

    def delete(self, id_magia: str) -> Optional[Magia]:
        magia = self._by_id.pop(id_magia, None)
        if magia:
            self._index_remove(magia)
        return magia

    def update(self, id_magia: str, magia_atualizada: Magia) -> Optional[Magia]:
        magia_antiga = self._by_id.get(id_magia)
        if not magia_antiga:
            return None
        self._index_remove(magia_antiga)
        self._by_id[id_magia] = magia_atualizada
        self._index_add(magia_atualizada)
        return magia_atualizada

    def query_ids(self, escola: Optional[str], nivel: Optional[int]) -> Optional[Set[str]]:
        # PERF: índices aceleram filtros exatos
        candidates: Optional[Set[str]] = None

        if escola is not None:
            candidates = set(self._index_by_school.get(escola, set()))

        if nivel is not None:
            by_level = set(self._index_by_level.get(nivel, set()))
            candidates = by_level if candidates is None else candidates.intersection(by_level)

        return candidates

    def list(self, ids_subset: Optional[Set[str]] = None) -> List[Magia]:
        if ids_subset is None:
            return list(self._by_id.values())
        return [self._by_id[i] for i in ids_subset if i in self._by_id]


REPO = MagiaRepository()
