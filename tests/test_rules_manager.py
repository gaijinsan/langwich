import pytest
import pathlib
from langwich.core.rules_manager import RulesManager
from langwich.tests.utils import unordered_lists_equal

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


#########################################
# Test cases for infinitivize (English) #
#########################################
def test_infinitivize_with_infinitive():
    verb = "(to) eat"
    assert rule_mgr.infinitivize(verb, "english") == [verb]

def test_infinitivize_with_infinitive_no_parens():
    verb = "to eat"
    assert rule_mgr.infinitivize(verb, "english") == [verb]

# if test name changed, update english.json test_name field too
def test_infinitivize_with_simple_past():
    verb = "jumped"
    infinitives = rule_mgr.infinitivize(verb, "english")
    assert unordered_lists_equal(infinitives, ["(to) jump", "(to) jumpe"])

# if test name changed, update english.json test_name field too
def test_infinitivize_with_simple_past_minlength():
    verb = "duped"
    infinitives = rule_mgr.infinitivize(verb, "english")
    assert unordered_lists_equal(infinitives, ["(to) dupe", "(to) dup"])

# if test name changed, update english.json test_name field too
def test_infinitivize_with_simple_past_minlength_too_short():
    word = "seed"
    infinitives = rule_mgr.infinitivize(word, "english")
    assert unordered_lists_equal(infinitives, ["seed"])

# if test name changed, update english.json test_name field too
def test_infinitivize_with_simple_past_y():
    verb = "copied"
    assert rule_mgr.infinitivize(verb, "english") == ["(to) copy"]

# if test name changed, update english.json test_name field too
def test_infinitivize_with_simple_past_y_minlength():
    verb = "tried"
    assert rule_mgr.infinitivize(verb, "english") == ["(to) try"]

# if test name changed, update english.json test_name field too
def test_infinitivize_with_simple_past_y_minlength_too_short():
    verb = "lied"
    assert rule_mgr.infinitivize(verb, "english") == ["lied"]

# if test name changed, update english.json test_name field too
def test_infinitivize_with_present_participle():
    verb = "printing"
    infinitives = rule_mgr.infinitivize(verb, "english")
    assert unordered_lists_equal(infinitives, ["(to) print", "(to) printe"])

# if test name changed, update english.json test_name field too
def test_infinitivize_with_present_participle_minlength():
    verb = "laying"
    infinitives = rule_mgr.infinitivize(verb, "english")
    assert unordered_lists_equal(infinitives, ["(to) lay", "(to) laye"])

# if test name changed, update english.json test_name field too
def test_infinitivize_with_present_participle_minlength_too_short():
    verb = "ring"
    infinitives = rule_mgr.infinitivize(verb, "english")
    assert unordered_lists_equal(infinitives, ["ring"])

# if test name changed, update english.json test_name field too
def test_infinitivize_with_present_tense():
    verb = "brings"
    assert rule_mgr.infinitivize(verb, "english") == ["(to) bring"]

# if test name changed, update english.json test_name field too
def test_infinitivize_with_present_tense_minlength():
    verb = "runs"
    assert rule_mgr.infinitivize(verb, "english") == ["(to) run"]

# if test name changed, update english.json test_name field too
def test_infinitivize_with_present_tense_minlength_too_short():
    word = "its"
    assert rule_mgr.infinitivize(word, "english") == ["its"]

# if test name changed, update english.json test_name field too
def test_infinitivize_with_present_tense_es():
    verb = "watches"
    infinitives = rule_mgr.infinitivize(verb, "english")
    assert unordered_lists_equal(infinitives, ["(to) watch", "(to) watche"])

# if test name changed, update english.json test_name field too
def test_infinitivize_with_present_tense_es_minlength():
    verb = "washes"
    infinitives = rule_mgr.infinitivize(verb, "english")
    assert unordered_lists_equal(infinitives, ["(to) wash", "(to) washe"])

# if test name changed, update english.json test_name field too
def test_infinitivize_with_present_tense_es_minlength_2():
    word = "aches"
    infinitives = rule_mgr.infinitivize(word, "english")
    assert unordered_lists_equal(infinitives, ["(to) ache"])

# if test name changed, update english.json test_name field too
def test_infinitivize_with_present_tense_es_minlength_too_short():
    word = "bees"
    assert rule_mgr.infinitivize(word, "english") == ["bees"]