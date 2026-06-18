from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.roles import AdminRole
from app.core.security import get_password_hash, verify_password
from app.models.admin import AdminUser


def _password_matches_configured_admin_password(hashed_password: str) -> bool:
    try:
        return verify_password(settings.admin_password, hashed_password)
    except Exception:
        return False


def seed_default_admin(db: Session) -> None:
    existing = db.query(AdminUser).filter(AdminUser.email == settings.admin_email).first()
    if existing:
        existing.full_name = settings.admin_full_name
        existing.role = AdminRole.SUPER_ADMIN.value
        existing.is_active = True
        if settings.admin_force_password_reset or not _password_matches_configured_admin_password(existing.hashed_password):
            existing.hashed_password = get_password_hash(settings.admin_password)
        db.commit()
        return

    admin = AdminUser(
        email=settings.admin_email,
        full_name=settings.admin_full_name,
        hashed_password=get_password_hash(settings.admin_password),
        role=AdminRole.SUPER_ADMIN.value,
        is_active=True,
    )
    db.add(admin)
    db.commit()
