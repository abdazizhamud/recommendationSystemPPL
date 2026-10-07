"""
Bangun katalog benih (products.csv) dari:
  - parameter lingkungan  : FAO EcoCrop (data/EcoCrop_DB.csv), atau estimasi manual bila tidak ada
  - data toko (harga, kemasan, brand, stok, benih per m2, umur panen) : SINTETIS -> ganti dengan data asli nanti

Satu komoditas = 3 brand x 2 ukuran kemasan. Parameter tumbuh sama untuk semua brand
(karena variannya belum ada), yang berbeda hanya brand, harga, dan ukuran kemasan.
Kolom `variety` sengaja dikosongkan; isi saat varietas asli tersedia.

Catatan penting:
  * EcoCrop menyimpan curah hujan PER TAHUN -> dibagi 12 jadi mm/bulan.
  * EcoCrop tidak punya batas bawah ketinggian -> `alt_min` diisi manual (default 0).
  * Umur panen (days_min/max) diisi manual per komoditas, bukan dari GMIN/GMAX EcoCrop (terlalu lebar).

Jalankan: python build_products.py
"""
import csv
import math
import random

import pandas as pd

rng = random.Random(7)
ECOCROP_PATH = "data/EcoCrop_DB.csv"

L, LP, LL, P = "lempung", "lempung berpasir", "liat berlempung", "berpasir"
ALL4 = "lahan|polybag|pot|hidroponik"

# ---------------------------------------------------------------------------
# Komoditas yang dijual (tanpa pohon & kopi).
# key, nama ilmiah EcoCrop, nama Indonesia, kategori, tujuan, tipe tanam,
# hari_min, hari_max, benih_per_m2, benih_per_gram, harga_per_gram, ukuran_kemasan_g,
# kesulitan(1-3), jam_matahari, alt_min, hama_umum, [override: topmn/topmx/altmx atau manual=(...)]
# ---------------------------------------------------------------------------
C = []


def add(*a, **ov):
    C.append((a, ov))


