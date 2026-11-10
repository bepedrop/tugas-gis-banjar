# -*- coding: utf-8 -*-
"""
Peta Perubahan Tutupan Lahan Kabupaten Banjar, Kalimantan Selatan,
2025 vs 2026 — VERSI MICROSOFT PLANETARY COMPUTER (tanpa-login).

Jalankan:  python3 landcover_change_banjar_2025_2026_PC.py
           (atau buka notebook landcover_change_banjar_2025_2026_PC.ipynb
            di Google Colab — cell pertama menginstall semua package)

Alur:  1) batas Banjar dari geoBoundaries ADM2 (divalidasi vs BPS 4.668,50 km2)
       2) cari scene Landsat 8/9 C2 L2 di STAC Planetary Computer
       3) komposit median Jun-Sep 2025 & 2026, mask awan QA_PIXEL
       4) ESA WorldCover 2021 -> 5 kelas, resample ke grid 30 m
       5) DEM Copernicus 30 m + kemiringan (slope) dari Planetary Computer
       6) peta kemurnian WorldCover (fraksi piksel 10 m sekelas modus
          di tiap sel 30 m); sampel latih hanya yang kemurniannya >= 8/9
       7) Random Forest (300 pohon) dilatih POOLED pada komposit 2025 DAN
          2026 (lokasi sampel sama, fitur kedua tahun), 14 fitur:
          6 band SR + NDVI/NDWI/NDBI/EVI/NDMI/BSI + elevasi + kemiringan
       8) prediksi kedua tahun dengan mask bersama (piksel yang valid di
          KEDUA tahun), akurasi (OA, Kappa, Producer/User), luas,
          matriks transisi
       9) ekspor GeoTIFF klasifikasi + perubahan dan statistik.json

Wilayah : Kabupaten Banjar, Kalimantan Selatan (EPSG:32650, 30 m)
Kelas   : 1 Hutan | 2 Pertanian & Perkebunan | 3 Permukiman / Lahan Terbangun
          4 Badan Air & Rawa | 5 Lahan Terbuka & Semak Belukar
Target  : OA >= 0,85 dan Kappa >= 0,80 (terhadap label WorldCover 2021)

HASIL YANG DICAPAI (dijalankan 2026-11-10): OA 2025 = 0,679, Kappa = 0,599;
OA 2026 = 0,689, Kappa = 0,611 — DI BAWAH target. Upaya perbaikan yang
sudah dicoba: tambah DEM/kemiringan + 5 indeks tambahan (v1 9 fitur
OA 0,62 -> v2 14 fitur OA 0,68), latih pooled dua tahun (memperbaiki
runtuhnya akurasi lintas-tahun v1), tambah sampel 1500 -> 2500/kelas,
kemurnian >= 8/9. ExtraTrees 300 pohon diuji dan LEBIH BURUK
(OA 0,662/0,669). Penyebab utama: label WorldCover 2021 sudah 4-5 tahun
tua (sawit tercatat sebagai "Tree cover", sawah kering sebagai semak),
tumpang tindih spektral antar 5 kelas yang luas, dan musim kemarau 2026
yang lebih kering (El Nino) mengubah rawa. Angka dilaporkan apa adanya;
akurasi ini terhadap referensi WorldCover 2021, BUKAN cek lapangan.

PENTING — kejujuran data: training/validasi berasal dari ESA WorldCover
2021 sebagai referensi, BUKAN cek lapangan. Sawit/karet di WorldCover
umumnya tercatat sebagai "Tree cover", sehingga kelas Hutan cenderung
terlalu luas dan Pertanian & Perkebunan terlalu sempit; sawah musim
kemarau sebagian tercatat sebagai semak/lahan terbuka. Perubahan
2021->2025/2026 menimbulkan bias pada label.
"""
import gc
import json
import os
import time
from collections import defaultdict

import numpy as np
import rasterio
from rasterio.features import rasterize
from rasterio.transform import Affine
from rasterio.windows import Window, from_bounds

