# Instagram Chat Media Downloader

A command-line tool that bulk-downloads every reel, post, and story shared in an Instagram DM thread.

I edit a lot of reference material that friends and collaborators send me over Instagram DMs. Saving them one by one was painful, so this grabs everything from a chat in one go.

## Features

- **Whole-chat downloads** — shared reels, posts, carousels, stories, disappearing photos/videos, and any pasted post/reel/IGTV link in a DM thread
- **Parallel downloads** (4 workers) with a live progress bar, plus a short delay per request to stay under Instagram's rate limits
- **Download history** — remembers everything already saved (even if you later delete the file), so re-runs only fetch new media
- **Saved sessions** — log in once; handles 2FA and Instagram login challenges
- **Remembers your chats** — re-run the same chats with one keypress
- Packaged as a standalone `.exe` with PyInstaller

## Usage

```bash
pip install -r requirements.txt
python downloader.py
```

Log in, enter one or more chat names (comma-separated), and media is saved to `downloads/`.

To build the Windows executable:

```bash
pip install pyinstaller
pyinstaller downloader.spec
```

## ⚠️ Note

This uses [instagrapi](https://github.com/subzeroid/instagrapi), an unofficial Instagram API. Automated access is against Instagram's Terms of Use and can get an account rate-limited or flagged — use it on your own account, sparingly, at your own risk. Your session file (`session.json`) contains your login; never share it.

## Stack

Python · instagrapi · colorama · ThreadPoolExecutor · PyInstaller

---

Made by **Fenil Shah** ([Legend Editx](https://www.youtube.com/@Legend_editx0))
