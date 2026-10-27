# Komponen pihak ketiga

Furnitur dan lantai dalam ruang menggunakan **Top-down Shooter Pack** karya **Kenney Vleugels**, dirilis 2016. Halaman resmi: https://kenney.nl/assets/top-down-shooter. Aset tersebut dirilis dengan **Creative Commons Zero (CC0)**. PNG dikurasi dari ZIP resmi; lisensi asli dan manifest hash tersedia di `assets/kenney/License.txt` dan `assets/kenney/manifest.json`. Salinan lisensi disertakan sebagai `licenses/Kenney-CC0.txt` dalam paket portable. Aset ditampilkan dengan perubahan skala, rotasi, tint malam, dan detail kampus tambahan. Arga, Nara dan monster digambar dari kode proyek; sprite karakter Kenney tidak dibundel.

Layout, susunan furnitur, detail kampus, HUD, pencahayaan dan sebagian ambience/UI dibuat dari kode proyek. Pose empat arah dan potret memakai ilustrasi kurva asli proyek, termasuk crop avatar kontak. Kusen/panel pintu, staircase, ilustrasi close-up ponsel, foto, dan tampilan kertas/buku juga digambar dari kode. Tidak ada gambar yang dibuat memakai layanan generatif dalam rilis ini.

Runtime dan build menggunakan:

- **Python 3.12.10** — https://www.python.org/ — license disertakan dalam folder `licenses` pada paket portable.
- **pygame-ce 2.5.8** — https://github.com/pygame-community/pygame-ce — teks LGPL yang disertakan oleh distribusi pygame-ce disalin ke folder `licenses`.
- **SDL dan library audio/gambar terkait** yang dikemas oleh distribusi pygame-ce — informasi komponen tersedia di repositori pygame-ce.
- **PyInstaller 6.22.3** untuk membuat executable — https://pyinstaller.org/.

Font antarmuka menggunakan font yang tersedia di sistem Windows; file font Windows tidak disalin ke paket game. pygame menyediakan fallback jika font pilihan tidak tersedia.

Menu memakai foto asli yang dipublikasikan ITS untuk Rektorat, Tower 2 dan Informatika, serta PNG lambang dari repositori panduan identitas visual ITS. Aset berada di `assets/campus/photos` dan `assets/branding`, dengan URL sumber serta SHA-256. Foto dan lambang merupakan media ITS; **bukan bagian dari lisensi CC0 Kenney**. Renderer mengadaptasi tampilan melalui skala proporsional, pemetaan palet, kontur, cahaya dan kabut saat runtime; berkas foto sumber tidak diubah. Logo tetap memakai warna asli. [Kredit dan sumber setiap berkas](docs/ITS_REFERENCES.md). Ilustrasi menu kode lama sudah dihapus karena tidak digunakan. Denah UTBK tetap hanya referensi dan tidak dibundel. Menara pemancar cerita berbeda dari Tower 2.


