"""Add one CC0 sound to assets/story_audio: copy it, hash it, write the manifest entry and the credit line.

Usage:
  python tools/add_story_audio.py SOURCE TARGET --author NAME --page URL

TARGET is the bundled name, one of radio_N, distant_N, book_N, tape_N, valve_N, tune_N, drink_N or deploy_N
with .ogg, .wav or .mp3 (for example distant_2.ogg). The game loads every file that matches a cue name and
falls back to its older borrowed foley when none exist. Afterwards run: python tools/audit_assets.py
"""
import argparse
import hashlib
import json
import re
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FOLDER = ROOT / "assets/story_audio"
CUES = ("radio", "distant", "book", "tape", "valve", "tune", "drink", "deploy")
ACCEPTED_LICENSES = {"CC0-1.0"}


def line_ending(text):
    return "\r\n" if "\r\n" in text else "\n"


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("source")
    parser.add_argument("target")
    parser.add_argument("--author", required=True)
    parser.add_argument("--page", required=True, help="URL of the page the sound was downloaded from")
    parser.add_argument("--license", default="CC0-1.0")
    parser.add_argument("--force", action="store_true", help="replace an existing file with the same name")
    args = parser.parse_args(argv)
    source, target = Path(args.source), args.target
    if not source.is_file():
        return f"Source file not found: {source}"
    if args.license not in ACCEPTED_LICENSES:
        return f"License {args.license} is not accepted; this project bundles CC0-1.0 sounds only."
    if not re.fullmatch(r"(" + "|".join(CUES) + r")_\d+\.(ogg|wav|mp3)", target):
        return f"TARGET must look like distant_2.ogg (cues: {', '.join(CUES)})."
    if source.suffix.lower() != Path(target).suffix:
        return f"TARGET extension {Path(target).suffix} does not match the source file ({source.suffix}); convert it first."
    if not args.page.startswith(("http://", "https://")):
        return "--page must be the https:// address of the page the sound came from."
    destination = FOLDER / target
    if destination.exists() and not args.force:
        return f"{target} already exists; pass --force to replace it."
    shutil.copyfile(source, destination)
    digest = hashlib.sha256(destination.read_bytes()).hexdigest()

    manifest_path = FOLDER / "manifest.json"
    raw = manifest_path.read_bytes().decode("utf-8")
    eol = line_ending(raw)
    manifest = json.loads(raw)
    entry = {"file": target, "author": args.author, "page": args.page, "license": args.license, "sha256": digest}
    manifest["files"] = [item for item in manifest["files"] if item["file"] != target] + [entry]
    text = json.dumps(manifest, indent=2).replace("\n", eol) + (eol if raw.endswith(eol) else "")
    manifest_path.write_bytes(text.encode("utf-8"))

    credits_path = FOLDER / "CREDITS.txt"
    raw = credits_path.read_bytes().decode("utf-8")
    eol = line_ending(raw)
    lines = [line for line in raw.splitlines() if not line.startswith(target + " - ")]
    lines.append(f"{target} - {args.author} - {args.license} - {args.page}")
    credits_path.write_bytes((eol.join(lines) + (eol if raw.endswith(eol) else "")).encode("utf-8"))

    print(f"Added {target} (sha256 {digest[:12]}...). Next: note it in THIRD_PARTY_NOTICES.md and run tools/audit_assets.py")
    return 0


if __name__ == "__main__":
    sys.exit(main())