# Changelog

## 0.2 (17 November 2026; kandidat untuk beta)

- Navigasi monster diganti dengan Hill Climbing + Simulated Annealing, peta bukit berbasis sensor, reheat/restart lokal, dan visualisasi split-screen 3D Wave Map (V). A* tidak menjadi planner monster (#9, PR #19).
- Bukaan fisik pintu, corner-slide, dan jangkauan interaksi E diselaraskan dengan kusen visual (#10, PR #20).
- Profil difficulty, tekanan pengejaran, wind-up serangan, cue visual/audio, dan kompatibilitas save monster diperbaiki (#11, PR #24).
- Kematian Story/Escape dan kemenangan Escape mempunyai cinematic sebelum hasil, dengan freeze gameplay, skip/pause, dan pemberian hasil sekali (#12, PR #26).
- Encounter perpustakaan menjadi 12 detik, reveal sesuai spawn gameplay, jeda reaksi 2,2 detik, dan fase kejar yang berlanjut melalui lantai (#13, PR #25).
- Tangga berpasangan, jendela courtyard, dan footprint atap luar Informatika diperbaiki tanpa mengubah collision gameplay (#14, PR #27).
- Variasi permukaan/dekor prosedural serta empat rekaman radio/buku menambah koleksi menjadi 73 media aktif; prioritas stinger, detak/napas, lifecycle audio, dan reduced motion diuji (#15–#16, PR #23).
- Waypoint memilih rute terjangkau dengan hysteresis, lookahead, clearance, dan invalidasi cache; HUD, M, serta prompt pintu/tangga konsisten (#18, PR #28).
- Evaluasi minimap dan prototipe default mati disertakan sebagai tool terpisah; penerapan produksi ditunda sampai ada bukti playtest manusia (#17, PR #29).
- `Jalankan.sh` mendukung Linux/macOS dan Git Bash, meneruskan argumen, serta memilih interpreter platform yang benar. `Build.sh` menyediakan entry point build Windows (PR #21).
- README, panduan, laporan QA, metadata Windows, dan presentasi diperbarui untuk v0.2.

Save schema tetap 7 dan pembaca versi 1–7 dipertahankan. Identitas Windows berubah menjadi 0.2.0.0. Persiapan ini belum membuat tag atau menerbitkan GitHub Release; [catatan v0.2](https://github.com/Boyeep/ITS-Horror-Game/blob/v0.2/docs/RELEASE_NOTES.md) dan [QA](https://github.com/Boyeep/ITS-Horror-Game/blob/v0.2/docs/QA.md) menjelaskan batas bukti.

## 0.1 (28 Oktober 2026)

Rilis awal pengembangan. Nomor patch yang pernah muncul sebelum rilis ini merupakan penanda internal; baseline tersebut ditetapkan sebagai versi 0.1.

- Story Mode tiga bab dan 25 tahap dengan prolog, empat adegan penting, puzzle, bukti, pendamping, serta ending.
- Escape dengan map 30 area, seed, Simulated Annealing, tiga monster, sensor pandangan dan noise.
- HP, stamina, backpack, tujuh jenis perlengkapan, serta 15 pencapaian lokal.
- Tiga slot manual, autosave, cadangan, dan pemulihan save lama.
- Kamera mengikuti pemain, pintu bercahaya saat disenter, UI native, dialog bertahap dan blip percakapan orisinal.
- Menu tiga foto kampus dengan grading horor dan lambang ITS.
- Tampilan aplikasi, render dunia/HUD, data cerita dan serialisasi save dipisah ke modul tersendiri.
- Nomor rilis dipusatkan; build menghasilkan manifest dan metadata Windows dari sumber yang sama.
- 83 aset yang telah tergantikan dihapus; importer dan manifest aset diperbarui. Lisensi serta sumber aset aktif tetap disertakan.

Format save tetap versi 7; perubahan nomor rilis tidak mereset data pemain.
