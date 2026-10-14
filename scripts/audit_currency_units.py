import os
import re

app_dir = r"C:\farm connect\app"
matches = []

for root, _, files in os.walk(app_dir):
    for f in files:
        if f.endswith((".html", ".py", ".js")):
            p = os.path.join(root, f)
            with open(p, "r", encoding="utf-8", errors="ignore") as file:
                lines = file.readlines()
                for idx, line in enumerate(lines, 1):
                    # Check if line has currency symbol
                    if "\u20b9" in line or "Rs" in line or "INR" in line:
                        matches.append((p, idx, line.strip()))

with open(r"C:\farm connect\scripts\currency_matches.txt", "w", encoding="utf-8") as out:
    for p, idx, line in matches:
        out.write(f"{p}:{idx}: {line}\n")

print(f"Total matches found: {len(matches)}")
