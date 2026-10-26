"""Crea .env desde la plantilla sin sobrescribirla, para Linux/macOS."""

from comun import ENV_FILE, ensure_env


def main() -> int:
    try:
        created = ensure_env()
    except FileNotFoundError as exc:
        print(f"Error: {exc}")
        return 1

    if created:
        print("Se creó .env. Edita GEMINI_API_KEY antes de generar resúmenes reales.")
    else:
        print(".env ya existe; no se modificó. Edítalo para cambiar la configuración.")
    print(f"Archivo de configuración: {ENV_FILE}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
