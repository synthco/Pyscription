
from __future__ import annotations
import json
import re
import time
from dataclasses import dataclass
from typing import Any, Callable, Iterable, List, Optional

from googleapiclient.discovery import build as _build
from googleapiclient.errors import HttpError

RETRYABLE_STATUS_CODES = {429}
RETRY_DELAY_BASE = 1.0
MAX_RETRIES = 5


def _should_retry(status: Optional[int]) -> bool:
    return status in RETRYABLE_STATUS_CODES or (status is not None and 500 <= status < 600)


def _execute_with_retries(action: Callable[[], Any]) -> Any:
    attempt = 0
    while True:
        try:
            return action()
        except HttpError as exc:
            status = getattr(exc, "status_code", None) or getattr(getattr(exc, "resp", None), "status", None)
            if attempt >= MAX_RETRIES or not _should_retry(status):
                raise
            sleep_for = RETRY_DELAY_BASE * (2 ** attempt)
            time.sleep(sleep_for)
            attempt += 1


def _authorized_http(service: Any):
    http = getattr(service, "_http", None)
    if http is None:
        raise ValueError("Service does not expose authorized HTTP client (_http)")
    return http


def _http_request_with_retries(service: Any, url: str, *, method: str, headers: Optional[dict] = None, body: Optional[bytes] = None):
    http = _authorized_http(service)

    def _do_request():
        response, content = http.request(url, method=method, headers=headers or {}, body=body)
        status = getattr(response, "status", None)
        if _should_retry(status):
            raise HttpError(response, content, uri=url)
        if status is not None and status >= 400 and status not in {308}:  # 308 == resumable upload incomplete
            raise HttpError(response, content, uri=url)
        return response, content

    return _execute_with_retries(_do_request)

@dataclass
class FileMeta:
    id: str
    name: str
    size: Optional[int] = None
    md5: Optional[str] = None
    mime: Optional[str] = None
    modified: Optional[str] = None

@dataclass
class UploadSession:
    session_url: str
    name: str
    folder_id: str
    total: Optional[int] = None

def build_service(credentials: Any) -> Any:
    """Construct a Google Drive API v3 client."""

    def _build_action():
        return _build("drive", "v3", credentials=credentials, cache_discovery=False)

    try:
        return _execute_with_retries(_build_action)
    except HttpError as exc:
        raise RuntimeError(f"Failed to initialize Google Drive service: {exc}") from exc

def list_files(service: Any, folder_id: str, pattern: Optional[str] = None) -> List[FileMeta]:
    """Return a list of files for a given Drive folder."""

    query_parts = [f"'{folder_id}' in parents", "trashed = false"]
    if pattern:
        escaped = pattern.replace("'", "\'")
        query_parts.append(f"name contains '{escaped}'")
    query = " and ".join(query_parts)

    request = service.files().list(
        q=query,
        spaces="drive",
        fields="files(id, name, size, md5Checksum, mimeType, modifiedTime)",
    )

    response = _execute_with_retries(request.execute)
    files: Iterable[dict[str, Any]] = response.get("files", [])
    result: List[FileMeta] = []
    for item in files:
        size = int(item["size"]) if item.get("size") is not None else None
        result.append(
            FileMeta(
                id=item.get("id", ""),
                name=item.get("name", ""),
                size=size,
                md5=item.get("md5Checksum"),
                mime=item.get("mimeType"),
                modified=item.get("modifiedTime"),
            )
        )
    return result

def stat(service: Any, file_id: str) -> FileMeta:
    request = service.files().get(
        fileId=file_id,
        fields="id, name, size, md5Checksum, mimeType, modifiedTime",
    )

    info = _execute_with_retries(request.execute)
    size = int(info["size"]) if info.get("size") is not None else None
    return FileMeta(
        id=info.get("id", file_id),
        name=info.get("name", ""),
        size=size,
        md5=info.get("md5Checksum"),
        mime=info.get("mimeType"),
        modified=info.get("modifiedTime"),
    )

