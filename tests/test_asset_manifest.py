"""A glob-loaded cue must never bypass the asset manifest and credits audit."""
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from tools.audit_assets import audit_manifest


class AssetManifestTests(unittest.TestCase):
    def setUp(self):
        self.folder = tempfile.TemporaryDirectory()
        self.addCleanup(self.folder.cleanup)
        self.path = Path(self.folder.name) / "story_audio"
        self.path.mkdir()
        (self.path / "radio_1.ogg").write_bytes(b"recorded media")
        self.entry = {"file": "radio_1.ogg", "sha256": hashlib.sha256(b"recorded media").hexdigest(),
                      "author": "Test author", "page": "https://example.org/source", "license": "CC0-1.0"}

    def manifest(self):
        (self.path / "manifest.json").write_text(json.dumps({"files": [self.entry]}), encoding="utf-8")

    def test_valid_manifest_and_credit(self):
        self.manifest()
        audit_manifest(self.path)

    def test_extra_recording_is_rejected_even_with_valid_existing_hashes(self):
        self.manifest()
        (self.path / "book_1.ogg").write_bytes(b"unrecorded media")
        with self.assertRaisesRegex(AssertionError, "Media missing from manifest"):
            audit_manifest(self.path)

    def test_changed_recording_is_rejected(self):
        self.manifest()
        (self.path / "radio_1.ogg").write_bytes(b"replaced media")
        with self.assertRaisesRegex(AssertionError, "Asset hash mismatch"):
            audit_manifest(self.path)

    def test_missing_credit_is_rejected(self):
        del self.entry["license"]
        self.manifest()
        with self.assertRaisesRegex(AssertionError, "Missing story audio credit"):
            audit_manifest(self.path)
