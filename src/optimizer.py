"""
Motor VRP — Consolidacion por ciudad, maxima ocupacion, 100% demanda atendida
Regla: max 4 clientes por viaje, misma ciudad, respeta capacidad vehiculo
Autor: Eider
"""

import numpy as np
from data_loader import haversine, VEHICULOS, TRANSPORTADORAS


def calcular_distancia(origen, destino):
    return haversine(origen["lat"], origen["lon"], destino["lat"], destino["lon"])


def seleccionar_transportadora(region):
    validas = [t for t in TRANSPORTADORAS if region in t["cobertura"]]
    return min(validas if validas else TRANSPORTADORAS, key=lambda t: t["factor_tarifa"])


def seleccionar_vehiculo(peso_kg, vol_m3):
    validos = sorted(
        [v for v in VEHICULOS if v["cap_peso_kg"] >= peso_kg and v["cap_vol_m3"] >= vol_m3],
        key=lambda v: v["cap_peso_kg"]  # el mas pequeno que quepa
    )
    return validos[0] if validos else VEHICULOS[-1]


def calcular_costo_viaje(distancia_km, vehiculo, transportadora, factor_costo=1.0):
    return round(distancia_km * vehiculo["costo_km"] * transportadora["factor_tarifa"] * factor_costo, 2)


