import pytest
import pathlib
from langwich.core.rules_manager import RulesManager

app_root_dir = pathlib.Path(__file__).resolve().parent.parent
rules_dir = app_root_dir / "data/rules"
rule_mgr = RulesManager(rules_dir=rules_dir)

def test_is_simple_word_with_kana():
    word = "ねこ"  # neko, hiragana
    assert rule_mgr.is_simple(word, "japanese") is True

def test_is_simple_word_with_kanji():
    word = "猫"  # neko, kanji
    assert rule_mgr.is_simple(word, "japanese") is False

def test_is_simple_word_with_mixed():
    word = "来る"  # neko, kanji
    assert rule_mgr.is_simple(word, "japanese") is False
