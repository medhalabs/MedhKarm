"""The API. Add routes here (or in app/routes/ once it grows); data goes through app.store."""

import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.store import Store

app = FastAPI(title="API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        o for o in os.environ.get("CORS_ORIGINS", "http://localhost:3000").split(",") if o
    ],
    allow_methods=["*"],
    allow_headers=["*"],
)
store = Store()


@app.get("/health")
def health() -> dict[str, bool]:
    return {"ok": True}
