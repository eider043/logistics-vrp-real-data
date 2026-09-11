"""
Dashboard VRP — Comparacion Base vs Optimizado + Monitoreo
Estructura inspirada en tablero operativo Carvajal
Autor: Eider
"""

import os, sys
import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, date

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(BASE_DIR, "src"))

st.set_page_config(page_title="VRP Logistics Optimizer", layout="wide", page_icon="truck")

FONT   = "#2C3E50"
C = {
    "azul":    "#AED6F1", "verde":   "#A9DFBF", "amarillo": "#F9E79F",
    "morado":  "#D7BDE2", "salmon":  "#F1948A", "naranja":  "#FAD7A0",
    "gris":    "#F2F3F4", "dark":    "#5D6D7E", "base":     "#85929E",
    "opt":     "#27AE60", "sidebar": "#4A235A",
}

# ── Estilos ───────────────────────────────────────────────────────────
st.markdown(f"""
<style>
    .stApp {{ background-color: #F4F6F9; }}
    section[data-testid="stSidebar"] {{ background-color: {C['sidebar']}; width: 220px !important; }}
    section[data-testid="stSidebar"] * {{ color: white !important; }}
    section[data-testid="stSidebar"] .stSelectbox label {{ color: white !important; }}
    section[data-testid="stSidebar"] .stMultiSelect label {{ color: white !important; }}
    .logo-box {{ padding: 10px 15px 5px 15px; border-bottom: 1px solid rgba(255,255,255,0.2); margin-bottom: 10px; }}
    .logo-text {{ font-size: 1.4rem; font-weight: 900; color: white; }}
    .logo-sub {{ font-size: 0.65rem; color: #FAD7A0; letter-spacing: 1px; }}
    .filtro-btn {{ background-color: #27AE60; color: white; border: none;
                   border-radius: 6px; padding: 8px 20px; font-weight: bold;
                   width: 100%; cursor: pointer; margin-top: 10px; }}
    .kpi-card {{
        background: white; border-radius: 10px; padding: 14px 10px 10px 10px;
        box-shadow: 0 2px 6px rgba(0,0,0,0.08); margin-bottom: 8px;
        border-top: 3px solid #AED6F1;
    }}
    .kpi-title {{ font-size: 0.72rem; color: #888; font-weight: 600;
                  text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 6px; }}
    .kpi-row {{ display: flex; justify-content: space-around; align-items: flex-end; }}
    .kpi-val {{ text-align: center; }}
    .kpi-num {{ font-size: 0.95rem; font-weight: 800; color: {FONT}; }}
    .kpi-num-opt {{ font-size: 0.95rem; font-weight: 800; color: #27AE60; }}
    .kpi-num-save {{ font-size: 0.95rem; font-weight: 800; color: #E74C3C; }}
    .kpi-lbl {{ font-size: 0.62rem; color: #AAA; }}
    .kpi-badge-save {{
        background: #EAFAF1; color: #27AE60; border-radius: 12px;
        padding: 2px 8px; font-size: 0.7rem; font-weight: bold; margin-top: 4px;
        display: inline-block;
    }}
    .section-header {{
        font-size: 1rem; font-weight: 700; color: {FONT};
        border-left: 4px solid #AED6F1; padding-left: 10px; margin: 10px 0 8px 0;
    }}
    .truck-box {{
        background: white; border-radius: 10px; padding: 16px;
        text-align: center; box-shadow: 0 2px 6px rgba(0,0,0,0.07); height: 100%;
    }}
    .truck-pct {{ font-size: 1.6rem; font-weight: 900; color: {FONT}; }}
    .truck-lbl {{ font-size: 0.75rem; color: #AAA; margin-bottom: 8px; }}
    .stTabs [data-baseweb="tab-list"] {{
        background-color: #EAF2FB; border-radius: 8px; padding: 3px; gap: 3px;
    }}
    .stTabs [data-baseweb="tab"] {{
        background-color: #D6EAF8 !important; border-radius: 6px !important;
        color: #1A252F !important; font-weight: 700 !important; font-size: 12px !important;
        padding: 7px 14px !important; border: 2px solid #5D8AA8 !important;
        white-space: nowrap !important; visibility: visible !important; opacity: 1 !important;
    }}
    .stTabs [data-baseweb="tab"] * {{ color: #1A252F !important; visibility: visible !important; }}
    .stTabs [aria-selected="true"] {{ background-color: {C['sidebar']} !important; color: white !important; }}
    .stTabs [aria-selected="true"] * {{ color: white !important; }}
    .monitor-card {{
        background: white; border-radius: 10px; padding: 14px;
        box-shadow: 0 2px 6px rgba(0,0,0,0.07); margin-bottom: 10px;
    }}
</style>
""", unsafe_allow_html=True)


# ── Funciones de layout ───────────────────────────────────────────────
def apply_layout(fig, height=360, **kwargs):
    base = dict(
        height=height, template="plotly_white", plot_bgcolor="white", paper_bgcolor="white",
        title=kwargs.pop("title", ""),
        font=dict(color=FONT, size=11),
        title_font=dict(color=FONT, size=13, family="Arial Black"),
        legend=dict(font=dict(color=FONT, size=10), bgcolor="rgba(255,255,255,0.9)",
                    orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0),
        margin=dict(l=40, r=20, t=50, b=40),
    )
    if "xaxis" not in kwargs:
        base["xaxis"] = dict(tickfont=dict(color=FONT, size=10),
                              title_font=dict(color=FONT), gridcolor="#F0F0F0")
    if "yaxis" not in kwargs:
        base["yaxis"] = dict(tickfont=dict(color=FONT, size=10),
                              title_font=dict(color=FONT), gridcolor="#F0F0F0")
    base.update(kwargs)
    fig.update_layout(**base)
    return fig


