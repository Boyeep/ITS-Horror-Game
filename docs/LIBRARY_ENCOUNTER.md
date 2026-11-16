# Pertemuan perpustakaan — #13

PR bertumpu pada balancing #11. Sebelumnya, adegan berlangsung 5,5 detik dan menggambar monster 165 px di kanan pemain, kemudian memilih posisi spawn lain dengan state patroli. Reveal dan ancaman gameplay dapat terasa tidak tersambung.

Kini titik reveal dipilih sebelum cutscene dari lantai legal 150–300 px, terlihat dari pemain, dengan penalti arah menuju tangga terdekat. Renderer memakai titik itu, dan monster gameplay muncul pada titik yang sama. Catatan diselesaikan sebelum adegan; petunjuk 2-4-1-3 tetap berada di jurnal.

| Tahap | Waktu | Perilaku |
| --- | --- | --- |
| Membaca | Selama pemain membutuhkan | Simulasi berhenti; tidak ada damage atau monster baru |
| Antisipasi | 0–4,5 detik | Hening, cue pintu pada 1,5 dan langkah berat pada 4; peredupan tunggal 3,2–4,2 |
| Reveal | 4,5–8,5 detik | Posisi legal yang sama dengan spawn; stinger satu kali pada 5,2; suara Penjaga pada 7,8 |
| Persiapan kabur | 8,5–12 detik | Petunjuk tangga; kamera kembali ke pemain |
| Kontrol kembali | Setelah 12 detik atau skip | Penjaga menunggu 2,2 detik sebelum bergerak; target awal adalah posisi terakhir yang terlihat |
| Pencarian lanjutan | 14 detik gameplay | Memori Penjaga tidak hilang seketika ketika berbelok/berpindah lantai; posisi baru tetap mengikuti sensor biasa |

Durasi adegan meningkat 5,5 → 12 detik. Tekanan 14 detik adalah jendela memori, bukan deteksi pemain tanpa sensor atau jaminan 14 detik state visual chase. Berhasil memutus pandangan, bergerak pelan dan memakai pengalih tetap sah. Penjaga yang cukup dekat dapat mendengar aksi tangga (budget sound field 8) dan mengikuti melalui transfer tertunda 2,8 detik, dengan jeda 0,7 detik saat tiba. Tidak ada teleport pengejar instan ke posisi pemain yang terus diperbarui.

Reduced motion menahan kamera dan meniadakan peredupan tambahan. Stinger sudah diputar dalam adegan; cooldown startle mencegah salinan kedua saat kontrol kembali. Jumlah encounter/chase dicatat sekali. HP, inventory, posisi pemain dan elapsed gameplay tidak berubah selama presentasi.

`library_reveal` dan `library_pressure` merupakan field opsional schema 7. Save lama tetap dibaca, tidak memutar ulang adegan yang sudah terlihat, dan memakai tekanan nol bila field tidak ada. Save di tengah adegan mempertahankan waktu serta titik reveal; cue yang sudah lewat tidak diulang. Pending encounter dikonsumsi sekali, termasuk setelah skip, load dan pemanggilan finish berulang. Pause/jurnal/dialog menghentikan timer tekanan.

| Bukti visual | Capture |
| --- | --- |
| Sebelum, capture renderer lama | [sebelum](reviews/library/before.png) |
| Catatan sebelum ancaman | [catatan](reviews/library/note.png) |
| Build-up dan reveal | [antisipasi](reviews/library/anticipation.png), [reveal](reviews/library/reveal.png) |
| Ancaman dan arah kabur | [ancaman](reviews/library/threat.png), [arah](reviews/library/route.png) |
| Reduced motion / kontrol kembali | [reduced](reviews/library/reduced.png), [handoff](reviews/library/handoff.png) |

[Laporan posisi/timing](reviews/library/report.json) dibuat oleh `python tools/review_library.py`, menggunakan profil sementara. Tes regresi mencakup membaca, natural finish, skip, clue jurnal, save/load setelah stinger, save lama, pause jurnal, transfer tangga, serta pencegahan duplikasi. Campaign bot dan tes sinematik tetap dijalankan; [hasil campaign](reviews/library/story-probe.json) merupakan bukti mekanik, bukan playtest pemain baru. Durasi akhir dan rasa dikejar masih memerlukan penilaian pemain sebelum tiket diterima penuh.
