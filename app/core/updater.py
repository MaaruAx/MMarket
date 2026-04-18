"""
updater.py — Chequea actualizaciones del app y abre reportes de bugs en GitHub.
"""

import json
import platform
import sys
import urllib.parse
import urllib.request
import webbrowser


def _parse_version(v: str) -> tuple:
    """Convierte '1.2.3' en (1, 2, 3) para comparación."""
    try:
        return tuple(int(x) for x in str(v).strip().split("."))
    except Exception:
        return (0, 0, 0)


class Updater:
    def __init__(self, config):
        self.config = config

    def check(self) -> dict:
        try:
            req = urllib.request.Request(
                self.config.VERSION_CHECK_URL,
                headers={"User-Agent": f"MMarket/{self.config.APP_VERSION}"},
            )
            with urllib.request.urlopen(req, timeout=10) as r:
                data = json.loads(r.read().decode("utf-8"))

            remote  = data.get("version", "0.0.0")
            current = self.config.APP_VERSION
            has_update = _parse_version(remote) > _parse_version(current)

            return {
                "ok":           True,
                "has_update":   has_update,
                "current":      current,
                "latest":       remote,
                "download_url": data.get("download_url", ""),
                "changelog":    data.get("changelog", ""),
            }
        except Exception as e:
            return {
                "ok":         False,
                "has_update": False,
                "error":      str(e),
            }

    def open_bug_report(self, info: dict) -> dict:
        """
        Abre el navegador con un Issue de GitHub pre-llenado.
        No envía ningún dato sin consentimiento del usuario.
        """
        base = f"https://github.com/{self.config.GITHUB_REPO}/issues/new"

        description = info.get("description", "").strip() or "(sin descripción)"
        module      = info.get("module", "No especificado")
        title       = info.get("title", "").strip() or "Reporte de bug"

        body = f"""## Descripción
{description}

## Módulo afectado
{module}

## Información del sistema
| Campo | Valor |
|---|---|
| MMarket | {self.config.APP_VERSION} |
| Python | {sys.version.split()[0]} |
| Windows | {platform.version()} |
| Resolve | {info.get("resolve_version", "No detectado")} |

---
*Generado automáticamente por MMarket*
"""

        params = urllib.parse.urlencode({
            "title":  f"[Bug] {title}",
            "body":   body,
            "labels": "bug",
        })

        webbrowser.open(f"{base}?{params}")
        return {"ok": True}