# ============================== KONFIGURASI ==============================
KERJA = os.path.dirname(os.path.abspath(__file__))  # folder script ini
DATA = os.path.join(KERJA, "data")
OUT = os.path.join(KERJA, "output")
BBOX = [114.5066, -3.7307, 115.5958, -2.8282]  # lon/lat Kab. Banjar
TAHUN_A, TAHUN_B = 2025, 2026
BULAN = ("06-01", "09-30")                    # Juni-September
BANDS = ["blue", "green", "red", "nir08", "swir16", "swir22"]  # B2..B7
MAX_PER_TILE = 3        # scene T1 cloud terendah per tile (path/row)
N_PER_KELAS = 2500      # lokasi sampel per kelas (dilatih di kedua tahun)
N_POHON = 300
SEED = 42
PURITY_MIN = 226        # kemurnian >= 8/9 (disimpan 0-255)
LUAS_BPS_KM2 = 4668.50
KELAS = {1: "Hutan", 2: "Pertanian & Perkebunan",
         3: "Permukiman / Lahan Terbangun", 4: "Badan Air & Rawa",
         5: "Lahan Terbuka & Semak Belukar"}
# WorldCover 2021 -> 5 kelas
WC_MAP = {10: 1, 95: 1, 40: 2, 50: 3, 80: 4, 90: 4, 20: 5, 30: 5, 60: 5}
CRS = "EPSG:32650"
# =========================================================================


def log(msg):
    print(f"[{time.strftime('%H:%M:%S')}] {msg}", flush=True)


# ---------------------------------------------------------------- 1. BATAS
def unduh_batas():
    """Batas Kab. Banjar dari geoBoundaries ADM2; validasi luas vs BPS."""
    import geopandas as gpd
    import requests
    os.makedirs(DATA, exist_ok=True)
    path = os.path.join(DATA, "banjar_boundary.geojson")
    if not os.path.exists(path):
        url = ("https://github.com/wmgeolab/geoBoundaries/raw/9469f09/"
               "releaseData/gbOpen/IDN/ADM2/"
               "geoBoundaries-IDN-ADM2_simplified.geojson")
        log("Unduh batas administrasi Indonesia (geoBoundaries ADM2) ...")
        r = requests.get(url, timeout=300)
        r.raise_for_status()
        g = gpd.read_file(__import__("io").BytesIO(r.content))
        b = g[g["shapeName"] == "Banjar"].copy()  # hanya ada satu 'Banjar'
        b.to_file(path, driver="GeoJSON")
    b = gpd.read_file(path)
    luas = b.to_crs(CRS).geometry.area.iloc[0] / 1e6
    selisih = abs(luas - LUAS_BPS_KM2) / LUAS_BPS_KM2 * 100
    log(f"Luas batas Banjar: {luas:,.2f} km2 (BPS {LUAS_BPS_KM2:,.2f} km2, "
        f"selisih {selisih:.2f}%)")
    assert selisih <= 5, "Luas batas menyimpang >5% dari BPS — batas salah!"
    return path


def grid_target(boundary_path):
    """Grid UTM 30 m mencakup batas Banjar (snap kelipatan 30 m)."""
    import geopandas as gpd
    b = gpd.read_file(boundary_path).to_crs(CRS)
    minx, miny, maxx, maxy = b.total_bounds
    minx = np.floor(minx / 30) * 30
    miny = np.floor(miny / 30) * 30
    maxx = np.ceil(maxx / 30) * 30
    maxy = np.ceil(maxy / 30) * 30
    w, h = int((maxx - minx) / 30), int((maxy - miny) / 30)
    return w, h, Affine(30, 0, minx, 0, -30, maxy)


# ------------------------------------------------------- 2. CARI SCENE STAC
def cari_scene(tahun):
    """Cari Landsat C2 L2 Jun-Sep, cloud<20, di STAC Planetary Computer."""
    from pystac_client import Client
    cat = Client.open("https://planetarycomputer.microsoft.com/api/stac/v1")
    cari = cat.search(
        collections=["landsat-c2-l2"], bbox=BBOX,
        datetime=f"{tahun}-{BULAN[0]}/{tahun}-{BULAN[1]}",
        query={"eo:cloud_cover": {"lt": 20}})
    items = list(cari.items())
    log(f"{tahun}: {len(items)} scene Landsat cloud<20 ditemukan")
    return items


