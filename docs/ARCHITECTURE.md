# Arsitektur

## Alur runtime

`main.py` membaca argumen, memilih mode, dan membuat `App`. Loop aplikasi memproses input, memperbarui simulasi/audio, menggambar, lalu mempresentasikan canvas. `App` memegang pengaturan, profil pencapaian, store save dan sesi aktif.

View dipisahkan sebagai mixin dengan antarmuka metode yang tetap. `MenuViews`, `StoryViews`, dan `InventoryViews` menggunakan state serta helper tombol milik `App`; mereka tidak mengimpor controller sehingga tidak membuat siklus dependensi. `WorldRenderer` dan `OverlayRenderer` menggunakan state/helper milik `Renderer` dengan pola yang sama.

| Bagian | Modul | Tanggung jawab |
| --- | --- | --- |
| Lifecycle dan input | `horror/app.py` | Mode, event, update, simpan/muat, dispatch tampilan |
| Tampilan aplikasi | `horror/ui/menus.py`, `story.py`, `inventory.py` | Menu, dialog/puzzle/jurnal, slot, tas, pencapaian |
| Komposisi renderer | `horror/render.py` | Kamera, cahaya, entity native, komposisi frame |
| Dunia dan overlay | `horror/rendering/world.py`, `overlays.py` | Cache dunia statis, dekorasi, objective, HUD, peta |
| Ilustrasi | `art.py`, `characters.py`, `architecture.py`, `pixels.py` | Sprite prosedural, ikon, pintu, stairs, drawing/DPI |
| Atmosfer dan pembacaan | `backdrop.py`, `reader.py`, `narrative.py`, `cinematics.py` | Foto bertema, bukti, dialog, shot/timeline |
| Simulasi bersama | `simulation.py` | Gerak, stamina/HP, monster, interaksi, noise |
| Map dan navigasi | `world.py`, `campus.py`, `floors.py`, `ground_floor.py`, `informatika.py` | Generator, collision, A*, geografi, interior, migrasi posisi |
| Cerita | `story.py`, `story_data.py`, `story_state.py` | Progresi, konten, transisi, snapshot/restore |
| Tujuan | `guidance.py` | Target dan rute tindakan tanpa membocorkan jawaban puzzle |
| Barang dan profil | `inventory.py`, `achievements.py` | Kapasitas, supply, alat, pencapaian lokal |
| Persistensi | `saves.py` | Validasi schema, write atomik, backup, legacy import |
| Audio | `audio.py`, `speech.py` | Bank foley/monster, musik, spasial, cadence teks |
| Metadata dan aset | `version.py`, `resources.py`, `asset_catalog.py`, `config.py` | Versi, path source/frozen, kurasi tile, konstanta gameplay |

## Aturan state dan render

Snapshot berisi state gameplay; cache permukaan, A*, dan font tidak diserialisasi. Menggambar harus tidak mengubah snapshot maupun kamera. Update kamera dilakukan terpisah. Grid yang sama menjadi acuan collision, jalur dan penempatan furnitur.

Dunia memakai viewport dekat dan cahaya raycast, sedangkan teks penting, karakter, pintu serta ikon dikomposisikan pada resolusi layar. Strip cahaya pintu satu piksel harus diduplikasi menjadi minimal dua piksel sebelum `smoothscale` untuk menghindari crash scaler native Windows. Pertahankan tes ini saat mengubah pipeline gambar.

## Persistensi dan rilis

Versi produk 0.1 berada di `version.py`; schema save 7 tidak mengikuti nomor produk. `StoryState` memulihkan data lama melalui migrasi yang ada, kemudian menghitung ulang cache navigasi. Profil achievement terpisah dari save perjalanan.

Path aset dihitung relatif terhadap paket lewat `resources.py`, sehingga source dan executable PyInstaller membaca struktur yang sama. `Build.bat` menjalankan `tools/build_release.py`; metadata Windows dihasilkan dari versi produk. `tools/package_release.py` menambahkan panduan, kredit dan lisensi ke ZIP portable.
