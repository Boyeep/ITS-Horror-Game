"""Verify the actual portable artifact, embedded assets and local documentation links."""
import hashlib
from datetime import datetime, timezone
import json
import re
import sys
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path
from urllib.parse import unquote

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from horror.version import VERSION, WINDOWS_VERSION


def documentation_links():
    checked = 0
    for path in [*ROOT.glob("*.md"), *ROOT.joinpath("docs").glob("*.md")]:
        for target in re.findall(r"!?\[[^\]]*\]\(([^\n]+?)\)", path.read_text(encoding="utf-8")):
            target = target.strip("<>").split("#")[0]
            if not target or re.match(r"[a-z]+://", target):
                continue
            if not (path.parent / unquote(target)).exists():
                raise AssertionError(f"Broken documentation link: {path.name} -> {target}")
            checked += 1
    return checked


def main():
    import pefile
    from PyInstaller.archive.readers import CArchiveReader

    dist = ROOT / "dist"
    exe = dist / "SetelahJamMalam.exe"
    archive = dist / "SetelahJamMalam-Windows-x64.zip"
    exe_hash = hashlib.sha256(exe.read_bytes()).hexdigest()
    with zipfile.ZipFile(archive) as package:
        assert package.testzip() is None, "Invalid ZIP CRC"
        assert hashlib.sha256(package.read(exe.name)).hexdigest() == exe_hash
        assert f"Versi {VERSION}" in package.read("BACA_DULU.txt").decode("utf-8")
        assert len([n for n in package.namelist() if n.startswith("licenses/")]) == 6
        assert "docs/PLAYER_GUIDE.md" in package.namelist()

    with pefile.PE(str(exe)) as pe:
        fixed = pe.VS_FIXEDFILEINFO[0]
        numbers = (fixed.FileVersionMS >> 16, fixed.FileVersionMS & 65535,
                   fixed.FileVersionLS >> 16, fixed.FileVersionLS & 65535)
        assert ".".join(map(str, numbers)) == WINDOWS_VERSION
        manifests = []
        for kind in pe.DIRECTORY_ENTRY_RESOURCE.entries:
            if kind.id == 24:
                for name in kind.directory.entries:
                    for lang in name.directory.entries:
                        data = lang.data.struct
                        manifests.append(pe.get_data(data.OffsetToData, data.Size))
        manifest = ET.fromstring(manifests[0])
        identity = manifest.find("{urn:schemas-microsoft-com:asm.v1}assemblyIdentity")
        assert identity.attrib["version"] == WINDOWS_VERSION
        assert b"PerMonitorV2" in manifests[0]

    bundle = CArchiveReader(str(exe))
    embedded = {n.replace("\\", "/"): n for n in bundle.toc if n.startswith("assets")}
    source = {p.relative_to(ROOT).as_posix(): p for p in (ROOT / "assets").rglob("*") if p.is_file()}
    assert set(embedded) == set(source), "Embedded asset set differs from source"
    for name, path in source.items():
        assert hashlib.sha256(bundle.extract(embedded[name])).digest() == hashlib.sha256(path.read_bytes()).digest(), name
    audit = json.loads((ROOT / "docs/assets-audit.json").read_text(encoding="utf-8"))
    assert not audit["unused"] and audit["version"] == VERSION
    log = (ROOT / "build/unit-test.log").read_text(encoding="utf-8")
    assert re.search(r"\nOK\s*$", log), "Unit test log does not report success"
    tests = int(re.search(r"Ran (\d+) tests", log).group(1))
    frozen = json.loads((ROOT / "docs/compiled-smoke.json").read_text(encoding="utf-8"))
    report = {"version": VERSION, "windows_version": WINDOWS_VERSION,
              "reviewed_utc": datetime.now(timezone.utc).isoformat(), "unit_tests": tests,
              "zip_crc": "passed", "exe_matches_zip": True, "exe_sha256": exe_hash,
              "exe_bytes": exe.stat().st_size, "zip_bytes": archive.stat().st_size,
              "embedded_assets_verified": len(source), "active_media": audit["loaded_count"],
              "documentation_links_checked": documentation_links(), "frozen_smoke_report": frozen}
    (ROOT / "docs/release-review.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(f"Release {VERSION} verified: {tests} tests, {len(source)} embedded asset files, valid ZIP, matching Windows metadata.")


if __name__ == "__main__":
    main()
