
import json, logging, os, sys, time, datetime as dt
from typing import Any, Dict

def _ensure_log_dir(log_dir: str):
    if log_dir and not os.path.exists(log_dir):
        os.makedirs(log_dir, exist_ok=True)

class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload: Dict[str, Any] = {
            "level": record.levelname,
            "ts": dt.datetime.utcfromtimestamp(record.created).isoformat() + "Z",
            "msg": record.getMessage(),
            "logger": record.name,
        }
        if record.args and isinstance(record.args, dict):
            payload.update(record.args)
        # Attach extra dict if present
        for key in ("ctx", "stage", "rate_mb_s", "bytes_done", "total", "retries"):
            if hasattr(record, key):
                payload[key] = getattr(record, key)
        return json.dumps(payload, ensure_ascii=False)

def get_logger(name: str = "loadpipe", log_dir: str = ".logs") -> logging.Logger:
    _ensure_log_dir(log_dir)
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger
    logger.setLevel(logging.INFO)

    stream = logging.StreamHandler(sys.stdout)
    stream.setFormatter(JsonFormatter())
    logger.addHandler(stream)

    try:
        fname = os.path.join(log_dir, f"loadpipe-{dt.datetime.utcnow().strftime('%Y%m%d')}.log")
        file_handler = logging.FileHandler(fname, encoding="utf-8")
        file_handler.setFormatter(JsonFormatter())
        logger.addHandler(file_handler)
    except Exception:
        # Best-effort logging to file
        pass
    return logger

def log_progress(logger: logging.Logger, stage: str, bytes_done: int, total: int | None, retries: int, rate_mb_s: float | None):
    extra = {
        "stage": stage,
        "bytes_done": bytes_done,
        "total": total,
        "retries": retries,
        "rate_mb_s": rate_mb_s,
    }
    logger.info(f"progress", extra=extra)
