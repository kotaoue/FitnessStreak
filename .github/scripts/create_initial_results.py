import json
import os
import sys

date = os.environ.get('DATE')
if not date:
    print("ERROR: DATE environment variable is required", file=sys.stderr)
    sys.exit(1)

result = {
    "date": date,
    "exercises": {
        "ラジオ体操": False,
        "ストレッチ": False,
        "筋トレ": False,
        "ツボ押し": False
    }
}

os.makedirs('results', exist_ok=True)
with open(f'results/{date}.json', 'w', encoding='utf-8') as f:
    json.dump(result, f, ensure_ascii=False, indent=2)
    f.write('\n')

print(f"Created results/{date}.json")
