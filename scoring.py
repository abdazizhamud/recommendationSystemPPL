"""
Rekomendasi benih berbasis aturan (rule-based).

Alur:
  1. Filter keras  -> produk yang pasti tidak cocok dibuang (umur panen, ketinggian, suhu,
                      tipe tanam, kategori, stok, budget).
  2. Skor 0-100    -> kecocokan iklim, tanah, waktu, sinar matahari, preferensi.
  3. Kebutuhan     -> berapa kemasan yang harus dibeli untuk luas lahan user.
  4. Penjelasan    -> alasan positif & peringatan per rekomendasi.

Pakai:
    from scoring import UserProfile, load_products, recommend
    products = load_products("products.csv")
    user = UserProfile(temp_avg=24, rain_mm_month=180, altitude_m=700, soil_texture="lempung",
                       soil_ph=6.3, area_m2=40, planting_type="lahan", days_available=90)
    for r in recommend(products, user, top_n=10):
        print(r["score"], r["name"], r["packs_needed"], r["total_price_idr"])
"""
import csv
import math
from dataclasses import dataclass, field
from typing import Optional

# ---------------------------------------------------------------------------
# Input user
# ---------------------------------------------------------------------------


@dataclass
class UserProfile:
    # --- iklim (isi salah satu: nilai tunggal, atau 12 nilai bulanan + start_month) ---
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
    categories: list = field(default_factory=list)  # [] = semua
    purpose: Optional[str] = None               # konsumsi | jual | hias | keduanya
    experience: int = 1                         # 1 pemula, 2 menengah, 3 mahir
    budget_idr: Optional[int] = None            # batas total belanja


# ---------------------------------------------------------------------------
# Muat data
# ---------------------------------------------------------------------------

NUM_FIELDS = ["days_min", "days_max", "temp_min", "temp_max", "alt_min", "alt_max",
              "rain_min_mm_month", "rain_max_mm_month", "ph_min", "ph_max", "sun_hours",
              "seeds_per_m2", "pack_g", "seeds_per_pack", "price_idr", "stock", "difficulty"]


def load_products(path="products.csv"):
    products = []
    with open(path, newline="", encoding="utf-8-sig") as f:
        for row in csv.DictReader(f):
            for k in NUM_FIELDS:
                row[k] = float(row[k]) if row.get(k) not in (None, "") else None
            for k in ("soil_textures", "grow_types", "purpose", "pest_resistance", "tags"):
                row[k] = [x for x in row.get(k, "").split("|") if x]
            products.append(row)
    return products


# ---------------------------------------------------------------------------
# Fungsi bantu
# ---------------------------------------------------------------------------


def trap(x, abs_lo, opt_lo, opt_hi, abs_hi):
    """Skor trapesium: 1 di rentang optimal, turun linear ke 0 di batas absolut."""
    if opt_lo <= x <= opt_hi:
        # di dalam rentang optimal: 0.92-1.0, makin dekat tengah makin tinggi (hindari skor kembar)
        half = (opt_hi - opt_lo) / 2
        if half <= 0:
            return 1.0
        return 0.92 + 0.08 * (1 - abs(x - (opt_lo + opt_hi) / 2) / half)
    if x < opt_lo:
        return 0.0 if x <= abs_lo else (x - abs_lo) / (opt_lo - abs_lo)
    return 0.0 if x >= abs_hi else (abs_hi - x) / (abs_hi - opt_hi)


def climate_over_period(user, days):
    """Rata-rata suhu & hujan selama masa tanam produk (kalau ada data bulanan)."""
    temp, rain = user.temp_avg, user.rain_mm_month
    n = max(1, math.ceil(days / 30))
    if user.monthly_temp and len(user.monthly_temp) == 12:
        idx = [(user.start_month - 1 + i) % 12 for i in range(n)]
        temp = sum(user.monthly_temp[i] for i in idx) / n
    if user.monthly_rain and len(user.monthly_rain) == 12:
        idx = [(user.start_month - 1 + i) % 12 for i in range(n)]
        rain = sum(user.monthly_rain[i] for i in idx) / n
    return temp, rain


