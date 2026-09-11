"""
Cargador de datos via Kaggle API — descarga automatica y transformacion
Dataset: syednaveed05/logistics-fleet-data
Autor: Eider
"""

import pandas as pd
import numpy as np
import os
import zipfile
import json

DATA_PATH = "../data"
DATASET_ID = "syednaveed05/logistics-fleet-data"

# ── Coordenadas ciudades ──────────────────────────────────────────────
CITY_COORDS = {
    "New York":      {"lat": 40.7128,  "lon": -74.0060,  "region": "Northeast"},
    "Los Angeles":   {"lat": 34.0522,  "lon": -118.2437, "region": "West"},
    "Chicago":       {"lat": 41.8781,  "lon": -87.6298,  "region": "Midwest"},
    "Houston":       {"lat": 29.7604,  "lon": -95.3698,  "region": "South"},
    "Phoenix":       {"lat": 33.4484,  "lon": -112.0740, "region": "West"},
    "Philadelphia":  {"lat": 39.9526,  "lon": -75.1652,  "region": "Northeast"},
    "San Antonio":   {"lat": 29.4241,  "lon": -98.4936,  "region": "South"},
    "San Diego":     {"lat": 32.7157,  "lon": -117.1611, "region": "West"},
    "Dallas":        {"lat": 32.7767,  "lon": -96.7970,  "region": "South"},
    "San Jose":      {"lat": 37.3382,  "lon": -121.8863, "region": "West"},
    "Austin":        {"lat": 30.2672,  "lon": -97.7431,  "region": "South"},
    "Jacksonville":  {"lat": 30.3322,  "lon": -81.6557,  "region": "Southeast"},
    "Fort Worth":    {"lat": 32.7555,  "lon": -97.3308,  "region": "South"},
    "Columbus":      {"lat": 39.9612,  "lon": -82.9988,  "region": "Midwest"},
    "Charlotte":     {"lat": 35.2271,  "lon": -80.8431,  "region": "Southeast"},
    "Indianapolis":  {"lat": 39.7684,  "lon": -86.1581,  "region": "Midwest"},
    "San Francisco": {"lat": 37.7749,  "lon": -122.4194, "region": "West"},
    "Seattle":       {"lat": 47.6062,  "lon": -122.3321, "region": "West"},
    "Denver":        {"lat": 39.7392,  "lon": -104.9903, "region": "West"},
    "Nashville":     {"lat": 36.1627,  "lon": -86.7816,  "region": "Southeast"},
}

CEDIS_CONFIG = {
    "HUB-EAST":  {"nombre": "Hub Este",   "ciudad": "New York",    "region": "Northeast"},
    "HUB-SOUTH": {"nombre": "Hub Sur",    "ciudad": "Houston",     "region": "South"},
    "HUB-WEST":  {"nombre": "Hub Oeste",  "ciudad": "Los Angeles", "region": "West"},
    "HUB-MID":   {"nombre": "Hub Centro", "ciudad": "Chicago",     "region": "Midwest"},
}

VEHICULOS = [
    {"tipo": "Moto mensajeria", "cap_peso_kg": 15,   "cap_vol_m3": 0.06,  "costo_km": 200},
    {"tipo": "Van pequena",     "cap_peso_kg": 40,   "cap_vol_m3": 0.16,  "costo_km": 450},
    {"tipo": "Furgon 150kg",    "cap_peso_kg": 150,  "cap_vol_m3": 0.60,  "costo_km": 800},
    {"tipo": "Camion 500kg",    "cap_peso_kg": 500,  "cap_vol_m3": 2.0,   "costo_km": 1400},
]

TRANSPORTADORAS = [
    {"nombre": "FedEx Freight",  "factor_tarifa": 1.10, "cobertura": ["Northeast","Southeast","Midwest","South","West"]},
    {"nombre": "UPS Freight",    "factor_tarifa": 1.00, "cobertura": ["Northeast","Midwest","South","West"]},
    {"nombre": "XPO Logistics",  "factor_tarifa": 0.90, "cobertura": ["South","West","Southeast"]},
    {"nombre": "Old Dominion",   "factor_tarifa": 0.85, "cobertura": ["Northeast","Southeast","Midwest"]},
]


