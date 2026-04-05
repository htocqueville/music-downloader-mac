# Music Downloader for Mac

A simple macOS app to download music from **Spotify** and **YouTube** playlists to your Music folder. No terminal knowledge required after setup.

- Downloads to `~/Music/<playlist name>/` automatically
- MP3, 320 kbps
- Spotify and YouTube are fully independent — use one, the other, or both

## Requirements

- macOS 12 or later
- Internet connection

## Installation

> **Never used a terminal before?** No problem — follow the steps below exactly as written.

### Step 1 — Open Terminal

Press **⌘ + Space**, type `Terminal`, press **Enter**.  
A black or white window with a text prompt will open. That's your Terminal.

### Step 2 — Copy and run the install commands

Select all three lines, copy them (**⌘ + C**), paste into Terminal (**⌘ + V**), then press **Enter**.

```bash
git clone https://github.com/htocqueville/music-downloader-mac.git
cd music-downloader-mac
bash setup.sh
```

The setup takes a few minutes (it installs the necessary tools). You'll see progress messages. At the end you should see **"Setup complete!"**.

### What gets installed

- [Homebrew](https://brew.sh) — macOS package manager (if not already installed)
- ffmpeg — audio conversion
- [spotdl](https://github.com/nyekuuu/spotify-downloader) (nyekuuu fork, with `--user-auth` OAuth support for the new Spotify API)
- [yt-dlp](https://github.com/yt-dlp/yt-dlp) — YouTube downloader
- **Music Downloader.app** → compiled and placed in `/Applications`

> **Re-running `setup.sh` is safe** — it upgrades all tools and rebuilds the app. Use it to update.

## Spotify Setup (one-time, ~5 min)

Spotify requires a free developer API key to access its catalog.

**Quick steps:**
1. Go to [developer.spotify.com/dashboard](https://developer.spotify.com/dashboard) and log in
2. Create an app — add both Redirect URIs: `http://127.0.0.1:9900/` and `http://127.0.0.1:9900`
3. Copy your **Client ID** and **Client Secret** from Settings

On your first Spotify download, the app will ask for these credentials and guide you through the one-time browser authorization.

→ See [docs/spotify-setup.md](docs/spotify-setup.md) for a detailed step-by-step guide with screenshots.

## YouTube Setup

No setup required. YouTube downloads work immediately after running `setup.sh`.

## Usage

1. Open **Music Downloader** from `/Applications` or Spotlight
2. Paste a Spotify or YouTube playlist URL
3. Click **Download**
4. A Terminal window opens showing live progress
5. Files land in `~/Music/<playlist name>/`

**Supported URLs:**
- `https://open.spotify.com/playlist/...`
- `https://www.youtube.com/playlist?list=...`
- `https://youtu.be/...` (single YouTube video → saved to `~/Music/YouTube/`)

## File naming

| Source | Path |
|--------|------|
| Spotify | `~/Music/<playlist name>/<track number> - <artists> - <title>.mp3` |
| YouTube playlist | `~/Music/<playlist name>/<video title>.mp3` |
| YouTube single | `~/Music/YouTube/<uploader> - <title>.mp3` |

## Updating

Open Terminal (⌘ + Space → "Terminal"), then run:

```bash
cd music-downloader-mac
git pull
bash setup.sh
```

## Troubleshooting

| Problem | Solution |
|---------|----------|
| App doesn't open / "damaged" error | Re-run `bash setup.sh` from the project folder |
| `spotdl: command not found` in Terminal | Re-run `setup.sh`, then restart your terminal |
| Spotify: "INVALID_CLIENT" | Re-check Client ID and Secret in your Spotify app settings |
| Spotify: "Invalid redirect URI" | Add both `http://127.0.0.1:9900/` and `http://127.0.0.1:9900` in your Spotify app Redirect URIs |
| YouTube download stops mid-playlist | Re-run the download — yt-dlp skips already-downloaded files |
| `ffmpeg not found` | Run: `brew install ffmpeg` |

## Credits

- [nyekuuu/spotify-downloader](https://github.com/nyekuuu/spotify-downloader) — spotdl fork with `--user-auth` OAuth
- [yt-dlp/yt-dlp](https://github.com/yt-dlp/yt-dlp)
- [FFmpeg](https://ffmpeg.org)

## License

MIT