TEXTURE_NEIGHBORS = {
    "berpasir": {"lempung berpasir"},
    "lempung berpasir": {"berpasir", "lempung"},
    "lempung": {"lempung berpasir", "liat berlempung"},
    "liat berlempung": {"lempung", "liat"},
    "liat": {"liat berlempung"},
}
DRAIN_REQ = {"baik": 2, "sedang": 1, "toleran": 0}      # kebutuhan produk
DRAIN_USER = {"baik": 2, "sedang": 1, "buruk": 0}       # kondisi lahan user

WEIGHTS = {"temp": 0.20, "rain": 0.12, "alt": 0.10, "ph": 0.10, "texture": 0.10,
           "drainage": 0.05, "time": 0.15, "sun": 0.05, "pref": 0.13}


def seeds_needed(p, user):
    if user.planting_type in ("pot", "polybag") and user.n_containers:
        return user.n_containers * 3        # asumsi 3 benih per wadah (lalu disisakan 1-2)
    return user.area_m2 * p["seeds_per_m2"]


def best_pack_for_variety(packs, need):
    """Pilih ukuran kemasan termurah untuk memenuhi kebutuhan benih."""
    best = None
    for p in packs:
        if p["stock"] <= 0:
            continue
        n = max(1, math.ceil(need / p["seeds_per_pack"]))
        if n > p["stock"]:
            continue
        cost = n * p["price_idr"]
        key = (cost, n)
        if best is None or key < best[0]:
            best = (key, p, n, cost)
    return best


# ---------------------------------------------------------------------------
# Skoring satu produk
# ---------------------------------------------------------------------------


