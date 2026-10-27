# Acuan ITS — rilis 0.1

Menu menggunakan tiga foto gedung asli dengan skala proporsional, palet horor, kontur, pencahayaan dan kabut saat runtime. Foto sumber tetap utuh. Menu memakai palet malam; exterior pembuka memakai senja. Gambar berganti setiap sembilan detik dan memenuhi viewport dengan crop proporsional tanpa meregangkan bangunan.

| Media | Publikasi resmi | Berkas yang dibundel |
| --- | --- | --- |
| Rektorat dan kolam depan | [UKP ITS — Tentang](https://www.its.ac.id/ukp/tentang/) | [Kolam-Rektorat.jpg](https://www.its.ac.id/ukp/wp-content/uploads/sites/167/2024/08/Kolam-Rektorat.jpg) → `assets/campus/photos/rektorat.jpg` |
| Tower 2 | [Berita peresmian Tower 2 ITS](https://www.its.ac.id/news/its-resmikan-tower-2-guna-menunjang-kebutuhan-akademik/) | [DJI_0954-scaled.jpg](https://www.its.ac.id/news/wp-content/uploads/sites/2/2023/08/DJI_0954-scaled.jpg) → `assets/campus/photos/tower2.jpg` |
| Informatika saat senja, sesuai foto referensi pengguna | [Departemen Teknik Informatika ITS](https://www.its.ac.id/informatika/) | [IFl-1.jpg](https://www.its.ac.id/informatika/wp-content/uploads/sites/44/2018/03/IFl-1.jpg) → `assets/campus/photos/informatika.jpg` |
| Lambang ITS berwarna | [Panduan Identitas Visual ITS](https://www.its.ac.id/tentang/panduan-identitas-visual/) → folder Lambang | [LAMBANG ITS.png](https://drive.google.com/file/d/1HNRAJR0T24f42mlCu0iTwwlJIz0YzgXz/view) → `assets/branding/its-crest.png` |

PNG lambang transparan dipakai dengan rasio 1:1 dan warna aslinya. Sumber, ukuran dan SHA-256 tercatat pada `assets/campus/photos/manifest.json` dan `assets/branding/source.json`. Foto/lambang adalah media ITS, **bukan aset CC0**. Penggunaan sebagai latar/lambang lokasi dalam permainan ini tidak menyatakan dukungan atau afiliasi resmi. Kredit juga ada dalam THIRD_PARTY_NOTICES.md paket Windows. Game berjalan offline; tidak mengunduh gambar saat dimainkan.

Denah publik ditelusuri dari [halaman UTBK resmi ITS](https://utbk.its.ac.id/), baris Departemen Teknik Informatika, menuju [folder denah Informatika](https://drive.google.com/drive/folders/1Rg_n3cKVlvx6kBb2EL0linT-FxPHZZg4). Berkas acuannya:

- [Gedung (1).jpg](https://drive.google.com/file/d/1k1H68bLRd7YSiCA7D1Y64NqNAn488BFN/view): tiga sayap mengelilingi courtyard, akses dari timur/selatan dan area parkir.
- [Lantai 3 - Teknik Informatika (1).jpg](https://drive.google.com/file/d/1FIoYRVd2O5F6bJ37l5Avx4-vbZuia_lv/view): dua sayap panjang dan koridor penghubung; Lab Pemrograman 1/2, NETICS serta empat posisi tangga.

Lantai dasar kini level tersendiri **64×48 tile / 2560×1920 unit**. Lab proyek **20×11 tile** memiliki satu pintu ke selasar, dengan meja kerja dan ponsel sedang dicas. Desain saat ini menghapus papan deadline serta label dekoratif; konteks proyek tetap dijelaskan dalam prolog, dan navigasi memakai HUD/penanda native. Area lain meliputi ruang diskusi, selasar utara/selatan, lobi, courtyard rumput dengan jalur beton serta empat landing tangga. Pintu main/south/courtyard dipasangkan ke footprint kampus **17×15**; footprint luar tidak lagi berisi miniatur lab yang bisa dimasuki.

Lantai 2 dan 3 masing-masing **38×44 tile**. Lantai 3 mengikuti topologi/lab pada denah UTBK. **Ruangan dasar dan lantai 2 diadaptasi untuk cerita**, karena denah lengkap kedua lantai itu tidak tersedia dalam folder acuan. Jumlah tile, fungsi ruang proyek, furnitur dan detail akses bukan ukuran bangunan hasil pengukuran atau replika 1:1. [Fasilitas Informatika ITS](https://www.its.ac.id/informatika/fasilitas/) menjadi acuan fungsi umum ruang.

Peta kampus yang lebih luas tetap memakai posisi relatif dari referensi sebelumnya. Tower 2 pada home screen berbeda dari menara pemancar fiktif dalam cerita. Save versi 1–6 tetap dimuat: progres dan barang dijaga; posisi pada interior dasar lama dipindah ke area baru. Prolog lama yang masih aktif dimulai kembali dengan naskah baru; prolog yang sudah selesai tidak diputar ulang.
