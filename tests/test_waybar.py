import importlib.machinery
import importlib.util
import json
import os
from pathlib import Path
import shlex
import subprocess
import tempfile
import unittest
from unittest.mock import patch
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
loader = importlib.machinery.SourceFileLoader("warp_waybar", str(ROOT / "bin/warp-waybar"))
spec = importlib.util.spec_from_loader(loader.name, loader)
adapter = importlib.util.module_from_spec(spec)
loader.exec_module(adapter)


class WaybarTests(unittest.TestCase):
    def test_status_and_markup(self):
        for data, state in [
            ({"available": False}, "missing"),
            ({"available": True, "ok": False}, "error"),
            ({"available": True, "ok": True, "connected": False}, "disconnected"),
            ({"available": True, "ok": True, "connected": True}, "connected"),
        ]:
            data["message"] = "<status> & detail"
            result = adapter.status_payload(data)
            self.assertEqual(result["class"], state)
            self.assertEqual(result["tooltip"], "&lt;status&gt; &amp; detail")

    def test_registration_terminal(self):
        with patch.dict(os.environ, {"WARP_TERMINAL": "kitty --"}):
            self.assertEqual(adapter.terminal_command(), ["kitty", "--", str(adapter.HELPER), "register"])
        with patch.dict(os.environ, {"WARP_TERMINAL": ""}), patch.object(adapter.shutil, "which", return_value=None):
            with self.assertRaises(ValueError):
                adapter.terminal_command()

    def test_action_failure_is_reported(self):
        with patch.dict(adapter.backend, {"run": lambda action: {"ok": False, "message": "daemon unavailable"}}), patch.object(adapter, "notify") as notify:
            self.assertEqual(adapter.main("connect"), 1)
            notify.assert_called_once_with("daemon unavailable", True)

    def test_debian_terminal(self):
        with patch.dict(os.environ, {"WARP_TERMINAL": ""}), patch.object(
                adapter.shutil, "which", side_effect=lambda name: "/usr/bin/x-terminal-emulator" if name == "x-terminal-emulator" else None):
            self.assertEqual(adapter.terminal_command(),
                             ["x-terminal-emulator", "-e", str(adapter.HELPER), "register"])

    def test_wofi_selection_and_cancel(self):
        for code, output, expected in [(0, "Connect\n", "connect"),
                                       (0, "WARP + DNS (DoH)\n", "warp+doh"),
                                       (1, "Connect\n", None), (0, "arbitrary command", None)]:
            with patch.object(adapter.subprocess, "run", return_value=subprocess.CompletedProcess([], code, output)), \
                 patch.dict(adapter.backend, {"run": lambda action: {"ok": True, "message": action}}), \
                 patch.object(adapter, "notify") as notify:
                self.assertEqual(adapter.main("menu"), 0)
                if expected:
                    notify.assert_called_once_with(expected, False)
                else:
                    notify.assert_not_called()

    def test_wofi_install(self):
        with tempfile.TemporaryDirectory() as directory:
            env = {**os.environ, "XDG_CONFIG_HOME": directory + "/config",
                   "XDG_DATA_HOME": directory + "/data"}
            subprocess.run(["python3", str(ROOT / "install-waybar.py"), "--menu", "wofi"],
                           env=env, check=True, capture_output=True)
            module = json.loads((Path(directory) / "config/waybar/warp/module.json").read_text())["custom/warp"]
            self.assertEqual(shlex.split(module["on-click"])[-1], "menu")
            self.assertNotIn("menu-file", module)
            self.assertNotIn("menu-actions", module)

    def test_install_and_menu_commands(self):
        # Spaces and shell metacharacters must survive generated command quoting.
        with tempfile.TemporaryDirectory(prefix="warp test '") as directory:
            base = Path(directory)
            env = {**os.environ, "XDG_CONFIG_HOME": str(base / "config"),
                   "XDG_DATA_HOME": str(base / "data")}
            subprocess.run(["python3", str(ROOT / "install-waybar.py")], env=env,
                           check=True, capture_output=True)
            target = base / "config/waybar/warp"
            module = json.loads((target / "module.json").read_text())["custom/warp"]
            xml = ET.parse(target / "menu.xml")
            ids = {item.attrib["id"] for item in xml.findall('.//object[@class="GtkMenuItem"]')}
            self.assertEqual(ids, set(module["menu-actions"]))
            self.assertTrue(Path(module["menu-file"]).is_file())
            for key, command in module["menu-actions"].items():
                argv = shlex.split(command)
                self.assertEqual(argv[1], "warp+doh" if key == "tunnel" else key)
                self.assertTrue(os.access(argv[0], os.X_OK))
            fakebin = base / "fakebin"
            fakebin.mkdir()
            fakecli = fakebin / "warp-cli"
            fakecli.write_text('#!/bin/sh\ncase "$1" in\nstatus) printf "Status update: Connected\\nNetwork: healthy\\n";;\n*) exit 1;;\nesac\n')
            fakecli.chmod(0o755)
            env["PATH"] = str(fakebin) + os.pathsep + env["PATH"]
            result = subprocess.run(module["exec"], shell=True, env=env,
                                    check=True, capture_output=True, text=True)
            data = json.loads(result.stdout)
            self.assertEqual(data["class"], "connected")
            self.assertIn("healthy", data["tooltip"])
            # Rerunning updates integration files without creating a main config.
            subprocess.run(["python3", str(ROOT / "install-waybar.py")], env=env,
                           check=True, capture_output=True)
            self.assertFalse((base / "config/waybar/config.jsonc").exists())


if __name__ == "__main__":
    unittest.main()