# ── Carga y optimizacion ──────────────────────────────────────────────
@st.cache_data
def cargar_datos():
    from data_loader import load_freight_data
    return load_freight_data()

@st.cache_data
def escenario_base_sin_optimizar(n_orders, seed):
    """Escenario base: un viaje por orden, sin consolidacion."""
    from data_loader import build_scenario, VEHICULOS, TRANSPORTADORAS
    from data_loader import haversine
    df = cargar_datos()
    scenario = build_scenario(df, n_orders=n_orders, seed=seed)
    viajes = []
    viaje_id = 1
    for orden in scenario["ordenes"]:
        cliente  = scenario["clientes_dict"][orden["orden_id"]]
        cedi     = scenario["cedis_dict"][orden["cedi_id"]]
        dist     = haversine(cedi["lat"], cedi["lon"], cliente["lat"], cliente["lon"])
        vehiculo = VEHICULOS[2] # Furgon 150kg siempre — representa operacion actual sobredimensionada
        region   = cedi.get("region","Midwest")
        trans    = TRANSPORTADORAS[0] # FedEx = factor 1.05, la mas cara — representa operacion actual
        costo    = round(dist * vehiculo["costo_km"] * trans["factor_tarifa"], 2)
        revenue  = float(cliente.get("revenue", orden["peso_kg"] * 0.15))
        viajes.append({
            "viaje_id":       f"BVJ{viaje_id:04d}",
            "cedi_id":        orden["cedi_id"],
            "cedi_nombre":    cedi["nombre"],
            "cedi_ciudad":    cedi["ciudad"],
            "cedi_lat":       cedi["lat"],
            "cedi_lon":       cedi["lon"],
            "cliente_ciudad": cliente["ciudad"],
            "cliente_lat":    cliente["lat"],
            "cliente_lon":    cliente["lon"],
            "n_paradas":      1,
            "distancia_km":   round(dist, 1),
            "peso_kg":        round(orden["peso_kg"], 2),
            "vol_m3":         round(orden["vol_m3"], 3),
            "vehiculo":       vehiculo["tipo"],
            "cap_peso_kg":    vehiculo["cap_peso_kg"],
            "cap_vol_m3":     vehiculo["cap_vol_m3"],
            "ocup_peso_pct":  round(min(orden["peso_kg"] / vehiculo["cap_peso_kg"] * 100, 100.0), 1),
            "ocup_vol_pct":   round(min(orden["vol_m3"]  / vehiculo["cap_vol_m3"]  * 100, 100.0), 1),
            "transportadora": trans["nombre"],
            "costo_total":    costo,
            "revenue_viaje":  revenue,
            "margen_viaje":   round(revenue - costo, 2),
            "costo_por_kg":   round(costo / max(orden["peso_kg"], 0.1), 4),
        })
        viaje_id += 1
    kpis = _calcular_kpis(viajes, n_ordenes_total=len(scenario["ordenes"]))
    return viajes, kpis, scenario

@st.cache_data
def escenario_optimizado(n_orders, seed, factor_costo):
    from data_loader import build_scenario
    from optimizer import optimizar_escenario
    df = cargar_datos()
    scenario = build_scenario(df, n_orders=n_orders, seed=seed)
    viajes, kpis = optimizar_escenario(scenario, {"factor_costo": factor_costo})
    return viajes, kpis, scenario

def _calcular_kpis(viajes, n_ordenes_total=None):
    if not viajes:
        return {k: 0 for k in ["total_viajes","costo_total","revenue_total","margen_total",
                                 "peso_total_kg","vol_total_m3","dist_total_km",
                                 "ocup_peso_prom","ocup_vol_prom","costo_por_kg_prom",
                                 "demanda_atendida_pct","viajes_paqueteo",
                                 "viajes_consolidados","clientes_por_viaje"]}
    
    ordenes_atendidas = sum(v.get("n_paradas", 1) for v in viajes)
    total = n_ordenes_total if n_ordenes_total else ordenes_atendidas
    
    return {
        "total_viajes":         len(viajes),
        "costo_total":          round(sum(v["costo_total"]   for v in viajes), 2),
        "revenue_total":        round(sum(v["revenue_viaje"] for v in viajes), 2),
        "margen_total":         round(sum(v["margen_viaje"]  for v in viajes), 2),
        "peso_total_kg":        round(sum(v["peso_kg"]       for v in viajes), 2),
        "vol_total_m3":         round(sum(v["vol_m3"]        for v in viajes), 3),
        "dist_total_km":        round(sum(v["distancia_km"]  for v in viajes), 1),
        "ocup_peso_prom":       round(np.mean([v["ocup_peso_pct"] for v in viajes]), 1),
        "ocup_vol_prom":        round(np.mean([v["ocup_vol_pct"]  for v in viajes]), 1),
        "costo_por_kg_prom":    round(np.mean([v["costo_por_kg"]  for v in viajes]), 4),
        "demanda_atendida_pct": round(ordenes_atendidas / max(total, 1) * 100, 1),
        "viajes_paqueteo":      sum(1 for v in viajes if v.get("requiere_paqueteo", False)),
        "viajes_consolidados":  sum(1 for v in viajes if not v.get("requiere_paqueteo", False)),
        "clientes_por_viaje":   round(ordenes_atendidas / max(len(viajes), 1), 2),
    }

def pct_ahorro(base, opt, invert=False):
    if base == 0: return 0.0
    r = (opt - base) / base * 100
    return -r if invert else r


