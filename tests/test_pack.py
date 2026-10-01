import os
import json
import re
import unittest
from generate_pack import (
    CJK_REGEX,
    is_command_key,
    convert_to_pinyin,
    load_overrides
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
        res_cobble = convert_to_pinyin("䃮", is_classical=True)
        self.assertEqual(res_cobble, "䃮 (Tán)")

        res_acacia = convert_to_pinyin("㭜木", is_classical=True)
        self.assertEqual(res_acacia, "㭜木 (Yuè Mù)")

        res_creaking = convert_to_pinyin("䦪鬼", is_classical=True)
        self.assertEqual(res_creaking, "䦪鬼 (Kù Guǐ)")

    def test_typography_spacing(self):
        """Verify boundary space is added between closing parenthesis and Latin tokens."""
        raw = "按下Enter键"
        converted = convert_to_pinyin(raw)
        self.assertIn(") Enter", converted)

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


if __name__ == "__main__":
    unittest.main()
