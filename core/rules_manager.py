import os
import json
import re
import itertools

class RulesManager:
    def __init__(self, rules_dir, languages=None):
        """
        :param rules_dir: directory where language JSON files live
        :param languages: list of languages to load (e.g., ["english", "ukrainian"])
                          if None, load all found in rules_dir
        """
        self.rules_dir = rules_dir
        self._rules = {}
        self.load(languages)

    def load(self, languages=None):
        """Load only requested languages (or all if None)."""
        self._rules.clear()

        available = [f for f in os.listdir(self.rules_dir) if f.endswith(".json")]
        for filename in available:
            lang = filename.replace(".json", "")
            if languages is None or lang in languages:
                filepath = os.path.join(self.rules_dir, filename)
                with open(filepath, encoding="utf-8") as f:
                    self._rules[lang] = json.load(f)

    def get_rules(self, language):
        if language not in self._rules:
            raise ValueError(f"No rules loaded for language: {language}")
        return self._rules[language]

    def is_infinitive(self, word):
        return word[:4] == "(to)" or word[:3] == "to "

    def infinitivize(self, word, language, rule_type="infinitive_verb_options"):
        if self.is_infinitive(word):
            return [word]
        return self._apply_grammar_rules(
            word, language, rule_type
        )

    def singularize(self, word, language, rule_type="singular_noun_options"):
        return self._apply_grammar_rules(
            word, language, rule_type,
            exceptions_key="singular_noun_exceptions"
        )

    def is_simple(self, word, language, rule_type="alphabets"):
        rules = self.get_rules(language)[rule_type]
        if rules == "simple":
            return True
        for _, info in rules.items():
            if info["simple"]:
                continue
            for ch in word:
                codepoint = ord(ch)
                for start, end in info["ranges"]:
                    if int(start, 16) <= codepoint <= int(end, 16):
                        return False
        return True

    def _apply_grammar_rules(self, word, language, rule_type, exceptions_key=None):

        rules = self.get_rules(language)

        words = [w.strip() for w in word.split(",")]

        all_candidates = []
        for w in words:
            if w in rules.get(exceptions_key, {}):
                candidates = [rules[exceptions_key][w]]
            else:
                candidates = []
                for rule in rules.get(rule_type, []):
                    if len(w) < rule.get("min_length", 0):
                        continue
                    pattern = rule["search_pattern"]
                    r_pattern = rule["replace_pattern"]
                    replacement = rule["replace"]
                    if re.search(pattern, w):
                        #print(f"match: {w} with {pattern} -> {replacement}")
                        new_candidate = re.sub(r_pattern, replacement, w)
                        if new_candidate not in candidates:
                            if "prefix" in rule:
                                new_candidate = rule["prefix"] + new_candidate
                            candidates.append(new_candidate)
                    #else:
                        #print(f"NO match: {w} with {pattern} -> {replacement}")
                if not candidates:
                    candidates = [w]
            all_candidates.append(candidates)

        results = (all_candidates[0] if len(all_candidates) == 1 else
            list(",".join(combo) for combo in itertools.product(*all_candidates)))
        return results