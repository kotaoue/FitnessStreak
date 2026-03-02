import json
import os
import re
import sys

title = os.environ.get('PR_TITLE', '').strip()
body = os.environ.get('PR_BODY', '')

if not title:
    print("ERROR: PR_TITLE environment variable is required", file=sys.stderr)
    sys.exit(1)

if not re.fullmatch(r'\d{4}-\d{2}-\d{2}', title):
    print(f"SKIP: PR_TITLE '{title}' is not in YYYY-MM-DD format")
    sys.exit(0)


def is_checked(exercise):
    return bool(re.search(r'- \[[xX]\] ' + re.escape(exercise), body))


result = {
    "date": title,
    "exercises": {
        "ラジオ体操": is_checked("ラジオ体操"),
        "ストレッチ": is_checked("ストレッチ"),
        "筋トレ": is_checked("筋トレ"),
        "ツボ押し": is_checked("ツボ押し")
    }
}

with open(f'results/{title}.json', 'w', encoding='utf-8') as f:
    json.dump(result, f, ensure_ascii=False, indent=2)
    f.write('\n')

print(f"Saved results/{title}.json")
for exercise, done in result["exercises"].items():
    print(f"  {exercise}: {done}")