# --- sayuran buah ---
add("cabai_rawit", "Capsicum frutescens", "Cabai Rawit", "sayuran buah", "konsumsi|jual", "lahan|polybag|pot", 90, 110, 4, 150, 9000, [2, 5, 10], 2, 6, 0, "layu fusarium|antraknosa")
add("cabai_merah", "Capsicum annuum", "Cabai Merah Keriting", "sayuran buah", "jual|konsumsi", "lahan|polybag", 100, 125, 3.5, 150, 12000, [5, 10], 2, 6, 0, "virus kuning|antraknosa")
add("cabai_habanero", "Capsicum chinense", "Cabai Habanero", "sayuran buah", "konsumsi|hias", "lahan|polybag|pot", 100, 130, 2, 200, 25000, [1, 2, 5], 3, 6, 0, "kutu kebul|antraknosa")
add("tomat", "Lycopersicon esculentum", "Tomat", "sayuran buah", "konsumsi|jual", ALL4, 80, 100, 3.5, 300, 6000, [2, 5, 10], 2, 6, 200, "layu bakteri|virus gemini")
add("terong", "Solanum melongena", "Terong", "sayuran buah", "konsumsi|jual", "lahan|polybag", 80, 100, 2.5, 250, 3500, [5, 10, 25], 1, 6, 0, "ulat buah|layu bakteri", altmx=1200)
add("timun", "Cucumis sativus", "Timun", "sayuran buah", "konsumsi|jual", "lahan|polybag|vertikultur", 40, 55, 5, 35, 800, [10, 25, 50], 1, 6, 0, "embun tepung|downy mildew")
add("paria", "Momordica charantia", "Paria (Pare)", "sayuran buah", "konsumsi|jual", "lahan|polybag|vertikultur", 55, 70, 2, 15, 2500, [10, 25], 2, 6, 0, "lalat buah|embun tepung")
add("kacang_panjang", "Vigna unguiculata ssp. sesquipedalis", "Kacang Panjang", "sayuran buah", "konsumsi|jual", "lahan|polybag|vertikultur", 45, 60, 8, 7, 450, [25, 50, 100], 1, 6, 0, "lalat bibit|karat daun")
add("buncis", "Phaseolus vulgaris", "Buncis", "sayuran buah", "konsumsi|jual", "lahan|polybag", 45, 60, 10, 3.5, 400, [25, 50, 100], 1, 6, 200, "karat daun|antraknosa")
add("jagung_manis", "Zea mays ssp. saccharata", "Jagung Manis", "sayuran buah", "konsumsi|jual", "lahan|polybag", 65, 80, 6, 4, 500, [50, 100, 250], 1, 8, 0, "bulai|ulat grayak", topmn=20, topmx=30)
add("okra", "Abelmoschus esculentus", "Okra", "sayuran buah", "konsumsi|jual", "lahan|polybag|pot", 50, 65, 4, 15, 1500, [10, 25], 1, 7, 0, "kutu daun|embun tepung")
add("labu_kuning", "Cucurbita moschata", "Labu Kuning", "sayuran buah", "konsumsi|jual", "lahan|vertikultur", 90, 110, 0.5, 5, 700, [10, 25], 1, 7, 0, "embun tepung|lalat buah")
add("zukini", "Cucurbita pepo", "Zukini", "sayuran buah", "konsumsi|jual", "lahan|polybag", 50, 60, 1.5, 6, 3000, [5, 10], 2, 6, 0, "embun tepung|virus mosaik", altmx=1500)
add("melon", "Cucumis melo", "Melon", "sayuran buah", "jual|konsumsi", "lahan|polybag", 60, 75, 2, 30, 6000, [5, 10], 3, 8, 0, "layu fusarium|embun tepung")
add("semangka", "Citrullus lanatus", "Semangka", "sayuran buah", "jual|konsumsi", "lahan", 65, 80, 1, 15, 4000, [5, 10], 3, 8, 0, "layu fusarium|lalat buah")
add("oyong", "Luffa acutangula", "Oyong (Gambas)", "sayuran buah", "konsumsi|jual", "lahan|vertikultur", 60, 75, 1.5, 10, 1500, [10, 25], 1, 6, 0, "embun tepung|lalat buah")
add("labu_air", "Lagenaria siceraria", "Labu Air (Labu Botol)", "sayuran buah", "konsumsi", "lahan|vertikultur", 70, 90, 1.5, 6, 900, [10, 25], 1, 6, 0, "embun tepung|kutu daun")
add("kundur", "Benincasa hispida", "Kundur (Beligo)", "sayuran buah", "konsumsi|jual", "lahan|vertikultur", 100, 120, 0.5, 12, 1500, [10, 25], 2, 7, 0, "lalat buah|layu fusarium")
add("ceplukan", "Physalis peruviana", "Ceplukan (Physalis)", "buah", "konsumsi|jual", "lahan|polybag|pot", 90, 120, 2, 1000, 8000, [1, 2], 2, 7, 300, "kutu daun|busuk akar")
add("pepaya", "Carica papaya", "Pepaya California", "buah", "konsumsi|jual", "lahan|polybag", 210, 270, 0.2, 50, 15000, [1, 2, 5], 2, 8, 0, "virus kuning|busuk akar")
# --- sayuran daun ---
add("kangkung", "Ipomoea aquatica", "Kangkung", "sayuran daun", "konsumsi|jual", ALL4, 25, 35, 150, 30, 150, [50, 100, 250], 1, 5, 0, "ulat daun|karat putih")
add("bayam", "Amaranthus tricolor", "Bayam", "sayuran daun", "konsumsi|jual", ALL4, 25, 35, 200, 100, 120, [25, 50, 100], 1, 5, 0, "karat putih|ulat daun")
add("bayam_malabar", "Basella alba", "Bayam Malabar (Gondola)", "sayuran daun", "konsumsi", "lahan|polybag|pot|vertikultur", 60, 80, 10, 35, 1500, [10, 25], 1, 5, 0, "bercak daun|kutu daun")
add("ginseng_jawa", "Talinum triangulare", "Ginseng Jawa (Som Jawa)", "sayuran daun", "konsumsi|jual", "lahan|polybag|pot", 40, 60, 100, 1500, 1500, [5, 10], 1, 5, 0, "ulat daun")
add("sawi_hijau", "Brassica rapa Gaisin gr.", "Sawi Hijau (Caisim)", "sayuran daun", "konsumsi|jual", ALL4, 30, 40, 40, 250, 400, [10, 25, 50], 1, 5, 0, "ulat tritip|busuk lunak")
add("pakcoy", "Brassica rapa Pak Choi", "Pakcoy", "sayuran daun", "konsumsi|jual", ALL4, 25, 35, 40, 250, 600, [10, 25, 50], 1, 5, 0, "ulat tritip|kutu daun")
add("sawi_keriting", "Brassica juncea", "Sawi Keriting (Mustard)", "sayuran daun", "konsumsi|jual", ALL4, 35, 50, 40, 300, 500, [10, 25, 50], 1, 5, 0, "ulat tritip|kutu daun")
add("sawi_sendok", "Brassica chinensis", "Sawi Sendok (Tatsoi)", "sayuran daun", "konsumsi|jual", ALL4, 30, 45, 40, 280, 700, [10, 25], 1, 5, 200, "ulat tritip")
add("selada", "Lactuca sativa var. capitata", "Selada", "sayuran daun", "konsumsi|jual", ALL4, 35, 50, 20, 800, 2500, [2, 5, 10], 2, 5, 300, "busuk lunak|kutu daun")
add("endive", "Cichorium endivia", "Endive", "sayuran daun", "konsumsi|jual", "lahan|polybag|pot|hidroponik", 60, 80, 30, 800, 3500, [2, 5, 10], 2, 5, 400, "busuk lunak")
add("seledri", "Apium graveolens var. dulce", "Seledri", "sayuran daun", "konsumsi|jual", "lahan|polybag|pot", 70, 90, 20, 2000, 2800, [2, 5], 2, 5, 600, "bercak daun|busuk batang")
add("bawang_daun", "Allium fistulosum", "Bawang Daun", "sayuran daun", "konsumsi|jual", "lahan|polybag|pot", 60, 80, 30, 250, 3000, [5, 10], 2, 5, 400, "trips|bercak ungu")
add("bayam_spinach", "Spinacia oleracea", "Spinach", "sayuran daun", "konsumsi|jual", "lahan|polybag|pot|hidroponik", 40, 55, 100, 90, 1500, [10, 25, 50], 2, 5, 500, "karat putih|bercak daun")
add("arugula", "Eruca sativa", "Arugula (Rocket)", "sayuran daun", "konsumsi|jual", "lahan|polybag|pot|hidroponik", 30, 40, 60, 400, 3500, [5, 10, 25], 1, 5, 0, "kutu loncat|ulat daun")
add("peterseli", "Petroselinum crispum", "Peterseli (Parsley)", "herbal & rempah", "konsumsi|jual", "lahan|polybag|pot|hidroponik", 70, 90, 40, 300, 3500, [2, 5, 10], 2, 5, 400, "bercak daun|busuk akar")
add("ketumbar", "Coriandrum sativum", "Ketumbar (Daun)", "herbal & rempah", "konsumsi|jual", "lahan|polybag|pot|hidroponik", 40, 55, 100, 90, 600, [25, 50, 100], 1, 6, 0, "embun tepung|kutu daun")
add("dill", "Anethum graveolens", "Dill", "herbal & rempah", "konsumsi", "lahan|polybag|pot", 50, 70, 40, 700, 2500, [2, 5, 10], 1, 6, 300, "kutu daun")
add("tong_ho", "Chrysanthemum coronarium var. coronarium", "Tong Ho (Krisan Sayur)", "sayuran daun", "konsumsi|jual", "lahan|polybag|pot|hidroponik", 35, 50, 80, 600, 2000, [5, 10, 25], 1, 5, 300, "kutu daun|bercak daun")
add("kale", "Brassica oleracea var. acephala", "Kale", "sayuran daun", "konsumsi|jual", "lahan|polybag|pot", 60, 85, 4, 250, 4500, [2, 5, 10], 2, 6, 500, "ulat kubis|kutu daun")
add("kohlrabi", "Brassica oleracea var. gongyloides", "Kohlrabi (Kol Rabi)", "sayuran umbi", "konsumsi|jual", "lahan|polybag", 55, 70, 20, 250, 4500, [5, 10], 2, 6, 600, "ulat kubis")
add("kubis", "Brassica oleracea var. capitata", "Kubis", "sayuran daun", "jual|konsumsi", "lahan|polybag", 70, 90, 4, 250, 3500, [5, 10], 2, 6, 700, "ulat kubis|akar gada")
add("kembang_kol", "Brassica oleracea var. botrytis", "Kembang Kol", "sayuran daun", "jual", "lahan", 60, 80, 4, 300, 4500, [5, 10], 3, 6, 700, "ulat kubis|busuk hitam")
add("brokoli", "Brassica oleracea var. italica", "Brokoli", "sayuran daun", "jual|konsumsi", "lahan|polybag", 70, 90, 4, 300, 5500, [5, 10], 3, 6, 700, "ulat kubis|busuk hitam")
# --- umbi ---
add("wortel", "Daucus carota", "Wortel", "sayuran umbi", "konsumsi|jual", "lahan|pot", 75, 100, 100, 700, 1800, [10, 25, 50], 2, 6, 500, "nematoda|bercak daun")
add("lobak", "Raphanus sativus", "Lobak", "sayuran umbi", "konsumsi|jual", "lahan|polybag|pot", 45, 60, 40, 100, 700, [10, 25, 50], 1, 6, 200, "kutu daun|ulat daun")
add("lobak_merah", "Raphanus sativus var. radicula", "Lobak Merah (Radish)", "sayuran umbi", "konsumsi|jual", "lahan|polybag|pot", 25, 35, 80, 120, 1000, [10, 25, 50], 1, 6, 0, "kutu loncat")
add("bit", "Beta vulgaris", "Bit", "sayuran umbi", "konsumsi|jual", "lahan|polybag|pot", 55, 70, 40, 60, 1800, [10, 25], 2, 6, 400, "bercak daun")
add("swiss_chard", "Beta vulgaris var. cicla", "Swiss Chard (Bayam Batang)", "sayuran daun", "konsumsi|jual", "lahan|polybag|pot", 50, 65, 25, 50, 2000, [10, 25], 2, 6, 0, "bercak daun|kutu daun")
add("bawang_merah", "Allium cepa var. aggregatum", "Bawang Merah (Biji TSS)", "sayuran umbi", "jual", "lahan", 90, 110, 40, 300, 1500, [5, 10, 25], 3, 8, 0, "trips|moler")
add("bawang_bombay", "Allium cepa var. cepa", "Bawang Bombay (Biji)", "sayuran umbi", "jual|konsumsi", "lahan", 110, 140, 80, 250, 4000, [2, 5, 10], 3, 8, 300, "trips|busuk leher")
# --- herbal & rempah ---
add("kemangi", "Ocimum americanum", "Kemangi", "herbal & rempah", "konsumsi|jual", ALL4, 45, 60, 20, 600, 1500, [2, 5, 10], 1, 6, 0, "kutu daun|layu")
add("basil", "Ocimum basilicum", "Basil Italia", "herbal & rempah", "konsumsi|jual", ALL4, 45, 60, 20, 600, 4000, [1, 2, 5], 2, 6, 0, "kutu daun|embun tepung")
add("basil_suci", "Ocimum tenuiflorum", "Basil Suci (Tulsi)", "herbal & rempah", "konsumsi|hias", "lahan|polybag|pot", 60, 80, 20, 600, 3000, [2, 5], 2, 6, 0, "kutu daun")
add("spearmint", "Mentha spicata var. crispa", "Spearmint (Pudina)", "herbal & rempah", "konsumsi|jual", "lahan|polybag|pot|hidroponik", 60, 80, 15, 5000, 8000, [1, 2], 2, 4, 400, "karat daun")
add("peppermint", "Mentha piperita", "Peppermint", "herbal & rempah", "konsumsi|jual", "lahan|polybag|pot|hidroponik", 60, 80, 15, 5000, 8500, [1, 2], 2, 4, 500, "karat daun")
add("telang", "Clitoria ternatea", "Bunga Telang", "herbal & rempah", "konsumsi|jual|hias", "lahan|polybag|pot|vertikultur", 60, 90, 2, 20, 1500, [10, 25], 1, 6, 0, "kutu daun")
add("stevia", "Stevia rebaudiana", "Stevia", "herbal & rempah", "jual|konsumsi", "lahan|polybag|pot", 90, 120, 6, 3000, 9000, [1, 2], 3, 6, 0, "bercak daun")
add("adas", "Foeniculum vulgare", "Adas", "herbal & rempah", "konsumsi|jual", "lahan|polybag", 90, 120, 20, 250, 1500, [5, 10, 25], 2, 6, 400, "kutu daun")
add("klabet", "Trigonella foenum-graecum", "Klabet (Fenugreek)", "herbal & rempah", "konsumsi|jual", "lahan|polybag|pot", 60, 90, 60, 60, 400, [25, 50, 100], 1, 6, 0, "embun tepung")
add("wijen", "Sesamum indicum", "Wijen", "kacang-kacangan", "jual|konsumsi", "lahan|polybag", 85, 100, 40, 300, 200, [50, 100, 250], 1, 8, 0, "ulat daun|layu")
add("rosela", "Hibiscus sabdariffa", "Rosela", "herbal & rempah", "jual|konsumsi", "lahan|polybag", 130, 160, 3, 40, 800, [10, 25], 1, 7, 0, "kutu putih|busuk batang")
add("sambiloto", "Andrographis paniculata", "Sambiloto", "herbal & rempah", "jual|konsumsi", "lahan|polybag|pot", 90, 120, 20, 1000, 1000, [5, 10], 1, 6, 0, "bercak daun")
add("jintan_hitam", "Nigella sativa", "Jintan Hitam (Habbatussauda)", "herbal & rempah", "jual|konsumsi", "lahan|polybag|pot", 120, 150, 100, 350, 600, [10, 25], 2, 7, 300, "embun tepung")
add("oregano", "Origanum vulgare", "Oregano", "herbal & rempah", "konsumsi|jual", "lahan|polybag|pot", 90, 120, 15, 5000, 10000, [1, 2], 2, 6, 500, "busuk akar")
add("lavender", "Lavandula angustifolia", "Lavender", "bunga hias", "hias|jual", "lahan|polybag|pot", 150, 200, 10, 1000, 12000, [1, 2], 3, 7, 800, "busuk akar|bercak daun")
# --- bunga hias ---
add("bunga_matahari", "Helianthus annuus", "Bunga Matahari", "bunga hias", "hias|jual", "lahan|polybag|pot", 65, 90, 6, 12, 1200, [10, 25, 50], 1, 8, 0, "karat daun|ulat")
add("jengger_ayam", "Celosia argentea", "Jengger Ayam (Celosia)", "bunga hias", "hias|jual", "lahan|polybag|pot", 60, 80, 20, 1000, 3000, [2, 5, 10], 1, 7, 0, "kutu daun")
add("tapak_dara", "Catharanthus roseus", "Tapak Dara", "bunga hias", "hias", "lahan|polybag|pot", 90, 120, 15, 800, 4000, [2, 5], 1, 6, 0, "busuk akar")
add("calendula", "Calendula officinalis", "Calendula (Kenikir Inggris)", "bunga hias", "hias|jual", "lahan|polybag|pot", 60, 80, 12, 120, 3500, [5, 10], 1, 6, 300, "embun tepung")
add("marigold", None, "Marigold (Tahi Ayam)", "bunga hias", "hias|jual", "lahan|polybag|pot", 50, 65, 12, 300, 1800, [5, 10, 25], 1, 6, 0, "kutu daun", manual=(10, 18, 28, 35, 400, 600, 1500, 2500, 5.0, 6.0, 7.0, 8.0, 1800))
add("zinnia", None, "Zinnia", "bunga hias", "hias|jual", "lahan|polybag|pot", 55, 70, 12, 130, 2500, [5, 10], 1, 7, 0, "embun tepung", manual=(10, 18, 30, 36, 400, 600, 1500, 2500, 5.5, 6.0, 7.0, 7.8, 1800))
add("kosmos", None, "Kosmos", "bunga hias", "hias|jual", "lahan|polybag|pot", 60, 80, 10, 220, 2000, [5, 10, 25], 1, 6, 300, "kutu daun", manual=(8, 15, 27, 33, 400, 600, 1500, 2500, 5.5, 6.0, 7.5, 8.0, 2000))
add("pacar_air", None, "Pacar Air (Balsam)", "bunga hias", "hias|jual", "lahan|polybag|pot", 60, 75, 15, 200, 2500, [5, 10], 1, 5, 0, "embun tepung", manual=(12, 20, 30, 35, 500, 800, 1800, 3000, 5.5, 6.0, 7.0, 7.5, 1500))
add("portulaca", None, "Bunga Pukul Sembilan (Portulaca)", "bunga hias", "hias|jual", "lahan|polybag|pot", 40, 60, 40, 10000, 10000, [1, 2], 1, 8, 0, "busuk akar", manual=(12, 20, 32, 38, 300, 500, 1200, 2000, 5.5, 6.0, 7.5, 8.0, 1500))
add("snapdragon", None, "Snapdragon (Antirrhinum)", "bunga hias", "hias|jual", "lahan|polybag|pot", 90, 120, 20, 6000, 15000, [1, 2], 3, 6, 600, "karat daun", manual=(5, 12, 22, 28, 400, 600, 1200, 2000, 5.5, 6.0, 7.0, 7.5, 2000))
add("gomphrena", None, "Bunga Kancing (Gomphrena)", "bunga hias", "hias|jual", "lahan|polybag|pot", 70, 90, 15, 400, 4000, [2, 5, 10], 1, 7, 0, "kutu daun", manual=(12, 20, 30, 36, 400, 600, 1500, 2500, 5.5, 6.0, 7.5, 8.0, 1800))
add("pukul_empat", None, "Bunga Pukul Empat", "bunga hias", "hias", "lahan|polybag|pot", 70, 90, 6, 3, 600, [10, 25], 1, 6, 0, "kutu daun", manual=(10, 18, 30, 36, 400, 600, 1500, 2500, 5.5, 6.0, 7.5, 8.0, 1800))
# --- kacang-kacangan & serealia ---
add("edamame", "Glycine max", "Edamame", "kacang-kacangan", "konsumsi|jual", "lahan|polybag", 65, 80, 16, 4, 900, [25, 50, 100], 1, 7, 0, "ulat polong|karat daun")
add("kedelai", "Glycine max", "Kedelai", "kacang-kacangan", "jual|konsumsi", "lahan", 80, 95, 40, 7, 150, [100, 250, 500, 1000], 1, 8, 0, "ulat polong|karat daun")
add("kacang_tanah", "Arachis hypogaea", "Kacang Tanah", "kacang-kacangan", "konsumsi|jual", "lahan|polybag", 85, 100, 16, 1.8, 250, [100, 250, 500], 1, 8, 0, "bercak daun|layu bakteri")
add("kacang_hijau", "Vigna radiata", "Kacang Hijau", "kacang-kacangan", "konsumsi|jual", "lahan|polybag", 55, 65, 25, 17, 200, [100, 250, 500], 1, 8, 0, "kutu daun|embun tepung")
add("kacang_hitam", "Vigna mungo", "Kacang Hitam", "kacang-kacangan", "konsumsi|jual", "lahan", 70, 90, 25, 17, 250, [100, 250, 500], 1, 8, 0, "kutu daun|karat daun")
add("kacang_tunggak", "Vigna unguiculata ssp. unguiculata", "Kacang Tunggak", "kacang-kacangan", "konsumsi|jual", "lahan|polybag", 60, 80, 15, 8, 250, [100, 250, 500], 1, 7, 0, "kutu daun|lalat bibit")
add("kapri", "Pisum sativum", "Kacang Kapri", "kacang-kacangan", "konsumsi|jual", "lahan|polybag", 60, 75, 20, 4, 700, [25, 50, 100], 2, 6, 600, "embun tepung|kutu daun")
add("kacang_merah", "Phaseolus vulgaris", "Kacang Merah", "kacang-kacangan", "konsumsi|jual", "lahan|polybag", 85, 100, 12, 2.5, 400, [50, 100, 250], 2, 6, 500, "karat daun|antraknosa")
add("kacang_gude", "Cajanus cajan", "Kacang Gude", "kacang-kacangan", "konsumsi|jual", "lahan", 120, 160, 4, 7, 300, [50, 100, 250], 1, 7, 0, "ulat polong")
add("komak", "Lablab purpureus", "Komak (Kacang Lablab)", "kacang-kacangan", "konsumsi", "lahan|vertikultur", 90, 120, 5, 3.5, 300, [50, 100, 250], 1, 6, 0, "kutu daun")
add("kecipir", "Psophocarpus tetragonolobus", "Kecipir", "kacang-kacangan", "konsumsi|jual", "lahan|vertikultur", 70, 90, 5, 4, 600, [25, 50, 100], 1, 6, 0, "kutu daun|karat daun")
add("koro_pedang", "Canavalia ensiformis", "Koro Pedang", "kacang-kacangan", "konsumsi|jual", "lahan|vertikultur", 120, 150, 2, 1.5, 300, [100, 250, 500], 1, 7, 0, "kutu daun")
add("padi", "Oryza sativa ssp. indica", "Padi", "serealia", "konsumsi|jual", "lahan", 105, 125, 150, 38, 20, [500, 1000, 5000], 2, 8, 0, "wereng|blast", topmn=24, topmx=33)
add("jagung_pipil", "Zea mays", "Jagung Pipil", "serealia", "jual|konsumsi", "lahan|polybag", 90, 110, 6, 4, 350, [100, 250, 500, 1000], 1, 8, 0, "bulai|ulat grayak", topmn=22, topmx=32)
add("sorgum", "Sorghum bicolor", "Sorgum", "serealia", "jual|konsumsi", "lahan", 100, 130, 20, 30, 150, [100, 250, 500, 1000], 2, 8, 0, "lalat bibit|burung")
add("jewawut", "Setaria italica", "Jewawut", "serealia", "konsumsi|jual", "lahan", 70, 90, 100, 450, 200, [50, 100, 250], 1, 8, 0, "burung")
add("soba", "Fagopyrum esculentum", "Soba (Buckwheat)", "serealia", "konsumsi|jual", "lahan|polybag", 60, 80, 100, 40, 300, [50, 100, 250], 2, 7, 300, "kutu daun")
# --- pupuk hijau & penutup tanah ---
add("orok_orok", "Crotalaria juncea", "Orok-orok (Crotalaria)", "pupuk hijau & pakan", "jual", "lahan", 45, 75, 100, 30, 120, [100, 250, 500, 1000], 1, 8, 0, "ulat daun")
add("kara_benguk", "Mucuna pruriens", "Kara Benguk (Mucuna)", "pupuk hijau & pakan", "jual", "lahan", 60, 90, 8, 3, 250, [100, 250, 500], 1, 7, 0, "")
add("calopogonium", "Calopogonium mucunoides", "Kacang Asu (Calopogonium)", "pupuk hijau & pakan", "jual", "lahan", 60, 90, 200, 80, 800, [50, 100, 250], 1, 7, 0, "")
add("centrosema", "Centrosema pubescens", "Centro (Centrosema)", "pupuk hijau & pakan", "jual", "lahan", 60, 90, 100, 50, 800, [50, 100, 250], 1, 7, 0, "")
# --- pakan ternak ---
add("brachiaria_d", "Brachiaria decumbens", "Rumput Signal (Brachiaria decumbens)", "pupuk hijau & pakan", "jual", "lahan", 90, 120, 100, 200, 350, [100, 250, 500, 1000], 1, 8, 0, "")
add("brachiaria_b", "Brachiaria brizantha", "Rumput Brachiaria brizantha", "pupuk hijau & pakan", "jual", "lahan", 90, 120, 100, 200, 400, [100, 250, 500, 1000], 1, 8, 0, "")
add("millet_pakan", "Pennisetum glaucum", "Millet Pakan (Pearl Millet)", "pupuk hijau & pakan", "jual", "lahan", 60, 90, 150, 130, 150, [100, 250, 500, 1000], 1, 8, 0, "burung")
add("rumput_gajah", "Pennisetum purpureum", "Rumput Gajah (Biji)", "pupuk hijau & pakan", "jual", "lahan", 90, 120, 100, 500, 1200, [50, 100, 250], 1, 8, 0, "")

