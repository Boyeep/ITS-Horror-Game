# Presentasi v0.2

[Unduh PowerPoint v0.2](presentations/ETS_KKA_Kelompok_2_ITS_Horror_v0.2.pptx). Presentasi mengikuti desain deck ETS Kelompok 2 sebelumnya; teks, tabel, flowchart, dan grafik tetap dapat diedit. Screenshot berasal dari implementasi game, bukan mockup. Deck v0.1 lokal dipertahankan sebagai sumber riwayat.

Versi ini memperbarui identitas produk, peran algoritma, fitur yang sudah digabungkan, kompatibilitas, dan hasil QA. Navigasi monster memakai **Hill Climbing + Simulated Annealing**, sedangkan A* dipakai oleh waypoint, Nara, dan bot penguji. SA untuk pembangkitan layout Escape tetap merupakan proses tersendiri.

| Slide | Isi |
| --- | --- |
| 1–4 | Identitas kelompok, v0.2, dan deskripsi proyek |
| 5–6 | Latar proyek dan loop Escape |
| 7 | Pembagian peran algoritma yang sesuai source v0.2 |
| 8–14 | Kandidat, cost, aturan SA, flowchart, dan contoh seed 42 |
| 15–16 | Screenshot menu, eksplorasi, tas, dan dialog v0.2 |
| 17 | HC+SA monster, sensor, dan Wave Map |
| 18 | Encounter perpustakaan dan cinematic hasil |
| 19 | Bangunan, waypoint, dan atmosfer |
| 20 | Distribusi, upgrade, dan status prototipe minimap |
| 21 | Hasil pemeriksaan otomatis v0.2 |
| 22 | Batas algoritma dan agenda playtest manusia |
| 23–24 | Rumus cost dan referensi |

Catatan pembicara menyebut sumber lokal dan kredit gambar. Angka QA mengikuti [QA](QA.md) serta [release-review.json](release-review.json); hasil bot tidak disajikan sebagai win-rate atau durasi manusia. Contoh grafik seed 42 hanya menunjukkan satu pencarian generator, bukan jaminan optimum global.

Saat memperbarui deck, gunakan salinan PowerPoint ini, pertahankan tabel/grafik yang dapat diedit, cocokkan klaim dengan source dan laporan terbaru, lalu periksa semua slide hasil render. Jangan mengubah nomor versi pada bukti lama tanpa menjalankan ulang pengujiannya. Tangkapan layar game yang baru dapat dibuat melalui `tools/review_presentation.py --headless`.
