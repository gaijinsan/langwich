import sys
import pathlib
import json
import hashlib
from datetime import datetime
import os
import shutil
import random
import re
from math import floor
from colorama import Fore, Back, Style
from langwich.core.rules_manager import RulesManager
from langwich import IS_DEV_MODE

app_root_dir = pathlib.Path(__file__).resolve().parent

data_dir = app_root_dir / "data"
metadata_path = app_root_dir / "metadata.json"
text_sents_dir = app_root_dir / "text_sentences"
text_words_dir = app_root_dir / "text_words"
texts_dir = app_root_dir / "texts"
words_dir = app_root_dir / "words"
rules_dir = app_root_dir / "data/rules"
langs_dir = app_root_dir / "langs"
backups_dir = app_root_dir / "backups"

# [x] word: has a skip flag
# word: has an index within a sentence (sent_index)
# word: has an index within the text_words file (list_index)
# word: has a source (ie. hash, later maybe a text_index)
# word: has an original representation within the text
# word: has a language
# word: has a base version (eg. houses => house, jumping => (to) jump) which may be same as word
#             this might be a list: check existing data for csv values and why i added it
# word: has a type, or part of speech (related to context of sentence) (eg. book => noun, (to) book => verb)
# word: has a translation (into user's native language)
# word: has a base translation (into user's native language)
# word: has stress markers (maybe a list for multiple pronunciations)
# word: has a gender which is enabled if language has gender (can be n/a for certain word types)
# word: has a case which is enabled if language has case-related endings (can be n/a for certain word types)
# word: has a list of alternate representations (think: kanji, furigana, romaji)
#             this dict and its structure are determined by the language
#             0 => romaji, 1 => furigana, 2 => kanji csv
# word: has a special alternate representation type (eg. romaji (for Mom) or furigana (for me))
# word: has a complete flag, if all lang-related properties are filled in
# wordlist
# word_delims
# word_next pointer
# word_prev pointer
# unnormalized word (eg. ["Canada"])
# normalized word (eg. Canada)
# prefix_delims (eg. [")
# suffix_delims (eg. "])
class Word:
    def __init__(self, data):
        self.skip = data.get("skip", False)
        # word comes from a text_sentences list, so it has an index

class Language:
    def __init__(self, language):
        self.language = language
        #with open("languages.json", "r") as f:
            #languages = json.load(f)
        self.editable_word_keys = ["type", "translation", "base", "base_translation"]
        if alt_representation_required:
            self.editable_word_keys.append("alt_representation")
            self.editable_word_keys.append("special_alt_rep")
        self.editable_word_keys.append("stress_marks")
        #more_word_keys = ["tags", "note"]
        #readonly_word_keys = ["internal_type", "index", "sentence"]

    @property
    def editable_word_keys(self):
        return self._editable_word_keys

    @editable_word_keys.setter
    def editable_word_keys(self, new_value):
        self._editable_word_keys = new_value

class Text:
    def __init__(self, hash=None):
        if hash:
            self.hash = hash
            metadata = get_metadata(self.hash)
            prev_metadata = get_metadata(self.hash)
            created_on = metadata.get("created_on")
        else:
            created_on = datetime.now()
            self.hash = generate_hash(created_on)
            metadata = {}
            prev_metadata = {}
        self.filename = f"{self.hash}.txt"
        self.hash_list = []
        self.hash_list.append(self.hash)
        self.next_hash = None
        self.prev_hash = None
        self.type = metadata.get("type", None)
        self.title = metadata.get("title", "")
        self.url = metadata.get("url", "")
        self.language = metadata.get("language", current_language)
        self.lang_code = metadata.get("lang_code", "")
        self.created_on = created_on
        self.num_words = metadata.get("num_words", -1)
        self.num_uniq_words = metadata.get("num_uniq_words", -1)
        self.study_count = metadata.get("study_count", -1)
        self.last_study_date = metadata.get("last_study_date", None)
        self.fulltext = metadata.get("fulltext", False)
        while True:
            prev_hash = prev_metadata.get("prev_hash", None)
            if prev_hash:
                if not self.prev_hash:
                    self.prev_hash = prev_hash
                self.hash_list.insert(0, prev_hash)
                prev_metadata = get_metadata(prev_hash)
            else:
                break
        while True:
            next_hash = metadata.get("next_hash", None)
            if next_hash:
                if not self.next_hash:
                    self.next_hash = next_hash
                self.hash_list.append(next_hash)
                metadata = get_metadata(next_hash)
            else:
                break

    #@property
    def type(self):
        return self._type
    #@property
    def title(self):
        return self._title
    #@property
    def url(self):
        return self._url
    #@property
    def language(self):
        return self._language
    #@property
    def lang_code(self):
        return self._lang_code
    #@property
    def created_on(self):
        return self._created_on
    #@property
    def num_words(self):
        return self._num_words
    #@property
    def num_uniq_words(self):
        return self._num_uniq_words
    @property
    def study_count(self):
        return self._study_count
    #@property
    def hash_list(self):
        return self._hash_list
    #@property
    def filename(self):
        return self._filename

    @study_count.setter
    def study_count(self, new_value):
        self._study_count = new_value

    def is_multipart(self):
        return (len(self._hash_list) > 1)
    def is_complete(self):
        return self._fulltext

# TODO  - https://www.lingq.com/jobs/
# TODO  - if i add a space between 2 words in a ja text, the indexes will now be off in the text_words file
#           - do we need to reparse? is there a way to notice this and auto-reparse? is there a way to just reparse sentence?
# TODO  - STUDY MODE
#         - functional
#           - extend the "create phrase" idea
#               - we start with words, we identify phrases
#               - then we can build longer phrases, clauses, and full sentences
#               - these will be properly translated
#               - the "history" of a sentence can be viewed
#           - editing works in study mode BUT we need to refactor to use same code as pure edit mode
#               - [ ] study mode; [x] edit mode; have lang setting for commands, y/n/x, etc,
#                     in a language so i don't have to switch between keyboards (in both rev and study)
#           - should be able to look at all words that share a base (will show how verbs are declined, or versions of pronouns, etc)
#               - note: some words have multiple bases, eg. матері (матір,мати)
#               - similarly all words of langs being studied that share a translation, eg. "chair" (result is chair in jp,uk,pl)
#           - after guessing, show any tags or notes
#           - turn on/off phonetic/romaji version (this adds a sentence which uses the lang_map to show english letters)
#         - visual
#           - "Other answer(s):" if base word is different, then display it here (dekinai shows meanings for dekiru)
#           - allow user preferences for stress colour (from all available in colorama)
#               - LIGHTMAGENTA_EX or LIGHTCYAN_EX are pretty good
#           - show (3) for a 3-letter answer; (11) for an eleven-letter answer; this will make things look nicer
#               - but still problem of the native sentence showing weird shortened english words
#           - minor: between word prompts, the number of empty lines varies, should be consistent
# TODO  - EDIT MODE
#         - functional
#           - similar to how we suggest singular nouns if a plural is entered, suggest infinitive of verbs
#               - [x] if "moves" or "moved" is entered, suggest "(to) move" and "(to) mov" (sic)
#               - think of how to systematize this, so that learners of other languages can define similar rules in json/yaml/etc
#               - wip: if type is verb, and word ends in "ed", remove "d" and "ed" and present both as infinitives
#               - for verbs: {"ed": ["e", ""]}, for nouns: {"es": ["e", ""]}
#           - during an edit session across hashes, instead of opening one file at a time for one word, could
#             we look at the next 30 words (from say 5 files) and get their data in 5 reads instead of 30?
#           - add "r)" for resources, which shows good dict sites, etc, and allows user to pin the url(s) while editing
#           - modify (or create new) index file that ignores hashes. just { word: { translations: [], bases: [], ..., stresses: []}}
#           - maintain local index while editing, as these changes won't be reflected in the main index (only gets indexed at start of edit session)
#               - when a reindex is run, the local index is cleared
#           - if a word has a single def'n, mark it as such, and somehow find a way to copy its values to other similar words
#               - which exist in the index
#               - and future versions that get imported
#           - if same word exists in index, include option to view these and copy from one
#               - adding a meaning to a word should show all identical words and allow user to add meaning to all or a subset
#           - phrase function should prompt for first-word position (with default suggestion to current)
#               - this will allow skipped words to be used as 1st word in a phrase
#               - !phrase should show all identical phrases and allow user to create phrases for all or subset (eg. 1,3,4-6 or something)
#           - after "Add alternate representation", !same (!cp to be consistent?) should copy the main word to the alt_rep
#           - user-friendly versions of key names in list
#           - use JMdict_e to find meaning suggestions, furigana, and other reps
#           - give each word a grade level (JMdict_e for JA) or difficulty level; that way words below a certain level will be ignored if "study hash level_4" is chosen
#           - create phrase sending a lot of unnecessary fields; word_data contains both last fields; etc
#           - add stress on base special alt rep (eg. for tanoshikatta we have stress on furigana, but we can't add stress on tanoshii)
#               - was thinking of moving stress to top-level of word entry in word index, but sake/sake has two stresses, so we can't
#           - reorder keys so that foreign-lang keys come first; then they can be used to search word index (esp. useful will be spec_alt_rep)
#         - visual
#           - when editing a word, number the readonly keys, but color the entire line dark gray
#           - (study mode too) native words in native_sent should be coloured for easier reading
#               - pass in the original sentence for comparison and if word is different, colour it
# TODO  - REPL
#           - compare words across existing languages
#           - "show" should show stresses if "show 01a stress"
#           - "show" should show alternate reps if "show 01a alt stress"
#           - colour text list so that texts not studied recently are red; recents are green; and middle are yellow
# TODO  - METADATA
#           - if linked text, show [unfinished], until we mark a text as finished
#           - with linked texts, num words stats are wrong
#           - show all linked texts if a text is linked.
#           - minor: importing should add all metadata keys (some are missing)
# TODO  - IMPORTING TEXTS
#           - if text type is word list, then the sentences parsed will be useless
#           - create and import wordlist of dictionary abbrevs from the slovnyk site
# TODO  - SKIPPING WORDS
#           - skipped word index: could extract surnames, names, city names for new study list
#               - !skiplist could show skipped words in text with ability to undo
# TODO  - TRACKING
#           - need a way to track num_times word is quizzed, and how often correct; in word_index?
#           - anki does a cool thing where it lets you choose num days until next appearance
# TODO  - check for todos strewn about the code then move this down 5 lines
# TODO  - ask AI for most representative sentence for each word (or at least the words you're having difficulty with)
# TODO  - reverse lesson; this creates the reverse form of a lesson; need to know user's base lang (how is this different from rev_study?)
# TODO  - add a way to study verbs or nouns, or words with a certain tag (need a tag index probably)
#           - tag index OR just pass on a word if it is not a verb or noun
#           - eg. study japanese verb OR study ukrainian noun
# TODO  - repl search word/phrase/sub-sentence function
# brainstorm TODO - add a note to a word which appears when studying it, allowing user to take a shortcut to another lesson that focuses on something about that word (ie. numbers and plurals, a type of case, etc.)
# AI TODO - for japanese, i need to manually add spaces to text before feeding into app (use AI later)
# minor TODO - add !edit function when prompting a word without translation.
# minor TODO - if word has tags/note without translation, show (*tags *note) after the prompt
# minor TODO - (not needed since have IME; but for other users) add jp_en.json containing all mappings from hiragana and katakana to english
# minor TODO - do we need a base_alt_representation value? or is it clear how this applies to non-base word? maybe leave for now
# note TODO - when a phrase is created, DO NOT remove spaces from the word; this will affect colouring, etc.
# REFERENCE - http://www.rikai.com/library/kanjitables/kanji_codes.unicode.shtml
# REFERENCE - https://character-table.netlify.app/ukrainian/

def generate_hash(timestamp):
    """Generates a hash from the given timestamp."""
    timestamp_str = timestamp.strftime("%Y%m%d_%H%M%S")
    hash_object = hashlib.sha256(timestamp_str.encode())
    return hash_object.hexdigest()

def get_text_title(text):
    """Extracts the title from the given text."""
    global current_language

    title = None
    if not current_language:
        title = "Untitled"

    if not title:
        pattern = r'(?<=[{}])[{}]?\s+'.format(sent_delims, sent_post_delims)
        first_sentence = re.split(pattern, text)[0]
        if len(first_sentence.split()) > 10:
            try:
                words = first_sentence.split()[:10]  # Get first 10 words
                title = " ".join(words)
            except (IndexError):
                title = "Untitled"
        else:
            title = first_sentence.strip()

    return title

def process_and_save_text(text, text_type, title=None, append_to=None):
    global glob_words_index_count

    #new_text = Text()
    md_timestamp = datetime.now()
    hash = generate_hash(md_timestamp)
    filename = f"{hash}.txt"
    text_dir = os.path.join(texts_dir, current_language)
    filepath = os.path.join(text_dir, filename)
    prev_hash = append_to if append_to else None

    os.makedirs(text_dir, exist_ok=True)

    # Save text to file
    try:
        with open(filepath, "x", encoding="utf-8") as f:
            f.write(text)
    except FileExistsError:
        print("File already exists, aborting.")
        return False

    # Add default timestamp and title metadata
    metadata = {
        "timestamp": md_timestamp.strftime("%Y-%m-%d %H:%M:%S"),
        "language": current_language,
        "type": text_type,
        "title": title if title else get_text_title(text)
    }

    link_hash = prev_hash
    while True:
        mtdt = get_metadata(link_hash)
        next_hash = mtdt.get("next_hash", None)
        if next_hash:
            link_hash = next_hash
        else:
            prev_hash = link_hash
            break

    if prev_hash:
        metadata["prev_hash"] = prev_hash

    # Update metadata file
    update_metadata(hash, metadata)

    if prev_hash:
        prev_metadata = get_metadata(prev_hash)
        prev_metadata["next_hash"] = hash
        update_metadata(prev_hash, prev_metadata)

    if not parse_sentences(hash):
        return False

    if not parse_text(hash):
        return False

    glob_words_index_count = 0

def update_metadata(hash, metadata):
  """Updates the metadata file with information about the new text block."""
  #metadata_path = "metadata.json"

  existing_metadata = get_metadata()
  if not existing_metadata:
      print("Could not write updated data to metadata file.")
      return False

  existing_metadata[hash] = metadata

  with open(metadata_path, "w") as f:
      json.dump(existing_metadata, f, indent=2)

def get_metadata(hash=None):
    #metadata_path = "metadata.json"
    metadata = None
    try:
        with open(metadata_path, "r") as f:
            metadata = json.load(f)
        if hash:
            file_metadata = None
            for h, m in metadata.items():
                if h != hash:
                    continue
                file_metadata = m
            metadata = file_metadata
    except FileNotFoundError:
        print("No metadata file found.")
    return metadata

def fix_metadata(hash_substring=None, quiet=False):
    if not backup_metadata():
        print(f"Metadata cannot be saved since backup failed.")
        return False

    linked_texts = None
    full_hash = None
    if hash_substring:
        full_hash = get_matching_hash(hash_substring)
        if not full_hash:
            return False
        text2fix = Text(full_hash)
        linked_texts = text2fix.hash_list

    existing_metadata = get_metadata()
    if not existing_metadata:
        err_msg = "Could not find any existing metadata. Aborting."
        print(f"{Fore.RED}{err_msg}{Style.RESET_ALL}")
        return

    updated_metadata = {}
    for hash, metadata in existing_metadata.items():
        if ((full_hash and linked_texts and hash not in linked_texts)
            or (full_hash and not linked_texts and full_hash != hash)
            or current_language != metadata["language"].lower()):
            updated_metadata[hash] = metadata
            continue
        filepath = os.path.join(texts_dir, current_language, hash + '.txt')
        if os.path.exists(filepath):
            # Check and update missing "timestamp"
            if "timestamp" not in metadata:
                create_tm = datetime.fromtimestamp(os.path.getctime(filepath))
                metadata["timestamp"] = create_tm.strftime("%Y-%m-%d %H:%M:%S")
                print(f"Info: Timestamp for file '{filepath}' set.")

            # Check and update missing "num_words"
            with open(filepath, "r", encoding="utf-8") as f:
                text = f.read()
            words = text.split()
            metadata["num_words"] = len(words)
            unique_words = set(normalize_word(word.lower()) for word in words)
            #unique_words = set(word.lower() for word in words)
            metadata["num_uniq_words"] = len(unique_words)

            if "lang_code" not in metadata:
                lang_code = None
                try:
                    langs_file = os.path.join(data_dir, "languages.json")
                    #with open("languages.json", "r") as f:
                    with open(langs_file, "r") as f:
                        languages = json.load(f)
                    if type(languages[current_language]) is dict:
                        lang_data = languages[current_language]
                        lang_code = lang_data["lang_code"]
                    else:
                        lang_code = languages[current_language]
                    metadata["lang_code"] = lang_code
                except FileNotFoundError:
                    print("No languages.json file found.")

            if "type" not in metadata:
                # set default text type to 'normal' as opposed to 'wordlist'
                metadata["type"] = "normal"

            updated_metadata[hash] = metadata

        else:
            # if we've manually removed the text, don't keep its metadata
            print(f"text file '{filepath}' not found. Removing metadata.")

    #metadata_path = "metadata.json"
    with open(metadata_path, "w") as f:
        json.dump(updated_metadata, f, indent=2)

    if not quiet:
        print("Metadata updated successfully.")

def list_metadata(hash_substring=None):
    """
    Lists the metadata for all text blocks.
    """
    full_hash = None
    if hash_substring:
        ensure_text_hashes_populated()
        full_hash = [h for h in text_hashes if h.startswith(hash_substring)]

        if len(full_hash) == 0:
            print(f"No text found with hash substring '{hash_substring}'.")
            return

        if len(full_hash) > 1:
            err_msg = (
                "Multiple texts found with hash substring '{}'. "
                "Please provide a more specific substring."
            )
            print(err_msg.format(hash_substring))
            return

        full_hash = full_hash[0]

    existing_metadata = get_metadata()

    for hash, metadata in existing_metadata.items():
        if full_hash and hash != full_hash:
            continue
        print(f"Filename: {hash}.txt")
        for key, value in metadata.items():
            print(f"  - {key}: {value}")
        print("-" * 20)