def pilih_scene(items):
    """Per tile (path/row) ambil maks 3 scene T1 cloud terendah."""
    by = defaultdict(list)
    for it in items:
        if "_T2" in it.id:
            continue
        by[it.id.split("_")[2]].append(it)
    dipilih = []
    for tile in sorted(by):
        v = sorted(by[tile], key=lambda x: x.properties["eo:cloud_cover"])
        dipilih.extend(v[:MAX_PER_TILE])
    return dipilih


# ------------------------------------------------------- 3. KOMPOSIT MEDIAN
def bangun_komposit(tahun, items, boundary_path):
    """Komposit median per piksel (mask awan QA_PIXEL), per blok baris."""
    import planetary_computer
    from pystac import Item
    out = os.path.join(DATA, f"komposit_{tahun}.tif")
    if os.path.exists(out):
        log(f"Komposit {tahun} sudah ada, lewati ({out})")
        return out
    scenes = []
    for it in pilih_scene(items):
        scenes.append(planetary_computer.sign(Item.from_dict(it.to_dict())))
    log(f"{tahun}: {len(scenes)} scene dipakai untuk komposit")
    w, h, transform = grid_target(boundary_path)
    log(f"Grid target: {w} x {h} piksel @ 30 m")
    prof = dict(driver="GTiff", width=w, height=h, count=len(BANDS),
                dtype="uint16", crs=CRS, transform=transform, nodata=0,
                compress="deflate", tiled=True, blockxsize=256, blockysize=256)
    blok = 256
    with rasterio.open(out, "w", **prof) as dst:
        for bi, band in enumerate(BANDS, start=1):
            log(f"[{tahun}] band {band} ({bi}/{len(BANDS)}) ...")
            pegangan = []
            for item in scenes:
                try:
                    pegangan.append((rasterio.open(item.assets[band].href),
                                     rasterio.open(item.assets["qa_pixel"].href)))
                except Exception as e:
                    log(f"  gagal buka {item.id} {band}: {e}")
            for r0 in range(0, h, blok):
                rh = min(blok, h - r0)
                x0, y_top = transform * (0, r0)
                x1, y_bot = transform * (w, r0 + rh)
                bb = (x0, y_bot, x1, y_top)
                tumpuk = []
                for ds_b, ds_q in pegangan:
                    try:
                        wb = from_bounds(*bb, ds_b.transform)
                        wq = from_bounds(*bb, ds_q.transform)
                        if wb.width <= 0 or wb.height <= 0:
                            continue
                        arr = ds_b.read(1, window=wb, out_shape=(rh, w),
                                        resampling=rasterio.enums.Resampling.nearest)
                        qa = ds_q.read(1, window=wq, out_shape=(rh, w),
                                       resampling=rasterio.enums.Resampling.nearest)
                    except Exception:
                        continue
                    # bit QA_PIXEL: 1 dilated cloud, 2 cirrus, 3 cloud,
                    # 4 cloud shadow; band==0 = fill/nodata
                    buruk = (arr == 0) | ((qa & 0b11110) != 0)
                    a = arr.astype(np.float32)
                    a[buruk] = np.nan
                    tumpuk.append(a)
                if tumpuk:
                    with np.errstate(all="ignore"):
                        med = np.nanmedian(np.stack(tumpuk), axis=0)
                    hasil = np.where(np.isnan(med), 0, med).astype(np.uint16)
                else:
                    hasil = np.zeros((rh, w), dtype=np.uint16)
                dst.write(hasil, bi, window=((r0, r0 + rh), (0, w)))
                del tumpuk, hasil
            for ds_b, ds_q in pegangan:
                ds_b.close()
                ds_q.close()
    log(f"Komposit {tahun} tersimpan: {out}")
    return out


