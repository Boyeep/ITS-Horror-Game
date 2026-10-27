"""Assemble a portable Windows archive from an already-built executable."""
import shutil
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from horror.version import VERSION


def main():
    import pygame
    dist = ROOT / "dist"
    exe = dist / "SetelahJamMalam.exe"
    if not exe.is_file():
        raise SystemExit("Build the executable first using Build.bat.")
    licenses = dist / "licenses"
    licenses.mkdir(parents=True, exist_ok=True)
    sources = {
        "Python-LICENSE.txt": Path(sys.base_prefix) / "LICENSE.txt",
        "pygame-ce-LGPL.txt": Path(pygame.__file__).parent / "docs/generated/LGPL.txt",
        "Kenney-CC0.txt": ROOT / "assets/kenney/License.txt",
        "Kenney-impact-CC0.txt": ROOT / "assets/audio/impact-License.txt",
        "Kenney-rpg-CC0.txt": ROOT / "assets/audio/rpg-License.txt",
        "Story-audio-CC0.txt": ROOT / "assets/story_audio/CREDITS.txt",
    }
    for name, source in sources.items():
        shutil.copyfile(source, licenses / name)
    docs = dist / "docs"
    docs.mkdir(parents=True, exist_ok=True)
    for name in ("ITS_REFERENCES.md", "PLAYER_GUIDE.md"):
        shutil.copyfile(ROOT / "docs" / name, docs / name)
    shutil.copyfile(ROOT / "THIRD_PARTY_NOTICES.md", dist / "THIRD_PARTY_NOTICES.md")
    shutil.copyfile(ROOT / "CHANGELOG.md", dist / "CHANGELOG.md")
    readme = dist / "BACA_DULU.txt"
    guide = (ROOT / "docs/PLAYER_GUIDE.md").read_text(encoding="utf-8")
    readme.write_text(f"SETELAH JAM MALAM — Versi {VERSION} / Windows x64\n\n" + guide, encoding="utf-8")
    archive = dist / "SetelahJamMalam-Windows-x64.zip"
    files = [exe, readme, dist / "THIRD_PARTY_NOTICES.md", dist / "CHANGELOG.md",
             docs / "ITS_REFERENCES.md", docs / "PLAYER_GUIDE.md",
             *(licenses / name for name in sources)]
    with zipfile.ZipFile(archive, "w", compression=zipfile.ZIP_DEFLATED) as package:
        for path in files:
            package.write(path, path.relative_to(dist))
    print(f"Release {VERSION}: {archive.name} ({archive.stat().st_size / 1024 / 1024:.1f} MiB)")


if __name__ == "__main__":
    main()
