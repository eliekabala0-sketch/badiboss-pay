from enum import Enum


class AdminRole(str, Enum):
    SUPER_ADMIN = "SUPER_ADMIN"
    FINANCE_ADMIN = "FINANCE_ADMIN"
    SUPPORT_ADMIN = "SUPPORT_ADMIN"
    VIEWER = "VIEWER"