def list_langs():
    existing_metadata = get_metadata()
    langs = {}
    for metadata in existing_metadata.values():
        if metadata["language"].lower() == "testing":
            continue
        if metadata["language"].lower() in langs:
            langs[metadata["language"].lower()] += 1
        else:
            langs[metadata["language"].lower()] = 0
    langs = sorted(langs.items(), key=lambda x: x[1], reverse=True)
    valid_ints = []
    for i, lang in enumerate(langs):
        valid_ints.append(str(i+1))
        print(f"{i+1}) {lang[0]}")
    lang_input = input("Enter a valid number: ")
    return langs[int(lang_input)-1][0] if lang_input in valid_ints else "_invalid_lang_"

def list_texts(filter=None, limit=None):

    # overkill?
    #fix_metadata(quiet=True)

    existing_metadata = get_metadata()
    if not existing_metadata:
        return

    hash_label = None
    if filter and filter not in ["a", "f", "nf"]:
        hash_label = get_matching_hash(filter)
    if filter and (filter not in ["a", "f", "nf"] and hash_label not in existing_metadata):
        print("Invalid argument. Valid arguments are: a, f, nf, or the hash of a text.")
        return

    show_label = None
    if hash_label in existing_metadata:
        show_label = existing_metadata[hash_label].get("label", None)
        filter = None  # reset filter to None if we found a hash label

    texts = {}
    texts_with_label = {}
    for hash, metadata in existing_metadata.items():
        lang = metadata["language"].lower()
        if not lang.startswith(current_language):
            continue
        # do not include texts that are subsequent parts of an initial text
        if metadata.get("prev_hash", "") != "":
            continue
        if metadata.get("hidden", False):
            continue
        if show_label and metadata.get("label", None) != show_label:
            continue
        if metadata.get("label", None):
            texts_with_label[hash] = metadata
        else:
            texts[hash] = metadata
    texts_with_label.update(texts)
    texts = texts_with_label

    print_texts = []
    labels = []
    for hash, metadata in texts.items():
        try:
          non_empty_translations = 0
          empty_translations = 0
          skipped = 0
          orig_hash = hash
          while True:
            text_words_file = os.path.join(text_words_dir, current_language, f"{hash}.json")
            with open(text_words_file, 'r', encoding='utf-8') as f:
                parsed_text = json.load(f)
            for word_data in parsed_text.values():
                for tr_data in word_data:
                    if tr_data.get("skip", False) == True:
                        skipped += 1
                        continue
                    if tr_data.get("translation", "") != "":
                        non_empty_translations += 1
                    else:
                        empty_translations += 1
                    if alt_representation_required:
                        if tr_data.get("alt_representation", "") != "":
                            non_empty_translations += 1
                        else:
                            empty_translations += 1
            mtdt = get_metadata(hash)
            next_hash = mtdt.get("next_hash", None)
            if next_hash:
                hash = next_hash
            else:
                break
          total_words = non_empty_translations + empty_translations
          percent_complete = 0
          if total_words > 0:
              percent_complete = round(100*non_empty_translations/total_words)
        except FileNotFoundError:
            percent_complete = 0

        short_hash = f"{orig_hash[:6]}"
        percent = f"{'{:3d}'.format(percent_complete)}%"
        if percent_complete <= 33:
            percent = Fore.RED + percent + Style.RESET_ALL
        elif percent_complete <= 66:
            percent = Fore.YELLOW + percent + Style.RESET_ALL
        else:
            percent = Fore.GREEN + percent + Style.RESET_ALL
        title = metadata.get('title', 'No Title').strip()
        url = "u" if metadata.get('url', None) else "-"
        fulltext = metadata.get('fulltext', None)
        if fulltext == None:
            fulltext = '--'
        else:
            fulltext = "FT" if fulltext else f"{Fore.RED}pt{Style.RESET_ALL}"
        last_study = f"{metadata.get('last_study_date', '____-__-__')[:10]}"
        tag = metadata.get('tag', "----")
        tag = f"{'{:>4}'.format(tag)}"
        label = metadata.get('label', None)
        hide_text = False
        if not show_label:
            if label and label not in labels:
                labels.append(label)
            elif label in labels:
                hide_text = True
        if hide_text:
            continue
        if (not filter or filter == "a"
            or (filter == "f" and percent_complete == 100 and fulltext == "FT")
            or (filter == "nf" and fulltext != "FT")):

            print_texts.append({
                "percent": percent,
                "percent_complete": percent_complete,
                "fulltext": fulltext,
                "last_study": last_study,
                "url": url,
                "short_hash": short_hash,
                "tag": tag,
                "label": None if show_label else label,
                "title": title
            })
    if show_label:
        print(f"Label: {show_label}")
    if not limit:
        limit = 1000  # default limit if not specified
    ctr = 0
    for text in print_texts:
        if ctr >= limit:
            break
        ctr += 1
        print(f'{"    " if text["label"] else text["percent"]}', end="|")
        print(f'{"  " if text["label"] else text["fulltext"]}', end="|")
        print(f'{"          " if text["label"] else text["last_study"]}', end="|")
        print(f'{" " if text["label"] else text["url"]}', end="|")
        print(f'{text["short_hash"]}', end="|")
        print(f'{"    " if text["label"] else text["tag"]}', end="|")
        print(f'{Fore.GREEN + text["label"] + Style.RESET_ALL if text["label"] else text["title"]}')
    print()

def ensure_text_hashes_populated():
    """
    Ensures that the global 'text_hashes' set is populated.
    """
    global text_hashes

    text_hashes = set()  # Initialize text_hashes
    existing_metadata = get_metadata()
    if not existing_metadata:
        return False
    for hash, metadata in existing_metadata.items():
        if current_language != metadata["language"].lower():
            continue
        text_hashes.add(hash)

def read_text(hash_substring):
    pass

def show_text(hash_substring):
    """
    Displays the text content based on the provided hash substring.
    """
    ensure_text_hashes_populated()

    matching_hashes = [h for h in text_hashes if h.startswith(hash_substring)]

    if len(matching_hashes) == 0:
        print(f"No text found with hash substring '{hash_substring}'.")
        return

    elif len(matching_hashes) > 1:
        err_msg = (
            "Multiple texts found with hash substring '{}'. "
            "Please provide a more specific substring."
        )
        print(err_msg.format(hash_substring))
        return

    full_hash = matching_hashes[0]
    print("-" * 20)
    text2show = Text(full_hash)
    for hash in text2show.hash_list:
        filepath = os.path.join(texts_dir, current_language, hash + '.txt')
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                text = f.read().replace(" __dummy__", "")
        except FileNotFoundError:
            print(f"Error: text file '{filepath}' not found.")
            return False
        print(text)
    print("-" * 20)

def normalize_word(word):
    return word.lower().strip(word_delims)

def normalize_sentence(sentence):
    return sentence.strip()

def backup_metadata():
    try:
        # Create a backup of the existing metadata
        bkp_fname = f"metadata_{datetime.now().strftime('%Y%m%d%H%M%S')}.json"
        backup_filepath = os.path.join(backups_dir, bkp_fname)
        os.makedirs(backups_dir, exist_ok=True)
        shutil.copy("metadata.json", backup_filepath)
        return True
    except (PermissionError, FileNotFoundError, OSError) as e:
        print(f"Error creating backup: {e}")
        return False

def backup_text_words(hash, word_filepath):
    try:
        # Create a backup of the existing word_data
        bkp_fname = f"{hash}_{datetime.now().strftime('%Y%m%d%H%M%S')}.json"
        backup_filepath = os.path.join(text_words_dir, "backups", bkp_fname)
        backup_path = os.path.join(text_words_dir, "backups")
        os.makedirs(backup_path, exist_ok=True)
        shutil.copy(word_filepath, backup_filepath)
        return True
    except (PermissionError, FileNotFoundError, OSError) as e:
        print(f"Error creating backup: {e}")
        return False

def char_is_dbl_len(c):
    if ("\u3000" <= c <= "\u30ff"
        or "\uff00" <= c <= "\uff60"
        or "\uffe0" <= c <= "\uffe6"
        or "\u4e00" <= c <= "\u9faf"
        or "\u3400" <= c <= "\u4dbf"):
        return True
    else:
        return False

def char_is_kanji(c):
    if "\u4e00" <= c <= "\u9faf":
        return True
    elif "\u3400" <= c <= "\u4dbf":
        return True
    else:
        return False

def char_is_kana(c):
    if "\u3041" <= c <= "\u3096":
        return True
    elif "\u30a1" <= c <= "\u30f7":
        return True
    else:
        return False

def word_has_kanji(w, any=False):
    for c in w:
        if char_is_kanji(c):
            return True
        if any and char_is_kana(c):
            return True
    return False

def alert(text):
    print(f"{Back.RED + str(text) + Style.RESET_ALL}")

def create_sentences(hash, alt=True):

    text_sents_file = os.path.join(text_sents_dir, current_language, f"{hash}.json")
    text_sents_list = None
    try:
        with open(text_sents_file, 'r', encoding='utf-8') as f:
            text_sents_list = json.load(f)
    except FileNotFoundError:
        err_msg = "Error in {}: {} not found."
        print(err_msg.format("_".join(["create","sentences"]), text_sents_file))
        return False

    text_words_file = os.path.join(text_words_dir, current_language, f"{hash}.json")
    try:
        with open(text_words_file, 'r', encoding='utf-8') as f:
            text_words_json = json.load(f)
    except FileNotFoundError:
        err_msg = "Error in {}: {} not found."
        print(err_msg.format("_".join(["create","sentences"]), text_words_file))
        return False

    # Initialize the sentence dictionaries
    sent_dict = {}
    alt_sent_dict = {}
    native_sent_dict = {}
    sent_phrase_dict = {}
    alt_sent_phrase_dict = {}
    native_sent_phrase_dict = {}

    # TODO if a sentence is repeated in a text, the sent_indexes will be off
    for sent in text_sents_list:
        sent_dict[sent] = {}
        alt_sent_dict[sent] = {}
        native_sent_dict[sent] = {}
        sent_phrase_dict[sent] = {}
        alt_sent_phrase_dict[sent] = {}
        native_sent_phrase_dict[sent] = {}

    # Populate the sentence dictionaries with all words in a sentence
    for word, word_data in text_words_json.items():
        for meaning in word_data:
            m_sent = ""
            if text_sents_list and meaning.get("sent_inx", -1) >= 0:
                try:
                    m_sent = text_sents_list[meaning["sent_inx"]]
                except IndexError:
                    pass
            m_inx = meaning["index"]
            if meaning["internal_type"] not in ["word", "phrase"]:
                continue
            if meaning.get("translation", ""):
                native_word = (
                    meaning["translation"].split(",")[0].replace("(","")
                    .replace(")","").replace(" ", format_delim_phrase)
                )
                try:
                    if meaning["internal_type"] == "phrase":
                        native_sent_phrase_dict[m_sent][m_inx] = f"{native_word}"
                    else:
                        native_sent_dict[m_sent][m_inx] = f"{native_word}"
                except KeyError:
                    alert(f"key error in create sentences: {native_sent_dict}")
            else:
                if meaning["internal_type"] == "phrase":
                    native_sent_phrase_dict[m_sent][m_inx] = word
                else:
                    native_sent_dict[m_sent][m_inx] = word
            if meaning.get("special_alt_rep", ""):
                if meaning["internal_type"] == "phrase":
                    alt_sent_phrase_dict[m_sent][m_inx] = meaning["special_alt_rep"]
                else:
                    alt_sent_dict[m_sent][m_inx] = meaning["special_alt_rep"]
            else:
                if meaning["internal_type"] == "phrase":
                    alt_sent_phrase_dict[m_sent][m_inx] = word
                else:
                    alt_sent_dict[m_sent][m_inx] = word
            if meaning["internal_type"] == "phrase":
                sent_phrase_dict[m_sent][m_inx] = word
            else:
                sent_dict[m_sent][m_inx] = word

    final_native_dict = {}
    final_alt_dict = {}

    dicts_to_delimit = [native_sent_dict]
    final_dicts = [final_native_dict]
    if alt:
        dicts_to_delimit.append(alt_sent_dict)
        final_dicts.append(final_alt_dict)

    # this loop compares the orig sent and the other sentence versions
    # and adds any missing delimiters
    for dict_index, dict_to_delimit in enumerate(dicts_to_delimit):
        for sent, sent_data in dict_to_delimit.items():
            words = sent.split()
            for i, word in enumerate(words):
                delims_prefix = ""
                for j in word[:-1]:
                    if j in word_delims:
                        delims_prefix += j
                    else:
                        break
                if i in sent_data:
                    sent_data[i] = delims_prefix + sent_data[i]
                else:
                    sent_data[i] = word
                delims_suffix = ""
                for j in word[::-1][:-1]:
                    if j in word_delims:
                        delims_suffix += j
                    else:
                        break
                if i in sent_data:
                    sent_data[i] = sent_data[i] + delims_suffix[::-1]
                else:
                    sent_data[i] = word
            new_sent = " ".join([s for _, s in sorted(sent_data.items())])
            final_dicts[dict_index][sent] = new_sent

    return sent_dict, final_native_dict, final_alt_dict

def non_std_count(v_string):
    count = 0
    if alt_representation_required:
        for v_ltr in v_string:
            if char_is_dbl_len(v_ltr):
                count += 1
    return count

def std_len(v_string):
    if alt_representation_required:
        str_len = 0
        for v_ltr in v_string:
            if char_is_dbl_len(v_ltr):
                str_len += 2
            else:
                str_len += 1
    else:
        str_len = len(v_string)
    return str_len

def match_case(source_word, dest_word):
    #new_word = dest_word
    #if source_word.isupper() and len(source_word) > 1:
        #new_word = dest_word.upper()
    #elif source_word[0].isupper():
        #new_word = dest_word.capitalize()
    #else:
    new_word = ""
    for i, chr in enumerate(dest_word):
        try:
            if source_word[i].isupper():
                new_word += chr.upper()
            else:
                new_word += chr
        except IndexError:
            new_word += chr
    return new_word

def format_sentences(sentence, native_sent, spec_alt_sent):

    text_sentences = sentence.split()
    ntv_sent_words = native_sent.split()

    if spec_alt_sent:
        alt_sent_words = spec_alt_sent.split()
        has_spec = True
    else:
        alt_sent_words = list(len(text_sentences) * "a")
        has_spec = False

    for i, sent_word in enumerate(text_sentences):
        #if not alt_representation_required:
        ntv_sent_words[i] = match_case(sent_word, ntv_sent_words[i])

        if has_spec:
            if i == 0 and ntv_sent_words[0] != sent_word:
                ntv_sent_words[0] = ntv_sent_words[0].capitalize()
            alt_sent_words[i] = match_case(sent_word, alt_sent_words[i])
            if sent_word.lower() == ntv_sent_words[i].lower() == alt_sent_words[i].lower():
                continue
        else:
            if sent_word.lower() == ntv_sent_words[i].lower():
                if sent_word != ntv_sent_words[i]:
                    ntv_sent_words[i] = sent_word
                continue

        word_offset = 0

        native_len = std_len(ntv_sent_words[i])
        ntv_dbl_count = non_std_count(ntv_sent_words[i])

        dlm_pos = ntv_sent_words[i].find(format_delim_phrase)
        delim_cnt = 0
        while dlm_pos != -1:
            delim_cnt += 1
            dlm_pos = ntv_sent_words[i].find(format_delim_phrase, dlm_pos+1)

        if delim_cnt:
            word_offset = (len(format_delim_phrase) - 1) * delim_cnt
            native_len -= word_offset

        word_len = std_len(sent_word)
        if has_spec:
            spec_len = std_len(alt_sent_words[i])
            max_len = max(native_len, spec_len)
            if max_len == native_len and native_len % 2 != spec_len % 2:
                if native_len % 2 == 1:
                    native_len += 1
        else:
            max_len = max(word_len, native_len)

        if max_len != word_len:
            if alt_representation_required:
                try:
                    text_sentences[i] = "{: ^{}s}".format(sent_word, max_len-non_std_count(sent_word))
                except ValueError:
                    alert(f"sent_word: {sent_word}")
                    alert(f"max_len: {int(max_len)}")
                    alert(f"non_std_count(sent_word): {non_std_count(sent_word)}")
            else:
                text_sentences[i] = "{: ^{}s}".format(sent_word, max_len)

        if max_len != native_len:
            ntv_sent_words[i] = "{: ^{}s}".format(ntv_sent_words[i], max_len+word_offset-ntv_dbl_count)

        if has_spec and max_len != spec_len:
            alt_sent_words[i] = "{: ^{}s}".format(alt_sent_words[i], max_len-len(alt_sent_words[i]))

    sentence = format_delim_word.join(text_sentences)
    native_sent = format_delim_word.join(ntv_sent_words)
    if has_spec:
        spec_alt_sent = format_delim_word.join(alt_sent_words)
    else:
        spec_alt_sent = ""

    return sentence, native_sent, spec_alt_sent

