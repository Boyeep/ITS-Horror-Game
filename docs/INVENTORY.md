# Backpack dan pencapaian

Sistem berlaku di Story dan Escape. B/Tab membuka tas; panah memilih; Enter/E memakai; X meletakkan satu item; Tab di dalam tas mengganti kategori. Simulasi dunia berhenti saat tas terbuka. Cooldown tindakan singkat tetap berjalan agar input tidak terkunci di menu. Memakai item menutup tas dan kembali ke permainan/jeda sebelumnya.

## Perlengkapan

| Item | Ruang/buah | Maks. tumpukan | Efek |
| --- | --- | --- | --- |
| Botol kaca | 1 | 8 | Q / gunakan: lempar sampai penghalang atau jarak 280; noise di titik pecah |
| P3K | 2 | 3 | +40 HP, dibatasi 100 |
| Perban | 1 | 5 | +20 HP, dibatasi 100 |
| Minuman energi | 1 | 3 | +45 stamina; 9 detik konsumsi sprint 17/s alih-alih 23/s dan pemulihan 26/s alih-alih 16/s |
| Lakban kain | 1 | 2 | Selama 20 detik, radius noise langkah ×0,55 dan gain langkah ×0,6; tambahan noise kaca/pintu tidak diubah |
| Alarm saku | 2 | 2 | Jeda 3 detik, noise radius 12 tiap 2 detik selama 10 detik; sumber tetap di alat |
| Lampu kimia | 1 | 4 | Cahaya radius 175 selama 45 detik; tiga lampu aktif per layer; pemasangan keempat mengganti yang tertua |

Kapasitas total 12 ruang. Bekal awal berisi perban, minuman, lampu kimia dan botol sesuai difficulty. E mengambil P3K; pemulihan hanya saat digunakan. Item pemulihan tidak habis pada HP penuh. Minuman/lakban tidak ditumpuk saat efeknya masih aktif. Alarm menuntun AI hanya jika suara lolos field pendengaran; monster yang masih melihat pemain tetap dapat mengejar. Lampu kimia meningkatkan visibilitas di area bercahaya tetapi tetap memerlukan LOS, dan tidak memberi koordinat pemain ke AI.

Supply di dunia ditentukan seed dan ditaruh pada tile yang terjangkau, bukan pada daun pintu. Ada 13 supply tambahan di kampus/Escape dan tiga pada setiap lantai atas, di luar botol/P3K lama. Item bisa diletakkan lalu diambil kembali. Tas penuh atau tumpukan maksimal tidak menghilangkan item. Barang yang berasal dari tas tidak dihitung sebagai temuan baru untuk achievement.

Barang penting—kartu, kunci, ponsel, foto dan sekring—ditampilkan di pouch terpisah, tidak mengambil ruang, dan tidak bisa dibuang. Flag listrik seperti Jalur bumi/Daya cadangan tetap berada dalam progres cerita, bukan diperlakukan sebagai barang fisik tas.

Ikon menggunakan gambar prosedural beresolusi tinggi dengan tepian diperhalus, palet material dan bentuk yang sama di UI/dunia. [Item art](screenshots/item-art.png), [backpack](screenshots/backpack.png), [pouch](screenshots/backpack-keys.png), [alat di dunia](screenshots/field-supplies.png).

## 15 pencapaian

| Nama | Kondisi |
| --- | --- |
| Bekal pertama | Mengambil satu perlengkapan alami dari dunia |
| Siap berangkat | Menemukan lima jenis perlengkapan dalam satu perjalanan |
| Pertolongan pertama | Menggunakan P3K/perban untuk memulihkan HP |
| Napas kedua | Meminum energi saat stamina ≤25 |
| Langkah ringan | Bergerak total 10 detik dengan lakban aktif |
| Salah arah | Monster merespons botol/alarm jauh dari pemain dan tidak melihat pemain |
| Jejak cahaya | Memasang lampu kimia di tiga area berbeda |
| Kenal kampus | Mengunjungi 20 area dalam satu perjalanan |
| Naik kelas | Mengunjungi kedelapan lantai atas Story |
| Tidak ada yang hilang | Mendapatkan seluruh 13 bukti cerita |
| Dua orang pulang | Menuntaskan Story sampai ending selesai |
| Lewat gerbang | Menang Escape |
| Malam tersulit | Menang Escape Hard |
| Tanpa luka | Menang Escape tanpa pernah terkena serangan |
| Tidak perlu berlari | Menang Escape tanpa bergerak sprint |

Penghargaan sekali per profil, disertai notifikasi dan bunyi UI tanpa noise gameplay. Halaman Pencapaian ada pada menu, jeda dan hasil; menampilkan kondisi serta progres terbaik perjalanan. Tidak ada popup yang menghentikan permainan. Notifikasi disembunyikan saat membuka panel inventory/pencapaian agar tidak menutupi informasi.

Profil di `%APPDATA%/ITS-Horror-Game/achievements.json` berisi timestamp unlock serta progres maksimal. Penulisan atomik dan cadangan `.bak` disediakan. Pemuatan save lama tidak menurunkan profil; jumlah serangan/sprint digunakan untuk tantangan bersih, bukan HP terakhir. Profil bersifat lokal, tanpa Steam/cloud.

## Penyimpanan dan kompatibilitas

Save versi 3 menambah isi tas, efek sementara, statistik perjalanan dan tiap layer: supply tersisa serta alarm/lampu dengan timer. Layer tidak aktif membekukan alat yang terpasang seperti AI di versi sebelumnya. Pouch memakai progres cerita yang sudah ada. Versi save 1/2 tetap dibaca: bekal awal dan supply baru diberikan, tanpa mengubah bukti/pintu/posisi progres lama. Profil pencapaian disimpan terpisah.

Tes fungsional memeriksa kapasitas, stack, item tak hilang saat penuh, pouch tidak memblokir progres, treatment, energi, noise lakban, jeda/target alarm, cahaya/occlusion, timer antar-lantai, migrasi save, pencegahan farming barang sendiri, unlock satu kali, riwayat tantangan, profil tidak rollback dan UI. [QA](QA.md).
