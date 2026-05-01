import os
import platform
from pathlib import Path


def _detect_capcut_drafts_dir() -> Path:
    """Locate the CapCut drafts folder for the current OS.

    Checks `CAPCUT_DRAFTS_DIR` first so users can override (testing, custom
    install, network drive). Falls back to the platform default.
    """
    override = os.environ.get("CAPCUT_DRAFTS_DIR")
    if override:
        return Path(override).expanduser()

    system = platform.system()
    if system == "Darwin":
        return (
            Path.home() / "Movies" / "CapCut" / "User Data"
            / "Projects" / "com.lveditor.draft"
        )
    if system == "Windows":
        local_app_data = os.environ.get("LOCALAPPDATA")
        base = Path(local_app_data) if local_app_data else (Path.home() / "AppData" / "Local")
        return base / "CapCut" / "User Data" / "Projects" / "com.lveditor.draft"
    if system == "Linux":
        return Path.home() / ".local" / "share" / "CapCut" / "drafts"
    return Path.home() / "CapCut" / "drafts"


CAPCUT_PROJECTS_ROOT = _detect_capcut_drafts_dir()


def draft_dir(name: str) -> Path:
    return CAPCUT_PROJECTS_ROOT / name


def ensure_root() -> Path:
    CAPCUT_PROJECTS_ROOT.mkdir(parents=True, exist_ok=True)
    return CAPCUT_PROJECTS_ROOT
