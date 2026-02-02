"""
Observability.

Logs/métricas (simulados) e correlação por request_id/client_id.
Camada pronta para plugar Datadog/OpenTelemetry sem alterar o domínio.
"""

from __future__ import annotations

import json
import time
import uuid
from typing import Any, Dict


METRICS: Dict[str, Any] = {
    "requests_total": 0,
    "errors_total": 0,
    "requests_by_operation": {},
    "errors_by_operation": {},
    "latency_ms_by_operation": {},
}


def _now_s() -> float:
    return time.time()


def new_request_id() -> str:
    return str(uuid.uuid4())


def log_event(event: Dict[str, Any]) -> None:
    # OBS: log estruturado JSON facilita ingestão em plataformas de observabilidade
    print(json.dumps(event, ensure_ascii=False))


def record_metric(operation: str, latency_ms: float, status: int) -> None:
    METRICS["requests_total"] += 1
    METRICS["requests_by_operation"][operation] = METRICS["requests_by_operation"].get(operation, 0) + 1

    if status >= 400:
        METRICS["errors_total"] += 1
        METRICS["errors_by_operation"][operation] = METRICS["errors_by_operation"].get(operation, 0) + 1

    METRICS["latency_ms_by_operation"].setdefault(operation, []).append(latency_ms)


def instrument(operation: str):
    # OBS: decorator para medir latência + registrar métricas + gerar logs por operação
    def decorator(fn):
        def wrapper(*args, **kwargs):
            request_id = kwargs.get("request_id") or new_request_id()
            start = time.perf_counter()
            res = None
            try:
                res = fn(*args, **kwargs, request_id=request_id)
                return res
            finally:
                latency_ms = (time.perf_counter() - start) * 1000
                status = 500
                if isinstance(res, dict) and "status" in res:
                    status = int(res["status"])
                record_metric(operation, latency_ms, status)
                log_event(
                    {
                        "request_id": request_id,
                        "operation": operation,
                        "latency_ms": round(latency_ms, 2),
                        "status": status,
                    }
                )

        return wrapper

    return decorator
