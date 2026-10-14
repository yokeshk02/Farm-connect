import glob

with open('scripts/duration_matches.txt', 'w', encoding='utf-8') as out:
    for p in glob.glob('app/templates/**/*.html', recursive=True):
        with open(p, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            for idx, line in enumerate(lines, 1):
                if any(k in line.lower() for k in ['duration', 'hour', 'billable']):
                    out.write(f"{p}:{idx}: {line.strip()}\n")

print("Done writing duration_matches.txt")
