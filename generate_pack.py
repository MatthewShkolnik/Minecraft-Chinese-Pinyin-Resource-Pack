import os
import json
import re
import zipfile
import io
import shutil
import logging

try:
    import requests
    import pypinyin
    import jieba
except ImportError:
    print("Please install dependencies: pip install -r requirements.txt")
    exit(1)

# Suppress jieba logging
jieba.setLogLevel(logging.WARNING)

def get_latest_version_manifest():
    url = "https://piston-meta.mojang.com/mc/game/version_manifest_v2.json"
    resp = requests.get(url)
    resp.raise_for_status()
    manifest = resp.json()
    
    latest_release = manifest["latest"]["release"]
    
    version_url = None
    for version in manifest["versions"]:
        if version["id"] == latest_release:
            version_url = version["url"]
            break
            
    if not version_url:
        raise ValueError(f"Could not find URL for version {latest_release}")
        
    return latest_release, version_url

def get_version_data(version_url):
    resp = requests.get(version_url)
    resp.raise_for_status()
    return resp.json()

def get_asset_index_info(v_data):
    asset_index_url = v_data["assetIndex"]["url"]
    pack_format = int(v_data["assetIndex"]["id"])
    return pack_format, asset_index_url

def get_en_us_lang(v_data):
    client_url = v_data["downloads"]["client"]["url"]
    resp = requests.get(client_url)
    resp.raise_for_status()
    
    with zipfile.ZipFile(io.BytesIO(resp.content)) as z:
        en_us_data = json.loads(z.read("assets/minecraft/lang/en_us.json").decode("utf-8"))
        
    return en_us_data

def get_lang_file(asset_index_url, lang_name):
    resp = requests.get(asset_index_url)
    resp.raise_for_status()
    asset_index = resp.json()
    
    lang_info = asset_index["objects"].get(f"minecraft/lang/{lang_name}")
    if not lang_info:
        raise ValueError(f"Could not find minecraft/lang/{lang_name} in asset index")
        
    lang_hash = lang_info["hash"]
    lang_url = f"https://resources.download.minecraft.net/{lang_hash[:2]}/{lang_hash}"
    
    resp = requests.get(lang_url)
    resp.raise_for_status()
    return resp.json()

def convert_to_pinyin(text):
    if not re.search(r'[\u4e00-\u9fff]', text):
        return text

    tokens = re.split(r'([\u4e00-\u9fff]+)', text)
    res = []
    
    for token in tokens:
        if not token:
            continue
        if re.match(r'^[\u4e00-\u9fff]+$', token):
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
            
    return ''.join(res)

def is_command_key(key):
    # Matches keys related to commands, command arguments, and command parsing errors
    return key.startswith(('command.', 'commands.', 'argument.', 'parser.'))

def process_and_save_lang(lang_name, lang_data, en_us_data, assets_dir):
    print(f"Applying Pinyin transformation to {lang_name}...")
    converted_data = {}
    
    for key, value in lang_data.items():
        if is_command_key(key):
            # Remove translation for commands (fallback to original English)
            converted_data[key] = en_us_data.get(key, value)
        else:
            converted_data[key] = convert_to_pinyin(value)
            
    lang_file_path = os.path.join(assets_dir, lang_name)
    with open(lang_file_path, "w", encoding="utf-8") as f:
        json.dump(converted_data, f, ensure_ascii=False, indent=2)
        
    print(f"✅ {lang_name} generated with Pinyin")
    return converted_data

def build_resource_pack():
    dist_dir = "dist"
    pack_dir = os.path.join(dist_dir, "Pinyin_Resource_Pack")
    assets_dir = os.path.join(pack_dir, "assets", "minecraft", "lang")
    
    os.makedirs(assets_dir, exist_ok=True)
    
    latest_release, version_url = get_latest_version_manifest()
    v_data = get_version_data(version_url)
    pack_format, asset_index_url = get_asset_index_info(v_data)
    print(f"✅ Latest version and asset hash resolved (Release: {latest_release}, Pack Format: {pack_format})")
    
    print("Downloading client jar to extract native English strings for commands...")
    en_us_data = get_en_us_lang(v_data)
    print("✅ English strings extracted")
    
    target_langs = ["zh_cn.json", "zh_hk.json", "zh_tw.json", "lzh.json"]
    zh_cn_data = None
    
    for lang in target_langs:
        try:
            lang_data = get_lang_file(asset_index_url, lang)
            converted = process_and_save_lang(lang, lang_data, en_us_data, assets_dir)
            if lang == "zh_cn.json":
                zh_cn_data = converted
        except Exception as e:
            print(f"Failed to process {lang}: {e}")
            
    if zh_cn_data:
        en_us_path = os.path.join(assets_dir, "en_us.json")
        with open(en_us_path, "w", encoding="utf-8") as f:
            json.dump(zh_cn_data, f, ensure_ascii=False, indent=2)
        print("✅ en_us.json fallback generated")
    
    mcmeta_path = os.path.join(pack_dir, "pack.mcmeta")
    mcmeta_data = {
        "pack": {
            "pack_format": pack_format,
            "description": "Minecraft Chinese with Pinyin (Un-translated Commands)"
        }
    }
    with open(mcmeta_path, "w", encoding="utf-8") as f:
        json.dump(mcmeta_data, f, ensure_ascii=False, indent=2)

    if os.path.exists("pack.png"):
        shutil.copy("pack.png", os.path.join(pack_dir, "pack.png"))
        
    zip_path = os.path.join(dist_dir, "Pinyin_Resource_Pack.zip")
    print("Creating ZIP archive...")
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for root, dirs, files in os.walk(pack_dir):
            for file in files:
                file_path = os.path.join(root, file)
                arcname = os.path.relpath(file_path, pack_dir)
                zf.write(file_path, arcname)
                
    print(f"✅ Resource pack directory and .zip updated (Output: {zip_path})")

if __name__ == "__main__":
    build_resource_pack()
