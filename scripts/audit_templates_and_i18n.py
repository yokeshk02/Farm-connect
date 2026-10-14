import glob
import re
import sys
import os

# 1. Load i18n dictionary
sys.path.insert(0, r"C:\farm connect")
from app.utils.i18n import TRANSLATIONS

print(f"Total i18n keys: {len(TRANSLATIONS)}")

# Check missing keys or missing ta/en
missing_en = []
missing_ta = []
for k, v in TRANSLATIONS.items():
    if not isinstance(v, dict):
        continue
    if "en" not in v or not v["en"]:
        missing_en.append(k)
    if "ta" not in v or not v["ta"]:
        missing_ta.append(k)

print(f"Keys missing en: {len(missing_en)}")
print(f"Keys missing ta: {len(missing_ta)}")
if missing_ta:
    print(f"Sample missing ta: {missing_ta[:10]}")

# 2. Extract all _t(...) calls from templates
t_calls = set()
dynamic_prefixes = set()
for p in glob.glob("app/templates/**/*.html", recursive=True):
    with open(p, "r", encoding="utf-8") as f:
        content = f.read()
        # Direct string literals _t('key') or _t("key")
        matches = re.findall(r"_t\(\s*['\"]([^'\"]+)['\"]\s*\)", content)
        for m in matches:
            t_calls.add(m)
        # Dynamic expressions like _t('pkg.' + ...) or _t('cat.' + ...) or _t('status.' + ...)
        dyn_matches = re.findall(r"_t\(\s*['\"]([^'\"]+)['\"]\s*\+", content)
        for dm in dyn_matches:
            dynamic_prefixes.add(dm)

print(f"Total static _t calls: {len(t_calls)}")
print(f"Dynamic _t prefixes: {dynamic_prefixes}")

missing_in_dict = []
for k in t_calls:
    if k not in TRANSLATIONS:
        missing_in_dict.append(k)

print(f"Static _t calls missing in i18n dictionary: {missing_in_dict}")

# 3. Check for None or null rendering
suspicious_vars = []
for p in glob.glob("app/templates/**/*.html", recursive=True):
    with open(p, "r", encoding="utf-8") as f:
        lines = f.readlines()
        for idx, line in enumerate(lines, 1):
            # find interpolations like {{ user.something }} or {{ m.something }}
            interps = re.findall(r"\{\{\s*([^}]+)\s*\}\}", line)
            for item in interps:
                item_s = item.strip()
                # Check if property could be None without filter
                if any(x in item_s for x in ["full_name", "business_name", "village_or_town", "notes", "make_model", "horsepower"]) and "if" not in line and "or" not in item_s and "default" not in item_s:
                    suspicious_vars.append((p, idx, item_s))

print(f"Suspicious variable interpolations that could be None without fallback: {len(suspicious_vars)}")
for p, idx, item_s in suspicious_vars[:15]:
    print(f"  {p}:{idx}: {item_s}")