def get_word_data(
        hash_list=None,
        randomize=False,
        alt=False,
        exclude_filters={}):
    # "alt" has been set to True in each place this function is called.
    # writing this comment on 2025-07-28
    # after some time of no issues, make the alt functionality the default one.

    global GLOBAL_WORD_INDEX

    data_delimiter = "__suhs__"
    word_hash_inx_list = []
    alt_list = []
    while True:
        for word, index_records in GLOBAL_WORD_INDEX.items():
            for index_record in index_records:
                if hash_list and index_record["hash"] not in hash_list:
                    continue
                if "word_ptr" in index_record:
                    continue
                if exclude_filters:
                    exclude = False
                    for excl_key, excl_value in exclude_filters.items():
                        # TODO: create unabbrev function?
                        index_value = index_record.get(excl_key, "")
                        if index_value == "_w_":
                            index_value = word
                        elif index_value == "_a_":
                            index_value = index_record.get("alt_representation", "")
                        elif index_value == "_t_":
                            index_value = index_record.get("translation", "")
                        if index_value == excl_value:
                            exclude = True
                    if exclude:
                        continue
                new_item = data_delimiter.join([
                    word,
                    index_record["hash"],
                    str(index_record["list_index"]),
                    str(index_record["index"]),
                    str(index_record["sent_inx"])
                ])
                word_hash_inx_list.append(new_item)
                alt_item = [
                    word,
                    index_record["hash"],
                    index_record["list_index"],
                    index_record["index"],
                    index_record["sent_inx"]
                ]
                alt_list.append(alt_item)
        sorted_alt_list = sorted(alt_list, key=lambda x: (x[1], x[4], x[3]))
        if alt:
            word_hash_inx_list = [data_delimiter.join([x[0], x[1], str(x[2]), str(x[3]), str(x[4])]) for x in sorted_alt_list]
        break
    if randomize:
        random.shuffle(word_hash_inx_list)
    all_words = []
    all_hashes = []
    all_list_inxs = []
    all_word_inxs = []
    all_sent_inxs = []
    for item in word_hash_inx_list:
        word, hash, list_index, word_index, sent_index = item.split(data_delimiter)
        all_words.append(word)
        all_hashes.append(hash)
        all_list_inxs.append(int(list_index))
        all_word_inxs.append(int(word_index))
        all_sent_inxs.append(int(sent_index))
    all_words_dict = {
        "all_words": all_words,
        "all_hashes": all_hashes,
        "all_list_inxs": all_list_inxs,
        "all_word_inxs": all_word_inxs,
        "all_sent_inxs": all_sent_inxs
    }
    return all_words_dict
    #return all_words, all_hashes, all_list_inxs, all_word_inxs, all_sent_inxs

def get_sentences(base_index, text_sents_list, offset=1, prev_hash=None, next_hash=None):

    num_sents = len(text_sents_list)
    if offset < 0:
        text_sents_list = [s for s in reversed(text_sents_list)]
        base_index = num_sents - base_index - 1

    context_sents = text_sents_list[(base_index+1):][:abs(offset)]
    if offset < 0:
        if len(context_sents) < abs(offset):
            if prev_hash:
                # open sentence file for the previous text
                prev_text_sents_file = os.path.join(text_sents_dir, current_language, f"{prev_hash}.json")
                with open(prev_text_sents_file, 'r', encoding='utf-8') as f:
                    prev_text_sents_list = json.load(f)
                # add the last sentences from the previous text.
                prev_sents = prev_text_sents_list[-(abs(offset) - len(context_sents)):]
                prev_sents = [s for s in reversed(prev_sents)]
                context_sents.extend(prev_sents)
            else:
                context_sents.append("<<< START TEXT >>>")
        context_sents = [s for s in reversed(context_sents)]
    else:
        if len(context_sents) < offset:
            if next_hash:
                # open sentence file for the next text
                next_text_sents_file = os.path.join(text_sents_dir, current_language, f"{next_hash}.json")
                with open(next_text_sents_file, 'r', encoding='utf-8') as f:
                    next_text_sents_list = json.load(f)
                # add the first sentences from the next text.
                context_sents.extend(next_text_sents_list[:(offset - len(context_sents))])
            else:
                context_sents.append("<<< END TEXT >>>")

    return context_sents

def abbrev_wordtype(word_type):
    if word_type == "adjective":
        return "a"
    elif word_type in ["pre-noun adjective", "pre-noun adjectival"]:
        return "np"
    elif word_type == "adverb":
        return "av"
    elif word_type == "verb":
        return "v"
    elif word_type == "suru verb":
        return "sv"
    elif word_type == "auxiliary verb":
        return "av"
    elif word_type == "prenominal verb":
        return "pv"
    elif word_type == "auxiliary":
        return "ax"
    elif word_type == "noun":
        return "n"
    elif word_type == "nominalizing suffix":
        return "ns"
    elif word_type == "noun suffix":
        return "nx"
    elif word_type == "noun prefix":
        return "nf"
    elif word_type == "noun phrase":
        return "nh"
    elif word_type == "suffix":
        return "sx"
    elif word_type == "prefix":
        return "px"
    elif word_type == "pronoun":
        return "pr"
    elif word_type == "particle":
        return "pa"
    elif word_type == "preposition":
        return "pp"
    elif word_type == "phrase":
        return "ph"
    elif word_type == "conjunction":
        return "c"
    elif word_type == "counter":
        return "ct"
    elif word_type == "numeric":
        return "nm"
    elif word_type == "number":
        return "nu"
    elif word_type == "expression":
        return "x"
    elif word_type == "interrogative":
        return "i"
    elif word_type == "interjection":
        return "in"
    elif word_type == "place":
        return "pl"
    elif word_type == "station":
        return "s"
    elif word_type == "copula":
        return "cp"
    elif word_type == "date":
        return "d"
    elif word_type == "name":
        return "na"
    elif word_type == "full name":
        return "fn"
    elif word_type == "surname":
        return "sn"
    elif word_type == "company":
        return "co"
    elif word_type == "group":
        return "g"
    elif word_type in ["org", "organization"]:
        return "o"
    elif word_type == "abbreviation":
        return "ab"
    else:
        return word_type

def unabbrev_wordtype(word_type):
    if word_type == "n":
        return "noun"
    elif word_type == "ns":
        return "nominalizing suffix"
    elif word_type == "nx":
        return "noun suffix"
    elif word_type == "nf":
        return "noun prefix"
    elif word_type == "nh":
        return "noun phrase"
    elif word_type == "px":
        return "prefix"
    elif word_type == "sx":
        return "suffix"
    elif word_type == "v":
        return "verb"
    elif word_type == "a":
        return "adjective"
    elif word_type in ["ad", "av"]:
        return "adverb"
    elif word_type == "np":
        return "pre-noun adjectival"
    elif word_type == "pa":
        return "particle"
    elif word_type == "c":
        return "conjunction"
    elif word_type == "ct":
        return "counter"
    elif word_type == "nm":
        return "numeric"
    elif word_type == "nu":
        return "number"
    elif word_type == "sv":
        return "suru verb"
    elif word_type == "av":
        return "auxiliary verb"
    elif word_type == "pv":
        return "prenominal verb"
    elif word_type == "ax":
        return "auxiliary"
    elif word_type in ["pr", "pn"]:
        return "pronoun"
    elif word_type == "pp":
        return "preposition"
    elif word_type == "ph":
        return "phrase"
    elif word_type == "i":
        return "interrogative"
    elif word_type == "in":
        return "interjection"
    elif word_type == "x":
        return "expression"
    elif word_type == "pl":
        return "place"
    elif word_type == "s":
        return "station"
    elif word_type == "cp":
        return "copula"
    elif word_type == "d":
        return "date"
    elif word_type == "na":
        return "name"
    elif word_type == "fn":
        return "full name"
    elif word_type == "sn":
        return "surname"
    elif word_type == "co":
        return "company"
    elif word_type == "g":
        return "group"
    elif word_type == "o":
        return "organization"
    elif word_type == "ab":
        return "abbreviation"
    else:
        return word_type
    
