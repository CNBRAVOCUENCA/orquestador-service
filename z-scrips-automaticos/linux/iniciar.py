"""Construye e inicia el stack integrado con Docker Compose desde Linux/macOS."""

import argparse

from comun import (
    compose_command,
    ensure_env,
    run_command,
    validate_orchestrator_build_version,
    validate_release_versions,
)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--release",
        action="store_true",
        help="descarga y ejecuta imágenes publicadas sin reconstruirlas",
    )
    parser.add_argument(
        "--local-release",
        action="store_true",
        help="ejecuta imágenes versionadas que ya existen en el daemon, sin descargarlas",
    )
    parser.add_argument(
        "--build-release",
        action="store_true",
        help="construye imágenes de release tras verificar que los tags son SHA del código",
    )
    args = parser.parse_args()
    selected_modes = sum((args.release, args.local_release, args.build_release))
    if selected_modes > 1:
        parser.error("--release, --local-release y --build-release son modos mutuamente excluyentes")

    try:
        created = ensure_env()
        if created:
            print("Se creó .env desde .env.example.")
            print("Configura GEMINI_API_KEY en .env para generar resúmenes reales.")

        command = compose_command()
        if args.release or args.local_release:
            validate_release_versions()
        elif args.build_release:
            validate_release_versions()
            validate_orchestrator_build_version()
        else:
            validate_orchestrator_build_version()
    except (FileNotFoundError, RuntimeError) as exc:
        print(f"Error: {exc}")
        return 1

    if args.build_release:
        print("Construyendo las imágenes de esta release...")
        return run_command(
            command + ["build", "documentos", "extraccion", "resumen", "notificaciones", "orquestador"]
        )

    if args.release:
        print("Descargando las imágenes fijadas para esta release...")
        result = run_command(command + ["pull"])
        if result != 0:
            return result
    if args.local_release:
        startup_args = [
            "up",
            "-d",
            "--no-build",
            "--pull",
            "never",
            "--wait",
            "--wait-timeout",
            "180",
        ]
    elif args.release:
        startup_args = [
            "up",
            "-d",
            "--no-build",
            "--wait",
            "--wait-timeout",
            "180",
        ]
    else:
        startup_args = [
            "up",
            "-d",
            "--build",
            "--wait",
            "--wait-timeout",
            "180",
        ]

    print("Iniciando microservicios...")
    result = run_command(command + startup_args)
    if result != 0:
        print("No se pudo iniciar el stack. Revisa el estado con:")
        print("docker compose --env-file .env -f infra/docker-compose.yml ps")
        return result

    print("Stack saludable. Últimos logs de cloudflared:")
    return run_command(compose_command() + ["logs", "--tail=30", "cloudflared"])


if __name__ == "__main__":
    raise SystemExit(main())
