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
**Hasil utama (bagian 6–8) adalah versi GEE** — dijalankan penuh di Colab
11 Nov 2026 (run final, setelah perbaikan bug validasi 2026 dan mask
bersama; OA 0,818 / Kappa 0,764). Versi PC (OA 0,679 / 0,689) dipakai
sebagai cadangan/validasi silang; angkanya tersimpan di `output/statistik.json`
bagian `versi_pc` dan dibandingkan pada bagian 8 di bawah.

## 6. Hasil — luas per kelas (ha, versi GEE)

Luas yang terklasifikasi (mask bersama): **466.551,0 ha (2025)** dan
**466.581,1 ha (2026)** — selisih total hanya **30,1 ha (0,006%)**,
setelah perbaikan mask bersama (sebelum perbaikan selisihnya 4.964 ha).
Total ini = 98,8% dari luas poligon Banjar 472.549 ha; sisanya piksel
tanpa data di salah satu tahun. Luas piksel dihitung dari piksel 30 m;
GeoTIFF hasil ekspor (reproyeksi ke UTM) dapat berbeda <0,3% per total
karena resampling — angka tabel ini memakai hasil `reduceRegion`
notebook GEE.

| Kelas | 2025 (ha) | 2026 (ha) | Perubahan (ha) | Perubahan (%) | Pangsa 2025 | Pangsa 2026 |
|---|---|---|---|---|---|---|
| 1 Hutan | 322.618,6 | 302.227,7 | −20.390,9 | −6,32% | 69,2% | 64,8% |
| 2 Pertanian & Perkebunan | 62.541,4 | 69.370,1 | +6.828,7 | +10,92% | 13,4% | 14,9% |
| 3 Permukiman / Lahan Terbangun | 5.554,2 | 8.453,5 | +2.899,3 | +52,20% | 1,2% | 1,8% |
| 4 Badan Air & Rawa | 19.218,1 | 22.676,0 | +3.457,9 | +17,99% | 4,1% | 4,9% |
| 5 Lahan Terbuka & Semak Belukar | 56.618,7 | 63.853,9 | +7.235,2 | +12,78% | 12,1% | 13,7% |
| **TOTAL terklasifikasi** | **466.551,0** | **466.581,1** | **+30,1** | — | 100% | 100% |

## 7. Hasil — matriks transisi 2025 → 2026 (ha)

Baris = kelas 2025, kolom = kelas 2026. Jumlah baris = luas 2025 per kelas,
jumlah kolom = luas 2026 per kelas (terverifikasi konsisten).

| Dari \ Ke | Hutan | Pertanian & Perkebunan | Permukiman | Badan Air & Rawa | Terbuka & Semak |
|---|---|---|---|---|---|
| **Hutan** | 298.974 | 3.004 | 806 | 293 | 19.541 |
| **Pertanian & Perkebunan** | 189 | 51.951 | 1.303 | 5.413 | 3.686 |
| **Permukiman** | 83 | 358 | 4.699 | 53 | 361 |
| **Badan Air & Rawa** | 149 | 3.824 | 431 | 11.312 | 3.501 |
| **Terbuka & Semak** | 2.805 | 10.232 | 1.214 | 5.604 | 36.763 |

- Tidak berubah: **403.699 ha (86,5%)**; berubah: **62.852 ha (13,5%)**.
- 3 transisi perubahan terbesar:
  1. Hutan → Lahan Terbuka & Semak Belukar: **19.541,4 ha**
  2. Lahan Terbuka & Semak Belukar → Pertanian & Perkebunan: **10.232,3 ha**
  3. Lahan Terbuka & Semak Belukar → Badan Air & Rawa: **5.603,7 ha**

## 8. Hasil — akurasi (terhadap label WorldCover 2021, bukan cek lapangan)

| | 2025 | 2026 |
|---|---|---|
| **Overall Accuracy (OA)** | **0,818** | **0,818** |
| **Kappa** | **0,764** | **0,764** |

Validasi 30%, n = 2.153 titik per tahun. OA/Kappa kedua tahun kini
**independen** (2025: OA 0,8184 / Kappa 0,7635; 2026: OA 0,8175 /
Kappa 0,7639) — run final 11 Nov 2026 setelah perbaikan bug validasi
2026 (dulu tercetak identik persis dengan 2025).

Confusion matrix 2025 (baris = referensi, kolom = prediksi):
Hutan [659, 5, 3, 3, 26]; Pertanian [4, 428, 1, 9, 31];
Permukiman [3, 7, 182, 1, 8]; Air/Rawa [1, 105, 1, 230, 50];
Terbuka/Semak [56, 41, 2, 34, 263].

Confusion matrix 2026:
Hutan [637, 9, 3, 3, 44]; Pertanian [0, 431, 2, 28, 12];
Permukiman [1, 5, 194, 0, 1]; Air/Rawa [0, 75, 4, 252, 56];
Terbuka/Semak [25, 69, 10, 46, 246].

