import os
import json
import re
import unittest
from generate_pack import (
    CJK_REGEX,
    is_command_key,
    convert_to_pinyin,
    convert_to_jyutping,
    convert_to_bopomofo,
    process_bedrock_lang,
    load_overrides,
    load_cantonese_dict,
    load_config,
    parse_args,
    normalize_color_code,
    __version__
)

class TestPinyinGenerator(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        overrides_path = os.path.join(os.path.dirname(__file__), "..", "data", "pinyin_overrides.json")
        overrides_path = os.path.abspath(overrides_path)
        load_overrides(overrides_path)

    def test_cjk_regex_coverage(self):
        """Verify CJK regex matches BMP, Extension A, compatibility, and supplementary plane."""
        # BMP
        self.assertTrue(CJK_REGEX.search("钻石剑"))
        # Extension A
        self.assertTrue(CJK_REGEX.search("䃮")) # Cobblestone
        self.assertTrue(CJK_REGEX.search("㭜")) # Acacia
        self.assertTrue(CJK_REGEX.search("䦪")) # Creaking
        # Supplementary plane (Extension B+)
        self.assertTrue(CJK_REGEX.search("𥹉"))

    def test_polyphone_overrides(self):
        """Verify Minecraft domain polyphone overrides are applied accurately."""
        # 重锤 should be Zhòngchuí (heavy hammer), not Chóngchuí
        res_mace = convert_to_pinyin("重锤")
        self.assertIn("Zhòng", res_mace)

        # 藏宝图 should be Cángbǎotú
        res_map = convert_to_pinyin("藏宝图")
        self.assertIn("Cáng", res_map)

        # 附魔 should be Fùmó
        res_enchant = convert_to_pinyin("附魔")
        self.assertIn("Fùmó", res_enchant)

    def test_extension_a_pinyin(self):
        """Verify CJK Extension A characters receive Pinyin annotations."""
        # Unstyled (plain)
        res_cobble = convert_to_pinyin("䃮", is_classical=True, pinyin_color=None)
        self.assertEqual(res_cobble, "䃮 (Tán)")

        res_acacia = convert_to_pinyin("㭜木", is_classical=True, pinyin_color=None)
        self.assertEqual(res_acacia, "㭜木 (Yuè Mù)")

        res_creaking = convert_to_pinyin("䦪鬼", is_classical=True, pinyin_color=None)
        self.assertEqual(res_creaking, "䦪鬼 (Kù Guǐ)")

        # Styled with default §7
        res_cobble_styled = convert_to_pinyin("䃮", is_classical=True)
        self.assertEqual(res_cobble_styled, "䃮 §7(Tán)§r")

    def test_typography_spacing(self):
        """Verify boundary space is added between closing parenthesis and Latin tokens."""
        raw = "按下Enter键"
        converted_plain = convert_to_pinyin(raw, pinyin_color=None)
        self.assertIn(") Enter", converted_plain)

        converted_styled = convert_to_pinyin(raw, pinyin_color="§7")
        self.assertIn(")§r Enter", converted_styled)

    def test_pinyin_color_styling(self):
        """Verify Pinyin color codes and reset codes are formatted correctly."""
        # Default is §7
        res_default = convert_to_pinyin("钻石剑")
        self.assertEqual(res_default, "钻石剑 §7(Zuànshí Jiàn)§r")

        # Custom color code '7' or '§7'
        res_code = convert_to_pinyin("钻石剑", pinyin_color="7")
        self.assertEqual(res_code, "钻石剑 §7(Zuànshí Jiàn)§r")

        # Another color e.g. gold §6
        res_gold = convert_to_pinyin("钻石剑", pinyin_color="6")
        self.assertEqual(res_gold, "钻石剑 §6(Zuànshí Jiàn)§r")

        # Named colors
        res_named_gold = convert_to_pinyin("钻石剑", pinyin_color="gold")
        self.assertEqual(res_named_gold, "钻石剑 §6(Zuànshí Jiàn)§r")

        res_named_yellow = convert_to_pinyin("钻石剑", pinyin_color="yellow")
        self.assertEqual(res_named_yellow, "钻石剑 §e(Zuànshí Jiàn)§r")

        res_named_gray = convert_to_pinyin("钻石剑", pinyin_color="gray")
        self.assertEqual(res_named_gray, "钻石剑 §7(Zuànshí Jiàn)§r")

        # Disabled color / plain
        res_plain = convert_to_pinyin("钻石剑", pinyin_color=None)
        self.assertEqual(res_plain, "钻石剑 (Zuànshí Jiàn)")

        res_none = convert_to_pinyin("钻石剑", pinyin_color="none")
        self.assertEqual(res_none, "钻石剑 (Zuànshí Jiàn)")

    def test_config_file_color_loading(self):
        """Verify color configuration can be read from a .config file in both INI/key-value and JSON formats."""
        import tempfile

        # 1. Test key=value format
        with tempfile.NamedTemporaryFile("w", delete=False, suffix=".config") as f:
            f.write("# Minecraft config\npinyin_color = §6\n")
            tmp_cfg = f.name
        try:
            parsed = parse_args(["--config", tmp_cfg])
            self.assertEqual(parsed.pinyin_color, "§6")
        finally:
            os.remove(tmp_cfg)

        # 2. Test named color in config
        with tempfile.NamedTemporaryFile("w", delete=False, suffix=".config") as f:
            f.write("color = gold\n")
            tmp_cfg = f.name
        try:
            parsed = parse_args(["--config", tmp_cfg])
            self.assertEqual(parsed.pinyin_color, "§6")
        finally:
            os.remove(tmp_cfg)

        # 3. Test JSON format config
        with tempfile.NamedTemporaryFile("w", delete=False, suffix=".config") as f:
            f.write('{"pinyin_color": "aqua"}\n')
            tmp_cfg = f.name
        try:
            parsed = parse_args(["--config", tmp_cfg])
            self.assertEqual(parsed.pinyin_color, "§b")
        finally:
            os.remove(tmp_cfg)

        # 4. Test no_color in config
        with tempfile.NamedTemporaryFile("w", delete=False, suffix=".config") as f:
            f.write("no_color = true\n")
            tmp_cfg = f.name
        try:
            parsed = parse_args(["--config", tmp_cfg])
            self.assertIsNone(parsed.pinyin_color)
        finally:
            os.remove(tmp_cfg)

        # 5. Test CLI override over config
        with tempfile.NamedTemporaryFile("w", delete=False, suffix=".config") as f:
            f.write("pinyin_color = §6\n")
            tmp_cfg = f.name
        try:
            # CLI --pinyin-color overrides config
            parsed = parse_args(["--config", tmp_cfg, "--pinyin-color", "§e"])
            self.assertEqual(parsed.pinyin_color, "§e")

            # CLI --no-color overrides config
            parsed_none = parse_args(["--config", tmp_cfg, "--no-color"])
            self.assertIsNone(parsed_none.pinyin_color)
        finally:
            os.remove(tmp_cfg)

    def test_pale_garden_and_121_overrides(self):
        """Verify 1.21.4 Pale Garden and mob/block phonetic overrides."""
        # Creaking (嘎枝)
        res_creaking = convert_to_pinyin("嘎枝")
        self.assertIn("Gāzhī", res_creaking)

        # Creaking Heart (嘎枝之心)
        res_heart = convert_to_pinyin("嘎枝之心")
        self.assertIn("Gāzhī Zhīxīn", res_heart)

        # Spawn Egg (刷怪蛋 -> Shuāguàidàn)
        res_egg = convert_to_pinyin("苦力怕刷怪蛋")
        self.assertIn("Shuāguàidàn", res_egg)

        # Breeze (旋风人 -> Xuánfēngrén)
        res_breeze = convert_to_pinyin("旋风人")
        self.assertIn("Xuánfēngrén", res_breeze)

        # Pale Garden (苍白之园)
        res_garden = convert_to_pinyin("苍白之园")
        self.assertIn("Cāngbái Zhīyuán", res_garden)

        # Eyeblossom (眼眸花)
        res_flower = convert_to_pinyin("眼眸花")
        self.assertIn("Yǎnmóu Huā", res_flower)

        # Sticky Piston (粘性活塞 should be Nián, not Zhān)
        res_sticky = convert_to_pinyin("粘性活塞")
        self.assertIn("Niánxìng", res_sticky)

    def test_tone_numbers_style(self):
        """Verify Pinyin tone numbers style (TONE3 format)."""
        res_num = convert_to_pinyin("钻石剑", pinyin_style="numbers")
        self.assertEqual(res_num, "钻石剑 §7(Zuan4shi2 Jian4)§r")

        res_mace_num = convert_to_pinyin("重锤", pinyin_style="numbers")
        self.assertEqual(res_mace_num, "重锤 §7(Zhong4chui2)§r")

        res_classical_num = convert_to_pinyin("䃮", is_classical=True, pinyin_style="numbers")
        self.assertEqual(res_classical_num, "䃮 §7(Tan2)§r")

    def test_recall_mode(self):
        """Verify recall mode displays Pinyin first with Hanzi in secondary parentheses."""
        # Styled recall
        res_recall = convert_to_pinyin("钻石剑", recall=True)
        self.assertEqual(res_recall, "Zuànshí Jiàn §7(钻石剑)§r")

        # Unstyled recall
        res_plain_recall = convert_to_pinyin("钻石剑", recall=True, pinyin_color=None)
        self.assertEqual(res_plain_recall, "Zuànshí Jiàn (钻石剑)")

        # Recall with tone numbers
        res_num_recall = convert_to_pinyin("钻石剑", recall=True, pinyin_style="numbers")
        self.assertEqual(res_num_recall, "Zuan4shi2 Jian4 §7(钻石剑)§r")

    def test_recall_typography_spacing(self):
        """Verify recall mode correctly adds boundary spacing between Latin and Pinyin tokens."""
        raw = "按下Enter键"
        res = convert_to_pinyin(raw, recall=True)
        self.assertEqual(res, "Ànxià §7(按下)§r Enter Jiàn §7(键)§r")

    def test_command_key_matching(self):
        """Verify all command, argument, parsing, and parser namespaces match."""
        # Commands
        self.assertTrue(is_command_key("command.compute.result.named.exact"))
        self.assertTrue(is_command_key("commands.gamerule.set"))
        self.assertTrue(is_command_key("commands.fillbiome.no_changes"))
        # Arguments
        self.assertTrue(is_command_key("argument.entity.selector.allPlayers"))
        self.assertTrue(is_command_key("arguments.block.tag.unknown"))
        self.assertTrue(is_command_key("arguments.item.component.malformed"))
        # Parsing
        self.assertTrue(is_command_key("parsing.bool.expected"))
        self.assertTrue(is_command_key("parsing.quote.expected.start"))
        # SNBT parser
        self.assertTrue(is_command_key("snbt.parser.empty_key"))
        self.assertTrue(is_command_key("snbt.parser.expected_decimal_numeral"))
        # Command feedback / errors
        self.assertTrue(is_command_key("clear.failed.multiple"))
        self.assertTrue(is_command_key("slot.unknown"))
        self.assertTrue(is_command_key("predicate.unknown"))
        self.assertTrue(is_command_key("item_modifier.unknown"))

        # Non-command keys should NOT match
        self.assertFalse(is_command_key("item.minecraft.diamond_sword"))
        self.assertFalse(is_command_key("block.minecraft.stone"))
        self.assertFalse(is_command_key("entity.minecraft.creeper"))
        self.assertFalse(is_command_key("gui.done"))

    def test_bopomofo_style(self):
        """Verify Bopomofo (Zhuyin) tone annotation."""
        # Default §7 styling
        res = convert_to_pinyin("鑽石劍", pinyin_style="bopomofo")
        self.assertEqual(res, "鑽石劍 §7(ㄗㄨㄢ ㄕˊ ㄐㄧㄢˋ)§r")

        # Via convert_to_bopomofo helper
        res_helper = convert_to_bopomofo("鑽石劍")
        self.assertEqual(res_helper, "鑽石劍 §7(ㄗㄨㄢ ㄕˊ ㄐㄧㄢˋ)§r")

        # Unstyled
        res_plain = convert_to_pinyin("鑽石劍", pinyin_style="bopomofo", pinyin_color=None)
        self.assertEqual(res_plain, "鑽石劍 (ㄗㄨㄢ ㄕˊ ㄐㄧㄢˋ)")

        # Recall mode
        res_recall = convert_to_pinyin("鑽石劍", pinyin_style="bopomofo", recall=True)
        self.assertEqual(res_recall, "ㄗㄨㄢ ㄕˊ ㄐㄧㄢˋ §7(鑽石劍)§r")

    def test_jyutping_style(self):
        """Verify Cantonese Jyutping phonetic annotation."""
        # Default §7 styling
        res = convert_to_pinyin("鑽石劍", pinyin_style="jyutping")
        self.assertEqual(res, "鑽石劍 §7(zyun3 sek6 gim3)§r")

        # Via convert_to_jyutping helper
        res_helper = convert_to_jyutping("鑽石劍")
        self.assertEqual(res_helper, "鑽石劍 §7(zyun3 sek6 gim3)§r")

        # Unstyled
        res_plain = convert_to_pinyin("鑽石劍", pinyin_style="jyutping", pinyin_color=None)
        self.assertEqual(res_plain, "鑽石劍 (zyun3 sek6 gim3)")

        # Recall mode
        res_recall = convert_to_pinyin("鑽石劍", pinyin_style="jyutping", recall=True)
        self.assertEqual(res_recall, "zyun3 sek6 gim3 §7(鑽石劍)§r")

    def test_bedrock_lang_processing(self):
        """Verify processing of Bedrock key=value .lang files and English command preservation."""
        sample_bedrock = (
            "## Sample comments\n"
            "item.diamond_sword.name=钻石剑\n"
            "commands.ability.description=设置一名玩家的能力。\n"
            "accessibility.chat.howtoopen=按 %s 打开聊天\n"
        )
        en_us_dict = {
            "commands.ability.description": "Sets a player's ability."
        }
        processed = process_bedrock_lang(sample_bedrock, en_us_dict)
        self.assertIn("## Sample comments", processed)
        self.assertIn("item.diamond_sword.name=钻石剑 §7(Zuànshí Jiàn)§r", processed)
        self.assertIn("commands.ability.description=Sets a player's ability.", processed)
        self.assertIn("accessibility.chat.howtoopen=按 §7(Àn)§r %s 打开聊天 §7(Dǎkāi Liáotiān)§r", processed)


class TestBuiltAssets(unittest.TestCase):
    """Validates the generated assets if dist/Pinyin_Resource_Pack exists."""

    @classmethod
    def setUpClass(cls):
        cls.dist_dir = os.path.join(os.path.dirname(__file__), "..", "dist", "Pinyin_Resource_Pack")
        cls.dist_dir = os.path.abspath(cls.dist_dir)
        cls.assets_exist = os.path.isdir(cls.dist_dir)

    def test_pack_mcmeta(self):
        if not self.assets_exist:
            self.skipTest("dist assets not built yet")
        mcmeta_path = os.path.join(self.dist_dir, "pack.mcmeta")
        self.assertTrue(os.path.exists(mcmeta_path))
        with open(mcmeta_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        self.assertIn("pack", data)
        self.assertIn("pack_format", data["pack"])
        self.assertIn("supported_formats", data["pack"])
        self.assertIn("language", data)
        self.assertIn("zh_py", data["language"])
        self.assertEqual(data["language"]["zh_py"]["name"], "中文 (拼音)")
        self.assertIn("zh_zy", data["language"])
        self.assertEqual(data["language"]["zh_zy"]["name"], "中文 (注音)")
        self.assertIn("zh_yue", data["language"])
        self.assertEqual(data["language"]["zh_yue"]["name"], "廣東話 (粵拼)")

    def test_command_keys_are_english_in_zh_cn(self):
        if not self.assets_exist:
            self.skipTest("dist assets not built yet")
        zh_cn_path = os.path.join(self.dist_dir, "assets", "minecraft", "lang", "zh_cn.json")
        self.assertTrue(os.path.exists(zh_cn_path))
        with open(zh_cn_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        chinese_char_re = re.compile(r'[\u3400-\u4dbf\u4e00-\u9fff]')
        leaked_keys = []
        for key, value in data.items():
            if is_command_key(key):
                if chinese_char_re.search(value):
                    leaked_keys.append((key, value))

        self.assertEqual(
            len(leaked_keys), 0,
            f"Found {len(leaked_keys)} command keys still containing Chinese: {leaked_keys[:5]}"
        )

    def test_custom_and_fallback_languages(self):
        if not self.assets_exist:
            self.skipTest("dist assets not built yet")
        lang_dir = os.path.join(self.dist_dir, "assets", "minecraft", "lang")

        # zh_py.json
        zh_py_path = os.path.join(lang_dir, "zh_py.json")
        self.assertTrue(os.path.exists(zh_py_path))
        with open(zh_py_path, "r", encoding="utf-8") as f:
            zh_py = json.load(f)
        self.assertEqual(zh_py.get("language.code"), "zh_py")
        self.assertEqual(zh_py.get("language.name"), "中文 (拼音)")

        # zh_zy.json (Bopomofo)
        zh_zy_path = os.path.join(lang_dir, "zh_zy.json")
        self.assertTrue(os.path.exists(zh_zy_path))
        with open(zh_zy_path, "r", encoding="utf-8") as f:
            zh_zy = json.load(f)
        self.assertEqual(zh_zy.get("language.code"), "zh_zy")
        self.assertEqual(zh_zy.get("language.name"), "中文 (注音)")
        sword_zy = zh_zy.get("item.minecraft.diamond_sword")
        if sword_zy:
            self.assertIn("ㄗㄨㄢ", sword_zy)

        # zh_yue.json (Cantonese Jyutping)
        zh_yue_path = os.path.join(lang_dir, "zh_yue.json")
        self.assertTrue(os.path.exists(zh_yue_path))
        with open(zh_yue_path, "r", encoding="utf-8") as f:
            zh_yue = json.load(f)
        self.assertEqual(zh_yue.get("language.code"), "zh_yue")
        self.assertEqual(zh_yue.get("language.name"), "廣東話 (粵拼)")
        sword_yue = zh_yue.get("item.minecraft.diamond_sword")
        if sword_yue:
            self.assertIn("zyun3", sword_yue)

        # en_us.json fallback
        en_us_path = os.path.join(lang_dir, "en_us.json")
        self.assertTrue(os.path.exists(en_us_path))
        with open(en_us_path, "r", encoding="utf-8") as f:
            en_us = json.load(f)
        self.assertEqual(en_us.get("language.name"), "English")
        self.assertIn("Chinese Pinyin Fallback", en_us.get("language.region", ""))

    def test_format_specifiers_integrity(self):
        if not self.assets_exist:
            self.skipTest("dist assets not built yet")
        zh_cn_path = os.path.join(self.dist_dir, "assets", "minecraft", "lang", "zh_cn.json")
        with open(zh_cn_path, "r", encoding="utf-8") as f:
            zh_cn = json.load(f)

        # Check for malformed format specifiers like % s or broken %
        for key, value in zh_cn.items():
            # If percentage exists, it shouldn't have broken spaces in % s, % d
            self.assertFalse(
                re.search(r'%\s+[sdf]', value),
                f"Malformed format specifier in {key}: {value}"
            )

    def test_pinyin_styling_in_built_assets(self):
        if not self.assets_exist:
            self.skipTest("dist assets not built yet")
        zh_cn_path = os.path.join(self.dist_dir, "assets", "minecraft", "lang", "zh_cn.json")
        with open(zh_cn_path, "r", encoding="utf-8") as f:
            zh_cn = json.load(f)

        diamond_sword = zh_cn.get("item.minecraft.diamond_sword")
        self.assertIsNotNone(diamond_sword)
        self.assertIn("§7(", diamond_sword)
        self.assertTrue(diamond_sword.endswith("§r"))

    def test_bedrock_built_assets(self):
        bedrock_dir = os.path.join(os.path.dirname(__file__), "..", "dist", "Pinyin_Bedrock_Pack")
        if not os.path.isdir(bedrock_dir):
            self.skipTest("dist/Pinyin_Bedrock_Pack not built yet")

        manifest_path = os.path.join(bedrock_dir, "manifest.json")
        self.assertTrue(os.path.exists(manifest_path))
        with open(manifest_path, "r", encoding="utf-8") as f:
            manifest = json.load(f)

        self.assertEqual(manifest.get("format_version"), 2)
        self.assertIn("header", manifest)
        expected_version = [int(p) for p in __version__.split(".") if p.isdigit()]
        self.assertEqual(manifest["header"].get("version"), expected_version)
        self.assertEqual(manifest["header"].get("min_engine_version"), [1, 20, 0])
        self.assertIn("uuid", manifest["header"])
        self.assertIn("modules", manifest)

        # pack_icon.png
        self.assertTrue(os.path.exists(os.path.join(bedrock_dir, "pack_icon.png")))

        # texts/languages.json
        lang_json_path = os.path.join(bedrock_dir, "texts", "languages.json")
        self.assertTrue(os.path.exists(lang_json_path))
        with open(lang_json_path, "r", encoding="utf-8") as f:
            languages = json.load(f)
        self.assertIn("zh_CN", languages)
        self.assertIn("zh_TW", languages)
        self.assertIn("en_US", languages)

        # texts/zh_CN.lang
        zh_cn_path = os.path.join(bedrock_dir, "texts", "zh_CN.lang")
        self.assertTrue(os.path.exists(zh_cn_path))
        with open(zh_cn_path, "r", encoding="utf-8") as f:
            zh_cn_content = f.read()

        # Commands should be English
        self.assertIn("commands.ability.description=Sets a player's ability.", zh_cn_content)
        # Normal items have pinyin
        self.assertIn("item.diamond_sword.name=钻石剑 §7(Zuànshí Jiàn)§r", zh_cn_content)


if __name__ == "__main__":
    unittest.main()
