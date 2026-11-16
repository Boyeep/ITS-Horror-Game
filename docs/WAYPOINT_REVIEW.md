# Navigasi dan penanda tujuan — #18

PR ini bertumpu pada geometri #14. Audit menemukan tiga sumber kebingungan: target dipilih menurut jarak lurus meskipun rutenya memutar, sebuah ray tipis mengabaikan lebar tubuh di sudut, dan prompt flight bertumpuk mengikuti urutan daftar alih-alih arah tujuan. Panah tepi juga memakai pusat layar sebagai asal, yang berbeda dari posisi pemain di dekat batas dunia.

`RouteGuide` memakai planner A* layout yang memang disediakan untuk HUD, dengan biaya pintu tertutup yang sama. Semua kandidat portal/objective dinilai menurut biaya rute; target tak terjangkau tidak diberi arah. Kandidat ekuivalen dipertahankan sampai rute lain lebih murah lebih dari tiga sel. Langkah berikut dibatasi lookahead delapan sel dan diuji dengan radius badan pemain; waypoint lama dipertahankan selama masih legal di rute dan lebih jauh dari 55 px. Pintu tertutup menjadi langkah “Buka pintu”, lalu cache dihitung ulang setelah pintu dibuka.

Cache mencakup identitas session/layout, lantai, tahap, revisi, keadaan setiap pintu, daftar target/display/label dan tile pemain. Perubahan multiobjek dalam tahap yang sama, save/load, perpindahan lantai dan perubahan pintu tanpa kenaikan revision tidak menggunakan rute lama. Informasi cache hanya berada di renderer, tidak ditulis ke progres/save.

Prompt tangga mengutamakan flight dengan arah yang dibutuhkan objective ketika beberapa flight dapat diaktifkan. Loot opsional tidak mengambil alih flight tujuan. Pintu tertutup yang menghalangi tetap harus dibuka terlebih dahulu. Flight lain tetap dapat digunakan untuk eksplorasi.

Label utama mendapat ruang lebih dulu; label lain menghindari karakter, kotak tujuan, batas layar dan label yang sudah ditempatkan. Kotak tujuan pindah sisi bila menutupi karakter dekat batas kamera. Ikon target yang tepat menumpuk tubuh tidak digambar di atas karakter. String panjang dipendekkan dengan elipsis; prompt tahan E tidak menggandakan kata “Tahan”. Panah memakai ray dari posisi pemain sebenarnya dan ditempatkan di area aman, termasuk saat WaveMap terbuka.

HUD dan peta M membaca objek route guide yang sama. Peta lantai memakai segitiga naik/turun yang ringkas, sehingga label flight berpasangan tidak bertumpuk. Garis hijau hanya menunjukkan prefix rute menuju langkah berikut, bukan planner monster atau jawaban puzzle. Objective multiobjek tetap dipilih menurut keterjangkauan, tidak menurut urutan jawaban katalog/katup. Tidak ada kode puzzle baru yang disisipkan ke petunjuk.

| Kasus | Sebelum | Sesudah |
| --- | --- | --- |
| Ponsel / prompt aktif | [HUD](reviews/guidance/before/phone.png) | [HUD](reviews/guidance/after/phone.png) |
| Flight Informatika, tujuan perlu turun | [prompt naik yang salah](reviews/guidance/before/paired-stairs.png) | [prompt turun](reviews/guidance/after/paired-stairs.png) |
| Objective katalog multiobjek | [HUD](reviews/guidance/before/catalog.png) | [HUD](reviews/guidance/after/catalog.png) |
| Rute kampus | [HUD](reviews/guidance/before/campus.png) | [HUD](reviews/guidance/after/campus.png) |
| Kesesuaian peta lantai | [M](reviews/guidance/before/paired-stairs-map.png) | [M dan langkah berikut](reviews/guidance/after/paired-stairs-map.png) |
| Kesesuaian peta kampus | [M](reviews/guidance/before/campus-map.png) | [M dan langkah berikut](reviews/guidance/after/campus-map.png) |

[Metadata sebelum](reviews/guidance/before/report.json) dan [sesudah](reviews/guidance/after/report.json) dibuat dengan `python tools/review_guidance.py --output build/guidance-review`. Perbandingan ini memakai titik, tahap dan kamera yang sama pada geometri #14. Capture bukan playtest pemain baru.

Sebelas regresi khusus memeriksa pilihan rute di balik dinding, target terputus, hysteresis portal, perubahan pintu/progres, sudut yang tidak muat badan, arah panah saat kamera terjepit, box label pada tiga ukuran, flight yang benar dan konsistensi HUD/M setelah pindah lantai/save-load. [Campaign bot](reviews/guidance/story-probe.json) memeriksa progres dan mencatat batasnya saat mati. Playtest pemain baru untuk kemudahan memahami penanda masih diperlukan; evaluasi minimap #17 menggunakan navigasi ini sebagai pembanding.
