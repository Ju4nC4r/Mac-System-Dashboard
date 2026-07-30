import importlib.util
import json
import threading
import unittest
from collections import deque
from pathlib import Path
from unittest.mock import patch
from urllib.request import Request, urlopen

SPEC = importlib.util.spec_from_file_location("dashboard_app", Path(__file__).with_name("app.py"))
app = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(app)


class MetricsTests(unittest.TestCase):
    def test_memory_calculation_uses_available_pages(self):
        def fake_run(command):
            if command == ["sysctl", "-n", "hw.pagesize"]:
                return "4096\n"
            if command == ["sysctl", "-n", "hw.memsize"]:
                return "409600\n"
            return "Pages free: 10.\nPages inactive: 20.\nPages speculative: 30.\n"

        with patch.object(app, "run", fake_run):
            result = app.memory()
        self.assertEqual(result["available"], 60 * 4096)
        self.assertEqual(result["used"], 409600 - 60 * 4096)

    def test_process_parser_orders_by_cpu(self):
        output = "  PID  PPID  %CPU %MEM STAT COMMAND\n  12 1 2.0 1.0 S /Applications/Low\n  13 1 8.0 0.5 R /Applications/High\n"
        with patch.object(app, "run", return_value=output), patch.object(app, "memory", return_value={"total": 1000}):
            result = app.processes()
        self.assertEqual([item["name"] for item in result], ["High", "Low"])
        self.assertEqual(result[0]["memory"], 5)

    def test_process_parser_accepts_decimal_commas(self):
        output = "  12 1 2,5 1,0 S /Applications/Example\n"
        with patch.object(app, "run", return_value=output), patch.object(app, "memory", return_value={"total": 1000}):
            result = app.processes()
        self.assertEqual(result[0]["cpu"], 2.5)
        self.assertEqual(result[0]["memory"], 10)

    def test_protected_process_is_never_signalled(self):
        with patch.object(app, "processes", return_value=[{"pid": 630, "name": "WindowServer"}]), patch("os.kill") as kill:
            ok, message = app.manage_process(630, False)
        self.assertFalse(ok)
        self.assertIn("protegido", message)
        kill.assert_not_called()

    def test_normal_process_receives_requested_signal(self):
        with patch.object(app, "processes", return_value=[{"pid": 42000, "name": "Example"}]), patch("os.kill") as kill:
            ok, _ = app.manage_process(42000, True)
        self.assertTrue(ok)
        kill.assert_called_once_with(42000, app.signal.SIGKILL)

    def test_battery_does_not_treat_not_charging_as_charging(self):
        output = "Now drawing from 'Battery Power'\n -InternalBattery-0 80%; not charging; 2:00 remaining present: true\n"
        with patch.object(app, "run", return_value=output):
            result = app.battery()
        self.assertTrue(result["available"])
        self.assertEqual(result["percentage"], 80)
        self.assertFalse(result["charging"])

    def test_battery_detects_charging_state(self):
        output = "Now drawing from 'AC Power'\n -InternalBattery-0 80%; charging; 1:00 remaining present: true\n"
        with patch.object(app, "run", return_value=output):
            result = app.battery()
        self.assertTrue(result["charging"])


class ApiTests(unittest.TestCase):
    def setUp(self):
        self.snapshot = {"timestamp": 1, "cpu": {}, "memory": {}, "disk": {}, "battery": {}}
        self.server = app.ThreadingHTTPServer(("127.0.0.1", 0), app.Handler)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.base = f"http://127.0.0.1:{self.server.server_port}"

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()

    def test_overview_and_processes_endpoints(self):
        with patch.object(app, "HISTORY", deque([self.snapshot])), patch.object(app, "processes", return_value=[{"pid": 2, "name": "Example"}]):
            overview = json.load(urlopen(f"{self.base}/api/overview"))
            processes = json.load(urlopen(f"{self.base}/api/processes"))
        self.assertEqual(overview, self.snapshot)
        self.assertEqual(processes[0]["name"], "Example")

    def test_process_action_returns_backend_message(self):
        with patch.object(app, "manage_process", return_value=(True, "Correcto")):
            request = Request(f"{self.base}/api/processes/22/terminate", method="POST")
            response = json.load(urlopen(request))
        self.assertEqual(response, {"ok": True, "message": "Correcto"})


if __name__ == "__main__":
    unittest.main()
