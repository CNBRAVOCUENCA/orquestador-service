"""Construye e inicia el stack integrado con Docker Compose desde Linux/macOS."""

from comun import compose_command, ensure_env, run_command


def main() -> int:
    try:
        created = ensure_env()
        if created:
            print("Se creó .env desde .env.example.")
            print("Configura GEMINI_API_KEY en .env para generar resúmenes reales.")

        command = compose_command() + [
            "up",
            "-d",
            "--build",
            "--wait",
            "--wait-timeout",
            "180",
        ]
    except (FileNotFoundError, RuntimeError) as exc:
        print(f"Error: {exc}")
        return 1

    print("Iniciando microservicios...")
    result = run_command(command)
    if result != 0:
        print("No se pudo iniciar el stack. Revisa el estado con:")
        print("docker compose --env-file .env -f infra/docker-compose.yml ps")
        return result

    print("Stack saludable. Últimos logs de cloudflared:")
    return run_command(compose_command() + ["logs", "--tail=30", "cloudflared"])


if __name__ == "__main__":
    raise SystemExit(main())
