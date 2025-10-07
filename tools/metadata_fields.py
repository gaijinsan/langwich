import json
#import os

fields = set()

with open("metadata.json", encoding="utf-8") as f:
    metadata = json.load(f)
for h, m in metadata.items():
    file_metadata = m
    for f, d in file_metadata.items():
        fields.add(f)

print(fields)