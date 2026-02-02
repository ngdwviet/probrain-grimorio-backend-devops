"""
Service (regras de negócio).

Responsabilidades:
- aplicar regras do domínio (magias, validações de regra, dano escalável)
- coordenar repository/cache
- NÃO conhecer HTTP/status codes (isso é do controller)
"""

from __future__ import annotations

import uuid
from typing import Any, Dict, List, Optional, Tuple

from .models import Magia, MagiaCreate, MagiaUpdate
from .repository import REPO


def _gen_id() -> str:
    return str(uuid.uuid4())


class MagiaService:
    def create(self, payload: Dict[str, Any]) -> Magia:
        magia_in = MagiaCreate(**payload)
        magia = Magia(id=_gen_id(), **magia_in.model_dump())
        REPO.insert(magia)
        return magia

    def read(self, nome: Optional[str], escola: Optional[str], nivel: Optional[int]) -> List[Magia]:
        # PERF: escola/nivel usam índice; nome parcial filtra em memória
        candidates_ids = REPO.query_ids(escola=escola, nivel=nivel)
        magias = REPO.list(ids_subset=candidates_ids)

        if nome is not None:
            n = nome.strip().lower()
            magias = [m for m in magias if n in m.nome.lower()]

        return magias

    def update(self, id_magia: str, payload: Dict[str, Any]) -> Optional[Magia]:
        existente = REPO.get(id_magia)
        if not existente:
            return None

        patch = MagiaUpdate(**payload).model_dump(exclude_none=True)
        merged = existente.model_dump()
        merged.update(patch)

        magia_atualizada = Magia(**merged)
        REPO.update(id_magia, magia_atualizada)
        return magia_atualizada

    def delete(self, id_magia: str) -> Optional[Magia]:
        return REPO.delete(id_magia)

    def calcular_dano_escala(self, id_magia: str, nivel_slot: int) -> Tuple[Optional[Dict[str, Any]], Optional[Dict[str, Any]], int]:
        magia = REPO.get(id_magia)
        if not magia:
            return None, {"code": "NOT_FOUND", "message": "Magia não encontrada."}, 404

        if magia.tipo != "ataque":
            return None, {"code": "NOT_APPLICABLE", "message": "Magia não é do tipo ataque."}, 422

        if magia.dano_escala is None:
            return None, {"code": "NO_SCALING", "message": "Magia de ataque sem progressão de dano cadastrada."}, 422

        try:
            dano = magia.dano_escala.calcular_para_slot(int(nivel_slot))
            data = {
                "id_magia": magia.id,
                "nome": magia.nome,
                "nivel_magia": magia.nivel,
                "nivel_slot": int(nivel_slot),
                "dano": dano,
            }
            return data, None, 200
        except ValueError as e:
            return None, {"code": "INVALID_SLOT", "message": str(e)}, 400


SERVICE = MagiaService()
