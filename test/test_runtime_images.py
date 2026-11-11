import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _runtime_user(dockerfile: Path) -> str | None:
    contents = dockerfile.read_text(encoding="utf-8")
    runtime_stage = re.search(r"(?ims)^FROM .+ AS runtime\s*(.*?)(?=^FROM |\Z)", contents)
    assert runtime_stage, f"{dockerfile.name} must declare a runtime stage"
    user_directive = re.search(r"(?im)^USER\s+(\S+)\s*$", runtime_stage.group(1))
    return user_directive.group(1) if user_directive else None


def test_application_images_run_as_non_root():
    for dockerfile in (ROOT / "Dockerfile", ROOT / "infra" / "Dockerfile.remote"):
        user = _runtime_user(dockerfile)
        assert user and user.lower() != "root", f"{dockerfile} must set a non-root runtime USER"
