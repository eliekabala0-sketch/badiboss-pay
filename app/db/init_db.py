from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.roles import AdminRole
from app.core.security import get_password_hash
from app.models.admin import AdminUser


def seed_default_admin(db: Session) -> None:
    existing = db.query(AdminUser).filter(AdminUser.email == settings.admin_email).first()
    if existing:
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
