# FFDownloader

Automated tool to resolve `fuckingfast.net` download links into direct file URLs.

## Requirements

- Python 3.8+
- Google Chrome installed

## Installation

```bash
pip install -r requirements.txt
```

## Usage

1. Put your links into `input.txt` (one per line):
```
https://fuckingfast.net/tsrth532tn8b
https://fuckingfast.net/zujz5opd3elw
```

2. Run the script:
```bash
python ffdownloader.py
# or on Windows:
py ffdownloader.py
```

3. Check `output.txt` for resolved direct download URLs:
```
https://ts.fuckingfast.net/d/tsrth532tn8b?v=...
https://ts.fuckingfast.net/d/zujz5opd3elw?v=...
```

## How It Works

- Launches a single undetected Chrome instance in minimized mode (bypasses Cloudflare).
- Navigates to each file page in sequence.
- Extracts the download gateway path from the page.
- Executes the internal HTMX request (`HX-Request`) inside the browser context.
- Intercepts the direct download URL from the `HX-Redirect` response header.
- **Zero ad popups, zero clipboard manipulation, ~4.5 seconds per link.**
