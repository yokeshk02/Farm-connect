import os
import re

root = r"C:\farm connect\app"
out_lines = []

for dirpath, _, filenames in os.walk(root):
    for fn in filenames:
        if fn.endswith((".html", ".py", ".js")):
            fp = os.path.join(dirpath, fn)
            with open(fp, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
                matches = re.finditer(r"(&#8377;|&#x20b9;|\u20b9|\bRs\.?\b|\bINR\b)", content)
                for m in matches:
                    start = max(0, m.start() - 40)
                    end = min(len(content), m.end() + 40)
                    snippet = content[start:end].replace("\n", " ").strip()
                    out_lines.append(f"{fp}:{m.start()}: {snippet}")

with open(r"C:\farm connect\scripts\currency_usages.txt", "w", encoding="utf-8") as out:
    for l in out_lines:
        out.write(l + "\n")

print(f"Wrote {len(out_lines)} lines to currency_usages.txt")
