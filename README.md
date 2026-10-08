# WARP Bar for Wayland

Control Cloudflare WARP from your status bar: connect, disconnect, switch DNS
modes, manage family filtering, and check whether the tunnel is active.

Includes a **Waybar module for Hyprland, Sway, and other Waybar-compatible Wayland
compositors**, plus an **Omarchy shell plugin**.

## What is WARP?

Cloudflare WARP creates an encrypted tunnel between your device and Cloudflare's
network, then routes your internet traffic through it. This adds privacy on your
local network and from your internet provider, while making Cloudflare the provider
you trust to carry that traffic. DNS-only mode encrypts website-name lookups without
tunneling the rest of your connection.

Turning WARP on changes the route your traffic takes, so browsing speed and latency
can improve or get worse depending on your network. It is not a guaranteed speed
boost, and download speeds can drop. Websites generally see a Cloudflare IP address
near your actual location; WARP does not make you anonymous or let you choose another
country. Some location-sensitive services may behave differently while connected.

See Cloudflare's [mode descriptions](https://developers.cloudflare.com/warp-client/warp-modes/)
and [FAQ](https://developers.cloudflare.com/warp-client/known-issues-and-faq/) for details.

**Installation:** [Debian / Ubuntu](#debian--ubuntu--compatible-derivatives) ·
[Arch Linux / Omarchy](#arch-linux--hyprland--omarchy) ·
[Waybar configuration](#waybar-hyprland-sway-and-compatible-compositors)

## Compatibility

| Desktop setup | Integration |
| --- | --- |
| Hyprland or Sway with Waybar | Waybar module with a click menu and desktop notifications |
| Other Wayland compositors running Waybar | Same Waybar module; requires compositor support for Waybar |
| Omarchy with its Quickshell-based shell | Native bar widget and popup |

Debian and Ubuntu users use the Waybar integration. A Wofi menu option supports
older Waybar packages, including Debian 12's package.

Wayland is the display protocol and Hyprland is a compositor. This project adds
controls to a supported bar; it is not a universal plugin for every Wayland panel.
The Omarchy QML widget requires Omarchy's shell components, not just Quickshell.

The Omarchy integration has been tested on a running desktop. The Waybar adapter
has automated checks for configuration, status output, and command handling;
its visual behavior has not yet been verified in a live Waybar session.
Debian/Ubuntu installation instructions have been checked against upstream
documentation; this project has not yet been tested on a live Debian/Ubuntu desktop.

## 1. Install Cloudflare WARP

### Arch Linux / Hyprland / Omarchy

Install the community-maintained AUR package using `yay` (if installed):

```bash
yay -S --needed cloudflare-warp-bin
sudo pacman -S --needed python curl
sudo systemctl enable --now warp-svc
```

Omarchy users can use `omarchy pkg aur add cloudflare-warp-bin` instead of `yay`.
The Arch package named `warp` is an unrelated file-sharing app.

### Debian / Ubuntu / compatible derivatives

Use a Waybar-compatible Wayland session such as Sway or Hyprland. Installing this
module does not make Waybar compatible with the default GNOME or Cinnamon panel.

Install the prerequisites:

```bash
sudo apt update
sudo apt install ca-certificates curl gnupg python3 waybar libnotify-bin wofi
```

If your session has no terminal or notification daemon, install Foot and Mako:

```bash
sudo apt install foot mako-notifier
```

Start Mako through your session's startup configuration if needed. Use only one
notification daemon per session.

Add Cloudflare's signed APT repository and install its client. Paste this block
into **Bash**; it stops if any step fails:

```bash
(
  set -euo pipefail
  . /etc/os-release
  warp_codename="${UBUNTU_CODENAME:-${VERSION_CODENAME:-}}"
  case "$warp_codename" in
    bookworm|trixie|jammy|noble|resolute) ;;
    *) echo "Check Cloudflare's repository support for this distribution first." >&2; exit 1 ;;
  esac

  warp_key_tmp=$(mktemp)
  trap 'rm -f "$warp_key_tmp"' EXIT
  curl -fsSL https://pkg.cloudflareclient.com/pubkey.gpg -o "$warp_key_tmp"
  sudo install -d -m 755 /usr/share/keyrings
  sudo gpg --batch --yes --dearmor \
    --output /usr/share/keyrings/cloudflare-warp-archive-keyring.gpg "$warp_key_tmp"
  sudo chmod 644 /usr/share/keyrings/cloudflare-warp-archive-keyring.gpg
  printf 'deb [signed-by=/usr/share/keyrings/cloudflare-warp-archive-keyring.gpg] https://pkg.cloudflareclient.com/ %s main\n' "$warp_codename" \
    | sudo tee /etc/apt/sources.list.d/cloudflare-client.list
  sudo apt update
  sudo apt install cloudflare-warp
  sudo systemctl enable --now warp-svc
)
```

The repository suite must match the Debian/Ubuntu **base release**. The block
uses `UBUNTU_CODENAME` when available for Ubuntu derivatives; it does not substitute
an unrelated release for unrecognized derivatives. Check [Cloudflare's repository
instructions](https://pkg.cloudflareclient.com/) for current release and architecture
availability. Do not add a second repository entry if you already configured one
in another APT sources file.

Next, install the module from this repository as your regular user:

```bash
python3 install-waybar.py --menu wofi
```

Then follow the Waybar configuration steps below, starting with the `include`
and `modules-right` entries. The Wofi option works without Waybar's newer native
menu feature. For a recent Waybar with native menus, omit `--menu wofi`.

### Other distributions

Follow [Cloudflare's Linux installation guide](https://developers.cloudflare.com/warp-client/get-started/linux/)
to configure the appropriate package repository and install its client. Install
Python 3 and curl through your distribution's package manager. On systemd systems:

```bash
sudo systemctl enable --now warp-svc
```

## 2. Install your bar integration

Clone or download this repository and open a terminal in its root directory.
Choose the integration matching the bar you use.

### Waybar (Hyprland, Sway, and compatible compositors)

Requires Waybar, `notify-send`, a notification
daemon (for example, Mako or SwayNC), and a terminal for registration.
The default menu requires custom-module menu support in Waybar; no separate
launcher is needed. The optional `--menu wofi` mode requires Wofi instead.

On Arch Linux, install these dependencies if needed:

```bash
sudo pacman -S --needed waybar libnotify
```

Run the installer as your regular user:

```bash
python3 install-waybar.py
```

For older Waybar releases, install Wofi and run `python3 install-waybar.py --menu wofi`
instead. This is the recommended route for the Debian/Ubuntu instructions above.

It installs scripts under `~/.local/share/warp-bar/` and module files under
`~/.config/waybar/warp/`, respecting `XDG_DATA_HOME` and `XDG_CONFIG_HOME` when set.
It updates only this integration's files and prints the generated paths; it does
not edit your main Waybar configuration.

Merge the following into your existing `~/.config/waybar/config.jsonc` (or `config`):

```jsonc
{
  "include": ["~/.config/waybar/warp/module.json"],
  "modules-right": ["custom/warp"]
}
```

Keep your existing modules and includes: add these entries to the corresponding
arrays instead of replacing them. For custom XDG paths, use the include path
printed by the installer.

Optional: add this at the top of your Waybar `style.css`:

```css
@import "warp/style.css";
```

Restart Waybar through your usual session or service launcher. Click **WARP** to
open the menu. Hover to see client status; command results appear as desktop
notifications. Status refreshes every five seconds.

Registration tries `xdg-terminal-exec`, Debian's `x-terminal-emulator`, Foot, Kitty, Alacritty, Ghostty,
GNOME Terminal, then Konsole. To override it, set `WARP_TERMINAL` in Waybar's
launch environment, including any arguments needed to run a command. For example:

```bash
WARP_TERMINAL='kitty --' waybar
```

Run that only when starting a new Waybar instance, not alongside an existing one.
You can always register directly in a terminal using the commands below.

### Omarchy shell

```bash
mkdir -p ~/.config/omarchy/plugins/seraph.warp/bin
cp manifest.json BarWidget.qml README.md ~/.config/omarchy/plugins/seraph.warp/
install -m 755 bin/warp ~/.config/omarchy/plugins/seraph.warp/bin/warp
omarchy plugin validate ~/.config/omarchy/plugins/seraph.warp
omarchy-shell shell rescanPlugins
```

Allow discovery a moment, then enable the widget:

```bash
omarchy plugin enable seraph.warp --section right
```

To place it beside the standard network widget:

```bash
omarchy bar move seraph.warp --section right --after omarchy.network
```

## 3. First-time setup

1. Click **WARP**, then **Register WARP (first time)**.
2. Follow the terminal prompts and press Enter to close it. Register once per device setup.
3. Select **WARP + DNS (DoH)**.
4. Select **Connect**.
5. Select **Check connection**. `warp=on` confirms the tunnel is active.

The equivalent terminal setup is:

```bash
warp-cli registration new
warp-cli mode warp+doh
warp-cli connect
```

## Menu options

| Option | What it does |
| --- | --- |
| Connect | Activates the selected connection mode. |
| Disconnect | Deactivates the connection. |
| DNS only (DoH) | Encrypts DNS lookups without tunneling other traffic. |
| WARP + DNS (DoH) | Routes traffic through WARP and encrypts DNS lookups. |
| Block malware | Filters known malicious domains through DNS. |
| Block malware + adult content | Filters both categories. |
| Turn off family filtering | Removes content filtering while keeping the selected connection mode. |
| Check connection | Checks tunnel status through Cloudflare's trace endpoint. |
| Register WARP (first time) | Opens a terminal to register the device. |

Filtering is optional and works with either connection mode. The menus issue
commands; they do not display the currently selected mode or filter as checked items.

## Troubleshooting

**Client missing:** check `command -v warp-cli`. Install Cloudflare's client if
nothing is returned.

**Cannot reach the daemon:** on systemd systems, run:

```bash
sudo systemctl enable --now warp-svc
systemctl status warp-svc
```

**Waybar menu does not open:** check that `module.json` is included, `custom/warp`
is in your module list, and your Waybar version supports `menu`, `menu-file`, and
`menu-actions` for custom modules. See the [Waybar custom-module documentation](https://github.com/Alexays/Waybar/wiki/Module:-Custom).
For an older version, install Wofi and rerun `python3 install-waybar.py --menu wofi`,
then restart Waybar. In Wofi mode, check that `command -v wofi` returns a path.

**No notifications:** ensure a notification daemon is running and `notify-send`
is installed. To inspect a result directly (default installation path):

```bash
~/.local/share/warp-bar/bin/warp-waybar check
```

**Omarchy plugin not found:** rescan, wait a few seconds, then repeat the enable
command. If code or appearance is stale, run `omarchy restart shell`.

**Connected but the tunnel check says off:** `warp=off` is expected in DNS-only
mode. Select **WARP + DNS (DoH)** and connect to use a tunnel.

For a manual check:

```bash
warp-cli status
curl --fail --silent --show-error https://www.cloudflare.com/cdn-cgi/trace
```

Use `/cdn-cgi/trace` without a trailing slash. `/cdn-cgi/trace/` can return HTTP 404.
A failed HTTP check alone does not mean the client has disconnected.

## Update or remove

To update, download/pull the latest files and repeat the installation steps for
your integration. Restart your bar if changes do not appear.
Keep `--menu wofi` when updating if you use the Wofi menu.

To remove the Waybar widget, remove `custom/warp` from your module list and remove
its include and stylesheet import. Restart Waybar. You can then delete the
`warp-bar` data directory and the `waybar/warp` configuration directory.

To hide the Omarchy widget:

```bash
omarchy plugin disable seraph.warp
```

Removing either widget does not disconnect or uninstall Cloudflare WARP.
Run `warp-cli disconnect` first if you want the connection off.

## Project files

- `bin/warp` — Shared WARP command helper (Python standard library only).
- `bin/warp-waybar` — Waybar JSON output, notifications, and terminal launching.
- `install-waybar.py` — Installs the Waybar files and generates machine-specific paths.
- `waybar/` — GTK menu and optional stylesheet.
- `BarWidget.qml`, `manifest.json` — Omarchy integration (`seraph.warp`).
- `tests/` — Run with `python3 -m unittest discover -s tests`.
