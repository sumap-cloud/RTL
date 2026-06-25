"""If MultiSimulator.exe is running, terminate it; otherwise continue."""

import subprocess

PROCESS_NAME = "MultiSimulator.exe"


def is_process_running(name: str) -> bool:
    """Return True if a process with the given image name is running."""
    try:
        output = subprocess.check_output(
            ["tasklist", "/FI", f"IMAGENAME eq {name}", "/NH"],
            stderr=subprocess.DEVNULL,
            text=True,
        )
    except subprocess.CalledProcessError:
        return False
    return name.lower() in output.lower()


def kill_process(name: str) -> bool:
    """Force-kill the process (and its child processes) by image name."""
    try:
        subprocess.run(
            ["taskkill", "/F", "/IM", name, "/T"],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        return True
    except subprocess.CalledProcessError:
        return False


def ensure_EFTSimulator_closed(name: str = PROCESS_NAME) -> None:
    if is_process_running(name):
        print(f"⚠️ {name} is running. Closing it...")
        if kill_process(name) and not is_process_running(name):
            print(f"✅ {name} closed successfully.")
        else:
            print(f"❌ Failed to close {name}.")
    else:
        print(f"➡️ {name} is not running. Moving to next step.")


if __name__ == "__main__":
    ensure_EFTSimulator_closed()
    # Next step continues here ...
