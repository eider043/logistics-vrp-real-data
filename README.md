# VRP Logistics Route Optimizer — Real Fleet Operations Data

![Python](https://img.shields.io/badge/Python-3.13-blue?logo=python)
![Status](https://img.shields.io/badge/Status-Completado-green)
![License](https://img.shields.io/badge/License-MIT-yellow)
![Data](https://img.shields.io/badge/Data-Real%20Kaggle-orange)
![Algorithm](https://img.shields.io/badge/Algorithm-Clarke--Wright%20VRP-purple)
![Dashboard](https://img.shields.io/badge/Dashboard-Streamlit-blue)
![Excel](https://img.shields.io/badge/Output-Excel-green)

## Descripcion

Proyecto de optimizacion de costos logisticos de distribucion basado en datos reales de
operaciones de flota (**Logistics Fleet Data — Kaggle**). Implementa el algoritmo
**Clarke-Wright Savings** para resolver el **Capacitated Vehicle Routing Problem (CVRP)**
con restricciones de peso y volumen, consolidacion de pedidos por ciudad (max. 4 clientes
por viaje) y seleccion optima de vehiculo y transportadora.

El dashboard permite comparar el **escenario base** (operacion actual sin optimizacion) contra
el **escenario optimizado** (resultado del modelo), cuantificando el ahorro en costos,
la reduccion de viajes y la mejora en ocupacion de flota. Incluye una segunda vista de
**monitoreo de la operacion futura** para validar que los ahorros se mantienen semana a semana
frente al mismo periodo del ano anterior.

---

## Problema resuelto

Dado un conjunto de pedidos de clientes asignados a Centros de Distribucion (Hubs), el
modelo busca:

- **Minimizar** el costo total de fletes (distancia x tarifa x factor transportadora)
- **Maximizar** la ocupacion de vehiculos en peso y volumen
- **Reducir** el numero de viajes realizados
- **Garantizar** el 100% de la demanda atendida en ambos escenarios
- **Identificar** viajes candidatos a paqueteo (ocupacion < 80%)

---

## Algoritmo de optimizacion

### Clarke-Wright Savings + First Fit Decreasing (FFD)

El algoritmo Clarke-Wright calcula el ahorro en distancia al combinar rutas individuales
de cada cliente hacia el depot en rutas conjuntas. Para cada par de clientes i, j, el ahorro
es `s_ij = c_i0 + c_0j - c_ij`. Las rutas se fusionan en orden descendente de ahorro,
siempre que no se supere la capacidad del vehiculo.

**Pipeline de optimizacion implementado:**

metricgate

Reasignacion al Hub mas cercano por distancia Haversine
Agrupacion por (Hub, Ciudad destino)
Ordenamiento de ordenes por peso descendente (FFD)
Consolidacion: hasta 4 clientes por viaje, mismo Hub y ciudad
Seleccion del vehiculo mas pequeno que cumpla la carga consolidada
Seleccion de la transportadora de menor tarifa con cobertura en la region
Calculo de costo ponderado por peso (distancia promedio)
Marcado de viajes con ocupacion < 80% como candidatos a paqueteo

**Escenario base (sin optimizar):**
- Un viaje por orden (sin consolidacion)
- Vehiculo sobredimensionado (Furgon 150kg por defecto)
- Transportadora con tarifa estandar (factor 1.10)

**Escenario optimizado:**
- Consolidacion de hasta 4 clientes en el mismo viaje si comparten ciudad
- Vehiculo mas economico que cumpla exactamente la carga consolidada
- Transportadora de menor tarifa disponible en la region (factor desde 0.85)

---

## Dataset

**Fuente:** [Logistics Fleet Data — Kaggle](https://www.kaggle.com/datasets/syednaveed05/logistics-fleet-data)

| Archivo | Contenido |
|---|---|
| Freight Data | Customer ID, Ciudad, Peso (kg), Volumen (cubico), Revenue |
| Cost Data | Truck ID, KM recorridos, Combustible, Mantenimiento, Costos fijos |

**Descarga automatica via Kaggle API:**

```bash
kaggle datasets download -d syednaveed05/logistics-fleet-data -p data/ --unzip
```

**Transformaciones aplicadas:**
- Normalizacion de nombres de columnas
- Deteccion automatica de columnas por keywords
- Imputacion de volumen desde peso (ratio 0.003 m3/kg)
- Asignacion de ciudades conocidas con coordenadas reales
- Clip de pesos entre 1 y 60 kg para consistencia con flota disponible
- Asignacion de Hub mas cercano por region geografica

---

## Red logistica simulada

### Hubs de distribucion (CEDIs)

| Hub ID | Nombre | Ciudad | Region |
|---|---|---|---|
| HUB-EAST | Hub Este | New York | Northeast |
| HUB-SOUTH | Hub Sur | Houston | South |
| HUB-WEST | Hub Oeste | Los Angeles | West |
| HUB-MID | Hub Centro | Chicago | Midwest |

### Flota de vehiculos

| Tipo | Capacidad Peso | Capacidad Vol | Costo/km |
|---|---|---|---|
| Moto mensajeria | 15 kg | 0.06 m3 | $200 |
| Van pequena | 40 kg | 0.16 m3 | $450 |
| Furgon 150kg | 150 kg | 0.60 m3 | $800 |
| Camion 500kg | 500 kg | 2.00 m3 | $1,400 |

### Transportadoras

| Transportadora | Factor tarifa | Cobertura |
|---|---|---|
| FedEx Freight | 1.10 | Nacional |
| UPS Freight | 1.00 | Northeast, Midwest, South, West |
| XPO Logistics | 0.90 | South, West, Southeast |
| Old Dominion | 0.85 | Northeast, Southeast, Midwest |

---

## Dashboard interactivo

El dashboard tiene dos vistas principales:

### Vista 1 — Optimizacion: Validacion del modelo

Compara escenario base vs optimizado con:

- **KPIs principales**: costo total fletes, costo/kg, demanda atendida, viajes realizados,
  ocupacion peso y volumen — todos con variacion porcentual vs base
- **Eficiencia logistica**: scatter costo total vs ocupacion por escenario
- **Evolucion capacidad por Hub**: barras comparativas base vs optimizado por Hub
- **Factor de ocupacion**: visualizacion tipo camion con % peso y volumen
- **Viajes por transportadora**: barras + linea de costo/kg por escenario
- **Viajes por Hub (CD)**: comparacion horizontal de volumen de rutas
- **Detalle por Hub**: tabla con ahorro en $/kg y reduccion de viajes
- **Mapa de rutas**: rutas base (gris) vs optimizadas (verde) sobre mapa real de EE.UU.
- **Tabla de viajes optimizados**: con colores de ocupacion y margen por viaje

### Vista 2 — Monitoreo: Operacion futura vs Año anterior

Acumula semana a semana la comparacion entre:
- Año anterior (sin modelo): simulado con parametros del escenario base
- Año actual (con modelo): resultado del optimizador semana a semana

Incluye:
- KPIs de ahorro acumulado, reduccion de costo %, viajes ahorrados y mejora de ocupacion
- Evolucion semanal de costo de flete
- Evolucion semanal de ocupacion de camiones con meta del 70%
- Viajes realizados por semana (barras comparativas)
- Costo por kg transportado semanal con etiquetas
- Tabla resumen de monitoreo semanal con formato condicional

### Filtros disponibles (sidebar)

- Numero de ordenes a optimizar (10 - 100)
- Escenario / semilla aleatoria
- Factor de tarifa del escenario optimizado
- Centro de distribucion (Hub)
- Ciudad destino
- Año y mes

---

## Salida Excel — Plan Operativo

El plan operativo exportado incluye 3 hojas:

### Hoja 1: Resumen Ejecutivo
KPIs consolidados: costo total, revenue, margen, peso movilizado, distancia,
ocupacion promedio, rentabilidad.

### Hoja 2: Plan de Viajes
| Campo | Descripcion |
|---|---|
| Viaje ID | Identificador unico del viaje |
| Hub Origen | Centro de distribucion de salida |
| Ciudad Hub | Ciudad del Hub |
| Cliente Principal | Cliente de mayor peso en el viaje |
| Ciudad Destino | Ciudad de entrega |
| N. Paradas | Clientes consolidados en el viaje |
| Distancia (km) | Distancia ponderada por peso |
| Peso (kg) | Carga total del viaje |
| Volumen (m3) | Volumen total del viaje |
| Ocup. Peso % | % de ocupacion en peso (verde > 70%, rojo < 30%) |
| Ocup. Vol % | % de ocupacion en volumen |
| Vehiculo | Tipo de vehiculo asignado |
| Cap. Peso (kg) | Capacidad maxima del vehiculo |
| Cap. Vol (m3) | Capacidad volumetrica del vehiculo |
| Transportadora | Empresa de transporte seleccionada |
| Costo Flete | Costo total del viaje en USD |
| Revenue | Ingreso asociado al viaje |
| Margen | Revenue - Costo (verde si positivo) |
| Costo/kg | Eficiencia de costo por kg transportado |
| Ordenes | IDs de ordenes incluidas en el viaje |

### Hoja 3: Resumen por Hub
Agregacion de viajes, costos, revenue, margen, peso y ocupacion por Hub.

---

## Estructura del proyecto

```
logistics-vrp-real-data/
├── src/
│ ├── main.py # Pipeline principal: carga, optimiza, exporta
│ ├── data_loader.py # Descarga API Kaggle, transformacion, build_scenario
│ ├── optimizer.py # Algoritmo Clarke-Wright + FFD, KPIs
│ ├── excel_exporter.py # Exportacion plan operativo Excel (openpyxl)
│ └── dashboard.py # Dashboard Streamlit: Base vs Optimizado + Monitoreo
├── notebooks/
│ └── analisis_exploratorio.ipynb # EDA del dataset real
├── data/
│ ├── (archivos Kaggle descargados aqui)
│ └── freight_transformed.csv # Dataset transformado y limpio
└── outputs/
└── plan_operativo_*.xlsx # Planes exportados
```

---

## Stack tecnologico

| Componente | Tecnologia |
|---|---|
| Lenguaje | Python 3.13 |
| Optimizacion | Clarke-Wright Savings + First Fit Decreasing |
| Distancias | Formula Haversine (coordenadas reales) |
| Dataset | Logistics Fleet Data (Kaggle API) |
| Visualizacion | Plotly + Streamlit |
| Mapa | Plotly Scattermapbox (carto-positron) |
| Plan operativo | openpyxl (Excel .xlsx) |
| Analisis | Pandas, NumPy, Matplotlib, Seaborn |

---

## Reproducir el proyecto

### Prerequisitos

```bash
# 1. Instalar dependencias
pip install -r requirements.txt

# 2. Configurar Kaggle API
# Descarga kaggle.json desde https://www.kaggle.com/settings
# Coloca el archivo en:
# Windows: C:\Users\<usuario>\.kaggle\kaggle.json
# Linux/Mac: ~/.kaggle/kaggle.json
```

### Ejecucion

```bash
# Paso 1: Pipeline principal (descarga, transforma, optimiza, exporta)
cd src
python main.py

# Paso 2: Dashboard interactivo
streamlit run dashboard.py
```
## Demo

[Tablero logístico](https://logistics-vrp-real-data-jmyjqrg8siaearrehdq9zb.streamlit.app/)

### Parametros configurables

| Parametro | Descripcion | Default |
|---|---|---|
| n_orders | Numero de ordenes a optimizar | 50 |
| seed | Semilla aleatoria del escenario | 42 |
| factor_opt | Factor de tarifa escenario optimizado | 0.92 |
| max_clientes_viaje | Max clientes consolidados por viaje | 4 |
| ocup_minima_pct | Umbral minimo ocupacion (bajo = paqueteo) | 80% |

---

## Resultados esperados (escenario 50 ordenes)

| Indicador | Base | Optimizado | Mejora |
|---|---|---|---|
| Viajes realizados | 50 | ~15-25 | -50% a -70% |
| Costo total fletes | Alto | Reducido | -30% a -50% |
| Ocupacion peso prom | ~10-20% | ~60-80% | +40-60 pp |
| Demanda atendida | 100% | 100% | 0% |
| Viajes candidatos paqueteo | 0 | Identificados | — |

---

## Conceptos clave

**VRP (Vehicle Routing Problem):** Problema de optimizacion combinatoria que busca
determinar el conjunto optimo de rutas para una flota de vehiculos que deben atender
a un conjunto de clientes desde un deposito central, minimizando el costo total.

**Clarke-Wright Savings:** Heuristica constructiva publicada en 1964 que produce soluciones
de alta calidad en tiempo O(n² log n), siendo el punto de partida estandar para planificacion
de rutas de entrega con flota de capacidad limitada. 

**First Fit Decreasing (FFD):** Heuristica de empaquetamiento que ordena los pedidos de
mayor a menor peso antes de asignarlos a vehiculos, maximizando la consolidacion y ocupacion.

**Paqueteo:** Viajes con ocupacion inferior al 80% que el negocio puede considerar enviar
mediante servicios de mensajeria o courier en lugar de vehiculo dedicado, reduciendo costos.

---

## Autor
**Eider** — Cientifico de Datos   
[![Fiverr](https://img.shields.io/badge/Fiverr-Contrátame-1DBF73?logo=fiverr)](https://www.fiverr.com/eiderdatadriven)
[![GitHub](https://img.shields.io/badge/GitHub-eider043-black?logo=github)](https://github.com/eider043)
