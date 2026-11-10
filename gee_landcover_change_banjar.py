# -*- coding: utf-8 -*-
"""
Peta Perubahan Tutupan Lahan Kabupaten Banjar, Kalimantan Selatan,
2025 vs 2026 — VERSI GOOGLE EARTH ENGINE (GEE).

Jalankan di Google Colab (lihat juga notebook landcover_change_banjar_GEE.ipynb)
atau di komputer lokal setelah `pip install earthengine-api geemap`.

PRASYARAT (sekali saja, oleh pemilik akun Google):
  1. Daftar di https://code.earthengine.google.com (akun Google biasa).
  2. Buat Google Cloud project di https://console.cloud.google.com,
     aktifkan Earth Engine API, lalu isi PROJECT_ID di bawah.
  3. Saat pertama kali jalan, ee.Authenticate() akan meminta token:
     buka link yang muncul, salin tokennya, paste ke Colab.

Isi pipeline SAMA dengan versi Planetary Computer (tanpa-login):
  - Wilayah: Kabupaten Banjar (batas WM/geoLab/geoBoundaries/600/ADM2).
  - Citra: Landsat 8 + Landsat 9 Collection 2 Level-2 Surface Reflectance,
    komposit median Juni-September 2025 vs 2026, mask awan QA_PIXEL.
  - Fitur (14): band B2-B7 + NDVI, NDWI, NDBI, EVI, NDMI, BSI
    + elevasi (SRTM 30 m, nilai negatif -> 0) + kemiringan (slope SRTM).
  - 5 kelas: 1 Hutan, 2 Pertanian & Perkebunan, 3 Permukiman / Lahan
    Terbangun, 4 Badan Air & Rawa, 5 Lahan Terbuka & Semak Belukar.
  - Training/validasi: ESA WorldCover 2021 (bukan cek lapangan!)
    dipetakan ke 5 kelas; sampel hanya dari piksel yang kemurniannya
    >= 8/9 (tetangga 3x3 sekelas), 2500 lokasi/kelas, split 70% / 30%
    stratified per kelas.
  - Klasifikasi: Random Forest ee.Classifier.smileRandomForest(300),
    dilatih POOLED pada komposit 2025 DAN 2026 (lokasi sampel sama).
  - Perubahan: post-classification comparison (matriks transisi + luas).
  - Hasil diekspor ke Google Drive (GeoTIFF) dan dicetak di console.

CATATAN HASIL: versi Planetary Computer (metode sama) mencapai
OA 2025 = 0,679, Kappa = 0,599; OA 2026 = 0,689, Kappa = 0,611
— di bawah target OA >= 0,85. Versi GEE ini BELUM pernah dijalankan
(belum ada login GEE); angka di atas hanya dari versi PC.
"""
import ee

# ============================== KONFIGURASI ==============================
PROJECT_ID = "NAMA-PROJECT-GCP-ANDA"   # <-- GANTI dengan Google Cloud project Anda
TAHUN_A, TAHUN_B = 2025, 2026
BULAN_AWAL, BULAN_AKHIR = 6, 9          # Juni-September (musim kemarau)
N_POHON = 300
N_TITIK_PER_KELAS = 2500
SEED = 42
SKALA_M = 30
CRS = "EPSG:32650"                      # UTM zona 50S

KELAS = {
    1: "Hutan",
    2: "Pertanian & Perkebunan",
    3: "Permukiman / Lahan Terbangun",
    4: "Badan Air & Rawa",
    5: "Lahan Terbuka & Semak Belukar",
}
# WorldCover 2021 -> 5 kelas
WC_DARI = [10, 95, 40, 50, 80, 90, 20, 30, 60]
WC_KE = [1, 1, 2, 3, 4, 4, 5, 5, 5]
BAND_SR = ["SR_B2", "SR_B3", "SR_B4", "SR_B5", "SR_B6", "SR_B7"]
BAND_INDEKS = ["NDVI", "NDWI", "NDBI", "EVI", "NDMI", "BSI"]
BAND_DEM = ["elevasi", "kemiringan"]
BAND_FITUR = BAND_SR + BAND_INDEKS + BAND_DEM   # 14 fitur
# =========================================================================


