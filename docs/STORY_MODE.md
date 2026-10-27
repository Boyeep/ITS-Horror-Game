# Story Mode

Arga dan Nara mengerjakan proyek di lab Informatika. Nara pergi ke perpustakaan dan meninggalkan ponselnya untuk dicas. Setelah listrik padam pada 23.47, pesan baru masuk dari nomor Nara sendiri. Penelusuran bukti membawa Arga ke jaringan suara SIMPUL, insiden lama, dan prosedur pemutusan yang membuka jalan pulang.

## Perjalanan

Tiga bab memuat 25 tahap: mencari bukti awal, mengungkap insiden, lalu memutus jaringan dan membawa Nara ke gerbang. Objective aktif menyebut lokasi/tindakan. Penanda fisik dan prompt E membantu mendekati objek; jurnal mempertahankan petunjuk puzzle. Jawaban tidak dibocorkan oleh navigasi.

Prolog berdurasi sekitar 50 detik, dari exterior senja ke lab, kepergian Nara, malam, listrik padam dan ponsel. Empat adegan penting lain mengikuti progres. Cutscene dapat dijeda, disimpan, dilanjutkan atau dilewati; tidak ada label shortcut permanen pada shot. Enter melewati, sedangkan opsi mouse tersedia di menu jeda.

Percakapan Arga/Nara memakai potret, teks bertahap dan blip orisinal yang berbeda. E/Enter/Space pertama menampilkan sisa kalimat; input berikutnya melanjutkan. Pause menghentikan timer/suara. Bukti tampil sebagai ponsel, foto, kertas atau buku, dengan teks penuh dan hening.

## Dunia

Kampus tetap berukuran 88×118 tile. Ruang luar memakai rumput, aspal dan beton. Informatika memiliki level dasar tersendiri 64×48 tile: lab satu pintu, selasar, ruang diskusi, lobi, courtyard dan empat landing stairs. Lantai 2/3 berukuran 38×44 tile; topologi lantai 3 merujuk denah UTBK publik. Ada sembilan lantai atas yang dapat dimainkan di lima bangunan, termasuk atap pemancar fiktif.

E pada flight tangga memindahkan lantai; state tiap level dipertahankan. Perpindahan ke kampus memakai pintu keluar yang berpasangan dengan footprint luar. Tidak ada ladder untuk akses lantai. Tower 2 pada menu berbeda dari menara pemancar dalam cerita. [Acuan dan batas adaptasi](ITS_REFERENCES.md).

## Save dan kompatibilitas

Autosave terpisah dari tiga slot manual. Save schema **7** memuat HP/stamina, posisi/floor, barang, pintu, puzzle, dialog, timer cutscene, pendamping, monster serta state setiap layer. `dialogue_time` opsional mempertahankan progres huruf. Schema **1–7** tetap diterima; posisi interior dasar lama dimigrasikan dan prolog lama yang belum selesai dapat dimulai kembali dengan timeline baru. Prolog yang selesai tidak diulang.

Data ditulis atomik ke `%APPDATA%/ITS-Horror-Game/saves/`; `.bak` menyimpan salinan valid sebelumnya. Import `story.json` lama tidak menghapus aslinya. Muat menjaga kondisi save; retry setelah kalah memulihkan HP/stamina dan memberi jeda aman. Profil pencapaian terpisah dari slot perjalanan. Versi produk 0.1 tidak mengganti nomor schema.

## Audio dan ancaman

Penjaga, Pendengar dan Penyergap memiliki siluet, sensor serta serangan berbeda. Musik eksplorasi/pengejaran, Night Shift, jangkrik, hum interior dan empat rekaman tiap monster membangun variasi suasana. Langkah menyesuaikan material. Slider musik/efek terpisah; efek layar dapat diringankan.

Campaign driver berjalan melalui collision/pintu dan 24 transisi tangga hingga ending pada semua difficulty. Bot mengetahui rute/jawaban dan melewati presentasi; waktunya tidak mewakili durasi manusia. [Hasil QA](QA.md) · [tas dan pencapaian](INVENTORY.md).