def score_product(p, u):
    """Return (hasil | None, alasan_dikeluarkan)."""
    days_mid = (p["days_min"] + p["days_max"]) / 2
    temp, rain = climate_over_period(u, days_mid)

    # ---- filter keras ----
    if p["days_min"] > u.days_available:
        return None, f"umur panen {int(p['days_min'])} hari > waktu tersedia"
    if u.planting_type not in p["grow_types"]:
        return None, f"tidak cocok untuk tipe tanam {u.planting_type}"
    if u.categories and p["category"] not in u.categories:
        return None, "kategori tidak dipilih"
    if u.purpose and u.purpose not in p["purpose"] and not (u.purpose == "keduanya" and p["purpose"]):
        return None, "tujuan tanam tidak sesuai"
    if u.altitude_m is not None and not (p["alt_min"] - 200 <= u.altitude_m <= p["alt_max"] + 200):
        return None, f"ketinggian {u.altitude_m:.0f} mdpl di luar rentang"
    if temp is not None and not (p["temp_min"] - 6 < temp < p["temp_max"] + 6):
        return None, f"suhu {temp:.1f}C terlalu jauh dari rentang"

    comps, notes_ok, notes_warn = {}, [], []

    # ---- suhu ----
    if temp is not None:
        s = trap(temp, p["temp_min"] - 6, p["temp_min"], p["temp_max"], p["temp_max"] + 6)
        comps["temp"] = s
        if s >= 0.9:
            notes_ok.append(f"suhu {temp:.0f}C sesuai (ideal {p['temp_min']:.0f}-{p['temp_max']:.0f}C)")
        elif s < 0.6:
            notes_warn.append(f"suhu {temp:.0f}C kurang ideal ({p['temp_min']:.0f}-{p['temp_max']:.0f}C)")

    # ---- curah hujan ----
    if rain is not None:
        lo, hi = p["rain_min_mm_month"], p["rain_max_mm_month"]
        s = trap(rain, lo * 0.4, lo, hi, hi * 1.6)
        comps["rain"] = s
        if s >= 0.9:
            notes_ok.append(f"curah hujan {rain:.0f} mm/bulan sesuai")
        elif rain < lo:
            notes_warn.append(f"hujan {rain:.0f} mm/bulan agak kering, siapkan penyiraman")
        elif rain > hi:
            notes_warn.append(f"hujan {rain:.0f} mm/bulan agak tinggi, pastikan drainase / naungan plastik")

    # ---- ketinggian ----
    if u.altitude_m is not None:
        s = trap(u.altitude_m, p["alt_min"] - 300, p["alt_min"], p["alt_max"], p["alt_max"] + 300)
        comps["alt"] = s
        if s >= 0.9:
            notes_ok.append(f"cocok di ketinggian {u.altitude_m:.0f} mdpl")
        elif s < 0.6:
            notes_warn.append(f"ketinggian {u.altitude_m:.0f} mdpl di tepi rentang ({int(p['alt_min'])}-{int(p['alt_max'])})")

    # ---- pH ----
    if u.soil_ph is not None:
        s = trap(u.soil_ph, p["ph_min"] - 1.2, p["ph_min"], p["ph_max"], p["ph_max"] + 1.2)
        comps["ph"] = s
        if s >= 0.9:
            notes_ok.append(f"pH {u.soil_ph:.1f} pas ({p['ph_min']}-{p['ph_max']})")
        elif u.soil_ph < p["ph_min"]:
            notes_warn.append(f"pH {u.soil_ph:.1f} agak asam, tambah kapur dolomit")
        else:
            notes_warn.append(f"pH {u.soil_ph:.1f} agak basa, tambah bahan organik")

    # ---- tekstur ----
    if u.soil_texture:
        if u.soil_texture in p["soil_textures"]:
            comps["texture"] = 1.0
            notes_ok.append(f"tanah {u.soil_texture} cocok")
        elif any(u.soil_texture in TEXTURE_NEIGHBORS.get(t, set()) for t in p["soil_textures"]):
            comps["texture"] = 0.6
            notes_warn.append(f"tanah {u.soil_texture} cukup cocok, ideal {'/'.join(p['soil_textures'])}")
        else:
            comps["texture"] = 0.25
            notes_warn.append(f"tanah {u.soil_texture} kurang cocok, ideal {'/'.join(p['soil_textures'])}")

    # ---- drainase ----
    if u.drainage:
        gap = DRAIN_REQ.get(p["drainage"], 1) - DRAIN_USER.get(u.drainage, 1)
        comps["drainage"] = 1.0 if gap <= 0 else max(0.0, 1 - 0.4 * gap)
        if gap > 0:
            notes_warn.append("drainase lahan kurang, buat bedengan tinggi")

    # ---- waktu / umur panen ----
    if p["days_max"] <= u.days_available:
        comps["time"] = 1.0
        spare = u.days_available - p["days_max"]
        notes_ok.append(f"panen ±{int(p['days_min'])}-{int(p['days_max'])} hari, muat dalam {u.days_available} hari"
                        + (f" (sisa {int(spare)} hari)" if spare >= 7 else ""))
    else:
        rng_ = max(1.0, p["days_max"] - p["days_min"])
        comps["time"] = 0.5 + 0.5 * (u.days_available - p["days_min"]) / rng_ * 0.8
        comps["time"] = min(0.9, max(0.3, comps["time"]))
        notes_warn.append(f"panen bisa sampai {int(p['days_max'])} hari, mepet dengan {u.days_available} hari")

    # ---- sinar matahari ----
    if u.sun_hours is not None and p["sun_hours"]:
        need = p["sun_hours"]
        comps["sun"] = 1.0 if u.sun_hours >= need - 1 else max(0.0, 1 - (need - 1 - u.sun_hours) / 3)
        if comps["sun"] < 0.7:
            notes_warn.append(f"butuh sinar ±{need:.0f} jam/hari, lahanmu {u.sun_hours:.0f} jam")

    # ---- preferensi ----
    pref = 0.0
    pref += 0.5 if (not u.purpose or u.purpose in p["purpose"] or u.purpose == "keduanya") else 0.0
    gap = p["difficulty"] - u.experience
    pref += 0.5 * (1.0 if gap <= 0 else max(0.0, 1 - 0.5 * gap))
    comps["pref"] = pref
    if gap > 0:
        notes_warn.append("perawatan relatif menantang untuk level pengalamanmu")
    elif p["difficulty"] == 1:
        notes_ok.append("mudah dirawat")

    # ---- gabung skor (bobot dinormalisasi untuk input yang kosong) ----
    wsum = sum(WEIGHTS[k] for k in comps)
    total = sum(WEIGHTS[k] * v for k, v in comps.items()) / wsum
    return {"score": round(total * 100, 1), "components": comps,
            "pros": notes_ok, "warnings": notes_warn}, None