def autentikasi():
    """Login GEE (sekali per sesi Colab)."""
    ee.Authenticate()                    # paste token saat diminta
    ee.Initialize(project=PROJECT_ID)
    print("GEE aktif, project:", PROJECT_ID)


def batas_banjar():
    """Batas Kabupaten Banjar dari geoBoundaries ADM2 (sumber BPS)."""
    fc = (ee.FeatureCollection("WM/geoLab/geoBoundaries/600/ADM2")
          .filter(ee.Filter.eq("shapeName", "Banjar"))
          # pengaman: hanya poligon di Kalimantan Selatan
          .filterBounds(ee.Geometry.Rectangle([114.5, -3.74, 115.6, -2.82])))
    roi = fc.geometry()
    luas_km2 = roi.area().divide(1e6).getInfo()
    print(f"Luas batas Banjar (geoBoundaries): {luas_km2:,.2f} km2 "
          f"(BPS: 4.668,50 km2)")
    return roi


def mask_awan(img):
    """Mask awan/bayangan/cirrus dari QA_PIXEL Landsat C2 L2."""
    qa = img.select("QA_PIXEL")
    # bit 1: dilated cloud, bit 2: cirrus, bit 3: cloud, bit 4: cloud shadow
    mask = (qa.bitwiseAnd(1 << 1).eq(0)
            .And(qa.bitwiseAnd(1 << 2).eq(0))
            .And(qa.bitwiseAnd(1 << 3).eq(0))
            .And(qa.bitwiseAnd(1 << 4).eq(0)))
    return img.updateMask(mask)


def skala_sr(img):
    """Ubah SR (DN) ke reflektansi: 0,0000275 * DN - 0,2."""
    opt = img.select(BAND_SR).multiply(0.0000275).add(-0.2)
    return img.addBands(opt, None, True)


def tambah_indeks(img):
    """NDVI, NDWI, NDBI, EVI, NDMI, BSI dari band reflektansi."""
    ndvi = img.normalizedDifference(["SR_B5", "SR_B4"]).rename("NDVI")
    ndwi = img.normalizedDifference(["SR_B3", "SR_B5"]).rename("NDWI")
    ndbi = img.normalizedDifference(["SR_B6", "SR_B5"]).rename("NDBI")
    evi = img.expression(
        "2.5 * (NIR - RED) / (NIR + 6 * RED - 7.5 * BLUE + 1)",
        {"NIR": img.select("SR_B5"), "RED": img.select("SR_B4"),
         "BLUE": img.select("SR_B2")}).rename("EVI")
    ndmi = img.normalizedDifference(["SR_B5", "SR_B6"]).rename("NDMI")
    bsi = img.expression(
        "((SWIR1 + RED) - (NIR + BLUE)) / ((SWIR1 + RED) + (NIR + BLUE))",
        {"SWIR1": img.select("SR_B6"), "RED": img.select("SR_B4"),
         "NIR": img.select("SR_B5"), "BLUE": img.select("SR_B2")}).rename("BSI")
    return img.addBands([ndvi, ndwi, ndbi, evi, ndmi, bsi])


def tambah_dem(img, roi):
    """Elevasi SRTM 30 m (negatif -> 0) + kemiringan, dipotong ke ROI."""
    srtm = ee.Image("USGS/SRTMGL1_003").clip(roi)
    elev = srtm.rename("elevasi").max(0)   # artefak negatif di atas air -> 0
    slope = ee.Terrain.slope(srtm).rename("kemiringan")
    return img.addBands([elev, slope])


def komposit(tahun, roi):
    """Komposit median Landsat 8+9 Jun-Sep satu tahun + 6 indeks + DEM."""
    awal = f"{tahun}-{BULAN_AWAL:02d}-01"
    akhir = f"{tahun}-{BULAN_AKHIR:02d}-30"
    col = (ee.ImageCollection("LANDSAT/LC08/C02/T1_L2")
           .merge(ee.ImageCollection("LANDSAT/LC09/C02/T1_L2"))
           .filterBounds(roi)
           .filterDate(awal, akhir)
           .map(mask_awan)
           .map(skala_sr)
           .map(tambah_indeks)
           .select(BAND_SR + BAND_INDEKS))
    n = col.size().getInfo()
    print(f"Komposit {tahun}: {n} scene dipakai")
    komp = col.median().clip(roi)
    return tambah_dem(komp, roi)


