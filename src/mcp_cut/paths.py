from pathlib import Path

CAPCUT_PROJECTS_ROOT = (
    Path.home() / "Movies" / "CapCut" / "User Data" / "Projects" / "com.lveditor.draft"
)


def draft_dir(name: str) -> Path:
    return CAPCUT_PROJECTS_ROOT / name


def ensure_root() -> Path:
    CAPCUT_PROJECTS_ROOT.mkdir(parents=True, exist_ok=True)
    return CAPCUT_PROJECTS_ROOT
