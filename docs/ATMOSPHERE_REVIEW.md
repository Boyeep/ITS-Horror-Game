# Review atmosfer dan aset v0.2 — #15 / #16

Review teknis PR #23 pada 16 November 2026. Pembanding adalah `a2a9bcc` (basis v0.2, presentasi v0.1), sesudah perbaikan kode `9ef4f94`. Pemeriksaan visual dan mixer tidak menggantikan playtest pemain baru. Kedua tiket masih memerlukan bukti pengalaman pemain sebelum dinyatakan selesai seluruhnya.

| Prioritas yang ditemukan | Perubahan yang dipilih | Cakupan |
| --- | --- | --- |
| Permukaan kampus tampak berulang | 25 variasi per material, retak/noda/rumput berkontras rendah, detail lampu | Kampus Story |
| Interior lantai atas kosong | Papan, poster, APAR, ventilasi, jam dan wear prosedural | Lantai atas non-atap; pintu, kaca, area luar, furnitur dan tangga tetap bebas |
| Radio/buku memakai foley kain | Tiga rekaman radio dan satu rekaman buku; fallback tetap tersedia | Interaksi Story; rekaman kain tetap dipakai pickup/heal |
| Ketegangan terasa datar | Detak, napas, jeda ambience, grain, vignette dan kedip cahaya mengikuti state simulasi | Story dan Escape |

Ini tahap prioritas aset, bukan penggantian seluruh tile bangunan atau animasi monster. Dekor hanya dibakar ke gambar dunia; grid, collision, sensor, puzzle dan save tidak berubah. Escape mendapat efek atmosfer bersama, sementara dekor lantai atas diterapkan pada interior Story.

| Momen / trigger | Cue dan intensitas | Jeda / prioritas |
| --- | --- | --- |
| Threat, encounter atau HP rendah | Tension 0–1; naik cepat (2,5), turun lambat (0,5) | Model membaca session tanpa menulis progres |
| Tension > 0,28 | Detak sintetis 66 BPM; berganti 112 BPM di > 0,72 dan kembali di < 0,55; gain maksimum 0,6 × slider efek | Channel loop tersendiri; sunyi ketika pause/modal/result/mute |
| Tension > 0,5 | Tiga variasi napas sintetis; gain 0,3–0,8 | Cooldown 4 detik; interval 3,5–7+ detik menurut tension; gap global 2,5 detik |
| Luar → dalam, tension < 0,3 | Cue jauh gain 0,3; ambience turun sampai 45% selama 1,6 detik | Cooldown 45 detik; dilewati bila voice/cue lain sedang aktif |
| Chase berakhir setelah ≥ 3 detik | Napas pelepasan gain 0,6; ambience turun sampai 45% selama 3,2 detik | Cooldown 20 detik; menunggu kesempatan maksimal 3 detik |
| Stinger, suara monster, damage, radio atau cue adegan | Cue gameplay mendapat prioritas; napas opsional dihentikan | Tunda atmosfer minimal 2,5 detik atau sepanjang klip prioritas |
| Tension meningkat | Kedip menurunkan lampu maksimal 30% dan senter 50%; vignette tepi maksimal alpha 105; grain 10 FPS | Reduced motion mematikan kedip, menahan satu frame grain, serta mempertahankan HUD setelah overlay |

Channel 6 disediakan untuk detak dan channel 7 untuk cue atmosfer. Memulai sesi baru membersihkan tension, napas, hush dan riwayat chase. Pause, jurnal, dialog, puzzle dan cutscene menghentikan cue opsional. Slider efek mengendalikan detak/napas secara terpisah dari slider musik. Gap prioritas dipertahankan bila stinger diputar sebelum update konteks pertama.

| Temuan review | Perbaikan / regresi yang diperiksa |
| --- | --- |
| Napas dapat terus terdengar setelah pause/modal atau berpindah sesi | Channel atmosfer tersendiri dihentikan pada transisi tersebut |
| Tension sesi lama membuat detak terdengar pada awal sesi baru | Reset state ketika session berganti |
| Gate hanya mengatur cue atmosfer, sehingga napas dapat menimpa stinger | Cue gameplay menghentikan napas dan menunda gate |
| Glob audio dapat memuat rekaman yang tidak dicatat manifest | Audit memeriksa setiap media terhadap manifest, hash dan metadata kredit |
| Kredit umum dan daftar aset masih menyebut 17 rekaman | Kredit baru ditambahkan, daftar diperbarui menjadi 21 rekaman story audio / 73 media aktif |