def kelas_referensi():
    """ESA WorldCover 2021 dipetakan ke 5 kelas tugas."""
    wc = ee.ImageCollection("ESA/WorldCover/v200").first().select("Map")
    return wc.remap(WC_DARI, WC_KE, 0).rename("kelas")


def peta_kemurnian(kelas_img):
    """Jumlah piksel sekelas di tetangga 3x3 (0-9); sampel hanya yang >= 8.

    Padanan di GEE untuk kemurnian WorldCover 10 m pada versi PC:
    di sini kemurnian dihitung pada grid 30 m (jumlah tetangga 3x3
    yang sekelas dengan piksel pusat, termasuk pusat).
    """
    total = ee.Image(0)
    for c in KELAS:
        satu = kelas_img.eq(c)
        cnt = satu.reduceNeighborhood(
            reducer=ee.Reducer.sum(),
            kernel=ee.Kernel.square(1, "pixels"))
        total = total.where(kelas_img.eq(c), cnt)
    return total.rename("kemurnian")


def ambil_sampel(komposit_ref, kelas_img, roi):
    """Sampel stratified dari WorldCover (murni >=8/9); split 70/30."""
    kemurnian = peta_kemurnian(kelas_img)
    dasar = komposit_ref.addBands(kelas_img).addBands(kemurnian)
    # stratifiedSample pada komposit 2025; hanya piksel murni yang lolos
    # (filter diterapkan pada hasil sampling)
    sampel = dasar.stratifiedSample(
        numPoints=N_TITIK_PER_KELAS, classBand="kelas", region=roi,
        scale=SKALA_M, seed=SEED, geometries=True)
    sampel = sampel.filter(ee.Filter.gte("kemurnian", 8))
    sampel = sampel.randomColumn("acak", SEED)
    latih = sampel.filter(ee.Filter.lt("acak", 0.7))
    validasi = sampel.filter(ee.Filter.gte("acak", 0.7))
    print(f"Sampel latih: {latih.size().getInfo()}, "
          f"validasi: {validasi.size().getInfo()}")
    return latih, validasi


def akurasi(clf, validasi, komp, nama):
    """OA, Kappa, Producer/User dari data validasi pada satu tahun."""
    pred = validasi.classify(clf)
    matriks = pred.errorMatrix("kelas", "classification")
    print(f"\n--- Akurasi {nama} (validasi 30%, label WorldCover 2021) ---")
    print("Overall Accuracy:", round(matriks.accuracy().getInfo(), 4))
    print("Kappa:", round(matriks.kappa().getInfo(), 4))
    print("Producer's accuracy per kelas:",
          [round(x, 3) for x in matriks.producersAccuracy().getInfo()])
    print("User's accuracy per kelas:",
          [round(x, 3) for x in matriks.consumersAccuracy().getInfo()])
    print("Confusion matrix (baris=referensi, kolom=prediksi):")
    print(matriks.array().getInfo())
    return matriks


def hitung_luas(img_kelas, roi, nama):
    """Luas (ha) per kelas dari citra klasifikasi."""
    luas = (ee.Image.pixelArea().addBands(img_kelas)
            .reduceRegion(reducer=ee.Reducer.sum().group(
                groupField=1, groupName="kelas"),
                geometry=roi, scale=SKALA_M, maxPixels=1e13))
    total = 0.0
    print(f"\n--- Luas {nama} ---")
    for g in luas.get("groups").getInfo():
        k, ha = int(g["kelas"]), g["sum"] / 1e4
        total += ha
        print(f"  {k} {KELAS[k]:35s} {ha:12,.1f} ha ({ha/466850*100:5.2f}%)")
    print(f"  {'TOTAL':35s} {total:12,.1f} ha")
    return total