# ---------------------------------------------------------------------------
BRANDS = {  # brand -> pengali harga
    "TaniMas": 1.00, "Benih Nusantara": 1.15, "Agro Subur": 0.85,
    "Kebun Lestari": 0.95, "Greenfield Seeds": 1.30, "BibitKu": 0.80,
}

TEXTURE_MAP = {
    "heavy": ["liat", "liat berlempung"],
    "medium": [L, LL, LP],
    "light": [P, LP],
}


def f(x, default=None):
    return default if x is None or (isinstance(x, float) and math.isnan(x)) else float(x)


def textures(txt):
    if not isinstance(txt, str):
        return [L, LP]
    out = []
    for k, vals in TEXTURE_MAP.items():
        if k in txt:
            for v in vals:
                if v not in out:
                    out.append(v)
    return out or [L, LP]


def drainage(txt):
    if not isinstance(txt, str):
        return "baik"
    if "poorly" in txt:
        return "toleran"
    return "baik"


def env_from_ecocrop(row, ov):
    """Ambil parameter EcoCrop; nilai kosong diisi default umum (dicatat di `filled`)."""
    filled = []

    def r(k, default):
        v = f(row[k])
        if v is None:
            filled.append(k)
            return default
        return v

    topmn, topmx = ov.get("topmn", r("TOPMN", 20.0)), ov.get("topmx", r("TOPMX", 30.0))
    tmin, tmax = r("TMIN", topmn - 8), r("TMAX", topmx + 6)
    tmin, tmax = min(tmin, topmn - 2), max(tmax, topmx + 2)
    ropmn, ropmx = r("ROPMN", 800.0), r("ROPMX", 1800.0)
    rmin, rmax = r("RMIN", ropmn * 0.5), r("RMAX", ropmx * 1.6)
    phopmn, phopmx = r("PHOPMN", 5.8), r("PHOPMX", 7.0)
    phmin, phmax = r("PHMIN", phopmn - 1.0), r("PHMAX", phopmx + 1.0)
    altmx = ov.get("altmx", f(row["ALTMX"]))
    return dict(
        t=(tmin, topmn, topmx, tmax),
        rain=tuple(v / 12 for v in (rmin, ropmn, ropmx, rmax)),
        ph=(phmin, phopmn, phopmx, phmax),
        alt_max=altmx if altmx else 1500.0,
        tex=textures(row["TEXT"]), drain=drainage(row["DRA"]), filled=filled,
    )