# ── Sidebar ───────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div class='logo-box'>
        <div class='logo-text'>VRP Optimizer</div>
        <div class='logo-sub'>LOGISTICS INTELLIGENCE</div>
    </div>""", unsafe_allow_html=True)

    st.markdown("**Filtros**")
    n_orders     = st.slider("Ordenes", 10, 100, 50, 5)
    seed         = st.selectbox("Escenario", [42, 123, 7, 99, 2024],
                                  help="Semilla aleatoria del escenario")
    factor_opt   = st.slider("Factor tarifa optimizado", 0.7, 1.0, 0.92, 0.01,
                               help="Factor aplicado al escenario optimizado")

    st.markdown("---")
    df_orig = cargar_datos()

    hubs_disp = ["Todas"] + (df_orig["cedi_id"].unique().tolist() if "cedi_id" in df_orig.columns else [])
    filtro_hub = st.selectbox("Centro distribucion", hubs_disp)

    ciudades_disp = ["Todas"] + sorted(df_orig["ciudad_destino"].unique().tolist()
                                        if "ciudad_destino" in df_orig.columns else [])
    filtro_ciudad = st.selectbox("Destino", ciudades_disp)

    anios = ["Todos"] + sorted(df_orig["fecha"].dt.year.dropna().unique().astype(str).tolist()
                                if "fecha" in df_orig.columns else [])
    filtro_anio = st.selectbox("Año", anios)

    meses = ["Todos"] + [str(m) for m in range(1, 13)]
    filtro_mes = st.selectbox("Mes", meses)

    if st.button("Borrar filtros"):
        filtro_hub    = "Todas"
        filtro_ciudad = "Todas"
        filtro_anio   = "Todos"
        filtro_mes    = "Todos"


# ── Cargar escenarios ─────────────────────────────────────────────────
vb, kb, scenario = escenario_base_sin_optimizar(n_orders, seed)
vo, ko, _        = escenario_optimizado(n_orders, seed, factor_opt)

dfb = pd.DataFrame(vb)
dfo = pd.DataFrame(vo)

# Aplicar filtros
def filtrar(df_v, hub, ciudad):
    res = df_v.copy()
    if hub != "Todas":
        res = res[res["cedi_id"] == hub]
    if ciudad != "Todas":
        res = res[res["cliente_ciudad"] == ciudad]
    return res

dfb_f = filtrar(dfb, filtro_hub, filtro_ciudad)
dfo_f = filtrar(dfo, filtro_hub, filtro_ciudad)
kb_f  = _calcular_kpis(dfb_f.to_dict("records"), n_ordenes_total=len(vb))
ko_f  = _calcular_kpis(dfo_f.to_dict("records"), n_ordenes_total=len(vo))


# ── Header ────────────────────────────────────────────────────────────
st.markdown(f"""
<div style='background:linear-gradient(135deg,{C["sidebar"]} 0%,#6C3483 100%);
            padding:12px 20px;border-radius:10px;margin-bottom:12px;'>
    <span style='color:white;font-size:1.4rem;font-weight:900'>
        Optimizacion Red Logistica
    </span>
    <span style='color:#FAD7A0;font-size:0.85rem;margin-left:15px'>
        Base vs Optimizado | {n_orders} ordenes | Factor {factor_opt}x
    </span>
