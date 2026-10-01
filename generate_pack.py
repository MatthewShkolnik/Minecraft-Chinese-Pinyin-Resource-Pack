import os
import json
import re
import zipfile
import io
import shutil
import logging
import argparse

try:
    import requests
    import pypinyin
    import jieba
except ImportError:
    print("Please install dependencies: pip install -r requirements.txt")
    exit(1)

# Suppress jieba logging
jieba.setLogLevel(logging.WARNING)

# Comprehensive CJK regex covering BMP, Extension A, compatibility ideographs, and Extension B+
CJK_REGEX = re.compile(r'([\u3400-\u4dbf\u4e00-\u9fff\uf900-\ufaff\U00020000-\U0002ebe0]+)')

# Fallback mapping of known versions to resource pack formats
KNOWN_PACK_FORMATS = {
    "1.20.5": 32, "1.20.6": 32,
    "1.21": 34, "1.21.1": 34,
    "1.21.2": 42, "1.21.3": 42,
    "1.21.4": 46
}

def load_overrides(overrides_path):
    """Loads custom pinyin and phrase overrides for Minecraft domain terms."""
    if not os.path.exists(overrides_path):
        return
    try:
        with open(overrides_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        phrases = data.get("phrases", {})
        if phrases:
            pypinyin.load_phrases_dict(phrases)
            for phrase in phrases:
                jieba.add_word(phrase)

        raw_chars = data.get("chars", {})
        if raw_chars:
            converted_chars = {}
            for ch, pinyin_val in raw_chars.items():
                code = ord(ch) if isinstance(ch, str) else ch
                if isinstance(pinyin_val, list):
                    val_str = ','.join([x[0] if isinstance(x, list) else x for x in pinyin_val])
                else:
                    val_str = str(pinyin_val)
                converted_chars[code] = val_str
            pypinyin.load_single_dict(converted_chars)

        print(f"Loaded {len(phrases)} phrase overrides and {len(raw_chars)} character overrides from {overrides_path}")
    except Exception as e:
        print(f"Warning: Failed to load overrides from {overrides_path}: {e}")

def fetch_json(url, cache_path=None, session=None):
    """Fetches JSON from URL with optional disk caching."""
    if cache_path and os.path.exists(cache_path):
        try:
            with open(cache_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass

    s = session or requests.Session()
    resp = s.get(url)
    resp.raise_for_status()
    data = resp.json()

    if cache_path:
        os.makedirs(os.path.dirname(cache_path), exist_ok=True)
        with open(cache_path, "w", encoding="utf-8") as f:
            json.dump(data, f)

    return data

def get_version_info(target_version=None, cache_dir=None, session=None):
    """Finds target version URL from Mojang version manifest."""
    manifest_cache = os.path.join(cache_dir, "version_manifest_v2.json") if cache_dir else None
    url = "https://piston-meta.mojang.com/mc/game/version_manifest_v2.json"
    manifest = fetch_json(url, manifest_cache, session)

    version_id = target_version or manifest["latest"]["release"]
    version_url = None

    for v in manifest["versions"]:
        if v["id"] == version_id:
            version_url = v["url"]
            break

    if not version_url:
        raise ValueError(f"Could not find URL for version {version_id}")

    return version_id, version_url

def get_version_data(version_id, version_url, cache_dir=None, session=None):
    """Retrieves full version data from version_url."""
    v_cache = os.path.join(cache_dir, f"version_{version_id}.json") if cache_dir else None
    return fetch_json(version_url, v_cache, session)

def get_client_assets(v_data, cache_dir=None, session=None):
    """Extracts en_us.json and pack_format from client jar, caching result locally."""
    version_id = v_data["id"]
    cache_path = os.path.join(cache_dir, f"client_assets_{version_id}.json") if cache_dir else None

    if cache_path and os.path.exists(cache_path):
        try:
            with open(cache_path, "r", encoding="utf-8") as f:
                cached = json.load(f)
                return cached["pack_format"], cached["en_us_data"]
        except Exception:
            pass

    print(f"Downloading client jar for {version_id} to extract en_us strings and pack metadata...")
    client_url = v_data["downloads"]["client"]["url"]
    s = session or requests.Session()
    resp = s.get(client_url)
    resp.raise_for_status()

    pack_format = KNOWN_PACK_FORMATS.get(version_id)
    with zipfile.ZipFile(io.BytesIO(resp.content)) as z:
        en_us_data = json.loads(z.read("assets/minecraft/lang/en_us.json").decode("utf-8"))
        try:
            v_json = json.loads(z.read("version.json").decode("utf-8"))
            pv = v_json.get("pack_version", {})
            resolved_pf = pv.get("resource_major") or pv.get("resource")
            if resolved_pf:
                pack_format = resolved_pf
        except Exception:
            pass

    if not pack_format:
        pack_format = 34

    if cache_path:
        os.makedirs(os.path.dirname(cache_path), exist_ok=True)
        with open(cache_path, "w", encoding="utf-8") as f:
            json.dump({"pack_format": pack_format, "en_us_data": en_us_data}, f)

    return pack_format, en_us_data

def get_lang_file(asset_index_url, lang_name, cache_dir=None, session=None):
    """Downloads a Minecraft language file from Mojang asset objects."""
    index_cache = os.path.join(cache_dir, "asset_index.json") if cache_dir else None
    asset_index = fetch_json(asset_index_url, index_cache, session)

    lang_info = asset_index["objects"].get(f"minecraft/lang/{lang_name}")
    if not lang_info:
        raise ValueError(f"Could not find minecraft/lang/{lang_name} in asset index")

    lang_hash = lang_info["hash"]
    lang_url = f"https://resources.download.minecraft.net/{lang_hash[:2]}/{lang_hash}"
    lang_cache = os.path.join(cache_dir, f"lang_{lang_hash}_{lang_name}") if cache_dir else None

    return fetch_json(lang_url, lang_cache, session)

def convert_to_pinyin(text, is_classical=False):
    """Converts Chinese characters within text to tone-marked Pinyin annotations."""
    if not CJK_REGEX.search(text):
        return text

    tokens = CJK_REGEX.split(text)
    res = []

    for token in tokens:
        if not token:
            continue
        if CJK_REGEX.fullmatch(token):
            if is_classical:
                # Monosyllabic / character-by-character for Classical Chinese
                py_words = []
                for ch in token:
                    pys = pypinyin.pinyin(ch, style=pypinyin.Style.TONE)
                    py_words.append(pys[0][0].capitalize())
            else:
                words = jieba.lcut(token)
                py_words = []
                for w in words:
                    pys = pypinyin.pinyin(w, style=pypinyin.Style.TONE)
                    w_py = ''.join([py[0] for py in pys]).capitalize()
                    py_words.append(w_py)

            pinyin_str = ' '.join(py_words)
            res.append(f"{token} ({pinyin_str})")
        else:
            res.append(token)

    raw = ''.join(res)
    # Ensure clean spacing between closing parenthesis and following alphanumeric characters
    formatted = re.sub(r'\)([A-Za-z0-9])', r') \1', raw)
    return formatted

def is_command_key(key):
    """Matches keys related to command syntax, arguments, parsers, and command feedback."""
    return key.startswith((
        'command.', 'commands.',
        'argument.', 'arguments.',
        'parsing.', 'snbt.parser.',
        'clear.failed.', 'slot.',
        'predicate.unknown', 'item_modifier.unknown'
    ))

def process_and_save_lang(lang_name, lang_data, en_us_data, assets_dir):
    """Processes translations with Pinyin, preserving English for commands."""
    print(f"Applying Pinyin transformation to {lang_name}...")
    converted_data = {}
    is_classical = (lang_name == "lzh.json")

    for key, value in lang_data.items():
        if is_command_key(key):
            # Command keys use original English
            converted_data[key] = en_us_data.get(key, value)
        else:
            converted_data[key] = convert_to_pinyin(value, is_classical=is_classical)

    lang_file_path = os.path.join(assets_dir, lang_name)
    with open(lang_file_path, "w", encoding="utf-8") as f:
        json.dump(converted_data, f, ensure_ascii=False, indent=2)

    print(f"✅ {lang_name} generated with Pinyin")
    return converted_data

def build_resource_pack(args):
    """Builds the complete resource pack."""
    cache_dir = None if args.no_cache else args.cache_dir
    dist_dir = args.output_dir
    pack_dir = os.path.join(dist_dir, "Pinyin_Resource_Pack")
    assets_dir = os.path.join(pack_dir, "assets", "minecraft", "lang")
    os.makedirs(assets_dir, exist_ok=True)

    # Load custom phonetic overrides
    load_overrides(args.overrides)

    session = requests.Session()
    session.headers.update({"User-Agent": "Minecraft-Chinese-Pinyin-Pack-Generator/1.1.0"})

    version_id, version_url = get_version_info(args.version, cache_dir, session)
    v_data = get_version_data(version_id, version_url, cache_dir, session)
    asset_index_url = v_data["assetIndex"]["url"]

    pack_format, en_us_data = get_client_assets(v_data, cache_dir, session)
    print(f"✅ Version resolved: {version_id} (Pack Format: {pack_format}, English keys: {len(en_us_data)})")

    target_langs = args.langs
    target_langs = [l if l.endswith(".json") else f"{l}.json" for l in target_langs]

    zh_cn_data = None
    processed_count = 0

    for lang in target_langs:
        try:
            lang_data = get_lang_file(asset_index_url, lang, cache_dir, session)
            converted = process_and_save_lang(lang, lang_data, en_us_data, assets_dir)
            processed_count += 1
            if lang == "zh_cn.json":
                zh_cn_data = converted
        except Exception as e:
            print(f"❌ Failed to process {lang}: {e}")

    if processed_count == 0:
        raise RuntimeError("Failed to process any target language files.")

    # Generate custom zh_py language and en_us fallback
    if zh_cn_data:
        # Dedicated custom language: zh_py (selectable in Language menu)
        zh_py_path = os.path.join(assets_dir, "zh_py.json")
        zh_py_data = dict(zh_cn_data)
        zh_py_data["language.code"] = "zh_py"
        zh_py_data["language.name"] = "中文 (拼音)"
        zh_py_data["language.region"] = "Chinese with Pinyin"
        with open(zh_py_path, "w", encoding="utf-8") as f:
            json.dump(zh_py_data, f, ensure_ascii=False, indent=2)
        print("✅ zh_py.json custom language generated")

        # English US fallback (labeled clearly in menu)
        en_us_path = os.path.join(assets_dir, "en_us.json")
        en_us_data_out = dict(zh_cn_data)
        en_us_data_out["language.code"] = "en_us"
        en_us_data_out["language.name"] = "English"
        en_us_data_out["language.region"] = "US (Chinese Pinyin Fallback)"
        with open(en_us_path, "w", encoding="utf-8") as f:
            json.dump(en_us_data_out, f, ensure_ascii=False, indent=2)
        print("✅ en_us.json fallback generated")

    # Generate pack.mcmeta with multi-version compatibility and custom language
    mcmeta_path = os.path.join(pack_dir, "pack.mcmeta")
    mcmeta_data = {
        "pack": {
            "pack_format": pack_format,
            "supported_formats": {
                "min_inclusive": 32,
                "max_inclusive": max(46, pack_format)
            },
            "description": "Minecraft Chinese with Pinyin (Un-translated Commands)"
        },
        "language": {
            "zh_py": {
                "name": "中文 (拼音)",
                "region": "Chinese with Pinyin",
                "bidirectional": False
            }
        }
    }
    with open(mcmeta_path, "w", encoding="utf-8") as f:
        json.dump(mcmeta_data, f, ensure_ascii=False, indent=2)
    print(f"✅ pack.mcmeta generated with supported_formats [32-{max(46, pack_format)}] and custom language zh_py")

    # Copy pack icon
    if os.path.exists("pack.png"):
        shutil.copy("pack.png", os.path.join(pack_dir, "pack.png"))

    # Create ZIP archive
    if not args.no_zip:
        zip_path = os.path.join(dist_dir, "Pinyin_Resource_Pack.zip")
        print("Creating ZIP archive...")
        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
            for root, dirs, files in os.walk(pack_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    arcname = os.path.relpath(file_path, pack_dir)
                    zf.write(file_path, arcname)
        print(f"✅ Resource pack archive created: {zip_path}")

    print(f"🎉 Build completed successfully in {pack_dir}")

def parse_args():
    parser = argparse.ArgumentParser(
        description="Minecraft Chinese with Pinyin Resource Pack Generator"
    )
    parser.add_argument(
        "--version", "-v",
        default=None,
        help="Target Minecraft version (e.g. '1.21.1'). Defaults to latest release."
    )
    parser.add_argument(
        "--output-dir", "-o",
        default="dist",
        help="Output directory (default: 'dist')"
    )
    parser.add_argument(
        "--no-zip",
        action="store_true",
        help="Skip creating the .zip archive"
    )
    parser.add_argument(
        "--no-cache",
        action="store_true",
        help="Disable local asset caching"
    )
    parser.add_argument(
        "--cache-dir",
        default=".cache",
        help="Directory to cache manifests and asset files (default: '.cache')"
    )
    parser.add_argument(
        "--overrides",
        default="data/pinyin_overrides.json",
        help="Path to custom phonetic overrides JSON (default: 'data/pinyin_overrides.json')"
    )
    parser.add_argument(
        "--langs",
        nargs="+",
        default=["zh_cn.json", "zh_hk.json", "zh_tw.json", "lzh.json"],
        help="Language files to process"
    )
    return parser.parse_args()

if __name__ == "__main__":
    args = parse_args()
    build_resource_pack(args)
