"""Stop one or more Windows services.

Notes
-----
- Stopping services almost always requires Administrator privileges.
  Run this script from an elevated PowerShell/CMD if you see "Access denied".
- `sc.exe query <name>` is used to detect current state (RUNNING / STOPPED / ...).
- `sc.exe stop  <name>` requests a stop and we poll until STOPPED or timeout.
"""

import subprocess
import time

# Edit this list to suit your needs
SERVICES_TO_STOP = [
    "RemedyEFTPOSServer"
    # "Spooler",
    # "wuauserv",
]


def _run(cmd):
    return subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        shell=False,
    )


def get_service_state(name: str) -> str:
    """Return service state ('RUNNING', 'STOPPED', 'NOT_FOUND', ...)."""
    r = _run(["sc.exe", "query", name])
    if r.returncode != 0:
        return "NOT_FOUND"
    for line in r.stdout.splitlines():
        line = line.strip()
        if line.upper().startswith("STATE"):
            # e.g. "STATE              : 4  RUNNING"
            parts = line.split()
            return parts[-1].upper()
    return "UNKNOWN"


def get_dependents(name: str) -> list:
    """Return list of services that depend on `name` (and are not stopped)."""
    r = _run(["sc.exe", "enumdepend", name])
    if r.returncode != 0:
        return []
    deps = []
    for line in r.stdout.splitlines():
        line = line.strip()
        # Lines look like: "SERVICE_NAME: SomeDependentService"
        if line.upper().startswith("SERVICE_NAME:"):
            deps.append(line.split(":", 1)[1].strip())
    return deps


def stop_service(name: str, wait_seconds: float = 15.0, _seen=None) -> bool:
    """Stop a service (and any dependents first). Returns True on success."""
    if _seen is None:
        _seen = set()
    if name in _seen:
        return True
    _seen.add(name)

    state = get_service_state(name)
    if state == "NOT_FOUND":
        print(f"❓ {name}: service not found.")
        return False
    if state == "STOPPED":
        print(f"➡️ {name}: already stopped.")
        return True

    # Stop dependents first
    for dep in get_dependents(name):
        print(f"   ↳ {name} depends on {dep}; stopping dependent first.")
        if not stop_service(dep, wait_seconds, _seen):
            print(f"❌ {name}: could not stop dependent {dep}; aborting.")
            return False

    print(f"⏹️ {name}: stopping...")
    r = _run(["sc.exe", "stop", name])
    output = (r.stdout + r.stderr).strip()
    if r.returncode != 0 and "1062" not in output:  # 1062 = not started
        print(f"❌ {name}: stop request failed -> {output}")
        return False

    deadline = time.time() + wait_seconds
    while time.time() < deadline:
        if get_service_state(name) == "STOPPED":
            print(f"✅ {name}: stopped.")
            return True
        time.sleep(0.5)

    print(f"⚠️ {name}: still not stopped after {wait_seconds:.0f}s.")
    return False


def stop_services(names) -> dict:
    """Stop a list of services. Returns {name: success_bool}."""
    return {n: stop_service(n) for n in names}

def ensure_services_stopped(names) -> None:


    """Stop services and print summary."""
    if not names:
        print("No services configured. Edit SERVICES_TO_STOP list and re-run.")
        return
    results = stop_services(names)
    failed = [n for n, ok in results.items() if not ok]
    if failed:
        print(f"\nFailed/incomplete: {failed}")
    else:
        print("\nAll requested services are stopped.")


if __name__ == "__main__":
    ensure_services_stopped(SERVICES_TO_STOP)