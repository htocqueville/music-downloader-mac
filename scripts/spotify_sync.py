#!/usr/bin/env python3
"""
spotify_sync.py — Reconcile a Spotify playlist's local folder before re-downloading.

Run before `spotdl download` so that previously-downloaded songs survive a
playlist reorder. spotdl's "file already exists" check is name-based, so when
{list-position} changes, the same song is downloaded again under a new name.

This script:
  1. Calls `spotdl save` to fetch the current playlist (with current positions)
  2. Reads ID3 tags of every MP3 in the playlist folder
  3. Matches files to songs by (title, first artist) — the same key spotdl uses
  4. Renames each matched file to the path spotdl would generate today
  5. Deletes duplicate files left over from previous reorders
  6. Reports orphan files that no longer match any track in the playlist

Designed to run on the Python interpreter inside spotdl's pipx venv so that
`spotdl` and `mutagen` are importable without extra installs.
"""
import argparse
import json
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

from mutagen.id3 import ID3, ID3NoHeaderError
from spotdl.types.song import Song
from spotdl.utils.formatter import create_file_name


TEMPLATE = "{list-name}/{list-position} - {artists} - {title}.{output-ext}"


def normalize(s: str) -> str:
    return re.sub(r"\s+", " ", s.lower().strip())


def read_tags(path: Path):
    try:
        tags = ID3(path)
    except (ID3NoHeaderError, Exception):
        return "", []
    title_frame = tags.get("TIT2")
    artist_frame = tags.get("TPE1")
    title = title_frame.text[0].strip() if title_frame and title_frame.text else ""
    artists: list[str] = []
    if artist_frame and artist_frame.text:
        # spotdl writes multi-artist as "A/B/C"
        raw = artist_frame.text[0]
        artists = [a.strip() for a in raw.split("/") if a.strip()]
    return title, artists


def run_spotdl_save(spotdl_path: str, url: str) -> list[dict]:
    with tempfile.NamedTemporaryFile(suffix=".spotdl", delete=False) as tf:
        spotdl_file = tf.name
    try:
        result = subprocess.run(
            [spotdl_path, "--config", "--user-auth", "save", url,
             "--save-file", spotdl_file],
            capture_output=True, text=True,
        )
        if result.returncode != 0:
            sys.stderr.write(result.stderr)
            sys.stderr.write("\nspotdl save failed; skipping pre-sync.\n")
            return []
        with open(spotdl_file) as f:
            return json.load(f)
    finally:
        try:
            os.remove(spotdl_file)
        except OSError:
            pass


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--url", required=True)
    ap.add_argument("--output-base", required=True,
                    help="Base directory ending in '/Soundloader'")
    ap.add_argument("--spotdl", required=True)
    args = ap.parse_args()

    songs_data = run_spotdl_save(args.spotdl, args.url)
    if not songs_data:
        return 0  # Non-fatal: let the download proceed without pre-sync.

    list_name = (songs_data[0].get("list_name") or "").strip()
    if not list_name:
        return 0  # Single track, not a playlist — nothing to reorder.

    output_base = Path(args.output_base).expanduser()
    songs = [Song.from_dict(d) for d in songs_data]

    # Compute the canonical (current) path for each song.
    song_targets: list[tuple[Song, Path]] = []
    for song in songs:
        target_rel = create_file_name(song, TEMPLATE, "mp3")
        song_targets.append((song, output_base / target_rel))

    playlist_dir = (output_base / list_name).resolve()
    if not playlist_dir.is_dir():
        print(f"[sync] Playlist folder not found yet: {playlist_dir}")
        return 0

    # Index existing MP3s by (title, first artist) — same key spotdl effectively uses.
    files_by_key: dict[tuple[str, str], list[Path]] = {}
    all_files: list[Path] = sorted(playlist_dir.glob("*.mp3"))
    for mp3 in all_files:
        title, artists = read_tags(mp3)
        if not title or not artists:
            continue
        key = (normalize(title), normalize(artists[0]))
        files_by_key.setdefault(key, []).append(mp3)

    renames: list[tuple[Path, Path]] = []
    duplicates: list[Path] = []
    matched_files: set[Path] = set()
    missing: list[tuple[int, str, str]] = []

    for song, target_path in song_targets:
        artists = song.artists or [song.artist]
        if not song.name or not artists:
            continue
        key = (normalize(song.name), normalize(artists[0]))
        candidates = files_by_key.get(key, [])
        if not candidates:
            missing.append((song.list_position, song.name, artists[0]))
            continue
        chosen = candidates[0]
        matched_files.add(chosen)
        # Any extra files matching the same song are stale duplicates.
        for extra in candidates[1:]:
            duplicates.append(extra)
            matched_files.add(extra)
        if chosen.resolve() != target_path.resolve():
            renames.append((chosen, target_path))

    orphans = [f for f in all_files if f not in matched_files]

    # Delete duplicates first so they don't collide with rename targets.
    for d in duplicates:
        try:
            d.unlink()
            print(f"[sync] removed duplicate: {d.name}")
        except OSError as e:
            print(f"[sync] failed to remove {d.name}: {e}", file=sys.stderr)

    # Two-pass rename to avoid collisions when two files swap positions.
    if renames:
        staged: list[tuple[Path, Path]] = []
        for i, (src, dst) in enumerate(renames):
            tmp = src.parent / f".__sync_tmp_{i}__{src.name}"
            try:
                src.rename(tmp)
                staged.append((tmp, dst))
            except OSError as e:
                print(f"[sync] failed to stage {src.name}: {e}", file=sys.stderr)
        for tmp, dst in staged:
            try:
                if dst.exists():
                    dst.unlink()
                dst.parent.mkdir(parents=True, exist_ok=True)
                tmp.rename(dst)
                print(f"[sync] renamed: {dst.name}")
            except OSError as e:
                print(f"[sync] failed to rename to {dst.name}: {e}", file=sys.stderr)

    if orphans:
        print(f"[sync] {len(orphans)} file(s) no longer in playlist (kept):")
        for o in orphans:
            print(f"         {o.name}")

    if missing:
        print(f"[sync] {len(missing)} song(s) to download:")
        for pos, title, artist in missing:
            print(f"         {pos:02d} - {artist} - {title}")
    else:
        print("[sync] all playlist tracks already present locally.")

    return 0


if __name__ == "__main__":
    sys.exit(main())
