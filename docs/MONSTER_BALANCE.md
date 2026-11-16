# Balancing monster v0.2 — #11

Parameter gameplay berada di `horror/balance.py`, terpisah dari budget, skor, temperatur dan recovery local search di `simulation.py`. Story dan Escape memakai aturan serangan/sensor yang sama. Tidak ada planner A*/BFS baru untuk pengejaran atau akses posisi pemain tersembunyi.

| Parameter | Easy | Normal | Hard |
| --- | ---: | ---: | ---: |
| Kecepatan Penjaga | 126,38 | 177,50 | 197,52 |
| Kecepatan Pendengar | 108,58 | 152,50 | 169,70 |
| Kecepatan Penyergap | 105,02 | 147,50 | 164,14 |
| Pengali jarak pandang | 1 | 1,25 | 1,35 |
| Pengali waktu reaksi | 1,25 | 1 | 0,9 |
| Grace awal (detik) | 12 | 9 | 7 |

Kecepatan pemain tetap 125 (jalan), 225 (sprint), 65 (pelan). Easy mempertahankan kecepatan monster lama. Normal/Hard tidak dapat diatasi dengan berjalan pasif selamanya; sprint singkat, belokan, pintu, memadamkan senter dan pengalih tetap berguna.

Penjaga mengandalkan penglihatan dan tekanan berjalan; Pendengar memiliki pendengaran 1,8 dibanding 0,85 pada dua jenis lain, pandangan dekat 43 px, dan memori lebih lama. Penyergap mempertahankan dash lurus 380 px/detik, wind-up 1 detik sebelum pengali kesulitan, recovery 2,5 detik dan cooldown 5 detik. Dash dibatasi collision/substep dan tidak diarahkan ulang diam-diam.

Serangan sentuh kini memiliki wind-up 0,50 detik (Penjaga), 0,65 (Pendengar), 0,55 (Penyergap), bunyi identitas dan cincin jingga yang statis. Selama wind-up, monster maju 90% dari kecepatan mengejar hanya selama pemain terlihat. Sprint keluar dari jangkauan menghindari hit; berjalan pasif bukan dodge otomatis. Setelah percobaan, jeda serang 1,8/2,0/1,8 detik, termasuk bila meleset. Damage 28/22/24 dan dash 38 tetap dikalikan kesulitan lama; invulnerability 1,6 detik dan knockback mencegah damage menumpuk.

Memori Penjaga 1,15×, Pendengar 1,30×, Penyergap 1× dari search time kesulitan. Hilang pandangan beralih ke pencarian sasaran terakhir; diam/pelan dalam gelap di balik dinding tidak memberi posisi baru. Botol/alarm mempertahankan jendela pengalihan 2,5 detik. Serangan, timer dan cooldown tersimpan dalam save; transfer tangga mengenali state serangan baru.

Probe `python tools/balance_probe.py` membandingkan diam, lari lurus dan putaran sudut + pengalihan pada arena terkontrol dengan footprint Escape dan lantai perpustakaan Story. [Sebelum](reviews/balance/before.json) berasal dari `a2a9bcc`; [sesudah](reviews/balance/after.json) memakai perubahan #11. Masing-masing 54 kasus, maksimal 30 detik, dengan runtime sensor/collision/HC/SA nyata. Ini bukan simulasi pemain baru, skor kesulitan manusia, atau pembuktian rute campaign.

| 18 kasus per kesulitan | Mati sebelum → sesudah | Bertahan sebelum → sesudah | Rerata waktu state chase/serangan (detik) |
| --- | --- | --- | --- |
| Easy | 6 → 7 | 12 → 11 | 2,76 → 4,87 |
| Normal | 9 → 11 | 9 → 7 | 3,22 → 7,59 |
| Hard | 11 → 13 | 7 → 5 | 3,64 → 7,14 |

Tradeoff: telegraph memberi ruang bereaksi, sementara kecepatan dan memori memperpanjang tekanan. Local search masih dapat kehilangan jejak ketika pemain berhasil memutus sensor; hal itu merupakan counterplay yang diinginkan. Menunggu di tempat tetap berbahaya. Hasil rinci menyimpan HP, jumlah hit, waktu kehilangan visual, jarak akhir dan state akhir, termasuk kasus bertahan yang tidak membuktikan monster sudah kehilangan jejak.

Tes regresi memeriksa cue sebelum damage, menghindar dengan sprint, berjalan pasif, dinding/pintu, gerak tanpa teleport, grace Easy, sensor pemain tersembunyi dan save/load di tengah wind-up. Penilaian rasa sulit serta kesempatan reaksi oleh pemain baru tetap diperlukan; jangan menyebut probe ini sebagai playtest manusia.

Verifikasi: 120 unittest lulus dan 55 capture presentasi selesai. [Campaign bot](reviews/balance/story-probe.json) menamatkan Easy dan Normal; Normal menerima satu hit, Hard mati oleh Penjaga pada tahap 16 setelah enam hit. Pesan bot `Stair failed` pada Hard dicatat saat status sudah lost, bukan pembuktian tangga tidak dapat dipakai. [Bot Escape](reviews/balance/escape-probe.json): Easy 10 menang, Normal 9 menang/1 mati, Hard 7 menang/2 mati/1 belum tuntas. Bot mengetahui rute dan jawaban puzzle; hasil ini hanya bukti mekanik. [Contoh cue serangan](reviews/balance/attack-cue.png).