def download_range(service: Any, file_id: str, start: int, end: int) -> bytes:
    if start < 0 or end < start:
        raise ValueError("Invalid byte range")

    url = f"https://www.googleapis.com/drive/v3/files/{file_id}?alt=media"
    headers = {"Range": f"bytes={start}-{end}"}
    response, content = _http_request_with_retries(
        service, url, method="GET", headers=headers
    )
    status = getattr(response, "status", None)
    if status not in {200, 206}:
        raise HttpError(response, content, uri=url)
    return content or b""

def begin_resumable_upload(service: Any, name: str, folder_id: str, size: Optional[int] = None, mime: str = "application/octet-stream") -> UploadSession:
    metadata: dict[str, Any] = {"name": name, "mimeType": mime}
    if folder_id:
        metadata["parents"] = [folder_id]

    body = json.dumps(metadata).encode("utf-8")
    headers = {
        "Content-Type": "application/json; charset=UTF-8",
        "X-Upload-Content-Type": mime,
    }
    if size is not None:
        headers["X-Upload-Content-Length"] = str(size)

    url = "https://www.googleapis.com/upload/drive/v3/files?uploadType=resumable"
    response, _ = _http_request_with_retries(
        service, url, method="POST", headers=headers, body=body
    )
    session_url = response.get("location") or response.get("Location")
    if not session_url:
        raise RuntimeError("Unable to obtain upload session Location header")

    return UploadSession(session_url=session_url, name=name, folder_id=folder_id, total=size)


def query_upload_status(service: Any, session: UploadSession, total: Optional[int] = None) -> int:
    """Return the next expected byte offset for a resumable upload session."""

    total_bytes = total or session.total
    range_total = str(total_bytes) if total_bytes is not None else "*"
    headers = {
        "Content-Length": "0",
        "Content-Range": f"bytes */{range_total}",
        "Content-Type": "application/octet-stream",
    }

    def _do_request():
        response, content = _authorized_http(service).request(
            session.session_url,
            method="PUT",
            headers=headers,
            body=b"",
        )
        status = getattr(response, "status", None)
        if _should_retry(status):
            raise HttpError(response, content, uri=session.session_url)
        if status is not None and status >= 400 and status not in {308}:
            raise HttpError(response, content, uri=session.session_url)
        return response, content

    response, content = _execute_with_retries(_do_request)
    status = getattr(response, "status", None)
    if status == 308:
        range_header = response.get("Range") or response.get("range")
        if range_header:
            match = re.search(r"bytes=(\d+)-(\d+)", range_header)
            if match:
                return int(match.group(2)) + 1
        return 0

    if status in {200, 201}:
        if content:
            try:
                payload = json.loads(content.decode("utf-8"))
                if "size" in payload:
                    return int(payload["size"])
            except (ValueError, TypeError):
                pass
        if total_bytes is not None:
            return int(total_bytes)

    return 0


def upload_chunk(service: Any, session: UploadSession, data: bytes, start: int, end: int, total: Optional[int] = None) -> int:
    if end < start:
        raise ValueError("Invalid chunk boundaries")
    if len(data) != end - start + 1:
        raise ValueError("Chunk buffer length does not match Content-Range")

    total_bytes = total or session.total
    range_total = str(total_bytes) if total_bytes is not None else "*"
    headers = {
        "Content-Length": str(len(data)),
        "Content-Range": f"bytes {start}-{end}/{range_total}",
        "Content-Type": "application/octet-stream",
    }

    def _do_upload():
        response, content = _authorized_http(service).request(
            session.session_url,
            method="PUT",
            headers=headers,
            body=data,
        )
        status = getattr(response, "status", None)
        if _should_retry(status):
            raise HttpError(response, content, uri=session.session_url)
        if status is not None and status >= 400 and status not in {308}:
            raise HttpError(response, content, uri=session.session_url)
        return response, content

    response, content = _execute_with_retries(_do_upload)
    status = getattr(response, "status", None)
    if status == 308:
        range_header = response.get("Range") or response.get("range")
        if range_header:
            match = re.search(r"bytes=(\d+)-(\d+)", range_header)
            if match:
                return int(match.group(2)) + 1
        return end + 1

    if status in {200, 201}:
        if content:
            try:
                payload = json.loads(content.decode("utf-8"))
                if "size" in payload:
                    return int(payload["size"])
            except (ValueError, TypeError):
                pass
        return end + 1

    return end + 1
