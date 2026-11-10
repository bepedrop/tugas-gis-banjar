# Peta Perubahan Tutupan Lahan Kabupaten Banjar, Kalimantan Selatan, 2025 vs 2026

**Mata kuliah:** Sistem Informasi Geografi (SIG) — **Dosen:** Prof. Dr. Ir. Ahmad Jauhari, M.P.
**Penyusun:** Boy (Program Studi Magister Kehutanan, Universitas Lambung Mangkurat)
**Tanggal pengerjaan:** 10–11 November 2026

---

## 1. Tujuan

Memetakan perubahan tutupan lahan Kabupaten Banjar, Kalimantan Selatan,
antara musim kemarau 2025 dan 2026 dari citra Landsat 8/9, dan menyajikan
hasilnya dalam WebGIS interaktif, file GeoTIFF, serta tabel luas dan
matriks transisi.

## 2. Wilayah

Kabupaten Banjar, Kalimantan Selatan. Luas resmi **BPS 4.668,50 km²**
(466.850 ha). Batas diambil dari **geoBoundaries ADM2** (poligon
`shapeName == 'Banjar'`); luas poligon hasil hitung **4.725,49 km²**
(selisih +1,22% dari BPS, dalam toleransi 5%). Bbox lon 114,5066–115,5958,
lat −3,7307–−2,8282. CRS kerja **EPSG:32650 (UTM zona 50S)**, resolusi 30 m.

## 3. Data

| Data | Sumber | Keterangan |
|---|---|---|
| Landsat 8 & 9, Collection 2 Level-2 Surface Reflectance | Microsoft Planetary Computer STAC (`landsat-c2-l2`) / Google Earth Engine (`LANDSAT/LC08` & `LC09/C02/T1_L2`) | Komposit median Jun–Sep 2025 (10 scene) dan Jun–Sep 2026 (12 scene), cloud cover < 20, mask awan/bayangan/cirrus dari band QA_PIXEL (bit 1–4) |
| Batas administrasi | geoBoundaries ADM2 (`WM/geoLab/geoBoundaries/600/ADM2`) | Poligon Kab. Banjar, divalidasi vs BPS |
| Label training/validasi | ESA WorldCover 2021 (`esa-worldcover` / `ESA/WorldCover/v200`, 10 m) | Dipetakan ke 5 kelas; **bukan cek lapangan** |
| Elevasi & kemiringan | Copernicus DEM 30 m (`cop-dem-glo-30` / `USGS/SRTMGL1_003` di GEE) | DEM min −67 m (artefak di atas air, dipangkas ke 0), maks 1.372,7 m, rerata 142,1 m; kemiringan maks 70,1°, rerata 6,6° |

## 4. Kelas tutupan lahan (5 kelas, sesuai jurnal terbaru)

| Kode | Kelas | Definisi (dari WorldCover 2021) |
|---|---|---|
| 1 | Hutan | Tree cover (10) + Mangroves (95) |
| 2 | Pertanian & Perkebunan | Cropland (40) |
| 3 | Permukiman / Lahan Terbangun | Built-up (50) |
| 4 | Badan Air & Rawa | Permanent water (80) + Herbaceous wetland (90) |
| 5 | Lahan Terbuka & Semak Belukar | Shrubland (20) + Grassland (30) + Bare/sparse vegetation (60) |

## 5. Metode

- **Komposit:** median per piksel dari semua scene Landsat 8/9 Jun–Sep tiap tahun, setelah mask awan QA_PIXEL.
- **Fitur (14):** 6 band Surface Reflectance (B2–B7, skala 0,0000275·DN − 0,2) + NDVI, NDWI, NDBI, EVI, NDMI, BSI + elevasi + kemiringan.
- **Sampel:** 2.500 lokasi per kelas (12.500 lokasi), dipilih secara acak stratified dari piksel WorldCover yang kemurniannya ≥ 8/9 (fraksi piksel 10 m sekelas modus di tiap sel 30 m; versi GEE memakai padanan 3×3 pada grid 30 m), valid di kedua tahun, dan berada di dalam batas Banjar. Split 70% latih / 30% validasi, stratified per kelas.
- **Klasifikasi:** Random Forest, 300 pohon (scikit-learn di versi PC; `ee.Classifier.smileRandomForest(300)` di versi GEE), dilatih **pooled**: lokasi sampel yang sama dipakai dua kali, sekali dengan fitur 2025 dan sekali dengan fitur 2026 (17.500 baris latih), sehingga satu model stabil untuk kedua tahun.
- **Prediksi:** memakai **mask bersama** — hanya piksel yang valid di KEDUA tahun yang diklasifikasi — supaya luas total kedua tahun sama dan matriks transisi konsisten.
- **Perubahan:** post-classification comparison; kode perubahan = kelas2025×10 + kelas2026 (mis. 15 = Hutan → Lahan Terbuka & Semak Belukar).

