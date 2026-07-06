from sqlalchemy import text
from sqlalchemy.orm import Session
from core.logging import get_logger

logger = get_logger("health_service")

def check_liveness() -> dict:
    return {"status": "ok"}

def check_readiness(db: Session) -> dict:
    try:
        db.execute(text("SELECT 1"))
        return {"status": "ready"}
    except Exception as e:
        logger.error(f"Falha na verificação de readiness (banco indisponível): {str(e)}")
        raise
