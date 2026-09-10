"""
Pipeline principal — VRP con datos reales de operaciones de flota
Autor: Eider
"""

import sys, os
sys.path.insert(0, os.path.dirname(__file__))

from data_loader import load_freight_data, build_scenario
from optimizer import optimizar_escenario
from excel_exporter import exportar_plan_operativo


def main():
    print("=" * 60)
    print("VRP LOGISTICO — DATOS REALES LOGISTICS FLEET DATA")
    print("Clarke-Wright Savings | First Fit Decreasing")
    print("=" * 60)

    print("\n[1/3] Cargando datos reales...")
    df = load_freight_data()

    print("\n[2/3] Optimizando rutas...")
    scenario = build_scenario(df, n_orders=50, seed=42)
    viajes, kpis = optimizar_escenario(scenario)

    print("\n[3/3] Exportando plan operativo...")
    path = exportar_plan_operativo(viajes, kpis, scenario, "RealData")

    print("\n--- RESULTADOS ---")
    for k, v in kpis.items():
        print(f"  {k:25s}: {v}")

    print(f"\nPlan guardado en: {path}")
    print("Dashboard: streamlit run dashboard.py")


if __name__ == "__main__":
    main()