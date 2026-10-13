import os
import json
import re
import zipfile
import io
import shutil
import logging
import argparse
import uuid

try:
    import requests
    import pypinyin
    import jieba
except ImportError:
    print("Please install dependencies: pip install -r requirements.txt")
    exit(1)

# Suppress jieba logging
jieba.setLogLevel(logging.WARNING)

__version__ = "1.2.1"

# Comprehensive CJK regex covering BMP, Extension A, compatibility ideographs, and Extension B+
CJK_REGEX = re.compile(r'([\u3400-\u4dbf\u4e00-\u9fff\uf900-\ufaff\U00020000-\U0002ebe0]+)')

CANTONESE_DICT = {}

def load_cantonese_dict(dict_path=None):
    """Loads Cantonese Jyutping dictionary if present."""
    global CANTONESE_DICT
    if dict_path is None:
        dict_path = os.path.join(os.path.dirname(__file__), "data", "cantonese_dict.json")
    if not os.path.exists(dict_path):
        return {}
    try:
        with open(dict_path, "r", encoding="utf-8") as f:
            CANTONESE_DICT = json.load(f)
        return CANTONESE_DICT
    except Exception as e:
        print(f"Warning: Failed to load Cantonese dictionary from {dict_path}: {e}")
        return {}

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

def fetch_text(url, cache_path=None, session=None):
    """Fetches text content from URL with optional disk caching."""
    if cache_path and os.path.exists(cache_path):
        try:
            with open(cache_path, "r", encoding="utf-8") as f:
                return f.read()
        except Exception:
            pass

    s = session or requests.Session()
    resp = s.get(url)
    resp.raise_for_status()
    text = resp.text

    if cache_path:
        os.makedirs(os.path.dirname(cache_path), exist_ok=True)
        with open(cache_path, "w", encoding="utf-8") as f:
            f.write(text)

    return text

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

MINECRAFT_COLOR_NAMES = {
    "black": "§0",
    "dark_blue": "§1",
    "dark_green": "§2",
    "dark_aqua": "§3",
    "dark_red": "§4",
    "dark_purple": "§5",
    "gold": "§6",
    "orange": "§6",
    "gray": "§7",
    "grey": "§7",
    "dark_gray": "§8",
    "dark_grey": "§8",
    "blue": "§9",
    "green": "§a",
    "aqua": "§b",
    "cyan": "§b",
    "red": "§c",
    "light_purple": "§d",
    "pink": "§d",
    "yellow": "§e",
    "white": "§f",
}

def normalize_color_code(pinyin_color):
    """Normalizes a Minecraft color code or returns None if disabled."""
    if not pinyin_color:
        return None
    val = str(pinyin_color).strip().lower()
    if val in ("none", "off", "false", "no", "plain", ""):
        return None
    if val in MINECRAFT_COLOR_NAMES:
        return MINECRAFT_COLOR_NAMES[val]
    if val.startswith("§"):
        return val
    return f"§{val}"