### Dua jalur pengerjaan (metode dan tabel sama)

| Jalur | File | Kapan dipakai |
|---|---|---|
| **Planetary Computer (tanpa-login)** | `landcover_change_banjar_2025_2026_PC.py`, `landcover_change_banjar_2025_2026_PC.ipynb` | Tidak punya/belum daftar GEE; semua data diunduh dari STAC Planetary Computer yang terbuka |
| **Google Earth Engine (GEE)** | `gee_landcover_change_banjar.py`, `landcover_change_banjar_GEE.ipynb` | Punya akun GEE + Google Cloud project; komputasi di cloud Google, hasil diekspor ke Google Drive folder `GEE_Banjar` |

Kedua jalur menghasilkan 5 kelas, matriks transisi, dan akurasi yang sama.
**Catatan:** versi GEE belum pernah dieksekusi end-to-end (belum ada login GEE
saat penyusunan); jalankan sendiri di Colab dengan akun GEE Anda, lalu
bandingkan hasilnya dengan versi PC. Versi PC sudah dijalankan penuh dan
hasilnya adalah angka pada bagian 6–8 di bawah ini.

## 6. Hasil — luas per kelas (ha)

Luas yang terklasifikasi (mask bersama): **430.839,8 ha** untuk kedua tahun
(= 91,2% dari luas poligon Banjar 472.549 ha; sisanya 41.709 ha / 8,8%
tidak terklasifikasi karena ada celah awan di salah satu tahun).

| Kelas | 2025 (ha) | 2026 (ha) | Perubahan (ha) | Perubahan (%) | Pangsa 2025 | Pangsa 2026 |
|---|---|---|---|---|---|---|
| 1 Hutan | 261.756,4 | 254.677,9 | −7.078,5 | −2,70% | 60,8% | 59,1% |
| 2 Pertanian & Perkebunan | 40.028,8 | 45.037,1 | +5.008,3 | +12,51% | 9,3% | 10,5% |
| 3 Permukiman / Lahan Terbangun | 35.134,5 | 43.998,5 | +8.864,0 | +25,23% | 8,2% | 10,2% |
| 4 Badan Air & Rawa | 27.846,1 | 22.200,3 | −5.645,8 | −20,27% | 6,5% | 5,2% |
| 5 Lahan Terbuka & Semak Belukar | 66.074,1 | 64.926,1 | −1.148,0 | −1,74% | 15,3% | 15,1% |
| **TOTAL terklasifikasi** | **430.839,8** | **430.839,8** | **0** | — | 100% | 100% |

## 7. Hasil — matriks transisi 2025 → 2026 (ha)

Baris = kelas 2025, kolom = kelas 2026. Jumlah baris = luas 2025 per kelas,
jumlah kolom = luas 2026 per kelas (terverifikasi konsisten).

| Dari \ Ke | Hutan | Pertanian & Perkebunan | Permukiman | Badan Air & Rawa | Terbuka & Semak |
|---|---|---|---|---|---|
| **Hutan** | 243.597,1 | 23,9 | 6.545,0 | 293,5 | 11.296,8 |
| **Pertanian & Perkebunan** | 31,7 | 33.556,2 | 2.027,3 | 2.801,0 | 1.612,5 |
| **Permukiman** | 4.573,1 | 1.232,4 | 25.878,4 | 237,7 | 3.212,9 |
| **Badan Air & Rawa** | 563,5 | 5.650,7 | 607,4 | 15.769,8 | 5.254,6 |
| **Terbuka & Semak** | 5.912,5 | 4.573,8 | 8.940,3 | 3.098,3 | 43.549,2 |

- Tidak berubah: **362.350,8 ha (84,1%)**; berubah: **68.489,0 ha (15,9%)**.
- 3 transisi perubahan terbesar:
  1. Hutan → Lahan Terbuka & Semak Belukar: **11.296,8 ha**
  2. Lahan Terbuka & Semak Belukar → Permukiman / Lahan Terbangun: **8.940,3 ha**
  3. Hutan → Permukiman / Lahan Terbangun: **6.545,0 ha**

## 8. Hasil — akurasi (terhadap label WorldCover 2021, bukan cek lapangan)

| | 2025 | 2026 |
|---|---|---|
| **Overall Accuracy (OA)** | **0,679** | **0,689** |
| **Kappa** | **0,599** | **0,611** |

Confusion matrix 2025 (baris = referensi, kolom = prediksi):
Hutan [638, 3, 50, 7, 52]; Pertanian [3, 485, 39, 84, 139];
Permukiman [56, 62, 552, 11, 69]; Air/Rawa [15, 138, 18, 459, 120];
Terbuka/Semak [134, 62, 56, 86, 412].

