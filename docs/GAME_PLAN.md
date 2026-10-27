# Desain permainan 0.1

## Tujuan

Membangun horor top-down dengan eksplorasi, puzzle dan pengejaran yang bisa dipahami pemain. Pemain memilih rute, mengelola stamina/bekal, membaca petunjuk, dan memutus jejak sebelum melanjutkan tujuan. Pygame-ce menangani grafis, input serta audio lokal; tidak ada layanan AI saat bermain.

## Dua mode

**Cerita** memakai geografi tetap yang terinspirasi ITS: tiga bab, 25 tahap, kampus terbuka dan interior bertingkat. Misteri Nara dan jaringan SIMPUL dibangun melalui prolog, dialog, dokumen dan encounter. Autosave serta slot manual mendukung perjalanan panjang. Waktu tamat manusia belum diukur.

**Escape** mempertahankan loop sesi acak: dua sekring → panel → pintu keluar. Map 30 area menggabungkan spanning tree dan edge tambahan; Simulated Annealing mengatur penempatan sasaran serta ancaman. Kemenangan terjadi setelah benar-benar melewati exit, bukan sekadar menemukan item.

## Ancaman dan pilihan pemain

Penjaga memakai pandangan dan patroli, Pendengar mengandalkan suara, Penyergap melakukan wind-up/dash dengan arah terkunci. Ketiganya menggunakan bukti sensor dan jalur yang valid. Berlari, pintu, kaca, botol dan alarm menimbulkan noise. Difficulty mengubah sensitivitas serta ancaman, termasuk pendengaran yang lebih kuat pada Hard.

HP, jeda kebal setelah serangan, stamina, perlengkapan dan tempat berlindung memberi kesempatan pulih. Senter membantu melihat sekaligus memengaruhi visibilitas. Supply terbatas dan tas 12 ruang membuat pemilihan bekal berarti; barang penting tidak bisa terbuang.

## Presentasi

Kamera dekat mengikuti Arga. Tujuan tetap terlihat, sementara prompt tindakan muncul dekat objek. Peta memberi nama/arah; label dekoratif yang tidak membantu dibuang. Karakter memiliki ciri warna/prop yang konsisten, potret percakapan dan bunyi teks orisinal. Dokumen dibaca sebagai bukti pada kertas, buku, foto atau layar ponsel.

Menu memakai tiga foto gedung asli dengan palet malam, cahaya dan kabut; opening dimulai pada senja sebelum berpindah ke malam melalui kejadian cerita. Musik, foley material, suara monster dan perubahan layar menyampaikan intensitas.

## Batas dan evaluasi

Map bukan replika terukur kampus; skala serta interior diadaptasi. Tidak ada multiplayer atau director adaptif global. Save memulihkan state permainan, tetapi cache A* dan RNG runtime dihitung ulang. Bot menguji keterjangkauan ending; ia tidak mengukur ketakutan, durasi atau win-rate pemain baru.

Playtest berikutnya sebaiknya mengamati apakah pemain memahami objective pertama, menemukan action point, membedakan monster, dan mengetahui alasan mereka tertangkap. Ukur perilaku tersebut sebelum menambah sistem baru. [Algoritma](ALGORITHMS.md), [cerita](STORY_MODE.md), [QA](QA.md).
