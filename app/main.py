"""
main.py - Entry point de MMarket.
"""

import json
import os
import sys
import webbrowser
import winreg
try:
    import requests as _requests
except ImportError:
    _requests = None
from pathlib import Path

APP_DIR = Path(__file__).parent
sys.path.insert(0, str(APP_DIR))

from core.config    import Config
from core.constants import INSTALL_TYPE_LABELS
from core.registry  import RegistryManager
from core.installer import Installer
from core.updater   import Updater


class MMarketAPI:
    def __init__(self):
        self._config    = Config()
        self._registry  = RegistryManager(self._config)
        self._installer = Installer(self._config)
        self._updater   = Updater(self._config)

    def _ok(self, data=None):
        return json.dumps({"ok": True, **(data or {})})

    def _err(self, msg):
        return json.dumps({"ok": False, "error": msg})

    def _j(self, obj):
        return json.dumps(obj, ensure_ascii=False)

    def _parse(self, s):
        if isinstance(s, str):
            return json.loads(s)
        return s

    def get_plugins(self, repo_url=None):
        data = self._registry.get_plugins(repo_url)
        if "plugins" in data:
            data["plugins"] = sorted(
                data["plugins"],
                key=lambda p: p.get("priority", 0),
                reverse=True
            )
        return self._j(data)

    def get_install_type_labels(self):
        return self._j(INSTALL_TYPE_LABELS)

    def validate_repo_url(self, url):
        return self._j(self._registry.validate_repo_url(url))

    def clear_cache(self):
        return self._j(self._registry.clear_cache())

    def get_repos(self):
        return self._j(self._config.get_repos())

    def add_repo(self, url):
        validation = self._registry.validate_repo_url(url)
        if not validation.get("ok"):
            return self._j(validation)
        return self._j(self._config.add_repo(url, validation.get("name")))

    def remove_repo(self, url):
        return self._j(self._config.remove_repo(url))

    def install_plugin(self, plugin_json):
        return self._j(self._installer.install(self._parse(plugin_json)))

    def uninstall_plugin(self, plugin_id):
        return self._j(self._installer.uninstall(plugin_id))

    def get_installed(self):
        installed = self._installer.get_installed()
        registry_data = self._registry.get_plugins()
        plugin_map = {p["id"]: p for p in registry_data.get("plugins", [])}
        for record in installed:
            latest = plugin_map.get(record["id"])
            if latest:
                from core.updater import _parse_version
                current = _parse_version(record.get("version", "0"))
                remote  = _parse_version(latest.get("version", "0"))
                record["has_update"]     = remote > current
                record["latest_version"] = latest.get("version")
                record["thumbnail"]      = latest.get("thumbnail", "")
            else:
                record["has_update"] = False
        return self._j(installed)

    def scan_resolve_folders(self):
        return self._j(self._installer.scan_resolve_folders())

    def delete_external_file(self, file_path):
        import shutil
        try:
            p = Path(file_path)
            if p.is_file(): p.unlink()
            elif p.is_dir(): shutil.rmtree(p)
            return self._ok()
        except Exception as e:
            return self._err(str(e))

    def get_settings(self):
        s = self._config.get_settings()
        s["app_version"] = self._config.APP_VERSION
        s["giscus"] = {
            "repo":        self._config.GISCUS_REPO,
            "repo_id":     self._config.GISCUS_REPO_ID,
            "category":    self._config.GISCUS_CATEGORY,
            "category_id": self._config.GISCUS_CATEGORY_ID,
        }
        return self._j(s)

    def save_settings(self, settings_json):
        return self._j(self._config.save_settings(self._parse(settings_json)))

    def detect_resolve_paths(self):
        return self._j(self._config._detect_resolve_paths())

    def check_update(self):
        return self._j(self._updater.check())

    def open_bug_report(self, info_json):
        return self._j(self._updater.open_bug_report(self._parse(info_json)))

    def get_system_fonts(self):
        fonts = []
        try:
            key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE,
                r"SOFTWARE\Microsoft\Windows NT\CurrentVersion\Fonts")
            i = 0
            while True:
                try:
                    name, _, _ = winreg.EnumValue(key, i)
                    fonts.append(name.replace(" (TrueType)","").replace(" (OpenType)","").strip())
                    i += 1
                except OSError:
                    break
        except Exception:
            fonts = ["Segoe UI", "Arial", "Consolas"]
        return self._j(sorted(set(fonts)))

    def open_url(self, url):
        webbrowser.open(url)
        return self._ok()

    def open_folder(self, path):
        try:
            p = __import__('pathlib').Path(path)
            p.mkdir(parents=True, exist_ok=True)
            os.startfile(str(p))
            return self._ok()
        except Exception as e:
            return self._err(str(e))

    def pick_folder(self, current_path):
        try:
            import webview
            import threading
            result = [None]
            def _pick():
                wins = webview.windows
                if not wins:
                    return
                try:
                    r = wins[0].create_file_dialog(
                        webview.FileDialog.FOLDER,
                        directory=current_path if current_path else ''
                    )
                except AttributeError:
                    r = wins[0].create_file_dialog(
                        webview.FOLDER_DIALOG,
                        directory=current_path if current_path else ''
                    )
                result[0] = r[0] if r else None
            t = threading.Thread(target=_pick)
            t.start()
            t.join(timeout=60)
            if result[0]:
                return self._j({'ok': True, 'path': result[0]})
            return self._j({'ok': False, 'cancelled': True})
        except Exception as e:
            return self._err(str(e))

    def get_app_version(self):
        return self._j({"version": self._config.APP_VERSION})


    # ── GitHub Auth (Device Flow) ────────────────────────────────────────────
    # Called by the frontend to bypass CORS restrictions from file:// origin.
    # Requires: pip install requests

    def github_device_code(self, client_id):
        """Request a device_code from GitHub for the Device Flow."""
        if _requests is None:
            return self._err("requests not installed. Run: pip install requests")
        try:
            r = _requests.post(
                "https://github.com/login/device/code",
                headers={"Accept": "application/json"},
                json={"client_id": client_id, "scope": "public_repo"},
                timeout=15,
            )
            return r.text
        except Exception as e:
            return self._err(str(e))

    def github_poll_token(self, client_id, device_code):
        """Poll for OAuth access_token after user completes Device Flow."""
        if _requests is None:
            return self._err("requests not installed")
        try:
            r = _requests.post(
                "https://github.com/login/oauth/access_token",
                headers={"Accept": "application/json"},
                json={
                    "client_id": client_id,
                    "device_code": device_code,
                    "grant_type": "urn:ietf:params:oauth:grant-type:device_code",
                },
                timeout=15,
            )
            return r.text
        except Exception as e:
            return self._err(str(e))

    def github_api_get(self, token, path):
        """Authenticated GET to GitHub API."""
        if _requests is None:
            return self._err("requests not installed")
        url = path if path.startswith("http") else f"https://api.github.com/{path}"
        try:
            r = _requests.get(
                url,
                headers={
                    "Authorization": f"Bearer {token}",
                    "Accept": "application/vnd.github.v3+json",
                },
                timeout=15,
            )
            return r.text
        except Exception as e:
            return self._err(str(e))

    def github_api_post(self, token, path, body):
        """Authenticated POST to GitHub API."""
        if _requests is None:
            return self._err("requests not installed")
        url = path if path.startswith("http") else f"https://api.github.com/{path}"
        try:
            r = _requests.post(
                url,
                headers={
                    "Authorization": f"Bearer {token}",
                    "Content-Type": "application/json",
                    "Accept": "application/vnd.github.v3+json",
                },
                data=body,
                timeout=15,
            )
            return r.text
        except Exception as e:
            return self._err(str(e))

    def uninstall_mmarket(self):
        import subprocess, tempfile
        app_data    = str(self._config.app_data_dir).replace('/', '\\')
        install_dir = str(APP_DIR.parent).replace('/', '\\')
        desktop_lnk = str(Path.home() / 'Desktop' / 'MMarket.lnk')

        bat = (
            "@echo off\n"
            "timeout /t 3 /nobreak >nul\n"
            f'if exist "{app_data}" rd /s /q "{app_data}"\n'
            f'if exist "{install_dir}" rd /s /q "{install_dir}"\n'
            f'if exist "{desktop_lnk}" del /f /q "{desktop_lnk}"\n'
            "echo MMarket desinstalado.\n"
        )
        tmp = Path(tempfile.mktemp(suffix=".bat"))
        tmp.write_text(bat, encoding="ascii")
        subprocess.Popen(
            ['cmd', '/c', 'start', '/min', str(tmp)],
            creationflags=subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP,
            close_fds=True
        )
        return self._ok()


def main():
    try:
        import webview
    except ImportError:
        print("ERROR: pip install pywebview")
        sys.exit(1)

    api     = MMarketAPI()
    ui_path = APP_DIR / "ui" / "index.html"

    webview.create_window(
        title="MMarket",
        url=ui_path.as_uri(),
        js_api=api,
        width=1280,
        height=820,
        min_size=(960, 640),
        background_color="#0d0d0d",
    )
    webview.start(debug=True)


if __name__ == "__main__":
    main()