def haversine(lat1, lon1, lat2, lon2):
    R = 6371
    phi1, phi2 = np.radians(lat1), np.radians(lat2)
    a = (np.sin((phi2-phi1)/2)**2 +
         np.cos(phi1)*np.cos(phi2)*np.sin(np.radians((lon2-lon1))/2)**2)
    return 2 * R * np.arcsin(np.sqrt(a))


# ── Descarga via Kaggle API ───────────────────────────────────────────

def _check_kaggle_credentials():
    import os
    # Intentar desde Streamlit secrets
    try:
        import streamlit as st
        os.environ["KAGGLE_USERNAME"] = st.secrets["KAGGLE_USERNAME"]
        os.environ["KAGGLE_KEY"]      = st.secrets["KAGGLE_KEY"]
        return
    except Exception:
        pass

    # Intentar desde variables de entorno
    if os.environ.get("KAGGLE_USERNAME") and os.environ.get("KAGGLE_KEY"):
        return

    # Intentar desde archivo local
    kaggle_json = os.path.expanduser("~/.kaggle/kaggle.json")
    if os.path.exists(kaggle_json):
        try:
            os.chmod(kaggle_json, 0o600)
        except Exception:
            pass
        return

    raise FileNotFoundError(
        "Credenciales de Kaggle no encontradas.\n"
        "Agrega KAGGLE_USERNAME y KAGGLE_KEY en Streamlit Secrets."
    )


def download_dataset(force=False):
    """
    Descarga el dataset via Kaggle API si no existe localmente.
    Retorna lista de archivos CSV descargados.
    """
    os.makedirs(DATA_PATH, exist_ok=True)
    csv_files = [f for f in os.listdir(DATA_PATH) if f.endswith(".csv")]

    if csv_files and not force:
        print(f"Dataset ya disponible: {csv_files}")
        return [os.path.join(DATA_PATH, f) for f in csv_files]

    print(f"Descargando dataset: {DATASET_ID}")
    _check_kaggle_credentials()

    try:
        from kaggle.api.kaggle_api_extended import KaggleApi
        api = KaggleApi()
        api.authenticate()
        api.dataset_download_files(DATASET_ID, path=DATA_PATH, unzip=True, quiet=False)
        print("Descarga completada.")
    except ImportError:
        raise ImportError("Instala kaggle: pip install kaggle")

    # Descomprimir zips residuales
    for f in os.listdir(DATA_PATH):
        if f.endswith(".zip"):
            with zipfile.ZipFile(os.path.join(DATA_PATH, f), "r") as z:
                z.extractall(DATA_PATH)
            os.remove(os.path.join(DATA_PATH, f))

    csv_files = [f for f in os.listdir(DATA_PATH) if f.endswith(".csv")]
    print(f"Archivos disponibles: {csv_files}")
    return [os.path.join(DATA_PATH, f) for f in csv_files]


# ── Transformaciones ──────────────────────────────────────────────────

def _normalize_columns(df):
    """Normaliza nombres de columnas."""
    df.columns = (df.columns.str.strip()
                             .str.lower()
                             .str.replace(r"[\s\(\)\/]", "_", regex=True)
                             .str.replace(r"_+", "_", regex=True)
                             .str.strip("_"))
    return df


def _find_column(df, keywords):
    """Encuentra la primera columna que coincida con alguna keyword."""
    for kw in keywords:
        col = next((c for c in df.columns if kw in c), None)
        if col:
            return col
    return None


def _assign_city(value, known_cities, rng):
    """Asigna ciudad conocida o aleatoria."""
    if isinstance(value, str):
        # Busqueda exacta
        if value in known_cities:
            return value
        # Busqueda parcial
        match = next((c for c in known_cities if c.lower() in value.lower()), None)
        if match:
            return match
    return rng.choice(known_cities)


def _assign_cedi(ciudad):
    region = CITY_COORDS.get(ciudad, {}).get("region", "Midwest")
    return {"Northeast":"HUB-EAST","Southeast":"HUB-EAST",
            "South":"HUB-SOUTH","West":"HUB-WEST","Midwest":"HUB-MID"}.get(region, "HUB-MID")


