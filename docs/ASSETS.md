# Aset

Game membaca aset lokal di `assets/`; tidak ada unduhan saat bermain. `horror/resources.py` menyatukan root aset source dan executable.

| Folder | Isi aktif | Asal |
| --- | --- | --- |
| `assets/kenney/` | 23 tile lantai/furnitur, manifest dan lisensi | Top-down Shooter, Kenney, CC0 |
| `assets/audio/` | 25 klip langkah, pintu dan foley, manifest dan lisensi | Kenney Impact Sounds / RPG Audio, CC0 |
| `assets/story_audio/` | 17 rekaman musik, ambience, stinger dan monster | Kreator CC0 pada kredit |
| `assets/campus/photos/` | Tiga foto gedung dan manifest sumber | Publikasi ITS |
| `assets/branding/` | Lambang ITS dan sumber | Panduan identitas visual ITS |

Karakter, monster, pintu, stairs, ikon, kertas/buku dan detail dunia digambar dari kode. Ilustrasi kampus lama dan sprite manusia/monster lama sudah tidak dibundel. Foto/logo ITS tidak memiliki lisensi CC0; lihat [acuan ITS](ITS_REFERENCES.md) dan [kredit lengkap](../THIRD_PARTY_NOTICES.md).

## Audit

```powershell
.\.venv\Scripts\python.exe tools/audit_assets.py
```

Audit bersifat read-only terhadap aset. Ia melacak pembacaan gambar/audio saat membangun semua jenis layout, seluruh lantai atas, variasi lantai/furnitur, foto menu/logo dan seluruh bank audio; kemudian memeriksa hash manifest. Aset media yang tersisa tetapi tidak digunakan dilaporkan pada [assets-audit.json](assets-audit.json). Audit tidak menghapus file otomatis.

Perapian rilis menghapus **83 berkas / 277.468 byte** yang telah tergantikan. Nama, hash dan alasan penghapusan ada pada [asset-cleanup.json](asset-cleanup.json). Ada **69 berkas media aktif** setelah cleanup. Lisensi dan manifest tetap disimpan; screenshot dokumentasi bukan aset runtime.

## Import ulang

`tools/import_game_assets.py` mengunduh ZIP resmi Kenney jika cache belum tersedia, lalu menyalin tile pada `horror/asset_catalog.py`. `tools/import_audio.py` membaca arsip `build/audio-source/impact.zip` dan `rpg.zip` yang harus sudah tersedia, lalu menyalin daftar klip terkurasi. Keduanya menulis sumber dan SHA-256. Jalankan importer dari root proyek, lalu audit kembali.

Musik dan media ITS sudah dibundel beserta sumber/hash; tidak ada importer otomatis untuk mengunduh ulang keduanya. Simpan metadata sumber ketika mengganti berkas. Jangan memasukkan arsip sumber, `.venv`, cache build atau screenshot ke paket runtime.