Foley: **Kenney Impact Sounds** (https://kenney.nl/assets/impact-sounds) dan **Kenney RPG Audio** (https://kenney.nl/assets/rpg-audio), keduanya CC0. Klip OGG dikurasi dari ZIP resmi. Manifest hash dan license asli ada di `assets/audio`; salinannya disertakan dalam `licenses/Kenney-impact-CC0.txt` serta `licenses/Kenney-rpg-CC0.txt` pada paket portable. Langkah berat dan gesekan mengalami perubahan pitch saat runtime. Rig monster dan ilustrasi arsitektur interaksi dibuat dari kode; sprite monster tidak berasal dari Kenney.

Tema lokasi merujuk nama fasilitas dalam direktori resmi ITS (https://www.its.ac.id/ppid/direktori-its/) dan kampus Sukolilo (https://www.its.ac.id/its-multikampus/its-sukolilo/). Map adalah interpretasi fiksi, bukan denah atau produk resmi ITS. Foto dan logo dicatat terpisah di atas; cerita ini bukan produk resmi ITS.

## Musik dan suara makhluk

Seluruh rekaman berikut dirilis **CC0 1.0** pada halaman sumber. Salinan berkas, kredit, serta SHA-256 terdapat di `assets/story_audio/manifest.json` dan `CREDITS.txt`; kredit juga dibundel sebagai `licenses/Story-audio-CC0.txt`.

| Aset | Kreator | Sumber | Adaptasi |
| --- | --- | --- | --- |
| Unsolved Investigation | isaiah658 | https://opengameart.org/content/unsolved-investigation | Musik eksplorasi, volume dan crossfade runtime |
| Chase - Diamond Dust | NBJDLukasAbsolute | https://opengameart.org/content/chase-diamond-dust | `chase2.wav` sebagai loop; `chase2_end.wav` dipotong 1,15 detik dan diberi fade untuk stinger |
| 16 Monster Growls | StarNinjas | https://opengameart.org/content/16-monster-growls | `monster.2.ogg`, `monster.6.ogg`, `monster.12.ogg` untuk tiga makhluk; gain spasial runtime |

### Referensi geografi

Story Mode menggambar ulang hubungan lokasi dari [ITS International Student Guide](https://www.its.ac.id/international/wp-content/uploads/sites/66/2019/03/Guide-Book-for-International-Students.pdf), halaman PDF 15/cetak 12, dan [Campus Forests ITS, peta topografi 2021](https://www.its.ac.id/sustainability/wp-content/uploads/sites/120/2023/10/campus-forest.pdf), halaman pertama. PDF hanya menjadi bahan referensi pengembangan; gambar dan berkas PDF tidak disertakan dalam game. Batas bangunan, interior dan skala diadaptasi untuk permainan.

Cerita Nara dan puzzle dibuat untuk proyek ini. Inspirasi Ao Oni terbatas pada ritme eksplorasi, puzzle dan pertemuan monster; tidak ada aset, musik atau cerita Ao Oni yang digunakan.

## Musik alternatif dan ambience

- **Night Shift**, iamoneabe, CC0: https://opengameart.org/content/night-shift — berkas `nightshift_0.mp3`, musik alternatif 269,27 detik; gain/crossfade saat runtime.
- **Crickets Ambient Noise — loopable**, Wolfgang_ / Ted Kerr, CC0: https://opengameart.org/content/crickets-ambient-noise-loopable — `crickets_1.mp3`, ambience luar ruang dengan gain transisi.
- Sembilan klip tambahan dari **16 Monster Growls** yang sama (StarNinjas, CC0). Total empat rekaman per jenis makhluk, tanpa pengulangan langsung. Nomor sumber: Penjaga 1/2/3/4, Pendengar 5/6/7/8, Penyergap 10/11/12/14.

Semua tambahan dicatat bersama SHA-256 di `assets/story_audio/manifest.json`; kredit dibundel dalam `licenses/Story-audio-CC0.txt`. Bank aspal dan metal merupakan adaptasi kecil pitch dari langkah beton Kenney, bukan rekaman lokasi kampus. Hum mekanis disintesis. Karakter, siluet bayangan, prop motor/tangga/pemancar, dan tile rumput/aspal/trotoar dibuat dari kode. Floorplan, jumlah lantai yang bisa dimainkan, serta menara servis adalah rancangan fiksi untuk permainan.

Ikon perlengkapan, pouch barang penting, backpack dan medali pencapaian dari kode proyek. Ikon tersebut dipakai pada UI serta item di dunia. Tidak menambahkan aset gambar eksternal. Bunyi alarm dan penghargaan disintesis; cue minum/lakban/pemasangan memakai foley Kenney yang sudah dibundel.


Dialog memakai bunyi percakapan Arga/Nara yang disintesis dari kode proyek: nada/harmonik, envelope pendek dan variasi pitch. Tidak memakai sampel, musik atau berkas suara Undertale. Inspirasi sebatas bunyi teks bergaya RPG. Penanda tujuan dan label interaksi juga digambar dari kode, tanpa aset eksternal baru.

## Kode proyek

Lisensi publik untuk kode utama belum ditetapkan. Ketentuan CC0 di atas berlaku pada aset yang dinyatakan CC0, bukan otomatis pada seluruh proyek atau foto/lambang ITS.