def transform_freight(df_raw, rng):
    """Transforma freight data al esquema estandar del VRP."""
    df = _normalize_columns(df_raw.copy())

    # Identificar columnas clave
    weight_col  = _find_column(df, ["weight_kg","weight","kg","peso"])
    volume_col  = _find_column(df, ["cubic","vol","m3","volumen"])
    city_col    = _find_column(df, ["city","ciudad","destination","dest"])
    customer_col = _find_column(df, ["customer","cliente","client","id"])
    revenue_col = _find_column(df, ["revenue","net_revenue","ingreso","value","goods"])
    date_col    = _find_column(df, ["date","fecha"])

    print(f"Columnas detectadas: peso={weight_col}, vol={volume_col}, "
          f"ciudad={city_col}, cliente={customer_col}, revenue={revenue_col}")

    # Peso
    if weight_col:
        df["peso_kg"] = pd.to_numeric(df[weight_col], errors="coerce").abs()
    else:
        df["peso_kg"] = rng.uniform(200, 5000, len(df))

    # Volumen
    if volume_col:
        df["vol_m3"] = pd.to_numeric(df[volume_col], errors="coerce").abs()
    else:
        df["vol_m3"] = df["peso_kg"] * rng.uniform(0.002, 0.005, len(df))

    # Rellenar nulos de volumen con estimacion
    mask_vol = df["vol_m3"].isna() | (df["vol_m3"] == 0)
    df.loc[mask_vol, "vol_m3"] = df.loc[mask_vol, "peso_kg"] * 0.003

    # Revenue
    if revenue_col:
        df["revenue"] = pd.to_numeric(df[revenue_col], errors="coerce").abs()
        df["revenue"].fillna(df["peso_kg"] * 0.15, inplace=True)
    else:
        df["revenue"] = df["peso_kg"] * rng.uniform(0.10, 0.25, len(df))

    # Ciudad destino
    known = list(CITY_COORDS.keys())
    if city_col:
        df["ciudad_destino"] = df[city_col].apply(lambda x: _assign_city(x, known, rng))
    else:
        df["ciudad_destino"] = rng.choice(known, len(df))

    # Cliente
    if customer_col:
        df["cliente_id"] = df[customer_col].astype(str).str[:20]
    else:
        df["cliente_id"] = [f"CLI{i:05d}" for i in range(len(df))]

    # Fecha
    if date_col:
        df["fecha"] = pd.to_datetime(df[date_col], errors="coerce")
    else:
        df["fecha"] = pd.NaT

    # CEDI asignado
    df["cedi_id"] = df["ciudad_destino"].apply(_assign_cedi)
    df["orden_id"] = [f"ORD{i:05d}" for i in range(len(df))]

    # Filtros de calidad
    df = df[df["peso_kg"] > 0].copy()
    df = df[df["vol_m3"] > 0].copy()
    df = df[df["peso_kg"] < 25000].copy()  # eliminar outliers extremos

    result = df[["orden_id","cliente_id","ciudad_destino","cedi_id",
                 "peso_kg","vol_m3","revenue","fecha"]].reset_index(drop=True)

    print(f"Registros transformados: {len(result)}")
    print(f"Peso promedio: {result['peso_kg'].mean():.1f} kg")
    print(f"Revenue promedio: ${result['revenue'].mean():,.0f}")
    return result


def transform_costs(df_raw):
    """Transforma cost data para calibrar tarifas reales."""
    df = _normalize_columns(df_raw.copy())
    km_col   = _find_column(df, ["km","distance","dist"])
    fuel_col = _find_column(df, ["fuel","combustible","liter"])
    maint_col = _find_column(df, ["maintenance","mantenimiento"])

    if km_col and fuel_col:
        df[km_col]   = pd.to_numeric(df[km_col],   errors="coerce")
        df[fuel_col] = pd.to_numeric(df[fuel_col], errors="coerce")
        df = df[(df[km_col] > 0) & (df[fuel_col] > 0)]
        costo_km_real = (df[fuel_col].sum() / df[km_col].sum()) * 3.5  # USD/km estimado
        print(f"Costo/km calibrado desde datos reales: {costo_km_real:.2f} USD/km")
        return {"costo_km_real": round(costo_km_real, 2), "registros": len(df)}
    return {}


