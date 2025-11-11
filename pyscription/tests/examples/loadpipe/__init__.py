"""Compatibility wrapper for the src-layout ``loadpipe`` package."""

from __future__ import annotations

from importlib import util as _importlib_util
from pathlib import Path as _Path
import sys as _sys

_pkg_root = _Path(__file__).resolve().parent
_src_pkg = _pkg_root / "src" / "loadpipe"

_spec = _importlib_util.spec_from_file_location( __name__, _src_pkg / "__init__.py", submodule_search_locations=[str(_src_pkg)])
if _spec is None or _spec.loader is None:  # pragma: no cover - defensive guard
    raise ImportError("Cannot load src-layout package metadata")

_current = _sys.modules[__name__]
_module = _importlib_util.module_from_spec(_spec)
_sys.modules[__name__] = _module

_spec.loader.exec_module(_module)

_current.__dict__.update(_module.__dict__)
_current.__path__ = _module.__path__  # type: ignore[attr-defined]
_sys.modules[__name__] = _current

del _importlib_util, _Path, _pkg_root, _src_pkg, _spec, _module, _current