def edit(edit_text=None, randomize=False):
    import pyperclip

    global GLOBAL_WORD_INDEX, glob_words_index_lang, glob_words_index_count
    global current_hash

    rule_mgr = RulesManager(rules_dir=rules_dir)

    backup_present = {}

    lang = Language(current_language)
    editable_word_keys = lang.editable_word_keys

    if not index_words(current_language):
        return False

    all_words_dict = get_word_data(
        hash_list=edit_text.hash_list if edit_text else None,
        alt=True
    )
    all_words = all_words_dict.get("all_words", None)
    all_hashes = all_words_dict.get("all_hashes", None)
    all_list_inxs = all_words_dict.get("all_list_inxs", None)
    all_word_inxs = all_words_dict.get("all_word_inxs", None)
    all_sent_inxs = all_words_dict.get("all_sent_inxs", None)

    if not all_words:
        print("Error: no words found!")
        return False

    rand_indxs = [i for i in range(len(all_words))]
    if randomize:
        random.shuffle(rand_indxs)

    ten_nums = [i for i in range(10)]
    last_hash = None
    skip_frequents = True
    do_skip = True
    skip_completed = True

    for inx in range(len(all_words)):
        word = all_words[rand_indxs[inx]]

        # skip "frequent" words 90% of the time
        if skip_frequents and frequents and word in frequents:
            random.shuffle(ten_nums)
            if ten_nums[0] != 0:
                continue
        # when traversing a sentence (< and > commands) do not skip "frequents"
        if not skip_frequents:
            skip_frequents = True

        hash = all_hashes[rand_indxs[inx]]
        list_index = all_list_inxs[rand_indxs[inx]]
        word_index = all_word_inxs[rand_indxs[inx]]

        edit_text = Text(hash)

        current_hash = hash # global
        prev_context = None
        next_context = None
        # TODO if hash is same as last hash and if we didn't save on the last word
        #          we don't need to reload parsed text.
        #      or, same hash, we did save, but this word isn't in list of previously-skipped words
        #          then we don't need to reload parsed text.
        text_sents_file = os.path.join(text_sents_dir, current_language, f"{hash}.json")
        text_sents_list = None
        try:
            with open(text_sents_file, 'r', encoding='utf-8') as f:
                text_sents_list = json.load(f)
        except FileNotFoundError:
            err_msg = "Error in {}: {} not found."
            print(err_msg.format("".join(["ed","it"]), text_sents_file))
            return False
        text_words_file = os.path.join(text_words_dir, current_language, f"{hash}.json")

        try:
            with open(text_words_file, 'r', encoding='utf-8') as f:
                parsed_text = json.load(f)
                #break
        except FileNotFoundError:
            print(f"Error in edit (): File '{text_words_file}' not found.")
            return False

        meaning = parsed_text[word][list_index]
        # even though the word index doesn't contain skipped words, during a session multiple instances of
        # a word can be skipped, which may affect upcoming words; hence, this check
        # TODO could avoid lots of file access by maintaining a list of skip word/hash/indexes in this session
        if do_skip and "skip" in meaning and meaning["skip"]:
            continue
        if not do_skip:
            do_skip = True
        can_edit = False
        for word_key in editable_word_keys:
            if meaning.get(word_key, "") in [False, ""]:
                if word_key == "stress_marks" and alt_representation_required and meaning.get("special_alt_rep", "") == "":
                    continue
                # TODO this should be a user setting based on whether they have access to dict w/stresses
                if word_key == "stress_marks" and current_language == "polish":
                    continue
                can_edit = True
                break
        if skip_completed and not can_edit:
            continue
        if not skip_completed:
            skip_completed = True

        if hash != last_hash or glob_words_index_count == default_words_index_count:
            _, native_sentences, alt_sentences = create_sentences(hash, alt=alt_representation_required)
        last_hash = hash

        save_required = False
        save_and_exit = False
        save_and_cont = False

        sentence = ""
        if text_sents_list and meaning.get("sent_inx", -1) >= 0:
            try:
                sentence = text_sents_list[meaning["sent_inx"]]
            except IndexError:
                pass

        if sentence in alt_sentences and alt_sentences[sentence]:
            alt_sentence = alt_sentences[sentence]
        else:
            alt_sentence = ""

        if sentence in native_sentences and native_sentences[sentence]:
            native_sent = native_sentences[sentence]
        else:
            native_sent = ""

        formatted_sent, native_sent, alt_sentence = format_sentences(sentence, native_sent, alt_sentence)

        if alt_sentence:
            alt_sentence = "\n> " + colour_sentence(
                alt_sentence, word, [meaning["index"]],
                colors=[Fore.BLACK, Fore.WHITE]
            )
        if native_sent:
            native_sent = f"{Fore.GREEN}>{Style.RESET_ALL} " + colour_sentence(
                native_sent, word, [meaning["index"]],
                orig_sent=formatted_sent,
                colors=[Fore.BLACK, Fore.BLUE],
                bg_clr=Back.BLUE,
                add_stress_marks=False,
                space_char="/"
            )
            native_sent = native_sent.replace(format_delim_word, " ")

        sugg_dict = {}
        base_params = {
            "return_one": True,
            "base": meaning.get("base", "")
        }
        sugg_params = {
            "type": base_params | {"search_keys": ["type"]},
            "translation": base_params,
            "base": base_params | {"search_keys": ["base"], "include": [word]},
            "base_translation": base_params | {"search_keys": ["base_translation"], "include": [meaning.get("translation", None)]}
        }
        if alt_representation_required:
            base_params["base"] = None
            sugg_params["alt_representation"] = base_params | {"search_keys": ["alt_representation", "special_alt_rep"]}
            sugg_params["special_alt_rep"] = base_params | {"search_keys": ["special_alt_rep"]}

        for word_key, sugg_param in sugg_params.items():
            if meaning.get(word_key, "") == "":
                key_sugg, _ = search_word_index(word, **sugg_param)
                if key_sugg:
                    sugg_dict[word_key] = key_sugg

        max_row_width = 0
        for word_key in sugg_params.keys():
            if (not meaning.get(word_key, "") and
                len(meaning.get(word_key, "<empty>")+word_key) > max_row_width):
                max_row_width = len(meaning.get(word_key, "<empty>")+word_key)

        # Loop that allows user to fill in any missing data for current word
        sentence_copied = False
        while True:
            if not sentence_copied:
                if copy_quotes:
                    pyperclip.copy(f'"{word}"')
                else:
                    pyperclip.copy(f'{word}')
            else:
                sentence_copied = False
            #try:
            #except:
                #pass
            edit_str = "Editing "
            print(f"\n{edit_str}{Fore.BLUE + word + Style.RESET_ALL}")
            # TODO make this work with dbl chars (use that function that counts wide chars)
            print("-" * len(edit_str + word))
            if prev_context:
                print("\n".join(prev_context))
            the_sent = colour_sentence(
                formatted_sent,
                word,
                [meaning["index"]],
                colors=([Fore.BLACK, Fore.BLUE]),
                add_stress_marks=not alt_representation_required
            )
            the_sent = f"\n{Fore.MAGENTA}>{Style.RESET_ALL} " + the_sent

            if IS_DEV_MODE:
                print(f"{Fore.RED}[DEV-DATA]{Style.RESET_ALL}")

            print(native_sent + alt_sentence + the_sent)
            if next_context:
                print("\n".join(next_context))
            print(f'\n  {meaning["internal_type"].capitalize()}: {Fore.BLUE + word + Style.RESET_ALL}')
            # TODO make these lang settings
            #import urllib.parse
            #safe_word = urllib.parse.quote_plus(word)
            #if language == "japanese":
                #print(f"{Fore.YELLOW}https://jisho.org/search/{safe_word}{Style.RESET_ALL}")
            #elif language == "ukrainian":
                #print(f"{Fore.YELLOW}https://dmklinger.github.io/ukrainian/#search?q={safe_word}?s=freq{Style.RESET_ALL}")
            has_green = False
            if len([sg for sg in sugg_dict.values() if sg]) == 1:
                sugg_dict = {}
            for i, word_key in enumerate(editable_word_keys):
                word_value = meaning.get(word_key, "")
                word_clr = Fore.BLUE
                max_i = i+1
                numf = i+1
                num_clr = None
                if word_key == "stress_marks" and alt_representation_required and meaning.get("special_alt_rep", "") == "":
                    num_clr = Fore.BLACK
                    numf = "-"
                    word_clr = Fore.BLACK
                    word_value = "<requires special_alt_rep>"
                    max_i = i
                    #max_i = i-1
                elif word_value in [False, ""]:
                    num_clr = Fore.GREEN
                    #numf = str(i+1)
                    has_green = True
                    word_clr = Fore.BLACK
                    word_value = "<empty>"
                    #max_i = i+1
                elif word_key == "stress_marks":
                    #num_clr = None
                    #numf = i+1
                    viz_stress = ""
                    if word_value != "(none)":
                        if alt_representation_required:
                            word2stress = meaning["special_alt_rep"]
                        else:
                            word2stress = word
                        viz_stress = f" ({add_stress(word2stress, word_value)})"
                    word_value += viz_stress
                    #max_i = i+1
                elif word_key == "type":
                    word_value = unabbrev_wordtype(word_value)
                #else:
                    #num_clr = None
                    #numf = i+1
                    #max_i = i+1
                sugg_text = ""
                if sugg_dict.get(word_key, ""):
                    if meaning.get(word_key, ""):
                        del(sugg_dict[word_key])
                    else:
                        if word_key == "type":
                            sugg_value = unabbrev_wordtype(sugg_dict[word_key])
                        else:
                            sugg_value = sugg_dict[word_key]
                        sugg_text = f"<= {numf}) {Fore.GREEN + sugg_value + Style.RESET_ALL}"
                        #sugg_text = f"<= {numf}) {Fore.GREEN + sugg_dict[word_key] + Style.RESET_ALL}"
                disp_text = f"  {numf}) [{word_key}] {word_value}"
                disp_text = "{0: <{1}s}".format(disp_text, max_row_width+9)
                disp_text = disp_text[::-1].replace(word_value[::-1], (word_clr + word_value + Style.RESET_ALL)[::-1], count=1)[::-1]
                if num_clr:
                    disp_text = disp_text.replace("  "+str(numf), "  "+num_clr + str(numf) + Style.RESET_ALL)
                print(f"{disp_text}{sugg_text}")
            if meaning["internal_type"] != "word":
                print("  d) delete")
            print(" <>) edit another word       c<>) more context")
            print("  a) accept suggestions        m) more info")
            skip_style = ""
            if meaning.get("skip", ""):
                skip_style = Fore.BLACK
            print(f"  {skip_style}s) skip{Style.RESET_ALL}                      p) phrase")
            pre_style = ""
            post_style = ""
            if has_green:
                pre_style = Fore.GREEN
                post_style = Style.RESET_ALL
            print(f"  {pre_style}n{post_style}) save and next             q) exit")
            while True:
                if IS_DEV_MODE:
                    print(f"{Fore.RED}[DEV-DATA]{Style.RESET_ALL}")
                num_input = input("Enter a valid option: ").lower()
                input_cmd = None
                edit_param = None
                try:
                    num_input, edit_param = num_input.split()
                except ValueError:
                    edit_param = None
                if num_input in edit_inputs:
                    input_cmd = edit_inputs[num_input]
                    break
                try:
                    if 1 <= int(num_input) <= max_i:
                        break
                    else:
                        continue
                except ValueError:
                    pass
            if input_cmd == 'exit':
                save_required = True
                save_and_exit = True
                break
            elif input_cmd == 'next':
                save_and_cont = True
                break

            elif input_cmd in ['word_prev', 'word_next']:
                words = text_sents_list[meaning["sent_inx"]].split()
                if len(words) == 1:
                    continue

                if edit_param:
                    try:
                        edit_param = int(edit_param)
                        if edit_param < 1:
                            print("must be 1, 2, 3")
                            continue
                    except ValueError:
                        print("must be a number")
                        continue
                else:
                    edit_param = 1
                chosen_word_offset = edit_param * (-1 if input_cmd == "word_prev" else 1)

                skip_frequents = False
                do_skip = False
                skip_completed = False

                chosen_word_index = word_index + chosen_word_offset
                if chosen_word_index < 0 or chosen_word_index > len(words)-1:
                    chosen_word_index = chosen_word_index % len(words)

                chosen_word = normalize_word(words[chosen_word_index])
                chosen_word_list_inx = [
                    i for i, w in enumerate(all_words)
                        if w == chosen_word
                        and all_hashes[i] == current_hash
                        and all_sent_inxs[i] == meaning["sent_inx"]
                        and all_word_inxs[i] == chosen_word_index
                ]
                if chosen_word_list_inx and len(chosen_word_list_inx) == 1:
                    chosen_word_list_inx = chosen_word_list_inx[0]
                    chosen_word_rand_inx = rand_indxs.index(chosen_word_list_inx)
                    #if the chosen word is actually next in the main list, simply continue
                    #if chosen_word_rand_inx == inx+1:
                        #continue
                    upcoming_rand_inx = rand_indxs.index(inx+1)
                    rand_indxs[chosen_word_rand_inx], rand_indxs[inx+1] = rand_indxs[inx+1], rand_indxs[chosen_word_rand_inx]
                    save_and_cont = True
                    break
                else:
                    alert(f"couldn't find {chosen_word} in expected spot in the word list")
                    continue
                # TODO message that word is skipped
                # TODO or just show the word with no options
                # TODO or just have swap_words move prev until a non-skipped word found
            elif input_cmd == 'context_prev':
                if edit_param:
                    try:
                        edit_param = int(edit_param)
                        if edit_param < 1:
                            print("must be 1, 2, 3")
                            continue
                        edit_param = -edit_param
                    except ValueError:
                        print("must be a number")
                        continue
                else:
                    edit_param = -1
                prev_context = get_sentences(meaning["sent_inx"],
                                             text_sents_list,
                                             offset=edit_param,
                                             prev_hash=edit_text.prev_hash)
            elif input_cmd == 'context_next':
                if edit_param:
                    try:
                        edit_param = int(edit_param)
                        if edit_param < 1:
                            print("must be 1, 2, 3")
                            continue
                    except ValueError:
                        print("must be a number")
                        continue
                else:
                    edit_param = 1
                next_context = get_sentences(meaning["sent_inx"],
                                             text_sents_list,
                                             offset=edit_param,
                                             next_hash=edit_text.next_hash)
            elif input_cmd == 'skip':
                confirmation = input(f"Do you really want to skip {Fore.BLUE + word + Style.RESET_ALL}? {Fore.GREEN}(y/n){Style.RESET_ALL}: ")
                if confirmation in yes_letter:
                    save_required = True
                    save_and_cont = True
                    parsed_text[word][list_index]["skip"] = True
                    same_words = []
                    for i, version in enumerate(parsed_text[word]):
                        if i == list_index or ("skip" in version and version["skip"]):
                            continue
                        same_words.append(i)
                    if same_words:
                        print("Do you want to skip other occurrences of this word from the same text?")
                        skipsame = input(f"Type 'y' to see a list (max. 10 items) {Fore.GREEN}(y/n){Style.RESET_ALL}: ")
                        if skipsame in yes_letter:
                            max_i = None
                            for i, sw in enumerate(same_words):
                                if i == 10:
                                    break
                                max_i = 0 if max_i == None else max_i+1
                                sw_trans = parsed_text[word][sw]["translation"]
                                sw_trans = "(none)" if not sw_trans else sw_trans
                                if (text_sents_list
                                    and parsed_text[word][sw]["sent_inx"] >= 0
                                    and text_sents_list[parsed_text[word][sw]["sent_inx"]]):
                                    sw_sent = text_sents_list[parsed_text[word][sw]["sent_inx"]]
                                sw_sent = colour_sentence(sw_sent, word, [parsed_text[word][sw]["index"]], word_delim=" ")
                                print(f"  {Fore.GREEN + str(i) + Style.RESET_ALL}) {word}: translation: {sw_trans}; sentence: {sw_sent}")
                            poss_ans = [str(i) for i in range(max_i+1)]
                            while True:
                                to_skip = input("Enter comma-separated numbers (eg. 2,4,5) or 'a' for ALL ('q' to exit): ").lower()
                                if to_skip in exit_letter:
                                    break
                                if to_skip in all_letter:
                                    to_skip = ",".join(poss_ans)
                                skips = to_skip.split(",")
                                invalid_char = False
                                for skip in skips:
                                    if skip not in poss_ans:
                                        print(f"{Fore.RED}Invalid numbers entered ({skip}). Try again.{Style.RESET_ALL}")
                                        invalid_char = True
                                        break
                                if invalid_char:
                                    continue
                                skip_conf = input(f"Are you sure you want to skip these: {to_skip}? {Fore.GREEN}(y/n){Style.RESET_ALL} ")
                                if skip_conf in yes_letter:
                                    for skip in skips:
                                        parsed_text[word][same_words[int(skip)]]["skip"] = True
                                else:
                                    print(f"{Fore.RED}Skip aborted.{Style.RESET_ALL}")
                                break
                        else:
                            print(f"{Fore.RED}List aborted.{Style.RESET_ALL}")
                    print()
                    continue
                else:
                    print(f"{Fore.RED}Skip aborted.{Style.RESET_ALL}")
            elif input_cmd == 'phrase':
                words_in_sentence = sentence.split()
                #sent_inx = None
                #if (text_sents_list
                    #and meaning.get("sent_inx", "") >= 0
                    #and text_sents_list[meaning["sent_inx"]]):
                sent_inx = meaning["sent_inx"]
                phrase, new_phrase = create_phrase(
                    parsed_text,
                    words_in_sentence,
                    meaning["index"],
                    sentence,
                    sent_inx=sent_inx
                )
                if phrase:
                    parsed_text.setdefault(phrase, []).append(new_phrase)
                    save_required = True
                else:
                    print("Failed to create phrase.")
            elif input_cmd == 'accept':
                while True:
                    to_accept = input("Press 'a' to accept all, or enter a comma-separated list ('q' to exit): ").lower()
                    if to_accept in exit_letter:
                        break
                    inx_list = []
                    for key, val in sugg_dict.items():
                        if sugg_dict[key]:
                            inx_list.append(str(editable_word_keys.index(key)+1))
                    if to_accept in all_letter:
                        to_accept = ",".join(inx_list)
                    accepts = to_accept.split(",")
                    invalid_char = False
                    for accept in accepts:
                        if accept not in inx_list:
                            print(f"{Fore.RED}Invalid numbers entered ({accept}). Try again.{Style.RESET_ALL}")
                            invalid_char = True
                            break
                    if invalid_char:
                        continue
                    accept_conf = input(f"Are you sure you want to accept these: {to_accept}? {Fore.GREEN}(y/n){Style.RESET_ALL} ")
                    if accept_conf in yes_letter:
                        for accept in accepts:
                            parsed_text[word][list_index][editable_word_keys[int(accept)-1]] = sugg_dict[editable_word_keys[int(accept)-1]]
                        sugg_dict = {}
                    else:
                        print(f"{Fore.RED}Accept aborted.{Style.RESET_ALL}")
                    break
            elif input_cmd == 'globals':
                alert(f"current_hash: {current_hash}")
                alert(f"glob_words_index_count: {glob_words_index_count}")
                pass
            elif input_cmd == 'more':
                print("\n")
                print(f"Hash: {hash}")
                orig_sent = sentence.replace(" __dummy__", "")
                if current_language == "japanese":
                    orig_sent = sentence.replace(' ', '')
                #else:
                    #orig_sent = sentence
                pyperclip.copy(f'{orig_sent}')
                print(f"Sentence: {orig_sent}")
                sentence_copied = True
            elif input_cmd == 'delete':
                if meaning["internal_type"] != "word":
                    del_conf = input(f"Are you sure you want to delete [{word}]? (y/n)")
                    if del_conf in yes_letter:
                        del parsed_text[word][list_index]
                        if not parsed_text[word]:
                            del parsed_text[word]
                        save_required = True
                    break
                else:
                    alert("You cannot delete an internally-created word!")
            elif editable_word_keys[int(num_input)-1] == "special_alt_rep":
                # show a selection list
                alt_reps = [word]
                alt_reps_simple = []
                if rule_mgr.is_simple(word, current_language):
                    alt_reps_simple.append(word)
                raw_alt_reps = meaning.get("alt_representation", "").split(",")
                for alt_rep in raw_alt_reps:
                    if alt_rep == word or not alt_rep:
                        continue
                    if rule_mgr.is_simple(alt_rep, current_language):
                        alt_reps_simple.append(alt_rep)
                    alt_reps.append(alt_rep)
                if current_language == "japanese":
                    alt_reps = alt_reps_simple
                print(f"Select a special alternate representation for {word}: ")
                for i, alt_rep in enumerate(alt_reps):
                    print(f"  {i+1}) {alt_rep}")
                    max_i = i+1
                print(f"  q) exit")
                while True:
                    user_input = input("Enter a valid option or type a new value: ")
                    if user_input in exit_letter:
                        break
                    try:
                        if 1 <= int(user_input) <= max_i:
                            spec_alt_rep = alt_reps[int(user_input)-1]
                        else:
                            continue
                    except ValueError:
                            spec_alt_rep = user_input
                    if "," in user_input:
                        print(f"{Fore.RED}No commas allowed. Please enter single value.{Style.RESET_ALL}")
                    else:
                        meaning["special_alt_rep"] = spec_alt_rep
                        parsed_text[word][list_index] = meaning
                        save_required = True
                        break
            elif editable_word_keys[int(num_input)-1] == "stress_marks":
                match_keys = {}
                if meaning.get("type", None):
                    match_keys["type"] = meaning["type"]
                if alt_representation_required and meaning.get("special_alt_rep", None):
                    match_keys["special_alt_rep"] = meaning["special_alt_rep"]
                suggestions, _ = search_word_index(
                    word,
                    match_keys=match_keys,
                    search_keys=["stress_marks"]
                )
                sugg_text = ""
                sugg_choices = {}
                if suggestions:
                    sugg_text = ", or type a letter"
                    print("Suggestions:")
                    abc = list(alphabet.keys())
                    for i, sugg in enumerate(suggestions):
                        sugg_choices[abc[i]] = sugg
                        print(f"  {abc[i]}) {sugg}")
                if current_language == "japanese":
                    # TODO this stuff should move to lang configs
                    word_stress = meaning["special_alt_rep"]
                    space_char = "\u3000"
                    nums = ["\uff11", "\uff12", "\uff13", "\uff14", "\uff15", "\uff16", "\uff17", "\uff18", "\uff19", "\uff10"]
                else:
                    # TODO this stuff should move to lang configs
                    word_stress = word
                    space_char = " "
                    nums = ["1", "2", "3", "4", "5", "6", "7", "8", "9", "0"]
                word_len = len(word_stress)
                poss_ans = [str(i) for i in range(1, word_len+1)]
                if word_len >= 10:
                    for i in range(9):
                        print(space_char, end="")
                    for i in range(word_len-9):
                        print(f'{Fore.GREEN + nums[floor(i/10)] + Style.RESET_ALL}', end=("" if i < word_len-10 else "\n"))
                for i in range(word_len):
                    print(f'{Fore.GREEN}{nums[i % 10]}{Style.RESET_ALL}', end="")
                print(f"\n{word_stress}")
                while True:
                    stress_marks = input(f"Add stresses (1 or 2,3 or 2-4), 'c' to clear, 'n' for none, 'q' to exit{sugg_text}: ").lower()
                    if stress_marks in exit_letter:
                        break
                    if stress_marks in ['c']:
                        meaning["stress_marks"] = ""
                        parsed_text[word][list_index] = meaning
                        save_required = True
                        break
                    if stress_marks in no_letter:
                        meaning["stress_marks"] = "(none)"
                        parsed_text[word][list_index] = meaning
                        save_required = True
                        break
                    stresses = stress_marks.split(",")
                    invalid_char = False
                    for j, stress in enumerate(stresses):
                        if stress in sugg_choices:
                            #stress_marks = sugg_choices[stress]
                            stresses[j] = sugg_choices[stress]
                            break
                        if "-" not in stress and stress not in poss_ans:
                            print(f"{Fore.RED}Invalid numbers entered. Try again.{Style.RESET_ALL}")
                            invalid_char = True
                            break
                        if "-" in stress:
                            str_start, str_end = stress.split("-")
                            if (str_start not in poss_ans
                                or str_end not in poss_ans
                                or int(str_start) >= int(str_end)):
                                print(f"{Fore.RED}Invalid numbers entered. Try again.{Style.RESET_ALL}")
                                invalid_char = True
                                break
                            stresses[j] = ",".join([str(i) for i in range(int(str_start), int(str_end)+1)])
                    stress_marks = ",".join(stresses)
                    if invalid_char:
                        continue
                    meaning["stress_marks"] = stress_marks
                    parsed_text[word][list_index] = meaning
                    save_required = True
                    break
            else:
                edit_key = editable_word_keys[int(num_input)-1]
                edit_input = None
                if edit_key == "base":
                    suggestions, _ = search_word_index(word, base=meaning.get("base", ""),
                                                       search_keys=["base"],
                                                       include=[word])
                    edit_input = get_user_suggestion(suggestions, "base")
                    if not edit_input:
                        continue
                elif edit_key == "base_translation":
                    suggestions, _ = search_word_index(
                        word,
                        base=meaning.get("base", ""),
                        type=meaning.get("type", ""),
                        search_keys=["base_translation"],
                        include=[meaning.get("translation", None)]
                    )
                    if suggestions:
                        edit_input = get_user_suggestion(suggestions, "base_translation")
                        if not edit_input:
                            continue
                elif edit_key == "alt_representation":
                    suggestions, _ = search_word_index(word, base=meaning.get("base", ""),
                                                       search_keys=["alt_representation", "special_alt_rep"],
                                                       include=[word])
                    edit_input = get_user_suggestion(suggestions, "alt_representation")
                    if not edit_input:
                        continue
                elif edit_key == "translation":
                    suggestions, _ = search_word_index(word, base=meaning.get("base", ""))
                    if suggestions:
                        edit_input = get_user_suggestion(suggestions, "translation")
                        if not edit_input:
                            continue
                elif edit_key == "type":
                    suggestions, _ = search_word_index(word, base=meaning.get("base", ""), search_keys=["type"])
                    if suggestions:
                        edit_input = get_user_suggestion(suggestions, "type")
                        if not edit_input:
                            continue
                if not edit_input:
                    edit_input = input(f"Enter a new value for {Fore.GREEN + edit_key + Style.RESET_ALL}: ").lower()
                if edit_key == "type":
                    edit_input = unabbrev_wordtype(edit_input)
                elif edit_key == "base" and edit_input in copy_string:
                    edit_input = word
                elif edit_key == "base_translation" and edit_input in copy_string:
                    edit_input = meaning.get("translation", "")
                elif edit_key == "alt_representation" and edit_input in copy_string:
                    edit_input = word
                orig_val = meaning.get(edit_key, "<empty>")
                if orig_val in ["", False]:
                    orig_val = "<empty>"
                meaning[edit_key] = edit_input
                parsed_text[word][list_index] = meaning
                save_required = True
                edit_input = None

        if save_required:
            # clear the suggestions dictionary
            sugg_dict = {}

            # let's only backup a file once per session
            if not backup_present.get("hash", "") and not backup_text_words(hash, text_words_file):
                print(f"Word data cannot be saved since backup failed.")
            else:
                # Save the edits
                try:
                    with open(text_words_file, "w", encoding="utf-8") as f:
                        json.dump(parsed_text, f, indent=2)
                    glob_words_index_count -= 1
                    backup_present[hash] = True
                except (FileNotFoundError, json.JSONDecodeError) as e:
                    print(f"Error saving word data: {e}")
                    return False

        # this needs to stay in the main loop
        if glob_words_index_count <= 1:
            if not index_words(current_language):
                return False
            with open(os.path.join(words_dir, f"{current_language}_index.json"), 'r') as f:
                GLOBAL_WORD_INDEX = json.load(f)
            glob_words_index_count = default_words_index_count

        # keep this after the above save
        if save_and_cont:
            continue

        # keep this after the above save
        if save_and_exit:
            break

def get_user_suggestion(suggestions, fieldname):
    user_exit = False
    while True:
        print("  Suggestions:")
        for i, suggestion in enumerate(suggestions):
            print(f"    {i+1}) {Fore.BLUE + suggestion + Style.RESET_ALL}")
            max_i = i+1
        print(f'Or type in a new {Fore.GREEN + fieldname + Style.RESET_ALL} (q to exit): ', end="")
        user_translation = input(f"{gr_prompt} ")
        if user_translation in exit_letter:
            user_exit = True
            break
        num_input = False
        try:
            if 1 <= int(user_translation) <= max_i:
                num_input = True
            else:
                continue
        except ValueError:
            edit_input = user_translation
        if num_input:
            edit_input = suggestions[int(user_translation)-1]
        break
    if user_exit:
        return False
    return edit_input

