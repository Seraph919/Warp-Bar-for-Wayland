#!/usr/bin/env python3
"""Install WARP's Waybar files without replacing the user's bar configuration."""
import argparse
import json
import os
from pathlib import Path
import shlex
import shutil


def install(menu="native"):
    source = Path(__file__).resolve().parent
    config = Path(os.environ.get("XDG_CONFIG_HOME") or Path.home() / ".config")
    data = Path(os.environ.get("XDG_DATA_HOME") or Path.home() / ".local/share")
    target = config / "waybar/warp"
    binary = data / "warp-bar/bin"
    target.mkdir(parents=True, exist_ok=True)
    binary.mkdir(parents=True, exist_ok=True)
    for name in ("warp", "warp-waybar"):
        shutil.copy2(source / "bin" / name, binary / name)
        (binary / name).chmod(0o755)
    for name in ("menu.xml", "style.css"):
        shutil.copy2(source / "waybar" / name, target / name)
    command = shlex.quote(str(binary / "warp-waybar"))
    actions = {name: name for name in
               ("connect", "disconnect", "doh", "malware", "full", "off", "check", "register")}
    actions["tunnel"] = "warp+doh"
    module = {"custom/warp": {
        "exec": command + " status", "return-type": "json", "interval": 5,
        "format": "{text}", "tooltip": True,
        "menu": "on-click", "menu-file": str(target / "menu.xml"),
        "menu-actions": {key: command + " " + shlex.quote(value) for key, value in actions.items()}
    }}
    if menu == "wofi":
        for key in ("menu", "menu-file", "menu-actions"):
            del module["custom/warp"][key]
        module["custom/warp"]["on-click"] = command + " menu"
    (target / "module.json").write_text(json.dumps(module, indent=2) + "\n")
    print("Installed WARP files. Merge this include into your Waybar configuration:")
    print(json.dumps({"include": [str(target / "module.json")]}, indent=2))
    print('Add "custom/warp" to your existing modules-right (or modules-left/center) array.')
    print("Optional stylesheet: " + str(target / "style.css"))
    print("Restart Waybar using your usual session/service launcher.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--menu", choices=("native", "wofi"), default="native",
                        help="Use wofi for older Waybar versions without native menu support")
    install(parser.parse_args().menu)
