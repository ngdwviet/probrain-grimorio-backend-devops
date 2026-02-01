"""
Controllers (HTTP-like).

Responsabilidades:
- receber inputs como "endpoints"
- chamar o service
- padronizar responses (status + data/error + request_id)
- NÃO conter regra de negócio (isso fica no service)
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional

from pydantic import ValidationError

from .auth import AuthClaims, verify_bearer_token
from .cache import CACHE, RATE_LIMITER
from .observability import instrument, new_request_id
from .service import SERVICE
from .seed import seed_data


CACHE_TTL_SECONDS = 60
LIST_DEFAULT_LIMIT = 20
LIST_MAX_LIMIT = 100

# --- Error Codes (contrato estável para front/back e observabilidade) ---
ERR_VALIDATION = "VALIDATION_ERROR"
ERR_BUSINESS_RULE = "BUSINESS_RULE"
ERR_UNAUTHORIZED = "UNAUTHORIZED"
ERR_FORBIDDEN = "FORBIDDEN"
ERR_RATE_LIMITED = "RATE_LIMITED"
ERR_INVALID_PAGINATION = "INVALID_PAGINATION"
ERR_SPELL_NOT_FOUND = "SPELL_NOT_FOUND"


@dataclass
class RequestContext:
    request_id: str
    client_id: str
    claims: Optional[AuthClaims] = None


def response(status: int, request_id: str, data: Any = None, error: Any = None, meta: Any = None) -> Dict[str, Any]:
    payload: Dict[str, Any] = {"status": status, "request_id": request_id}
    if data is not None:
        payload["data"] = data
    if error is not None:
        payload["error"] = error
    if meta is not None:
        payload["meta"] = meta
    return payload


def magia_to_dict(magia) -> Dict[str, Any]:
    return magia.model_dump()


def _require_write_access(ctx: RequestContext) -> Optional[Dict[str, Any]]:
    # SEC: escrita exige writer/admin
    if not ctx.claims:
        return {"code": ERR_UNAUTHORIZED, "message": "Autenticação necessária."}
    if ctx.claims.role not in {"writer", "admin"}:
        return {"code": ERR_FORBIDDEN, "message": "Permissão insuficiente para escrita."}
    return None


def _rate_limit_or_error(ctx: RequestContext) -> Optional[Dict[str, Any]]:
    # COST: proteção contra volume excessivo
    if not RATE_LIMITER.allow(ctx.client_id):
        return {"code": ERR_RATE_LIMITED, "message": "Limite de requisições excedido (60/min)."}
    return None


def _cache_key_list(nome: Optional[str], escola: Optional[str], nivel: Optional[int], limit: int, offset: int) -> str:
    return f"spells:list:nome={nome}|escola={escola}|nivel={nivel}|limit={limit}|offset={offset}"


def _invalidate_spells_cache() -> None:
    CACHE.invalidate_prefix("spells:list:")


def reset_all_state() -> None:
    # TEST: utilitário para testes e notebook
    seed_data()
    _invalidate_spells_cache()
    RATE_LIMITER.reset()


@instrument("create_magia")
def create_magia_controller(
    payload: Dict[str, Any],
    authorization: Optional[str],
    client_id: str,
    request_id: Optional[str] = None,
) -> Dict[str, Any]:
    request_id = request_id or new_request_id()
    ctx = RequestContext(request_id=request_id, client_id=client_id)

    rl_error = _rate_limit_or_error(ctx)
    if rl_error:
        return response(429, request_id, error=rl_error)

    ok, claims, reason = verify_bearer_token(authorization)
    if not ok:
        return response(401, request_id, error={"code": ERR_UNAUTHORIZED, "message": reason})
    ctx.claims = claims

    perm_error = _require_write_access(ctx)
    if perm_error:
        return response(403, request_id, error=perm_error)

    try:
        magia = SERVICE.create(payload)
        _invalidate_spells_cache()
        return response(201, request_id, data=magia_to_dict(magia))
    except ValidationError as e:
        return response(
            400,
            request_id,
            error={"code": ERR_VALIDATION, "message": "Payload inválido", "details": e.errors()},
        )
    except ValueError as e:
        return response(400, request_id, error={"code": ERR_BUSINESS_RULE, "message": str(e)})


@instrument("read_magias")
def read_magias_controller(
    nome: Optional[str],
    escola: Optional[str],
    nivel: Optional[int],
    limit: Optional[int],
    offset: Optional[int],
    client_id: str,
    request_id: Optional[str] = None,
) -> Dict[str, Any]:
    request_id = request_id or new_request_id()
    ctx = RequestContext(request_id=request_id, client_id=client_id)

    rl_error = _rate_limit_or_error(ctx)
    if rl_error:
        return response(429, request_id, error=rl_error)

    lim = LIST_DEFAULT_LIMIT if limit is None else int(limit)
    off = 0 if offset is None else int(offset)

    if lim <= 0 or lim > LIST_MAX_LIMIT or off < 0:
        return response(
            400,
            request_id,
            error={"code": ERR_INVALID_PAGINATION, "message": "limit deve ser 1..100 e offset >= 0."},
        )

    key = _cache_key_list(nome, escola, nivel, lim, off)
    cached = CACHE.get(key)
    if cached is not None:
        cached["meta"] = {**cached.get("meta", {}), "cache": "hit"}
        return cached

    magias = SERVICE.read(nome=nome, escola=escola, nivel=nivel)
    total = len(magias)
    paged = magias[off : off + lim]

    if total == 0:
        res = response(
            404,
            request_id,
            error={"code": ERR_SPELL_NOT_FOUND, "message": "Nenhuma magia encontrada para os filtros informados."},
        )
        CACHE.set(key, res, CACHE_TTL_SECONDS)
        return res

    res = response(
        200,
        request_id,
        data=[magia_to_dict(m) for m in paged],
        meta={"limit": lim, "offset": off, "returned": len(paged), "total": total, "cache": "miss"},
    )
    CACHE.set(key, res, CACHE_TTL_SECONDS)
    return res


@instrument("update_magia")
def update_magia_controller(
    id_magia: str,
    payload: Dict[str, Any],
    authorization: Optional[str],
    client_id: str,
    request_id: Optional[str] = None,
) -> Dict[str, Any]:
    request_id = request_id or new_request_id()
    ctx = RequestContext(request_id=request_id, client_id=client_id)

    rl_error = _rate_limit_or_error(ctx)
    if rl_error:
        return response(429, request_id, error=rl_error)

    ok, claims, reason = verify_bearer_token(authorization)
    if not ok:
        return response(401, request_id, error={"code": ERR_UNAUTHORIZED, "message": reason})
    ctx.claims = claims

    perm_error = _require_write_access(ctx)
    if perm_error:
        return response(403, request_id, error=perm_error)

    try:
        magia = SERVICE.update(id_magia, payload)
        if not magia:
            return response(404, request_id, error={"code": ERR_SPELL_NOT_FOUND, "message": "Magia não encontrada."})
        _invalidate_spells_cache()
        return response(200, request_id, data=magia_to_dict(magia))
    except ValidationError as e:
        return response(
            400,
            request_id,
            error={"code": ERR_VALIDATION, "message": "Payload inválido", "details": e.errors()},
        )
    except ValueError as e:
        return response(400, request_id, error={"code": ERR_BUSINESS_RULE, "message": str(e)})


@instrument("delete_magia")
def delete_magia_controller(
    id_magia: str,
    authorization: Optional[str],
    client_id: str,
    request_id: Optional[str] = None,
) -> Dict[str, Any]:
    request_id = request_id or new_request_id()
    ctx = RequestContext(request_id=request_id, client_id=client_id)

    rl_error = _rate_limit_or_error(ctx)
    if rl_error:
        return response(429, request_id, error=rl_error)

    ok, claims, reason = verify_bearer_token(authorization)
    if not ok:
        return response(401, request_id, error={"code": ERR_UNAUTHORIZED, "message": reason})
    ctx.claims = claims

    perm_error = _require_write_access(ctx)
    if perm_error:
        return response(403, request_id, error=perm_error)

    removida = SERVICE.delete(id_magia)
    if not removida:
        return response(404, request_id, error={"code": ERR_SPELL_NOT_FOUND, "message": "Magia não encontrada."})

    _invalidate_spells_cache()
    return response(200, request_id, data={"message": "Magia removida com sucesso.", "removed": magia_to_dict(removida)})


@instrument("calcular_dano_escala")
def calcular_dano_escala_controller(
    id_magia: str,
    nivel_slot: int,
    client_id: str,
    request_id: Optional[str] = None,
) -> Dict[str, Any]:
    request_id = request_id or new_request_id()
    ctx = RequestContext(request_id=request_id, client_id=client_id)

    rl_error = _rate_limit_or_error(ctx)
    if rl_error:
        return response(429, request_id, error=rl_error)

    data, err, status = SERVICE.calcular_dano_escala(id_magia, int(nivel_slot))
    if err:
        # padroniza NOT_FOUND quando aplicável
        if isinstance(err, dict) and err.get("code") == "NOT_FOUND":
            err = {"code": ERR_SPELL_NOT_FOUND, "message": err.get("message", "Magia não encontrada.")}
        return response(status, request_id, error=err)

    return response(200, request_id, data=data)