def index_words(language):
    global GLOBAL_WORD_INDEX, glob_words_index_lang, glob_words_index_count

    if (GLOBAL_WORD_INDEX
        and glob_words_index_lang == language
        and glob_words_index_count > 1):
        # no need to reindex
        return True

    metadata = get_metadata()
    if not metadata:
        print("Error: no metadata found")
        return False

    word_index = {}
    language_found = False
    for text_hash, text_data in metadata.items():
        if text_data.get("language").lower() == language:
            language_found = True
            text_words_file = os.path.join(text_words_dir, current_language, f"{text_hash}.json")
            try:
                with open(text_words_file, 'r', encoding='utf-8') as f:
                    parsed_text = json.load(f)
            except FileNotFoundError:
                print(f"Error in {'_'.join('index', 'words')}(): Could not find text words file.")
                return False

            for word, word_data in parsed_text.items():
                for i, meaning in enumerate(word_data):
                    if meaning.get("skip", "") == True:
                        continue

                    i_index = meaning.get("index", -1)
                    i_type = meaning.get("type", "")
                    i_base = meaning.get("base", "")
                    i_translation = meaning.get("translation", "")
                    i_base_translation = meaning.get("base_translation", "")
                    i_alt_representation = meaning.get("alt_representation", "")
                    i_special_alt_rep = meaning.get("special_alt_rep", "")
                    orig_spec_alt_rep = i_special_alt_rep
                    i_stress_marks = meaning.get("stress_marks", "")

                    if (frequents and word in frequents and
                        not i_base and not i_translation and
                        not i_base_translation and not i_alt_representation and
                        not i_special_alt_rep and not i_stress_marks):
                        # skip new frequent words 90% of time.
                        # otherwise, they just clog up the index.
                        # they'll get in sooner or later :)
                        ten_nums = [i for i in range(10)]
                        random.shuffle(ten_nums)
                        if ten_nums[1] != 1:
                            continue

                    if word not in word_index:
                        word_index[word] = []

                    word_index[word].append({
                        "hash": text_hash,
                        "list_index": i,
                        "index": i_index,
                        "sent_inx": meaning.get("sent_inx", "")
                    })

                    if i_type:
                        i_type = abbrev_wordtype(i_type)
                        word_index[word][len(word_index[word])-1]["type"] = i_type
                    if i_base:
                        # if base is same as word, then store abbreviation value of "_w_" unless base is shorter
                        if i_base == word and len("_w_") < std_len(i_base):
                            i_base = "_w_"
                        word_index[word][len(word_index[word])-1]["base"] = i_base
                    if i_translation:
                        word_index[word][len(word_index[word])-1]["translation"] = i_translation
                    if i_base_translation:
                        # if base_translation is same as translation, then store abbreviation value of "_t_" unless base_translation is shorter
                        if i_base_translation == i_translation and len("_t_") < std_len(i_base_translation):
                            i_base_translation = "_t_"
                        word_index[word][len(word_index[word])-1]["base_translation"] = i_base_translation
                    if i_alt_representation:
                        # if alt_representation is same as word, then store abbreviation value of "_w_" unless alt_representation is shorter
                        if i_alt_representation == word and len("_w_") < std_len(i_alt_representation):
                            i_alt_representation = "_w_"
                        word_index[word][len(word_index[word])-1]["alt_representation"] = i_alt_representation
                    if i_special_alt_rep:
                        # if i_special_alt_rep is same as alt_representation, then store abbreviation value of "_a_" unless special_alt_rep is shorter
                        if i_special_alt_rep == i_alt_representation and len("_a_") < std_len(i_special_alt_rep):
                            i_special_alt_rep = "_a_"
                        # if i_special_alt_rep is same as word, then store abbreviation value of "_w_" unless special_alt_rep is shorter
                        elif i_special_alt_rep == word and len("_w_") < std_len(i_special_alt_rep):
                            i_special_alt_rep = "_w_"
                        word_index[word][len(word_index[word])-1]["special_alt_rep"] = i_special_alt_rep
                    if i_stress_marks:
                        word_index[word][len(word_index[word])-1]["stress_marks"] = i_stress_marks

                    if orig_spec_alt_rep and orig_spec_alt_rep != word:
                        if orig_spec_alt_rep not in word_index:
                            word_index[orig_spec_alt_rep] = []

                        word_index[orig_spec_alt_rep].append({
                            "word_ptr": word,
                            "hash": text_hash,
                            "index": i_index
                        })

    if not language_found:
        print(f"{language} not found in metadata file. Aborting.")
        return False
    if not word_index:
        print("No words found to index. Aborting.")
        return False
    os.makedirs(words_dir, exist_ok=True)
    with open(os.path.join(words_dir, f"{language}_index.json"), 'w') as f:
        json.dump(word_index, f, indent=2)
    GLOBAL_WORD_INDEX = word_index
    glob_words_index_lang = language
    glob_words_index_count = default_words_index_count
    return True

def validate_language(lang):
    try:
        langs_file = os.path.join(data_dir, "languages.json")
        #with open("languages.json", "r") as f:
        with open(langs_file, "r") as f:
            languages = json.load(f)
    except FileNotFoundError:
        print("No languages.json file found.")
        return False
    try:
        languages[lang]
        return True
    except KeyError:
        print("Language not found in languages.json")
        return False

def get_langdata(lang, user_friendly=False, quiet=False):
    global sent_delims, sent_post_delims, word_delims
    global alt_representation_required, ignore_spaces_in_rev_study
    global underscore, edit_inputs, yes_letter, exit_letter, all_letter
    global no_letter, copy_quotes, copy_string, alphabet, current_language
    global frequents

    set_lang_defaults()

    lang_code = None
    lang_data = {}
    uf_lang_data = {}
    try:
        langs_file = os.path.join(data_dir, "languages.json")
        #with open("languages.json", "r") as f:
        with open(langs_file, "r") as f:
            languages = json.load(f)
    except FileNotFoundError:
        languages = {}
        print("No languages.json file found.")
        return False, False

    sent_delims = default_sent_delims
    sent_post_delims = default_sent_post_delims
    word_delims = default_word_delims
    alt_representation_required = default_alt_representation_required
    ignore_spaces_in_rev_study = default_ignore_spaces_in_rev_study
    underscore = default_underscore
    edit_inputs = default_edit_inputs
    copy_string = default_copy_string
    copy_quotes = default_copy_quotes
    yes_letter = default_yes_letter
    no_letter = default_no_letter
    exit_letter = default_exit_letter
    all_letter = default_all_letter
    alphabet = default_alphabet
    frequents = default_frequents

    try:
        if type(languages[lang]) is dict:
            lang_data = languages[lang]
            lang_code = lang_data["lang_code"]

            if user_friendly:
                uf_lang_data["sent_delims"] = sent_delims
                if "uf_sent_delims" in lang_data:
                    uf_lang_data["sent_delims"] += lang_data["uf_sent_delims"]
            if "sent_delims" in lang_data:
                sent_delims += lang_data["sent_delims"]

            if user_friendly:
                uf_lang_data["sent_post_delims"] = sent_post_delims
                if "uf_sent_post_delims" in lang_data:
                    uf_lang_data["sent_post_delims"] += lang_data["uf_sent_post_delims"]
            if "sent_post_delims" in lang_data:
                sent_post_delims += lang_data["sent_post_delims"]

            if "word_delims" in lang_data:
                word_delims += lang_data["word_delims"]
            if user_friendly:
                uf_lang_data["word_delims"] = word_delims

            if "alt_representation_required" in lang_data:
                alt_representation_required = lang_data["alt_representation_required"]
            if user_friendly:
                uf_lang_data["alt_representation_required"] = alt_representation_required

            if "ignore_spaces_in_rev_study" in lang_data:
                ignore_spaces_in_rev_study = lang_data["ignore_spaces_in_rev_study"]
            if user_friendly:
                uf_lang_data["ignore_spaces_in_rev_study"] = ignore_spaces_in_rev_study

            if "underscore" in lang_data:
                underscore = lang_data["underscore"]
            if user_friendly:
                uf_lang_data["underscore"] = underscore

            if "alphabet" in lang_data:
                alphabet = lang_data["alphabet"]

            if "frequents" in lang_data:
                frequents = lang_data["frequents"]

            if "copy_quotes" in lang_data:
                copy_quotes = lang_data["copy_quotes"]

            if "edit_inputs" in lang_data:
                edit_inputs = edit_inputs | lang_data["edit_inputs"]

            if "copy_string" in lang_data:
                # TODO change to + as below
                copy_string.append(lang_data["copy_string"])

            if "yes_letter" in lang_data:
                yes_letter = yes_letter + lang_data["yes_letter"]
                #yes_letter.append(lang_data["yes_letter"])

            if "no_letter" in lang_data:
                # TODO change to + as above
                no_letter.append(lang_data["no_letter"])

            if "exit_letter" in lang_data:
                # TODO change to + as above
                exit_letter.append(lang_data["exit_letter"])

            if "all_letter" in lang_data:
                # TODO change to + as above
                all_letter.append(lang_data["all_letter"])
        else:
            lang_code = languages[lang]
        current_language = lang
    except KeyError:
        if not quiet:
            print("Language not found in languages.json file.")
        return False, False

    if user_friendly:
        return uf_lang_data
    else:
        return lang_code, lang_data

def get_matching_hash(hash_substring):

    ensure_text_hashes_populated()
    matching_hashes = [h for h in text_hashes if h.startswith(hash_substring)]

    if len(matching_hashes) == 0:
        print(f"No text found with hash substring '{hash_substring}'.")
        return False

    if len(matching_hashes) > 1:
        print(f"Multiple texts found with hash substring '{hash_substring}'. Please provide a more specific substring.")
        return False

    return matching_hashes[0]

def parse_sentences(full_hash):

    text_filepath = os.path.join(texts_dir, current_language, full_hash + ".txt")
    sent_dir = os.path.join(text_sents_dir, current_language)
    sent_filepath = os.path.join(sent_dir, full_hash + ".json")

    try:
        with open(text_filepath, "r", encoding="utf-8") as f:
            text = f.read()
    except FileNotFoundError:
        print(f"Error: text file '{text_filepath}' not found.")
        return False

    metadata = get_metadata(full_hash)
    lang = metadata["language"].lower()
    if lang:
        _, _ = get_langdata(lang)

    sent_data = []

    # Split the text into sentences
    sentences = text.split("\n")

    for sentence in sentences:
        if sentence:
            sent_data.append(normalize_sentence(sentence))

    try:
        os.makedirs(sent_dir, exist_ok=True)
        with open(sent_filepath, "w", encoding="utf-8") as f:
            json.dump(sent_data, f, indent=2)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"Error processing text: {e}")
        return False

    return True

def parse_text(full_hash):

    text_filepath = os.path.join(texts_dir, current_language, full_hash + ".txt")
    word_filepath = os.path.join(text_words_dir, current_language, full_hash + ".json")
    sent_filepath = os.path.join(text_sents_dir, current_language, full_hash + ".json")

    try:
        with open(sent_filepath, "r", encoding="utf-8") as f:
            sentences = json.load(f)
    except FileNotFoundError:
        print(f"Error: Sentence file '{sent_filepath}' not found.")
        return False

    try:
        with open(text_filepath, "r", encoding="utf-8") as f:
            pass
    except FileNotFoundError:
        print(f"Error: text file '{text_filepath}' not found.")
        return False

    # Create a dictionary to store word data
    word_data = {}

    metadata = get_metadata(full_hash)
    lang = metadata["language"].lower()
    if lang:
        _, _ = get_langdata(lang)

    # Process each sentence
    for sent_inx, sentence in enumerate(sentences):

        sentence = normalize_sentence(sentence)
        words = sentence.split()

        for i, word in enumerate(words):
            skip = False
            bkp_word = word
            word = normalize_word(word)
            if not word:
                # This means that normalizing removed all characters, so the "word" was comprised only of delimiters.
                # For the sake of accurate word-indexing, we'll add this "word" but with "skip: True".
                word = bkp_word
                skip = True
            if word not in word_data:
                word_data[word] = []
            word_data[word].append({"internal_type": "word",
                                    "type": "",
                                    "translation": "",
                                    "sent_inx": sent_inx,
                                    "skip": skip,
                                    "index": i})

    text_sents_file = os.path.join(text_sents_dir, current_language, f"{full_hash}.json")
    text_sents_list = None
    try:
        with open(text_sents_file, 'r', encoding='utf-8') as f:
            text_sents_list = json.load(f)
    except FileNotFoundError:
        err_msg = "Error in {}: {} not found."
        print(err_msg.format("_".join(["parse","text"]), text_sents_file))
        return False

    # Load existing word data if it exists
    try:
        with open(word_filepath, "r", encoding="utf-8") as f:
            parsed_data = json.load(f)
        for word, meanings in parsed_data.items():
            if word not in word_data:
                # Add phrase data directly
                if meanings[0]["internal_type"] == "phrase":
                    word_data[word] = meanings
                continue
            for existing_meaning in meanings:
                for i, meaning in enumerate(word_data[word]):
                    if text_sents_list:
                        the_sent = text_sents_list[meaning["sent_inx"]]
                    else:
                        the_sent = meaning["sentence"]
                    if existing_meaning["index"] == meaning["index"] and existing_meaning["sentence"] == the_sent:
                        word_data[word][i].update({k: v for k, v in existing_meaning.items() if k != "sentence"})
                        break

    except FileNotFoundError:
        pass  # File doesn't exist, continue

    # Save word data to JSON file
    try:
        word_dirpath = os.path.join(text_words_dir, current_language)
        os.makedirs(word_dirpath, exist_ok=True)
        with open(word_filepath, "w", encoding="utf-8") as f:
            json.dump(word_data, f, indent=2)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"Error processing text: {e}")
        return False

    #if not index_words(lang):
        #return False
    return True

def help(more=False):
  """Displays a list of available commands."""
  if not more:
      print("Try these commands:")
      print("  > list          (this shows all texts available for study)")
      print("  > study 12435   (this allows you to study the text with hash 12435)")
      print("  > edit 12435    (this allows you to add meanings and other data to the text with hash 12435)")
      print("  > edit japanese (this allows you to add meanings and other data to any Japanese words, etc.)")
      print()
      return

  print("Available commands:")
  for command in valid_commands:
      print(f"  - {command}")

def encoder(unicode_string):
    return unicode_string.encode("unicode-escape")

def decoder(text):
    try:
        return bytes(text, 'utf8').decode('unicode-escape')
    except UnicodeDecodeError:
        print("Invalid Unicode escape sequence.")
        return text

def map_input(foreign_word, lang_map):
  word = ""
  for foreign_letter in foreign_word:
    letter = lang_map.get(foreign_letter.lower(), foreign_letter)
    word += letter
  return word

def set_lang_defaults():
    global sent_delims, sent_post_delims, word_delims
    global alt_representation_required, ignore_spaces_in_rev_study
    global underscore, edit_inputs, yes_letter, exit_letter, all_letter
    global no_letter, copy_quotes, copy_string, alphabet
    global frequents

    sent_delims = default_sent_delims
    sent_post_delims = default_sent_post_delims
    word_delims = default_word_delims
    alt_representation_required = default_alt_representation_required
    ignore_spaces_in_rev_study = default_ignore_spaces_in_rev_study
    underscore = default_underscore
    edit_inputs = default_edit_inputs
    copy_quotes = default_copy_quotes
    copy_string = default_copy_string
    yes_letter = default_yes_letter
    no_letter = default_no_letter
    exit_letter = default_exit_letter
    all_letter = default_all_letter
    alphabet = default_alphabet
    frequents = default_frequents

def add_stress(word, stresses, stress_colours={"bg": Back.BLUE, "fg": Fore.YELLOW}, norm_colours={"fg": Fore.BLUE}):
    if not stresses:
        return f'{norm_colours["fg"] + word + Style.RESET_ALL}'

    stresses = stresses.split(",")
    stressed_word = ""
    for j, w in enumerate(word):
        if str(j+1) in stresses:
            bg_clr = stress_colours["bg"] if "bg" in stress_colours else ""
            fg_clr = stress_colours["fg"] if "fg" in stress_colours else ""
            stressed_word += f"{bg_clr + fg_clr + w + Style.RESET_ALL}"
        else:
            bg = norm_colours["bg"] if "bg" in norm_colours else ""
            stressed_word += f'{bg + norm_colours["fg"] + w + Style.RESET_ALL}'
    return stressed_word

def build_word_heading(word, word_data, rev_study=False):

    head_alt_clr = Fore.BLACK
    head_type_clr = Fore.BLACK
    head_samebase_clr = Fore.BLACK
    head_word_clr = {
        "reg": {"fg": Fore.BLUE},
        "stress": {"fg": Fore.WHITE, "bg": Back.BLUE}
    }

    if rev_study:
        translation = word_data.get("translation")
        trans_list = translation.split(",")
        trans_set = set(trans_list)
        trans_output = ", ".join(trans_list)
        word_heading = Fore.BLUE + trans_output + Style.RESET_ALL

        base_translation = ""
        base_output = None
        if "base_translation" in word_data and word_data.get("base_translation", "") != "":
            base_translation = word_data.get("base_translation")
            base_list = base_translation.split(",")
            base_set = set(base_list)
            base_output = ", ".join(base_list)

        if base_translation and base_output and base_set != trans_set:
           word_heading += f" {Fore.BLACK}[{base_output}]{Style.RESET_ALL}"

        short_heading = None

    else:
        base_word = ""
        if "base" in word_data and word_data.get("base", "") != "":
            base_word = word_data.get("base")

        spec_alt_rep = ""
        if "special_alt_rep" in word_data and word_data.get("special_alt_rep", "") != "":
            spec_alt_rep = word_data.get("special_alt_rep")

        alt_rep = ""
        if "alt_representation" in word_data and word_data.get("alt_representation", "") != "":
            alt_rep = word_data.get("alt_representation")
            if spec_alt_rep:
                alt_reps = alt_rep.split(",")
                alt_reps = [ar for ar in alt_reps if ar != spec_alt_rep]
                alt_rep = ",".join(alt_reps)

        if word == spec_alt_rep or not alt_representation_required:
            word_heading = add_stress(
                word,
                word_data.get("stress_marks", ""),
                stress_colours=head_word_clr["stress"],
                norm_colours={"fg": head_word_clr["reg"]["fg"]}
            )
        else:
            word_heading = head_word_clr["reg"]["fg"] + word + Style.RESET_ALL

        short_heading = word_heading

        if spec_alt_rep and spec_alt_rep != word:
            spec_stress = add_stress(
                spec_alt_rep,
                word_data.get("stress_marks", ""),
                norm_colours={"fg": Fore.CYAN}
            )
            word_heading += f" ({spec_stress})"

        if base_word and base_word != word:
            if not spec_alt_rep and not alt_rep:
                base_color = Fore.CYAN
            else:
                base_color = Fore.BLUE
            word_heading += f" ({base_color + base_word + Style.RESET_ALL})"
        elif base_word:
            word_heading = f"{head_samebase_clr}(b){Style.RESET_ALL} " + word_heading

        if alt_rep and alt_rep != word:
            word_heading += f" {head_alt_clr}({alt_rep}){Style.RESET_ALL}"

    if "type" in word_data and word_data.get("type", "") != "":
        word_heading += f' {head_type_clr}({word_data.get("type")}){Style.RESET_ALL}'

    label = []
    if "tags" in word_data and word_data.get("tags", "") != "":
        label.append("*tags")
    if "note" in word_data and word_data.get("note", "") != "":
        label.append("*note")
    if label:
        word_heading += " (" + " ".join(label) + ")"

    return word_heading, short_heading