# ------------------------------------------------- 4. WORLDCOVER -> 5 KELAS
def resample_worldcover(komposit_ref):
    """ESA WorldCover 2021 (10 m) -> grid 30 m, petakan ke 5 kelas."""
    from rasterio.warp import Resampling, reproject
    import planetary_computer
    from pystac_client import Client
    out = os.path.join(DATA, "worldcover_30m.tif")
    if os.path.exists(out):
        log(f"WorldCover 30 m sudah ada, lewati ({out})")
        return out
    cat = Client.open("https://planetarycomputer.microsoft.com/api/stac/v1")
    items = list(cat.search(collections=["esa-worldcover"], bbox=BBOX,
                            datetime="2021-01-01/2021-12-31").items())
    log(f"{len(items)} tile WorldCover 2021")
    srcs = [rasterio.open(planetary_computer.sign(it).assets["map"].href)
            for it in items]
    with rasterio.open(komposit_ref) as comp:
        prof = comp.profile.copy()
        prof.update(count=1, dtype="uint8", nodata=0)
        h, w, transform, crs = comp.height, comp.width, comp.transform, comp.crs
        with rasterio.open(out, "w", **prof) as dst:
            for r0 in range(0, h, 256):
                rh = min(256, h - r0)
                win = Window(0, r0, w, rh)
                gabung = np.zeros((rh, w), dtype=np.uint8)
                tr = rasterio.windows.transform(win, transform)
                for ds in srcs:
                    tmp = np.zeros((rh, w), dtype=np.uint8)
                    reproject(source=rasterio.band(ds, 1), destination=tmp,
                              src_transform=ds.transform, src_crs=ds.crs,
                              dst_transform=tr, dst_crs=crs,
                              resampling=Resampling.mode,
                              src_nodata=0, dst_nodata=0)
                    isi = (gabung == 0) & (tmp != 0)
                    gabung[isi] = tmp[isi]
                peta = np.zeros((rh, w), dtype=np.uint8)
                for wc, kl in WC_MAP.items():
                    peta[gabung == wc] = kl
                dst.write(peta, 1, window=win)
    for ds in srcs:
        ds.close()
    log(f"WorldCover 30 m tersimpan: {out}")
    return out


# --------------------------------------- 5. DEM + SLOPE, 6. KEMURNIAN WC
def dem_dan_kemiringan(komposit_ref):
    """Copernicus DEM 30 m (PC) -> grid 30 m; kemiringan dari gradien DEM.

    Nilai DEM negatif (artefak di atas air) dipangkas ke 0 pada saat
    dipakai sebagai fitur.
    """
    from rasterio.warp import Resampling, reproject
    import planetary_computer
    from pystac_client import Client
    out_dem = os.path.join(DATA, "dem_30m.tif")
    out_slope = os.path.join(DATA, "slope_30m.tif")
    if os.path.exists(out_dem) and os.path.exists(out_slope):
        log("DEM + slope sudah ada, lewati")
        return out_dem, out_slope
    cat = Client.open("https://planetarycomputer.microsoft.com/api/stac/v1")
    items = list(cat.search(collections=["cop-dem-glo-30"],
                            bbox=BBOX).items())
    log(f"{len(items)} tile Copernicus DEM")
    srcs = [rasterio.open(planetary_computer.sign(it).assets["data"].href)
            for it in items]
    with rasterio.open(komposit_ref) as comp:
        prof = comp.profile.copy()
        prof.update(count=1, dtype="float32", nodata=-9999)
        h, w, transform, crs = comp.height, comp.width, comp.transform, comp.crs
        with rasterio.open(out_dem, "w", **prof) as dst:
            for r0 in range(0, h, 256):
                rh = min(256, h - r0)
                win = Window(0, r0, w, rh)
                gab = np.full((rh, w), -9999, dtype=np.float32)
                tr = rasterio.windows.transform(win, transform)
                for ds in srcs:
                    tmp = np.full((rh, w), -9999, dtype=np.float32)
                    reproject(source=rasterio.band(ds, 1), destination=tmp,
                              src_transform=ds.transform, src_crs=ds.crs,
                              dst_transform=tr, dst_crs=crs,
                              resampling=Resampling.bilinear,
                              src_nodata=-9999, dst_nodata=-9999)
                    isi = (gab == -9999) & (tmp != -9999)
                    gab[isi] = tmp[isi]
                dst.write(gab, 1, window=win)
    for ds in srcs:
        ds.close()
    with rasterio.open(out_dem) as ds:
        dem_arr = ds.read(1)
        prof2 = ds.profile.copy()
    dem_arr = np.where(dem_arr == -9999, np.nan, dem_arr)
    gy, gx = np.gradient(dem_arr, 30, 30)
    slope = np.degrees(np.arctan(np.sqrt(gx ** 2 + gy ** 2)))
    slope = np.where(np.isnan(slope), 0, slope).astype(np.float32)
    with rasterio.open(out_slope, "w", **prof2) as dst:
        dst.write(slope, 1)
    log("DEM + slope tersimpan")
    return out_dem, out_slope