def load_freight_data(force_download=False):
    """
    Pipeline completo:
    1. Descarga via Kaggle API
    2. Identifica archivos freight y cost
    3. Transforma al esquema VRP
    4. Retorna DataFrame estandarizado
    """
    rng = np.random.default_rng(42)
    csv_paths = download_dataset(force=force_download)

    # Clasificar archivos
    freight_paths = [p for p in csv_paths if "freight" in p.lower() or "cargo" in p.lower()]
    cost_paths    = [p for p in csv_paths if "cost" in p.lower()]

    if not freight_paths:
        # Usar el archivo mas grande como freight
        freight_paths = sorted(csv_paths, key=os.path.getsize, reverse=True)[:1]

    print(f"\nArchivo freight: {freight_paths[0]}")
    df_raw = pd.read_csv(freight_paths[0])
    print(f"Shape raw: {df_raw.shape}")
    print(f"Columnas raw: {list(df_raw.columns)}")

    df = transform_freight(df_raw, rng)

    # Calibrar costos si hay cost data
    if cost_paths:
        print(f"\nArchivo costos: {cost_paths[0]}")
        df_cost = pd.read_csv(cost_paths[0])
        cost_stats = transform_costs(df_cost)
        df.attrs["cost_stats"] = cost_stats

    df.to_csv(os.path.join(DATA_PATH, "freight_transformed.csv"), index=False)
    print(f"\nDataset transformado guardado: freight_transformed.csv")
    return df


def build_scenario(df_freight, n_orders=50, seed=42):
    """Construye el escenario VRP desde el DataFrame transformado."""
    rng = np.random.default_rng(seed)
    sample = df_freight.sample(
        min(n_orders, len(df_freight)), random_state=seed
    ).reset_index(drop=True)

    cedis = [
        {**{"id": cid}, **cfg,
         "lat": CITY_COORDS[cfg["ciudad"]]["lat"],
         "lon": CITY_COORDS[cfg["ciudad"]]["lon"]}
        for cid, cfg in CEDIS_CONFIG.items()
    ]

    clientes = []
    for _, row in sample.iterrows():
        ciudad = row["ciudad_destino"]
        coords = CITY_COORDS.get(ciudad, {"lat": 39.5, "lon": -98.0})

        # Ajuste: clipear pesos para que sean consolidables en vehiculos medianos
        peso_kg = float(np.clip(row["peso_kg"], 1, 60))
        vol_m3  = float(np.clip(row["vol_m3"],  0.004, 0.24))

        clientes.append({
            "id":            row["orden_id"],
            "cliente_id":    str(row["cliente_id"]),
            "ciudad":        ciudad,
            "region":        CITY_COORDS.get(ciudad, {}).get("region", "Midwest"),
            "lat":           coords["lat"] + rng.uniform(-0.3, 0.3),
            "lon":           coords["lon"] + rng.uniform(-0.3, 0.3),
            "cedi_asignado": row["cedi_id"],
            "peso_kg":       peso_kg,
            "vol_m3":        vol_m3,
            "revenue":       float(row["revenue"]),
        })

    ordenes = [
        {"orden_id": c["id"], "cliente_id": c["cliente_id"],
         "cedi_id": c["cedi_asignado"], "peso_kg": c["peso_kg"],
         "vol_m3": c["vol_m3"], "productos": {"Carga General": 1}}
        for c in clientes
    ]

    cedis_dict    = {c["id"]: c for c in cedis}
    clientes_dict = {c["id"]: c for c in clientes}

    return {
        "cedis": cedis, "clientes": clientes,
        "vehiculos": VEHICULOS, "transportadoras": TRANSPORTADORAS,
        "productos": [{"sku":"GEN","nombre":"Carga General","peso_kg":1.0,"vol_m3":0.003}],
        "ordenes": ordenes,
        "cedis_dict": cedis_dict, "clientes_dict": clientes_dict,
        "productos_dict": {"GEN": {"sku":"GEN","nombre":"Carga General","peso_kg":1.0,"vol_m3":0.003}},
        "df_freight": sample,
    }


if __name__ == "__main__":
    df = load_freight_data()
    print(df.head())
    scenario = build_scenario(df, n_orders=50)
    print(f"Escenario: {len(scenario['ordenes'])} ordenes")