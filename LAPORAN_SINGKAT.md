# Laporan Singkat: Perubahan Tutupan Lahan Kabupaten Banjar 2025 vs 2026

**Mata kuliah:** Sistem Informasi Geografi (SIG)
**Wilayah:** Kabupaten Banjar, Kalimantan Selatan (4.668,50 km², BPS)
**Citra:** Landsat 8/9 Collection 2 L2, komposit median Jun–Sep 2025 vs 2026
**Metode:** Random Forest (300 pohon, 14 fitur: band B2–B7 + NDVI/NDWI/NDBI/EVI/NDMI/BSI + elevasi + kemiringan), latih pooled dua tahun, label referensi ESA WorldCover 2021
**Versi utama:** Google Earth Engine (GEE), dijalankan di Colab 11 Nov 2026 (run final, setelah perbaikan bug). Versi Microsoft Planetary Computer (PC) dipakai sebagai cadangan/validasi silang.

## Hasil utama (versi GEE)

Luas yang terklasifikasi 466.551,0 ha (2025) dan 466.581,1 ha (2026) — selisih total hanya 30,1 ha (0,006%), setelah perbaikan mask bersama. Sebesar **403.699,0 ha (86,5%) tidak berubah**, dan **62.852,0 ha (13,5%) berubah kelas** antara 2025 dan 2026.

| Kelas | 2025 (ha) | 2026 (ha) | Perubahan |
|---|---|---|---|
| Hutan | 322.618,6 | 302.227,7 | **−20.390,9 ha (−6,32%)** |
| Pertanian & Perkebunan | 62.541,4 | 69.370,1 | **+6.828,7 ha (+10,92%)** |
| Permukiman / Lahan Terbangun | 5.554,2 | 8.453,5 | **+2.899,3 ha (+52,20%)** |
| Badan Air & Rawa | 19.218,1 | 22.676,0 | **+3.457,9 ha (+17,99%)** |
| Lahan Terbuka & Semak Belukar | 56.618,7 | 63.853,9 | **+7.235,2 ha (+12,78%)** |

Tiga transisi perubahan terbesar: **Hutan → Lahan Terbuka & Semak Belukar 19.541,4 ha**; **Lahan Terbuka & Semak Belukar → Pertanian & Perkebunan 10.232,3 ha**; **Lahan Terbuka & Semak Belukar → Badan Air & Rawa 5.603,7 ha**.

## Interpretasi

**Hutan berkurang 20.391 ha.** Transisi terbesarnya bukan langsung ke permukiman atau pertanian, melainkan ke Lahan Terbuka & Semak Belukar (19.541 ha) — pola yang khas untuk pembukaan lahan tahap awal: tegakan dibuka, menjadi semak/belukar, baru kemudian berubah fungsi. Di Banjar, pola ini sesuai dengan tekanan di kaki Pegunungan Meratus (kecamatan Aranio, Karang Intan, Paramasan, Telaga Bauntung) — pembukaan kebun sawit/karet rakyat, penambangan rakyat, dan perladangan — serta di sekitar Riam Kanan, tempat tekanan wisata dan permukiman di tepi waduk terus bertambah. Perlu dicatat, sebagian Hutan yang "hilang" ini sebenarnya sawit/karet yang di WorldCover tercatat sebagai Tree cover: saat kanopi sawit muda masih terbuka, model membacanya sebagai semak/lahan terbuka.

**Pertanian & Perkebunan bertambah 6.829 ha (+10,9%).** Kenaikan ini sejalan dengan tren jangka panjang Banjar (studi gambut 1990–2020: sawit +1.073 ha/tahun, pertanian +1.508 ha/tahun) — perluasan kebun sawit di dataran rendah timur dan tengah, serta sawah di dataran aluvial Martapura–Sungai Tabuk. Sebagian kenaikan juga berasal dari lahan terbuka yang berubah menjadi pertanian (10.232 ha), jadi angka ini bukan murni perluasan kebun baru.

**Permukiman bertambah 2.899 ha (+52,2%) — angka ini paling tidak dapat dipercaya secara harfiah.** Pertumbuhan nyata memang ada: Martapura sebagai ibu kota kabupaten terus meluas ke Gambut, Sungai Tabuk, dan Astambul, ditambah permukiman di koridor Banjarbaru–Martapura. Namun kenaikan 52% dalam satu tahun tidak mungkin seluruhnya nyata; sebagian besar adalah artefak klasifikasi — lahan terbuka yang kering pada 2026 (musim kemarau lebih kering) terbaca sebagai lahan terbangun. Demikian pula aliran balik Permukiman → Hutan seluas 83 ha dan Terbuka/Semak → Permukiman yang kecil menunjukkan model masih sering tertukar pada kelas ini (Producer's accuracy Permukiman memang tinggi, tetapi User's accuracy Pertanian hanya 0,73).

