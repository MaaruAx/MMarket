"""
config.py - Gestion de configuracion y rutas de MMarket
"""

import json
import os
from pathlib import Path
from core.constants import (
    APP_VERSION, APP_NAME, GITHUB_REPO,
    GISCUS_REPO, GISCUS_REPO_ID, GISCUS_CATEGORY, GISCUS_CATEGORY_ID,
    OFFICIAL_REGISTRY, VERSION_CHECK_URL, INSTALL_TYPES
)


class Config:
    APP_VERSION        = APP_VERSION
    APP_NAME           = APP_NAME
    GITHUB_REPO        = GITHUB_REPO
    GISCUS_REPO        = GISCUS_REPO
    GISCUS_REPO_ID     = GISCUS_REPO_ID
    GISCUS_CATEGORY    = GISCUS_CATEGORY
    GISCUS_CATEGORY_ID = GISCUS_CATEGORY_ID
    OFFICIAL_REGISTRY  = OFFICIAL_REGISTRY
    VERSION_CHECK_URL  = VERSION_CHECK_URL

    def __init__(self):
        self.app_data_dir = Path(os.environ.get("APPDATA", Path.home())) / "MMarket"
        self.app_data_dir.mkdir(parents=True, exist_ok=True)
        self.config_file    = self.app_data_dir / "config.json"
        self.installed_file = self.app_data_dir / "installed.json"
        self.cache_dir      = self.app_data_dir / "cache"
        self.cache_dir.mkdir(exist_ok=True)
        self._data = self._load()

    def _resolve_support_dir(self):
        appdata = os.environ.get("APPDATA", "")
        return Path(appdata) / "Blackmagic Design" / "DaVinci Resolve" / "Support"

    def _detect_resolve_paths(self):
        base = self._resolve_support_dir()
        return {k: str(base / v) for k, v in INSTALL_TYPES.items()}

    def _defaults(self):
        return {
            "repos": [
                {
                    "name": "MMarket Official",
                    "url": OFFICIAL_REGISTRY,
                    "official": True,
                    "enabled": True,
                }
            ],
            "theme": "default",
            "font": "Segoe UI",
            "custom_theme": {},
            "show_external": False,
            "check_updates_on_start": True,
            "resolve_paths": self._detect_resolve_paths(),
            "first_run": True,
        }

    def _load(self):
        if self.config_file.exists():
            try:
                return json.loads(self.config_file.read_text(encoding="utf-8"))
            except Exception:
                pass
        defaults = self._defaults()
        self._save(defaults)
        return defaults

    def _save(self, data):
        self.config_file.write_text(
            json.dumps(data, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

    def save(self):
        self._save(self._data)

    def get_settings(self):
        return dict(self._data)

    def save_settings(self, settings):
        if "repos" in settings:
            official = next(
                (r for r in self._data.get("repos", []) if r.get("official")), None
            )
            if official and not any(r.get("official") for r in settings["repos"]):
                settings["repos"].insert(0, official)
        self._data.update(settings)
        self.save()
        return {"ok": True}

    def get_repos(self):
        return self._data.get("repos", [])

    def add_repo(self, url, name=None):
        repos = self._data.get("repos", [])
        if any(r["url"] == url for r in repos):
            return {"ok": False, "error": "Este repositorio ya esta agregado"}
        repos.append({
            "name": name or url,
            "url": url,
            "official": False,
            "enabled": True,
        })
        self._data["repos"] = repos
        self.save()
        return {"ok": True}

    def remove_repo(self, url):
        self._data["repos"] = [
            r for r in self._data.get("repos", [])
            if r["url"] != url or r.get("official")
        ]
        self.save()
        return {"ok": True}

    def get_resolve_paths(self):
        stored = self._data.get("resolve_paths", {})
        # Rellenar tipos que falten con la deteccion automatica
        detected = self._detect_resolve_paths()
        for k in detected:
            if k not in stored:
                stored[k] = detected[k]
        return stored
