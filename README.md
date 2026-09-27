# Minecraft Chinese with Pinyin (拼音) Resource Pack

[![Release](https://img.shields.io/badge/Release-v1.0.0-emerald?style=for-the-badge&logo=github)](https://github.com/MatthewShkolnik/Minecraft-Chinese-Pinyin-Resource-Pack/releases)
[![Minecraft Version](https://img.shields.io/badge/Minecraft-1.20.5%2B%20%7C%201.21%2B-blue?style=for-the-badge&logo=mojang)](https://minecraft.net)
[![Pack Format](https://img.shields.io/badge/Pack%20Format-32-purple?style=for-the-badge)](https://minecraft.wiki/w/Pack_format)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow?style=for-the-badge)](LICENSE)
[![Python 3.9+](https://img.shields.io/badge/Generator-Python%203.9%2B-orange?style=for-the-badge&logo=python)](generate_pack.py)


A Minecraft: Java Edition resource pack that displays Chinese characters (Hanzi) alongside tone-marked Pinyin for items, blocks, mobs, and UI elements, while keeping all in-game slash commands in standard English.
<p align="center">
  <img src="banner.png" alt="Minecraft Chinese with Pinyin Banner" width="100%">
</p>
---

## Features

* **Dual Hanzi and Tone-Marked Pinyin**: Every in-game item, block, mob, and menu string is annotated with pronunciation and tone marks using Chinese NLP tokenization (`jieba` + `pypinyin`).
* **English Commands Preserved**: All command syntax, arguments, and error parsing strings (`/give`, `/teleport`, `/locate`, `/gamerule`, etc.) remain in English to maintain muscle memory and autocomplete functionality.
* **Broad Dialect Support**:
  * Simplified Chinese (`zh_cn`)
  * Traditional Chinese - Hong Kong (`zh_hk`)
  * Traditional Chinese - Taiwan (`zh_tw`)
  * Classical Chinese (`lzh`)
  * English Client Fallback (`en_us`): Allows players using English language settings to view Chinese with Pinyin without changing the system language.
* **Automated Asset Generation**: Includes a Python generator that queries Mojang's official `piston-meta` API to extract and build language assets for any game version.

---

## In-Game Examples

| Item / Concept | Standard English | Vanilla Chinese | Pinyin Resource Pack |
| :--- | :--- | :--- | :--- |
| Diamond Sword | Diamond Sword | 钻石剑 | `钻石剑 (Zuànshí Jiàn)` |
| Creeper | Creeper | 苦力怕 | `苦力怕 (Kǔlì Pà)` |
| Crafting Table | Crafting Table | 工作台 | `工作台 (Gōngzuòtái)` |
| Golden Apple | Golden Apple | 金苹果 | `金苹果 (Jīn Píngguǒ)` |
| Ender Dragon | Ender Dragon | 末影龙 | `末影龙 (Mòyǐnglóng)` |
| Potion of Swiftness | Potion of Swiftness | 迅捷药水 | `迅捷药水 (Xùnjié Yàoshuǐ)` |
| Commands | `/teleport @p ~ ~10 ~` | `/teleport @p ~ ~10 ~` | `/teleport @p ~ ~10 ~` (English) |

---

## Installation

### Method 1: Using the Pre-Built Release (Recommended)
1. Download `Minecraft-Chinese-Pinyin-v1.0.0.zip` from the [Releases](https://github.com/MatthewShkolnik/Minecraft-Chinese-Pinyin-Resource-Pack/releases) page or the [`release/`](release/) folder.
2. In Minecraft: Java Edition, go to **Options** -> **Resource Packs...** -> **Open Pack Folder**.
3. Copy the `.zip` file into the opened `resourcepacks` directory.
4. Move the pack from the **Available** column to the **Selected** column, then click **Done**.

### Method 2: Manual Folder Paths
* **Windows**: `%appdata%\.minecraft\resourcepacks`
* **macOS**: `~/Library/Application Support/minecraft/resourcepacks`
* **Linux**: `~/.minecraft/resourcepacks`

---

## Building from Source

To generate the resource pack from scratch or update it for newer Minecraft releases:

### 1. Prerequisites
Python 3.9 or newer is required.

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Run Generator
```bash
python generate_pack.py
```

The build script will:
1. Fetch the latest version manifest from Mojang's official `piston-meta` API.
2. Download English strings from the client jar for command preservation.
3. Download Chinese locale files (`zh_cn`, `zh_hk`, `zh_tw`, `lzh`).
4. Apply word segmentation and tone-marked Pinyin transformations.
5. Generate the unpacked pack and zip archive under `dist/`.

---

## Repository Structure

```text
Minecraft-Chinese-Pinyin-Resource-Pack/
├── curseforge/                         # CurseForge release graphics
│   ├── curseforge_logo.png             # 1024x1024 project avatar
│   ├── curseforge_banner.png           # 1376x768 (16:9) banner
│   └── curseforge_banner_wide.png      # 1376x458 (3:1) header banner
├── dist/                               # Generated unpacked pack and zip
│   ├── Pinyin_Resource_Pack/
│   │   ├── assets/minecraft/lang/      # zh_cn, zh_hk, zh_tw, lzh, en_us
│   │   ├── pack.mcmeta
│   │   └── pack.png
│   └── Pinyin_Resource_Pack.zip
├── release/                            # Distribution release assets
│   ├── Minecraft-Chinese-Pinyin-v1.0.0.zip
│   ├── RELEASE_NOTES.md
│   ├── SHA256SUMS.txt
│   ├── INSTALL.md
│   ├── pack.mcmeta
│   └── pack.png
├── generate_pack.py                    # Pack generator script
├── pack.png                            # Pack icon (256x256)
├── requirements.txt                    # Python dependencies
├── LICENSE                             # MIT License
└── README.md                           # Documentation
```

---

## Contributing

Feedback, bug reports, and pull requests are welcome:
* Polyphonic character pronunciation corrections (多音字).
* Support for additional game versions or Bedrock Edition.
* Submit issues and pull requests via the [GitHub Issues](https://github.com/MatthewShkolnik/Minecraft-Chinese-Pinyin-Resource-Pack/issues) page.

---

## License

Distributed under the [MIT License](LICENSE).

Minecraft is a registered trademark of Mojang AB / Microsoft. This project is an independent community resource pack and is not affiliated with Mojang or Microsoft.
