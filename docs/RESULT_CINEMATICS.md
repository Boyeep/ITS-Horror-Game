# Penutup Story dan Escape — #12

Audit menemukan ending Story sudah terhubung dengan dialog dan hasil; tiga jalur lain langsung berpindah ke layar hasil. Ending Story tetap dipakai satu kali, sementara presentasi terminal ditambahkan untuk tiga jalur yang belum memiliki adegan.

| Jalur | Sebelum | Sesudah | Bukti |
| --- | --- | --- | --- |
| Story mati | Langsung hasil | Adegan padam 5,5 detik → hasil/checkpoint | [adegan](reviews/outcomes/story-lost.png), [hasil](reviews/outcomes/story-lost-result.png) |
| Story tamat | Dialog → ending 8,5 detik → hasil | Tetap memakai ending yang ada, tanpa adegan sukses tambahan | [ending](reviews/outcomes/story-ending.png), [hasil](reviews/outcomes/story-won-result.png) |
| Escape mati | Langsung hasil | Adegan padam 5,5 detik → hasil/retry seed yang sama | [adegan](reviews/outcomes/escape-lost.png), [hasil](reviews/outcomes/escape-lost-result.png) |
| Escape kabur | Langsung hasil | Gerbang terbuka 6,5 detik → hasil/map baru | [adegan](reviews/outcomes/escape-won.png), [hasil](reviews/outcomes/escape-won-result.png) |

`OutcomePresentation` menerima salinan frame terakhir tanpa HUD, bukan session simulasi. Mode `outcome` hanya memajukan timer presentasi. Pemain, monster, HP, stamina, inventory, perlengkapan dan progres tidak berjalan selama adegan. Gambar gerbang, peredupan dan caption dibuat dari kode; tidak ada aset unduhan baru. Reduced motion meniadakan zoom dan memakai pergantian gate yang tetap, tanpa kilatan atau shake.

Enter/Spasi dan tombol mouse melewati adegan. Esc atau kehilangan fokus menjeda timer; resume kembali ke adegan yang sama. Skip mengakhiri pemrosesan batch input, mengabaikan key repeat dan menunggu pelepasan tombol konfirmasi sebelum tombol hasil menerima Enter berikutnya. Ini mencegah satu tombol skip sekaligus memicu retry. Pause pada terminal tidak menawarkan backpack atau simpan keadaan mati; muat checkpoint tetap tersedia.

Status hasil dan penghargaan dicatat sekali untuk setiap objek session. Memanggil pemeriksaan hasil/skip berulang tidak menambah jumlah kemenangan atau memutar adegan kedua. Retry/new/load membersihkan state presentasi. Save kematian tidak mengganti checkpoint hidup; Story retry memulihkan checkpoint dan memberi pemulihan yang sudah tersedia. Save Story selesai tetap dicatat oleh alur ending lama.

Cue `caught`/`win` gameplay tetap diputar satu kali; presentasi tidak menambahkan salinan. Pause, skip dan kembali ke menu menghentikan suara sekali putar dan voice. Loop musik/ambience tetap dikelola context mix; bila channel detak dari #16 tersedia, loopnya dipertahankan dalam keadaan mute agar sesi berikutnya dapat memakainya kembali.

[Matriks otomatis](reviews/outcomes/report.json) dibuat oleh `python tools/review_outcomes.py` dengan profil sementara. Tes memeriksa empat jalur, freeze simulasi, natural finish, skip keyboard/mouse, pause/resume, key repeat/batch, retry, checkpoint, penghargaan sekali, gambar pada dua resolusi dan reduced motion, serta penghentian cue mixer. Seluruh gambar diperiksa secara lokal; penilaian artistik/emosi tetap merupakan pekerjaan playtest pemain.
