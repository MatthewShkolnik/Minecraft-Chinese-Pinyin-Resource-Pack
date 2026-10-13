# Minecraft Chinese with Pinyin (v1.2.1)

Welcome to the **v1.2.1** release of the Minecraft Chinese Pinyin Resource Pack.

This release introduces **persistent configuration via a `.config` file**, named Minecraft color support for Pinyin annotations, and preserves the full suite of Java and Bedrock Edition packs, regional phonetics, and learning modes introduced in v1.2.0.

---

## What's New in v1.2.1

### 1. Configuration File Support (`.config`)
* **Persistent Defaults**: You can now define your preferred Pinyin annotation color, phonetic style, and study modes in a project `.config` file instead of passing CLI arguments on every generator run.
* **Format Flexibility**: Accepts standard INI/key-value pairs (with `#` and `;` comments) as well as JSON formatting.
* **Precedence Rules**: CLI options (`--pinyin-color`, `--no-color`, `--pinyin-style`, `--recall`) cleanly take priority over `.config` settings.

### 2. Named Minecraft Colors
* Pinyin annotation colors can now be specified using intuitive color names both in `.config` and via the `--pinyin-color` CLI flag:
  * `gold` (`§6`), `yellow` (`§e`), `gray` (`§7`), `aqua` (`§b`), `green` (`§a`), `red` (`§c`), `light_purple` (`§d`), `white` (`§f`), and more.
  * Disabling color annotations is supported with `none`, `off`, or `false`.

---

## Features from v1.2.0

* **Minecraft Bedrock Edition Export (`.mcpack`)**: Complete cross-platform Bedrock resource pack with official vanilla string translations and 100% English slash command retention.
* **Regional Phonetics & Custom In-Game Languages**:
  * **中文 (注音)** (`zh_zy`) with character-spaced Bopomofo annotations.
  * **廣東話 (粵拼)** (`zh_yue`) with offline LSHK Jyutping dictionary.
* **Muted Pinyin Styling (`§7` Gray)**: Pronunciation annotations appear in clean subtle gray `§7(...)§r` so Chinese characters remain visually distinct and dominant.
* **Learning Modes & Multi-Variant Builder**: Tone Numbers mode (`--pinyin-style numbers`), Character Recall mode (`--recall`), and multi-pack generation (`--all-variants`).
* **1.21.4 Pale Garden Support**: Phonetic polyphone overrides for Creaking (`嘎枝`), Creaking Heart (`嘎枝之心`), Pale Garden (`苍白之园`), Eyeblossom (`眼眸花`), and Breeze (`旋风人`).

---

## Release Assets

| File | Type | Description |
| :--- | :--- | :--- |
| `Minecraft-Chinese-Pinyin-v1.2.1.zip` | Java Edition Pack | Standard tone-marked pack with `zh_py`, `zh_zy`, and `zh_yue` |
| `Minecraft-Chinese-Pinyin-v1.2.1-Numbers.zip` | Java Edition Pack | Pinyin tone numbers variant (e.g. `Zuan4shi2 Jian4`) |
| `Minecraft-Chinese-Pinyin-v1.2.1-Recall.zip` | Java Edition Pack | Character recall mode variant (Pinyin first) |
| `Minecraft-Chinese-Pinyin-v1.2.1.mcpack` | Bedrock Edition Pack | Bedrock resource pack for Windows, Android, iOS, and consoles |
| `SHA256SUMS.txt` | Checksums | Cryptographic integrity verification |

---

## Installation

### Java Edition
1. Download `Minecraft-Chinese-Pinyin-v1.2.1.zip` (or Numbers / Recall).
2. Open Minecraft: Java Edition, go to **Options** -> **Resource Packs...** -> **Open Pack Folder**.
3. Drag and drop the `.zip` file into the folder.
4. Move the pack to **Selected** and click **Done**.
5. Under **Options** -> **Language...**, choose **中文 (拼音)**, **中文 (注音)**, **廣東話 (粵拼)**, or your preferred language.

### Bedrock Edition
1. Download `Minecraft-Chinese-Pinyin-v1.2.1.mcpack`.
2. Double-click or open the `.mcpack` file on your device to import into Minecraft.
3. In Minecraft: Bedrock Edition, go to **Settings** -> **Global Resources**, find the pack, and click **Activate**.
