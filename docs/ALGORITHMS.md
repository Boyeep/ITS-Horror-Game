# Algoritma

## Local search untuk Escape

Simulated Annealing mengoptimalkan kandidat `S = (f1, f2, m1, m2, m3, L)`: dua ruang sekring, tiga ruang spawn monster, dan enam edge tambahan pada graph 6×5 area. Randomized DFS menghasilkan spanning tree `T`; kandidat memakai `G = T ∪ L`, sehingga pergantian edge tambahan tetap mempertahankan keterhubungan.

Hard constraints menolak sasaran/monster duplikat, lokasi terlarang, monster terlalu dekat spawn, dan edge tambahan duplikat. Biaya menggabungkan jarak rute tujuan serta pemisahan ancaman:

```text
r = min(d(spawn,f1)+d(f1,f2)+d(f2,panel),
        d(spawn,f2)+d(f2,f1)+d(f1,panel)) + d(panel,exit)
cost = 1.4 * abs(r - 19)
     + 2.0 * max(0, 5 - d(f1,f2))
     + 0.6 * sum(max(0, 5 - d(spawn,m)))
     + 0.4 * (max(0, 2 - d(m1,m2)) + max(0, 2 - d(m2,m3)))
```

Jarak adalah edge antararea. Neighbor mengubah satu variabel atau edge tambahan. Perbaikan diterima; kenaikan biaya `Δ` diterima dengan probabilitas `exp(-Δ/T)`. Temperatur awal 2,5 menurun ×0,985 dengan minimum 0,025 selama 420 iterasi. Kandidat terbaik disimpan terpisah. Seed menghasilkan layout awal yang dapat diulang; aksi dan timing pemain tetap memengaruhi perjalanan.

Biaya ini parameter desain, bukan pengukuran langsung keseruan. Story memakai map tetap; Simulated Annealing tidak mengacak progres cerita.

## Jalur, noise dan persepsi

A* memakai grid empat arah dan heuristic Manhattan. Lantai berbiaya 1; pintu tertutup berbiaya 2 dan dapat dibuka monster. Collision lingkaran terhadap AABB dengan substep memakai grid yang sama. BFS memvalidasi keterjangkauan sasaran dan exit. Validator tidak memodelkan puzzle cerita; progresi diuji oleh campaign driver terpisah.

Noise mengirim posisi sumber, kekuatan dan jenis aksi. Dijkstra merambatkan suara dengan biaya lantai 1 dan pintu tertutup 3,5, berhenti ketika budget habis. Dinding/furnitur padat menghalangi model akustik sederhana ini. Difficulty dan jenis monster mengalikan budget. Playback audio terpisah: mute tidak mengubah pendengaran AI.

Vision menggunakan jarak, arah hadap, senter, gerakan dan line of sight. Monster mengejar bukti terakhir saat pemain menghilang dari pandangan, mencari di sekitarnya lalu kembali patroli. Penyergap mengunci arah ketika wind-up. Tidak ada koordinat pemain tersembunyi yang disuntikkan ke target monster.

## Kamera, cahaya dan UI

Kamera mengikuti target pemain dengan smoothing `1 - exp(-10*dt)` lalu dijepit pada batas map. Viewport mengikuti rasio layar dengan zoom dekat. Mouse dikonversi ke koordinat dunia melalui zoom dan kamera. Cahaya radial/cone memakai raycast dengan penyempurnaan titik tumbukan. Dunia dikomposisikan terlebih dahulu; teks penting, objek dan karakter ditampilkan pada piksel native.

HUD memisahkan tujuan akhir dari tindakan berikutnya. `guidance.py` mencari langkah yang dapat dijangkau, pintu keluar atau tangga; petunjuk tidak memberikan jawaban puzzle. Cache rute bukan bagian save. Teks dialog muncul bertahap, memakai jeda tanda baca dan pulse suara tiap beberapa karakter; narasi/dokumen hening.

## Persistensi

Save schema 7 menyimpan progres, kondisi pemain, level, pintu, item, puzzle, monster, pendamping dan presentasi aktif. Write atomik serta backup menjaga save terakhir yang valid. Restore menerima schema versi 1 sampai 7 dan memigrasikan interior Informatika lama. Versi produk 0.1 terpisah dari schema tersebut.

## Bacaan konsep

- [Poole & Mackworth, local search dan Simulated Annealing](https://artint.info/3e/html/ArtInt3e.Ch4.S6.html)
- [Shaker, Togelius & Nelson, Procedural Content Generation in Games](https://www.pcgbook.com/)
- [Red Blob Games, A*](https://www.redblobgames.com/pathfinding/a-star/introduction.html)
- [Michael Booth, The AI Systems of Left 4 Dead](https://cdn.fastly.steamstatic.com/apps/valve/2009/ai_systems_of_l4d_mike_booth.pdf) menjadi acuan variasi intensitas. Game ini belum memiliki director adaptif global.

Implementasi berada di `horror/world.py`, `simulation.py`, `guidance.py`, dan modul rendering. [Arsitektur](ARCHITECTURE.md) · [verifikasi](QA.md).