def env_from_manual(m):
    return dict(
        t=m[0:4], rain=tuple(v / 12 for v in m[4:8]), ph=m[8:12], alt_max=float(m[12]),
        tex=[L, LP], drain="baik",
    )


COLUMNS = [
    "product_id", "item_id", "commodity_id", "commodity", "scientific_name", "category", "brand", "variety",
    "name", "description", "days_min", "days_max",
    "temp_abs_min", "temp_opt_min", "temp_opt_max", "temp_abs_max",
    "rain_abs_min", "rain_opt_min", "rain_opt_max", "rain_abs_max",
    "ph_abs_min", "ph_opt_min", "ph_opt_max", "ph_abs_max",
    "alt_min", "alt_max", "soil_textures", "drainage", "sun_hours", "grow_types",
    "seeds_per_m2", "seeds_per_pack", "pack_g", "price_idr", "stock", "difficulty", "purpose",
    "common_pests", "env_source", "shop_data_synthetic",
]


def main():
    eco = pd.read_csv(ECOCROP_PATH, encoding="latin-1")
    eco = eco[eco["TMIN"].notna()]
    rows, missing = [], []
    for idx, (a, ov) in enumerate(C, 1):
        (key, sci, name, cat, purpose, grow, dmin, dmax, sm2, spg, ppg, packs, diff, sun, alt_min, pests) = a
        if "manual" in ov:
            env, src = env_from_manual(ov["manual"]), "manual_estimate"
        else:
            m = eco[eco["ScientificName"] == sci]
            if m.empty:
                missing.append(sci)
                continue
            env, src = env_from_ecocrop(m.iloc[0], ov), "ecocrop"
            if env["filled"]:
                print(f"  [default dipakai] {name}: {env['filled']}")
        tmin, topmn, topmx, tmax = env["t"]
        rmin, ropmn, ropmx, rmax = env["rain"]
        phmin, phopmn, phopmx, phmax = env["ph"]
        alt_max = min(3000.0, max(env["alt_max"], alt_min + 300))

        brands = rng.sample(list(BRANDS), 3)
        for b in brands:
            sizes = sorted(packs) if len(packs) <= 2 else sorted(rng.sample(packs, 2))
            for i, g in enumerate(sizes):
                price = ppg * g * BRANDS[b] * rng.uniform(0.95, 1.08) * (0.9 ** i)
                price = max(2500, round(price / 500) * 500)
                stock = 0 if rng.random() < 0.05 else rng.randint(10, 400)
                rows.append({
                    "product_id": f"{key.upper()}-{b.split()[0][:3].upper()}-{g:g}G",
                    "item_id": f"{key}:{b}",
                    "commodity_id": key,
                    "commodity": name,
                    "scientific_name": sci or "",
                    "category": cat,
                    "brand": b,
                    "variety": "",
                    "name": f"Benih {name} - {b} ({g:g} g)",
                    "description": (f"Benih {name}. Panen sekitar {dmin}-{dmax} hari, suhu ideal "
                                    f"{topmn:.0f}-{topmx:.0f} C, pH {phopmn:.1f}-{phopmx:.1f}, "
                                    f"cocok hingga {alt_max:.0f} mdpl."),
                    "days_min": dmin, "days_max": dmax,
                    "temp_abs_min": tmin, "temp_opt_min": topmn, "temp_opt_max": topmx, "temp_abs_max": tmax,
                    "rain_abs_min": round(rmin, 1), "rain_opt_min": round(ropmn, 1),
                    "rain_opt_max": round(ropmx, 1), "rain_abs_max": round(rmax, 1),
                    "ph_abs_min": phmin, "ph_opt_min": phopmn, "ph_opt_max": phopmx, "ph_abs_max": phmax,
                    "alt_min": alt_min, "alt_max": alt_max,
                    "soil_textures": "|".join(env["tex"]), "drainage": env["drain"], "sun_hours": sun,
                    "grow_types": grow, "seeds_per_m2": sm2,
                    "seeds_per_pack": max(1, int(round(g * spg))), "pack_g": g,
                    "price_idr": int(price), "stock": stock, "difficulty": diff, "purpose": purpose,
                    "common_pests": pests, "env_source": src, "shop_data_synthetic": 1,
                })

    if missing:
        print("TIDAK DITEMUKAN di EcoCrop:", missing)
    with open("products.csv", "w", newline="", encoding="utf-8-sig") as fh:
        w = csv.DictWriter(fh, fieldnames=COLUMNS)
        w.writeheader()
        w.writerows(rows)
    n_comm = len({r["commodity_id"] for r in rows})
    print(f"{n_comm} komoditas, {len(rows)} produk -> products.csv")


if __name__ == "__main__":
    main()