#def get_singular(plural):
    #poss_sing = []
    #plurals = plural.split(",")
    #for plural in plurals:
        #if len(plural) > 4 and (plural[-4:] in ["ches", "shes"] or plural[-3:] in ["ses", "xes", "oes"]):
            #poss_sing.append(plural[:-2])
            #if plural[-3:] == "ses":
                #poss_sing.append(plural[:-2])
        #elif len(plural) > 4 and plural[-4:] == "zzes":
            #poss_sing.append(plural[:-3])
        #elif len(plural) > 2 and plural[-1:] == "s" and plural[-2:] != "ss":
            #poss_sing.append(plural[:-1])
    #if len(poss_sing) > 1:
        #poss_sing.append(",".join(poss_sing))
    #return poss_sing

# TODO - have IPA symbols as an option and an IPA helper with native words that use displayed symbols
# TODO - old-fashioned terminal app (not CLI) possible? (ratatui?)
#def get_infinitive(verb):
    ## if "to" or "(to)" already at start, return None
    #if verb[:4] == "(to)" or verb[:3] == "to ":
        #return [verb]

    #poss_infs = []
    #infs_set = set()
    #verbs = verb.split(",")
    #for verb in verbs:
        #infs_set.add("(to) " + verb)
        #if verb[-1:] in ['s', 'd']:
            #infs_set.add("(to) " + verb[:-1])
        #if verb[-2:] in ['es', 'ed']:
            #infs_set.add("(to) " + verb[:-2])
        #if verb[-2:] == "ed" and verb[-3] == verb[-4]:
            #infs_set.add("(to) " + verb[:-3])
    #for inf in infs_set:
        #if inf.strip() != "(to)":
            #poss_infs.append(inf)
    #return poss_infs
    # "moves"   => -s   => "(to) move"
    # "reaches" => -es  => "(to) reach"
    # "moved"   => -d   => "(to) move"
    # "treated" => -ed  => "(to) treat"
    # "tapped"  => -ped => "(to) tap"

def search_word_index(word,
                      base=None,
                      type=None,
                      search_keys=["translation", "base_translation"],
                      sub_search_keys=[],
                      match_keys={},
                      return_one=False,
                      include=[]):

    global GLOBAL_WORD_INDEX

    rule_mgr = RulesManager(rules_dir=rules_dir)

    suggestions = set()
    sugg_dict = {}
    cnt_dict = {}

    if include:
        for inc in include:
            suggestions.add(inc)
            cnt_dict[inc] = 1 if not cnt_dict.get(inc, "") else cnt_dict[inc]+1
            # try to determine infinitive verb if we think we have a simple past/present verb
            if type in ["verb", "suru verb"] and search_keys == ["base_translation"]:
                pos_inf = rule_mgr.infinitivize(inc, "english")
                #pos_inf = get_infinitive(inc)
                for inf in pos_inf:
                    suggestions.add(inf)
                    cnt_dict[inf] = 1 if not cnt_dict.get(inf, "") else cnt_dict[inf]+1
            # try to determine singular noun if we think we have a regular plural noun
            if type == "noun" and search_keys == ["base_translation"]:
                pos_sing = rule_mgr.singularize(inc, "english")
                #suggestions.add("rule_mgr 3")
                #pos_sing = get_singular(inc)
                for sing in pos_sing:
                    suggestions.add(sing)
                    cnt_dict[sing] = 1 if not cnt_dict.get(sing, "") else cnt_dict[sing]+1

    while True:
        if word in GLOBAL_WORD_INDEX:
            index_entry = GLOBAL_WORD_INDEX[word]
            rewrite_skey = False
            for meaning in index_entry:
                for skey in search_keys:
                    if match_keys:
                        nomatch = False
                        for key, val in match_keys.items():
                            meaning_value = meaning.get(key, "")
                            if key == "type":
                                meaning_value = unabbrev_wordtype(meaning_value)
                            elif meaning_value == "_w_":
                                meaning_value = word
                            elif meaning_value == "_t_":
                                meaning_value = meaning.get("translation", "")
                            elif meaning_value == "_a_":
                                meaning_value = meaning.get("alt_representation", "")
                            if meaning_value != val:
                                nomatch = True
                                break
                        if skey == "word_ptr":
                            if meaning.get("word_ptr", "") == "":
                                nomatch = True
                        if not nomatch and skey == "word_ptr":
                            word = meaning.get("word_ptr")
                            rewrite_skey = True
                        elif not nomatch:
                            new_sugg = meaning.get(skey, "")
                            if skey == "type":
                                new_sugg = unabbrev_wordtype(new_sugg)
                            elif new_sugg == "_w_":
                                new_sugg = word
                            elif new_sugg == "_t_":
                                new_sugg = meaning.get("translation", "")
                            elif new_sugg == "_a_":
                                new_sugg = meaning.get("alt_representation", "")
                            if new_sugg != "":
                                sugg_dict.setdefault(skey, []).append(new_sugg)
                                suggestions.add(new_sugg)
                                cnt_dict[new_sugg] = 1 if not cnt_dict.get(new_sugg, "") else cnt_dict[new_sugg] + 1
                                if type in ["verb", "suru verb"] and search_keys == ["base_translation"]:
                                    pos_inf = rule_mgr.infinitivize(new_sugg, "english")
                                    #pos_inf = get_infinitive(new_sugg)
                                    for inf in pos_inf:
                                        suggestions.add(inf)
                                        cnt_dict[inf] = 1 if not cnt_dict.get(inf, "") else cnt_dict[inf]+1
                                if type == "noun" and search_keys == ["base_translation"]:
                                    pos_sing = rule_mgr.singularize(new_sugg, "english")
                                    #suggestions.add("rule_mgr 2")
                                    #pos_sing = get_singular(new_sugg)
                                    for sing in pos_sing:
                                        suggestions.add(sing)
                                        cnt_dict[sing] = 1 if not cnt_dict.get(sing, "") else cnt_dict[sing]+1
                    else:
                        new_sugg = meaning.get(skey, "")
                        if skey == "type":
                            new_sugg = unabbrev_wordtype(new_sugg)
                        elif new_sugg == "_w_":
                            new_sugg = word
                        elif new_sugg == "_t_":
                            new_sugg = meaning.get("translation", "")
                        elif new_sugg == "_a_":
                            new_sugg = meaning.get("alt_representation", "")
                        if new_sugg != "":
                            sugg_dict.setdefault(skey, []).append(new_sugg)
                            suggestions.add(new_sugg)
                            cnt_dict[new_sugg] = 1 if not cnt_dict.get(new_sugg, "") else cnt_dict[new_sugg] + 1
                            if type in ["verb", "suru verb"] and search_keys == ["base_translation"]:
                                pos_inf = rule_mgr.infinitivize(new_sugg, "english")
                                #pos_inf = get_infinitive(new_sugg)
                                for inf in pos_inf:
                                    suggestions.add(inf)
                                    cnt_dict[inf] = 1 if not cnt_dict.get(inf, "") else cnt_dict[inf]+1
                            if type == "noun" and search_keys == ["base_translation"]:
                                pos_sing = rule_mgr.singularize(new_sugg, "english")
                                #suggestions.add("rule_mgr 1")
                                #pos_sing = get_singular(new_sugg)
                                for sing in pos_sing:
                                    suggestions.add(sing)
                                    cnt_dict[sing] = 1 if not cnt_dict.get(sing, "") else cnt_dict[sing]+1
                    if rewrite_skey:
                        break
                if rewrite_skey:
                    search_keys = sub_search_keys
                    break
            if not rewrite_skey:
                break
        else:
            break

    # TODO if we're looking for "base" suggestions,
    #      these should probably come first
    # TODO to make this really useful, index the base entry as we do the spec_alt_rep
    #      with pointers. but only if not already exists?

    if base and word != base and base != "" and base in GLOBAL_WORD_INDEX:
        base_entry = GLOBAL_WORD_INDEX[base]
        for meaning in base_entry:
            for skey in search_keys:
                if match_keys:
                    for key, val in match_keys.items():
                        the_val = meaning.get(key, "")
                        if key == "type":
                            the_val = unabbrev_wordtype(the_val)
                        elif the_val == "_w_":
                            the_val = base
                        elif the_val == "_t_":
                            the_val = meaning.get("translation", "")
                        elif the_val == "_a_":
                            the_val = meaning.get("alt_representation", "")
                        if the_val != val:
                            break
                        new_sugg = meaning.get(skey, "")
                        if new_sugg:
                            if skey == "type":
                                new_sugg = unabbrev_wordtype(new_sugg)
                            elif new_sugg == "_w_":
                                new_sugg = base
                            elif new_sugg == "_t_":
                                new_sugg = meaning.get("translation", "")
                            elif new_sugg == "_a_":
                                new_sugg = meaning.get("alt_representation", "")
                        suggestions.add(new_sugg)
                        cnt_dict[new_sugg] = 1 if not cnt_dict.get(new_sugg, "") else cnt_dict[new_sugg] + 1
                        if type in ["verb", "suru verb"] and search_keys == ["base_translation"]:
                            pos_inf = rule_mgr.infinitivize(new_sugg, "english")
                            #pos_inf = get_infinitive(new_sugg)
                            for inf in pos_inf:
                                suggestions.add(inf)
                                cnt_dict[inf] = 1 if not cnt_dict.get(inf, "") else cnt_dict[inf]+1
                        if type == "noun" and search_keys == ["base_translation"]:
                            pos_sing = rule_mgr.singularize(new_sugg, "english")
                            #suggestions.add("rule_mgr 4")
                            #pos_sing = get_singular(new_sugg)
                            for sing in pos_sing:
                                suggestions.add(sing)
                                cnt_dict[sing] = 1 if not cnt_dict.get(sing, "") else cnt_dict[sing]+1
                else:
                    new_sugg = meaning.get(skey, "")
                    if new_sugg:
                        if skey == "type":
                            new_sugg = unabbrev_wordtype(new_sugg)
                        elif new_sugg == "_w_":
                            new_sugg = base
                        elif new_sugg == "_t_":
                            new_sugg = meaning.get("translation", "")
                        elif new_sugg == "_a_":
                            new_sugg = meaning.get("alt_representation", "")
                    suggestions.add(new_sugg)
                    cnt_dict[new_sugg] = 1 if not cnt_dict.get(new_sugg, "") else cnt_dict[new_sugg] + 1
                    if type in ["verb", "suru verb"] and search_keys == ["base_translation"]:
                        pos_inf = rule_mgr.infinitivize(new_sugg, "english")
                        #pos_inf = get_infinitive(new_sugg)
                        for inf in pos_inf:
                            suggestions.add(inf)
                            cnt_dict[inf] = 1 if not cnt_dict.get(inf, "") else cnt_dict[inf]+1
                    if type == "noun" and search_keys == ["base_translation"]:
                        pos_sing = rule_mgr.singularize(new_sugg, "english")
                        #suggestions.add("rule_mgr 5")
                        #pos_sing = get_singular(new_sugg)
                        for sing in pos_sing:
                            suggestions.add(sing)
                            cnt_dict[sing] = 1 if not cnt_dict.get(sing, "") else cnt_dict[sing]+1

    suggestions.discard("")

    if suggestions:
        suggestions = sorted(list(suggestions), key=cnt_dict.get, reverse=True)
        if return_one:
            suggestions = suggestions[0]
    else:
        suggestions = []
        if return_one:
            suggestions = None
    # TODO I think we're meant to move everything to the new sugg_dict format
    return suggestions, sugg_dict

def colour_sentence(sentence, word, indices,
                    orig_sent=None,
                    rev_study=False,
                    colors=None,
                    bg_clr=Back.WHITE,
                    word_delim=None,
                    space_char=" ",
                    add_stress_marks=True,
                    phrase_space_char=" "):

    global current_hash

    if not word_delim:
        word_delim = format_delim_word

    if not colors:
        colors=[Fore.WHITE, Fore.BLUE]
    norm_clr = colors[0]
    hili_clr = colors[1]

    # Split the sentence into a list of words
    words_in_sentence = sentence.split(word_delim)

    # Construct the colored sentence
    colored_sentence = ""
    match_keys = {"hash": current_hash}
    for i, w in enumerate(words_in_sentence):
        word_colored = False
        w = w.replace(format_delim_phrase, phrase_space_char)
        match_keys["index"] = i
        if alt_representation_required:
            match_keys["special_alt_rep"] = w.replace(phrase_space_char, " ").strip().strip(word_delims).lower()
        for j in indices:
            # "i" in this range means we've found the word being studied
            if j <= i < (j + len(word.split())):
                if rev_study:
                    bare_word = w.strip().strip(word_delims)
                    unsc_word = "_" * len(bare_word)
                    w = w.replace(bare_word, unsc_word)
                    colored_sentence += hili_clr + w + Style.RESET_ALL + space_char
                else:
                    stress_marks, _ = search_word_index(word, match_keys=match_keys, search_keys=["stress_marks"])
                    if stress_marks == "(none)":
                        stress_marks = None
                    bare_word = w.replace(phrase_space_char, " ").strip().strip(word_delims)
                    if stress_marks and add_stress_marks:
                        stressed_word = add_stress(bare_word,
                                                   stress_marks[0],
                                                   stress_colours={"fg": Fore.LIGHTCYAN_EX},
                                                   norm_colours={"fg": norm_clr})
                        colored_sentence += w.replace(bare_word, stressed_word) + space_char
                    else:
                        clr_word = hili_clr + bg_clr + bare_word + Style.RESET_ALL
                        colored_sentence += w.replace(bare_word, clr_word) + space_char
                word_colored = True

        # If this is some other word in the sentence
        if not word_colored:

            bare_word = w.replace(phrase_space_char, " ").strip().strip(word_delims)
            stressed_word = None
            _, results_dict = search_word_index(
                bare_word.lower(),
                match_keys=match_keys,
                search_keys=["stress_marks", "translation", "skip"]
            )

            if add_stress_marks:
                stress_marks = results_dict.get("stress_marks", None)
                if not stress_marks:
                    ptr_match_keys = {"hash": current_hash, "index": i}
                    stress_marks, _ = search_word_index(
                        bare_word.lower(),
                        match_keys=ptr_match_keys,
                        search_keys=["word_ptr"],
                        sub_search_keys=["stress_marks"]
                    )

                if stress_marks == "(none)":
                    stress_marks = None
                if stress_marks:
                    stressed_word = add_stress(
                        bare_word,
                        stress_marks[0],
                        stress_colours={"fg": Fore.LIGHTCYAN_EX},
                        norm_colours={"fg": Fore.WHITE}
                    )
                if stressed_word:
                    clr_word = stressed_word
                else:
                    clr_word = norm_clr + bare_word + Style.RESET_ALL
                colored_sentence += w.replace(bare_word, clr_word) + space_char
            else:
                clr = norm_clr
                if orig_sent:
                    orig_words = orig_sent.split(format_delim_word)
                    if w.lower() != orig_words[i].lower():
                        clr = hili_clr
                clr_word = clr + bare_word + Style.RESET_ALL
                colored_sentence += w.replace(bare_word, clr_word) + space_char
    colored_sentence = colored_sentence[:-1] + Style.RESET_ALL
    return colored_sentence

def set_metadata(requested_hash, edit_dict):
    # TODO get_metadata can take a hash param; so do that
    existing_metadata = get_metadata()
    if not existing_metadata:
        print(f"{Fore.RED}Could not retrieve existing metadata. Save aborted!{Style.RESET_ALL}")
        return False
    updated_metadata = {}
    for hash, metadata in existing_metadata.items():
        if hash != requested_hash:
            updated_metadata[hash] = metadata
            continue
        for key, value in edit_dict.items():
            if key == "last_study_date" and value:
                metadata["last_study_date"] = value

            # get current val and add 1, or set to 1 if not exist
            elif key == "study_count_up" and value:
                try:
                    if "study_count" in metadata and int(metadata["study_count"]):
                        metadata["study_count"] = int(metadata["study_count"]) + 1
                    else:
                        metadata["study_count"] = 1
                except ValueError:
                    metadata["study_count"] = 1

            else:
                metadata[key] = value
        updated_metadata[hash] = metadata

    if not backup_metadata():
        print(f"Metadata cannot be saved since backup failed.")
        return False

    #metadata_path = "metadata.json"
    with open(metadata_path, "w") as f:
        json.dump(updated_metadata, f, indent=2)
    return True

