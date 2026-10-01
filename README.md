# Minecraft Chinese with Pinyin (拼音) Resource Pack

[![Release](https://img.shields.io/badge/Release-v1.1.0-emerald?style=for-the-badge&logo=github)](https://github.com/MatthewShkolnik/Minecraft-Chinese-Pinyin-Resource-Pack/releases)
[![Minecraft Version](https://img.shields.io/badge/Minecraft-1.20.5%2B%20%7C%201.21%2B-blue?style=for-the-badge&logo=mojang)](https://minecraft.net)
[![Pack Format](https://img.shields.io/badge/Pack%20Format-32--97-purple?style=for-the-badge)](https://minecraft.wiki/w/Pack_format)
[![CI](https://img.shields.io/badge/CI-Passing-brightgreen?style=for-the-badge&logo=github-actions)](https://github.com/MatthewShkolnik/Minecraft-Chinese-Pinyin-Resource-Pack/actions)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow?style=for-the-badge)](LICENSE)
[![Python 3.9+](https://img.shields.io/badge/Generator-Python%203.9%2B-orange?style=for-the-badge&logo=python)](generate_pack.py)

<p align="center">
  <img src="banner.png" alt="Minecraft Chinese with Pinyin Banner" width="100%">
</p>

A Minecraft: Java Edition resource pack that displays Chinese characters (Hanzi) alongside tone-marked Pinyin for items, blocks, mobs, and UI elements, while keeping all in-game slash commands and parser feedback in standard English.

---

## Features

* **Dual Hanzi and Tone-Marked Pinyin**: Every in-game item, block, mob, and menu string is annotated with pronunciation and tone marks using Chinese NLP tokenization (`jieba` + `pypinyin`).
* **Broad CJK Unicode Coverage**: Supports standard BMP Hanzi as well as CJK Extension A, compatibility, and supplementary plane characters (e.g. `䃮` cobblestone, `㭜` acacia, `䦪` creaking, `𥹉`).
* **Domain Polyphone Overrides (`data/pinyin_overrides.json`)**: Fine-tuned pronunciation for Minecraft-specific terminology (e.g. `重锤` -> `Zhòngchuí`, `藏宝图` -> `Cángbǎotú`, `附魔` -> `Fùmó`, `潜影贝` -> `Qiányǐngbèi`).
* **100% English Commands Preserved**: All command syntax, arguments, error parsing strings, and command feedback (`/give`, `/teleport`, `/locate`, `/gamerule`, argument helpers, SNBT parsing) remain in standard English to maintain muscle memory and autocomplete functionality.
* **Broad Dialect & Custom Language Support**:
  * **Dedicated Language (`zh_py`)**: Registered directly in `pack.mcmeta` as **中文 (拼音) / Chinese with Pinyin**, selectable from the Language menu without changing system English.
  * Simplified Chinese (`zh_cn`)
  * Traditional Chinese - Hong Kong (`zh_hk`)
  * Traditional Chinese - Taiwan (`zh_tw`)
  * Classical Chinese (`lzh`): Uses clean monosyllabic tokenization for classical grammar morphemes.
  * English Client Fallback (`en_us`): Allows players using English language settings to view Chinese with Pinyin immediately upon activating the pack.
* **Multi-Version Compatibility**: Includes `supported_formats` (`min_inclusive: 32, max_inclusive: 97+`) to eliminate red "Incompatible pack" warnings across 1.20.5 through 1.21.4+ and newer releases.
* **Fast Automated Asset Generation**: Includes a cached Python generator that queries Mojang's official `piston-meta` API with local caching and CLI flags.

---

## Use Cases

* **Language Learning**: Learn vocabulary and character pronunciation through in-game context without relying on standalone flashcards.
* **Multiplayer and International Servers**: Navigate Chinese-language Minecraft servers, inventories, trade menus, and chat references without translation friction.
* **Heritage Speakers**: Bridge existing conversational spoken Mandarin with character recognition using Pinyin phonetic guides.
* **Server Administration**: Maintain and execute command blocks, macros, and server commands without broken syntax or localized command arguments.
* **Bilingual Content Creation**: Produce dual-language content accessible to both English- and Chinese-speaking audiences.

---

## In-Game Examples

| Item / Concept | Standard English | Vanilla Chinese | Pinyin Resource Pack |
| :--- | :--- | :--- | :--- |
| Diamond Sword | Diamond Sword | 钻石剑 | `钻石剑 (Zuànshí Jiàn)` |
| Mace | Mace | 重锤 | `重锤 (Zhòngchuí)` |
| Creeper | Creeper | 苦力怕 | `苦力怕 (Kǔlì Pà)` |
| Crafting Table | Crafting Table | 工作台 | `工作台 (Gōngzuòtái)` |
| Golden Apple | Golden Apple | 金苹果 | `金苹果 (Jīnpíngguǒ)` |
| Buried Treasure Map | Buried Treasure Map | 藏宝图 | `藏宝图 (Cángbǎotú)` |
| Ender Dragon | Ender Dragon | 末影龙 | `末影龙 (Mòyǐnglóng)` |
| Cobblestone (Classical) | Cobblestone | 䃮 | `䃮 (Tán)` |
| Commands | `/gamerule keepInventory true` | `游戏规则...` | `/gamerule keepInventory true` (English) |

---

## Installation

### Method 1: Using the Pre-Built Release (Recommended)
1. Download `Minecraft-Chinese-Pinyin-v1.1.0.zip` from the [Releases](https://github.com/MatthewShkolnik/Minecraft-Chinese-Pinyin-Resource-Pack/releases) page or the [`release/`](release/) folder.
2. In Minecraft: Java Edition, go to **Options** -> **Resource Packs...** -> **Open Pack Folder**.
3. Copy the `.zip` file into the opened `resourcepacks` directory.
4. Move the pack from the **Available** column to the **Selected** column, then click **Done**.
5. Under **Options** -> **Language...**, select **中文 (拼音)**, any Chinese dialect, or keep **English (US)**.

### Method 2: Manual Folder Paths
* **Windows**: `%appdata%\.minecraft\resourcepacks`
* **macOS**: `~/Library/Application Support/minecraft/resourcepacks`
* **Linux**: `~/.minecraft/resourcepacks`

---

## Building from Source

To generate the resource pack from scratch or target specific Minecraft releases:

### 1. Prerequisites
Python 3.9 or newer is required.

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Run Generator
```bash
# Build latest release with default caching
python generate_pack.py

# Or target a specific Minecraft release
python generate_pack.py --version 1.21.1

# Or skip creating the .zip archive for quick inspection
python generate_pack.py --no-zip
```

### 4. Run Automated Test Suite
```bash
python -m unittest discover -s tests -v
```

---

## Repository Structure

```text
Minecraft-Chinese-Pinyin-Resource-Pack/
├── .github/
│   └── workflows/
│       └── ci.yml                      # Automated CI workflow (Python 3.9-3.13)
├── curseforge/                         # CurseForge release graphics
│   ├── curseforge_logo.png             # 1024x1024 project avatar
│   ├── curseforge_banner.png           # 1376x768 (16:9) banner
│   └── curseforge_banner_wide.png      # 1376x458 (3:1) header banner
├── data/
│   └── pinyin_overrides.json           # Domain polyphone & CJK extension overrides
├── dist/                               # Generated unpacked pack and zip
│   ├── Pinyin_Resource_Pack/
│   │   ├── assets/minecraft/lang/      # zh_cn, zh_hk, zh_tw, lzh, zh_py, en_us
│   │   ├── pack.mcmeta
│   │   └── pack.png
│   └── Pinyin_Resource_Pack.zip
├── release/                            # Distribution release assets
│   ├── Minecraft-Chinese-Pinyin-v1.1.0.zip
│   ├── RELEASE_NOTES.md
│   ├── SHA256SUMS.txt
│   ├── INSTALL.md
│   ├── pack.mcmeta
│   └── pack.png
├── tests/
│   └── test_pack.py                    # Automated test suite
├── banner.png                          # Repository banner
├── generate_pack.py                    # Pack generator script
├── pack.png                            # Pack icon (256x256)
├── requirements.txt                    # Python dependencies
├── LICENSE                             # MIT License
└── README.md                           # Documentation
```

---

## Contributing

Feedback, bug reports, and pull requests are welcome:
* **Polyphonic corrections (多音字)**: Submit updates directly to [`data/pinyin_overrides.json`](data/pinyin_overrides.json).
* **New Minecraft versions**: Test compatibility with new snapshots or drops.
* Submit issues and pull requests via the [GitHub Issues](https://github.com/MatthewShkolnik/Minecraft-Chinese-Pinyin-Resource-Pack/issues) page.

---

## License

Distributed under the [MIT License](LICENSE).

Minecraft is a registered trademark of Mojang AB / Microsoft. This project is an independent community resource pack and is not affiliated with Mojang or Microsoft.
