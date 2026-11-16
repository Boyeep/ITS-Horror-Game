# Pengembangan

Gunakan Python 3.12, `.venv`, dan dependency terkunci pada `requirements-dev.txt`. Jalankan perintah dari root proyek. Panduan instalasi ada di [README](README.md).

## Batas modul

`App` mengatur input, mode dan lifecycle. View di `horror/ui/` membaca state melalui controller. `Renderer` mengatur kamera, pencahayaan dan komposisi; `horror/rendering/` menangani dunia statis serta HUD/peta. View dan renderer tidak boleh mengubah progres cerita atau isi save saat menggambar.

`Session` menyimpan simulasi bersama. `StorySession` menambahkan progres cerita dan perpindahan level; `story_data.py` menyimpan konten dan `story_state.py` menangani snapshot/restore. Rincian dependensi: [arsitektur](docs/ARCHITECTURE.md).

## Verifikasi perubahan

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests
.\.venv\Scripts\python.exe main.py --validate 100
.\.venv\Scripts\python.exe tools/audit_assets.py
```

Untuk perubahan progresi, jalankan `tools/story_probe.py`. Untuk perubahan tampilan, jalankan `tools/review_presentation.py --headless`, lalu periksa screenshot terkait. Untuk mixer/window Windows, jalankan `tools/native_smoke.py`. Setelah build, jalankan `tools/frozen_smoke.py` dan `tools/verify_release.py`.

Tes memakai temporary directory untuk data pengguna. Saat mencoba source secara manual, gunakan `main.py --data-dir build/dev-profile` agar terpisah dari save pribadi. Jangan menghapus `%APPDATA%/ITS-Horror-Game/` sebagai bagian dari cleanup proyek.

## Menambah konten dan aset

- Pertahankan satu sumber collision/navigation bagi dinding, pintu dan furnitur.
- Tambahkan objective di `story_data.py`, perilaku di `story.py`, dan navigasi penanda di `guidance.py` bila diperlukan.
- Aset baru harus memiliki sumber, lisensi, serta SHA-256. Ikuti [panduan aset](docs/ASSETS.md); importer harus menghasilkan daftar yang sama dengan runtime.
- Save schema berbeda dari versi produk. Ubah schema hanya bila perlu, dengan migrasi serta tes pemulihan save lama.
- Nomor produk cukup diubah di `horror/version.py`; jangan menyalin versi ke banyak modul.

## Build Windows

`Build.bat` memasang dependency build, mengaudit aset, menghasilkan manifest DPI/metadata versi, membuat executable, lalu mengemas ZIP portable beserta panduan dan lisensi. Hasil ada di `dist/`, berkas antara di `build/`; keduanya diabaikan Git. `tools/windows.manifest` adalah template, bukan manifest siap pakai untuk PyInstaller langsung.

Kode utama belum memiliki lisensi publik yang ditetapkan. Jangan menganggap lisensi CC0 aset memberikan izin yang sama terhadap seluruh source atau media ITS.

## Menyiapkan versi produk

Integrasi fitur v0.2 berada pada branch `v0.2`; PR promosi menargetkan `beta`. Gunakan commit `type(scope): ringkasan`. Ubah `horror/version.py`, README, changelog, catatan rilis, dan identitas presentasi bersama-sama. Save schema tidak perlu dinaikkan hanya karena versi produk berubah.

Jalankan unit test dan simpan output ke `build/unit-test.log`; ulangi validasi map, audit, campaign, serta capture yang terkait. Bangun ulang executable setelah mengubah versi, jalankan smoke native/frozen, lalu `tools/verify_release.py` untuk mencocokkan Windows metadata, aset, ZIP, dan tautan dokumentasi. Laporan lama di `docs/reviews/` dipertahankan sebagai riwayat; angka QA aktif harus merujuk eksekusi terbaru.

Sertakan PowerPoint yang dapat diedit pada `docs/presentations/` dan perbarui [panduan presentasi](docs/PRESENTATION.md). Jangan commit `.venv`, build, dist, cache, atau data save pribadi. Pembuatan PR tidak otomatis membuat tag, menerbitkan release, atau menyatakan playtest manusia selesai.