Confusion matrix 2026:
Hutan [611, 1, 61, 9, 68]; Pertanian [6, 535, 68, 51, 90];
Permukiman [46, 52, 614, 7, 31]; Air/Rawa [13, 153, 33, 429, 122];
Terbuka/Semak [128, 65, 88, 74, 395].

Producer's / User's accuracy per kelas, 2025:
Hutan 0,851 / 0,754; Pertanian 0,647 / 0,647; Permukiman 0,736 / 0,772;
Air/Rawa 0,612 / 0,709; Terbuka/Semak 0,549 / 0,520.
2026: Hutan 0,815 / 0,760; Pertanian 0,713 / 0,664; Permukiman 0,819 / 0,711;
Air/Rawa 0,572 / 0,753; Terbuka/Semak 0,527 / 0,559.

**Target tugas OA ≥ 0,85 dan Kappa ≥ 0,80 TIDAK tercapai.** Upaya perbaikan
yang sudah dicoba (dan hasilnya):
- v1 (9 fitur: 6 band + NDVI/NDWI/NDBI; latih hanya 2025; 1.500 sampel/kelas):
  OA 2025 = 0,621, Kappa 0,526; cek silang ke 2026 runtuh ke OA 0,535.
- v2 (14 fitur + DEM/kemiringan + 5 indeks tambahan; latih pooled dua tahun;
  2.500 sampel/kelas; kemurnian ≥ 8/9): OA 0,679 / 0,689, Kappa 0,599 / 0,611.
- ExtraTrees 300 pohon (pooled): OA 0,662 / 0,669 — **lebih buruk** dari RF.
- Pembersihan label latih berbasis aturan spektral: tidak selesai diuji
  (proses kehabisan memori); tidak dilaporkan sebagai hasil.

Kepentingan fitur model v2: elevasi 0,201; kemiringan 0,160; sisanya
0,038–0,076 (NDWI 0,076 tertinggi di antara fitur spektral).

## 9. Cara menjalankan

### Versi Planetary Computer (tanpa-login)

**Script Python:**
```bash
pip install pystac-client planetary-computer rasterio geopandas scikit-learn
python3 landcover_change_banjar_2025_2026_PC.py
```
Langkah yang sudah ada hasilnya dilewati otomatis (komposit, WorldCover,
DEM, kemurnian). Waktu jalan penuh dari nol: ±35 menit (komposit paling
lama, ±15 menit/tahun) + ±6 menit klasifikasi.

**Notebook Colab (deliverable utama):** buka
`landcover_change_banjar_2025_2026_PC.ipynb` di Google Colab, jalankan
cell 1 (install), lalu jalankan semua cell berurutan. Cell terakhir
mengunduh `hasil_gis_banjar.zip` berisi GeoTIFF, statistik, dan PNG peta.
Notebook ini **sudah diuji end-to-end** dengan `nbconvert --execute` di
direktori kerja bersih (hanya file notebook; semua data diunduh dan
dihasilkan sendiri oleh notebook): 0 error di semua 12 cell code, dan
hasilnya (OA, Kappa, luas, matriks transisi) **identik** dengan hasil
utama di folder ini. Pengujian menemukan satu bug nyata pada cell
kemurnian (reshape array yang kurang) — sudah diperbaiki dan diuji ulang
sampai lolos. Catatan: pengujian memakai kernel Python sistem VM karena
rasterio dari instalasi pip baru di venv menolak sertifikat TLS proxy
keluar VM ini (bukan masalah notebook; di Colab sertifikatnya normal).
Cell berat (komposit, WorldCover, DEM, kemurnian) dilewati otomatis bila
filenya sudah ada, seperti pada script `.py`.

### Versi Google Earth Engine

1. Daftar di https://code.earthengine.google.com, buat Google Cloud
   project, aktifkan Earth Engine API.
2. Buka `landcover_change_banjar_GEE.ipynb` di Colab, isi `PROJECT_ID`,
   jalankan cell autentikasi (paste token saat diminta), lalu semua cell.
   Atau jalankan `gee_landcover_change_banjar.py` setelah
   `pip install earthengine-api geemap`.
3. Hasil diekspor ke Google Drive folder `GEE_Banjar`.

### WebGIS

Buka `peta_perubahan_tutupan_lahan_banjar.html` di browser (file tunggal,
Leaflet via CDN, butuh internet untuk basemap OSM). Overlay raster
di-downsample 4× (~120 m) agar file ringan (0,37 MB).

## 10. File hasil

