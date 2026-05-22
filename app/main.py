from fastapi import FastAPI

from app.api.v1.auth import router as auth_router

app = FastAPI(
    title="PriceGrid",
    description="Market price intelligence API",
    version="0.1.0",
)

app.include_router(auth_router, prefix="/api/v1")


@app.get("/health", tags=["health"])
async def health():
    return {"status": "ok"}