def convert_to_pinyin(text, is_classical=False, pinyin_color="§7", pinyin_style="marks", recall=False):
    """Converts Chinese characters within text to tone-marked Pinyin, Bopomofo, or Jyutping annotations."""
    if not CJK_REGEX.search(text):
        return text

    is_bopomofo = pinyin_style in ("bopomofo", "zhuyin")
    is_jyutping = (pinyin_style == "jyutping")

    if pinyin_style == "numbers":
        style_enum = pypinyin.Style.TONE3
    elif pinyin_style in ("plain", "normal"):
        style_enum = pypinyin.Style.NORMAL
    elif is_bopomofo:
        style_enum = pypinyin.Style.BOPOMOFO
    else:
        style_enum = pypinyin.Style.TONE

    color_code = normalize_color_code(pinyin_color)
    tokens = CJK_REGEX.split(text)
    res = []

    for token in tokens:
        if not token:
            continue
        if CJK_REGEX.fullmatch(token):
            if is_jyutping:
                if not CANTONESE_DICT:
                    load_cantonese_dict()
                py_words = []
                for ch in token:
                    jy = CANTONESE_DICT.get(ch)
                    if not jy:
                        pys = pypinyin.pinyin(ch, style=pypinyin.Style.TONE3)
                        jy = pys[0][0] if pys else ch
                    py_words.append(jy)
            elif is_bopomofo:
                py_words = []
                for ch in token:
                    pys = pypinyin.pinyin(ch, style=pypinyin.Style.BOPOMOFO)
                    py_words.append(pys[0][0])
            elif is_classical:
                # Monosyllabic / character-by-character for Classical Chinese
                py_words = []
                for ch in token:
                    pys = pypinyin.pinyin(ch, style=style_enum)
                    py_words.append(pys[0][0].capitalize())
            else:
                words = jieba.lcut(token)
                py_words = []
                for w in words:
                    pys = pypinyin.pinyin(w, style=style_enum)
                    w_py = ''.join([py[0] for py in pys]).capitalize()
                    py_words.append(w_py)

            pinyin_str = ' '.join(py_words)
            if recall:
                if color_code:
                    res.append(f"{pinyin_str} {color_code}({token})§r")
                else:
                    res.append(f"{pinyin_str} ({token})")
            else:
                if color_code:
                    res.append(f"{token} {color_code}({pinyin_str})§r")
                else:
                    res.append(f"{token} ({pinyin_str})")
        else:
            res.append(token)

    raw = ''.join(res)
    # Ensure clean spacing between closing parenthesis / color reset and following alphanumeric characters
    formatted = re.sub(r'(\)(?:§[0-9a-fk-or])?)([A-Za-z0-9])', r'\1 \2', raw)
    if recall:
        # In recall mode, ensure clean spacing between preceding Latin/number token and following capitalized Pinyin token
        formatted = re.sub(r'([a-z0-9])([A-Z])', r'\1 \2', formatted)
    return formatted

def convert_to_jyutping(text, pinyin_color="§7", recall=False):
    """Converts Chinese text to Cantonese Jyutping annotations."""
    return convert_to_pinyin(text, pinyin_color=pinyin_color, pinyin_style="jyutping", recall=recall)

def convert_to_bopomofo(text, pinyin_color="§7", recall=False):
    """Converts Chinese text to Bopomofo (Zhuyin) annotations."""
    return convert_to_pinyin(text, pinyin_color=pinyin_color, pinyin_style="bopomofo", recall=recall)

def is_command_key(key):
    """Matches keys related to command syntax, arguments, parsers, and command feedback."""
    return key.startswith((
        'command.', 'commands.',
        'argument.', 'arguments.',
        'parsing.', 'snbt.parser.',
        'clear.failed.', 'slot.',
        'predicate.unknown', 'item_modifier.unknown'
    ))

def process_and_save_lang(lang_name, lang_data, en_us_data, assets_dir, pinyin_color="§7", pinyin_style="marks", recall=False):
    """Processes translations with Pinyin, preserving English for commands."""
    print(f"Applying Pinyin transformation to {lang_name}...")
    converted_data = {}
    is_classical = (lang_name == "lzh.json")

    for key, value in lang_data.items():
        if is_command_key(key):
            # Command keys use original English
            converted_data[key] = en_us_data.get(key, value)
        else:
            converted_data[key] = convert_to_pinyin(
                value,
                is_classical=is_classical,
                pinyin_color=pinyin_color,
                pinyin_style=pinyin_style,
                recall=recall
            )

    lang_file_path = os.path.join(assets_dir, lang_name)
    with open(lang_file_path, "w", encoding="utf-8") as f:
        json.dump(converted_data, f, ensure_ascii=False, indent=2)

    print(f"✅ {lang_name} generated with Pinyin")
    return converted_data

