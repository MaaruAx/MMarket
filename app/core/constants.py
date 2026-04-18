
APP_VERSION   = "0.1.0"
APP_NAME      = "MMarket"
GITHUB_REPO   = "MaaruAx/MMarket"
GISCUS_REPO   = "MaaruAx/MMarket"
GISCUS_REPO_ID     = ""
GISCUS_CATEGORY    = "Plugins"
GISCUS_CATEGORY_ID = ""

OFFICIAL_REGISTRY = (
    "https://raw.githubusercontent.com/MaaruAx/MMarket/main/registry/registry.json"
)
VERSION_CHECK_URL = (
    "https://raw.githubusercontent.com/MaaruAx/MMarket/main/registry/version.json"
)

# Mapeo install_type -> subcarpeta relativa dentro de Support\
INSTALL_TYPES = {
    "drfx":    r"Fusion\Templates",
    "setting": r"Fusion\Templates\Edit",
    "script":  r"Fusion\Scripts\Utility",
    "fuse":    r"Fusion\Fuses",
    "macro":   r"Fusion\Macros",
    "lut":     r"LUT",
}

INSTALL_TYPE_LABELS = {
    "drfx":    "Plugin (.drfx)",
    "setting": "Efecto (.setting)",
    "script":  "Script (.py / .lua)",
    "fuse":    "Fuse (.fuse)",
    "macro":   "Macro (.setting)",
    "lut":     "LUT (.cube / .3dl)",
}
