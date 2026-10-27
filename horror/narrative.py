"""Save-friendly presentation metadata; narration never impersonates a speaker."""
DOCUMENT_KINDS={"pesan":"message","rak":"paper","jalur":"paper","rekaman":"screen",
                "jaga":"book","foto":"photo","server":"screen","film":"book",
                "katalog":"book","antena":"screen","nara":"paper","insiden":"paper","sunyi":"screen"}
LEGACY_DOCUMENTS={"Catatan Nara":"rak","Catatan perpustakaan":"rak","Diagram":"jalur",
                  "Buku jaga":"jaga","Kamar Nara":"foto","SIMPUL":"server","Mikrofilm":"film",
                  "Daftar evakuasi":"katalog","Laporan insiden":"insiden"}
DOCUMENT_TEXT={
    "rak":"Loker rektorat · 04\nUrutan rak yang kita lewati:\n2 — 4 — 1 — 3\n\nYang berpita merah itu Juru Malam. Jangan tunggu dia menoleh.\n— Nara",
    "jalur":"KARTU AKSES: kotak sekring Kimia + Elektro\n\nUrutan pemulihan:\n1. AIR — Teknik Lingkungan\n2. MESIN — Teknik Mesin\n3. DATA — Sistem Informasi\n\nSesudahnya: pemancar Taman Alumni.",
    "jaga":"23.18   Nara menitipkan kartu asrama. Menuju perpustakaan.\n23.47   GERBANG GAGAL.\n\nKunci mekanis: ruang servis pemancar.\nJangan buka jalur utama selama jaringan masih mengulang.\n\nTanda tangan petugas: tidak terbaca.",
    "foto":"17 / 08 / 1998\n\nKalau aku terdengar seperti rekaman, tanyakan warna tasmu.\n\nSandi server: tahun pada cap proyek, bukan ulang tahunku.\n— Nara",
    "film":"CATATAN 04 / REKAMAN 17 / EVAKUASI 09\n\nBaca bundel sesuai urutan kejadian. Lemari katalog: satu lantai di bawah.\n\nDaftar evakuasi:\nkotak properti dipindahkan ke Graha ITS.",
    "katalog":"Kunci servis: kotak properti Graha.\n\nPanel pemancar:\nUTARA: hidup\nTENGAH: padam\nSELATAN: hidup\n\nPintu atap tidak dikunci.\n\nIa tidak berdiri di bawah lampu. Ia menunggu di bayangannya.",
    "nara":"Arga,\nPentanahan dulu, lalu generator cadangan, isolasi pemancar, baru konsol atap.\n\nLaporan insidennya ada di rektorat. Aku menunggu di kantin bersama petugas yang terluka.\n\nJangan jawab suara dari ponsel.\n— Nara",
    "insiden":"PROSEDUR PEMUTUSAN SIMPUL\n\n1. Pembumian — halaman Manarul Ilmi\n2. Generator — Teknik Mesin, lantai 2\n3. Isolasi — Robotika, lantai 3\n4. Konsol pemancar — atap\n\nKatup: A, C, B\nIsolasi: UTARA padam / TENGAH hidup / SELATAN padam\nKunci gerbang: lemari servis, lantai 2.",
}


def speech(speaker,body,title=""):
    return {"kind":"speech","speaker":speaker,"title":title or speaker.title(),"body":body}


def document(key):
    return {"kind":DOCUMENT_KINDS[key],"document":key}


def coerce_page(page):
    if isinstance(page,dict):return dict(page)
    title,body=page
    if title in LEGACY_DOCUMENTS:return document(LEGACY_DOCUMENTS[title])
    if title=="Nara":
        if str(body).startswith("23.47"):return document("pesan")
        return speech("nara",body)
    return {"kind":"narration","title":title,"body":body}
