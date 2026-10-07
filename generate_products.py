"""
Generator katalog benih & biji (SINTETIS) -> products.csv

SEMUA data di sini dibuat otomatis untuk prototype (kolom is_synthetic=1).
Parameter komoditas (suhu, ketinggian, pH, umur panen, dll) adalah perkiraan kasar
berdasarkan pengetahuan umum budidaya, BUKAN data resmi. Nama varietas dan merek
adalah fiktif. Ganti dengan data produk asli begitu tersedia; skema kolom tetap
bisa dipakai oleh scoring.py.

Jalankan: python generate_products.py
"""
import csv
import random

rng = random.Random(42)

# ---------------------------------------------------------------------------
# Tabel komoditas
# (nama, kategori, tmin, tmax, alt_min, alt_max, hujan_min, hujan_max, ph_min, ph_max,
#  tekstur, drainase, jam_matahari, hari_min, hari_max, jarak_tanam_cm,
#  benih_per_m2, benih_per_gram, harga_per_gram_idr, kesulitan(1-3),
#  tipe_tanam, potensi_hasil_ton_ha, hama_penyakit, tujuan, ukuran_kemasan_gram)
# hujan = curah hujan optimal mm/bulan; hari = umur sampai panen pertama (dari semai)
# ---------------------------------------------------------------------------
L, LP, LL, P = "lempung", "lempung berpasir", "liat berlempung", "berpasir"
ALL4 = "lahan|polybag|pot|hidroponik"

