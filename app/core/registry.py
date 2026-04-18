"""
registry.py — Descarga y caché de registries de múltiples repos
TTL de caché: 5 minutos. Si el fetch falla, usa el caché stale.
"""

import hashlib
import json
import time
import urllib.error
import urllib.request
from pathlib import Path


CACHE_TTL = 300  # segundos


class RegistryManager:
    def __init__(self, config):
        self.config    = config
        self.cache_dir = config.cache_dir

    # ──────────────────────────────────────────────────────────────────────────
    # Caché
    # ──────────────────────────────────────────────────────────────────────────

    def _cache_path(self, url: str) -> Path:
        h = hashlib.md5(url.encode()).hexdigest()
        return self.cache_dir / f"reg_{h}.json"

    def _fetch_url(self, url: str, timeout: int = 10) -> dict | None:
        try:
            req = urllib.request.Request(
                url,
                headers={"User-Agent": f"MMarket/{self.config.APP_VERSION}"},
            )
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return json.loads(r.read().decode("utf-8"))
        except Exception:
            return None

    def _get_cached_or_fetch(self, url: str) -> dict | None:
        cache_file = self._cache_path(url)

        # Caché válido
        if cache_file.exists():
            age = time.time() - cache_file.stat().st_mtime
            if age < CACHE_TTL:
                try:
                    return json.loads(cache_file.read_text(encoding="utf-8"))
                except Exception:
                    pass

        # Fetch fresco
        data = self._fetch_url(url)
        if data:
            try:
                cache_file.write_text(json.dumps(data), encoding="utf-8")
            except Exception:
                pass
            return data

        # Caché stale (mejor que nada)
        if cache_file.exists():
            try:
                return json.loads(cache_file.read_text(encoding="utf-8"))
            except Exception:
                pass

        return None

    # ──────────────────────────────────────────────────────────────────────────
    # API pública
    # ──────────────────────────────────────────────────────────────────────────

    def get_plugins(self, repo_url: str = None) -> dict:
        repos = self.config.get_repos()
        if repo_url:
            repos = [r for r in repos if r["url"] == repo_url]

        all_plugins = []
        failed_repos = []

        for repo in repos:
            if not repo.get("enabled", True):
                continue

            data = self._get_cached_or_fetch(repo["url"])
            if data and "plugins" in data:
                repo_meta = data.get("repo", {})
                for plugin in data["plugins"]:
                    # Inyectar metadata del repo en cada plugin
                    plugin["_repo_name"]     = repo_meta.get("name", repo["name"])
                    plugin["_repo_url"]      = repo["url"]
                    plugin["_repo_official"] = repo.get("official", False)
                all_plugins.extend(data["plugins"])
            else:
                failed_repos.append(repo.get("name", repo["url"]))

        return {"plugins": all_plugins, "failed": failed_repos}

    def validate_repo_url(self, url: str) -> dict:
        """Valida que una URL apunte a un registry.json válido antes de agregarlo."""
        data = self._fetch_url(url)
        if not data:
            return {"ok": False, "error": "No se pudo conectar a esa URL"}
        if "plugins" not in data:
            return {"ok": False, "error": "El archivo no tiene el formato de registry correcto"}
        name = data.get("repo", {}).get("name", url)
        count = len(data["plugins"])
        return {"ok": True, "name": name, "plugin_count": count}

    def clear_cache(self) -> dict:
        for f in self.cache_dir.glob("reg_*.json"):
            try:
                f.unlink()
            except Exception:
                pass
        return {"ok": True}