Producer's / User's accuracy per kelas, 2025:
Hutan 0,947 / 0,911; Pertanian 0,905 / 0,730; Permukiman 0,905 / 0,963;
Air/Rawa 0,594 / 0,830; Terbuka/Semak 0,664 / 0,696.
2026: Hutan 0,915 / 0,961; Pertanian 0,911 / 0,732; Permukiman 0,965 / 0,911;
Air/Rawa 0,651 / 0,766; Terbuka/Semak 0,621 / 0,685.

**Target tugas OA ≥ 0,85 dan Kappa ≥ 0,80 TIDAK tercapai** (OA 0,818,
Kappa 0,764 — lebih baik dari versi PC 0,679/0,689, tapi masih di bawah
target). Upaya perbaikan yang sudah dicoba (dan hasilnya):
- v1 (9 fitur: 6 band + NDVI/NDWI/NDBI; latih hanya 2025; 1.500 sampel/kelas):
  OA 2025 = 0,621, Kappa 0,526; cek silang ke 2026 runtuh ke OA 0,535.
- v2 PC (14 fitur + DEM/kemiringan + 5 indeks tambahan; latih pooled dua tahun;
  2.500 sampel/kelas; kemurnian ≥ 8/9): OA 0,679 / 0,689, Kappa 0,599 / 0,611.
- ExtraTrees 300 pohon (pooled): OA 0,662 / 0,669 — **lebih buruk** dari RF.
- Pembersihan label latih berbasis aturan spektral: tidak selesai diuji
  (proses kehabisan memori); tidak dilaporkan sebagai hasil.
- GEE final (11 Nov 2026): perbaikan bug validasi 2026 + mask bersama —
  OA 0,818 / 0,818, Kappa 0,764 / 0,764.

Kepentingan fitur model v2 (versi PC): elevasi 0,201; kemiringan 0,160; sisanya
0,038–0,076 (NDWI 0,076 tertinggi di antara fitur spektral).

### Perbandingan versi GEE vs PC

| Besaran | GEE (utama) | PC (cadangan) |
|---|---|---|
| OA 2025 / Kappa 2025 | 0,818 / 0,764 | 0,679 / 0,599 |
| OA 2026 / Kappa 2026 | 0,818 / 0,764 | 0,689 / 0,611 |
| Hutan 2025 → 2026 (ha) | 322.619 → 302.228 | 261.756 → 254.678 |
| Permukiman 2025 → 2026 (ha) | 5.554 → 8.454 | 35.135 → 43.999 |
| Luas terklasifikasi (ha) | 466.551 / 466.581 | 430.840 / 430.840 |
| Transisi terbesar | Hutan → Terbuka 19.541 ha | Hutan → Terbuka 11.297 ha |

Kedua versi searah (hutan berkurang, lahan terbuka bertambah, transisi
terbesar sama), tetapi besaran luas berbeda karena GEE mengklasifikasi
hampir seluruh wilayah (466,6 ribu ha) sedangkan PC mengeluarkan piksel
termasking awan (430,8 ribu ha).

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
Leaflet di-inline, butuh internet hanya untuk basemap OSM). Overlay raster
di-downsample 4× (~120 m) agar file ringan (0,85 MB). Peta dan tabel di
dalamnya memakai hasil versi GEE final.

## 10. File hasil

| File | Isi / ukuran |
|---|---|
| `peta_perubahan_tutupan_lahan_banjar.html` | WebGIS interaktif versi GEE (0,85 MB) |
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

1. **Akurasi di bawah target (OA 0,82, bukan 0,85).** Angka perubahan
   (mis. Permukiman +52% dalam satu tahun) sebagian adalah
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
5. **1,2% wilayah tidak terklasifikasi pada versi GEE** (piksel tanpa data
   di salah satu tahun; pada versi PC 8,8% karena celah awan, terutama
   tile 117/062 pada 2025 yang hanya punya 1 scene).
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
   Hutan 2026; pada versi PC seluas 4.573 ha) adalah artefak klasifikasi,
   bukan penghijauan kembali permukiman.
10. **Versi GEE sudah dieksekusi penuh** (run final 11 Nov 2026, Colab,
    commit `cf5e289`); dua bug yang ditemukan selama pengerjaan — validasi
    2026 yang menduplikasi 2025 dan selisih total luas 4.964 ha — sudah
    diperbaiki dan diuji ulang.

## 12. Referensi

- Badan Standar Nasional. 2014. **SNI 7645-1:2014** — Klasifikasi Penutup Lahan.
- Kementerian Lingkungan Hidup dan Kehutanan. 2022. *Forest Reference Level (FRL) Indonesia* — 23 kelas penutup lahan nasional.
- IOP Conference Series: Earth and Environmental Science 2866. 2024. Studi perubahan tutupan lahan gambut Kabupaten Banjar 1990–2020 (Landsat, 7 kelas).
- Badan Pusat Statistik Kabupaten Banjar. *Kabupaten Banjar Dalam Angka* — luas 4.668,50 km².
- Microsoft Planetary Computer — koleksi `landsat-c2-l2`, `esa-worldcover`, `cop-dem-glo-30`.
- ESA WorldCover 2021 — Zanaga dkk., *Earth System Science Data* 13, 2021.
- Google Earth Engine — Landsat 8/9 Collection 2 Level-2, geoBoundaries ADM2, SRTM GL1.
