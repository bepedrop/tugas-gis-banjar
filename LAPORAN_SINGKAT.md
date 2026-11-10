# Laporan Singkat: Perubahan Tutupan Lahan Kabupaten Banjar 2025 vs 2026

**Mata kuliah:** Sistem Informasi Geografi (SIG) — **Dosen:** Dr. Ir. Mufidah Asy'ari, M.P.
**Wilayah:** Kabupaten Banjar, Kalimantan Selatan (4.668,50 km², BPS)
**Citra:** Landsat 8/9 Collection 2 L2, komposit median Jun–Sep 2025 vs 2026
**Metode:** Random Forest (300 pohon, 14 fitur: band B2–B7 + NDVI/NDWI/NDBI/EVI/NDMI/BSI + elevasi + kemiringan), latih pooled dua tahun, label referensi ESA WorldCover 2021

## Hasil utama

Luas yang terklasifikasi 430.839,8 ha (91,2% wilayah; 8,8% tidak terklasifikasi karena celah awan). Sebesar **362.350,8 ha (84,1%) tidak berubah**, dan **68.489,0 ha (15,9%) berubah kelas** antara 2025 dan 2026.

| Kelas | 2025 (ha) | 2026 (ha) | Perubahan |
|---|---|---|---|
| Hutan | 261.756,4 | 254.677,9 | **−7.078,5 ha (−2,70%)** |
| Pertanian & Perkebunan | 40.028,8 | 45.037,1 | **+5.008,3 ha (+12,51%)** |
| Permukiman / Lahan Terbangun | 35.134,5 | 43.998,5 | **+8.864,0 ha (+25,23%)** |
| Badan Air & Rawa | 27.846,1 | 22.200,3 | **−5.645,8 ha (−20,27%)** |
| Lahan Terbuka & Semak Belukar | 66.074,1 | 64.926,1 | −1.148,0 ha (−1,74%) |

Tiga transisi perubahan terbesar: **Hutan → Lahan Terbuka & Semak Belukar 11.296,8 ha**; **Lahan Terbuka & Semak Belukar → Permukiman 8.940,3 ha**; **Hutan → Permukiman 6.545,0 ha**.

## Interpretasi

**Hutan berkurang 7.079 ha.** Transisi terbesarnya bukan langsung ke permukiman atau pertanian, melainkan ke Lahan Terbuka & Semak Belukar (11.297 ha) — pola yang khas untuk pembukaan lahan tahap awal: tegakan dibuka, menjadi semak/belukar, baru kemudian berubah fungsi. Di Banjar, pola ini sesuai dengan tekanan di kaki Pegunungan Meratus (kecamatan Aranio, Karang Intan, Paramasan, Telaga Bauntung) — pembukaan kebun sawit/karet rakyat, penambangan rakyat, dan perladangan — serta di sekitar Riam Kanan, tempat tekanan wisata dan permukiman di tepi waduk terus bertambah. Perlu dicatat, sebagian Hutan yang "hilang" ini sebenarnya sawit/karet yang di WorldCover tercatat sebagai Tree cover: saat kanopi sawit muda masih terbuka, model membacanya sebagai semak/lahan terbuka.

**Pertanian & Perkebunan bertambah 5.008 ha (+12,5%).** Kenaikan ini sejalan dengan tren jangka panjang Banjar (studi gambut 1990–2020: sawit +1.073 ha/tahun, pertanian +1.508 ha/tahun) — perluasan kebun sawit di dataran rendah timur dan tengah, serta sawah di dataran aluvial Martapura–Sungai Tabuk. Sebagian kenaikan juga berasal dari rawa yang mengering dan terklasifikasi sebagai pertanian (5.651 ha Badan Air & Rawa → Pertanian), jadi angka ini bukan murni perluasan kebun.

**Permukiman bertambah 8.864 ha (+25,2%) — angka ini paling tidak dapat dipercaya secara harfiah.** Pertumbuhan nyata memang ada: Martapura sebagai ibu kota kabupaten terus meluas ke Gambut, Sungai Tabuk, dan Astambul, ditambah permukiman di koridor Banjarbaru–Martapura. Namun kenaikan 25% dalam satu tahun tidak mungkin seluruhnya nyata; sebagian besar adalah artefak klasifikasi — lahan terbuka yang kering pada 2026 (musim kemarau lebih kering) terbaca sebagai lahan terbangun, dan 8.940 ha "Terbuka/Semak → Permukiman" adalah transisi yang paling dicurigai sebagai noise. Demikian pula aliran balik Permukiman → Hutan seluas 4.573 ha jelas bukan penghijauan permukiman, melainkan kesalahan klasifikasi.

**Badan Air & Rawa berkurang 5.646 ha (−20,3%).** Ini sebagian nyata, sebagian artefak. Tahun 2026 adalah tahun El Niño sedang–kuat dengan musim kemarau yang lebih kering: rawa-rawa di dataran rendah barat dan selatan (Gambut, Aluh-Aluh, Beruntung Baru, Sungai Tabuk) menyusut dan mengering — terdeteksi dari naiknya NDBI dan SWIR1 pada kelas ini. Sebagian rawa yang mengering itu kemudian terklasifikasi sebagai Pertanian (5.651 ha) atau Terbuka/Semak (5.255 ha). Jadi penyusutan rawa itu nyata secara hidrologis, tetapi besarnya dibesar-besarkan oleh klasifikasi.

## Catatan akurasi — yang paling penting

**Akurasi model: OA 2025 = 0,679, Kappa = 0,599; OA 2026 = 0,689, Kappa = 0,611 — di bawah target tugas OA ≥ 0,85 dan Kappa ≥ 0,80.** Angka perubahan di atas karena itu harus dibaca sebagai **indikasi arah, bukan pengukuran pasti**. Kebingungan terbesar ada pada pasangan Terbuka/Semak ↔ Hutan (Producer's accuracy Terbuka/Semak hanya 0,55) dan Air/Rawa ↔ Pertanian. Penyebabnya: (1) label referensi WorldCover 2021 sudah 4–5 tahun tua; (2) tidak ada cek lapangan; (3) lima kelas yang sangat luas secara spektral tumpang tindih; (4) musim kemarau 2026 yang lebih kering mengubah tampilan spektral rawa dan sawah.

Sudah dicoba untuk menaikkan akurasi: tambah DEM/kemiringan dan 5 indeks (OA naik dari 0,62 ke 0,68), latih pooled dua tahun (memperbaiki runtuhnya akurasi lintas-tahun), tambah sampel, dan uji ExtraTrees (lebih buruk). Kenaikan lebih lanjut membutuhkan survei lapangan (ground truth) dan/atau data tambahan (mis. Sentinel-2 10 m, citra musim hujan sebagai pembanding, atau data tutupan sawit). **Untuk keperluan tugas SIG ini, laporan menyajikan hasil apa adanya dengan keterbatasannya, bukan angka yang dipercantik.**

## Kesimpulan

Arah perubahan 2025→2026 di Kabupaten Banjar: hutan menyusut dan berubah menjadi lahan terbuka/semak; pertanian dan permukiman meluas, terutama di sekitar Martapura dan dataran rendah; rawa menyusut seiring musim kemarau 2026 yang lebih kering. Namun besaran perubahan — terutama lonjakan permukiman +25% — sebagian besar mencerminkan keterbatasan klasifikasi (OA ~0,68) dan harus diverifikasi lapangan sebelum dipakai sebagai dasar kebijakan.
