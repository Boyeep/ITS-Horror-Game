# Evaluasi minimap opsional — #17

Keputusan: **tunda penerapan penuh**. Pertahankan M dan waypoint yang diperbaiki pada #18 sebagai navigasi utama. Prototipe tersedia untuk perbandingan, tetapi belum ada bukti pemain baru bahwa tambahan HUD memperbaiki orientasi tanpa mengurangi perhatian pada dunia dan ketegangan. Menambah minimap ke produk sebelum bukti itu bertentangan dengan batas eksplorasi tiket.

`tools/minimap_prototype.py` adalah alat review, tidak diimpor `main.py` atau dikemas sebagai fitur game. `python tools/minimap_prototype.py --interactive --story` membuka Story dengan profil sementara; tanpa `--story` memakai Escape seed 42. Tekan I untuk toggle, default mati. M dan kontrol game biasa tetap tersedia. Tanpa `--interactive`, tool membuat capture deterministik tanpa membuka window native.

| Kondisi | HUD / waypoint | Peta M | Prototipe opsional |
| --- | --- | --- | --- |
| Kampus Story | [HUD](reviews/minimap/campus-hud.png) | [M](reviews/minimap/campus-map.png) | [minimap](reviews/minimap/campus-minimap.png) |
| Interior perpustakaan | [HUD](reviews/minimap/interior-hud.png) | [M](reviews/minimap/interior-map.png) | [minimap](reviews/minimap/interior-minimap.png) |
| Escape | [HUD](reviews/minimap/escape-hud.png) | [M](reviews/minimap/escape-map.png) | [minimap](reviews/minimap/escape-minimap.png) |

| Pilihan | Manfaat yang dapat diperiksa | Risiko / hal yang belum diketahui |
| --- | --- | --- |
| M + waypoint #18 | Rute langkah berikut sudah sama di HUD/M; tidak memakai ruang HUD tambahan | M memerlukan pergantian perhatian; kemudahan pemain baru belum dinilai |
| Minimap ber-fog | Arah pemain dan geometri lokal tersedia tanpa membuka M | Dapat memindahkan perhatian dari dunia ke panel; dampak pada rasa tegang belum diukur |
| Peta kecil seluruh layout / monster | Ditolak dari prototipe | Membocorkan eksplorasi/ancaman, tidak diperlukan untuk pertanyaan tiket |

Prototipe hanya mengingat tile yang terlihat menurut jarak dekat, cone senter dan line of sight. Di balik dinding atau pintu tertutup tetap kosong. Informasi tiap lantai terpisah; sesi baru menghapus pengetahuan sesi sebelumnya, termasuk bila seed sama. Tidak membaca atau menggambar posisi monster, fuse, pickup, loot atau jawaban puzzle. Satu dot langkah berikut Story hanya tampil jika selnya sudah dikenal. Arah utara tetap; indikator pemain mengikuti facing tanpa memutar seluruh panel.

Panel 200×196 berada di sudut yang tidak mengenai karakter, kotak tujuan, prompt atau footer HP/inventory. Bila tidak ada ruang, panel disembunyikan. M, WaveMap, dialog, puzzle, cutscene dan mode selain playing menyembunyikannya. Area yang dikenal tidak ditulis ke save atau settings, dan toggle tidak mengubah kontrol game utama.

[Probe lokal](reviews/minimap/report.json): satu arah senter pada tiap spawn mengenali 34/10.384 sel kampus, 47/768 sel interior dan 39/3.082 sel Escape. Seluruh snapshot tetap sama. Pengukuran 120 draw tambahan hanya mengukur overlay hangat dengan sampel FOV yang tercache, bukan waktu observasi awal, AI, frame game, atau performa perangkat lain.

Jika hasil playtest mendukung kelanjutan, spesifikasi minimal yang diusulkan: toggle I dan opsi aksesibilitas default mati, preferensi UI dapat disimpan terpisah dari progres; orientasi utara tetap; pemain/facing, lantai aktif, tile yang pernah terlihat dan langkah berikut yang sudah dikenal; tanpa monster/item/urutan puzzle tersembunyi. Reset/invalidate mengikuti new/load/retry, lantai, pintu dan geometri. Panel mengikuti safe area HUD dan tidak muncul bersamaan dengan M/WaveMap/modal. Retensi fog lintas save perlu diputuskan berdasarkan kebutuhan orientasi, bukan otomatis ditambahkan ke schema progres.

Catatan evaluasi saat ini adalah capture dan probe mekanik, **bukan playtest manusia**. Protokol penerimaan: bandingkan M+waypoint saja dengan minimap toggle pada rute kampus, interior bertangga, dan Escape yang setara; counterbalance urutan agar pembelajaran rute tidak menguntungkan satu kondisi. Catat waktu mencapai objective, salah belok/lantai, frekuensi membuka M, perhatian pada panel versus dunia, kematian/penyebab lolos, serta penilaian ketegangan dan repetisi. Keputusan berikutnya harus mencantumkan hasil nyata tersebut. Tidak ada angka orientasi, perhatian atau rasa takut yang diada-adakan dalam laporan ini.

Delapan regresi menguji default mati, dinding/fog, rahasia yang tidak memengaruhi pixel, snapshot read-only, isolasi lantai, reset sesi, penempatan pada dua resolusi dan sembunyi saat M/WaveMap/modal. Prototipe dapat dipakai reviewer sekarang; implementasi produksi tetap ditunda.