COMMODITIES = [
    # --- sayuran buah ---
    ("Cabai Rawit", "sayuran buah", 22, 32, 0, 1000, 100, 200, 5.5, 7.0, f"{L}|{LP}", "baik", 6, 90, 110, "50x60", 4, 150, 9000, 2, "lahan|polybag|pot", "8-12", "layu fusarium|antraknosa", "konsumsi|jual", [2, 5, 10]),
    ("Cabai Merah Keriting", "sayuran buah", 20, 30, 0, 1200, 100, 200, 5.5, 6.8, f"{L}|{LP}", "baik", 6, 100, 125, "60x50", 3.5, 150, 12000, 2, "lahan|polybag", "12-20", "virus kuning|antraknosa", "jual|keduanya", [5, 10]),
    ("Cabai Besar", "sayuran buah", 20, 28, 100, 1200, 100, 200, 5.5, 6.8, f"{L}|{LP}", "baik", 6, 100, 125, "60x50", 3.5, 150, 11000, 3, "lahan|polybag", "12-18", "antraknosa|layu bakteri", "jual", [5, 10]),
    ("Tomat", "sayuran buah", 18, 27, 300, 1500, 100, 200, 5.8, 6.8, f"{L}|{LP}", "baik", 6, 80, 100, "60x50", 3.5, 300, 6000, 2, ALL4, "30-60", "layu bakteri|virus gemini", "konsumsi|jual|keduanya", [2, 5, 10]),
    ("Terong", "sayuran buah", 22, 32, 0, 1000, 100, 200, 5.5, 6.8, f"{L}|{LP}|{LL}", "sedang", 6, 80, 100, "70x60", 2.5, 250, 3500, 1, "lahan|polybag", "20-35", "ulat buah|layu bakteri", "konsumsi|jual", [5, 10, 25]),
    ("Timun", "sayuran buah", 22, 30, 0, 1000, 80, 180, 5.5, 7.0, f"{LP}|{L}", "baik", 6, 40, 55, "60x40", 5, 35, 800, 1, "lahan|polybag|vertikultur", "20-35", "embun tepung|downy mildew", "konsumsi|jual", [10, 25, 50]),
    ("Paria", "sayuran buah", 24, 32, 0, 800, 100, 200, 6.0, 6.7, L, "baik", 6, 55, 70, "100x50", 2, 15, 2500, 2, "lahan|polybag|vertikultur", "15-25", "lalat buah|embun tepung", "konsumsi|keduanya", [10, 25]),
    ("Kacang Panjang", "sayuran buah", 24, 32, 0, 800, 80, 180, 5.8, 6.8, f"{L}|{LP}", "sedang", 6, 45, 60, "60x30", 8, 7, 450, 1, "lahan|polybag|vertikultur", "10-20", "lalat bibit|karat daun", "konsumsi|jual", [25, 50, 100]),
    ("Buncis", "sayuran buah", 18, 26, 300, 1500, 80, 150, 5.5, 6.8, L, "baik", 6, 45, 60, "50x30", 10, 3.5, 400, 1, "lahan|polybag", "10-18", "karat daun|antraknosa", "konsumsi|jual", [25, 50, 100]),
    ("Jagung Manis", "sayuran buah", 21, 30, 0, 1200, 80, 150, 5.8, 7.0, f"{L}|{LP}", "baik", 8, 65, 80, "70x25", 6, 4, 500, 1, "lahan|polybag", "10-15", "bulai|ulat grayak", "konsumsi|jual|keduanya", [50, 100, 250]),
    ("Okra", "sayuran buah", 24, 34, 0, 800, 80, 200, 6.0, 7.0, f"{L}|{LP}", "baik", 7, 50, 65, "60x40", 4, 15, 1500, 1, "lahan|polybag|pot", "8-14", "kutu daun|embun tepung", "konsumsi|keduanya", [10, 25]),
    ("Labu Kuning", "sayuran buah", 22, 30, 0, 1000, 80, 180, 5.5, 7.0, L, "baik", 7, 90, 110, "200x100", 0.5, 5, 700, 1, "lahan|vertikultur", "20-40", "embun tepung|lalat buah", "konsumsi|jual", [10, 25]),
    ("Zukini", "sayuran buah", 18, 28, 0, 1000, 80, 160, 6.0, 7.0, f"{L}|{LP}", "baik", 6, 50, 60, "90x60", 1.5, 6, 3000, 2, "lahan|polybag", "20-40", "embun tepung|virus mosaik", "konsumsi|keduanya", [5, 10]),
    ("Melon", "sayuran buah", 25, 32, 0, 800, 50, 120, 6.0, 6.8, LP, "baik", 8, 60, 75, "100x50", 2, 30, 6000, 3, "lahan|polybag", "20-35", "layu fusarium|embun tepung", "jual|keduanya", [5, 10]),
    ("Semangka", "sayuran buah", 25, 32, 0, 600, 50, 120, 6.0, 6.8, LP, "baik", 8, 65, 80, "200x60", 1, 15, 4000, 3, "lahan", "20-40", "layu fusarium|lalat buah", "jual|keduanya", [5, 10]),
    # --- sayuran daun ---
    ("Kangkung", "sayuran daun", 25, 35, 0, 1000, 100, 300, 5.5, 7.5, f"{L}|{LL}|{LP}", "toleran", 5, 25, 35, "10x10", 150, 30, 150, 1, ALL4, "15-25", "ulat daun|karat putih", "konsumsi|jual", [50, 100, 250]),
    ("Bayam", "sayuran daun", 20, 32, 0, 1200, 80, 200, 6.0, 7.0, f"{L}|{LP}", "sedang", 5, 25, 35, "10x10", 200, 100, 120, 1, ALL4, "10-20", "karat putih|ulat daun", "konsumsi|jual", [25, 50, 100]),
    ("Sawi Hijau", "sayuran daun", 20, 30, 0, 1200, 100, 200, 6.0, 7.0, f"{L}|{LP}|{LL}", "sedang", 5, 30, 40, "20x20", 40, 250, 400, 1, ALL4, "15-25", "ulat tritip|busuk lunak", "konsumsi|jual", [10, 25, 50]),
    ("Pakcoy", "sayuran daun", 18, 28, 0, 1500, 100, 200, 6.0, 7.0, f"{L}|{LP}", "sedang", 5, 25, 35, "20x20", 40, 250, 600, 1, ALL4, "15-25", "ulat tritip|kutu daun", "konsumsi|jual", [10, 25, 50]),
    ("Selada", "sayuran daun", 15, 24, 500, 1800, 80, 150, 6.0, 7.0, L, "baik", 5, 35, 50, "25x25", 20, 800, 2500, 2, "lahan|polybag|pot|hidroponik", "15-25", "busuk lunak|kutu daun", "konsumsi|jual", [2, 5, 10]),
    ("Seledri", "sayuran daun", 16, 24, 800, 1800, 90, 160, 6.0, 6.8, L, "sedang", 5, 70, 90, "25x25", 20, 2000, 2800, 2, "lahan|polybag|pot", "15-30", "bercak daun|busuk batang", "konsumsi|jual", [2, 5]),
    ("Bawang Daun", "sayuran daun", 18, 25, 700, 1800, 100, 180, 6.0, 7.0, L, "baik", 5, 60, 80, "20x15", 30, 250, 3000, 2, "lahan|polybag|pot", "15-30", "trips|bercak ungu", "konsumsi|jual", [5, 10]),
    ("Kailan", "sayuran daun", 18, 28, 0, 1500, 100, 200, 6.0, 7.0, f"{L}|{LP}", "sedang", 5, 40, 55, "25x25", 20, 300, 800, 2, "lahan|polybag|pot|hidroponik", "10-20", "ulat tritip", "konsumsi|jual", [10, 25]),
    # --- kubis & umbi ---
    ("Kubis", "sayuran daun", 15, 22, 800, 2000, 100, 200, 6.0, 6.8, f"{L}|{LL}", "sedang", 6, 70, 90, "50x40", 4, 250, 3500, 2, "lahan|polybag", "30-60", "ulat kubis|akar gada", "jual|keduanya", [5, 10]),
    ("Kembang Kol", "sayuran daun", 15, 21, 800, 2000, 100, 200, 6.0, 6.8, f"{L}|{LL}", "sedang", 6, 60, 80, "50x50", 4, 300, 4500, 3, "lahan", "20-35", "ulat kubis|busuk hitam", "jual", [5, 10]),
    ("Brokoli", "sayuran daun", 15, 22, 800, 2000, 100, 200, 6.0, 7.0, f"{L}|{LL}", "sedang", 6, 70, 90, "50x50", 4, 300, 5500, 3, "lahan|polybag", "15-25", "ulat kubis|busuk hitam", "jual|keduanya", [5, 10]),
    ("Wortel", "sayuran umbi", 16, 22, 700, 1800, 80, 160, 6.0, 6.8, f"{LP}|{L}", "baik", 6, 75, 100, "20x10", 100, 700, 1800, 2, "lahan|pot", "20-35", "nematoda|bercak daun", "konsumsi|jual", [10, 25, 50]),
    ("Lobak", "sayuran umbi", 15, 25, 300, 1500, 80, 160, 6.0, 6.8, f"{LP}|{L}", "baik", 6, 45, 60, "20x15", 40, 100, 700, 1, "lahan|polybag|pot", "15-30", "kutu daun|ulat daun", "konsumsi|jual", [10, 25, 50]),
    ("Bit", "sayuran umbi", 15, 24, 500, 1700, 80, 160, 6.0, 7.0, f"{LP}|{L}", "baik", 6, 55, 70, "20x15", 40, 60, 1800, 2, "lahan|polybag|pot", "15-30", "bercak daun", "konsumsi|keduanya", [10, 25]),
    ("Bawang Merah (TSS)", "sayuran umbi", 24, 32, 0, 800, 50, 100, 6.0, 6.8, LP, "baik", 8, 90, 110, "15x15", 40, 250, 50000, 3, "lahan", "10-20", "trips|moler", "jual", [1, 2, 5]),
    # --- herbal & rempah ---
    ("Kemangi", "herbal", 22, 32, 0, 1000, 80, 200, 6.0, 7.0, f"{L}|{LP}", "baik", 6, 45, 60, "25x25", 20, 600, 1500, 1, ALL4, "5-10", "kutu daun|layu", "konsumsi|jual", [2, 5, 10]),
    ("Basil Italia", "herbal", 20, 30, 0, 1200, 80, 180, 6.0, 7.0, f"{L}|{LP}", "baik", 6, 45, 60, "25x25", 20, 600, 4000, 2, ALL4, "5-10", "kutu daun|embun tepung", "konsumsi|keduanya", [1, 2, 5]),
    ("Pudina", "herbal", 18, 26, 400, 1500, 100, 200, 6.0, 7.0, L, "sedang", 4, 60, 80, "25x25", 15, 5000, 8000, 2, "lahan|polybag|pot|hidroponik", "5-10", "karat daun", "konsumsi|keduanya", [1, 2]),
    ("Bunga Telang", "herbal", 22, 32, 0, 1000, 100, 200, 6.0, 7.5, f"{L}|{LP}", "baik", 6, 60, 90, "100x50", 2, 20, 1500, 1, "lahan|polybag|pot|vertikultur", "3-6", "kutu daun", "konsumsi|jual|hias", [10, 25]),
    ("Stevia", "herbal", 20, 30, 0, 1200, 100, 200, 6.0, 7.0, f"{LP}|{L}", "baik", 6, 90, 120, "40x30", 6, 3000, 9000, 3, "lahan|polybag|pot", "3-6", "bercak daun", "jual|keduanya", [1, 2]),
    # --- bunga hias ---
    ("Bunga Matahari", "bunga hias", 20, 30, 0, 1500, 80, 160, 6.0, 7.5, f"{L}|{LP}", "baik", 8, 65, 90, "50x30", 6, 12, 1200, 1, "lahan|polybag|pot", "-", "karat daun|ulat", "hias|jual", [10, 25, 50]),
    ("Marigold", "bunga hias", 18, 30, 0, 1500, 80, 160, 6.0, 7.0, f"{L}|{LP}", "baik", 6, 50, 65, "25x25", 12, 300, 1800, 1, "lahan|polybag|pot", "-", "kutu daun", "hias|jual", [5, 10, 25]),
    ("Zinnia", "bunga hias", 18, 30, 0, 1500, 80, 160, 6.0, 7.0, f"{L}|{LP}", "baik", 7, 55, 70, "25x25", 12, 130, 2500, 1, "lahan|polybag|pot", "-", "embun tepung", "hias|jual", [5, 10]),
    ("Kosmos", "bunga hias", 15, 27, 300, 1500, 80, 160, 6.0, 7.0, f"{L}|{LP}", "baik", 6, 60, 80, "30x30", 10, 220, 2000, 1, "lahan|polybag|pot", "-", "kutu daun", "hias|jual", [5, 10, 25]),
    # --- kacang-kacangan ---
    ("Edamame", "kacang-kacangan", 22, 30, 0, 800, 80, 160, 6.0, 7.0, f"{L}|{LP}", "baik", 7, 65, 80, "40x15", 16, 4, 900, 1, "lahan|polybag", "5-9", "ulat polong|karat daun", "konsumsi|jual", [25, 50, 100]),
    ("Kacang Tanah", "kacang-kacangan", 25, 32, 0, 800, 60, 140, 5.5, 6.8, LP, "baik", 8, 85, 100, "40x15", 16, 1.8, 250, 1, "lahan|polybag", "2-4", "bercak daun|layu bakteri", "konsumsi|jual", [100, 250, 500]),
    ("Kacang Hijau", "kacang-kacangan", 25, 32, 0, 800, 60, 120, 6.0, 7.0, f"{L}|{LP}", "baik", 8, 55, 65, "40x10", 25, 17, 200, 1, "lahan|polybag", "1-2", "kutu daun|embun tepung", "konsumsi|jual", [100, 250, 500]),
    # --- buah ---
    ("Pepaya California", "buah", 22, 32, 0, 700, 100, 250, 6.0, 6.5, LP, "baik", 8, 210, 270, "250x250", 0.2, 50, 15000, 2, "lahan|polybag", "40-80", "virus kuning|busuk akar", "konsumsi|jual", [1, 2, 5]),
]