# ---------------------------------------------------------------------------
# Rekomendasi
# ---------------------------------------------------------------------------


def recommend(products, user, top_n=10, max_per_commodity=2, min_score=40, debug=False):
    # kelompokkan produk per varietas (satu varietas bisa punya beberapa ukuran kemasan)
    by_variety = {}
    for p in products:
        by_variety.setdefault(p["variety_id"], []).append(p)

    results, excluded = [], {}
    for vid, packs in by_variety.items():
        res, why = score_product(packs[0], user)       # atribut tumbuh sama di semua kemasan
        if res is None:
            excluded[vid] = (packs[0]["name"], why)
            continue
        if res["score"] < min_score:
            continue
        pack = best_pack_for_variety(packs, seeds_needed(packs[0], user))
        if pack is None:
            excluded[vid] = (packs[0]["name"], "stok tidak cukup")
            continue
        _, chosen, n_packs, cost = pack
        if user.budget_idr and cost > user.budget_idr:
            excluded[vid] = (chosen["name"], "melebihi budget")
            continue
        results.append({
            "score": res["score"],
            "commodity": chosen["commodity"],
            "variety": chosen["variety"],
            "brand": chosen["brand"],
            "product_id": chosen["product_id"],
            "name": chosen["name"],
            "pack_g": chosen["pack_g"],
            "packs_needed": n_packs,
            "total_price_idr": int(cost),
            "days": f"{int(chosen['days_min'])}-{int(chosen['days_max'])}",
            "pros": res["pros"],
            "warnings": res["warnings"],
            "components": {k: round(v, 2) for k, v in res["components"].items()},
        })

    # urut skor, batasi jumlah per komoditas supaya hasil beragam
    results.sort(key=lambda r: (-r["score"], r["total_price_idr"]))
    final, count = [], {}
    for r in results:
        if count.get(r["commodity"], 0) >= max_per_commodity:
            continue
        count[r["commodity"]] = count.get(r["commodity"], 0) + 1
        final.append(r)
        if len(final) >= top_n:
            break
    return (final, excluded) if debug else final


# ---------------------------------------------------------------------------
# Demo
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    products = load_products("products.csv")

    demo = UserProfile(
        temp_avg=24, rain_mm_month=190, altitude_m=700,
        soil_texture="lempung", soil_ph=6.3, drainage="baik", sun_hours=7,
        area_m2=40, planting_type="lahan", days_available=75,
        purpose="konsumsi", experience=1, budget_idr=300_000,
    )
    print(f"Dataset: {len(products)} produk\n")
    for i, r in enumerate(recommend(products, demo, top_n=8), 1):
        print(f"{i}. [{r['score']}] {r['name']}  | {r['brand']}")
        print(f"   beli {r['packs_needed']} x {r['pack_g']:.0f} g = Rp{r['total_price_idr']:,}  (panen {r['days']} hari)")
        for t in r["pros"][:3]:
            print(f"   + {t}")
        for t in r["warnings"][:2]:
            print(f"   ! {t}")
