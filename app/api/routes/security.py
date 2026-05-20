from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_db, require_roles
from app.core.roles import AdminRole
from app.models.admin_login_history import AdminLoginHistory
from app.models.ip_blacklist import IpBlacklist
from app.models.security_log import SecurityLog

router = APIRouter(prefix="/security", tags=["Security"])


@router.get("/blacklist")
def list_blacklist(
    db: Session = Depends(get_db),
    _=Depends(require_roles(AdminRole.SUPER_ADMIN, AdminRole.SUPPORT_ADMIN)),
):
    return db.query(IpBlacklist).order_by(IpBlacklist.created_at.desc()).limit(300).all()


@router.post("/blacklist", status_code=status.HTTP_201_CREATED)
def add_blacklist_ip(
    ip_address: str,
    reason: str = "",
    db: Session = Depends(get_db),
    _=Depends(require_roles(AdminRole.SUPER_ADMIN, AdminRole.SUPPORT_ADMIN)),
):
    existing = db.query(IpBlacklist).filter(IpBlacklist.ip_address == ip_address).first()
    if existing:
        existing.is_active = True
        existing.reason = reason or existing.reason
        db.commit()
        db.refresh(existing)
        return existing
    row = IpBlacklist(ip_address=ip_address, reason=reason, is_active=True)
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


@router.delete("/blacklist/{ip_address}")
def remove_blacklist_ip(
    ip_address: str,
    db: Session = Depends(get_db),
    _=Depends(require_roles(AdminRole.SUPER_ADMIN, AdminRole.SUPPORT_ADMIN)),
):
    row = db.query(IpBlacklist).filter(IpBlacklist.ip_address == ip_address).first()
    if not row:
        raise HTTPException(status_code=404, detail="IP not found")
    row.is_active = False
    db.commit()
    return {"success": True}


@router.get("/admin-logins")
def admin_login_history(
    db: Session = Depends(get_db),
    _=Depends(require_roles(AdminRole.SUPER_ADMIN, AdminRole.SUPPORT_ADMIN)),
):
    return db.query(AdminLoginHistory).order_by(AdminLoginHistory.created_at.desc()).limit(500).all()


@router.get("/events")
def security_events(
    db: Session = Depends(get_db),
    _=Depends(require_roles(AdminRole.SUPER_ADMIN, AdminRole.SUPPORT_ADMIN)),
):
    return db.query(SecurityLog).order_by(SecurityLog.created_at.desc()).limit(500).all()