def peta_kemurnian(komposit_ref):
    """Kemurnian WorldCover: fraksi piksel 10 m yang sama dengan kelas
    modus di tiap sel 30 m (0-255; 255 = 9/9 piksel murni)."""
    from rasterio.transform import Affine as _Af
    from rasterio.warp import Resampling, reproject
    import planetary_computer
    from pystac_client import Client
    out = os.path.join(DATA, "wc_purity.tif")
    if os.path.exists(out):
        log("Peta kemurnian sudah ada, lewati")
        return out
    cat = Client.open("https://planetarycomputer.microsoft.com/api/stac/v1")
    items = list(cat.search(collections=["esa-worldcover"], bbox=BBOX,
                            datetime="2021-01-01/2021-12-31").items())
    srcs = [rasterio.open(planetary_computer.sign(it).assets["map"].href)
            for it in items]
    with rasterio.open(komposit_ref) as comp:
        prof = comp.profile.copy()
        prof.update(count=1, dtype="uint8", nodata=0)
        h, w, transform, crs = comp.height, comp.width, comp.transform, comp.crs
        with rasterio.open(out, "w", **prof) as dst:
            for r0 in range(0, h, 256):
                rh = min(256, h - r0)
                win = Window(0, r0, w, rh)
                t = rasterio.windows.transform(win, transform)
                gab = np.zeros((rh * 3, w * 3), dtype=np.uint8)
                t10 = _Af(t.a / 3, t.b, t.c, t.d, t.e / 3, t.f)
                for ds in srcs:
                    tmp = np.zeros((rh * 3, w * 3), dtype=np.uint8)
                    reproject(source=rasterio.band(ds, 1), destination=tmp,
                              src_transform=ds.transform, src_crs=ds.crs,
                              dst_transform=t10, dst_crs=crs,
                              dst_nodata=0, src_nodata=0,
                              resampling=Resampling.nearest)
                    isi = (gab == 0) & (tmp != 0)
                    gab[isi] = tmp[isi]
                # 9 sub-piksel 10 m tiap sel 30 m (transpose agar urutan
                # sumbu benar sebelum reshape)
                a = gab.reshape(rh, 3, w, 3).transpose(0, 2, 1, 3).reshape(rh, w, 9)
                srt = np.sort(a, axis=2)
                same = np.ones((rh, w, 9), dtype=bool)
                same[:, :, 1:] = srt[:, :, 1:] == srt[:, :, :-1]
                maxrun = np.ones((rh, w), dtype=np.uint8)
                cur = np.ones((rh, w), dtype=np.uint8)
                for j in range(1, 9):
                    cur = np.where(same[:, :, j], cur + 1, 1).astype(np.uint8)
                    maxrun = np.maximum(maxrun, cur)
                frac = (maxrun.astype(np.uint16) * 255 // 9).astype(np.uint8)
                dst.write(frac, 1, window=win)
    for ds in srcs:
        ds.close()
    log("Peta kemurnian tersimpan: data/wc_purity.tif")
    return out


# ------------------------------------------- 7-8. SAMPLING, RF, PERUBAHAN
def fitur(comp, dem_arr, slope_arr):
    """(6,h,w) uint16 SR + DEM/slope -> 14 fitur float32.

    6 band reflektansi (skala C2 L2: 0,0000275*DN - 0,2), lalu
    NDVI, NDWI, NDBI, EVI, NDMI, BSI, elevasi (m, negatif -> 0),
    kemiringan (derajat).
    """
    r = comp.astype(np.float32) * 0.0000275 - 0.2
    blue, green, red, nir, swir1, swir2 = r
    eps = 1e-6
    ndvi = (nir - red) / (nir + red + eps)
    ndwi = (green - nir) / (green + nir + eps)
    ndbi = (swir1 - nir) / (swir1 + nir + eps)
    evi = 2.5 * (nir - red) / (nir + 6 * red - 7.5 * blue + 1 + eps)
    ndmi = (nir - swir1) / (nir + swir1 + eps)
    bsi = ((swir1 + red) - (nir + blue)) / ((swir1 + red) + (nir + blue) + eps)
    elev = np.clip(dem_arr, 0, None).astype(np.float32)
    return np.stack([blue, green, red, nir, swir1, swir2,
                     ndvi, ndwi, ndbi, evi, ndmi, bsi, elev, slope_arr])


def fitur_titik(comp, dem_arr, slope_arr, yy, xx):
    """14 fitur HANYA di titik sampel (yy, xx) — hemat memori.

    Aritmetika sama persis dengan fitur() di atas, tapi dihitung pada
    (6, N) nilai piksel sampel saja, bukan pada grid penuh (grid penuh
    14 band float32 butuh ~750 MB). Dipakai untuk training/validasi.
    """
    r = comp[:, yy, xx].astype(np.float32) * 0.0000275 - 0.2
    blue, green, red, nir, swir1, swir2 = r
    eps = 1e-6
    ndvi = (nir - red) / (nir + red + eps)
    ndwi = (green - nir) / (green + nir + eps)
    ndbi = (swir1 - nir) / (swir1 + nir + eps)
    evi = 2.5 * (nir - red) / (nir + 6 * red - 7.5 * blue + 1 + eps)
    ndmi = (nir - swir1) / (nir + swir1 + eps)
    bsi = ((swir1 + red) - (nir + blue)) / ((swir1 + red) + (nir + blue) + eps)
    elev = np.clip(dem_arr[yy, xx], 0, None).astype(np.float32)
    return np.stack([blue, green, red, nir, swir1, swir2,
                     ndvi, ndwi, ndbi, evi, ndmi, bsi,
                     elev, slope_arr[yy, xx]], axis=1).astype(np.float32)


def klasifikasi(boundary_path):
    """Latih RF pooled (2025+2026), prediksi kedua tahun, akurasi, luas,
    matriks transisi."""
    from sklearn.ensemble import RandomForestClassifier
    from sklearn.metrics import (accuracy_score, cohen_kappa_score,
                                 confusion_matrix)
    from sklearn.model_selection import train_test_split
    os.makedirs(OUT, exist_ok=True)
    with rasterio.open(os.path.join(DATA, "komposit_2025.tif")) as ds:
        prof = ds.profile.copy()
        c25 = ds.read()
    with rasterio.open(os.path.join(DATA, "komposit_2026.tif")) as ds:
        c26 = ds.read()
    with rasterio.open(os.path.join(DATA, "worldcover_30m.tif")) as ds:
        wc = ds.read(1)
    with rasterio.open(os.path.join(DATA, "wc_purity.tif")) as ds:
        purity = ds.read(1)
    with rasterio.open(os.path.join(DATA, "dem_30m.tif")) as ds:
        dem = ds.read(1)
    with rasterio.open(os.path.join(DATA, "slope_30m.tif")) as ds:
        slope = ds.read(1)
    h, w = wc.shape
    with rasterio.open(os.path.join(DATA, "komposit_2025.tif")) as ds:
        import geopandas as gpd
        shapes = [(g, 1) for g in
                  gpd.read_file(boundary_path).to_crs(ds.crs).geometry]
        mask = rasterize(shapes, out_shape=(h, w), transform=ds.transform,
                         fill=0, dtype=np.uint8)
    valid = (mask == 1) & (wc > 0) & (purity >= PURITY_MIN) \
        & (c25[0] > 0) & (c26[0] > 0)
    log(f"Piksel valid bersama (murni >=8/9): {valid.sum():,} dari {h*w:,}")
    rng = np.random.default_rng(SEED)
    ys, xs = [], []
    for k in sorted(KELAS):
        yy, xx = np.where(valid & (wc == k))
        log(f"  kandidat kelas {k} {KELAS[k]}: {len(yy):,}")
        idx = rng.choice(len(yy), size=min(N_PER_KELAS, len(yy)),
                         replace=False)
        ys.append(yy[idx]); xs.append(xx[idx])
    ys = np.concatenate(ys); xs = np.concatenate(xs)
    y = wc[ys, xs]
    log(f"Total lokasi sampel: {len(y)}")
    i_tr, i_va = train_test_split(np.arange(len(y)), test_size=0.30,
                                  random_state=SEED, stratify=y)
    y_tr, y_va = y[i_tr], y[i_va]

    def fitur_sampel(comp, yy, xx):
        return fitur_titik(comp, dem, slope, yy, xx)
    # pooled: lokasi sampel yang sama dipakai dengan fitur 2025 DAN 2026
    X_tr = np.vstack([fitur_sampel(c25, ys[i_tr], xs[i_tr]),
                      fitur_sampel(c26, ys[i_tr], xs[i_tr])])
    y_tr2 = np.concatenate([y_tr, y_tr])
    X_va25 = fitur_sampel(c25, ys[i_va], xs[i_va])
    X_va26 = fitur_sampel(c26, ys[i_va], xs[i_va])
    del c25, c26
    gc.collect()
    log(f"Baris latih pooled: {len(X_tr)} (14 fitur)")
    log("Latih Random Forest (300 pohon) ...")
    clf = RandomForestClassifier(n_estimators=N_POHON, n_jobs=-1,
                                 random_state=SEED)
    clf.fit(X_tr, y_tr2)
    log(f"Kepentingan fitur: {np.round(clf.feature_importances_, 3)}")

    def laporan(y_true, y_pred, nama):
        oa = accuracy_score(y_true, y_pred)
        kap = cohen_kappa_score(y_true, y_pred)
        cm = confusion_matrix(y_true, y_pred, labels=[1, 2, 3, 4, 5])
        log(f"Akurasi {nama}: OA={oa:.4f}  Kappa={kap:.4f}")
        prod, user = [], []
        for i in range(5):
            prod.append(float(cm[i, i] / cm[i, :].sum()) if cm[i, :].sum() else 0)
            user.append(float(cm[i, i] / cm[:, i].sum()) if cm[:, i].sum() else 0)
            log(f"  kelas {i+1} {KELAS[i+1]}: "
                f"Producer {prod[-1]:.3f}  User {user[-1]:.3f}")
        return {"OA": float(oa), "Kappa": float(kap),
                "confusion_matrix": cm.tolist(),
                "producers": prod, "users": user}
    stat = {"akurasi_2025": laporan(y_va, clf.predict(X_va25),
                                    "validasi 2025 (model pooled)"),
            "akurasi_2026": laporan(y_va, clf.predict(X_va26),
                                    "validasi 2026 (model pooled)")}
    del X_tr, X_va25, X_va26
    gc.collect()

    # prediksi dengan mask bersama (valid di KEDUA tahun) — blok kecil
    # dan prediksi per potongan agar hemat memori
    common = (mask == 1)
    with rasterio.open(os.path.join(DATA, "komposit_2025.tif")) as ds:
        common &= (ds.read(1) > 0)
    with rasterio.open(os.path.join(DATA, "komposit_2026.tif")) as ds:
        common &= (ds.read(1) > 0)
    log(f"Piksel terklasifikasi (mask bersama): {common.sum():,}")
    prof.update(count=1, dtype="uint8", nodata=0)
    for tahun in (TAHUN_A, TAHUN_B):
        out = os.path.join(OUT, f"klasifikasi_{tahun}.tif")
        log(f"Prediksi {tahun} ...")
        with rasterio.open(os.path.join(DATA, f"komposit_{tahun}.tif")) as ds, \
             rasterio.open(out, "w", **prof) as dst:
            for r0 in range(0, h, 256):
                rh = min(256, h - r0)
                comp = ds.read(window=Window(0, r0, w, rh))
                f = fitur(comp, dem[r0:r0 + rh], slope[r0:r0 + rh])
                del comp
                X = np.moveaxis(f, 0, -1).reshape(-1, f.shape[0])
                del f
                gc.collect()
                mflat = common[r0:r0 + rh].reshape(-1)
                pred = np.zeros(rh * w, dtype=np.uint8)
                idx = np.where(mflat)[0]
                for s in range(0, len(idx), 100000):
                    chunk = idx[s:s + 100000]
                    pred[chunk] = clf.predict(X[chunk])
                    del chunk
                del X, idx
                gc.collect()
                dst.write(pred.reshape(rh, w), 1, window=Window(0, r0, w, rh))
        log(f"  tersimpan {out}")

    with rasterio.open(os.path.join(OUT, "klasifikasi_2025.tif")) as ds:
        k25 = ds.read(1)
    with rasterio.open(os.path.join(OUT, "klasifikasi_2026.tif")) as ds:
        k26 = ds.read(1)
    kode = np.where((k25 > 0) & (k26 > 0), k25 * 10 + k26, 0).astype(np.uint8)
    with rasterio.open(os.path.join(OUT, "perubahan_2025_2026.tif"),
                       "w", **prof) as dst:
        dst.write(kode, 1)
    px_ha = 30 * 30 / 1e4
    luas = {}
    for tahun, k in ((TAHUN_A, k25), (TAHUN_B, k26)):
        luas[str(tahun)] = {KELAS[c]: float((k == c).sum() * px_ha)
                            for c in KELAS}
        luas[str(tahun)]["TOTAL"] = float((k > 0).sum() * px_ha)
    trans = {(a, b): float(((k25 == a) & (k26 == b)).sum() * px_ha)
             for a in KELAS for b in KELAS}
    stat["luas_ha"] = luas
    stat["matriks_transisi_ha"] = {f"{a}->{b}": v
                                   for (a, b), v in trans.items()}
    top = sorted(((v, a, b) for (a, b), v in trans.items() if a != b),
                 reverse=True)[:3]
    stat["transisi_terbesar_ha"] = [
        {"dari": KELAS[a], "ke": KELAS[b], "ha": float(v)} for v, a, b in top]
    log("Luas (ha):")
    for t in ("2025", "2026"):
        log(f"  {t}: " + ", ".join(f"{k}={v:,.0f}"
                                  for k, v in luas[t].items()))
    log("3 transisi perubahan terbesar:")
    for v, a, b in top:
        log(f"  {KELAS[a]} -> {KELAS[b]}: {v:,.1f} ha")
    with open(os.path.join(OUT, "statistik.json"), "w") as f:
        json.dump(stat, f, indent=2, ensure_ascii=False)
    log("Statistik tersimpan: output/statistik.json")
    return stat


def main():
    t0 = time.time()
    os.makedirs(DATA, exist_ok=True)
    os.makedirs(OUT, exist_ok=True)
    batas = unduh_batas()
    for tahun in (TAHUN_A, TAHUN_B):
        items = cari_scene(tahun)
        bangun_komposit(tahun, items, batas)
    ref = os.path.join(DATA, "komposit_2025.tif")
    resample_worldcover(ref)
    dem_dan_kemiringan(ref)
    peta_kemurnian(ref)
    klasifikasi(batas)
    log(f"SELESAI total {time.time()-t0:.0f} detik. "
        f"Hasil di folder: {OUT}")


if __name__ == "__main__":
    main()
