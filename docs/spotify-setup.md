# Spotify Developer Setup

To download from Spotify, you need a **free** Spotify Developer account and a personal API app. This takes about 5 minutes.

## Step 1 — Create a Spotify Developer account

1. Go to [developer.spotify.com/dashboard](https://developer.spotify.com/dashboard)
2. Log in with your existing Spotify account (or create one — free tier works)
3. Accept the Developer Terms of Service if prompted

## Step 2 — Create an app

1. Click **"Create app"**
2. Fill in the form:
   - **App name**: anything you like (e.g. `My Music Downloader`)
   - **App description**: anything (e.g. `Personal use`)
   - **Redirect URIs**: add both values (required by the nyekuuu fix):
     - `http://127.0.0.1:9900/`
     - `http://127.0.0.1:9900`
   - **APIs used**: check **Web API**
3. Click **Save**

> **Note on Redirect URIs**: The nyekuuu fork uses `http://127.0.0.1:9900` (port 9900, not 8888). You must add **both** values (`http://127.0.0.1:9900/` with trailing slash and `http://127.0.0.1:9900` without) in your Spotify app settings, or the OAuth login will fail.

## Step 3 — Get your credentials

1. In the dashboard, click on your newly created app
2. Click **"Settings"** (top right)
3. You'll see your **Client ID** immediately
4. Click **"View client secret"** to reveal your **Client Secret**
5. Copy both — you'll paste them into the app on first use

## Step 4 — First download (OAuth authorization)

When you paste a Spotify URL into Music Downloader for the first time after entering your credentials:

1. A browser window will open asking you to **log in to Spotify** and authorize the app
2. After authorizing, the browser redirects to `localhost:8888` — this is normal
3. The Terminal window will continue downloading automatically
4. This authorization is cached in `~/.spotdl/.spotipy` — you won't need to do it again

## Updating credentials

If you ever need to change your Client ID or Secret:

```bash
~/.local/pipx/venvs/spotdl/bin/spotdl \
  --client-id YOUR_NEW_ID \
  --client-secret YOUR_NEW_SECRET \
  save
```

Or delete `~/.spotdl/config.json` and `~/.spotdl/.spotipy` to reset everything and go through the setup again from the app.

## Troubleshooting

**"INVALID_CLIENT" error in Terminal**
→ Double-check that your Client ID and Secret were copied correctly (no extra spaces).

**Browser opens but shows "Invalid redirect URI"**
→ In your Spotify app settings, make sure you have added **both** Redirect URIs:
- `http://127.0.0.1:9900/`
- `http://127.0.0.1:9900`

**Authorization page never loads**
→ Make sure nothing else is using port 8888 on your Mac. You can check with: `lsof -i :8888`

**Token expired / need to re-authorize**
→ Delete `~/.spotdl/.spotipy` and run a download again. The OAuth flow will restart.
