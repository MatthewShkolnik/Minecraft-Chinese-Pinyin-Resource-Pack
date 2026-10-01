# Minecraft Chinese with Pinyin (v1.1.0)

Welcome to the v1.1.0 release of the Minecraft Chinese Pinyin Resource Pack.

This release brings major enhancements to linguistic coverage, Minecraft version compatibility, command filtering accuracy, and developer tooling.

---

## What's New in v1.1.0

### 1. Dedicated In-Game Custom Language (`zh_py`)
* Registered a new custom language entry in `pack.mcmeta`: **中文 (拼音) / Chinese with Pinyin** (`zh_py`).
* Players can now choose Chinese with Pinyin directly from Minecraft's **Options -> Language...** menu without needing to alter native English (`en_us`).
* The `en_us.json` fallback continues to be included and is now cleanly labeled as `English (US (Chinese Pinyin Fallback))` to prevent language menu confusion.

### 2. Broad Multi-Version Compatibility
* Added `supported_formats` (`min_inclusive: 32, max_inclusive: 97+`) in `pack.mcmeta`.
* Eliminates the red "Incompatible pack! Made for an older/newer version" warning across Minecraft 1.20.5 through 1.21.4+ and future releases.

### 3. Comprehensive CJK Unicode Coverage
* Expanded the tokenizer regex from standard BMP characters (`\u4e00-\u9fff`) to include CJK Extension A (`\u3400-\u4dbf`), compatibility ideographs, and supplementary plane ideographs (Extension B+).
* Corrected previously unannotated characters across Classical Chinese (`lzh`) and Hong Kong (`zh_hk`), including cobblestone (`䃮 (Tán)`), acacia (`㭜 (Yuè)`), and creaking (`䦪 (Kù)`).
* Classical Chinese (`lzh`) now utilizes monosyllabic tokenization for natural morpheme transliteration.

### 4. Custom Phonetic Overrides (`data/pinyin_overrides.json`)
* Introduced a structured domain dictionary overriding polyphonic characters (多音字) and niche Minecraft vocabulary.
* Examples:
  * `重锤` (Mace) -> `Zhòngchuí`
  * `藏宝图` (Treasure Map) -> `Cángbǎotú`
  * `附魔` (Enchantment) -> `Fùmó`
  * `潜影贝` (Shulker) -> `Qiányǐngbèi`
  * `潜行` (Sneak) -> `Qiánxíng`
  * `重生` (Respawn) -> `Chóngshēng`

### 5. 100% Command & Parser English Preservation
* Expanded command key filtering to cover `arguments.`, `parsing.`, `snbt.parser.`, `clear.failed.`, `slot.`, `predicate.unknown`, and `item_modifier.unknown`.
* Fixed 39 command feedback strings that previously remained in Chinese due to incomplete client JAR extraction. 100% of command keys are now native English.

### 6. Generator Pipeline & Developer Tooling
* **Asset Caching**: Added local disk caching under `.cache/` for Mojang manifests and assets, reducing generator execution time to ~2 seconds on cached runs.
* **CLI Arguments**: Added CLI flags for `--version`, `--output-dir`, `--no-zip`, `--no-cache`, `--cache-dir`, `--overrides`, and `--langs`.
* **Automated QA**: Added `tests/test_pack.py` with 9 automated unit tests verifying regex coverage, overrides, command filtering, and JSON integrity.
* **Continuous Integration**: Added `.github/workflows/ci.yml` running tests on push and pull requests across Python 3.9 through 3.13.

---

## Download Assets

| File | Size | Description |
| :--- | :--- | :--- |
| [`Minecraft-Chinese-Pinyin-v1.1.0.zip`](Minecraft-Chinese-Pinyin-v1.1.0.zip) | ~935 KB | Resource pack archive for Minecraft Java Edition |
| [`SHA256SUMS.txt`](SHA256SUMS.txt) | 108 B | SHA-256 integrity checksum |
| [`pack.png`](pack.png) | 10.5 KB | Pack icon (256x256) |
| [`pack.mcmeta`](pack.mcmeta) | 260 B | Resource pack metadata descriptor |

### Checksums

```text
16707e832ee7d58088931bd1aa811ee2a7b56b0d6e333d68c4d827b0c521c0b5  Minecraft-Chinese-Pinyin-v1.1.0.zip
```

---

## Installation

1. Download `Minecraft-Chinese-Pinyin-v1.1.0.zip`.
2. In Minecraft: Java Edition, navigate to **Options** -> **Resource Packs...**.
3. Click **Open Pack Folder**.
4. Drag and drop `Minecraft-Chinese-Pinyin-v1.1.0.zip` into the opened folder.
5. In Minecraft, move the pack from **Available** to **Selected** and click **Done**.
6. Under **Options** -> **Language...**, select **中文 (拼音)**, any Chinese dialect, or keep **English (US)**.
