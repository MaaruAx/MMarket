-----

# MMarket
![Version](https://img.shields.io/badge/Version-1.0.0-yellow?style=for-the-badge&labelColor=black)
![Development](https://img.shields.io/badge/Status-Active_Development-green?style=for-the-badge&labelColor=black)
![Resolve Compatibility](https://img.shields.io/badge/DaVinci_Resolve-All_Versions-white?style=for-the-badge&logo=davinciresolve&logoColor=white&labelColor=black&color=6370FF)
![Platform](https://img.shields.io/badge/Platform-Windows-0078D4?style=for-the-badge&logo=windows&logoColor=white&labelColor=black)

**MMarket** is a free, open-source marketplace designed to streamline your DaVinci Resolve workflow. Browse, install, and manage plugins, macros, LUTs, fuses, and scripts from a single standalone desktop application.

-----

## ⚡ Quick Start

Install MMarket instantly via PowerShell. The installer handles dependencies and configuration for you.

```powershell
irm https://raw.githubusercontent.com/MaaruAx/MMarket/main/install.ps1 | iex
```

> [\!IMPORTANT]
> **System Requirements:** Windows only. Requires **Python 3.8–3.13 (64-bit)**.

-----

## ✨ Core Features

  * **Integrated Store:** Browse by type, repository, or compatibility (Free vs. Studio). Includes detailed views with screenshots, carousels, usage notes, and changelogs.
  * **Software Hub:** A dedicated section for companion apps and external tools that enhance DaVinci Resolve.
  * **Smart Management:**
      * **Downloads:** Real-time progress tracking with persistent history.
      * **Installed:** One-click updates and uninstalls. Features a "Ghost Scan" to find local files not installed via MMarket.
  * **Community Presets:** A collaborative space to share and request presets. Submissions are managed transparently via GitHub Issues.
  * **Theming Engine:** Fully customizable UI. Ships with a signature Black & Yellow dark theme. Edit any color via hex or use themes provided by community repositories.

-----

## 🌐 Decentralized Repositories

MMarket is built for the community. You aren't locked into a single store:

  * **Multiple Sources:** Add any `registry.json` URL in Settings to merge different registries into your local store.
  * **Simple Schema:** Hosting your own registry is as easy as hosting a JSON file. Supports YouTube embeds, image galleries, and compatibility flags.

[**View Registry Example →**](https://github.com/MaaruAx/MMarket/blob/main/registry/registry.json)

-----

## 🛠️ Contributing

MMarket is 100% open source. There are several ways to help:

1.  **Plugins:** Submit your tools to the official registry.
2.  **Themes:** Share your custom UI skins.
3.  **Presets:** Help others by sharing your Resolve presets.

Maintainers can manage the official registry via our **Vercel-hosted Admin Panel**, eliminating the need for manual JSON editing for verified contributors.

-----

### Links

  * **Main Repository:** [github.com/MaaruAx/MMarket](https://github.com/MaaruAx/MMarket)
  * **Report a Bug:** [GitHub Issues](https://github.com/MaaruAx/MMarket/issues)
## License

MIT 

