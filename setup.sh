#!/bin/bash
set -euo pipefail

BOLD="\033[1m"
GREEN="\033[0;32m"
YELLOW="\033[1;33m"
RED="\033[0;31m"
RESET="\033[0m"

info()    { echo -e "${BOLD}==> $1${RESET}"; }
success() { echo -e "${GREEN}✓ $1${RESET}"; }
warn()    { echo -e "${YELLOW}⚠ $1${RESET}"; }
error()   { echo -e "${RED}✗ $1${RESET}"; exit 1; }

echo -e "${BOLD}"
echo "╔══════════════════════════════════╗"
echo "║   Music Downloader — Setup       ║"
echo "╚══════════════════════════════════╝"
echo -e "${RESET}"

# ── 1. Homebrew ───────────────────────────────────────────────────────────────
info "Checking Homebrew..."
if ! command -v brew &>/dev/null; then
    info "Installing Homebrew..."
    /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
    # Add brew to PATH for Apple Silicon
    if [[ -f /opt/homebrew/bin/brew ]]; then
        eval "$(/opt/homebrew/bin/brew shellenv)"
    fi
else
    success "Homebrew already installed"
fi

# ── 2. ffmpeg ─────────────────────────────────────────────────────────────────
info "Checking ffmpeg..."
if ! command -v ffmpeg &>/dev/null; then
    info "Installing ffmpeg..."
    brew install ffmpeg
else
    success "ffmpeg already installed"
fi

# ── 3. pipx ───────────────────────────────────────────────────────────────────
info "Checking pipx..."
if ! command -v pipx &>/dev/null; then
    info "Installing pipx..."
    brew install pipx
    pipx ensurepath
    export PATH="$HOME/.local/bin:$PATH"
else
    success "pipx already installed"
fi

# ── 4. spotdl (nyekuuu fork — adds --user-auth OAuth for Spotify) ─────────────
info "Checking spotdl..."
SPOTDL_FORK="git+https://github.com/nyekuuu/spotify-downloader.git"
if pipx list 2>/dev/null | grep -q "spotdl"; then
    info "Upgrading spotdl from nyekuuu fork..."
    pipx install --force "$SPOTDL_FORK" || warn "spotdl upgrade failed, keeping existing version"
else
    info "Installing spotdl from nyekuuu fork..."
    pipx install "$SPOTDL_FORK"
fi

# ── 5. yt-dlp ─────────────────────────────────────────────────────────────────
info "Checking yt-dlp..."
if ! command -v yt-dlp &>/dev/null; then
    info "Installing yt-dlp..."
    brew install yt-dlp
else
    success "yt-dlp already installed"
    info "Updating yt-dlp to latest..."
    brew upgrade yt-dlp 2>/dev/null || true
fi

# ── 6. Resolve binary paths ───────────────────────────────────────────────────
info "Resolving binary paths..."

# spotdl path inside its pipx venv
PIPX_VENVS="$(pipx environment --value PIPX_LOCAL_VENVS 2>/dev/null || echo "$HOME/.local/pipx/venvs")"
SPOTDL_PATH="$PIPX_VENVS/spotdl/bin/spotdl"

if [ ! -f "$SPOTDL_PATH" ]; then
    # Fallback: find in PATH
    SPOTDL_PATH="$(command -v spotdl 2>/dev/null || true)"
    if [ -z "$SPOTDL_PATH" ]; then
        error "spotdl binary not found. Try re-running setup.sh after restarting your terminal."
    fi
fi
success "spotdl: $SPOTDL_PATH"

# yt-dlp path
YTDLP_PATH="$(command -v yt-dlp 2>/dev/null || true)"
if [ -z "$YTDLP_PATH" ]; then
    # Check inside spotdl venv
    YTDLP_PATH="$PIPX_VENVS/spotdl/bin/yt-dlp"
    if [ ! -f "$YTDLP_PATH" ]; then
        error "yt-dlp binary not found. Try: brew install yt-dlp"
    fi
fi
success "yt-dlp: $YTDLP_PATH"

# ── 7. Compile AppleScript ────────────────────────────────────────────────────
info "Compiling Music Downloader.app..."

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
APPLESCRIPT_SOURCE="$SCRIPT_DIR/app/MusicDownloader.applescript"
APP_DEST="/Applications/Music Downloader.app"
TMP_SCRIPT="/tmp/MusicDownloader_build.applescript"

if [ ! -f "$APPLESCRIPT_SOURCE" ]; then
    error "AppleScript source not found at $APPLESCRIPT_SOURCE"
fi

# Inject binary paths into the script
sed \
    -e "s|__SPOTDL_PATH__|$SPOTDL_PATH|g" \
    -e "s|__YTDLP_PATH__|$YTDLP_PATH|g" \
    "$APPLESCRIPT_SOURCE" > "$TMP_SCRIPT"

# Remove old app if present
if [ -d "$APP_DEST" ]; then
    rm -rf "$APP_DEST"
fi

osacompile -o "$APP_DEST" "$TMP_SCRIPT"
rm -f "$TMP_SCRIPT"

# Remove quarantine flag (app was built locally, shouldn't be quarantined,
# but being explicit prevents Gatekeeper dialogs on older macOS)
find "$APP_DEST" -exec xattr -c {} \; 2>/dev/null || true

success "App installed to $APP_DEST"

# ── Done ──────────────────────────────────────────────────────────────────────
echo ""
echo -e "${GREEN}${BOLD}╔══════════════════════════════════════════════════╗"
echo "║   Setup complete!                                ║"
echo "╚══════════════════════════════════════════════════╝${RESET}"
echo ""
echo "  Open 'Music Downloader' from /Applications or Spotlight."
echo ""
echo "  YouTube  → works immediately, no setup needed."
echo "  Spotify  → the app will guide you through credentials on first use."
echo "             See docs/spotify-setup.md for a step-by-step guide."
echo ""
