from __future__ import annotations

import json
import os
import re
import shutil
import signal
import subprocess
import threading
import time
from collections import deque
from http import HTTPStatus
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parent.parent
STATIC_DIR = ROOT / "backend" / "static"
SAMPLE_INTERVAL = 2
HISTORY = deque(maxlen=1800)
PROTECTED_NAMES = {"launchd", "kernel_task", "WindowServer", "loginwindow", "syslogd"}


def run(command: list[str]) -> str:
    # Keep command output machine-readable even when macOS is configured with
    # a locale that uses decimal commas (for example, Spanish).
    environment = {**os.environ, "LC_ALL": "C"}
    return subprocess.run(command, capture_output=True, text=True, check=False, env=environment).stdout


def memory() -> dict[str, float]:
    page_size = int(run(["sysctl", "-n", "hw.pagesize"]).strip() or 4096)
    total = int(run(["sysctl", "-n", "hw.memsize"]).strip() or 0)
    values = {key: int(value) for key, value in re.findall(r"Pages (\w+):\s+(\d+)", run(["vm_stat"]))}
    available_pages = values.get("free", 0) + values.get("inactive", 0) + values.get("speculative", 0)
    available = available_pages * page_size
    used = max(0, total - available)
    return {"total": total, "used": used, "available": available, "percentage": round(used / total * 100, 1) if total else 0}


def cpu() -> dict[str, float]:
    cores = os.cpu_count() or 1
    load = os.getloadavg()[0]
    return {"percentage": round(min(100, load / cores * 100), 1), "load": round(load, 2), "cores": cores}


def disk() -> dict[str, float]:
    usage = shutil.disk_usage("/")
    return {"total": usage.total, "used": usage.used, "free": usage.free, "percentage": round(usage.used / usage.total * 100, 1)}


def battery() -> dict[str, object]:
    output = run(["pmset", "-g", "batt"])
    match = re.search(r"(\d+)%", output)
    # pmset reports states such as "charging", "charged", "discharging" and
    # "not charging".  A substring check would incorrectly treat the latter
    # as charging, so read the state field immediately after the percentage.
    state_match = re.search(r"\d+%\s*;\s*([^;]+)\s*;", output.lower())
    state = state_match.group(1).strip() if state_match else ""
    return {
        "available": bool(match),
        "percentage": int(match.group(1)) if match else None,
        "charging": state in {"charging", "finishing charge"},
    }


def snapshot() -> dict[str, object]:
    return {"timestamp": int(time.time() * 1000), "cpu": cpu(), "memory": memory(), "disk": disk(), "battery": battery()}


def sample_loop() -> None:
    while True:
        HISTORY.append(snapshot())
        time.sleep(SAMPLE_INTERVAL)


def processes() -> list[dict[str, object]]:
    total_memory = memory()["total"]
    # Use macOS' system ps directly.  `-e` includes processes without a
    # controlling terminal, which is where most system and GUI processes are.
    rows = run(["/bin/ps", "-e", "-o", "pid=,ppid=,%cpu=,%mem=,stat=,comm="]).splitlines()
    output = []
    for row in rows:
        parts = row.strip().split(None, 5)
        if len(parts) != 6:
            continue
        pid, ppid, cpu_usage, mem_pct, state, command = parts
        try:
            percent = float(mem_pct.replace(",", "."))
            output.append({"pid": int(pid), "ppid": int(ppid), "name": Path(command).name, "command": command,
                           "cpu": round(float(cpu_usage.replace(",", ".")), 1), "memory": int(total_memory * percent / 100), "state": state})
        except ValueError:
            continue
    return sorted(output, key=lambda item: (item["cpu"], item["memory"]), reverse=True)


def manage_process(pid: int, force: bool) -> tuple[bool, str]:
    target = next((item for item in processes() if item["pid"] == pid), None)
    if not target:
        return False, "El proceso ya no existe."
    if pid in {0, 1, os.getpid()} or target["name"] in PROTECTED_NAMES:
        return False, "Ese proceso está protegido por seguridad."
    try:
        os.kill(pid, signal.SIGKILL if force else signal.SIGTERM)
    except PermissionError:
        return False, "macOS no permite gestionar este proceso con los permisos actuales."
    except ProcessLookupError:
        return False, "El proceso ya no existe."
    return True, "Se ha enviado la señal al proceso."


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(STATIC_DIR), **kwargs)

    def send_json(self, value: object, status: int = 200) -> None:
        body = json.dumps(value).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:
        path = urlparse(self.path).path
        if path == "/api/overview":
            self.send_json(HISTORY[-1] if HISTORY else snapshot())
        elif path == "/api/history":
            self.send_json(list(HISTORY))
        elif path == "/api/processes":
            self.send_json(processes())
        elif path.startswith("/api/"):
            self.send_json({"error": "Ruta no encontrada"}, HTTPStatus.NOT_FOUND)
        else:
            if path != "/" and not (STATIC_DIR / path.lstrip("/")).exists():
                self.path = "/index.html"
            super().do_GET()

    def do_POST(self) -> None:
        match = re.fullmatch(r"/api/processes/(\d+)/(terminate|force)", urlparse(self.path).path)
        if not match:
            self.send_json({"error": "Ruta no encontrada"}, HTTPStatus.NOT_FOUND)
            return
        ok, message = manage_process(int(match.group(1)), match.group(2) == "force")
        self.send_json({"ok": ok, "message": message}, HTTPStatus.OK if ok else HTTPStatus.BAD_REQUEST)

    def log_message(self, fmt: str, *args) -> None:
        print(f"[{self.log_date_time_string()}] {fmt % args}")


if __name__ == "__main__":
    HISTORY.append(snapshot())
    threading.Thread(target=sample_loop, daemon=True).start()
    print("Dashboard disponible en http://127.0.0.1:8765")
    ThreadingHTTPServer(("127.0.0.1", 8765), Handler).serve_forever()
