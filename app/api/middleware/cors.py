from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.configs.config import get_settings

settings = get_settings()


def setup_cors(app: FastAPI) -> None:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[settings.FRONTEND_URL, "http://localhost:3000"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