BRANDS = ["Benih Nusantara", "TaniMas", "Agro Subur", "Kebun Lestari", "Greenfield Seeds", "BibitKu", "Tani Jaya", "Sumber Panen"]
WORDS = ["Surya", "Bara", "Mekar", "Kencana", "Gading", "Rimba", "Pelangi", "Cakra", "Lestari", "Nusa",
         "Tirta", "Fajar", "Cempaka", "Bima", "Arjuna", "Sinar", "Permata", "Garuda", "Rajawali", "Intan",
         "Bintang", "Samudra", "Mutiara", "Anggun", "Perkasa", "Sakti", "Dewi", "Kartika"]

# varian: nama, deskripsi singkat
VARIANTS = ["Standar", "Genjah", "Dataran Tinggi", "Dataran Rendah", "Tahan Panas", "Tahan Hujan",
            "Tahan Kering", "Kompak", "Hibrida F1", "Organik"]

COLUMNS = [
    "product_id", "variety_id", "name", "brand", "commodity", "category", "variety", "variety_type", "tags",
    "days_min", "days_max", "temp_min", "temp_max", "alt_min", "alt_max", "rain_min_mm_month", "rain_max_mm_month",
    "ph_min", "ph_max", "soil_textures", "drainage", "sun_hours", "grow_types", "spacing_cm",
    "seeds_per_m2", "pack_g", "seeds_per_pack", "price_idr", "stock", "difficulty", "purpose",
    "pest_resistance", "yield_t_ha", "description", "is_synthetic",
]