def edit_metadata(hash_substring):
    full_hash = get_matching_hash(hash_substring)
    if not full_hash:
        return False

    # TODO this needs to fix metadata for any linked texts
    fix_metadata(hash_substring, quiet=True)

    editable_keys = ["url", "title", "type", "fulltext", "label", "tag", "hidden"]
    readonly_keys = ["timestamp", ("num_words", "num_uniq_words"), ("language", "lang_code"), ("last_study_date", "study_count")]
    print(full_hash)
    while True:
        metadata = get_metadata(full_hash)
        save_dict = {}
        max_i = None
        for i, key in enumerate(editable_keys):
            max_i = i+1
            print(f"{i+1}) {key}: ", end="")
            md_val = metadata.get(key, None)
            if md_val == None:
                md_val = Fore.RED + "<empty>" + Style.RESET_ALL
            else:
                md_val = Fore.GREEN + str(md_val) + Style.RESET_ALL
            print(md_val)
        for key in readonly_keys:
            if type(key) == tuple:
                print(f'-) {key[0]}: {Fore.BLACK}{metadata[key[0]] if key[0] in metadata else "<empty>"}{Style.RESET_ALL}', end="")
                print(f', {key[1]}: {Fore.BLACK}{metadata[key[1]] if key[1] in metadata else "<empty>"}{Style.RESET_ALL}')
            else:
                print(f"-) {key}: ", end="")
                print(f'{Fore.BLACK}{metadata[key] if key in metadata else "<empty>"}{Style.RESET_ALL}')

        valid_option = False
        while not valid_option:
            user_input = input("Enter a valid option (or q to exit): ").lower()
            if user_input == 'q':
                valid_option = True
            else:
                try:
                    if 1 <= int(user_input) <= max_i:
                        new_val = input(f"Enter new value for '{editable_keys[int(user_input)-1]}': ")
                        valid_option = True
                except ValueError:
                    pass
        if user_input == 'q':
            break

        print(f"Changing {Fore.GREEN + editable_keys[int(user_input)-1] + Style.RESET_ALL} from {md_val} to {Fore.GREEN + new_val + Style.RESET_ALL}")
        confirmation = input("Please confirm (y/n): ")
        if confirmation.lower() == "y":
            if editable_keys[int(user_input)-1] == "fulltext":
                if new_val == "true":
                    new_val = True
                else:
                    new_val = False
            save_dict[editable_keys[int(user_input)-1]] = new_val
            metadata[editable_keys[int(user_input)-1]] = new_val
            user_input = None
            new_val = None
            if not set_metadata(full_hash, save_dict):
                return False
            print(f"{Fore.GREEN}New metadata updated successfully.,{Style.RESET_ALL}")
        else:
            print(Fore.RED + "Change aborted!" + Style.RESET_ALL)

def study(hash_substring=None, rev_study=False, lang_map=None):

    import pyperclip

    global current_hash, GLOBAL_WORD_INDEX, glob_words_index_lang, glob_words_index_count

    backup_present = {}
    hash_list = []
    language = current_language
    if hash_substring:
        full_hash = get_matching_hash(hash_substring)
        if not full_hash:
            return False
        metadata = get_metadata(full_hash)

        hash_list.append(full_hash)
        while True:
            next_hash = metadata.get("next_hash", None)
            if next_hash:
                hash_list.append(next_hash)
                metadata = get_metadata(next_hash)
            else:
                break

    if not index_words(language):
        return False
    #if (not GLOBAL_WORD_INDEX
        #or glob_words_index_lang != language
        #or glob_words_index_count <= 1):
        #if not index_words(language):
            #return False
        #with open(os.path.join(words_dir, f"{language}_index.json"), 'r') as f:
            #GLOBAL_WORD_INDEX = json.load(f)
        #glob_words_index_lang = language
        #glob_words_index_count = default_words_index_count

    all_words_dict = get_word_data(
        hash_list=hash_list,
        randomize=True,
        exclude_filters={"translation": ""},
        alt=True
    )
    all_words = all_words_dict["all_words"]
    all_hashes = all_words_dict["all_hashes"]
    all_list_inxs = all_words_dict["all_list_inxs"]
    #all_word_inxs = all_words_dict["all_word_inxs"]
    #all_sent_inxs = all_words_dict["all_sent_inxs"]

    #all_words, all_hashes, all_list_inxs, _, _ = get_word_hash_inx_list(
        #hash_list=hash_list,
        #randomize=True,
        #exclude_filters={"translation": ""}
    #)

    if not all_words:
        print("No translations found. Please edit the text or the language.")
        return True

    editable_word_keys = ["type", "translation", "base", "base_translation", "tags", "note"]
    #readonly_word_keys = ["internal_type", "index"]
    if alt_representation_required:
        editable_word_keys.append("alt_representation")

    words_studied = {}
    for hash in set(all_hashes):
        words_studied[hash] = 0

    if IS_DEV_MODE:
        print(f"{Fore.RED}[DEV-DATA]{Style.RESET_ALL}")
    print(f"{Fore.BLUE}If you're stumped, press '.' and enter to get a hint.{Style.RESET_ALL}")
    skip_word = False
    next_word = False
    dupes_to_skip = []
    last_hash = None
    for word, full_hash, index in zip(all_words, all_hashes, all_list_inxs):

        current_hash = full_hash

        _, native_sentences, alt_sentences = create_sentences(full_hash, alt=alt_representation_required)

        # do we need to load new data?
        if full_hash != last_hash:
            last_hash = full_hash
            text_sents_file = os.path.join(text_sents_dir, current_language, f"{full_hash}.json")
            text_sents_list = None
            try:
                with open(text_sents_file, 'r', encoding='utf-8') as f:
                    text_sents_list = json.load(f)
            except FileNotFoundError:
                err_msg = "Error in {}: {} not found."
                print(err_msg.format("".join(["stu","dy"]), text_sents_file))
                return False

            word_filepath = os.path.join(text_words_dir, current_language, full_hash + ".json")
            #try_count = 0
            #while True:
                #if try_count >= 2:
                    #break
            try:
                with open(word_filepath, "r", encoding="utf-8") as f:
                    new_words_data = json.load(f)
                    #break
            except FileNotFoundError:
                #try_count += 1
                #if not parse_text(full_hash):
                    #print(f"Error: Word data file '{word_filepath}' not found and couldn't reparse the text.")
                    print(f"Error: Word data file '{word_filepath}' not found.")
                    #return False

        if not skip_word and not next_word:
            # TODO make this a user setting
            if words_studied[full_hash] == 5:
                # consider this a study session
                set_metadata(full_hash, {"study_count_up": True, "last_study_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S")})
            words_studied[full_hash] += 1
        skip_word = False
        next_word = False
        word_data = new_words_data[word][index]
        sentence = ""
        try:
            if (text_sents_list
                and word_data.get("sent_inx", "") >= 0
                and text_sents_list[word_data["sent_inx"]]):
                sentence = text_sents_list[word_data["sent_inx"]]
        except IndexError:
            alert(str(word_data))
            alert(str(text_sents_list))

        if True:
            if sentence in alt_sentences and alt_sentences[sentence]:
                alt_sentence = alt_sentences[sentence]
            else:
                alt_sentence = ""
            if sentence in native_sentences and native_sentences[sentence]:
                native_sent = native_sentences[sentence]
            else:
                native_sent = ""
            word_index = word_data.get("index", -1)
            if (word, word_index) in dupes_to_skip:
                skip_word = True
                continue
            if word_index >= 0:
                # Find all indices where translation, sentence is the same
                indices = [word_index]
                for i, version in enumerate(new_words_data[word]):
                    if version["index"] == word_index:
                        continue

                    if (text_sents_list
                        and version.get("sent_inx", "") >= 0
                        and text_sents_list[version["sent_inx"]]):
                        ver_sent = text_sents_list[version["sent_inx"]]

                    if (text_sents_list
                        and word_data.get("sent_inx", "") >= 0
                        and text_sents_list[word_data["sent_inx"]]):
                        word_sent = text_sents_list[word_data["sent_inx"]]
                    if (ver_sent
                        and ver_sent == word_sent
                        and version["translation"] == word_data.get("translation", "")):
                        # The `indices` list points to words with same meaning in same sentence.
                        # We don't need to prompt each of these, so skip all but first one.
                        indices.append(version["index"])
                        dupes_to_skip.append((word, version["index"]))

                # Split the sentence into a list of words
                words_in_sentence = sentence.split()

                sentence, native_sent, alt_sentence = format_sentences(sentence, native_sent, alt_sentence)
                formatted_sentence = sentence

                if alt_sentence:
                    alt_sentence = "\n> "+colour_sentence(
                        alt_sentence,
                        word,
                        indices,
                        orig_sent=formatted_sentence,
                        rev_study=rev_study,
                        colors=[Fore.BLACK, Fore.WHITE]
                    )
                sentence = colour_sentence(sentence, word, indices,
                                           add_stress_marks=False if alt_representation_required else True,
                                           rev_study=rev_study)
                if native_sent:
                    native_sent = f"\n{Fore.GREEN}>{Style.RESET_ALL} " + colour_sentence(
                        native_sent, word, indices,
                        orig_sent=formatted_sentence,
                        rev_study=True,
                        colors=[Fore.BLACK, Fore.BLUE],
                        add_stress_marks=False,
                        space_char="/"
                    )
                    native_sent = native_sent.replace(format_delim_word, " ")

            sentence = f"\n{Fore.MAGENTA}>{Style.RESET_ALL} " + sentence

        correct_base = word_data.get("base", "")
        if correct_base == word:
            correct_base = None
        elif correct_base == "":
            correct_base = None

        guessed = False
        graded = False
        while True:
            save_required = False
            if (("translation" in word_data and word_data["translation"] != "")
                and ((alt_representation_required and "alt_representation" in word_data and word_data["alt_representation"] != "")
                or not alt_representation_required)):

                word_heading, short_heading = build_word_heading(word, word_data, rev_study=rev_study)

                correct_translation = word_data.get("translation")

                correct_base_translation = word_data.get("base_translation", "")
                if correct_base_translation == correct_translation:
                   correct_base_translation = None
                elif correct_base_translation == "":
                   correct_base_translation = None

                alt_rep = word_data.get("alt_representation", "")
                if alt_rep == word or alt_rep == correct_base:
                   alt_rep = None
                elif alt_rep == "":
                   alt_rep = None

                tags = []
                note = []
                if "tags" in word_data and word_data.get("tags", "") != "":
                   tags = word_data["tags"]
                if "note" in word_data and word_data.get("note", "") != "":
                   note = word_data["note"]

                if not guessed:
                    hint_len = 0
                    whole_hint = word if rev_study else correct_translation.split(",")[0].replace("(","").replace(")","")
                    while True:
                        hint = f' (hint: {Fore.GREEN + whole_hint[:hint_len] + Style.RESET_ALL})' if hint_len else ""
                        if not rev_study:
                            word_prompt = f"{Fore.BLUE + short_heading + Style.RESET_ALL}"
                        else:
                            word_prompt = word_heading if alt_representation_required else f"{Fore.BLUE + correct_translation + Style.RESET_ALL}"

                        if IS_DEV_MODE:
                            print(f"{Fore.RED}[DEV-DATA]{Style.RESET_ALL}")

                        user_input = input(f"\n{word_heading}{native_sent}{alt_sentence}{sentence}\n{Fore.GREEN}Guess the translation of{Style.RESET_ALL} {word_prompt}{hint}? ")
                        if user_input != '.':
                            break
                        hint_len += 1
                        if whole_hint[hint_len-1:hint_len] == ' ':
                            hint_len += 1
                    guessed = True
                else:
                    user_input = input(f"{gr_prompt} Next command or hit enter for next word: ")
                    if user_input == "":
                        print(" ")
                        break

                if user_input.lower() in ["x", "!stop"]:
                    return
                elif user_input.lower() == "!tags":
                    if not tags:
                       print(Fore.RED + "No tags found!" + Style.RESET_ALL)
                    else:
                       print(f"Tags: {Fore.GREEN + tags + Style.RESET_ALL}")
                elif user_input.lower() == "!next":
                    next_word = True
                    break
                elif user_input.lower() == "!note":
                    if not note:
                       print(Fore.RED + "No note found!" + Style.RESET_ALL)
                    else:
                       print(f"Note: {Fore.GREEN + note + Style.RESET_ALL}")
                elif user_input.lower() == "!skip":
                    confirmation = input(f"Do you really want to skip {Fore.BLUE + word + Style.RESET_ALL}? (y/n): ")
                    if confirmation.lower() == 'y':
                        word_data["skip"] = True
                        new_words_data[word][index] = word_data
                        save_required = True
                        skip_word = True
                elif user_input.lower() == "!edit":
                    while True:
                        try:
                            if copy_quotes:
                                pyperclip.copy(f'"{word}"')
                            else:
                                pyperclip.copy(f'{word}')
                        except:
                            pass

                        if IS_DEV_MODE:
                            print(f"{Fore.RED}[DEV-DATA]{Style.RESET_ALL}")

                        print(f"\nEditing {Fore.BLUE + word + Style.RESET_ALL}")
                        for i, word_key in enumerate(editable_word_keys):
                            print(f'{i+1}) {word_key}: {Fore.GREEN + word_data.get(word_key, "<empty>") + Style.RESET_ALL}')
                            max_i = i+1
                        if word_data["internal_type"] != "word":
                            print(f"d) delete")
                        #for ro_word_key in readonly_word_keys:
                            #ro_word_value = word_data.get(ro_word_key, "<empty>")
                            #print(f"-) {ro_word_key}: {ro_word_value}")
                        while True:
                            num_input = input("Enter a valid number to edit (or x to exit): ")
                            if num_input.lower() in ['x', 'd']:
                                break
                            try:
                                if 1 <= int(num_input) <= max_i:
                                    break
                                else:
                                    continue
                            except ValueError:
                                pass
                        if num_input.lower() == 'x':
                            break
                        if num_input.lower() == 'd':
                            if word_data["internal_type"] != "word":
                                del_conf = input(f"Are you sure you want to delete {word}? (y/n)")
                                if del_conf.lower() == "y":
                                    del new_words_data[word][index]
                                    if not new_words_data[word]:
                                        del new_words_data[word]
                                    save_required = True
                            else:
                                print("You cannot delete an internally-created word!")
                            break
                        edit_key = editable_word_keys[int(num_input)-1]
                        edit_input = None
                        copy_option = ""
                        cp_str = f"{Fore.BLUE}!cp{Style.RESET_ALL}"
                        if edit_key == "base":
                            copy_option = f"(enter {cp_str} to copy from {Fore.BLUE + word + Style.RESET_ALL}) "
                        elif edit_key == "base_translation":
                            copy_option = f'(enter {cp_str} to copy from {Fore.BLUE + word_data.get("translation", "") + Style.RESET_ALL}) '
                        elif edit_key == "translation":
                            # use index to find translation suggestions
                            suggestions, _ = search_word_index(word, base=correct_base)
                            # TODO use get_user_sugg here
                            if suggestions:
                                print("  Suggestions:")
                                for i, suggestion in enumerate(suggestions):
                                    print(f"  {i+1}) {Fore.BLUE + suggestion + Style.RESET_ALL}")
                                    max_i = i+1
                                print("Or type in a new translation:", end=" ")
                                user_translation = input(f"{gr_prompt} ")
                                num_input = False
                                try:
                                    if 1 <= int(user_translation) <= max_i:
                                        num_input = True
                                    else:
                                        continue
                                except ValueError:
                                    edit_input = user_translation
                                if num_input:
                                    edit_input = suggestions[int(user_translation)-1]
                        if not edit_input:
                            edit_input = input(f"Enter a new value for {Fore.GREEN + edit_key + Style.RESET_ALL}: {copy_option}").lower()
                        if edit_key == "base" and edit_input == "!cp":
                            edit_input = word
                        elif edit_key == "base_translation" and edit_input == "!cp":
                            edit_input = word_data.get("translation", "")
                        print(f'Changing {Fore.GREEN + edit_key + Style.RESET_ALL} from {Fore.RED + word_data.get(edit_key, "<empty>") + Style.RESET_ALL} to {Fore.GREEN + edit_input + Style.RESET_ALL}')
                        confirmation = input("Please confirm (y/n): ")
                        if confirmation.lower() == "y":
                            word_data[edit_key] = edit_input
                            new_words_data[word][index] = word_data
                            save_required = True
                            print(Fore.RED + "New value will be saved after exiting edit mode." + Style.RESET_ALL)
                            edit_input = None
                        else:
                            print(Fore.RED + "Change aborted!" + Style.RESET_ALL)
                elif user_input.lower() == "!phrase":
                    sent_inx = None
                    if (text_sents_list
                        and new_words_data[word][index].get("sent_inx", "") >= 0
                        and text_sents_list[new_words_data[word][index]["sent_inx"]]):
                        sent_inx = new_words_data[word][index]["sent_inx"]
                    phrase, new_phrase = create_phrase(
                        new_words_data,
                        words_in_sentence,
                        word_index,
                        text_sents_list[sent_inx],
                        sent_inx=sent_inx
                    )
                    if phrase:
                        new_words_data.setdefault(phrase, []).append(new_phrase)
                        save_required = True
                # process the guess
                elif not graded:
                    def add_unique_alt_answers(new_answers, existing_answers):
                        unique_answers = []
                        for new_answer in new_answers:
                            if new_answer not in existing_answers and new_answer not in unique_answers:
                                unique_answers.append(new_answer)
                        return unique_answers

                    if not rev_study:
                        # create one list to use with any() in the if statement below
                        orig_answers = correct_translation.split(",")
                        possible_answers = correct_translation.split(",")
                        alt_answers = []

                        no_parens = correct_translation.replace("(","").replace(")","").split(",")
                        possible_answers += no_parens
                        alt_answers += add_unique_alt_answers(no_parens, alt_answers + orig_answers)

                        no_parens_text = [a.strip() for a in re.sub(r"\([^())]*\)[ ]?", "", correct_translation).split(",")]
                        possible_answers += no_parens_text
                        alt_answers += add_unique_alt_answers(no_parens_text, alt_answers + orig_answers)

                        if correct_base_translation:
                            answers = correct_base_translation.split(",")
                            possible_answers += answers
                            alt_answers += add_unique_alt_answers(answers, alt_answers + orig_answers)

                            no_parens = correct_base_translation.replace("(","").replace(")","").split(",")
                            possible_answers += no_parens
                            alt_answers += add_unique_alt_answers(no_parens, alt_answers + orig_answers)

                            no_parens_text = [a.strip() for a in re.sub(r"\([^())]*\)[ ]?", "", correct_base_translation).split(",")]
                            possible_answers += no_parens_text
                            alt_answers += add_unique_alt_answers(no_parens_text, alt_answers + orig_answers)

                        possible_answers = set(answer.lower() for answer in possible_answers)
                        answers_output = f'{Fore.GREEN + ", ".join(orig_answers) + Style.RESET_ALL}'
                        if alt_answers:
                            answers_output += f'\nOther answer(s): {", ".join(alt_answers)}'

                    elif rev_study and not lang_map:
                        # create one list to use with any() in the if statement below
                        possible_answers = []
                        raw_possible_answers = [word]
                        alt_answers = []
                        if correct_base and correct_base != word:
                            raw_possible_answers.append(correct_base)
                            alt_answers += add_unique_alt_answers([correct_base], alt_answers)
                        if alt_representation_required and alt_rep and alt_rep != word:
                            raw_possible_answers.append(alt_rep)
                        for poss_ans in raw_possible_answers:
                            if ignore_spaces_in_rev_study:
                                no_spaces = poss_ans.replace(" ", "").split(",")
                                possible_answers += no_spaces
                                alt_answers += add_unique_alt_answers(no_spaces, alt_answers + [word])
                            else:
                                with_spaces = poss_ans.split(",")
                                possible_answers += with_spaces
                                alt_answers += add_unique_alt_answers(with_spaces, alt_answers + [word])
                        possible_answers = set(answer.lower() for answer in possible_answers)
                        answers_output = f"{Fore.GREEN + word + Style.RESET_ALL}"
                        if alt_answers:
                            answers_output += f'\nOther answer(s): {", ".join(alt_answers)}'

                    if not rev_study and any(user_input.lower() == translation for translation in possible_answers):
                        print(Fore.GREEN + "Correct!" + Style.RESET_ALL)
                        print(f"Acceptable answer(s): {answers_output}")
                    elif rev_study and not lang_map and any(user_input.lower() == w for w in possible_answers):
                        print(Fore.GREEN + "Correct!" + Style.RESET_ALL)
                        print(f"Acceptable answer(s): {answers_output}")
                    elif rev_study and lang_map and user_input.lower() == map_input(word.lower(), lang_map):
                        print(Fore.GREEN + f"Correct! The word is {word.lower()}" + Style.RESET_ALL)
                    else:
                        print(Fore.RED + "Incorrect." + Style.RESET_ALL)
                        print(f"Acceptable answer(s): {answers_output}")
                        typed_word = input(f"{Fore.RED}Please type the word, or hit enter to continue:{Style.RESET_ALL} ")
                        if typed_word not in possible_answers:
                            print(f"{Fore.RED}Try again next time!{Style.RESET_ALL}")
                        else:
                            print(f"{Fore.GREEN}Good!{Style.RESET_ALL}")
                    graded = True

            elif (not rev_study and ("translation" not in word_data or word_data["translation"] == "")
                  and ("skip" not in word_data or not word_data["skip"])):

                word_heading, short_heading = build_word_heading(word, word_data, rev_study=rev_study)
                print(f"{word_heading}{alt_sentence}{sentence}Add a translation for {short_heading}:", end=" ")
                # use index to find translation suggestions
                suggestions, _ = search_word_index(word, base=correct_base)
                if suggestions:
                    print("\n  Suggestions:")
                    for i, suggestion in enumerate(suggestions):
                        print(f"  {i+1}) {Fore.BLUE + suggestion + Style.RESET_ALL}")
                        max_i = i+1
                    print("Or type in a new translation:", end=" ")
                user_translation = input()
                num_input = False
                try:
                    if 1 <= int(user_translation) <= max_i:
                        num_input = True
                except ValueError:
                    pass
                if num_input:
                    save_conf = input(f"Are you sure you want to save this translation {Fore.BLUE + suggestions[int(user_translation)-1] + Style.RESET_ALL}? (y/n) ")
                    if save_conf.lower() == "y":
                        word_data["translation"] = suggestions[int(user_translation)-1]
                        new_words_data[word][index] = word_data
                        save_required = True
                    else:
                        print("Save aborted.")
                elif user_translation.lower() == "!stop":
                    return
                elif user_translation.lower() == "!skip":
                    confirmation = input(f"Do you really want to skip {Fore.BLUE + word + Style.RESET_ALL}? (y/n): ")
                    if confirmation.lower() == 'y':
                        word_data["skip"] = True
                        new_words_data[word][index] = word_data
                        save_required = True
                        skip_word = True
                elif user_translation.lower() == "!next":
                    next_word = True
                    break
                elif user_translation.lower() == "!phrase":
                    sent_inx = None
                    if (text_sents_list
                        and new_words_data[word][index].get("sent_inx", "") >= 0
                        and text_sents_list[new_words_data[word][index]["sent_inx"]]):
                        sent_inx = new_words_data[word][index]["sent_inx"]
                    phrase, new_phrase = create_phrase(
                        new_words_data,
                        words_in_sentence,
                        word_index,
                        text_sents_list[sent_inx],
                        sent_inx=sent_inx
                    )
                    if phrase:
                        new_words_data.setdefault(phrase, []).append(new_phrase)
                        save_required = True
                    else:
                        continue
                else:
                    save_conf = input(f"Are you sure you want to save this translation {Fore.BLUE + user_translation + Style.RESET_ALL}? (y/n) ")
                    if save_conf.lower() == "y":
                        word_data["translation"] = user_translation
                        new_words_data[word][index] = word_data
                        save_required = True
                    else:
                        print("Save aborted.")
            else:
                break

            if save_required:
                # let's only backup a file once per session
                if not backup_present.get("hash", "") and not backup_text_words(full_hash, word_filepath):
                    print(f"Word data cannot be saved since backup failed.")
                    continue

                try:
                    with open(word_filepath, "w", encoding="utf-8") as f:
                        json.dump(new_words_data, f, indent=2)
                        backup_present[full_hash] = True
                except (FileNotFoundError, json.JSONDecodeError) as e:
                    print(f"Error saving word data: {e}")

