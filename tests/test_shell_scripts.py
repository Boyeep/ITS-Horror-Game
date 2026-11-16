"""Exercise launcher/build routing without installing packages or opening a game."""
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]


def find_bash():
    if os.name == "nt":
        git = shutil.which("git")
        if git:
            result = subprocess.run([git, "--exec-path"], capture_output=True, text=True, check=True)
            candidate = Path(result.stdout.strip()).parents[2] / "bin/bash.exe"
            if candidate.is_file():
                return str(candidate)
        return None
    return shutil.which("bash")


BASH = find_bash()


@unittest.skipUnless(BASH, "Bash is required to exercise the shell entry points")
class ShellScriptTests(unittest.TestCase):
    def setUp(self):
        self.folder = tempfile.TemporaryDirectory(prefix="game scripts ")
        self.addCleanup(self.folder.cleanup)
        self.root = Path(self.folder.name)
        for name in ("Jalankan.sh", "Build.sh"):
            shutil.copyfile(ROOT / name, self.root / name)
        self.bin = self.root / "fake bin"
        self.bin.mkdir()
        self.env = dict(os.environ, TEST_PLATFORM="Linux", TEST_STATUS="0", TEST_IMPORT_STATUS="0",
                        TEST_LOG="calls.txt", TEST_ENV_PYTHON=".venv/bin/python")
        self.script("fake bin/uname", 'printf "%s\n" "$TEST_PLATFORM"\n')
        self.script("runtime", '''
printf 'python' >> "$TEST_LOG"
printf ' <%s>' "$@" >> "$TEST_LOG"
printf '\n' >> "$TEST_LOG"
if [[ "$1" == -c ]]; then exit "$TEST_IMPORT_STATUS"; fi
if [[ "$1" == main.py ]]; then exit "$TEST_STATUS"; fi
''')
        bootstrap = '''
printf 'bootstrap <%s> <%s> <%s>\n' "$1" "$2" "$3" >> "$TEST_LOG"
mkdir -p "$(dirname "$TEST_ENV_PYTHON")"
cp runtime "$TEST_ENV_PYTHON"
chmod +x "$TEST_ENV_PYTHON"
'''
        self.script("fake bin/python", bootstrap)
        self.script("fake bin/python3", bootstrap)

    def script(self, name, body):
        path = self.root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("#!/usr/bin/env bash\n" + body, encoding="utf-8", newline="\n")
        path.chmod(0o755)

    def runtime(self, platform="Linux"):
        self.env["TEST_PLATFORM"] = platform
        target = ".venv/Scripts/python.exe" if platform.startswith(("MINGW", "MSYS", "CYGWIN")) else ".venv/bin/python"
        self.env["TEST_ENV_PYTHON"] = target
        path = self.root / target
        path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(self.root / "runtime", path)
        path.chmod(0o755)

    def run_script(self, name="Jalankan.sh", *args):
        # Start outside the project, and keep spaces in the project/argument paths.
        return subprocess.run([BASH, "-c", 'export PATH="$(cd "$1" && pwd):$PATH"; shift; bash "$@"',
                               "test", self.bin.as_posix(), (self.root / name).as_posix(), *args],
                              cwd=self.root.parent, env=self.env, capture_output=True, text=True, timeout=20)

    def calls(self):
        path = self.root / "calls.txt"
        return path.read_text(encoding="utf-8") if path.exists() else ""

    def test_posix_existing_environment_and_arguments(self):
        for platform in ("Linux", "Darwin"):
            with self.subTest(platform=platform):
                self.runtime(platform)
                result = self.run_script("Jalankan.sh", "--data-dir", "profile with spaces", "--frames", "1")
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertIn("python <main.py> <--data-dir> <profile with spaces> <--frames> <1>", self.calls())
                self.assertNotIn("bootstrap", self.calls())

    def test_windows_source_reuses_scripts_environment(self):
        self.runtime("MINGW64_NT-10.0")
        result = self.run_script("Jalankan.sh", "--headless")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("python <main.py> <--headless>", self.calls())
        self.assertNotIn("bootstrap", self.calls())

    def test_bootstrap_installs_missing_dependency(self):
        self.env["TEST_IMPORT_STATUS"] = "1"
        result = self.run_script()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("bootstrap <-m> <venv> <.venv>", self.calls())
        self.assertIn("python <-m> <pip> <install> <-r> <requirements.txt>", self.calls())

    def test_windows_executable_is_native_even_with_wine(self):
        self.env["TEST_PLATFORM"] = "MINGW64_NT-10.0"
        self.script("dist/SetelahJamMalam.exe", 'printf "native <%s>\n" "$1" >> "$TEST_LOG"\n')
        self.script("fake bin/wine", 'exit 99\n')
        result = self.run_script("Jalankan.sh", "--headless")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("native <--headless>", self.calls())

    def test_windows_bootstrap_creates_scripts_environment(self):
        self.env.update(TEST_PLATFORM="MINGW64_NT-10.0", TEST_ENV_PYTHON=".venv/Scripts/python.exe")
        result = self.run_script()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("bootstrap <-m> <venv> <.venv>", self.calls())
        self.assertIn("python <main.py>", self.calls())

    def test_posix_wine_forwards_arguments(self):
        self.script("dist/SetelahJamMalam.exe", "exit 99\n")
        self.script("fake bin/wine", 'printf "wine <%s> <%s> <%s>\n" "$1" "$2" "$3" >> "$TEST_LOG"\n')
        result = self.run_script("Jalankan.sh", "--data-dir", "profile with spaces")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("wine <dist/SetelahJamMalam.exe> <--data-dir> <profile with spaces>", self.calls())

    def test_game_failure_preserves_exit_code_without_waiting(self):
        self.runtime()
        self.env["TEST_STATUS"] = "17"
        result = self.run_script()
        self.assertEqual(result.returncode, 17)
        self.assertIn("Game belum dapat dijalankan", result.stderr)

    def test_build_rejects_posix_before_bootstrapping(self):
        result = self.run_script("Build.sh")
        self.assertEqual(result.returncode, 1)
        self.assertIn("hanya didukung pada Windows", result.stderr)
        self.assertEqual(self.calls(), "")

    def test_build_routes_windows_pipeline(self):
        self.runtime("MINGW64_NT-10.0")
        result = self.run_script("Build.sh")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("python <-m> <pip> <install> <-r> <requirements-dev.txt>", self.calls())
        self.assertIn("python <tools/build_release.py>", self.calls())


if __name__ == "__main__":
    unittest.main()
