"""
installer.py - Instala y desinstala plugins en las carpetas de DaVinci Resolve.
"""

import json
import shutil
import urllib.request
import zipfile
import tarfile
from pathlib import Path
from core.constants import INSTALL_TYPES


class Installer:
    def __init__(self, config):
        self._config         = config
        self.installed_file  = config.installed_file
        self._installed      = self._load()

    def _load(self):
        if self.installed_file.exists():
            try:
                return json.loads(self.installed_file.read_text(encoding="utf-8"))
            except Exception:
                pass
        return {}

    def _save(self):
        self.installed_file.write_text(
            json.dumps(self._installed, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

    def _get_install_path(self, install_type):
        paths = self._config.get_resolve_paths()
        if install_type not in paths:
            return None
        return Path(paths[install_type])

    def _download(self, url, dest):
        try:
            req = urllib.request.Request(
                url,
                headers={"User-Agent": "MMarket/" + self._config.APP_VERSION},
            )
            with urllib.request.urlopen(req, timeout=60) as r:
                dest.write_bytes(r.read())
            return True
        except Exception:
            return False

    def install(self, plugin):
        plugin_id    = plugin.get("id")
        install_type = plugin.get("install_type")
        download_url = plugin.get("download_url")

        if not all([plugin_id, install_type, download_url]):
            return {"ok": False, "error": "Datos del plugin incompletos"}

        if install_type not in INSTALL_TYPES:
            return {"ok": False, "error": "Tipo de instalacion desconocido: " + install_type}

        install_path = self._get_install_path(install_type)
        if not install_path:
            return {"ok": False, "error": "Ruta de instalacion no configurada para: " + install_type}

        try:
            install_path.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            return {"ok": False, "error": "No se pudo crear el directorio: " + str(e)}

        filename  = download_url.split("/")[-1].split("?")[0]
        temp_file = self._config.cache_dir / ("dl_" + plugin_id + "_" + filename)

        if not self._download(download_url, temp_file):
            return {"ok": False, "error": "Error al descargar el plugin"}

        installed_files = []
        try:
            if filename.endswith(".zip"):
                with zipfile.ZipFile(temp_file, "r") as z:
                    z.extractall(install_path)
                    installed_files = [str(install_path / n) for n in z.namelist()]
            elif filename.endswith((".tar.gz", ".tgz")):
                with tarfile.open(temp_file, "r:gz") as t:
                    t.extractall(install_path)
                    installed_files = [str(install_path / m.name) for m in t.getmembers()]
            else:
                dest = install_path / filename
                shutil.copy2(temp_file, dest)
                installed_files = [str(dest)]
        except Exception as e:
            return {"ok": False, "error": "Error al instalar: " + str(e)}
        finally:
            temp_file.unlink(missing_ok=True)

        self._installed[plugin_id] = {
            "id":           plugin_id,
            "name":         plugin.get("name", plugin_id),
            "version":      plugin.get("version", "unknown"),
            "install_type": install_type,
            "install_path": str(install_path),
            "files":        installed_files,
            "repo_url":     plugin.get("_repo_url", ""),
            "repo_name":    plugin.get("_repo_name", ""),
        }
        self._save()
        return {"ok": True, "plugin_id": plugin_id}

    def uninstall(self, plugin_id):
        if plugin_id not in self._installed:
            return {"ok": False, "error": "Plugin no registrado en MMarket"}

        record  = self._installed[plugin_id]
        errores = []
        for f_str in record.get("files", []):
            try:
                p = Path(f_str)
                if p.is_file():   p.unlink()
                elif p.is_dir():  shutil.rmtree(p)
            except Exception as e:
                errores.append(str(e))

        del self._installed[plugin_id]
        self._save()
        return {"ok": True, "warnings": errores} if errores else {"ok": True}

    def get_installed(self):
        return list(self._installed.values())

    def is_installed(self, plugin_id):
        return plugin_id in self._installed

    def get_installed_version(self, plugin_id):
        record = self._installed.get(plugin_id)
        return record["version"] if record else None

    def scan_resolve_folders(self):
        paths    = self._config.get_resolve_paths()
        tracked  = set()
        for record in self._installed.values():
            tracked.update(record.get("files", []))

        external = []
        for type_key, path_str in paths.items():
            folder = Path(path_str)
            if not folder.exists():
                continue
            for item in folder.iterdir():
                if str(item) not in tracked:
                    external.append({
                        "name":         item.name,
                        "path":         str(item),
                        "install_type": type_key,
                        "is_dir":       item.is_dir(),
                        "size":         item.stat().st_size if item.is_file() else 0,
                    })
        return external
