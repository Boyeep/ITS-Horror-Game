# Verifikasi rilis 0.1

Lingkungan: Windows 11 x64, Python 3.12.10, pygame-ce 2.5.8, PyInstaller 6.22.3. Mixer stereo 44.100 Hz / signed 16-bit. Hasil rilis dicatat setelah cleanup dan modularisasi, bukan diwarisi dari nomor patch pengembangan.

| Pemeriksaan | Bukti |
| --- | --- |
| Unit/integration dan kompatibilitas save | **102/102 lolos**; [release-review.json](release-review.json) |
| Generator Escape | **100/100 seed valid**; cost Simulated Annealing membaik pada 98 seed |
| Aset aktif, pemuatan semua jenis level, varian furnitur/lantai, bank audio dan hash | [assets-audit.json](assets-audit.json) |
| Berkas aset yang dihapus, ukuran, hash dan alasan | [asset-cleanup.json](asset-cleanup.json) |
| Semua 25 tahap hingga ending | **4/4 skenario**; Easy/Normal/Hard dengan monster berakhir pada HP 76/74/72; [story-probe.json](story-probe.json) |
| Render native, menu, stairs, pintu, dokumen, item, objective dan cutscene | [presentation-review.json](presentation-review.json) |
| Window/mixer Windows dan handoff intro ke kontrol | [native-window.json](native-window.json) |
| Executable dari working directory lain | **9/9 skenario lolos**; [compiled-smoke.json](compiled-smoke.json) |
| CRC ZIP, hash EXE, versi Windows dan aset dalam bundle | [release-review.json](release-review.json) |

Metadata executable dan manifest Windows **0.1.0.0** sesuai versi produk **0.1**. Seluruh **79 berkas aset** dalam executable cocok dengan source, termasuk metadata/lisensi; 69 di antaranya media aktif. Audit tidak menemukan media runtime yang tidak terpakai. Pemeriksaan tautan lokal dokumentasi juga lolos.

## Menjalankan ulang

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests
.\.venv\Scripts\python.exe main.py --validate 100
.\.venv\Scripts\python.exe tools/audit_assets.py
.\.venv\Scripts\python.exe tools/story_probe.py
.\.venv\Scripts\python.exe tools/review_presentation.py --headless
.\.venv\Scripts\python.exe tools/native_smoke.py
.\Build.bat
.\.venv\Scripts\python.exe tools/frozen_smoke.py
.\.venv\Scripts\python.exe tools/verify_release.py
```

Review tools menimpa laporan/screenshot hasil generasi. Jalankan dari root proyek. `tools/performance_probe.py` tersedia untuk pengukuran frame offscreen bila mengubah rendering; angka tersebut tidak mewakili latensi monitor atau semua perangkat.

## Batas bukti

Campaign bot mengetahui peta dan jawaban, melewati dialog/cutscene, serta memakai supply yang ditemui. Ia bergerak melalui collision/pintu/stairs sebenarnya, tanpa teleportasi atau memberi HP/item. Waktu simulasi bukan durasi tamat atau win-rate manusia.

Tes mencakup render tanpa mutasi snapshot/kamera, restore save lama, batas inventory, persepsi berbasis bukti, occlusion cahaya, dan strip cahaya pintu minimal dua piksel sebelum interpolasi native. Screenshot membantu memeriksa komposisi; rasa takut, kualitas suara subjektif dan keterbacaan pemain baru tetap membutuhkan playtest manusia.

Map merupakan interpretasi fiksi, bukan survei 1:1 bangunan. Paket portable diuji lokal pada Windows pengembangan. [Acuan ITS](ITS_REFERENCES.md) dan [kredit](../THIRD_PARTY_NOTICES.md).
