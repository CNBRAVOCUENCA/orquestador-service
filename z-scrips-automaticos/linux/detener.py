"""Detiene el stack sin borrar los volúmenes persistentes desde Linux/macOS."""

from comun import compose_command, ensure_env, run_command


def main() -> int:
    try:
        created = ensure_env()
        if created:
            print("Se creó .env desde .env.example.")
        command = compose_command() + ["down"]
    except (FileNotFoundError, RuntimeError) as exc:
        print(f"Error: {exc}")
        return 1

    result = run_command(command)
    if result == 0:
        print("Stack detenido. Los volúmenes y datos persistentes se conservaron.")
    return result


if __name__ == "__main__":
    raise SystemExit(main())
