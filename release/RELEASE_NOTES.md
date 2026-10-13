# Minecraft Chinese with Pinyin (v1.2.0)

Welcome to the **v1.2.0** major release of the Minecraft Chinese Pinyin Resource Pack.

This release brings support for **Minecraft Bedrock Edition (`.mcpack`)**, regional phonetic guides (**Zhuyin/Bopomofo** and **Cantonese Jyutping**), **Muted Pinyin Styling**, **Tone Numbers**, **Character Recall Mode**, and modern **1.21.4 Pale Garden** terminology.

---

## What's New in v1.2.0

### 1. Minecraft Bedrock Edition Export (`.mcpack`)
* **Cross-Platform Compatibility**: Full support for Minecraft Bedrock Edition across Windows, iOS, iPadOS, Android, and consoles.
* **One-Click Installation**: Packaged as a standard `.mcpack` file (`Minecraft-Chinese-Pinyin-v1.2.0.mcpack`) that can be opened or double-clicked to import directly into Minecraft Bedrock.
* **Official Bedrock Vanilla Strings**: Fetches and transforms official `.lang` files (`texts/zh_CN.lang`, `texts/zh_TW.lang`, `texts/en_US.lang`) directly from Mojang's bedrock-samples repository.
* **100% English Commands Preserved**: All Bedrock commands (`commands.*`, `argument.*`) remain in native English.
* **Pack Metadata**: Includes Bedrock format version 2 `manifest.json` with deterministic UUIDs and `pack_icon.png`.

### 2. Regional Phonetics & Custom In-Game Languages
* **Taiwan Zhuyin / Bopomofo (`zh_zy`)**:
  * Added dedicated selectable language: **中文 (注音) / Chinese with Zhuyin** (`zh_zy`).
  * Full character-spaced Bopomofo annotations (e.g. `鑽石劍 §7(ㄗㄨㄢ ㄕˊ ㄐㄧㄢˋ)§r`).
* **Hong Kong Cantonese Jyutping (`zh_yue`)**:
  * Added dedicated selectable language: **廣東話 (粵拼) / Cantonese with Jyutping** (`zh_yue`).
  * Offline phonetic dictionary (`data/cantonese_dict.json`) covering 2,050+ unique CJK characters with LSHK standard Jyutping (e.g. `鑽石劍 §7(zyun3 sek6 gim3)§r`).

### 3. Muted Pinyin Styling (`§7` Gray)
* Pronunciation annotations now use Minecraft's muted gray formatting code `§7(...)§r` by default.
* Chinese characters remain visually distinct and dominant while phonetic guides provide readable, unintrusive assistance.
* Configurable via CLI: `--pinyin-color <code|none>` and `--no-color`.

### 4. Learning Modes & Multi-Variant Builder
* **Tone Numbers Mode (`--pinyin-style numbers`)**: Generates Pinyin with numeric tone annotations (e.g. `钻石剑 §7(Zuan4shi2 Jian4)§r`).
* **Character Recall Mode (`--recall`)**: Inverts display order to display Pinyin first with Hanzi in secondary parentheses (e.g. `Zuànshí Jiàn §7(钻石剑)§r`), perfect for active recall study.
* **Multi-Variant Builder (`--all-variants`)**: Generates Standard, Numbers, Recall (`.zip`), and Bedrock (`.mcpack`) packages in a single run.

### 5. 1.21.4 Pale Garden & Modern Terminology Overrides
* Expanded `data/pinyin_overrides.json` to cover recent drops and polyphones:
  * `嘎枝` (Creaking) -> `Gāzhī`
  * `嘎枝之心` (Creaking Heart) -> `Gāzhī Zhīxīn`
  * `苍白之园` (Pale Garden) -> `Cāngbái Zhīyuán`
  * `眼眸花` (Eyeblossom) -> `Yǎnmóu Huā`
  * `旋风人` (Breeze) -> `Xuánfēngrén`
  * `刷怪蛋` (Spawn Egg) -> `Shuāguàidàn`
  * `粘性活塞` (Sticky Piston) -> `Niánxìng Huósāi`

---

## Release Assets

| File | Type | Description |
| :--- | :--- | :--- |
| `Minecraft-Chinese-Pinyin-v1.2.0.zip` | Java Edition Pack | Standard tone-marked pack with `zh_py`, `zh_zy`, and `zh_yue` |
| `Minecraft-Chinese-Pinyin-v1.2.0-Numbers.zip` | Java Edition Pack | Pinyin tone numbers variant (e.g. `Zuan4shi2 Jian4`) |
| `Minecraft-Chinese-Pinyin-v1.2.0-Recall.zip` | Java Edition Pack | Character recall mode variant (Pinyin first) |
| `Minecraft-Chinese-Pinyin-v1.2.0.mcpack` | Bedrock Edition Pack | Bedrock resource pack for Windows, Android, iOS, and consoles |
| `SHA256SUMS.txt` | Checksums | Cryptographic integrity verification |

---

## Installation

### Java Edition
1. Download `Minecraft-Chinese-Pinyin-v1.2.0.zip` (or Numbers / Recall).
2. Open Minecraft: Java Edition, go to **Options** -> **Resource Packs...** -> **Open Pack Folder**.
3. Drag and drop the `.zip` file into the folder.
4. Move the pack to **Selected** and click **Done**.
5. Under **Options** -> **Language...**, choose **中文 (拼音)**, **中文 (注音)**, **廣東話 (粵拼)**, or your preferred language.

### Bedrock Edition
1. Download `Minecraft-Chinese-Pinyin-v1.2.0.mcpack`.
2. Double-click or open the `.mcpack` file on your device to import into Minecraft.
3. In Minecraft: Bedrock Edition, go to **Settings** -> **Global Resources**, find the pack, and click **Activate**.