def optimizar_escenario(scenario, params=None):
    """
    Logica de optimizacion:
    1. Agrupar ordenes por CEDI mas cercano al cliente
    2. Dentro de cada CEDI, agrupar por ciudad destino
    3. Dentro de cada ciudad, consolidar hasta 4 clientes por viaje
       respetando capacidad de peso y volumen
    4. Seleccionar vehiculo mas economico que cumpla la carga consolidada
    5. Seleccionar transportadora de menor tarifa con cobertura en la region
    6. Garantizar 100% demanda atendida
    7. Viajes con ocupacion < 80% marcados como 'paqueteo'
    """
    if params is None:
        params = {}

    factor_costo = params.get("factor_costo", 1.0)
    max_clientes_viaje = params.get("max_clientes_viaje", 4)
    ocup_minima_pct    = params.get("ocup_minima_pct", 80.0)

    cedis_dict    = scenario["cedis_dict"]
    clientes_dict = scenario["clientes_dict"]
    ordenes       = scenario["ordenes"]

    # ── Paso 1: Reasignar cada orden al CEDI mas cercano ─────────────
    def cedi_mas_cercano(cliente):
        return min(
            cedis_dict.keys(),
            key=lambda cid: calcular_distancia(cedis_dict[cid], cliente)
        )

    for orden in ordenes:
        cliente = clientes_dict[orden["orden_id"]]
        orden["cedi_id"] = cedi_mas_cercano(cliente)

    # ── Paso 2: Agrupar por CEDI y ciudad destino ────────────────────
    grupos = {}  # (cedi_id, ciudad) -> [ordenes]
    for orden in ordenes:
        cliente = clientes_dict[orden["orden_id"]]
        key = (orden["cedi_id"], cliente["ciudad"])
        grupos.setdefault(key, []).append(orden)

    viajes    = []
    viaje_id  = 1
    paqueteo  = []

    for (cedi_id, ciudad), ordenes_grupo in grupos.items():
        cedi   = cedis_dict[cedi_id]
        region = cedi.get("region", "Midwest")
        trans  = seleccionar_transportadora(region)

        # ── Paso 3: Consolidar por First Fit Decreasing ──────────────
        pendientes = sorted(ordenes_grupo, key=lambda o: o["peso_kg"], reverse=True)

        while pendientes:
            carga    = []
            peso_act = 0.0
            vol_act  = 0.0
            no_caben = []

            for orden in pendientes:
                if (len(carga) < max_clientes_viaje and
                    peso_act + orden["peso_kg"] <= max(v["cap_peso_kg"] for v in VEHICULOS) and
                    vol_act  + orden["vol_m3"]  <= max(v["cap_vol_m3"]  for v in VEHICULOS)):
                    carga.append(orden)
                    peso_act += orden["peso_kg"]
                    vol_act  += orden["vol_m3"]
                else:
                    no_caben.append(orden)

            if not carga:
                # Fuerza mayor: orden que excede cualquier vehiculo — viaje individual
                carga    = [pendientes[0]]
                peso_act = pendientes[0]["peso_kg"]
                vol_act  = pendientes[0]["vol_m3"]
                no_caben = pendientes[1:]

            vehiculo = seleccionar_vehiculo(peso_act, vol_act)
            ocup_peso = round(min(peso_act / vehiculo["cap_peso_kg"] * 100, 100.0), 1)
            ocup_vol  = round(min(vol_act  / vehiculo["cap_vol_m3"]  * 100, 100.0), 1)

            # Distancia: promedio ponderado por peso al centroide de clientes
            dist_prom = sum(
                calcular_distancia(cedi, clientes_dict[o["orden_id"]]) * o["peso_kg"]
                for o in carga
            ) / peso_act

            costo    = calcular_costo_viaje(dist_prom, vehiculo, trans, factor_costo)
            revenue  = sum(clientes_dict[o["orden_id"]].get("revenue", o["peso_kg"] * 0.15)
                           for o in carga)
            cliente_principal = clientes_dict[max(carga, key=lambda o: o["peso_kg"])["orden_id"]]

            viaje = {
                "viaje_id":        f"VJ{viaje_id:04d}",
                "cedi_id":         cedi_id,
                "cedi_nombre":     cedi["nombre"],
                "cedi_ciudad":     cedi["ciudad"],
                "cedi_lat":        cedi["lat"],
                "cedi_lon":        cedi["lon"],
                "cliente_ciudad":  ciudad,
                "cliente_lat":     cliente_principal["lat"],
                "cliente_lon":     cliente_principal["lon"],
                "cliente_nombre":  cliente_principal.get("cliente_id","N/A"),
                "ordenes":         [o["orden_id"] for o in carga],
                "n_paradas":       len(carga),
                "distancia_km":    round(dist_prom, 1),
                "peso_kg":         round(peso_act, 2),
                "vol_m3":          round(vol_act, 3),
                "vehiculo":        vehiculo["tipo"],
                "cap_peso_kg":     vehiculo["cap_peso_kg"],
                "cap_vol_m3":      vehiculo["cap_vol_m3"],
                "ocup_peso_pct":   ocup_peso,
                "ocup_vol_pct":    ocup_vol,
                "transportadora":  trans["nombre"],
                "costo_km_base":   vehiculo["costo_km"],
                "costo_total":     costo,
                "revenue_viaje":   round(revenue, 2),
                "margen_viaje":    round(revenue - costo, 2),
                "costo_por_kg":    round(costo / max(peso_act, 0.1), 4),
                "productos":       {"Carga General": int(round(peso_act))},
                "requiere_paqueteo": ocup_peso < ocup_minima_pct,
            }
            viajes.append(viaje)
            if ocup_peso < ocup_minima_pct:
                paqueteo.append(viaje["viaje_id"])

            viaje_id  += 1
            pendientes = no_caben

    # ── KPIs ──────────────────────────────────────────────────────────
    n_ordenes_total = len(ordenes)
    n_ordenes_atendidas = sum(len(v["ordenes"]) for v in viajes)

    kpis = {
        "total_viajes":         len(viajes),
        "viajes_paqueteo":      len(paqueteo),
        "viajes_consolidados":  len(viajes) - len(paqueteo),
        "costo_total":          round(sum(v["costo_total"]   for v in viajes), 2),
        "revenue_total":        round(sum(v["revenue_viaje"] for v in viajes), 2),
        "margen_total":         round(sum(v["margen_viaje"]  for v in viajes), 2),
        "peso_total_kg":        round(sum(v["peso_kg"]       for v in viajes), 2),
        "vol_total_m3":         round(sum(v["vol_m3"]        for v in viajes), 3),
        "dist_total_km":        round(sum(v["distancia_km"]  for v in viajes), 1),
        "ocup_peso_prom":       round(np.mean([v["ocup_peso_pct"] for v in viajes]), 1),
        "ocup_vol_prom":        round(np.mean([v["ocup_vol_pct"]  for v in viajes]), 1),
        "costo_por_kg_prom":    round(np.mean([v["costo_por_kg"]  for v in viajes]), 4),
        "demanda_atendida_pct": round(n_ordenes_atendidas / max(n_ordenes_total, 1) * 100, 1),
        "clientes_por_viaje":   round(np.mean([v["n_paradas"] for v in viajes]), 2),
    }

    return viajes, kpis