**Badan Air & Rawa bertambah 3.458 ha (+18,0%) — berbeda arah dengan versi PC yang mencatat penyusutan 20%.** Perbedaan ini menunjukkan kelas rawa adalah yang paling tidak stabil: Producer's accuracy-nya paling rendah (0,59–0,65). Pada versi GEE, 5.604 ha Lahan Terbuka & Semak terklasifikasi menjadi Badan Air & Rawa pada 2026, dan 5.413 ha Pertanian menjadi Badan Air & Rawa — kemungkinan rawa yang tergenang pada 2026 atau sawah yang berair terbaca sebagai rawa. Angka ini karena itu harus dibaca dengan sangat hati-hati.

**Lahan Terbuka & Semak Belukar bertambah 7.235 ha (+12,8%).** Kenaikan ini sebagian nyata (bekas pembukaan hutan), sebagian artefak (sawah bera dan kebun muda yang kanopinya masih terbuka).

## Catatan akurasi — yang paling penting

**Akurasi model GEE: OA 2025 = 0,818, Kappa = 0,764; OA 2026 = 0,818, Kappa = 0,764 — di bawah target tugas OA ≥ 0,85 dan Kappa ≥ 0,80.** Angka perubahan di atas karena itu harus dibaca sebagai **indikasi arah, bukan pengukuran pasti**. Kebingungan terbesar ada pada pasangan Badan Air & Rawa ↔ Pertanian (Producer's accuracy Air/Rawa hanya 0,59–0,65) dan Terbuka/Semak ↔ Hutan (Producer's accuracy Terbuka/Semak hanya 0,62–0,66). Penyebabnya: (1) label referensi WorldCover 2021 sudah 4–5 tahun tua; (2) tidak ada cek lapangan; (3) lima kelas yang sangat luas secara spektral tumpang tindih; (4) musim kemarau 2026 yang lebih kering mengubah tampilan spektral rawa dan sawah.

Dua bug yang ditemukan selama pengerjaan versi GEE sudah diperbaiki dan diuji ulang pada run final 11 Nov 2026: (1) validasi 2026 yang diam-diam mengukur fitur 2025 kembali (akurasi 2026 tercetak identik persis dengan 2025) — diperbaiki dengan men-strip properti band lama sebelum sampling 2026, sehingga OA/Kappa 2026 kini independen (0,8175 / 0,7639 vs 0,8184 / 0,7635); (2) selisih total luas 4.964 ha antar tahun — diperbaiki dengan mask bersama (piksel harus valid di kedua tahun), sehingga selisihnya tinggal 30,1 ha (0,006%).

Sudah dicoba untuk menaikkan akurasi: tambah DEM/kemiringan dan 5 indeks (OA naik dari 0,62 ke 0,68 pada versi PC), latih pooled dua tahun (memperbaiki runtuhnya akurasi lintas-tahun), tambah sampel, dan uji ExtraTrees (lebih buruk). Kenaikan lebih lanjut membutuhkan survei lapangan (ground truth) dan/atau data tambahan (mis. Sentinel-2 10 m, citra musim hujan sebagai pembanding, atau data tutupan sawit). **Untuk keperluan tugas SIG ini, laporan menyajikan hasil apa adanya dengan keterbatasannya, bukan angka yang dipercantik.**

## Perbandingan dengan versi PC (cadangan)

| Besaran | GEE (utama) | PC (cadangan) |
|---|---|---|
| OA 2025 / Kappa 2025 | 0,818 / 0,764 | 0,679 / 0,599 |
| OA 2026 / Kappa 2026 | 0,818 / 0,764 | 0,689 / 0,611 |
| Hutan 2025 → 2026 (ha) | 322.619 → 302.228 | 261.756 → 254.678 |
| Permukiman 2025 → 2026 (ha) | 5.554 → 8.454 | 35.135 → 43.999 |
| Luas terklasifikasi (ha) | 466.551 / 466.581 | 430.840 / 430.840 |
| Transisi terbesar | Hutan → Terbuka 19.541 ha | Hutan → Terbuka 11.297 ha |

Kedua versi searah (hutan berkurang, lahan terbuka bertambah, transisi terbesar sama), tetapi besaran luas berbeda karena GEE mengklasifikasi hampir seluruh wilayah sedangkan PC mengeluarkan piksel termasking awan. Versi GEE dipakai sebagai hasil utama karena akurasinya lebih tinggi dan cakupannya lebih lengkap.

## Kesimpulan

Arah perubahan 2025→2026 di Kabupaten Banjar: hutan menyusut dan berubah menjadi lahan terbuka/semak; pertanian dan permukiman meluas, terutama di sekitar Martapura dan dataran rendah; rawa menunjukkan perubahan yang tidak stabil antar versi dan perlu verifikasi lapangan. Namun besaran perubahan — terutama lonjakan permukiman +52% dan rawa +18% — sebagian mencerminkan keterbatasan klasifikasi (OA ~0,82) dan harus diverifikasi lapangan sebelum dipakai sebagai dasar kebijakan.
