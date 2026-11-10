"""Tests for immutable application-image names and release version validation."""

import importlib.util
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = ROOT / "z-scrips-automaticos" / "linux"
SPEC = importlib.util.spec_from_file_location("deployment_comun", SCRIPTS_DIR / "comun.py")
assert SPEC is not None and SPEC.loader is not None
deployment_comun = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(deployment_comun)

REMOTE_SERVICES = {
    "documentos": "DOCUMENTOS_VERSION",
    "extraccion": "EXTRACCION_VERSION",
    "resumen": "RESUMEN_VERSION",
    "notificaciones": "NOTIFICACIONES_VERSION",
}


def test_compose_uses_service_commit_for_remote_image_tag_and_build_ref():
    for service, version in REMOTE_SERVICES.items():
        compose_file = ROOT / "infra" / "services" / service / "compose.yaml"
        contents = compose_file.read_text(encoding="utf-8")
        version_expression = f"${{{version}:?Set {version} in .env}}"

        assert f'image: "${{IMAGE_NAMESPACE:-pdf-ms}}/{service}:{version_expression}"' in contents
        assert f'SERVICE_REF: "{version_expression}"' in contents


def test_orchestrator_image_requires_an_explicit_version():
    compose_file = ROOT / "infra" / "services" / "orquestador" / "compose.yaml"
    contents = compose_file.read_text(encoding="utf-8")

    assert (
        'image: "${IMAGE_NAMESPACE:-pdf-ms}/orquestador:'
        "${ORQUESTADOR_VERSION:?Set ORQUESTADOR_VERSION in .env}\""
    ) in contents


def test_release_requires_full_git_shas_for_all_application_images(tmp_path, monkeypatch):
    env_file = tmp_path / ".env"
    sha = "a" * 40
    env_file.write_text(
        "\n".join(f"{key}={sha}" for key in deployment_comun.RELEASE_VERSION_KEYS),
        encoding="utf-8",
    )
    monkeypatch.setattr(deployment_comun, "ENV_FILE", env_file)

    deployment_comun.validate_release_versions()


def test_release_rejects_mutable_image_tags(tmp_path, monkeypatch):
    env_file = tmp_path / ".env"
    values = {key: "a" * 40 for key in deployment_comun.RELEASE_VERSION_KEYS}
    values["ORQUESTADOR_VERSION"] = "dev"
    env_file.write_text("\n".join(f"{key}={value}" for key, value in values.items()), encoding="utf-8")
    monkeypatch.setattr(deployment_comun, "ENV_FILE", env_file)

    with pytest.raises(RuntimeError, match="ORQUESTADOR_VERSION"):
        deployment_comun.validate_release_versions()


def test_versioned_orchestrator_build_requires_matching_clean_commit(tmp_path, monkeypatch):
    sha = "b" * 40
    env_file = tmp_path / ".env"
    env_file.write_text(f"ORQUESTADOR_VERSION={sha}\n", encoding="utf-8")
    monkeypatch.setattr(deployment_comun, "ENV_FILE", env_file)
    monkeypatch.setattr(deployment_comun.shutil, "which", lambda _: "git")
    results = iter(
        (
            SimpleNamespace(returncode=0, stdout=f"{sha}\n", stderr=""),
            SimpleNamespace(returncode=0, stdout="", stderr=""),
        )
    )
    monkeypatch.setattr(deployment_comun.subprocess, "run", lambda *args, **kwargs: next(results))

    deployment_comun.validate_orchestrator_build_version()


def test_versioned_orchestrator_build_rejects_dirty_checkout(tmp_path, monkeypatch):
    sha = "b" * 40
    env_file = tmp_path / ".env"
    env_file.write_text(f"ORQUESTADOR_VERSION={sha}\n", encoding="utf-8")
    monkeypatch.setattr(deployment_comun, "ENV_FILE", env_file)
    monkeypatch.setattr(deployment_comun.shutil, "which", lambda _: "git")
    results = iter(
        (
            SimpleNamespace(returncode=0, stdout=f"{sha}\n", stderr=""),
            SimpleNamespace(returncode=0, stdout=" M App/main.py\n", stderr=""),
        )
    )
    monkeypatch.setattr(deployment_comun.subprocess, "run", lambda *args, **kwargs: next(results))

    with pytest.raises(RuntimeError, match="checkout limpio"):
        deployment_comun.validate_orchestrator_build_version()


def test_local_release_never_pulls_images(monkeypatch):
    monkeypatch.syspath_prepend(str(SCRIPTS_DIR))
    import iniciar

    commands = []
    monkeypatch.setattr(iniciar, "ensure_env", lambda: False)
    monkeypatch.setattr(iniciar, "compose_command", lambda: ["docker", "compose"])
    monkeypatch.setattr(iniciar, "validate_release_versions", lambda: None)
    monkeypatch.setattr(
        iniciar,
        "run_command",
        lambda command: commands.append(command) or 0,
    )
    monkeypatch.setattr(sys, "argv", ["iniciar.py", "--local-release"])

    assert iniciar.main() == 0
    assert commands[0] == [
        "docker",
        "compose",
        "up",
        "-d",
        "--no-build",
        "--pull",
        "never",
        "--wait",
        "--wait-timeout",
        "180",
    ]