def create_phrase(words_data, words_in_sentence, word_index, sentence, sent_inx=None):
    try:
        phrase_length = int(input("Enter the desired phrase length: "))
    except ValueError:
        print("Invalid input. Please enter a number greater than 1.")
        return False, False
    if phrase_length < 2:
        print("Invalid input. Please enter a number greater than 1.")
        return False, False
    try:
        # Extract the phrase from the sentence
        phrase = normalize_word(' '.join(words_in_sentence[word_index:word_index+phrase_length]))
        confirmation = input(f"Is '{Fore.GREEN + phrase + Style.RESET_ALL}' the correct phrase? (y/n): ")
        if confirmation.lower() == 'y':
            for existing_phrase, existing_phrase_data in words_data.items():
                for existing_version in existing_phrase_data:
                    if existing_phrase == phrase and existing_version.get("index") == word_index and existing_version.get("sentence") == sentence:
                        print(Fore.RED + "Phrase already exists at that index for this sentence." + Style.RESET_ALL)
                        return False, False
            # Create a new main entry for the phrase
            new_entry = {
                "internal_type": "phrase",
                "type": "",
                "translation": "",  # Initially no translation for the phrase
                "index": word_index
            }
            if sent_inx is not None:
                new_entry["sent_inx"] = sent_inx
            print(f"New phrase '{phrase}' added to the data.")
            return phrase, new_entry
        else:
            print("Phrase entry not added.")
            return False, False
    except IndexError:
        print("Invalid phrase length.")
        return False, False

def manage_backups():
    """
    Scans the backup folders and checks if there are more than 10 backup files for any file.
    If so, it deletes the old backups, and leaves the 10 newest ones in place.
    """
    text_backup_dir = os.path.join(text_words_dir, "backups")
    text_files = []
    text_files.append((backups_dir, "metadata.json"))
    for langdir in os.listdir(text_words_dir):
        if "backup" in langdir:
            continue
        for i in os.listdir(os.path.join(text_words_dir, langdir)):
            text_files.append((text_backup_dir, i))

    files_to_delete = []
    for backup_dir, filename in text_files:
        if filename.endswith(".json"):
            file_start = filename.split(".")[0]
            backup_files = [f for f in os.listdir(backup_dir) if f.startswith(file_start) and f.endswith(".json")]

            if len(backup_files) > 10:
                backup_files.sort(key=lambda x: os.path.getctime(os.path.join(backup_dir, x)), reverse=True)  # Sort by creation time (newest first)
                files_to_delete.extend([(backup_dir, bf) for bf in backup_files[10:]])

    if files_to_delete and len(files_to_delete) > 10:
        for backup_dir, file in files_to_delete:
            file_path = os.path.join(backup_dir, file)
            try:
                os.remove(file_path)
            except OSError as e:
                print(f"Error deleting {file_path}: {e}")

def show_langdata(language):
    lang_data = get_langdata(language, user_friendly=True)
    for key, value in lang_data.items():
        print(f"{key}: {Fore.GREEN}{value}{Style.RESET_ALL}")

def repl():
    global current_language
    global GLOBAL_WORD_INDEX, glob_words_index_lang
    global default_words_index_count, glob_words_index_count
    global valid_commands
    global default_sent_delims, sent_delims
    global default_sent_post_delims, sent_post_delims
    global default_word_delims, word_delims
    global default_alt_representation_required, alt_representation_required
    global default_ignore_spaces_in_rev_study, ignore_spaces_in_rev_study
    global default_underscore, underscore
    global default_edit_inputs, edit_inputs
    global default_copy_quotes, copy_quotes
    global default_copy_string, copy_string
    global default_yes_letter, yes_letter
    global default_no_letter, no_letter
    global default_exit_letter, exit_letter
    global default_all_letter, all_letter
    global default_alphabet, alphabet
    global default_frequents, frequents
    global format_delim_phrase, format_delim_word
    global gr_prompt

    current_language = None
    format_delim_phrase = "__su__"
    format_delim_word = "__hs__"
    GLOBAL_WORD_INDEX = None
    glob_words_index_lang = None
    glob_words_index_count = 5
    gr_prompt = f"{Fore.GREEN + '>' + Style.RESET_ALL}"

    valid_commands = {"import", "fix_metadata", "metadata", "md", #"parse_text",
                      "list_metadata", "list", "show", "read", "rev_study",
                      "encode", "decode", "edit", "study", #"parse_sentences",
                      "lang", "show_langdata", "help", "exit", "q", "quit"}
    sent_delims = '.!?\\n'
    sent_post_delims = '\'")\\]}'
    word_delims = ",.:;?!\"'()[]«»„“”…-*"
    alt_representation_required = False
    ignore_spaces_in_rev_study = False
    underscore = "_"
    edit_inputs = {
        "c<": "context_prev",
        "c>": "context_next",
        "<": "word_prev",
        ">": "word_next",
        "g": "globals",
        "m": "more",
        "n": "next",
        "a": "accept",
        "k": "accept",
        "p": "phrase",
        "s": "skip",
        "q": "exit",
        "d": "delete"
    }
    copy_quotes = False
    copy_string = ["cp", "!cp"]
    yes_letter = ["y", "Y"]
    no_letter = ["n"]
    exit_letter = ["q"]
    all_letter = ["a", "k"]
    alphabet = {
        "a": "a", "b": "b", "c": "c", "d": "d", "e": "e", "f": "f", "g": "g",
        "h": "h", "i": "i", "j": "j", "k": "k", "l": "l", "m": "m", "n": "n",
        "o": "o", "p": "p", "q": "q", "r": "r", "s": "s", "t": "t", "u": "u",
        "v": "v", "w": "w", "x": "x", "y": "y", "z": "z"
    }
    frequents = None

    default_words_index_count = glob_words_index_count
    default_sent_delims = sent_delims
    default_sent_post_delims = sent_post_delims
    default_word_delims = word_delims
    default_alt_representation_required = alt_representation_required
    default_ignore_spaces_in_rev_study = ignore_spaces_in_rev_study
    default_underscore = underscore
    default_edit_inputs = edit_inputs
    default_copy_quotes = copy_quotes
    default_copy_string = copy_string
    default_yes_letter = yes_letter
    default_no_letter = no_letter
    default_exit_letter = exit_letter
    default_all_letter = all_letter
    default_alphabet = alphabet
    default_frequents = frequents

    print("\nWelcome to the langwich REPL.")
    print("Type 'help' for a list of available commands. Type 'exit' to quit.")

    manage_backups()

    while True:

        command = input(f"{gr_prompt} ").lower()

        if not command:
            continue

        if command in ["quit", "exit", "q"]:
            print("Exiting...")
            break

        if command.split()[0] not in valid_commands:
            print(f"Unrecognized command: {command}")
            print("Type 'help' for a list of available commands.")
            continue

        elif command.strip() == "lang":
            new_lang = list_langs()
            _, _ = get_langdata(new_lang)
        elif command.startswith("lang "):
            new_lang = command.split(" ")[1]
            _, _ = get_langdata(new_lang)

        # Import a new text
        elif command.startswith("import"):
            if not current_language:
                print("Please choose a language first (e.g. 'lang japanese')")
                continue
            print(f"Current language set to '{current_language}'")
            alert("Ensure sentences are on separate lines. No longer splitting on punctuation, only line breaks.")
            params = command.split(" ")
            text_type = None
            full_hash = None
            if len(params) > 1:
                # confirm if user wants to extend this existing text
                short_hash = params[1]
                full_hash = get_matching_hash(short_hash)
                if not full_hash:
                    print("Could not find a matching text. Aborting.")
                    return False
                metadata = get_metadata(full_hash)
                text_type = metadata["type"].lower()
            if not text_type:
                while True:
                    text_num = input("Enter text type: '1' for normal, '2' for wordlist: ")
                    if text_num not in ["1", "2"]:
                        continue
                    text_type = "normal"
                    if text_type == "2":
                        text_type = "wordlist"
                    break
            title = input("Enter text title (or <enter> for auto-title): ")
            print(f"Copy text below. Multi-line ok. Ctrl-z on empty line to end: {gr_prompt}")
            raw_text = ""
            try:
                while True:
                    line = input()
                    raw_text += line + "\n"
            except EOFError:
                pass
            process_and_save_text(
                raw_text,
                text_type,
                title=title if title else None,
                append_to=full_hash
            )

        # Fix/populate the metadata for one text or all texts
        elif command.startswith("fix_metadata"):
            params = command.split(" ")
            if len(params) == 1:
                fix_metadata()
            else:
                fix_metadata(params[1])

        # List the metadata for one text or all texts
        elif command.startswith("list_metadata"):
            params = command.split(" ")
            if len(params) == 1:
                list_metadata()
            else:
                list_metadata(params[1])

        # List all texts or list all texts of a specified language
        elif command.startswith("list"):
            if not current_language:
                print("Please choose a language first (e.g. 'lang japanese')")
                continue
            params = command.split(" ")
            filter = None
            limit = None
            if len(params) >= 2:
                filter = params[1]
            if len(params) >= 3:
                try:
                    limit = int(params[2])
                except ValueError:
                    limit = None
            list_texts(filter, limit)

        # Show the full text of a specified text
        elif command.startswith("show "):
            params = command.strip().split(" ")
            if len(params) > 2:
                print("Error: Too many parameters. Use 'show <hash_substring>' to show a specific text.")
                continue
            hash_substring = command.split(" ")[1]
            show_text(hash_substring)
        elif command == "show":
            print(f"Error: Please provide a hash substring after the '{command}' command. For example: '{command} 124356'")

        elif command.startswith("read "):
            hash_substring = command.split(" ")[1]
            read_text(hash_substring)
        elif command == "read":
            print(f"Error: Please provide a hash substring after the '{command}' command. For example: '{command} 124356'")

        # Enter edit mode for the specified language or the specified text
        elif command.startswith("edit "):
            if not current_language:
                print("Please choose a language first (e.g. 'lang japanese')")
                continue
            params = command.split(" ")
            short_hash = params[1]
            randomize = True
            if len(params) == 3 and params[2] == "o":
                randomize = False
            hash = get_matching_hash(short_hash)
            if not hash:
                continue
            edit_text = Text(hash)
            #print(edit_text)
            edit(edit_text=edit_text, randomize=randomize)
        elif command == "edit":
            # TODO maybe move this check way up. Compare command to a list of cmds that require a lang
            if not current_language:
                print("Please choose a language first (e.g. 'lang japanese')")
                continue
            edit(randomize=True)

        # Edit metadata for the specified text
        elif command.startswith("metadata ") or command.startswith("md "):
            hash_substring = command.split(" ")[1]
            edit_metadata(hash_substring)
        elif command in ("metadata", "md"):
            print("Error: Please provide a hash substring after the 'metadata' command. For example: 'metadata 124356'")

        # Enter study mode for the specified text
        elif command.startswith("study "):
            if not current_language:
                print("Please choose a language first (e.g. 'lang japanese')")
                continue
            param = command.split(" ")[1]
            study(hash_substring=param)
        elif command == "study":
            if not current_language:
                print("Please choose a language first (e.g. 'lang japanese')")
                continue
            study()

        # Enter reverse study mode for the specified text
        elif command.startswith("rev_study "):
            rev_params = command.split()[1:]
            hash_substring = rev_params[0]
            lang_map = None
            if len(rev_params) > 1:
                lang_file = rev_params[1]
                lang_file = os.path.join(langs_dir, lang_file + '.json')
                try:
                    with open(lang_file, "r", encoding="utf-8") as f:
                       lang_map = json.load(f)
                except FileNotFoundError:
                    print(f"Error: Language file '{lang_file}' not found.")
                    return
            study(hash_substring, rev_study=True, lang_map=lang_map)
        elif command == "rev_study":
            print("Error: Please provide a hash substring after the 'rev_study' command. For example: 'rev_study 124356'")

        # Show all language configs for the specified language
        elif command.startswith("show_langdata "):
            language = command.split(" ")[1]
            show_langdata(language)
        elif command == "show_langdata":
            print("Error: Please provide a language after the 'show_langdata' command. For example: 'show_langdata ukrainian'")

        # Encode a unicode string
        elif command.startswith("encode "):
            string2encode = command.split(" ")
            string2encode = " ".join(string2encode[1:])
            encoded_text = encoder(string2encode)
            print(f"Encoded string: {encoded_text}")
        elif command == "encode":
            print("Error: Please provide a unicode string")

        # Decode a string of unicode code points
        elif command.startswith("decode "):
            string2decode = command.split(" ")
            string2decode = " ".join(string2decode[1:])
            decoded_text = decoder(string2decode)
            print(f"Decoded string: {decoded_text}")
        elif command == "decode":
            print("Error: Please provide a string of unicode code points")

        # Outputs some help text or all commands if "help more" is entered
        elif command.startswith("help"):
            params = command.split(" ")
            if len(params) == 1 or params[1] != "more":
                help()
            else:
                help(more=True)

if __name__ == "__main__":
  repl()