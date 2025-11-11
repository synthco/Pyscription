
from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Optional

from ..errors import AuthError


try:
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
except ImportError as exc:
    raise AuthError(
        "You need the google-auth and google-auth-oauthlib packages. "
        "Install them (`pip install google-auth google-auth-oauthlib google-api-python-client`)."
    ) from exc


@dataclass
class AuthPaths:
    client_secrets: Path
    token: Path
    scopes: Iterable[str]


def _resolve_paths(auth_config) -> AuthPaths:
    secrets = Path(getattr(auth_config, "client_secrets_path", ".secrets/client_secrets.json"))
    token = Path(getattr(auth_config, "token_path", ".secrets/token.json"))
    scopes = tuple(getattr(auth_config, "scopes", ("https://www.googleapis.com/auth/drive",)))
    return AuthPaths(client_secrets=secrets, token=token, scopes=scopes)


def _load_stored_credentials(paths: AuthPaths) -> Optional[Credentials]:
    if not paths.token.exists():
        return None
    try:
        creds = Credentials.from_authorized_user_file(str(paths.token), scopes=list(paths.scopes))
    except Exception as exc:
        # If token is broken delete it and re-run auth
        paths.token.unlink(missing_ok=True)
        raise AuthError(f"Failed to read token at {paths.token}: {exc}") from exc
    return creds


def _persist_credentials(paths: AuthPaths, creds: Credentials) -> None:
    paths.token.parent.mkdir(parents=True, exist_ok=True)
    with paths.token.open("w", encoding="utf-8") as fh:
        fh.write(creds.to_json())


def login(auth_config) -> Credentials:
    """Init local OAuth flow and save token."""
    paths = _resolve_paths(auth_config)

    if not paths.client_secrets.exists():
        raise AuthError(
            f"Can't find {paths.client_secrets}. Add client_secrets.json and retry."
        )

    try:
        flow = InstalledAppFlow.from_client_secrets_file(
            str(paths.client_secrets), scopes=list(paths.scopes)
        )
        creds = flow.run_local_server(port=0, open_browser=True)
    except Exception as exc:  # pragma: no cover - depends on browser/network
        raise AuthError(f"Auth failed: {exc}") from exc

    _persist_credentials(paths, creds)
    return creds


def credentials(auth_config) -> Any:
    """Return actual auth data by updating, or execute login"""
    paths = _resolve_paths(auth_config)

    try:
        creds = _load_stored_credentials(paths)
    except AuthError:
        # Broken token file -> call full login
        creds = None

    if creds and creds.expired and creds.refresh_token:
        try:
            creds.refresh(Request())
        except Exception as exc:
            raise AuthError(f"Can't update token {exc}") from exc
        else:
            _persist_credentials(paths, creds)

    if not creds or not creds.valid:
        creds = login(auth_config)

    return creds
