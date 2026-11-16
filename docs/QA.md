# Verifikasi kandidat v0.2

Pemeriksaan ulang 17 November 2026 setelah seluruh PR fitur masuk `v0.2`. Lingkungan: Windows 11 x64, Python 3.12.10, pygame-ce 2.5.8, PyInstaller 6.22.3. Mixer stereo 44.100 Hz / signed 16-bit. Ini bukti kandidat integrasi ke `beta`, bukan pengumuman GitHub Release.

| Pemeriksaan | Bukti |
| --- | --- |
| Unit/integration, shell launcher, save dan regresi fitur | **199/199 lolos**; [release-review.json](release-review.json) |
| Generator Escape | **100/100 seed valid**; cost Simulated Annealing membaik pada 98 seed; [data generator](reviews/release-v0.2/generator.json) |
| Aset aktif, pemuatan semua jenis level, varian furnitur/lantai, bank audio dan hash | [assets-audit.json](assets-audit.json) |
| Berkas aset yang dihapus, ukuran, hash dan alasan | [asset-cleanup.json](asset-cleanup.json) |
| Semua 25 tahap hingga ending | **4/4 skenario** pada eksekusi ini; tanpa monster HP 100, Easy/Normal/Hard dengan monster HP **96/84/90**; [story-probe.json](story-probe.json) |
| Render native, menu, stairs, pintu, dokumen, item, objective dan cutscene | **55 capture**, 1280×800; [presentation-review.json](presentation-review.json) |
| Window/mixer Windows dan handoff intro ke kontrol | [native-window.json](native-window.json) |
| Executable dari working directory lain | **9/9 skenario lolos**; [compiled-smoke.json](compiled-smoke.json) |
| CRC ZIP, hash EXE, versi Windows dan aset dalam bundle | [release-review.json](release-review.json) |
| Waktu frame offscreen pada satu perangkat | [performance-review.json](performance-review.json); bukan FPS pengguna |
| Presentasi dan isi rilis | [PowerPoint v0.2](PRESENTATION.md), [catatan upgrade](RELEASE_NOTES.md) |

Metadata executable dan manifest Windows **0.2.0.0** sesuai versi produk **0.2**. Seluruh **83 berkas aset** dalam executable cocok dengan source, termasuk metadata/lisensi; **73** di antaranya media aktif. Audit tidak menemukan media runtime yang tidak terpakai. Pemeriksaan tautan lokal dokumentasi juga lolos. Save schema tetap **7**, dengan pembaca versi 1–7.

Laporan top-level mencerminkan kandidat v0.2. Dokumen tiap tiket dan isi `reviews/` mempertahankan hasil pengujian saat PR tersebut dikerjakan; angka subsetnya tidak menggantikan 199 tes gabungan. `asset-cleanup.json` merupakan riwayat cleanup v0.1. Versi lama di laporan historis tidak diubah menjadi hasil baru.

## Menjalankan ulang

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests *> build/unit-test.log
.\.venv\Scripts\python.exe main.py --validate 100
.\.venv\Scripts\python.exe tools/audit_assets.py
.\.venv\Scripts\python.exe tools/story_probe.py
.\.venv\Scripts\python.exe tools/review_presentation.py --headless
.\.venv\Scripts\python.exe tools/performance_probe.py
.\.venv\Scripts\python.exe tools/native_smoke.py
.\Build.bat
.\.venv\Scripts\python.exe tools/frozen_smoke.py
.\.venv\Scripts\python.exe tools/verify_release.py
```

Review tools menimpa laporan/screenshot hasil generasi. Jalankan dari root proyek. `tools/performance_probe.py` tersedia untuk pengukuran frame offscreen bila mengubah rendering; angka tersebut tidak mewakili latensi monitor atau semua perangkat.

## Batas bukti

Regresi v0.2 mencakup HC+SA/sensor, wind-up/cooldown, encounter dan save/load, freeze/hasil sekali pada cinematic terminal, geometri tangga/atap/courtyard, waypoint/cache, serta lifecycle dan prioritas cue atmosfer. Tes minimap hanya menguji tool evaluasi terpisah yang default mati; game utama tidak mengaktifkannya.

Campaign bot mengetahui peta dan jawaban, melewati dialog/cutscene, serta memakai supply yang ditemui. Ia bergerak melalui collision/pintu/stairs sebenarnya, tanpa teleportasi atau memberi HP/item. Waktu simulasi bukan durasi tamat atau win-rate manusia.

Empat skenario campaign di atas membuktikan jalur yang dicoba dapat selesai; hasilnya bukan jaminan semua pola gerak akan menang. Laporan bot per-ticket dapat berbeda karena kode/pola perjalanan pada saat itu berbeda. HC+SA tidak menjamin rute terpendek atau optimum global. Wine, Linux dan macOS belum diuji langsung dalam persiapan Windows ini.

Tes mencakup render tanpa mutasi snapshot/kamera, restore save lama, batas inventory, persepsi berbasis bukti, occlusion cahaya, dan strip cahaya pintu minimal dua piksel sebelum interpolasi native. Screenshot membantu memeriksa komposisi; rasa takut, kualitas suara subjektif dan keterbacaan pemain baru tetap membutuhkan playtest manusia.

Map merupakan interpretasi fiksi, bukan survei 1:1 bangunan. Paket portable diuji lokal pada Windows pengembangan. [Acuan ITS](ITS_REFERENCES.md) dan [kredit](../THIRD_PARTY_NOTICES.md).