def build_pack_variant(
    dist_dir,
    pack_name,
    pack_format,
    target_langs,
    raw_langs,
    en_us_data,
    pinyin_color="§7",
    pinyin_style="marks",
    recall=False,
    zip_filename="Pinyin_Resource_Pack.zip",
    no_zip=False
):
    """Builds a specific resource pack variant."""
    pack_dir = os.path.join(dist_dir, pack_name)
    assets_dir = os.path.join(pack_dir, "assets", "minecraft", "lang")
    os.makedirs(assets_dir, exist_ok=True)

    zh_cn_data = None
    for lang in target_langs:
        lang_data = raw_langs[lang]
        converted = process_and_save_lang(
            lang,
            lang_data,
            en_us_data,
            assets_dir,
            pinyin_color=pinyin_color,
            pinyin_style=pinyin_style,
            recall=recall
        )
        if lang == "zh_cn.json":
            zh_cn_data = converted

    if zh_cn_data:
        # Dedicated custom language: zh_py (selectable in Language menu)
        zh_py_path = os.path.join(assets_dir, "zh_py.json")
        zh_py_data = dict(zh_cn_data)
        zh_py_data["language.code"] = "zh_py"
        zh_py_data["language.name"] = "中文 (拼音)"
        zh_py_data["language.region"] = "Chinese with Pinyin"
        with open(zh_py_path, "w", encoding="utf-8") as f:
            json.dump(zh_py_data, f, ensure_ascii=False, indent=2)
        print(f"✅ zh_py.json custom language generated for {pack_name}")

        # English US fallback (labeled clearly in menu)
        en_us_path = os.path.join(assets_dir, "en_us.json")
        en_us_data_out = dict(zh_cn_data)
        en_us_data_out["language.code"] = "en_us"
        en_us_data_out["language.name"] = "English"
        en_us_data_out["language.region"] = "US (Chinese Pinyin Fallback)"
        with open(en_us_path, "w", encoding="utf-8") as f:
            json.dump(en_us_data_out, f, ensure_ascii=False, indent=2)
        print(f"✅ en_us.json fallback generated for {pack_name}")

    # Generate custom zh_zy (Zhuyin/Bopomofo) from zh_tw
    if "zh_tw.json" in raw_langs:
        zh_zy_data = {}
        for k, v in raw_langs["zh_tw.json"].items():
            if is_command_key(k):
                zh_zy_data[k] = en_us_data.get(k, v)
            else:
                zh_zy_data[k] = convert_to_pinyin(
                    v,
                    pinyin_color=pinyin_color,
                    pinyin_style="bopomofo",
                    recall=recall
                )
        zh_zy_data["language.code"] = "zh_zy"
        zh_zy_data["language.name"] = "中文 (注音)"
        zh_zy_data["language.region"] = "Chinese with Zhuyin"
        zh_zy_path = os.path.join(assets_dir, "zh_zy.json")
        with open(zh_zy_path, "w", encoding="utf-8") as f:
            json.dump(zh_zy_data, f, ensure_ascii=False, indent=2)
        print(f"✅ zh_zy.json custom language generated for {pack_name}")

    # Generate custom zh_yue (Cantonese Jyutping) from zh_hk
    if "zh_hk.json" in raw_langs:
        zh_yue_data = {}
        for k, v in raw_langs["zh_hk.json"].items():
            if is_command_key(k):
                zh_yue_data[k] = en_us_data.get(k, v)
            else:
                zh_yue_data[k] = convert_to_pinyin(
                    v,
                    pinyin_color=pinyin_color,
                    pinyin_style="jyutping",
                    recall=recall
                )
        zh_yue_data["language.code"] = "zh_yue"
        zh_yue_data["language.name"] = "廣東話 (粵拼)"
        zh_yue_data["language.region"] = "Cantonese with Jyutping"
        zh_yue_path = os.path.join(assets_dir, "zh_yue.json")
        with open(zh_yue_path, "w", encoding="utf-8") as f:
            json.dump(zh_yue_data, f, ensure_ascii=False, indent=2)
        print(f"✅ zh_yue.json custom language generated for {pack_name}")

    if recall:
        desc = "Minecraft Chinese with Pinyin - Recall Mode (Un-translated Commands)"
    elif pinyin_style == "numbers":
        desc = "Minecraft Chinese with Pinyin - Tone Numbers (Un-translated Commands)"
    elif pinyin_style in ("bopomofo", "zhuyin"):
        desc = "Minecraft Chinese with Zhuyin - Bopomofo (Un-translated Commands)"
    elif pinyin_style == "jyutping":
        desc = "Minecraft Chinese with Jyutping - Cantonese (Un-translated Commands)"
    elif pinyin_style in ("plain", "normal"):
        desc = "Minecraft Chinese with Pinyin - Plain (Un-translated Commands)"
    else:
        desc = "Minecraft Chinese with Pinyin (Un-translated Commands)"

    mcmeta_path = os.path.join(pack_dir, "pack.mcmeta")
    mcmeta_data = {
        "pack": {
            "pack_format": pack_format,
            "supported_formats": {
                "min_inclusive": 32,
                "max_inclusive": max(46, pack_format)
            },
            "description": desc
        },
        "language": {
            "zh_py": {
                "name": "中文 (拼音)",
                "region": "Chinese with Pinyin",
                "bidirectional": False
            },
            "zh_zy": {
                "name": "中文 (注音)",
                "region": "Chinese with Zhuyin",
                "bidirectional": False
            },
            "zh_yue": {
                "name": "廣東話 (粵拼)",
                "region": "Cantonese with Jyutping",
                "bidirectional": False
            }
        }
    }
    with open(mcmeta_path, "w", encoding="utf-8") as f:
        json.dump(mcmeta_data, f, ensure_ascii=False, indent=2)
    print(f"✅ pack.mcmeta generated for {pack_name}")

    # Copy pack icon
    if os.path.exists("pack.png"):
        shutil.copy("pack.png", os.path.join(pack_dir, "pack.png"))

    # Create ZIP archive
    if not no_zip:
        if not zip_filename.endswith(".zip"):
            zip_filename += ".zip"
        zip_path = os.path.join(dist_dir, zip_filename)
        print(f"Creating ZIP archive ({zip_filename})...")
        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
            for root, dirs, files in os.walk(pack_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    arcname = os.path.relpath(file_path, pack_dir)
                    zf.write(file_path, arcname)
        print(f"✅ Resource pack archive created: {zip_path}")

    print(f"🎉 Build completed successfully in {pack_dir}")

BEDROCK_TEXTS_BASE_URL = "https://raw.githubusercontent.com/Mojang/bedrock-samples/main/resource_pack/texts"

def process_bedrock_lang(raw_text, en_us_dict, pinyin_color="§7", pinyin_style="marks", recall=False):
    """Processes lines of a Bedrock .lang file, transforming text and preserving English commands."""
    output_lines = []
    for line in raw_text.splitlines():
        trimmed = line.strip()
        if not trimmed or trimmed.startswith(("#", "//")):
            output_lines.append(line)
            continue
        if "=" in line:
            key, _, val = line.partition("=")
            key = key.strip()
            comment_suffix = ""
            if "\t#" in val:
                val, comment_suffix = val.split("\t#", 1)
                comment_suffix = "\t#" + comment_suffix

            if is_command_key(key):
                clean_val = en_us_dict.get(key, val)
            else:
                clean_val = convert_to_pinyin(
                    val,
                    pinyin_color=pinyin_color,
                    pinyin_style=pinyin_style,
                    recall=recall
                )
            output_lines.append(f"{key}={clean_val}{comment_suffix}")
        else:
            output_lines.append(line)
    return "\n".join(output_lines) + "\n"

def build_bedrock_pack(
    dist_dir,
    pack_name="Pinyin_Bedrock_Pack",
    pinyin_color="§7",
    pinyin_style="marks",
    recall=False,
    mcpack_filename="Pinyin_Resource_Pack.mcpack",
    cache_dir=None,
    session=None,
    no_zip=False
):
    """Builds a Minecraft Bedrock Edition resource pack (.mcpack)."""
    pack_dir = os.path.join(dist_dir, pack_name)
    texts_dir = os.path.join(pack_dir, "texts")
    os.makedirs(texts_dir, exist_ok=True)

    bedrock_cache_dir = os.path.join(cache_dir, "bedrock") if cache_dir else None

    # Fetch bedrock language files
    s = session or requests.Session()
    s.headers.update({"User-Agent": f"Minecraft-Chinese-Pinyin-Pack-Generator/{__version__}"})

    print("Fetching Bedrock language files...")
    en_us_raw = fetch_text(
        f"{BEDROCK_TEXTS_BASE_URL}/en_US.lang",
        os.path.join(bedrock_cache_dir, "en_US.lang") if bedrock_cache_dir else None,
        s
    )
    zh_cn_raw = fetch_text(
        f"{BEDROCK_TEXTS_BASE_URL}/zh_CN.lang",
        os.path.join(bedrock_cache_dir, "zh_CN.lang") if bedrock_cache_dir else None,
        s
    )
    zh_tw_raw = fetch_text(
        f"{BEDROCK_TEXTS_BASE_URL}/zh_TW.lang",
        os.path.join(bedrock_cache_dir, "zh_TW.lang") if bedrock_cache_dir else None,
        s
    )

    # Parse en_US into dict for command lookups
    en_us_dict = {}
    for line in en_us_raw.splitlines():
        if "=" in line and not line.strip().startswith(("#", "//")):
            k, _, v = line.partition("=")
            if "\t#" in v:
                v = v.split("\t#", 1)[0]
            en_us_dict[k.strip()] = v

    # Convert zh_CN.lang
    print(f"Applying Pinyin transformation to Bedrock zh_CN.lang...")
    converted_zh_cn = process_bedrock_lang(
        zh_cn_raw,
        en_us_dict,
        pinyin_color=pinyin_color,
        pinyin_style=pinyin_style,
        recall=recall
    )
    with open(os.path.join(texts_dir, "zh_CN.lang"), "w", encoding="utf-8") as f:
        f.write(converted_zh_cn)
    print("✅ Bedrock texts/zh_CN.lang generated")

    # Convert zh_TW.lang
    print(f"Applying Pinyin transformation to Bedrock zh_TW.lang...")
    converted_zh_tw = process_bedrock_lang(
        zh_tw_raw,
        en_us_dict,
        pinyin_color=pinyin_color,
        pinyin_style=pinyin_style,
        recall=recall
    )
    with open(os.path.join(texts_dir, "zh_TW.lang"), "w", encoding="utf-8") as f:
        f.write(converted_zh_tw)
    print("✅ Bedrock texts/zh_TW.lang generated")

    # en_US.lang fallback (provide converted zh_CN so English clients see Pinyin)
    with open(os.path.join(texts_dir, "en_US.lang"), "w", encoding="utf-8") as f:
        f.write(converted_zh_cn)
    print("✅ Bedrock texts/en_US.lang fallback generated")

    # texts/languages.json
    languages_json = ["zh_CN", "zh_TW", "en_US"]
    with open(os.path.join(texts_dir, "languages.json"), "w", encoding="utf-8") as f:
        json.dump(languages_json, f, indent=2)
    print("✅ Bedrock texts/languages.json generated")

    # Bedrock manifest.json
    header_uuid = str(uuid.uuid5(uuid.NAMESPACE_DNS, f"minecraft-chinese-pinyin-bedrock-header-{pinyin_style}-{recall}"))
    module_uuid = str(uuid.uuid5(uuid.NAMESPACE_DNS, f"minecraft-chinese-pinyin-bedrock-module-{pinyin_style}-{recall}"))

    if recall:
        desc = "Minecraft Chinese with Pinyin - Recall Mode (Un-translated Commands)"
    elif pinyin_style == "numbers":
        desc = "Minecraft Chinese with Pinyin - Tone Numbers (Un-translated Commands)"
    elif pinyin_style in ("bopomofo", "zhuyin"):
        desc = "Minecraft Chinese with Zhuyin - Bopomofo (Un-translated Commands)"
    elif pinyin_style == "jyutping":
        desc = "Minecraft Chinese with Jyutping - Cantonese (Un-translated Commands)"
    elif pinyin_style in ("plain", "normal"):
        desc = "Minecraft Chinese with Pinyin - Plain (Un-translated Commands)"
    else:
        desc = "Minecraft Chinese with Pinyin (Un-translated Commands)"

    ver_nums = [int(p) for p in __version__.split(".") if p.isdigit()]
    if len(ver_nums) < 3:
        ver_nums = (ver_nums + [0, 0, 0])[:3]

    manifest = {
        "format_version": 2,
        "header": {
            "name": "Minecraft Chinese with Pinyin",
            "description": desc,
            "uuid": header_uuid,
            "version": ver_nums,
            "min_engine_version": [1, 20, 0]
        },
        "modules": [
            {
                "description": desc,
                "type": "resources",
                "uuid": module_uuid,
                "version": ver_nums
            }
        ]
    }
    with open(os.path.join(pack_dir, "manifest.json"), "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)
    print(f"✅ Bedrock manifest.json generated for {pack_name}")

    # Copy pack icon as pack_icon.png
    if os.path.exists("pack.png"):
        shutil.copy("pack.png", os.path.join(pack_dir, "pack_icon.png"))
        print("✅ Bedrock pack_icon.png copied")

    # Create .mcpack archive
    if not no_zip:
        if not mcpack_filename.endswith(".mcpack"):
            mcpack_filename += ".mcpack"
        mcpack_path = os.path.join(dist_dir, mcpack_filename)
        print(f"Creating Bedrock MCPack archive ({mcpack_filename})...")
        with zipfile.ZipFile(mcpack_path, "w", zipfile.ZIP_DEFLATED) as zf:
            for root, dirs, files in os.walk(pack_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    arcname = os.path.relpath(file_path, pack_dir)
                    zf.write(file_path, arcname)
        print(f"✅ Bedrock pack archive created: {mcpack_path}")

    print(f"🎉 Bedrock build completed successfully in {pack_dir}")

def build_resource_pack(args):
    """Builds the resource pack (or all variants)."""
    cache_dir = None if args.no_cache else args.cache_dir
    dist_dir = args.output_dir

    # Load custom phonetic overrides and Cantonese dictionary
    load_overrides(args.overrides)
    load_cantonese_dict()

    session = requests.Session()
    session.headers.update({"User-Agent": f"Minecraft-Chinese-Pinyin-Pack-Generator/{__version__}"})

    version_id, version_url = get_version_info(args.version, cache_dir, session)
    v_data = get_version_data(version_id, version_url, cache_dir, session)
    asset_index_url = v_data["assetIndex"]["url"]

    pack_format, en_us_data = get_client_assets(v_data, cache_dir, session)
    print(f"✅ Version resolved: {version_id} (Pack Format: {pack_format}, English keys: {len(en_us_data)})")

    target_langs = args.langs
    target_langs = [l if l.endswith(".json") else f"{l}.json" for l in target_langs]

    raw_langs = {}
    for lang in target_langs:
        try:
            raw_langs[lang] = get_lang_file(asset_index_url, lang, cache_dir, session)
        except Exception as e:
            print(f"❌ Failed to fetch {lang}: {e}")

    if not raw_langs:
        raise RuntimeError("Failed to process any target language files.")

    valid_langs = list(raw_langs.keys())
    pinyin_color = None if args.no_color else args.pinyin_color
    base_zip = args.zip_name or "Pinyin_Resource_Pack.zip"
    if not base_zip.endswith(".zip"):
        base_zip += ".zip"

    if args.all_variants:
        stem = base_zip[:-4]
        variants = [
            ("Pinyin_Resource_Pack", "marks", False, base_zip),
            ("Pinyin_Resource_Pack_Numbers", "numbers", False, f"{stem}-Numbers.zip"),
            ("Pinyin_Resource_Pack_Recall", "marks", True, f"{stem}-Recall.zip")
        ]
        for p_name, p_style, p_recall, z_name in variants:
            print(f"\n--- Building variant: {p_name} ({z_name}) ---")
            build_pack_variant(
                dist_dir=dist_dir,
                pack_name=p_name,
                pack_format=pack_format,
                target_langs=valid_langs,
                raw_langs=raw_langs,
                en_us_data=en_us_data,
                pinyin_color=pinyin_color,
                pinyin_style=p_style,
                recall=p_recall,
                zip_filename=z_name,
                no_zip=args.no_zip
            )
    else:
        build_pack_variant(
            dist_dir=dist_dir,
            pack_name="Pinyin_Resource_Pack",
            pack_format=pack_format,
            target_langs=valid_langs,
            raw_langs=raw_langs,
            en_us_data=en_us_data,
            pinyin_color=pinyin_color,
            pinyin_style=args.pinyin_style,
            recall=args.recall,
            zip_filename=base_zip,
            no_zip=args.no_zip
        )

    if args.bedrock or args.all_variants:
        if args.zip_name and args.zip_name.endswith(".mcpack"):
            bedrock_filename = args.zip_name
        elif base_zip.endswith(".zip"):
            bedrock_filename = base_zip[:-4] + ".mcpack"
        else:
            bedrock_filename = base_zip + ".mcpack"

        print(f"\n--- Building Bedrock Edition pack ({bedrock_filename}) ---")
        build_bedrock_pack(
            dist_dir=dist_dir,
            pack_name="Pinyin_Bedrock_Pack",
            pinyin_color=pinyin_color,
            pinyin_style=args.pinyin_style,
            recall=args.recall,
            mcpack_filename=bedrock_filename,
            cache_dir=cache_dir,
            session=session,
            no_zip=args.no_zip
        )

def load_config(config_path=".config"):
    """Loads settings from a configuration file.
    Supports .config, .ini, .json, and flat key=value format.
    """
    if not config_path or not os.path.exists(config_path):
        return {}
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            content = f.read().strip()
        if not content:
            return {}
        # Support JSON format
        if content.startswith("{"):
            try:
                data = json.loads(content)
                if isinstance(data, dict):
                    return {str(k).lower().replace("-", "_"): v for k, v in data.items()}
            except Exception:
                pass
        # Support key=value / INI format
        config = {}
        for line in content.splitlines():
            line = line.strip()
            if not line or line.startswith(("#", ";", "[")):
                continue
            if "=" in line:
                k, _, v = line.partition("=")
            elif ":" in line:
                k, _, v = line.partition(":")
            else:
                continue
            k = k.strip().lower().replace("-", "_")
            v = v.strip().strip("'\"")
            if v.lower() in ("true", "yes", "on"):
                config[k] = True
            elif v.lower() in ("false", "no", "off"):
                config[k] = False
            else:
                config[k] = v
        return config
    except Exception as e:
        print(f"Warning: Failed to load config from {config_path}: {e}")
        return {}

def parse_args(args_list=None):
    parser = argparse.ArgumentParser(
        description="Minecraft Chinese with Pinyin Resource Pack Generator"
    )
    parser.add_argument(
        "--config",
        default=".config",
        help="Path to configuration file (default: '.config')"
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
        "--zip-name",
        default="Pinyin_Resource_Pack.zip",
        help="Custom name for the output ZIP archive (default: 'Pinyin_Resource_Pack.zip')"
    )
    parser.add_argument(
        "--no-zip",
        action="store_true",
        help="Skip creating the .zip archive"
    )
    parser.add_argument(
        "--pinyin-color",
        default=None,
        help="Minecraft color code for Pinyin annotations (e.g. '7', '§7', 'gold', or 'none'). Defaults to .config (or '§7')."
    )
    parser.add_argument(
        "--no-color",
        action="store_true",
        help="Disable colored Pinyin annotations (use plain unstyled text)"
    )
    parser.add_argument(
        "--pinyin-style",
        choices=["marks", "numbers", "plain", "bopomofo", "zhuyin", "jyutping"],
        default=None,
        help="Phonetic style: 'marks' (tone marks), 'numbers' (tone numbers), 'plain' (no tones), 'bopomofo'/'zhuyin' (注音符號), or 'jyutping' (粵拼). Defaults to .config (or 'marks')."
    )
    parser.add_argument(
        "--bedrock",
        action="store_true",
        help="Build Minecraft Bedrock Edition resource pack (.mcpack)"
    )
    parser.add_argument(
        "--recall",
        action="store_true",
        default=False,
        help="Recall mode: places Pinyin first with Chinese characters in secondary parentheses (e.g. 'Zuànshí Jiàn §7(钻石剑)§r')."
    )
    parser.add_argument(
        "--all-variants",
        action="store_true",
        help="Build all variants (Standard, Numbers, Recall, and Bedrock) in a single run."
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
    parsed = parser.parse_args(args_list)

    # Load settings from .config file if present
    cfg = load_config(parsed.config) if parsed.config else {}

    # Resolve pinyin_color with precedence:
    # 1. CLI --no-color flag
    # 2. CLI --pinyin-color option
    # 3. .config no_color option
    # 4. .config pinyin_color / color option
    # 5. Default "§7"
    if parsed.no_color:
        parsed.pinyin_color = None
    elif parsed.pinyin_color is not None:
        parsed.pinyin_color = normalize_color_code(parsed.pinyin_color)
    elif cfg.get("no_color"):
        parsed.pinyin_color = None
    elif "pinyin_color" in cfg or "color" in cfg:
        cfg_val = cfg.get("pinyin_color") if "pinyin_color" in cfg else cfg.get("color")
        parsed.pinyin_color = normalize_color_code(cfg_val)
    else:
        parsed.pinyin_color = "§7"

    # Resolve pinyin_style (CLI overrides config, fallback "marks")
    if parsed.pinyin_style is None:
        parsed.pinyin_style = cfg.get("pinyin_style", "marks")

    # Resolve recall mode (CLI overrides config)
    if not parsed.recall and cfg.get("recall"):
        parsed.recall = bool(cfg.get("recall"))

    return parsed

if __name__ == "__main__":
    args = parse_args()
    build_resource_pack(args)
