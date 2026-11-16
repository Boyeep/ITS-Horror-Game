# Audit bangunan v0.2 — #14

Prioritas audit adalah akses Informatika, perpustakaan dan Robotika pada rute Story. Bangunan tetap merupakan adaptasi fiksi; perubahan ini tidak mengklaim denah atau skala kampus nyata yang baru.

| Lokasi / temuan | Sebelum | Perbaikan |
| --- | --- | --- |
| Informatika lantai 2, flight NW/NE | Pusat tangga terpisah 80 px, gambar tinggi 112 px: overlap 32 px | Ukuran bersama 60×76, tanpa overlap |
| Informatika flight SW/SE | Pusat terpisah 80 px, gambar lebar 88 px: overlap 8 px | Ukuran baru menyisakan jarak 20 px |
| Informatika courtyard lantai atas | Jendela top border digambar melintasi bagian yang tidak dihuni | Bay jendela hanya pada span dinding dengan ruang di bawahnya; dua bay pada sayap atas |
| Informatika eksterior kampus | Seluruh massa padat tampak sebagai susunan tile dinding | Atap menyatu, trim tepi, kaca fasad dan ventilasi mengikuti tepat sel collision padat |
| Perpustakaan, Robotika, Rektorat, Teknik Mesin | Flight naik dan turun generik berada di sudut berlawanan | Flight lawan berbagi bay barat daya: turun (5,19), naik (8,19), terpisah 120 px |

Ukuran tangga dipakai oleh renderer native dan helper bounds pada `architecture.py`; anchor berada di pusat interaksi. Flight naik/turun tetap memiliki gambar berbeda, skala terhadap pemain/pintu konsisten, serta ambang interaksi yang sama. Pintu dan lebar collision #10 dipertahankan.

Atap hanya menggambar sel `informatika_cells` yang bernilai wall. Courtyard, jalan, celah masuk dan interior walkable tidak ditimpa. Collision tidak dibuat dari gambar; renderer hanya membaca grid yang sama dengan navigasi. Furnitur generik menghindari bay tangga baru. Lantai Informatika tetap memakai pasangan portal NW/NE/SW/SE yang sudah sesuai.

Save schema 7 tetap berlaku. Posisi/progres lama dipertahankan; mekanisme restore nearest-floor yang sudah ada memulihkan posisi yang kini berimpit dengan furnitur. Waypoint memakai titik tangga baru dari layout, bukan koordinat yang disalin ke save.

| Bukti | Sebelum | Sesudah |
| --- | --- | --- |
| Massa eksterior Informatika | [overview](reviews/buildings/before/campus-overview.png) | [overview](reviews/buildings/after/campus-overview.png) |
| Courtyard dan flight Informatika | [overview](reviews/buildings/before/11-1-overview.png) | [overview](reviews/buildings/after/11-1-overview.png) |
| Tangga dalam gameplay | [gameplay](reviews/buildings/before/paired-stairs-gameplay.png) | [gameplay](reviews/buildings/after/paired-stairs-gameplay.png) |
| Bay perpustakaan | [overview](reviews/buildings/before/22-1-overview.png) | [overview](reviews/buildings/after/22-1-overview.png) |
| Bay Robotika | [overview](reviews/buildings/before/5-2-overview.png) | [overview](reviews/buildings/after/5-2-overview.png) |

Overview menampilkan bake tanpa pencahayaan dan prop arsitektur pada ukuran dunia; capture gameplay memakai lighting/HUD runtime. Reproduksi: `python tools/review_buildings.py --output build/building-review`. [Metadata sebelum](reviews/buildings/before/report.json) / [sesudah](reviews/buildings/after/report.json).

Tes memeriksa bounds setiap flight, posisi jendela, semua jalur objective/tangga, transfer lantai, save lama dan grid yang tidak berubah ketika atap dirender. [Campaign probe](reviews/buildings/story-probe.json) menamatkan seluruh 25 tahap/24 transfer pada Easy; Normal/Hard mati ketika ancaman aktif. Pesan aksi bot setelah kematian tidak dianggap bukti geometri terputus. Seluruh objective juga diverifikasi secara struktural, dan kasus pintu Escape pada seed 1/7/19/42/73 tercakup tes regresi. Capture/probe bukan penilaian pemain baru atas navigasi.
