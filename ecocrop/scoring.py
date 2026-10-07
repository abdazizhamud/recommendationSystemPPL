"""
Rekomendasi benih berbasis aturan (rule-based), memakai parameter EcoCrop.

Alur:
  1. Filter keras  -> komoditas yang pasti tidak cocok dibuang (umur panen, ketinggian, suhu ekstrem,
                      tipe tanam, kategori, tujuan).
  2. Skor 0-100    -> kecocokan suhu, hujan, ketinggian, pH, tekstur, drainase, waktu, sinar, preferensi.
                      Tiap parameter pakai kurva trapesium EcoCrop: ~1.0 di rentang optimal, turun linear
                      ke 0 di batas absolut.
  3. Penawaran     -> untuk komoditas yang lolos, tampilkan brand yang tersedia + jumlah kemasan
                      yang perlu dibeli untuk luas lahan user, diurutkan dari yang termurah.

Pakai:
    from scoring import UserProfile, load_products, recommend
    products = load_products("products.csv")
    user = UserProfile(temp_avg=24, rain_mm_month=190, altitude_m=700, soil_texture="lempung",
                       soil_ph=6.3, area_m2=40, planting_type="lahan", days_available=90)
    for r in recommend(products, user, top_n=10):
        print(r["score"], r["commodity"], r["offers"][0])
"""
import csv
import math
from dataclasses import dataclass, field
from typing import Optional

CATEGORIES = ["sayuran buah", "sayuran daun", "sayuran umbi", "herbal & rempah", "bunga hias",
              "kacang-kacangan", "serealia", "buah", "pupuk hijau & pakan"]

# ---------------------------------------------------------------------------
# Input user
# ---------------------------------------------------------------------------


@dataclass
class UserProfile:
    # --- iklim: isi nilai tunggal, atau 12 nilai bulanan + start_month ---
    temp_avg: Optional[float] = None            # suhu rata-rata (C)
    rain_mm_month: Optional[float] = None       # curah hujan rata-rata (mm/bulan)
    altitude_m: Optional[float] = None          # ketinggian (mdpl)
    monthly_temp: Optional[list] = None         # 12 nilai, Jan..Des
    monthly_rain: Optional[list] = None         # 12 nilai, Jan..Des
    start_month: int = 1                        # bulan mulai tanam (1-12)
    # --- tanah ---
    soil_texture: Optional[str] = None          # berpasir | lempung berpasir | lempung | liat berlempung | liat
    soil_ph: Optional[float] = None             # None = user tidak tahu
    drainage: Optional[str] = None              # baik | sedang | buruk
    sun_hours: Optional[float] = None           # jam sinar langsung per hari
    # --- lahan & waktu ---
    area_m2: float = 10.0
    planting_type: str = "lahan"                # lahan | polybag | pot | hidroponik | vertikultur
    n_containers: Optional[int] = None          # jumlah pot/polybag (jika planting_type pot/polybag)
    days_available: int = 90                    # berapa hari sampai user mau panen
    # --- preferensi ---
    categories: list = field(default_factory=list)  # [] = semua (lihat CATEGORIES)
    purpose: Optional[str] = None               # konsumsi | jual | hias | keduanya
    experience: int = 1                         # 1 pemula, 2 menengah, 3 mahir
    budget_idr: Optional[int] = None            # batas total belanja per komoditas


# ---------------------------------------------------------------------------
# Muat data
# ---------------------------------------------------------------------------

NUM_FIELDS = ["days_min", "days_max", "temp_abs_min", "temp_opt_min", "temp_opt_max", "temp_abs_max",
              "rain_abs_min", "rain_opt_min", "rain_opt_max", "rain_abs_max",
              "ph_abs_min", "ph_opt_min", "ph_opt_max", "ph_abs_max", "alt_min", "alt_max",
              "sun_hours", "seeds_per_m2", "seeds_per_pack", "pack_g", "price_idr", "stock", "difficulty"]
LIST_FIELDS = ["soil_textures", "grow_types", "purpose", "common_pests"]


def load_products(path="products.csv"):
    products = []
    with open(path, newline="", encoding="utf-8-sig") as f:
        for row in csv.DictReader(f):
            for k in NUM_FIELDS:
                row[k] = float(row[k]) if row.get(k) not in (None, "") else None
            for k in LIST_FIELDS:
                row[k] = [x for x in row.get(k, "").split("|") if x]
            products.append(row)
    return products


# ---------------------------------------------------------------------------
# Fungsi bantu
# ---------------------------------------------------------------------------


