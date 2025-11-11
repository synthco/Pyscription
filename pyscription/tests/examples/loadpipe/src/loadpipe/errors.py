from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping, Optional


class LoadpipeError(Exception):
    """Base exception for the loadpipe package."""

    default_message = "Unknown loadpipe error."

    def __init__(
        self,
        message: Optional[str] = None,
        *,
        hint: Optional[str] = None,
        context: Optional[Mapping[str, Any]] = None,
    ) -> None:
        final_message = (message or self.default_message).strip()
        super().__init__(final_message)
        self.message = final_message
        self.hint = hint
        self.context = dict(context or {})

    def __str__(self) -> str:
        if self.hint:
            return f"{self.message} (hint: {self.hint})"
        return self.message

    def as_dict(self) -> dict[str, Any]:
        data: dict[str, Any] = {"type": self.__class__.__name__, "message": self.message}
        if self.hint:
            data["hint"] = self.hint
        if self.context:
            data["context"] = self.context
        return data


class AuthError(LoadpipeError):
    """Issues related to Google OAuth authentication flows."""

    default_message = "Authentication failed."

    def __init__(
        self,
        message: Optional[str] = None,
        *,
        path: Optional[Path | str] = None,
        hint: Optional[str] = None,
        context: Optional[Mapping[str, Any]] = None,
    ) -> None:
        ctx = dict(context or {})
        if path is not None:
            ctx.setdefault("path", str(path))
            hint = hint or "Check client_secrets.json and stored token."
        super().__init__(message, hint=hint, context=ctx)


class ConfigError(LoadpipeError):
    """Raised when configuration parsing or validation fails."""

    default_message = "Unable to process configuration."

    def __init__(
        self,
        message: Optional[str] = None,
        *,
        path: Optional[Path | str] = None,
        hint: Optional[str] = None,
        context: Optional[Mapping[str, Any]] = None,
    ) -> None:
        ctx = dict(context or {})
        if path is not None:
            ctx.setdefault("path", str(path))
            hint = hint or "Verify the config file and its schema."
        super().__init__(message, hint=hint, context=ctx)


class RateLimitError(LoadpipeError):
    """API request rate limit exceeded."""

    default_message = "Rate limit exceeded."

    def __init__(
        self,
        message: Optional[str] = None,
        *,
        retry_after: Optional[int] = None,
        hint: Optional[str] = None,
        context: Optional[Mapping[str, Any]] = None,
    ) -> None:
        ctx = dict(context or {})
        if retry_after is not None:
            ctx.setdefault("retry_after", retry_after)
            hint = hint or f"Retry after {retry_after} seconds."
        super().__init__(message, hint=hint, context=ctx)


class ResumeMismatchError(LoadpipeError):
    """Stored metadata does not match the remote file anymore."""

    default_message = "Cached metadata no longer matches the server file."


class IntegrityError(LoadpipeError):
    """Local cache or manifest integrity issue."""

    default_message = "Manifest or cache appears corrupted."


class StorageOptionsError(LoadpipeError):
    """Raised when filesystem storage kwargs are missing or invalid."""

    default_message = "Invalid filesystem storage options."


class DrivePathError(LoadpipeError):
    """Raised when a Drive URL cannot be parsed."""

    default_message = "Drive URL is invalid."
