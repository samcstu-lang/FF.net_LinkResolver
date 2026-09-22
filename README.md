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

2. Run the script:
```bash
python ffdownloader.py
# or on Windows:
py ffdownloader.py
```

3. Check `output.txt` for resolved direct download URLs:

## How It Works

- Launches a single undetected Chrome instance in minimized mode (bypasses Cloudflare).
- Navigates to each file page in sequence.
- Extracts the download gateway path from the page.
- **Zero ad popups, zero clipboard manipulation
