# Setelah Jam Malam v0.2

Kandidat integrasi ke `beta`, disiapkan 17 November 2026. Nomor produk **0.2**, metadata Windows **0.2.0.0**, save schema **7**. Penyiapan branch dan PR tidak menerbitkan tag atau GitHub Release.

## Perubahan dari v0.1

| Bagian | Perilaku v0.2 | Rujukan |
| --- | --- | --- |
| AI monster | Hill Climbing + Simulated Annealing pada bukit lokal; sensor menentukan bukti yang boleh dipakai. Reheat, memori jejak, dan restart membantu keluar dari macet. V membuka 3D Wave Map. A* hanya untuk sistem bantu. | [Algoritma](https://github.com/Boyeep/ITS-Horror-Game/blob/v0.2/docs/ALGORITHMS.md), #9 / PR #19 |
| Pintu | Bukaan fisik sesuai kusen, corner-slide dan prompt E lebih mudah didekati. | #10 / PR #20 |
| Difficulty | Easy mempertahankan kecepatan lama; Normal/Hard menambah tekanan. Wind-up dan cue serangan memberi kesempatan bereaksi. | [Balancing](https://github.com/Boyeep/ITS-Horror-Game/blob/v0.2/docs/MONSTER_BALANCE.md), #11 / PR #24 |
| Perpustakaan | Adegan 12 detik memakai reveal/spawn yang sama, jeda reaksi 2,2 detik, lalu pengejaran berbasis sensor yang dapat berlanjut melalui lantai. | [Encounter](https://github.com/Boyeep/ITS-Horror-Game/blob/v0.2/docs/LIBRARY_ENCOUNTER.md), #13 / PR #25 |
| Hasil permainan | Kematian Story/Escape dan kemenangan Escape mendapat presentasi frame beku sebelum layar hasil. Skip/pause/resume ditangani; ending Story tetap satu kali. | [Cinematic](https://github.com/Boyeep/ITS-Horror-Game/blob/v0.2/docs/RESULT_CINEMATICS.md), #12 / PR #26 |
| Bangunan | Flight tangga berpasangan memakai bay yang konsisten; jendela courtyard dan footprint atap Informatika diperbaiki. | [Bangunan](https://github.com/Boyeep/ITS-Horror-Game/blob/v0.2/docs/BUILDING_REVIEW.md), #14 / PR #27 |
| Aset dan atmosfer | Dekor/permukaan prosedural, empat rekaman radio/buku, detak/napas dan efek visual. Cue utama mendapat prioritas; pause/modal/mute menghentikan atmosfer opsional. | [Atmosfer](https://github.com/Boyeep/ITS-Horror-Game/blob/v0.2/docs/ATMOSPHERE_REVIEW.md), #15–#16 / PR #23 |
| Petunjuk | Waypoint memilih rute terjangkau, menahan pergantian target yang tidak perlu, dan menyamakan tindakan berikut pada HUD, prompt, serta M. | [Waypoint](https://github.com/Boyeep/ITS-Horror-Game/blob/v0.2/docs/WAYPOINT_REVIEW.md), #18 / PR #28 |
| Minimap | Tool evaluasi terpisah, default mati dan memakai fog informasi yang sudah terlihat. Belum menjadi fitur produksi. | [Evaluasi](https://github.com/Boyeep/ITS-Horror-Game/blob/v0.2/docs/MINIMAP_EVALUATION.md), #17 / PR #29 |
| Launcher | Source dapat dijalankan dengan `Jalankan.sh` di Linux/macOS; Git Bash memakai interpreter Windows yang benar. Build executable tetap Windows. | PR #21, [README](https://github.com/Boyeep/ITS-Horror-Game/blob/v0.2/README.md) |

## Memperbarui dari v0.1

1. Tutup game. Bila perlu, salin `%APPDATA%/ITS-Horror-Game/` sebagai cadangan pribadi.
2. Ekstrak paket v0.2 ke folder baru. Jalankan executable baru dari folder tersebut; jangan memakai executable v0.1 yang masih berada di folder lama.
3. Pertahankan folder data pengguna. Pengaturan, pencapaian, tiga slot manual, dan autosave tetap memakai lokasi yang sama.
4. Buka **Lanjut cerita** atau **Muat permainan**. Pembaca menerima save schema 1–7; versi produk tidak mengubah schema. Migrasi interior/prolog lama mengikuti aturan [Story Mode](https://github.com/Boyeep/ITS-Horror-Game/blob/v0.2/docs/STORY_MODE.md).

Linux/macOS memerlukan Python 3.12 dengan `venv` dan dependency proyek bila bermain dari source. Paket `.exe`/ZIP diuji pada Windows x64; launcher Wine tidak berarti kompatibilitas Wine/macOS telah diuji langsung.

## Bukti dan batas penerimaan

[QA v0.2](https://github.com/Boyeep/ITS-Horror-Game/blob/v0.2/docs/QA.md) dan [laporan paket](https://github.com/Boyeep/ITS-Horror-Game/blob/v0.2/docs/release-review.json) mencatat hasil otomatis, metadata executable, audit aset, serta smoke test. Presentasi tersedia pada [halaman PowerPoint](https://github.com/Boyeep/ITS-Horror-Game/blob/v0.2/docs/PRESENTATION.md).

Bot campaign mengetahui rute dan jawaban; screenshot tidak mengukur ketakutan, fairness, durasi tamat, atau kemudahan pemain baru. Playtest manusia untuk balancing, pacing perpustakaan, waypoint, dan campuran audio tetap diperlukan. HC+SA adalah local search; rutenya tidak dijamin terpendek atau selalu setara planner global. Performa offscreen berasal dari satu perangkat pengembangan. Map adalah adaptasi fiksi, bukan replika 1:1 ITS.

Riwayat review pada `docs/reviews/` tetap memakai angka, commit, dan identitas produk ketika pemeriksaan itu dijalankan. Jangan mengganti label laporan lama menjadi v0.2 tanpa mengulang pemeriksaannya.
