import time
import uuid
import json
from collections import defaultdict, deque

from fastapi import Request
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.db.session import SessionLocal
from app.models.api_log import ApiLog
from app.models.failed_request import FailedRequest
from app.models.ip_blacklist import IpBlacklist
from app.models.security_log import SecurityLog

_RATE_WINDOW_SECONDS = 60
_IP_HITS = defaultdict(deque)


def _extract_client_ip(request: Request):
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else None


async def request_context_middleware(request: Request, call_next):
    request_id = str(uuid.uuid4())
    request.state.request_id = request_id
    started = time.perf_counter()
    response = None
    error_message = None
    client_ip = _extract_client_ip(request)
    db = SessionLocal()
    app_id = request.headers.get("x-badiboss-app-id")
    company_id = request.headers.get("x-badiboss-company-id")
    actor = request.headers.get("x-admin-email")

    blacklisted = False
    if client_ip:
        blacklisted = (
            db.query(IpBlacklist)
            .filter(IpBlacklist.ip_address == client_ip, IpBlacklist.is_active.is_(True))
            .first()
            is not None
        )
    if blacklisted:
        response = JSONResponse(status_code=403, content={"detail": "IP blacklisted"})
    else:
        now_ts = time.time()
        if client_ip:
            hits = _IP_HITS[client_ip]
            while hits and now_ts - hits[0] > _RATE_WINDOW_SECONDS:
                hits.popleft()
            if len(hits) >= settings.rate_limit_per_minute:
                response = JSONResponse(status_code=429, content={"detail": "Rate limit exceeded"})
                db.add(
                    SecurityLog(
                        event_type="RATE_LIMIT_BLOCKED",
                        severity="warning",
                        actor=actor,
                        ip_address=client_ip,
                        user_agent=request.headers.get("user-agent"),
                        app_id=app_id,
                        company_id=company_id,
                        details=f"Path={request.url.path}",
                    )
                )
            else:
                hits.append(now_ts)

    if response is None:
        try:
            response = await call_next(request)
        except Exception as exc:
            error_message = str(exc)
            response = JSONResponse(status_code=500, content={"detail": "Internal server error"})

    duration_ms = int((time.perf_counter() - started) * 1000)
    response.headers["X-Request-ID"] = request_id
    response.headers["X-Process-Time-Ms"] = str(duration_ms)

    app_id = getattr(request.state, "log_app_id", app_id)
    company_id = getattr(request.state, "log_company_id", company_id)

    try:
        db.add(
            ApiLog(
                request_id=request_id,
                method=request.method,
                path=request.url.path,
                status_code=response.status_code,
                duration_ms=duration_ms,
                app_id=app_id,
                company_id=company_id,
                actor=actor,
                error_message=error_message,
            )
        )

        if response.status_code >= 400:
            request_payload = None
            if request.method in {"POST", "PUT", "PATCH"}:
                try:
                    body = await request.body()
                    request_payload = body.decode("utf-8")[:4000] if body else None
                except Exception:
                    request_payload = json.dumps({"error": "payload_unavailable"})

            db.add(
                FailedRequest(
                    request_id=request_id,
                    method=request.method,
                    path=request.url.path,
                    status_code=response.status_code,
                    app_id=app_id,
                    company_id=company_id,
                    payload=request_payload,
                    error_message=error_message,
                )
            )
            db.add(
                SecurityLog(
                    event_type="REQUEST_FAILED",
                    severity="warning",
                    actor=actor,
                    ip_address=client_ip,
                    user_agent=request.headers.get("user-agent"),
                    app_id=app_id,
                    company_id=company_id,
                    details=f"status={response.status_code} path={request.url.path}",
                )
            )
        db.commit()
    finally:
        db.close()

    return response
