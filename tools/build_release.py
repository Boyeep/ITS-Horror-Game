"""Build the Windows executable and portable ZIP from one release identity."""
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from horror.version import VERSION, WINDOWS_VERSION


def write_metadata(destination):
    destination.mkdir(parents=True, exist_ok=True)
    manifest = destination / "windows.manifest"
    template = (ROOT / "tools/windows.manifest").read_text(encoding="utf-8")
    manifest.write_text(template.replace("@WINDOWS_VERSION@", WINDOWS_VERSION), encoding="utf-8")
    version_file = destination / "version-info.txt"
    numbers = tuple(map(int, WINDOWS_VERSION.split(".")))
    version_file.write_text(f'''VSVersionInfo(
  ffi=FixedFileInfo(filevers={numbers!r}, prodvers={numbers!r},
    mask=0x3f, flags=0, OS=0x40004, fileType=1, subtype=0, date=(0, 0)),
  kids=[StringFileInfo([StringTable('040904B0', [
    StringStruct('FileDescription', 'Setelah Jam Malam'),
    StringStruct('FileVersion', '{VERSION}'),
    StringStruct('ProductName', 'Setelah Jam Malam'),
    StringStruct('ProductVersion', '{VERSION}'),
    StringStruct('OriginalFilename', 'SetelahJamMalam.exe')])]),
    VarFileInfo([VarStruct('Translation', [1033, 1200])])])
''', encoding="utf-8")
    return manifest, version_file


def main():
    from audit_assets import audit
    report = audit()
    if report["unused"]:
        raise SystemExit("Unused runtime assets found; run tools/audit_assets.py and review them.")
    manifest, version_file = write_metadata(ROOT / "build/release")
    subprocess.run([sys.executable, "-m", "PyInstaller", "--noconfirm", "--clean",
                    "--onefile", "--windowed", "--add-data", "assets;assets",
                    "--manifest", str(manifest), "--version-file", str(version_file),
                    "--name", "SetelahJamMalam", "main.py"], cwd=ROOT, check=True)
    from package_release import main as package
    package()


if __name__ == "__main__":
    main()
