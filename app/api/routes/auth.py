from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_admin, get_db
from app.core.security import create_access_token, verify_password
from app.models.admin_login_history import AdminLoginHistory
from app.models.admin import AdminUser
from app.schemas.auth import AdminPublic, LoginRequest, TokenResponse
from app.services.audit_service import log_security_event

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, request: Request, db: Session = Depends(get_db)):
    client_ip = request.headers.get("x-forwarded-for", "").split(",")[0].strip() or (request.client.host if request.client else None)
    user_agent = request.headers.get("user-agent")
    admin = db.query(AdminUser).filter(AdminUser.email == payload.email).first()
    if not admin or not verify_password(payload.password, admin.hashed_password):
        db.add(AdminLoginHistory(email=payload.email, success=False, ip_address=client_ip, user_agent=user_agent))
        db.commit()
        log_security_event(
            db,
            request=request,
            event_type="AUTH_LOGIN_FAILED",
            severity="warning",
            actor=payload.email,
            details="Invalid credentials",
        )
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    token = create_access_token(subject=admin.email)
    db.add(AdminLoginHistory(email=admin.email, success=True, ip_address=client_ip, user_agent=user_agent))
    db.commit()
    log_security_event(
        db,
        request=request,
        event_type="AUTH_LOGIN_SUCCESS",
        severity="info",
        actor=admin.email,
        details=f"Role={admin.role}",
    )
    return TokenResponse(access_token=token)


@router.get("/me", response_model=AdminPublic)
def me(current_admin: AdminUser = Depends(get_current_admin)):
    return current_admin
