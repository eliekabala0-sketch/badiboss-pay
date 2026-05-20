from fastapi import APIRouter

router = APIRouter(tags=["Health"])


@router.get("/")
async def home():
    return {"message": "Badiboss Pay API Running"}


@router.get("/health")
async def health():
    return {"status": "ok"}