Perbandingan 1280×800, posisi/arah/senter tetap, seed Escape 42, tanpa monster bergerak: [sebelum](reviews/atmosphere/before/report.json) dan [sesudah](reviews/atmosphere/after/report.json). Setiap lokasi memiliki kondisi calm, tense, dan reduced. Screenshot ini memeriksa presentasi, bukan rute progresi atau reaksi pemain.

| Contoh | Sebelum | Sesudah | Saat tegang / reduced motion |
| --- | --- | --- | --- |
| Kampus | [calm](reviews/atmosphere/before/campus-calm.png) | [calm](reviews/atmosphere/after/campus-calm.png) | [tense](reviews/atmosphere/after/campus-tense.png) |
| Perpustakaan | [calm](reviews/atmosphere/before/library-calm.png) | [calm](reviews/atmosphere/after/library-calm.png) | [tense](reviews/atmosphere/after/library-tense.png) |
| Informatika | [calm](reviews/atmosphere/before/informatika-calm.png) | [calm](reviews/atmosphere/after/informatika-calm.png) | [reduced](reviews/atmosphere/after/informatika-reduced.png) |
| Escape | [calm](reviews/atmosphere/before/escape-calm.png) | [calm](reviews/atmosphere/after/escape-calm.png) | [reduced](reviews/atmosphere/after/escape-reduced.png) |

Objek yang disorot senter, karakter, pintu, tangga dan teks tujuan tetap terbaca pada capture yang diperiksa. Noda/retak dibuat redup agar tidak menyerupai pickup. Penambahan vignette paling terasa pada tepi layar; keterbacaan ketika benar-benar dikejar tetap perlu dinilai pemain.

| Render 120 frame, SDL dummy | Sebelum (ms/frame) | Sesudah (ms/frame) |
| --- | ---: | ---: |
| Kampus | 11,678 | 15,793 |
| Perpustakaan | 19,324 | 20,024 |
| Informatika | 15,321 | 18,137 |
| Escape | 15,805 | 18,140 |

Ini satu pengukuran lokal per kondisi, draw saja tanpa AI/audio/frame cap; bukan FPS playtest atau benchmark lintas perangkat. Overlay menambah biaya render. Empat buffer grain dan satu vignette juga memakai lebih banyak memori daripada satu buffer grain lama. Aset rekaman bertambah 42.274 byte; tidak ada file visual runtime baru.

Verifikasi otomatis: 142 unittest lulus, 100 seed map valid (SA memperbaiki 98), audit memuat 73 media dengan nol aset tidak terpakai, serta 55 capture dari `tools/review_presentation.py --headless`. Tes baru mencakup pause/modal/retry, prioritas stinger, mute dan slider terpisah, variasi rekaman, reduced motion, resize native, serta audit manifest.

Build Windows berhasil. [Verifikasi paket](reviews/atmosphere/release-review.json) memeriksa ZIP CRC, metadata Windows dan hash seluruh 83 berkas aset tertanam terhadap source. ZIP portable berukuran sekitar 41,1 MiB. [Sembilan skenario executable](reviews/atmosphere/compiled-smoke.json) lulus dari working directory eksternal, termasuk Story, Escape, save lantai atas, reader, portrait dan resume intro. [Smoke native](reviews/atmosphere/native-window.json) lulus pada layar 1920×1200 dengan mixer 44100 Hz / stereo dan handoff intro. [Log unittest](reviews/atmosphere/unit-test.log) dan [laporan presentasi](reviews/atmosphere/presentation-review.json) disertakan. Identitas produk tetap 0.1 mengikuti branch basis; ini verifikasi build pengembangan, bukan penerbitan rilis baru.

Reproduksi capture/timing: jalankan `python tools/review_atmosphere.py --output build/atmosphere-review --frames 120` pada branch yang diperiksa. Untuk basis yang belum memiliki tool, salin script ke `build/review_atmosphere.py` sebelum `git switch --detach origin/v0.2`, lalu jalankan salinan tersebut dengan output terpisah. Tool memakai profil sementara dan tidak menyentuh save pribadi.

Sisa penerimaan tiket: lakukan perbandingan bermain/rekaman Story dan Escape dengan pemain baru, catat momen yang lebih tegang atau repetitif, keterbacaan saat chase, kualitas campuran audio dan performa pada perangkat target. Metadata CC0/hash/kredit baru telah diperiksa secara lokal; halaman sumber OpenGameArt menolak akses web otomatis pada sesi review, sehingga konfirmasi halaman sumber tetap perlu dilakukan manual. Penyelarasan akhir dengan balancing monster #11 dan adegan perpustakaan #13 juga perlu diverifikasi setelah dependensi tersebut tersedia. Sampai bukti ini ada, #15 dan #16 belum layak ditutup penuh.