def trap(x, abs_lo, opt_lo, opt_hi, abs_hi):
    """Kurva trapesium EcoCrop: 0.92-1.0 di rentang optimal (makin dekat tengah makin tinggi),
    turun linear ke 0 di batas absolut."""
    if opt_lo <= x <= opt_hi:
        half = (opt_hi - opt_lo) / 2
        if half <= 0:
            return 1.0
        return 0.92 + 0.08 * (1 - abs(x - (opt_lo + opt_hi) / 2) / half)
    if x < opt_lo:
        return 0.0 if x <= abs_lo else 0.92 * (x - abs_lo) / (opt_lo - abs_lo)
    return 0.0 if x >= abs_hi else 0.92 * (abs_hi - x) / (abs_hi - opt_hi)


def climate_over_period(user, days):
    """Rata-rata suhu & hujan selama masa tanam (kalau user punya data bulanan)."""
    temp, rain = user.temp_avg, user.rain_mm_month
    n = max(1, math.ceil(days / 30))
    idx = [(user.start_month - 1 + i) % 12 for i in range(n)]
    if user.monthly_temp and len(user.monthly_temp) == 12:
        temp = sum(user.monthly_temp[i] for i in idx) / n
    if user.monthly_rain and len(user.monthly_rain) == 12:
        rain = sum(user.monthly_rain[i] for i in idx) / n
    return temp, rain


TEXTURE_NEIGHBORS = {
    "berpasir": {"lempung berpasir"},
    "lempung berpasir": {"berpasir", "lempung"},
    "lempung": {"lempung berpasir", "liat berlempung"},
    "liat berlempung": {"lempung", "liat"},
    "liat": {"liat berlempung"},
}
DRAIN_REQ = {"baik": 2, "sedang": 1, "toleran": 0}      # kebutuhan komoditas
DRAIN_USER = {"baik": 2, "sedang": 1, "buruk": 0}       # kondisi lahan user

WEIGHTS = {"temp": 0.22, "rain": 0.07, "alt": 0.05, "ph": 0.10, "texture": 0.08,
           "drainage": 0.05, "time": 0.18, "sun": 0.05, "pref": 0.12}
RAIN_FLOOR = 0.4    # hujan tidak pernah menggugurkan total (bisa diatasi irigasi/bedengan/naungan)


def seeds_needed(p, user):
    if user.planting_type in ("pot", "polybag") and user.n_containers:
        return user.n_containers * 3 * 1.1          # 3 benih per wadah, lalu disisakan 1-2
    return user.area_m2 * p["seeds_per_m2"] * 1.1   # +10% cadangan


def offers_for(products, need, budget=None):
    """Satu penawaran per brand: ukuran kemasan termurah yang cukup & stoknya ada."""
    best = {}
    for p in products:
        if p["stock"] <= 0:
            continue
        n = max(1, math.ceil(need / p["seeds_per_pack"]))
        if n > p["stock"]:
            continue
        cost = n * p["price_idr"]
        cur = best.get(p["brand"])
        if cur is None or (cost, n) < (cur["total_price_idr"], cur["packs_needed"]):
            best[p["brand"]] = {"brand": p["brand"], "product_id": p["product_id"], "name": p["name"],
                                "pack_g": p["pack_g"], "packs_needed": n, "total_price_idr": int(cost)}
    out = sorted(best.values(), key=lambda o: o["total_price_idr"])
    if budget:
        out = [o for o in out if o["total_price_idr"] <= budget]
    return out


# ---------------------------------------------------------------------------
# Skoring satu komoditas
# ---------------------------------------------------------------------------