| File | Isi / ukuran |
|---|---|
| `peta_perubahan_tutupan_lahan_banjar.html` | WebGIS interaktif (0,37 MB) |
| `output/klasifikasi_2025.tif` | Klasifikasi 2025, EPSG:32650, 30 m, 5 kelas + nodata (0,51 MB) |
| `output/klasifikasi_2026.tif` | Klasifikasi 2026, sama (0,53 MB) |
| `output/perubahan_2025_2026.tif` | Kode perubahan 11–55 (0,85 MB) |
| `output/statistik.json` | Luas, matriks transisi, akurasi, confusion matrix |
| `landcover_change_banjar_2025_2026_PC.py` | Script lengkap versi PC (metode v2) |
| `landcover_change_banjar_2025_2026_PC.ipynb` | Notebook Colab versi PC (metode v2) |
| `gee_landcover_change_banjar.py` | Script versi GEE (metode v2) |
| `landcover_change_banjar_GEE.ipynb` | Notebook Colab versi GEE (metode v2) |
| `data/` | Data antara: batas, komposit 2025/2026, WorldCover 30 m, kemurnian, DEM, slope, log |
| `README.md`, `LAPORAN_SINGKAT.md` | Dokumen ini dan ringkasan 1–2 halaman |

## 11. Keterbatasan dan ketidakpastian — baca sebelum memakai angka

1. **Akurasi di bawah target (OA 0,68, bukan 0,85).** Angka perubahan
   (mis. Permukiman +25% dalam satu tahun) sebagian besar adalah
   **noise klasifikasi**, bukan perubahan nyata. Lihat LAPORAN_SINGKAT.md.
2. **Tanpa cek lapangan.** Training/validasi memakai WorldCover 2021
   sebagai referensi. Sawit/karet di WorldCover umumnya tercatat sebagai
   "Tree cover", sehingga Hutan cenderung terlalu luas dan Pertanian &
   Perkebunan terlalu sempit; sawah musim kemarau sebagian tercatat
   sebagai semak/lahan terbuka.
3. **Label 2021 vs citra 2025/2026.** Perubahan lahan selama 4–5 tahun
   membuat sebagian label referensi sudah tidak sesuai saat klasifikasi.
4. **Musim kemarau 2026 lebih kering** (El Niño sedang–kuat, puncak
   musim kemarau Agu–Sep 2026): rawa mengering (NDBI Badan Air & Rawa
   naik dari −0,157 ke +0,075; SWIR1 rerata naik), sehingga sebagian
   Badan Air & Rawa terklasifikasi sebagai Pertanian atau Terbuka/Semak.
5. **8,8% wilayah tidak terklasifikasi** (celah awan di salah satu tahun,
   terutama tile 117/062 pada 2025 yang hanya punya 1 scene).
6. **Tumpang tindih spektral** antar 5 kelas yang luas: kebingungan
   terbesar Terbuka/Semak ↔ Hutan dan Air/Rawa ↔ Pertanian.
7. **DEM mendominasi model** (kepentingan 0,20 + 0,16): sebagian keputusan
   klasifikasi didorong elevasi/kemiringan, bukan spektral — masuk akal
   untuk Banjar (rawa di dataran rendah vs hutan di pegunungan Meratus),
   tapi membuat model kurang sensitif pada perubahan spektral murni.
8. **Resolusi 30 m** dan jendela Jun–Sep: perubahan kecil (mis. pembukaan
   lahan < 1 ha) tidak terdeteksi; sawah yang sedang bera terlihat
   seperti lahan terbuka.
9. **Perubahan yang tampak tidak masuk akal** (mis. Permukiman 2025 →
   Hutan 2026 seluas 4.573 ha) adalah artefak klasifikasi, bukan
   penghijauan kembali permukiman.
10. **Versi GEE belum dieksekusi** — angka hasil berasal dari versi PC.

## 12. Referensi

- Badan Standar Nasional. 2014. **SNI 7645-1:2014** — Klasifikasi Penutup Lahan.
- Kementerian Lingkungan Hidup dan Kehutanan. 2022. *Forest Reference Level (FRL) Indonesia* — 23 kelas penutup lahan nasional.
- IOP Conference Series: Earth and Environmental Science 2866. 2024. Studi perubahan tutupan lahan gambut Kabupaten Banjar 1990–2020 (Landsat, 7 kelas).
- Badan Pusat Statistik Kabupaten Banjar. *Kabupaten Banjar Dalam Angka* — luas 4.668,50 km².
- Microsoft Planetary Computer — koleksi `landsat-c2-l2`, `esa-worldcover`, `cop-dem-glo-30`.
- ESA WorldCover 2021 — Zanaga dkk., *Earth System Science Data* 13, 2021.
- Google Earth Engine — Landsat 8/9 Collection 2 Level-2, geoBoundaries ADM2, SRTM GL1.
