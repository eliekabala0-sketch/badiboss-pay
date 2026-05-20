from fastapi import APIRouter

from app.api.routes.analytics import router as analytics_router
from app.api.routes.apps import router as apps_router
from app.api.routes.auth import router as auth_router
from app.api.routes.dashboard import router as dashboard_router
from app.api.routes.health import router as health_router
from app.api.routes.legacy import router as legacy_router
from app.api.routes.logs import router as logs_router
from app.api.routes.payments import router as payments_router
from app.api.routes.security import router as security_router
from app.api.routes.finance import router as finance_router
from app.api.routes.subscriptions import router as subscriptions_router
from app.api.routes.transactions import router as transactions_router
from app.api.routes.webhooks import router as webhooks_router

api_router = APIRouter()
api_router.include_router(health_router)
api_router.include_router(legacy_router)
api_router.include_router(auth_router)
api_router.include_router(apps_router)
api_router.include_router(payments_router)
api_router.include_router(transactions_router)
api_router.include_router(subscriptions_router)
api_router.include_router(analytics_router)
api_router.include_router(dashboard_router)
api_router.include_router(logs_router)
api_router.include_router(finance_router)
api_router.include_router(security_router)
api_router.include_router(webhooks_router)