def score_commodity(p, u):
    """Return (hasil | None, alasan_dikeluarkan). `p` = salah satu baris produk komoditas itu."""
    days_mid = (p["days_min"] + p["days_max"]) / 2
    temp, rain = climate_over_period(u, days_mid)

    # ---- filter keras ----
    if p["days_min"] > u.days_available:
        return None, f"umur panen {p['days_min']:.0f} hari > waktu tersedia"
    if u.planting_type not in p["grow_types"]:
        return None, f"tidak cocok untuk tipe tanam {u.planting_type}"
    if u.categories and p["category"] not in u.categories:
        return None, "kategori tidak dipilih"
    if u.purpose == "keduanya":
        if not ({"konsumsi", "jual"} & set(p["purpose"])):
            return None, "tujuan tanam tidak sesuai"
    elif u.purpose and u.purpose not in p["purpose"]:
        return None, "tujuan tanam tidak sesuai"
    if u.altitude_m is not None and not (p["alt_min"] - 500 <= u.altitude_m <= p["alt_max"] + 600):
        return None, f"ketinggian {u.altitude_m:.0f} mdpl di luar rentang"
    if temp is not None and not (p["temp_abs_min"] <= temp <= p["temp_abs_max"]):
        return None, f"suhu {temp:.1f}C di luar batas tumbuh"

    comps, pros, warns = {}, [], []

    # ---- suhu ----
    if temp is not None:
        s = trap(temp, p["temp_abs_min"], p["temp_opt_min"], p["temp_opt_max"], p["temp_abs_max"])
        comps["temp"] = s
        if s >= 0.9:
            pros.append(f"suhu {temp:.0f}C sesuai (ideal {p['temp_opt_min']:.0f}-{p['temp_opt_max']:.0f}C)")
        elif s < 0.6:
            warns.append(f"suhu {temp:.0f}C kurang ideal (ideal {p['temp_opt_min']:.0f}-{p['temp_opt_max']:.0f}C)")

    # ---- curah hujan (mm/bulan) ----
    if rain is not None:
        s = trap(rain, p["rain_abs_min"], p["rain_opt_min"], p["rain_opt_max"], p["rain_abs_max"])
        comps["rain"] = RAIN_FLOOR + (1 - RAIN_FLOOR) * s
        if s >= 0.9:
            pros.append(f"curah hujan {rain:.0f} mm/bulan sesuai")
        elif rain > p["rain_opt_max"]:
            warns.append(f"hujan {rain:.0f} mm/bulan di atas ideal (maks {p['rain_opt_max']:.0f}), "
                         "pakai bedengan tinggi atau naungan plastik")
        elif rain < p["rain_opt_min"]:
            warns.append(f"hujan {rain:.0f} mm/bulan di bawah ideal (min {p['rain_opt_min']:.0f}), siapkan penyiraman")

    # ---- ketinggian ----
    if u.altitude_m is not None:
        s = trap(u.altitude_m, p["alt_min"] - 400, p["alt_min"], p["alt_max"], p["alt_max"] + 500)
        comps["alt"] = s
        if s < 0.6:
            warns.append(f"ketinggian {u.altitude_m:.0f} mdpl di tepi rentang "
                         f"({p['alt_min']:.0f}-{p['alt_max']:.0f})")

    # ---- pH ----
    if u.soil_ph is not None:
        s = trap(u.soil_ph, p["ph_abs_min"], p["ph_opt_min"], p["ph_opt_max"], p["ph_abs_max"])
        comps["ph"] = s
        if s >= 0.9:
            pros.append(f"pH {u.soil_ph:.1f} pas ({p['ph_opt_min']:.1f}-{p['ph_opt_max']:.1f})")
        elif u.soil_ph < p["ph_opt_min"]:
            warns.append(f"pH {u.soil_ph:.1f} agak asam (ideal min {p['ph_opt_min']:.1f}), tambah kapur dolomit")
        else:
            warns.append(f"pH {u.soil_ph:.1f} agak basa (ideal maks {p['ph_opt_max']:.1f}), tambah bahan organik")

    # ---- tekstur ----
    if u.soil_texture:
        if u.soil_texture in p["soil_textures"]:
            comps["texture"] = 1.0
            pros.append(f"tanah {u.soil_texture} cocok")
        elif any(u.soil_texture in TEXTURE_NEIGHBORS.get(t, set()) for t in p["soil_textures"]):
            comps["texture"] = 0.6
            warns.append(f"tanah {u.soil_texture} cukup cocok (ideal {'/'.join(p['soil_textures'])})")
        else:
            comps["texture"] = 0.25
            warns.append(f"tanah {u.soil_texture} kurang cocok (ideal {'/'.join(p['soil_textures'])})")

    # ---- drainase ----
    if u.drainage:
        gap = DRAIN_REQ.get(p["drainage"], 1) - DRAIN_USER.get(u.drainage, 1)
        comps["drainage"] = 1.0 if gap <= 0 else max(0.0, 1 - 0.4 * gap)
        if gap > 0:
            warns.append("drainase lahan kurang, buat bedengan tinggi")
        elif p["drainage"] == "toleran" and u.drainage == "buruk":
            pros.append("tahan genangan, cocok untuk lahan basah")

    # ---- waktu / umur panen ----
    dmin, dmax, avail = p["days_min"], p["days_max"], u.days_available
    if dmax <= avail:
        comps["time"] = 1.0
        msg = f"panen ±{dmin:.0f}-{dmax:.0f} hari, muat dalam {avail} hari"
        cycles = int(avail // dmax)
        if cycles >= 2:
            msg += f" (bisa ±{cycles} kali tanam)"
        pros.append(msg)
    else:
        span = max(1.0, dmax - dmin)
        comps["time"] = max(0.4, 1.0 - 0.6 * (dmax - avail) / span)
        warns.append(f"panen bisa sampai {dmax:.0f} hari, mepet dengan {avail} hari")

    # ---- sinar matahari ----
    if u.sun_hours is not None and p["sun_hours"]:
        need = p["sun_hours"]
        comps["sun"] = 1.0 if u.sun_hours >= need - 1 else max(0.0, 1 - (need - 1 - u.sun_hours) / 3)
        if comps["sun"] < 0.7:
            warns.append(f"butuh sinar ±{need:.0f} jam/hari, lahanmu {u.sun_hours:.0f} jam")

    # ---- preferensi: tujuan + pengalaman ----
    if not u.purpose or (p["purpose"] and p["purpose"][0] == u.purpose):
        pref_purpose = 1.0                     # tujuan utama komoditas = tujuan user
    else:
        pref_purpose = 0.85                    # cocok sebagai tujuan sekunder
    gap = p["difficulty"] - u.experience
    pref_exp = 1.0 if gap <= 0 else max(0.0, 1 - 0.5 * gap)
    comps["pref"] = 0.5 * pref_purpose + 0.5 * pref_exp
    if gap > 0:
        warns.append("perawatan relatif menantang untuk level pengalamanmu")
    elif p["difficulty"] == 1:
        pros.append("mudah dirawat")

    wsum = sum(WEIGHTS[k] for k in comps)
    total = sum(WEIGHTS[k] * v for k, v in comps.items()) / wsum
    return {"score": round(total * 100, 1), "components": comps, "pros": pros, "warnings": warns}, None


# ---------------------------------------------------------------------------
# Rekomendasi
# ---------------------------------------------------------------------------


def recommend(products, user, top_n=10, max_per_category=4, min_score=40, debug=False):
    by_commodity = {}
    for p in products:
        by_commodity.setdefault(p["commodity_id"], []).append(p)

    results, excluded = [], {}
    for cid, items in by_commodity.items():
        head = items[0]                                # atribut tumbuh sama di semua brand
        res, why = score_commodity(head, user)
        if res is None:
            excluded[cid] = why
            continue
        if res["score"] < min_score:
            excluded[cid] = f"skor rendah ({res['score']})"
            continue
        offers = offers_for(items, seeds_needed(head, user), user.budget_idr)
        if not offers:
            excluded[cid] = "tidak ada penawaran (stok/budget)"
            continue
        results.append({
            "commodity_id": cid,
            "commodity": head["commodity"],
            "category": head["category"],
            "score": res["score"],
            "days": f"{head['days_min']:.0f}-{head['days_max']:.0f}",
            "pros": res["pros"],
            "warnings": res["warnings"],
            "components": {k: round(v, 2) for k, v in res["components"].items()},
            "offers": offers,                          # termurah dulu
        })

    results.sort(key=lambda r: (-r["score"], r["offers"][0]["total_price_idr"]))
    final, per_cat = [], {}
    for r in results:
        if max_per_category and per_cat.get(r["category"], 0) >= max_per_category:
            continue
        per_cat[r["category"]] = per_cat.get(r["category"], 0) + 1
        final.append(r)
        if len(final) >= top_n:
            break
    return (final, excluded) if debug else final


# ---------------------------------------------------------------------------
# Demo
# ---------------------------------------------------------------------------


def show(title, user, products, top_n=6):
    print(f"\n=== {title} ===")
    for i, r in enumerate(recommend(products, user, top_n=top_n), 1):
        o = r["offers"][0]
        print(f"{i}. [{r['score']}] {r['commodity']}  ({r['category']}, panen {r['days']} hari)")
        print(f"   termurah: {o['brand']} {o['packs_needed']} x {o['pack_g']:g} g = Rp{o['total_price_idr']:,}"
              f"   | {len(r['offers'])} brand tersedia")
        for t in r["pros"][:2]:
            print(f"   + {t}")
        for t in r["warnings"][:2]:
            print(f"   ! {t}")


if __name__ == "__main__":
    products = load_products("products.csv")
    print(f"Dataset: {len(products)} produk, {len({p['commodity_id'] for p in products})} komoditas")

    show("Kebun dataran menengah, 40 m2, pemula, mau panen < 75 hari", UserProfile(
        temp_avg=24, rain_mm_month=190, altitude_m=700, soil_texture="lempung", soil_ph=6.3,
        drainage="baik", sun_hours=7, area_m2=40, planting_type="lahan", days_available=75,
        purpose="konsumsi", experience=1, budget_idr=300_000), products)

    show("Pekarangan dataran rendah, 8 pot, tanah liat, hujan tinggi", UserProfile(
        temp_avg=29, rain_mm_month=300, altitude_m=20, soil_texture="liat berlempung", drainage="buruk",
        sun_hours=6, planting_type="pot", n_containers=8, days_available=60, experience=1), products)

    show("Dataran tinggi sejuk, 100 m2, tujuan jual, 4 bulan", UserProfile(
        temp_avg=17, rain_mm_month=220, altitude_m=1300, soil_texture="lempung", soil_ph=6.0,
        drainage="baik", sun_hours=6, area_m2=100, planting_type="lahan", days_available=120,
        purpose="jual", experience=2), products)