def matriks_transisi(kls_a, kls_b, roi):
    """Matriks transisi 5x5 (ha) dari tahun A ke tahun B."""
    kode = kls_a.multiply(10).add(kls_b).rename("perubahan")
    out = (ee.Image.pixelArea().addBands(kode)
           .reduceRegion(reducer=ee.Reducer.sum().group(
               groupField=1, groupName="perubahan"),
               geometry=roi, scale=SKALA_M, maxPixels=1e13))
    mat = {(a, b): 0.0 for a in KELAS for b in KELAS}
    for g in out.get("groups").getInfo():
        kode_val = int(g["perubahan"])
        a, b = kode_val // 10, kode_val % 10
        if (a, b) in mat:
            mat[(a, b)] = g["sum"] / 1e4
    print("\n--- Matriks transisi 2025 -> 2026 (ha) ---")
    print("dari \\ ke | " + " | ".join(f"{KELAS[k][:12]:>12s}" for k in KELAS))
    for a in KELAS:
        print(f"{KELAS[a][:9]:9s} | " +
              " | ".join(f"{mat[(a, b)]:12,.0f}" for b in KELAS))
    # 3 transisi perubahan terbesar (a != b)
    trans = sorted(((v, a, b) for (a, b), v in mat.items() if a != b),
                   reverse=True)[:3]
    print("\n3 transisi perubahan terbesar:")
    for v, a, b in trans:
        print(f"  {KELAS[a]} -> {KELAS[b]}: {v:,.1f} ha")
    return kode, mat


def main():
    autentikasi()
    roi = batas_banjar()
    komp_a = komposit(TAHUN_A, roi)
    komp_b = komposit(TAHUN_B, roi)
    kelas_img = kelas_referensi()

    latih, validasi = ambil_sampel(komp_a, kelas_img, roi)
    # POOLED: lokasi latih yang sama dipakai dengan fitur 2026 juga
    latih_2026 = komp_b.sampleRegions(
        collection=latih, scale=SKALA_M, geometries=False)
    latih_pooled = latih.merge(latih_2026)
    print(f"Baris latih pooled: {latih_pooled.size().getInfo()}")
    clf = ee.Classifier.smileRandomForest(N_POHON).train(
        latih_pooled, "kelas", BAND_FITUR)
    kls_a = komp_a.classify(clf).rename("kelas").toUint8()
    kls_b = komp_b.classify(clf).rename("kelas").toUint8()

    # ---- Akurasi per tahun (data validasi, terhadap label WorldCover) ----
    # validasi sudah membawa fitur 2025; untuk 2026 ambil fitur di titik sama
    validasi_2026 = komp_b.sampleRegions(
        collection=validasi, scale=SKALA_M, geometries=False)
    akurasi(clf, validasi, komp_a, f"validasi {TAHUN_A} (model pooled)")
    akurasi(clf, validasi_2026, komp_b, f"validasi {TAHUN_B} (model pooled)")

    hitung_luas(kls_a, roi, f"klasifikasi {TAHUN_A}")
    hitung_luas(kls_b, roi, f"klasifikasi {TAHUN_B}")
    kode, _ = matriks_transisi(kls_a, kls_b, roi)

    # ---- Ekspor ke Google Drive ----
    for img, nama in [(kls_a, f"klasifikasi_{TAHUN_A}"),
                      (kls_b, f"klasifikasi_{TAHUN_B}"),
                      (kode.toUint8(), f"perubahan_{TAHUN_A}_{TAHUN_B}")]:
        tugas = ee.batch.Export.image.toDrive(
            image=img, description=nama, folder="GEE_Banjar",
            fileNamePrefix=nama, region=roi, scale=SKALA_M,
            crs=CRS, maxPixels=1e13)
        tugas.start()
        print("Ekspor dimulai:", nama, "-> Google Drive / GEE_Banjar /")
    print("\nSELESAI. Periksa status ekspor di https://code.earthengine.google.com/tasks")
    print("CATATAN: akurasi di atas memakai label WorldCover 2021 sebagai "
          "referensi, BUKAN cek lapangan.")


if __name__ == "__main__":
    main()
