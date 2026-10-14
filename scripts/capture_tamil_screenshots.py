import subprocess
import os

edge_path = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
chrome_path = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
browser = chrome_path if os.path.exists(chrome_path) else edge_path

out_dir = r"C:\Users\yogid\.gemini\antigravity-ide\brain\7d0cd292-5cd6-4df2-9d03-66b130591771"
temp_dir = os.path.join(os.environ.get("TEMP", r"C:\temp"), "browser_snap_audit2")

targets = [
    ("http://127.0.0.1:5000/set-language/ta?next=/machinery/", "catalogue_tamil_verified.png"),
    ("http://127.0.0.1:5000/set-language/ta?next=/machinery/5826ab2e-23a6-457d-8804-f38dde629063", "machinery_detail_tamil_verified.png"),
]

for url, fname in targets:
    out_file = os.path.join(out_dir, fname)
    cmd = [
        browser,
        "--headless=new",
        "--no-sandbox",
        "--disable-gpu",
        "--hide-scrollbars",
        f"--user-data-dir={temp_dir}",
        f"--screenshot={out_file}",
        "--window-size=1280,1000",
        url,
    ]
    print("Capturing:", url, "->", fname)
    try:
        subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        print("Success, exists:", os.path.exists(out_file))
    except Exception as e:
        print("Error capturing:", e)