def apply_variant(base, v):
    """Kembalikan salinan parameter dengan penyesuaian sesuai varian."""
    d = dict(base)
    d["variety_type"] = "OP"
    d["price_mult"] = 1.0
    d["tags"] = []
    if v == "Genjah":
        d["days_min"] = round(d["days_min"] * 0.85)
        d["days_max"] = round(d["days_max"] * 0.85)
        d["yield_mult"] = 0.9
        d["tags"].append("genjah")
    elif v == "Dataran Tinggi":
        d["alt_min"] = max(d["alt_min"], 500) if d["alt_max"] >= 800 else d["alt_min"]
        d["alt_max"] = d["alt_max"] + 400
        d["temp_min"] -= 2
        d["temp_max"] -= 2
        d["tags"].append("dataran tinggi")
    elif v == "Dataran Rendah":
        d["alt_min"] = max(0, d["alt_min"] - 500)
        d["alt_max"] = min(d["alt_max"], 700) if d["alt_max"] > 900 else d["alt_max"]
        d["temp_min"] += 1
        d["temp_max"] += 2
        d["tags"].append("dataran rendah")
    elif v == "Tahan Panas":
        d["temp_max"] += 3
        d["alt_min"] = max(0, d["alt_min"] - 300)
        d["tags"].append("tahan panas")
    elif v == "Tahan Hujan":
        d["rain_max"] += 80
        if d["drainage"] == "baik":
            d["drainage"] = "sedang"
        d["tags"].append("tahan hujan")
    elif v == "Tahan Kering":
        d["rain_min"] = max(30, d["rain_min"] - 30)
        d["rain_max"] = max(d["rain_min"] + 40, d["rain_max"] - 40)
        d["tags"].append("tahan kering")
    elif v == "Kompak":
        types = d["grow_types"].split("|")
        for t in ("pot", "polybag"):
            if t not in types:
                types.append(t)
        d["grow_types"] = "|".join(types)
        d["seeds_per_m2"] = round(d["seeds_per_m2"] * 1.5, 1)
        d["yield_mult"] = 0.6
        d["tags"].append("kompak/cocok pot")
    elif v == "Hibrida F1":
        d["variety_type"] = "F1"
        d["yield_mult"] = 1.25
        d["price_mult"] = 1.8
        d["tags"].append("hibrida")
    elif v == "Organik":
        d["price_mult"] = 1.3
        d["tags"].append("organik")
    return d


