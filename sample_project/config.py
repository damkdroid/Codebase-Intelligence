
import os
import logging
from datetime import datetime
from typing import Dict, Any


def load_settings() -> Dict[str, Any]:
    return {
        "app_env": os.getenv("APP_ENV", "development"),
        "database_url": os.getenv("DATABASE_URL", "sqlite:///app.db"),
        "jwt_secret": os.getenv("JWT_SECRET", "super-secret-key-12345"),
        "debug": os.getenv("DEBUG", "true").lower() in ("true", "1"),
        "tax_rate": float(os.getenv("TAX_RATE", "0.0825")),
    }


def setup_logger(name: str = "app") -> logging.Logger:
    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter("[%(asctime)s] [%(levelname)s] %(name)s: %(message)s")
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
    return logger


def format_iso_timestamp(timestamp: datetime = None) -> str:
    if timestamp is None:
        timestamp = datetime.utcnow()
    return timestamp.strftime("%Y-%m-%dT%H:%M:%SZ")
