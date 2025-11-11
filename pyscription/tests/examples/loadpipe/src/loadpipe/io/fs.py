
import os, tempfile, shutil

def ensure_dir(path: str):
    if path and not os.path.exists(path):
        os.makedirs(path, exist_ok=True)

def atomic_write(path: str, data_iter):
    ensure_dir(os.path.dirname(path) or ".")
    dir_name = os.path.dirname(path) or "."
    fd, tmp = tempfile.mkstemp(prefix=".tmp.", dir=dir_name)
    try:
        with os.fdopen(fd, "wb") as f:
            for chunk in data_iter:
                f.write(chunk)
        os.replace(tmp, path)
    finally:
        try:
            if os.path.exists(tmp):
                os.remove(tmp)
        except Exception:
            pass