def fmt_yield(rng_str, mult):
    if rng_str in ("-", ""):
        return ""
    lo, hi = [float(x) for x in rng_str.split("-")]
    return f"{lo * mult:.1f}-{hi * mult:.1f}"


def main():
    rows = []
    vid = 0
    for c in COMMODITIES:
        (name, cat, tmin, tmax, amin, amax, rmin, rmax, phmin, phmax, tex, drain, sun,
         dmin, dmax, spacing, sm2, spg, ppg, diff, types, yld, pests, purpose, packs) = c
        base = dict(
            temp_min=tmin, temp_max=tmax, alt_min=amin, alt_max=amax, rain_min=rmin, rain_max=rmax,
            ph_min=phmin, ph_max=phmax, soil_textures=tex, drainage=drain, sun_hours=sun,
            days_min=dmin, days_max=dmax, spacing=spacing, seeds_per_m2=sm2, grow_types=types,
            difficulty=diff, yield_mult=1.0,
        )
        variants = ["Standar"] + rng.sample(VARIANTS[1:], 5)
        used_words = set()
        for v in variants:
            d = apply_variant(base, v)
            vid += 1
            variety_id = f"V{vid:04d}"
            # nama varietas fiktif
            while True:
                w = rng.choice(WORDS)
                if w not in used_words:
                    used_words.add(w)
                    break
            num = rng.randint(10, 99)
            variety = f"{w} {num}" + (" F1" if d["variety_type"] == "F1" else "")
            brand = rng.choice(BRANDS)
            # variasi kecil pada umur panen supaya tiap varietas unik
            jitter = rng.randint(-3, 3)
            dmin_v = max(10, d["days_min"] + jitter)
            dmax_v = max(dmin_v + 4, d["days_max"] + jitter)
            price_mult = d["price_mult"] * rng.uniform(0.9, 1.15)
            diff_v = min(3, max(1, d["difficulty"] + (1 if d["variety_type"] == "F1" and rng.random() < 0.2 else 0)))
            pest = pests.split("|")
            if rng.random() < 0.6:
                pest = pest[:1] if rng.random() < 0.5 else pest
            pest_res = "|".join(pest) if rng.random() < 0.7 else ""
            tags = "|".join(d["tags"])
            alt_txt = f"{int(d['alt_min'])}-{int(d['alt_max'])} mdpl"
            for i, g in enumerate(sorted(packs)):
                seeds_pack = int(round(g * spg))
                price = ppg * g * price_mult * (0.88 ** i)
                price = max(3000, round(price / 500) * 500)
                stock = 0 if rng.random() < 0.05 else rng.randint(10, 500)
                rows.append({
                    "product_id": f"SKU-{vid:04d}-{g}G",
                    "variety_id": variety_id,
                    "name": f"Benih {name} {variety} ({g} g)",
                    "brand": brand,
                    "commodity": name,
                    "category": cat,
                    "variety": variety,
                    "variety_type": d["variety_type"],
                    "tags": tags,
                    "days_min": dmin_v,
                    "days_max": dmax_v,
                    "temp_min": d["temp_min"],
                    "temp_max": d["temp_max"],
                    "alt_min": int(d["alt_min"]),
                    "alt_max": int(d["alt_max"]),
                    "rain_min_mm_month": d["rain_min"],
                    "rain_max_mm_month": d["rain_max"],
                    "ph_min": d["ph_min"],
                    "ph_max": d["ph_max"],
                    "soil_textures": d["soil_textures"],
                    "drainage": d["drainage"],
                    "sun_hours": d["sun_hours"],
                    "grow_types": d["grow_types"],
                    "spacing_cm": d["spacing"],
                    "seeds_per_m2": d["seeds_per_m2"],
                    "pack_g": g,
                    "seeds_per_pack": seeds_pack,
                    "price_idr": int(price),
                    "stock": stock,
                    "difficulty": diff_v,
                    "purpose": purpose,
                    "pest_resistance": pest_res,
                    "yield_t_ha": fmt_yield(yld, d["yield_mult"]),
                    "description": (f"{name} varietas {variety}. Panen pertama sekitar {dmin_v}-{dmax_v} hari, "
                                    f"cocok {alt_txt}, pH tanah {d['ph_min']}-{d['ph_max']}, "
                                    f"suhu ideal {d['temp_min']}-{d['temp_max']} C."),
                    "is_synthetic": 1,
                })

    with open("products.csv", "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=COLUMNS)
        w.writeheader()
        w.writerows(rows)
    print(f"{len(COMMODITIES)} komoditas, {vid} varietas, {len(rows)} produk -> products.csv")


if __name__ == "__main__":
    main()
