import concurrent.futures
import time
import urllib.error
import urllib.request

PUBLIC_URL = "http://traefik/probe"
INTERNAL_URL = "http://traefik:8081/probe"
BACKEND_CONTROL_URL = "http://backend:8000/control"


def get_status(url):
    try:
        with urllib.request.urlopen(url, timeout=3) as response:
            return response.status
    except urllib.error.HTTPError as error:
        return error.code


def set_backend_failure(enabled):
    get_status(f"{BACKEND_CONTROL_URL}?fail={int(enabled)}")


def wait_until_healthy():
    deadline = time.monotonic() + 20
    while time.monotonic() < deadline:
        if get_status(INTERNAL_URL) == 200:
            return
        time.sleep(0.25)
    raise AssertionError("Traefik no logró enrutar a la respuesta saludable del backend")


wait_until_healthy()

with concurrent.futures.ThreadPoolExecutor(max_workers=50) as executor:
    public_statuses = list(executor.map(lambda _: get_status(PUBLIC_URL), range(100)))
assert 429 in public_statuses, "el Rate Limit público no produjo HTTP 429"

with concurrent.futures.ThreadPoolExecutor(max_workers=50) as executor:
    internal_statuses = list(executor.map(lambda _: get_status(INTERNAL_URL), range(50)))
assert all(status == 200 for status in internal_statuses), (
    "el entrypoint interno aplicó el Rate Limit público o falló el flujo normal"
)

set_backend_failure(True)
breaker_statuses = []
deadline = time.monotonic() + 8.0
while time.monotonic() < deadline:
    breaker_statuses.append(get_status(INTERNAL_URL))
    if breaker_statuses[-1] == 503:
        break
    time.sleep(0.1)
assert 500 in breaker_statuses and breaker_statuses[-1] == 503, (
    f"el Circuit Breaker no abrió ante errores 5xx: {breaker_statuses}"
)

set_backend_failure(False)
deadline = time.monotonic() + 25
while time.monotonic() < deadline:
    if get_status(INTERNAL_URL) == 200:
        break
    time.sleep(0.5)
else:
    raise AssertionError("el Circuit Breaker no permitió tráfico tras recuperarse el backend")

print("OK: Rate Limit, Circuit Breaker (apertura/recuperación) y flujo interno")
