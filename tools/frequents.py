import json
import os

frequents = {}

# Load JSON data
lang_dir = os.path.join("text_words", "japanese")
text_word_files = [tw_file for tw_file in os.listdir(lang_dir)]
for tw_file in text_word_files:
    with open(os.path.join(lang_dir, tw_file), "r", encoding="utf-8") as f:
        #print(f"processing {tw_file}")
        text_words_dict = json.load(f)
    for word, meaning in text_words_dict.items():
        for m in meaning:
            frequents[word] = 1 if word not in frequents else frequents[word]+1

# Find words with long meaning arrays
#for word, meanings in data.items():
    #frequents[word] = len(meanings)

sorted_words = sorted(frequents.items(), key=lambda x: x[1])
# Print results
for word, length in sorted_words:
    print(f"{word}: {length}")
'''
私: 54
へ: 54
ー: 58
だった: 63
など: 67
・: 69
もの: 72
だ: 78
その: 79
では: 79
である: 82
年: 85
には: 85
ある: 99
です: 101
という: 104
この: 109
や: 128
こと: 176
から: 197
も: 221
な: 253
で: 387
と: 459
に: 872
が: 929
は: 938
を: 1091
の: 2142
саме: 10
бо: 10
ін: 10
які: 11
тому: 11
тут: 11
він: 11
хочу: 12
було: 13
ж: 13
хто: 14
бути: 14
хоче: 15
україни: 15
нас: 15
від: 15
вже: 16
хоч: 16
щоб: 17
ще: 20
так: 20
для: 21
все: 21
є: 25
коли: 26
хочеш: 26
ми: 29
й: 29
за: 29
але: 30
про: 34
я: 36
до: 38
а: 40
це: 42
з: 47
як: 47
та: 48
у: 54
на: 62
в: 78
що: 84
не: 97
і: 121
'''