</div>
""", unsafe_allow_html=True)

# ── KPI Cards ─────────────────────────────────────────────────────────
def kpi_card(titulo, val_base, val_opt, fmt="{:,.0f}", prefix="$",
             suffix="", invert=True, color_top="#AED6F1"):
    # Abreviar numeros grandes
    def abreviar(v):
        if isinstance(v, (int, float)):
            if abs(v) >= 1_000_000: return f"{prefix}{v/1_000_000:.1f}M{suffix}"
            if abs(v) >= 1_000:     return f"{prefix}{v/1_000:.1f}K{suffix}"
        return prefix + fmt.format(v) + suffix
    
    ahorro = pct_ahorro(val_base, val_opt, invert=invert)
    badge_color = "#27AE60" if (ahorro > 0 and invert) or (ahorro < 0 and not invert) else "#E74C3C"
    ahorro_str  = f"{ahorro:+.1f}%"
    b_str = abreviar(val_base)
    o_str = abreviar(val_opt)
    return f"""
    <div class='kpi-card' style='border-top-color:{color_top}'>
        <div class='kpi-title'>{titulo}</div>
        <div class='kpi-row'>
            <div class='kpi-val'>
                <div class='kpi-num'>{b_str}</div>
                <div class='kpi-lbl'>Base</div>
            </div>
            <div class='kpi-val'>
                <div class='kpi-num-opt'>{o_str}</div>
                <div class='kpi-lbl'>Optimizado</div>
                <div class='kpi-badge-save' style='background:#EAFAF1;color:{badge_color}'>{ahorro_str}</div>
            </div>
        </div>
    </div>"""

k1, k2, k3, k4, k5, k6 = st.columns(6)
with k1:
    st.markdown(kpi_card("Costo total fletes",
                          kb_f["costo_total"], ko_f["costo_total"],
                          fmt="{:,.0f}", prefix="$", color_top=C["salmon"]), unsafe_allow_html=True)
with k2:
    st.markdown(kpi_card("Costo promedio / kg",
                          kb_f["costo_por_kg_prom"], ko_f["costo_por_kg_prom"],
                          fmt="{:.4f}", prefix="$", color_top=C["amarillo"]), unsafe_allow_html=True)
with k3:
    dem_b = kb["demanda_atendida_pct"]
    dem_o = ko["demanda_atendida_pct"]
    st.markdown(kpi_card("Demanda atendida",
                          dem_b, dem_o,
                          fmt="{:.1f}", prefix="", suffix="%",
                          invert=False, color_top=C["verde"]), unsafe_allow_html=True)
with k4:
    st.markdown(kpi_card("Viajes realizados",
                          kb_f["total_viajes"], ko_f["total_viajes"],
                          fmt="{:,.0f}", prefix="", color_top=C["azul"]), unsafe_allow_html=True)
with k5:
    st.markdown(kpi_card("Ocupacion peso prom",
                          kb_f["ocup_peso_prom"], ko_f["ocup_peso_prom"],
                          fmt="{:.1f}", prefix="", suffix="%",
                          invert=False, color_top=C["morado"]), unsafe_allow_html=True)
with k6:
    st.markdown(kpi_card("Ocupacion volumen prom",
                          kb_f["ocup_vol_prom"], ko_f["ocup_vol_prom"],
                          fmt="{:.1f}", prefix="", suffix="%",
                          invert=False, color_top=C["naranja"]), unsafe_allow_html=True)

st.markdown("---")

# ── Tabs principales ──────────────────────────────────────────────────
tab_opt, tab_mon = st.tabs([
    "Optimizacion — Validacion del Modelo",
    "Monitoreo — Operacion Futura vs Año Anterior"
])


# ════════════════════════════════════════════════════════════════════
# TAB 1 — OPTIMIZACION
# ════════════════════════════════════════════════════════════════════
with tab_opt:

    c_left, c_mid, c_right = st.columns([1.2, 1.2, 0.8])

    # ── Eficiencia logistica (scatter costo vs ocupacion) ────────────
    with c_left:
        st.markdown("<div class='section-header'>Eficiencia logistica</div>",
                    unsafe_allow_html=True)
        dfb_f["Escenario"] = "Base"
        dfo_f["Escenario"] = "Optimizado"
        df_eff = pd.concat([
            dfb_f[["costo_total","ocup_peso_pct","peso_kg","cedi_nombre","Escenario"]],
            dfo_f[["costo_total","ocup_peso_pct","peso_kg","cedi_nombre","Escenario"]]
        ])
        fig = px.scatter(df_eff, x="costo_total", y="ocup_peso_pct",
                         color="Escenario", size="peso_kg",
                         color_discrete_map={"Base": C["base"], "Optimizado": C["opt"]},
                         labels={"costo_total": "Costo Total (USD)",
                                 "ocup_peso_pct": "% Capacidad utilizada kg"},
                         hover_data=["cedi_nombre"])
        apply_layout(fig, height=320, title="")
        st.plotly_chart(fig, use_container_width=True)

    # ── Evolucion capacidad utilizada por hub ────────────────────────
    with c_mid:
        st.markdown("<div class='section-header'>Evolucion cap. utilizada por Hub</div>",
                    unsafe_allow_html=True)
        hubs_order = sorted(dfb_f["cedi_nombre"].unique()) if len(dfb_f) > 0 else []
        ocup_b = dfb_f.groupby("cedi_nombre")["ocup_peso_pct"].mean().reindex(hubs_order)
        ocup_o = dfo_f.groupby("cedi_nombre")["ocup_peso_pct"].mean().reindex(hubs_order)

        fig2 = go.Figure()
        fig2.add_trace(go.Bar(name="Base", x=hubs_order, y=ocup_b.values,
                               marker_color=C["base"],
                               text=[f"{v:.1f}%" for v in ocup_b.values],
                               textposition="outside",
                               textfont=dict(color=FONT, size=10)))
        fig2.add_trace(go.Bar(name="Optimizado", x=hubs_order, y=ocup_o.values,
                               marker_color=C["opt"],
                               text=[f"{v:.1f}%" for v in ocup_o.values],
                               textposition="outside",
                               textfont=dict(color=FONT, size=10)))
        apply_layout(fig2, height=320, title="", barmode="group",
                     yaxis=dict(tickfont=dict(color=FONT), title="% Ocup. Peso",
                                gridcolor="#F0F0F0", range=[0, 110]))
        st.plotly_chart(fig2, use_container_width=True)

    # ── Factor de ocupacion (camiones animados) ───────────────────────
    with c_right:
        st.markdown("<div class='section-header'>Factor de ocupacion (kg)</div>",
                    unsafe_allow_html=True)

        def truck_svg(pct_peso, pct_vol, color, label):
            fill_w_peso = max(int(pct_peso * 0.6), 2)
            fill_w_vol  = max(int(pct_vol  * 0.6), 2)
            return f"""
            <div class='truck-box' style='margin-bottom:8px'>
                <div class='truck-lbl'>{label}</div>
                <div style='display:flex;justify-content:center;gap:20px'>
                    <div style='text-align:center'>
                        <div class='truck-pct' style='color:{color};font-size:1.2rem'>{pct_peso:.1f}%</div>
                        <div style='font-size:0.65rem;color:#AAA'>Peso (kg)</div>
                    </div>
                    <div style='text-align:center'>
                        <div class='truck-pct' style='color:{color};font-size:1.2rem'>{pct_vol:.1f}%</div>
                        <div style='font-size:0.65rem;color:#AAA'>Volumen (m3)</div>
                    </div>
                </div>
                <svg width='110' height='44' viewBox='0 0 110 44'>
                <rect x='5' y='8' width='70' height='26' rx='3'
                        fill='#EEE' stroke='#CCC' stroke-width='1'/>
                <rect x='5' y='8' width='{fill_w_peso}' height='13' rx='2'
                        fill='{color}' opacity='0.8'/>
                <rect x='5' y='21' width='{fill_w_vol}' height='13' rx='2'
                        fill='{color}' opacity='0.4'/>
                <text x='40' y='17' font-size='7' fill='#666' text-anchor='middle'>kg</text>
                <text x='40' y='30' font-size='7' fill='#666' text-anchor='middle'>m3</text>
                <rect x='75' y='18' width='22' height='16' rx='2'
                        fill='#DDD' stroke='#BBB' stroke-width='1'/>
                <circle cx='20' cy='38' r='5' fill='#555'/>
                <circle cx='20' cy='38' r='3' fill='#AAA'/>
                <circle cx='60' cy='38' r='5' fill='#555'/>
                <circle cx='60' cy='38' r='3' fill='#AAA'/>
                <circle cx='88' cy='38' r='5' fill='#555'/>
                <circle cx='88' cy='38' r='3' fill='#AAA'/>
                </svg>
            </div>"""

        ocup_base_total = kb_f["ocup_peso_prom"]
        ocup_opt_total  = ko_f["ocup_peso_prom"]
        st.markdown(
            truck_svg(ocup_base_total, kb_f["ocup_vol_prom"], C["base"], "Base") +
            truck_svg(ocup_opt_total,  ko_f["ocup_vol_prom"], C["opt"],  "Optimizado"),
            unsafe_allow_html=True
        )

    # ── Fila 2: Viajes por transportadora + por Hub + Detalle ─────────
    c1, c2, c3 = st.columns([1.3, 1.0, 1.2])

    with c1:
        st.markdown("<div class='section-header'>Viajes por Transportadora</div>",
                    unsafe_allow_html=True)
        vt_b = dfb_f.groupby("transportadora").agg(
            viajes=("viaje_id","count"),
            costo_kg=("costo_por_kg","mean")
        ).reset_index()
        vt_o = dfo_f.groupby("transportadora").agg(
            viajes=("viaje_id","count"),
            costo_kg=("costo_por_kg","mean")
        ).reset_index()
        all_trans = sorted(set(vt_b["transportadora"]).union(set(vt_o["transportadora"])))

        vt_b = vt_b.set_index("transportadora").reindex(all_trans).fillna(0).reset_index()
        vt_o = vt_o.set_index("transportadora").reindex(all_trans).fillna(0).reset_index()

        fig3 = go.Figure()
        fig3.add_trace(go.Bar(name="Base", x=vt_b["transportadora"], y=vt_b["viajes"],
                               marker_color=C["base"],
                               text=vt_b["viajes"].astype(int),
                               textposition="outside",
                               textfont=dict(color=FONT, size=9)))
        fig3.add_trace(go.Bar(name="Optimizado", x=vt_o["transportadora"], y=vt_o["viajes"],
                               marker_color=C["opt"],
                               text=vt_o["viajes"].astype(int),
                               textposition="outside",
                               textfont=dict(color=FONT, size=9)))
        fig3.add_trace(go.Scatter(name="USD/kg Base", x=vt_b["transportadora"],
                                   y=vt_b["costo_kg"],
                                   mode="lines+markers+text",
                                   yaxis="y2", line=dict(color="#E74C3C", width=2),
                                   marker=dict(size=7),
                                   text=[f"${v:.2f}" for v in vt_b["costo_kg"]],
                                   textposition="top center",
                                   textfont=dict(color="#E74C3C", size=9)))
        apply_layout(fig3, height=320, title="", barmode="group",
                     xaxis=dict(tickfont=dict(color=FONT, size=8), tickangle=-20),
                     yaxis=dict(tickfont=dict(color=FONT), title="Nro. Viajes",
                                gridcolor="#F0F0F0"),
                     yaxis2=dict(title="USD/kg", overlaying="y", side="right",
                                  tickfont=dict(color="#E74C3C", size=9),
                                  title_font=dict(color="#E74C3C")))
        st.plotly_chart(fig3, use_container_width=True)

    with c2:
        st.markdown("<div class='section-header'>Viajes por Hub (CD)</div>",
                    unsafe_allow_html=True)
        vc_b = dfb_f.groupby("cedi_nombre")["viaje_id"].count().reset_index()
        vc_o = dfo_f.groupby("cedi_nombre")["viaje_id"].count().reset_index()
        vc_b.columns = ["CD", "viajes_b"]
        vc_o.columns = ["CD", "viajes_o"]
        vc = vc_b.merge(vc_o, on="CD", how="outer").fillna(0)
        vc["total"] = vc["viajes_b"] + vc["viajes_o"]
        vc = vc.sort_values("total", ascending=False)

        fig4 = go.Figure()
        fig4.add_trace(go.Bar(name="Base", y=vc["CD"], x=vc["viajes_b"],
                               orientation="h", marker_color=C["base"],
                               text=vc["viajes_b"].astype(int),
                               textfont=dict(color=FONT, size=9),
                               textposition="inside"))
        fig4.add_trace(go.Bar(name="Optimizado", y=vc["CD"], x=vc["viajes_o"],
                               orientation="h", marker_color=C["opt"],
                               text=vc["viajes_o"].astype(int),
                               textfont=dict(color=FONT, size=9),
                               textposition="inside"))
        apply_layout(fig4, height=320, title="", barmode="group",
                     xaxis=dict(tickfont=dict(color=FONT), title="Viajes"),
                     yaxis=dict(tickfont=dict(color=FONT, size=9)))
        st.plotly_chart(fig4, use_container_width=True)

    with c3:
        st.markdown("<div class='section-header'>Detalle por Hub</div>",
                    unsafe_allow_html=True)

        det_b = dfb_f.groupby("cedi_nombre").agg(
            peso=("peso_kg","sum"),
            costo_kg=("costo_por_kg","mean"),
            viajes=("viaje_id","count"),
        ).reset_index()
        det_b.columns = ["Hub","Peso (kg)","$/kg Base","Viajes Base"]

        det_o = dfo_f.groupby("cedi_nombre").agg(
            costo_kg_opt=("costo_por_kg","mean"),
            viajes_opt=("viaje_id","count"),
        ).reset_index()
        det_o.columns = ["Hub","$/kg Opt","Viajes Opt"]

        det = det_b.merge(det_o, on="Hub", how="outer").fillna(0)
        det["Ahorro %"] = ((det["$/kg Base"] - det["$/kg Opt"]) /
                            det["$/kg Base"].replace(0, np.nan) * 100).round(1)

        def color_ahorro(v):
            if isinstance(v, float):
                return "color:#27AE60;font-weight:bold" if v > 0 else "color:#E74C3C"
            return ""

        det_display = det[["Hub","Peso (kg)","$/kg Base","$/kg Opt","Ahorro %",
                             "Viajes Base","Viajes Opt"]].copy()
        st.dataframe(
            det_display.style
                .map(color_ahorro, subset=["Ahorro %"])
                .format({"Peso (kg)":"{:,.0f}","$/kg Base":"${:.3f}",
                         "$/kg Opt":"${:.3f}","Ahorro %":"{:+.1f}%",
                         "Viajes Base":"{:.0f}","Viajes Opt":"{:.0f}"}),
            use_container_width=True, height=310
        )

    # ── Fila 3: Mapa + tabla de viajes ─────────────────────────────────
    st.markdown("<div class='section-header'>Mapa de rutas — Base vs Optimizado</div>",
                unsafe_allow_html=True)

    c_map, c_tbl = st.columns([1.5, 1])
    with c_map:
        cedis_df = pd.DataFrame(scenario["cedis"])
        fig_m = go.Figure()

        for v in vb[:30]:
            fig_m.add_trace(go.Scattermap(
                lat=[v["cedi_lat"], v["cliente_lat"]],
                lon=[v["cedi_lon"], v["cliente_lon"]],
                mode="lines", opacity=0.3,
                line=dict(width=1, color="#85929E"),
                hoverinfo="skip", showlegend=False
            ))
        for v in vo[:30]:
            fig_m.add_trace(go.Scattermap(
                lat=[v["cedi_lat"], v["cliente_lat"]],
                lon=[v["cedi_lon"], v["cliente_lon"]],
                mode="lines", opacity=0.5,
                line=dict(width=1.5, color="#27AE60"),
                hoverinfo="skip", showlegend=False
            ))

        fig_m.add_trace(go.Scattermap(
            lat=cedis_df["lat"], lon=cedis_df["lon"],
            mode="markers+text",
            marker=dict(size=18, color=C["sidebar"], symbol="square"),
            text=cedis_df["nombre"], textposition="top right",
            textfont=dict(size=11, color="#1A1A1A"),
            name="Hubs"
        ))
        fig_m.add_trace(go.Scattermap(
            lat=dfb_f["cliente_lat"], lon=dfb_f["cliente_lon"],
            mode="markers",
            marker=dict(size=7, color=C["base"], opacity=0.7),
            name="Rutas Base", hoverinfo="skip"
        ))
        fig_m.add_trace(go.Scattermap(
            lat=dfo_f["cliente_lat"], lon=dfo_f["cliente_lon"],
            mode="markers",
            marker=dict(size=9, color=C["opt"], opacity=0.8),
            name="Rutas Opt.",
            hovertext=dfo_f["cliente_ciudad"] + "<br>Costo: $" +
                       dfo_f["costo_total"].apply(lambda x: f"{x:,.0f}"),
            hoverinfo="text"
        ))
        fig_m.update_layout(
            map=dict(style="carto-positron", center=dict(lat=38.0, lon=-96.0), zoom=3.2),
            height=380, margin=dict(l=0,r=0,t=0,b=0),
            legend=dict(bgcolor="rgba(255,255,255,0.9)", font=dict(color=FONT, size=11),
                        x=0.01, y=0.99),
            paper_bgcolor="white", font=dict(color=FONT)
        )
        st.plotly_chart(fig_m, use_container_width=True)
        st.caption("Gris: rutas base (sin consolidar) | Verde: rutas optimizadas | Cuadrado: Hub CD")

    with c_tbl:
        st.markdown("**Comparacion de viajes optimizados**")
        tbl = dfo_f[["viaje_id","cedi_nombre","cliente_ciudad","peso_kg",
                      "ocup_peso_pct","vehiculo","transportadora",
                      "costo_total","margen_viaje"]].copy()
        tbl.columns = ["Viaje","Hub","Destino","Peso(kg)","Ocup%",
                        "Vehiculo","Transportadora","Costo","Margen"]

        def c_m(v):
            if isinstance(v,(int,float)):
                return "color:#27AE60" if v > 0 else "color:#E74C3C"
            return ""
        def c_o(v):
            if isinstance(v,(int,float)):
                if v < 30: return "background:#F1948A"
                if v > 70: return "background:#A9DFBF"
            return ""

        st.dataframe(
            tbl.style.map(c_m, subset=["Margen"]).map(c_o, subset=["Ocup%"])
               .format({"Costo":"${:,.0f}","Margen":"${:,.0f}",
                        "Peso(kg)":"{:.0f}","Ocup%":"{:.1f}%"}),
            use_container_width=True, height=380
        )


# ════════════════════════════════════════════════════════════════════
# TAB 2 — MONITOREO
# ════════════════════════════════════════════════════════════════════
with tab_mon:
    st.markdown("""
    <div style='background:#EAFAF1;border-left:4px solid #27AE60;
                padding:10px 15px;border-radius:6px;margin-bottom:12px'>
        <b style='color:#1E8449'>Monitoreo de operacion futura</b> —
        Compara los resultados reales de cada semana/mes contra el mismo periodo
        del año anterior (antes de implementar el modelo de optimizacion).
        A medida que avanza la operacion, los datos se acumulan automaticamente.
    </div>
    """, unsafe_allow_html=True)

    # Simulacion de datos historicos (año anterior) vs futuros (con modelo)
    np.random.seed(99)
    semanas = list(range(1, 13))
    hist_costo    = [kb_f["costo_total"] * np.random.uniform(0.95, 1.10) for _ in semanas]
    hist_viajes   = [kb_f["total_viajes"] * np.random.uniform(0.90, 1.15) for _ in semanas]
    hist_ocup     = [kb_f["ocup_peso_prom"] * np.random.uniform(0.85, 1.05) for _ in semanas]
    hist_costo_kg = [kb_f["costo_por_kg_prom"] * np.random.uniform(0.95, 1.10) for _ in semanas]

    # Semanas "futuras" con modelo (solo hasta semana actual simulada)
    semana_actual = st.slider("Semana actual (simulacion de avance)", 1, 12, 6)
    fut_costo    = [ko_f["costo_total"] * np.random.uniform(0.92, 1.05)
                    if i < semana_actual else None for i in range(12)]
    fut_viajes   = [ko_f["total_viajes"] * np.random.uniform(0.90, 1.05)
                    if i < semana_actual else None for i in range(12)]
    fut_ocup     = [ko_f["ocup_peso_prom"] * np.random.uniform(0.95, 1.10)
                    if i < semana_actual else None for i in range(12)]
    fut_costo_kg = [ko_f["costo_por_kg_prom"] * np.random.uniform(0.90, 1.05)
                    if i < semana_actual else None for i in range(12)]

    # KPIs de monitoreo
    sem_reales = [v for v in fut_costo if v is not None]
    sem_hist   = hist_costo[:len(sem_reales)]
    ahorro_acum = sum(h - f for h, f in zip(sem_hist, sem_reales))
    pct_red     = ahorro_acum / sum(sem_hist) * 100 if sem_hist else 0

    m1, m2, m3, m4 = st.columns(4)
    with m1:
        st.markdown(f"""<div class='monitor-card'>
            <div class='kpi-title'>Ahorro acumulado (USD)</div>
            <div class='kpi-num-opt' style='font-size:1.4rem'>${ahorro_acum:,.0f}</div>
            <div class='kpi-lbl'>{semana_actual} semanas con modelo</div>
        </div>""", unsafe_allow_html=True)
    with m2:
        st.markdown(f"""<div class='monitor-card'>
            <div class='kpi-title'>Reduccion de costo</div>
            <div class='kpi-num-opt' style='font-size:1.4rem'>{pct_red:.1f}%</div>
            <div class='kpi-lbl'>vs año anterior mismo periodo</div>
        </div>""", unsafe_allow_html=True)
    with m3:
        viajes_red = (kb_f["total_viajes"] - ko_f["total_viajes"]) * semana_actual
        st.markdown(f"""<div class='monitor-card'>
            <div class='kpi-title'>Viajes ahorrados</div>
            <div class='kpi-num-opt' style='font-size:1.4rem'>{int(viajes_red)}</div>
            <div class='kpi-lbl'>vs operacion sin modelo</div>
        </div>""", unsafe_allow_html=True)
    with m4:
        mejora_ocup = ko_f["ocup_peso_prom"] - kb_f["ocup_peso_prom"]
        st.markdown(f"""<div class='monitor-card'>
            <div class='kpi-title'>Mejora ocupacion</div>
            <div class='kpi-num-opt' style='font-size:1.4rem'>{mejora_ocup:+.1f}%</div>
            <div class='kpi-lbl'>puntos porcentuales</div>
        </div>""", unsafe_allow_html=True)

    st.markdown("---")
    mc1, mc2 = st.columns(2)

    with mc1:
        st.markdown("<div class='section-header'>Evolucion costo de flete semanal</div>",
                    unsafe_allow_html=True)
        fig_mon1 = go.Figure()
        fig_mon1.add_trace(go.Scatter(
            x=semanas, y=hist_costo, name="Año anterior (sin modelo)",
            mode="lines+markers", line=dict(color=C["base"], width=2, dash="dash"),
            marker=dict(size=7, color=C["base"])
        ))
        fig_mon1.add_trace(go.Scatter(
            x=semanas[:semana_actual],
            y=[v for v in fut_costo if v is not None],
            name="Año actual (con modelo)",
            mode="lines+markers", line=dict(color=C["opt"], width=2),
            marker=dict(size=8, color=C["opt"])
        ))
        fig_mon1.add_vrect(
            x0=semana_actual - 0.5, x1=12.5,
            fillcolor="#F9E79F", opacity=0.3, line_width=0,
            annotation_text="Semanas futuras",
            annotation_font=dict(color=FONT, size=10)
        )
        apply_layout(fig_mon1, height=320, title="",
                     xaxis=dict(tickfont=dict(color=FONT), title="Semana"),
                     yaxis=dict(tickfont=dict(color=FONT), title="Costo Flete (USD)",
                                gridcolor="#F0F0F0"))
        st.plotly_chart(fig_mon1, use_container_width=True)

    with mc2:
        st.markdown("<div class='section-header'>Evolucion ocupacion de camiones semanal</div>",
                    unsafe_allow_html=True)
        fig_mon2 = go.Figure()
        fig_mon2.add_trace(go.Scatter(
            x=semanas, y=hist_ocup, name="Año anterior",
            mode="lines+markers", line=dict(color=C["base"], width=2, dash="dash"),
            marker=dict(size=7, color=C["base"])
        ))
        fig_mon2.add_trace(go.Scatter(
            x=semanas[:semana_actual],
            y=[v for v in fut_ocup if v is not None],
            name="Año actual (con modelo)",
            mode="lines+markers", line=dict(color=C["opt"], width=2),
            marker=dict(size=8, color=C["opt"])
        ))
        fig_mon2.add_hline(y=70, line_dash="dot", line_color="#E74C3C",
                           annotation_text="Meta 70%",
                           annotation_font_color=FONT)
        apply_layout(fig_mon2, height=320, title="",
                     xaxis=dict(tickfont=dict(color=FONT), title="Semana"),
                     yaxis=dict(tickfont=dict(color=FONT), title="Ocup. Peso (%)",
                                gridcolor="#F0F0F0", range=[0, 120]))
        st.plotly_chart(fig_mon2, use_container_width=True)

    mc3, mc4 = st.columns(2)

    with mc3:
        st.markdown("<div class='section-header'>Viajes realizados por semana</div>",
                    unsafe_allow_html=True)
        fig_mon3 = go.Figure()
        fig_mon3.add_trace(go.Bar(
            x=semanas, y=hist_viajes, name="Año anterior",
            marker_color=C["base"], opacity=0.7
        ))
        fig_mon3.add_trace(go.Bar(
            x=semanas[:semana_actual],
            y=[v for v in fut_viajes if v is not None],
            name="Año actual (con modelo)", marker_color=C["opt"]
        ))
        apply_layout(fig_mon3, height=300, title="", barmode="group",
                     xaxis=dict(tickfont=dict(color=FONT), title="Semana"),
                     yaxis=dict(tickfont=dict(color=FONT), title="Nro. Viajes",
                                gridcolor="#F0F0F0"))
        st.plotly_chart(fig_mon3, use_container_width=True)

    with mc4:
        st.markdown("<div class='section-header'>Costo por kg transportado</div>",
                    unsafe_allow_html=True)
        fig_mon4 = go.Figure()
        fig_mon4.add_trace(go.Scatter(
            x=semanas, y=hist_costo_kg, name="Año anterior",
            mode="lines+markers+text",
            line=dict(color=C["base"], width=2, dash="dash"),
            text=[f"${v:.3f}" for v in hist_costo_kg],
            textposition="top center",
            textfont=dict(color=C["base"], size=8),
            marker=dict(size=6)
        ))
        fig_mon4.add_trace(go.Scatter(
            x=semanas[:semana_actual],
            y=[v for v in fut_costo_kg if v is not None],
            name="Año actual", mode="lines+markers+text",
            line=dict(color=C["opt"], width=2),
            text=[f"${v:.3f}" for v in fut_costo_kg if v is not None],
            textposition="top center",
            textfont=dict(color=C["opt"], size=8),
            marker=dict(size=8)
        ))
        apply_layout(fig_mon4, height=300, title="",
                     xaxis=dict(tickfont=dict(color=FONT), title="Semana"),
                     yaxis=dict(tickfont=dict(color=FONT), title="USD/kg",
                                gridcolor="#F0F0F0"))
        st.plotly_chart(fig_mon4, use_container_width=True)

    # Tabla resumen de monitoreo
    st.markdown("<div class='section-header'>Tabla resumen de monitoreo semanal</div>",
                unsafe_allow_html=True)
    df_mon = pd.DataFrame({
        "Semana":           semanas,
        "Costo Año Ant.":  [round(v, 0) for v in hist_costo],
        "Costo Con Modelo": [round(v, 0) if v else None for v in fut_costo],
        "Ahorro USD":       [round(h - f, 0) if f else None
                             for h, f in zip(hist_costo, fut_costo)],
        "Ahorro %":         [round((h - f) / h * 100, 1) if f else None
                             for h, f in zip(hist_costo, fut_costo)],
        "Viajes Ant.":      [round(v, 0) for v in hist_viajes],
        "Viajes Modelo":    [round(v, 0) if v else None for v in fut_viajes],
        "Ocup% Ant.":       [round(v, 1) for v in hist_ocup],
        "Ocup% Modelo":     [round(v, 1) if v else None for v in fut_ocup],
    })

    def c_ahorro(v):
        if isinstance(v,(int,float)): return "color:#27AE60;font-weight:bold" if v > 0 else ""
        return ""

    st.dataframe(
        df_mon.style
              .map(c_ahorro, subset=["Ahorro USD","Ahorro %"])
              .format({"Costo Año Ant.":"${:,.0f}","Costo Con Modelo":"${:,.0f}",
                       "Ahorro USD":"${:,.0f}","Ahorro %":"{:.1f}%",
                       "Viajes Ant.":"{:.0f}","Viajes Modelo":"{:.0f}",
                       "Ocup% Ant.":"{:.1f}%","Ocup% Modelo":"{:.1f}%"},
                      na_rep="—"),
        use_container_width=True, height=320
    )

# ── Exportar ──────────────────────────────────────────────────────────
if st.sidebar.button("Exportar Plan Optimizado Excel"):
    with st.spinner("Generando..."):
        from excel_exporter import exportar_plan_operativo
        nombre = f"Opt_Ord{n_orders}_F{factor_opt}"
        path = exportar_plan_operativo(vo, ko, scenario, nombre)
        with open(path, "rb") as f:
            st.sidebar.download_button(
                "Descargar Excel", f, os.path.basename(path),
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

st.markdown("---")
st.caption("VRP Fleet Optimization | Clarke-Wright | Base vs Optimizado | Eider — Data Scientist")